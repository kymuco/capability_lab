from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from capability_lab.epistemics import (
    CapabilityClaimId,
    CapabilitySubjectRef,
    ClaimEvaluationId,
    ConflictStatus,
    ContextFactor,
    ContextFactorKind,
    CoverageAssessment,
    CoverageStatus,
    EvaluationConclusion,
    EvaluatorKind,
    EvaluatorRef,
    EvidenceBearing,
    EvidenceId,
    EvidenceReliability,
    ProvenanceSource,
    ProvenanceSourceKind,
    ProvenanceTrail,
)
from capability_lab.pilots.civilization_bootstrap_01.evaluation_policy import (
    InvalidPilotEvaluationPolicy,
    PILOT_01_EXECUTION_CLAIM_KEY,
    PILOT_01_REASONING_CLAIM_KEY,
    build_civilization_bootstrap_pilot_01_evaluation_policy_v1,
)
from capability_lab.pilots.civilization_bootstrap_01.claim_evaluation import (
    InvalidPilotClaimEvaluation,
    PilotHumanSingleEvidenceEvaluationDecision,
    evaluate_reviewed_civilization_bootstrap_pilot_01_single_evidence_v1,
    instantiate_civilization_bootstrap_pilot_01_capability_claim_v1,
    validate_civilization_bootstrap_pilot_01_capability_claim_v1,
)
from capability_lab.pilots.civilization_bootstrap_01 import (
    REVIEWED_PILOT_CAPTURE_TO_EVIDENCE_POLICY_V1,
    InvalidPilotEvidenceMaterialization,
    PilotEvidenceMaterializationId,
    PilotEvidenceMaterializationReview,
    PilotEvidenceMaterializationReviewId,
    PilotEvidenceMaterializationReviewerKind,
    PilotEvidenceMaterializationReviewerRef,
    PilotEvidenceMaterializationVerdict,
    PilotReviewedMaterializationResolutionBinding,
    initialize_private_workspace,
    pilot_evidence_materialization_candidate_sha256,
    propose_pilot_capture_evidence_materialization_v1,
    record_text_capture,
    resolve_reviewed_pilot_evidence_materialization_with_receipt_v1,
)


T0 = datetime(2026, 1, 22, 12, 0, tzinfo=timezone.utc)


def _policy():
    return build_civilization_bootstrap_pilot_01_evaluation_policy_v1()


def _claim_provenance():
    return ProvenanceTrail(
        sources=(
            ProvenanceSource(
                ProvenanceSourceKind.SYSTEM,
                "pilot_01_claim_definition",
            ),
        ),
    )


def _claim(
    *,
    claim_key=PILOT_01_REASONING_CLAIM_KEY,
    subject_ref=CapabilitySubjectRef("subject_pr11_1"),
    created_minute=5,
):
    return instantiate_civilization_bootstrap_pilot_01_capability_claim_v1(
        claim_key=claim_key,
        subject_ref=subject_ref,
        claim_id=CapabilityClaimId(f"claim_{claim_key}"),
        created_at=T0 + timedelta(minutes=created_minute),
        provenance=_claim_provenance(),
        policy=_policy(),
    )


def _reviewer():
    return PilotEvidenceMaterializationReviewerRef(
        PilotEvidenceMaterializationReviewerKind.HUMAN,
        "reviewer_pr11_1_materialization",
    )


def _resolved(tmp_path, *, probe_id, suffix):
    root = tmp_path / f"workspace_{suffix}"
    initialize_private_workspace(
        root,
        session_id=f"session_{suffix}",
        subject_ref=CapabilitySubjectRef("subject_pr11_1"),
        created_at=T0,
    )
    record_text_capture(
        root,
        capture_id=f"capture_{suffix}",
        probe_id=probe_id,
        text_content=f"Synthetic reviewed evidence for {probe_id}.",
        captured_at=T0 + timedelta(minutes=1),
    )
    candidate = propose_pilot_capture_evidence_materialization_v1(
        root,
        capture_id=f"capture_{suffix}",
        materialization_id=PilotEvidenceMaterializationId(
            f"materialization_{suffix}"
        ),
        proposed_evidence_id=EvidenceId(f"evidence_{suffix}"),
        proposed_at=T0 + timedelta(minutes=2),
    )
    review = PilotEvidenceMaterializationReview(
        review_id=PilotEvidenceMaterializationReviewId(f"review_{suffix}"),
        materialization_id=candidate.materialization_id,
        candidate_sha256=pilot_evidence_materialization_candidate_sha256(
            candidate
        ),
        policy_ref=REVIEWED_PILOT_CAPTURE_TO_EVIDENCE_POLICY_V1,
        reviewer_ref=_reviewer(),
        verdict=PilotEvidenceMaterializationVerdict.MATERIALIZE,
        reviewed_at=T0 + timedelta(minutes=3),
        rationale="Explicit human materialization review.",
    )
    evidence, receipt = resolve_reviewed_pilot_evidence_materialization_with_receipt_v1(
        root,
        candidate=candidate,
        review=review,
        resolved_at=T0 + timedelta(minutes=4),
    )
    assert evidence is not None
    assert receipt is not None
    return (
        candidate,
        evidence,
        PilotReviewedMaterializationResolutionBinding(review, receipt),
    )


def _decision(
    *,
    claim,
    evidence,
    claim_key,
    bearing=EvidenceBearing.SUPPORTS,
    reliability=EvidenceReliability.MODERATE,
    coverage_status=CoverageStatus.PARTIAL,
    conclusion=EvaluationConclusion.INSUFFICIENT,
    evaluated_minute=6,
    evaluator_kind=EvaluatorKind.HUMAN,
):
    return PilotHumanSingleEvidenceEvaluationDecision(
        evaluation_id=ClaimEvaluationId(
            f"evaluation_{claim_key}_{evidence.evidence_id}"
        ),
        claim_key=claim_key,
        claim_id=claim.claim_id,
        evidence_id=evidence.evidence_id,
        policy_ref=_policy().policy_ref,
        evaluator_ref=EvaluatorRef(evaluator_kind, "human_reviewer_pr11_1"),
        evaluated_at=T0 + timedelta(minutes=evaluated_minute),
        bearing=bearing,
        reliability=reliability,
        coverage=CoverageAssessment(
            coverage_status,
            "Explicit human coverage judgment for this single evidence item.",
        ),
        conflict_status=ConflictStatus.NONE,
        conclusion=conclusion,
        coverage_note="Single-probe coverage note.",
        evidence_rationale="Explicit human evidence-bearing rationale.",
        evaluation_rationale="Explicit human claim-evaluation rationale.",
    )


def test_claim_instantiation_uses_exact_pr11_0_template_without_evidence_provenance():
    policy = _policy()
    claim = _claim()
    template = policy.claim(PILOT_01_REASONING_CLAIM_KEY)

    assert claim.concept_ref == template.concept_ref
    assert claim.statement == template.statement
    assert claim.scope == template.scope
    assert all(
        source.kind is not ProvenanceSourceKind.EVIDENCE_RECORD
        for source in claim.provenance.sources
    )
    validate_civilization_bootstrap_pilot_01_capability_claim_v1(
        claim,
        claim_key=PILOT_01_REASONING_CLAIM_KEY,
        policy=policy,
    )


def test_claim_validation_rejects_same_id_template_statement_rebinding():
    claim = _claim()
    changed = replace(claim, statement="Changed proposition under the same claim id.")
    with pytest.raises(
        InvalidPilotClaimEvaluation,
        match="claim statement does not match exact PR11.0 claim template",
    ):
        validate_civilization_bootstrap_pilot_01_capability_claim_v1(
            changed,
            claim_key=PILOT_01_REASONING_CLAIM_KEY,
            policy=_policy(),
        )


def test_claim_instantiation_rejects_non_exact_policy_revision():
    policy = _policy()
    changed = replace(
        policy,
        reliability_rule="Changed exact policy content under the same nominal ref.",
    )
    with pytest.raises(InvalidPilotEvaluationPolicy):
        instantiate_civilization_bootstrap_pilot_01_capability_claim_v1(
            claim_key=PILOT_01_REASONING_CLAIM_KEY,
            subject_ref=CapabilitySubjectRef("subject_pr11_1"),
            claim_id=CapabilityClaimId("claim_non_exact_policy"),
            created_at=T0 + timedelta(minutes=5),
            provenance=_claim_provenance(),
            policy=changed,
        )


def test_single_reasoning_evidence_preserves_support_bearing_but_claim_stays_insufficient(
    tmp_path,
):
    candidate, evidence, binding = _resolved(
        tmp_path,
        probe_id="conceptual_explanation",
        suffix="reasoning_support",
    )
    claim = _claim()
    decision = _decision(
        claim=claim,
        evidence=evidence,
        claim_key=PILOT_01_REASONING_CLAIM_KEY,
        bearing=EvidenceBearing.SUPPORTS,
        coverage_status=CoverageStatus.PARTIAL,
        conclusion=EvaluationConclusion.INSUFFICIENT,
    )

    evaluation = evaluate_reviewed_civilization_bootstrap_pilot_01_single_evidence_v1(
        claim_key=PILOT_01_REASONING_CLAIM_KEY,
        claim=claim,
        policy=_policy(),
        candidate=candidate,
        evidence=evidence,
        resolution_binding=binding,
        decision=decision,
    )

    assert evaluation.claim_id == claim.claim_id
    assert evaluation.policy_ref == _policy().policy_ref
    assert evaluation.evaluator_ref.kind is EvaluatorKind.HUMAN
    assert len(evaluation.evidence_assessments) == 1
    assert evaluation.evidence_assessments[0].bearing is EvidenceBearing.SUPPORTS
    assert evaluation.coverage.status is CoverageStatus.PARTIAL
    assert evaluation.conclusion is EvaluationConclusion.INSUFFICIENT


def test_single_reasoning_evidence_cannot_claim_sufficient_multi_probe_coverage(tmp_path):
    candidate, evidence, binding = _resolved(
        tmp_path,
        probe_id="calculation_work",
        suffix="reasoning_sufficient",
    )
    claim = _claim()
    decision = _decision(
        claim=claim,
        evidence=evidence,
        claim_key=PILOT_01_REASONING_CLAIM_KEY,
        coverage_status=CoverageStatus.SUFFICIENT_FOR_CLAIM,
        conclusion=EvaluationConclusion.SUPPORTED,
    )

    with pytest.raises(
        InvalidPilotClaimEvaluation,
        match="single-evidence evaluation cannot establish SUFFICIENT_FOR_CLAIM",
    ):
        evaluate_reviewed_civilization_bootstrap_pilot_01_single_evidence_v1(
            claim_key=PILOT_01_REASONING_CLAIM_KEY,
            claim=claim,
            policy=_policy(),
            candidate=candidate,
            evidence=evidence,
            resolution_binding=binding,
            decision=decision,
        )


def test_partial_single_evidence_cannot_emit_directional_claim_wide_conclusion(tmp_path):
    candidate, evidence, binding = _resolved(
        tmp_path,
        probe_id="diagnosis_reasoning",
        suffix="reasoning_directional",
    )
    claim = _claim()
    decision = _decision(
        claim=claim,
        evidence=evidence,
        claim_key=PILOT_01_REASONING_CLAIM_KEY,
        coverage_status=CoverageStatus.PARTIAL,
        conclusion=EvaluationConclusion.SUPPORTED,
    )

    with pytest.raises(
        InvalidPilotClaimEvaluation,
        match="claim-wide conclusion must remain INSUFFICIENT or ABSTAINED",
    ):
        evaluate_reviewed_civilization_bootstrap_pilot_01_single_evidence_v1(
            claim_key=PILOT_01_REASONING_CLAIM_KEY,
            claim=claim,
            policy=_policy(),
            candidate=candidate,
            evidence=evidence,
            resolution_binding=binding,
            decision=decision,
        )


def test_single_execution_artifact_can_reach_sufficient_supported_evaluation(tmp_path):
    candidate, evidence, binding = _resolved(
        tmp_path,
        probe_id="execution_artifact",
        suffix="execution_support",
    )
    claim = _claim(claim_key=PILOT_01_EXECUTION_CLAIM_KEY)
    decision = _decision(
        claim=claim,
        evidence=evidence,
        claim_key=PILOT_01_EXECUTION_CLAIM_KEY,
        bearing=EvidenceBearing.SUPPORTS,
        reliability=EvidenceReliability.HIGH,
        coverage_status=CoverageStatus.SUFFICIENT_FOR_CLAIM,
        conclusion=EvaluationConclusion.SUPPORTED,
    )

    evaluation = evaluate_reviewed_civilization_bootstrap_pilot_01_single_evidence_v1(
        claim_key=PILOT_01_EXECUTION_CLAIM_KEY,
        claim=claim,
        policy=_policy(),
        candidate=candidate,
        evidence=evidence,
        resolution_binding=binding,
        decision=decision,
    )

    assert evaluation.coverage.status is CoverageStatus.SUFFICIENT_FOR_CLAIM
    assert evaluation.conclusion is EvaluationConclusion.SUPPORTED
    assert evaluation.evidence_assessments[0].reliability is EvidenceReliability.HIGH


def test_evaluation_rejects_probe_bound_to_other_claim(tmp_path):
    candidate, evidence, binding = _resolved(
        tmp_path,
        probe_id="execution_artifact",
        suffix="probe_mismatch",
    )
    claim = _claim(claim_key=PILOT_01_REASONING_CLAIM_KEY)
    decision = _decision(
        claim=claim,
        evidence=evidence,
        claim_key=PILOT_01_REASONING_CLAIM_KEY,
    )

    with pytest.raises(
        InvalidPilotClaimEvaluation,
        match="probe is not bound to the selected claim",
    ):
        evaluate_reviewed_civilization_bootstrap_pilot_01_single_evidence_v1(
            claim_key=PILOT_01_REASONING_CLAIM_KEY,
            claim=claim,
            policy=_policy(),
            candidate=candidate,
            evidence=evidence,
            resolution_binding=binding,
            decision=decision,
        )


def test_evaluation_rejects_post_receipt_evidence_mutation(tmp_path):
    candidate, evidence, binding = _resolved(
        tmp_path,
        probe_id="conceptual_explanation",
        suffix="evidence_mutation",
    )
    claim = _claim()
    changed_context = replace(
        evidence.context,
        factors=evidence.context.factors
        + (ContextFactor(ContextFactorKind.TOOL, "post_receipt_mutation_tool"),),
    )
    changed = replace(evidence, context=changed_context)
    decision = _decision(
        claim=claim,
        evidence=changed,
        claim_key=PILOT_01_REASONING_CLAIM_KEY,
    )

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="evidence_sha256 does not match exact current EvidenceRecord",
    ):
        evaluate_reviewed_civilization_bootstrap_pilot_01_single_evidence_v1(
            claim_key=PILOT_01_REASONING_CLAIM_KEY,
            claim=claim,
            policy=_policy(),
            candidate=candidate,
            evidence=changed,
            resolution_binding=binding,
            decision=decision,
        )


def test_decision_requires_explicit_human_evaluator(tmp_path):
    _candidate, evidence, _binding = _resolved(
        tmp_path,
        probe_id="conceptual_explanation",
        suffix="model_evaluator",
    )
    claim = _claim()
    with pytest.raises(
        InvalidPilotClaimEvaluation,
        match="requires an explicit HUMAN EvaluatorRef",
    ):
        _decision(
            claim=claim,
            evidence=evidence,
            claim_key=PILOT_01_REASONING_CLAIM_KEY,
            evaluator_kind=EvaluatorKind.MODEL,
        )


def test_decision_must_bind_exact_claim_and_evidence_ids(tmp_path):
    candidate, evidence, binding = _resolved(
        tmp_path,
        probe_id="conceptual_explanation",
        suffix="decision_binding",
    )
    claim = _claim()
    decision = replace(
        _decision(
            claim=claim,
            evidence=evidence,
            claim_key=PILOT_01_REASONING_CLAIM_KEY,
        ),
        evidence_id=EvidenceId("different_evidence"),
    )

    with pytest.raises(
        InvalidPilotClaimEvaluation,
        match="decision evidence_id does not match exact reviewed EvidenceRecord",
    ):
        evaluate_reviewed_civilization_bootstrap_pilot_01_single_evidence_v1(
            claim_key=PILOT_01_REASONING_CLAIM_KEY,
            claim=claim,
            policy=_policy(),
            candidate=candidate,
            evidence=evidence,
            resolution_binding=binding,
            decision=decision,
        )


def test_evaluation_rejects_cross_subject_claim_binding(tmp_path):
    candidate, evidence, binding = _resolved(
        tmp_path,
        probe_id="conceptual_explanation",
        suffix="cross_subject",
    )
    claim = _claim(subject_ref=CapabilitySubjectRef("other_subject"))
    decision = _decision(
        claim=claim,
        evidence=evidence,
        claim_key=PILOT_01_REASONING_CLAIM_KEY,
    )

    with pytest.raises(
        InvalidPilotClaimEvaluation,
        match="candidate subject_ref does not match CapabilityClaim subject_ref",
    ):
        evaluate_reviewed_civilization_bootstrap_pilot_01_single_evidence_v1(
            claim_key=PILOT_01_REASONING_CLAIM_KEY,
            claim=claim,
            policy=_policy(),
            candidate=candidate,
            evidence=evidence,
            resolution_binding=binding,
            decision=decision,
        )


def test_evaluation_time_cannot_precede_reviewed_evidence_record(tmp_path):
    candidate, evidence, binding = _resolved(
        tmp_path,
        probe_id="conceptual_explanation",
        suffix="time_boundary",
    )
    claim = _claim(created_minute=1)
    decision = _decision(
        claim=claim,
        evidence=evidence,
        claim_key=PILOT_01_REASONING_CLAIM_KEY,
        evaluated_minute=3,
    )

    with pytest.raises(
        InvalidPilotClaimEvaluation,
        match="evaluated_at must not precede reviewed EvidenceRecord recorded_at",
    ):
        evaluate_reviewed_civilization_bootstrap_pilot_01_single_evidence_v1(
            claim_key=PILOT_01_REASONING_CLAIM_KEY,
            claim=claim,
            policy=_policy(),
            candidate=candidate,
            evidence=evidence,
            resolution_binding=binding,
            decision=decision,
        )
