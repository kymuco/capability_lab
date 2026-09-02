"""Transactional public mutation and stable-snapshot boundary for Pilot 01.

The low-level workspace module owns structural parsing and validation. This
module is the public mutation surface: it pre-validates a complete workspace,
uses staging before publication, freezes required-probe capture geometry, and
returns a stable content fingerprint after a double-read validation pass.

The guarantees are deliberately bounded. A returned validation report is not a
lock or authenticated history, and an artifact capture spans two final paths,
so an abrupt process/host failure can still leave a fail-closed orphan state.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import os
from pathlib import Path
import shutil
import tempfile

from capability_lab.epistemics import CapabilitySubjectRef

from .capture import CaptureOriginKind, CapturedArtifact, PilotCaptureRecord
from .protocol import (
    PilotCaptureKind,
    PilotProbeRequirement,
    PilotProtocol,
    build_civilization_bootstrap_pilot_01_protocol_v1,
)
from .serialization import (
    pilot_capture_to_json,
    pilot_protocol_to_json,
    workspace_manifest_to_json,
)
from . import workspace as _workspace


InvalidPrivatePilotWorkspace = _workspace.InvalidPrivatePilotWorkspace
PilotWorkspaceError = _workspace.PilotWorkspaceError
PrivatePilotWorkspaceManifest = _workspace.PrivatePilotWorkspaceManifest

ARTIFACTS_DIRNAME = _workspace.ARTIFACTS_DIRNAME
CAPTURES_DIRNAME = _workspace.CAPTURES_DIRNAME
PRIVATE_NOTICE = _workspace.PRIVATE_NOTICE
PRIVATE_NOTICE_FILENAME = _workspace.PRIVATE_NOTICE_FILENAME
PROTOCOL_SNAPSHOT_FILENAME = _workspace.PROTOCOL_SNAPSHOT_FILENAME
WORKSPACE_MANIFEST_FILENAME = _workspace.WORKSPACE_MANIFEST_FILENAME

_SNAPSHOT_DOMAIN = b"capability_lab/civilization_bootstrap_pilot_01_workspace_snapshot@1\x00"


@dataclass(frozen=True, slots=True)
class PilotWorkspaceValidationReport:
    session_id: str
    capture_count: int
    artifact_count: int
    captured_probe_ids: tuple[str, ...]
    missing_required_probe_ids: tuple[str, ...]
    snapshot_sha256: str

    @property
    def capture_complete(self) -> bool:
        return not self.missing_required_probe_ids


def _write_staged_text(path: Path, content: str) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())


def _atomic_publish_existing_file(staged_path: Path, final_path: Path) -> None:
    """Atomically create one final file without replacing an existing path."""

    try:
        os.link(staged_path, final_path)
    except FileExistsError as exc:
        raise InvalidPrivatePilotWorkspace(
            f"refusing to overwrite existing file: {final_path}"
        ) from exc
    except OSError as exc:
        raise InvalidPrivatePilotWorkspace(
            f"cannot atomically publish file {final_path.name}: {exc}"
        ) from exc


def _atomic_publish_new_text(final_path: Path, content: str, *, staging_parent: Path) -> None:
    staging_parent.mkdir(parents=True, exist_ok=True)
    fd, raw_temp = tempfile.mkstemp(
        prefix=f".{final_path.name}.",
        suffix=".pilot01-tmp",
        dir=staging_parent,
        text=True,
    )
    temp_path = Path(raw_temp)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        _atomic_publish_existing_file(temp_path, final_path)
    finally:
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass


def _populate_staging_workspace(
    staging: Path,
    *,
    manifest: PrivatePilotWorkspaceManifest,
    protocol: PilotProtocol,
) -> None:
    (staging / CAPTURES_DIRNAME).mkdir()
    (staging / ARTIFACTS_DIRNAME).mkdir()
    _write_staged_text(
        staging / WORKSPACE_MANIFEST_FILENAME,
        workspace_manifest_to_json(manifest),
    )
    _write_staged_text(
        staging / PROTOCOL_SNAPSHOT_FILENAME,
        pilot_protocol_to_json(protocol),
    )
    _write_staged_text(staging / PRIVATE_NOTICE_FILENAME, PRIVATE_NOTICE)


def initialize_private_workspace(
    workspace: str | Path,
    *,
    session_id: str,
    subject_ref: CapabilitySubjectRef,
    created_at: datetime,
    protocol: PilotProtocol | None = None,
) -> Path:
    """Publish a complete empty workspace by staging then renaming one directory."""

    root = _workspace.validate_private_workspace_location(workspace)
    if not isinstance(subject_ref, CapabilitySubjectRef):
        raise InvalidPrivatePilotWorkspace("subject_ref must be CapabilitySubjectRef")
    frozen_protocol = protocol or build_civilization_bootstrap_pilot_01_protocol_v1()
    expected = build_civilization_bootstrap_pilot_01_protocol_v1()
    if frozen_protocol != expected:
        raise InvalidPrivatePilotWorkspace("Pilot 01 workspace must use the frozen Pilot 01 protocol")
    manifest = PrivatePilotWorkspaceManifest(
        protocol_ref=frozen_protocol.protocol_ref,
        session_id=session_id,
        subject_ref=subject_ref,
        created_at=created_at,
    )

    if root.exists():
        if root.is_symlink() or not root.is_dir():
            raise InvalidPrivatePilotWorkspace("workspace path must be a real directory")
        if any(root.iterdir()):
            raise InvalidPrivatePilotWorkspace("workspace directory must be empty on initialization")
        root.rmdir()

    root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(
            prefix=f".{root.name}.init-",
            suffix=".pilot01-tmp",
            dir=root.parent,
        )
    )
    try:
        _populate_staging_workspace(
            staging,
            manifest=manifest,
            protocol=frozen_protocol,
        )
        try:
            os.rename(staging, root)
        except OSError as exc:
            raise InvalidPrivatePilotWorkspace(
                f"cannot publish initialized private workspace: {exc}"
            ) from exc
        validate_private_workspace(root)
        return root
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


def _validate_capture_geometry(
    captures: tuple[PilotCaptureRecord, ...],
    *,
    protocol: PilotProtocol,
) -> None:
    required_seen: dict[str, str] = {}
    for capture in captures:
        probe = protocol.probe(capture.probe_id)
        if probe.requirement is not PilotProbeRequirement.REQUIRED:
            continue
        previous = required_seen.get(capture.probe_id)
        if previous is not None:
            raise InvalidPrivatePilotWorkspace(
                "Pilot 01 required probes allow at most one capture: "
                f"{capture.probe_id} is represented by both {previous} and {capture.capture_id}"
            )
        required_seen[capture.probe_id] = capture.capture_id


def _workspace_snapshot_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    digest.update(_SNAPSHOT_DOMAIN)
    entries = sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix())
    for path in entries:
        if path.is_symlink():
            raise InvalidPrivatePilotWorkspace("workspace snapshot must not traverse symlinks")
        relative = path.relative_to(root).as_posix().encode("utf-8")
        if path.is_dir():
            kind = b"D"
            payload = b""
        elif path.is_file():
            kind = b"F"
            try:
                payload = path.read_bytes()
            except OSError as exc:
                raise InvalidPrivatePilotWorkspace(
                    f"cannot read workspace snapshot entry {path.name}: {exc}"
                ) from exc
        else:
            raise InvalidPrivatePilotWorkspace("workspace snapshot contains unsupported filesystem entry")
        digest.update(kind)
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def _validated_snapshot_once(
    workspace: str | Path,
) -> tuple[_workspace.PilotWorkspaceValidationReport, str]:
    report = _workspace.validate_private_workspace(workspace)
    root, _manifest, protocol = _workspace.load_private_workspace(workspace)
    capture_set = _workspace.load_capture_set(root)
    _validate_capture_geometry(capture_set.captures, protocol=protocol)
    return report, _workspace_snapshot_sha256(root)


def validate_private_workspace(workspace: str | Path) -> PilotWorkspaceValidationReport:
    """Validate twice and return a deterministic content fingerprint for the stable read."""

    first_report, first_digest = _validated_snapshot_once(workspace)
    second_report, second_digest = _validated_snapshot_once(workspace)
    if first_report != second_report or first_digest != second_digest:
        raise InvalidPrivatePilotWorkspace("private workspace changed during validation")
    return PilotWorkspaceValidationReport(
        session_id=second_report.session_id,
        capture_count=second_report.capture_count,
        artifact_count=second_report.artifact_count,
        captured_probe_ids=second_report.captured_probe_ids,
        missing_required_probe_ids=second_report.missing_required_probe_ids,
        snapshot_sha256=second_digest,
    )


def _prepare_capture_append(
    workspace: str | Path,
    *,
    probe_id: str,
    capture_kind: PilotCaptureKind,
) -> tuple[Path, PrivatePilotWorkspaceManifest, PilotProtocol]:
    # Full closure must be green before a mutation starts. Metadata-only loading is
    # not enough because it would permit append-after-corruption.
    validate_private_workspace(workspace)
    root, manifest, protocol = _workspace.load_private_workspace(workspace)
    probe = protocol.probe(probe_id)
    if capture_kind not in probe.allowed_capture_kinds:
        raise InvalidPrivatePilotWorkspace(
            f"capture kind {capture_kind.value} is not allowed for probe {probe_id}"
        )
    if probe.requirement is PilotProbeRequirement.REQUIRED:
        existing = _workspace.load_capture_set(root)
        for capture in existing.captures:
            if capture.probe_id == probe_id:
                raise InvalidPrivatePilotWorkspace(
                    "Pilot 01 required probes allow at most one capture: "
                    f"{probe_id} already has capture {capture.capture_id}"
                )
    return root, manifest, protocol


def record_text_capture(
    workspace: str | Path,
    *,
    capture_id: str,
    probe_id: str,
    text_content: str,
    captured_at: datetime,
    declared_tools: tuple[str, ...] = (),
    participant_note: str = "",
) -> PilotCaptureRecord:
    root, manifest, _protocol = _prepare_capture_append(
        workspace,
        probe_id=probe_id,
        capture_kind=PilotCaptureKind.TEXT_RESPONSE,
    )
    capture = PilotCaptureRecord(
        capture_id=capture_id,
        protocol_ref=manifest.protocol_ref,
        session_id=manifest.session_id,
        subject_ref=manifest.subject_ref,
        probe_id=probe_id,
        capture_kind=PilotCaptureKind.TEXT_RESPONSE,
        origin_kind=CaptureOriginKind.SUBJECT_PROVIDED,
        captured_at=captured_at,
        declared_tools=declared_tools,
        participant_note=participant_note,
        text_content=text_content,
    )
    if capture.captured_at < manifest.created_at:
        raise InvalidPrivatePilotWorkspace("capture captured_at must not precede workspace created_at")
    final_path = root / CAPTURES_DIRNAME / f"{capture.capture_id}.json"
    _atomic_publish_new_text(
        final_path,
        pilot_capture_to_json(capture),
        staging_parent=root.parent,
    )
    # Revalidate the exact post-write state. A concurrent mutation may still make
    # the operation fail after publication; PR10.0 does not claim linearizable
    # multi-process transactions.
    validate_private_workspace(root)
    return capture


def record_artifact_capture(
    workspace: str | Path,
    *,
    capture_id: str,
    probe_id: str,
    source_file: str | Path,
    captured_at: datetime,
    declared_tools: tuple[str, ...] = (),
    participant_note: str = "",
) -> PilotCaptureRecord:
    root, manifest, _protocol = _prepare_capture_append(
        workspace,
        probe_id=probe_id,
        capture_kind=PilotCaptureKind.FILE_ARTIFACT,
    )
    capture_key = _workspace._capture_file_key(capture_id)
    final_capture_path = root / CAPTURES_DIRNAME / f"{capture_key}.json"
    final_artifact_dir = root / ARTIFACTS_DIRNAME / capture_key
    if final_capture_path.exists():
        raise InvalidPrivatePilotWorkspace(f"refusing to overwrite existing file: {final_capture_path}")
    if final_artifact_dir.exists():
        raise InvalidPrivatePilotWorkspace(
            f"artifact destination already exists for capture: {capture_key}"
        )

    source_raw = Path(source_file)
    _workspace._reject_existing_symlink_components(source_raw, "artifact source path")
    try:
        source = source_raw.resolve(strict=True)
    except FileNotFoundError as exc:
        raise InvalidPrivatePilotWorkspace("artifact source file does not exist") from exc
    if not source.is_file():
        raise InvalidPrivatePilotWorkspace("artifact source must be a regular file")
    filename = _workspace._artifact_filename(source.name)

    staging = Path(
        tempfile.mkdtemp(
            prefix=f".{root.name}.{capture_key}.artifact-",
            suffix=".pilot01-tmp",
            dir=root.parent,
        )
    )
    artifact_published = False
    capture_published = False
    try:
        staged_artifact_dir = staging / "artifact"
        staged_artifact_dir.mkdir()
        staged_artifact = staged_artifact_dir / filename
        shutil.copyfile(source, staged_artifact)
        artifact = CapturedArtifact(
            relative_path=f"{ARTIFACTS_DIRNAME}/{capture_key}/{filename}",
            original_filename=filename,
            byte_size=staged_artifact.stat().st_size,
            sha256=_workspace._sha256(staged_artifact),
        )
        capture = PilotCaptureRecord(
            capture_id=capture_key,
            protocol_ref=manifest.protocol_ref,
            session_id=manifest.session_id,
            subject_ref=manifest.subject_ref,
            probe_id=probe_id,
            capture_kind=PilotCaptureKind.FILE_ARTIFACT,
            origin_kind=CaptureOriginKind.SUBJECT_PROVIDED,
            captured_at=captured_at,
            declared_tools=declared_tools,
            participant_note=participant_note,
            artifact=artifact,
        )
        if capture.captured_at < manifest.created_at:
            raise InvalidPrivatePilotWorkspace("capture captured_at must not precede workspace created_at")
        staged_capture = staging / "capture.json"
        _write_staged_text(staged_capture, pilot_capture_to_json(capture))

        try:
            os.rename(staged_artifact_dir, final_artifact_dir)
        except OSError as exc:
            raise InvalidPrivatePilotWorkspace(
                f"cannot publish artifact directory for capture {capture_key}: {exc}"
            ) from exc
        artifact_published = True
        _atomic_publish_existing_file(staged_capture, final_capture_path)
        capture_published = True
        validate_private_workspace(root)
        return capture
    except Exception:
        # Handled failures before capture publication roll back the runner-owned
        # artifact destination. An abrupt process/host failure between the two
        # final publications cannot run this handler and remains intentionally
        # fail-closed as an orphan artifact directory.
        if artifact_published and not capture_published and not final_capture_path.exists():
            shutil.rmtree(final_artifact_dir, ignore_errors=True)
        raise
    finally:
        shutil.rmtree(staging, ignore_errors=True)
