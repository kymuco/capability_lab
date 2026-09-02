"""Strict serialization for PR12.1 candidate and human review artifacts."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import re

from capability_lab.epistemics import CapabilitySubjectRef, EvidenceId

from .core import (
    ExternalObservationForm,
    ExternalObservationId,
    ExternalObservationOriginKind,
    ExternalObservationSourceKind,
    ExternalObservationSourceRef,
)
from .materialization import (
    ExternalObservationEvidenceMaterializationCandidate,
    ExternalObservationEvidenceMaterializationId,
    ExternalObservationEvidenceMaterializationPolicyRef,
    ExternalObservationEvidenceMaterializationReview,
    ExternalObservationEvidenceMaterializationVerdict,
    ExternalObservationEvidenceReviewId,
    ExternalObservationEvidenceReviewerKind,
    ExternalObservationEvidenceReviewerRef,
    InvalidExternalObservationEvidenceMaterialization,
    _strict_candidate,
    _strict_review,
)

_SCHEMA_VERSION = 1
_TIME_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]{1,6})?(?:Z|[+-][0-9]{2}:[0-9]{2})$"
)

def _fail(message: str) -> None:
    raise InvalidExternalObservationEvidenceMaterialization(message)

def _obj(payload: object, fields: set[str], label: str) -> dict:
    if type(payload) is not dict:
        _fail(f"{label} must be a JSON object")
    actual = set(payload)
    if actual != fields:
        _fail(
            f"{label} fields must match schema exactly; "
            f"missing={tuple(sorted(fields-actual))!r}, unknown={tuple(sorted(actual-fields))!r}"
        )
    return payload

def _format_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

def _parse_time(value: object, label: str) -> datetime:
    if type(value) is not str or _TIME_RE.fullmatch(value) is None:
        _fail(f"{label} must use extended ISO-8601 with explicit timezone")
    raw = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise InvalidExternalObservationEvidenceMaterialization(
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
    except InvalidExternalObservationEvidenceMaterialization:
        raise
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise InvalidExternalObservationEvidenceMaterialization(
            f"invalid JSON payload: {exc}"
        ) from exc

def _dumps(payload: object) -> str:
    try:
        return json.dumps(
            payload, ensure_ascii=True, sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise InvalidExternalObservationEvidenceMaterialization(
            f"payload is not canonically JSON serializable: {exc}"
        ) from exc

def _source_to_dict(value: ExternalObservationSourceRef) -> dict:
    return {"kind": value.kind.value, "ref": value.ref}

def _source_from_dict(payload: object) -> ExternalObservationSourceRef:
    obj = _obj(payload, {"kind", "ref"}, "source_ref")
    try:
        return ExternalObservationSourceRef(
            ExternalObservationSourceKind(obj["kind"]), obj["ref"]
        )
    except (TypeError, ValueError) as exc:
        raise InvalidExternalObservationEvidenceMaterialization(
            f"invalid source_ref: {exc}"
        ) from exc

def external_observation_evidence_candidate_to_dict(
    value: ExternalObservationEvidenceMaterializationCandidate,
) -> dict:
    _strict_candidate(value)
    return {
        "schema_version": _SCHEMA_VERSION,
        "materialization_id": str(value.materialization_id),
        "policy_ref": str(value.policy_ref),
        "observation_id": str(value.observation_id),
        "observation_sha256": value.observation_sha256,
        "subject_ref": str(value.subject_ref),
        "source_ref": _source_to_dict(value.source_ref),
        "source_event_id": value.source_event_id,
        "form": value.form.value,
        "origin_kind": value.origin_kind.value,
        "materialized_evidence_id": str(value.materialized_evidence_id),
        "proposed_at": _format_time(value.proposed_at),
    }

def external_observation_evidence_candidate_from_dict(
    payload: object,
) -> ExternalObservationEvidenceMaterializationCandidate:
    fields = {
        "schema_version", "materialization_id", "policy_ref", "observation_id",
        "observation_sha256", "subject_ref", "source_ref", "source_event_id",
        "form", "origin_kind", "materialized_evidence_id", "proposed_at",
    }
    obj = _obj(payload, fields, "materialization candidate")
    if type(obj["schema_version"]) is not int or obj["schema_version"] != _SCHEMA_VERSION:
        _fail("candidate schema_version must be exact integer 1")
    try:
        result = ExternalObservationEvidenceMaterializationCandidate(
            materialization_id=ExternalObservationEvidenceMaterializationId(
                obj["materialization_id"]
            ),
            policy_ref=ExternalObservationEvidenceMaterializationPolicyRef.parse(
                obj["policy_ref"]
            ),
            observation_id=ExternalObservationId(obj["observation_id"]),
            observation_sha256=obj["observation_sha256"],
            subject_ref=CapabilitySubjectRef(obj["subject_ref"]),
            source_ref=_source_from_dict(obj["source_ref"]),
            source_event_id=obj["source_event_id"],
            form=ExternalObservationForm(obj["form"]),
            origin_kind=ExternalObservationOriginKind(obj["origin_kind"]),
            materialized_evidence_id=EvidenceId(obj["materialized_evidence_id"]),
            proposed_at=_parse_time(obj["proposed_at"], "proposed_at"),
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InvalidExternalObservationEvidenceMaterialization):
            raise
        raise InvalidExternalObservationEvidenceMaterialization(
            f"invalid materialization candidate: {exc}"
        ) from exc
    return _strict_candidate(result)

def external_observation_evidence_candidate_to_json(value) -> str:
    return _dumps(external_observation_evidence_candidate_to_dict(value))

def external_observation_evidence_candidate_from_json(payload: object):
    return external_observation_evidence_candidate_from_dict(_loads(payload))

def external_observation_evidence_review_to_dict(
    value: ExternalObservationEvidenceMaterializationReview,
) -> dict:
    _strict_review(value)
    return {
        "schema_version": _SCHEMA_VERSION,
        "review_id": str(value.review_id),
        "materialization_id": str(value.materialization_id),
        "candidate_sha256": value.candidate_sha256,
        "policy_ref": str(value.policy_ref),
        "reviewer_ref": {
            "kind": value.reviewer_ref.kind.value,
            "ref": value.reviewer_ref.ref,
        },
        "verdict": value.verdict.value,
        "reviewed_at": _format_time(value.reviewed_at),
        "rationale": value.rationale,
    }

def external_observation_evidence_review_from_dict(
    payload: object,
) -> ExternalObservationEvidenceMaterializationReview:
    fields = {
        "schema_version", "review_id", "materialization_id", "candidate_sha256",
        "policy_ref", "reviewer_ref", "verdict", "reviewed_at", "rationale",
    }
    obj = _obj(payload, fields, "materialization review")
    if type(obj["schema_version"]) is not int or obj["schema_version"] != _SCHEMA_VERSION:
        _fail("review schema_version must be exact integer 1")
    reviewer = _obj(obj["reviewer_ref"], {"kind", "ref"}, "reviewer_ref")
    try:
        result = ExternalObservationEvidenceMaterializationReview(
            review_id=ExternalObservationEvidenceReviewId(obj["review_id"]),
            materialization_id=ExternalObservationEvidenceMaterializationId(
                obj["materialization_id"]
            ),
            candidate_sha256=obj["candidate_sha256"],
            policy_ref=ExternalObservationEvidenceMaterializationPolicyRef.parse(
                obj["policy_ref"]
            ),
            reviewer_ref=ExternalObservationEvidenceReviewerRef(
                ExternalObservationEvidenceReviewerKind(reviewer["kind"]),
                reviewer["ref"],
            ),
            verdict=ExternalObservationEvidenceMaterializationVerdict(obj["verdict"]),
            reviewed_at=_parse_time(obj["reviewed_at"], "reviewed_at"),
            rationale=obj["rationale"],
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InvalidExternalObservationEvidenceMaterialization):
            raise
        raise InvalidExternalObservationEvidenceMaterialization(
            f"invalid materialization review: {exc}"
        ) from exc
    return _strict_review(result)

def external_observation_evidence_review_to_json(value) -> str:
    return _dumps(external_observation_evidence_review_to_dict(value))

def external_observation_evidence_review_from_json(payload: object):
    return external_observation_evidence_review_from_dict(_loads(payload))
