"""Strict deterministic serialization for PR12.3 interpretation reviews and ledgers."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import re

from .core import (
    ExternalEvidenceInterpretationPolicyRef,
    ExternalEvidenceInterpretationProposalId,
    InvalidExternalEvidenceInterpretation,
)
from .review import (
    ExternalEvidenceClaimInterpretationReview,
    ExternalEvidenceInterpretationReviewId,
    ExternalEvidenceInterpretationReviewerKind,
    ExternalEvidenceInterpretationReviewerRef,
    ExternalEvidenceInterpretationReviewVerdict,
    _strict_review,
)

_SCHEMA_VERSION = 1
_TIME_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]{1,6})?(?:Z|[+-][0-9]{2}:[0-9]{2})$"
)


def _fail(message: str) -> None:
    raise InvalidExternalEvidenceInterpretation(message)


def _obj(payload: object, fields: set[str], label: str) -> dict:
    if type(payload) is not dict:
        _fail(f"{label} must be a JSON object")
    actual = set(payload)
    if actual != fields:
        _fail(
            f"{label} fields must match schema exactly; "
            f"missing={tuple(sorted(fields-actual))!r}, "
            f"unknown={tuple(sorted(actual-fields))!r}"
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
        raise InvalidExternalEvidenceInterpretation(
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
    except InvalidExternalEvidenceInterpretation:
        raise
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise InvalidExternalEvidenceInterpretation(
            f"invalid JSON payload: {exc}"
        ) from exc


def _dumps(payload: object) -> str:
    try:
        return json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise InvalidExternalEvidenceInterpretation(
            f"payload is not canonically JSON serializable: {exc}"
        ) from exc


def external_evidence_claim_interpretation_review_to_dict(
    value: ExternalEvidenceClaimInterpretationReview,
) -> dict:
    _strict_review(value)
    return {
        "schema_version": _SCHEMA_VERSION,
        "review_id": str(value.review_id),
        "policy_ref": str(value.policy_ref),
        "proposal_id": str(value.proposal_id),
        "candidate_sha256": value.candidate_sha256,
        "reviewer_ref": {
            "kind": value.reviewer_ref.kind.value,
            "ref": value.reviewer_ref.ref,
        },
        "verdict": value.verdict.value,
        "reviewed_at": _format_time(value.reviewed_at),
        "rationale": value.rationale,
    }


def external_evidence_claim_interpretation_review_from_dict(
    payload: object,
) -> ExternalEvidenceClaimInterpretationReview:
    fields = {
        "schema_version",
        "review_id",
        "policy_ref",
        "proposal_id",
        "candidate_sha256",
        "reviewer_ref",
        "verdict",
        "reviewed_at",
        "rationale",
    }
    obj = _obj(payload, fields, "interpretation review")
    if type(obj["schema_version"]) is not int or obj["schema_version"] != _SCHEMA_VERSION:
        _fail("review schema_version must be exact integer 1")
    reviewer = _obj(obj["reviewer_ref"], {"kind", "ref"}, "reviewer_ref")
    try:
        result = ExternalEvidenceClaimInterpretationReview(
            review_id=ExternalEvidenceInterpretationReviewId(obj["review_id"]),
            policy_ref=ExternalEvidenceInterpretationPolicyRef.parse(obj["policy_ref"]),
            proposal_id=ExternalEvidenceInterpretationProposalId(obj["proposal_id"]),
            candidate_sha256=obj["candidate_sha256"],
            reviewer_ref=ExternalEvidenceInterpretationReviewerRef(
                ExternalEvidenceInterpretationReviewerKind(reviewer["kind"]),
                reviewer["ref"],
            ),
            verdict=ExternalEvidenceInterpretationReviewVerdict(obj["verdict"]),
            reviewed_at=_parse_time(obj["reviewed_at"], "reviewed_at"),
            rationale=obj["rationale"],
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InvalidExternalEvidenceInterpretation):
            raise
        raise InvalidExternalEvidenceInterpretation(
            f"invalid interpretation review: {exc}"
        ) from exc
    return _strict_review(result)


def external_evidence_claim_interpretation_review_to_json(value) -> str:
    return _dumps(external_evidence_claim_interpretation_review_to_dict(value))


def external_evidence_claim_interpretation_review_from_json(payload: object):
    return external_evidence_claim_interpretation_review_from_dict(_loads(payload))


def external_evidence_claim_interpretation_review_ledger_to_dict(value) -> dict:
    from .review_ledger import _strict_review_ledger

    _strict_review_ledger(value)
    return {
        "schema_version": _SCHEMA_VERSION,
        "reviews": [
            external_evidence_claim_interpretation_review_to_dict(review)
            for review in value.reviews
        ],
    }


def external_evidence_claim_interpretation_review_ledger_from_dict(payload: object):
    from .review_ledger import ExternalEvidenceInterpretationReviewLedger

    obj = _obj(payload, {"schema_version", "reviews"}, "interpretation review ledger")
    if type(obj["schema_version"]) is not int or obj["schema_version"] != _SCHEMA_VERSION:
        _fail("review ledger schema_version must be exact integer 1")
    if type(obj["reviews"]) is not list:
        _fail("review ledger reviews must be an array")
    return ExternalEvidenceInterpretationReviewLedger(
        reviews=tuple(
            external_evidence_claim_interpretation_review_from_dict(item)
            for item in obj["reviews"]
        )
    )


def external_evidence_claim_interpretation_review_ledger_to_json(value) -> str:
    return _dumps(external_evidence_claim_interpretation_review_ledger_to_dict(value))


def external_evidence_claim_interpretation_review_ledger_from_json(payload: object):
    return external_evidence_claim_interpretation_review_ledger_from_dict(_loads(payload))
