from datetime import datetime, timezone

import pytest

from capability_lab.epistemics import ClaimScope, EvaluationPolicyRef
from capability_lab.evaluation_policy import (
    DomainEvaluationPolicyRequirement,
    DomainEvaluationPolicyReviewId,
    DomainEvaluationPolicyReviewerKind,
    DomainEvaluationPolicyReviewerRef,
    DomainEvaluationPolicyReviewLedger,
    DomainEvaluationPolicyReviewVerdict,
    DomainEvaluationPolicySpecification,
    InvalidDomainEvaluationPolicyGovernance,
    admit_domain_evaluation_policy_review_v1,
    domain_evaluation_policy_review_ledger_sha256_v1,
    review_domain_evaluation_policy_specification_v1,
    validate_domain_evaluation_policy_review_ledger_successor_v1,
)
from capability_lab.semantics import CapabilityConceptRef, CapabilityId


_NOW = datetime(2026, 8, 31, 12, 0, tzinfo=timezone.utc)


def _specification(revision: int) -> DomainEvaluationPolicySpecification:
    return DomainEvaluationPolicySpecification(
        policy_ref=EvaluationPolicyRef("research", "signal_reasoning_human_review", revision),
        concept_ref=CapabilityConceptRef(CapabilityId.parse("research:signal_reasoning"), 1),
        claim_scope=ClaimScope("Bounded signal interpretation.", ("bounded_reasoning",)),
        requirements=(
            DomainEvaluationPolicyRequirement(
                "explanation_quality",
                f"Explains revision {revision} policy semantics accurately.",
                True,
            ),
        ),
    )


def _review(specification: DomainEvaluationPolicySpecification, review_id: str, rationale: str):
    return review_domain_evaluation_policy_specification_v1(
        specification=specification,
        review_id=DomainEvaluationPolicyReviewId(review_id),
        reviewer_ref=DomainEvaluationPolicyReviewerRef(
            DomainEvaluationPolicyReviewerKind.HUMAN,
            "human:reviewer_01",
        ),
        verdict=DomainEvaluationPolicyReviewVerdict.APPROVE,
        reviewed_at=_NOW,
        rationale=rationale,
    )


def _two_review_lineage():
    first_spec = _specification(1)
    second_spec = _specification(2)
    first_review = _review(first_spec, "policy-review-v1", "Approve revision one.")
    second_review = _review(second_spec, "policy-review-v2", "Approve revision two.")
    first, first_admission = admit_domain_evaluation_policy_review_v1(
        review_ledger=DomainEvaluationPolicyReviewLedger(),
        specification=first_spec,
        review=first_review,
    )
    second, second_admission = admit_domain_evaluation_policy_review_v1(
        review_ledger=first,
        specification=second_spec,
        review=second_review,
    )
    return (
        first_spec,
        second_spec,
        first_review,
        second_review,
        first,
        second,
        first_admission,
        second_admission,
    )


def test_review_ledger_hash_is_deterministic_and_append_changes_identity():
    _, _, _, _, first, second, _, _ = _two_review_lineage()
    assert domain_evaluation_policy_review_ledger_sha256_v1(first) == domain_evaluation_policy_review_ledger_sha256_v1(
        DomainEvaluationPolicyReviewLedger.from_json(first.to_json())
    )
    assert domain_evaluation_policy_review_ledger_sha256_v1(first) != domain_evaluation_policy_review_ledger_sha256_v1(second)


def test_review_ledger_successor_rejects_removal():
    _, _, _, _, first, second, _, _ = _two_review_lineage()
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="may not remove"):
        validate_domain_evaluation_policy_review_ledger_successor_v1(second, first)


def test_review_ledger_successor_rejects_same_length_mutation():
    first_spec, _, _, _, first, _, _, _ = _two_review_lineage()
    changed_review = _review(
        first_spec,
        "policy-review-v1-mutated",
        "A different terminal review for the same specification.",
    )
    changed = DomainEvaluationPolicyReviewLedger(reviews=(changed_review,))
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="exact prior review prefix"):
        validate_domain_evaluation_policy_review_ledger_successor_v1(first, changed)


def test_review_ledger_successor_rejects_reordering():
    _, _, first_review, second_review, _, second, _, _ = _two_review_lineage()
    reordered = DomainEvaluationPolicyReviewLedger(reviews=(second_review, first_review))
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="exact prior review prefix"):
        validate_domain_evaluation_policy_review_ledger_successor_v1(second, reordered)
