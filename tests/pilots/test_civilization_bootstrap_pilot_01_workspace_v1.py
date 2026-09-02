from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from capability_lab.epistemics import CapabilitySubjectRef
from capability_lab.pilots.civilization_bootstrap_01 import (
    ARTIFACTS_DIRNAME,
    CAPTURES_DIRNAME,
    PRIVATE_NOTICE_FILENAME,
    PROTOCOL_SNAPSHOT_FILENAME,
    WORKSPACE_MANIFEST_FILENAME,
    InvalidPrivatePilotWorkspace,
    initialize_private_workspace,
    load_capture_set,
    load_private_workspace,
    record_artifact_capture,
    record_text_capture,
    validate_private_workspace,
    validate_private_workspace_location,
)


T0 = datetime(2026, 8, 16, 12, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("pilot_subject")


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    return repo


def _workspace(tmp_path: Path) -> Path:
    repo = _repo(tmp_path)
    root = repo / ".local" / "pilots" / "cb01"
    initialize_private_workspace(
        root,
        session_id="cb01_session",
        subject_ref=SUBJECT,
        created_at=T0,
    )
    return root


def test_in_repo_workspace_must_live_below_dot_local_but_external_workspace_is_allowed(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    with pytest.raises(InvalidPrivatePilotWorkspace, match="below '<repo>/.local/'"):
        validate_private_workspace_location(repo / "pilot_data" / "cb01")
    with pytest.raises(InvalidPrivatePilotWorkspace, match="below '<repo>/.local/'"):
        validate_private_workspace_location(repo / ".local")

    allowed = validate_private_workspace_location(repo / ".local" / "pilots" / "cb01")
    assert allowed == (repo / ".local" / "pilots" / "cb01").resolve()

    external = tmp_path / "external_private_workspace"
    assert validate_private_workspace_location(external) == external.resolve()


def test_initialization_creates_only_empty_private_capture_structure_and_refuses_overwrite(tmp_path: Path) -> None:
    root = _workspace(tmp_path)

    assert {item.name for item in root.iterdir()} == {
        WORKSPACE_MANIFEST_FILENAME,
        PROTOCOL_SNAPSHOT_FILENAME,
        PRIVATE_NOTICE_FILENAME,
        CAPTURES_DIRNAME,
        ARTIFACTS_DIRNAME,
    }
    assert list((root / CAPTURES_DIRNAME).iterdir()) == []
    assert list((root / ARTIFACTS_DIRNAME).iterdir()) == []
    notice = (root / PRIVATE_NOTICE_FILENAME).read_text(encoding="utf-8")
    assert "does not generate participant answers or synthetic evidence" in notice
    assert "not automatically EvidenceRecords" in notice

    with pytest.raises(InvalidPrivatePilotWorkspace, match="must be empty"):
        initialize_private_workspace(
            root,
            session_id="another_session",
            subject_ref=SUBJECT,
            created_at=T0,
        )


def test_required_probe_absence_is_reported_as_incomplete_not_as_failure(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    initial = validate_private_workspace(root)

    assert initial.capture_count == 0
    assert initial.capture_complete is False
    assert initial.missing_required_probe_ids == (
        "conceptual_explanation",
        "calculation_work",
        "diagnosis_reasoning",
    )

    record_text_capture(
        root,
        capture_id="conceptual_01",
        probe_id="conceptual_explanation",
        text_content="A real participant response.",
        captured_at=T0 + timedelta(minutes=1),
    )
    partial = validate_private_workspace(root)
    assert partial.capture_count == 1
    assert partial.capture_complete is False
    assert partial.missing_required_probe_ids == (
        "calculation_work",
        "diagnosis_reasoning",
    )


def test_three_required_text_captures_complete_capture_without_optional_execution(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    for index, probe_id in enumerate(
        ("conceptual_explanation", "calculation_work", "diagnosis_reasoning"),
        start=1,
    ):
        record_text_capture(
            root,
            capture_id=f"capture_{index}",
            probe_id=probe_id,
            text_content=f"Participant response for {probe_id}.",
            captured_at=T0 + timedelta(minutes=index),
        )

    report = validate_private_workspace(root)
    assert report.capture_complete is True
    assert report.missing_required_probe_ids == ()
    assert "execution_artifact" not in report.captured_probe_ids


def test_capture_files_are_append_only_and_canonicalized_by_id(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    record_text_capture(
        root,
        capture_id="z_capture",
        probe_id="conceptual_explanation",
        text_content="First response.",
        captured_at=T0 + timedelta(minutes=1),
    )
    record_text_capture(
        root,
        capture_id="a_capture",
        probe_id="calculation_work",
        text_content="Second response.",
        captured_at=T0 + timedelta(minutes=2),
    )

    captures = load_capture_set(root)
    assert tuple(item.capture_id for item in captures.captures) == ("a_capture", "z_capture")

    with pytest.raises(InvalidPrivatePilotWorkspace, match="refusing to overwrite|at most one capture"):
        record_text_capture(
            root,
            capture_id="z_capture",
            probe_id="conceptual_explanation",
            text_content="Replacement response must not overwrite.",
            captured_at=T0 + timedelta(minutes=3),
        )
    assert "First response." in (root / CAPTURES_DIRNAME / "z_capture.json").read_text(encoding="utf-8")


def test_artifact_capture_preflights_path_key_copies_bytes_and_detects_tampering(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    source = tmp_path / "measurement.txt"
    source.write_bytes(b"meter reading: 4.98 V\n")

    with pytest.raises(InvalidPrivatePilotWorkspace, match="file-key syntax"):
        record_artifact_capture(
            root,
            capture_id="../escape",
            probe_id="execution_artifact",
            source_file=source,
            captured_at=T0 + timedelta(minutes=1),
        )
    assert not (root / "escape").exists()

    capture = record_artifact_capture(
        root,
        capture_id="execution_photo_01",
        probe_id="execution_artifact",
        source_file=source,
        captured_at=T0 + timedelta(minutes=2),
        participant_note="Subject-provided low-voltage measurement note.",
    )
    artifact_path = root / capture.artifact.relative_path
    assert artifact_path.read_bytes() == source.read_bytes()
    assert validate_private_workspace(root).artifact_count == 1

    artifact_path.write_bytes(b"meter reading: 0.00 V\n")
    with pytest.raises(InvalidPrivatePilotWorkspace, match="byte_size|sha256"):
        validate_private_workspace(root)


def test_artifact_kind_mismatch_rolls_back_copied_file(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    source = tmp_path / "photo.bin"
    source.write_bytes(b"binary photo placeholder from subject")

    with pytest.raises(InvalidPrivatePilotWorkspace, match="not allowed for probe"):
        record_artifact_capture(
            root,
            capture_id="wrong_kind_01",
            probe_id="conceptual_explanation",
            source_file=source,
            captured_at=T0 + timedelta(minutes=1),
        )
    assert not (root / ARTIFACTS_DIRNAME / "wrong_kind_01").exists()
    assert not (root / CAPTURES_DIRNAME / "wrong_kind_01.json").exists()


def test_protocol_snapshot_tampering_invalidates_workspace(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    protocol_path = root / PROTOCOL_SNAPSHOT_FILENAME
    original = protocol_path.read_text(encoding="utf-8")
    protocol_path.write_text(original.replace("Basic Electricity", "Tampered Electricity", 1), encoding="utf-8")

    with pytest.raises(InvalidPrivatePilotWorkspace, match="does not equal frozen Pilot 01 protocol"):
        load_private_workspace(root)
