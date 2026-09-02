"""Reviewed source-lineage completeness governance for PR10.1 Pilot 01 evidence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import re
import unicodedata

from . import materialization as _materialization
from . import materialization_dependence as _dependence
from . import materialization_source_lineage as _source_lineage


_OPAQUE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_GRAPH_HASH_DOMAIN = (
    b"capability_lab/pilot_upstream_source_lineage_graph_review_binding@1\x00"
)
_SCOPE_HASH_DOMAIN = (
    b"capability_lab/pilot_upstream_source_origin_scope_review_binding@1\x00"
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


def _source_payload(source: _dependence.PilotUpstreamSourceRef) -> dict[str, str]:
    return {
        "kind": source.kind.value,
        "ref": source.ref,
    }


def _lineage_entries_tuple(lineage_entries):
    if isinstance(lineage_entries, (str, bytes)):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "lineage_entries must be an iterable of PilotMaterializedEvidenceUpstreamLineageEntry values"
        )
    try:
        entries = tuple(lineage_entries)
    except TypeError as exc:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "lineage_entries must be iterable"
        ) from exc
    if any(
        not isinstance(
            item,
            _dependence.PilotMaterializedEvidenceUpstreamLineageEntry,
        )
        for item in entries
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "lineage_entries must contain PilotMaterializedEvidenceUpstreamLineageEntry values"
        )
    return tuple(
        sorted(
            entries,
            key=lambda item: str(item.basis_entry.evidence.evidence_id),
        )
    )


def pilot_upstream_source_lineage_graph_sha256_v1(
    graph: _source_lineage.PilotUpstreamSourceLineageGraph,
) -> str:
    """Bind a review to the exact canonical source-lineage graph."""

    if not isinstance(graph, _source_lineage.PilotUpstreamSourceLineageGraph):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "graph must be PilotUpstreamSourceLineageGraph"
        )
    payload = {
        "relations": [
            {
                "relation_kind": relation.relation_kind.value,
                "source": _source_payload(relation.source),
                "upstream": _source_payload(relation.upstream),
            }
            for relation in graph.relations
        ]
    }
    return _canonical_digest(_GRAPH_HASH_DOMAIN, payload)


def pilot_upstream_source_origin_scope_sha256_v1(lineage_entries) -> str:
    """Bind completeness review to exact observations and source declarations."""

    entries = _lineage_entries_tuple(lineage_entries)
    payload = {
        "entries": [
            {
                "candidate_sha256": (
                    entry.upstream_declaration.candidate_sha256
                ),
                "evidence_id": str(entry.basis_entry.evidence.evidence_id),
                "exact_capture_source": entry.basis_entry.exact_source_key,
                "sources": [
                    _source_payload(source)
                    for source in entry.upstream_declaration.sources
                ],
            }
            for entry in entries
        ]
    }
    return _canonical_digest(_SCOPE_HASH_DOMAIN, payload)


class PilotLineageCompletenessStatus(str, Enum):
    """Human-reviewed completeness status for one exact bounded scope."""

    COMPLETE_FOR_SCOPE = "COMPLETE_FOR_SCOPE"
    INCOMPLETE = "INCOMPLETE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class PilotUpstreamLineageCompletenessReview:
    """Declared human review of source disclosure and graph completeness.

    This record is structurally bound to an exact observation/source-declaration
    scope and an exact canonical lineage graph. It is not a signature, authenticated
    identity, or proof that the reviewer is correct.
    """

    review_id: str
    scope_sha256: str
    graph_sha256: str
    upstream_source_declarations_status: PilotLineageCompletenessStatus
    source_lineage_graph_status: PilotLineageCompletenessStatus
    reviewer_ref: _materialization.PilotEvidenceMaterializationReviewerRef
    reviewed_at: datetime
    rationale: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.review_id, str)
            or _OPAQUE_ID_RE.fullmatch(self.review_id) is None
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "lineage completeness review_id must be a canonical opaque ASCII identifier"
            )
        for field_name in ("scope_sha256", "graph_sha256"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
                raise _materialization.InvalidPilotEvidenceMaterialization(
                    f"{field_name} must be a lowercase 64-character sha256 digest"
                )
        if not isinstance(
            self.upstream_source_declarations_status,
            PilotLineageCompletenessStatus,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "upstream source declarations status must be PilotLineageCompletenessStatus"
            )
        if not isinstance(
            self.source_lineage_graph_status,
            PilotLineageCompletenessStatus,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "source lineage graph status must be PilotLineageCompletenessStatus"
            )
        if not isinstance(
            self.reviewer_ref,
            _materialization.PilotEvidenceMaterializationReviewerRef,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "lineage completeness reviewer_ref must be PilotEvidenceMaterializationReviewerRef"
            )
        if (
            self.reviewer_ref.kind
            is not _materialization.PilotEvidenceMaterializationReviewerKind.HUMAN
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "PR10.1 lineage completeness review requires an explicitly declared human reviewer"
            )
        if not isinstance(self.reviewed_at, datetime):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "lineage completeness reviewed_at must be datetime"
            )
        if self.reviewed_at.tzinfo is None or self.reviewed_at.utcoffset() is None:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "lineage completeness reviewed_at must be timezone-aware"
            )
        object.__setattr__(
            self,
            "reviewed_at",
            self.reviewed_at.astimezone(timezone.utc),
        )
        if not isinstance(self.rationale, str):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "lineage completeness rationale must be a string"
            )
        rationale = unicodedata.normalize("NFC", self.rationale).strip()
        if not rationale:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "lineage completeness rationale must be non-empty"
            )
        object.__setattr__(self, "rationale", rationale)


def build_pilot_upstream_lineage_completeness_review_v1(
    lineage_entries,
    *,
    source_lineage_graph: _source_lineage.PilotUpstreamSourceLineageGraph,
    review_id: str,
    upstream_source_declarations_status: PilotLineageCompletenessStatus,
    source_lineage_graph_status: PilotLineageCompletenessStatus,
    reviewer_ref: _materialization.PilotEvidenceMaterializationReviewerRef,
    reviewed_at: datetime,
    rationale: str,
) -> PilotUpstreamLineageCompletenessReview:
    """Create an exact-scope/exact-graph completeness review record."""

    entries = _lineage_entries_tuple(lineage_entries)
    return PilotUpstreamLineageCompletenessReview(
        review_id=review_id,
        scope_sha256=pilot_upstream_source_origin_scope_sha256_v1(entries),
        graph_sha256=pilot_upstream_source_lineage_graph_sha256_v1(
            source_lineage_graph
        ),
        upstream_source_declarations_status=upstream_source_declarations_status,
        source_lineage_graph_status=source_lineage_graph_status,
        reviewer_ref=reviewer_ref,
        reviewed_at=reviewed_at,
        rationale=rationale,
    )


def validate_pilot_materialized_evidence_reviewed_source_origin_preconditions_v1(
    lineage_entries,
    *,
    source_lineage_graph: _source_lineage.PilotUpstreamSourceLineageGraph,
    completeness_review: PilotUpstreamLineageCompletenessReview,
):
    """Require exact reviewed completeness after all structural ancestry gates.

    A PASS means that earlier exact-source/session/elicitation/upstream/ancestry
    checks passed and a declared human review marked both observation-to-source
    disclosure and source-lineage graph coverage COMPLETE_FOR_SCOPE for the exact
    bound basis and graph. It remains a governance precondition, not statistical
    or epistemic proof of independence.
    """

    entries = _lineage_entries_tuple(lineage_entries)
    if not isinstance(
        completeness_review,
        PilotUpstreamLineageCompletenessReview,
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "completeness_review must be PilotUpstreamLineageCompletenessReview"
        )

    entries = (
        _source_lineage.validate_pilot_materialized_evidence_source_ancestry_preconditions_v1(
            entries,
            source_lineage_graph=source_lineage_graph,
        )
    )

    _dependence._validate_completeness_review_temporal_causality_v1(
        completeness_review.reviewed_at,
        (entry.basis_entry.evidence for entry in entries),
        family="source",
    )

    expected_scope_sha256 = pilot_upstream_source_origin_scope_sha256_v1(entries)
    if completeness_review.scope_sha256 != expected_scope_sha256:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "lineage completeness review scope_sha256 does not match exact evaluated observation/source-declaration scope"
        )

    expected_graph_sha256 = pilot_upstream_source_lineage_graph_sha256_v1(
        source_lineage_graph
    )
    if completeness_review.graph_sha256 != expected_graph_sha256:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "lineage completeness review graph_sha256 does not match exact source-lineage graph"
        )

    if (
        completeness_review.upstream_source_declarations_status
        is not PilotLineageCompletenessStatus.COMPLETE_FOR_SCOPE
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "upstream source declarations are not reviewed COMPLETE_FOR_SCOPE; "
            "hidden observation-to-source dependence remains unresolved"
        )

    if (
        completeness_review.source_lineage_graph_status
        is not PilotLineageCompletenessStatus.COMPLETE_FOR_SCOPE
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "source lineage graph is not reviewed COMPLETE_FOR_SCOPE; "
            "hidden common-origin dependence remains unresolved"
        )

    return entries
