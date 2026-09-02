from datetime import datetime, timezone

import pytest

from capability_lab.epistemics import (
    CapabilityClaimId,
    ClaimEvaluationId,
    EvaluationPolicyRef,
    EvidenceId,
)
from capability_lab.interpretation import (
    GENERIC_EXTERNAL_EVIDENCE_HUMAN_EVALUATION_POLICY_V1,
    ExternalEvidenceClaimEvaluationAdmissionReceipt,
    ExternalEvidenceInterpretationProposalId,
    ExternalEvidenceInterpretationReviewId,
    InvalidExternalEvidenceInterpretation,
)


def _receipt_kwargs():
    return {
        "policy_ref": GENERIC_EXTERNAL_EVIDENCE_HUMAN_EVALUATION_POLICY_V1,
        "proposal_id": ExternalEvidenceInterpretationProposalId("strict-proposal"),
        "candidate_sha256": "a" * 64,
        "review_id": ExternalEvidenceInterpretationReviewId("strict-review"),
        "review_sha256": "b" * 64,
        "claim_materialization_receipt_sha256": "c" * 64,
        "evidence_id": EvidenceId("external_observation:" + "d" * 64),
        "evidence_sha256": "e" * 64,
        "claim_id": CapabilityClaimId("strict-claim"),
        "claim_sha256": "f" * 64,
        "evaluation_id": ClaimEvaluationId("strict-evaluation"),
        "evaluation_sha256": "0" * 64,
        "predecessor_snapshot_sha256": "1" * 64,
        "successor_snapshot_sha256": "2" * 64,
        "evaluated_at": datetime(2026, 8, 31, 14, 0, tzinfo=timezone.utc),
    }


def test_receipt_rejects_non_exact_policy_ref_type_at_constructor():
    class DerivedPolicyRef(EvaluationPolicyRef):
        pass

    kwargs = _receipt_kwargs()
    kwargs["policy_ref"] = DerivedPolicyRef(
        GENERIC_EXTERNAL_EVIDENCE_HUMAN_EVALUATION_POLICY_V1.namespace,
        GENERIC_EXTERNAL_EVIDENCE_HUMAN_EVALUATION_POLICY_V1.key,
        GENERIC_EXTERNAL_EVIDENCE_HUMAN_EVALUATION_POLICY_V1.revision,
    )
    with pytest.raises(InvalidExternalEvidenceInterpretation, match="exact EvaluationPolicyRef"):
        ExternalEvidenceClaimEvaluationAdmissionReceipt(**kwargs)


@pytest.mark.parametrize(
    ("field", "message"),
    [
        ("proposal_id", "proposal_id"),
        ("review_id", "review_id"),
        ("claim_id", "claim_id"),
    ],
)
def test_receipt_rejects_untyped_governance_ids_at_constructor(field, message):
    kwargs = _receipt_kwargs()
    kwargs[field] = "forged-untyped-id"
    with pytest.raises(InvalidExternalEvidenceInterpretation, match=message):
        ExternalEvidenceClaimEvaluationAdmissionReceipt(**kwargs)
