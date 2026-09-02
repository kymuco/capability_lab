import pytest

from capability_lab.epistemics import ClaimScope, EvaluationPolicyRef
from capability_lab.evaluation_policy import (
    DomainEvaluationPolicyRequirement,
    DomainEvaluationPolicySpecification,
    InvalidDomainEvaluationPolicySpecification,
    domain_evaluation_policy_specification_from_dict,
)
from capability_lab.semantics import CapabilityConceptRef, CapabilityId


def _payload() -> dict:
    specification = DomainEvaluationPolicySpecification(
        policy_ref=EvaluationPolicyRef(
            "research",
            "signal_reasoning_human_review",
            1,
        ),
        concept_ref=CapabilityConceptRef(
            CapabilityId.parse("research:signal_reasoning"),
            1,
        ),
        claim_scope=ClaimScope(
            "Bounded signal interpretation.",
            ("bounded_reasoning", "signal_evidence"),
        ),
        requirements=(
            DomainEvaluationPolicyRequirement(
                "explanation_quality",
                "Explains the relevant signal structure accurately.",
                True,
            ),
        ),
    )
    return specification.to_dict()


class _AlwaysEqual:
    def __eq__(self, other: object) -> bool:
        return True


class _BehavioralStr(str):
    def __eq__(self, other: object) -> bool:
        return True

    def __hash__(self) -> int:
        return str.__hash__(self)

    def count(self, sub: str, *args) -> int:
        return 1

    def rsplit(self, sep=None, maxsplit=-1):
        return ["research:signal_reasoning", "1"]


def test_from_dict_rejects_behavioral_sufficiency_semantics_object():
    payload = _payload()
    payload["sufficiency_semantics"] = _AlwaysEqual()

    with pytest.raises(
        InvalidDomainEvaluationPolicySpecification,
        match="sufficiency_semantics must use exact str storage",
    ):
        domain_evaluation_policy_specification_from_dict(payload)


def test_from_dict_rejects_str_subclass_for_policy_ref():
    payload = _payload()
    payload["policy_ref"] = _BehavioralStr(payload["policy_ref"])

    with pytest.raises(
        InvalidDomainEvaluationPolicySpecification,
        match="policy_ref must use exact str storage",
    ):
        domain_evaluation_policy_specification_from_dict(payload)


def test_from_dict_rejects_str_subclass_for_concept_ref():
    payload = _payload()
    payload["concept_ref"] = _BehavioralStr(payload["concept_ref"])

    with pytest.raises(
        InvalidDomainEvaluationPolicySpecification,
        match="concept_ref must use exact str storage",
    ):
        domain_evaluation_policy_specification_from_dict(payload)


def test_from_dict_rejects_non_string_object_key_before_schema_equality():
    payload = _payload()
    payload[object()] = payload.pop("schema_version")

    with pytest.raises(
        InvalidDomainEvaluationPolicySpecification,
        match="keys must use exact str JSON-object storage",
    ):
        domain_evaluation_policy_specification_from_dict(payload)
