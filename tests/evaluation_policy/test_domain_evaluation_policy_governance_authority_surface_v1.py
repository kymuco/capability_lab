import ast
from dataclasses import fields
from pathlib import Path

from capability_lab.evaluation_policy import (
    DomainEvaluationPolicyAdmissionReceipt,
    DomainEvaluationPolicyRegistry,
    DomainEvaluationPolicyRegistryEntry,
    DomainEvaluationPolicyReview,
    DomainEvaluationPolicyReviewAdmission,
    DomainEvaluationPolicyReviewLedger,
)


def _imports(source: str) -> set[str]:
    tree = ast.parse(source)
    result: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            result.add(node.module or "")
    return result


def _public_function_parameters(source: str) -> set[str]:
    tree = ast.parse(source)
    result: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
            result.update(argument.arg for argument in node.args.args)
            result.update(argument.arg for argument in node.args.kwonlyargs)
    return result


def test_governance_production_import_surface_is_exact_and_authority_localized():
    root = Path(__file__).resolve().parents[2] / "src" / "capability_lab" / "evaluation_policy"
    governance_source = (root / "governance.py").read_text(encoding="utf-8")
    serialization_source = (root / "governance_serialization.py").read_text(encoding="utf-8")

    assert _imports(governance_source) == {
        "__future__",
        "dataclasses",
        "datetime",
        "enum",
        "hashlib",
        "json",
        "re",
        "unicodedata",
        "capability_lab.epistemics",
        "specification",
        "governance_serialization",
    }
    assert _imports(serialization_source) == {
        "__future__",
        "importlib",
        "json",
        "capability_lab.epistemics",
        "specification",
    }

    for forbidden_import in (
        "capability_lab.derivation",
        "capability_lab.history",
        "capability_lab.interpretation",
        "capability_lab.observations",
        "capability_lab.pilots",
        "capability_lab.player_window",
        "capability_lab.progression",
        "capability_lab.proposals",
    ):
        assert forbidden_import not in _imports(governance_source)
        assert forbidden_import not in _imports(serialization_source)


def test_governance_records_expose_only_review_admission_and_registry_authority():
    forbidden_fields = {
        "evidence_id",
        "evidence_ids",
        "evidence_basis",
        "claim_id",
        "claim_ids",
        "evaluation_id",
        "evaluation_ids",
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
        assert not ({field.name for field in fields(record_type)} & forbidden_fields)


def test_runtime_review_admission_capability_has_no_serialization_surface():
    assert not hasattr(DomainEvaluationPolicyReviewAdmission, "to_dict")
    assert not hasattr(DomainEvaluationPolicyReviewAdmission, "from_dict")
    assert not hasattr(DomainEvaluationPolicyReviewAdmission, "to_json")
    assert not hasattr(DomainEvaluationPolicyReviewAdmission, "from_json")


def test_public_governance_functions_accept_no_evidence_claim_or_state_authority_inputs():
    root = Path(__file__).resolve().parents[2] / "src" / "capability_lab" / "evaluation_policy"
    governance_source = (root / "governance.py").read_text(encoding="utf-8")
    parameters = _public_function_parameters(governance_source)
    forbidden_parameters = {
        "evidence",
        "evidence_id",
        "evidence_ids",
        "evidence_basis",
        "claim",
        "claim_id",
        "claim_ids",
        "evaluation",
        "evaluation_id",
        "bearing",
        "reliability",
        "coverage",
        "conflict",
        "conclusion",
        "state",
        "state_id",
        "score",
        "mastery",
        "readiness",
        "permission",
        "progression",
        "presentation",
    }
    assert not (parameters & forbidden_parameters)
    assert "review_admission" in parameters


def test_no_pilot_specific_probe_or_domain_vocabulary_leaks_into_production():
    root = Path(__file__).resolve().parents[2] / "src" / "capability_lab" / "evaluation_policy"
    combined = "\n".join(
        (root / name).read_text(encoding="utf-8").lower()
        for name in ("governance.py", "governance_serialization.py")
    )
    for forbidden in (
        "conceptual_explanation",
        "calculation_work",
        "diagnosis_reasoning",
        "pilot_01",
        "bounded_reasoning_policy_v1",
    ):
        assert forbidden not in combined
