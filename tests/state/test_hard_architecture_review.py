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
    ProvenanceSource,
    ProvenanceSourceKind,
    ProvenanceTrail,
)
from capability_lab.semantics import CapabilityConceptRef
from capability_lab.state import (
    CompetenceDimensionState,
    CompetenceFrameRef,
    DimensionConflictStatus,
    DimensionStanding,
    InvalidPersonalCapabilityState,
    InvalidStateSet,
    PersonalCapabilityState,
    PersonalCapabilityStateId,
    PersonalCapabilityStateSet,
    StateDerivationPolicyRef,
    StateDeriverKind,
    StateDeriverRef,
)


T0 = datetime(2026, 8, 15, 6, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("subject_review")
CONCEPT = CapabilityConceptRef.parse("core:review_capability@1")
CLAIM_ID = CapabilityClaimId("claim_review")
SUPPORTED_EVAL_ID = ClaimEvaluationId("eval_supported")
UNRESOLVED_EVAL_ID = ClaimEvaluationId("eval_unresolved")


def trail() -> ProvenanceTrail:
    return ProvenanceTrail(
        (ProvenanceSource(ProvenanceSourceKind.ACTOR, "reviewer"),)
    )


def evidence(evidence_id: str) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=EvidenceId(evidence_id),
        subject_ref=SUBJECT,
        kind=EvidenceKind.PROJECT,
        summary=f"Review evidence {evidence_id}.",
        context=EvidenceContext("Bounded review context."),
        observed_at=T0 - timedelta(minutes=20),
        recorded_at=T0 - timedelta(minutes=19),
        provenance=trail(),
    )


def records() -> EpistemicRecordSet:
    support = evidence("ev_support")
    contradiction = evidence("ev_contradict")
    claim = CapabilityClaim(
        claim_id=CLAIM_ID,
        subject_ref=SUBJECT,
        concept_ref=CONCEPT,
        statement="Can perform the bounded review capability.",
        scope=ClaimScope("Bounded review scope."),
        created_at=T0 - timedelta(minutes=15),
        provenance=trail(),
    )
    supported = ClaimEvaluation(
        evaluation_id=SUPPORTED_EVAL_ID,
        claim_id=CLAIM_ID,
        policy_ref=EvaluationPolicyRef.parse("core:review_policy_a@1"),
        evaluator_ref=EvaluatorRef(EvaluatorKind.HUMAN, "reviewer_a"),
        evaluated_at=T0 - timedelta(minutes=5),
        evidence_assessments=(
            EvidenceAssessment(
                support.evidence_id,
                EvidenceBearing.SUPPORTS,
                EvidenceReliability.HIGH,
                "Direct bounded coverage.",
                "This evidence supports the scoped proposition.",
            ),
        ),
        coverage=CoverageAssessment(
            CoverageStatus.SUFFICIENT_FOR_CLAIM,
            "Sufficient for the bounded claim.",
        ),
        conflict_status=ConflictStatus.NONE,
        conclusion=EvaluationConclusion.SUPPORTED,
        rationale="One governed policy supports the scoped claim.",
    )
    unresolved = ClaimEvaluation(
        evaluation_id=UNRESOLVED_EVAL_ID,
        claim_id=CLAIM_ID,
        policy_ref=EvaluationPolicyRef.parse("core:review_policy_b@1"),
        evaluator_ref=EvaluatorRef(EvaluatorKind.HUMAN, "reviewer_b"),
        evaluated_at=T0 - timedelta(minutes=4),
        evidence_assessments=(
            EvidenceAssessment(
                support.evidence_id,
                EvidenceBearing.SUPPORTS,
                EvidenceReliability.MODERATE,
                "Partial positive coverage.",
                "Support remains visible.",
            ),
            EvidenceAssessment(
                contradiction.evidence_id,
                EvidenceBearing.CONTRADICTS,
                EvidenceReliability.MODERATE,
                "Partial contradictory coverage.",
                "Contradiction remains visible.",
            ),
        ),
        coverage=CoverageAssessment(
            CoverageStatus.PARTIAL,
            "The conflict prevents a clean directional conclusion.",
        ),
        conflict_status=ConflictStatus.UNRESOLVED,
        conclusion=EvaluationConclusion.INSUFFICIENT,
        rationale="The second policy preserves unresolved conflict.",
    )
    return EpistemicRecordSet(
        evidence_records=(support, contradiction),
        claims=(claim,),
        evaluations=(supported, unresolved),
    )


def state_with_dimension(dimension: CompetenceDimensionState) -> PersonalCapabilityStateSet:
    state = PersonalCapabilityState(
        state_id=PersonalCapabilityStateId("state_review"),
        subject_ref=SUBJECT,
        concept_ref=CONCEPT,
        frame_ref=CompetenceFrameRef.parse("core:review_frame@1"),
        derivation_policy_ref=StateDerivationPolicyRef.parse(
            "core:review_state_policy@1"
        ),
        deriver_ref=StateDeriverRef(StateDeriverKind.RULE, "review_rule"),
        as_of=T0,
        derived_at=T0,
        dimensions=(dimension,),
        rationale="Hard-review state fixture.",
    )
    return PersonalCapabilityStateSet(SUBJECT, (state,))


def supported_conflicted_dimension() -> CompetenceDimensionState:
    return CompetenceDimensionState(
        "execution",
        DimensionStanding.SUPPORTED,
        supported_claim_ids=(CLAIM_ID,),
        basis_evaluation_ids=(SUPPORTED_EVAL_ID, UNRESOLVED_EVAL_ID),
        rationale="Supported scoped content remains while conflict is unresolved.",
        conflict_status=DimensionConflictStatus.UNRESOLVED,
    )


def test_supported_content_can_coexist_with_unresolved_conflict() -> None:
    state_with_dimension(supported_conflicted_dimension()).validate_against_epistemics(
        records()
    )


def test_insufficient_content_can_coexist_with_unresolved_conflict() -> None:
    dimension = CompetenceDimensionState(
        "execution",
        DimensionStanding.INSUFFICIENT,
        basis_evaluation_ids=(UNRESOLVED_EVAL_ID,),
        rationale="No supported state content is accepted while conflict remains.",
        conflict_status=DimensionConflictStatus.UNRESOLVED,
    )
    state_with_dimension(dimension).validate_against_epistemics(records())


def test_state_must_not_hide_unresolved_conflict_present_in_basis() -> None:
    dimension = CompetenceDimensionState(
        "execution",
        DimensionStanding.SUPPORTED,
        supported_claim_ids=(CLAIM_ID,),
        basis_evaluation_ids=(SUPPORTED_EVAL_ID, UNRESOLVED_EVAL_ID),
        rationale="Invalid hidden-conflict fixture.",
        conflict_status=DimensionConflictStatus.NONE,
    )
    with pytest.raises(InvalidStateSet, match="must not hide"):
        state_with_dimension(dimension).validate_against_epistemics(records())


def test_unknown_cannot_claim_dimension_conflict_without_basis() -> None:
    with pytest.raises(InvalidPersonalCapabilityState, match="UNKNOWN"):
        CompetenceDimensionState(
            "execution",
            DimensionStanding.UNKNOWN,
            rationale="Invalid unknown conflict fixture.",
            conflict_status=DimensionConflictStatus.UNRESOLVED,
        )


def test_dimension_conflict_roundtrips_without_collapsing_into_standing() -> None:
    state_set = state_with_dimension(supported_conflicted_dimension())
    restored = PersonalCapabilityStateSet.from_json(state_set.to_json())
    dimension = restored.states[0].dimensions[0]
    assert dimension.standing is DimensionStanding.SUPPORTED
    assert dimension.conflict_status is DimensionConflictStatus.UNRESOLVED


def test_naive_state_time_uses_state_domain_error() -> None:
    naive = datetime(2026, 8, 15, 6, 0)
    with pytest.raises(InvalidPersonalCapabilityState, match="timezone-aware"):
        PersonalCapabilityState(
            state_id=PersonalCapabilityStateId("state_naive"),
            subject_ref=SUBJECT,
            concept_ref=CONCEPT,
            frame_ref=CompetenceFrameRef.parse("core:review_frame@1"),
            derivation_policy_ref=StateDerivationPolicyRef.parse(
                "core:review_state_policy@1"
            ),
            deriver_ref=StateDeriverRef(StateDeriverKind.HUMAN, "reviewer"),
            as_of=naive,
            derived_at=T0,
            dimensions=(
                CompetenceDimensionState(
                    "execution",
                    DimensionStanding.UNKNOWN,
                    rationale="No basis.",
                ),
            ),
            rationale="Invalid naive-time fixture.",
        )


def test_invalid_deriver_ref_uses_state_domain_error() -> None:
    with pytest.raises(
        InvalidPersonalCapabilityState,
        match="state deriver ref",
    ):
        StateDeriverRef(StateDeriverKind.MODEL, "not valid whitespace")
