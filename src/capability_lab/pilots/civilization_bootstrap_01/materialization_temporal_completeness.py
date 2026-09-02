"""Reviewed temporal/intervention/carryover completeness governance for PR10.1 Pilot 01."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import re
import unicodedata

from . import materialization as _materialization
from . import materialization_coordination_completeness as _coordination_completeness
from . import materialization_coordination_lineage as _coordination_lineage
from . import materialization_dependence as _dependence
from . import materialization_lineage_completeness as _source_completeness
from . import materialization_mechanism_completeness as _mechanism_completeness
from . import materialization_mechanism_lineage as _mechanism_lineage
from . import materialization_source_lineage as _source_lineage
from . import materialization_temporal_dependence as _temporal
from . import materialization_temporal_lineage as _temporal_lineage


_OPAQUE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_TEMPORAL_GRAPH_HASH_DOMAIN = (
    b"capability_lab/pilot_observation_temporal_lineage_graph_review_binding@1\x00"
)
_TEMPORAL_SCOPE_HASH_DOMAIN = (
    b"capability_lab/pilot_observation_temporal_origin_scope_review_binding@1\x00"
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


def _temporal_entries_tuple(temporal_entries):
    if isinstance(temporal_entries, (str, bytes)):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "temporal_entries must be an iterable of "
            "PilotMaterializedEvidenceTemporalEntry values"
        )
    try:
        entries = tuple(temporal_entries)
    except TypeError as exc:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "temporal_entries must be iterable"
        ) from exc
    if any(
        not isinstance(item, _temporal.PilotMaterializedEvidenceTemporalEntry)
        for item in entries
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "temporal_entries must contain "
            "PilotMaterializedEvidenceTemporalEntry values"
        )
    return tuple(
        sorted(
            entries,
            key=lambda item: str(
                item.coordination_entry.mechanism_entry.upstream_lineage_entry
                .basis_entry.evidence.evidence_id
            ),
        )
    )


def pilot_observation_temporal_lineage_graph_sha256_v1(
    graph: _temporal_lineage.PilotObservationTemporalLineageGraph,
) -> str:
    """Bind a completeness review to the exact canonical temporal lineage graph."""

    if not isinstance(
        graph,
        _temporal_lineage.PilotObservationTemporalLineageGraph,
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "graph must be PilotObservationTemporalLineageGraph"
        )
    payload = {
        "relations": [
            {
                "relation_kind": relation.relation_kind.value,
                "temporal": _temporal_payload(relation.temporal),
                "upstream": _temporal_payload(relation.upstream),
            }
            for relation in graph.relations
        ]
    }
    return _canonical_digest(_TEMPORAL_GRAPH_HASH_DOMAIN, payload)


def pilot_observation_temporal_origin_scope_sha256_v1(
    temporal_entries,
) -> str:
    """Bind review to the exact observation through temporal declaration basis."""

    entries = _temporal_entries_tuple(temporal_entries)
    payload = {
        "entries": [
            {
                "candidate_sha256": entry.temporal_declaration.candidate_sha256,
                "evidence_id": str(
                    entry.coordination_entry.mechanism_entry.upstream_lineage_entry
                    .basis_entry.evidence.evidence_id
                ),
                "exact_capture_source": (
                    entry.coordination_entry.mechanism_entry.upstream_lineage_entry
                    .basis_entry.exact_source_key
                ),
                "upstream_sources": [
                    _source_payload(source)
                    for source in (
                        entry.coordination_entry.mechanism_entry.upstream_lineage_entry
                        .upstream_declaration.sources
                    )
                ],
                "mechanisms": [
                    _mechanism_payload(mechanism)
                    for mechanism in (
                        entry.coordination_entry.mechanism_entry
                        .mechanism_declaration.mechanisms
                    )
                ],
                "coordinations": [
                    _coordination_payload(coordination)
                    for coordination in (
                        entry.coordination_entry.coordination_declaration.coordinations
                    )
                ],
                "temporals": [
                    _temporal_payload(temporal)
                    for temporal in entry.temporal_declaration.temporals
                ],
            }
            for entry in entries
        ]
    }
    return _canonical_digest(_TEMPORAL_SCOPE_HASH_DOMAIN, payload)


class PilotTemporalCompletenessStatus(str, Enum):
    """Human-reviewed completeness status for one bounded temporal scope."""

    COMPLETE_FOR_SCOPE = "COMPLETE_FOR_SCOPE"
    INCOMPLETE = "INCOMPLETE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class PilotTemporalLineageCompletenessReview:
    """Declared human review of temporal disclosure and lineage completeness.

    The record is bound to an exact observation/source/mechanism/coordination/
    temporal scope and exact canonical temporal-lineage graph. It is not a
    signature, authenticated reviewer identity, or causal-independence proof.
    """

    review_id: str
    scope_sha256: str
    graph_sha256: str
    temporal_declarations_status: PilotTemporalCompletenessStatus
    temporal_lineage_graph_status: PilotTemporalCompletenessStatus
    reviewer_ref: _materialization.PilotEvidenceMaterializationReviewerRef
    reviewed_at: datetime
    rationale: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.review_id, str)
            or _OPAQUE_ID_RE.fullmatch(self.review_id) is None
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "temporal completeness review_id must be a canonical opaque "
                "ASCII identifier"
            )
        for field_name in ("scope_sha256", "graph_sha256"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
                raise _materialization.InvalidPilotEvidenceMaterialization(
                    f"{field_name} must be a lowercase 64-character sha256 digest"
                )
        if not isinstance(
            self.temporal_declarations_status,
            PilotTemporalCompletenessStatus,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "temporal declarations status must be PilotTemporalCompletenessStatus"
            )
        if not isinstance(
            self.temporal_lineage_graph_status,
            PilotTemporalCompletenessStatus,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "temporal lineage graph status must be PilotTemporalCompletenessStatus"
            )
        if not isinstance(
            self.reviewer_ref,
            _materialization.PilotEvidenceMaterializationReviewerRef,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "temporal completeness reviewer_ref must be "
                "PilotEvidenceMaterializationReviewerRef"
            )
        if (
            self.reviewer_ref.kind
            is not _materialization.PilotEvidenceMaterializationReviewerKind.HUMAN
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "PR10.1 temporal completeness review requires an explicitly "
                "declared human reviewer"
            )
        if not isinstance(self.reviewed_at, datetime):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "temporal completeness reviewed_at must be datetime"
            )
        if self.reviewed_at.tzinfo is None or self.reviewed_at.utcoffset() is None:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "temporal completeness reviewed_at must be timezone-aware"
            )
        object.__setattr__(
            self,
            "reviewed_at",
            self.reviewed_at.astimezone(timezone.utc),
        )
        if not isinstance(self.rationale, str):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "temporal completeness rationale must be a string"
            )
        rationale = unicodedata.normalize("NFC", self.rationale).strip()
        if not rationale:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "temporal completeness rationale must be non-empty"
            )
        object.__setattr__(self, "rationale", rationale)


def build_pilot_temporal_lineage_completeness_review_v1(
    temporal_entries,
    *,
    temporal_lineage_graph: _temporal_lineage.PilotObservationTemporalLineageGraph,
    review_id: str,
    temporal_declarations_status: PilotTemporalCompletenessStatus,
    temporal_lineage_graph_status: PilotTemporalCompletenessStatus,
    reviewer_ref: _materialization.PilotEvidenceMaterializationReviewerRef,
    reviewed_at: datetime,
    rationale: str,
) -> PilotTemporalLineageCompletenessReview:
    """Create an exact-scope/exact-graph temporal completeness review."""

    entries = _temporal_entries_tuple(temporal_entries)
    return PilotTemporalLineageCompletenessReview(
        review_id=review_id,
        scope_sha256=pilot_observation_temporal_origin_scope_sha256_v1(entries),
        graph_sha256=pilot_observation_temporal_lineage_graph_sha256_v1(
            temporal_lineage_graph
        ),
        temporal_declarations_status=temporal_declarations_status,
        temporal_lineage_graph_status=temporal_lineage_graph_status,
        reviewer_ref=reviewer_ref,
        reviewed_at=reviewed_at,
        rationale=rationale,
    )


def validate_pilot_materialized_evidence_reviewed_temporal_origin_preconditions_v1(
    temporal_entries,
    *,
    source_lineage_graph: _source_lineage.PilotUpstreamSourceLineageGraph,
    source_completeness_review: _source_completeness.PilotUpstreamLineageCompletenessReview,
    mechanism_lineage_graph: _mechanism_lineage.PilotObservationMechanismLineageGraph,
    mechanism_completeness_review: _mechanism_completeness.PilotMechanismLineageCompletenessReview,
    coordination_lineage_graph: _coordination_lineage.PilotObservationCoordinationLineageGraph,
    coordination_completeness_review: _coordination_completeness.PilotCoordinationLineageCompletenessReview,
    temporal_lineage_graph: _temporal_lineage.PilotObservationTemporalLineageGraph,
    temporal_completeness_review: PilotTemporalLineageCompletenessReview,
):
    """Require reviewed temporal declaration/lineage completeness after prior gates.

    PASS remains only a bounded governance precondition. It does not establish
    statistical independence or authorize an independent-replication claim.
    """

    entries = _temporal_entries_tuple(temporal_entries)
    if not isinstance(
        temporal_completeness_review,
        PilotTemporalLineageCompletenessReview,
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "temporal_completeness_review must be "
            "PilotTemporalLineageCompletenessReview"
        )

    entries = (
        _temporal_lineage.validate_pilot_materialized_evidence_temporal_ancestry_preconditions_v1(
            entries,
            source_lineage_graph=source_lineage_graph,
            source_completeness_review=source_completeness_review,
            mechanism_lineage_graph=mechanism_lineage_graph,
            mechanism_completeness_review=mechanism_completeness_review,
            coordination_lineage_graph=coordination_lineage_graph,
            coordination_completeness_review=coordination_completeness_review,
            temporal_lineage_graph=temporal_lineage_graph,
        )
    )

    _dependence._validate_completeness_review_temporal_causality_v1(
        temporal_completeness_review.reviewed_at,
        (
            entry.coordination_entry.mechanism_entry.upstream_lineage_entry
            .basis_entry.evidence
            for entry in entries
        ),
        family="temporal",
    )

    expected_scope_sha256 = pilot_observation_temporal_origin_scope_sha256_v1(
        entries
    )
    if temporal_completeness_review.scope_sha256 != expected_scope_sha256:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "temporal completeness review scope_sha256 does not match exact "
            "evaluated observation/source/mechanism/coordination/temporal scope"
        )

    expected_graph_sha256 = pilot_observation_temporal_lineage_graph_sha256_v1(
        temporal_lineage_graph
    )
    if temporal_completeness_review.graph_sha256 != expected_graph_sha256:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "temporal completeness review graph_sha256 does not match exact "
            "temporal-lineage graph"
        )

    if (
        temporal_completeness_review.temporal_declarations_status
        is not PilotTemporalCompletenessStatus.COMPLETE_FOR_SCOPE
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "observation temporal declarations are not reviewed "
            "COMPLETE_FOR_SCOPE; hidden temporal/intervention/carryover "
            "dependence remains unresolved"
        )

    if (
        temporal_completeness_review.temporal_lineage_graph_status
        is not PilotTemporalCompletenessStatus.COMPLETE_FOR_SCOPE
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "temporal lineage graph is not reviewed COMPLETE_FOR_SCOPE; "
            "hidden common temporal/intervention/carryover origin remains unresolved"
        )

    return entries
