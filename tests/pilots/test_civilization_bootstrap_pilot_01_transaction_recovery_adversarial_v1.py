from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import shutil

import pytest

from capability_lab.epistemics import CapabilitySubjectRef
from capability_lab.pilots.civilization_bootstrap_01 import (
    ARTIFACTS_DIRNAME,
    CAPTURES_DIRNAME,
    InvalidPrivatePilotWorkspace,
    initialize_private_workspace,
    record_artifact_capture,
    record_text_capture,
    validate_private_workspace,
)
from capability_lab.pilots.civilization_bootstrap_01 import transactional


T0 = datetime(2026, 8, 16, 13, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("pilot_subject")


def _repo_workspace(tmp_path: Path, name: str = "cb01") -> Path:
    repo = tmp_path / f"repo_{name}"
    repo.mkdir()
    (repo / ".git").mkdir()
    root = repo / ".local" / "pilots" / name
    initialize_private_workspace(
        root,
        session_id="cb01_session",
        subject_ref=SUBJECT,
        created_at=T0,
    )
    return root


def _canonical_json(data: object) -> str:
    return json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ) + "\n"


def _record_conceptual(root: Path, *, capture_id: str = "conceptual_01") -> None:
    record_text_capture(
        root,
        capture_id=capture_id,
        probe_id="conceptual_explanation",
        text_content="Participant response about voltage, current, and resistance.",
        captured_at=T0 + timedelta(minutes=1),
    )


def test_initialization_failure_never_publishes_partial_final_workspace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    root = repo / ".local" / "pilots" / "cb01"

    original = transactional._populate_staging_workspace

    def fail_after_partial_staging(staging: Path, **kwargs) -> None:
        (staging / CAPTURES_DIRNAME).mkdir()
        (staging / "partial.txt").write_text("interrupted init", encoding="utf-8")
        raise OSError("injected initialization interruption")

    monkeypatch.setattr(transactional, "_populate_staging_workspace", fail_after_partial_staging)
    with pytest.raises(OSError, match="injected initialization interruption"):
        initialize_private_workspace(
            root,
            session_id="cb01_session",
            subject_ref=SUBJECT,
            created_at=T0,
        )

    assert not root.exists()
    assert list((repo / ".local" / "pilots").glob(".cb01.init-*.pilot01-tmp")) == []

    monkeypatch.setattr(transactional, "_populate_staging_workspace", original)
    initialize_private_workspace(
        root,
        session_id="cb01_session",
        subject_ref=SUBJECT,
        created_at=T0,
    )
    assert validate_private_workspace(root).capture_count == 0


def test_text_capture_publication_failure_leaves_no_partial_final_capture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _repo_workspace(tmp_path)

    def fail_link(_source, _destination) -> None:
        raise OSError("injected atomic-link failure")

    monkeypatch.setattr(transactional.os, "link", fail_link)
    with pytest.raises(InvalidPrivatePilotWorkspace, match="cannot atomically publish"):
        _record_conceptual(root)

    assert list((root / CAPTURES_DIRNAME).iterdir()) == []
    report = validate_private_workspace(root)
    assert report.capture_count == 0
    assert report.capture_complete is False


def test_handled_artifact_capture_publication_failure_rolls_back_runner_owned_destination(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _repo_workspace(tmp_path)
    source = tmp_path / "measurement.txt"
    source.write_text("4.98 V", encoding="utf-8")

    def fail_capture_publish(_source: Path, _destination: Path) -> None:
        raise InvalidPrivatePilotWorkspace("injected capture publication failure")

    monkeypatch.setattr(transactional, "_atomic_publish_existing_file", fail_capture_publish)
    with pytest.raises(InvalidPrivatePilotWorkspace, match="injected capture publication failure"):
        record_artifact_capture(
            root,
            capture_id="execution_01",
            probe_id="execution_artifact",
            source_file=source,
            captured_at=T0 + timedelta(minutes=1),
        )

    assert not (root / ARTIFACTS_DIRNAME / "execution_01").exists()
    assert not (root / CAPTURES_DIRNAME / "execution_01.json").exists()
    assert validate_private_workspace(root).artifact_count == 0


def test_abrupt_artifact_pair_crash_window_is_fail_closed_and_blocks_next_append(tmp_path: Path) -> None:
    root = _repo_workspace(tmp_path)
    crash_orphan = root / ARTIFACTS_DIRNAME / "execution_crash"
    crash_orphan.mkdir()
    (crash_orphan / "measurement.txt").write_text("staged bytes published before capture JSON", encoding="utf-8")

    with pytest.raises(InvalidPrivatePilotWorkspace, match="artifact directory closure"):
        validate_private_workspace(root)

    with pytest.raises(InvalidPrivatePilotWorkspace, match="artifact directory closure"):
        _record_conceptual(root)

    assert not (root / CAPTURES_DIRNAME / "conceptual_01.json").exists()


def test_append_after_existing_capture_corruption_is_rejected_before_new_publication(tmp_path: Path) -> None:
    root = _repo_workspace(tmp_path)
    _record_conceptual(root)
    conceptual = root / CAPTURES_DIRNAME / "conceptual_01.json"
    conceptual.write_text(conceptual.read_text(encoding="utf-8") + "corruption", encoding="utf-8")

    with pytest.raises(InvalidPrivatePilotWorkspace, match="invalid capture file|canonical deterministic JSON"):
        record_text_capture(
            root,
            capture_id="calculation_01",
            probe_id="calculation_work",
            text_content="This must not append over a corrupt snapshot.",
            captured_at=T0 + timedelta(minutes=2),
        )

    assert not (root / CAPTURES_DIRNAME / "calculation_01.json").exists()


def test_append_after_existing_artifact_corruption_is_rejected_before_new_publication(tmp_path: Path) -> None:
    root = _repo_workspace(tmp_path)
    source = tmp_path / "measurement.txt"
    source.write_text("4.98 V", encoding="utf-8")
    capture = record_artifact_capture(
        root,
        capture_id="execution_01",
        probe_id="execution_artifact",
        source_file=source,
        captured_at=T0 + timedelta(minutes=1),
    )
    artifact_path = root / capture.artifact.relative_path
    artifact_path.write_text("tampered after capture", encoding="utf-8")

    with pytest.raises(InvalidPrivatePilotWorkspace, match="byte_size|sha256"):
        _record_conceptual(root)

    assert not (root / CAPTURES_DIRNAME / "conceptual_01.json").exists()


def test_required_probe_has_one_capture_geometry_not_multiple_attempts_hidden_as_one_probe(tmp_path: Path) -> None:
    root = _repo_workspace(tmp_path)
    _record_conceptual(root, capture_id="conceptual_01")

    with pytest.raises(InvalidPrivatePilotWorkspace, match="at most one capture"):
        record_text_capture(
            root,
            capture_id="conceptual_02",
            probe_id="conceptual_explanation",
            text_content="Second response cannot silently coexist under the same required probe.",
            captured_at=T0 + timedelta(minutes=2),
        )

    assert not (root / CAPTURES_DIRNAME / "conceptual_02.json").exists()


def test_manual_duplicate_required_probe_geometry_invalidates_workspace(tmp_path: Path) -> None:
    root = _repo_workspace(tmp_path)
    _record_conceptual(root, capture_id="conceptual_01")
    first_path = root / CAPTURES_DIRNAME / "conceptual_01.json"
    raw = json.loads(first_path.read_text(encoding="utf-8"))
    raw["capture_id"] = "conceptual_02"
    raw["captured_at"] = "2026-08-16T13:02:00.000000Z"
    (root / CAPTURES_DIRNAME / "conceptual_02.json").write_text(
        _canonical_json(raw),
        encoding="utf-8",
    )

    with pytest.raises(InvalidPrivatePilotWorkspace, match="at most one capture"):
        validate_private_workspace(root)


def test_optional_execution_preserves_plural_text_and_file_captures(tmp_path: Path) -> None:
    root = _repo_workspace(tmp_path)
    record_text_capture(
        root,
        capture_id="execution_note_01",
        probe_id="execution_artifact",
        text_content="Participant measurement notes, part one.",
        captured_at=T0 + timedelta(minutes=1),
    )
    record_text_capture(
        root,
        capture_id="execution_note_02",
        probe_id="execution_artifact",
        text_content="Participant measurement notes, part two.",
        captured_at=T0 + timedelta(minutes=2),
    )
    source_a = tmp_path / "measurement_a.txt"
    source_b = tmp_path / "measurement_b.txt"
    source_a.write_text("4.98 V", encoding="utf-8")
    source_b.write_text("9.01 mA", encoding="utf-8")
    record_artifact_capture(
        root,
        capture_id="execution_file_01",
        probe_id="execution_artifact",
        source_file=source_a,
        captured_at=T0 + timedelta(minutes=3),
    )
    record_artifact_capture(
        root,
        capture_id="execution_file_02",
        probe_id="execution_artifact",
        source_file=source_b,
        captured_at=T0 + timedelta(minutes=4),
    )

    report = validate_private_workspace(root)
    assert report.capture_count == 4
    assert report.artifact_count == 2
    assert report.captured_probe_ids == ("execution_artifact",)


def test_double_read_validation_detects_mutation_during_validation_window(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _repo_workspace(tmp_path)
    _record_conceptual(root)
    capture_path = root / CAPTURES_DIRNAME / "conceptual_01.json"
    original_fingerprint = transactional._workspace_snapshot_sha256
    calls = 0

    def mutate_after_first_fingerprint(path: Path) -> str:
        nonlocal calls
        digest = original_fingerprint(path)
        calls += 1
        if calls == 1:
            raw = json.loads(capture_path.read_text(encoding="utf-8"))
            raw["text_content"] = "A concurrent canonical rewrite during validation."
            capture_path.write_text(_canonical_json(raw), encoding="utf-8")
        return digest

    monkeypatch.setattr(transactional, "_workspace_snapshot_sha256", mutate_after_first_fingerprint)
    with pytest.raises(InvalidPrivatePilotWorkspace, match="changed during validation"):
        validate_private_workspace(root)


def test_validation_report_is_snapshot_identity_not_a_lock_against_later_mutation(tmp_path: Path) -> None:
    root = _repo_workspace(tmp_path)
    _record_conceptual(root)
    before = validate_private_workspace(root)

    capture_path = root / CAPTURES_DIRNAME / "conceptual_01.json"
    raw = json.loads(capture_path.read_text(encoding="utf-8"))
    raw["text_content"] = "Canonical content changed after the earlier validation returned."
    capture_path.write_text(_canonical_json(raw), encoding="utf-8")

    after = validate_private_workspace(root)
    assert before.snapshot_sha256 != after.snapshot_sha256
    assert before.capture_count == after.capture_count == 1


def test_copy_after_validation_must_be_revalidated_and_compared_to_expected_snapshot(tmp_path: Path) -> None:
    root = _repo_workspace(tmp_path)
    _record_conceptual(root)
    expected = validate_private_workspace(root)

    capture_path = root / CAPTURES_DIRNAME / "conceptual_01.json"
    raw = json.loads(capture_path.read_text(encoding="utf-8"))
    raw["text_content"] = "Mutation after validation but before the caller copies the workspace."
    capture_path.write_text(_canonical_json(raw), encoding="utf-8")

    copied = tmp_path / "copied_workspace"
    shutil.copytree(root, copied)
    copied_report = validate_private_workspace(copied)

    assert copied_report.snapshot_sha256 != expected.snapshot_sha256
    assert copied_report.capture_count == expected.capture_count


def test_byte_equivalent_copy_replays_to_same_workspace_snapshot_fingerprint(tmp_path: Path) -> None:
    root = _repo_workspace(tmp_path)
    _record_conceptual(root)
    source = tmp_path / "measurement.txt"
    source.write_text("4.98 V", encoding="utf-8")
    record_artifact_capture(
        root,
        capture_id="execution_01",
        probe_id="execution_artifact",
        source_file=source,
        captured_at=T0 + timedelta(minutes=2),
    )
    original = validate_private_workspace(root)

    copied = tmp_path / "byte_equivalent_copy"
    shutil.copytree(root, copied)
    replay = validate_private_workspace(copied)

    assert replay.snapshot_sha256 == original.snapshot_sha256
    assert replay.session_id == original.session_id
    assert replay.capture_count == original.capture_count
    assert replay.artifact_count == original.artifact_count


def test_independent_deterministic_replay_with_same_declared_records_and_bytes_has_same_fingerprint(
    tmp_path: Path,
) -> None:
    source = tmp_path / "measurement.txt"
    source.write_text("4.98 V", encoding="utf-8")
    roots: list[Path] = []

    for index in range(2):
        root = _repo_workspace(tmp_path, name=f"cb01_{index}")
        record_text_capture(
            root,
            capture_id="conceptual_01",
            probe_id="conceptual_explanation",
            text_content="Same participant-declared bytes for deterministic replay.",
            captured_at=T0 + timedelta(minutes=1),
        )
        record_artifact_capture(
            root,
            capture_id="execution_01",
            probe_id="execution_artifact",
            source_file=source,
            captured_at=T0 + timedelta(minutes=2),
        )
        roots.append(root)

    first = validate_private_workspace(roots[0])
    second = validate_private_workspace(roots[1])
    assert first.snapshot_sha256 == second.snapshot_sha256
    assert first.snapshot_sha256 != "0" * 64
    assert len(first.snapshot_sha256) == 64


def test_snapshot_fingerprint_does_not_add_evidence_or_history_authority() -> None:
    report_fields = set(transactional.PilotWorkspaceValidationReport.__dataclass_fields__)
    assert "snapshot_sha256" in report_fields
    assert "evidence_id" not in report_fields
    assert "evaluation_id" not in report_fields
    assert "state_id" not in report_fields
    assert "authenticated_at" not in report_fields
    assert "trusted_timestamp" not in report_fields
