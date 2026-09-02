"""Exact experimental allocation/assignment dependence governance for PR10.1 Pilot 01."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import re

from . import materialization as _materialization
from . import materialization_coordination_completeness as _coordination_completeness
from . import materialization_coordination_lineage as _coordination_lineage
from . import materialization_lineage_completeness as _source_completeness
from . import materialization_mechanism_completeness as _mechanism_completeness
from . import materialization_mechanism_lineage as _mechanism_lineage
from . import materialization_source_lineage as _source_lineage
from . import materialization_temporal_completeness as _temporal_completeness
from . import materialization_temporal_dependence as _temporal
from . import materialization_temporal_lineage as _temporal_lineage


_ALLOCATION_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ALLOCATION_DOMAIN = (
    b"capability_lab/pilot_observation_experimental_allocation_dependence@1\x00"
)


class PilotObservationAllocationKind(str, Enum):
    """Explicit bounded experimental allocation/assignment causal identities.

    These values identify exact allocation instances or coupled design units.
    They do not identify treatment labels, arm names, allocation algorithms,
    nominal probabilities, or generic experimental-design families.
    """

    ALLOCATION_BLOCK = "ALLOCATION_BLOCK"
    ASSIGNMENT_EPISODE = "ASSIGNMENT_EPISODE"
    RANDOMIZATION_STATE = "RANDOMIZATION_STATE"
    ADAPTIVE_ALLOCATION_STATE = "ADAPTIVE_ALLOCATION_STATE"
    CLUSTER_ASSIGNMENT_UNIT = "CLUSTER_ASSIGNMENT_UNIT"
    MATCHED_ALLOCATION_SET = "MATCHED_ALLOCATION_SET"
    OTHER = "OTHER"


@dataclass(frozen=True, slots=True)
class PilotObservationAllocationRef:
    """One exact declared bounded allocation/assignment causal identity."""

    kind: PilotObservationAllocationKind
    ref: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, PilotObservationAllocationKind):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation allocation kind must be PilotObservationAllocationKind"
            )
        if (
            not isinstance(self.ref, str)
            or _ALLOCATION_REF_RE.fullmatch(self.ref) is None
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation allocation ref must be a canonical opaque ASCII identifier"
            )


def pilot_observation_allocation_dependence_key_v1(
    allocation: PilotObservationAllocationRef,
) -> str:
    """Return a privacy-reducing key for one exact declared allocation identity."""

    if not isinstance(allocation, PilotObservationAllocationRef):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "allocation must be PilotObservationAllocationRef"
        )
    canonical = json.dumps(
        {"kind": allocation.kind.value, "ref": allocation.ref},
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    digest = hashlib.sha256()
    digest.update(_ALLOCATION_DOMAIN)
    digest.update(canonical)
    return f"pilot_observation_allocation:{digest.hexdigest()}"


@dataclass(frozen=True, slots=True)
class PilotMaterializationAllocationDeclaration:
    """Private exact-candidate-bound allocation/assignment declaration.

    Empty means only that no allocation refs were supplied. It does not assert
    absence of randomization-block, assignment-episode, adaptive-allocation,
    cluster-assignment, matched-set, or other experimental-design dependence.
    """

    candidate_sha256: str
    allocations: tuple[PilotObservationAllocationRef, ...] = ()

    def __post_init__(self) -> None:
        if (
            not isinstance(self.candidate_sha256, str)
            or _SHA256_RE.fullmatch(self.candidate_sha256) is None
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "allocation declaration candidate_sha256 must be a lowercase "
                "64-character sha256 digest"
            )
        if not isinstance(self.allocations, tuple):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "allocation declaration allocations must be a tuple"
            )
        if any(
            not isinstance(item, PilotObservationAllocationRef)
            for item in self.allocations
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "allocation declaration must contain "
                "PilotObservationAllocationRef values"
            )
        if len(set(self.allocations)) != len(self.allocations):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "allocation declaration must not repeat an exact allocation ref"
            )
        object.__setattr__(
            self,
            "allocations",
            tuple(
                sorted(
                    self.allocations,
                    key=lambda item: (item.kind.value, item.ref),
                )
            ),
        )


def build_pilot_materialization_allocation_declaration_v1(
    candidate,
    *,
    allocations: tuple[PilotObservationAllocationRef, ...] = (),
) -> PilotMaterializationAllocationDeclaration:
    """Bind explicit experimental allocation metadata to exact candidate bytes."""

    if not isinstance(
        candidate,
        _materialization.PilotEvidenceMaterializationCandidate,
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "candidate must be PilotEvidenceMaterializationCandidate"
        )
    return PilotMaterializationAllocationDeclaration(
        candidate_sha256=(
            _materialization.pilot_evidence_materialization_candidate_sha256(
                candidate
            )
        ),
        allocations=allocations,
    )


@dataclass(frozen=True, slots=True)
class PilotMaterializedEvidenceAllocationEntry:
    """One reviewed temporal basis plus candidate-bound allocation metadata."""

    temporal_entry: _temporal.PilotMaterializedEvidenceTemporalEntry
    allocation_declaration: PilotMaterializationAllocationDeclaration

    def __post_init__(self) -> None:
        if not isinstance(
            self.temporal_entry,
            _temporal.PilotMaterializedEvidenceTemporalEntry,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "allocation entry temporal_entry must be "
                "PilotMaterializedEvidenceTemporalEntry"
            )
        if not isinstance(
            self.allocation_declaration,
            PilotMaterializationAllocationDeclaration,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "allocation entry declaration must be "
                "PilotMaterializationAllocationDeclaration"
            )
        candidate = (
            self.temporal_entry.coordination_entry.mechanism_entry
            .upstream_lineage_entry.basis_entry.candidate
        )
        expected_candidate_sha256 = (
            _materialization.pilot_evidence_materialization_candidate_sha256(
                candidate
            )
        )
        if (
            self.allocation_declaration.candidate_sha256
            != expected_candidate_sha256
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "allocation declaration candidate_sha256 does not match exact "
                "basis candidate"
            )

    @property
    def allocation_keys(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                pilot_observation_allocation_dependence_key_v1(allocation)
                for allocation in self.allocation_declaration.allocations
            )
        )


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
        not isinstance(item, PilotMaterializedEvidenceAllocationEntry)
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


def validate_pilot_materialized_evidence_shared_allocation_preconditions_v1(
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
):
    """Reject exact shared experimental allocation/assignment causal identities.

    The full reviewed source/mechanism/coordination/temporal ladder is required
    first. PASS means only that no exact declared allocation identity is shared
    across observations. Distinct refs, empty declarations, equal arm labels,
    equal nominal probabilities, or equal allocation algorithms are not
    certificates of independent randomization or independent replication.
    """

    entries = _allocation_entries_tuple(allocation_entries)

    reviewed_temporal_entries = (
        _temporal_completeness.validate_pilot_materialized_evidence_reviewed_temporal_origin_preconditions_v1(
            (item.temporal_entry for item in entries),
            source_lineage_graph=source_lineage_graph,
            source_completeness_review=source_completeness_review,
            mechanism_lineage_graph=mechanism_lineage_graph,
            mechanism_completeness_review=mechanism_completeness_review,
            coordination_lineage_graph=coordination_lineage_graph,
            coordination_completeness_review=coordination_completeness_review,
            temporal_lineage_graph=temporal_lineage_graph,
            temporal_completeness_review=temporal_completeness_review,
        )
    )
    if tuple(item.temporal_entry for item in entries) != reviewed_temporal_entries:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "allocation entries do not match reviewed temporal-origin basis ordering"
        )

    seen_allocation: dict[str, object] = {}
    for entry in entries:
        evidence_id = (
            entry.temporal_entry.coordination_entry.mechanism_entry
            .upstream_lineage_entry.basis_entry.evidence.evidence_id
        )
        for key in entry.allocation_keys:
            previous = seen_allocation.get(key)
            if previous is not None:
                raise _materialization.InvalidPilotEvidenceMaterialization(
                    "distinct materialized Pilot observations share one exact "
                    "declared experimental allocation/assignment causal identity; "
                    "known shared allocation state cannot satisfy PR10.1 "
                    "shared-allocation independence preconditions: "
                    f"allocation={key}, first={previous}, second={evidence_id}"
                )
            seen_allocation[key] = evidence_id

    return entries
