"""Core person-scoped epistemic records for Capability Lab."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import re
import unicodedata

from capability_lab.semantics import CapabilityConceptRef


class EpistemicError(ValueError):
    """Base validation error for PR2 epistemic records."""


class InvalidEpistemicId(EpistemicError):
    pass


class InvalidEvidenceError(EpistemicError):
    pass


class InvalidClaimError(EpistemicError):
    pass


class InvalidEvaluationError(EpistemicError):
    pass


class InvalidProvenanceError(EpistemicError):
    pass


_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_NAMESPACE_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*$")
_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_POLICY_RE = re.compile(r"^([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*):([a-z][a-z0-9_]*)@([1-9][0-9]*)$")
_TAG_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_TIME_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]{1,6})?(?:Z|[+-][0-9]{2}:[0-9]{2})$"
)


def _clean_text(value: object, field_name: str, error_type: type[EpistemicError]) -> str:
    if not isinstance(value, str):
        raise error_type(f"{field_name} must be a string")
    cleaned = unicodedata.normalize("NFC", value).strip()
    if not cleaned:
        raise error_type(f"{field_name} must be non-empty")
    return cleaned


def _clean_optional_text(value: object | None, field_name: str, error_type: type[EpistemicError]) -> str | None:
    if value is None:
        return None
    return _clean_text(value, field_name, error_type)


def _opaque_id(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise InvalidEpistemicId(f"{field_name} must be a canonical opaque ASCII identifier")
    return value


def _tuple_of_strings(value: object, field_name: str, error_type: type[EpistemicError], *, tag: bool = False) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise error_type(f"{field_name} must be an iterable of strings, not a string")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise error_type(f"{field_name} must be iterable") from exc
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = _clean_text(item, field_name, error_type)
        if tag and not _TAG_RE.fullmatch(text):
            raise error_type(f"{field_name} values must use lowercase machine-tag syntax")
        if text in seen:
            raise error_type(f"duplicate {field_name} value: {text!r}")
        seen.add(text)
        cleaned.append(text)
    return tuple(sorted(cleaned))


def canonical_time(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise EpistemicError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise EpistemicError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def format_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_time(value: object, field_name: str) -> datetime:
    if not isinstance(value, str):
        raise EpistemicError(f"{field_name} must be an ISO-8601 string")
    if _TIME_RE.fullmatch(value) is None:
        raise EpistemicError(
            f"{field_name} must use extended ISO-8601 with T and an explicit timezone"
        )
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise EpistemicError(f"{field_name} must be valid ISO-8601") from exc
    return canonical_time(parsed, field_name)


@dataclass(frozen=True, order=True, slots=True)
class EvidenceId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _opaque_id(self.value, "evidence id"))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, order=True, slots=True)
class CapabilityClaimId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _opaque_id(self.value, "claim id"))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, order=True, slots=True)
class ClaimEvaluationId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _opaque_id(self.value, "evaluation id"))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, order=True, slots=True)
class CapabilitySubjectRef:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _opaque_id(self.value, "subject ref"))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, order=True, slots=True)
class ActorRef:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _opaque_id(self.value, "actor ref"))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, order=True, slots=True)
class EvaluationPolicyRef:
    namespace: str
    key: str
    revision: int

    def __post_init__(self) -> None:
        if not isinstance(self.namespace, str) or not _NAMESPACE_RE.fullmatch(self.namespace):
            raise InvalidEvaluationError("policy namespace must use canonical namespace syntax")
        if not isinstance(self.key, str) or not _KEY_RE.fullmatch(self.key):
            raise InvalidEvaluationError("policy key must use canonical key syntax")
        if isinstance(self.revision, bool) or not isinstance(self.revision, int) or self.revision < 1:
            raise InvalidEvaluationError("policy revision must be an integer >= 1")

    @classmethod
    def parse(cls, value: object) -> "EvaluationPolicyRef":
        if not isinstance(value, str):
            raise InvalidEvaluationError("policy ref must be a string")
        match = _POLICY_RE.fullmatch(value)
        if match is None:
            raise InvalidEvaluationError("policy ref must use '<namespace>:<key>@<revision>' canonical syntax")
        return cls(match.group(1), match.group(2), int(match.group(3)))

    def __str__(self) -> str:
        return f"{self.namespace}:{self.key}@{self.revision}"


class ContextFactorKind(str, Enum):
    TOOL = "tool"
    ASSISTANCE = "assistance"
    ACCOMMODATION = "accommodation"
    COLLABORATION = "collaboration"
    REFERENCE_MATERIAL = "reference_material"
    AUTOMATION = "automation"
    ENVIRONMENT = "environment"
    OTHER = "other"


@dataclass(frozen=True, order=True, slots=True)
class ContextFactor:
    kind: ContextFactorKind
    description: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, ContextFactorKind):
            raise InvalidEvidenceError("context factor kind must be ContextFactorKind")
        object.__setattr__(self, "description", _clean_text(self.description, "context factor description", InvalidEvidenceError))


@dataclass(frozen=True, slots=True)
class EvidenceContext:
    description: str
    scope_tags: tuple[str, ...] = ()
    factors: tuple[ContextFactor, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "description", _clean_text(self.description, "evidence context description", InvalidEvidenceError))
        object.__setattr__(self, "scope_tags", _tuple_of_strings(self.scope_tags, "scope_tags", InvalidEvidenceError, tag=True))
        if isinstance(self.factors, (str, bytes)):
            raise InvalidEvidenceError("context factors must be an iterable")
        try:
            factors = tuple(self.factors)
        except TypeError as exc:
            raise InvalidEvidenceError("context factors must be iterable") from exc
        if any(not isinstance(item, ContextFactor) for item in factors):
            raise InvalidEvidenceError("context factors must contain ContextFactor values")
        if len(set(factors)) != len(factors):
            raise InvalidEvidenceError("duplicate context factors are not allowed")
        object.__setattr__(self, "factors", tuple(sorted(factors)))


class ProvenanceSourceKind(str, Enum):
    ACTOR = "actor"
    ARTIFACT = "artifact"
    EXTERNAL_RECORD = "external_record"
    SYSTEM = "system"
    EVIDENCE_RECORD = "evidence_record"
    CLAIM = "claim"


@dataclass(frozen=True, order=True, slots=True)
class ProvenanceSource:
    kind: ProvenanceSourceKind
    ref: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, ProvenanceSourceKind):
            raise InvalidProvenanceError("provenance source kind must be ProvenanceSourceKind")
        object.__setattr__(self, "ref", _opaque_id(self.ref, "provenance source ref"))


@dataclass(frozen=True, order=True, slots=True)
class ProvenanceStep:
    operation_key: str
    occurred_at: datetime
    actor_ref: ActorRef | None = None
    mechanism_ref: str | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.operation_key, str) or not _TAG_RE.fullmatch(self.operation_key):
            raise InvalidProvenanceError("provenance operation_key must use machine-tag syntax")
        if self.actor_ref is not None and not isinstance(self.actor_ref, ActorRef):
            raise InvalidProvenanceError("provenance actor_ref must be ActorRef or None")
        object.__setattr__(self, "occurred_at", canonical_time(self.occurred_at, "provenance occurred_at"))
        object.__setattr__(self, "mechanism_ref", _clean_optional_text(self.mechanism_ref, "mechanism_ref", InvalidProvenanceError))
        object.__setattr__(self, "note", _clean_optional_text(self.note, "provenance note", InvalidProvenanceError))


@dataclass(frozen=True, slots=True)
class ProvenanceTrail:
    sources: tuple[ProvenanceSource, ...]
    steps: tuple[ProvenanceStep, ...] = ()

    def __post_init__(self) -> None:
        if isinstance(self.sources, (str, bytes)) or isinstance(self.steps, (str, bytes)):
            raise InvalidProvenanceError("provenance sources/steps must be iterables")
        try:
            sources = tuple(self.sources)
            steps = tuple(self.steps)
        except TypeError as exc:
            raise InvalidProvenanceError("provenance sources/steps must be iterable") from exc
        if not sources:
            raise InvalidProvenanceError("provenance requires at least one source")
        if any(not isinstance(item, ProvenanceSource) for item in sources):
            raise InvalidProvenanceError("provenance sources must contain ProvenanceSource values")
        if any(not isinstance(item, ProvenanceStep) for item in steps):
            raise InvalidProvenanceError("provenance steps must contain ProvenanceStep values")
        if len(set(sources)) != len(sources):
            raise InvalidProvenanceError("duplicate provenance sources are not allowed")
        for previous, current in zip(steps, steps[1:]):
            if current.occurred_at < previous.occurred_at:
                raise InvalidProvenanceError("provenance steps must be ordered by nondecreasing occurred_at")
        object.__setattr__(self, "sources", tuple(sorted(sources)))
        object.__setattr__(self, "steps", steps)


class EvidenceKind(str, Enum):
    SELF_REPORT = "self_report"
    CONVERSATION_OBSERVATION = "conversation_observation"
    QUIZ = "quiz"
    SUPERVISED_EXERCISE = "supervised_exercise"
    ARTIFACT = "artifact"
    PROJECT = "project"
    EXTERNAL_ASSESSMENT = "external_assessment"
    REPEATED_PERFORMANCE = "repeated_performance"
    REAL_WORLD_DEMONSTRATION = "real_world_demonstration"
    OTHER = "other"


class EvidenceOutcomeStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILURE = "failure"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True, slots=True)
class EvidenceOutcome:
    status: EvidenceOutcomeStatus
    description: str

    def __post_init__(self) -> None:
        if not isinstance(self.status, EvidenceOutcomeStatus):
            raise InvalidEvidenceError("evidence outcome status must be EvidenceOutcomeStatus")
        object.__setattr__(self, "description", _clean_text(self.description, "evidence outcome description", InvalidEvidenceError))


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    evidence_id: EvidenceId
    subject_ref: CapabilitySubjectRef
    kind: EvidenceKind
    summary: str
    context: EvidenceContext
    observed_at: datetime
    recorded_at: datetime
    provenance: ProvenanceTrail
    observation_started_at: datetime | None = None
    outcome: EvidenceOutcome | None = None
    payload_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.evidence_id, EvidenceId):
            raise InvalidEvidenceError("evidence_id must be EvidenceId")
        if not isinstance(self.subject_ref, CapabilitySubjectRef):
            raise InvalidEvidenceError("subject_ref must be CapabilitySubjectRef")
        if not isinstance(self.kind, EvidenceKind):
            raise InvalidEvidenceError("kind must be EvidenceKind")
        if not isinstance(self.context, EvidenceContext):
            raise InvalidEvidenceError("context must be EvidenceContext")
        if not isinstance(self.provenance, ProvenanceTrail):
            raise InvalidEvidenceError("provenance must be ProvenanceTrail")
        evidence_id_value = str(self.evidence_id)
        for source in self.provenance.sources:
            if source.kind is ProvenanceSourceKind.CLAIM:
                raise InvalidEvidenceError(
                    "evidence provenance may not depend on CapabilityClaim; claims are interpretations, not source evidence"
                )
            if source.kind is ProvenanceSourceKind.EVIDENCE_RECORD and source.ref == evidence_id_value:
                raise InvalidEvidenceError("evidence may not derive from itself")
        if self.outcome is not None and not isinstance(self.outcome, EvidenceOutcome):
            raise InvalidEvidenceError("outcome must be EvidenceOutcome or None")
        object.__setattr__(self, "summary", _clean_text(self.summary, "evidence summary", InvalidEvidenceError))
        observed = canonical_time(self.observed_at, "observed_at")
        recorded = canonical_time(self.recorded_at, "recorded_at")
        started = None
        if self.observation_started_at is not None:
            started = canonical_time(self.observation_started_at, "observation_started_at")
            if started > observed:
                raise InvalidEvidenceError("observation_started_at must not follow observed_at")
        if self.kind is EvidenceKind.REPEATED_PERFORMANCE and started is None:
            raise InvalidEvidenceError(
                "REPEATED_PERFORMANCE requires observation_started_at to preserve its observation window"
            )
        if recorded < observed:
            raise InvalidEvidenceError("recorded_at must not precede observed_at")
        if any(step.occurred_at > recorded for step in self.provenance.steps):
            raise InvalidEvidenceError(
                "evidence provenance step must not occur after evidence recorded_at"
            )
        object.__setattr__(self, "observation_started_at", started)
        object.__setattr__(self, "observed_at", observed)
        object.__setattr__(self, "recorded_at", recorded)
        object.__setattr__(self, "payload_refs", _tuple_of_strings(self.payload_refs, "payload_refs", InvalidEvidenceError))


@dataclass(frozen=True, slots=True)
class ClaimScope:
    description: str
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "description", _clean_text(self.description, "claim scope description", InvalidClaimError))
        object.__setattr__(self, "tags", _tuple_of_strings(self.tags, "claim scope tags", InvalidClaimError, tag=True))


@dataclass(frozen=True, slots=True)
class CapabilityClaim:
    claim_id: CapabilityClaimId
    subject_ref: CapabilitySubjectRef
    concept_ref: CapabilityConceptRef
    statement: str
    scope: ClaimScope
    created_at: datetime
    provenance: ProvenanceTrail

    def __post_init__(self) -> None:
        if not isinstance(self.claim_id, CapabilityClaimId):
            raise InvalidClaimError("claim_id must be CapabilityClaimId")
        if not isinstance(self.subject_ref, CapabilitySubjectRef):
            raise InvalidClaimError("subject_ref must be CapabilitySubjectRef")
        if not isinstance(self.concept_ref, CapabilityConceptRef):
            raise InvalidClaimError("concept_ref must be exact CapabilityConceptRef, not CapabilityId")
        if not isinstance(self.scope, ClaimScope):
            raise InvalidClaimError("scope must be ClaimScope")
        if not isinstance(self.provenance, ProvenanceTrail):
            raise InvalidClaimError("provenance must be ProvenanceTrail")
        claim_id_value = str(self.claim_id)
        for source in self.provenance.sources:
            if source.kind is ProvenanceSourceKind.EVIDENCE_RECORD:
                raise InvalidClaimError(
                    "claim provenance may not bind EvidenceRecord; evaluated evidence belongs to ClaimEvaluation"
                )
            if source.kind is ProvenanceSourceKind.CLAIM and source.ref == claim_id_value:
                raise InvalidClaimError("claim may not derive from itself")
        object.__setattr__(self, "statement", _clean_text(self.statement, "claim statement", InvalidClaimError))
        created = canonical_time(self.created_at, "claim created_at")
        if any(step.occurred_at > created for step in self.provenance.steps):
            raise InvalidClaimError(
                "claim provenance step must not occur after claim created_at"
            )
        object.__setattr__(self, "created_at", created)


class EvaluatorKind(str, Enum):
    HUMAN = "human"
    RULE = "rule"
    MODEL = "model"
    EXTERNAL_SYSTEM = "external_system"


@dataclass(frozen=True, order=True, slots=True)
class EvaluatorRef:
    kind: EvaluatorKind
    ref: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, EvaluatorKind):
            raise InvalidEvaluationError("evaluator kind must be EvaluatorKind")
        object.__setattr__(self, "ref", _opaque_id(self.ref, "evaluator ref"))


class EvidenceBearing(str, Enum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    INDETERMINATE = "indeterminate"
    NOT_RELEVANT = "not_relevant"


class EvidenceReliability(str, Enum):
    UNASSESSED = "unassessed"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class EvidenceAssessment:
    evidence_id: EvidenceId
    bearing: EvidenceBearing
    reliability: EvidenceReliability
    coverage_note: str
    rationale: str

    def __post_init__(self) -> None:
        if not isinstance(self.evidence_id, EvidenceId):
            raise InvalidEvaluationError("assessment evidence_id must be EvidenceId")
        if not isinstance(self.bearing, EvidenceBearing):
            raise InvalidEvaluationError("assessment bearing must be EvidenceBearing")
        if not isinstance(self.reliability, EvidenceReliability):
            raise InvalidEvaluationError("assessment reliability must be EvidenceReliability")
        object.__setattr__(self, "coverage_note", _clean_text(self.coverage_note, "assessment coverage_note", InvalidEvaluationError))
        object.__setattr__(self, "rationale", _clean_text(self.rationale, "assessment rationale", InvalidEvaluationError))


class CoverageStatus(str, Enum):
    UNASSESSED = "unassessed"
    PARTIAL = "partial"
    SUFFICIENT_FOR_CLAIM = "sufficient_for_claim"


@dataclass(frozen=True, slots=True)
class CoverageAssessment:
    status: CoverageStatus
    notes: str

    def __post_init__(self) -> None:
        if not isinstance(self.status, CoverageStatus):
            raise InvalidEvaluationError("coverage status must be CoverageStatus")
        object.__setattr__(self, "notes", _clean_text(self.notes, "coverage notes", InvalidEvaluationError))


class ConflictStatus(str, Enum):
    NONE = "none"
    RESOLVED_BY_POLICY = "resolved_by_policy"
    UNRESOLVED = "unresolved"


class EvaluationConclusion(str, Enum):
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    MIXED = "mixed"
    INSUFFICIENT = "insufficient"
    ABSTAINED = "abstained"


@dataclass(frozen=True, slots=True)
class ClaimEvaluation:
    evaluation_id: ClaimEvaluationId
    claim_id: CapabilityClaimId
    policy_ref: EvaluationPolicyRef
    evaluator_ref: EvaluatorRef
    evaluated_at: datetime
    evidence_assessments: tuple[EvidenceAssessment, ...]
    coverage: CoverageAssessment
    conflict_status: ConflictStatus
    conclusion: EvaluationConclusion
    rationale: str

    def __post_init__(self) -> None:
        if not isinstance(self.evaluation_id, ClaimEvaluationId):
            raise InvalidEvaluationError("evaluation_id must be ClaimEvaluationId")
        if not isinstance(self.claim_id, CapabilityClaimId):
            raise InvalidEvaluationError("claim_id must be CapabilityClaimId")
        if not isinstance(self.policy_ref, EvaluationPolicyRef):
            raise InvalidEvaluationError("policy_ref must be EvaluationPolicyRef")
        if not isinstance(self.evaluator_ref, EvaluatorRef):
            raise InvalidEvaluationError("evaluator_ref must be EvaluatorRef")
        if not isinstance(self.coverage, CoverageAssessment):
            raise InvalidEvaluationError("coverage must be CoverageAssessment")
        if not isinstance(self.conflict_status, ConflictStatus):
            raise InvalidEvaluationError("conflict_status must be ConflictStatus")
        if not isinstance(self.conclusion, EvaluationConclusion):
            raise InvalidEvaluationError("conclusion must be EvaluationConclusion")
        if isinstance(self.evidence_assessments, (str, bytes)):
            raise InvalidEvaluationError("evidence_assessments must be an iterable")
        try:
            assessments = tuple(self.evidence_assessments)
        except TypeError as exc:
            raise InvalidEvaluationError("evidence_assessments must be iterable") from exc
        if any(not isinstance(item, EvidenceAssessment) for item in assessments):
            raise InvalidEvaluationError("evidence_assessments must contain EvidenceAssessment values")
        ids = [item.evidence_id for item in assessments]
        if len(set(ids)) != len(ids):
            raise InvalidEvaluationError("an evaluation may assess each evidence record at most once")
        object.__setattr__(self, "evidence_assessments", tuple(sorted(assessments, key=lambda item: item.evidence_id)))
        object.__setattr__(self, "evaluated_at", canonical_time(self.evaluated_at, "evaluated_at"))
        object.__setattr__(self, "rationale", _clean_text(self.rationale, "evaluation rationale", InvalidEvaluationError))
        _validate_evaluation_logic(self)


def _validate_evaluation_logic(value: ClaimEvaluation) -> None:
    support = sum(item.bearing is EvidenceBearing.SUPPORTS for item in value.evidence_assessments)
    contradict = sum(item.bearing is EvidenceBearing.CONTRADICTS for item in value.evidence_assessments)
    relevant = sum(item.bearing is not EvidenceBearing.NOT_RELEVANT for item in value.evidence_assessments)
    conflict = support > 0 and contradict > 0

    if not value.evidence_assessments and value.conclusion not in {EvaluationConclusion.INSUFFICIENT, EvaluationConclusion.ABSTAINED}:
        raise InvalidEvaluationError("evaluations without evidence may only be INSUFFICIENT or ABSTAINED")
    if value.coverage.status is CoverageStatus.SUFFICIENT_FOR_CLAIM and relevant == 0:
        raise InvalidEvaluationError(
            "SUFFICIENT_FOR_CLAIM coverage requires at least one relevant evidence assessment"
        )
    if value.conflict_status is ConflictStatus.NONE and conflict:
        raise InvalidEvaluationError("supporting and contradicting evidence requires explicit conflict status")
    if value.conflict_status is ConflictStatus.UNRESOLVED:
        if not conflict or value.conclusion not in {
            EvaluationConclusion.MIXED,
            EvaluationConclusion.INSUFFICIENT,
            EvaluationConclusion.ABSTAINED,
        }:
            raise InvalidEvaluationError(
                "UNRESOLVED conflict requires both support and contradiction with MIXED, INSUFFICIENT, or ABSTAINED conclusion"
            )
    if value.conflict_status is ConflictStatus.RESOLVED_BY_POLICY:
        if not conflict or value.conclusion not in {EvaluationConclusion.SUPPORTED, EvaluationConclusion.CONTRADICTED}:
            raise InvalidEvaluationError("RESOLVED_BY_POLICY requires conflicting evidence and a directional conclusion")
    if value.conclusion is EvaluationConclusion.SUPPORTED and support == 0:
        raise InvalidEvaluationError("SUPPORTED conclusion requires at least one supporting evidence assessment")
    if value.conclusion is EvaluationConclusion.CONTRADICTED and contradict == 0:
        raise InvalidEvaluationError("CONTRADICTED conclusion requires at least one contradicting evidence assessment")
    if value.conclusion is EvaluationConclusion.MIXED and not conflict:
        raise InvalidEvaluationError("MIXED conclusion requires both supporting and contradicting evidence")
