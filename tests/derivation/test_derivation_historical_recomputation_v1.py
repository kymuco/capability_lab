from datetime import datetime, timedelta, timezone

import pytest

from capability_lab.derivation import (
    ClaimDimensionBinding,
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
    DimensionStanding,
    PersonalCapabilityStateId,
    PersonalCapabilityStateSet,
)


T0 = datetime(2026, 8, 15, 10, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("subject_pr4_history")
CONCEPT = CapabilityConceptRef.parse("core:pr4_history@1")
CLAIM_ID = CapabilityClaimId("claim_pr4_history")
EVAL_ID = ClaimEvaluationId("eval_pr4_history")
ALT_EVAL_ID = ClaimEvaluationId("eval_pr4_history_alt")


def provenance(ref: str) -> ProvenanceTrail:
    return ProvenanceTrail((ProvenanceSource(ProvenanceSourceKind.ACTOR, ref),))


def frame() -> CompetenceFrame:
    return CompetenceFrame(
        CompetenceFrameId.parse("core:pr4_history_frame"),
        1,
        "History frame",
        "Historical recomputation boundary frame.",
        (
            CompetenceDimensionDefinition(
                "execution", "Execution", "Bounded execution dimension."
            ),
        ),
    )


def evidence(evidence_id: str) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=EvidenceId(evidence_id),
        subject_ref=SUBJECT,
        kind=EvidenceKind.PROJECT,
        summary=f"Historical evidence {evidence_id}.",
        context=EvidenceContext("Historical recomputation context."),
        observed_at=T0 - timedelta(minutes=40),
        recorded_at=T0 - timedelta(minutes=39),
        provenance=provenance(f"actor_{evidence_id}"),
    )


def claim() -> CapabilityClaim:
    return CapabilityClaim(
        claim_id=CLAIM_ID,
        subject_ref=SUBJECT,
        concept_ref=CONCEPT,
        statement="Can perform the bounded historical capability.",
        scope=ClaimScope("Bounded historical scope."),
        created_at=T0 - timedelta(minutes=30),
        provenance=provenance("actor_claim_history"),
    )


def evaluation(
    evaluation_id: ClaimEvaluationId,
    conclusion: EvaluationConclusion,
    evidence_id: str,
) -> ClaimEvaluation:
    bearing = (
        EvidenceBearing.SUPPORTS
        if conclusion is EvaluationConclusion.SUPPORTED
        else EvidenceBearing.CONTRADICTS
    )
    return ClaimEvaluation(
        evaluation_id=evaluation_id,
        claim_id=CLAIM_ID,
        policy_ref=EvaluationPolicyRef.parse("core:pr4_history_eval@1"),
        evaluator_ref=EvaluatorRef(EvaluatorKind.RULE, f"reviewer_{evaluation_id}"),
        evaluated_at=T0 - timedelta(minutes=10),
        evidence_assessments=(
            EvidenceAssessment(
                EvidenceId(evidence_id),
                bearing,
                EvidenceReliability.HIGH,
                "Historical coverage note.",
                "Historical evaluation rationale.",
            ),
        ),
        coverage=CoverageAssessment(
            CoverageStatus.SUFFICIENT_FOR_CLAIM,
            "Historical coverage.",
        ),
        conflict_status=ConflictStatus.NONE,
        conclusion=conclusion,
        rationale="Historical evaluation.",
    )


def records(*evaluations: ClaimEvaluation) -> EpistemicRecordSet:
    return EpistemicRecordSet(
        evidence_records=(
            evidence("ev_pr4_history"),
            evidence("ev_pr4_history_alt"),
        ),
        claims=(claim(),),
        evaluations=evaluations,
    )


def request(
    selected: tuple[ClaimEvaluationId, ...],
    *,
    state_id: str = "state_pr4_history",
    as_of=T0,
) -> DeterministicStateDerivationRequest:
    return DeterministicStateDerivationRequest(
        state_id=PersonalCapabilityStateId(state_id),
        subject_ref=SUBJECT,
        concept_ref=CONCEPT,
        frame_ref=frame().ref,
        as_of=as_of,
        derived_at=as_of,
        selected_evaluation_ids=selected,
        claim_dimension_bindings=(
            ClaimDimensionBinding(CLAIM_ID, ("execution",)),
        ),
    )


def test_exact_snapshot_and_exact_request_reproduce_identical_state() -> None:
    snapshot = records(
        evaluation(EVAL_ID, EvaluationConclusion.SUPPORTED, "ev_pr4_history")
    )
    derivation_request = request((EVAL_ID,))

    first = derive_supported_state_v1(
        records=snapshot, frame=frame(), request=derivation_request
    )
    second = derive_supported_state_v1(
        records=snapshot, frame=frame(), request=derivation_request
    )

    assert first == second
    assert PersonalCapabilityStateSet(SUBJECT, (first,)).to_json() == (
        PersonalCapabilityStateSet(SUBJECT, (second,)).to_json()
    )


def test_historical_reconstruction_requires_selected_evaluation_to_remain_available() -> None:
    with pytest.raises(StateDerivationError, match="selected evaluation does not exist"):
        derive_supported_state_v1(
            records=records(),
            frame=frame(),
            request=request((EVAL_ID,)),
        )


def test_same_state_id_with_changed_effective_request_is_not_same_historical_record() -> None:
    snapshot = records(
        evaluation(EVAL_ID, EvaluationConclusion.SUPPORTED, "ev_pr4_history"),
        evaluation(
            ALT_EVAL_ID,
            EvaluationConclusion.CONTRADICTED,
            "ev_pr4_history_alt",
        ),
    )
    supported = derive_supported_state_v1(
        records=snapshot,
        frame=frame(),
        request=request((EVAL_ID,)),
    )
    contradicted = derive_supported_state_v1(
        records=snapshot,
        frame=frame(),
        request=request((ALT_EVAL_ID,)),
    )

    assert supported.state_id == contradicted.state_id
    assert supported != contradicted
    assert supported.dimensions[0].standing is DimensionStanding.SUPPORTED
    assert contradicted.dimensions[0].standing is DimensionStanding.INSUFFICIENT


def test_same_opaque_evaluation_id_with_changed_material_is_not_same_exact_input() -> None:
    supported_snapshot = records(
        evaluation(EVAL_ID, EvaluationConclusion.SUPPORTED, "ev_pr4_history")
    )
    contradicted_snapshot = records(
        evaluation(
            EVAL_ID,
            EvaluationConclusion.CONTRADICTED,
            "ev_pr4_history_alt",
        )
    )
    derivation_request = request((EVAL_ID,))

    supported = derive_supported_state_v1(
        records=supported_snapshot,
        frame=frame(),
        request=derivation_request,
    )
    contradicted = derive_supported_state_v1(
        records=contradicted_snapshot,
        frame=frame(),
        request=derivation_request,
    )

    assert supported != contradicted
    assert supported.dimensions[0].standing is DimensionStanding.SUPPORTED
    assert contradicted.dimensions[0].standing is DimensionStanding.INSUFFICIENT
