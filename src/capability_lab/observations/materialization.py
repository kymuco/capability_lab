"""PR12.1 reviewed external-observation to neutral-evidence materialization v1."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import re
import unicodedata

from capability_lab.epistemics import (
    ActorRef, CapabilitySubjectRef, ContextFactor, ContextFactorKind,
    EvidenceContext, EvidenceId, EvidenceKind, EvidenceRecord,
    ProvenanceSource, ProvenanceSourceKind, ProvenanceStep, ProvenanceTrail,
)
from .core import (
    ExternalObservationEnvelope, ExternalObservationError, ExternalObservationForm,
    ExternalObservationId, ExternalObservationLedger, ExternalObservationOriginKind,
    ExternalObservationSourceRef, external_observation_sha256_v1,
    validate_external_observation_ledger_v1,
)

class ExternalObservationEvidenceMaterializationError(ExternalObservationError):
    """Base error for PR12.1 reviewed external-observation materialization."""

class InvalidExternalObservationEvidenceMaterialization(
    ExternalObservationEvidenceMaterializationError
):
    pass

_OPAQUE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_NAMESPACE_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*$")
_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_CANDIDATE_HASH_DOMAIN = b"capability_lab/external_observation_evidence_candidate@1\x00"

def _fail(message: str) -> None:
    raise InvalidExternalObservationEvidenceMaterialization(message)

def _exact(value: object, expected: type, label: str):
    if type(value) is not expected:
        _fail(f"{label} must use exact type {expected.__name__}")
    return value

def _opaque_id(value: object, label: str) -> str:
    if type(value) is not str or _OPAQUE_ID_RE.fullmatch(value) is None:
        _fail(f"{label} must be a canonical opaque ASCII identifier")
    return value

def _sha256(value: object, label: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        _fail(f"{label} must be 64 lowercase hexadecimal SHA-256 characters")
    return value

def _text(value: object, label: str) -> str:
    if type(value) is not str:
        _fail(f"{label} must be a string")
    cleaned = unicodedata.normalize("NFC", value).strip()
    if not cleaned:
        _fail(f"{label} must be non-empty")
    return cleaned

def _time(value: object, label: str) -> datetime:
    if type(value) is not datetime:
        _fail(f"{label} must use exact datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        _fail(f"{label} must be timezone-aware")
    return value.astimezone(timezone.utc)

@dataclass(frozen=True, order=True, slots=True)
class ExternalObservationEvidenceMaterializationId:
    value: str
    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _opaque_id(self.value, "materialization id"))
    def __str__(self) -> str:
        return self.value

@dataclass(frozen=True, order=True, slots=True)
class ExternalObservationEvidenceReviewId:
    value: str
    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _opaque_id(self.value, "review id"))
    def __str__(self) -> str:
        return self.value

@dataclass(frozen=True, order=True, slots=True)
class ExternalObservationEvidenceMaterializationPolicyRef:
    namespace: str
    key: str
    revision: int
    def __post_init__(self) -> None:
        if type(self.namespace) is not str or _NAMESPACE_RE.fullmatch(self.namespace) is None:
            _fail("policy namespace must use canonical syntax")
        if type(self.key) is not str or _KEY_RE.fullmatch(self.key) is None:
            _fail("policy key must use canonical syntax")
        if type(self.revision) is not int or self.revision < 1:
            _fail("policy revision must be an integer >= 1")
    @classmethod
    def parse(cls, value: object):
        if type(value) is not str:
            _fail("policy ref must be a string")
        match = re.fullmatch(
            r"([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*):([a-z][a-z0-9_]*)@([1-9][0-9]*)",
            value,
        )
        if match is None:
            _fail("policy ref must use '<namespace>:<key>@<revision>'")
        return cls(match.group(1), match.group(2), int(match.group(3)))
    def __str__(self) -> str:
        return f"{self.namespace}:{self.key}@{self.revision}"

REVIEWED_EXTERNAL_OBSERVATION_TO_EVIDENCE_POLICY_V1 = (
    ExternalObservationEvidenceMaterializationPolicyRef(
        "capability_lab", "reviewed_external_observation_to_evidence", 1
    )
)

class ExternalObservationEvidenceReviewerKind(str, Enum):
    HUMAN = "HUMAN"

@dataclass(frozen=True, order=True, slots=True)
class ExternalObservationEvidenceReviewerRef:
    kind: ExternalObservationEvidenceReviewerKind
    ref: str
    def __post_init__(self) -> None:
        _exact(self.kind, ExternalObservationEvidenceReviewerKind, "reviewer kind")
        if self.kind is not ExternalObservationEvidenceReviewerKind.HUMAN:
            _fail("PR12.1 v1 requires an explicitly declared human reviewer")
        object.__setattr__(self, "ref", _opaque_id(self.ref, "reviewer ref"))

class ExternalObservationEvidenceMaterializationVerdict(str, Enum):
    MATERIALIZE = "MATERIALIZE"
    DO_NOT_MATERIALIZE = "DO_NOT_MATERIALIZE"

@dataclass(frozen=True, slots=True)
class ExternalObservationEvidenceMaterializationCandidate:
    materialization_id: ExternalObservationEvidenceMaterializationId
    policy_ref: ExternalObservationEvidenceMaterializationPolicyRef
    observation_id: ExternalObservationId
    observation_sha256: str
    subject_ref: CapabilitySubjectRef
    source_ref: ExternalObservationSourceRef
    source_event_id: str
    form: ExternalObservationForm
    origin_kind: ExternalObservationOriginKind
    materialized_evidence_id: EvidenceId
    proposed_at: datetime
    def __post_init__(self) -> None:
        _exact(self.materialization_id, ExternalObservationEvidenceMaterializationId, "materialization_id")
        if self.policy_ref != REVIEWED_EXTERNAL_OBSERVATION_TO_EVIDENCE_POLICY_V1:
            _fail("candidate must use the frozen PR12.1 policy")
        _exact(self.observation_id, ExternalObservationId, "observation_id")
        object.__setattr__(self, "observation_sha256", _sha256(self.observation_sha256, "observation_sha256"))
        _exact(self.subject_ref, CapabilitySubjectRef, "subject_ref")
        _exact(self.source_ref, ExternalObservationSourceRef, "source_ref")
        object.__setattr__(self, "source_event_id", _opaque_id(self.source_event_id, "source_event_id"))
        _exact(self.form, ExternalObservationForm, "form")
        _exact(self.origin_kind, ExternalObservationOriginKind, "origin_kind")
        _exact(self.materialized_evidence_id, EvidenceId, "materialized_evidence_id")
        object.__setattr__(self, "proposed_at", _time(self.proposed_at, "proposed_at"))

@dataclass(frozen=True, slots=True)
class ExternalObservationEvidenceMaterializationReview:
    review_id: ExternalObservationEvidenceReviewId
    materialization_id: ExternalObservationEvidenceMaterializationId
    candidate_sha256: str
    policy_ref: ExternalObservationEvidenceMaterializationPolicyRef
    reviewer_ref: ExternalObservationEvidenceReviewerRef
    verdict: ExternalObservationEvidenceMaterializationVerdict
    reviewed_at: datetime
    rationale: str
    def __post_init__(self) -> None:
        _exact(self.review_id, ExternalObservationEvidenceReviewId, "review_id")
        _exact(self.materialization_id, ExternalObservationEvidenceMaterializationId, "materialization_id")
        object.__setattr__(self, "candidate_sha256", _sha256(self.candidate_sha256, "candidate_sha256"))
        if self.policy_ref != REVIEWED_EXTERNAL_OBSERVATION_TO_EVIDENCE_POLICY_V1:
            _fail("review must use the frozen PR12.1 policy")
        _exact(self.reviewer_ref, ExternalObservationEvidenceReviewerRef, "reviewer_ref")
        _exact(self.verdict, ExternalObservationEvidenceMaterializationVerdict, "verdict")
        object.__setattr__(self, "reviewed_at", _time(self.reviewed_at, "reviewed_at"))
        object.__setattr__(self, "rationale", _text(self.rationale, "review rationale"))

def _strict_candidate(candidate: ExternalObservationEvidenceMaterializationCandidate):
    if type(candidate) is not ExternalObservationEvidenceMaterializationCandidate:
        _fail("candidate must use exact ExternalObservationEvidenceMaterializationCandidate")
    try:
        restored = ExternalObservationEvidenceMaterializationCandidate(
            materialization_id=ExternalObservationEvidenceMaterializationId(candidate.materialization_id.value),
            policy_ref=ExternalObservationEvidenceMaterializationPolicyRef(
                candidate.policy_ref.namespace, candidate.policy_ref.key, candidate.policy_ref.revision
            ),
            observation_id=ExternalObservationId(candidate.observation_id.value),
            observation_sha256=candidate.observation_sha256,
            subject_ref=CapabilitySubjectRef(candidate.subject_ref.value),
            source_ref=ExternalObservationSourceRef(candidate.source_ref.kind, candidate.source_ref.ref),
            source_event_id=candidate.source_event_id,
            form=ExternalObservationForm(candidate.form.value),
            origin_kind=ExternalObservationOriginKind(candidate.origin_kind.value),
            materialized_evidence_id=EvidenceId(candidate.materialized_evidence_id.value),
            proposed_at=candidate.proposed_at,
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InvalidExternalObservationEvidenceMaterialization):
            raise
        raise InvalidExternalObservationEvidenceMaterialization(
            f"candidate failed strict semantic reconstruction: {exc}"
        ) from exc
    if restored != candidate:
        _fail("candidate must equal strict semantic reconstruction")
    return candidate

def _strict_review(review: ExternalObservationEvidenceMaterializationReview):
    if type(review) is not ExternalObservationEvidenceMaterializationReview:
        _fail("review must use exact ExternalObservationEvidenceMaterializationReview")
    try:
        restored = ExternalObservationEvidenceMaterializationReview(
            review_id=ExternalObservationEvidenceReviewId(review.review_id.value),
            materialization_id=ExternalObservationEvidenceMaterializationId(review.materialization_id.value),
            candidate_sha256=review.candidate_sha256,
            policy_ref=ExternalObservationEvidenceMaterializationPolicyRef(
                review.policy_ref.namespace, review.policy_ref.key, review.policy_ref.revision
            ),
            reviewer_ref=ExternalObservationEvidenceReviewerRef(
                ExternalObservationEvidenceReviewerKind(review.reviewer_ref.kind.value),
                review.reviewer_ref.ref,
            ),
            verdict=ExternalObservationEvidenceMaterializationVerdict(review.verdict.value),
            reviewed_at=review.reviewed_at,
            rationale=review.rationale,
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InvalidExternalObservationEvidenceMaterialization):
            raise
        raise InvalidExternalObservationEvidenceMaterialization(
            f"review failed strict semantic reconstruction: {exc}"
        ) from exc
    if restored != review:
        _fail("review must equal strict semantic reconstruction")
    return review

def external_observation_evidence_id_v1(observation: ExternalObservationEnvelope) -> EvidenceId:
    """Return the sole deterministic EvidenceId for one exact PR12.0 observation."""
    try:
        digest = external_observation_sha256_v1(observation)
        return EvidenceId(f"external_observation:{digest}")
    except (TypeError, ValueError) as exc:
        raise InvalidExternalObservationEvidenceMaterialization(
            f"cannot derive deterministic evidence id: {exc}"
        ) from exc

def external_observation_evidence_materialization_candidate_sha256_v1(
    candidate: ExternalObservationEvidenceMaterializationCandidate,
) -> str:
    _strict_candidate(candidate)
    from .materialization_serialization import external_observation_evidence_candidate_to_json
    digest = hashlib.sha256()
    digest.update(_CANDIDATE_HASH_DOMAIN)
    digest.update(external_observation_evidence_candidate_to_json(candidate).encode("utf-8"))
    return digest.hexdigest()

def _find_admitted_observation(
    *, ledger: ExternalObservationLedger, observation_id: ExternalObservationId
) -> ExternalObservationEnvelope:
    try:
        validate_external_observation_ledger_v1(ledger)
    except (TypeError, ValueError) as exc:
        raise InvalidExternalObservationEvidenceMaterialization(
            f"invalid PR12.0 observation ledger: {exc}"
        ) from exc
    if type(observation_id) is not ExternalObservationId:
        _fail("observation_id must use exact ExternalObservationId")
    matches = tuple(item for item in ledger.observations if item.observation_id == observation_id)
    if len(matches) != 1:
        _fail("selected observation_id is absent or ambiguous in admitted ledger")
    return matches[0]

def propose_external_observation_evidence_materialization_v1(
    *,
    ledger: ExternalObservationLedger,
    observation_id: ExternalObservationId,
    materialization_id: ExternalObservationEvidenceMaterializationId,
    proposed_at: datetime,
) -> ExternalObservationEvidenceMaterializationCandidate:
    """Pin one admitted observation without creating PR2 evidence."""
    observation = _find_admitted_observation(ledger=ledger, observation_id=observation_id)
    proposed = _time(proposed_at, "proposed_at")
    if proposed < observation.captured_at:
        _fail("materialization proposal must not predate observation captured_at")
    try:
        return ExternalObservationEvidenceMaterializationCandidate(
            materialization_id=materialization_id,
            policy_ref=REVIEWED_EXTERNAL_OBSERVATION_TO_EVIDENCE_POLICY_V1,
            observation_id=observation.observation_id,
            observation_sha256=external_observation_sha256_v1(observation),
            subject_ref=observation.subject_ref,
            source_ref=observation.source_ref,
            source_event_id=observation.source_event_id,
            form=observation.form,
            origin_kind=observation.origin_kind,
            materialized_evidence_id=external_observation_evidence_id_v1(observation),
            proposed_at=proposed,
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InvalidExternalObservationEvidenceMaterialization):
            raise
        raise InvalidExternalObservationEvidenceMaterialization(
            f"cannot propose materialization: {exc}"
        ) from exc

def _verify_candidate_source(
    *, ledger: ExternalObservationLedger,
    candidate: ExternalObservationEvidenceMaterializationCandidate,
) -> ExternalObservationEnvelope:
    _strict_candidate(candidate)
    observation = _find_admitted_observation(
        ledger=ledger, observation_id=candidate.observation_id
    )
    try:
        digest = external_observation_sha256_v1(observation)
    except (TypeError, ValueError) as exc:
        raise InvalidExternalObservationEvidenceMaterialization(
            f"cannot hash admitted observation: {exc}"
        ) from exc
    if digest != candidate.observation_sha256:
        _fail("candidate observation_sha256 does not match admitted observation")
    if observation.subject_ref != candidate.subject_ref:
        _fail("candidate subject_ref does not match admitted observation")
    if observation.source_ref != candidate.source_ref:
        _fail("candidate source_ref does not match admitted observation")
    if observation.source_event_id != candidate.source_event_id:
        _fail("candidate source_event_id does not match admitted observation")
    if observation.form is not candidate.form:
        _fail("candidate form does not match admitted observation")
    if observation.origin_kind is not candidate.origin_kind:
        _fail("candidate origin_kind does not match admitted observation")
    if candidate.materialized_evidence_id != external_observation_evidence_id_v1(observation):
        _fail("candidate materialized_evidence_id is not the deterministic observation evidence id")
    if candidate.proposed_at < observation.captured_at:
        _fail("candidate proposed_at must not predate observation captured_at")
    return observation

def _evidence_kind(observation: ExternalObservationEnvelope) -> EvidenceKind:
    if observation.form is ExternalObservationForm.ARTIFACT:
        return EvidenceKind.ARTIFACT
    if observation.form is ExternalObservationForm.CONVERSATION:
        return EvidenceKind.CONVERSATION_OBSERVATION
    return EvidenceKind.OTHER

def _expected_summary(observation: ExternalObservationEnvelope) -> str:
    return (
        f"External observation '{observation.observation_id}' from "
        f"{observation.source_ref.kind.value}:{observation.source_ref.ref} "
        f"(form={observation.form.value}; origin declared {observation.origin_kind.value})."
    )

def _expected_context_description(observation: ExternalObservationEnvelope) -> str:
    return (
        f"Exact external observation '{observation.observation_id}'; "
        f"source={observation.source_ref.kind.value}:{observation.source_ref.ref}; "
        f"source_event={observation.source_event_id}; form={observation.form.value}; "
        f"origin declared {observation.origin_kind.value}. "
        "Source and origin metadata are declared, not authenticated. "
        "Payload content remains external and is not interpreted by this materialization."
    )

def _evidence_context(observation: ExternalObservationEnvelope) -> EvidenceContext:
    return EvidenceContext(
        description=_expected_context_description(observation),
        scope_tags=("external_observation",),
        factors=tuple(
            ContextFactor(ContextFactorKind(item.kind.value), item.description)
            for item in observation.context_factors
        ),
    )

def _build_neutral_evidence(
    *,
    observation: ExternalObservationEnvelope,
    candidate: ExternalObservationEvidenceMaterializationCandidate,
    review: ExternalObservationEvidenceMaterializationReview,
    recorded_at: datetime,
) -> EvidenceRecord:
    candidate_sha256 = external_observation_evidence_materialization_candidate_sha256_v1(candidate)
    source_ref = f"external_observation:{candidate.observation_sha256}"
    note = (
        f"materialization_id={candidate.materialization_id}; "
        f"candidate_sha256={candidate_sha256}; review_id={review.review_id}; "
        f"observation_id={candidate.observation_id}; "
        f"observation_sha256={candidate.observation_sha256}"
    )
    try:
        return EvidenceRecord(
            evidence_id=candidate.materialized_evidence_id,
            subject_ref=observation.subject_ref,
            kind=_evidence_kind(observation),
            summary=_expected_summary(observation),
            context=_evidence_context(observation),
            observed_at=observation.observed_at,
            recorded_at=recorded_at,
            provenance=ProvenanceTrail(
                sources=(ProvenanceSource(ProvenanceSourceKind.EXTERNAL_RECORD, source_ref),),
                steps=(ProvenanceStep(
                    operation_key="external_observation_materialize",
                    occurred_at=recorded_at,
                    actor_ref=ActorRef(review.reviewer_ref.ref),
                    mechanism_ref=str(candidate.policy_ref),
                    note=note,
                ),),
            ),
            observation_started_at=observation.observation_started_at,
            outcome=None,
            payload_refs=tuple(item.ref for item in observation.payload_refs),
        )
    except (TypeError, ValueError) as exc:
        raise InvalidExternalObservationEvidenceMaterialization(
            f"neutral PR2 EvidenceRecord construction failed: {exc}"
        ) from exc
