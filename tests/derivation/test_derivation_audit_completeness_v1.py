from datetime import datetime, timedelta, timezone

from capability_lab.derivation import (
    ClaimDimensionBinding,
    DeterministicStateDerivationRequest,
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
    PersonalCapabilityStateId,
)


T0 = datetime(2026, 8, 15, 9, 30, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("subject_pr4_audit")
CONCEPT = CapabilityConceptRef.parse("core:pr4_audit@1")
CLAIM_A = CapabilityClaimId("claim_pr4_audit_a")
CLAIM_B = CapabilityClaimId("claim_pr4_audit_b")
EVAL_A1 = ClaimEvaluationId("eval_pr4_audit_a1")
EVAL_A2 = ClaimEvaluationId("eval_pr4_audit_a2")
EVAL_B1 = ClaimEvaluationId("eval_pr4_audit_b1")


def provenance(ref: str) -> ProvenanceTrail:
    return ProvenanceTrail(
        (ProvenanceSource(ProvenanceSourceKind.ACTOR, ref),)
    )


def evidence(evidence_id: str) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=EvidenceId(evidence_id),
        subject_ref=SUBJECT,
        kind=EvidenceKind.PROJECT,
        summary=f"Audit evidence {evidence_id}.",
        context=EvidenceContext("Audit context."),
        observed_at=T0 - timedelta(minutes=30),
        recorded_at=T0 - timedelta(minutes=29),
        provenance=provenance(f"actor_{evidence_id}"),
    )


def claim(claim_id: CapabilityClaimId) -> CapabilityClaim:
    return CapabilityClaim(
        claim_id=claim_id,
        subject_ref=SUBJECT,
        concept_ref=CONCEPT,
        statement=f"Audit proposition {claim_id}.",
        scope=ClaimScope("Audit scope."),
        created_at=T0 - timedelta(minutes=20),
        provenance=provenance(f"actor_{claim_id}"),
    )


def evaluation(
    evaluation_id: ClaimEvaluationId,
    claim_id: CapabilityClaimId,
    evidence_id: str,
    conclusion: EvaluationConclusion,
) -> ClaimEvaluation:
    bearing = (
        EvidenceBearing.SUPPORTS
        if conclusion is EvaluationConclusion.SUPPORTED
        else EvidenceBearing.CONTRADICTS
    )
    return ClaimEvaluation(
        evaluation_id=evaluation_id,
        claim_id=claim_id,
        policy_ref=EvaluationPolicyRef.parse("core:pr4_audit_policy@1"),
        evaluator_ref=EvaluatorRef(EvaluatorKind.RULE, f"reviewer_{evaluation_id}"),
        evaluated_at=T0 - timedelta(minutes=10),
        evidence_assessments=(
            EvidenceAssessment(
                EvidenceId(evidence_id),
                bearing,
                EvidenceReliability.HIGH,
                "Audit coverage note.",
                "Audit rationale.",
            ),
        ),
        coverage=CoverageAssessment(
            CoverageStatus.SUFFICIENT_FOR_CLAIM,
            "Audit coverage.",
        ),
        conflict_status=ConflictStatus.NONE,
        conclusion=conclusion,
        rationale="Audit evaluation.",
    )


def test_output_basis_exactly_preserves_effective_selected_set_and_bindings() -> None:
    frame = CompetenceFrame(
        CompetenceFrameId.parse("core:pr4_audit_frame"),
        1,
        "Audit frame",
        "Audit-completeness frame.",
        (
            CompetenceDimensionDefinition(
                "execution", "Execution", "Execution dimension."
            ),
            CompetenceDimensionDefinition(
                "diagnosis", "Diagnosis", "Diagnosis dimension."
            ),
            CompetenceDimensionDefinition(
                "explanation", "Explanation", "Explanation dimension."
            ),
        ),
    )
    records = EpistemicRecordSet(
        evidence_records=(
            evidence("ev_pr4_audit_a1"),
            evidence("ev_pr4_audit_a2"),
            evidence("ev_pr4_audit_b1"),
        ),
        claims=(claim(CLAIM_A), claim(CLAIM_B)),
        evaluations=(
            evaluation(
                EVAL_A1,
                CLAIM_A,
                "ev_pr4_audit_a1",
                EvaluationConclusion.SUPPORTED,
            ),
            evaluation(
                EVAL_A2,
                CLAIM_A,
                "ev_pr4_audit_a2",
                EvaluationConclusion.CONTRADICTED,
            ),
            evaluation(
                EVAL_B1,
                CLAIM_B,
                "ev_pr4_audit_b1",
                EvaluationConclusion.SUPPORTED,
            ),
        ),
    )
    bindings = (
        ClaimDimensionBinding(CLAIM_A, ("execution", "diagnosis")),
        ClaimDimensionBinding(CLAIM_B, ("explanation",)),
    )
    request = DeterministicStateDerivationRequest(
        state_id=PersonalCapabilityStateId("state_pr4_audit"),
        subject_ref=SUBJECT,
        concept_ref=CONCEPT,
        frame_ref=frame.ref,
        as_of=T0,
        derived_at=T0,
        selected_evaluation_ids=(EVAL_B1, EVAL_A2, EVAL_A1),
        claim_dimension_bindings=bindings,
    )

    state = derive_supported_state_v1(
        records=records,
        frame=frame,
        request=request,
    )

    output_selected = {
        evaluation_id
        for dimension in state.dimensions
        for evaluation_id in dimension.basis_evaluation_ids
    }
    assert output_selected == set(request.selected_evaluation_ids)

    evaluations_by_id = {
        evaluation.evaluation_id: evaluation for evaluation in records.evaluations
    }
    reconstructed_dimensions_by_claim = {}
    for dimension in state.dimensions:
        for evaluation_id in dimension.basis_evaluation_ids:
            claim_id = evaluations_by_id[evaluation_id].claim_id
            reconstructed_dimensions_by_claim.setdefault(claim_id, set()).add(
                dimension.dimension_key
            )

    expected_dimensions_by_claim = {
        binding.claim_id: set(binding.dimension_keys)
        for binding in request.claim_dimension_bindings
    }
    assert reconstructed_dimensions_by_claim == expected_dimensions_by_claim
