"""Strict deterministic serialization for PR2 epistemic records."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any, TypeVar

from capability_lab.semantics import CapabilityConceptRef

from .core import (
    ActorRef,
    CapabilityClaim,
    CapabilityClaimId,
    CapabilitySubjectRef,
    ClaimEvaluation,
    ClaimEvaluationId,
    ClaimScope,
    ConflictStatus,
    ContextFactor,
    ContextFactorKind,
    CoverageAssessment,
    CoverageStatus,
    EpistemicError,
    EvaluationConclusion,
    EvaluationPolicyRef,
    EvaluatorKind,
    EvaluatorRef,
    EvidenceAssessment,
    EvidenceBearing,
    EvidenceContext,
    EvidenceId,
    EvidenceKind,
    EvidenceOutcome,
    EvidenceOutcomeStatus,
    EvidenceRecord,
    EvidenceReliability,
    ProvenanceSource,
    ProvenanceSourceKind,
    ProvenanceStep,
    ProvenanceTrail,
    format_time,
    parse_time,
)
from .record_set import EpistemicRecordSet, InvalidRecordSetError

_SCHEMA = "capability_epistemics/v1"
E = TypeVar("E")


def _mapping(value: object, context: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise InvalidRecordSetError(f"{context} must be an object")
    if any(not isinstance(key, str) for key in value):
        raise InvalidRecordSetError(f"{context} keys must be strings")
    return value


def _sequence(value: object, context: str) -> Sequence[Any]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise InvalidRecordSetError(f"{context} must be an array")
    return value


def _keys(value: Mapping[str, Any], allowed: set[str], required: set[str], context: str) -> None:
    unknown = sorted(set(value) - allowed)
    missing = sorted(required - set(value))
    if unknown:
        raise InvalidRecordSetError(f"{context} contains unknown fields: {', '.join(unknown)}")
    if missing:
        raise InvalidRecordSetError(f"{context} is missing fields: {', '.join(missing)}")


def _enum(enum_type, value: object, context: str):
    if not isinstance(value, str):
        raise InvalidRecordSetError(f"{context} must be a string enum value")
    try:
        return enum_type(value)
    except ValueError as exc:
        raise InvalidRecordSetError(f"invalid {context}: {value!r}") from exc


def _strings(value: object, context: str) -> tuple[str, ...]:
    items = _sequence(value, context)
    if any(not isinstance(item, str) for item in items):
        raise InvalidRecordSetError(f"{context} must contain strings")
    return tuple(items)


def _source_to_dict(value: ProvenanceSource) -> dict[str, Any]:
    return {"kind": value.kind.value, "ref": value.ref}


def _source_from_dict(value: object) -> ProvenanceSource:
    data = _mapping(value, "provenance source")
    _keys(data, {"kind", "ref"}, {"kind", "ref"}, "provenance source")
    return ProvenanceSource(_enum(ProvenanceSourceKind, data["kind"], "provenance source kind"), data["ref"])


def _step_to_dict(value: ProvenanceStep) -> dict[str, Any]:
    return {
        "operation_key": value.operation_key,
        "occurred_at": format_time(value.occurred_at),
        "actor_ref": str(value.actor_ref) if value.actor_ref else None,
        "mechanism_ref": value.mechanism_ref,
        "note": value.note,
    }


def _step_from_dict(value: object) -> ProvenanceStep:
    data = _mapping(value, "provenance step")
    allowed = {"operation_key", "occurred_at", "actor_ref", "mechanism_ref", "note"}
    _keys(data, allowed, allowed, "provenance step")
    actor = None if data["actor_ref"] is None else ActorRef(data["actor_ref"])
    return ProvenanceStep(
        operation_key=data["operation_key"],
        occurred_at=parse_time(data["occurred_at"], "provenance occurred_at"),
        actor_ref=actor,
        mechanism_ref=data["mechanism_ref"],
        note=data["note"],
    )


def _provenance_to_dict(value: ProvenanceTrail) -> dict[str, Any]:
    return {
        "sources": [_source_to_dict(item) for item in value.sources],
        "steps": [_step_to_dict(item) for item in value.steps],
    }


def _provenance_from_dict(value: object) -> ProvenanceTrail:
    data = _mapping(value, "provenance")
    _keys(data, {"sources", "steps"}, {"sources", "steps"}, "provenance")
    return ProvenanceTrail(
        sources=tuple(_source_from_dict(item) for item in _sequence(data["sources"], "provenance sources")),
        steps=tuple(_step_from_dict(item) for item in _sequence(data["steps"], "provenance steps")),
    )


def _context_to_dict(value: EvidenceContext) -> dict[str, Any]:
    return {
        "description": value.description,
        "scope_tags": list(value.scope_tags),
        "factors": [
            {"kind": item.kind.value, "description": item.description}
            for item in value.factors
        ],
    }


def _context_from_dict(value: object) -> EvidenceContext:
    data = _mapping(value, "evidence context")
    allowed = {"description", "scope_tags", "factors"}
    _keys(data, allowed, allowed, "evidence context")
    factors = []
    for raw in _sequence(data["factors"], "context factors"):
        item = _mapping(raw, "context factor")
        _keys(item, {"kind", "description"}, {"kind", "description"}, "context factor")
        factors.append(ContextFactor(_enum(ContextFactorKind, item["kind"], "context factor kind"), item["description"]))
    return EvidenceContext(data["description"], _strings(data["scope_tags"], "scope_tags"), tuple(factors))


def _outcome_to_dict(value: EvidenceOutcome | None) -> dict[str, Any] | None:
    if value is None:
        return None
    return {"status": value.status.value, "description": value.description}


def _outcome_from_dict(value: object) -> EvidenceOutcome | None:
    if value is None:
        return None
    data = _mapping(value, "evidence outcome")
    _keys(data, {"status", "description"}, {"status", "description"}, "evidence outcome")
    return EvidenceOutcome(_enum(EvidenceOutcomeStatus, data["status"], "evidence outcome status"), data["description"])


def _evidence_to_dict(value: EvidenceRecord) -> dict[str, Any]:
    return {
        "evidence_id": str(value.evidence_id),
        "subject_ref": str(value.subject_ref),
        "kind": value.kind.value,
        "summary": value.summary,
        "context": _context_to_dict(value.context),
        "observation_started_at": (
            format_time(value.observation_started_at)
            if value.observation_started_at is not None
            else None
        ),
        "observed_at": format_time(value.observed_at),
        "recorded_at": format_time(value.recorded_at),
        "provenance": _provenance_to_dict(value.provenance),
        "outcome": _outcome_to_dict(value.outcome),
        "payload_refs": list(value.payload_refs),
    }


def _evidence_from_dict(value: object) -> EvidenceRecord:
    data = _mapping(value, "evidence record")
    allowed = {
        "evidence_id",
        "subject_ref",
        "kind",
        "summary",
        "context",
        "observation_started_at",
        "observed_at",
        "recorded_at",
        "provenance",
        "outcome",
        "payload_refs",
    }
    _keys(data, allowed, allowed, "evidence record")
    observation_started_at = (
        None
        if data["observation_started_at"] is None
        else parse_time(data["observation_started_at"], "observation_started_at")
    )
    return EvidenceRecord(
        evidence_id=EvidenceId(data["evidence_id"]),
        subject_ref=CapabilitySubjectRef(data["subject_ref"]),
        kind=_enum(EvidenceKind, data["kind"], "evidence kind"),
        summary=data["summary"],
        context=_context_from_dict(data["context"]),
        observed_at=parse_time(data["observed_at"], "observed_at"),
        recorded_at=parse_time(data["recorded_at"], "recorded_at"),
        provenance=_provenance_from_dict(data["provenance"]),
        observation_started_at=observation_started_at,
        outcome=_outcome_from_dict(data["outcome"]),
        payload_refs=_strings(data["payload_refs"], "payload_refs"),
    )


def _claim_to_dict(value: CapabilityClaim) -> dict[str, Any]:
    return {
        "claim_id": str(value.claim_id),
        "subject_ref": str(value.subject_ref),
        "concept_ref": str(value.concept_ref),
        "statement": value.statement,
        "scope": {"description": value.scope.description, "tags": list(value.scope.tags)},
        "created_at": format_time(value.created_at),
        "provenance": _provenance_to_dict(value.provenance),
    }


def _claim_from_dict(value: object) -> CapabilityClaim:
    data = _mapping(value, "capability claim")
    allowed = {"claim_id", "subject_ref", "concept_ref", "statement", "scope", "created_at", "provenance"}
    _keys(data, allowed, allowed, "capability claim")
    scope = _mapping(data["scope"], "claim scope")
    _keys(scope, {"description", "tags"}, {"description", "tags"}, "claim scope")
    return CapabilityClaim(
        claim_id=CapabilityClaimId(data["claim_id"]),
        subject_ref=CapabilitySubjectRef(data["subject_ref"]),
        concept_ref=CapabilityConceptRef.parse(data["concept_ref"]),
        statement=data["statement"],
        scope=ClaimScope(scope["description"], _strings(scope["tags"], "claim scope tags")),
        created_at=parse_time(data["created_at"], "claim created_at"),
        provenance=_provenance_from_dict(data["provenance"]),
    )


def _assessment_to_dict(value: EvidenceAssessment) -> dict[str, Any]:
    return {
        "evidence_id": str(value.evidence_id),
        "bearing": value.bearing.value,
        "reliability": value.reliability.value,
        "coverage_note": value.coverage_note,
        "rationale": value.rationale,
    }


def _assessment_from_dict(value: object) -> EvidenceAssessment:
    data = _mapping(value, "evidence assessment")
    allowed = {"evidence_id", "bearing", "reliability", "coverage_note", "rationale"}
    _keys(data, allowed, allowed, "evidence assessment")
    return EvidenceAssessment(
        EvidenceId(data["evidence_id"]),
        _enum(EvidenceBearing, data["bearing"], "evidence bearing"),
        _enum(EvidenceReliability, data["reliability"], "evidence reliability"),
        data["coverage_note"],
        data["rationale"],
    )


def _evaluation_to_dict(value: ClaimEvaluation) -> dict[str, Any]:
    return {
        "evaluation_id": str(value.evaluation_id),
        "claim_id": str(value.claim_id),
        "policy_ref": str(value.policy_ref),
        "evaluator_ref": {"kind": value.evaluator_ref.kind.value, "ref": value.evaluator_ref.ref},
        "evaluated_at": format_time(value.evaluated_at),
        "evidence_assessments": [_assessment_to_dict(item) for item in value.evidence_assessments],
        "coverage": {"status": value.coverage.status.value, "notes": value.coverage.notes},
        "conflict_status": value.conflict_status.value,
        "conclusion": value.conclusion.value,
        "rationale": value.rationale,
    }


def _evaluation_from_dict(value: object) -> ClaimEvaluation:
    data = _mapping(value, "claim evaluation")
    allowed = {"evaluation_id", "claim_id", "policy_ref", "evaluator_ref", "evaluated_at", "evidence_assessments", "coverage", "conflict_status", "conclusion", "rationale"}
    _keys(data, allowed, allowed, "claim evaluation")
    evaluator = _mapping(data["evaluator_ref"], "evaluator ref")
    _keys(evaluator, {"kind", "ref"}, {"kind", "ref"}, "evaluator ref")
    coverage = _mapping(data["coverage"], "coverage assessment")
    _keys(coverage, {"status", "notes"}, {"status", "notes"}, "coverage assessment")
    return ClaimEvaluation(
        evaluation_id=ClaimEvaluationId(data["evaluation_id"]),
        claim_id=CapabilityClaimId(data["claim_id"]),
        policy_ref=EvaluationPolicyRef.parse(data["policy_ref"]),
        evaluator_ref=EvaluatorRef(_enum(EvaluatorKind, evaluator["kind"], "evaluator kind"), evaluator["ref"]),
        evaluated_at=parse_time(data["evaluated_at"], "evaluated_at"),
        evidence_assessments=tuple(_assessment_from_dict(item) for item in _sequence(data["evidence_assessments"], "evidence assessments")),
        coverage=CoverageAssessment(_enum(CoverageStatus, coverage["status"], "coverage status"), coverage["notes"]),
        conflict_status=_enum(ConflictStatus, data["conflict_status"], "conflict status"),
        conclusion=_enum(EvaluationConclusion, data["conclusion"], "evaluation conclusion"),
        rationale=data["rationale"],
    )


def record_set_to_dict(value: EpistemicRecordSet) -> dict[str, Any]:
    if not isinstance(value, EpistemicRecordSet):
        raise InvalidRecordSetError("value must be EpistemicRecordSet")
    return {
        "schema": _SCHEMA,
        "evidence_records": [_evidence_to_dict(item) for item in value.evidence_records],
        "claims": [_claim_to_dict(item) for item in value.claims],
        "evaluations": [_evaluation_to_dict(item) for item in value.evaluations],
    }


def record_set_from_dict(payload: object) -> EpistemicRecordSet:
    data = _mapping(payload, "epistemic record set")
    allowed = {"schema", "evidence_records", "claims", "evaluations"}
    _keys(data, allowed, allowed, "epistemic record set")
    if data["schema"] != _SCHEMA:
        raise InvalidRecordSetError(f"unsupported epistemic schema: {data['schema']!r}")
    try:
        return EpistemicRecordSet(
            evidence_records=tuple(_evidence_from_dict(item) for item in _sequence(data["evidence_records"], "evidence_records")),
            claims=tuple(_claim_from_dict(item) for item in _sequence(data["claims"], "claims")),
            evaluations=tuple(_evaluation_from_dict(item) for item in _sequence(data["evaluations"], "evaluations")),
        )
    except EpistemicError:
        raise
    except (TypeError, ValueError) as exc:
        raise InvalidRecordSetError(f"invalid epistemic record set: {exc}") from exc


def _loads_strict(payload: object) -> Mapping[str, Any]:
    if not isinstance(payload, str):
        raise InvalidRecordSetError("epistemic JSON payload must be a string")

    def pairs_hook(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise InvalidRecordSetError(f"duplicate JSON object key: {key!r}")
            result[key] = value
        return result

    def reject_constant(value: str):
        raise InvalidRecordSetError(f"non-standard JSON numeric constant is not allowed: {value}")

    try:
        decoded = json.loads(payload, object_pairs_hook=pairs_hook, parse_constant=reject_constant)
    except json.JSONDecodeError as exc:
        raise InvalidRecordSetError(f"invalid epistemic JSON: {exc}") from exc
    return _mapping(decoded, "epistemic JSON root")


def record_set_to_json(value: EpistemicRecordSet) -> str:
    return json.dumps(record_set_to_dict(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def record_set_from_json(payload: object) -> EpistemicRecordSet:
    return record_set_from_dict(_loads_strict(payload))
