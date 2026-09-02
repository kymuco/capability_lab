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


def test_review_process_authority_import_surface_is_minimal():
    root = Path(__file__).resolve().parents[2] / "src" / "capability_lab" / "evaluation_policy"
    source = (root / "review_process_authority.py").read_text(encoding="utf-8")

    assert _imports(source) == {
        "__future__",
        "os",
        "types",
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


def test_review_process_authority_adds_no_domain_evaluation_or_state_vocabulary():
    root = Path(__file__).resolve().parents[2] / "src" / "capability_lab" / "evaluation_policy"
    source = (root / "review_process_authority.py").read_text(encoding="utf-8").lower()
    for forbidden in (
        "evidence_id",
        "claim_id",
        "evaluation_id",
        "bearing",
        "reliability",
        "coverage",
        "conflict",
        "conclusion",
        "score",
        "mastery",
        "readiness",
        "permission",
        "progression",
        "presentation",
        "pilot_01",
        "majority_vote",
        "confidence_weight",
    ):
        assert forbidden not in source
