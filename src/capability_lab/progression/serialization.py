"""Strict deterministic serialization for PR8 progression projections."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import re
from typing import Any, Mapping

from capability_lab.epistemics import CapabilitySubjectRef
from capability_lab.semantics import CapabilityConceptRef, RelationKind, RelationScope, RelationStrength
from capability_lab.state import CompetenceFrameRef, DimensionConflictStatus, PersonalCapabilityStateId

from .core import (
    ExplorationInput,
    ExplorationOpportunity,
    FrontierAdjacencyWitness,
    FrontierCandidate,
    FrontierSeedBinding,
    InvalidProgressionFrontier,
    InvalidProgressionRequest,
    InvalidProgressionSet,
    PrerequisiteCheckBinding,
    PrerequisiteDimensionGap,
    PrerequisiteDimensionGapKind,
    PrerequisiteEvidenceGap,
    ProgressionDeriverRef,
    ProgressionError,
    ProgressionFocus,
    ProgressionFrontier,
    ProgressionFrontierId,
    ProgressionFrontierRequest,
    ProgressionFrontierSet,
    ProgressionMechanismKind,
    ProgressionPolicyRef,
    ProgressionRelationWitness,
    ProgressionRequesterRef,
)

_SCHEMA_VERSION = 1
_TIME_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]{1,6})?(?:Z|[+-][0-9]{2}:[0-9]{2})$"
)


def request_to_json(request: ProgressionFrontierRequest) -> str:
    return _dumps(request_to_dict(request))


def request_from_json(payload: object) -> ProgressionFrontierRequest:
    return request_from_dict(_loads(payload, "progression request"))


def request_to_dict(request: ProgressionFrontierRequest) -> dict[str, Any]:
    if not isinstance(request, ProgressionFrontierRequest):
        raise InvalidProgressionRequest("request must be ProgressionFrontierRequest")
    return {"schema_version": _SCHEMA_VERSION, "request": _request_record_to_dict(request)}


def request_from_dict(payload: object) -> ProgressionFrontierRequest:
    mapping = _mapping(payload, "progression request", InvalidProgressionRequest)
    _keys(mapping, {"schema_version", "request"}, "progression request", InvalidProgressionRequest)
    _schema(mapping["schema_version"], "progression request", InvalidProgressionRequest)
    return _request_record_from_dict(mapping["request"])


def frontier_to_json(frontier: ProgressionFrontier) -> str:
    return _dumps(frontier_to_dict(frontier))


def frontier_from_json(payload: object) -> ProgressionFrontier:
    return frontier_from_dict(_loads(payload, "progression frontier"))


def frontier_to_dict(frontier: ProgressionFrontier) -> dict[str, Any]:
    if not isinstance(frontier, ProgressionFrontier):
        raise InvalidProgressionFrontier("frontier must be ProgressionFrontier")
    return {"schema_version": _SCHEMA_VERSION, "frontier": _frontier_record_to_dict(frontier)}


def frontier_from_dict(payload: object) -> ProgressionFrontier:
    mapping = _mapping(payload, "progression frontier", InvalidProgressionFrontier)
    _keys(mapping, {"schema_version", "frontier"}, "progression frontier", InvalidProgressionFrontier)
    _schema(mapping["schema_version"], "progression frontier", InvalidProgressionFrontier)
    return _frontier_record_from_dict(mapping["frontier"])


def frontier_set_to_json(frontier_set: ProgressionFrontierSet) -> str:
    return _dumps(frontier_set_to_dict(frontier_set))


def frontier_set_from_json(payload: object) -> ProgressionFrontierSet:
    return frontier_set_from_dict(_loads(payload, "progression frontier set"))


def frontier_set_to_dict(frontier_set: ProgressionFrontierSet) -> dict[str, Any]:
    if not isinstance(frontier_set, ProgressionFrontierSet):
        raise InvalidProgressionSet("frontier_set must be ProgressionFrontierSet")
    return {
        "schema_version": _SCHEMA_VERSION,
        "subject_ref": str(frontier_set.subject_ref),
        "frontiers": [_frontier_record_to_dict(item) for item in frontier_set.frontiers],
    }


def frontier_set_from_dict(payload: object) -> ProgressionFrontierSet:
    mapping = _mapping(payload, "progression frontier set", InvalidProgressionSet)
    _keys(mapping, {"schema_version", "subject_ref", "frontiers"}, "progression frontier set", InvalidProgressionSet)
    _schema(mapping["schema_version"], "progression frontier set", InvalidProgressionSet)
    return ProgressionFrontierSet(
        subject_ref=CapabilitySubjectRef(_string(mapping["subject_ref"], "subject_ref", InvalidProgressionSet)),
        frontiers=tuple(_frontier_record_from_dict(item) for item in _list(mapping["frontiers"], "frontiers", InvalidProgressionSet)),
    )


def _request_record_to_dict(request: ProgressionFrontierRequest) -> dict[str, Any]:
    return {
        "frontier_id": str(request.frontier_id),
        "subject_ref": str(request.subject_ref),
        "as_of": _format_time(request.as_of),
        "generated_at": _format_time(request.generated_at),
        "requester_ref": _mechanism_to_dict(request.requester_ref),
        "focuses": [_focus_to_dict(item) for item in request.focuses],
        "seed_bindings": [_seed_to_dict(item) for item in request.seed_bindings],
        "prerequisite_bindings": [_prerequisite_binding_to_dict(item) for item in request.prerequisite_bindings],
        "exploration_inputs": [_exploration_input_to_dict(item) for item in request.exploration_inputs],
    }


def _request_record_from_dict(payload: object) -> ProgressionFrontierRequest:
    mapping = _mapping(payload, "progression request record", InvalidProgressionRequest)
    expected = {"frontier_id", "subject_ref", "as_of", "generated_at", "requester_ref", "focuses", "seed_bindings", "prerequisite_bindings", "exploration_inputs"}
    _keys(mapping, expected, "progression request record", InvalidProgressionRequest)
    return ProgressionFrontierRequest(
        frontier_id=ProgressionFrontierId(_string(mapping["frontier_id"], "frontier_id", InvalidProgressionRequest)),
        subject_ref=CapabilitySubjectRef(_string(mapping["subject_ref"], "subject_ref", InvalidProgressionRequest)),
        as_of=_parse_time(mapping["as_of"], "request as_of", InvalidProgressionRequest),
        generated_at=_parse_time(mapping["generated_at"], "request generated_at", InvalidProgressionRequest),
        requester_ref=_requester_from_dict(mapping["requester_ref"]),
        focuses=tuple(_focus_from_dict(item) for item in _list(mapping["focuses"], "focuses", InvalidProgressionRequest)),
        seed_bindings=tuple(_seed_from_dict(item) for item in _list(mapping["seed_bindings"], "seed_bindings", InvalidProgressionRequest)),
        prerequisite_bindings=tuple(_prerequisite_binding_from_dict(item) for item in _list(mapping["prerequisite_bindings"], "prerequisite_bindings", InvalidProgressionRequest)),
        exploration_inputs=tuple(_exploration_input_from_dict(item) for item in _list(mapping["exploration_inputs"], "exploration_inputs", InvalidProgressionRequest)),
    )


def _frontier_record_to_dict(frontier: ProgressionFrontier) -> dict[str, Any]:
    return {
        "frontier_id": str(frontier.frontier_id),
        "subject_ref": str(frontier.subject_ref),
        "as_of": _format_time(frontier.as_of),
        "generated_at": _format_time(frontier.generated_at),
        "policy_ref": str(frontier.policy_ref),
        "deriver_ref": _mechanism_to_dict(frontier.deriver_ref),
        "requester_ref": _mechanism_to_dict(frontier.requester_ref),
        "focuses": [_focus_to_dict(item) for item in frontier.focuses],
        "seed_bindings": [_seed_to_dict(item) for item in frontier.seed_bindings],
        "prerequisite_bindings": [_prerequisite_binding_to_dict(item) for item in frontier.prerequisite_bindings],
        "exploration_inputs": [_exploration_input_to_dict(item) for item in frontier.exploration_inputs],
        "candidates": [_candidate_to_dict(item) for item in frontier.candidates],
        "prerequisite_gaps": [_gap_to_dict(item) for item in frontier.prerequisite_gaps],
        "exploration_opportunities": [_opportunity_to_dict(item) for item in frontier.exploration_opportunities],
        "rationale": frontier.rationale,
    }


def _frontier_record_from_dict(payload: object) -> ProgressionFrontier:
    mapping = _mapping(payload, "progression frontier record", InvalidProgressionFrontier)
    expected = {"frontier_id", "subject_ref", "as_of", "generated_at", "policy_ref", "deriver_ref", "requester_ref", "focuses", "seed_bindings", "prerequisite_bindings", "exploration_inputs", "candidates", "prerequisite_gaps", "exploration_opportunities", "rationale"}
    _keys(mapping, expected, "progression frontier record", InvalidProgressionFrontier)
    return ProgressionFrontier(
        frontier_id=ProgressionFrontierId(_string(mapping["frontier_id"], "frontier_id", InvalidProgressionFrontier)),
        subject_ref=CapabilitySubjectRef(_string(mapping["subject_ref"], "subject_ref", InvalidProgressionFrontier)),
        as_of=_parse_time(mapping["as_of"], "frontier as_of", InvalidProgressionFrontier),
        generated_at=_parse_time(mapping["generated_at"], "frontier generated_at", InvalidProgressionFrontier),
        policy_ref=ProgressionPolicyRef.parse(_string(mapping["policy_ref"], "policy_ref", InvalidProgressionFrontier)),
        deriver_ref=_deriver_from_dict(mapping["deriver_ref"]),
        requester_ref=_requester_from_dict(mapping["requester_ref"]),
        focuses=tuple(_focus_from_dict(item, InvalidProgressionFrontier) for item in _list(mapping["focuses"], "focuses", InvalidProgressionFrontier)),
        seed_bindings=tuple(_seed_from_dict(item, InvalidProgressionFrontier) for item in _list(mapping["seed_bindings"], "seed_bindings", InvalidProgressionFrontier)),
        prerequisite_bindings=tuple(_prerequisite_binding_from_dict(item, InvalidProgressionFrontier) for item in _list(mapping["prerequisite_bindings"], "prerequisite_bindings", InvalidProgressionFrontier)),
        exploration_inputs=tuple(_exploration_input_from_dict(item, InvalidProgressionFrontier) for item in _list(mapping["exploration_inputs"], "exploration_inputs", InvalidProgressionFrontier)),
        candidates=tuple(_candidate_from_dict(item) for item in _list(mapping["candidates"], "candidates", InvalidProgressionFrontier)),
        prerequisite_gaps=tuple(_gap_from_dict(item) for item in _list(mapping["prerequisite_gaps"], "prerequisite_gaps", InvalidProgressionFrontier)),
        exploration_opportunities=tuple(_opportunity_from_dict(item) for item in _list(mapping["exploration_opportunities"], "exploration_opportunities", InvalidProgressionFrontier)),
        rationale=_string(mapping["rationale"], "rationale", InvalidProgressionFrontier),
    )


def _focus_to_dict(item: ProgressionFocus) -> dict[str, Any]:
    return {"concept_ref": str(item.concept_ref), "rationale": item.rationale}


def _focus_from_dict(payload: object, error_type=InvalidProgressionRequest) -> ProgressionFocus:
    mapping = _mapping(payload, "focus", error_type)
    _keys(mapping, {"concept_ref", "rationale"}, "focus", error_type)
    try:
        return ProgressionFocus(CapabilityConceptRef.parse(_string(mapping["concept_ref"], "concept_ref", error_type)), _string(mapping["rationale"], "rationale", error_type))
    except ProgressionError:
        raise
    except ValueError as exc:
        raise error_type(str(exc)) from exc


def _seed_to_dict(item: FrontierSeedBinding) -> dict[str, Any]:
    return {"state_id": str(item.state_id), "dimension_keys": list(item.dimension_keys)}


def _seed_from_dict(payload: object, error_type=InvalidProgressionRequest) -> FrontierSeedBinding:
    mapping = _mapping(payload, "seed binding", error_type)
    _keys(mapping, {"state_id", "dimension_keys"}, "seed binding", error_type)
    return FrontierSeedBinding(
        state_id=PersonalCapabilityStateId(_string(mapping["state_id"], "state_id", error_type)),
        dimension_keys=tuple(_string(x, "dimension key", error_type) for x in _list(mapping["dimension_keys"], "dimension_keys", error_type)),
    )


def _scope_to_dict(scope: RelationScope | None):
    if scope is None:
        return None
    return {"key": scope.key, "description": scope.description}


def _scope_from_dict(payload: object, error_type):
    if payload is None:
        return None
    mapping = _mapping(payload, "relation scope", error_type)
    _keys(mapping, {"key", "description"}, "relation scope", error_type)
    try:
        return RelationScope(_string(mapping["key"], "scope key", error_type), _string(mapping["description"], "scope description", error_type))
    except ValueError as exc:
        raise error_type(str(exc)) from exc


def _prerequisite_binding_to_dict(item: PrerequisiteCheckBinding) -> dict[str, Any]:
    return {
        "target_ref": str(item.target_ref),
        "prerequisite_ref": str(item.prerequisite_ref),
        "relation_scope": _scope_to_dict(item.relation_scope),
        "frame_ref": str(item.frame_ref),
        "required_dimension_keys": list(item.required_dimension_keys),
        "state_id": str(item.state_id) if item.state_id is not None else None,
    }


def _prerequisite_binding_from_dict(payload: object, error_type=InvalidProgressionRequest) -> PrerequisiteCheckBinding:
    mapping = _mapping(payload, "prerequisite binding", error_type)
    expected = {"target_ref", "prerequisite_ref", "relation_scope", "frame_ref", "required_dimension_keys", "state_id"}
    _keys(mapping, expected, "prerequisite binding", error_type)
    try:
        return PrerequisiteCheckBinding(
            target_ref=CapabilityConceptRef.parse(_string(mapping["target_ref"], "target_ref", error_type)),
            prerequisite_ref=CapabilityConceptRef.parse(_string(mapping["prerequisite_ref"], "prerequisite_ref", error_type)),
            relation_scope=_scope_from_dict(mapping["relation_scope"], error_type),
            frame_ref=CompetenceFrameRef.parse(_string(mapping["frame_ref"], "frame_ref", error_type)),
            required_dimension_keys=tuple(_string(x, "required dimension key", error_type) for x in _list(mapping["required_dimension_keys"], "required_dimension_keys", error_type)),
            state_id=None if mapping["state_id"] is None else PersonalCapabilityStateId(_string(mapping["state_id"], "state_id", error_type)),
        )
    except ProgressionError:
        raise
    except ValueError as exc:
        raise error_type(str(exc)) from exc


def _exploration_input_to_dict(item: ExplorationInput) -> dict[str, Any]:
    return {"concept_ref": str(item.concept_ref), "rationale": item.rationale}


def _exploration_input_from_dict(payload: object, error_type=InvalidProgressionRequest) -> ExplorationInput:
    mapping = _mapping(payload, "exploration input", error_type)
    _keys(mapping, {"concept_ref", "rationale"}, "exploration input", error_type)
    try:
        return ExplorationInput(CapabilityConceptRef.parse(_string(mapping["concept_ref"], "concept_ref", error_type)), _string(mapping["rationale"], "rationale", error_type))
    except ProgressionError:
        raise
    except ValueError as exc:
        raise error_type(str(exc)) from exc


def _relation_to_dict(item: ProgressionRelationWitness) -> dict[str, Any]:
    return {"source_ref": str(item.source_ref), "target_ref": str(item.target_ref), "kind": item.kind.value, "scope": _scope_to_dict(item.scope), "strength": item.strength.value}


def _relation_from_dict(payload: object) -> ProgressionRelationWitness:
    mapping = _mapping(payload, "relation witness", InvalidProgressionFrontier)
    _keys(mapping, {"source_ref", "target_ref", "kind", "scope", "strength"}, "relation witness", InvalidProgressionFrontier)
    try:
        kind = RelationKind(_string(mapping["kind"], "relation kind", InvalidProgressionFrontier))
        strength = RelationStrength(_string(mapping["strength"], "relation strength", InvalidProgressionFrontier))
        return ProgressionRelationWitness(
            CapabilityConceptRef.parse(_string(mapping["source_ref"], "source_ref", InvalidProgressionFrontier)),
            CapabilityConceptRef.parse(_string(mapping["target_ref"], "target_ref", InvalidProgressionFrontier)),
            kind,
            _scope_from_dict(mapping["scope"], InvalidProgressionFrontier),
            strength,
        )
    except ProgressionError:
        raise
    except ValueError as exc:
        raise InvalidProgressionFrontier("invalid relation witness enum/reference") from exc


def _adjacency_to_dict(item: FrontierAdjacencyWitness) -> dict[str, Any]:
    return {"state_id": str(item.state_id), "seed_concept_ref": str(item.seed_concept_ref), "seed_dimension_keys": list(item.seed_dimension_keys), "relation": _relation_to_dict(item.relation)}


def _adjacency_from_dict(payload: object) -> FrontierAdjacencyWitness:
    mapping = _mapping(payload, "adjacency witness", InvalidProgressionFrontier)
    _keys(mapping, {"state_id", "seed_concept_ref", "seed_dimension_keys", "relation"}, "adjacency witness", InvalidProgressionFrontier)
    try:
        seed_ref = CapabilityConceptRef.parse(_string(mapping["seed_concept_ref"], "seed_concept_ref", InvalidProgressionFrontier))
    except ValueError as exc:
        raise InvalidProgressionFrontier(str(exc)) from exc
    return FrontierAdjacencyWitness(
        PersonalCapabilityStateId(_string(mapping["state_id"], "state_id", InvalidProgressionFrontier)),
        seed_ref,
        tuple(_string(x, "seed dimension key", InvalidProgressionFrontier) for x in _list(mapping["seed_dimension_keys"], "seed_dimension_keys", InvalidProgressionFrontier)),
        _relation_from_dict(mapping["relation"]),
    )


def _candidate_to_dict(item: FrontierCandidate) -> dict[str, Any]:
    return {
        "concept_ref": str(item.concept_ref),
        "explicit_focus": item.explicit_focus,
        "adjacency_witnesses": [_adjacency_to_dict(x) for x in item.adjacency_witnesses],
        "assessed_prerequisites": [_relation_to_dict(x) for x in item.assessed_prerequisites],
        "unassessed_prerequisites": [_relation_to_dict(x) for x in item.unassessed_prerequisites],
    }


def _candidate_from_dict(payload: object) -> FrontierCandidate:
    mapping = _mapping(payload, "frontier candidate", InvalidProgressionFrontier)
    expected = {"concept_ref", "explicit_focus", "adjacency_witnesses", "assessed_prerequisites", "unassessed_prerequisites"}
    _keys(mapping, expected, "frontier candidate", InvalidProgressionFrontier)
    if not isinstance(mapping["explicit_focus"], bool):
        raise InvalidProgressionFrontier("explicit_focus must be a boolean")
    try:
        ref = CapabilityConceptRef.parse(_string(mapping["concept_ref"], "concept_ref", InvalidProgressionFrontier))
    except ValueError as exc:
        raise InvalidProgressionFrontier(str(exc)) from exc
    return FrontierCandidate(
        ref,
        mapping["explicit_focus"],
        tuple(_adjacency_from_dict(x) for x in _list(mapping["adjacency_witnesses"], "adjacency_witnesses", InvalidProgressionFrontier)),
        tuple(_relation_from_dict(x) for x in _list(mapping["assessed_prerequisites"], "assessed_prerequisites", InvalidProgressionFrontier)),
        tuple(_relation_from_dict(x) for x in _list(mapping["unassessed_prerequisites"], "unassessed_prerequisites", InvalidProgressionFrontier)),
    )


def _dimension_gap_to_dict(item: PrerequisiteDimensionGap) -> dict[str, Any]:
    return {"dimension_key": item.dimension_key, "kind": item.kind.value, "conflict_status": item.conflict_status.value if item.conflict_status is not None else None}


def _dimension_gap_from_dict(payload: object) -> PrerequisiteDimensionGap:
    mapping = _mapping(payload, "prerequisite dimension gap", InvalidProgressionFrontier)
    _keys(mapping, {"dimension_key", "kind", "conflict_status"}, "prerequisite dimension gap", InvalidProgressionFrontier)
    try:
        kind = PrerequisiteDimensionGapKind(_string(mapping["kind"], "gap kind", InvalidProgressionFrontier))
        conflict = None if mapping["conflict_status"] is None else DimensionConflictStatus(_string(mapping["conflict_status"], "conflict_status", InvalidProgressionFrontier))
    except ValueError as exc:
        raise InvalidProgressionFrontier("unknown prerequisite gap enum") from exc
    return PrerequisiteDimensionGap(_string(mapping["dimension_key"], "dimension_key", InvalidProgressionFrontier), kind, conflict)


def _gap_to_dict(item: PrerequisiteEvidenceGap) -> dict[str, Any]:
    return {
        "target_ref": str(item.target_ref), "prerequisite_ref": str(item.prerequisite_ref),
        "relation": _relation_to_dict(item.relation), "frame_ref": str(item.frame_ref),
        "state_id": str(item.state_id) if item.state_id is not None else None,
        "dimension_gaps": [_dimension_gap_to_dict(x) for x in item.dimension_gaps],
    }


def _gap_from_dict(payload: object) -> PrerequisiteEvidenceGap:
    mapping = _mapping(payload, "prerequisite evidence gap", InvalidProgressionFrontier)
    expected = {"target_ref", "prerequisite_ref", "relation", "frame_ref", "state_id", "dimension_gaps"}
    _keys(mapping, expected, "prerequisite evidence gap", InvalidProgressionFrontier)
    try:
        target = CapabilityConceptRef.parse(_string(mapping["target_ref"], "target_ref", InvalidProgressionFrontier))
        prerequisite = CapabilityConceptRef.parse(_string(mapping["prerequisite_ref"], "prerequisite_ref", InvalidProgressionFrontier))
        frame = CompetenceFrameRef.parse(_string(mapping["frame_ref"], "frame_ref", InvalidProgressionFrontier))
    except ValueError as exc:
        raise InvalidProgressionFrontier(str(exc)) from exc
    return PrerequisiteEvidenceGap(
        target, prerequisite, _relation_from_dict(mapping["relation"]), frame,
        None if mapping["state_id"] is None else PersonalCapabilityStateId(_string(mapping["state_id"], "state_id", InvalidProgressionFrontier)),
        tuple(_dimension_gap_from_dict(x) for x in _list(mapping["dimension_gaps"], "dimension_gaps", InvalidProgressionFrontier)),
    )


def _opportunity_to_dict(item: ExplorationOpportunity) -> dict[str, Any]:
    return {"concept_ref": str(item.concept_ref), "rationale": item.rationale}


def _opportunity_from_dict(payload: object) -> ExplorationOpportunity:
    mapping = _mapping(payload, "exploration opportunity", InvalidProgressionFrontier)
    _keys(mapping, {"concept_ref", "rationale"}, "exploration opportunity", InvalidProgressionFrontier)
    try:
        ref = CapabilityConceptRef.parse(_string(mapping["concept_ref"], "concept_ref", InvalidProgressionFrontier))
    except ValueError as exc:
        raise InvalidProgressionFrontier(str(exc)) from exc
    return ExplorationOpportunity(ref, _string(mapping["rationale"], "rationale", InvalidProgressionFrontier))


def _mechanism_to_dict(item) -> dict[str, str]:
    return {"kind": item.kind.value, "ref": item.ref}


def _requester_from_dict(payload: object) -> ProgressionRequesterRef:
    mapping = _mapping(payload, "requester ref", InvalidProgressionRequest)
    _keys(mapping, {"kind", "ref"}, "requester ref", InvalidProgressionRequest)
    try:
        kind = ProgressionMechanismKind(_string(mapping["kind"], "requester kind", InvalidProgressionRequest))
    except ValueError as exc:
        raise InvalidProgressionRequest("unknown requester mechanism kind") from exc
    return ProgressionRequesterRef(kind, _string(mapping["ref"], "requester ref", InvalidProgressionRequest))


def _deriver_from_dict(payload: object) -> ProgressionDeriverRef:
    mapping = _mapping(payload, "deriver ref", InvalidProgressionFrontier)
    _keys(mapping, {"kind", "ref"}, "deriver ref", InvalidProgressionFrontier)
    try:
        kind = ProgressionMechanismKind(_string(mapping["kind"], "deriver kind", InvalidProgressionFrontier))
    except ValueError as exc:
        raise InvalidProgressionFrontier("unknown deriver mechanism kind") from exc
    return ProgressionDeriverRef(kind, _string(mapping["ref"], "deriver ref", InvalidProgressionFrontier))


def _dumps(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _loads(payload: object, label: str) -> object:
    if not isinstance(payload, str):
        raise ProgressionError(f"{label} JSON payload must be a string")

    def reject_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ProgressionError(f"duplicate JSON object key: {key!r}")
            result[key] = value
        return result

    def reject_constant(value: str):
        raise ProgressionError(f"non-finite JSON number is forbidden: {value}")

    try:
        return json.loads(payload, object_pairs_hook=reject_duplicates, parse_constant=reject_constant)
    except ProgressionError:
        raise
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ProgressionError(f"{label} JSON payload must be valid strict JSON") from exc


def _mapping(value: object, label: str, error_type) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise error_type(f"{label} must be an object")
    if any(not isinstance(key, str) for key in value):
        raise error_type(f"{label} keys must be strings")
    return value


def _keys(mapping: Mapping[str, Any], expected: set[str], label: str, error_type) -> None:
    actual = set(mapping)
    if actual != expected:
        raise error_type(f"{label} fields mismatch: missing={sorted(expected-actual)}, extra={sorted(actual-expected)}")


def _list(value: object, label: str, error_type) -> list[Any]:
    if not isinstance(value, list):
        raise error_type(f"{label} must be a JSON array")
    return value


def _string(value: object, label: str, error_type) -> str:
    if not isinstance(value, str):
        raise error_type(f"{label} must be a string")
    return value


def _schema(value: object, label: str, error_type) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value != _SCHEMA_VERSION:
        raise error_type(f"{label} schema_version must be exact integer {_SCHEMA_VERSION}")


def _format_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_time(value: object, field_name: str, error_type) -> datetime:
    if not isinstance(value, str) or _TIME_RE.fullmatch(value) is None:
        raise error_type(f"{field_name} must use YYYY-MM-DDTHH:MM:SS[.ffffff](Z|±HH:MM)")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise error_type(f"{field_name} must be valid ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise error_type(f"{field_name} must be timezone-aware")
    return parsed.astimezone(timezone.utc)
