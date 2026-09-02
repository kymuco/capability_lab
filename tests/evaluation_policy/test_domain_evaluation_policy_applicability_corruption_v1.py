import pytest

from capability_lab.epistemics import ClaimScope, EvaluationPolicyRef
from capability_lab.evaluation_policy import (
    DomainEvaluationPolicyRequirement,
    DomainEvaluationPolicySpecification,
    InvalidDomainEvaluationPolicySpecification,
    domain_evaluation_policy_specification_applies_to_v1,
)
from capability_lab.semantics import CapabilityConceptRef, CapabilityId


def _concept(revision: int = 1) -> CapabilityConceptRef:
    return CapabilityConceptRef(
        CapabilityId.parse("research:signal_reasoning"),
        revision,
    )


def _scope() -> ClaimScope:
    return ClaimScope(
        "Bounded signal interpretation.",
        ("bounded_reasoning", "signal_evidence"),
    )


def _specification() -> DomainEvaluationPolicySpecification:
    return DomainEvaluationPolicySpecification(
        policy_ref=EvaluationPolicyRef(
            "research",
            "signal_reasoning_human_review",
            1,
        ),
        concept_ref=_concept(),
        claim_scope=_scope(),
        requirements=(
            DomainEvaluationPolicyRequirement(
                "explanation_quality",
                "Explains the relevant signal structure accurately.",
                True,
            ),
        ),
    )


def test_applicability_rejects_corrupted_concept_ref_boolean_revision():
    corrupted = _concept()
    object.__setattr__(corrupted, "revision", True)

    with pytest.raises(
        InvalidDomainEvaluationPolicySpecification,
        match="concept_ref revision must use exact int storage",
    ):
        domain_evaluation_policy_specification_applies_to_v1(
            _specification(),
            concept_ref=corrupted,
            claim_scope=_scope(),
        )


def test_applicability_rejects_corrupted_noncanonical_claim_scope_storage():
    corrupted = _scope()
    object.__setattr__(
        corrupted,
        "tags",
        ["bounded_reasoning", "signal_evidence"],
    )

    with pytest.raises(
        InvalidDomainEvaluationPolicySpecification,
        match=r"claim_scope tags must use canonical tuple\[str, \.\.\.\] storage",
    ):
        domain_evaluation_policy_specification_applies_to_v1(
            _specification(),
            concept_ref=_concept(),
            claim_scope=corrupted,
        )
