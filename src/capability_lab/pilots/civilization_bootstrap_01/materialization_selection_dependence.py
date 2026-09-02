"""Exact sampling/selection/cohort-construction dependence governance for PR10.1 Pilot 01."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import re

from . import materialization as _materialization
from . import materialization_allocation_completeness as _allocation_completeness
from . import materialization_allocation_dependence as _allocation
from . import materialization_allocation_lineage as _allocation_lineage
from . import materialization_coordination_completeness as _coordination_completeness
from . import materialization_coordination_lineage as _coordination_lineage
from . import materialization_lineage_completeness as _source_completeness
from . import materialization_mechanism_completeness as _mechanism_completeness
from . import materialization_mechanism_lineage as _mechanism_lineage
from . import materialization_source_lineage as _source_lineage
from . import materialization_temporal_completeness as _temporal_completeness
from . import materialization_temporal_lineage as _temporal_lineage


_SELECTION_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SELECTION_DOMAIN = (
    b"capability_lab/pilot_observation_sampling_selection_dependence@1\x00"
)


class PilotObservationSelectionKind(str, Enum):
    """Explicit bounded sampling/selection/cohort-construction identities.

    Values identify exact selection-process instances or coupled selection
    units. They do not identify population labels, cohort names, sampling
    algorithms, inclusion-rule definitions, generic dataset names, or study
    families.
    """

    SAMPLING_FRAME_INSTANCE = "SAMPLING_FRAME_INSTANCE"
    SELECTION_EPISODE = "SELECTION_EPISODE"
    COHORT_CONSTRUCTION_STATE = "COHORT_CONSTRUCTION_STATE"
    RECRUITMENT_BATCH = "RECRUITMENT_BATCH"
    RESAMPLING_DRAW = "RESAMPLING_DRAW"
    INCLUSION_POLICY_EXECUTION = "INCLUSION_POLICY_EXECUTION"
    OTHER = "OTHER"


@dataclass(frozen=True, slots=True)
class PilotObservationSelectionRef:
    """One exact declared bounded sampling/selection causal identity."""

    kind: PilotObservationSelectionKind
    ref: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, PilotObservationSelectionKind):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation selection kind must be PilotObservationSelectionKind"
            )
        if (
            not isinstance(self.ref, str)
            or _SELECTION_REF_RE.fullmatch(self.ref) is None
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation selection ref must be a canonical opaque ASCII identifier"
            )


def pilot_observation_selection_dependence_key_v1(
    selection: PilotObservationSelectionRef,
) -> str:
    """Return a privacy-reducing key for one exact declared selection identity."""

    if not isinstance(selection, PilotObservationSelectionRef):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "selection must be PilotObservationSelectionRef"
        )
    canonical = json.dumps(
        {"kind": selection.kind.value, "ref": selection.ref},
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    digest = hashlib.sha256()
    digest.update(_SELECTION_DOMAIN)
    digest.update(canonical)
    return f"pilot_observation_selection:{digest.hexdigest()}"


@dataclass(frozen=True, slots=True)
class PilotMaterializationSelectionDeclaration:
    """Private exact-candidate-bound sampling/selection declaration.

    Empty means only that no selection refs were supplied. It does not assert
    absence of sampling-frame, cohort-construction, recruitment, resampling,
    inclusion-policy, or other selection-process dependence.
    """

    candidate_sha256: str
    selections: tuple[PilotObservationSelectionRef, ...] = ()

    def __post_init__(self) -> None:
        if (
            not isinstance(self.candidate_sha256, str)
            or _SHA256_RE.fullmatch(self.candidate_sha256) is None
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "selection declaration candidate_sha256 must be a lowercase "
                "64-character sha256 digest"
            )
        if not isinstance(self.selections, tuple):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "selection declaration selections must be a tuple"
            )
        if any(
            not isinstance(item, PilotObservationSelectionRef)
            for item in self.selections
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "selection declaration must contain PilotObservationSelectionRef values"
            )
        if len(set(self.selections)) != len(self.selections):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "selection declaration must not repeat an exact selection ref"
            )
        object.__setattr__(
            self,
            "selections",
            tuple(
                sorted(
                    self.selections,
                    key=lambda item: (item.kind.value, item.ref),
                )
            ),
        )


def build_pilot_materialization_selection_declaration_v1(
    candidate,
    *,
    selections: tuple[PilotObservationSelectionRef, ...] = (),
) -> PilotMaterializationSelectionDeclaration:
    """Bind explicit sampling/selection metadata to exact candidate bytes."""

    if not isinstance(
        candidate,
        _materialization.PilotEvidenceMaterializationCandidate,
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "candidate must be PilotEvidenceMaterializationCandidate"
        )
    return PilotMaterializationSelectionDeclaration(
        candidate_sha256=(
            _materialization.pilot_evidence_materialization_candidate_sha256(
                candidate
            )
        ),
        selections=selections,
    )


@dataclass(frozen=True, slots=True)
class PilotMaterializedEvidenceSelectionEntry:
    """One reviewed allocation basis plus candidate-bound selection metadata."""

    allocation_entry: _allocation.PilotMaterializedEvidenceAllocationEntry
    selection_declaration: PilotMaterializationSelectionDeclaration

    def __post_init__(self) -> None:
        if not isinstance(
            self.allocation_entry,
            _allocation.PilotMaterializedEvidenceAllocationEntry,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "selection entry allocation_entry must be "
                "PilotMaterializedEvidenceAllocationEntry"
            )
        if not isinstance(
            self.selection_declaration,
            PilotMaterializationSelectionDeclaration,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "selection entry declaration must be "
                "PilotMaterializationSelectionDeclaration"
            )
        candidate = (
            self.allocation_entry.temporal_entry.coordination_entry.mechanism_entry
            .upstream_lineage_entry.basis_entry.candidate
        )
        expected_candidate_sha256 = (
            _materialization.pilot_evidence_materialization_candidate_sha256(
                candidate
            )
        )
        if self.selection_declaration.candidate_sha256 != expected_candidate_sha256:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "selection declaration candidate_sha256 does not match exact "
                "basis candidate"
            )

    @property
    def selection_keys(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                pilot_observation_selection_dependence_key_v1(selection)
                for selection in self.selection_declaration.selections
            )
        )


def _selection_entries_tuple(selection_entries):
    if isinstance(selection_entries, (str, bytes)):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "selection_entries must be an iterable of "
            "PilotMaterializedEvidenceSelectionEntry values"
        )
    try:
        entries = tuple(selection_entries)
    except TypeError as exc:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "selection_entries must be iterable"
        ) from exc
    if any(
        not isinstance(item, PilotMaterializedEvidenceSelectionEntry)
        for item in entries
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "selection_entries must contain PilotMaterializedEvidenceSelectionEntry values"
        )
    return tuple(
        sorted(
            entries,
            key=lambda item: str(
                item.allocation_entry.temporal_entry.coordination_entry.mechanism_entry
                .upstream_lineage_entry.basis_entry.evidence.evidence_id
            ),
        )
    )


def validate_pilot_materialized_evidence_shared_selection_preconditions_v1(
    selection_entries,
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
    allocation_completeness_review: _allocation_completeness.PilotAllocationLineageCompletenessReview,
):
    """Reject exact shared sampling/selection/cohort-construction identities.

    The full reviewed source/mechanism/coordination/temporal/allocation ladder
    is required first. PASS means only that no exact declared selection identity
    is shared across observations. Distinct refs, empty declarations, equal
    cohort labels, equal sampling algorithms, or equal inclusion-rule
    definitions are not certificates of independent sampling or replication.
    """

    entries = _selection_entries_tuple(selection_entries)

    reviewed_allocation_entries = (
        _allocation_completeness.validate_pilot_materialized_evidence_reviewed_allocation_origin_preconditions_v1(
            (item.allocation_entry for item in entries),
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
        )
    )
    if tuple(item.allocation_entry for item in entries) != reviewed_allocation_entries:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "selection entries do not match reviewed allocation-origin basis ordering"
        )

    seen_selection: dict[str, object] = {}
    for entry in entries:
        evidence_id = (
            entry.allocation_entry.temporal_entry.coordination_entry.mechanism_entry
            .upstream_lineage_entry.basis_entry.evidence.evidence_id
        )
        for key in entry.selection_keys:
            previous = seen_selection.get(key)
            if previous is not None:
                raise _materialization.InvalidPilotEvidenceMaterialization(
                    "distinct materialized Pilot observations share one exact "
                    "declared sampling/selection/cohort-construction causal identity; "
                    "known shared selection state cannot satisfy PR10.1 "
                    "shared-selection independence preconditions: "
                    f"selection={key}, first={previous}, second={evidence_id}"
                )
            seen_selection[key] = evidence_id

    return entries
