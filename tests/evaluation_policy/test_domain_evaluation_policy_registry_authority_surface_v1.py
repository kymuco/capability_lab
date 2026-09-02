import ast
from pathlib import Path


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


def test_registry_authority_import_surface_is_narrow_and_domain_neutral():
    root = Path(__file__).resolve().parents[2] / "src" / "capability_lab" / "evaluation_policy"
    source = (root / "registry_authority.py").read_text(encoding="utf-8")

    assert _imports(source) == {
        "__future__",
        "importlib",
        "os",
        "types",
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
        assert forbidden_import not in _imports(source)


def test_registry_authority_public_api_accepts_no_evidence_claim_or_state_inputs():
    root = Path(__file__).resolve().parents[2] / "src" / "capability_lab" / "evaluation_policy"
    source = (root / "registry_authority.py").read_text(encoding="utf-8")
    parameters = _public_function_parameters(source)
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
        "active",
        "latest",
        "supersedes",
    }
    assert not (parameters & forbidden_parameters)


def test_registry_authority_contains_no_pilot_or_independence_shortcut_vocabulary():
    root = Path(__file__).resolve().parents[2] / "src" / "capability_lab" / "evaluation_policy"
    source = (root / "registry_authority.py").read_text(encoding="utf-8").lower()
    for forbidden in (
        "conceptual_explanation",
        "calculation_work",
        "diagnosis_reasoning",
        "pilot_01",
        "bounded_reasoning_policy_v1",
        "independent_observation",
        "majority_vote",
        "confidence_weight",
    ):
        assert forbidden not in source
