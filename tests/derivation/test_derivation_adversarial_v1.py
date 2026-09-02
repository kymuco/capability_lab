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
    DimensionConflictStatus,
    DimensionStanding,
    PersonalCapabilityStateId,
    PersonalCapabilityStateSet,
)


T0 = datetime(2026, 8, 15, 9, 0, tzinfo=timezone.utc)
SUBJECT_A = CapabilitySubjectRef("subject_pr4_adversarial_a")
SUBJECT_B = CapabilitySubjectRef("subject_pr4_adversarial_b")
CONCEPT_A = CapabilityConceptRef.parse("core:pr4_adversarial@1")
CONCEPT_B = CapabilityConceptRef.parse("core:pr4_adversarial_other@1")
CLAIM_A = CapabilityClaimId("claim_pr4_adversarial_a")
CLAIM_B = CapabilityClaimId("claim_pr4_adversarial_b")
CLAIM_C = CapabilityClaimId("claim_pr4_adversarial_c")
EVAL_MAIN = ClaimEvaluationId("eval_pr4_adversarial_main")
EVAL_SECOND = ClaimEvaluationId("eval_pr4_adversarial_second")
EVAL_FOREIGN = ClaimEvaluationId("eval_pr4_adversarial_foreign")
EVAL_OTHER_CONCEPT = ClaimEvaluationId("eval_pr4_adversarial_other_concept")
EVAL_OTHER_CLAIM = ClaimEvaluationId("eval_pr4_adversarial_other_claim")


def provenance(actor: str) -> ProvenanceTrail:
    return ProvenanceTrail(
        (ProvenanceSource(ProvenanceSourceKind.ACTOR, actor),)
    )


def frame() -> CompetenceFrame:
    return CompetenceFrame(
        CompetenceFrameId.parse("core:pr4_adversarial_frame"),
        1,
        "PR4 adversarial frame",
        "Adversarial deterministic derivation frame.",
        (
            CompetenceDimensionDefinition(
                "execution", "Execution", "Bounded execution dimension."
            ),
            CompetenceDimensionDefinition(
                "diagnosis", "Diagnosis", "Bounded diagnosis dimension."
            ),
        ),
    )


def evidence(evidence_id: str, subject: CapabilitySubjectRef) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=EvidenceId(evidence_id),
        subject_ref=subject,
        kind=EvidenceKind.PROJECT,
        summary=f"Adversarial evidence {evidence_id}.",
        context=EvidenceContext("Bounded adversarial context."),
        observed_at=T0 - timedelta(minutes=40),
        recorded_at=T0 - timedelta(minutes=39),
        provenance=provenance(f"actor_{evidence_id}"),
    )


def claim(
    claim_id: CapabilityClaimId,
    subject: CapabilitySubjectRef,
    concept: CapabilityConceptRef,
) -> CapabilityClaim:
    return CapabilityClaim(
        claim_id=claim_id,
        subject_ref=subject,
        concept_ref=concept,
        statement=f"Bounded proposition {claim_id}.",
        scope=ClaimScope("Bounded adversarial scope."),
        created_at=T0 - timedelta(minutes=30),
        provenance=provenance(f"actor_{claim_id}"),
    )


def evaluation(
    *,
    evaluation_id: ClaimEvaluationId,
    claim_id: CapabilityClaimId,
    evidence_id: str,
    conclusion: EvaluationConclusion,
    evaluator_kind: EvaluatorKind = EvaluatorKind.HUMAN,
    policy_ref: str = "core:pr4_adversarial_policy@1",
    reliability: EvidenceReliability = EvidenceReliability.HIGH,
    coverage: CoverageStatus = CoverageStatus.SUFFICIENT_FOR_CLAIM,
) -> ClaimEvaluation:
    if conclusion is EvaluationConclusion.CONTRADICTED:
        bearing = EvidenceBearing.CONTRADICTS
    else:
        bearing = EvidenceBearing.SUPPORTS
    return ClaimEvaluation(
        evaluation_id=evaluation_id,
        claim_id=claim_id,
        policy_ref=EvaluationPolicyRef.parse(policy_ref),
        evaluator_ref=EvaluatorRef(
            evaluator_kind,
            f"reviewer_{evaluation_id}",
        ),
        evaluated_at=T0 - timedelta(minutes=10),
        evidence_assessments=(
            EvidenceAssessment(
                EvidenceId(evidence_id),
                bearing,
                reliability,
                "Adversarial coverage note.",
                "Adversarial assessment rationale.",
            ),
        ),
        coverage=CoverageAssessment(
            coverage,
            "Adversarial coverage assessment.",
        ),
        conflict_status=ConflictStatus.NONE,
        conclusion=conclusion,
        rationale="Adversarial evaluation rationale.",
    )


def records(
    *,
    evidence_records,
    claims,
    evaluations,
) -> EpistemicRecordSet:
    return EpistemicRecordSet(
        evidence_records=tuple(evidence_records),
        claims=tuple(claims),
        evaluations=tuple(evaluations),
    )


def request(selected, bindings) -> DeterministicStateDerivationRequest:
    return DeterministicStateDerivationRequest(
        state_id=PersonalCapabilityStateId("state_pr4_adversarial"),
        subject_ref=SUBJECT_A,
        concept_ref=CONCEPT_A,
        frame_ref=frame().ref,
        as_of=T0,
        derived_at=T0,
        selected_evaluation_ids=tuple(selected),
        claim_dimension_bindings=tuple(bindings),
    )


def binding(claim_id: CapabilityClaimId, *keys: str) -> ClaimDimensionBinding:
    return ClaimDimensionBinding(claim_id, tuple(keys))


def dimension(state, key: str):
    return next(item for item in state.dimensions if item.dimension_key == key)


def derive(single_evaluation: ClaimEvaluation):
    snapshot = records(
        evidence_records=(evidence("ev_adv_main", SUBJECT_A),),
        claims=(claim(CLAIM_A, SUBJECT_A, CONCEPT_A),),
        evaluations=(single_evaluation,),
    )
    return derive_supported_state_v1(
        records=snapshot,
        frame=frame(),
        request=request(
            (EVAL_MAIN,),
            (binding(CLAIM_A, "execution"),),
        ),
    )


def test_selected_conclusion_not_evaluator_policy_reliability_or_coverage_controls_state() -> None:
    human_high = evaluation(
        evaluation_id=EVAL_MAIN,
        claim_id=CLAIM_A,
        evidence_id="ev_adv_main",
        conclusion=EvaluationConclusion.SUPPORTED,
        evaluator_kind=EvaluatorKind.HUMAN,
        policy_ref="core:pr4_adversarial_policy@1",
        reliability=EvidenceReliability.HIGH,
        coverage=CoverageStatus.SUFFICIENT_FOR_CLAIM,
    )
    model_low_partial = evaluation(
        evaluation_id=EVAL_MAIN,
        claim_id=CLAIM_A,
        evidence_id="ev_adv_main",
        conclusion=EvaluationConclusion.SUPPORTED,
        evaluator_kind=EvaluatorKind.MODEL,
        policy_ref="research:alternative_policy@7",
        reliability=EvidenceReliability.LOW,
        coverage=CoverageStatus.PARTIAL,
    )

    first = derive(human_high)
    second = derive(model_low_partial)

    assert first == second
    assert PersonalCapabilityStateSet(SUBJECT_A, (first,)).to_json() == (
        PersonalCapabilityStateSet(SUBJECT_A, (second,)).to_json()
    )
    assert dimension(first, "execution").standing is DimensionStanding.SUPPORTED


def test_unselected_foreign_subject_records_are_inert() -> None:
    selected = evaluation(
        evaluation_id=EVAL_MAIN,
        claim_id=CLAIM_A,
        evidence_id="ev_adv_main",
        conclusion=EvaluationConclusion.SUPPORTED,
    )
    foreign = evaluation(
        evaluation_id=EVAL_FOREIGN,
        claim_id=CLAIM_B,
        evidence_id="ev_adv_foreign",
        conclusion=EvaluationConclusion.CONTRADICTED,
        evaluator_kind=EvaluatorKind.MODEL,
    )

    base_records = records(
        evidence_records=(evidence("ev_adv_main", SUBJECT_A),),
        claims=(claim(CLAIM_A, SUBJECT_A, CONCEPT_A),),
        evaluations=(selected,),
    )
    expanded_records = records(
        evidence_records=(
            evidence("ev_adv_main", SUBJECT_A),
            evidence("ev_adv_foreign", SUBJECT_B),
        ),
        claims=(
            claim(CLAIM_A, SUBJECT_A, CONCEPT_A),
            claim(CLAIM_B, SUBJECT_B, CONCEPT_A),
        ),
        evaluations=(selected, foreign),
    )
    derive_request = request(
        (EVAL_MAIN,),
        (binding(CLAIM_A, "execution"),),
    )

    base = derive_supported_state_v1(
        records=base_records,
        frame=frame(),
        request=derive_request,
    )
    expanded = derive_supported_state_v1(
        records=expanded_records,
        frame=frame(),
        request=derive_request,
    )
    assert base == expanded


def test_selected_foreign_subject_evaluation_is_rejected() -> None:
    foreign = evaluation(
        evaluation_id=EVAL_FOREIGN,
        claim_id=CLAIM_B,
        evidence_id="ev_adv_foreign",
        conclusion=EvaluationConclusion.SUPPORTED,
    )
    snapshot = records(
        evidence_records=(evidence("ev_adv_foreign", SUBJECT_B),),
        claims=(claim(CLAIM_B, SUBJECT_B, CONCEPT_A),),
        evaluations=(foreign,),
    )
    with pytest.raises(StateDerivationError, match="different subject"):
        derive_supported_state_v1(
            records=snapshot,
            frame=frame(),
            request=request(
                (EVAL_FOREIGN,),
                (binding(CLAIM_B, "execution"),),
            ),
        )


def test_selected_other_concept_evaluation_is_rejected() -> None:
    other_concept = evaluation(
        evaluation_id=EVAL_OTHER_CONCEPT,
        claim_id=CLAIM_C,
        evidence_id="ev_adv_other_concept",
        conclusion=EvaluationConclusion.SUPPORTED,
    )
    snapshot = records(
        evidence_records=(evidence("ev_adv_other_concept", SUBJECT_A),),
        claims=(claim(CLAIM_C, SUBJECT_A, CONCEPT_B),),
        evaluations=(other_concept,),
    )
    with pytest.raises(StateDerivationError, match="different capability concept revision"):
        derive_supported_state_v1(
            records=snapshot,
            frame=frame(),
            request=request(
                (EVAL_OTHER_CONCEPT,),
                (binding(CLAIM_C, "execution"),),
            ),
        )


def test_supported_plus_insufficient_is_not_directional_conflict_or_negative_vote() -> None:
    supported = evaluation(
        evaluation_id=EVAL_MAIN,
        claim_id=CLAIM_A,
        evidence_id="ev_adv_main",
        conclusion=EvaluationConclusion.SUPPORTED,
    )
    insufficient = evaluation(
        evaluation_id=EVAL_SECOND,
        claim_id=CLAIM_A,
        evidence_id="ev_adv_second",
        conclusion=EvaluationConclusion.INSUFFICIENT,
        coverage=CoverageStatus.PARTIAL,
    )
    snapshot = records(
        evidence_records=(
            evidence("ev_adv_main", SUBJECT_A),
            evidence("ev_adv_second", SUBJECT_A),
        ),
        claims=(claim(CLAIM_A, SUBJECT_A, CONCEPT_A),),
        evaluations=(supported, insufficient),
    )
    state = derive_supported_state_v1(
        records=snapshot,
        frame=frame(),
        request=request(
            (EVAL_MAIN, EVAL_SECOND),
            (binding(CLAIM_A, "execution"),),
        ),
    )
    execution = dimension(state, "execution")
    assert execution.standing is DimensionStanding.SUPPORTED
    assert execution.conflict_status is DimensionConflictStatus.NONE
    assert execution.supported_claim_ids == (CLAIM_A,)
    assert execution.basis_evaluation_ids == tuple(
        sorted((EVAL_MAIN, EVAL_SECOND))
    )


def test_multiple_supported_evaluations_do_not_duplicate_supported_claim_content() -> None:
    first = evaluation(
        evaluation_id=EVAL_MAIN,
        claim_id=CLAIM_A,
        evidence_id="ev_adv_main",
        conclusion=EvaluationConclusion.SUPPORTED,
    )
    second = evaluation(
        evaluation_id=EVAL_SECOND,
        claim_id=CLAIM_A,
        evidence_id="ev_adv_second",
        conclusion=EvaluationConclusion.SUPPORTED,
        evaluator_kind=EvaluatorKind.MODEL,
    )
    snapshot = records(
        evidence_records=(
            evidence("ev_adv_main", SUBJECT_A),
            evidence("ev_adv_second", SUBJECT_A),
        ),
        claims=(claim(CLAIM_A, SUBJECT_A, CONCEPT_A),),
        evaluations=(first, second),
    )
    state = derive_supported_state_v1(
        records=snapshot,
        frame=frame(),
        request=request(
            (EVAL_MAIN, EVAL_SECOND),
            (binding(CLAIM_A, "execution"),),
        ),
    )
    execution = dimension(state, "execution")
    assert execution.supported_claim_ids == (CLAIM_A,)
    assert execution.basis_evaluation_ids == tuple(
        sorted((EVAL_MAIN, EVAL_SECOND))
    )
    assert execution.standing is DimensionStanding.SUPPORTED


def test_opposite_directional_conclusions_on_different_claims_do_not_invent_same_claim_conflict() -> None:
    supported = evaluation(
        evaluation_id=EVAL_MAIN,
        claim_id=CLAIM_A,
        evidence_id="ev_adv_main",
        conclusion=EvaluationConclusion.SUPPORTED,
    )
    contradicted_other_claim = evaluation(
        evaluation_id=EVAL_OTHER_CLAIM,
        claim_id=CLAIM_C,
        evidence_id="ev_adv_other_claim",
        conclusion=EvaluationConclusion.CONTRADICTED,
    )
    snapshot = records(
        evidence_records=(
            evidence("ev_adv_main", SUBJECT_A),
            evidence("ev_adv_other_claim", SUBJECT_A),
        ),
        claims=(
            claim(CLAIM_A, SUBJECT_A, CONCEPT_A),
            claim(CLAIM_C, SUBJECT_A, CONCEPT_A),
        ),
        evaluations=(supported, contradicted_other_claim),
    )
    state = derive_supported_state_v1(
        records=snapshot,
        frame=frame(),
        request=request(
            (EVAL_MAIN, EVAL_OTHER_CLAIM),
            (
                binding(CLAIM_A, "execution"),
                binding(CLAIM_C, "execution"),
            ),
        ),
    )
    execution = dimension(state, "execution")
    assert execution.standing is DimensionStanding.SUPPORTED
    assert execution.conflict_status is DimensionConflictStatus.NONE
    assert execution.supported_claim_ids == (CLAIM_A,)
    assert execution.basis_evaluation_ids == tuple(
        sorted((EVAL_MAIN, EVAL_OTHER_CLAIM))
    )
