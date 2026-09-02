"""Reviewed experimental allocation/randomization completeness governance for PR10.1 Pilot 01."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import re
import unicodedata

from . import materialization as _materialization
from . import materialization_allocation_dependence as _allocation
from . import materialization_allocation_lineage as _allocation_lineage
from . import materialization_coordination_completeness as _coordination_completeness
from . import materialization_coordination_lineage as _coordination_lineage
from . import materialization_dependence as _dependence
from . import materialization_lineage_completeness as _source_completeness
from . import materialization_mechanism_completeness as _mechanism_completeness
from . import materialization_mechanism_lineage as _mechanism_lineage
from . import materialization_source_lineage as _source_lineage
from . import materialization_temporal_completeness as _temporal_completeness
from . import materialization_temporal_lineage as _temporal_lineage


_OPAQUE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ALLOCATION_GRAPH_HASH_DOMAIN = (
    b"capability_lab/pilot_observation_allocation_lineage_graph_review_binding@1\x00"
)
_ALLOCATION_SCOPE_HASH_DOMAIN = (
    b"capability_lab/pilot_observation_allocation_origin_scope_review_binding@1\x00"
)


def _canonical_digest(domain: bytes, payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    digest = hashlib.sha256()
    digest.update(domain)
    digest.update(encoded)
    return digest.hexdigest()


def _source_payload(source) -> dict[str, str]:
    return {"kind": source.kind.value, "ref": source.ref}


def _mechanism_payload(mechanism) -> dict[str, str]:
    return {"kind": mechanism.kind.value, "ref": mechanism.ref}


def _coordination_payload(coordination) -> dict[str, str]:
    return {"kind": coordination.kind.value, "ref": coordination.ref}


def _temporal_payload(temporal) -> dict[str, str]:
    return {"kind": temporal.kind.value, "ref": temporal.ref}


def _allocation_payload(allocation) -> dict[str, str]:
    return {"kind": allocation.kind.value, "ref": allocation.ref}


def _allocation_entries_tuple(allocation_entries):
    if isinstance(allocation_entries, (str, bytes)):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "allocation_entries must be an iterable of "
            "PilotMaterializedEvidenceAllocationEntry values"
        )
    try:
        entries = tuple(allocation_entries)
    except TypeError as exc:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "allocation_entries must be iterable"
        ) from exc
    if any(
        not isinstance(item, _allocation.PilotMaterializedEvidenceAllocationEntry)
        for item in entries
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "allocation_entries must contain "
            "PilotMaterializedEvidenceAllocationEntry values"
        )
    return tuple(
        sorted(
            entries,
            key=lambda item: str(
                item.temporal_entry.coordination_entry.mechanism_entry
                .upstream_lineage_entry.basis_entry.evidence.evidence_id
            ),
        )
    )


def pilot_observation_allocation_lineage_graph_sha256_v1(
    graph: _allocation_lineage.PilotObservationAllocationLineageGraph,
) -> str:
    """Bind a completeness review to the exact canonical allocation lineage graph."""

    if not isinstance(
        graph,
        _allocation_lineage.PilotObservationAllocationLineageGraph,
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "graph must be PilotObservationAllocationLineageGraph"
        )
    payload = {
        "relations": [
            {
                "relation_kind": relation.relation_kind.value,
                "allocation": _allocation_payload(relation.allocation),
                "upstream": _allocation_payload(relation.upstream),
            }
            for relation in graph.relations
        ]
    }
    return _canonical_digest(_ALLOCATION_GRAPH_HASH_DOMAIN, payload)


def pilot_observation_allocation_origin_scope_sha256_v1(
    allocation_entries,
) -> str:
    """Bind review to the exact observation through allocation declaration basis."""

    entries = _allocation_entries_tuple(allocation_entries)
    payload = {
        "entries": [
            {
                "candidate_sha256": entry.allocation_declaration.candidate_sha256,
                "evidence_id": str(
                    entry.temporal_entry.coordination_entry.mechanism_entry
                    .upstream_lineage_entry.basis_entry.evidence.evidence_id
                ),
                "exact_capture_source": (
                    entry.temporal_entry.coordination_entry.mechanism_entry
                    .upstream_lineage_entry.basis_entry.exact_source_key
                ),
                "upstream_sources": [
                    _source_payload(source)
                    for source in (
                        entry.temporal_entry.coordination_entry.mechanism_entry
                        .upstream_lineage_entry.upstream_declaration.sources
                    )
                ],
                "mechanisms": [
                    _mechanism_payload(mechanism)
                    for mechanism in (
                        entry.temporal_entry.coordination_entry.mechanism_entry
                        .mechanism_declaration.mechanisms
                    )
                ],
                "coordinations": [
                    _coordination_payload(coordination)
                    for coordination in (
                        entry.temporal_entry.coordination_entry
                        .coordination_declaration.coordinations
                    )
                ],
                "temporals": [
                    _temporal_payload(temporal)
                    for temporal in entry.temporal_entry.temporal_declaration.temporals
                ],
                "allocations": [
                    _allocation_payload(allocation)
                    for allocation in entry.allocation_declaration.allocations
                ],
            }
            for entry in entries
        ]
    }
    return _canonical_digest(_ALLOCATION_SCOPE_HASH_DOMAIN, payload)


class PilotAllocationCompletenessStatus(str, Enum):
    """Human-reviewed completeness status for one bounded allocation scope."""

    COMPLETE_FOR_SCOPE = "COMPLETE_FOR_SCOPE"
    INCOMPLETE = "INCOMPLETE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class PilotAllocationLineageCompletenessReview:
    """Declared human review of allocation disclosure and lineage completeness.

    The record is structurally bound to the exact observation/source/mechanism/
    coordination/temporal/allocation scope and exact canonical allocation-lineage
    graph. It is not a signature, authenticated reviewer identity, proof of
    randomization, or causal/statistical independence certificate.
    """

    review_id: str
    scope_sha256: str
    graph_sha256: str
    allocation_declarations_status: PilotAllocationCompletenessStatus
    allocation_lineage_graph_status: PilotAllocationCompletenessStatus
    reviewer_ref: _materialization.PilotEvidenceMaterializationReviewerRef
    reviewed_at: datetime
    rationale: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.review_id, str)
            or _OPAQUE_ID_RE.fullmatch(self.review_id) is None
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "allocation completeness review_id must be a canonical opaque "
                "ASCII identifier"
            )
        for field_name in ("scope_sha256", "graph_sha256"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
                raise _materialization.InvalidPilotEvidenceMaterialization(
                    f"{field_name} must be a lowercase 64-character sha256 digest"
                )
        if not isinstance(
            self.allocation_declarations_status,
            PilotAllocationCompletenessStatus,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "allocation declarations status must be "
                "PilotAllocationCompletenessStatus"
            )
        if not isinstance(
            self.allocation_lineage_graph_status,
            PilotAllocationCompletenessStatus,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "allocation lineage graph status must be "
                "PilotAllocationCompletenessStatus"
            )
        if not isinstance(
            self.reviewer_ref,
            _materialization.PilotEvidenceMaterializationReviewerRef,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "allocation completeness reviewer_ref must be "
                "PilotEvidenceMaterializationReviewerRef"
            )
        if (
            self.reviewer_ref.kind
            is not _materialization.PilotEvidenceMaterializationReviewerKind.HUMAN
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "PR10.1 allocation completeness review requires an explicitly "
                "declared human reviewer"
            )
        if not isinstance(self.reviewed_at, datetime):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "allocation completeness reviewed_at must be datetime"
            )
        if self.reviewed_at.tzinfo is None or self.reviewed_at.utcoffset() is None:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "allocation completeness reviewed_at must be timezone-aware"
            )
        object.__setattr__(
            self,
            "reviewed_at",
            self.reviewed_at.astimezone(timezone.utc),
        )
        if not isinstance(self.rationale, str):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "allocation completeness rationale must be a string"
            )
        rationale = unicodedata.normalize("NFC", self.rationale).strip()
        if not rationale:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "allocation completeness rationale must be non-empty"
            )
        object.__setattr__(self, "rationale", rationale)


def build_pilot_allocation_lineage_completeness_review_v1(
    allocation_entries,
    *,
    allocation_lineage_graph: (
        _allocation_lineage.PilotObservationAllocationLineageGraph
    ),
    review_id: str,
    allocation_declarations_status: PilotAllocationCompletenessStatus,
    allocation_lineage_graph_status: PilotAllocationCompletenessStatus,
    reviewer_ref: _materialization.PilotEvidenceMaterializationReviewerRef,
    reviewed_at: datetime,
    rationale: str,
) -> PilotAllocationLineageCompletenessReview:
    """Create an exact-scope/exact-graph allocation completeness review."""

    entries = _allocation_entries_tuple(allocation_entries)
    return PilotAllocationLineageCompletenessReview(
        review_id=review_id,
        scope_sha256=pilot_observation_allocation_origin_scope_sha256_v1(entries),
        graph_sha256=pilot_observation_allocation_lineage_graph_sha256_v1(
            allocation_lineage_graph
        ),
        allocation_declarations_status=allocation_declarations_status,
        allocation_lineage_graph_status=allocation_lineage_graph_status,
        reviewer_ref=reviewer_ref,
        reviewed_at=reviewed_at,
        rationale=rationale,
    )


def validate_pilot_materialized_evidence_reviewed_allocation_origin_preconditions_v1(
    allocation_entries,
    *,
    source_lineage_graph: _source_lineage.PilotUpstreamSourceLineageGraph,
    source_completeness_review: _source_completeness.PilotUpstreamLineageCompletenessReview,
    mechanism_lineage_graph: _mechanism_lineage.PilotObservationMechanismLineageGraph,
    mechanism_completeness_review: _mechanism_completeness.PilotMechanismLineageCompletenessReview,
    coordination_lineage_graph: _coordination_lineage.PilotObservationCoordinationLineageGraph,
    coordination_completeness_review: _coordination_completeness.PilotCoordinationLineageCompletenessReview,
    temporal_lineage_graph: _temporal_lineage.PilotObservationTemporalLineageGraph,
    temporal_completeness_review: _temporal_completeness.PilotTemporalLineageCompletenessReview,
    allocation_lineage_graph: _allocation_lineage.PilotObservationAllocationLineageGraph,
    allocation_completeness_review: PilotAllocationLineageCompletenessReview,
):
    """Require reviewed allocation declaration/lineage completeness after prior gates.

    PASS remains only a bounded governance precondition. It does not establish
    independent randomization, statistical independence, or authority to claim
    independent replication.
    """

    entries = _allocation_entries_tuple(allocation_entries)
    if not isinstance(
        allocation_completeness_review,
        PilotAllocationLineageCompletenessReview,
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "allocation_completeness_review must be "
            "PilotAllocationLineageCompletenessReview"
        )

    entries = (
        _allocation_lineage.validate_pilot_materialized_evidence_allocation_ancestry_preconditions_v1(
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
        )
    )

    _dependence._validate_completeness_review_temporal_causality_v1(
        allocation_completeness_review.reviewed_at,
        (
            entry.temporal_entry.coordination_entry.mechanism_entry
            .upstream_lineage_entry.basis_entry.evidence
            for entry in entries
        ),
        family="allocation",
    )

    expected_scope_sha256 = pilot_observation_allocation_origin_scope_sha256_v1(
        entries
    )
    if allocation_completeness_review.scope_sha256 != expected_scope_sha256:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "allocation completeness review scope_sha256 does not match exact "
            "evaluated observation/source/mechanism/coordination/temporal/"
            "allocation scope"
        )

    expected_graph_sha256 = pilot_observation_allocation_lineage_graph_sha256_v1(
        allocation_lineage_graph
    )
    if allocation_completeness_review.graph_sha256 != expected_graph_sha256:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "allocation completeness review graph_sha256 does not match exact "
            "allocation-lineage graph"
        )

    if (
        allocation_completeness_review.allocation_declarations_status
        is not PilotAllocationCompletenessStatus.COMPLETE_FOR_SCOPE
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "observation allocation declarations are not reviewed "
            "COMPLETE_FOR_SCOPE; hidden experimental allocation/randomization "
            "dependence remains unresolved"
        )

    if (
        allocation_completeness_review.allocation_lineage_graph_status
        is not PilotAllocationCompletenessStatus.COMPLETE_FOR_SCOPE
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "allocation lineage graph is not reviewed COMPLETE_FOR_SCOPE; "
            "hidden common allocation/randomization origin remains unresolved"
        )

    return entries
