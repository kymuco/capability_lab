from pathlib import Path

import pytest

from capability_lab.pilots.civilization_bootstrap_01.run import build_parser, main


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    return repo


def test_runner_initializes_records_and_validates_real_input_without_generation(tmp_path: Path, capsys) -> None:
    repo = _repo(tmp_path)
    workspace = repo / ".local" / "pilots" / "cb01"
    response = tmp_path / "conceptual.md"
    response.write_text("My own bounded explanation of voltage, current, and resistance.", encoding="utf-8")

    assert main([
        "init",
        "--workspace", str(workspace),
        "--session-id", "cb01_session",
        "--subject-ref", "pilot_subject",
        "--created-at", "2026-08-16T12:00:00+00:00",
    ]) == 0
    capsys.readouterr()

    assert main([
        "record-text",
        "--workspace", str(workspace),
        "--capture-id", "conceptual_01",
        "--probe", "conceptual_explanation",
        "--input", str(response),
        "--captured-at", "2026-08-16T12:01:00+00:00",
        "--tool", "plain text editor",
    ]) == 0
    capsys.readouterr()

    assert main(["validate", "--workspace", str(workspace)]) == 0
    output = capsys.readouterr().out
    assert "capture_count=1" in output
    assert "capture_complete=false" in output
    assert "calculation_work" in output
    assert "diagnosis_reasoning" in output

    with pytest.raises(SystemExit):
        build_parser().parse_args([
            "validate", "--workspace", str(workspace), "--require-complete"
        ])


def test_runner_surface_contains_no_generate_grade_evaluate_demo_or_sample_command() -> None:
    parser = build_parser()
    for forbidden in ("generate", "grade", "evaluate", "demo", "sample"):
        with pytest.raises(SystemExit):
            parser.parse_args([forbidden])


def test_show_protocol_is_public_protocol_only_and_does_not_create_workspace(tmp_path: Path, capsys) -> None:
    before = set(tmp_path.iterdir())
    assert main(["show-protocol"]) == 0
    output = capsys.readouterr().out.lower()
    after = set(tmp_path.iterdir())

    assert before == after
    assert "civilization_bootstrap:pilot_01_basic_electricity@1" in output
    assert "participant_prompt" in output
    assert "expected_answer" not in output
    assert "evaluation_policy" not in output
    assert "personalcapabilitystate" not in output
