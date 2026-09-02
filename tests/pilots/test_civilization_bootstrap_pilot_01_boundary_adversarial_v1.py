from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import shutil

import pytest

from capability_lab.epistemics import CapabilitySubjectRef
from capability_lab.pilots.civilization_bootstrap_01 import (
    ARTIFACTS_DIRNAME,
    CAPTURES_DIRNAME,
    PRIVATE_NOTICE_FILENAME,
    PROTOCOL_SNAPSHOT_FILENAME,
    WORKSPACE_MANIFEST_FILENAME,
    CaptureOriginKind,
    InvalidPrivatePilotWorkspace,
    PilotCaptureKind,
    PilotCaptureRecord,
    build_civilization_bootstrap_pilot_01_protocol_v1,
    initialize_private_workspace,
    pilot_capture_to_json,
    pilot_protocol_to_json,
    record_artifact_capture,
    record_text_capture,
    validate_private_workspace,
)
from capability_lab.pilots.civilization_bootstrap_01.run import build_parser, main


T0 = datetime(2026, 8, 16, 12, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("pilot_subject")
PROTOCOL_SHA256_V1 = "aa0c601450ed28516fa08af60ca92501180fde0483d453b83962df2689e5bd7c"


def _workspace(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    root = repo / ".local" / "pilots" / "cb01"
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


def _symlink_or_skip(link: Path, target: Path, *, target_is_directory: bool) -> None:
    try:
        link.symlink_to(target, target_is_directory=target_is_directory)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlink creation unavailable on this platform: {exc}")


def test_frozen_protocol_revision_has_exact_canonical_regression_fingerprint() -> None:
    raw = pilot_protocol_to_json(build_civilization_bootstrap_pilot_01_protocol_v1()).encode("utf-8")
    assert hashlib.sha256(raw).hexdigest() == PROTOCOL_SHA256_V1


def test_protocol_fingerprint_is_regression_identity_not_authentication() -> None:
    # A local SHA-256 freezes the exact serialized @1 bytes for regression review.
    # It does not identify an issuer, authenticate a historical archive, or prove who supplied a workspace.
    assert len(PROTOCOL_SHA256_V1) == 64
    assert set(PROTOCOL_SHA256_V1) <= set("0123456789abcdef")


def test_workspace_rejects_symlinked_capture_directory(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    outside = tmp_path / "outside_captures"
    outside.mkdir()
    capture_dir = root / CAPTURES_DIRNAME
    capture_dir.rmdir()
    _symlink_or_skip(capture_dir, outside, target_is_directory=True)

    with pytest.raises(InvalidPrivatePilotWorkspace, match="captures directory.*non-symlink"):
        validate_private_workspace(root)


def test_workspace_rejects_symlinked_artifact_directory(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    outside = tmp_path / "outside_artifacts"
    outside.mkdir()
    artifact_dir = root / ARTIFACTS_DIRNAME
    artifact_dir.rmdir()
    _symlink_or_skip(artifact_dir, outside, target_is_directory=True)

    with pytest.raises(InvalidPrivatePilotWorkspace, match="artifacts directory.*non-symlink"):
        validate_private_workspace(root)


def test_workspace_rejects_symlinked_metadata_file(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    manifest = root / WORKSPACE_MANIFEST_FILENAME
    outside = tmp_path / "manifest_copy.json"
    shutil.copyfile(manifest, outside)
    manifest.unlink()
    _symlink_or_skip(manifest, outside, target_is_directory=False)

    with pytest.raises(InvalidPrivatePilotWorkspace, match="workspace manifest.*non-symlink"):
        validate_private_workspace(root)


def test_workspace_rejects_unexpected_top_level_synthetic_or_authority_file(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    (root / "synthetic.json").write_text('{"pretend":"capture"}\n', encoding="utf-8")

    with pytest.raises(InvalidPrivatePilotWorkspace, match="top-level layout must be exact"):
        validate_private_workspace(root)


def test_captures_directory_rejects_hidden_non_json_or_noncanonical_capture(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    (root / CAPTURES_DIRNAME / "hidden.txt").write_text("not a capture", encoding="utf-8")
    with pytest.raises(InvalidPrivatePilotWorkspace, match="only regular canonical JSON capture files"):
        validate_private_workspace(root)

    (root / CAPTURES_DIRNAME / "hidden.txt").unlink()
    capture = record_text_capture(
        root,
        capture_id="conceptual_01",
        probe_id="conceptual_explanation",
        text_content="Participant response.",
        captured_at=T0 + timedelta(minutes=1),
    )
    path = root / CAPTURES_DIRNAME / f"{capture.capture_id}.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    path.write_text(json.dumps(raw, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    with pytest.raises(InvalidPrivatePilotWorkspace, match="canonical deterministic JSON"):
        validate_private_workspace(root)


def test_artifact_capture_cannot_launder_another_capture_artifact_path(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    source_a = tmp_path / "a.txt"
    source_b = tmp_path / "b.txt"
    source_a.write_bytes(b"A")
    source_b.write_bytes(b"BBBB")
    capture_a = record_artifact_capture(
        root,
        capture_id="artifact_a",
        probe_id="execution_artifact",
        source_file=source_a,
        captured_at=T0 + timedelta(minutes=1),
    )
    capture_b = record_artifact_capture(
        root,
        capture_id="artifact_b",
        probe_id="execution_artifact",
        source_file=source_b,
        captured_at=T0 + timedelta(minutes=2),
    )

    path_a = root / CAPTURES_DIRNAME / "artifact_a.json"
    raw_a = json.loads(path_a.read_text(encoding="utf-8"))
    raw_a["artifact"]["relative_path"] = capture_b.artifact.relative_path
    raw_a["artifact"]["original_filename"] = capture_b.artifact.original_filename
    raw_a["artifact"]["byte_size"] = capture_b.artifact.byte_size
    raw_a["artifact"]["sha256"] = capture_b.artifact.sha256
    path_a.write_text(_canonical_json(raw_a), encoding="utf-8")

    with pytest.raises(InvalidPrivatePilotWorkspace, match="canonical capture linkage"):
        validate_private_workspace(root)

    assert capture_a.capture_id == "artifact_a"


def test_orphan_and_extra_artifact_entries_are_rejected(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    orphan = root / ARTIFACTS_DIRNAME / "orphan_capture"
    orphan.mkdir()
    (orphan / "orphan.txt").write_text("unlinked", encoding="utf-8")

    with pytest.raises(InvalidPrivatePilotWorkspace, match="artifact directory closure"):
        validate_private_workspace(root)

    shutil.rmtree(orphan)
    source = tmp_path / "measurement.txt"
    source.write_text("4.98 V", encoding="utf-8")
    capture = record_artifact_capture(
        root,
        capture_id="execution_01",
        probe_id="execution_artifact",
        source_file=source,
        captured_at=T0 + timedelta(minutes=1),
    )
    artifact_dir = root / ARTIFACTS_DIRNAME / capture.capture_id
    (artifact_dir / "extra.txt").write_text("hidden adjacent input", encoding="utf-8")

    with pytest.raises(InvalidPrivatePilotWorkspace, match="must contain exactly"):
        validate_private_workspace(root)


def test_capture_session_subject_protocol_and_timestamp_substitution_fail_closed(tmp_path: Path) -> None:
    fields_and_values = (
        ("session_id", "other_session", "session_id does not match"),
        ("subject_ref", "other_subject", "subject_ref does not match"),
        ("protocol_ref", "civilization_bootstrap:pilot_01_basic_electricity@2", "protocol_ref does not match"),
        ("captured_at", "2026-08-16T11:59:59.000000Z", "captured_at must not precede"),
    )

    for index, (field, value, message) in enumerate(fields_and_values):
        case_root = tmp_path / f"case_{index}"
        case_root.mkdir()
        (case_root / ".git").mkdir()
        root = case_root / ".local" / "cb01"
        initialize_private_workspace(
            root,
            session_id="cb01_session",
            subject_ref=SUBJECT,
            created_at=T0,
        )
        capture = record_text_capture(
            root,
            capture_id="conceptual_01",
            probe_id="conceptual_explanation",
            text_content="Participant response.",
            captured_at=T0 + timedelta(minutes=1),
        )
        path = root / CAPTURES_DIRNAME / f"{capture.capture_id}.json"
        raw = json.loads(path.read_text(encoding="utf-8"))
        raw[field] = value
        path.write_text(_canonical_json(raw), encoding="utf-8")
        with pytest.raises(InvalidPrivatePilotWorkspace, match=message):
            validate_private_workspace(root)


def test_manual_subject_provided_declaration_can_be_structurally_valid_without_authenticating_authorship(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    protocol = build_civilization_bootstrap_pilot_01_protocol_v1()
    manually_constructed = PilotCaptureRecord(
        capture_id="manual_01",
        protocol_ref=protocol.protocol_ref,
        session_id="cb01_session",
        subject_ref=SUBJECT,
        probe_id="conceptual_explanation",
        capture_kind=PilotCaptureKind.TEXT_RESPONSE,
        origin_kind=CaptureOriginKind.SUBJECT_PROVIDED,
        captured_at=T0 + timedelta(minutes=1),
        participant_note="The structural format alone cannot authenticate who authored these bytes.",
        text_content="Externally supplied text with declared subject-provided origin.",
    )
    (root / CAPTURES_DIRNAME / "manual_01.json").write_text(
        pilot_capture_to_json(manually_constructed),
        encoding="utf-8",
    )

    report = validate_private_workspace(root)
    assert report.capture_count == 1
    assert report.capture_complete is False
    assert manually_constructed.origin_kind is CaptureOriginKind.SUBJECT_PROVIDED


def test_incomplete_workspace_validation_is_successful_and_has_no_require_complete_mode(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _workspace(tmp_path)

    assert main(["validate", "--workspace", str(root)]) == 0
    output = capsys.readouterr().out
    assert "capture_complete=false" in output
    assert "missing_required_probe_ids=" in output

    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["validate", "--workspace", str(root), "--require-complete"])


def test_private_notice_and_protocol_snapshot_are_frozen_workspace_inputs(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    notice = root / PRIVATE_NOTICE_FILENAME
    notice.write_text(notice.read_text(encoding="utf-8") + "tampered\n", encoding="utf-8")
    with pytest.raises(InvalidPrivatePilotWorkspace, match="notice does not equal frozen"):
        validate_private_workspace(root)

    # Re-create an independent case for protocol content substitution under the same ref.
    second = tmp_path / "second"
    second.mkdir()
    (second / ".git").mkdir()
    root2 = second / ".local" / "cb01"
    initialize_private_workspace(root2, session_id="cb01_session", subject_ref=SUBJECT, created_at=T0)
    protocol_path = root2 / PROTOCOL_SNAPSHOT_FILENAME
    raw = json.loads(protocol_path.read_text(encoding="utf-8"))
    raw["description"] = "Different protocol semantics under the same exact ref."
    protocol_path.write_text(_canonical_json(raw), encoding="utf-8")
    with pytest.raises(InvalidPrivatePilotWorkspace, match="does not equal frozen Pilot 01 protocol"):
        validate_private_workspace(root2)
