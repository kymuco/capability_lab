"""Reviewed coordination/control completeness governance for PR10.1 Pilot 01."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import re
import unicodedata

from . import materialization as _materialization
from . import materialization_coordination_dependence as _coordination
from . import materialization_coordination_lineage as _coordination_lineage
from . import materialization_dependence as _dependence
from . import materialization_lineage_completeness as _source_completeness
from . import materialization_mechanism_completeness as _mechanism_completeness
from . import materialization_mechanism_lineage as _mechanism_lineage
from . import materialization_source_lineage as _source_lineage


_OPAQUE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_COORDINATION_GRAPH_HASH_DOMAIN = (
    b"capability_lab/pilot_observation_coordination_lineage_graph_review_binding@1\x00"
)
_COORDINATION_SCOPE_HASH_DOMAIN = (
    b"capability_lab/pilot_observation_coordination_origin_scope_review_binding@1\x00"
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


def _coordination_entries_tuple(coordination_entries):
    if isinstance(coordination_entries, (str, bytes)):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "coordination_entries must be an iterable of "
            "PilotMaterializedEvidenceCoordinationEntry values"
        )
    try:
        entries = tuple(coordination_entries)
    except TypeError as exc:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "coordination_entries must be iterable"
        ) from exc
    if any(
        not isinstance(item, _coordination.PilotMaterializedEvidenceCoordinationEntry)
        for item in entries
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "coordination_entries must contain "
            "PilotMaterializedEvidenceCoordinationEntry values"
        )
    return tuple(
        sorted(
            entries,
            key=lambda item: str(
                item.mechanism_entry.upstream_lineage_entry.basis_entry.evidence.evidence_id
            ),
        )
    )


def pilot_observation_coordination_lineage_graph_sha256_v1(
    graph: _coordination_lineage.PilotObservationCoordinationLineageGraph,
) -> str:
    """Bind a completeness review to the exact canonical coordination lineage graph."""

    if not isinstance(
        graph,
        _coordination_lineage.PilotObservationCoordinationLineageGraph,
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "graph must be PilotObservationCoordinationLineageGraph"
        )
    payload = {
        "relations": [
            {
                "relation_kind": relation.relation_kind.value,
                "coordination": _coordination_payload(relation.coordination),
                "upstream": _coordination_payload(relation.upstream),
            }
            for relation in graph.relations
        ]
    }
    return _canonical_digest(_COORDINATION_GRAPH_HASH_DOMAIN, payload)


def pilot_observation_coordination_origin_scope_sha256_v1(
    coordination_entries,
) -> str:
    """Bind review to the exact observation/source/mechanism/coordination basis."""

    entries = _coordination_entries_tuple(coordination_entries)
    payload = {
        "entries": [
            {
                "candidate_sha256": (
                    entry.coordination_declaration.candidate_sha256
                ),
                "evidence_id": str(
                    entry.mechanism_entry.upstream_lineage_entry.basis_entry.evidence.evidence_id
                ),
                "exact_capture_source": (
                    entry.mechanism_entry.upstream_lineage_entry.basis_entry.exact_source_key
                ),
                "upstream_sources": [
                    _source_payload(source)
                    for source in (
                        entry.mechanism_entry.upstream_lineage_entry
                        .upstream_declaration.sources
                    )
                ],
                "mechanisms": [
                    _mechanism_payload(mechanism)
                    for mechanism in entry.mechanism_entry.mechanism_declaration.mechanisms
                ],
                "coordinations": [
                    _coordination_payload(coordination)
                    for coordination in entry.coordination_declaration.coordinations
                ],
            }
            for entry in entries
        ]
    }
    return _canonical_digest(_COORDINATION_SCOPE_HASH_DOMAIN, payload)


class PilotCoordinationCompletenessStatus(str, Enum):
    """Human-reviewed completeness status for one bounded coordination scope."""

    COMPLETE_FOR_SCOPE = "COMPLETE_FOR_SCOPE"
    INCOMPLETE = "INCOMPLETE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class PilotCoordinationLineageCompletenessReview:
    """Declared human review of coordination disclosure and lineage completeness.

    This record is structurally bound to an exact observation/source/mechanism/
    coordination scope and exact canonical coordination-lineage graph. It is not
    a signature, authenticated identity, or proof that the reviewer is correct.
    """

    review_id: str
    scope_sha256: str
    graph_sha256: str
    coordination_declarations_status: PilotCoordinationCompletenessStatus
    coordination_lineage_graph_status: PilotCoordinationCompletenessStatus
    reviewer_ref: _materialization.PilotEvidenceMaterializationReviewerRef
    reviewed_at: datetime
    rationale: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.review_id, str)
            or _OPAQUE_ID_RE.fullmatch(self.review_id) is None
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "coordination completeness review_id must be a canonical opaque "
                "ASCII identifier"
            )
        for field_name in ("scope_sha256", "graph_sha256"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
                raise _materialization.InvalidPilotEvidenceMaterialization(
                    f"{field_name} must be a lowercase 64-character sha256 digest"
                )
        if not isinstance(
            self.coordination_declarations_status,
            PilotCoordinationCompletenessStatus,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "coordination declarations status must be "
                "PilotCoordinationCompletenessStatus"
            )
        if not isinstance(
            self.coordination_lineage_graph_status,
            PilotCoordinationCompletenessStatus,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "coordination lineage graph status must be "
                "PilotCoordinationCompletenessStatus"
            )
        if not isinstance(
            self.reviewer_ref,
            _materialization.PilotEvidenceMaterializationReviewerRef,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "coordination completeness reviewer_ref must be "
                "PilotEvidenceMaterializationReviewerRef"
            )
        if (
            self.reviewer_ref.kind
            is not _materialization.PilotEvidenceMaterializationReviewerKind.HUMAN
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "PR10.1 coordination completeness review requires an explicitly "
                "declared human reviewer"
            )
        if not isinstance(self.reviewed_at, datetime):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "coordination completeness reviewed_at must be datetime"
            )
        if self.reviewed_at.tzinfo is None or self.reviewed_at.utcoffset() is None:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "coordination completeness reviewed_at must be timezone-aware"
            )
        object.__setattr__(
            self,
            "reviewed_at",
            self.reviewed_at.astimezone(timezone.utc),
        )
        if not isinstance(self.rationale, str):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "coordination completeness rationale must be a string"
            )
        rationale = unicodedata.normalize("NFC", self.rationale).strip()
        if not rationale:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "coordination completeness rationale must be non-empty"
            )
        object.__setattr__(self, "rationale", rationale)


def build_pilot_coordination_lineage_completeness_review_v1(
    coordination_entries,
    *,
    coordination_lineage_graph: (
        _coordination_lineage.PilotObservationCoordinationLineageGraph
    ),
    review_id: str,
    coordination_declarations_status: PilotCoordinationCompletenessStatus,
    coordination_lineage_graph_status: PilotCoordinationCompletenessStatus,
    reviewer_ref: _materialization.PilotEvidenceMaterializationReviewerRef,
    reviewed_at: datetime,
    rationale: str,
) -> PilotCoordinationLineageCompletenessReview:
    """Create an exact-scope/exact-graph coordination completeness review."""

    entries = _coordination_entries_tuple(coordination_entries)
    return PilotCoordinationLineageCompletenessReview(
        review_id=review_id,
        scope_sha256=pilot_observation_coordination_origin_scope_sha256_v1(entries),
        graph_sha256=pilot_observation_coordination_lineage_graph_sha256_v1(
            coordination_lineage_graph
        ),
        coordination_declarations_status=coordination_declarations_status,
        coordination_lineage_graph_status=coordination_lineage_graph_status,
        reviewer_ref=reviewer_ref,
        reviewed_at=reviewed_at,
        rationale=rationale,
    )


def validate_pilot_materialized_evidence_reviewed_coordination_origin_preconditions_v1(
    coordination_entries,
    *,
    source_lineage_graph: _source_lineage.PilotUpstreamSourceLineageGraph,
    source_completeness_review: _source_completeness.PilotUpstreamLineageCompletenessReview,
    mechanism_lineage_graph: _mechanism_lineage.PilotObservationMechanismLineageGraph,
    mechanism_completeness_review: _mechanism_completeness.PilotMechanismLineageCompletenessReview,
    coordination_lineage_graph: (
        _coordination_lineage.PilotObservationCoordinationLineageGraph
    ),
    coordination_completeness_review: PilotCoordinationLineageCompletenessReview,
):
    """Require reviewed coordination disclosure/lineage completeness after prior gates.

    PASS remains only a bounded governance precondition. It is neither proof of
    statistical independence nor authority to claim independent replication.
    """

    entries = _coordination_entries_tuple(coordination_entries)
    if not isinstance(
        coordination_completeness_review,
        PilotCoordinationLineageCompletenessReview,
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "coordination_completeness_review must be "
            "PilotCoordinationLineageCompletenessReview"
        )

    entries = (
        _coordination_lineage.validate_pilot_materialized_evidence_coordination_ancestry_preconditions_v1(
            entries,
            source_lineage_graph=source_lineage_graph,
            source_completeness_review=source_completeness_review,
            mechanism_lineage_graph=mechanism_lineage_graph,
            mechanism_completeness_review=mechanism_completeness_review,
            coordination_lineage_graph=coordination_lineage_graph,
        )
    )

    _dependence._validate_completeness_review_temporal_causality_v1(
        coordination_completeness_review.reviewed_at,
        (
            entry.mechanism_entry.upstream_lineage_entry.basis_entry.evidence
            for entry in entries
        ),
        family="coordination",
    )

    expected_scope_sha256 = pilot_observation_coordination_origin_scope_sha256_v1(
        entries
    )
    if coordination_completeness_review.scope_sha256 != expected_scope_sha256:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "coordination completeness review scope_sha256 does not match exact "
            "evaluated observation/source/mechanism/coordination scope"
        )

    expected_graph_sha256 = pilot_observation_coordination_lineage_graph_sha256_v1(
        coordination_lineage_graph
    )
    if coordination_completeness_review.graph_sha256 != expected_graph_sha256:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "coordination completeness review graph_sha256 does not match exact "
            "coordination-lineage graph"
        )

    if (
        coordination_completeness_review.coordination_declarations_status
        is not PilotCoordinationCompletenessStatus.COMPLETE_FOR_SCOPE
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "observation coordination declarations are not reviewed "
            "COMPLETE_FOR_SCOPE; hidden observation-to-control dependence remains "
            "unresolved"
        )

    if (
        coordination_completeness_review.coordination_lineage_graph_status
        is not PilotCoordinationCompletenessStatus.COMPLETE_FOR_SCOPE
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "coordination lineage graph is not reviewed COMPLETE_FOR_SCOPE; "
            "hidden common-control-origin dependence remains unresolved"
        )

    return entries
