"""Strict deterministic serialization for PR10.1 reviewed materialization records."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
import json
import re
from typing import Any

from capability_lab.epistemics import CapabilitySubjectRef, EvidenceId

from .materialization import (
    InvalidPilotEvidenceMaterialization,
    PilotEvidenceMaterializationCandidate,
    PilotEvidenceMaterializationId,
    PilotEvidenceMaterializationPolicyRef,
    PilotEvidenceMaterializationReview,
    PilotEvidenceMaterializationReviewId,
    PilotEvidenceMaterializationReviewerKind,
    PilotEvidenceMaterializationReviewerRef,
    PilotEvidenceMaterializationVerdict,
)
from .protocol import PilotCaptureKind, PilotProtocolRef


MATERIALIZATION_CANDIDATE_SCHEMA = (
    "capability_lab/pilot_evidence_materialization_candidate@1"
)
MATERIALIZATION_REVIEW_SCHEMA = "capability_lab/pilot_evidence_materialization_review@1"
_SCHEMA_VERSION = 1
_TIME_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]{1,6})?(?:Z|[+-][0-9]{2}:[0-9]{2})$"
)


class PilotEvidenceMaterializationSerializationError(ValueError):
    pass


def _mapping(value: object, context: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise PilotEvidenceMaterializationSerializationError(
            f"{context} must be an object"
        )
    if any(not isinstance(key, str) for key in value):
        raise PilotEvidenceMaterializationSerializationError(
            f"{context} keys must be strings"
        )
    return value


def _keys(value: Mapping[str, Any], fields: set[str], context: str) -> None:
    unknown = sorted(set(value) - fields)
    missing = sorted(fields - set(value))
    if unknown:
        raise PilotEvidenceMaterializationSerializationError(
            f"{context} contains unknown fields: {', '.join(unknown)}"
        )
    if missing:
        raise PilotEvidenceMaterializationSerializationError(
            f"{context} is missing fields: {', '.join(missing)}"
        )


def _schema_version(value: object, context: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value != _SCHEMA_VERSION:
        raise PilotEvidenceMaterializationSerializationError(
            f"{context} schema_version must be integer 1"
        )


def _format_time(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise PilotEvidenceMaterializationSerializationError(
            "timestamp must be timezone-aware"
        )
    return (
        value.astimezone(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _parse_time(value: object, context: str) -> datetime:
    if not isinstance(value, str) or _TIME_RE.fullmatch(value) is None:
        raise PilotEvidenceMaterializationSerializationError(
            f"{context} must use extended ISO-8601 with explicit timezone"
        )
    raw = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise PilotEvidenceMaterializationSerializationError(
            f"invalid {context}"
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise PilotEvidenceMaterializationSerializationError(
            f"{context} must be timezone-aware"
        )
    return parsed.astimezone(timezone.utc)


def _enum(enum_type, value: object, context: str):
    if not isinstance(value, str):
        raise PilotEvidenceMaterializationSerializationError(
            f"{context} must be a string"
        )
    try:
        return enum_type(value)
    except ValueError as exc:
        raise PilotEvidenceMaterializationSerializationError(
            f"invalid {context}: {value!r}"
        ) from exc


def _reject_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PilotEvidenceMaterializationSerializationError(
                f"duplicate JSON key: {key}"
            )
        result[key] = value
    return result


def _reject_constant(value: str):
    raise PilotEvidenceMaterializationSerializationError(
        f"non-finite JSON constant is not allowed: {value}"
    )


def _loads(value: str, context: str) -> object:
    if not isinstance(value, str):
        raise PilotEvidenceMaterializationSerializationError(
            f"{context} JSON must be a string"
        )
    try:
        return json.loads(
            value,
            object_pairs_hook=_reject_pairs,
            parse_constant=_reject_constant,
        )
    except PilotEvidenceMaterializationSerializationError:
        raise
    except json.JSONDecodeError as exc:
        raise PilotEvidenceMaterializationSerializationError(
            f"invalid {context} JSON"
        ) from exc


def _dumps(value: Mapping[str, Any]) -> str:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    )


def materialization_candidate_to_dict(
    value: PilotEvidenceMaterializationCandidate,
) -> dict[str, Any]:
    if not isinstance(value, PilotEvidenceMaterializationCandidate):
        raise PilotEvidenceMaterializationSerializationError(
            "value must be PilotEvidenceMaterializationCandidate"
        )
    return {
        "schema": MATERIALIZATION_CANDIDATE_SCHEMA,
        "schema_version": _SCHEMA_VERSION,
        "materialization_id": str(value.materialization_id),
        "policy_ref": str(value.policy_ref),
        "protocol_ref": str(value.protocol_ref),
        "session_id": value.session_id,
        "subject_ref": str(value.subject_ref),
        "capture_id": value.capture_id,
        "probe_id": value.probe_id,
        "capture_kind": value.capture_kind.value,
        "source_snapshot_sha256": value.source_snapshot_sha256,
        "source_capture_sha256": value.source_capture_sha256,
        "proposed_evidence_id": str(value.proposed_evidence_id),
        "proposed_at": _format_time(value.proposed_at),
    }


def materialization_candidate_from_dict(
    value: object,
) -> PilotEvidenceMaterializationCandidate:
    data = _mapping(value, "materialization candidate")
    fields = {
        "schema",
        "schema_version",
        "materialization_id",
        "policy_ref",
        "protocol_ref",
        "session_id",
        "subject_ref",
        "capture_id",
        "probe_id",
        "capture_kind",
        "source_snapshot_sha256",
        "source_capture_sha256",
        "proposed_evidence_id",
        "proposed_at",
    }
    _keys(data, fields, "materialization candidate")
    if data["schema"] != MATERIALIZATION_CANDIDATE_SCHEMA:
        raise PilotEvidenceMaterializationSerializationError(
            "invalid materialization candidate schema"
        )
    _schema_version(data["schema_version"], "materialization candidate")
    try:
        return PilotEvidenceMaterializationCandidate(
            materialization_id=PilotEvidenceMaterializationId(
                data["materialization_id"]
            ),
            policy_ref=PilotEvidenceMaterializationPolicyRef.parse(
                data["policy_ref"]
            ),
            protocol_ref=PilotProtocolRef.parse(data["protocol_ref"]),
            session_id=data["session_id"],
            subject_ref=CapabilitySubjectRef(data["subject_ref"]),
            capture_id=data["capture_id"],
            probe_id=data["probe_id"],
            capture_kind=_enum(
                PilotCaptureKind,
                data["capture_kind"],
                "materialization capture_kind",
            ),
            source_snapshot_sha256=data["source_snapshot_sha256"],
            source_capture_sha256=data["source_capture_sha256"],
            proposed_evidence_id=EvidenceId(data["proposed_evidence_id"]),
            proposed_at=_parse_time(data["proposed_at"], "proposed_at"),
        )
    except (InvalidPilotEvidenceMaterialization, ValueError) as exc:
        raise PilotEvidenceMaterializationSerializationError(str(exc)) from exc


def materialization_candidate_to_json(
    value: PilotEvidenceMaterializationCandidate,
) -> str:
    return _dumps(materialization_candidate_to_dict(value))


def materialization_candidate_from_json(
    value: str,
) -> PilotEvidenceMaterializationCandidate:
    return materialization_candidate_from_dict(
        _loads(value, "materialization candidate")
    )


def materialization_review_to_dict(
    value: PilotEvidenceMaterializationReview,
) -> dict[str, Any]:
    if not isinstance(value, PilotEvidenceMaterializationReview):
        raise PilotEvidenceMaterializationSerializationError(
            "value must be PilotEvidenceMaterializationReview"
        )
    return {
        "schema": MATERIALIZATION_REVIEW_SCHEMA,
        "schema_version": _SCHEMA_VERSION,
        "review_id": str(value.review_id),
        "materialization_id": str(value.materialization_id),
        "candidate_sha256": value.candidate_sha256,
        "policy_ref": str(value.policy_ref),
        "reviewer_kind": value.reviewer_ref.kind.value,
        "reviewer_ref": value.reviewer_ref.ref,
        "verdict": value.verdict.value,
        "reviewed_at": _format_time(value.reviewed_at),
        "rationale": value.rationale,
    }


def materialization_review_from_dict(
    value: object,
) -> PilotEvidenceMaterializationReview:
    data = _mapping(value, "materialization review")
    fields = {
        "schema",
        "schema_version",
        "review_id",
        "materialization_id",
        "candidate_sha256",
        "policy_ref",
        "reviewer_kind",
        "reviewer_ref",
        "verdict",
        "reviewed_at",
        "rationale",
    }
    _keys(data, fields, "materialization review")
    if data["schema"] != MATERIALIZATION_REVIEW_SCHEMA:
        raise PilotEvidenceMaterializationSerializationError(
            "invalid materialization review schema"
        )
    _schema_version(data["schema_version"], "materialization review")
    try:
        return PilotEvidenceMaterializationReview(
            review_id=PilotEvidenceMaterializationReviewId(data["review_id"]),
            materialization_id=PilotEvidenceMaterializationId(
                data["materialization_id"]
            ),
            candidate_sha256=data["candidate_sha256"],
            policy_ref=PilotEvidenceMaterializationPolicyRef.parse(
                data["policy_ref"]
            ),
            reviewer_ref=PilotEvidenceMaterializationReviewerRef(
                kind=_enum(
                    PilotEvidenceMaterializationReviewerKind,
                    data["reviewer_kind"],
                    "materialization reviewer_kind",
                ),
                ref=data["reviewer_ref"],
            ),
            verdict=_enum(
                PilotEvidenceMaterializationVerdict,
                data["verdict"],
                "materialization verdict",
            ),
            reviewed_at=_parse_time(data["reviewed_at"], "reviewed_at"),
            rationale=data["rationale"],
        )
    except (InvalidPilotEvidenceMaterialization, ValueError) as exc:
        raise PilotEvidenceMaterializationSerializationError(str(exc)) from exc


def materialization_review_to_json(
    value: PilotEvidenceMaterializationReview,
) -> str:
    return _dumps(materialization_review_to_dict(value))


def materialization_review_from_json(
    value: str,
) -> PilotEvidenceMaterializationReview:
    return materialization_review_from_dict(_loads(value, "materialization review"))
