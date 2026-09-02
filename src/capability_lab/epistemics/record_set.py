"""Cross-record validation for immutable epistemic snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .core import (
    CapabilityClaim,
    ClaimEvaluation,
    EpistemicError,
    EvidenceRecord,
    ProvenanceSourceKind,
)

if TYPE_CHECKING:
    from capability_lab.semantics import CapabilityCatalog


class InvalidRecordSetError(EpistemicError):
    pass


@dataclass(frozen=True, slots=True)
class EpistemicRecordSet:
    """Immutable snapshot of person-scoped epistemic records; not personal state."""

    evidence_records: tuple[EvidenceRecord, ...] = ()
    claims: tuple[CapabilityClaim, ...] = ()
    evaluations: tuple[ClaimEvaluation, ...] = ()

    def __post_init__(self) -> None:
        evidence = _validated_tuple(self.evidence_records, EvidenceRecord, "evidence_records")
        claims = _validated_tuple(self.claims, CapabilityClaim, "claims")
        evaluations = _validated_tuple(self.evaluations, ClaimEvaluation, "evaluations")

        evidence = tuple(sorted(evidence, key=lambda item: item.evidence_id))
        claims = tuple(sorted(claims, key=lambda item: item.claim_id))
        evaluations = tuple(sorted(evaluations, key=lambda item: item.evaluation_id))

        _reject_duplicate_ids((item.evidence_id for item in evidence), "evidence id")
        _reject_duplicate_ids((item.claim_id for item in claims), "claim id")
        _reject_duplicate_ids((item.evaluation_id for item in evaluations), "evaluation id")

        evidence_by_id = {item.evidence_id: item for item in evidence}
        claim_by_id = {item.claim_id: item for item in claims}

        _validate_internal_provenance(evidence, claims)

        for evaluation in evaluations:
            claim = claim_by_id.get(evaluation.claim_id)
            if claim is None:
                raise InvalidRecordSetError(
                    f"evaluation references missing claim: {evaluation.claim_id}"
                )
            if evaluation.evaluated_at < claim.created_at:
                raise InvalidRecordSetError(
                    "evaluation evaluated_at must not precede claim created_at"
                )
            for assessment in evaluation.evidence_assessments:
                record = evidence_by_id.get(assessment.evidence_id)
                if record is None:
                    raise InvalidRecordSetError(
                        f"evaluation references missing evidence: {assessment.evidence_id}"
                    )
                if record.subject_ref != claim.subject_ref:
                    raise InvalidRecordSetError(
                        "evaluated evidence subject must match claim subject"
                    )
                if evaluation.evaluated_at < record.observed_at:
                    raise InvalidRecordSetError(
                        "evaluation evaluated_at must not precede assessed evidence observed_at"
                    )

        object.__setattr__(self, "evidence_records", evidence)
        object.__setattr__(self, "claims", claims)
        object.__setattr__(self, "evaluations", evaluations)

    def validate_against_catalog(self, catalog: "CapabilityCatalog") -> None:
        from capability_lab.semantics import CapabilityCatalog

        if not isinstance(catalog, CapabilityCatalog):
            raise InvalidRecordSetError("catalog must be CapabilityCatalog")
        by_id = {item.capability_id: item for item in catalog.concepts}
        for claim in self.claims:
            concept = by_id.get(claim.concept_ref.capability_id)
            if concept is None:
                raise InvalidRecordSetError(
                    f"claim references capability absent from catalog: {claim.concept_ref}"
                )
            if concept.revision != claim.concept_ref.revision:
                raise InvalidRecordSetError(
                    "catalog validation requires exact concept revision; silent latest-revision substitution is forbidden: "
                    f"claim={claim.concept_ref}, catalog={concept.ref}"
                )

    def to_dict(self) -> dict:
        from .serialization import record_set_to_dict

        return record_set_to_dict(self)

    @classmethod
    def from_dict(cls, payload: object) -> "EpistemicRecordSet":
        from .serialization import record_set_from_dict

        return record_set_from_dict(payload)

    def to_json(self) -> str:
        from .serialization import record_set_to_json

        return record_set_to_json(self)

    @classmethod
    def from_json(cls, payload: object) -> "EpistemicRecordSet":
        from .serialization import record_set_from_json

        return record_set_from_json(payload)


def _validated_tuple(value: object, item_type: type, field_name: str) -> tuple:
    if isinstance(value, (str, bytes)):
        raise InvalidRecordSetError(f"{field_name} must be an iterable")
    try:
        result = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise InvalidRecordSetError(f"{field_name} must be iterable") from exc
    if any(not isinstance(item, item_type) for item in result):
        raise InvalidRecordSetError(f"{field_name} contains invalid record type")
    return result


def _reject_duplicate_ids(values, label: str) -> None:
    seen = set()
    for value in values:
        if value in seen:
            raise InvalidRecordSetError(f"duplicate {label}: {value}")
        seen.add(value)


def _validate_internal_provenance(
    evidence: tuple[EvidenceRecord, ...],
    claims: tuple[CapabilityClaim, ...],
) -> None:
    """Validate typed internal provenance without collapsing evidence and claims."""

    evidence_by_value = {str(item.evidence_id): item for item in evidence}
    claims_by_value = {str(item.claim_id): item for item in claims}
    evidence_parents: dict[str, set[str]] = {
        key: set() for key in evidence_by_value
    }
    claim_parents: dict[str, set[str]] = {key: set() for key in claims_by_value}

    for record in evidence:
        child = str(record.evidence_id)
        internal_parent_times = []
        for step in record.provenance.steps:
            if step.occurred_at > record.recorded_at:
                raise InvalidRecordSetError(
                    "evidence provenance step must not occur after evidence recorded_at"
                )
        for source in record.provenance.sources:
            if source.kind is ProvenanceSourceKind.CLAIM:
                raise InvalidRecordSetError(
                    "evidence provenance may not depend on CapabilityClaim; "
                    "internal claims are interpretations, not source evidence"
                )
            if source.kind is not ProvenanceSourceKind.EVIDENCE_RECORD:
                continue
            parent = evidence_by_value.get(source.ref)
            if parent is None:
                raise InvalidRecordSetError(
                    f"derived evidence references missing source evidence: {source.ref}"
                )
            if source.ref == child:
                raise InvalidRecordSetError("evidence may not derive from itself")
            if parent.subject_ref != record.subject_ref:
                raise InvalidRecordSetError(
                    "derived evidence source subject must match derived evidence subject"
                )
            if parent.recorded_at > record.recorded_at:
                raise InvalidRecordSetError(
                    "derived evidence source recorded_at must not follow derived evidence recorded_at"
                )
            evidence_parents[child].add(source.ref)
            internal_parent_times.append(parent.recorded_at)
        if internal_parent_times and record.provenance.steps:
            if record.provenance.steps[0].occurred_at < max(internal_parent_times):
                raise InvalidRecordSetError(
                    "derived evidence transformation steps must not precede source evidence recorded_at"
                )

    for claim in claims:
        child = str(claim.claim_id)
        internal_parent_times = []
        for step in claim.provenance.steps:
            if step.occurred_at > claim.created_at:
                raise InvalidRecordSetError(
                    "claim provenance step must not occur after claim created_at"
                )
        for source in claim.provenance.sources:
            if source.kind is ProvenanceSourceKind.EVIDENCE_RECORD:
                raise InvalidRecordSetError(
                    "claim provenance may not bind EvidenceRecord; evaluated evidence "
                    "belongs to ClaimEvaluation, not claim identity"
                )
            if source.kind is not ProvenanceSourceKind.CLAIM:
                continue
            parent = claims_by_value.get(source.ref)
            if parent is None:
                raise InvalidRecordSetError(
                    f"claim provenance references missing source claim: {source.ref}"
                )
            if source.ref == child:
                raise InvalidRecordSetError("claim may not derive from itself")
            if parent.subject_ref != claim.subject_ref:
                raise InvalidRecordSetError(
                    "source claim subject must match derived claim subject"
                )
            if parent.created_at > claim.created_at:
                raise InvalidRecordSetError(
                    "source claim created_at must not follow derived claim created_at"
                )
            claim_parents[child].add(source.ref)
            internal_parent_times.append(parent.created_at)
        if internal_parent_times and claim.provenance.steps:
            if claim.provenance.steps[0].occurred_at < max(internal_parent_times):
                raise InvalidRecordSetError(
                    "derived claim transformation steps must not precede source claim created_at"
                )

    _assert_acyclic(evidence_parents, "derived evidence provenance")
    _assert_acyclic(claim_parents, "claim provenance")


def _assert_acyclic(parents: dict[str, set[str]], label: str) -> None:
    state: dict[str, int] = {key: 0 for key in parents}
    for start in sorted(parents):
        if state[start] != 0:
            continue
        stack: list[tuple[str, bool]] = [(start, False)]
        while stack:
            node, exiting = stack.pop()
            if exiting:
                state[node] = 2
                continue
            if state[node] == 2:
                continue
            if state[node] == 1:
                raise InvalidRecordSetError(f"{label} must be acyclic")
            state[node] = 1
            stack.append((node, True))
            for parent in sorted(parents[node], reverse=True):
                if state[parent] == 1:
                    raise InvalidRecordSetError(f"{label} must be acyclic")
                if state[parent] == 0:
                    stack.append((parent, False))
