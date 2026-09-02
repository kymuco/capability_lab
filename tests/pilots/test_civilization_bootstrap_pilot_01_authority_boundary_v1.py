import ast
from pathlib import Path

import capability_lab.pilots.civilization_bootstrap_01 as pilot
from capability_lab.pilots.civilization_bootstrap_01.run import build_parser


FORBIDDEN_AUTHORITY_MODULES = {
    "capability_lab.derivation",
    "capability_lab.history",
    "capability_lab.player_window",
    "capability_lab.progression",
    "capability_lab.proposals",
}
FORBIDDEN_PILOT_SNAPSHOT_MODULES = {"capability_lab.epistemics.snapshot_transition"}
FORBIDDEN_PILOT_SNAPSHOT_IMPORTS = {
    "EpistemicSnapshotSuccessionReceipt",
    "EpistemicSnapshotTransitionError",
    "InvalidEpistemicSnapshotSuccessor",
    "epistemic_snapshot_sha256_v1",
    "validate_epistemic_snapshot_successor_v1",
}
FORBIDDEN_PILOT_PORTFOLIO_MODULES = {"capability_lab.epistemics.evaluation_portfolio"}
FORBIDDEN_PILOT_PORTFOLIO_IMPORTS = {
    "ClaimEvaluationPortfolioEntry",
    "ClaimEvaluationPortfolioError",
    "ClaimEvaluationPortfolioReceipt",
    "InvalidClaimEvaluationPortfolio",
    "build_complete_claim_evaluation_portfolio_v1",
    "validate_exact_claim_evaluation_selection_v1",
}
RAW_CAPTURE_EPISTEMIC_IMPORTS = {"CapabilitySubjectRef"}
MATERIALIZATION_EPISTEMIC_IMPORTS = {
    "ActorRef", "CapabilitySubjectRef", "ContextFactor", "ContextFactorKind",
    "EvidenceContext", "EvidenceId", "EvidenceKind", "EvidenceRecord",
    "ProvenanceSource", "ProvenanceSourceKind", "ProvenanceStep", "ProvenanceTrail",
}
MATERIALIZATION_SERIALIZATION_EPISTEMIC_IMPORTS = {"CapabilitySubjectRef", "EvidenceId"}
EVALUATION_POLICY_EPISTEMIC_IMPORTS = {"ClaimScope", "EvaluationPolicyRef", "EvidenceBearing"}
EVALUATION_POLICY_EXACT_EPISTEMIC_IMPORTS = {"EvaluationPolicyRef"}
CLAIM_EVALUATION_EPISTEMIC_IMPORTS = {
    "CapabilityClaim", "CapabilityClaimId", "CapabilitySubjectRef", "ClaimEvaluation",
    "ClaimEvaluationId", "ConflictStatus", "CoverageAssessment", "CoverageStatus",
    "EvaluationConclusion", "EvaluationPolicyRef", "EvaluatorKind", "EvaluatorRef",
    "EvidenceAssessment", "EvidenceBearing", "EvidenceId", "EvidenceRecord",
    "EvidenceReliability", "ProvenanceTrail",
}
MULTI_CLAIM_EVALUATION_EPISTEMIC_IMPORTS = {
    "CapabilityClaim", "CapabilityClaimId", "ClaimEvaluation", "ClaimEvaluationId",
    "ConflictStatus", "CoverageAssessment", "CoverageStatus", "EvaluationConclusion",
    "EvaluationPolicyRef", "EvaluatorKind", "EvaluatorRef", "EvidenceAssessment",
    "EvidenceBearing", "EvidenceId", "EvidenceReliability",
}


def test_repository_gitignore_reserves_dot_local_for_private_pilot_data() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    lines = {
        line.strip()
        for line in (repo_root / ".gitignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    assert ".local/" in lines


def test_pilot_01_public_surface_has_no_unreviewed_capture_to_authority_shortcut() -> None:
    forbidden = {
        "materialize_capture_as_evidence", "materialize_evidence", "evaluate_capture",
        "evaluate_session", "evaluate_reviewed_civilization_bootstrap_pilot_01_multi_evidence_v1",
        "epistemic_snapshot_sha256_v1", "validate_epistemic_snapshot_successor_v1",
        "build_complete_claim_evaluation_portfolio_v1", "validate_exact_claim_evaluation_selection_v1",
        "derive_state", "derive_frontier", "render_player_window", "generate_answer",
        "generate_sample_capture",
    }
    assert forbidden.isdisjoint(set(pilot.__all__))
    assert all(not hasattr(pilot, name) for name in forbidden)
    assert "resolve_reviewed_pilot_evidence_materialization_v1" in pilot.__all__


def test_pilot_01_public_capture_mutations_are_routed_through_transaction_boundary() -> None:
    for name in (
        "initialize_private_workspace", "record_text_capture", "record_artifact_capture",
        "validate_private_workspace",
    ):
        function = getattr(pilot, name)
        assert function.__module__ == "capability_lab.pilots.civilization_bootstrap_01.transactional"


def test_raw_capture_runner_still_has_no_materialization_or_evaluation_command() -> None:
    parser = build_parser()
    command_action = next(action for action in parser._actions if getattr(action, "choices", None))
    commands = set(command_action.choices)
    assert commands == {"init", "show-protocol", "record-text", "record-artifact", "validate"}
    assert {"materialize", "review", "evaluate", "derive-state"}.isdisjoint(commands)


def _allowed_epistemic_imports(path_name: str) -> set[str]:
    if path_name == "materialization.py":
        return MATERIALIZATION_EPISTEMIC_IMPORTS
    if path_name == "materialization_serialization.py":
        return MATERIALIZATION_SERIALIZATION_EPISTEMIC_IMPORTS
    if path_name == "evaluation_policy.py":
        return EVALUATION_POLICY_EPISTEMIC_IMPORTS
    if path_name == "evaluation_policy_exact.py":
        return EVALUATION_POLICY_EXACT_EPISTEMIC_IMPORTS
    if path_name == "claim_evaluation.py":
        return CLAIM_EVALUATION_EPISTEMIC_IMPORTS
    if path_name == "claim_evaluation_multi.py":
        return MULTI_CLAIM_EVALUATION_EPISTEMIC_IMPORTS
    return RAW_CAPTURE_EPISTEMIC_IMPORTS


def test_pilot_01_implementation_keeps_authority_imports_narrow_and_localized() -> None:
    package_root = Path(pilot.__file__).resolve().parent
    implementation_files = tuple(sorted(package_root.glob("*.py")))
    assert implementation_files
    for path in implementation_files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = {alias.name for alias in node.names}
                assert FORBIDDEN_AUTHORITY_MODULES.isdisjoint(imported), path.name
                assert FORBIDDEN_PILOT_SNAPSHOT_MODULES.isdisjoint(imported), path.name
                assert FORBIDDEN_PILOT_PORTFOLIO_MODULES.isdisjoint(imported), path.name
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                assert module not in FORBIDDEN_AUTHORITY_MODULES, path.name
                assert module not in FORBIDDEN_PILOT_SNAPSHOT_MODULES, path.name
                assert module not in FORBIDDEN_PILOT_PORTFOLIO_MODULES, path.name
                if module == "capability_lab.epistemics":
                    imported_names = {alias.name for alias in node.names}
                    assert FORBIDDEN_PILOT_SNAPSHOT_IMPORTS.isdisjoint(imported_names), path.name
                    assert FORBIDDEN_PILOT_PORTFOLIO_IMPORTS.isdisjoint(imported_names), path.name
                    assert imported_names <= _allowed_epistemic_imports(path.name), (path.name, imported_names)
                    if path.name not in {"claim_evaluation.py", "claim_evaluation_multi.py"}:
                        assert "CapabilityClaim" not in imported_names, path.name
                        assert "ClaimEvaluation" not in imported_names, path.name


def test_pr11_3_snapshot_transition_imports_match_exact_authority_allowlist() -> None:
    import capability_lab.epistemics.snapshot_transition as transition_module
    allowed_imports = {"hashlib"}
    allowed_from_imports = {
        (0, "__future__"): {"annotations"},
        (0, "dataclasses"): {"dataclass"},
        (1, "core"): {"CapabilityClaimId", "ClaimEvaluationId", "EpistemicError", "EvidenceId"},
        (1, "record_set"): {"EpistemicRecordSet"},
        (1, "serialization"): {"record_set_to_json"},
    }
    path = Path(transition_module.__file__)
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert {alias.name for alias in node.names} <= allowed_imports
        elif isinstance(node, ast.ImportFrom):
            key = (node.level, node.module or "")
            assert key in allowed_from_imports
            assert {alias.name for alias in node.names} <= allowed_from_imports[key]


def test_pr11_3_receipt_distinguishes_structural_construction_from_validator_issue() -> None:
    from capability_lab.epistemics import (
        EpistemicRecordSet, EpistemicSnapshotSuccessionReceipt,
        epistemic_snapshot_sha256_v1, validate_epistemic_snapshot_successor_v1,
    )
    empty = EpistemicRecordSet(); empty_sha256 = epistemic_snapshot_sha256_v1(empty)
    structural = EpistemicSnapshotSuccessionReceipt(
        predecessor_sha256=empty_sha256, successor_sha256=empty_sha256,
    )
    issued = validate_epistemic_snapshot_successor_v1(predecessor=empty, successor=empty)
    assert structural.validator_issued is False
    assert issued.validator_issued is True
    assert isinstance(issued, EpistemicSnapshotSuccessionReceipt)


def test_pr11_4_evaluation_portfolio_imports_match_exact_authority_allowlist() -> None:
    import capability_lab.epistemics.evaluation_portfolio as portfolio_module
    allowed_from_imports = {
        (0, "__future__"): {"annotations"},
        (0, "dataclasses"): {"dataclass"},
        (0, "datetime"): {"datetime"},
        (0, "capability_lab.semantics"): {"CapabilityConceptRef"},
        (1, "core"): {
            "CapabilityClaimId", "CapabilitySubjectRef", "ClaimEvaluationId",
            "EpistemicError", "canonical_time",
        },
        (1, "record_set"): {"EpistemicRecordSet"},
        (1, "snapshot_transition"): {"epistemic_snapshot_sha256_v1"},
    }
    path = Path(portfolio_module.__file__)
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not node.names
        elif isinstance(node, ast.ImportFrom):
            key = (node.level, node.module or "")
            assert key in allowed_from_imports
            assert {alias.name for alias in node.names} <= allowed_from_imports[key]


def test_pr11_4_receipt_distinguishes_structural_construction_from_builder_issue() -> None:
    from datetime import datetime, timezone
    from capability_lab.epistemics import (
        CapabilitySubjectRef, ClaimEvaluationPortfolioReceipt, EpistemicRecordSet,
        build_complete_claim_evaluation_portfolio_v1, epistemic_snapshot_sha256_v1,
    )
    from capability_lab.semantics import CapabilityConceptRef
    empty = EpistemicRecordSet()
    subject_ref = CapabilitySubjectRef("subject_pr11_4_authority")
    concept_ref = CapabilityConceptRef.parse("core:pr11_4_authority@1")
    as_of = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)
    structural = ClaimEvaluationPortfolioReceipt(
        snapshot_sha256=epistemic_snapshot_sha256_v1(empty), subject_ref=subject_ref,
        concept_ref=concept_ref, as_of=as_of,
    )
    issued = build_complete_claim_evaluation_portfolio_v1(
        records=empty, subject_ref=subject_ref, concept_ref=concept_ref, as_of=as_of,
    )
    assert structural.validator_issued is False
    assert issued.validator_issued is True
    assert isinstance(issued, ClaimEvaluationPortfolioReceipt)
