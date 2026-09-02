"""Strict deterministic JSON serialization for PR9 Player Window."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import re

from capability_lab.epistemics import CapabilityClaimId, CapabilitySubjectRef, ClaimEvaluationId, ConflictStatus, EvaluationConclusion
from capability_lab.history import AchievementInstanceId, PersonalLegendId, PersonalMilestoneEventId
from capability_lab.progression import ProgressionFrontierId, PrerequisiteDimensionGapKind
from capability_lab.semantics import CapabilityConceptRef
from capability_lab.state import CompetenceFrameRef, DimensionConflictStatus, DimensionStanding, PersonalCapabilityStateId

from .core import (
    InvalidPlayerWindow,
    InvalidPlayerWindowRequest,
    InvalidPlayerWindowSet,
    PlayerWindow,
    PlayerWindowAchievementEntry,
    PlayerWindowCapabilityEntry,
    PlayerWindowClaimEntry,
    PlayerWindowDimensionEntry,
    PlayerWindowEvaluationEntry,
    PlayerWindowExplorationEntry,
    PlayerWindowFrontierCandidateEntry,
    PlayerWindowFrontierPanel,
    PlayerWindowGapDimensionEntry,
    PlayerWindowGeneratorRef,
    PlayerWindowId,
    PlayerWindowLegendEntry,
    PlayerWindowLegendPanel,
    PlayerWindowMechanismKind,
    PlayerWindowMilestoneEntry,
    PlayerWindowPolicyRef,
    PlayerWindowPrerequisiteGapEntry,
    PlayerWindowRequest,
    PlayerWindowRequesterRef,
    PlayerWindowSet,
    PlayerWindowViewerRef,
)

_SCHEMA_VERSION = 1
_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})$")


def dumps_canonical(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidPlayerWindow("duplicate JSON object keys are not allowed")
        result[key] = value
    return result


def _constant(value):
    raise InvalidPlayerWindow(f"non-finite JSON constant is not allowed: {value}")


def _loads(payload: str):
    if not isinstance(payload, str):
        raise InvalidPlayerWindow("JSON payload must be a string")
    try:
        return json.loads(payload, object_pairs_hook=_pairs, parse_constant=_constant)
    except json.JSONDecodeError as exc:
        raise InvalidPlayerWindow(f"invalid JSON: {exc.msg}") from exc


def _obj(value, keys, label, error_type=InvalidPlayerWindow):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise error_type(f"{label} must contain exactly: {', '.join(sorted(keys))}")
    return value


def _schema(value, error_type=InvalidPlayerWindow):
    if isinstance(value, bool) or not isinstance(value, int) or value != _SCHEMA_VERSION:
        raise error_type(f"schema_version must be integer {_SCHEMA_VERSION}")


def _ts(value: datetime) -> str:
    value = value.astimezone(timezone.utc)
    text = value.isoformat(timespec="microseconds").replace("+00:00", "Z")
    return text.replace(".000000Z", "Z")


def _parse_ts(value, label, error_type=InvalidPlayerWindow):
    if not isinstance(value, str) or _TS_RE.fullmatch(value) is None:
        raise error_type(f"{label} must use strict extended timezone-aware ISO-8601 syntax")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise error_type(f"invalid {label}") from exc
    return parsed.astimezone(timezone.utc)


def _mechanism(ref):
    return {"kind": ref.kind.value, "ref": ref.ref}


def _requester(value, cls, error_type):
    obj = _obj(value, {"kind", "ref"}, "mechanism ref", error_type)
    try:
        kind = PlayerWindowMechanismKind(obj["kind"])
    except (ValueError, TypeError) as exc:
        raise error_type("invalid PlayerWindowMechanismKind") from exc
    return cls(kind, obj["ref"])


def request_to_dict(value: PlayerWindowRequest) -> dict:
    return {
        "schema_version": _SCHEMA_VERSION,
        "window_id": str(value.window_id),
        "subject_ref": str(value.subject_ref),
        "as_of": _ts(value.as_of),
        "generated_at": _ts(value.generated_at),
        "requester_ref": _mechanism(value.requester_ref),
        "viewer_ref": _mechanism(value.viewer_ref),
        "selected_state_ids": [str(item) for item in value.selected_state_ids],
        "selected_achievement_ids": [str(item) for item in value.selected_achievement_ids],
        "selected_milestone_ids": [str(item) for item in value.selected_milestone_ids],
        "selected_legend_id": str(value.selected_legend_id) if value.selected_legend_id else None,
        "selected_frontier_id": str(value.selected_frontier_id) if value.selected_frontier_id else None,
    }


def request_from_dict(payload) -> PlayerWindowRequest:
    obj = _obj(payload, {"schema_version", "window_id", "subject_ref", "as_of", "generated_at", "requester_ref", "viewer_ref", "selected_state_ids", "selected_achievement_ids", "selected_milestone_ids", "selected_legend_id", "selected_frontier_id"}, "player window request", InvalidPlayerWindowRequest)
    _schema(obj["schema_version"], InvalidPlayerWindowRequest)
    for name in ("selected_state_ids", "selected_achievement_ids", "selected_milestone_ids"):
        if not isinstance(obj[name], list):
            raise InvalidPlayerWindowRequest(f"{name} must be a JSON array")
    return PlayerWindowRequest(
        window_id=PlayerWindowId(obj["window_id"]),
        subject_ref=CapabilitySubjectRef(obj["subject_ref"]),
        as_of=_parse_ts(obj["as_of"], "as_of", InvalidPlayerWindowRequest),
        generated_at=_parse_ts(obj["generated_at"], "generated_at", InvalidPlayerWindowRequest),
        requester_ref=_requester(obj["requester_ref"], PlayerWindowRequesterRef, InvalidPlayerWindowRequest),
        viewer_ref=_requester(obj["viewer_ref"], PlayerWindowViewerRef, InvalidPlayerWindowRequest),
        selected_state_ids=tuple(PersonalCapabilityStateId(item) for item in obj["selected_state_ids"]),
        selected_achievement_ids=tuple(AchievementInstanceId(item) for item in obj["selected_achievement_ids"]),
        selected_milestone_ids=tuple(PersonalMilestoneEventId(item) for item in obj["selected_milestone_ids"]),
        selected_legend_id=PersonalLegendId(obj["selected_legend_id"]) if obj["selected_legend_id"] is not None else None,
        selected_frontier_id=ProgressionFrontierId(obj["selected_frontier_id"]) if obj["selected_frontier_id"] is not None else None,
    )


def request_to_json(value: PlayerWindowRequest) -> str:
    return dumps_canonical(request_to_dict(value))


def request_from_json(payload: str) -> PlayerWindowRequest:
    try:
        return request_from_dict(_loads(payload))
    except InvalidPlayerWindow as exc:
        if isinstance(exc, InvalidPlayerWindowRequest):
            raise
        raise InvalidPlayerWindowRequest(str(exc)) from exc


def _claim_to_dict(item):
    return {"claim_id": str(item.claim_id), "statement": item.statement, "scope_description": item.scope_description, "scope_tags": list(item.scope_tags)}


def _claim_from_dict(value):
    obj = _obj(value, {"claim_id", "statement", "scope_description", "scope_tags"}, "claim entry")
    if not isinstance(obj["scope_tags"], list):
        raise InvalidPlayerWindow("scope_tags must be a JSON array")
    return PlayerWindowClaimEntry(CapabilityClaimId(obj["claim_id"]), obj["statement"], obj["scope_description"], tuple(obj["scope_tags"]))


def _evaluation_to_dict(item):
    return {"evaluation_id": str(item.evaluation_id), "conclusion": item.conclusion.value, "conflict_status": item.conflict_status.value, "policy_ref": item.policy_ref, "evaluator_kind": item.evaluator_kind, "evaluator_ref": item.evaluator_ref}


def _evaluation_from_dict(value):
    obj = _obj(value, {"evaluation_id", "conclusion", "conflict_status", "policy_ref", "evaluator_kind", "evaluator_ref"}, "evaluation entry")
    try:
        conclusion = EvaluationConclusion(obj["conclusion"])
        conflict = ConflictStatus(obj["conflict_status"])
    except (ValueError, TypeError) as exc:
        raise InvalidPlayerWindow("invalid evaluation enum") from exc
    return PlayerWindowEvaluationEntry(ClaimEvaluationId(obj["evaluation_id"]), conclusion, conflict, obj["policy_ref"], obj["evaluator_kind"], obj["evaluator_ref"])


def _dimension_to_dict(item):
    return {"dimension_key": item.dimension_key, "name": item.name, "description": item.description, "standing": item.standing.value, "conflict_status": item.conflict_status.value, "rationale": item.rationale, "claims": [_claim_to_dict(x) for x in item.claims], "evaluations": [_evaluation_to_dict(x) for x in item.evaluations]}


def _dimension_from_dict(value):
    obj = _obj(value, {"dimension_key", "name", "description", "standing", "conflict_status", "rationale", "claims", "evaluations"}, "dimension entry")
    if not isinstance(obj["claims"], list) or not isinstance(obj["evaluations"], list):
        raise InvalidPlayerWindow("dimension claims/evaluations must be JSON arrays")
    try:
        standing = DimensionStanding(obj["standing"])
        conflict = DimensionConflictStatus(obj["conflict_status"])
    except (ValueError, TypeError) as exc:
        raise InvalidPlayerWindow("invalid dimension enum") from exc
    return PlayerWindowDimensionEntry(obj["dimension_key"], obj["name"], obj["description"], standing, conflict, obj["rationale"], tuple(_claim_from_dict(x) for x in obj["claims"]), tuple(_evaluation_from_dict(x) for x in obj["evaluations"]))


def _capability_to_dict(item):
    return {"state_id": str(item.state_id), "concept_ref": str(item.concept_ref), "concept_name": item.concept_name, "concept_definition": item.concept_definition, "frame_ref": str(item.frame_ref), "frame_name": item.frame_name, "state_policy_ref": item.state_policy_ref, "state_deriver_kind": item.state_deriver_kind, "state_deriver_ref": item.state_deriver_ref, "as_of": _ts(item.as_of), "derived_at": _ts(item.derived_at), "dimensions": [_dimension_to_dict(x) for x in item.dimensions]}


def _capability_from_dict(value):
    obj = _obj(value, {"state_id", "concept_ref", "concept_name", "concept_definition", "frame_ref", "frame_name", "state_policy_ref", "state_deriver_kind", "state_deriver_ref", "as_of", "derived_at", "dimensions"}, "capability entry")
    if not isinstance(obj["dimensions"], list):
        raise InvalidPlayerWindow("capability dimensions must be a JSON array")
    return PlayerWindowCapabilityEntry(PersonalCapabilityStateId(obj["state_id"]), CapabilityConceptRef.parse(obj["concept_ref"]), obj["concept_name"], obj["concept_definition"], CompetenceFrameRef.parse(obj["frame_ref"]), obj["frame_name"], obj["state_policy_ref"], obj["state_deriver_kind"], obj["state_deriver_ref"], _parse_ts(obj["as_of"], "capability as_of"), _parse_ts(obj["derived_at"], "capability derived_at"), tuple(_dimension_from_dict(x) for x in obj["dimensions"]))


def _achievement_to_dict(item):
    return {"achievement_id": str(item.achievement_id), "family_ref": item.family_ref, "family_name": item.family_name, "achieved_at": _ts(item.achieved_at), "recorded_at": _ts(item.recorded_at), "context": item.context, "variant": item.variant, "record_note": item.record_note, "qualification_policy_ref": item.qualification_policy_ref, "qualifier_kind": item.qualifier_kind, "qualifier_ref": item.qualifier_ref}


def _achievement_from_dict(value):
    obj = _obj(value, {"achievement_id", "family_ref", "family_name", "achieved_at", "recorded_at", "context", "variant", "record_note", "qualification_policy_ref", "qualifier_kind", "qualifier_ref"}, "achievement entry")
    return PlayerWindowAchievementEntry(AchievementInstanceId(obj["achievement_id"]), obj["family_ref"], obj["family_name"], _parse_ts(obj["achieved_at"], "achieved_at"), _parse_ts(obj["recorded_at"], "recorded_at"), obj["context"], obj["variant"], obj["record_note"], obj["qualification_policy_ref"], obj["qualifier_kind"], obj["qualifier_ref"])


def _milestone_to_dict(item):
    return {"milestone_id": str(item.milestone_id), "title": item.title, "description": item.description, "significance_note": item.significance_note, "occurred_at": _ts(item.occurred_at), "recorded_at": _ts(item.recorded_at), "recorder_kind": item.recorder_kind, "recorder_ref": item.recorder_ref, "recording_policy_ref": item.recording_policy_ref}


def _milestone_from_dict(value):
    obj = _obj(value, {"milestone_id", "title", "description", "significance_note", "occurred_at", "recorded_at", "recorder_kind", "recorder_ref", "recording_policy_ref"}, "milestone entry")
    return PlayerWindowMilestoneEntry(PersonalMilestoneEventId(obj["milestone_id"]), obj["title"], obj["description"], obj["significance_note"], _parse_ts(obj["occurred_at"], "occurred_at"), _parse_ts(obj["recorded_at"], "recorded_at"), obj["recorder_kind"], obj["recorder_ref"], obj["recording_policy_ref"])


def _legend_to_dict(item):
    return None if item is None else {"legend_id": str(item.legend_id), "title": item.title, "summary": item.summary, "as_of": _ts(item.as_of), "generated_at": _ts(item.generated_at), "policy_ref": item.policy_ref, "generator_kind": item.generator_kind, "generator_ref": item.generator_ref, "entries": [{"source_refs": list(x.source_refs), "heading": x.heading, "narrative": x.narrative} for x in item.entries]}


def _legend_from_dict(value):
    if value is None:
        return None
    obj = _obj(value, {"legend_id", "title", "summary", "as_of", "generated_at", "policy_ref", "generator_kind", "generator_ref", "entries"}, "legend panel")
    if not isinstance(obj["entries"], list):
        raise InvalidPlayerWindow("legend entries must be a JSON array")
    entries = []
    for raw in obj["entries"]:
        entry = _obj(raw, {"source_refs", "heading", "narrative"}, "legend entry")
        if not isinstance(entry["source_refs"], list):
            raise InvalidPlayerWindow("legend source_refs must be a JSON array")
        entries.append(PlayerWindowLegendEntry(tuple(entry["source_refs"]), entry["heading"], entry["narrative"]))
    return PlayerWindowLegendPanel(PersonalLegendId(obj["legend_id"]), obj["title"], obj["summary"], _parse_ts(obj["as_of"], "legend as_of"), _parse_ts(obj["generated_at"], "legend generated_at"), obj["policy_ref"], obj["generator_kind"], obj["generator_ref"], tuple(entries))


def _candidate_to_dict(item):
    return {"concept_ref": str(item.concept_ref), "concept_name": item.concept_name, "explicit_focus": item.explicit_focus, "adjacency_reasons": list(item.adjacency_reasons), "assessed_prerequisites": list(item.assessed_prerequisites), "unassessed_prerequisites": list(item.unassessed_prerequisites)}


def _candidate_from_dict(value):
    obj = _obj(value, {"concept_ref", "concept_name", "explicit_focus", "adjacency_reasons", "assessed_prerequisites", "unassessed_prerequisites"}, "frontier candidate entry")
    if not isinstance(obj["explicit_focus"], bool):
        raise InvalidPlayerWindow("explicit_focus must be bool")
    for name in ("adjacency_reasons", "assessed_prerequisites", "unassessed_prerequisites"):
        if not isinstance(obj[name], list):
            raise InvalidPlayerWindow(f"{name} must be a JSON array")
    return PlayerWindowFrontierCandidateEntry(CapabilityConceptRef.parse(obj["concept_ref"]), obj["concept_name"], obj["explicit_focus"], tuple(obj["adjacency_reasons"]), tuple(obj["assessed_prerequisites"]), tuple(obj["unassessed_prerequisites"]))


def _gap_to_dict(item):
    return {"target_ref": str(item.target_ref), "target_name": item.target_name, "prerequisite_ref": str(item.prerequisite_ref), "prerequisite_name": item.prerequisite_name, "relation_description": item.relation_description, "frame_ref": str(item.frame_ref), "state_id": str(item.state_id) if item.state_id else None, "dimension_gaps": [{"dimension_key": x.dimension_key, "kind": x.kind.value, "conflict_status": x.conflict_status.value if x.conflict_status else None} for x in item.dimension_gaps]}


def _gap_from_dict(value):
    obj = _obj(value, {"target_ref", "target_name", "prerequisite_ref", "prerequisite_name", "relation_description", "frame_ref", "state_id", "dimension_gaps"}, "prerequisite gap entry")
    if not isinstance(obj["dimension_gaps"], list):
        raise InvalidPlayerWindow("dimension_gaps must be a JSON array")
    dims = []
    for raw in obj["dimension_gaps"]:
        dim = _obj(raw, {"dimension_key", "kind", "conflict_status"}, "gap dimension")
        try:
            kind = PrerequisiteDimensionGapKind(dim["kind"])
            conflict = DimensionConflictStatus(dim["conflict_status"]) if dim["conflict_status"] is not None else None
        except (ValueError, TypeError) as exc:
            raise InvalidPlayerWindow("invalid prerequisite gap enum") from exc
        dims.append(PlayerWindowGapDimensionEntry(dim["dimension_key"], kind, conflict))
    return PlayerWindowPrerequisiteGapEntry(CapabilityConceptRef.parse(obj["target_ref"]), obj["target_name"], CapabilityConceptRef.parse(obj["prerequisite_ref"]), obj["prerequisite_name"], obj["relation_description"], CompetenceFrameRef.parse(obj["frame_ref"]), PersonalCapabilityStateId(obj["state_id"]) if obj["state_id"] is not None else None, tuple(dims))


def _frontier_to_dict(item):
    return None if item is None else {"frontier_id": str(item.frontier_id), "policy_ref": item.policy_ref, "deriver_kind": item.deriver_kind, "deriver_ref": item.deriver_ref, "requester_kind": item.requester_kind, "requester_ref": item.requester_ref, "rationale": item.rationale, "candidates": [_candidate_to_dict(x) for x in item.candidates], "prerequisite_gaps": [_gap_to_dict(x) for x in item.prerequisite_gaps], "exploration": [{"concept_ref": str(x.concept_ref), "concept_name": x.concept_name, "rationale": x.rationale} for x in item.exploration]}


def _frontier_from_dict(value):
    if value is None:
        return None
    obj = _obj(value, {"frontier_id", "policy_ref", "deriver_kind", "deriver_ref", "requester_kind", "requester_ref", "rationale", "candidates", "prerequisite_gaps", "exploration"}, "frontier panel")
    if not all(isinstance(obj[name], list) for name in ("candidates", "prerequisite_gaps", "exploration")):
        raise InvalidPlayerWindow("frontier collections must be JSON arrays")
    exploration = []
    for raw in obj["exploration"]:
        exp = _obj(raw, {"concept_ref", "concept_name", "rationale"}, "exploration entry")
        exploration.append(PlayerWindowExplorationEntry(CapabilityConceptRef.parse(exp["concept_ref"]), exp["concept_name"], exp["rationale"]))
    return PlayerWindowFrontierPanel(ProgressionFrontierId(obj["frontier_id"]), obj["policy_ref"], obj["deriver_kind"], obj["deriver_ref"], obj["requester_kind"], obj["requester_ref"], obj["rationale"], tuple(_candidate_from_dict(x) for x in obj["candidates"]), tuple(_gap_from_dict(x) for x in obj["prerequisite_gaps"]), tuple(exploration))


def window_to_dict(value: PlayerWindow) -> dict:
    return {
        "schema_version": _SCHEMA_VERSION,
        "window_id": str(value.window_id), "subject_ref": str(value.subject_ref),
        "as_of": _ts(value.as_of), "generated_at": _ts(value.generated_at),
        "policy_ref": str(value.policy_ref), "generator_ref": _mechanism(value.generator_ref),
        "requester_ref": _mechanism(value.requester_ref), "viewer_ref": _mechanism(value.viewer_ref),
        "selected_state_ids": [str(x) for x in value.selected_state_ids],
        "selected_achievement_ids": [str(x) for x in value.selected_achievement_ids],
        "selected_milestone_ids": [str(x) for x in value.selected_milestone_ids],
        "selected_legend_id": str(value.selected_legend_id) if value.selected_legend_id else None,
        "selected_frontier_id": str(value.selected_frontier_id) if value.selected_frontier_id else None,
        "capabilities": [_capability_to_dict(x) for x in value.capabilities],
        "achievements": [_achievement_to_dict(x) for x in value.achievements],
        "milestones": [_milestone_to_dict(x) for x in value.milestones],
        "legend": _legend_to_dict(value.legend), "frontier": _frontier_to_dict(value.frontier),
        "rationale": value.rationale,
    }


def window_from_dict(payload) -> PlayerWindow:
    keys = {"schema_version", "window_id", "subject_ref", "as_of", "generated_at", "policy_ref", "generator_ref", "requester_ref", "viewer_ref", "selected_state_ids", "selected_achievement_ids", "selected_milestone_ids", "selected_legend_id", "selected_frontier_id", "capabilities", "achievements", "milestones", "legend", "frontier", "rationale"}
    obj = _obj(payload, keys, "player window")
    _schema(obj["schema_version"])
    for name in ("selected_state_ids", "selected_achievement_ids", "selected_milestone_ids", "capabilities", "achievements", "milestones"):
        if not isinstance(obj[name], list):
            raise InvalidPlayerWindow(f"{name} must be a JSON array")
    return PlayerWindow(
        window_id=PlayerWindowId(obj["window_id"]), subject_ref=CapabilitySubjectRef(obj["subject_ref"]),
        as_of=_parse_ts(obj["as_of"], "as_of"), generated_at=_parse_ts(obj["generated_at"], "generated_at"),
        policy_ref=PlayerWindowPolicyRef.parse(obj["policy_ref"]),
        generator_ref=_requester(obj["generator_ref"], PlayerWindowGeneratorRef, InvalidPlayerWindow),
        requester_ref=_requester(obj["requester_ref"], PlayerWindowRequesterRef, InvalidPlayerWindow),
        viewer_ref=_requester(obj["viewer_ref"], PlayerWindowViewerRef, InvalidPlayerWindow),
        selected_state_ids=tuple(PersonalCapabilityStateId(x) for x in obj["selected_state_ids"]),
        selected_achievement_ids=tuple(AchievementInstanceId(x) for x in obj["selected_achievement_ids"]),
        selected_milestone_ids=tuple(PersonalMilestoneEventId(x) for x in obj["selected_milestone_ids"]),
        selected_legend_id=PersonalLegendId(obj["selected_legend_id"]) if obj["selected_legend_id"] is not None else None,
        selected_frontier_id=ProgressionFrontierId(obj["selected_frontier_id"]) if obj["selected_frontier_id"] is not None else None,
        capabilities=tuple(_capability_from_dict(x) for x in obj["capabilities"]),
        achievements=tuple(_achievement_from_dict(x) for x in obj["achievements"]),
        milestones=tuple(_milestone_from_dict(x) for x in obj["milestones"]),
        legend=_legend_from_dict(obj["legend"]), frontier=_frontier_from_dict(obj["frontier"]), rationale=obj["rationale"],
    )


def window_to_json(value: PlayerWindow) -> str:
    return dumps_canonical(window_to_dict(value))


def window_from_json(payload: str) -> PlayerWindow:
    return window_from_dict(_loads(payload))


def window_set_to_dict(value: PlayerWindowSet) -> dict:
    return {"schema_version": _SCHEMA_VERSION, "subject_ref": str(value.subject_ref), "windows": [window_to_dict(x) for x in value.windows]}


def window_set_from_dict(payload) -> PlayerWindowSet:
    obj = _obj(payload, {"schema_version", "subject_ref", "windows"}, "player window set", InvalidPlayerWindowSet)
    _schema(obj["schema_version"], InvalidPlayerWindowSet)
    if not isinstance(obj["windows"], list):
        raise InvalidPlayerWindowSet("windows must be a JSON array")
    return PlayerWindowSet(CapabilitySubjectRef(obj["subject_ref"]), tuple(window_from_dict(x) for x in obj["windows"]))


def window_set_to_json(value: PlayerWindowSet) -> str:
    return dumps_canonical(window_set_to_dict(value))


def window_set_from_json(payload: str) -> PlayerWindowSet:
    try:
        return window_set_from_dict(_loads(payload))
    except InvalidPlayerWindow as exc:
        if isinstance(exc, InvalidPlayerWindowSet):
            raise
        raise InvalidPlayerWindowSet(str(exc)) from exc
