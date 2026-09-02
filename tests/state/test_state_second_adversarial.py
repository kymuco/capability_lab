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
    InvalidStateSet,
    PersonalCapabilityState,
    PersonalCapabilityStateId,
    PersonalCapabilityStateSet,
    StateDerivationPolicyRef,
    StateDeriverKind,
    StateDeriverRef,
)


T0 = datetime(2026, 8, 15, 6, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("subject_second_review")
CONCEPT = CapabilityConceptRef.parse("core:second_review_capability@1")
CLAIM_ID = CapabilityClaimId("claim_second_review")
SUPPORT_EVAL_ID = ClaimEvaluationId("eval_second_support")
CONTRADICT_EVAL_ID = ClaimEvaluationId("eval_second_contradict")
UNRESOLVED_EVAL_ID = ClaimEvaluationId("eval_second_unresolved")


def provenance() -> ProvenanceTrail:
    return ProvenanceTrail(
        (ProvenanceSource(ProvenanceSourceKind.ACTOR, "second_reviewer"),)
    )


def _evidence(evidence_id: str) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=EvidenceId(evidence_id),
        subject_ref=SUBJECT,
        kind=EvidenceKind.PROJECT,
        summary=f"Second adversarial evidence {evidence_id}.",
        context=EvidenceContext("Bounded second-pass context."),
        observed_at=T0 - timedelta(minutes=30),
        recorded_at=T0 - timedelta(minutes=29),
        provenance=provenance(),
    )


def _claim() -> CapabilityClaim:
    return CapabilityClaim(
        claim_id=CLAIM_ID,
        subject_ref=SUBJECT,
        concept_ref=CONCEPT,
        statement="Can perform the bounded second-pass capability.",
        scope=ClaimScope("Bounded second-pass scope."),
        created_at=T0 - timedelta(minutes=25),
        provenance=provenance(),
    )


def _assessment(
    evidence_id: str,
    bearing: EvidenceBearing,
) -> EvidenceAssessment:
    return EvidenceAssessment(
        EvidenceId(evidence_id),
        bearing,
        EvidenceReliability.HIGH,
        "Direct bounded coverage.",
        "The evidence has the stated directional bearing on the claim.",
    )


def _supported_evaluation(*, evaluated_at=T0 - timedelta(minutes=10)) -> ClaimEvaluation:
    return ClaimEvaluation(
        evaluation_id=SUPPORT_EVAL_ID,
        claim_id=CLAIM_ID,
        policy_ref=EvaluationPolicyRef.parse("core:second_support_policy@1"),
        evaluator_ref=EvaluatorRef(EvaluatorKind.HUMAN, "second_support_reviewer"),
        evaluated_at=evaluated_at,
        evidence_assessments=(
            _assessment("ev_second_support", EvidenceBearing.SUPPORTS),
        ),
        coverage=CoverageAssessment(
            CoverageStatus.SUFFICIENT_FOR_CLAIM,
            "Sufficient bounded support coverage.",
        ),
        conflict_status=ConflictStatus.NONE,
        conclusion=EvaluationConclusion.SUPPORTED,
        rationale="The bounded claim is supported under this evaluation policy.",
    )


def _contradicted_evaluation(
    *,
    evaluated_at=T0 - timedelta(minutes=9),
) -> ClaimEvaluation:
    return ClaimEvaluation(
        evaluation_id=CONTRADICT_EVAL_ID,
        claim_id=CLAIM_ID,
        policy_ref=EvaluationPolicyRef.parse("core:second_contradict_policy@1"),
        evaluator_ref=EvaluatorRef(
            EvaluatorKind.HUMAN,
            "second_contradict_reviewer",
        ),
        evaluated_at=evaluated_at,
        evidence_assessments=(
            _assessment("ev_second_contradict", EvidenceBearing.CONTRADICTS),
        ),
        coverage=CoverageAssessment(
            CoverageStatus.SUFFICIENT_FOR_CLAIM,
            "Sufficient bounded contradiction coverage.",
        ),
        conflict_status=ConflictStatus.NONE,
        conclusion=EvaluationConclusion.CONTRADICTED,
        rationale="The bounded claim is contradicted under this evaluation policy.",
    )


def _unresolved_evaluation() -> ClaimEvaluation:
    return ClaimEvaluation(
        evaluation_id=UNRESOLVED_EVAL_ID,
        claim_id=CLAIM_ID,
        policy_ref=EvaluationPolicyRef.parse("core:second_unresolved_policy@1"),
        evaluator_ref=EvaluatorRef(
            EvaluatorKind.HUMAN,
            "second_unresolved_reviewer",
        ),
        evaluated_at=T0 - timedelta(minutes=8),
        evidence_assessments=(
            _assessment("ev_second_support", EvidenceBearing.SUPPORTS),
            _assessment("ev_second_contradict", EvidenceBearing.CONTRADICTS),
        ),
        coverage=CoverageAssessment(
            CoverageStatus.PARTIAL,
            "Directional conflict remains unresolved.",
        ),
        conflict_status=ConflictStatus.UNRESOLVED,
        conclusion=EvaluationConclusion.INSUFFICIENT,
        rationale="The evaluation preserves unresolved directional conflict.",
    )


def records(
    *,
    include_contradicted: bool = True,
    include_unresolved: bool = False,
    contradicted_at=T0 - timedelta(minutes=9),
) -> EpistemicRecordSet:
    evaluations = [_supported_evaluation()]
    if include_contradicted:
        evaluations.append(_contradicted_evaluation(evaluated_at=contradicted_at))
    if include_unresolved:
        evaluations.append(_unresolved_evaluation())
    return EpistemicRecordSet(
        evidence_records=(
            _evidence("ev_second_support"),
            _evidence("ev_second_contradict"),
        ),
        claims=(_claim(),),
        evaluations=tuple(evaluations),
    )


def _state(
    state_id: str,
    dimensions: tuple[CompetenceDimensionState, ...],
    *,
    as_of=T0,
) -> PersonalCapabilityState:
    return PersonalCapabilityState(
        state_id=PersonalCapabilityStateId(state_id),
        subject_ref=SUBJECT,
        concept_ref=CONCEPT,
        frame_ref=CompetenceFrameRef.parse("core:second_review_frame@1"),
        derivation_policy_ref=StateDerivationPolicyRef.parse(
            "core:second_review_state_policy@1"
        ),
        deriver_ref=StateDeriverRef(StateDeriverKind.RULE, "second_review_rule"),
        as_of=as_of,
        derived_at=as_of,
        dimensions=dimensions,
        rationale="Second adversarial state fixture.",
    )


def _supported_dimension(
    key: str,
    *,
    conflict_status=DimensionConflictStatus.NONE,
) -> CompetenceDimensionState:
    return CompetenceDimensionState(
        key,
        DimensionStanding.SUPPORTED,
        supported_claim_ids=(CLAIM_ID,),
        basis_evaluation_ids=(SUPPORT_EVAL_ID,),
        rationale="The scoped claim is represented as supported content.",
        conflict_status=conflict_status,
    )


def test_cross_dimension_partition_cannot_hide_directional_conflict() -> None:
    state = _state(
        "state_partitioned_conflict",
        (
            _supported_dimension("execution"),
            CompetenceDimensionState(
                "diagnosis",
                DimensionStanding.INSUFFICIENT,
                basis_evaluation_ids=(CONTRADICT_EVAL_ID,),
                rationale="Contradicting basis is represented separately.",
            ),
        ),
    )
    with pytest.raises(InvalidStateSet, match="elsewhere in the same state basis"):
        PersonalCapabilityStateSet(SUBJECT, (state,)).validate_against_epistemics(
            records()
        )


def test_unresolved_claim_conflict_propagates_to_other_dimension_using_claim() -> None:
    state = _state(
        "state_partitioned_unresolved",
        (
            _supported_dimension("execution"),
            CompetenceDimensionState(
                "diagnosis",
                DimensionStanding.INSUFFICIENT,
                basis_evaluation_ids=(UNRESOLVED_EVAL_ID,),
                rationale="This dimension exposes the unresolved evaluation.",
                conflict_status=DimensionConflictStatus.UNRESOLVED,
            ),
        ),
    )
    with pytest.raises(InvalidStateSet, match="elsewhere in the same state basis"):
        PersonalCapabilityStateSet(SUBJECT, (state,)).validate_against_epistemics(
            records(include_contradicted=False, include_unresolved=True)
        )


def test_same_nonconflicting_basis_may_be_reused_across_dimensions() -> None:
    state = _state(
        "state_shared_basis",
        (
            _supported_dimension("execution"),
            _supported_dimension("explanation"),
        ),
    )
    PersonalCapabilityStateSet(SUBJECT, (state,)).validate_against_epistemics(
        records(include_contradicted=False)
    )


def test_alternative_state_records_do_not_cross_contaminate_conflict() -> None:
    supported_state = _state(
        "state_alternative_supported",
        (_supported_dimension("execution"),),
    )
    contradicted_state = _state(
        "state_alternative_contradicted",
        (
            CompetenceDimensionState(
                "execution",
                DimensionStanding.INSUFFICIENT,
                basis_evaluation_ids=(CONTRADICT_EVAL_ID,),
                rationale="Alternative state uses only the contradicting evaluation.",
            ),
        ),
    )
    PersonalCapabilityStateSet(
        SUBJECT,
        (supported_state, contradicted_state),
    ).validate_against_epistemics(records())


def test_future_unselected_conflict_does_not_rewrite_historical_state() -> None:
    historical_as_of = T0
    later_contradiction = T0 + timedelta(minutes=10)
    historical_state = _state(
        "state_historical_before_conflict",
        (_supported_dimension("execution"),),
        as_of=historical_as_of,
    )
    PersonalCapabilityStateSet(
        SUBJECT,
        (historical_state,),
    ).validate_against_epistemics(
        records(contradicted_at=later_contradiction)
    )
