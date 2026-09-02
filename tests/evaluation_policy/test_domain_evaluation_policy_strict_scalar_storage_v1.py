import pytest

from capability_lab.epistemics import ClaimScope, EvaluationPolicyRef
from capability_lab.evaluation_policy import (
    DomainEvaluationPolicyRequirement,
    DomainEvaluationPolicySpecification,
    InvalidDomainEvaluationPolicySpecification,
    domain_evaluation_policy_specification_applies_to_v1,
    domain_evaluation_policy_specification_sha256_v1,
)
from capability_lab.semantics import CapabilityConceptRef, CapabilityId


def _scope() -> ClaimScope:
    return ClaimScope("Bounded signal reasoning.", ("bounded_reasoning",))


def _concept() -> CapabilityConceptRef:
    return CapabilityConceptRef(CapabilityId.parse("research:signal_reasoning"), 1)


def _requirement() -> DomainEvaluationPolicyRequirement:
    return DomainEvaluationPolicyRequirement(
        "explanation_quality",
        "Explains the bounded signal structure accurately.",
        True,
    )


def _specification(*, policy_ref: EvaluationPolicyRef | None = None) -> DomainEvaluationPolicySpecification:
    return DomainEvaluationPolicySpecification(
        policy_ref=policy_ref
        or EvaluationPolicyRef("research", "signal_reasoning_human_review", 1),
        concept_ref=_concept(),
        claim_scope=_scope(),
        requirements=(_requirement(),),
    )


class _BehavioralRevision:
    def __str__(self) -> str:
        return "1"

    def __format__(self, format_spec: str) -> str:
        return "1"

    def __eq__(self, other: object) -> bool:
        return True


class _MisleadingInt(int):
    def __new__(cls, value: int):
        return int.__new__(cls, value)

    def __str__(self) -> str:
        return "2"

    def __format__(self, format_spec: str) -> str:
        return "2"


class _MisleadingStr(str):
    def __str__(self) -> str:
        return "other_namespace"


def test_applicability_rejects_behavioral_revision_object_even_when_it_mimics_target():
    policy = _specification()
    corrupted = _concept()
    object.__setattr__(corrupted, "revision", _BehavioralRevision())

    with pytest.raises(InvalidDomainEvaluationPolicySpecification, match="exact int storage"):
        domain_evaluation_policy_specification_applies_to_v1(
            policy,
            concept_ref=corrupted,
            claim_scope=_scope(),
        )


def test_policy_hash_and_serialization_reject_int_subclass_revision():
    misleading_ref = EvaluationPolicyRef(
        "research",
        "signal_reasoning_human_review",
        _MisleadingInt(1),
    )
    policy = _specification(policy_ref=misleading_ref)

    with pytest.raises(InvalidDomainEvaluationPolicySpecification, match="exact int storage"):
        domain_evaluation_policy_specification_sha256_v1(policy)
    with pytest.raises(InvalidDomainEvaluationPolicySpecification, match="exact int storage"):
        policy.to_json()


def test_policy_hash_rejects_str_subclass_storage_inside_policy_ref():
    misleading_ref = EvaluationPolicyRef(
        _MisleadingStr("research"),
        "signal_reasoning_human_review",
        1,
    )
    policy = _specification(policy_ref=misleading_ref)

    with pytest.raises(InvalidDomainEvaluationPolicySpecification, match="exact str storage"):
        domain_evaluation_policy_specification_sha256_v1(policy)


def test_applicability_rejects_str_subclass_storage_inside_capability_id():
    capability_id = CapabilityId(
        _MisleadingStr("research"),
        "signal_reasoning",
    )
    corrupted = CapabilityConceptRef(capability_id, 1)

    with pytest.raises(InvalidDomainEvaluationPolicySpecification, match="exact str storage"):
        domain_evaluation_policy_specification_applies_to_v1(
            _specification(),
            concept_ref=corrupted,
            claim_scope=_scope(),
        )
