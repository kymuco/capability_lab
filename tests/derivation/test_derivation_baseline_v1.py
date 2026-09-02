from datetime import datetime, timedelta, timezone

import pytest

from capability_lab.derivation import (
    ClaimDimensionBinding,
    DETERMINISTIC_SUPPORTED_STATE_DERIVER_V1,
    DETERMINISTIC_SUPPORTED_STATE_POLICY_V1,
    DeterministicStateDerivationRequest,
    StateDerivationError,
    derive_supported_state_v1,
)
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
    CompetenceDimensionDefinition,
    CompetenceFrame,
    CompetenceFrameId,
    CompetenceFrameRef,
    DimensionConflictStatus,
    DimensionStanding,
    PersonalCapabilityStateId,
    PersonalCapabilityStateSet,
    StateDeriverKind,
)


T0 = datetime(2026, 8, 15, 8, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("subject_pr4")
CONCEPT = CapabilityConceptRef.parse("core:pr4_capability@1")
CLAIM_ID = CapabilityClaimId("claim_pr4")
SUPPORT_ID = ClaimEvaluationId("eval_pr4_support")
CONTRADICT_ID = ClaimEvaluationId("eval_pr4_contradict")
UNRESOLVED_ID = ClaimEvaluationId("eval_pr4_unresolved")
RESOLVED_ID = ClaimEvaluationId("eval_pr4_resolved")
FUTURE_ID = ClaimEvaluationId("eval_pr4_future")
MODEL_ID = ClaimEvaluationId("eval_pr4_model")


def provenance() -> ProvenanceTrail:
    return ProvenanceTrail(
        (ProvenanceSource(ProvenanceSourceKind.ACTOR, "pr4_reviewer"),)
    )


def frame(*, reverse: bool = False) -> CompetenceFrame:
    dimensions = [
        CompetenceDimensionDefinition(
            "execution", "Execution", "Bounded execution competence."
        ),
        CompetenceDimensionDefinition(
            "diagnosis", "Diagnosis", "Bounded diagnosis competence."
        ),
        CompetenceDimensionDefinition(
            "independence", "Independence", "Bounded independence competence."
        ),
    ]
    if reverse:
        dimensions.reverse()
    return CompetenceFrame(
        CompetenceFrameId.parse("core:pr4_frame"),
        1,
        "PR4 frame",
        "Deterministic derivation test frame.",
        tuple(dimensions),
    )


def evidence(evidence_id: str) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=EvidenceId(evidence_id),
        subject_ref=SUBJECT,
        kind=EvidenceKind.PROJECT,
        summary=f"PR4 evidence {evidence_id}.",
        context=EvidenceContext("Bounded PR4 context."),
        observed_at=T0 - timedelta(minutes=40),
        recorded_at=T0 - timedelta(minutes=39),
        provenance=provenance(),
    )


def claim() -> CapabilityClaim:
    return CapabilityClaim(
        claim_id=CLAIM_ID,
        subject_ref=SUBJECT,
        concept_ref=CONCEPT,
        statement="Can perform the bounded PR4 capability.",
        scope=ClaimScope("Bounded PR4 scope."),
        created_at=T0 - timedelta(minutes=30),
        provenance=provenance(),
    )


def assessment(evidence_id: str, bearing: EvidenceBearing) -> EvidenceAssessment:
    return EvidenceAssessment(
        EvidenceId(evidence_id),
        bearing,
        EvidenceReliability.HIGH,
        "Bounded coverage.",
        "The evidence has the declared bearing.",
    )


def support_eval(
    evaluation_id: ClaimEvaluationId = SUPPORT_ID,
    *,
    evaluator_kind: EvaluatorKind = EvaluatorKind.HUMAN,
    evaluated_at=T0 - timedelta(minutes=10),
) -> ClaimEvaluation:
    return ClaimEvaluation(
        evaluation_id=evaluation_id,
        claim_id=CLAIM_ID,
        policy_ref=EvaluationPolicyRef.parse("core:pr4_support_policy@1"),
        evaluator_ref=EvaluatorRef(evaluator_kind, f"reviewer_{evaluation_id}"),
        evaluated_at=evaluated_at,
        evidence_assessments=(
            assessment("ev_pr4_support", EvidenceBearing.SUPPORTS),
        ),
        coverage=CoverageAssessment(
            CoverageStatus.SUFFICIENT_FOR_CLAIM,
            "Sufficient bounded coverage.",
        ),
        conflict_status=ConflictStatus.NONE,
        conclusion=EvaluationConclusion.SUPPORTED,
        rationale="The claim is supported under this evaluation policy.",
    )


def contradict_eval(
    evaluation_id: ClaimEvaluationId = CONTRADICT_ID,
    *,
    evaluated_at=T0 - timedelta(minutes=9),
) -> ClaimEvaluation:
    return ClaimEvaluation(
        evaluation_id=evaluation_id,
        claim_id=CLAIM_ID,
        policy_ref=EvaluationPolicyRef.parse("core:pr4_contradict_policy@1"),
        evaluator_ref=EvaluatorRef(EvaluatorKind.HUMAN, f"reviewer_{evaluation_id}"),
        evaluated_at=evaluated_at,
        evidence_assessments=(
            assessment("ev_pr4_contradict", EvidenceBearing.CONTRADICTS),
        ),
        coverage=CoverageAssessment(
            CoverageStatus.SUFFICIENT_FOR_CLAIM,
            "Sufficient bounded contradiction coverage.",
        ),
        conflict_status=ConflictStatus.NONE,
        conclusion=EvaluationConclusion.CONTRADICTED,
        rationale="The claim is contradicted under this evaluation policy.",
    )


def unresolved_eval() -> ClaimEvaluation:
    return ClaimEvaluation(
        evaluation_id=UNRESOLVED_ID,
        claim_id=CLAIM_ID,
        policy_ref=EvaluationPolicyRef.parse("core:pr4_unresolved_policy@1"),
        evaluator_ref=EvaluatorRef(EvaluatorKind.HUMAN, "reviewer_unresolved"),
        evaluated_at=T0 - timedelta(minutes=8),
        evidence_assessments=(
            assessment("ev_pr4_support", EvidenceBearing.SUPPORTS),
            assessment("ev_pr4_contradict", EvidenceBearing.CONTRADICTS),
        ),
        coverage=CoverageAssessment(
            CoverageStatus.PARTIAL,
            "Directional conflict remains unresolved.",
        ),
        conflict_status=ConflictStatus.UNRESOLVED,
        conclusion=EvaluationConclusion.INSUFFICIENT,
        rationale="The evaluation preserves unresolved conflict.",
    )


def resolved_eval() -> ClaimEvaluation:
    return ClaimEvaluation(
        evaluation_id=RESOLVED_ID,
        claim_id=CLAIM_ID,
        policy_ref=EvaluationPolicyRef.parse("core:pr4_resolved_policy@1"),
        evaluator_ref=EvaluatorRef(EvaluatorKind.HUMAN, "reviewer_resolved"),
        evaluated_at=T0 - timedelta(minutes=7),
        evidence_assessments=(
            assessment("ev_pr4_support", EvidenceBearing.SUPPORTS),
            assessment("ev_pr4_contradict", EvidenceBearing.CONTRADICTS),
        ),
        coverage=CoverageAssessment(
            CoverageStatus.SUFFICIENT_FOR_CLAIM,
            "The evaluation policy resolves its internal conflict.",
        ),
        conflict_status=ConflictStatus.RESOLVED_BY_POLICY,
        conclusion=EvaluationConclusion.SUPPORTED,
        rationale="Evaluation-level conflict is resolved by its own policy.",
    )


def records(*evaluations: ClaimEvaluation, reverse: bool = False) -> EpistemicRecordSet:
    items = list(evaluations)
    if reverse:
        items.reverse()
    return EpistemicRecordSet(
        evidence_records=(
            evidence("ev_pr4_support"),
            evidence("ev_pr4_contradict"),
            evidence("ev_pr4_extra"),
        ),
        claims=(claim(),),
        evaluations=tuple(items),
    )


def request(
    selected=(),
    bindings=(),
    *,
    frame_ref: CompetenceFrameRef | None = None,
    as_of=T0,
) -> DeterministicStateDerivationRequest:
    return DeterministicStateDerivationRequest(
        state_id=PersonalCapabilityStateId("state_pr4"),
        subject_ref=SUBJECT,
        concept_ref=CONCEPT,
        frame_ref=frame_ref or frame().ref,
        as_of=as_of,
        derived_at=as_of,
        selected_evaluation_ids=tuple(selected),
        claim_dimension_bindings=tuple(bindings),
    )


def binding(*keys: str) -> ClaimDimensionBinding:
    return ClaimDimensionBinding(CLAIM_ID, tuple(keys))


def dimension(state, key: str):
    return next(item for item in state.dimensions if item.dimension_key == key)


def test_empty_selection_derives_explicit_all_unknown_state() -> None:
    state = derive_supported_state_v1(
        records=records(),
        frame=frame(),
        request=request(),
    )
    assert all(item.standing is DimensionStanding.UNKNOWN for item in state.dimensions)
    assert all(item.conflict_status is DimensionConflictStatus.NONE for item in state.dimensions)
    assert all(not item.basis_evaluation_ids for item in state.dimensions)
    assert state.derivation_policy_ref == DETERMINISTIC_SUPPORTED_STATE_POLICY_V1
    assert state.deriver_ref == DETERMINISTIC_SUPPORTED_STATE_DERIVER_V1
    assert state.deriver_ref.kind is StateDeriverKind.RULE


def test_supported_evaluation_derives_scoped_supported_content() -> None:
    state = derive_supported_state_v1(
        records=records(support_eval()),
        frame=frame(),
        request=request((SUPPORT_ID,), (binding("execution"),)),
    )
    execution = dimension(state, "execution")
    assert execution.standing is DimensionStanding.SUPPORTED
    assert execution.supported_claim_ids == (CLAIM_ID,)
    assert execution.basis_evaluation_ids == (SUPPORT_ID,)
    assert execution.conflict_status is DimensionConflictStatus.NONE
    assert dimension(state, "diagnosis").standing is DimensionStanding.UNKNOWN


def test_contradicted_evaluation_does_not_become_low_or_supported_state() -> None:
    state = derive_supported_state_v1(
        records=records(contradict_eval()),
        frame=frame(),
        request=request((CONTRADICT_ID,), (binding("execution"),)),
    )
    execution = dimension(state, "execution")
    assert execution.standing is DimensionStanding.INSUFFICIENT
    assert execution.supported_claim_ids == ()
    assert execution.conflict_status is DimensionConflictStatus.NONE


def test_same_claim_support_and_contradiction_preserves_support_and_unresolved_conflict() -> None:
    state = derive_supported_state_v1(
        records=records(support_eval(), contradict_eval()),
        frame=frame(),
        request=request(
            (CONTRADICT_ID, SUPPORT_ID),
            (binding("execution", "diagnosis"),),
        ),
    )
    for key in ("execution", "diagnosis"):
        item = dimension(state, key)
        assert item.standing is DimensionStanding.SUPPORTED
        assert item.supported_claim_ids == (CLAIM_ID,)
        assert item.basis_evaluation_ids == tuple(sorted((SUPPORT_ID, CONTRADICT_ID)))
        assert item.conflict_status is DimensionConflictStatus.UNRESOLVED


def test_explicit_unresolved_evaluation_derives_insufficient_plus_unresolved() -> None:
    state = derive_supported_state_v1(
        records=records(unresolved_eval()),
        frame=frame(),
        request=request((UNRESOLVED_ID,), (binding("diagnosis"),)),
    )
    diagnosis = dimension(state, "diagnosis")
    assert diagnosis.standing is DimensionStanding.INSUFFICIENT
    assert diagnosis.supported_claim_ids == ()
    assert diagnosis.conflict_status is DimensionConflictStatus.UNRESOLVED


def test_evaluation_level_resolved_conflict_is_not_state_level_resolution() -> None:
    state = derive_supported_state_v1(
        records=records(resolved_eval()),
        frame=frame(),
        request=request((RESOLVED_ID,), (binding("execution"),)),
    )
    execution = dimension(state, "execution")
    assert execution.standing is DimensionStanding.SUPPORTED
    assert execution.conflict_status is DimensionConflictStatus.NONE
    assert all(
        item.conflict_status is not DimensionConflictStatus.RESOLVED_BY_POLICY
        for item in state.dimensions
    )


def test_same_claim_receives_same_complete_selected_basis_in_every_bound_dimension() -> None:
    state = derive_supported_state_v1(
        records=records(support_eval(), contradict_eval()),
        frame=frame(),
        request=request(
            (SUPPORT_ID, CONTRADICT_ID),
            (binding("execution", "independence"),),
        ),
    )
    assert dimension(state, "execution").basis_evaluation_ids == dimension(
        state, "independence"
    ).basis_evaluation_ids


def test_unselected_model_evaluation_and_extra_evidence_cannot_change_output() -> None:
    selected = support_eval()
    model_contradiction = contradict_eval(MODEL_ID)
    base = derive_supported_state_v1(
        records=records(selected),
        frame=frame(),
        request=request((SUPPORT_ID,), (binding("execution"),)),
    )
    expanded = derive_supported_state_v1(
        records=records(selected, model_contradiction),
        frame=frame(),
        request=request((SUPPORT_ID,), (binding("execution"),)),
    )
    assert base == expanded
    assert PersonalCapabilityStateSet(SUBJECT, (base,)).to_json() == PersonalCapabilityStateSet(
        SUBJECT, (expanded,)
    ).to_json()


def test_input_order_does_not_change_state_or_canonical_json() -> None:
    first = derive_supported_state_v1(
        records=records(support_eval(), contradict_eval()),
        frame=frame(),
        request=request(
            (SUPPORT_ID, CONTRADICT_ID),
            (binding("diagnosis", "execution"),),
        ),
    )
    second = derive_supported_state_v1(
        records=records(support_eval(), contradict_eval(), reverse=True),
        frame=frame(reverse=True),
        request=request(
            (CONTRADICT_ID, SUPPORT_ID),
            (binding("execution", "diagnosis"),),
            frame_ref=frame(reverse=True).ref,
        ),
    )
    assert first == second
    assert PersonalCapabilityStateSet(SUBJECT, (first,)).to_json() == PersonalCapabilityStateSet(
        SUBJECT, (second,)
    ).to_json()


def test_selected_future_evaluation_is_rejected_but_unselected_future_is_harmless() -> None:
    future = support_eval(FUTURE_ID, evaluated_at=T0 + timedelta(minutes=5))
    with pytest.raises(StateDerivationError, match="after the request as_of"):
        derive_supported_state_v1(
            records=records(future),
            frame=frame(),
            request=request((FUTURE_ID,), (binding("execution"),)),
        )

    state = derive_supported_state_v1(
        records=records(support_eval(), future),
        frame=frame(),
        request=request((SUPPORT_ID,), (binding("execution"),)),
    )
    assert dimension(state, "execution").basis_evaluation_ids == (SUPPORT_ID,)


def test_selected_evaluation_claim_must_be_bound_and_bound_claim_must_be_selected() -> None:
    with pytest.raises(StateDerivationError, match="must have an explicit dimension binding"):
        derive_supported_state_v1(
            records=records(support_eval()),
            frame=frame(),
            request=request((SUPPORT_ID,), ()),
        )

    with pytest.raises(StateDerivationError, match="must have at least one selected evaluation"):
        derive_supported_state_v1(
            records=records(support_eval()),
            frame=frame(),
            request=request((), (binding("execution"),)),
        )


def test_exact_frame_and_dimension_bindings_are_enforced() -> None:
    with pytest.raises(StateDerivationError, match="exact frame"):
        derive_supported_state_v1(
            records=records(support_eval()),
            frame=frame(),
            request=request(
                (SUPPORT_ID,),
                (binding("execution"),),
                frame_ref=CompetenceFrameRef.parse("core:pr4_frame@2"),
            ),
        )

    with pytest.raises(StateDerivationError, match="absent from the exact frame"):
        derive_supported_state_v1(
            records=records(support_eval()),
            frame=frame(),
            request=request((SUPPORT_ID,), (binding("teaching"),)),
        )


def test_duplicate_selection_or_binding_is_rejected_before_derivation() -> None:
    with pytest.raises(StateDerivationError, match="duplicate selected evaluation"):
        request((SUPPORT_ID, SUPPORT_ID), (binding("execution"),))
    with pytest.raises(StateDerivationError, match="at most one claim-dimension binding"):
        request(
            (SUPPORT_ID,),
            (binding("execution"), binding("diagnosis")),
        )
