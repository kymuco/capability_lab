"""Immutable non-authoritative proposal records for Capability Lab."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import re
import unicodedata

from capability_lab.epistemics import (
    CapabilityClaimId,
    CapabilitySubjectRef,
    ClaimEvaluationId,
    ClaimScope,
    EvidenceId,
)
from capability_lab.semantics import (
    CapabilityConcept,
    CapabilityConceptRef,
    CapabilityId,
    CapabilityRelation,
    ConceptLifecycle,
    RelationKind,
    RelationScope,
    RelationStrength,
)


class ProposalError(ValueError):
    """Base validation error for PR6 proposal records."""


class InvalidProposalId(ProposalError):
    pass


class InvalidProposalError(ProposalError):
    pass


class InvalidProposalReviewError(ProposalError):
    pass


_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_NAMESPACE_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*$")
_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_POLICY_RE = re.compile(
    r"^([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*):([a-z][a-z0-9_]*)@([1-9][0-9]*)$"
)


def _clean_text(value: object, field_name: str, error_type: type[ProposalError]) -> str:
    if not isinstance(value, str):
        raise error_type(f"{field_name} must be a string")
    cleaned = unicodedata.normalize("NFC", value).strip()
    if not cleaned:
        raise error_type(f"{field_name} must be non-empty")
    return cleaned


def _clean_optional_text(
    value: object | None,
    field_name: str,
    error_type: type[ProposalError],
) -> str | None:
    if value is None:
        return None
    return _clean_text(value, field_name, error_type)


def _opaque_id(value: object, field_name: str) -> str:
    if not isinstance(value, str) or _ID_RE.fullmatch(value) is None:
        raise InvalidProposalId(f"{field_name} must be a canonical opaque ASCII identifier")
    return value


def _canonical_time(value: object, field_name: str, error_type: type[ProposalError]) -> datetime:
    if not isinstance(value, datetime):
        raise error_type(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise error_type(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _clean_aliases(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise InvalidProposalError("candidate aliases must be an iterable of strings, not a string")
    try:
        raw = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise InvalidProposalError("candidate aliases must be iterable") from exc
    cleaned = tuple(
        _clean_text(item, "candidate alias", InvalidProposalError) for item in raw
    )
    if len(set(cleaned)) != len(cleaned):
        raise InvalidProposalError("candidate aliases must not contain duplicates")
    return tuple(sorted(cleaned))


def _policy_parts(value: object, field_name: str) -> tuple[str, str, int]:
    if not isinstance(value, str):
        raise InvalidProposalError(f"{field_name} must be a string")
    match = _POLICY_RE.fullmatch(value)
    if match is None:
        raise InvalidProposalError(
            f"{field_name} must use '<namespace>:<key>@<revision>' canonical syntax"
        )
    return match.group(1), match.group(2), int(match.group(3))


@dataclass(frozen=True, order=True, slots=True)
class CapabilityProposalId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _opaque_id(self.value, "proposal id"))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, order=True, slots=True)
class ProposalReviewId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _opaque_id(self.value, "proposal review id"))

    def __str__(self) -> str:
        return self.value


class ProposalMechanismKind(str, Enum):
    HUMAN = "human"
    RULE = "rule"
    MODEL = "model"
    HYBRID = "hybrid"
    EXTERNAL_SYSTEM = "external_system"


@dataclass(frozen=True, order=True, slots=True)
class ProposalGeneratorRef:
    kind: ProposalMechanismKind
    ref: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, ProposalMechanismKind):
            raise InvalidProposalError("generator kind must be ProposalMechanismKind")
        object.__setattr__(self, "ref", _opaque_id(self.ref, "generator ref"))


@dataclass(frozen=True, order=True, slots=True)
class ProposalReviewerRef:
    kind: ProposalMechanismKind
    ref: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, ProposalMechanismKind):
            raise InvalidProposalReviewError("reviewer kind must be ProposalMechanismKind")
        object.__setattr__(self, "ref", _opaque_id(self.ref, "reviewer ref"))


@dataclass(frozen=True, order=True, slots=True)
class ProposalGenerationPolicyRef:
    namespace: str
    key: str
    revision: int

    def __post_init__(self) -> None:
        if not isinstance(self.namespace, str) or _NAMESPACE_RE.fullmatch(self.namespace) is None:
            raise InvalidProposalError("generation policy namespace must use canonical namespace syntax")
        if not isinstance(self.key, str) or _KEY_RE.fullmatch(self.key) is None:
            raise InvalidProposalError("generation policy key must use canonical key syntax")
        if isinstance(self.revision, bool) or not isinstance(self.revision, int) or self.revision < 1:
            raise InvalidProposalError("generation policy revision must be an integer >= 1")

    @classmethod
    def parse(cls, value: object) -> "ProposalGenerationPolicyRef":
        namespace, key, revision = _policy_parts(value, "generation policy ref")
        return cls(namespace, key, revision)

    def __str__(self) -> str:
        return f"{self.namespace}:{self.key}@{self.revision}"


@dataclass(frozen=True, order=True, slots=True)
class ProposalReviewPolicyRef:
    namespace: str
    key: str
    revision: int

    def __post_init__(self) -> None:
        if not isinstance(self.namespace, str) or _NAMESPACE_RE.fullmatch(self.namespace) is None:
            raise InvalidProposalReviewError("review policy namespace must use canonical namespace syntax")
        if not isinstance(self.key, str) or _KEY_RE.fullmatch(self.key) is None:
            raise InvalidProposalReviewError("review policy key must use canonical key syntax")
        if isinstance(self.revision, bool) or not isinstance(self.revision, int) or self.revision < 1:
            raise InvalidProposalReviewError("review policy revision must be an integer >= 1")

    @classmethod
    def parse(cls, value: object) -> "ProposalReviewPolicyRef":
        try:
            namespace, key, revision = _policy_parts(value, "review policy ref")
        except InvalidProposalError as exc:
            raise InvalidProposalReviewError(str(exc)) from exc
        return cls(namespace, key, revision)

    def __str__(self) -> str:
        return f"{self.namespace}:{self.key}@{self.revision}"


class ProposalBasisKind(str, Enum):
    CAPABILITY_CONCEPT = "capability_concept"
    EVIDENCE_RECORD = "evidence_record"
    CAPABILITY_CLAIM = "capability_claim"
    CLAIM_EVALUATION = "claim_evaluation"
    EXTERNAL_ARTIFACT = "external_artifact"
    OTHER = "other"


@dataclass(frozen=True, order=True, slots=True)
class ProposalBasisRef:
    kind: ProposalBasisKind
    ref: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, ProposalBasisKind):
            raise InvalidProposalError("proposal basis kind must be ProposalBasisKind")
        ref = _clean_text(self.ref, "proposal basis ref", InvalidProposalError)
        try:
            if self.kind is ProposalBasisKind.CAPABILITY_CONCEPT:
                ref = str(CapabilityConceptRef.parse(ref))
            elif self.kind is ProposalBasisKind.EVIDENCE_RECORD:
                ref = str(EvidenceId(ref))
            elif self.kind is ProposalBasisKind.CAPABILITY_CLAIM:
                ref = str(CapabilityClaimId(ref))
            elif self.kind is ProposalBasisKind.CLAIM_EVALUATION:
                ref = str(ClaimEvaluationId(ref))
        except ValueError as exc:
            raise InvalidProposalError(f"invalid {self.kind.value} basis ref: {ref!r}") from exc
        object.__setattr__(self, "ref", ref)


@dataclass(frozen=True, slots=True)
class ConceptCandidateSpec:
    suggested_capability_id: CapabilityId
    name: str
    definition: str
    aliases: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.suggested_capability_id, CapabilityId):
            raise InvalidProposalError("suggested_capability_id must be CapabilityId")
        aliases = _clean_aliases(self.aliases)
        try:
            validated = CapabilityConcept(
                capability_id=self.suggested_capability_id,
                name=self.name,
                definition=self.definition,
                aliases=aliases,
                revision=1,
            )
        except ValueError as exc:
            raise InvalidProposalError(f"invalid concept candidate: {exc}") from exc
        object.__setattr__(self, "name", validated.name)
        object.__setattr__(self, "definition", validated.definition)
        object.__setattr__(self, "aliases", validated.aliases)


@dataclass(frozen=True, slots=True)
class ConceptCreateCandidate:
    proposed: ConceptCandidateSpec

    def __post_init__(self) -> None:
        if not isinstance(self.proposed, ConceptCandidateSpec):
            raise InvalidProposalError("create-concept candidate requires ConceptCandidateSpec")


@dataclass(frozen=True, slots=True)
class ConceptRevisionCandidate:
    target_ref: CapabilityConceptRef
    proposed_name: str
    proposed_definition: str
    proposed_aliases: tuple[str, ...] = ()
    proposed_lifecycle: ConceptLifecycle = ConceptLifecycle.ACTIVE
    deprecation_note: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.target_ref, CapabilityConceptRef):
            raise InvalidProposalError("revision target_ref must be exact CapabilityConceptRef")
        if not isinstance(self.proposed_lifecycle, ConceptLifecycle):
            raise InvalidProposalError("proposed_lifecycle must be ConceptLifecycle")
        aliases = _clean_aliases(self.proposed_aliases)
        try:
            validated = CapabilityConcept(
                capability_id=self.target_ref.capability_id,
                name=self.proposed_name,
                definition=self.proposed_definition,
                aliases=aliases,
                revision=self.target_ref.revision,
                lifecycle=self.proposed_lifecycle,
                deprecation_note=self.deprecation_note,
            )
        except ValueError as exc:
            raise InvalidProposalError(f"invalid concept revision candidate: {exc}") from exc
        object.__setattr__(self, "proposed_name", validated.name)
        object.__setattr__(self, "proposed_definition", validated.definition)
        object.__setattr__(self, "proposed_aliases", validated.aliases)
        object.__setattr__(self, "deprecation_note", validated.deprecation_note)


@dataclass(frozen=True, slots=True)
class ConceptSplitCandidate:
    source_ref: CapabilityConceptRef
    outputs: tuple[ConceptCandidateSpec, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.source_ref, CapabilityConceptRef):
            raise InvalidProposalError("split source_ref must be exact CapabilityConceptRef")
        if isinstance(self.outputs, (str, bytes)):
            raise InvalidProposalError("split outputs must be an iterable")
        try:
            outputs = tuple(self.outputs)
        except TypeError as exc:
            raise InvalidProposalError("split outputs must be iterable") from exc
        if len(outputs) < 2 or any(not isinstance(item, ConceptCandidateSpec) for item in outputs):
            raise InvalidProposalError("split requires at least two ConceptCandidateSpec outputs")
        output_ids = [item.suggested_capability_id for item in outputs]
        if len(set(output_ids)) != len(output_ids):
            raise InvalidProposalError("split output suggested ids must be unique")
        if self.source_ref.capability_id in output_ids:
            raise InvalidProposalError("split output suggested id must not reuse source capability id")
        object.__setattr__(
            self,
            "outputs",
            tuple(sorted(outputs, key=lambda item: item.suggested_capability_id)),
        )


@dataclass(frozen=True, slots=True)
class ConceptMergeCandidate:
    source_refs: tuple[CapabilityConceptRef, ...]
    output: ConceptCandidateSpec

    def __post_init__(self) -> None:
        if isinstance(self.source_refs, (str, bytes)):
            raise InvalidProposalError("merge source_refs must be an iterable")
        try:
            refs = tuple(self.source_refs)
        except TypeError as exc:
            raise InvalidProposalError("merge source_refs must be iterable") from exc
        if len(refs) < 2 or any(not isinstance(item, CapabilityConceptRef) for item in refs):
            raise InvalidProposalError("merge requires at least two exact CapabilityConceptRef values")
        source_ids = [item.capability_id for item in refs]
        if len(set(source_ids)) != len(source_ids):
            raise InvalidProposalError("merge sources must identify distinct capability lineages")
        if not isinstance(self.output, ConceptCandidateSpec):
            raise InvalidProposalError("merge output must be ConceptCandidateSpec")
        if self.output.suggested_capability_id in set(source_ids):
            raise InvalidProposalError("merge output suggested id must not reuse a source capability id")
        object.__setattr__(self, "source_refs", tuple(sorted(refs, key=str)))


@dataclass(frozen=True, slots=True)
class RelationCreateCandidate:
    source_ref: CapabilityConceptRef
    target_ref: CapabilityConceptRef
    kind: RelationKind
    scope: RelationScope | None = None
    strength: RelationStrength = RelationStrength.UNSPECIFIED
    provenance_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.source_ref, CapabilityConceptRef):
            raise InvalidProposalError("relation source_ref must be exact CapabilityConceptRef")
        if not isinstance(self.target_ref, CapabilityConceptRef):
            raise InvalidProposalError("relation target_ref must be exact CapabilityConceptRef")
        try:
            validated = CapabilityRelation(
                source_id=self.source_ref.capability_id,
                target_id=self.target_ref.capability_id,
                kind=self.kind,
                scope=self.scope,
                strength=self.strength,
                provenance_refs=self.provenance_refs,
            )
        except ValueError as exc:
            raise InvalidProposalError(f"invalid relation candidate: {exc}") from exc
        source_ref, target_ref = self.source_ref, self.target_ref
        if validated.source_id != source_ref.capability_id:
            source_ref, target_ref = target_ref, source_ref
        object.__setattr__(self, "source_ref", source_ref)
        object.__setattr__(self, "target_ref", target_ref)
        object.__setattr__(self, "scope", validated.scope)
        object.__setattr__(self, "strength", validated.strength)
        object.__setattr__(self, "provenance_refs", validated.provenance_refs)

    @property
    def semantic_key(self) -> tuple[str, str, str, str]:
        return (
            str(self.source_ref.capability_id),
            self.kind.value,
            str(self.target_ref.capability_id),
            self.scope.key if self.scope else "",
        )


@dataclass(frozen=True, slots=True)
class ClaimCreateCandidate:
    concept_ref: CapabilityConceptRef
    statement: str
    scope: ClaimScope

    def __post_init__(self) -> None:
        if not isinstance(self.concept_ref, CapabilityConceptRef):
            raise InvalidProposalError("claim candidate concept_ref must be exact CapabilityConceptRef")
        if not isinstance(self.scope, ClaimScope):
            raise InvalidProposalError("claim candidate scope must be ClaimScope")
        object.__setattr__(
            self,
            "statement",
            _clean_text(self.statement, "claim candidate statement", InvalidProposalError),
        )


class ProposalKind(str, Enum):
    CREATE_CONCEPT = "create_concept"
    REVISE_CONCEPT = "revise_concept"
    SPLIT_CONCEPT = "split_concept"
    MERGE_CONCEPTS = "merge_concepts"
    CREATE_RELATION = "create_relation"
    CREATE_CLAIM = "create_claim"


ProposalPayload = (
    ConceptCreateCandidate
    | ConceptRevisionCandidate
    | ConceptSplitCandidate
    | ConceptMergeCandidate
    | RelationCreateCandidate
    | ClaimCreateCandidate
)

_PAYLOAD_TYPE_BY_KIND: dict[ProposalKind, type] = {
    ProposalKind.CREATE_CONCEPT: ConceptCreateCandidate,
    ProposalKind.REVISE_CONCEPT: ConceptRevisionCandidate,
    ProposalKind.SPLIT_CONCEPT: ConceptSplitCandidate,
    ProposalKind.MERGE_CONCEPTS: ConceptMergeCandidate,
    ProposalKind.CREATE_RELATION: RelationCreateCandidate,
    ProposalKind.CREATE_CLAIM: ClaimCreateCandidate,
}


@dataclass(frozen=True, slots=True)
class CapabilityProposal:
    proposal_id: CapabilityProposalId
    kind: ProposalKind
    payload: ProposalPayload
    subject_ref: CapabilitySubjectRef | None
    generator_ref: ProposalGeneratorRef
    generation_policy_ref: ProposalGenerationPolicyRef
    created_at: datetime
    rationale: str
    basis_refs: tuple[ProposalBasisRef, ...] = ()
    supersedes_proposal_id: CapabilityProposalId | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.proposal_id, CapabilityProposalId):
            raise InvalidProposalError("proposal_id must be CapabilityProposalId")
        if not isinstance(self.kind, ProposalKind):
            raise InvalidProposalError("kind must be ProposalKind")
        expected_type = _PAYLOAD_TYPE_BY_KIND[self.kind]
        if not isinstance(self.payload, expected_type):
            raise InvalidProposalError(
                f"proposal kind {self.kind.value!r} requires payload {expected_type.__name__}"
            )
        if self.subject_ref is not None and not isinstance(self.subject_ref, CapabilitySubjectRef):
            raise InvalidProposalError("subject_ref must be CapabilitySubjectRef or None")
        if self.kind is ProposalKind.CREATE_CLAIM and self.subject_ref is None:
            raise InvalidProposalError("claim proposals are person-scoped and require subject_ref")
        if not isinstance(self.generator_ref, ProposalGeneratorRef):
            raise InvalidProposalError("generator_ref must be ProposalGeneratorRef")
        if not isinstance(self.generation_policy_ref, ProposalGenerationPolicyRef):
            raise InvalidProposalError("generation_policy_ref must be ProposalGenerationPolicyRef")
        if self.supersedes_proposal_id is not None and not isinstance(
            self.supersedes_proposal_id, CapabilityProposalId
        ):
            raise InvalidProposalError("supersedes_proposal_id must be CapabilityProposalId or None")
        if self.supersedes_proposal_id == self.proposal_id:
            raise InvalidProposalError("proposal may not supersede itself")
        if isinstance(self.basis_refs, (str, bytes)):
            raise InvalidProposalError("basis_refs must be an iterable")
        try:
            basis_refs = tuple(self.basis_refs)
        except TypeError as exc:
            raise InvalidProposalError("basis_refs must be iterable") from exc
        if any(not isinstance(item, ProposalBasisRef) for item in basis_refs):
            raise InvalidProposalError("basis_refs must contain ProposalBasisRef values")
        if len(set(basis_refs)) != len(basis_refs):
            raise InvalidProposalError("basis_refs must not contain duplicates")
        object.__setattr__(self, "basis_refs", tuple(sorted(basis_refs)))
        object.__setattr__(
            self,
            "created_at",
            _canonical_time(self.created_at, "proposal created_at", InvalidProposalError),
        )
        object.__setattr__(
            self,
            "rationale",
            _clean_text(self.rationale, "proposal rationale", InvalidProposalError),
        )

    @property
    def is_person_scoped(self) -> bool:
        return self.subject_ref is not None


class ProposalReviewVerdict(str, Enum):
    RECOMMEND_ACCEPT = "recommend_accept"
    RECOMMEND_REJECT = "recommend_reject"
    REQUEST_REVISION = "request_revision"
    ABSTAIN = "abstain"


@dataclass(frozen=True, slots=True)
class ProposalReview:
    review_id: ProposalReviewId
    proposal_id: CapabilityProposalId
    reviewer_ref: ProposalReviewerRef
    review_policy_ref: ProposalReviewPolicyRef
    reviewed_at: datetime
    verdict: ProposalReviewVerdict
    rationale: str

    def __post_init__(self) -> None:
        if not isinstance(self.review_id, ProposalReviewId):
            raise InvalidProposalReviewError("review_id must be ProposalReviewId")
        if not isinstance(self.proposal_id, CapabilityProposalId):
            raise InvalidProposalReviewError("proposal_id must be CapabilityProposalId")
        if not isinstance(self.reviewer_ref, ProposalReviewerRef):
            raise InvalidProposalReviewError("reviewer_ref must be ProposalReviewerRef")
        if not isinstance(self.review_policy_ref, ProposalReviewPolicyRef):
            raise InvalidProposalReviewError("review_policy_ref must be ProposalReviewPolicyRef")
        if not isinstance(self.verdict, ProposalReviewVerdict):
            raise InvalidProposalReviewError("verdict must be ProposalReviewVerdict")
        object.__setattr__(
            self,
            "reviewed_at",
            _canonical_time(self.reviewed_at, "reviewed_at", InvalidProposalReviewError),
        )
        object.__setattr__(
            self,
            "rationale",
            _clean_text(self.rationale, "review rationale", InvalidProposalReviewError),
        )
