"""Explicit cross-observation coordination/control dependence governance for PR10.1 Pilot 01."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import re

from . import materialization as _materialization
from . import materialization_lineage_completeness as _source_completeness
from . import materialization_mechanism_completeness as _mechanism_completeness
from . import materialization_mechanism_dependence as _mechanism
from . import materialization_mechanism_lineage as _mechanism_lineage
from . import materialization_source_lineage as _source_lineage


_COORDINATION_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_COORDINATION_DOMAIN = b"capability_lab/pilot_observation_coordination_control_dependence@1\x00"


class PilotObservationCoordinationKind(str, Enum):
    """Explicit higher-order cross-observation coordination/control categories."""

    CONTROLLER = "CONTROLLER"
    POLICY_EXECUTION = "POLICY_EXECUTION"
    ADAPTIVE_SELECTOR = "ADAPTIVE_SELECTOR"
    CONDITION_ASSIGNER = "CONDITION_ASSIGNER"
    SCHEDULER = "SCHEDULER"
    ADJUDICATION_AUTHORITY = "ADJUDICATION_AUTHORITY"
    COORDINATION_PROCESS = "COORDINATION_PROCESS"
    OTHER = "OTHER"


@dataclass(frozen=True, slots=True)
class PilotObservationCoordinationRef:
    """One exact declared cross-observation coordination/control identity."""

    kind: PilotObservationCoordinationKind
    ref: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, PilotObservationCoordinationKind):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation coordination kind must be PilotObservationCoordinationKind"
            )
        if not isinstance(self.ref, str) or _COORDINATION_REF_RE.fullmatch(self.ref) is None:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation coordination ref must be a canonical opaque ASCII identifier"
            )


def pilot_observation_coordination_dependence_key_v1(
    coordination: PilotObservationCoordinationRef,
) -> str:
    """Return a privacy-reducing key for one exact declared coordination identity."""

    if not isinstance(coordination, PilotObservationCoordinationRef):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "coordination must be PilotObservationCoordinationRef"
        )
    canonical = json.dumps(
        {"kind": coordination.kind.value, "ref": coordination.ref},
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    digest = hashlib.sha256()
    digest.update(_COORDINATION_DOMAIN)
    digest.update(canonical)
    return f"pilot_observation_coordination:{digest.hexdigest()}"


@dataclass(frozen=True, slots=True)
class PilotMaterializationCoordinationDeclaration:
    """Private exact-candidate-bound higher-order coordination declaration.

    Empty means only that no coordination refs were supplied, not that no
    higher-order controller or authority existed.
    """

    candidate_sha256: str
    coordinations: tuple[PilotObservationCoordinationRef, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.candidate_sha256, str) or _SHA256_RE.fullmatch(self.candidate_sha256) is None:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "coordination declaration candidate_sha256 must be a lowercase 64-character sha256 digest"
            )
        if not isinstance(self.coordinations, tuple):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "coordination declaration coordinations must be a tuple"
            )
        if any(not isinstance(item, PilotObservationCoordinationRef) for item in self.coordinations):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "coordination declaration must contain PilotObservationCoordinationRef values"
            )
        if len(set(self.coordinations)) != len(self.coordinations):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "coordination declaration must not repeat an exact coordination ref"
            )
        object.__setattr__(
            self,
            "coordinations",
            tuple(sorted(self.coordinations, key=lambda item: (item.kind.value, item.ref))),
        )


def build_pilot_materialization_coordination_declaration_v1(
    candidate,
    *,
    coordinations: tuple[PilotObservationCoordinationRef, ...] = (),
) -> PilotMaterializationCoordinationDeclaration:
    """Bind explicit coordination metadata to exact materialization candidate bytes."""

    if not isinstance(candidate, _materialization.PilotEvidenceMaterializationCandidate):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "candidate must be PilotEvidenceMaterializationCandidate"
        )
    return PilotMaterializationCoordinationDeclaration(
        candidate_sha256=_materialization.pilot_evidence_materialization_candidate_sha256(candidate),
        coordinations=coordinations,
    )


@dataclass(frozen=True, slots=True)
class PilotMaterializedEvidenceCoordinationEntry:
    """One reviewed-mechanism basis plus candidate-bound coordination metadata."""

    mechanism_entry: _mechanism.PilotMaterializedEvidenceMechanismEntry
    coordination_declaration: PilotMaterializationCoordinationDeclaration

    def __post_init__(self) -> None:
        if not isinstance(self.mechanism_entry, _mechanism.PilotMaterializedEvidenceMechanismEntry):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "coordination entry mechanism_entry must be PilotMaterializedEvidenceMechanismEntry"
            )
        if not isinstance(self.coordination_declaration, PilotMaterializationCoordinationDeclaration):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "coordination entry declaration must be PilotMaterializationCoordinationDeclaration"
            )
        expected_candidate_sha256 = _materialization.pilot_evidence_materialization_candidate_sha256(
            self.mechanism_entry.upstream_lineage_entry.basis_entry.candidate
        )
        if self.coordination_declaration.candidate_sha256 != expected_candidate_sha256:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "coordination declaration candidate_sha256 does not match exact basis candidate"
            )

    @property
    def coordination_keys(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                pilot_observation_coordination_dependence_key_v1(coordination)
                for coordination in self.coordination_declaration.coordinations
            )
        )


def validate_pilot_materialized_evidence_shared_coordination_preconditions_v1(
    coordination_entries,
    *,
    source_lineage_graph: _source_lineage.PilotUpstreamSourceLineageGraph,
    source_completeness_review: _source_completeness.PilotUpstreamLineageCompletenessReview,
    mechanism_lineage_graph: _mechanism_lineage.PilotObservationMechanismLineageGraph,
    mechanism_completeness_review: _mechanism_completeness.PilotMechanismLineageCompletenessReview,
):
    """Reject exact shared coordination after the full reviewed provenance ladder."""

    if isinstance(coordination_entries, (str, bytes)):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "coordination_entries must be an iterable of PilotMaterializedEvidenceCoordinationEntry values"
        )
    try:
        entries = tuple(coordination_entries)
    except TypeError as exc:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "coordination_entries must be iterable"
        ) from exc
    if any(not isinstance(item, PilotMaterializedEvidenceCoordinationEntry) for item in entries):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "coordination_entries must contain PilotMaterializedEvidenceCoordinationEntry values"
        )

    entries = tuple(
        sorted(
            entries,
            key=lambda item: str(
                item.mechanism_entry.upstream_lineage_entry.basis_entry.evidence.evidence_id
            ),
        )
    )
    reviewed_mechanism_entries = (
        _mechanism_completeness.validate_pilot_materialized_evidence_reviewed_mechanism_origin_preconditions_v1(
            (item.mechanism_entry for item in entries),
            source_lineage_graph=source_lineage_graph,
            source_completeness_review=source_completeness_review,
            mechanism_lineage_graph=mechanism_lineage_graph,
            mechanism_completeness_review=mechanism_completeness_review,
        )
    )
    if tuple(item.mechanism_entry for item in entries) != reviewed_mechanism_entries:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "coordination entries do not match reviewed mechanism-origin basis ordering"
        )

    seen_coordination: dict[str, object] = {}
    for entry in entries:
        evidence_id = entry.mechanism_entry.upstream_lineage_entry.basis_entry.evidence.evidence_id
        for key in entry.coordination_keys:
            previous = seen_coordination.get(key)
            if previous is not None:
                raise _materialization.InvalidPilotEvidenceMaterialization(
                    "distinct materialized Pilot observations share one exact declared "
                    "cross-observation coordination/control authority; known shared "
                    "coordination cannot satisfy PR10.1 shared-coordination independence "
                    f"preconditions: coordination={key}, first={previous}, second={evidence_id}"
                )
            seen_coordination[key] = evidence_id

    return entries
