"""Reviewed selection-origin completeness governance for PR10.1 Pilot 01."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import re
import unicodedata

from . import materialization as _m
from . import materialization_dependence as _dependence
from . import materialization_selection_dependence as _selection
from . import materialization_selection_lineage as _lineage

_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_SHA_RE = re.compile(r"^[0-9a-f]{64}$")
_GRAPH_DOMAIN = b"capability_lab/pilot_observation_selection_lineage_graph_review_binding@1\x00"
_SCOPE_DOMAIN = b"capability_lab/pilot_observation_selection_origin_scope_review_binding@1\x00"


def _digest(domain: bytes, payload: object) -> str:
    encoded = json.dumps(
        payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(domain + encoded).hexdigest()


def _ref_payload(value) -> dict[str, str]:
    return {"kind": value.kind.value, "ref": value.ref}


def _entries_tuple(values):
    if isinstance(values, (str, bytes)):
        raise _m.InvalidPilotEvidenceMaterialization(
            "selection_entries must be an iterable of PilotMaterializedEvidenceSelectionEntry values"
        )
    try:
        entries = tuple(values)
    except TypeError as exc:
        raise _m.InvalidPilotEvidenceMaterialization(
            "selection_entries must be iterable"
        ) from exc
    if any(not isinstance(item, _selection.PilotMaterializedEvidenceSelectionEntry) for item in entries):
        raise _m.InvalidPilotEvidenceMaterialization(
            "selection_entries must contain PilotMaterializedEvidenceSelectionEntry values"
        )
    return tuple(sorted(entries, key=lambda item: str(
        item.allocation_entry.temporal_entry.coordination_entry.mechanism_entry
        .upstream_lineage_entry.basis_entry.evidence.evidence_id
    )))


def pilot_observation_selection_lineage_graph_sha256_v1(graph) -> str:
    if not isinstance(graph, _lineage.PilotObservationSelectionLineageGraph):
        raise _m.InvalidPilotEvidenceMaterialization(
            "graph must be PilotObservationSelectionLineageGraph"
        )
    return _digest(_GRAPH_DOMAIN, {"relations": [
        {
            "relation_kind": rel.relation_kind.value,
            "selection": _ref_payload(rel.selection),
            "upstream": _ref_payload(rel.upstream),
        }
        for rel in graph.relations
    ]})


def pilot_observation_selection_origin_scope_sha256_v1(selection_entries) -> str:
    entries = _entries_tuple(selection_entries)
    payload = {"entries": []}
    for entry in entries:
        allocation = entry.allocation_entry
        temporal = allocation.temporal_entry
        coordination = temporal.coordination_entry
        mechanism = coordination.mechanism_entry
        upstream = mechanism.upstream_lineage_entry
        basis = upstream.basis_entry
        payload["entries"].append({
            "candidate_sha256": entry.selection_declaration.candidate_sha256,
            "evidence_id": str(basis.evidence.evidence_id),
            "exact_capture_source": basis.exact_source_key,
            "upstream_sources": [_ref_payload(x) for x in upstream.upstream_declaration.sources],
            "mechanisms": [_ref_payload(x) for x in mechanism.mechanism_declaration.mechanisms],
            "coordinations": [_ref_payload(x) for x in coordination.coordination_declaration.coordinations],
            "temporals": [_ref_payload(x) for x in temporal.temporal_declaration.temporals],
            "allocations": [_ref_payload(x) for x in allocation.allocation_declaration.allocations],
            "selections": [_ref_payload(x) for x in entry.selection_declaration.selections],
        })
    return _digest(_SCOPE_DOMAIN, payload)


class PilotSelectionCompletenessStatus(str, Enum):
    COMPLETE_FOR_SCOPE = "COMPLETE_FOR_SCOPE"
    INCOMPLETE = "INCOMPLETE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class PilotSelectionLineageCompletenessReview:
    review_id: str
    scope_sha256: str
    graph_sha256: str
    selection_declarations_status: PilotSelectionCompletenessStatus
    selection_lineage_graph_status: PilotSelectionCompletenessStatus
    reviewer_ref: _m.PilotEvidenceMaterializationReviewerRef
    reviewed_at: datetime
    rationale: str

    def __post_init__(self) -> None:
        if not isinstance(self.review_id, str) or _ID_RE.fullmatch(self.review_id) is None:
            raise _m.InvalidPilotEvidenceMaterialization(
                "selection completeness review_id must be a canonical opaque ASCII identifier"
            )
        for name in ("scope_sha256", "graph_sha256"):
            value = getattr(self, name)
            if not isinstance(value, str) or _SHA_RE.fullmatch(value) is None:
                raise _m.InvalidPilotEvidenceMaterialization(
                    f"{name} must be a lowercase 64-character sha256 digest"
                )
        if not isinstance(self.selection_declarations_status, PilotSelectionCompletenessStatus):
            raise _m.InvalidPilotEvidenceMaterialization(
                "selection declarations status must be PilotSelectionCompletenessStatus"
            )
        if not isinstance(self.selection_lineage_graph_status, PilotSelectionCompletenessStatus):
            raise _m.InvalidPilotEvidenceMaterialization(
                "selection lineage graph status must be PilotSelectionCompletenessStatus"
            )
        if not isinstance(self.reviewer_ref, _m.PilotEvidenceMaterializationReviewerRef):
            raise _m.InvalidPilotEvidenceMaterialization(
                "selection completeness reviewer_ref must be PilotEvidenceMaterializationReviewerRef"
            )
        if self.reviewer_ref.kind is not _m.PilotEvidenceMaterializationReviewerKind.HUMAN:
            raise _m.InvalidPilotEvidenceMaterialization(
                "PR10.1 selection completeness review requires an explicitly declared human reviewer"
            )
        if not isinstance(self.reviewed_at, datetime):
            raise _m.InvalidPilotEvidenceMaterialization(
                "selection completeness reviewed_at must be datetime"
            )
        if self.reviewed_at.tzinfo is None or self.reviewed_at.utcoffset() is None:
            raise _m.InvalidPilotEvidenceMaterialization(
                "selection completeness reviewed_at must be timezone-aware"
            )
        object.__setattr__(self, "reviewed_at", self.reviewed_at.astimezone(timezone.utc))
        if not isinstance(self.rationale, str):
            raise _m.InvalidPilotEvidenceMaterialization(
                "selection completeness rationale must be a string"
            )
        rationale = unicodedata.normalize("NFC", self.rationale).strip()
        if not rationale:
            raise _m.InvalidPilotEvidenceMaterialization(
                "selection completeness rationale must be non-empty"
            )
        object.__setattr__(self, "rationale", rationale)


def build_pilot_selection_lineage_completeness_review_v1(
    selection_entries,
    *,
    selection_lineage_graph,
    review_id,
    selection_declarations_status,
    selection_lineage_graph_status,
    reviewer_ref,
    reviewed_at,
    rationale,
):
    entries = _entries_tuple(selection_entries)
    return PilotSelectionLineageCompletenessReview(
        review_id=review_id,
        scope_sha256=pilot_observation_selection_origin_scope_sha256_v1(entries),
        graph_sha256=pilot_observation_selection_lineage_graph_sha256_v1(selection_lineage_graph),
        selection_declarations_status=selection_declarations_status,
        selection_lineage_graph_status=selection_lineage_graph_status,
        reviewer_ref=reviewer_ref,
        reviewed_at=reviewed_at,
        rationale=rationale,
    )


def validate_pilot_materialized_evidence_reviewed_selection_origin_preconditions_v1(
    selection_entries,
    *,
    source_lineage_graph,
    source_completeness_review,
    mechanism_lineage_graph,
    mechanism_completeness_review,
    coordination_lineage_graph,
    coordination_completeness_review,
    temporal_lineage_graph,
    temporal_completeness_review,
    allocation_lineage_graph,
    allocation_completeness_review,
    selection_lineage_graph,
    selection_completeness_review,
):
    entries = _entries_tuple(selection_entries)
    if not isinstance(selection_completeness_review, PilotSelectionLineageCompletenessReview):
        raise _m.InvalidPilotEvidenceMaterialization(
            "selection_completeness_review must be PilotSelectionLineageCompletenessReview"
        )

    entries = _lineage.validate_pilot_materialized_evidence_selection_ancestry_preconditions_v1(
        entries,
        source_lineage_graph=source_lineage_graph,
        source_completeness_review=source_completeness_review,
        mechanism_lineage_graph=mechanism_lineage_graph,
        mechanism_completeness_review=mechanism_completeness_review,
        coordination_lineage_graph=coordination_lineage_graph,
        coordination_completeness_review=coordination_completeness_review,
        temporal_lineage_graph=temporal_lineage_graph,
        temporal_completeness_review=temporal_completeness_review,
        allocation_lineage_graph=allocation_lineage_graph,
        allocation_completeness_review=allocation_completeness_review,
        selection_lineage_graph=selection_lineage_graph,
    )

    _dependence._validate_completeness_review_temporal_causality_v1(
        selection_completeness_review.reviewed_at,
        (
            entry.allocation_entry.temporal_entry.coordination_entry.mechanism_entry
            .upstream_lineage_entry.basis_entry.evidence
            for entry in entries
        ),
        family="selection",
    )

    if selection_completeness_review.scope_sha256 != pilot_observation_selection_origin_scope_sha256_v1(entries):
        raise _m.InvalidPilotEvidenceMaterialization(
            "selection completeness review scope_sha256 does not match exact evaluated "
            "observation/source/mechanism/coordination/temporal/allocation/selection scope"
        )
    if selection_completeness_review.graph_sha256 != pilot_observation_selection_lineage_graph_sha256_v1(selection_lineage_graph):
        raise _m.InvalidPilotEvidenceMaterialization(
            "selection completeness review graph_sha256 does not match exact selection-lineage graph"
        )
    if selection_completeness_review.selection_declarations_status is not PilotSelectionCompletenessStatus.COMPLETE_FOR_SCOPE:
        raise _m.InvalidPilotEvidenceMaterialization(
            "observation selection declarations are not reviewed COMPLETE_FOR_SCOPE; "
            "hidden sampling/selection/cohort-construction dependence remains unresolved"
        )
    if selection_completeness_review.selection_lineage_graph_status is not PilotSelectionCompletenessStatus.COMPLETE_FOR_SCOPE:
        raise _m.InvalidPilotEvidenceMaterialization(
            "selection lineage graph is not reviewed COMPLETE_FOR_SCOPE; hidden common "
            "sampling/selection/cohort-construction origin remains unresolved"
        )
    return entries
