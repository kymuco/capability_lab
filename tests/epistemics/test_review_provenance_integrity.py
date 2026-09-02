from datetime import datetime, timedelta, timezone

import pytest

from capability_lab.epistemics import (
    CapabilityClaim,
    CapabilityClaimId,
    CapabilitySubjectRef,
    ClaimEvaluation,
    ClaimEvaluationId,
    ClaimScope,
    ConflictStatus,
    CoverageAssessment,
    CoverageStatus,
    EpistemicRecordSet,
    EvaluationConclusion,
    EvaluationPolicyRef,
    EvaluatorKind,
    EvaluatorRef,
    EvidenceAssessment,
    EvidenceBearing,
    EvidenceContext,
    EvidenceId,
    EvidenceKind,
    EvidenceRecord,
    EvidenceReliability,
    InvalidClaimError,
    InvalidEvidenceError,
    InvalidRecordSetError,
    ProvenanceSource,
    ProvenanceSourceKind,
    ProvenanceStep,
    ProvenanceTrail,
)
from capability_lab.semantics import CapabilityConceptRef


T0 = datetime(2026, 8, 14, 9, 0, tzinfo=timezone.utc)
ALICE = CapabilitySubjectRef("alice")
BOB = CapabilitySubjectRef("bob")


def actor_trail(*, step_at: datetime | None = None) -> ProvenanceTrail:
    steps = () if step_at is None else (ProvenanceStep("capture", step_at),)
    return ProvenanceTrail(
        sources=(ProvenanceSource(ProvenanceSourceKind.ACTOR, "operator"),),
        steps=steps,
    )


def evidence(
    eid: str,
    *,
    subject: CapabilitySubjectRef = ALICE,
    observed_at: datetime = T0,
    recorded_at: datetime = T0 + timedelta(minutes=2),
    provenance: ProvenanceTrail | None = None,
) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=EvidenceId(eid),
        subject_ref=subject,
        kind=EvidenceKind.PROJECT,
        summary=f"Observation {eid}.",
        context=EvidenceContext("Bounded bench context."),
        observed_at=observed_at,
        recorded_at=recorded_at,
        provenance=provenance or actor_trail(),
    )


def claim(
    cid: str,
    *,
    subject: CapabilitySubjectRef = ALICE,
    created_at: datetime = T0 + timedelta(minutes=5),
    provenance: ProvenanceTrail | None = None,
) -> CapabilityClaim:
    return CapabilityClaim(
        claim_id=CapabilityClaimId(cid),
        subject_ref=subject,
        concept_ref=CapabilityConceptRef.parse(
            "civilization_bootstrap:electric_motor_construction@1"
        ),
        statement=f"Scoped proposition {cid}.",
        scope=ClaimScope("Low-voltage bounded scope."),
        created_at=created_at,
        provenance=provenance or actor_trail(),
    )


def evaluation(
    claim_id: str,
    evidence_id: str,
    *,
    evaluated_at: datetime,
) -> ClaimEvaluation:
    return ClaimEvaluation(
        evaluation_id=ClaimEvaluationId("eval_01"),
        claim_id=CapabilityClaimId(claim_id),
        policy_ref=EvaluationPolicyRef.parse("core:manual_evidence_review@1"),
        evaluator_ref=EvaluatorRef(EvaluatorKind.HUMAN, "reviewer"),
        evaluated_at=evaluated_at,
        evidence_assessments=(
            EvidenceAssessment(
                EvidenceId(evidence_id),
                EvidenceBearing.SUPPORTS,
                EvidenceReliability.HIGH,
                "Bounded coverage.",
                "Relevant observation.",
            ),
        ),
        coverage=CoverageAssessment(CoverageStatus.PARTIAL, "Bounded evidence."),
        conflict_status=ConflictStatus.NONE,
        conclusion=EvaluationConclusion.SUPPORTED,
        rationale="Supported within the stated scope.",
    )


def test_evidence_provenance_may_not_depend_on_internal_claim() -> None:
    with pytest.raises(InvalidEvidenceError, match="claims are interpretations"):
        evidence(
            "ev_a",
            provenance=ProvenanceTrail(
                sources=(ProvenanceSource(ProvenanceSourceKind.CLAIM, "claim_a"),)
            ),
        )


def test_claim_provenance_may_not_bind_evidence_record() -> None:
    with pytest.raises(InvalidClaimError, match="belongs to ClaimEvaluation"):
        claim(
            "claim_a",
            provenance=ProvenanceTrail(
                sources=(
                    ProvenanceSource(ProvenanceSourceKind.EVIDENCE_RECORD, "ev_a"),
                )
            ),
        )


def test_dangling_source_claim_is_rejected() -> None:
    c = claim(
        "claim_a",
        provenance=ProvenanceTrail(
            sources=(ProvenanceSource(ProvenanceSourceKind.CLAIM, "missing"),)
        ),
    )
    with pytest.raises(InvalidRecordSetError, match="missing source claim"):
        EpistemicRecordSet(claims=(c,))


def test_claim_provenance_cycle_is_rejected() -> None:
    a = claim(
        "claim_a",
        provenance=ProvenanceTrail(
            sources=(ProvenanceSource(ProvenanceSourceKind.CLAIM, "claim_b"),)
        ),
    )
    b = claim(
        "claim_b",
        provenance=ProvenanceTrail(
            sources=(ProvenanceSource(ProvenanceSourceKind.CLAIM, "claim_a"),)
        ),
    )
    with pytest.raises(InvalidRecordSetError, match="claim provenance must be acyclic"):
        EpistemicRecordSet(claims=(a, b))


def test_derived_evidence_cannot_cross_subjects() -> None:
    source = evidence("ev_source", subject=BOB)
    derived = evidence(
        "ev_derived",
        subject=ALICE,
        provenance=ProvenanceTrail(
            sources=(
                ProvenanceSource(ProvenanceSourceKind.EVIDENCE_RECORD, "ev_source"),
            )
        ),
    )
    with pytest.raises(InvalidRecordSetError, match="source subject must match"):
        EpistemicRecordSet(evidence_records=(source, derived))


def test_derived_claim_cannot_cross_subjects() -> None:
    source = claim("claim_source", subject=BOB)
    derived = claim(
        "claim_derived",
        subject=ALICE,
        provenance=ProvenanceTrail(
            sources=(
                ProvenanceSource(ProvenanceSourceKind.CLAIM, "claim_source"),
            )
        ),
    )
    with pytest.raises(InvalidRecordSetError, match="source claim subject must match"):
        EpistemicRecordSet(claims=(source, derived))


def test_derived_evidence_cannot_precede_source_recording() -> None:
    source = evidence("ev_source", recorded_at=T0 + timedelta(minutes=4))
    derived = evidence(
        "ev_derived",
        recorded_at=T0 + timedelta(minutes=3),
        provenance=ProvenanceTrail(
            sources=(
                ProvenanceSource(ProvenanceSourceKind.EVIDENCE_RECORD, "ev_source"),
            )
        ),
    )
    with pytest.raises(InvalidRecordSetError, match="must not follow derived evidence"):
        EpistemicRecordSet(evidence_records=(source, derived))


def test_derived_evidence_steps_cannot_predate_source_record() -> None:
    source = evidence("ev_source", recorded_at=T0 + timedelta(minutes=4))
    derived = evidence(
        "ev_derived",
        recorded_at=T0 + timedelta(minutes=6),
        provenance=ProvenanceTrail(
            sources=(
                ProvenanceSource(ProvenanceSourceKind.EVIDENCE_RECORD, "ev_source"),
            ),
            steps=(ProvenanceStep("derive", T0 + timedelta(minutes=3)),),
        ),
    )
    with pytest.raises(InvalidRecordSetError, match="must not precede source evidence"):
        EpistemicRecordSet(evidence_records=(source, derived))


def test_derived_claim_steps_cannot_predate_source_claim() -> None:
    source = claim("claim_source", created_at=T0 + timedelta(minutes=5))
    derived = claim(
        "claim_derived",
        created_at=T0 + timedelta(minutes=7),
        provenance=ProvenanceTrail(
            sources=(
                ProvenanceSource(ProvenanceSourceKind.CLAIM, "claim_source"),
            ),
            steps=(ProvenanceStep("derive", T0 + timedelta(minutes=4)),),
        ),
    )
    with pytest.raises(InvalidRecordSetError, match="must not precede source claim"):
        EpistemicRecordSet(claims=(source, derived))


def test_provenance_step_cannot_postdate_record_creation() -> None:
    with pytest.raises(InvalidEvidenceError, match="after evidence recorded_at"):
        evidence(
            "ev_a",
            recorded_at=T0 + timedelta(minutes=2),
            provenance=actor_trail(step_at=T0 + timedelta(minutes=3)),
        )

    with pytest.raises(InvalidClaimError, match="after claim created_at"):
        claim(
            "claim_a",
            created_at=T0 + timedelta(minutes=5),
            provenance=actor_trail(step_at=T0 + timedelta(minutes=6)),
        )


def test_evaluation_cannot_predate_claim() -> None:
    ev = evidence("ev_a")
    c = claim("claim_a", created_at=T0 + timedelta(minutes=5))
    result = evaluation(
        "claim_a",
        "ev_a",
        evaluated_at=T0 + timedelta(minutes=4),
    )
    with pytest.raises(InvalidRecordSetError, match="precede claim created_at"):
        EpistemicRecordSet(evidence_records=(ev,), claims=(c,), evaluations=(result,))


def test_evaluation_cannot_use_evidence_observed_in_its_future() -> None:
    ev = evidence(
        "ev_a",
        observed_at=T0 + timedelta(minutes=9),
        recorded_at=T0 + timedelta(minutes=10),
    )
    c = claim("claim_a", created_at=T0 + timedelta(minutes=5))
    result = evaluation(
        "claim_a",
        "ev_a",
        evaluated_at=T0 + timedelta(minutes=8),
    )
    with pytest.raises(InvalidRecordSetError, match="assessed evidence observed_at"):
        EpistemicRecordSet(evidence_records=(ev,), claims=(c,), evaluations=(result,))


def test_historical_evaluation_allows_later_local_evidence_ingestion() -> None:
    ev = evidence(
        "ev_a",
        observed_at=T0,
        recorded_at=T0 + timedelta(minutes=20),
    )
    c = claim("claim_a", created_at=T0 + timedelta(minutes=5))
    result = evaluation(
        "claim_a",
        "ev_a",
        evaluated_at=T0 + timedelta(minutes=8),
    )
    records = EpistemicRecordSet(
        evidence_records=(ev,),
        claims=(c,),
        evaluations=(result,),
    )
    assert records.evaluations == (result,)
