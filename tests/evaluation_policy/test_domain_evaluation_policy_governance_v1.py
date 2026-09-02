from dataclasses import fields
from datetime import datetime, timezone
import inspect

import pytest

from capability_lab.epistemics import ClaimScope, EvaluationPolicyRef
from capability_lab.evaluation_policy import (
    DomainEvaluationPolicyAdmissionReceipt,
    DomainEvaluationPolicyRegistry,
    DomainEvaluationPolicyRegistryEntry,
    DomainEvaluationPolicyRequirement,
    DomainEvaluationPolicyReview,
    DomainEvaluationPolicyReviewAdmission,
    DomainEvaluationPolicyReviewId,
    DomainEvaluationPolicyReviewerKind,
    DomainEvaluationPolicyReviewerRef,
    DomainEvaluationPolicyReviewLedger,
    DomainEvaluationPolicyReviewVerdict,
    DomainEvaluationPolicySpecification,
    InvalidDomainEvaluationPolicyGovernance,
    admit_domain_evaluation_policy_review_v1,
    admit_domain_evaluation_policy_v1,
    domain_evaluation_policy_admission_receipt_sha256_v1,
    domain_evaluation_policy_registry_sha256_v1,
    domain_evaluation_policy_review_sha256_v1,
    domain_evaluation_policy_specification_sha256_v1,
    resolve_admitted_domain_evaluation_policy_v1,
    review_domain_evaluation_policy_specification_v1,
    validate_domain_evaluation_policy_admission_receipt_v1,
    validate_domain_evaluation_policy_registry_successor_v1,
    validate_domain_evaluation_policy_review_admission_v1,
    validate_domain_evaluation_policy_review_v1,
)
from capability_lab.semantics import CapabilityConceptRef, CapabilityId


_REVIEWED_AT = datetime(2026, 8, 31, 12, 0, tzinfo=timezone.utc)
_ADMITTED_AT = datetime(2026, 8, 31, 13, 0, tzinfo=timezone.utc)


def _specification(
    *,
    policy_revision: int = 1,
    changed: bool = False,
) -> DomainEvaluationPolicySpecification:
    return DomainEvaluationPolicySpecification(
        policy_ref=EvaluationPolicyRef(
            "research", "signal_reasoning_human_review", policy_revision
        ),
        concept_ref=CapabilityConceptRef(
            CapabilityId.parse("research:signal_reasoning"), 1
        ),
        claim_scope=ClaimScope(
            "Bounded signal interpretation.",
            ("bounded_reasoning", "signal_evidence"),
        ),
        requirements=(
            DomainEvaluationPolicyRequirement(
                "diagnostic_reasoning",
                "Diagnoses a bounded signal case."
                if not changed
                else "Diagnoses the bounded signal case with an explicit alternative.",
                True,
            ),
            DomainEvaluationPolicyRequirement(
                "explanation_quality",
                "Explains the relevant signal structure accurately.",
                True,
            ),
        ),
    )


def _reviewer() -> DomainEvaluationPolicyReviewerRef:
    return DomainEvaluationPolicyReviewerRef(
        DomainEvaluationPolicyReviewerKind.HUMAN,
        "human:reviewer_01",
    )


def _review(
    specification: DomainEvaluationPolicySpecification,
    *,
    review_id: str = "policy-review-01",
    verdict: DomainEvaluationPolicyReviewVerdict = DomainEvaluationPolicyReviewVerdict.APPROVE,
) -> DomainEvaluationPolicyReview:
    return review_domain_evaluation_policy_specification_v1(
        specification=specification,
        review_id=DomainEvaluationPolicyReviewId(review_id),
        reviewer_ref=_reviewer(),
        verdict=verdict,
        reviewed_at=_REVIEWED_AT,
        rationale="Reviewed exact declarative policy content and scope.",
    )


def _admit_review(
    specification: DomainEvaluationPolicySpecification,
    *,
    ledger: DomainEvaluationPolicyReviewLedger | None = None,
    review_id: str = "policy-review-01",
    verdict: DomainEvaluationPolicyReviewVerdict = DomainEvaluationPolicyReviewVerdict.APPROVE,
):
    if ledger is None:
        ledger = DomainEvaluationPolicyReviewLedger()
    review = _review(specification, review_id=review_id, verdict=verdict)
    successor, admission = admit_domain_evaluation_policy_review_v1(
        review_ledger=ledger,
        specification=specification,
        review=review,
    )
    return successor, admission, review


def _admit_policy(
    specification: DomainEvaluationPolicySpecification,
    *,
    registry: DomainEvaluationPolicyRegistry | None = None,
    ledger: DomainEvaluationPolicyReviewLedger | None = None,
    admission: DomainEvaluationPolicyReviewAdmission | None = None,
    review_id: str = "policy-review-01",
):
    if ledger is None or admission is None:
        ledger, admission, _ = _admit_review(
            specification, ledger=ledger, review_id=review_id
        )
    if registry is None:
        registry = DomainEvaluationPolicyRegistry()
    return admit_domain_evaluation_policy_v1(
        registry=registry,
        review_ledger=ledger,
        review_admission=admission,
        specification=specification,
        admitted_at=_ADMITTED_AT,
    )


def test_review_binds_exact_pr12_6_specification_digest_and_declared_human():
    specification = _specification()
    review = _review(specification)
    assert review.policy_ref == specification.policy_ref
    assert review.specification_sha256 == domain_evaluation_policy_specification_sha256_v1(
        specification
    )
    assert review.reviewer_ref.kind is DomainEvaluationPolicyReviewerKind.HUMAN
    validate_domain_evaluation_policy_review_v1(
        specification=specification,
        review=review,
    )

    changed = _specification(changed=True)
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="specification_sha256"):
        validate_domain_evaluation_policy_review_v1(
            specification=changed,
            review=review,
        )
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="reviewer kind"):
        DomainEvaluationPolicyReviewerRef("HUMAN", "human:reviewer_01")  # type: ignore[arg-type]


def test_terminal_review_exact_replay_is_idempotent_and_issues_fresh_authority():
    specification = _specification()
    review = _review(specification)
    empty = DomainEvaluationPolicyReviewLedger()
    ledger, admission1 = admit_domain_evaluation_policy_review_v1(
        review_ledger=empty,
        specification=specification,
        review=review,
    )
    replay, admission2 = admit_domain_evaluation_policy_review_v1(
        review_ledger=ledger,
        specification=specification,
        review=review,
    )
    assert replay == ledger
    assert len(replay.reviews) == 1
    assert admission1 is not admission2
    assert validate_domain_evaluation_policy_review_admission_v1(
        review_ledger=ledger,
        specification=specification,
        review_admission=admission2,
    ) == review

    conflicting = _review(
        specification,
        review_id="policy-review-02",
        verdict=DomainEvaluationPolicyReviewVerdict.REJECT,
    )
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="different terminal review"):
        admit_domain_evaluation_policy_review_v1(
            review_ledger=ledger,
            specification=specification,
            review=conflicting,
        )


def test_raw_approval_wrapped_in_direct_or_deserialized_ledger_is_not_registry_authority():
    specification = _specification()
    raw_approval = _review(specification)
    direct = DomainEvaluationPolicyReviewLedger(reviews=(raw_approval,))
    restored = DomainEvaluationPolicyReviewLedger.from_json(direct.to_json())

    signature = inspect.signature(admit_domain_evaluation_policy_v1)
    assert "review_admission" in signature.parameters
    assert signature.parameters["review_admission"].default is inspect.Parameter.empty

    for ledger in (direct, restored):
        with pytest.raises(TypeError, match="review_admission"):
            admit_domain_evaluation_policy_v1(
                registry=DomainEvaluationPolicyRegistry(),
                review_ledger=ledger,
                specification=specification,
                admitted_at=_ADMITTED_AT,
            )


def test_review_admission_cannot_be_publicly_constructed_or_forged_with_object_new():
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="only be issued"):
        DomainEvaluationPolicyReviewAdmission()

    specification = _specification()
    review = _review(specification)
    forged = object.__new__(DomainEvaluationPolicyReviewAdmission)
    object.__setattr__(forged, "policy_ref", specification.policy_ref)
    object.__setattr__(
        forged,
        "specification_sha256",
        domain_evaluation_policy_specification_sha256_v1(specification),
    )
    object.__setattr__(forged, "review_id", review.review_id)
    object.__setattr__(forged, "review_sha256", domain_evaluation_policy_review_sha256_v1(review))
    object.__setattr__(forged, "predecessor_review_ledger_sha256", "0" * 64)
    object.__setattr__(forged, "successor_review_ledger_sha256", "0" * 64)
    object.__setattr__(forged, "review_ledger_sha256", "0" * 64)
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="was not issued"):
        validate_domain_evaluation_policy_review_admission_v1(
            review_ledger=DomainEvaluationPolicyReviewLedger(reviews=(review,)),
            specification=specification,
            review_admission=forged,
        )


def test_review_admission_is_exact_spec_bound_and_becomes_stale_after_ledger_growth():
    first = _specification(policy_revision=1)
    first_ledger, first_admission, _ = _admit_review(first, review_id="review-v1")
    changed_same_ref = _specification(policy_revision=1, changed=True)
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="specification_sha256"):
        validate_domain_evaluation_policy_review_admission_v1(
            review_ledger=first_ledger,
            specification=changed_same_ref,
            review_admission=first_admission,
        )

    second = _specification(policy_revision=2, changed=True)
    second_ledger, _, _ = _admit_review(
        second, ledger=first_ledger, review_id="review-v2"
    )
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="stale"):
        validate_domain_evaluation_policy_review_admission_v1(
            review_ledger=second_ledger,
            specification=first,
            review_admission=first_admission,
        )

    replayed_ledger, fresh_admission = admit_domain_evaluation_policy_review_v1(
        review_ledger=second_ledger,
        specification=first,
        review=first_ledger.reviews[0],
    )
    assert replayed_ledger == second_ledger
    assert len(replayed_ledger.reviews) == 2
    validate_domain_evaluation_policy_review_admission_v1(
        review_ledger=replayed_ledger,
        specification=first,
        review_admission=fresh_admission,
    )


def test_terminal_reject_has_governed_authority_but_admits_no_policy():
    specification = _specification()
    ledger, admission, review = _admit_review(
        specification,
        verdict=DomainEvaluationPolicyReviewVerdict.REJECT,
    )
    assert review.verdict is DomainEvaluationPolicyReviewVerdict.REJECT
    registry = DomainEvaluationPolicyRegistry()
    before = domain_evaluation_policy_registry_sha256_v1(registry)
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="REJECT"):
        admit_domain_evaluation_policy_v1(
            registry=registry,
            review_ledger=ledger,
            review_admission=admission,
            specification=specification,
            admitted_at=_ADMITTED_AT,
        )
    assert registry.entries == ()
    assert domain_evaluation_policy_registry_sha256_v1(registry) == before


def test_approve_admits_exact_content_and_receipt_replays_full_transition():
    specification = _specification()
    ledger, admission, review = _admit_review(specification)
    predecessor = DomainEvaluationPolicyRegistry()
    successor, receipt = admit_domain_evaluation_policy_v1(
        registry=predecessor,
        review_ledger=ledger,
        review_admission=admission,
        specification=specification,
        admitted_at=_ADMITTED_AT,
    )
    assert len(successor.entries) == 1
    entry = successor.entries[0]
    assert entry.policy_ref == specification.policy_ref
    assert entry.specification_sha256 == domain_evaluation_policy_specification_sha256_v1(
        specification
    )
    assert entry.specification.to_json() == specification.to_json()
    assert entry.review_id == review.review_id
    assert entry.review_sha256 == domain_evaluation_policy_review_sha256_v1(review)
    assert receipt.predecessor_registry_sha256 == domain_evaluation_policy_registry_sha256_v1(
        predecessor
    )
    assert receipt.successor_registry_sha256 == domain_evaluation_policy_registry_sha256_v1(
        successor
    )
    assert len(domain_evaluation_policy_admission_receipt_sha256_v1(receipt)) == 64

    validate_domain_evaluation_policy_admission_receipt_v1(
        predecessor_registry=predecessor,
        successor_registry=successor,
        review_ledger=ledger,
        review_admission=admission,
        specification=specification,
        receipt=receipt,
    )
    resolved = resolve_admitted_domain_evaluation_policy_v1(
        registry=successor,
        policy_ref=specification.policy_ref,
        specification_sha256=entry.specification_sha256,
    )
    assert resolved.to_json() == specification.to_json()


def test_same_ref_same_exact_content_is_idempotent_exact_registry_replay():
    specification = _specification()
    ledger, admission, _ = _admit_review(specification)
    registry, receipt = _admit_policy(
        specification, ledger=ledger, admission=admission
    )
    replay_registry, replay_receipt = admit_domain_evaluation_policy_v1(
        registry=registry,
        review_ledger=ledger,
        review_admission=admission,
        specification=specification,
        admitted_at=datetime(2026, 8, 31, 14, 0, tzinfo=timezone.utc),
    )
    assert replay_registry == registry
    assert replay_receipt == receipt
    assert replay_receipt.admitted_at == _ADMITTED_AT
    assert len(replay_registry.entries) == 1


def test_same_policy_ref_changed_content_cannot_rebind_registry():
    original = _specification()
    original_ledger, original_admission, _ = _admit_review(original)
    registry, _ = _admit_policy(
        original, ledger=original_ledger, admission=original_admission
    )

    changed = _specification(changed=True)
    changed_ledger, changed_admission, _ = _admit_review(
        changed, ledger=original_ledger, review_id="policy-review-changed"
    )
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="immutably bound"):
        admit_domain_evaluation_policy_v1(
            registry=registry,
            review_ledger=changed_ledger,
            review_admission=changed_admission,
            specification=changed,
            admitted_at=_ADMITTED_AT,
        )


def test_changed_content_under_new_policy_revision_is_independently_admissible():
    first = _specification(policy_revision=1)
    ledger1, admission1, _ = _admit_review(first, review_id="policy-review-v1")
    registry1, _ = _admit_policy(first, ledger=ledger1, admission=admission1)

    second = _specification(policy_revision=2, changed=True)
    ledger2, admission2, _ = _admit_review(
        second, ledger=ledger1, review_id="policy-review-v2"
    )
    registry2, receipt2 = admit_domain_evaluation_policy_v1(
        registry=registry1,
        review_ledger=ledger2,
        review_admission=admission2,
        specification=second,
        admitted_at=_ADMITTED_AT,
    )
    assert len(registry2.entries) == 2
    assert tuple(entry.policy_ref.revision for entry in registry2.entries) == (1, 2)
    assert receipt2.policy_ref.revision == 2


def test_registry_removal_mutation_and_reordering_fail_closed():
    first = _specification(policy_revision=1)
    ledger1, admission1, _ = _admit_review(first, review_id="review-v1")
    registry1, _ = _admit_policy(first, ledger=ledger1, admission=admission1)
    second = _specification(policy_revision=2, changed=True)
    ledger2, admission2, _ = _admit_review(second, ledger=ledger1, review_id="review-v2")
    registry2, _ = admit_domain_evaluation_policy_v1(
        registry=registry1,
        review_ledger=ledger2,
        review_admission=admission2,
        specification=second,
        admitted_at=_ADMITTED_AT,
    )

    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="may not remove"):
        validate_domain_evaluation_policy_registry_successor_v1(registry2, registry1)
    mutated = DomainEvaluationPolicyRegistry.from_json(registry2.to_json())
    object.__setattr__(mutated.entries[0], "review_sha256", "0" * 64)
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="prior registry prefix"):
        validate_domain_evaluation_policy_registry_successor_v1(registry2, mutated)
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="predecessor digest"):
        DomainEvaluationPolicyRegistry(entries=tuple(reversed(registry2.entries)))


def test_receipt_mutation_is_rejected_by_full_transition_replay():
    specification = _specification()
    ledger, admission, _ = _admit_review(specification)
    predecessor = DomainEvaluationPolicyRegistry()
    successor, receipt = admit_domain_evaluation_policy_v1(
        registry=predecessor,
        review_ledger=ledger,
        review_admission=admission,
        specification=specification,
        admitted_at=_ADMITTED_AT,
    )
    corrupted = DomainEvaluationPolicyAdmissionReceipt.from_json(receipt.to_json())
    object.__setattr__(corrupted, "successor_registry_sha256", "0" * 64)
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="successor_registry_sha256"):
        validate_domain_evaluation_policy_admission_receipt_v1(
            predecessor_registry=predecessor,
            successor_registry=successor,
            review_ledger=ledger,
            review_admission=admission,
            specification=specification,
            receipt=corrupted,
        )


def test_registry_resolution_requires_exact_ref_and_exact_content_digest():
    specification = _specification()
    registry, _ = _admit_policy(specification)
    digest = domain_evaluation_policy_specification_sha256_v1(specification)
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="digest"):
        resolve_admitted_domain_evaluation_policy_v1(
            registry=registry,
            policy_ref=specification.policy_ref,
            specification_sha256="0" * 64,
        )
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="not admitted"):
        resolve_admitted_domain_evaluation_policy_v1(
            registry=registry,
            policy_ref=EvaluationPolicyRef(
                specification.policy_ref.namespace,
                specification.policy_ref.key,
                2,
            ),
            specification_sha256=digest,
        )


def test_governance_surface_contains_no_policy_application_or_state_authority_fields():
    forbidden = {
        "evidence_id",
        "evidence_ids",
        "claim_id",
        "evaluation_id",
        "evaluator_ref",
        "bearing",
        "reliability",
        "coverage",
        "conflict",
        "conclusion",
        "state_id",
        "score",
        "mastery",
        "readiness",
        "permission",
        "progression",
        "presentation",
        "active",
        "latest",
        "supersedes",
    }
    for record_type in (
        DomainEvaluationPolicyReview,
        DomainEvaluationPolicyReviewLedger,
        DomainEvaluationPolicyRegistryEntry,
        DomainEvaluationPolicyRegistry,
        DomainEvaluationPolicyAdmissionReceipt,
    ):
        assert not ({item.name for item in fields(record_type)} & forbidden)
