"""Strict deterministic JSON serialization for Civilization Bootstrap Pilot 01."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any

from capability_lab.epistemics import CapabilitySubjectRef
from capability_lab.semantics import CapabilityConceptRef
from capability_lab.state import CompetenceFrameRef

from .capture import (
    CaptureOriginKind,
    CapturedArtifact,
    InvalidPilotCapture,
    PilotCaptureRecord,
)
from .protocol import (
    InvalidPilotProtocol,
    PilotCaptureKind,
    PilotProbeDefinition,
    PilotProbeRequirement,
    PilotProtocol,
    PilotProtocolRef,
)


PROTOCOL_SCHEMA = "capability_lab/civilization_bootstrap_pilot_protocol@1"
WORKSPACE_SCHEMA = "capability_lab/private_pilot_workspace@1"
CAPTURE_SCHEMA = "capability_lab/pilot_capture@1"
_SCHEMA_VERSION = 1


class PilotSerializationError(ValueError):
    pass


def _mapping(value: object, context: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise PilotSerializationError(f"{context} must be an object")
    if any(not isinstance(key, str) for key in value):
        raise PilotSerializationError(f"{context} keys must be strings")
    return value


def _sequence(value: object, context: str) -> Sequence[Any]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise PilotSerializationError(f"{context} must be an array")
    return value


def _keys(value: Mapping[str, Any], allowed: set[str], required: set[str], context: str) -> None:
    unknown = sorted(set(value) - allowed)
    missing = sorted(required - set(value))
    if unknown:
        raise PilotSerializationError(f"{context} contains unknown fields: {', '.join(unknown)}")
    if missing:
        raise PilotSerializationError(f"{context} is missing fields: {', '.join(missing)}")


def _schema_version(value: object, context: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value != _SCHEMA_VERSION:
        raise PilotSerializationError(f"{context} schema_version must be integer 1")


def _enum(enum_type, value: object, context: str):
    if not isinstance(value, str):
        raise PilotSerializationError(f"{context} must be a string enum value")
    try:
        return enum_type(value)
    except ValueError as exc:
        raise PilotSerializationError(f"invalid {context}: {value!r}") from exc


def _strings(value: object, context: str) -> tuple[str, ...]:
    items = _sequence(value, context)
    if any(not isinstance(item, str) for item in items):
        raise PilotSerializationError(f"{context} must contain strings")
    return tuple(items)


def _format_time(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise PilotSerializationError("timestamp must be timezone-aware")
    canonical = value.astimezone(timezone.utc)
    return canonical.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _parse_time(value: object, context: str) -> datetime:
    if not isinstance(value, str):
        raise PilotSerializationError(f"{context} must be an ISO timestamp string")
    raw = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise PilotSerializationError(f"invalid {context}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise PilotSerializationError(f"{context} must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _reject_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PilotSerializationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str):
    raise PilotSerializationError(f"non-finite JSON constant is not allowed: {value}")


def _loads(value: str, context: str) -> object:
    if not isinstance(value, str):
        raise PilotSerializationError(f"{context} JSON must be a string")
    try:
        return json.loads(value, object_pairs_hook=_reject_pairs, parse_constant=_reject_constant)
    except PilotSerializationError:
        raise
    except json.JSONDecodeError as exc:
        raise PilotSerializationError(f"invalid {context} JSON") from exc


def _dumps(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"


def pilot_protocol_to_dict(value: PilotProtocol) -> dict[str, Any]:
    if not isinstance(value, PilotProtocol):
        raise PilotSerializationError("value must be PilotProtocol")
    return {
        "schema": PROTOCOL_SCHEMA,
        "schema_version": _SCHEMA_VERSION,
        "protocol_ref": str(value.protocol_ref),
        "title": value.title,
        "description": value.description,
        "capability_ref": str(value.capability_ref),
        "frame_ref": str(value.frame_ref),
        "participant_instructions": list(value.participant_instructions),
        "privacy_boundaries": list(value.privacy_boundaries),
        "physical_boundaries": list(value.physical_boundaries),
        "probes": [
            {
                "probe_id": probe.probe_id,
                "title": probe.title,
                "requirement": probe.requirement.value,
                "allowed_capture_kinds": [item.value for item in probe.allowed_capture_kinds],
                "participant_prompt": probe.participant_prompt,
            }
            for probe in value.probes
        ],
    }


def pilot_protocol_from_dict(value: object) -> PilotProtocol:
    data = _mapping(value, "pilot protocol")
    allowed = {
        "schema", "schema_version", "protocol_ref", "title", "description",
        "capability_ref", "frame_ref", "participant_instructions", "privacy_boundaries",
        "physical_boundaries", "probes",
    }
    _keys(data, allowed, allowed, "pilot protocol")
    if data["schema"] != PROTOCOL_SCHEMA:
        raise PilotSerializationError("invalid pilot protocol schema")
    _schema_version(data["schema_version"], "pilot protocol")
    probes: list[PilotProbeDefinition] = []
    for raw in _sequence(data["probes"], "pilot protocol probes"):
        item = _mapping(raw, "pilot probe")
        fields = {"probe_id", "title", "requirement", "allowed_capture_kinds", "participant_prompt"}
        _keys(item, fields, fields, "pilot probe")
        probes.append(PilotProbeDefinition(
            probe_id=item["probe_id"],
            title=item["title"],
            requirement=_enum(PilotProbeRequirement, item["requirement"], "pilot probe requirement"),
            allowed_capture_kinds=tuple(
                _enum(PilotCaptureKind, entry, "pilot capture kind")
                for entry in _sequence(item["allowed_capture_kinds"], "allowed_capture_kinds")
            ),
            participant_prompt=item["participant_prompt"],
        ))
    try:
        return PilotProtocol(
            protocol_ref=PilotProtocolRef.parse(data["protocol_ref"]),
            title=data["title"],
            description=data["description"],
            capability_ref=CapabilityConceptRef.parse(data["capability_ref"]),
            frame_ref=CompetenceFrameRef.parse(data["frame_ref"]),
            participant_instructions=_strings(data["participant_instructions"], "participant_instructions"),
            privacy_boundaries=_strings(data["privacy_boundaries"], "privacy_boundaries"),
            physical_boundaries=_strings(data["physical_boundaries"], "physical_boundaries"),
            probes=tuple(probes),
        )
    except (InvalidPilotProtocol, ValueError) as exc:
        raise PilotSerializationError(str(exc)) from exc


def pilot_protocol_to_json(value: PilotProtocol) -> str:
    return _dumps(pilot_protocol_to_dict(value))


def pilot_protocol_from_json(value: str) -> PilotProtocol:
    return pilot_protocol_from_dict(_loads(value, "pilot protocol"))


# Workspace manifest is kept as a plain strict record so workspace.py does not
# depend on JSON implementation details.
def workspace_manifest_to_dict(value) -> dict[str, Any]:
    from .workspace import PrivatePilotWorkspaceManifest

    if not isinstance(value, PrivatePilotWorkspaceManifest):
        raise PilotSerializationError("value must be PrivatePilotWorkspaceManifest")
    return {
        "schema": WORKSPACE_SCHEMA,
        "schema_version": _SCHEMA_VERSION,
        "protocol_ref": str(value.protocol_ref),
        "session_id": value.session_id,
        "subject_ref": str(value.subject_ref),
        "created_at": _format_time(value.created_at),
    }


def workspace_manifest_from_dict(value: object):
    from .workspace import PrivatePilotWorkspaceManifest

    data = _mapping(value, "private pilot workspace manifest")
    fields = {"schema", "schema_version", "protocol_ref", "session_id", "subject_ref", "created_at"}
    _keys(data, fields, fields, "private pilot workspace manifest")
    if data["schema"] != WORKSPACE_SCHEMA:
        raise PilotSerializationError("invalid private pilot workspace schema")
    _schema_version(data["schema_version"], "private pilot workspace")
    try:
        return PrivatePilotWorkspaceManifest(
            protocol_ref=PilotProtocolRef.parse(data["protocol_ref"]),
            session_id=data["session_id"],
            subject_ref=CapabilitySubjectRef(data["subject_ref"]),
            created_at=_parse_time(data["created_at"], "workspace created_at"),
        )
    except ValueError as exc:
        raise PilotSerializationError(str(exc)) from exc


def workspace_manifest_to_json(value) -> str:
    return _dumps(workspace_manifest_to_dict(value))


def workspace_manifest_from_json(value: str):
    return workspace_manifest_from_dict(_loads(value, "private pilot workspace manifest"))


def _artifact_to_dict(value: CapturedArtifact | None) -> dict[str, Any] | None:
    if value is None:
        return None
    return {
        "relative_path": value.relative_path,
        "original_filename": value.original_filename,
        "byte_size": value.byte_size,
        "sha256": value.sha256,
    }


def _artifact_from_dict(value: object) -> CapturedArtifact | None:
    if value is None:
        return None
    data = _mapping(value, "captured artifact")
    fields = {"relative_path", "original_filename", "byte_size", "sha256"}
    _keys(data, fields, fields, "captured artifact")
    try:
        return CapturedArtifact(
            relative_path=data["relative_path"],
            original_filename=data["original_filename"],
            byte_size=data["byte_size"],
            sha256=data["sha256"],
        )
    except InvalidPilotCapture as exc:
        raise PilotSerializationError(str(exc)) from exc


def pilot_capture_to_dict(value: PilotCaptureRecord) -> dict[str, Any]:
    if not isinstance(value, PilotCaptureRecord):
        raise PilotSerializationError("value must be PilotCaptureRecord")
    return {
        "schema": CAPTURE_SCHEMA,
        "schema_version": _SCHEMA_VERSION,
        "capture_id": value.capture_id,
        "protocol_ref": str(value.protocol_ref),
        "session_id": value.session_id,
        "subject_ref": str(value.subject_ref),
        "probe_id": value.probe_id,
        "capture_kind": value.capture_kind.value,
        "origin_kind": value.origin_kind.value,
        "captured_at": _format_time(value.captured_at),
        "declared_tools": list(value.declared_tools),
        "participant_note": value.participant_note,
        "text_content": value.text_content,
        "artifact": _artifact_to_dict(value.artifact),
    }


def pilot_capture_from_dict(value: object) -> PilotCaptureRecord:
    data = _mapping(value, "pilot capture")
    fields = {
        "schema", "schema_version", "capture_id", "protocol_ref", "session_id", "subject_ref",
        "probe_id", "capture_kind", "origin_kind", "captured_at", "declared_tools",
        "participant_note", "text_content", "artifact",
    }
    _keys(data, fields, fields, "pilot capture")
    if data["schema"] != CAPTURE_SCHEMA:
        raise PilotSerializationError("invalid pilot capture schema")
    _schema_version(data["schema_version"], "pilot capture")
    if data["text_content"] is not None and not isinstance(data["text_content"], str):
        raise PilotSerializationError("pilot capture text_content must be string or null")
    try:
        return PilotCaptureRecord(
            capture_id=data["capture_id"],
            protocol_ref=PilotProtocolRef.parse(data["protocol_ref"]),
            session_id=data["session_id"],
            subject_ref=CapabilitySubjectRef(data["subject_ref"]),
            probe_id=data["probe_id"],
            capture_kind=_enum(PilotCaptureKind, data["capture_kind"], "pilot capture kind"),
            origin_kind=_enum(CaptureOriginKind, data["origin_kind"], "pilot capture origin kind"),
            captured_at=_parse_time(data["captured_at"], "capture captured_at"),
            declared_tools=_strings(data["declared_tools"], "declared_tools"),
            participant_note=data["participant_note"],
            text_content=data["text_content"],
            artifact=_artifact_from_dict(data["artifact"]),
        )
    except (InvalidPilotCapture, ValueError) as exc:
        raise PilotSerializationError(str(exc)) from exc


def pilot_capture_to_json(value: PilotCaptureRecord) -> str:
    return _dumps(pilot_capture_to_dict(value))


def pilot_capture_from_json(value: str) -> PilotCaptureRecord:
    return pilot_capture_from_dict(_loads(value, "pilot capture"))
