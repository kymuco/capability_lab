from dataclasses import fields
import ast
from pathlib import Path

import pytest

from capability_lab.epistemics import ClaimScope, EvaluationPolicyRef
from capability_lab.evaluation_policy import (
    DOMAIN_EVALUATION_SUFFICIENCY_SEMANTICS_V1,
    DomainEvaluationPolicyRequirement,
    DomainEvaluationPolicySpecification,
    InvalidDomainEvaluationPolicySpecification,
    domain_evaluation_policy_specification_applies_to_v1,
    domain_evaluation_policy_specification_from_dict,
    domain_evaluation_policy_specification_from_json,
    domain_evaluation_policy_specification_sha256_v1,
)
from capability_lab.semantics import CapabilityConceptRef, CapabilityId


def _concept(revision: int = 1) -> CapabilityConceptRef:
    return CapabilityConceptRef(CapabilityId.parse("research:signal_reasoning"), revision)


def _scope(*, description: str = "Bounded signal interpretation.") -> ClaimScope:
    return ClaimScope(description, ("bounded_reasoning", "signal_evidence"))


def _requirement(
    key: str = "explanation_quality",
    *,
    description: str = "Explains the relevant signal structure accurately.",
    required: bool = True,
) -> DomainEvaluationPolicyRequirement:
    return DomainEvaluationPolicyRequirement(key, description, required)


def _specification() -> DomainEvaluationPolicySpecification:
    return DomainEvaluationPolicySpecification(
        policy_ref=EvaluationPolicyRef("research", "signal_reasoning_human_review", 1),
        concept_ref=_concept(),
        claim_scope=_scope(),
        requirements=(
            _requirement("diagnostic_reasoning", description="Diagnoses a bounded signal case."),
            _requirement(),
            _requirement(
                "optional_context",
                description="Addresses optional contextual detail.",
                required=False,
            ),
        ),
    )


def test_specification_canonicalizes_requirements_and_round_trips():
    value = _specification()
    assert tuple(item.requirement_key for item in value.requirements) == (
        "diagnostic_reasoning",
        "explanation_quality",
        "optional_context",
    )
    payload = value.to_json()
    restored = DomainEvaluationPolicySpecification.from_json(payload)
    assert restored == value
    assert restored.to_json() == payload
    assert DOMAIN_EVALUATION_SUFFICIENCY_SEMANTICS_V1 in payload


def test_exact_concept_revision_and_claim_scope_applicability():
    value = _specification()
    assert domain_evaluation_policy_specification_applies_to_v1(
        value,
        concept_ref=_concept(1),
        claim_scope=_scope(),
    )
    assert not domain_evaluation_policy_specification_applies_to_v1(
        value,
        concept_ref=_concept(2),
        claim_scope=_scope(),
    )
    assert not domain_evaluation_policy_specification_applies_to_v1(
        value,
        concept_ref=_concept(1),
        claim_scope=_scope(description="A wider but similar scope."),
    )


def test_policy_content_digest_is_deterministic_and_content_bound():
    first = _specification()
    second = _specification()
    assert domain_evaluation_policy_specification_sha256_v1(first) == domain_evaluation_policy_specification_sha256_v1(second)

    changed = DomainEvaluationPolicySpecification(
        policy_ref=first.policy_ref,
        concept_ref=first.concept_ref,
        claim_scope=first.claim_scope,
        requirements=(
            _requirement("diagnostic_reasoning", description="Changed semantic requirement."),
            _requirement(),
        ),
    )
    assert changed.policy_ref == first.policy_ref
    assert domain_evaluation_policy_specification_sha256_v1(changed) != domain_evaluation_policy_specification_sha256_v1(first)


def test_duplicate_requirement_keys_are_rejected():
    with pytest.raises(InvalidDomainEvaluationPolicySpecification, match="duplicate"):
        DomainEvaluationPolicySpecification(
            policy_ref=EvaluationPolicyRef("research", "signal_reasoning_human_review", 1),
            concept_ref=_concept(),
            claim_scope=_scope(),
            requirements=(
                _requirement("same_key", description="First."),
                _requirement("same_key", description="Second."),
            ),
        )


def test_at_least_one_requirement_must_be_required_for_sufficiency():
    with pytest.raises(InvalidDomainEvaluationPolicySpecification, match="at least one"):
        DomainEvaluationPolicySpecification(
            policy_ref=EvaluationPolicyRef("research", "signal_reasoning_human_review", 1),
            concept_ref=_concept(),
            claim_scope=_scope(),
            requirements=(_requirement(required=False),),
        )


def test_requirement_key_and_bool_are_strict():
    with pytest.raises(InvalidDomainEvaluationPolicySpecification, match="machine-key"):
        _requirement("Execution Artifact")
    with pytest.raises(InvalidDomainEvaluationPolicySpecification, match="exact bool"):
        DomainEvaluationPolicyRequirement("valid_key", "Valid description.", 1)


def test_constructor_rejects_subclassed_authority_refs():
    class DerivedPolicyRef(EvaluationPolicyRef):
        pass

    with pytest.raises(InvalidDomainEvaluationPolicySpecification, match="exact EvaluationPolicyRef"):
        DomainEvaluationPolicySpecification(
            policy_ref=DerivedPolicyRef("research", "signal_reasoning_human_review", 1),
            concept_ref=_concept(),
            claim_scope=_scope(),
            requirements=(_requirement(),),
        )


def test_serialization_rejects_unknown_missing_duplicate_and_noncanonical_order():
    value = _specification()
    obj = value.to_dict()

    unknown = dict(obj)
    unknown["active"] = True
    with pytest.raises(InvalidDomainEvaluationPolicySpecification, match="unknown"):
        domain_evaluation_policy_specification_from_dict(unknown)

    missing = dict(obj)
    missing.pop("concept_ref")
    with pytest.raises(InvalidDomainEvaluationPolicySpecification, match="missing"):
        domain_evaluation_policy_specification_from_dict(missing)

    duplicate = value.to_json().replace(
        '"schema_version":1',
        '"schema_version":1,"schema_version":1',
        1,
    )
    with pytest.raises(InvalidDomainEvaluationPolicySpecification, match="duplicate JSON"):
        domain_evaluation_policy_specification_from_json(duplicate)

    noncanonical = value.to_dict()
    noncanonical["requirements"] = list(reversed(noncanonical["requirements"]))
    with pytest.raises(InvalidDomainEvaluationPolicySpecification, match="canonical reconstruction"):
        domain_evaluation_policy_specification_from_dict(noncanonical)


def test_serialization_rejects_changed_frozen_sufficiency_semantics():
    obj = _specification().to_dict()
    obj["sufficiency_semantics"] = "three_observations_required"
    with pytest.raises(InvalidDomainEvaluationPolicySpecification, match="frozen v1"):
        domain_evaluation_policy_specification_from_dict(obj)


def test_strict_digest_rejects_post_construction_nested_corruption():
    value = _specification()
    object.__setattr__(value, "concept_ref", object())
    with pytest.raises((InvalidDomainEvaluationPolicySpecification, AttributeError, TypeError)):
        domain_evaluation_policy_specification_sha256_v1(value)


def test_public_specification_surface_contains_no_evaluation_or_state_authority_fields():
    specification_fields = {item.name for item in fields(DomainEvaluationPolicySpecification)}
    requirement_fields = {item.name for item in fields(DomainEvaluationPolicyRequirement)}
    forbidden = {
        "claim_id",
        "evidence_id",
        "evaluation_id",
        "evaluator_ref",
        "bearing",
        "reliability",
        "conclusion",
        "state_id",
        "score",
        "mastery",
        "readiness",
        "permission",
        "progression",
        "active",
        "approved",
    }
    assert not (specification_fields & forbidden)
    assert not (requirement_fields & forbidden)


def test_generic_production_import_surface_is_frozen_and_domain_neutral():
    root = Path(__file__).resolve().parents[2] / "src" / "capability_lab" / "evaluation_policy"
    specification_source = (root / "specification.py").read_text(encoding="utf-8")
    serialization_source = (root / "serialization.py").read_text(encoding="utf-8")

    def imports(source: str) -> set[str]:
        tree = ast.parse(source)
        result = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                result.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                result.add(node.module or "")
        return result

    assert imports(specification_source) == {
        "__future__",
        "dataclasses",
        "hashlib",
        "json",
        "re",
        "unicodedata",
        "capability_lab.epistemics",
        "capability_lab.semantics",
        "serialization",
    }
    assert imports(serialization_source) == {
        "__future__",
        "json",
        "capability_lab.epistemics",
        "capability_lab.semantics",
        "specification",
    }

    combined = (specification_source + serialization_source).lower()
    for forbidden in (
        "capability_lab.derivation",
        "capability_lab.history",
        "capability_lab.progression",
        "capability_lab.player_window",
        "capability_lab.pilots",
        "personalcapabilitystate",
        "claim evaluation",
    ):
        assert forbidden not in combined
