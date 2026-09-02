"""Reviewed observation-mechanism completeness governance for PR10.1 Pilot 01."""

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
from . import materialization_mechanism_dependence as _mechanism
from . import materialization_mechanism_lineage as _mechanism_lineage
from . import materialization_source_lineage as _source_lineage
from . import materialization_lineage_completeness as _source_completeness


_OPAQUE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_MECHANISM_GRAPH_HASH_DOMAIN = (
    b"capability_lab/pilot_observation_mechanism_lineage_graph_review_binding@1\x00"
)
_MECHANISM_SCOPE_HASH_DOMAIN = (
    b"capability_lab/pilot_observation_mechanism_origin_scope_review_binding@1\x00"
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


def _mechanism_payload(
    mechanism: _mechanism.PilotObservationMechanismRef,
) -> dict[str, str]:
    return {
        "kind": mechanism.kind.value,
        "ref": mechanism.ref,
    }


def _source_payload(source) -> dict[str, str]:
    return {
        "kind": source.kind.value,
        "ref": source.ref,
    }


def _mechanism_entries_tuple(mechanism_entries):
    if isinstance(mechanism_entries, (str, bytes)):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "mechanism_entries must be an iterable of PilotMaterializedEvidenceMechanismEntry values"
        )
    try:
        entries = tuple(mechanism_entries)
    except TypeError as exc:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "mechanism_entries must be iterable"
        ) from exc
    if any(
        not isinstance(item, _mechanism.PilotMaterializedEvidenceMechanismEntry)
        for item in entries
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "mechanism_entries must contain PilotMaterializedEvidenceMechanismEntry values"
        )
    return tuple(
        sorted(
            entries,
            key=lambda item: str(
                item.upstream_lineage_entry.basis_entry.evidence.evidence_id
            ),
        )
    )


def pilot_observation_mechanism_lineage_graph_sha256_v1(
    graph: _mechanism_lineage.PilotObservationMechanismLineageGraph,
) -> str:
    """Bind a completeness review to the exact canonical mechanism-lineage graph."""

    if not isinstance(
        graph,
        _mechanism_lineage.PilotObservationMechanismLineageGraph,
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "graph must be PilotObservationMechanismLineageGraph"
        )
    payload = {
        "relations": [
            {
                "relation_kind": relation.relation_kind.value,
                "mechanism": _mechanism_payload(relation.mechanism),
                "upstream": _mechanism_payload(relation.upstream),
            }
            for relation in graph.relations
        ]
    }
    return _canonical_digest(_MECHANISM_GRAPH_HASH_DOMAIN, payload)


def pilot_observation_mechanism_origin_scope_sha256_v1(
    mechanism_entries,
) -> str:
    """Bind mechanism completeness review to exact observation/source/mechanism scope."""

    entries = _mechanism_entries_tuple(mechanism_entries)
    payload = {
        "entries": [
            {
                "candidate_sha256": entry.mechanism_declaration.candidate_sha256,
                "evidence_id": str(
                    entry.upstream_lineage_entry.basis_entry.evidence.evidence_id
                ),
                "exact_capture_source": (
                    entry.upstream_lineage_entry.basis_entry.exact_source_key
                ),
                "upstream_sources": [
                    _source_payload(source)
                    for source in entry.upstream_lineage_entry.upstream_declaration.sources
                ],
                "mechanisms": [
                    _mechanism_payload(mechanism)
                    for mechanism in entry.mechanism_declaration.mechanisms
                ],
            }
            for entry in entries
        ]
    }
    return _canonical_digest(_MECHANISM_SCOPE_HASH_DOMAIN, payload)


class PilotMechanismCompletenessStatus(str, Enum):
    """Human-reviewed completeness status for one exact mechanism scope."""

    COMPLETE_FOR_SCOPE = "COMPLETE_FOR_SCOPE"
    INCOMPLETE = "INCOMPLETE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class PilotMechanismLineageCompletenessReview:
    """Declared human review of mechanism disclosure and lineage completeness.

    The record is bound to exact observation/source/mechanism scope and exact
    canonical mechanism-lineage graph. It is not a signature, authenticated
    identity, or proof that the reviewer is correct.
    """

    review_id: str
    scope_sha256: str
    graph_sha256: str
    mechanism_declarations_status: PilotMechanismCompletenessStatus
    mechanism_lineage_graph_status: PilotMechanismCompletenessStatus
    reviewer_ref: _materialization.PilotEvidenceMaterializationReviewerRef
    reviewed_at: datetime
    rationale: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.review_id, str)
            or _OPAQUE_ID_RE.fullmatch(self.review_id) is None
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "mechanism completeness review_id must be a canonical opaque ASCII identifier"
            )
        for field_name in ("scope_sha256", "graph_sha256"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
                raise _materialization.InvalidPilotEvidenceMaterialization(
                    f"{field_name} must be a lowercase 64-character sha256 digest"
                )
        if not isinstance(
            self.mechanism_declarations_status,
            PilotMechanismCompletenessStatus,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "mechanism declarations status must be PilotMechanismCompletenessStatus"
            )
        if not isinstance(
            self.mechanism_lineage_graph_status,
            PilotMechanismCompletenessStatus,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "mechanism lineage graph status must be PilotMechanismCompletenessStatus"
            )
        if not isinstance(
            self.reviewer_ref,
            _materialization.PilotEvidenceMaterializationReviewerRef,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "mechanism completeness reviewer_ref must be PilotEvidenceMaterializationReviewerRef"
            )
        if (
            self.reviewer_ref.kind
            is not _materialization.PilotEvidenceMaterializationReviewerKind.HUMAN
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "PR10.1 mechanism completeness review requires an explicitly declared human reviewer"
            )
        if not isinstance(self.reviewed_at, datetime):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "mechanism completeness reviewed_at must be datetime"
            )
        if self.reviewed_at.tzinfo is None or self.reviewed_at.utcoffset() is None:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "mechanism completeness reviewed_at must be timezone-aware"
            )
        object.__setattr__(
            self,
            "reviewed_at",
            self.reviewed_at.astimezone(timezone.utc),
        )
        if not isinstance(self.rationale, str):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "mechanism completeness rationale must be a string"
            )
        rationale = unicodedata.normalize("NFC", self.rationale).strip()
        if not rationale:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "mechanism completeness rationale must be non-empty"
            )
        object.__setattr__(self, "rationale", rationale)


def build_pilot_mechanism_lineage_completeness_review_v1(
    mechanism_entries,
    *,
    mechanism_lineage_graph: _mechanism_lineage.PilotObservationMechanismLineageGraph,
    review_id: str,
    mechanism_declarations_status: PilotMechanismCompletenessStatus,
    mechanism_lineage_graph_status: PilotMechanismCompletenessStatus,
    reviewer_ref: _materialization.PilotEvidenceMaterializationReviewerRef,
    reviewed_at: datetime,
    rationale: str,
) -> PilotMechanismLineageCompletenessReview:
    """Create an exact-scope/exact-graph mechanism completeness review."""

    entries = _mechanism_entries_tuple(mechanism_entries)
    return PilotMechanismLineageCompletenessReview(
        review_id=review_id,
        scope_sha256=pilot_observation_mechanism_origin_scope_sha256_v1(entries),
        graph_sha256=pilot_observation_mechanism_lineage_graph_sha256_v1(
            mechanism_lineage_graph
        ),
        mechanism_declarations_status=mechanism_declarations_status,
        mechanism_lineage_graph_status=mechanism_lineage_graph_status,
        reviewer_ref=reviewer_ref,
        reviewed_at=reviewed_at,
        rationale=rationale,
    )


def validate_pilot_materialized_evidence_reviewed_mechanism_origin_preconditions_v1(
    mechanism_entries,
    *,
    source_lineage_graph: _source_lineage.PilotUpstreamSourceLineageGraph,
    source_completeness_review: _source_completeness.PilotUpstreamLineageCompletenessReview,
    mechanism_lineage_graph: _mechanism_lineage.PilotObservationMechanismLineageGraph,
    mechanism_completeness_review: PilotMechanismLineageCompletenessReview,
):
    """Require reviewed mechanism disclosure/lineage completeness after prior gates.

    A PASS means the full source-origin and mechanism structural gates passed and
    a declared human review marked both exact observation-to-mechanism disclosure
    and mechanism-lineage graph coverage COMPLETE_FOR_SCOPE for the bound scope.
    It remains a governance precondition, not proof of statistical independence
    or authority to claim independent replication.
    """

    entries = _mechanism_entries_tuple(mechanism_entries)
    if not isinstance(
        mechanism_completeness_review,
        PilotMechanismLineageCompletenessReview,
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "mechanism_completeness_review must be PilotMechanismLineageCompletenessReview"
        )

    entries = (
        _mechanism_lineage.validate_pilot_materialized_evidence_mechanism_ancestry_preconditions_v1(
            entries,
            source_lineage_graph=source_lineage_graph,
            completeness_review=source_completeness_review,
            mechanism_lineage_graph=mechanism_lineage_graph,
        )
    )

    _dependence._validate_completeness_review_temporal_causality_v1(
        mechanism_completeness_review.reviewed_at,
        (
            entry.upstream_lineage_entry.basis_entry.evidence
            for entry in entries
        ),
        family="mechanism",
    )

    expected_scope_sha256 = (
        pilot_observation_mechanism_origin_scope_sha256_v1(entries)
    )
    if mechanism_completeness_review.scope_sha256 != expected_scope_sha256:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "mechanism completeness review scope_sha256 does not match exact evaluated observation/source/mechanism scope"
        )

    expected_graph_sha256 = (
        pilot_observation_mechanism_lineage_graph_sha256_v1(
            mechanism_lineage_graph
        )
    )
    if mechanism_completeness_review.graph_sha256 != expected_graph_sha256:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "mechanism completeness review graph_sha256 does not match exact mechanism-lineage graph"
        )

    if (
        mechanism_completeness_review.mechanism_declarations_status
        is not PilotMechanismCompletenessStatus.COMPLETE_FOR_SCOPE
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "observation mechanism declarations are not reviewed COMPLETE_FOR_SCOPE; "
            "hidden observation-to-mechanism dependence remains unresolved"
        )

    if (
        mechanism_completeness_review.mechanism_lineage_graph_status
        is not PilotMechanismCompletenessStatus.COMPLETE_FOR_SCOPE
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "mechanism lineage graph is not reviewed COMPLETE_FOR_SCOPE; "
            "hidden common-mechanism-origin dependence remains unresolved"
        )

    return entries
