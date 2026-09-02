"""Explicit temporal/intervention/carryover dependence governance for PR10.1 Pilot 01."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import re

from . import materialization as _materialization
from . import materialization_coordination_completeness as _coordination_completeness
from . import materialization_coordination_dependence as _coordination
from . import materialization_coordination_lineage as _coordination_lineage
from . import materialization_lineage_completeness as _source_completeness
from . import materialization_mechanism_completeness as _mechanism_completeness
from . import materialization_mechanism_lineage as _mechanism_lineage
from . import materialization_source_lineage as _source_lineage


_TEMPORAL_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_TEMPORAL_DOMAIN = (
    b"capability_lab/pilot_observation_temporal_intervention_dependence@1\x00"
)


class PilotObservationTemporalKind(str, Enum):
    """Explicit bounded temporal/intervention causal-context categories."""

    INTERVENTION_EPISODE = "INTERVENTION_EPISODE"
    ADAPTIVE_STATE = "ADAPTIVE_STATE"
    CARRYOVER_STATE = "CARRYOVER_STATE"
    EXPOSURE_EPISODE = "EXPOSURE_EPISODE"
    HISTORY_STATE = "HISTORY_STATE"
    OTHER = "OTHER"


@dataclass(frozen=True, slots=True)
class PilotObservationTemporalRef:
    """One exact declared bounded temporal/intervention causal identity."""

    kind: PilotObservationTemporalKind
    ref: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, PilotObservationTemporalKind):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation temporal kind must be PilotObservationTemporalKind"
            )
        if (
            not isinstance(self.ref, str)
            or _TEMPORAL_REF_RE.fullmatch(self.ref) is None
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation temporal ref must be a canonical opaque ASCII identifier"
            )


def pilot_observation_temporal_dependence_key_v1(
    temporal: PilotObservationTemporalRef,
) -> str:
    """Return a privacy-reducing key for one exact declared temporal identity."""

    if not isinstance(temporal, PilotObservationTemporalRef):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "temporal must be PilotObservationTemporalRef"
        )
    canonical = json.dumps(
        {"kind": temporal.kind.value, "ref": temporal.ref},
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    digest = hashlib.sha256()
    digest.update(_TEMPORAL_DOMAIN)
    digest.update(canonical)
    return f"pilot_observation_temporal:{digest.hexdigest()}"


@dataclass(frozen=True, slots=True)
class PilotMaterializationTemporalDeclaration:
    """Private exact-candidate-bound temporal/intervention declaration.

    Empty means only that no temporal refs were supplied. It does not assert
    absence of intervention, carryover, adaptive state, exposure, or history
    dependence.
    """

    candidate_sha256: str
    temporals: tuple[PilotObservationTemporalRef, ...] = ()

    def __post_init__(self) -> None:
        if (
            not isinstance(self.candidate_sha256, str)
            or _SHA256_RE.fullmatch(self.candidate_sha256) is None
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "temporal declaration candidate_sha256 must be a lowercase "
                "64-character sha256 digest"
            )
        if not isinstance(self.temporals, tuple):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "temporal declaration temporals must be a tuple"
            )
        if any(
            not isinstance(item, PilotObservationTemporalRef)
            for item in self.temporals
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "temporal declaration must contain PilotObservationTemporalRef values"
            )
        if len(set(self.temporals)) != len(self.temporals):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "temporal declaration must not repeat an exact temporal ref"
            )
        object.__setattr__(
            self,
            "temporals",
            tuple(
                sorted(
                    self.temporals,
                    key=lambda item: (item.kind.value, item.ref),
                )
            ),
        )


def build_pilot_materialization_temporal_declaration_v1(
    candidate,
    *,
    temporals: tuple[PilotObservationTemporalRef, ...] = (),
) -> PilotMaterializationTemporalDeclaration:
    """Bind explicit temporal/intervention metadata to exact candidate bytes."""

    if not isinstance(
        candidate,
        _materialization.PilotEvidenceMaterializationCandidate,
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "candidate must be PilotEvidenceMaterializationCandidate"
        )
    return PilotMaterializationTemporalDeclaration(
        candidate_sha256=(
            _materialization.pilot_evidence_materialization_candidate_sha256(
                candidate
            )
        ),
        temporals=temporals,
    )


@dataclass(frozen=True, slots=True)
class PilotMaterializedEvidenceTemporalEntry:
    """One reviewed coordination basis plus candidate-bound temporal metadata."""

    coordination_entry: _coordination.PilotMaterializedEvidenceCoordinationEntry
    temporal_declaration: PilotMaterializationTemporalDeclaration

    def __post_init__(self) -> None:
        if not isinstance(
            self.coordination_entry,
            _coordination.PilotMaterializedEvidenceCoordinationEntry,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "temporal entry coordination_entry must be "
                "PilotMaterializedEvidenceCoordinationEntry"
            )
        if not isinstance(
            self.temporal_declaration,
            PilotMaterializationTemporalDeclaration,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "temporal entry declaration must be "
                "PilotMaterializationTemporalDeclaration"
            )
        candidate = (
            self.coordination_entry.mechanism_entry.upstream_lineage_entry
            .basis_entry.candidate
        )
        expected_candidate_sha256 = (
            _materialization.pilot_evidence_materialization_candidate_sha256(
                candidate
            )
        )
        if self.temporal_declaration.candidate_sha256 != expected_candidate_sha256:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "temporal declaration candidate_sha256 does not match exact "
                "basis candidate"
            )

    @property
    def temporal_keys(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                pilot_observation_temporal_dependence_key_v1(temporal)
                for temporal in self.temporal_declaration.temporals
            )
        )


def validate_pilot_materialized_evidence_shared_temporal_preconditions_v1(
    temporal_entries,
    *,
    source_lineage_graph: _source_lineage.PilotUpstreamSourceLineageGraph,
    source_completeness_review: _source_completeness.PilotUpstreamLineageCompletenessReview,
    mechanism_lineage_graph: _mechanism_lineage.PilotObservationMechanismLineageGraph,
    mechanism_completeness_review: _mechanism_completeness.PilotMechanismLineageCompletenessReview,
    coordination_lineage_graph: (
        _coordination_lineage.PilotObservationCoordinationLineageGraph
    ),
    coordination_completeness_review: (
        _coordination_completeness.PilotCoordinationLineageCompletenessReview
    ),
):
    """Reject exact shared temporal/intervention causal identities after prior gates.

    PASS means only that the full reviewed source/mechanism/coordination ladder
    passed and no exact declared temporal identity was repeated across the
    observations. Different refs, empty declarations, or separated timestamps
    are not independence certificates.
    """

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
        not isinstance(item, PilotMaterializedEvidenceTemporalEntry)
        for item in entries
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "temporal_entries must contain "
            "PilotMaterializedEvidenceTemporalEntry values"
        )

    entries = tuple(
        sorted(
            entries,
            key=lambda item: str(
                item.coordination_entry.mechanism_entry.upstream_lineage_entry
                .basis_entry.evidence.evidence_id
            ),
        )
    )

    reviewed_coordination_entries = (
        _coordination_completeness.validate_pilot_materialized_evidence_reviewed_coordination_origin_preconditions_v1(
            (item.coordination_entry for item in entries),
            source_lineage_graph=source_lineage_graph,
            source_completeness_review=source_completeness_review,
            mechanism_lineage_graph=mechanism_lineage_graph,
            mechanism_completeness_review=mechanism_completeness_review,
            coordination_lineage_graph=coordination_lineage_graph,
            coordination_completeness_review=coordination_completeness_review,
        )
    )
    if (
        tuple(item.coordination_entry for item in entries)
        != reviewed_coordination_entries
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "temporal entries do not match reviewed coordination-origin basis ordering"
        )

    seen_temporal: dict[str, object] = {}
    for entry in entries:
        evidence_id = (
            entry.coordination_entry.mechanism_entry.upstream_lineage_entry
            .basis_entry.evidence.evidence_id
        )
        for key in entry.temporal_keys:
            previous = seen_temporal.get(key)
            if previous is not None:
                raise _materialization.InvalidPilotEvidenceMaterialization(
                    "distinct materialized Pilot observations share one exact "
                    "declared temporal/intervention/carryover causal identity; "
                    "known shared temporal context cannot satisfy PR10.1 "
                    "shared-temporal independence preconditions: "
                    f"temporal={key}, first={previous}, second={evidence_id}"
                )
            seen_temporal[key] = evidence_id

    return entries
