"""Private local workspace boundary for Civilization Bootstrap Pilot 01."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import re
import shutil

from capability_lab.epistemics import CapabilitySubjectRef

from .capture import (
    CaptureOriginKind,
    CapturedArtifact,
    InvalidPilotCapture,
    PilotCaptureRecord,
    PilotCaptureSet,
    validate_capture_file_key,
)
from .protocol import (
    PilotCaptureKind,
    PilotProtocol,
    PilotProtocolRef,
    build_civilization_bootstrap_pilot_01_protocol_v1,
)
from .serialization import (
    PilotSerializationError,
    pilot_capture_from_json,
    pilot_capture_to_json,
    pilot_protocol_from_json,
    pilot_protocol_to_json,
    workspace_manifest_from_json,
    workspace_manifest_to_json,
)


class PilotWorkspaceError(ValueError):
    """Base error for private pilot workspace operations."""


class InvalidPrivatePilotWorkspace(PilotWorkspaceError):
    pass


_SESSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_WINDOWS_RESERVED_FILE_STEMS = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}

WORKSPACE_MANIFEST_FILENAME = "workspace.json"
PROTOCOL_SNAPSHOT_FILENAME = "protocol.json"
PRIVATE_NOTICE_FILENAME = "PRIVATE_WORKSPACE.txt"
CAPTURES_DIRNAME = "captures"
ARTIFACTS_DIRNAME = "artifacts"

_EXPECTED_TOP_LEVEL_NAMES = frozenset(
    {
        WORKSPACE_MANIFEST_FILENAME,
        PROTOCOL_SNAPSHOT_FILENAME,
        PRIVATE_NOTICE_FILENAME,
        CAPTURES_DIRNAME,
        ARTIFACTS_DIRNAME,
    }
)

PRIVATE_NOTICE = """Capability Lab — PRIVATE PILOT WORKSPACE\n\nThis directory may contain private participant responses and artifacts.\n\n- Keep it local unless you intentionally export it.\n- Copying or sharing this directory is a data export.\n- Captures are not automatically EvidenceRecords, claims, evaluations, states, achievements, or frontier inputs.\n- The Pilot 01 runner does not generate participant answers or synthetic evidence.\n- origin=SUBJECT_PROVIDED is a declaration, not authentication of human authorship.\n- This workspace does not grant publication, safety, licensing, or action permission.\n"""


def _session_id(value: object) -> str:
    if not isinstance(value, str) or _SESSION_RE.fullmatch(value) is None:
        raise InvalidPrivatePilotWorkspace("session_id must be a canonical opaque ASCII identifier")
    return value


def _capture_file_key(value: object) -> str:
    try:
        return validate_capture_file_key(value)
    except InvalidPilotCapture as exc:
        raise InvalidPrivatePilotWorkspace(str(exc)) from exc


def _canonical_time(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise InvalidPrivatePilotWorkspace(f"{field_name} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise InvalidPrivatePilotWorkspace(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _reject_existing_symlink_components(path: Path, field_name: str) -> None:
    absolute = path.absolute()
    for candidate in (absolute, *absolute.parents):
        if candidate.is_symlink():
            raise InvalidPrivatePilotWorkspace(f"{field_name} must not contain symlink components")


def _find_git_root(start: Path) -> Path | None:
    current = start.resolve(strict=False)
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def validate_private_workspace_location(workspace: str | Path) -> Path:
    """Return a resolved workspace path after enforcing the in-repo `.local/` boundary."""

    raw = Path(workspace)
    _reject_existing_symlink_components(raw, "private workspace path")
    resolved = raw.resolve(strict=False)
    git_root = _find_git_root(resolved.parent)
    if git_root is not None and _is_relative_to(resolved, git_root):
        local_root = (git_root / ".local").resolve(strict=False)
        if resolved == local_root or not _is_relative_to(resolved, local_root):
            raise InvalidPrivatePilotWorkspace(
                "workspace inside a git repository must be below '<repo>/.local/'"
            )
    return resolved


@dataclass(frozen=True, slots=True)
class PrivatePilotWorkspaceManifest:
    protocol_ref: PilotProtocolRef
    session_id: str
    subject_ref: CapabilitySubjectRef
    created_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.protocol_ref, PilotProtocolRef):
            raise InvalidPrivatePilotWorkspace("protocol_ref must be PilotProtocolRef")
        object.__setattr__(self, "session_id", _session_id(self.session_id))
        if not isinstance(self.subject_ref, CapabilitySubjectRef):
            raise InvalidPrivatePilotWorkspace("subject_ref must be CapabilitySubjectRef")
        object.__setattr__(self, "created_at", _canonical_time(self.created_at, "created_at"))


@dataclass(frozen=True, slots=True)
class PilotWorkspaceValidationReport:
    session_id: str
    capture_count: int
    artifact_count: int
    captured_probe_ids: tuple[str, ...]
    missing_required_probe_ids: tuple[str, ...]

    @property
    def capture_complete(self) -> bool:
        return not self.missing_required_probe_ids


def _write_new_text(path: Path, content: str) -> None:
    try:
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
    except FileExistsError as exc:
        raise InvalidPrivatePilotWorkspace(f"refusing to overwrite existing file: {path}") from exc


def _require_regular_file(path: Path, field_name: str) -> Path:
    if path.is_symlink() or not path.is_file():
        raise InvalidPrivatePilotWorkspace(f"{field_name} must be a regular non-symlink file")
    return path


def _require_real_directory(path: Path, field_name: str) -> Path:
    if path.is_symlink() or not path.is_dir():
        raise InvalidPrivatePilotWorkspace(f"{field_name} must be a real non-symlink directory")
    return path


def _artifact_filename(value: str) -> str:
    if not isinstance(value, str) or not value or value in {".", ".."}:
        raise InvalidPrivatePilotWorkspace("artifact original_filename must be a non-empty filename")
    if "/" in value or "\\" in value:
        raise InvalidPrivatePilotWorkspace("artifact original_filename must not contain path separators")
    if any(ord(char) < 32 or char in '<>:"|?*' for char in value):
        raise InvalidPrivatePilotWorkspace("artifact original_filename is not cross-platform safe")
    if value.endswith((" ", ".")):
        raise InvalidPrivatePilotWorkspace("artifact original_filename must not end in space or dot")
    stem = value.split(".", 1)[0].upper()
    if stem in _WINDOWS_RESERVED_FILE_STEMS:
        raise InvalidPrivatePilotWorkspace("artifact original_filename uses a Windows reserved device name")
    return value


def initialize_private_workspace(
    workspace: str | Path,
    *,
    session_id: str,
    subject_ref: CapabilitySubjectRef,
    created_at: datetime,
    protocol: PilotProtocol | None = None,
) -> Path:
    """Create an empty private workspace; never create participant answers or example captures."""

    root = validate_private_workspace_location(workspace)
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
        if not root.is_dir():
            raise InvalidPrivatePilotWorkspace("workspace path must be a directory")
        if any(root.iterdir()):
            raise InvalidPrivatePilotWorkspace("workspace directory must be empty on initialization")
    else:
        root.mkdir(parents=True)

    (root / CAPTURES_DIRNAME).mkdir()
    (root / ARTIFACTS_DIRNAME).mkdir()
    _write_new_text(root / WORKSPACE_MANIFEST_FILENAME, workspace_manifest_to_json(manifest))
    _write_new_text(root / PROTOCOL_SNAPSHOT_FILENAME, pilot_protocol_to_json(frozen_protocol))
    _write_new_text(root / PRIVATE_NOTICE_FILENAME, PRIVATE_NOTICE)
    return root


def load_private_workspace(workspace: str | Path) -> tuple[Path, PrivatePilotWorkspaceManifest, PilotProtocol]:
    root = validate_private_workspace_location(workspace)
    _require_real_directory(root, "private workspace")

    names = {item.name for item in root.iterdir()}
    if names != _EXPECTED_TOP_LEVEL_NAMES:
        missing = sorted(_EXPECTED_TOP_LEVEL_NAMES - names)
        unexpected = sorted(names - _EXPECTED_TOP_LEVEL_NAMES)
        details: list[str] = []
        if missing:
            details.append("missing=" + ",".join(missing))
        if unexpected:
            details.append("unexpected=" + ",".join(unexpected))
        raise InvalidPrivatePilotWorkspace(
            "private workspace top-level layout must be exact" + (": " + "; ".join(details) if details else "")
        )

    manifest_path = _require_regular_file(root / WORKSPACE_MANIFEST_FILENAME, "workspace manifest")
    protocol_path = _require_regular_file(root / PROTOCOL_SNAPSHOT_FILENAME, "protocol snapshot")
    notice_path = _require_regular_file(root / PRIVATE_NOTICE_FILENAME, "private workspace notice")
    _require_real_directory(root / CAPTURES_DIRNAME, "captures directory")
    _require_real_directory(root / ARTIFACTS_DIRNAME, "artifacts directory")

    try:
        manifest_text = manifest_path.read_text(encoding="utf-8")
        protocol_text = protocol_path.read_text(encoding="utf-8")
        manifest = workspace_manifest_from_json(manifest_text)
        protocol = pilot_protocol_from_json(protocol_text)
        notice_text = notice_path.read_text(encoding="utf-8")
    except (OSError, PilotSerializationError, ValueError) as exc:
        raise InvalidPrivatePilotWorkspace(f"invalid private workspace metadata: {exc}") from exc

    if workspace_manifest_to_json(manifest) != manifest_text:
        raise InvalidPrivatePilotWorkspace("workspace manifest must use canonical deterministic JSON")
    if pilot_protocol_to_json(protocol) != protocol_text:
        raise InvalidPrivatePilotWorkspace("protocol snapshot must use canonical deterministic JSON")
    if notice_text != PRIVATE_NOTICE:
        raise InvalidPrivatePilotWorkspace("private workspace notice does not equal frozen Pilot 01 notice")

    expected = build_civilization_bootstrap_pilot_01_protocol_v1()
    if protocol != expected:
        raise InvalidPrivatePilotWorkspace("protocol snapshot does not equal frozen Pilot 01 protocol")
    if manifest.protocol_ref != protocol.protocol_ref:
        raise InvalidPrivatePilotWorkspace("workspace manifest protocol_ref does not match protocol snapshot")
    return root, manifest, protocol


def _capture_path(root: Path, capture_id: str) -> Path:
    key = _capture_file_key(capture_id)
    return root / CAPTURES_DIRNAME / f"{key}.json"


def _validate_capture_against_workspace(
    capture: PilotCaptureRecord,
    *,
    manifest: PrivatePilotWorkspaceManifest,
    protocol: PilotProtocol,
) -> None:
    if capture.protocol_ref != manifest.protocol_ref:
        raise InvalidPrivatePilotWorkspace("capture protocol_ref does not match workspace")
    if capture.session_id != manifest.session_id:
        raise InvalidPrivatePilotWorkspace("capture session_id does not match workspace")
    if capture.subject_ref != manifest.subject_ref:
        raise InvalidPrivatePilotWorkspace("capture subject_ref does not match workspace")
    if capture.captured_at < manifest.created_at:
        raise InvalidPrivatePilotWorkspace("capture captured_at must not precede workspace created_at")
    probe = protocol.probe(capture.probe_id)
    if capture.capture_kind not in probe.allowed_capture_kinds:
        raise InvalidPrivatePilotWorkspace(
            f"capture kind {capture.capture_kind.value} is not allowed for probe {capture.probe_id}"
        )


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
    root, manifest, protocol = load_private_workspace(workspace)
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
    _validate_capture_against_workspace(capture, manifest=manifest, protocol=protocol)
    _write_new_text(_capture_path(root, capture.capture_id), pilot_capture_to_json(capture))
    return capture


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
    root, manifest, protocol = load_private_workspace(workspace)
    capture_key = _capture_file_key(capture_id)
    probe = protocol.probe(probe_id)
    if PilotCaptureKind.FILE_ARTIFACT not in probe.allowed_capture_kinds:
        raise InvalidPrivatePilotWorkspace(
            f"capture kind {PilotCaptureKind.FILE_ARTIFACT.value} is not allowed for probe {probe_id}"
        )
    capture_path = _capture_path(root, capture_key)
    if capture_path.exists():
        raise InvalidPrivatePilotWorkspace(f"refusing to overwrite existing file: {capture_path}")

    source_raw = Path(source_file)
    _reject_existing_symlink_components(source_raw, "artifact source path")
    try:
        source = source_raw.resolve(strict=True)
    except FileNotFoundError as exc:
        raise InvalidPrivatePilotWorkspace("artifact source file does not exist") from exc
    if not source.is_file():
        raise InvalidPrivatePilotWorkspace("artifact source must be a regular file")
    filename = _artifact_filename(source.name)

    artifact_dir = root / ARTIFACTS_DIRNAME / capture_key
    if artifact_dir.exists():
        raise InvalidPrivatePilotWorkspace(f"artifact destination already exists for capture: {capture_key}")
    artifact_dir.mkdir()
    try:
        destination = artifact_dir / filename
        shutil.copyfile(source, destination)
        artifact = CapturedArtifact(
            relative_path=destination.relative_to(root).as_posix(),
            original_filename=filename,
            byte_size=destination.stat().st_size,
            sha256=_sha256(destination),
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
        _validate_capture_against_workspace(capture, manifest=manifest, protocol=protocol)
        _write_new_text(capture_path, pilot_capture_to_json(capture))
        return capture
    except Exception:
        shutil.rmtree(artifact_dir, ignore_errors=True)
        raise


def load_capture_set(workspace: str | Path) -> PilotCaptureSet:
    root, manifest, protocol = load_private_workspace(workspace)
    capture_dir = _require_real_directory(root / CAPTURES_DIRNAME, "captures directory")
    captures: list[PilotCaptureRecord] = []
    for path in sorted(capture_dir.iterdir(), key=lambda item: item.name):
        if path.is_symlink() or not path.is_file() or path.suffix != ".json":
            raise InvalidPrivatePilotWorkspace("captures directory may contain only regular canonical JSON capture files")
        try:
            raw = path.read_text(encoding="utf-8")
            capture = pilot_capture_from_json(raw)
        except (OSError, PilotSerializationError, ValueError) as exc:
            raise InvalidPrivatePilotWorkspace(f"invalid capture file {path.name}: {exc}") from exc
        if raw != pilot_capture_to_json(capture):
            raise InvalidPrivatePilotWorkspace(f"capture file {path.name} must use canonical deterministic JSON")
        if path.name != f"{capture.capture_id}.json":
            raise InvalidPrivatePilotWorkspace("capture filename must match capture_id")
        _validate_capture_against_workspace(capture, manifest=manifest, protocol=protocol)
        captures.append(capture)
    return PilotCaptureSet(manifest.protocol_ref, manifest.session_id, manifest.subject_ref, tuple(captures)).canonical()


def _reject_symlink_components(root: Path, relative_path: str) -> Path:
    current = root
    for part in Path(relative_path).parts:
        current = current / part
        if current.is_symlink():
            raise InvalidPrivatePilotWorkspace("captured artifact path must not contain symlink components")
    return current


def validate_private_workspace(workspace: str | Path) -> PilotWorkspaceValidationReport:
    root, manifest, protocol = load_private_workspace(workspace)
    capture_set = load_capture_set(root)
    artifacts_root = _require_real_directory(root / ARTIFACTS_DIRNAME, "artifacts directory")
    artifact_count = 0
    captured_probe_ids: set[str] = set()
    expected_artifact_dirs: set[str] = set()

    for capture in capture_set.captures:
        captured_probe_ids.add(capture.probe_id)
        if capture.artifact is None:
            continue

        artifact_count += 1
        filename = _artifact_filename(capture.artifact.original_filename)
        expected_relative = f"{ARTIFACTS_DIRNAME}/{capture.capture_id}/{filename}"
        if capture.artifact.relative_path != expected_relative:
            raise InvalidPrivatePilotWorkspace(
                "artifact relative_path must match canonical capture linkage "
                f"'{expected_relative}'"
            )
        expected_artifact_dirs.add(capture.capture_id)

        artifact_dir = _require_real_directory(
            artifacts_root / capture.capture_id,
            f"artifact directory for capture {capture.capture_id}",
        )
        entries = list(artifact_dir.iterdir())
        if len(entries) != 1 or entries[0].name != filename:
            raise InvalidPrivatePilotWorkspace(
                f"artifact directory for capture {capture.capture_id} must contain exactly '{filename}'"
            )

        raw_artifact_path = _reject_symlink_components(root, expected_relative)
        artifact_path = raw_artifact_path.resolve(strict=False)
        if not _is_relative_to(artifact_path, root):
            raise InvalidPrivatePilotWorkspace("artifact path escapes private workspace")
        _require_regular_file(artifact_path, "captured artifact")
        if artifact_path.stat().st_size != capture.artifact.byte_size:
            raise InvalidPrivatePilotWorkspace("captured artifact byte_size does not match file")
        if _sha256(artifact_path) != capture.artifact.sha256:
            raise InvalidPrivatePilotWorkspace("captured artifact sha256 does not match file")

    actual_artifact_dirs: set[str] = set()
    for entry in artifacts_root.iterdir():
        if entry.is_symlink() or not entry.is_dir():
            raise InvalidPrivatePilotWorkspace("artifacts directory may contain only real capture artifact directories")
        actual_artifact_dirs.add(entry.name)
    if actual_artifact_dirs != expected_artifact_dirs:
        orphaned = sorted(actual_artifact_dirs - expected_artifact_dirs)
        missing_dirs = sorted(expected_artifact_dirs - actual_artifact_dirs)
        details: list[str] = []
        if orphaned:
            details.append("orphaned=" + ",".join(orphaned))
        if missing_dirs:
            details.append("missing=" + ",".join(missing_dirs))
        raise InvalidPrivatePilotWorkspace(
            "artifact directory closure does not match artifact captures"
            + (": " + "; ".join(details) if details else "")
        )

    missing = tuple(
        probe_id for probe_id in protocol.required_probe_ids if probe_id not in captured_probe_ids
    )
    return PilotWorkspaceValidationReport(
        session_id=manifest.session_id,
        capture_count=len(capture_set.captures),
        artifact_count=artifact_count,
        captured_probe_ids=tuple(sorted(captured_probe_ids)),
        missing_required_probe_ids=missing,
    )
