"""Strict deterministic serialization for PR7 history and legend records."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import re
from typing import Any, Mapping

from capability_lab.epistemics import CapabilitySubjectRef

from .core import (
    AchievementBasisKind,
    AchievementBasisRef,
    AchievementCriterion,
    AchievementFamily,
    AchievementFamilyCatalog,
    AchievementFamilyId,
    AchievementFamilyLifecycle,
    AchievementFamilyRef,
    AchievementInstance,
    AchievementInstanceId,
    AchievementQualificationPolicyRef,
    AchievementQualifierRef,
    HistoryError,
    HistoryMechanismKind,
    InvalidAchievementFamily,
    InvalidAchievementInstance,
    InvalidMilestoneEvent,
    InvalidPersonalLegend,
    LegendGeneratorRef,
    LegendProjectionPolicyRef,
    LegendSourceKind,
    LegendSourceRef,
    MilestoneRecorderRef,
    MilestoneRecordingPolicyRef,
    MilestoneSourceKind,
    MilestoneSourceRef,
    PersonalLegend,
    PersonalLegendEntry,
    PersonalLegendId,
    PersonalMilestoneEvent,
    PersonalMilestoneEventId,
)

_SCHEMA_VERSION = 1
_TIME_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]{1,6})?(?:Z|[+-][0-9]{2}:[0-9]{2})$"
)


def family_catalog_to_json(catalog: AchievementFamilyCatalog) -> str:
    return _dumps(family_catalog_to_dict(catalog))


def family_catalog_from_json(payload: object) -> AchievementFamilyCatalog:
    return family_catalog_from_dict(_loads(payload, "achievement-family catalog"))


def family_catalog_to_dict(catalog: AchievementFamilyCatalog) -> dict[str, Any]:
    if not isinstance(catalog, AchievementFamilyCatalog):
        raise InvalidAchievementFamily("catalog must be AchievementFamilyCatalog")
    return {
        "schema_version": _SCHEMA_VERSION,
        "families": [_family_to_dict(item) for item in catalog.families],
    }


def family_catalog_from_dict(payload: object) -> AchievementFamilyCatalog:
    mapping = _mapping(payload, "achievement-family catalog", InvalidAchievementFamily)
    _keys(mapping, {"schema_version", "families"}, "achievement-family catalog", InvalidAchievementFamily)
    _schema(mapping["schema_version"], "achievement-family catalog", InvalidAchievementFamily)
    families = tuple(
        _family_from_dict(item)
        for item in _list(mapping["families"], "families", InvalidAchievementFamily)
    )
    return AchievementFamilyCatalog(families=families)


def history_set_to_json(record_set) -> str:
    return _dumps(history_set_to_dict(record_set))


def history_set_from_json(payload: object):
    return history_set_from_dict(_loads(payload, "personal history set"))


def history_set_to_dict(record_set) -> dict[str, Any]:
    from .record_set import PersonalHistoryRecordSet

    if not isinstance(record_set, PersonalHistoryRecordSet):
        raise InvalidAchievementInstance("record_set must be PersonalHistoryRecordSet")
    return {
        "schema_version": _SCHEMA_VERSION,
        "subject_ref": str(record_set.subject_ref),
        "achievement_instances": [
            _achievement_to_dict(item) for item in record_set.achievement_instances
        ],
        "milestone_events": [
            _milestone_to_dict(item) for item in record_set.milestone_events
        ],
    }


def history_set_from_dict(payload: object):
    from .record_set import PersonalHistoryRecordSet

    mapping = _mapping(payload, "personal history set", InvalidAchievementInstance)
    _keys(
        mapping,
        {"schema_version", "subject_ref", "achievement_instances", "milestone_events"},
        "personal history set",
        InvalidAchievementInstance,
    )
    _schema(mapping["schema_version"], "personal history set", InvalidAchievementInstance)
    return PersonalHistoryRecordSet(
        subject_ref=CapabilitySubjectRef(_string(mapping["subject_ref"], "subject_ref", InvalidAchievementInstance)),
        achievement_instances=tuple(
            _achievement_from_dict(item)
            for item in _list(
                mapping["achievement_instances"],
                "achievement_instances",
                InvalidAchievementInstance,
            )
        ),
        milestone_events=tuple(
            _milestone_from_dict(item)
            for item in _list(mapping["milestone_events"], "milestone_events", InvalidMilestoneEvent)
        ),
    )


def legend_to_json(legend: PersonalLegend) -> str:
    return _dumps(legend_to_dict(legend))


def legend_from_json(payload: object) -> PersonalLegend:
    return legend_from_dict(_loads(payload, "personal legend"))


def legend_to_dict(legend: PersonalLegend) -> dict[str, Any]:
    if not isinstance(legend, PersonalLegend):
        raise InvalidPersonalLegend("legend must be PersonalLegend")
    return {"schema_version": _SCHEMA_VERSION, "legend": _legend_record_to_dict(legend)}


def legend_from_dict(payload: object) -> PersonalLegend:
    mapping = _mapping(payload, "personal legend", InvalidPersonalLegend)
    _keys(mapping, {"schema_version", "legend"}, "personal legend", InvalidPersonalLegend)
    _schema(mapping["schema_version"], "personal legend", InvalidPersonalLegend)
    return _legend_record_from_dict(mapping["legend"])


def legend_set_to_json(legend_set) -> str:
    return _dumps(legend_set_to_dict(legend_set))


def legend_set_from_json(payload: object):
    return legend_set_from_dict(_loads(payload, "personal legend set"))


def legend_set_to_dict(legend_set) -> dict[str, Any]:
    from .record_set import PersonalLegendSet

    if not isinstance(legend_set, PersonalLegendSet):
        raise InvalidPersonalLegend("legend_set must be PersonalLegendSet")
    return {
        "schema_version": _SCHEMA_VERSION,
        "subject_ref": str(legend_set.subject_ref),
        "legends": [_legend_record_to_dict(item) for item in legend_set.legends],
    }


def legend_set_from_dict(payload: object):
    from .record_set import PersonalLegendSet

    mapping = _mapping(payload, "personal legend set", InvalidPersonalLegend)
    _keys(mapping, {"schema_version", "subject_ref", "legends"}, "personal legend set", InvalidPersonalLegend)
    _schema(mapping["schema_version"], "personal legend set", InvalidPersonalLegend)
    return PersonalLegendSet(
        subject_ref=CapabilitySubjectRef(_string(mapping["subject_ref"], "subject_ref", InvalidPersonalLegend)),
        legends=tuple(
            _legend_record_from_dict(item)
            for item in _list(mapping["legends"], "legends", InvalidPersonalLegend)
        ),
    )


def _family_to_dict(family: AchievementFamily) -> dict[str, Any]:
    return {
        "family_id": str(family.family_id),
        "revision": family.revision,
        "name": family.name,
        "definition": family.definition,
        "qualification_criteria": [
            {"key": item.key, "description": item.description}
            for item in family.qualification_criteria
        ],
        "aliases": list(family.aliases),
        "lifecycle": family.lifecycle.value,
        "deprecation_note": family.deprecation_note,
    }


def _family_from_dict(payload: object) -> AchievementFamily:
    mapping = _mapping(payload, "achievement family", InvalidAchievementFamily)
    _keys(
        mapping,
        {
            "family_id",
            "revision",
            "name",
            "definition",
            "qualification_criteria",
            "aliases",
            "lifecycle",
            "deprecation_note",
        },
        "achievement family",
        InvalidAchievementFamily,
    )
    criteria = []
    for raw in _list(
        mapping["qualification_criteria"],
        "qualification_criteria",
        InvalidAchievementFamily,
    ):
        item = _mapping(raw, "achievement criterion", InvalidAchievementFamily)
        _keys(item, {"key", "description"}, "achievement criterion", InvalidAchievementFamily)
        criteria.append(
            AchievementCriterion(
                _string(item["key"], "criterion key", InvalidAchievementFamily),
                _string(item["description"], "criterion description", InvalidAchievementFamily),
            )
        )
    try:
        lifecycle = AchievementFamilyLifecycle(
            _string(mapping["lifecycle"], "family lifecycle", InvalidAchievementFamily)
        )
    except ValueError as exc:
        raise InvalidAchievementFamily("unknown achievement family lifecycle") from exc
    note = mapping["deprecation_note"]
    if note is not None:
        note = _string(note, "deprecation_note", InvalidAchievementFamily)
    return AchievementFamily(
        family_id=AchievementFamilyId.parse(
            _string(mapping["family_id"], "family_id", InvalidAchievementFamily)
        ),
        revision=_integer(mapping["revision"], "family revision", InvalidAchievementFamily),
        name=_string(mapping["name"], "family name", InvalidAchievementFamily),
        definition=_string(mapping["definition"], "family definition", InvalidAchievementFamily),
        qualification_criteria=tuple(criteria),
        aliases=tuple(
            _string(item, "family alias", InvalidAchievementFamily)
            for item in _list(mapping["aliases"], "aliases", InvalidAchievementFamily)
        ),
        lifecycle=lifecycle,
        deprecation_note=note,
    )


def _achievement_to_dict(item: AchievementInstance) -> dict[str, Any]:
    return {
        "achievement_id": str(item.achievement_id),
        "subject_ref": str(item.subject_ref),
        "family_ref": str(item.family_ref),
        "achieved_at": _format_time(item.achieved_at),
        "recorded_at": _format_time(item.recorded_at),
        "qualification_policy_ref": str(item.qualification_policy_ref),
        "qualifier_ref": {"kind": item.qualifier_ref.kind.value, "ref": item.qualifier_ref.ref},
        "basis_refs": [{"kind": ref.kind.value, "ref": ref.ref} for ref in item.basis_refs],
        "context": item.context,
        "variant": item.variant,
        "record_note": item.record_note,
    }


def _achievement_from_dict(payload: object) -> AchievementInstance:
    mapping = _mapping(payload, "achievement instance", InvalidAchievementInstance)
    _keys(
        mapping,
        {
            "achievement_id",
            "subject_ref",
            "family_ref",
            "achieved_at",
            "recorded_at",
            "qualification_policy_ref",
            "qualifier_ref",
            "basis_refs",
            "context",
            "variant",
            "record_note",
        },
        "achievement instance",
        InvalidAchievementInstance,
    )
    qualifier = _mechanism_ref(
        mapping["qualifier_ref"],
        "qualifier_ref",
        InvalidAchievementInstance,
        AchievementQualifierRef,
    )
    basis_refs = []
    for raw in _list(mapping["basis_refs"], "basis_refs", InvalidAchievementInstance):
        basis = _mapping(raw, "achievement basis", InvalidAchievementInstance)
        _keys(basis, {"kind", "ref"}, "achievement basis", InvalidAchievementInstance)
        try:
            kind = AchievementBasisKind(
                _string(basis["kind"], "achievement basis kind", InvalidAchievementInstance)
            )
        except ValueError as exc:
            raise InvalidAchievementInstance("unknown achievement basis kind") from exc
        basis_refs.append(
            AchievementBasisRef(
                kind,
                _string(basis["ref"], "achievement basis ref", InvalidAchievementInstance),
            )
        )
    return AchievementInstance(
        achievement_id=AchievementInstanceId(
            _string(mapping["achievement_id"], "achievement_id", InvalidAchievementInstance)
        ),
        subject_ref=CapabilitySubjectRef(
            _string(mapping["subject_ref"], "subject_ref", InvalidAchievementInstance)
        ),
        family_ref=AchievementFamilyRef.parse(
            _string(mapping["family_ref"], "family_ref", InvalidAchievementInstance)
        ),
        achieved_at=_parse_time(mapping["achieved_at"], "achieved_at", InvalidAchievementInstance),
        recorded_at=_parse_time(mapping["recorded_at"], "recorded_at", InvalidAchievementInstance),
        qualification_policy_ref=AchievementQualificationPolicyRef.parse(
            _string(
                mapping["qualification_policy_ref"],
                "qualification_policy_ref",
                InvalidAchievementInstance,
            )
        ),
        qualifier_ref=qualifier,
        basis_refs=tuple(basis_refs),
        context=_string(mapping["context"], "achievement context", InvalidAchievementInstance),
        variant=_optional_string(mapping["variant"], "achievement variant", InvalidAchievementInstance),
        record_note=_optional_string(
            mapping["record_note"], "achievement record_note", InvalidAchievementInstance
        ),
    )


def _milestone_to_dict(item: PersonalMilestoneEvent) -> dict[str, Any]:
    return {
        "milestone_id": str(item.milestone_id),
        "subject_ref": str(item.subject_ref),
        "title": item.title,
        "description": item.description,
        "significance_note": item.significance_note,
        "started_at": None if item.started_at is None else _format_time(item.started_at),
        "occurred_at": _format_time(item.occurred_at),
        "recorded_at": _format_time(item.recorded_at),
        "recorder_ref": {"kind": item.recorder_ref.kind.value, "ref": item.recorder_ref.ref},
        "recording_policy_ref": str(item.recording_policy_ref),
        "source_refs": [{"kind": ref.kind.value, "ref": ref.ref} for ref in item.source_refs],
        "tags": list(item.tags),
    }


def _milestone_from_dict(payload: object) -> PersonalMilestoneEvent:
    mapping = _mapping(payload, "milestone event", InvalidMilestoneEvent)
    _keys(
        mapping,
        {
            "milestone_id",
            "subject_ref",
            "title",
            "description",
            "significance_note",
            "started_at",
            "occurred_at",
            "recorded_at",
            "recorder_ref",
            "recording_policy_ref",
            "source_refs",
            "tags",
        },
        "milestone event",
        InvalidMilestoneEvent,
    )
    recorder = _mechanism_ref(
        mapping["recorder_ref"], "recorder_ref", InvalidMilestoneEvent, MilestoneRecorderRef
    )
    refs = []
    for raw in _list(mapping["source_refs"], "source_refs", InvalidMilestoneEvent):
        source = _mapping(raw, "milestone source", InvalidMilestoneEvent)
        _keys(source, {"kind", "ref"}, "milestone source", InvalidMilestoneEvent)
        try:
            kind = MilestoneSourceKind(
                _string(source["kind"], "milestone source kind", InvalidMilestoneEvent)
            )
        except ValueError as exc:
            raise InvalidMilestoneEvent("unknown milestone source kind") from exc
        refs.append(
            MilestoneSourceRef(
                kind,
                _string(source["ref"], "milestone source ref", InvalidMilestoneEvent),
            )
        )
    started = mapping["started_at"]
    return PersonalMilestoneEvent(
        milestone_id=PersonalMilestoneEventId(
            _string(mapping["milestone_id"], "milestone_id", InvalidMilestoneEvent)
        ),
        subject_ref=CapabilitySubjectRef(
            _string(mapping["subject_ref"], "subject_ref", InvalidMilestoneEvent)
        ),
        title=_string(mapping["title"], "milestone title", InvalidMilestoneEvent),
        description=_string(mapping["description"], "milestone description", InvalidMilestoneEvent),
        significance_note=_string(
            mapping["significance_note"], "milestone significance_note", InvalidMilestoneEvent
        ),
        started_at=(
            None
            if started is None
            else _parse_time(started, "milestone started_at", InvalidMilestoneEvent)
        ),
        occurred_at=_parse_time(mapping["occurred_at"], "occurred_at", InvalidMilestoneEvent),
        recorded_at=_parse_time(mapping["recorded_at"], "recorded_at", InvalidMilestoneEvent),
        recorder_ref=recorder,
        recording_policy_ref=MilestoneRecordingPolicyRef.parse(
            _string(
                mapping["recording_policy_ref"],
                "recording_policy_ref",
                InvalidMilestoneEvent,
            )
        ),
        source_refs=tuple(refs),
        tags=tuple(
            _string(item, "milestone tag", InvalidMilestoneEvent)
            for item in _list(mapping["tags"], "tags", InvalidMilestoneEvent)
        ),
    )


def _legend_record_to_dict(legend: PersonalLegend) -> dict[str, Any]:
    return {
        "legend_id": str(legend.legend_id),
        "subject_ref": str(legend.subject_ref),
        "as_of": _format_time(legend.as_of),
        "generated_at": _format_time(legend.generated_at),
        "legend_policy_ref": str(legend.legend_policy_ref),
        "generator_ref": {"kind": legend.generator_ref.kind.value, "ref": legend.generator_ref.ref},
        "title": legend.title,
        "summary": legend.summary,
        "entries": [
            {
                "source_refs": [
                    {"kind": ref.kind.value, "ref": ref.ref} for ref in entry.source_refs
                ],
                "heading": entry.heading,
                "narrative": entry.narrative,
            }
            for entry in legend.entries
        ],
    }


def _legend_record_from_dict(payload: object) -> PersonalLegend:
    mapping = _mapping(payload, "legend record", InvalidPersonalLegend)
    _keys(
        mapping,
        {
            "legend_id",
            "subject_ref",
            "as_of",
            "generated_at",
            "legend_policy_ref",
            "generator_ref",
            "title",
            "summary",
            "entries",
        },
        "legend record",
        InvalidPersonalLegend,
    )
    generator = _mechanism_ref(
        mapping["generator_ref"], "generator_ref", InvalidPersonalLegend, LegendGeneratorRef
    )
    entries = []
    for raw in _list(mapping["entries"], "legend entries", InvalidPersonalLegend):
        entry = _mapping(raw, "legend entry", InvalidPersonalLegend)
        _keys(entry, {"source_refs", "heading", "narrative"}, "legend entry", InvalidPersonalLegend)
        refs = []
        for raw_ref in _list(entry["source_refs"], "legend source_refs", InvalidPersonalLegend):
            source = _mapping(raw_ref, "legend source", InvalidPersonalLegend)
            _keys(source, {"kind", "ref"}, "legend source", InvalidPersonalLegend)
            try:
                kind = LegendSourceKind(
                    _string(source["kind"], "legend source kind", InvalidPersonalLegend)
                )
            except ValueError as exc:
                raise InvalidPersonalLegend("unknown legend source kind") from exc
            refs.append(
                LegendSourceRef(
                    kind,
                    _string(source["ref"], "legend source ref", InvalidPersonalLegend),
                )
            )
        entries.append(
            PersonalLegendEntry(
                source_refs=tuple(refs),
                heading=_string(entry["heading"], "legend entry heading", InvalidPersonalLegend),
                narrative=_string(entry["narrative"], "legend entry narrative", InvalidPersonalLegend),
            )
        )
    return PersonalLegend(
        legend_id=PersonalLegendId(
            _string(mapping["legend_id"], "legend_id", InvalidPersonalLegend)
        ),
        subject_ref=CapabilitySubjectRef(
            _string(mapping["subject_ref"], "subject_ref", InvalidPersonalLegend)
        ),
        as_of=_parse_time(mapping["as_of"], "legend as_of", InvalidPersonalLegend),
        generated_at=_parse_time(
            mapping["generated_at"], "legend generated_at", InvalidPersonalLegend
        ),
        legend_policy_ref=LegendProjectionPolicyRef.parse(
            _string(mapping["legend_policy_ref"], "legend_policy_ref", InvalidPersonalLegend)
        ),
        generator_ref=generator,
        title=_string(mapping["title"], "legend title", InvalidPersonalLegend),
        summary=_string(mapping["summary"], "legend summary", InvalidPersonalLegend),
        entries=tuple(entries),
    )


def _mechanism_ref(payload: object, label: str, error_type, cls):
    mapping = _mapping(payload, label, error_type)
    _keys(mapping, {"kind", "ref"}, label, error_type)
    try:
        kind = HistoryMechanismKind(_string(mapping["kind"], f"{label} kind", error_type))
    except ValueError as exc:
        raise error_type(f"unknown {label} mechanism kind") from exc
    return cls(kind=kind, ref=_string(mapping["ref"], f"{label} ref", error_type))


def _dumps(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _loads(payload: object, label: str) -> object:
    if not isinstance(payload, str):
        raise HistoryError(f"{label} JSON payload must be a string")

    def reject_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise HistoryError(f"duplicate JSON object key: {key!r}")
            result[key] = value
        return result

    def reject_constant(value: str):
        raise HistoryError(f"non-finite JSON number is forbidden: {value}")

    try:
        return json.loads(
            payload,
            object_pairs_hook=reject_duplicates,
            parse_constant=reject_constant,
        )
    except HistoryError:
        raise
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise HistoryError(f"{label} JSON payload must be valid strict JSON") from exc


def _mapping(value: object, label: str, error_type) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise error_type(f"{label} must be an object")
    if any(not isinstance(key, str) for key in value):
        raise error_type(f"{label} keys must be strings")
    return value


def _keys(mapping: Mapping[str, Any], expected: set[str], label: str, error_type) -> None:
    actual = set(mapping)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise error_type(f"{label} fields mismatch: missing={missing}, extra={extra}")


def _list(value: object, label: str, error_type) -> list[Any]:
    if not isinstance(value, list):
        raise error_type(f"{label} must be a JSON array")
    return value


def _string(value: object, label: str, error_type) -> str:
    if not isinstance(value, str):
        raise error_type(f"{label} must be a string")
    return value


def _optional_string(value: object, label: str, error_type) -> str | None:
    if value is None:
        return None
    return _string(value, label, error_type)


def _integer(value: object, label: str, error_type) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise error_type(f"{label} must be an integer")
    return value


def _schema(value: object, label: str, error_type) -> None:
    if value != _SCHEMA_VERSION:
        raise error_type(f"{label} schema_version must be exactly {_SCHEMA_VERSION}")


def _format_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_time(value: object, field_name: str, error_type) -> datetime:
    if not isinstance(value, str):
        raise error_type(f"{field_name} must be an ISO-8601 string")
    if _TIME_RE.fullmatch(value) is None:
        raise error_type(
            f"{field_name} must use YYYY-MM-DDTHH:MM:SS[.ffffff](Z|±HH:MM)"
        )
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise error_type(f"{field_name} must be valid ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise error_type(f"{field_name} must be timezone-aware")
    return parsed.astimezone(timezone.utc)
