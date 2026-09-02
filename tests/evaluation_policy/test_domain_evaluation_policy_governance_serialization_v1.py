from datetime import datetime, timezone

import pytest

from capability_lab.epistemics import ClaimScope, EvaluationPolicyRef
from capability_lab.evaluation_policy import (
    DomainEvaluationPolicyAdmissionReceipt,
    DomainEvaluationPolicyRegistry,
    DomainEvaluationPolicyRequirement,
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
    domain_evaluation_policy_admission_receipt_from_dict,
    domain_evaluation_policy_admission_receipt_from_json,
    domain_evaluation_policy_registry_from_dict,
    domain_evaluation_policy_registry_from_json,
    domain_evaluation_policy_review_from_dict,
    domain_evaluation_policy_review_from_json,
    domain_evaluation_policy_review_ledger_from_dict,
    domain_evaluation_policy_review_ledger_from_json,
    review_domain_evaluation_policy_specification_v1,
)
from capability_lab.semantics import CapabilityConceptRef, CapabilityId


_REVIEWED_AT = datetime(2026, 8, 31, 12, 0, tzinfo=timezone.utc)
_ADMITTED_AT = datetime(2026, 8, 31, 13, 0, tzinfo=timezone.utc)


def _specification(*, revision: int = 1) -> DomainEvaluationPolicySpecification:
    return DomainEvaluationPolicySpecification(
        policy_ref=EvaluationPolicyRef("research", "signal_reasoning_human_review", revision),
        concept_ref=CapabilityConceptRef(CapabilityId.parse("research:signal_reasoning"), 1),
        claim_scope=ClaimScope(
            "Bounded signal interpretation.",
            ("bounded_reasoning", "signal_evidence"),
        ),
        requirements=(
            DomainEvaluationPolicyRequirement(
                "diagnostic_reasoning", "Diagnoses a bounded signal case.", True
            ),
            DomainEvaluationPolicyRequirement(
                "explanation_quality",
                "Explains the relevant signal structure accurately.",
                True,
            ),
        ),
    )


def _review(specification: DomainEvaluationPolicySpecification, review_id: str):
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


def _review_and_ledger(specification: DomainEvaluationPolicySpecification):
    review = _review(specification, f"policy-review-v{specification.policy_ref.revision}")
    ledger, admission = admit_domain_evaluation_policy_review_v1(
        review_ledger=DomainEvaluationPolicyReviewLedger(),
        specification=specification,
        review=review,
    )
    return review, ledger, admission


def _artifacts():
    specification = _specification()
    review, ledger, admission = _review_and_ledger(specification)
    predecessor = DomainEvaluationPolicyRegistry()
    successor, receipt = admit_domain_evaluation_policy_v1(
        registry=predecessor,
        review_ledger=ledger,
        review_admission=admission,
        specification=specification,
        admitted_at=_ADMITTED_AT,
    )
    return specification, review, ledger, admission, predecessor, successor, receipt


class _AlwaysEqual:
    def __eq__(self, other: object) -> bool:
        return True


class _BehavioralStr(str):
    def __eq__(self, other: object) -> bool:
        return True

    def __hash__(self) -> int:
        return str.__hash__(self)


def test_review_ledger_registry_and_receipt_round_trip_deterministically():
    _, review, ledger, admission, _, registry, receipt = _artifacts()
    for value, cls in (
        (review, type(review)),
        (ledger, DomainEvaluationPolicyReviewLedger),
        (registry, DomainEvaluationPolicyRegistry),
        (receipt, DomainEvaluationPolicyAdmissionReceipt),
    ):
        payload = value.to_json()
        restored = cls.from_json(payload)
        assert restored == value
        assert restored.to_json() == payload

    assert review.to_dict()["reviewed_at"] == "2026-08-31T12:00:00.000000Z"
    assert receipt.to_dict()["admitted_at"] == "2026-08-31T13:00:00.000000Z"
    assert not hasattr(admission, "to_json")
    assert not hasattr(DomainEvaluationPolicyReviewAdmission, "from_json")


def test_deserialized_populated_ledger_is_audit_data_not_runtime_authority():
    specification, review, ledger, _, _, _, _ = _artifacts()
    restored = DomainEvaluationPolicyReviewLedger.from_json(ledger.to_json())
    assert restored.reviews == (review,)
    with pytest.raises(TypeError, match="review_admission"):
        admit_domain_evaluation_policy_v1(
            registry=DomainEvaluationPolicyRegistry(),
            review_ledger=restored,
            specification=specification,
            admitted_at=_ADMITTED_AT,
        )


def test_review_serialization_rejects_unknown_missing_duplicate_and_noncanonical_time():
    _, review, _, _, _, _, _ = _artifacts()
    obj = review.to_dict()
    unknown = dict(obj)
    unknown["claim_support"] = True
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="unknown"):
        domain_evaluation_policy_review_from_dict(unknown)
    missing = dict(obj)
    missing.pop("specification_sha256")
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="missing"):
        domain_evaluation_policy_review_from_dict(missing)
    duplicate = review.to_json().replace(
        '"schema_version":1', '"schema_version":1,"schema_version":1', 1
    )
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="duplicate JSON"):
        domain_evaluation_policy_review_from_json(duplicate)
    noncanonical_time = review.to_dict()
    noncanonical_time["reviewed_at"] = "2026-08-31T12:00:00+00:00"
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="canonical UTC"):
        domain_evaluation_policy_review_from_dict(noncanonical_time)


def test_runtime_dict_boundaries_reject_behavioral_scalars_and_non_string_keys():
    _, review, _, _, _, _, _ = _artifacts()
    behavioral_digest = review.to_dict()
    behavioral_digest["specification_sha256"] = _BehavioralStr(
        behavioral_digest["specification_sha256"]
    )
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="exact str"):
        domain_evaluation_policy_review_from_dict(behavioral_digest)
    behavioral_verdict = review.to_dict()
    behavioral_verdict["verdict"] = _AlwaysEqual()
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="exact str"):
        domain_evaluation_policy_review_from_dict(behavioral_verdict)
    bad_key = review.to_dict()
    bad_key[object()] = bad_key.pop("schema_version")
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="keys must use exact str"):
        domain_evaluation_policy_review_from_dict(bad_key)
    bool_schema = review.to_dict()
    bool_schema["schema_version"] = True
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="exact integer 1"):
        domain_evaluation_policy_review_from_dict(bool_schema)


def test_review_ledger_serialization_rejects_wrong_container_and_conflicting_terminal_reviews():
    specification = _specification()
    review, ledger, _ = _review_and_ledger(specification)
    wrong_container = ledger.to_dict()
    wrong_container["reviews"] = tuple(wrong_container["reviews"])
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="JSON array"):
        domain_evaluation_policy_review_ledger_from_dict(wrong_container)
    conflict = review.to_dict()
    conflict["review_id"] = "policy-review-conflict"
    conflict["verdict"] = "REJECT"
    duplicated_identity = ledger.to_dict()
    duplicated_identity["reviews"].append(conflict)
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="terminal review"):
        domain_evaluation_policy_review_ledger_from_dict(duplicated_identity)
    duplicate_json = ledger.to_json().replace('"reviews":', '"reviews":[],"reviews":', 1)
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="duplicate JSON"):
        domain_evaluation_policy_review_ledger_from_json(duplicate_json)


def test_registry_serialization_rejects_reordering_and_noncanonical_embedded_specification():
    first = _specification(revision=1)
    review1, ledger1, admission1 = _review_and_ledger(first)
    registry1, _ = admit_domain_evaluation_policy_v1(
        registry=DomainEvaluationPolicyRegistry(),
        review_ledger=ledger1,
        review_admission=admission1,
        specification=first,
        admitted_at=_ADMITTED_AT,
    )

    second = _specification(revision=2)
    review2 = _review(second, "policy-review-v2")
    ledger2, admission2 = admit_domain_evaluation_policy_review_v1(
        review_ledger=ledger1,
        specification=second,
        review=review2,
    )
    registry2, _ = admit_domain_evaluation_policy_v1(
        registry=registry1,
        review_ledger=ledger2,
        review_admission=admission2,
        specification=second,
        admitted_at=_ADMITTED_AT,
    )

    reordered = registry2.to_dict()
    reordered["entries"] = list(reversed(reordered["entries"]))
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="predecessor digest"):
        domain_evaluation_policy_registry_from_dict(reordered)

    noncanonical_spec = registry1.to_dict()
    noncanonical_spec["entries"][0]["specification"]["requirements"] = list(
        reversed(noncanonical_spec["entries"][0]["specification"]["requirements"])
    )
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="canonical reconstruction"):
        domain_evaluation_policy_registry_from_dict(noncanonical_spec)

    duplicate_json = registry2.to_json().replace(
        '"schema_version":1', '"schema_version":1,"schema_version":1', 1
    )
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="duplicate JSON"):
        domain_evaluation_policy_registry_from_json(duplicate_json)


def test_registry_and_receipt_serialization_reject_behavioral_or_unknown_values():
    _, _, _, _, _, registry, receipt = _artifacts()
    behavioral = registry.to_dict()
    behavioral["entries"][0]["policy_ref"] = _BehavioralStr(
        behavioral["entries"][0]["policy_ref"]
    )
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="exact str"):
        domain_evaluation_policy_registry_from_dict(behavioral)
    wrong_container = registry.to_dict()
    wrong_container["entries"] = tuple(wrong_container["entries"])
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="JSON array"):
        domain_evaluation_policy_registry_from_dict(wrong_container)

    unknown = receipt.to_dict()
    unknown["signature"] = "not-authority"
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="unknown"):
        domain_evaluation_policy_admission_receipt_from_dict(unknown)
    receipt_behavioral = receipt.to_dict()
    receipt_behavioral["successor_registry_sha256"] = _BehavioralStr(
        receipt_behavioral["successor_registry_sha256"]
    )
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="exact str"):
        domain_evaluation_policy_admission_receipt_from_dict(receipt_behavioral)
    duplicate_json = receipt.to_json().replace(
        '"schema_version":1', '"schema_version":1,"schema_version":1', 1
    )
    with pytest.raises(InvalidDomainEvaluationPolicyGovernance, match="duplicate JSON"):
        domain_evaluation_policy_admission_receipt_from_json(duplicate_json)
