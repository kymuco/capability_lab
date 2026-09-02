"""Strict deterministic serialization for PR12.2 interpretation candidates."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import re

from capability_lab.epistemics import CapabilitySubjectRef, ClaimScope, EvidenceId
from capability_lab.semantics import CapabilityConceptRef

from .core import (
    ExternalEvidenceClaimInterpretationCandidate,
    ExternalEvidenceInterpretationPolicyRef,
    ExternalEvidenceInterpretationProposalId,
    ExternalEvidenceInterpretationProposerKind,
    ExternalEvidenceInterpretationProposerRef,
    InvalidExternalEvidenceInterpretation,
    _strict_candidate,
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


def external_evidence_claim_interpretation_candidate_to_dict(
    value: ExternalEvidenceClaimInterpretationCandidate,
) -> dict:
    _strict_candidate(value)
    return {
        "schema_version": _SCHEMA_VERSION,
        "proposal_id": str(value.proposal_id),
        "policy_ref": str(value.policy_ref),
        "evidence_id": str(value.evidence_id),
        "evidence_sha256": value.evidence_sha256,
        "subject_ref": str(value.subject_ref),
        "concept_ref": str(value.concept_ref),
        "claim_statement": value.claim_statement,
        "claim_scope": {
            "description": value.claim_scope.description,
            "tags": list(value.claim_scope.tags),
        },
        "proposer_ref": {
            "kind": value.proposer_ref.kind.value,
            "ref": value.proposer_ref.ref,
        },
        "proposed_at": _format_time(value.proposed_at),
        "rationale": value.rationale,
    }


def external_evidence_claim_interpretation_candidate_from_dict(
    payload: object,
) -> ExternalEvidenceClaimInterpretationCandidate:
    fields = {
        "schema_version",
        "proposal_id",
        "policy_ref",
        "evidence_id",
        "evidence_sha256",
        "subject_ref",
        "concept_ref",
        "claim_statement",
        "claim_scope",
        "proposer_ref",
        "proposed_at",
        "rationale",
    }
    obj = _obj(payload, fields, "interpretation candidate")
    if type(obj["schema_version"]) is not int or obj["schema_version"] != _SCHEMA_VERSION:
        _fail("candidate schema_version must be exact integer 1")
    scope = _obj(obj["claim_scope"], {"description", "tags"}, "claim_scope")
    if type(scope["tags"]) is not list or any(type(item) is not str for item in scope["tags"]):
        _fail("claim_scope tags must be an array of strings")
    proposer = _obj(obj["proposer_ref"], {"kind", "ref"}, "proposer_ref")
    try:
        result = ExternalEvidenceClaimInterpretationCandidate(
            proposal_id=ExternalEvidenceInterpretationProposalId(obj["proposal_id"]),
            policy_ref=ExternalEvidenceInterpretationPolicyRef.parse(obj["policy_ref"]),
            evidence_id=EvidenceId(obj["evidence_id"]),
            evidence_sha256=obj["evidence_sha256"],
            subject_ref=CapabilitySubjectRef(obj["subject_ref"]),
            concept_ref=CapabilityConceptRef.parse(obj["concept_ref"]),
            claim_statement=obj["claim_statement"],
            claim_scope=ClaimScope(scope["description"], tuple(scope["tags"])),
            proposer_ref=ExternalEvidenceInterpretationProposerRef(
                ExternalEvidenceInterpretationProposerKind(proposer["kind"]),
                proposer["ref"],
            ),
            proposed_at=_parse_time(obj["proposed_at"], "proposed_at"),
            rationale=obj["rationale"],
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InvalidExternalEvidenceInterpretation):
            raise
        raise InvalidExternalEvidenceInterpretation(
            f"invalid interpretation candidate: {exc}"
        ) from exc
    return _strict_candidate(result)


def external_evidence_claim_interpretation_candidate_to_json(value) -> str:
    return _dumps(external_evidence_claim_interpretation_candidate_to_dict(value))


def external_evidence_claim_interpretation_candidate_from_json(payload: object):
    return external_evidence_claim_interpretation_candidate_from_dict(_loads(payload))
