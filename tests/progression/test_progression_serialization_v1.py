from datetime import datetime, timedelta, timezone
import json

import pytest

from capability_lab.domains import (
    build_civilization_bootstrap_frame_catalog_v1,
    build_civilization_bootstrap_seed_catalog_v0,
)
from capability_lab.epistemics import CapabilitySubjectRef, EpistemicRecordSet
from capability_lab.progression import (
    InvalidProgressionRequest,
    ProgressionFocus,
    ProgressionFrontier,
    ProgressionFrontierId,
    ProgressionFrontierRequest,
    ProgressionFrontierSet,
    ProgressionMechanismKind,
    ProgressionRequesterRef,
    derive_progression_frontier_v1,
)
from capability_lab.progression.serialization import request_from_json, request_to_json
from capability_lab.state import PersonalCapabilityStateSet


T0 = datetime(2026, 8, 15, 17, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("subject_pr8_serialization")


def _request():
    catalog = build_civilization_bootstrap_seed_catalog_v0()
    concept = next(item for item in catalog.concepts if item.capability_id.key == "radio_communication")
    return ProgressionFrontierRequest(
        ProgressionFrontierId("frontier_pr8_serialization"),
        SUBJECT,
        T0,
        T0 + timedelta(minutes=1),
        ProgressionRequesterRef(ProgressionMechanismKind.HUMAN, "test:serialization_requester"),
        focuses=(ProgressionFocus(concept.ref, "Explicit focus for deterministic roundtrip."),),
    )


def test_request_and_frontier_roundtrip_are_canonical() -> None:
    request = _request()
    request_json = request_to_json(request)
    assert request_from_json(request_json) == request
    assert request_to_json(request_from_json(request_json)) == request_json

    frontier = derive_progression_frontier_v1(
        capability_catalog=build_civilization_bootstrap_seed_catalog_v0(),
        frame_catalog=build_civilization_bootstrap_frame_catalog_v1(),
        records=EpistemicRecordSet(),
        state_set=PersonalCapabilityStateSet(SUBJECT, ()),
        request=request,
    )
    encoded = frontier.to_json()
    assert ProgressionFrontier.from_json(encoded) == frontier
    assert ProgressionFrontier.from_json(encoded).to_json() == encoded

    frontier_set = ProgressionFrontierSet(SUBJECT, (frontier,))
    assert ProgressionFrontierSet.from_json(frontier_set.to_json()) == frontier_set


def test_strict_ingestion_rejects_boolean_schema_version_unknown_fields_and_duplicate_json_keys() -> None:
    payload = json.loads(request_to_json(_request()))
    payload["schema_version"] = True
    with pytest.raises(InvalidProgressionRequest):
        ProgressionFrontierRequest.from_dict(payload)

    payload = json.loads(request_to_json(_request()))
    payload["unexpected"] = 1
    with pytest.raises(InvalidProgressionRequest):
        ProgressionFrontierRequest.from_dict(payload)

    raw = request_to_json(_request())
    duplicated = raw.replace('{"request":', '{"request":null,"request":', 1)
    with pytest.raises(Exception):
        request_from_json(duplicated)
