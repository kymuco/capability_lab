from datetime import datetime, timezone
import json

import pytest

from capability_lab.epistemics import CapabilitySubjectRef
from capability_lab.pilots.civilization_bootstrap_01 import (
    CaptureOriginKind,
    PilotCaptureKind,
    PilotCaptureRecord,
    PilotSerializationError,
    build_civilization_bootstrap_pilot_01_protocol_v1,
    pilot_capture_from_json,
    pilot_capture_to_json,
    pilot_protocol_from_json,
    pilot_protocol_to_json,
)


T0 = datetime(2026, 8, 16, 12, 0, tzinfo=timezone.utc)


def _capture() -> PilotCaptureRecord:
    protocol = build_civilization_bootstrap_pilot_01_protocol_v1()
    return PilotCaptureRecord(
        capture_id="conceptual_01",
        protocol_ref=protocol.protocol_ref,
        session_id="cb01_session",
        subject_ref=CapabilitySubjectRef("pilot_subject"),
        probe_id="conceptual_explanation",
        capture_kind=PilotCaptureKind.TEXT_RESPONSE,
        origin_kind=CaptureOriginKind.SUBJECT_PROVIDED,
        captured_at=T0,
        declared_tools=("plain text editor",),
        participant_note="Recorded without a prepared answer.",
        text_content="Voltage, current, and resistance are related under stated assumptions.",
    )


def test_protocol_and_capture_roundtrip_are_canonical() -> None:
    protocol = build_civilization_bootstrap_pilot_01_protocol_v1()
    protocol_json = pilot_protocol_to_json(protocol)
    capture = _capture()
    capture_json = pilot_capture_to_json(capture)

    assert pilot_protocol_from_json(protocol_json) == protocol
    assert pilot_protocol_to_json(pilot_protocol_from_json(protocol_json)) == protocol_json
    assert pilot_capture_from_json(capture_json) == capture
    assert pilot_capture_to_json(pilot_capture_from_json(capture_json)) == capture_json


def test_strict_json_rejects_duplicate_keys_unknown_fields_and_bool_schema_version() -> None:
    protocol_json = pilot_protocol_to_json(build_civilization_bootstrap_pilot_01_protocol_v1())
    duplicate = protocol_json.replace(
        '"schema_version":1',
        '"schema_version":1,"schema_version":1',
        1,
    )
    with pytest.raises(PilotSerializationError, match="duplicate JSON key"):
        pilot_protocol_from_json(duplicate)

    raw = json.loads(protocol_json)
    raw["unexpected"] = "nope"
    with pytest.raises(PilotSerializationError, match="unknown fields"):
        pilot_protocol_from_json(json.dumps(raw))

    raw = json.loads(protocol_json)
    raw["schema_version"] = True
    with pytest.raises(PilotSerializationError, match="integer 1"):
        pilot_protocol_from_json(json.dumps(raw))


def test_capture_serialization_rejects_naive_time_and_non_subject_origin() -> None:
    raw = json.loads(pilot_capture_to_json(_capture()))
    raw["captured_at"] = "2026-08-16T12:00:00"
    with pytest.raises(PilotSerializationError, match="timezone-aware"):
        pilot_capture_from_json(json.dumps(raw))

    raw = json.loads(pilot_capture_to_json(_capture()))
    raw["origin_kind"] = "MODEL_GENERATED"
    with pytest.raises(PilotSerializationError, match="origin kind"):
        pilot_capture_from_json(json.dumps(raw))


def test_capture_id_is_a_cross_platform_file_key() -> None:
    raw = json.loads(pilot_capture_to_json(_capture()))
    raw["capture_id"] = "../escape"
    with pytest.raises(PilotSerializationError, match="file-key syntax"):
        pilot_capture_from_json(json.dumps(raw))

    raw = json.loads(pilot_capture_to_json(_capture()))
    raw["capture_id"] = "drive:escape"
    with pytest.raises(PilotSerializationError, match="file-key syntax"):
        pilot_capture_from_json(json.dumps(raw))

    raw = json.loads(pilot_capture_to_json(_capture()))
    raw["capture_id"] = "CON"
    with pytest.raises(PilotSerializationError, match="Windows reserved device name"):
        pilot_capture_from_json(json.dumps(raw))
