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
    InvalidClaimEvidenceCandidatePortfolio,
    ProvenanceSource,
    ProvenanceSourceKind,
    ProvenanceTrail,
    build_complete_claim_evidence_candidate_portfolio_v1,
    claim_evidence_candidate_portfolio_receipt_from_dict,
    claim_evidence_candidate_portfolio_receipt_from_json,
    validate_exact_claim_evidence_candidate_selection_v1,
)
from capability_lab.semantics import CapabilityConceptRef, CapabilityId


def _time(hour: int) -> datetime:
    return datetime(2026, 9, 1, hour, 0, tzinfo=timezone.utc)


def _provenance(ref: str) -> ProvenanceTrail:
    return ProvenanceTrail(
        sources=(ProvenanceSource(ProvenanceSourceKind.SYSTEM, ref),)
    )


def _claim() -> CapabilityClaim:
    return CapabilityClaim(
        claim_id=CapabilityClaimId("claim_1"),
        subject_ref=CapabilitySubjectRef("subject_1"),
        concept_ref=CapabilityConceptRef(
            CapabilityId.parse("research:signal_reasoning"), 1
        ),
        statement="The subject can reason about bounded signal evidence.",
        scope=ClaimScope("Bounded signal reasoning.", ("bounded_reasoning",)),
        created_at=_time(12),
        provenance=_provenance("claim_source"),
    )


def _evidence(value: str) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=EvidenceId(value),
        subject_ref=CapabilitySubjectRef("subject_1"),
        kind=EvidenceKind.ARTIFACT,
        summary=f"Evidence {value}.",
        context=EvidenceContext("Generic context.", ("generic",)),
        observed_at=_time(10),
        recorded_at=_time(11),
        provenance=_provenance(f"source_{value}"),
    )


def test_partial_existing_claim_evaluation_cannot_filter_candidate_membership():
    claim = _claim()
    first = _evidence("evidence_1")
    second = _evidence("evidence_2")
    evaluation = ClaimEvaluation(
        evaluation_id=ClaimEvaluationId("evaluation_1"),
        claim_id=claim.claim_id,
        policy_ref=EvaluationPolicyRef("capability_lab", "test_policy", 1),
        evaluator_ref=EvaluatorRef(EvaluatorKind.HUMAN, "reviewer_1"),
        evaluated_at=_time(14),
        evidence_assessments=(
            EvidenceAssessment(
                evidence_id=first.evidence_id,
                bearing=EvidenceBearing.NOT_RELEVANT,
                reliability=EvidenceReliability.LOW,
                coverage_note="Only one candidate was dispositioned.",
                rationale="Existing evaluation cannot define PR12.8 membership.",
            ),
        ),
        coverage=CoverageAssessment(CoverageStatus.PARTIAL, "Partial coverage."),
        conflict_status=ConflictStatus.NONE,
        conclusion=EvaluationConclusion.INSUFFICIENT,
        rationale="Partial existing evaluation.",
    )
    records = EpistemicRecordSet(
        evidence_records=(first, second),
        claims=(claim,),
        evaluations=(evaluation,),
    )

    portfolio = build_complete_claim_evidence_candidate_portfolio_v1(
        records=records,
        claim_id=claim.claim_id,
        as_of=_time(14),
    )
    assert portfolio.evidence_ids == (
        EvidenceId("evidence_1"),
        EvidenceId("evidence_2"),
    )


def test_schema_parser_rejects_non_string_keys_and_nonstandard_json_constants():
    claim = _claim()
    records = EpistemicRecordSet(
        evidence_records=(_evidence("evidence_1"),),
        claims=(claim,),
    )
    portfolio = build_complete_claim_evidence_candidate_portfolio_v1(
        records=records,
        claim_id=claim.claim_id,
        as_of=_time(14),
    )

    payload = portfolio.to_dict()
    payload[1] = "bad-key"
    with pytest.raises(
        InvalidClaimEvidenceCandidatePortfolio,
        match="keys must use exact strings",
    ):
        claim_evidence_candidate_portfolio_receipt_from_dict(payload)

    bad_json = portfolio.to_json().replace(
        '"schema_version":1',
        '"schema_version":NaN',
    )
    with pytest.raises(
        InvalidClaimEvidenceCandidatePortfolio,
        match="non-standard JSON constant",
    ):
        claim_evidence_candidate_portfolio_receipt_from_json(bad_json)


def test_post_construction_noncanonical_timestamps_fail_closed():
    claim = _claim()
    evidence = _evidence("evidence_1")
    records = EpistemicRecordSet(evidence_records=(evidence,), claims=(claim,))
    portfolio = build_complete_claim_evidence_candidate_portfolio_v1(
        records=records,
        claim_id=claim.claim_id,
        as_of=_time(14),
    )

    shifted = portfolio.as_of.astimezone(timezone(timedelta(hours=6)))
    object.__setattr__(portfolio, "as_of", shifted)
    with pytest.raises(
        InvalidClaimEvidenceCandidatePortfolio,
        match="canonical UTC",
    ):
        validate_exact_claim_evidence_candidate_selection_v1(
            records=records,
            claim_id=claim.claim_id,
            as_of=_time(14),
            selected_evidence_ids=(EvidenceId("evidence_1"),),
            portfolio=portfolio,
        )

    object.__setattr__(evidence, "recorded_at", shifted)
    corrupted_records = EpistemicRecordSet(
        evidence_records=(evidence,),
        claims=(claim,),
    )
    with pytest.raises(
        InvalidClaimEvidenceCandidatePortfolio,
        match="canonical UTC",
    ):
        build_complete_claim_evidence_candidate_portfolio_v1(
            records=corrupted_records,
            claim_id=claim.claim_id,
            as_of=_time(14),
        )
