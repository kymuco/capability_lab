"""Explicit observation/acquisition mechanism dependence governance for PR10.1 Pilot 01."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import re

from . import materialization as _materialization
from . import materialization_dependence as _dependence
from . import materialization_lineage_completeness as _completeness
from . import materialization_source_lineage as _source_lineage


_MECHANISM_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_MECHANISM_DOMAIN = (
    b"capability_lab/pilot_observation_mechanism_dependence@1\x00"
)


class PilotObservationMechanismKind(str, Enum):
    """Explicit acquisition/governance mechanism categories for one observation."""

    OPERATOR = "OPERATOR"
    MODEL_RUN = "MODEL_RUN"
    ACQUISITION_PIPELINE = "ACQUISITION_PIPELINE"
    ENVIRONMENT = "ENVIRONMENT"
    TOOL_EXECUTION = "TOOL_EXECUTION"
    REVIEW_PROCESS = "REVIEW_PROCESS"
    OTHER = "OTHER"


@dataclass(frozen=True, slots=True)
class PilotObservationMechanismRef:
    """One exact mechanism identity explicitly declared relevant to an observation."""

    kind: PilotObservationMechanismKind
    ref: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, PilotObservationMechanismKind):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation mechanism kind must be PilotObservationMechanismKind"
            )
        if (
            not isinstance(self.ref, str)
            or _MECHANISM_REF_RE.fullmatch(self.ref) is None
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation mechanism ref must be a canonical opaque ASCII identifier"
            )


def pilot_observation_mechanism_dependence_key_v1(
    mechanism: PilotObservationMechanismRef,
) -> str:
    """Return a privacy-reducing key for one exact declared mechanism identity.

    Equality means the same exact kind/ref pair was declared. Inequality does not
    prove that two mechanisms are causally independent, distinct, or unrelated.
    """

    if not isinstance(mechanism, PilotObservationMechanismRef):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "mechanism must be PilotObservationMechanismRef"
        )
    canonical = json.dumps(
        {
            "kind": mechanism.kind.value,
            "ref": mechanism.ref,
        },
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    digest = hashlib.sha256()
    digest.update(_MECHANISM_DOMAIN)
    digest.update(canonical)
    return f"pilot_observation_mechanism:{digest.hexdigest()}"


@dataclass(frozen=True, slots=True)
class PilotMaterializationMechanismDeclaration:
    """Private exact-candidate-bound declaration of relevant mechanisms.

    An empty declaration means only that no mechanism refs were supplied by this
    declaration. It does not assert mechanism absence or independence.
    """

    candidate_sha256: str
    mechanisms: tuple[PilotObservationMechanismRef, ...] = ()

    def __post_init__(self) -> None:
        if (
            not isinstance(self.candidate_sha256, str)
            or _SHA256_RE.fullmatch(self.candidate_sha256) is None
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "mechanism declaration candidate_sha256 must be a lowercase 64-character sha256 digest"
            )
        if not isinstance(self.mechanisms, tuple):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "mechanism declaration mechanisms must be a tuple"
            )
        if any(
            not isinstance(item, PilotObservationMechanismRef)
            for item in self.mechanisms
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "mechanism declaration must contain PilotObservationMechanismRef values"
            )
        if len(set(self.mechanisms)) != len(self.mechanisms):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "mechanism declaration must not repeat an exact mechanism ref"
            )
        object.__setattr__(
            self,
            "mechanisms",
            tuple(
                sorted(
                    self.mechanisms,
                    key=lambda item: (item.kind.value, item.ref),
                )
            ),
        )


def build_pilot_materialization_mechanism_declaration_v1(
    candidate,
    *,
    mechanisms: tuple[PilotObservationMechanismRef, ...] = (),
) -> PilotMaterializationMechanismDeclaration:
    """Bind an explicit mechanism declaration to exact candidate bytes."""

    if not isinstance(
        candidate,
        _materialization.PilotEvidenceMaterializationCandidate,
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "candidate must be PilotEvidenceMaterializationCandidate"
        )
    return PilotMaterializationMechanismDeclaration(
        candidate_sha256=(
            _materialization.pilot_evidence_materialization_candidate_sha256(
                candidate
            )
        ),
        mechanisms=mechanisms,
    )


@dataclass(frozen=True, slots=True)
class PilotMaterializedEvidenceMechanismEntry:
    """One exact source-lineage basis plus candidate-bound mechanism metadata."""

    upstream_lineage_entry: _dependence.PilotMaterializedEvidenceUpstreamLineageEntry
    mechanism_declaration: PilotMaterializationMechanismDeclaration

    def __post_init__(self) -> None:
        if not isinstance(
            self.upstream_lineage_entry,
            _dependence.PilotMaterializedEvidenceUpstreamLineageEntry,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "mechanism entry upstream_lineage_entry must be PilotMaterializedEvidenceUpstreamLineageEntry"
            )
        if not isinstance(
            self.mechanism_declaration,
            PilotMaterializationMechanismDeclaration,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "mechanism entry declaration must be PilotMaterializationMechanismDeclaration"
            )
        expected_candidate_sha256 = (
            _materialization.pilot_evidence_materialization_candidate_sha256(
                self.upstream_lineage_entry.basis_entry.candidate
            )
        )
        if (
            self.mechanism_declaration.candidate_sha256
            != expected_candidate_sha256
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "mechanism declaration candidate_sha256 does not match exact basis candidate"
            )

    @property
    def mechanism_keys(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                pilot_observation_mechanism_dependence_key_v1(mechanism)
                for mechanism in self.mechanism_declaration.mechanisms
            )
        )


def validate_pilot_materialized_evidence_shared_mechanism_preconditions_v1(
    mechanism_entries,
    *,
    source_lineage_graph: _source_lineage.PilotUpstreamSourceLineageGraph,
    completeness_review: _completeness.PilotUpstreamLineageCompletenessReview,
):
    """Reject exact shared declared mechanisms after reviewed source-origin gates.

    Passing means that the exact reviewed source-origin preconditions passed and
    no exact declared acquisition/governance mechanism kind/ref was repeated
    across observations. It does not prove mechanism disclosure completeness,
    causal independence, or independent replication.
    """

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
        not isinstance(item, PilotMaterializedEvidenceMechanismEntry)
        for item in entries
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "mechanism_entries must contain PilotMaterializedEvidenceMechanismEntry values"
        )

    entries = tuple(
        sorted(
            entries,
            key=lambda item: str(
                item.upstream_lineage_entry.basis_entry.evidence.evidence_id
            ),
        )
    )

    reviewed_entries = (
        _completeness.validate_pilot_materialized_evidence_reviewed_source_origin_preconditions_v1(
            (
                item.upstream_lineage_entry
                for item in entries
            ),
            source_lineage_graph=source_lineage_graph,
            completeness_review=completeness_review,
        )
    )
    if tuple(
        item.upstream_lineage_entry for item in entries
    ) != reviewed_entries:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "mechanism entries do not match reviewed source-origin basis ordering"
        )

    seen_mechanisms: dict[str, object] = {}
    for entry in entries:
        evidence_id = entry.upstream_lineage_entry.basis_entry.evidence.evidence_id
        for key in entry.mechanism_keys:
            previous = seen_mechanisms.get(key)
            if previous is not None:
                raise _materialization.InvalidPilotEvidenceMaterialization(
                    "distinct materialized Pilot observations share one exact declared "
                    "acquisition/governance mechanism; known common observation mechanisms "
                    "cannot satisfy PR10.1 shared-mechanism independence preconditions: "
                    f"mechanism={key}, first={previous}, second={evidence_id}"
                )
            seen_mechanisms[key] = evidence_id

    return entries
