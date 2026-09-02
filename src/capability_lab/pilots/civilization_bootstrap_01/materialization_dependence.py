"""Structural dependence governance for PR10.1 materialized Pilot 01 evidence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import re

from . import materialization as _materialization


_PILOT_CAPTURE_SOURCE_REF_RE = re.compile(r"^pilot_capture:[0-9a-f]{64}$")
_MATERIALIZATION_NOTE_RE = re.compile(
    r"^materialization_id=([A-Za-z0-9][A-Za-z0-9._:-]{0,127}); "
    r"candidate_sha256=([0-9a-f]{64}); "
    r"review_id=([A-Za-z0-9][A-Za-z0-9._:-]{0,127})$"
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_UPSTREAM_SOURCE_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
_SESSION_LINEAGE_DOMAIN = (
    b"capability_lab/pilot_materialization_session_lineage@1\x00"
)
_ELICITATION_LINEAGE_DOMAIN = (
    b"capability_lab/pilot_materialization_elicitation_lineage@1\x00"
)
_UPSTREAM_SOURCE_DOMAIN = (
    b"capability_lab/pilot_materialization_upstream_source_lineage@1\x00"
)


def _materialization_note_fields_v1(evidence) -> tuple[str, str, str]:
    steps = evidence.provenance.steps
    if len(steps) != 1:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "PR10.1 materialized evidence must have exactly one provenance step"
        )
    step = steps[0]
    if step.operation_key != "pilot_materialize":
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "PR10.1 materialized evidence provenance step must be pilot_materialize"
        )
    if step.mechanism_ref != str(
        _materialization.REVIEWED_PILOT_CAPTURE_TO_EVIDENCE_POLICY_V1
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "PR10.1 materialized evidence mechanism_ref must match the frozen policy"
        )
    if step.note is None:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "PR10.1 materialized evidence must preserve exact materialization provenance note"
        )
    match = _MATERIALIZATION_NOTE_RE.fullmatch(step.note)
    if match is None:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "PR10.1 materialized evidence provenance note is not canonical"
        )
    return match.group(1), match.group(2), match.group(3)


def _domain_separated_metadata_key(
    *,
    domain: bytes,
    prefix: str,
    payload: dict[str, str],
) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    digest = hashlib.sha256()
    digest.update(domain)
    digest.update(canonical)
    return f"{prefix}{digest.hexdigest()}"


def pilot_materialized_evidence_dependence_key_v1(evidence) -> str:
    """Return the exact PilotCaptureRecord source key for one PR10.1 evidence record.

    The returned key identifies exact same-source dependence only. Distinct keys do
    not establish statistical or epistemic independence.
    """

    if not isinstance(evidence, _materialization.EvidenceRecord):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "evidence must be EvidenceRecord"
        )
    if evidence.outcome is not None:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "PR10.1 materialized evidence must preserve outcome=None"
        )

    sources = evidence.provenance.sources
    if len(sources) != 1:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "PR10.1 materialized evidence must have exactly one provenance source"
        )
    source = sources[0]
    if source.kind is not _materialization.ProvenanceSourceKind.EXTERNAL_RECORD:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "PR10.1 materialized evidence source must be EXTERNAL_RECORD"
        )
    if _PILOT_CAPTURE_SOURCE_REF_RE.fullmatch(source.ref) is None:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "PR10.1 materialized evidence source must be an exact pilot_capture sha256 ref"
        )
    if evidence.payload_refs != (source.ref,):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "PR10.1 materialized evidence payload_refs must exactly repeat its pilot capture source"
        )

    _materialization_note_fields_v1(evidence)
    return source.ref


def pilot_materialization_candidate_session_lineage_key_v1(candidate) -> str:
    """Return a conservative same-session lineage key for one reviewed candidate.

    Equality proves a shared PR10.1 protocol/subject/session lineage. Inequality does
    not prove independence.
    """

    if not isinstance(candidate, _materialization.PilotEvidenceMaterializationCandidate):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "candidate must be PilotEvidenceMaterializationCandidate"
        )
    return _domain_separated_metadata_key(
        domain=_SESSION_LINEAGE_DOMAIN,
        prefix="pilot_session_lineage:",
        payload={
            "protocol_ref": str(candidate.protocol_ref),
            "session_id": candidate.session_id,
            "subject_ref": str(candidate.subject_ref),
        },
    )


def pilot_materialization_candidate_elicitation_lineage_key_v1(candidate) -> str:
    """Return the repeated-test-form lineage key for one reviewed candidate.

    Equality proves that one subject was observed under the same exact protocol
    revision and probe identifier. Different session IDs do not break this known
    elicitation lineage. Inequality does not prove independence.
    """

    if not isinstance(candidate, _materialization.PilotEvidenceMaterializationCandidate):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "candidate must be PilotEvidenceMaterializationCandidate"
        )
    return _domain_separated_metadata_key(
        domain=_ELICITATION_LINEAGE_DOMAIN,
        prefix="pilot_elicitation_lineage:",
        payload={
            "probe_id": candidate.probe_id,
            "protocol_ref": str(candidate.protocol_ref),
            "subject_ref": str(candidate.subject_ref),
        },
    )


class PilotUpstreamSourceKind(str, Enum):
    """Declared upstream causal-source categories for PR10.1 dependence review."""

    REFERENCE = "REFERENCE"
    ARTIFACT = "ARTIFACT"
    DATASET = "DATASET"
    MODEL_OUTPUT = "MODEL_OUTPUT"
    TOOL_OUTPUT = "TOOL_OUTPUT"
    OPERATOR_INPUT = "OPERATOR_INPUT"
    EXTERNAL_RECORD = "EXTERNAL_RECORD"
    OTHER = "OTHER"


@dataclass(frozen=True, slots=True)
class PilotUpstreamSourceRef:
    """One exact, declared upstream-source identity within local governance."""

    kind: PilotUpstreamSourceKind
    ref: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, PilotUpstreamSourceKind):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "upstream source kind must be PilotUpstreamSourceKind"
            )
        if (
            not isinstance(self.ref, str)
            or _UPSTREAM_SOURCE_REF_RE.fullmatch(self.ref) is None
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "upstream source ref must be a canonical opaque ASCII identifier"
            )


def pilot_upstream_source_dependence_key_v1(source: PilotUpstreamSourceRef) -> str:
    """Return a privacy-reducing key for one exact declared upstream-source ref.

    Equality means the declarations name the same kind/ref pair. Inequality does
    not prove that the underlying causal sources are independent or even distinct.
    """

    if not isinstance(source, PilotUpstreamSourceRef):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "source must be PilotUpstreamSourceRef"
        )
    return _domain_separated_metadata_key(
        domain=_UPSTREAM_SOURCE_DOMAIN,
        prefix="pilot_upstream_source:",
        payload={
            "kind": source.kind.value,
            "ref": source.ref,
        },
    )


@dataclass(frozen=True, slots=True)
class PilotMaterializationUpstreamSourceDeclaration:
    """Private, exact-candidate-bound declaration of known upstream sources.

    An empty tuple means that this declaration supplies no upstream-source refs.
    It does not prove that no upstream source exists.
    """

    candidate_sha256: str
    sources: tuple[PilotUpstreamSourceRef, ...] = ()

    def __post_init__(self) -> None:
        if (
            not isinstance(self.candidate_sha256, str)
            or _SHA256_RE.fullmatch(self.candidate_sha256) is None
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "upstream declaration candidate_sha256 must be a lowercase 64-character sha256 digest"
            )
        if not isinstance(self.sources, tuple):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "upstream declaration sources must be a tuple"
            )
        if any(not isinstance(item, PilotUpstreamSourceRef) for item in self.sources):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "upstream declaration sources must contain PilotUpstreamSourceRef values"
            )
        if len(set(self.sources)) != len(self.sources):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "upstream declaration must not repeat an exact source ref"
            )
        object.__setattr__(
            self,
            "sources",
            tuple(sorted(self.sources, key=lambda item: (item.kind.value, item.ref))),
        )


def build_pilot_materialization_upstream_source_declaration_v1(
    candidate,
    *,
    sources: tuple[PilotUpstreamSourceRef, ...] = (),
) -> PilotMaterializationUpstreamSourceDeclaration:
    """Bind an explicit upstream-source declaration to exact candidate bytes."""

    if not isinstance(candidate, _materialization.PilotEvidenceMaterializationCandidate):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "candidate must be PilotEvidenceMaterializationCandidate"
        )
    return PilotMaterializationUpstreamSourceDeclaration(
        candidate_sha256=(
            _materialization.pilot_evidence_materialization_candidate_sha256(
                candidate
            )
        ),
        sources=sources,
    )


@dataclass(frozen=True, slots=True)
class PilotMaterializedEvidenceBasisEntry:
    """Candidate paired with one structurally PR10.1-shaped EvidenceRecord.

    This lower diagnostic basis does not itself prove that the selected MATERIALIZE
    review was presented. Terminal PR10.1 governance additionally requires the
    resolver-issued reviewed-resolution receipt binding for every observation slot.
    """

    candidate: _materialization.PilotEvidenceMaterializationCandidate
    evidence: _materialization.EvidenceRecord

    def __post_init__(self) -> None:
        if not isinstance(
            self.candidate,
            _materialization.PilotEvidenceMaterializationCandidate,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "basis entry candidate must be PilotEvidenceMaterializationCandidate"
            )
        if not isinstance(self.evidence, _materialization.EvidenceRecord):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "basis entry evidence must be EvidenceRecord"
            )

        source_key = pilot_materialized_evidence_dependence_key_v1(self.evidence)
        if source_key != self.candidate.source_capture_ref:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "basis entry evidence source does not match candidate source capture"
            )
        if self.evidence.evidence_id != self.candidate.proposed_evidence_id:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "basis entry evidence_id does not match candidate proposed_evidence_id"
            )
        if self.evidence.subject_ref != self.candidate.subject_ref:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "basis entry evidence subject does not match candidate subject"
            )

        materialization_id, candidate_sha256, _review_id = (
            _materialization_note_fields_v1(self.evidence)
        )
        if materialization_id != str(self.candidate.materialization_id):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "basis entry provenance materialization_id does not match candidate"
            )
        expected_candidate_sha256 = (
            _materialization.pilot_evidence_materialization_candidate_sha256(
                self.candidate
            )
        )
        if candidate_sha256 != expected_candidate_sha256:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "basis entry provenance candidate_sha256 does not match exact candidate"
            )

    @property
    def exact_source_key(self) -> str:
        return pilot_materialized_evidence_dependence_key_v1(self.evidence)

    @property
    def session_lineage_key(self) -> str:
        return pilot_materialization_candidate_session_lineage_key_v1(self.candidate)

    @property
    def elicitation_lineage_key(self) -> str:
        return pilot_materialization_candidate_elicitation_lineage_key_v1(
            self.candidate
        )


@dataclass(frozen=True, slots=True)
class PilotMaterializedEvidenceUpstreamLineageEntry:
    """One exact basis entry plus candidate-bound upstream-source metadata."""

    basis_entry: PilotMaterializedEvidenceBasisEntry
    upstream_declaration: PilotMaterializationUpstreamSourceDeclaration

    def __post_init__(self) -> None:
        if not isinstance(self.basis_entry, PilotMaterializedEvidenceBasisEntry):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "upstream lineage entry basis_entry must be PilotMaterializedEvidenceBasisEntry"
            )
        if not isinstance(
            self.upstream_declaration,
            PilotMaterializationUpstreamSourceDeclaration,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "upstream lineage entry declaration must be PilotMaterializationUpstreamSourceDeclaration"
            )
        expected_candidate_sha256 = (
            _materialization.pilot_evidence_materialization_candidate_sha256(
                self.basis_entry.candidate
            )
        )
        if self.upstream_declaration.candidate_sha256 != expected_candidate_sha256:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "upstream declaration candidate_sha256 does not match exact basis candidate"
            )

    @property
    def upstream_source_keys(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                pilot_upstream_source_dependence_key_v1(source)
                for source in self.upstream_declaration.sources
            )
        )


def _validate_unique_basis_evidence_identity_v1(entries) -> None:
    seen: set[object] = set()
    for entry in entries:
        evidence_id = entry.evidence.evidence_id
        if evidence_id in seen:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "duplicate EvidenceId appears in the lower PR10.1 materialized basis; "
                "one EvidenceRecord identity cannot occupy multiple observation slots: "
                f"evidence_id={evidence_id}"
            )
        seen.add(evidence_id)


def _validate_completeness_review_temporal_causality_v1(
    reviewed_at,
    evidence_records,
    *,
    family: str,
) -> None:
    """Fail closed when a real family review predates its materialized basis.

    Isolated unit tests may monkeypatch family entry-normalizers with SimpleNamespace
    fixtures. Those fixtures intentionally do not claim to be real EvidenceRecord
    values, so chronology is enforced only when the supplied records are actual PR2
    EvidenceRecord instances. Production family gates reach this helper only through
    their normal exact entry types.
    """

    records = tuple(evidence_records)
    if not records or any(
        not isinstance(record, _materialization.EvidenceRecord)
        for record in records
    ):
        return
    latest_recorded_at = max(record.recorded_at for record in records)
    if reviewed_at < latest_recorded_at:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            f"{family} completeness reviewed_at must not precede the latest "
            "materialized EvidenceRecord recorded_at in the exact reviewed basis"
        )


def validate_pilot_materialized_evidence_no_same_source_amplification_v1(
    evidence_records,
):
    """Reject repeated exact PilotCaptureRecord sources in a multi-evidence basis.

    This is an anti-amplification gate, not an independence prover. A successful
    validation means only that no exact PilotCaptureRecord source was repeated.
    """

    if isinstance(evidence_records, (str, bytes)):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "evidence_records must be an iterable of EvidenceRecord values"
        )
    try:
        records = tuple(evidence_records)
    except TypeError as exc:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "evidence_records must be iterable"
        ) from exc

    seen: dict[str, object] = {}
    for evidence in records:
        key = pilot_materialized_evidence_dependence_key_v1(evidence)
        previous = seen.get(key)
        if previous is not None:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "same PilotCaptureRecord source appears in multiple materialized "
                "EvidenceRecord values; same-source materializations are dependent "
                f"and cannot occupy multiple evidence slots: source={key}, "
                f"first={previous}, second={evidence.evidence_id}"
            )
        seen[key] = evidence.evidence_id

    return tuple(sorted(records, key=lambda item: item.evidence_id))


def validate_pilot_materialized_evidence_independence_preconditions_v1(
    basis_entries,
):
    """Reject ambiguous identity, exact-source reuse and known same-session correlation.

    This is the first-tier structural gate retained from the previous PR10.1
    closure. Passing it never proved cross-session independence; callers making
    a cross-session replication/independence claim must additionally use
    validate_pilot_materialized_evidence_cross_session_replication_preconditions_v1.
    """

    if isinstance(basis_entries, (str, bytes)):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "basis_entries must be an iterable of PilotMaterializedEvidenceBasisEntry values"
        )
    try:
        entries = tuple(basis_entries)
    except TypeError as exc:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "basis_entries must be iterable"
        ) from exc
    if any(not isinstance(item, PilotMaterializedEvidenceBasisEntry) for item in entries):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "basis_entries must contain PilotMaterializedEvidenceBasisEntry values"
        )

    # EvidenceId is the ordering/identity key used throughout reviewed scope
    # canonicalization. Ambiguous duplicate identity is therefore rejected at the
    # first multi-basis gate, not left solely to the terminal aggregate guard.
    _validate_unique_basis_evidence_identity_v1(entries)

    validate_pilot_materialized_evidence_no_same_source_amplification_v1(
        entry.evidence for entry in entries
    )

    seen_sessions: dict[str, object] = {}
    for entry in entries:
        key = entry.session_lineage_key
        previous = seen_sessions.get(key)
        if previous is not None:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "distinct PilotCaptureRecord sources share one reviewed Pilot session "
                "lineage; same-session observations are structurally correlated and "
                "cannot satisfy PR10.1 independence preconditions: "
                f"session_lineage={key}, first={previous}, "
                f"second={entry.evidence.evidence_id}"
            )
        seen_sessions[key] = entry.evidence.evidence_id

    return tuple(sorted(entries, key=lambda item: item.evidence.evidence_id))


def validate_pilot_materialized_evidence_cross_session_replication_preconditions_v1(
    basis_entries,
):
    """Reject known correlation before treating cross-session records as replication.

    This stronger gate composes the exact-source and same-session protections with
    repeated-test-form detection across otherwise distinct sessions. Passing it is
    still only a necessary structural precondition, never proof of independence.
    """

    entries = validate_pilot_materialized_evidence_independence_preconditions_v1(
        basis_entries
    )

    seen_elicitations: dict[str, object] = {}
    for entry in entries:
        key = entry.elicitation_lineage_key
        previous = seen_elicitations.get(key)
        if previous is not None:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "distinct PilotCaptureRecord sources repeat one exact Pilot elicitation "
                "lineage across sessions; repeated same-probe observations share one "
                "test-form mechanism and cannot satisfy PR10.1 cross-session "
                "replication preconditions: "
                f"elicitation_lineage={key}, first={previous}, "
                f"second={entry.evidence.evidence_id}"
            )
        seen_elicitations[key] = entry.evidence.evidence_id

    return entries


def validate_pilot_materialized_evidence_upstream_lineage_preconditions_v1(
    lineage_entries,
):
    """Reject known shared declared upstream sources after earlier structural gates.

    This gate composes exact-source, same-session, and repeated-test-form checks,
    then rejects an exact upstream kind/ref that appears in more than one
    candidate-bound declaration. Passing it means only that no such shared
    declared source was supplied; it is never proof of source completeness or
    independence.
    """

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
        not isinstance(item, PilotMaterializedEvidenceUpstreamLineageEntry)
        for item in entries
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "lineage_entries must contain PilotMaterializedEvidenceUpstreamLineageEntry values"
        )

    validate_pilot_materialized_evidence_cross_session_replication_preconditions_v1(
        entry.basis_entry for entry in entries
    )

    seen_sources: dict[str, object] = {}
    for entry in sorted(
        entries,
        key=lambda item: item.basis_entry.evidence.evidence_id,
    ):
        for key in entry.upstream_source_keys:
            previous = seen_sources.get(key)
            if previous is not None:
                raise _materialization.InvalidPilotEvidenceMaterialization(
                    "distinct materialized Pilot observations share one exact declared "
                    "upstream source lineage; known common upstream sources cannot "
                    "satisfy PR10.1 upstream-lineage independence preconditions: "
                    f"upstream_source={key}, first={previous}, "
                    f"second={entry.basis_entry.evidence.evidence_id}"
                )
            seen_sources[key] = entry.basis_entry.evidence.evidence_id

    return tuple(
        sorted(entries, key=lambda item: item.basis_entry.evidence.evidence_id)
    )
