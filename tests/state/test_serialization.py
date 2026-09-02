from datetime import datetime, timezone

import pytest

from capability_lab.epistemics import CapabilityClaimId, CapabilitySubjectRef, ClaimEvaluationId
from capability_lab.semantics import CapabilityConceptRef
from capability_lab.state import (
    CompetenceDimensionDefinition,
    CompetenceDimensionState,
    CompetenceFrame,
    CompetenceFrameCatalog,
    CompetenceFrameId,
    DimensionConflictStatus,
    DimensionStanding,
    InvalidCompetenceFrame,
    InvalidStateSet,
    PersonalCapabilityState,
    PersonalCapabilityStateId,
    PersonalCapabilityStateSet,
    StateDerivationPolicyRef,
    StateDeriverKind,
    StateDeriverRef,
)

T0 = datetime(2026, 8, 15, 6, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("subject_serialization")


def frame_catalog() -> CompetenceFrameCatalog:
    return CompetenceFrameCatalog(
        (
            CompetenceFrame(
                CompetenceFrameId.parse("core:technical_competence"),
                1,
                "Technical competence",
                "Strict serialization frame fixture.",
                (
                    CompetenceDimensionDefinition("execution", "Execution", "Bounded execution."),
                    CompetenceDimensionDefinition("diagnosis", "Diagnosis", "Bounded diagnosis."),
                ),
            ),
        )
    )


def state_set() -> PersonalCapabilityStateSet:
    frame = frame_catalog().frames[0]
    return PersonalCapabilityStateSet(
        SUBJECT,
        (
            PersonalCapabilityState(
                PersonalCapabilityStateId("state_serialized"),
                SUBJECT,
                CapabilityConceptRef.parse("core:test_capability@1"),
                frame.ref,
                StateDerivationPolicyRef.parse("core:manual_supported_state@1"),
                StateDeriverRef(StateDeriverKind.RULE, "fixture_rule"),
                T0,
                T0,
                (
                    CompetenceDimensionState(
                        "execution",
                        DimensionStanding.SUPPORTED,
                        (CapabilityClaimId("claim_exec"),),
                        (ClaimEvaluationId("eval_exec"),),
                        "Scoped supported content.",
                    ),
                    CompetenceDimensionState(
                        "diagnosis",
                        DimensionStanding.UNKNOWN,
                        rationale="No diagnosis basis.",
                    ),
                ),
                "Canonical serialization fixture.",
            ),
        ),
    )


def test_frame_catalog_roundtrip_is_deterministic() -> None:
    value = frame_catalog()
    payload = value.to_json()
    assert payload == value.to_json()
    assert CompetenceFrameCatalog.from_json(payload) == value
    assert '"schema":"competence_frames/v1"' in payload


def test_state_set_roundtrip_is_deterministic() -> None:
    value = state_set()
    payload = value.to_json()
    assert payload == value.to_json()
    assert PersonalCapabilityStateSet.from_json(payload) == value
    assert '"schema":"personal_capability_states/v1"' in payload
    assert '"as_of":"2026-08-15T06:00:00Z"' in payload
    assert '"conflict_status":"none"' in payload


def test_state_json_rejects_unknown_nested_fields() -> None:
    payload = state_set().to_dict()
    payload["states"][0]["dimensions"][0]["score"] = 0.9
    with pytest.raises(InvalidStateSet, match="unknown fields"):
        PersonalCapabilityStateSet.from_dict(payload)


def test_state_json_requires_explicit_conflict_status() -> None:
    payload = state_set().to_dict()
    del payload["states"][0]["dimensions"][0]["conflict_status"]
    with pytest.raises(InvalidStateSet, match="missing fields"):
        PersonalCapabilityStateSet.from_dict(payload)


def test_state_json_rejects_invalid_conflict_status() -> None:
    payload = state_set().to_dict()
    payload["states"][0]["dimensions"][0]["conflict_status"] = "contested"
    with pytest.raises(InvalidStateSet, match="invalid dimension conflict status"):
        PersonalCapabilityStateSet.from_dict(payload)


def test_state_json_rejects_string_where_array_required() -> None:
    payload = state_set().to_dict()
    payload["states"][0]["dimensions"] = "execution"
    with pytest.raises(InvalidStateSet, match="must be an array"):
        PersonalCapabilityStateSet.from_dict(payload)


def test_state_json_rejects_duplicate_object_keys() -> None:
    payload = '{"schema":"personal_capability_states/v1","subject_ref":"subject_serialization","subject_ref":"other","states":[]}'
    with pytest.raises(InvalidStateSet, match="duplicate JSON object key"):
        PersonalCapabilityStateSet.from_json(payload)


def test_state_json_rejects_nonstandard_numeric_constants() -> None:
    payload = '{"schema":"personal_capability_states/v1","subject_ref":"subject_serialization","states":[],"x":NaN}'
    with pytest.raises(InvalidStateSet, match="non-standard JSON numeric constant"):
        PersonalCapabilityStateSet.from_json(payload)


def test_state_json_rejects_permissive_timestamp_forms() -> None:
    payload = state_set().to_dict()
    payload["states"][0]["as_of"] = "2026-08-15 06:00:00+00:00"
    with pytest.raises(InvalidStateSet, match="extended ISO-8601"):
        PersonalCapabilityStateSet.from_dict(payload)


def test_frame_json_rejects_unknown_fields_with_frame_domain_error() -> None:
    payload = frame_catalog().to_dict()
    payload["frames"][0]["weight"] = 1.0
    with pytest.raises(InvalidCompetenceFrame, match="unknown fields"):
        CompetenceFrameCatalog.from_dict(payload)


def test_frame_json_rejects_duplicate_keys_with_frame_domain_error() -> None:
    payload = '{"schema":"competence_frames/v1","frames":[],"frames":[]}'
    with pytest.raises(InvalidCompetenceFrame, match="duplicate JSON object key"):
        CompetenceFrameCatalog.from_json(payload)


def test_conflict_enum_values_are_non_ordinal_and_explicit() -> None:
    assert {item.value for item in DimensionConflictStatus} == {
        "none",
        "resolved_by_policy",
        "unresolved",
    }
