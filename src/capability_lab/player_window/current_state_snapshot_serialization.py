"""Strict canonical serialization for PR11.11 governed read snapshots."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import re

from capability_lab.epistemics import CapabilitySubjectRef
from capability_lab.history import AchievementInstanceId, PersonalLegendId, PersonalMilestoneEventId
from capability_lab.progression import (
    CurrentStatePrerequisiteCheck,
    CurrentStateProgressionAuthorityBinding,
    CurrentStateProgressionAuthorityStatus,
    CurrentStateProgressionFrontierRequest,
    CurrentStateProgressionSeed,
    ExplorationInput,
    ProgressionFocus,
    ProgressionFrontierId,
    ProgressionMechanismKind,
    ProgressionRequesterRef,
)
from capability_lab.semantics import CapabilityConceptRef, RelationScope
from capability_lab.state import (
    CompetenceFrameRef,
    CurrentStateSelectionAction,
    PersonalCapabilityCurrentStatePortfolioEntry,
    PersonalCapabilityStateId,
)
from .core import (
    PlayerWindowId,
    PlayerWindowMechanismKind,
    PlayerWindowRequesterRef,
    PlayerWindowViewerRef,
)
from .serialization import window_from_dict, window_to_dict
from .current_state_snapshot import (
    CurrentStateGovernedPlayerWindow,
    CurrentStatePlayerWindowRequest,
    InvalidCurrentStateGovernedPlayerWindow,
)


_SCHEMA_VERSION = 1
_TS_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})$"
)


def dumps_canonical(payload: object) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _fail(message: str):
    raise InvalidCurrentStateGovernedPlayerWindow(message)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            _fail("duplicate JSON object keys are not allowed")
        result[key] = value
    return result


def _constant(value):
    _fail(f"non-finite JSON constant is not allowed: {value}")


def _loads(payload: str):
    if type(payload) is not str:
        _fail("JSON payload must be a string")
    try:
        return json.loads(
            payload,
            object_pairs_hook=_pairs,
            parse_constant=_constant,
        )
    except json.JSONDecodeError as exc:
        _fail(f"invalid JSON: {exc.msg}")


def _obj(value, keys, label):
    if type(value) is not dict or set(value) != set(keys):
        _fail(f"{label} must contain exactly: {', '.join(sorted(keys))}")
    return value


def _list(value, label):
    if type(value) is not list:
        _fail(f"{label} must be a JSON array")
    return value


def _schema(value):
    if type(value) is not int or value != _SCHEMA_VERSION:
        _fail(f"schema_version must be integer {_SCHEMA_VERSION}")


def _ts(value: datetime) -> str:
    text = value.astimezone(timezone.utc).isoformat(timespec="microseconds")
    text = text.replace("+00:00", "Z")
    return text.replace(".000000Z", "Z")


def _parse_ts(value, label):
    if type(value) is not str or _TS_RE.fullmatch(value) is None:
        _fail(f"{label} must use strict extended timezone-aware ISO-8601 syntax")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(
            timezone.utc
        )
    except ValueError as exc:
        raise InvalidCurrentStateGovernedPlayerWindow(
            f"invalid {label}"
        ) from exc


def _mechanism(value):
    return {"kind": value.kind.value, "ref": value.ref}


def _player_mechanism(payload, cls):
    obj = _obj(payload, {"kind", "ref"}, "player-window mechanism ref")
    try:
        return cls(PlayerWindowMechanismKind(obj["kind"]), obj["ref"])
    except (TypeError, ValueError) as exc:
        raise InvalidCurrentStateGovernedPlayerWindow(
            f"invalid player-window mechanism ref: {exc}"
        ) from exc


def _progression_mechanism(payload):
    obj = _obj(payload, {"kind", "ref"}, "progression requester ref")
    try:
        return ProgressionRequesterRef(
            ProgressionMechanismKind(obj["kind"]),
            obj["ref"],
        )
    except (TypeError, ValueError) as exc:
        raise InvalidCurrentStateGovernedPlayerWindow(
            f"invalid progression requester ref: {exc}"
        ) from exc


def _progression_to_dict(value: CurrentStateProgressionFrontierRequest) -> dict:
    return {
        "frontier_id": str(value.frontier_id),
        "as_of": _ts(value.as_of),
        "generated_at": _ts(value.generated_at),
        "requester_ref": _mechanism(value.requester_ref),
        "focuses": [
            {
                "concept_ref": str(item.concept_ref),
                "rationale": item.rationale,
            }
            for item in value.focuses
        ],
        "seeds": [
            {
                "concept_ref": str(item.concept_ref),
                "frame_ref": str(item.frame_ref),
                "dimension_keys": list(item.dimension_keys),
            }
            for item in value.seeds
        ],
        "prerequisite_checks": [
            {
                "target_ref": str(item.target_ref),
                "prerequisite_ref": str(item.prerequisite_ref),
                "relation_scope": (
                    None
                    if item.relation_scope is None
                    else {
                        "key": item.relation_scope.key,
                        "description": item.relation_scope.description,
                    }
                ),
                "frame_ref": str(item.frame_ref),
                "required_dimension_keys": list(item.required_dimension_keys),
            }
            for item in value.prerequisite_checks
        ],
        "exploration_inputs": [
            {
                "concept_ref": str(item.concept_ref),
                "rationale": item.rationale,
            }
            for item in value.exploration_inputs
        ],
    }


def _progression_from_dict(payload) -> CurrentStateProgressionFrontierRequest:
    obj = _obj(
        payload,
        {
            "frontier_id",
            "as_of",
            "generated_at",
            "requester_ref",
            "focuses",
            "seeds",
            "prerequisite_checks",
            "exploration_inputs",
        },
        "progression_request",
    )
    focuses = []
    for value in _list(obj["focuses"], "focuses"):
        item = _obj(value, {"concept_ref", "rationale"}, "progression focus")
        focuses.append(
            ProgressionFocus(
                CapabilityConceptRef.parse(item["concept_ref"]),
                item["rationale"],
            )
        )

    seeds = []
    for value in _list(obj["seeds"], "seeds"):
        item = _obj(
            value,
            {"concept_ref", "frame_ref", "dimension_keys"},
            "progression seed",
        )
        seeds.append(
            CurrentStateProgressionSeed(
                concept_ref=CapabilityConceptRef.parse(item["concept_ref"]),
                frame_ref=CompetenceFrameRef.parse(item["frame_ref"]),
                dimension_keys=tuple(_list(item["dimension_keys"], "dimension_keys")),
            )
        )

    checks = []
    for value in _list(obj["prerequisite_checks"], "prerequisite_checks"):
        item = _obj(
            value,
            {
                "target_ref",
                "prerequisite_ref",
                "relation_scope",
                "frame_ref",
                "required_dimension_keys",
            },
            "progression prerequisite check",
        )
        relation_scope = item["relation_scope"]
        if relation_scope is not None:
            relation_scope = _obj(
                relation_scope,
                {"key", "description"},
                "relation_scope",
            )
            relation_scope = RelationScope(
                relation_scope["key"],
                relation_scope["description"],
            )
        checks.append(
            CurrentStatePrerequisiteCheck(
                target_ref=CapabilityConceptRef.parse(item["target_ref"]),
                prerequisite_ref=CapabilityConceptRef.parse(item["prerequisite_ref"]),
                relation_scope=relation_scope,
                frame_ref=CompetenceFrameRef.parse(item["frame_ref"]),
                required_dimension_keys=tuple(
                    _list(
                        item["required_dimension_keys"],
                        "required_dimension_keys",
                    )
                ),
            )
        )

    exploration = []
    for value in _list(obj["exploration_inputs"], "exploration_inputs"):
        item = _obj(
            value,
            {"concept_ref", "rationale"},
            "progression exploration input",
        )
        exploration.append(
            ExplorationInput(
                CapabilityConceptRef.parse(item["concept_ref"]),
                item["rationale"],
            )
        )

    try:
        return CurrentStateProgressionFrontierRequest(
            frontier_id=ProgressionFrontierId(obj["frontier_id"]),
            as_of=_parse_ts(obj["as_of"], "progression as_of"),
            generated_at=_parse_ts(
                obj["generated_at"],
                "progression generated_at",
            ),
            requester_ref=_progression_mechanism(obj["requester_ref"]),
            focuses=tuple(focuses),
            seeds=tuple(seeds),
            prerequisite_checks=tuple(checks),
            exploration_inputs=tuple(exploration),
        )
    except (TypeError, ValueError) as exc:
        raise InvalidCurrentStateGovernedPlayerWindow(
            f"invalid progression_request: {exc}"
        ) from exc


def request_to_dict(value: CurrentStatePlayerWindowRequest) -> dict:
    if type(value) is not CurrentStatePlayerWindowRequest:
        _fail("request must be CurrentStatePlayerWindowRequest")
    return {
        "schema_version": _SCHEMA_VERSION,
        "window_id": str(value.window_id),
        "generated_at": _ts(value.generated_at),
        "requester_ref": _mechanism(value.requester_ref),
        "viewer_ref": _mechanism(value.viewer_ref),
        "progression_request": _progression_to_dict(value.progression_request),
        "visible_achievement_ids": [
            str(item) for item in value.visible_achievement_ids
        ],
        "visible_milestone_ids": [
            str(item) for item in value.visible_milestone_ids
        ],
        "visible_legend_id": (
            str(value.visible_legend_id)
            if value.visible_legend_id is not None
            else None
        ),
    }


def request_from_dict(payload: object) -> CurrentStatePlayerWindowRequest:
    obj = _obj(
        payload,
        {
            "schema_version",
            "window_id",
            "generated_at",
            "requester_ref",
            "viewer_ref",
            "progression_request",
            "visible_achievement_ids",
            "visible_milestone_ids",
            "visible_legend_id",
        },
        "current-state player-window request",
    )
    _schema(obj["schema_version"])
    try:
        return CurrentStatePlayerWindowRequest(
            window_id=PlayerWindowId(obj["window_id"]),
            generated_at=_parse_ts(obj["generated_at"], "generated_at"),
            requester_ref=_player_mechanism(
                obj["requester_ref"],
                PlayerWindowRequesterRef,
            ),
            viewer_ref=_player_mechanism(
                obj["viewer_ref"],
                PlayerWindowViewerRef,
            ),
            progression_request=_progression_from_dict(
                obj["progression_request"]
            ),
            visible_achievement_ids=tuple(
                AchievementInstanceId(item)
                for item in _list(
                    obj["visible_achievement_ids"],
                    "visible_achievement_ids",
                )
            ),
            visible_milestone_ids=tuple(
                PersonalMilestoneEventId(item)
                for item in _list(
                    obj["visible_milestone_ids"],
                    "visible_milestone_ids",
                )
            ),
            visible_legend_id=(
                PersonalLegendId(obj["visible_legend_id"])
                if obj["visible_legend_id"] is not None
                else None
            ),
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InvalidCurrentStateGovernedPlayerWindow):
            raise
        raise InvalidCurrentStateGovernedPlayerWindow(
            f"invalid current-state player-window request: {exc}"
        ) from exc


def request_to_json(value: CurrentStatePlayerWindowRequest) -> str:
    return dumps_canonical(request_to_dict(value))


def request_from_json(payload: str) -> CurrentStatePlayerWindowRequest:
    return request_from_dict(_loads(payload))


def _entry_to_dict(item: PersonalCapabilityCurrentStatePortfolioEntry) -> dict:
    return {
        "concept_ref": str(item.concept_ref),
        "frame_ref": str(item.frame_ref),
        "action": item.action.value,
        "current_selection_sha256": item.current_selection_sha256,
        "selected_state_id": (
            str(item.selected_state_id)
            if item.selected_state_id is not None
            else None
        ),
        "selected_state_sha256": item.selected_state_sha256,
    }


def _entry_from_dict(payload) -> PersonalCapabilityCurrentStatePortfolioEntry:
    obj = _obj(
        payload,
        {
            "concept_ref",
            "frame_ref",
            "action",
            "current_selection_sha256",
            "selected_state_id",
            "selected_state_sha256",
        },
        "current-state entry",
    )
    try:
        return PersonalCapabilityCurrentStatePortfolioEntry(
            concept_ref=CapabilityConceptRef.parse(obj["concept_ref"]),
            frame_ref=CompetenceFrameRef.parse(obj["frame_ref"]),
            action=CurrentStateSelectionAction(obj["action"]),
            current_selection_sha256=obj["current_selection_sha256"],
            selected_state_id=(
                PersonalCapabilityStateId(obj["selected_state_id"])
                if obj["selected_state_id"] is not None
                else None
            ),
            selected_state_sha256=obj["selected_state_sha256"],
        )
    except (TypeError, ValueError) as exc:
        raise InvalidCurrentStateGovernedPlayerWindow(
            f"invalid current-state entry: {exc}"
        ) from exc


def _binding_to_dict(item: CurrentStateProgressionAuthorityBinding) -> dict:
    return {
        "concept_ref": str(item.concept_ref),
        "frame_ref": str(item.frame_ref),
        "status": item.status.value,
        "current_selection_sha256": item.current_selection_sha256,
        "selected_state_id": (
            str(item.selected_state_id)
            if item.selected_state_id is not None
            else None
        ),
        "selected_state_sha256": item.selected_state_sha256,
    }


def _binding_from_dict(payload) -> CurrentStateProgressionAuthorityBinding:
    obj = _obj(
        payload,
        {
            "concept_ref",
            "frame_ref",
            "status",
            "current_selection_sha256",
            "selected_state_id",
            "selected_state_sha256",
        },
        "frontier authority binding",
    )
    try:
        return CurrentStateProgressionAuthorityBinding(
            concept_ref=CapabilityConceptRef.parse(obj["concept_ref"]),
            frame_ref=CompetenceFrameRef.parse(obj["frame_ref"]),
            status=CurrentStateProgressionAuthorityStatus(obj["status"]),
            current_selection_sha256=obj["current_selection_sha256"],
            selected_state_id=(
                PersonalCapabilityStateId(obj["selected_state_id"])
                if obj["selected_state_id"] is not None
                else None
            ),
            selected_state_sha256=obj["selected_state_sha256"],
        )
    except (TypeError, ValueError) as exc:
        raise InvalidCurrentStateGovernedPlayerWindow(
            f"invalid frontier authority binding: {exc}"
        ) from exc


def snapshot_to_dict(value: CurrentStateGovernedPlayerWindow) -> dict:
    if type(value) is not CurrentStateGovernedPlayerWindow:
        _fail("snapshot must be CurrentStateGovernedPlayerWindow")
    return {
        "schema_version": _SCHEMA_VERSION,
        "request": request_to_dict(value.request),
        "subject_ref": str(value.subject_ref),
        "current_selection_history_sha256": value.current_selection_history_sha256,
        "current_state_portfolio_sha256": value.current_state_portfolio_sha256,
        "governed_frontier_sha256": value.governed_frontier_sha256,
        "current_state_entries": [
            _entry_to_dict(item) for item in value.current_state_entries
        ],
        "frontier_authority_bindings": [
            _binding_to_dict(item)
            for item in value.frontier_authority_bindings
        ],
        "window": window_to_dict(value.window),
    }


def snapshot_from_dict(payload: object) -> CurrentStateGovernedPlayerWindow:
    obj = _obj(
        payload,
        {
            "schema_version",
            "request",
            "subject_ref",
            "current_selection_history_sha256",
            "current_state_portfolio_sha256",
            "governed_frontier_sha256",
            "current_state_entries",
            "frontier_authority_bindings",
            "window",
        },
        "current-state governed player window",
    )
    _schema(obj["schema_version"])
    try:
        return CurrentStateGovernedPlayerWindow(
            request=request_from_dict(obj["request"]),
            subject_ref=CapabilitySubjectRef(obj["subject_ref"]),
            current_selection_history_sha256=obj[
                "current_selection_history_sha256"
            ],
            current_state_portfolio_sha256=obj[
                "current_state_portfolio_sha256"
            ],
            governed_frontier_sha256=obj["governed_frontier_sha256"],
            current_state_entries=tuple(
                _entry_from_dict(item)
                for item in _list(
                    obj["current_state_entries"],
                    "current_state_entries",
                )
            ),
            frontier_authority_bindings=tuple(
                _binding_from_dict(item)
                for item in _list(
                    obj["frontier_authority_bindings"],
                    "frontier_authority_bindings",
                )
            ),
            window=window_from_dict(obj["window"]),
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InvalidCurrentStateGovernedPlayerWindow):
            raise
        raise InvalidCurrentStateGovernedPlayerWindow(
            f"invalid current-state governed player window: {exc}"
        ) from exc


def snapshot_to_json(value: CurrentStateGovernedPlayerWindow) -> str:
    return dumps_canonical(snapshot_to_dict(value))


def snapshot_from_json(payload: str) -> CurrentStateGovernedPlayerWindow:
    return snapshot_from_dict(_loads(payload))
