"""Private raw-capture records for Civilization Bootstrap Pilot 01.

A PilotCaptureRecord preserves participant-provided material before any PR2
EvidenceRecord, claim, evaluation, or PR3 state materialization. The declared
origin is provenance metadata only; it is not proof of human authorship.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import re
import unicodedata

from capability_lab.epistemics import CapabilitySubjectRef

from .protocol import PilotCaptureKind, PilotProtocolRef


class PilotCaptureError(ValueError):
    """Base validation error for private pilot captures."""


class InvalidPilotCapture(PilotCaptureError):
    pass


_OPAQUE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_FILE_KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_WINDOWS_RESERVED_FILE_STEMS = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}


def _opaque_id(value: object, field_name: str) -> str:
    if not isinstance(value, str) or _OPAQUE_ID_RE.fullmatch(value) is None:
        raise InvalidPilotCapture(f"{field_name} must be a canonical opaque ASCII identifier")
    return value


def validate_capture_file_key(value: object) -> str:
    """Validate a capture id that is safe to use as a cross-platform filename stem."""

    if not isinstance(value, str) or _FILE_KEY_RE.fullmatch(value) is None:
        raise InvalidPilotCapture(
            "capture id must use cross-platform file-key syntax [A-Za-z0-9._-]"
        )
    windows_stem = value.split(".", 1)[0].upper()
    if windows_stem in _WINDOWS_RESERVED_FILE_STEMS:
        raise InvalidPilotCapture("capture id must not use a Windows reserved device name")
    return value


def _key(value: object, field_name: str) -> str:
    if not isinstance(value, str) or _KEY_RE.fullmatch(value) is None:
        raise InvalidPilotCapture(f"{field_name} must use canonical lowercase key syntax")
    return value


def _clean_text(value: object, field_name: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise InvalidPilotCapture(f"{field_name} must be a string")
    cleaned = unicodedata.normalize("NFC", value).strip()
    if not cleaned and not allow_empty:
        raise InvalidPilotCapture(f"{field_name} must be non-empty")
    return cleaned


def _canonical_time(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise InvalidPilotCapture(f"{field_name} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise InvalidPilotCapture(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


class CaptureOriginKind(str, Enum):
    SUBJECT_PROVIDED = "SUBJECT_PROVIDED"


@dataclass(frozen=True, slots=True)
class CapturedArtifact:
    relative_path: str
    original_filename: str
    byte_size: int
    sha256: str

    def __post_init__(self) -> None:
        relative_path = _clean_text(self.relative_path, "artifact relative_path")
        if relative_path.startswith(("/", "\\")) or ".." in relative_path.replace("\\", "/").split("/"):
            raise InvalidPilotCapture("artifact relative_path must stay within the private workspace")
        object.__setattr__(self, "relative_path", relative_path.replace("\\", "/"))
        object.__setattr__(
            self,
            "original_filename",
            _clean_text(self.original_filename, "artifact original_filename"),
        )
        if isinstance(self.byte_size, bool) or not isinstance(self.byte_size, int) or self.byte_size < 0:
            raise InvalidPilotCapture("artifact byte_size must be an integer >= 0")
        if not isinstance(self.sha256, str) or _SHA256_RE.fullmatch(self.sha256) is None:
            raise InvalidPilotCapture("artifact sha256 must be a lowercase 64-character hex digest")


@dataclass(frozen=True, slots=True)
class PilotCaptureRecord:
    capture_id: str
    protocol_ref: PilotProtocolRef
    session_id: str
    subject_ref: CapabilitySubjectRef
    probe_id: str
    capture_kind: PilotCaptureKind
    origin_kind: CaptureOriginKind
    captured_at: datetime
    declared_tools: tuple[str, ...] = ()
    participant_note: str = ""
    text_content: str | None = None
    artifact: CapturedArtifact | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "capture_id", validate_capture_file_key(self.capture_id))
        if not isinstance(self.protocol_ref, PilotProtocolRef):
            raise InvalidPilotCapture("protocol_ref must be PilotProtocolRef")
        object.__setattr__(self, "session_id", _opaque_id(self.session_id, "session id"))
        if not isinstance(self.subject_ref, CapabilitySubjectRef):
            raise InvalidPilotCapture("subject_ref must be CapabilitySubjectRef")
        object.__setattr__(self, "probe_id", _key(self.probe_id, "probe id"))
        if not isinstance(self.capture_kind, PilotCaptureKind):
            raise InvalidPilotCapture("capture_kind must be PilotCaptureKind")
        if self.origin_kind is not CaptureOriginKind.SUBJECT_PROVIDED:
            raise InvalidPilotCapture("Pilot 01 captures must be explicitly subject-provided")
        object.__setattr__(self, "captured_at", _canonical_time(self.captured_at, "captured_at"))

        if not isinstance(self.declared_tools, tuple):
            raise InvalidPilotCapture("declared_tools must be a tuple")
        cleaned_tools = tuple(_clean_text(item, "declared tool") for item in self.declared_tools)
        if len(set(cleaned_tools)) != len(cleaned_tools):
            raise InvalidPilotCapture("declared_tools must not contain duplicates")
        object.__setattr__(self, "declared_tools", cleaned_tools)
        object.__setattr__(
            self,
            "participant_note",
            _clean_text(self.participant_note, "participant_note", allow_empty=True),
        )

        if self.capture_kind is PilotCaptureKind.TEXT_RESPONSE:
            if self.artifact is not None:
                raise InvalidPilotCapture("text capture must not contain an artifact")
            if self.text_content is None:
                raise InvalidPilotCapture("text capture requires text_content")
            object.__setattr__(self, "text_content", _clean_text(self.text_content, "text_content"))
        elif self.capture_kind is PilotCaptureKind.FILE_ARTIFACT:
            if self.text_content is not None:
                raise InvalidPilotCapture("artifact capture must not contain text_content")
            if not isinstance(self.artifact, CapturedArtifact):
                raise InvalidPilotCapture("artifact capture requires CapturedArtifact")
        else:  # pragma: no cover - enum exhaustiveness guard
            raise InvalidPilotCapture("unsupported capture kind")


@dataclass(frozen=True, slots=True)
class PilotCaptureSet:
    protocol_ref: PilotProtocolRef
    session_id: str
    subject_ref: CapabilitySubjectRef
    captures: tuple[PilotCaptureRecord, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.protocol_ref, PilotProtocolRef):
            raise InvalidPilotCapture("capture set protocol_ref must be PilotProtocolRef")
        object.__setattr__(self, "session_id", _opaque_id(self.session_id, "session id"))
        if not isinstance(self.subject_ref, CapabilitySubjectRef):
            raise InvalidPilotCapture("capture set subject_ref must be CapabilitySubjectRef")
        if not isinstance(self.captures, tuple):
            raise InvalidPilotCapture("captures must be a tuple")
        if any(not isinstance(item, PilotCaptureRecord) for item in self.captures):
            raise InvalidPilotCapture("captures must contain PilotCaptureRecord values")
        capture_ids = tuple(item.capture_id for item in self.captures)
        if len(set(capture_ids)) != len(capture_ids):
            raise InvalidPilotCapture("capture ids must be unique")
        for capture in self.captures:
            if capture.protocol_ref != self.protocol_ref:
                raise InvalidPilotCapture("capture protocol_ref must match capture set")
            if capture.session_id != self.session_id:
                raise InvalidPilotCapture("capture session_id must match capture set")
            if capture.subject_ref != self.subject_ref:
                raise InvalidPilotCapture("capture subject_ref must match capture set")

    def canonical(self) -> "PilotCaptureSet":
        return PilotCaptureSet(
            self.protocol_ref,
            self.session_id,
            self.subject_ref,
            tuple(sorted(self.captures, key=lambda item: item.capture_id)),
        )
