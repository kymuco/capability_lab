from __future__ import annotations

from pathlib import Path

from tools.public_lineage_gate import (
    EXPECTED_ROOT,
    HEAD_ENV,
    LineageFacts,
    evaluate_lineage,
    resolve_target_ref,
)


ROOT = Path(__file__).resolve().parents[1]
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def _facts(
    *,
    roots: tuple[str, ...] = (EXPECTED_ROOT,),
    root_parents: tuple[str, ...] = (),
    author_email: str = "137753702+kymuco@users.noreply.github.com",
    committer_email: str = "137753702+kymuco@users.noreply.github.com",
    owner_identity_violations: tuple[str, ...] = (),
) -> LineageFacts:
    return LineageFacts(
        roots=roots,
        root_parents=root_parents,
        author_email=author_email,
        committer_email=committer_email,
        owner_identity_violations=owner_identity_violations,
    )


def test_public_lineage_gate_accepts_frozen_clean_root():
    assert evaluate_lineage(_facts()) == ()


def test_public_lineage_gate_rejects_wrong_or_multiple_roots():
    wrong_root = "0" * 40
    failures = evaluate_lineage(_facts(roots=(EXPECTED_ROOT, wrong_root)))

    assert failures
    assert "exactly one root" in failures[0]


def test_public_lineage_gate_rejects_root_with_parent():
    failures = evaluate_lineage(_facts(root_parents=("1" * 40,)))

    assert failures
    assert any("zero parents" in failure for failure in failures)


def test_public_lineage_gate_rejects_personal_root_email_metadata():
    failures = evaluate_lineage(
        _facts(
            author_email="author@example.com",
            committer_email="committer@example.com",
        )
    )

    assert len(failures) == 2
    assert any("author email" in failure for failure in failures)
    assert any("committer email" in failure for failure in failures)


def test_public_lineage_gate_rejects_owner_commit_without_noreply_identity():
    failures = evaluate_lineage(
        _facts(owner_identity_violations=("abc123:author:Ikymuco",))
    )

    assert failures
    assert any("owner-authored" in failure for failure in failures)
    assert all("@" not in failure for failure in failures)


def test_target_ref_defaults_to_head_and_accepts_explicit_pr_head(monkeypatch):
    monkeypatch.delenv(HEAD_ENV, raising=False)
    assert resolve_target_ref() == "HEAD"

    monkeypatch.setenv(HEAD_ENV, EXPECTED_ROOT)
    assert resolve_target_ref() == EXPECTED_ROOT

    assert resolve_target_ref("  branch-head  ") == "branch-head"


def test_ci_fetches_complete_history_and_checks_pr_head_before_tests():
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")

    assert "actions/checkout@v7" in workflow
    assert "fetch-depth: 0" in workflow
    assert "python tools/public_lineage_gate.py" in workflow
    assert "actions/setup-python@v7" in workflow
    assert (
        "PUBLIC_LINEAGE_HEAD_SHA: "
        "${{ github.event.pull_request.head.sha || github.sha }}"
    ) in workflow

    lineage_position = workflow.index("python tools/public_lineage_gate.py")
    pytest_position = workflow.index("python -m pytest -q")
    assert lineage_position < pytest_position
