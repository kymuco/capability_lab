"""Strict deterministic serialization for PR12.0 external observations."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import re

from capability_lab.epistemics import CapabilitySubjectRef

from .core import (
    ExternalObservationContextFactor,
    ExternalObservationContextFactorKind,
    ExternalObservationEnvelope,
    ExternalObservationForm,
    ExternalObservationId,
    ExternalObservationLedger,
    ExternalObservationOriginKind,
    ExternalObservationPayloadRef,
    ExternalObservationSourceKind,
    ExternalObservationSourceRef,
    InvalidExternalObservation,
    InvalidExternalObservationLedger,
    validate_external_observation_ledger_v1,
    validate_external_observation_v1,
)


_SCHEMA_VERSION = 1
_TIME_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T"
    r"[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]{1,6})?(?:Z|[+-][0-9]{2}:[0-9]{2})$"
)


def _fail(message: str) -> None:
    raise InvalidExternalObservation(message)


def _ledger_fail(message: str) -> None:
    raise InvalidExternalObservationLedger(message)


def _obj(
    payload: object,
    expected_fields: set[str],
    label: str,
    *,
    ledger: bool = False,
) -> dict:
    error = _ledger_fail if ledger else _fail
    if type(payload) is not dict:
        error(f"{label} must be a JSON object")
    fields = set(payload)
    if fields != expected_fields:
        missing = tuple(sorted(expected_fields - fields))
        unknown = tuple(sorted(fields - expected_fields))
        error(
            f"{label} fields must match schema exactly; "
            f"missing={missing!r}, unknown={unknown!r}"
        )
    return payload


def _list(payload: object, label: str, *, ledger: bool = False) -> list:
    error = _ledger_fail if ledger else _fail
    if type(payload) is not list:
        error(f"{label} must be a JSON array")
    return payload


def _schema(value: object, *, ledger: bool = False) -> None:
    error = _ledger_fail if ledger else _fail
    if type(value) is not int or value != _SCHEMA_VERSION:
        error(f"schema_version must be exact integer {_SCHEMA_VERSION}")


def _format_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_time(value: object, label: str) -> datetime:
    if type(value) is not str or _TIME_RE.fullmatch(value) is None:
        _fail(
            f"{label} must use extended ISO-8601 with explicit timezone"
        )
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise InvalidExternalObservation(
            f"{label} must be valid ISO-8601"
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        _fail(f"{label} must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _no_duplicate_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            _fail(f"duplicate JSON object keys are forbidden: {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str):
    _fail(f"non-finite JSON constant is forbidden: {value}")


def _loads(payload: object):
    if type(payload) is not str:
        _fail("JSON payload must be a string")
    try:
        return json.loads(
            payload,
            object_pairs_hook=_no_duplicate_pairs,
            parse_constant=_reject_constant,
        )
    except InvalidExternalObservation:
        raise
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise InvalidExternalObservation(f"invalid JSON payload: {exc}") from exc


def dumps_canonical(payload: object) -> str:
    try:
        return json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise InvalidExternalObservation(
            f"payload is not canonically JSON serializable: {exc}"
        ) from exc


def _source_to_dict(value: ExternalObservationSourceRef) -> dict:
    return {
        "kind": value.kind.value,
        "ref": value.ref,
    }


def _source_from_dict(payload: object) -> ExternalObservationSourceRef:
    obj = _obj(payload, {"kind", "ref"}, "source_ref")
    try:
        return ExternalObservationSourceRef(
            kind=ExternalObservationSourceKind(obj["kind"]),
            ref=obj["ref"],
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InvalidExternalObservation):
            raise
        raise InvalidExternalObservation(
            f"invalid source_ref: {exc}"
        ) from exc


def _factor_to_dict(value: ExternalObservationContextFactor) -> dict:
    return {
        "kind": value.kind.value,
        "description": value.description,
    }


def _factor_from_dict(payload: object) -> ExternalObservationContextFactor:
    obj = _obj(payload, {"kind", "description"}, "context factor")
    try:
        return ExternalObservationContextFactor(
            kind=ExternalObservationContextFactorKind(obj["kind"]),
            description=obj["description"],
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InvalidExternalObservation):
            raise
        raise InvalidExternalObservation(
            f"invalid context factor: {exc}"
        ) from exc


def _payload_ref_to_dict(value: ExternalObservationPayloadRef) -> dict:
    return {
        "ref": value.ref,
        "sha256": value.sha256,
        "byte_size": value.byte_size,
        "media_type": value.media_type,
    }


def _payload_ref_from_dict(payload: object) -> ExternalObservationPayloadRef:
    obj = _obj(
        payload,
        {"ref", "sha256", "byte_size", "media_type"},
        "payload ref",
    )
    try:
        return ExternalObservationPayloadRef(
            ref=obj["ref"],
            sha256=obj["sha256"],
            byte_size=obj["byte_size"],
            media_type=obj["media_type"],
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InvalidExternalObservation):
            raise
        raise InvalidExternalObservation(
            f"invalid payload ref: {exc}"
        ) from exc


def external_observation_to_dict(
    value: ExternalObservationEnvelope,
) -> dict:
    validate_external_observation_v1(value)
    return {
        "schema_version": _SCHEMA_VERSION,
        "observation_id": str(value.observation_id),
        "subject_ref": str(value.subject_ref),
        "source_ref": _source_to_dict(value.source_ref),
        "source_event_id": value.source_event_id,
        "form": value.form.value,
        "origin_kind": value.origin_kind.value,
        "observed_at": _format_time(value.observed_at),
        "captured_at": _format_time(value.captured_at),
        "observation_started_at": (
            _format_time(value.observation_started_at)
            if value.observation_started_at is not None
            else None
        ),
        "context_factors": [
            _factor_to_dict(item) for item in value.context_factors
        ],
        "payload_refs": [
            _payload_ref_to_dict(item) for item in value.payload_refs
        ],
    }


def external_observation_from_dict(
    payload: object,
) -> ExternalObservationEnvelope:
    obj = _obj(
        payload,
        {
            "schema_version",
            "observation_id",
            "subject_ref",
            "source_ref",
            "source_event_id",
            "form",
            "origin_kind",
            "observed_at",
            "captured_at",
            "observation_started_at",
            "context_factors",
            "payload_refs",
        },
        "external observation",
    )
    _schema(obj["schema_version"])
    started_raw = obj["observation_started_at"]
    try:
        result = ExternalObservationEnvelope(
            observation_id=ExternalObservationId(obj["observation_id"]),
            subject_ref=CapabilitySubjectRef(obj["subject_ref"]),
            source_ref=_source_from_dict(obj["source_ref"]),
            source_event_id=obj["source_event_id"],
            form=ExternalObservationForm(obj["form"]),
            origin_kind=ExternalObservationOriginKind(obj["origin_kind"]),
            observed_at=_parse_time(obj["observed_at"], "observed_at"),
            captured_at=_parse_time(obj["captured_at"], "captured_at"),
            observation_started_at=(
                _parse_time(started_raw, "observation_started_at")
                if started_raw is not None
                else None
            ),
            context_factors=tuple(
                _factor_from_dict(item)
                for item in _list(
                    obj["context_factors"],
                    "context_factors",
                )
            ),
            payload_refs=tuple(
                _payload_ref_from_dict(item)
                for item in _list(
                    obj["payload_refs"],
                    "payload_refs",
                )
            ),
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InvalidExternalObservation):
            raise
        raise InvalidExternalObservation(
            f"invalid external observation: {exc}"
        ) from exc
    validate_external_observation_v1(result)
    return result


def external_observation_to_json(
    value: ExternalObservationEnvelope,
) -> str:
    return dumps_canonical(external_observation_to_dict(value))


def external_observation_from_json(
    payload: object,
) -> ExternalObservationEnvelope:
    return external_observation_from_dict(_loads(payload))


def external_observation_ledger_to_dict(
    value: ExternalObservationLedger,
) -> dict:
    validate_external_observation_ledger_v1(value)
    return {
        "schema_version": _SCHEMA_VERSION,
        "subject_ref": str(value.subject_ref),
        "observations": [
            external_observation_to_dict(item)
            for item in value.observations
        ],
    }


def external_observation_ledger_from_dict(
    payload: object,
) -> ExternalObservationLedger:
    obj = _obj(
        payload,
        {"schema_version", "subject_ref", "observations"},
        "external observation ledger",
        ledger=True,
    )
    _schema(obj["schema_version"], ledger=True)
    try:
        result = ExternalObservationLedger(
            subject_ref=CapabilitySubjectRef(obj["subject_ref"]),
            observations=tuple(
                external_observation_from_dict(item)
                for item in _list(
                    obj["observations"],
                    "observations",
                    ledger=True,
                )
            ),
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InvalidExternalObservationLedger):
            raise
        if isinstance(exc, InvalidExternalObservation):
            raise InvalidExternalObservationLedger(str(exc)) from exc
        raise InvalidExternalObservationLedger(
            f"invalid external observation ledger: {exc}"
        ) from exc
    validate_external_observation_ledger_v1(result)
    return result


def external_observation_ledger_to_json(
    value: ExternalObservationLedger,
) -> str:
    try:
        return dumps_canonical(
            external_observation_ledger_to_dict(value)
        )
    except InvalidExternalObservation as exc:
        raise InvalidExternalObservationLedger(str(exc)) from exc


def external_observation_ledger_from_json(
    payload: object,
) -> ExternalObservationLedger:
    try:
        return external_observation_ledger_from_dict(_loads(payload))
    except InvalidExternalObservationLedger:
        raise
    except InvalidExternalObservation as exc:
        raise InvalidExternalObservationLedger(str(exc)) from exc
