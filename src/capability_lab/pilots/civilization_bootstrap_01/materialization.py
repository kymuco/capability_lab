"""Reviewed Pilot 01 capture-to-PR2 evidence materialization boundary."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import re
import unicodedata

from capability_lab.epistemics import (
    ActorRef,
    CapabilitySubjectRef,
    ContextFactor,
    ContextFactorKind,
    EvidenceContext,
    EvidenceId,
    EvidenceKind,
    EvidenceRecord,
    ProvenanceSource,
    ProvenanceSourceKind,
    ProvenanceStep,
    ProvenanceTrail,
)

from .capture import PilotCaptureRecord
from .protocol import PilotCaptureKind, PilotProtocolRef
from .serialization import pilot_capture_to_json
from .transactional import validate_private_workspace
from .workspace import load_capture_set, load_private_workspace


class PilotEvidenceMaterializationError(ValueError):
    """Base validation error for PR10.1 materialization records."""


class InvalidPilotEvidenceMaterialization(PilotEvidenceMaterializationError):
    pass


_OPAQUE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_NAMESPACE_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*$")
_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_CAPTURE_HASH_DOMAIN = b"capability_lab/pilot_capture_source@1\x00"
_CANDIDATE_HASH_DOMAIN = (
    b"capability_lab/pilot_evidence_materialization_candidate_review_binding@1\x00"
)


def _opaque_id(value: object, field_name: str) -> str:
    if not isinstance(value, str) or _OPAQUE_ID_RE.fullmatch(value) is None:
        raise InvalidPilotEvidenceMaterialization(
            f"{field_name} must be a canonical opaque ASCII identifier"
        )
    return value


def _clean_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise InvalidPilotEvidenceMaterialization(f"{field_name} must be a string")
    cleaned = unicodedata.normalize("NFC", value).strip()
    if not cleaned:
        raise InvalidPilotEvidenceMaterialization(f"{field_name} must be non-empty")
    return cleaned


def _canonical_time(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise InvalidPilotEvidenceMaterialization(f"{field_name} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise InvalidPilotEvidenceMaterialization(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _sha256(value: object, field_name: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise InvalidPilotEvidenceMaterialization(
            f"{field_name} must be a lowercase 64-character sha256 digest"
        )
    return value


@dataclass(frozen=True, order=True, slots=True)
class PilotEvidenceMaterializationId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _opaque_id(self.value, "pilot evidence materialization id"),
        )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, order=True, slots=True)
class PilotEvidenceMaterializationReviewId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _opaque_id(self.value, "pilot evidence materialization review id"),
        )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, order=True, slots=True)
class PilotEvidenceMaterializationPolicyRef:
    namespace: str
    key: str
    revision: int

    def __post_init__(self) -> None:
        if not isinstance(self.namespace, str) or _NAMESPACE_RE.fullmatch(self.namespace) is None:
            raise InvalidPilotEvidenceMaterialization(
                "materialization policy namespace must use canonical namespace syntax"
            )
        if not isinstance(self.key, str) or _KEY_RE.fullmatch(self.key) is None:
            raise InvalidPilotEvidenceMaterialization(
                "materialization policy key must use canonical key syntax"
            )
        if (
            isinstance(self.revision, bool)
            or not isinstance(self.revision, int)
            or self.revision < 1
        ):
            raise InvalidPilotEvidenceMaterialization(
                "materialization policy revision must be an integer >= 1"
            )

    @classmethod
    def parse(cls, value: object) -> "PilotEvidenceMaterializationPolicyRef":
        if not isinstance(value, str):
            raise InvalidPilotEvidenceMaterialization(
                "materialization policy ref must be a string"
            )
        match = re.fullmatch(
            r"([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*):"
            r"([a-z][a-z0-9_]*)@([1-9][0-9]*)",
            value,
        )
        if match is None:
            raise InvalidPilotEvidenceMaterialization(
                "materialization policy ref must use '<namespace>:<key>@<revision>'"
            )
        return cls(match.group(1), match.group(2), int(match.group(3)))

    def __str__(self) -> str:
        return f"{self.namespace}:{self.key}@{self.revision}"


REVIEWED_PILOT_CAPTURE_TO_EVIDENCE_POLICY_V1 = PilotEvidenceMaterializationPolicyRef(
    "capability_lab",
    "reviewed_pilot_capture_to_evidence",
    1,
)


class PilotEvidenceMaterializationReviewerKind(str, Enum):
    HUMAN = "HUMAN"


@dataclass(frozen=True, order=True, slots=True)
class PilotEvidenceMaterializationReviewerRef:
    kind: PilotEvidenceMaterializationReviewerKind
    ref: str

    def __post_init__(self) -> None:
        if self.kind is not PilotEvidenceMaterializationReviewerKind.HUMAN:
            raise InvalidPilotEvidenceMaterialization(
                "PR10.1 v1 requires an explicitly declared human reviewer"
            )
        object.__setattr__(
            self,
            "ref",
            _opaque_id(self.ref, "materialization reviewer ref"),
        )


class PilotEvidenceMaterializationVerdict(str, Enum):
    MATERIALIZE = "MATERIALIZE"
    DO_NOT_MATERIALIZE = "DO_NOT_MATERIALIZE"


@dataclass(frozen=True, slots=True)
class PilotEvidenceMaterializationCandidate:
    materialization_id: PilotEvidenceMaterializationId
    policy_ref: PilotEvidenceMaterializationPolicyRef
    protocol_ref: PilotProtocolRef
    session_id: str
    subject_ref: CapabilitySubjectRef
    capture_id: str
    probe_id: str
    capture_kind: PilotCaptureKind
    source_snapshot_sha256: str
    source_capture_sha256: str
    proposed_evidence_id: EvidenceId
    proposed_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.materialization_id, PilotEvidenceMaterializationId):
            raise InvalidPilotEvidenceMaterialization(
                "materialization_id must be PilotEvidenceMaterializationId"
            )
        if self.policy_ref != REVIEWED_PILOT_CAPTURE_TO_EVIDENCE_POLICY_V1:
            raise InvalidPilotEvidenceMaterialization(
                "PR10.1 candidate must use the frozen reviewed materialization policy"
            )
        if not isinstance(self.protocol_ref, PilotProtocolRef):
            raise InvalidPilotEvidenceMaterialization("protocol_ref must be PilotProtocolRef")
        object.__setattr__(self, "session_id", _opaque_id(self.session_id, "session id"))
        if not isinstance(self.subject_ref, CapabilitySubjectRef):
            raise InvalidPilotEvidenceMaterialization(
                "subject_ref must be CapabilitySubjectRef"
            )
        object.__setattr__(self, "capture_id", _opaque_id(self.capture_id, "capture id"))
        if not isinstance(self.probe_id, str) or _KEY_RE.fullmatch(self.probe_id) is None:
            raise InvalidPilotEvidenceMaterialization(
                "probe_id must use canonical lowercase key syntax"
            )
        if not isinstance(self.capture_kind, PilotCaptureKind):
            raise InvalidPilotEvidenceMaterialization(
                "capture_kind must be PilotCaptureKind"
            )
        object.__setattr__(
            self,
            "source_snapshot_sha256",
            _sha256(self.source_snapshot_sha256, "source_snapshot_sha256"),
        )
        object.__setattr__(
            self,
            "source_capture_sha256",
            _sha256(self.source_capture_sha256, "source_capture_sha256"),
        )
        if not isinstance(self.proposed_evidence_id, EvidenceId):
            raise InvalidPilotEvidenceMaterialization(
                "proposed_evidence_id must be EvidenceId"
            )
        object.__setattr__(
            self,
            "proposed_at",
            _canonical_time(self.proposed_at, "proposed_at"),
        )

    @property
    def source_capture_ref(self) -> str:
        return f"pilot_capture:{self.source_capture_sha256}"


def pilot_evidence_materialization_candidate_sha256(
    candidate: PilotEvidenceMaterializationCandidate,
) -> str:
    """Return a domain-separated digest of exact canonical candidate bytes."""

    if not isinstance(candidate, PilotEvidenceMaterializationCandidate):
        raise InvalidPilotEvidenceMaterialization(
            "candidate must be PilotEvidenceMaterializationCandidate"
        )
    # Local import avoids a module-import cycle while keeping one canonical
    # serialization source for both persistence and review authority binding.
    from .materialization_serialization import materialization_candidate_to_json

    digest = hashlib.sha256()
    digest.update(_CANDIDATE_HASH_DOMAIN)
    digest.update(materialization_candidate_to_json(candidate).encode("utf-8"))
    return digest.hexdigest()


@dataclass(frozen=True, slots=True)
class PilotEvidenceMaterializationReview:
    review_id: PilotEvidenceMaterializationReviewId
    materialization_id: PilotEvidenceMaterializationId
    candidate_sha256: str
    policy_ref: PilotEvidenceMaterializationPolicyRef
    reviewer_ref: PilotEvidenceMaterializationReviewerRef
    verdict: PilotEvidenceMaterializationVerdict
    reviewed_at: datetime
    rationale: str

    def __post_init__(self) -> None:
        if not isinstance(self.review_id, PilotEvidenceMaterializationReviewId):
            raise InvalidPilotEvidenceMaterialization(
                "review_id must be PilotEvidenceMaterializationReviewId"
            )
        if not isinstance(self.materialization_id, PilotEvidenceMaterializationId):
            raise InvalidPilotEvidenceMaterialization(
                "materialization_id must be PilotEvidenceMaterializationId"
            )
        object.__setattr__(
            self,
            "candidate_sha256",
            _sha256(self.candidate_sha256, "candidate_sha256"),
        )
        if self.policy_ref != REVIEWED_PILOT_CAPTURE_TO_EVIDENCE_POLICY_V1:
            raise InvalidPilotEvidenceMaterialization(
                "PR10.1 review must use the frozen reviewed materialization policy"
            )
        if not isinstance(self.reviewer_ref, PilotEvidenceMaterializationReviewerRef):
            raise InvalidPilotEvidenceMaterialization(
                "reviewer_ref must be PilotEvidenceMaterializationReviewerRef"
            )
        if not isinstance(self.verdict, PilotEvidenceMaterializationVerdict):
            raise InvalidPilotEvidenceMaterialization(
                "verdict must be PilotEvidenceMaterializationVerdict"
            )
        object.__setattr__(
            self,
            "reviewed_at",
            _canonical_time(self.reviewed_at, "reviewed_at"),
        )
        object.__setattr__(
            self,
            "rationale",
            _clean_text(self.rationale, "review rationale"),
        )


def pilot_capture_source_sha256(capture: PilotCaptureRecord) -> str:
    """Return a domain-separated digest of canonical capture-record bytes."""

    if not isinstance(capture, PilotCaptureRecord):
        raise InvalidPilotEvidenceMaterialization("capture must be PilotCaptureRecord")
    digest = hashlib.sha256()
    digest.update(_CAPTURE_HASH_DOMAIN)
    digest.update(pilot_capture_to_json(capture).encode("utf-8"))
    return digest.hexdigest()


def _load_pinned_capture(
    workspace,
    *,
    capture_id: str,
    expected_snapshot_sha256: str | None = None,
) -> tuple[PilotCaptureRecord, str]:
    first = validate_private_workspace(workspace)
    if (
        expected_snapshot_sha256 is not None
        and first.snapshot_sha256 != expected_snapshot_sha256
    ):
        raise InvalidPilotEvidenceMaterialization(
            "private workspace snapshot no longer matches materialization candidate"
        )

    root, manifest, _protocol = load_private_workspace(workspace)
    matches = tuple(
        capture
        for capture in load_capture_set(root).captures
        if capture.capture_id == capture_id
    )
    if len(matches) != 1:
        raise InvalidPilotEvidenceMaterialization(
            f"selected capture id is absent or ambiguous: {capture_id}"
        )
    capture = matches[0]
    if capture.subject_ref != manifest.subject_ref:
        raise InvalidPilotEvidenceMaterialization(
            "selected capture subject does not match workspace manifest"
        )

    second = validate_private_workspace(workspace)
    if first.snapshot_sha256 != second.snapshot_sha256:
        raise InvalidPilotEvidenceMaterialization(
            "private workspace changed while materialization source was read"
        )
    return capture, second.snapshot_sha256


def propose_pilot_capture_evidence_materialization_v1(
    workspace,
    *,
    capture_id: str,
    materialization_id: PilotEvidenceMaterializationId,
    proposed_evidence_id: EvidenceId,
    proposed_at: datetime,
) -> PilotEvidenceMaterializationCandidate:
    """Pin one explicit validated capture as a candidate without creating evidence."""

    proposed = _canonical_time(proposed_at, "proposed_at")
    capture, snapshot_sha256 = _load_pinned_capture(
        workspace,
        capture_id=capture_id,
    )
    if proposed < capture.captured_at:
        raise InvalidPilotEvidenceMaterialization(
            "materialization proposal must not predate the selected capture"
        )

    return PilotEvidenceMaterializationCandidate(
        materialization_id=materialization_id,
        policy_ref=REVIEWED_PILOT_CAPTURE_TO_EVIDENCE_POLICY_V1,
        protocol_ref=capture.protocol_ref,
        session_id=capture.session_id,
        subject_ref=capture.subject_ref,
        capture_id=capture.capture_id,
        probe_id=capture.probe_id,
        capture_kind=capture.capture_kind,
        source_snapshot_sha256=snapshot_sha256,
        source_capture_sha256=pilot_capture_source_sha256(capture),
        proposed_evidence_id=proposed_evidence_id,
        proposed_at=proposed,
    )


def _verify_candidate_source(
    workspace,
    candidate: PilotEvidenceMaterializationCandidate,
) -> PilotCaptureRecord:
    capture, snapshot_sha256 = _load_pinned_capture(
        workspace,
        capture_id=candidate.capture_id,
        expected_snapshot_sha256=candidate.source_snapshot_sha256,
    )
    if snapshot_sha256 != candidate.source_snapshot_sha256:
        raise InvalidPilotEvidenceMaterialization(
            "private workspace snapshot changed after source verification"
        )
    if capture.protocol_ref != candidate.protocol_ref:
        raise InvalidPilotEvidenceMaterialization(
            "candidate protocol_ref does not match capture"
        )
    if capture.session_id != candidate.session_id:
        raise InvalidPilotEvidenceMaterialization(
            "candidate session_id does not match capture"
        )
    if capture.subject_ref != candidate.subject_ref:
        raise InvalidPilotEvidenceMaterialization(
            "candidate subject_ref does not match capture"
        )
    if capture.probe_id != candidate.probe_id:
        raise InvalidPilotEvidenceMaterialization(
            "candidate probe_id does not match capture"
        )
    if capture.capture_kind is not candidate.capture_kind:
        raise InvalidPilotEvidenceMaterialization(
            "candidate capture_kind does not match capture"
        )
    if pilot_capture_source_sha256(capture) != candidate.source_capture_sha256:
        raise InvalidPilotEvidenceMaterialization(
            "candidate source_capture_sha256 does not match exact capture bytes"
        )
    return capture


def _evidence_kind(capture: PilotCaptureRecord) -> EvidenceKind:
    if capture.capture_kind is PilotCaptureKind.FILE_ARTIFACT:
        return EvidenceKind.ARTIFACT
    return EvidenceKind.OTHER


def _evidence_context(capture: PilotCaptureRecord) -> EvidenceContext:
    return EvidenceContext(
        description=(
            f"Exact private Pilot 01 capture under {capture.protocol_ref}; "
            f"session={capture.session_id}; probe={capture.probe_id}; "
            f"capture_kind={capture.capture_kind.value}; origin is declared "
            "SUBJECT_PROVIDED. Source content remains in the private capture "
            "workspace and is not interpreted here."
        ),
        scope_tags=("pilot_capture", capture.probe_id),
        factors=tuple(
            ContextFactor(ContextFactorKind.TOOL, tool)
            for tool in capture.declared_tools
        ),
    )


def resolve_reviewed_pilot_evidence_materialization_v1(
    workspace,
    *,
    candidate: PilotEvidenceMaterializationCandidate,
    review: PilotEvidenceMaterializationReview,
    resolved_at: datetime,
) -> EvidenceRecord | None:
    """Resolve one exact candidate through one explicitly selected human review."""

    if not isinstance(candidate, PilotEvidenceMaterializationCandidate):
        raise InvalidPilotEvidenceMaterialization(
            "candidate must be PilotEvidenceMaterializationCandidate"
        )
    if not isinstance(review, PilotEvidenceMaterializationReview):
        raise InvalidPilotEvidenceMaterialization(
            "review must be PilotEvidenceMaterializationReview"
        )
    resolved = _canonical_time(resolved_at, "resolved_at")
    if review.materialization_id != candidate.materialization_id:
        raise InvalidPilotEvidenceMaterialization(
            "review materialization_id does not match candidate"
        )
    if review.policy_ref != candidate.policy_ref:
        raise InvalidPilotEvidenceMaterialization(
            "review policy_ref does not match candidate"
        )
    expected_candidate_sha256 = pilot_evidence_materialization_candidate_sha256(candidate)
    if review.candidate_sha256 != expected_candidate_sha256:
        raise InvalidPilotEvidenceMaterialization(
            "review candidate_sha256 does not match exact candidate"
        )
    if review.reviewed_at < candidate.proposed_at:
        raise InvalidPilotEvidenceMaterialization(
            "reviewed_at must not precede candidate proposed_at"
        )
    if resolved < review.reviewed_at:
        raise InvalidPilotEvidenceMaterialization(
            "resolved_at must not precede review reviewed_at"
        )

    capture = _verify_candidate_source(workspace, candidate)
    if review.reviewed_at < capture.captured_at:
        raise InvalidPilotEvidenceMaterialization(
            "reviewed_at must not precede selected capture"
        )

    if review.verdict is PilotEvidenceMaterializationVerdict.DO_NOT_MATERIALIZE:
        return None

    source_ref = candidate.source_capture_ref
    return EvidenceRecord(
        evidence_id=candidate.proposed_evidence_id,
        subject_ref=capture.subject_ref,
        kind=_evidence_kind(capture),
        summary=(
            f"Pilot 01 capture for probe '{capture.probe_id}' "
            f"(kind={capture.capture_kind.value}; "
            f"origin declared {capture.origin_kind.value})."
        ),
        context=_evidence_context(capture),
        observed_at=capture.captured_at,
        recorded_at=resolved,
        provenance=ProvenanceTrail(
            sources=(
                ProvenanceSource(
                    ProvenanceSourceKind.EXTERNAL_RECORD,
                    source_ref,
                ),
            ),
            steps=(
                ProvenanceStep(
                    operation_key="pilot_materialize",
                    occurred_at=resolved,
                    actor_ref=ActorRef(review.reviewer_ref.ref),
                    mechanism_ref=str(candidate.policy_ref),
                    note=(
                        f"materialization_id={candidate.materialization_id}; "
                        f"candidate_sha256={review.candidate_sha256}; "
                        f"review_id={review.review_id}"
                    ),
                ),
            ),
        ),
        observation_started_at=None,
        outcome=None,
        payload_refs=(source_ref,),
    )
