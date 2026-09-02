"""Strict deterministic serialization for PR12.5 evaluation admission receipts."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import re

from capability_lab.epistemics import (
    CapabilityClaimId,
    ClaimEvaluationId,
    EvaluationPolicyRef,
    EvidenceId,
)

from .core import (
    ExternalEvidenceInterpretationProposalId,
    InvalidExternalEvidenceInterpretation,
)
from .generic_claim_evaluation import (
    ExternalEvidenceClaimEvaluationAdmissionReceipt,
)
from .review import ExternalEvidenceInterpretationReviewId


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


def external_evidence_claim_evaluation_admission_receipt_to_dict(
    value: ExternalEvidenceClaimEvaluationAdmissionReceipt,
) -> dict:
    if type(value) is not ExternalEvidenceClaimEvaluationAdmissionReceipt:
        _fail(
            "evaluation admission receipt must use exact "
            "ExternalEvidenceClaimEvaluationAdmissionReceipt"
        )
    return {
        "schema_version": _SCHEMA_VERSION,
        "policy_ref": str(value.policy_ref),
        "proposal_id": str(value.proposal_id),
        "candidate_sha256": value.candidate_sha256,
        "review_id": str(value.review_id),
        "review_sha256": value.review_sha256,
        "claim_materialization_receipt_sha256": value.claim_materialization_receipt_sha256,
        "evidence_id": str(value.evidence_id),
        "evidence_sha256": value.evidence_sha256,
        "claim_id": str(value.claim_id),
        "claim_sha256": value.claim_sha256,
        "evaluation_id": str(value.evaluation_id),
        "evaluation_sha256": value.evaluation_sha256,
        "predecessor_snapshot_sha256": value.predecessor_snapshot_sha256,
        "successor_snapshot_sha256": value.successor_snapshot_sha256,
        "evaluated_at": _format_time(value.evaluated_at),
    }


def external_evidence_claim_evaluation_admission_receipt_from_dict(
    payload: object,
) -> ExternalEvidenceClaimEvaluationAdmissionReceipt:
    fields = {
        "schema_version",
        "policy_ref",
        "proposal_id",
        "candidate_sha256",
        "review_id",
        "review_sha256",
        "claim_materialization_receipt_sha256",
        "evidence_id",
        "evidence_sha256",
        "claim_id",
        "claim_sha256",
        "evaluation_id",
        "evaluation_sha256",
        "predecessor_snapshot_sha256",
        "successor_snapshot_sha256",
        "evaluated_at",
    }
    obj = _obj(payload, fields, "external evidence claim evaluation admission receipt")
    if type(obj["schema_version"]) is not int or obj["schema_version"] != _SCHEMA_VERSION:
        _fail("evaluation admission receipt schema_version must be exact integer 1")
    try:
        result = ExternalEvidenceClaimEvaluationAdmissionReceipt(
            policy_ref=EvaluationPolicyRef.parse(obj["policy_ref"]),
            proposal_id=ExternalEvidenceInterpretationProposalId(obj["proposal_id"]),
            candidate_sha256=obj["candidate_sha256"],
            review_id=ExternalEvidenceInterpretationReviewId(obj["review_id"]),
            review_sha256=obj["review_sha256"],
            claim_materialization_receipt_sha256=obj[
                "claim_materialization_receipt_sha256"
            ],
            evidence_id=EvidenceId(obj["evidence_id"]),
            evidence_sha256=obj["evidence_sha256"],
            claim_id=CapabilityClaimId(obj["claim_id"]),
            claim_sha256=obj["claim_sha256"],
            evaluation_id=ClaimEvaluationId(obj["evaluation_id"]),
            evaluation_sha256=obj["evaluation_sha256"],
            predecessor_snapshot_sha256=obj["predecessor_snapshot_sha256"],
            successor_snapshot_sha256=obj["successor_snapshot_sha256"],
            evaluated_at=_parse_time(obj["evaluated_at"], "evaluated_at"),
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InvalidExternalEvidenceInterpretation):
            raise
        raise InvalidExternalEvidenceInterpretation(
            f"invalid evaluation admission receipt: {exc}"
        ) from exc
    # Re-serialize to ensure every typed field has exact canonical semantics.
    if external_evidence_claim_evaluation_admission_receipt_to_dict(result) != obj:
        # schema_version is intentionally not stored in the dataclass; compare
        # against the exact canonical representation including it.
        canonical = external_evidence_claim_evaluation_admission_receipt_to_dict(result)
        if canonical != obj:
            _fail("evaluation admission receipt must equal canonical reconstruction")
    return result


def external_evidence_claim_evaluation_admission_receipt_to_json(
    value: ExternalEvidenceClaimEvaluationAdmissionReceipt,
) -> str:
    return _dumps(external_evidence_claim_evaluation_admission_receipt_to_dict(value))


def external_evidence_claim_evaluation_admission_receipt_from_json(
    payload: object,
) -> ExternalEvidenceClaimEvaluationAdmissionReceipt:
    return external_evidence_claim_evaluation_admission_receipt_from_dict(
        _loads(payload)
    )
