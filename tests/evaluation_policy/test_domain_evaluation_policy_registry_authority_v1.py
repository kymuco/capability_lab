from datetime import datetime, timezone

import pytest

from capability_lab.epistemics import ClaimScope, EvaluationPolicyRef
from capability_lab.evaluation_policy import (
    DomainEvaluationPolicyRegistry,
    DomainEvaluationPolicyRegistryEntry,
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
    domain_evaluation_policy_registry_sha256_v1,
    domain_evaluation_policy_review_sha256_v1,
    domain_evaluation_policy_specification_sha256_v1,
    resolve_admitted_domain_evaluation_policy_v1,
    review_domain_evaluation_policy_specification_v1,
)
from capability_lab.semantics import CapabilityConceptRef, CapabilityId


_REVIEWED_AT = datetime(2026, 8, 31, 12, 0, tzinfo=timezone.utc)
_ADMITTED_AT = datetime(2026, 8, 31, 13, 0, tzinfo=timezone.utc)


def _specification(*, revision: int = 1) -> DomainEvaluationPolicySpecification:
    return DomainEvaluationPolicySpecification(
        policy_ref=EvaluationPolicyRef(
            "research",
            "registry_authority_review",
            revision,
        ),
        concept_ref=CapabilityConceptRef(
            CapabilityId.parse("research:signal_reasoning"),
            1,
        ),
        claim_scope=ClaimScope(
            "Bounded signal interpretation.",
            ("bounded_reasoning",),
        ),
        requirements=(
            DomainEvaluationPolicyRequirement(
                "diagnostic_reasoning",
                "Diagnoses a bounded signal case.",
                True,
            ),
        ),
    )


def _review(specification: DomainEvaluationPolicySpecification, *, suffix: str = "01"):
    return review_domain_evaluation_policy_specification_v1(
        specification=specification,
        review_id=DomainEvaluationPolicyReviewId(f"registry-review-{suffix}"),
        reviewer_ref=DomainEvaluationPolicyReviewerRef(
            DomainEvaluationPolicyReviewerKind.HUMAN,
            "human:reviewer_01",
        ),
        verdict=DomainEvaluationPolicyReviewVerdict.APPROVE,
        reviewed_at=_REVIEWED_AT,
        rationale="Reviewed exact policy content for registry authority.",
    )


def _review_admission(
    specification: DomainEvaluationPolicySpecification,
    *,
    ledger: DomainEvaluationPolicyReviewLedger | None = None,
    suffix: str = "01",
):
    if ledger is None:
        ledger = DomainEvaluationPolicyReviewLedger()
    review = _review(specification, suffix=suffix)
    successor, admission = admit_domain_evaluation_policy_review_v1(
        review_ledger=ledger,
        specification=specification,
        review=review,
    )
    return successor, admission, review


def _policy_admission(specification: DomainEvaluationPolicySpecification):
    ledger, review_admission, review = _review_admission(specification)
    registry, receipt = admit_domain_evaluation_policy_v1(
        registry=DomainEvaluationPolicyRegistry(),
        review_ledger=ledger,
        review_admission=review_admission,
        specification=specification,
        admitted_at=_ADMITTED_AT,
    )
    return registry, receipt, ledger, review_admission, review


def _manual_registry(
    specification: DomainEvaluationPolicySpecification,
    review,
) -> DomainEvaluationPolicyRegistry:
    empty = DomainEvaluationPolicyRegistry()
    entry = DomainEvaluationPolicyRegistryEntry(
        policy_ref=specification.policy_ref,
        specification_sha256=domain_evaluation_policy_specification_sha256_v1(
            specification
        ),
        specification=specification,
        review_id=review.review_id,
        review_sha256=domain_evaluation_policy_review_sha256_v1(review),
        admitted_at=_ADMITTED_AT,
        predecessor_registry_sha256=domain_evaluation_policy_registry_sha256_v1(
            empty
        ),
    )
    return DomainEvaluationPolicyRegistry(entries=(entry,))


def _resolve(registry, specification):
    return resolve_admitted_domain_evaluation_policy_v1(
        registry=registry,
        policy_ref=specification.policy_ref,
        specification_sha256=domain_evaluation_policy_specification_sha256_v1(
            specification
        ),
    )


def test_manual_structurally_valid_registry_is_audit_data_not_admission_authority():
    specification = _specification()
    review = _review(specification)
    manual = _manual_registry(specification, review)

    with pytest.raises(
        InvalidDomainEvaluationPolicyGovernance,
        match="no runtime admission authority",
    ):
        _resolve(manual, specification)


def test_governed_admission_issues_authority_for_exact_registry_object():
    specification = _specification()
    registry, _, _, _, _ = _policy_admission(specification)

    assert _resolve(registry, specification).to_json() == specification.to_json()

    structurally_equal_copy = DomainEvaluationPolicyRegistry(entries=registry.entries)
    assert structurally_equal_copy == registry
    assert structurally_equal_copy is not registry
    with pytest.raises(
        InvalidDomainEvaluationPolicyGovernance,
        match="no runtime admission authority",
    ):
        _resolve(structurally_equal_copy, specification)


def test_registry_json_round_trip_drops_authority_until_explicit_governed_replay():
    specification = _specification()
    registry, original_receipt, ledger, _, review = _policy_admission(specification)

    restored_registry = DomainEvaluationPolicyRegistry.from_json(registry.to_json())
    restored_ledger = DomainEvaluationPolicyReviewLedger.from_json(ledger.to_json())
    with pytest.raises(
        InvalidDomainEvaluationPolicyGovernance,
        match="no runtime admission authority",
    ):
        _resolve(restored_registry, specification)

    replayed_ledger, fresh_review_admission = (
        admit_domain_evaluation_policy_review_v1(
            review_ledger=restored_ledger,
            specification=specification,
            review=review,
        )
    )
    replayed_registry, replayed_receipt = admit_domain_evaluation_policy_v1(
        registry=restored_registry,
        review_ledger=replayed_ledger,
        review_admission=fresh_review_admission,
        specification=specification,
        admitted_at=datetime(2026, 8, 31, 14, 0, tzinfo=timezone.utc),
    )

    assert replayed_registry == restored_registry
    assert replayed_registry is not restored_registry
    assert replayed_registry.to_json() == registry.to_json()
    assert replayed_receipt == original_receipt
    assert _resolve(replayed_registry, specification).to_json() == specification.to_json()
    with pytest.raises(
        InvalidDomainEvaluationPolicyGovernance,
        match="no runtime admission authority",
    ):
        _resolve(restored_registry, specification)


def test_grown_registry_does_not_inherit_predecessor_object_authority_for_old_policy():
    first = _specification(revision=1)
    registry1, _, ledger1, _, review1 = _policy_admission(first)
    assert _resolve(registry1, first) == first

    second = _specification(revision=2)
    ledger2, second_review_admission, _ = _review_admission(
        second,
        ledger=ledger1,
        suffix="02",
    )
    registry2, _ = admit_domain_evaluation_policy_v1(
        registry=registry1,
        review_ledger=ledger2,
        review_admission=second_review_admission,
        specification=second,
        admitted_at=datetime(2026, 8, 31, 15, 0, tzinfo=timezone.utc),
    )
    assert registry2 is not registry1
    assert _resolve(registry2, second) == second

    with pytest.raises(
        InvalidDomainEvaluationPolicyGovernance,
        match="no runtime admission authority",
    ):
        _resolve(registry2, first)

    replayed_ledger, first_review_admission = (
        admit_domain_evaluation_policy_review_v1(
            review_ledger=ledger2,
            specification=first,
            review=review1,
        )
    )
    replayed_registry, _ = admit_domain_evaluation_policy_v1(
        registry=registry2,
        review_ledger=replayed_ledger,
        review_admission=first_review_admission,
        specification=first,
        admitted_at=datetime(2026, 8, 31, 16, 0, tzinfo=timezone.utc),
    )
    assert replayed_registry == registry2
    assert replayed_registry is not registry2
    assert _resolve(replayed_registry, first) == first
    with pytest.raises(
        InvalidDomainEvaluationPolicyGovernance,
        match="no runtime admission authority",
    ):
        _resolve(registry2, first)


def test_structurally_valid_post_admission_registry_growth_stales_existing_authority():
    first = _specification(revision=1)
    registry, _, _, _, _ = _policy_admission(first)
    original_digest = domain_evaluation_policy_registry_sha256_v1(registry)
    assert _resolve(registry, first) == first

    second = _specification(revision=2)
    second_review = _review(second, suffix="02")
    second_entry = DomainEvaluationPolicyRegistryEntry(
        policy_ref=second.policy_ref,
        specification_sha256=domain_evaluation_policy_specification_sha256_v1(second),
        specification=second,
        review_id=second_review.review_id,
        review_sha256=domain_evaluation_policy_review_sha256_v1(second_review),
        admitted_at=datetime(2026, 8, 31, 15, 0, tzinfo=timezone.utc),
        predecessor_registry_sha256=original_digest,
    )
    object.__setattr__(registry, "entries", registry.entries + (second_entry,))

    with pytest.raises(
        InvalidDomainEvaluationPolicyGovernance,
        match="stale",
    ):
        _resolve(registry, first)


def test_normal_governance_submodule_import_uses_hardened_public_facade():
    import capability_lab.evaluation_policy.governance as governance

    assert governance.admit_domain_evaluation_policy_v1 is admit_domain_evaluation_policy_v1
    assert (
        governance.resolve_admitted_domain_evaluation_policy_v1
        is resolve_admitted_domain_evaluation_policy_v1
    )

    specification = _specification()
    review = _review(specification)
    manual = _manual_registry(specification, review)
    with pytest.raises(
        InvalidDomainEvaluationPolicyGovernance,
        match="no runtime admission authority",
    ):
        governance.resolve_admitted_domain_evaluation_policy_v1(
            registry=manual,
            policy_ref=specification.policy_ref,
            specification_sha256=domain_evaluation_policy_specification_sha256_v1(
                specification
            ),
        )
