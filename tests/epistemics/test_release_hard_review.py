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
    EpistemicError,
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
    InvalidEvaluationError,
    InvalidEvidenceError,
    ProvenanceSource,
    ProvenanceSourceKind,
    ProvenanceStep,
    ProvenanceTrail,
)
from capability_lab.semantics import CapabilityConceptRef


T0 = datetime(2026, 8, 15, 11, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("subject_release_review")


def actor_trail(*, step_at: datetime | None = None) -> ProvenanceTrail:
    steps = () if step_at is None else (ProvenanceStep("capture", step_at),)
    return ProvenanceTrail(
        sources=(ProvenanceSource(ProvenanceSourceKind.ACTOR, "operator"),),
        steps=steps,
    )


def evidence_record() -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=EvidenceId("ev_release"),
        subject_ref=SUBJECT,
        kind=EvidenceKind.PROJECT,
        summary="Bounded release-review observation.",
        context=EvidenceContext("Release-review context."),
        observed_at=T0,
        recorded_at=T0 + timedelta(minutes=1),
        provenance=actor_trail(),
    )


def test_evidence_rejects_self_parent_before_snapshot_assembly() -> None:
    provenance = ProvenanceTrail(
        sources=(
            ProvenanceSource(ProvenanceSourceKind.EVIDENCE_RECORD, "ev_self"),
        )
    )
    with pytest.raises(InvalidEvidenceError, match="may not derive from itself"):
        EvidenceRecord(
            evidence_id=EvidenceId("ev_self"),
            subject_ref=SUBJECT,
            kind=EvidenceKind.PROJECT,
            summary="Impossible self-derived evidence.",
            context=EvidenceContext("Bounded context."),
            observed_at=T0,
            recorded_at=T0 + timedelta(minutes=1),
            provenance=provenance,
        )


def test_claim_rejects_self_parent_before_snapshot_assembly() -> None:
    provenance = ProvenanceTrail(
        sources=(ProvenanceSource(ProvenanceSourceKind.CLAIM, "claim_self"),)
    )
    with pytest.raises(InvalidClaimError, match="may not derive from itself"):
        CapabilityClaim(
            claim_id=CapabilityClaimId("claim_self"),
            subject_ref=SUBJECT,
            concept_ref=CapabilityConceptRef.parse("core:bounded_capability@1"),
            statement="Impossible self-derived proposition.",
            scope=ClaimScope("Bounded scope."),
            created_at=T0 + timedelta(minutes=2),
            provenance=provenance,
        )


def test_evidence_rejects_provenance_step_after_recording_boundary() -> None:
    with pytest.raises(InvalidEvidenceError, match="after evidence recorded_at"):
        EvidenceRecord(
            evidence_id=EvidenceId("ev_future_step"),
            subject_ref=SUBJECT,
            kind=EvidenceKind.PROJECT,
            summary="Impossible future transformation.",
            context=EvidenceContext("Bounded context."),
            observed_at=T0,
            recorded_at=T0 + timedelta(minutes=1),
            provenance=actor_trail(step_at=T0 + timedelta(minutes=2)),
        )


def test_claim_rejects_provenance_step_after_creation_boundary() -> None:
    with pytest.raises(InvalidClaimError, match="after claim created_at"):
        CapabilityClaim(
            claim_id=CapabilityClaimId("claim_future_step"),
            subject_ref=SUBJECT,
            concept_ref=CapabilityConceptRef.parse("core:bounded_capability@1"),
            statement="Impossible future-derived proposition.",
            scope=ClaimScope("Bounded scope."),
            created_at=T0 + timedelta(minutes=2),
            provenance=actor_trail(step_at=T0 + timedelta(minutes=3)),
        )


def test_sufficient_coverage_requires_relevant_evidence() -> None:
    not_relevant = EvidenceAssessment(
        evidence_id=EvidenceId("ev_irrelevant"),
        bearing=EvidenceBearing.NOT_RELEVANT,
        reliability=EvidenceReliability.HIGH,
        coverage_note="Outside the claim scope.",
        rationale="The observation does not bear on this proposition.",
    )
    with pytest.raises(InvalidEvaluationError, match="requires at least one relevant"):
        ClaimEvaluation(
            evaluation_id=ClaimEvaluationId("eval_bad_coverage"),
            claim_id=CapabilityClaimId("claim_coverage"),
            policy_ref=EvaluationPolicyRef.parse("core:manual_evidence_review@1"),
            evaluator_ref=EvaluatorRef(EvaluatorKind.HUMAN, "reviewer"),
            evaluated_at=T0 + timedelta(minutes=3),
            evidence_assessments=(not_relevant,),
            coverage=CoverageAssessment(
                CoverageStatus.SUFFICIENT_FOR_CLAIM,
                "Invalid claim of sufficient coverage.",
            ),
            conflict_status=ConflictStatus.NONE,
            conclusion=EvaluationConclusion.INSUFFICIENT,
            rationale="No relevant evidence is available.",
        )


def test_sufficient_coverage_allows_indeterminate_relevant_evidence() -> None:
    indeterminate = EvidenceAssessment(
        evidence_id=EvidenceId("ev_indeterminate"),
        bearing=EvidenceBearing.INDETERMINATE,
        reliability=EvidenceReliability.MODERATE,
        coverage_note="The claim scope was directly examined.",
        rationale="The observation is relevant but directionally unresolved.",
    )
    item = ClaimEvaluation(
        evaluation_id=ClaimEvaluationId("eval_indeterminate_coverage"),
        claim_id=CapabilityClaimId("claim_coverage"),
        policy_ref=EvaluationPolicyRef.parse("core:manual_evidence_review@1"),
        evaluator_ref=EvaluatorRef(EvaluatorKind.HUMAN, "reviewer"),
        evaluated_at=T0 + timedelta(minutes=3),
        evidence_assessments=(indeterminate,),
        coverage=CoverageAssessment(
            CoverageStatus.SUFFICIENT_FOR_CLAIM,
            "The scoped area was examined despite an indeterminate result.",
        ),
        conflict_status=ConflictStatus.NONE,
        conclusion=EvaluationConclusion.INSUFFICIENT,
        rationale="Coverage and directional support remain separate dimensions.",
    )
    assert item.coverage.status is CoverageStatus.SUFFICIENT_FOR_CLAIM
    assert item.conclusion is EvaluationConclusion.INSUFFICIENT


@pytest.mark.parametrize(
    "invalid_timestamp",
    [
        "2026-08-15Q11:00:00+00:00",
        "2026-08-15 11:00:00+00:00",
        "20260815T110000+0000",
        "2026-08-15T11:00:00",
    ],
)
def test_strict_ingestion_rejects_non_profile_timestamp_forms(
    invalid_timestamp: str,
) -> None:
    payload = EpistemicRecordSet(evidence_records=(evidence_record(),)).to_dict()
    payload["evidence_records"][0]["observed_at"] = invalid_timestamp
    with pytest.raises(EpistemicError, match="extended ISO-8601"):
        EpistemicRecordSet.from_dict(payload)


def test_strict_ingestion_accepts_explicit_offset_and_canonicalizes_to_utc() -> None:
    payload = EpistemicRecordSet(evidence_records=(evidence_record(),)).to_dict()
    payload["evidence_records"][0]["observed_at"] = "2026-08-15T17:00:00+06:00"
    payload["evidence_records"][0]["recorded_at"] = "2026-08-15T17:01:00+06:00"

    restored = EpistemicRecordSet.from_dict(payload)

    assert restored.evidence_records[0].observed_at == T0
    assert restored.to_dict()["evidence_records"][0]["observed_at"] == "2026-08-15T11:00:00Z"
