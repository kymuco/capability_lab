"""Strict deterministic serialization for PR3 competence frames and personal state."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from capability_lab.epistemics import (
    CapabilityClaimId,
    CapabilitySubjectRef,
    ClaimEvaluationId,
)
from capability_lab.epistemics.core import format_time, parse_time
from capability_lab.semantics import CapabilityConceptRef

from .core import (
    CompetenceDimensionDefinition,
    CompetenceDimensionState,
    CompetenceFrame,
    CompetenceFrameCatalog,
    CompetenceFrameId,
    CompetenceFrameRef,
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
    StateError,
)

_FRAME_SCHEMA = "competence_frames/v1"
_STATE_SCHEMA = "personal_capability_states/v1"


def dumps_canonical(payload: object) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _mapping(value: object, context: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise InvalidStateSet(f"{context} must be an object")
    if any(not isinstance(key, str) for key in value):
        raise InvalidStateSet(f"{context} keys must be strings")
    return value


def _sequence(value: object, context: str) -> Sequence[Any]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise InvalidStateSet(f"{context} must be an array")
    return value


def _keys(
    value: Mapping[str, Any],
    allowed: set[str],
    required: set[str],
    context: str,
) -> None:
    unknown = sorted(set(value) - allowed)
    missing = sorted(required - set(value))
    if unknown:
        raise InvalidStateSet(
            f"{context} contains unknown fields: {', '.join(unknown)}"
        )
    if missing:
        raise InvalidStateSet(
            f"{context} is missing fields: {', '.join(missing)}"
        )


def _enum(enum_type, value: object, context: str):
    if not isinstance(value, str):
        raise InvalidStateSet(f"{context} must be a string enum value")
    try:
        return enum_type(value)
    except ValueError as exc:
        raise InvalidStateSet(f"invalid {context}: {value!r}") from exc


def _strings(value: object, context: str) -> tuple[str, ...]:
    items = _sequence(value, context)
    if any(not isinstance(item, str) for item in items):
        raise InvalidStateSet(f"{context} must contain strings")
    return tuple(items)


def _loads_strict(payload: object, context: str) -> Mapping[str, Any]:
    if not isinstance(payload, str):
        raise InvalidStateSet(f"{context} JSON payload must be a string")

    def pairs_hook(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise InvalidStateSet(
                    f"duplicate JSON object key: {key!r}"
                )
            result[key] = value
        return result

    def reject_constant(value: str):
        raise InvalidStateSet(
            f"non-standard JSON numeric constant is not allowed: {value}"
        )

    try:
        decoded = json.loads(
            payload,
            object_pairs_hook=pairs_hook,
            parse_constant=reject_constant,
        )
    except json.JSONDecodeError as exc:
        raise InvalidStateSet(f"invalid {context} JSON: {exc}") from exc
    return _mapping(decoded, f"{context} JSON root")


def _dimension_definition_to_dict(
    value: CompetenceDimensionDefinition,
) -> dict[str, Any]:
    return {
        "key": value.key,
        "name": value.name,
        "description": value.description,
    }


def _dimension_definition_from_dict(
    value: object,
) -> CompetenceDimensionDefinition:
    data = _mapping(value, "competence dimension definition")
    allowed = {"key", "name", "description"}
    _keys(data, allowed, allowed, "competence dimension definition")
    return CompetenceDimensionDefinition(
        data["key"],
        data["name"],
        data["description"],
    )


def _frame_to_dict(value: CompetenceFrame) -> dict[str, Any]:
    return {
        "frame_id": str(value.frame_id),
        "revision": value.revision,
        "name": value.name,
        "description": value.description,
        "dimensions": [
            _dimension_definition_to_dict(item) for item in value.dimensions
        ],
    }


def _frame_from_dict(value: object) -> CompetenceFrame:
    data = _mapping(value, "competence frame")
    allowed = {
        "frame_id",
        "revision",
        "name",
        "description",
        "dimensions",
    }
    _keys(data, allowed, allowed, "competence frame")
    return CompetenceFrame(
        frame_id=CompetenceFrameId.parse(data["frame_id"]),
        revision=data["revision"],
        name=data["name"],
        description=data["description"],
        dimensions=tuple(
            _dimension_definition_from_dict(item)
            for item in _sequence(
                data["dimensions"],
                "competence frame dimensions",
            )
        ),
    )


def frame_catalog_to_dict(value: CompetenceFrameCatalog) -> dict[str, Any]:
    if not isinstance(value, CompetenceFrameCatalog):
        raise InvalidCompetenceFrame(
            "value must be CompetenceFrameCatalog"
        )
    return {
        "schema": _FRAME_SCHEMA,
        "frames": [_frame_to_dict(item) for item in value.frames],
    }


def frame_catalog_from_dict(payload: object) -> CompetenceFrameCatalog:
    try:
        data = _mapping(payload, "competence frame catalog")
        allowed = {"schema", "frames"}
        _keys(data, allowed, allowed, "competence frame catalog")
        if data["schema"] != _FRAME_SCHEMA:
            raise InvalidStateSet(
                f"unsupported competence-frame schema: {data['schema']!r}"
            )
        return CompetenceFrameCatalog(
            frames=tuple(
                _frame_from_dict(item)
                for item in _sequence(data["frames"], "frames")
            )
        )
    except InvalidCompetenceFrame:
        raise
    except InvalidStateSet as exc:
        raise InvalidCompetenceFrame(
            f"invalid competence frame catalog: {exc}"
        ) from exc
    except (TypeError, ValueError) as exc:
        raise InvalidCompetenceFrame(
            f"invalid competence frame catalog: {exc}"
        ) from exc


def loads_frame_catalog(payload: str) -> CompetenceFrameCatalog:
    try:
        decoded = _loads_strict(payload, "competence frame catalog")
    except InvalidStateSet as exc:
        raise InvalidCompetenceFrame(
            f"invalid competence frame catalog JSON: {exc}"
        ) from exc
    return frame_catalog_from_dict(decoded)


def _dimension_state_to_dict(
    value: CompetenceDimensionState,
) -> dict[str, Any]:
    return {
        "dimension_key": value.dimension_key,
        "standing": value.standing.value,
        "conflict_status": value.conflict_status.value,
        "supported_claim_ids": [
            str(item) for item in value.supported_claim_ids
        ],
        "basis_evaluation_ids": [
            str(item) for item in value.basis_evaluation_ids
        ],
        "rationale": value.rationale,
    }


def _dimension_state_from_dict(value: object) -> CompetenceDimensionState:
    data = _mapping(value, "competence dimension state")
    allowed = {
        "dimension_key",
        "standing",
        "conflict_status",
        "supported_claim_ids",
        "basis_evaluation_ids",
        "rationale",
    }
    _keys(data, allowed, allowed, "competence dimension state")
    return CompetenceDimensionState(
        dimension_key=data["dimension_key"],
        standing=_enum(
            DimensionStanding,
            data["standing"],
            "dimension standing",
        ),
        supported_claim_ids=tuple(
            CapabilityClaimId(item)
            for item in _strings(
                data["supported_claim_ids"],
                "supported_claim_ids",
            )
        ),
        basis_evaluation_ids=tuple(
            ClaimEvaluationId(item)
            for item in _strings(
                data["basis_evaluation_ids"],
                "basis_evaluation_ids",
            )
        ),
        rationale=data["rationale"],
        conflict_status=_enum(
            DimensionConflictStatus,
            data["conflict_status"],
            "dimension conflict status",
        ),
    )


def _state_to_dict(value: PersonalCapabilityState) -> dict[str, Any]:
    return {
        "state_id": str(value.state_id),
        "subject_ref": str(value.subject_ref),
        "concept_ref": str(value.concept_ref),
        "frame_ref": str(value.frame_ref),
        "derivation_policy_ref": str(value.derivation_policy_ref),
        "deriver_ref": {
            "kind": value.deriver_ref.kind.value,
            "ref": value.deriver_ref.ref,
        },
        "as_of": format_time(value.as_of),
        "derived_at": format_time(value.derived_at),
        "dimensions": [
            _dimension_state_to_dict(item) for item in value.dimensions
        ],
        "rationale": value.rationale,
    }


def _state_from_dict(value: object) -> PersonalCapabilityState:
    data = _mapping(value, "personal capability state")
    allowed = {
        "state_id",
        "subject_ref",
        "concept_ref",
        "frame_ref",
        "derivation_policy_ref",
        "deriver_ref",
        "as_of",
        "derived_at",
        "dimensions",
        "rationale",
    }
    _keys(data, allowed, allowed, "personal capability state")
    deriver = _mapping(data["deriver_ref"], "state deriver ref")
    _keys(
        deriver,
        {"kind", "ref"},
        {"kind", "ref"},
        "state deriver ref",
    )
    return PersonalCapabilityState(
        state_id=PersonalCapabilityStateId(data["state_id"]),
        subject_ref=CapabilitySubjectRef(data["subject_ref"]),
        concept_ref=CapabilityConceptRef.parse(data["concept_ref"]),
        frame_ref=CompetenceFrameRef.parse(data["frame_ref"]),
        derivation_policy_ref=StateDerivationPolicyRef.parse(
            data["derivation_policy_ref"]
        ),
        deriver_ref=StateDeriverRef(
            _enum(
                StateDeriverKind,
                deriver["kind"],
                "state deriver kind",
            ),
            deriver["ref"],
        ),
        as_of=parse_time(data["as_of"], "state as_of"),
        derived_at=parse_time(data["derived_at"], "state derived_at"),
        dimensions=tuple(
            _dimension_state_from_dict(item)
            for item in _sequence(data["dimensions"], "state dimensions")
        ),
        rationale=data["rationale"],
    )


def state_set_to_dict(value: PersonalCapabilityStateSet) -> dict[str, Any]:
    if not isinstance(value, PersonalCapabilityStateSet):
        raise InvalidStateSet(
            "value must be PersonalCapabilityStateSet"
        )
    return {
        "schema": _STATE_SCHEMA,
        "subject_ref": str(value.subject_ref),
        "states": [_state_to_dict(item) for item in value.states],
    }


def state_set_from_dict(payload: object) -> PersonalCapabilityStateSet:
    data = _mapping(payload, "personal capability state set")
    allowed = {"schema", "subject_ref", "states"}
    _keys(data, allowed, allowed, "personal capability state set")
    if data["schema"] != _STATE_SCHEMA:
        raise InvalidStateSet(
            "unsupported personal-capability-state schema: "
            f"{data['schema']!r}"
        )
    try:
        return PersonalCapabilityStateSet(
            subject_ref=CapabilitySubjectRef(data["subject_ref"]),
            states=tuple(
                _state_from_dict(item)
                for item in _sequence(data["states"], "states")
            ),
        )
    except StateError:
        raise
    except (TypeError, ValueError) as exc:
        raise InvalidStateSet(
            f"invalid personal capability state set: {exc}"
        ) from exc


def loads_state_set(payload: str) -> PersonalCapabilityStateSet:
    return state_set_from_dict(
        _loads_strict(payload, "personal capability state set")
    )
