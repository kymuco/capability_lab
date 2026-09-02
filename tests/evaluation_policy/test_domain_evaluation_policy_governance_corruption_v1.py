from datetime import datetime, timedelta, timezone

import pytest

from capability_lab.epistemics import ClaimScope, EvaluationPolicyRef
from capability_lab.evaluation_policy import (
    DomainEvaluationPolicyAdmissionReceipt,
    DomainEvaluationPolicyRegistry,
    DomainEvaluationPolicyRequirement,
    DomainEvaluationPolicyReviewId,
    DomainEvaluationPolicyReviewerKind,
    DomainEvaluationPolicyReviewerRef,
    DomainEvaluationPolicyReviewLedger,
    DomainEvaluationPolicyReviewVerdict,
    DomainEvaluationPolicySpecification,
    InvalidDomainEvaluationPolicyGovernance,
    admit_domain_evaluation_policy_review_v1,
    admit_domain_evaluation_policy_v1,
    domain_evaluation_policy_registry_from_dict,
    domain_evaluation_policy_review_sha256_v1,
    review_domain_evaluation_policy_specification_v1,
)
from capability_lab.semantics import CapabilityConceptRef, CapabilityId


_REVIEWED_AT = datetime(2026, 8, 31, 12, 0, tzinfo=timezone.utc)
_ADMITTED_AT = datetime(2026, 8, 31, 13, 0, tzinfo=timezone.utc)


def _specification() -> DomainEvaluationPolicySpecification:
    return DomainEvaluationPolicySpecification(
        policy_ref=EvaluationPolicyRef("research", "signal_reasoning_human_review", 1),
        concept_ref=CapabilityConceptRef(CapabilityId.parse("research:signal_reasoning"), 1),
        claim_scope=ClaimScope(
            "Bounded signal interpretation.",
            ("bounded_reasoning", "signal_evidence"),
        ),
        requirements=(
            DomainEvaluationPolicyRequirement(
                "diagnostic_reasoning", "Diagnoses a bounded signal case.", True
            ),
        ),
    )


def _review(specification: DomainEvaluationPolicySpecification, review_id: str = "policy-review-01"):
    return review_domain_evaluation_policy_specification_v1(
        specification=specification,
        review_id=DomainEvaluationPolicyReviewId(review_id),
        reviewer_ref=DomainEvaluationPolicyReviewerRef(
            DomainEvaluationPolicyReviewerKind.HUMAN,
            "human:reviewer_01",
        ),
        verdict=DomainEvaluationPolicyReviewVerdict.APPROVE,
        reviewed_at=_REVIEWED_AT,
        rationale="Reviewed exact declarative policy content and scope.",
    )


def _artifacts():
    specification = _specification()
    review = _review(specification)
    ledger, review_admission = admit_domain_evaluation_policy_review_v1(
        review_ledger=DomainEvaluationPolicyReviewLedger(),
        specification=specification,
        review=review,
    )
    registry, receipt = admit_domain_evaluation_policy_v1(
        registry=DomainEvaluationPolicyRegistry(),
        review_ledger=ledger,
        review_admission=review_admission,
        specification=specification,
        admitted_at=_ADMITTED_AT,
    )
    return specification, review, ledger, review_admission, registry, receipt


class _BehavioralStr(str):
    def __eq__(self, other: object) -> bool:
        return True

    def __hash__(self) -> int:
        return str.__hash__(self)


def test_review_hash_rejects_post_construction_corrupted_nested_reviewer_ref():
    _, review, _, _, _, _ = _artifacts()
    object.__setattr__(review.reviewer_ref, "ref", _BehavioralStr("human:reviewer_01"))
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="exact str storage"):
        domain_evaluation_policy_review_sha256_v1(review)


def test_review_hash_rejects_post_construction_noncanonical_timezone_storage():
    _, review, _, _, _, _ = _artifacts()
    object.__setattr__(review, "reviewed_at", _REVIEWED_AT.astimezone(timezone(timedelta(hours=6))))
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="canonical UTC storage"):
        domain_evaluation_policy_review_sha256_v1(review)


def test_registry_serialization_rejects_post_construction_corrupted_review_hash():
    _, _, _, _, registry, _ = _artifacts()
    object.__setattr__(registry.entries[0], "review_sha256", _BehavioralStr("0" * 64))
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="exact str storage"):
        registry.to_json()


def test_receipt_serialization_rejects_post_construction_noncanonical_time():
    _, _, _, _, _, receipt = _artifacts()
    object.__setattr__(receipt, "admitted_at", _ADMITTED_AT.astimezone(timezone(timedelta(hours=6))))
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="canonical UTC storage"):
        receipt.to_json()


def test_embedded_noncanonical_pr12_6_specification_is_wrapped_as_governance_failure():
    specification = DomainEvaluationPolicySpecification(
        policy_ref=EvaluationPolicyRef("research", "two_requirement_policy", 1),
        concept_ref=CapabilityConceptRef(CapabilityId.parse("research:signal_reasoning"), 1),
        claim_scope=ClaimScope("Bounded signal interpretation.", ("bounded_reasoning",)),
        requirements=(
            DomainEvaluationPolicyRequirement("a_requirement", "First requirement.", True),
            DomainEvaluationPolicyRequirement("b_requirement", "Second requirement.", True),
        ),
    )
    review = _review(specification, "policy-review-two")
    ledger, review_admission = admit_domain_evaluation_policy_review_v1(
        review_ledger=DomainEvaluationPolicyReviewLedger(),
        specification=specification,
        review=review,
    )
    registry, _ = admit_domain_evaluation_policy_v1(
        registry=DomainEvaluationPolicyRegistry(),
        review_ledger=ledger,
        review_admission=review_admission,
        specification=specification,
        admitted_at=_ADMITTED_AT,
    )
    payload = registry.to_dict()
    payload["entries"][0]["specification"]["requirements"] = list(
        reversed(payload["entries"][0]["specification"]["requirements"])
    )
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="canonical reconstruction"):
        domain_evaluation_policy_registry_from_dict(payload)


def test_receipt_exact_scalar_corruption_fails_before_behavioral_equality():
    _, _, _, _, _, receipt = _artifacts()
    corrupted = DomainEvaluationPolicyAdmissionReceipt.from_json(receipt.to_json())
    object.__setattr__(
        corrupted,
        "successor_registry_sha256",
        _BehavioralStr(corrupted.successor_registry_sha256),
    )
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="exact str storage"):
        corrupted.to_dict()
