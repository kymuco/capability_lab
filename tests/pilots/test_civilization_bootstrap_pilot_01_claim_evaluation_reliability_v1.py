from datetime import datetime, timezone

import pytest

from capability_lab.epistemics import (
    CapabilityClaimId,
    ClaimEvaluationId,
    ConflictStatus,
    CoverageAssessment,
    CoverageStatus,
    EvaluationConclusion,
    EvaluatorKind,
    EvaluatorRef,
    EvidenceBearing,
    EvidenceId,
    EvidenceReliability,
)
from capability_lab.pilots.civilization_bootstrap_01.claim_evaluation import (
    InvalidPilotClaimEvaluation,
    PilotHumanSingleEvidenceEvaluationDecision,
)
from capability_lab.pilots.civilization_bootstrap_01.evaluation_policy import (
    PILOT_01_EXECUTION_CLAIM_KEY,
    build_civilization_bootstrap_pilot_01_evaluation_policy_v1,
)


def test_decision_rejects_unassessed_reliability():
    policy = build_civilization_bootstrap_pilot_01_evaluation_policy_v1()

    with pytest.raises(
        InvalidPilotClaimEvaluation,
        match="explicit human reliability assessment",
    ):
        PilotHumanSingleEvidenceEvaluationDecision(
            evaluation_id=ClaimEvaluationId("evaluation_unassessed_reliability"),
            claim_key=PILOT_01_EXECUTION_CLAIM_KEY,
            claim_id=CapabilityClaimId("claim_bounded_execution"),
            evidence_id=EvidenceId("evidence_unassessed_reliability"),
            policy_ref=policy.policy_ref,
            evaluator_ref=EvaluatorRef(EvaluatorKind.HUMAN, "human_reviewer"),
            evaluated_at=datetime(2026, 1, 22, 12, 0, tzinfo=timezone.utc),
            bearing=EvidenceBearing.SUPPORTS,
            reliability=EvidenceReliability.UNASSESSED,
            coverage=CoverageAssessment(
                CoverageStatus.SUFFICIENT_FOR_CLAIM,
                "Explicit human coverage judgment.",
            ),
            conflict_status=ConflictStatus.NONE,
            conclusion=EvaluationConclusion.SUPPORTED,
            coverage_note="Single execution evidence covers the bounded claim.",
            evidence_rationale="The reviewed artifact bears positively on execution.",
            evaluation_rationale="Directional conclusion from explicit human review.",
        )
