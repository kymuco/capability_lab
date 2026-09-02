"""PR8 progression-frontier advisory projection primitives."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import re
import unicodedata

from capability_lab.epistemics import CapabilitySubjectRef
from capability_lab.epistemics.core import EpistemicError, canonical_time
from capability_lab.semantics import CapabilityConceptRef, RelationKind, RelationScope, RelationStrength
from capability_lab.state import CompetenceFrameRef, DimensionConflictStatus, PersonalCapabilityStateId


class ProgressionError(ValueError):
    """Base validation error for PR8 progression projections."""


class InvalidProgressionId(ProgressionError):
    pass


class InvalidProgressionRequest(ProgressionError):
    pass


class InvalidProgressionFrontier(ProgressionError):
    pass


class InvalidProgressionSet(ProgressionError):
    pass


_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_NAMESPACE_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*$")
_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_REF_RE = re.compile(r"^([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*):([a-z][a-z0-9_]*)@([1-9][0-9]*)$")
_ALLOWED_FRONTIER_RELATIONS = {
    RelationKind.SPECIALIZES,
    RelationKind.REQUIRES,
    RelationKind.SUPPORTED_BY,
    RelationKind.ENABLED_BY,
}


def _clean_text(value: object, field_name: str, error_type: type[ProgressionError]) -> str:
    if not isinstance(value, str):
        raise error_type(f"{field_name} must be a string")
    cleaned = unicodedata.normalize("NFC", value).strip()
    if not cleaned:
        raise error_type(f"{field_name} must be non-empty")
    return cleaned


def _opaque_id(value: object, field_name: str, error_type: type[ProgressionError]) -> str:
    if not isinstance(value, str) or _ID_RE.fullmatch(value) is None:
        raise error_type(f"{field_name} must be a canonical opaque ASCII identifier")
    return value


def _namespace(value: object, field_name: str, error_type: type[ProgressionError]) -> str:
    if not isinstance(value, str) or _NAMESPACE_RE.fullmatch(value) is None:
        raise error_type(f"{field_name} must use canonical namespace syntax")
    return value


def _key(value: object, field_name: str, error_type: type[ProgressionError]) -> str:
    if not isinstance(value, str) or _KEY_RE.fullmatch(value) is None:
        raise error_type(f"{field_name} must use canonical lowercase key syntax")
    return value


def _revision(value: object, field_name: str, error_type: type[ProgressionError]) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise error_type(f"{field_name} must be an integer >= 1")
    return value


def _time(value: object, field_name: str, error_type: type[ProgressionError]) -> datetime:
    try:
        return canonical_time(value, field_name)
    except EpistemicError as exc:
        raise error_type(str(exc)) from exc


def _dimension_keys(value: object, field_name: str, error_type: type[ProgressionError] = InvalidProgressionRequest) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise error_type(f"{field_name} must be an iterable")
    try:
        keys = tuple(value)
    except TypeError as exc:
        raise error_type(f"{field_name} must be iterable") from exc
    if not keys:
        raise error_type(f"{field_name} requires at least one dimension key")
    for key in keys:
        _key(key, field_name, error_type)
    if len(set(keys)) != len(keys):
        raise error_type(f"{field_name} must not contain duplicate dimension keys")
    return tuple(sorted(keys))


@dataclass(frozen=True, order=True, slots=True)
class ProgressionFrontierId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _opaque_id(self.value, "progression frontier id", InvalidProgressionId))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, order=True, slots=True)
class ProgressionPolicyRef:
    namespace: str
    key: str
    revision: int

    def __post_init__(self) -> None:
        _namespace(self.namespace, "progression policy namespace", InvalidProgressionRequest)
        _key(self.key, "progression policy key", InvalidProgressionRequest)
        _revision(self.revision, "progression policy revision", InvalidProgressionRequest)

    @classmethod
    def parse(cls, value: object) -> "ProgressionPolicyRef":
        if not isinstance(value, str):
            raise InvalidProgressionRequest("progression policy ref must be a string")
        match = _REF_RE.fullmatch(value)
        if match is None:
            raise InvalidProgressionRequest("progression policy ref must use '<namespace>:<key>@<revision>'")
        return cls(match.group(1), match.group(2), int(match.group(3)))

    def __str__(self) -> str:
        return f"{self.namespace}:{self.key}@{self.revision}"


class ProgressionMechanismKind(str, Enum):
    HUMAN = "human"
    RULE = "rule"
    MODEL = "model"
    HYBRID = "hybrid"
    EXTERNAL_SYSTEM = "external_system"


@dataclass(frozen=True, order=True, slots=True)
class ProgressionRequesterRef:
    kind: ProgressionMechanismKind
    ref: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, ProgressionMechanismKind):
            raise InvalidProgressionRequest("progression requester kind must be ProgressionMechanismKind")
        object.__setattr__(self, "ref", _opaque_id(self.ref, "progression requester ref", InvalidProgressionRequest))


@dataclass(frozen=True, order=True, slots=True)
class ProgressionDeriverRef:
    kind: ProgressionMechanismKind
    ref: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, ProgressionMechanismKind):
            raise InvalidProgressionFrontier("progression deriver kind must be ProgressionMechanismKind")
        object.__setattr__(self, "ref", _opaque_id(self.ref, "progression deriver ref", InvalidProgressionFrontier))


@dataclass(frozen=True, order=True, slots=True)
class ProgressionFocus:
    concept_ref: CapabilityConceptRef
    rationale: str

    def __post_init__(self) -> None:
        if not isinstance(self.concept_ref, CapabilityConceptRef):
            raise InvalidProgressionRequest("focus concept_ref must be exact CapabilityConceptRef")
        object.__setattr__(self, "rationale", _clean_text(self.rationale, "focus rationale", InvalidProgressionRequest))


@dataclass(frozen=True, order=True, slots=True)
class FrontierSeedBinding:
    state_id: PersonalCapabilityStateId
    dimension_keys: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.state_id, PersonalCapabilityStateId):
            raise InvalidProgressionRequest("seed binding state_id must be PersonalCapabilityStateId")
        object.__setattr__(self, "dimension_keys", _dimension_keys(self.dimension_keys, "seed binding dimension_keys"))


@dataclass(frozen=True, slots=True)
class PrerequisiteCheckBinding:
    target_ref: CapabilityConceptRef
    prerequisite_ref: CapabilityConceptRef
    relation_scope: RelationScope | None
    frame_ref: CompetenceFrameRef
    required_dimension_keys: tuple[str, ...]
    state_id: PersonalCapabilityStateId | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.target_ref, CapabilityConceptRef):
            raise InvalidProgressionRequest("prerequisite binding target_ref must be exact CapabilityConceptRef")
        if not isinstance(self.prerequisite_ref, CapabilityConceptRef):
            raise InvalidProgressionRequest("prerequisite binding prerequisite_ref must be exact CapabilityConceptRef")
        if self.target_ref == self.prerequisite_ref:
            raise InvalidProgressionRequest("prerequisite binding target and prerequisite must differ")
        if self.relation_scope is not None and not isinstance(self.relation_scope, RelationScope):
            raise InvalidProgressionRequest("prerequisite binding relation_scope must be RelationScope or None")
        if not isinstance(self.frame_ref, CompetenceFrameRef):
            raise InvalidProgressionRequest("prerequisite binding frame_ref must be exact CompetenceFrameRef")
        if self.state_id is not None and not isinstance(self.state_id, PersonalCapabilityStateId):
            raise InvalidProgressionRequest("prerequisite binding state_id must be PersonalCapabilityStateId or None")
        object.__setattr__(self, "required_dimension_keys", _dimension_keys(self.required_dimension_keys, "prerequisite binding required_dimension_keys"))

    @property
    def deterministic_key(self) -> tuple[str, ...]:
        return (
            str(self.target_ref), str(self.prerequisite_ref),
            self.relation_scope.key if self.relation_scope else "",
            self.relation_scope.description if self.relation_scope else "",
            str(self.frame_ref), str(self.state_id) if self.state_id else "",
            *self.required_dimension_keys,
        )


@dataclass(frozen=True, order=True, slots=True)
class ExplorationInput:
    concept_ref: CapabilityConceptRef
    rationale: str

    def __post_init__(self) -> None:
        if not isinstance(self.concept_ref, CapabilityConceptRef):
            raise InvalidProgressionRequest("exploration concept_ref must be exact CapabilityConceptRef")
        object.__setattr__(self, "rationale", _clean_text(self.rationale, "exploration rationale", InvalidProgressionRequest))


@dataclass(frozen=True, slots=True)
class ProgressionFrontierRequest:
    frontier_id: ProgressionFrontierId
    subject_ref: CapabilitySubjectRef
    as_of: datetime
    generated_at: datetime
    requester_ref: ProgressionRequesterRef
    focuses: tuple[ProgressionFocus, ...] = ()
    seed_bindings: tuple[FrontierSeedBinding, ...] = ()
    prerequisite_bindings: tuple[PrerequisiteCheckBinding, ...] = ()
    exploration_inputs: tuple[ExplorationInput, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.frontier_id, ProgressionFrontierId):
            raise InvalidProgressionRequest("frontier_id must be ProgressionFrontierId")
        if not isinstance(self.subject_ref, CapabilitySubjectRef):
            raise InvalidProgressionRequest("subject_ref must be CapabilitySubjectRef")
        if not isinstance(self.requester_ref, ProgressionRequesterRef):
            raise InvalidProgressionRequest("requester_ref must be ProgressionRequesterRef")
        as_of = _time(self.as_of, "progression as_of", InvalidProgressionRequest)
        generated_at = _time(self.generated_at, "progression generated_at", InvalidProgressionRequest)
        if generated_at < as_of:
            raise InvalidProgressionRequest("generated_at must not precede as_of")
        specs = (
            ("focuses", self.focuses, ProgressionFocus),
            ("seed_bindings", self.seed_bindings, FrontierSeedBinding),
            ("prerequisite_bindings", self.prerequisite_bindings, PrerequisiteCheckBinding),
            ("exploration_inputs", self.exploration_inputs, ExplorationInput),
        )
        normalized = {}
        for name, raw, expected in specs:
            if isinstance(raw, (str, bytes)):
                raise InvalidProgressionRequest(f"{name} must be an iterable")
            try:
                items = tuple(raw)
            except TypeError as exc:
                raise InvalidProgressionRequest(f"{name} must be iterable") from exc
            if any(not isinstance(item, expected) for item in items):
                raise InvalidProgressionRequest(f"{name} must contain {expected.__name__} values")
            normalized[name] = items
        if not (normalized["focuses"] or normalized["seed_bindings"] or normalized["exploration_inputs"]):
            raise InvalidProgressionRequest("progression request requires a seed binding, explicit focus, or exploration input")
        focus_refs = [item.concept_ref for item in normalized["focuses"]]
        if len(set(focus_refs)) != len(focus_refs):
            raise InvalidProgressionRequest("duplicate focus concept refs are not allowed")
        seed_ids = [item.state_id for item in normalized["seed_bindings"]]
        if len(set(seed_ids)) != len(seed_ids):
            raise InvalidProgressionRequest("each state may have at most one frontier seed binding per request")
        prerequisite_keys = [item.deterministic_key for item in normalized["prerequisite_bindings"]]
        if len(set(prerequisite_keys)) != len(prerequisite_keys):
            raise InvalidProgressionRequest("duplicate prerequisite check bindings are not allowed")
        exploration_refs = [item.concept_ref for item in normalized["exploration_inputs"]]
        if len(set(exploration_refs)) != len(exploration_refs):
            raise InvalidProgressionRequest("duplicate exploration concept refs are not allowed")
        object.__setattr__(self, "as_of", as_of)
        object.__setattr__(self, "generated_at", generated_at)
        object.__setattr__(self, "focuses", tuple(sorted(normalized["focuses"], key=lambda x: x.concept_ref)))
        object.__setattr__(self, "seed_bindings", tuple(sorted(normalized["seed_bindings"], key=lambda x: str(x.state_id))))
        object.__setattr__(self, "prerequisite_bindings", tuple(sorted(normalized["prerequisite_bindings"], key=lambda x: x.deterministic_key)))
        object.__setattr__(self, "exploration_inputs", tuple(sorted(normalized["exploration_inputs"], key=lambda x: x.concept_ref)))

    def to_dict(self):
        from .serialization import request_to_dict
        return request_to_dict(self)

    @classmethod
    def from_dict(cls, payload):
        from .serialization import request_from_dict
        return request_from_dict(payload)

    def to_json(self) -> str:
        from .serialization import request_to_json
        return request_to_json(self)

    @classmethod
    def from_json(cls, payload: str) -> "ProgressionFrontierRequest":
        from .serialization import request_from_json
        return request_from_json(payload)


@dataclass(frozen=True, slots=True)
class ProgressionRelationWitness:
    source_ref: CapabilityConceptRef
    target_ref: CapabilityConceptRef
    kind: RelationKind
    scope: RelationScope | None = None
    strength: RelationStrength = RelationStrength.UNSPECIFIED

    def __post_init__(self) -> None:
        if not isinstance(self.source_ref, CapabilityConceptRef) or not isinstance(self.target_ref, CapabilityConceptRef):
            raise InvalidProgressionFrontier("relation witness endpoints must be exact CapabilityConceptRef values")
        if not isinstance(self.kind, RelationKind) or self.kind not in _ALLOWED_FRONTIER_RELATIONS:
            raise InvalidProgressionFrontier("relation witness kind is not an allowed direct frontier relation")
        if self.scope is not None and not isinstance(self.scope, RelationScope):
            raise InvalidProgressionFrontier("relation witness scope must be RelationScope or None")
        if not isinstance(self.strength, RelationStrength):
            raise InvalidProgressionFrontier("relation witness strength must be RelationStrength")
        if self.source_ref.capability_id == self.target_ref.capability_id:
            raise InvalidProgressionFrontier("relation witness may not be a self relation")
        if self.kind is RelationKind.SPECIALIZES and (self.scope is not None or self.strength is not RelationStrength.UNSPECIFIED):
            raise InvalidProgressionFrontier("SPECIALIZES witness does not accept scope or strength")
        if self.kind in {RelationKind.REQUIRES, RelationKind.ENABLED_BY} and self.strength is not RelationStrength.UNSPECIFIED:
            raise InvalidProgressionFrontier(f"{self.kind.value} witness is categorical")

    @property
    def deterministic_key(self) -> tuple[str, ...]:
        return (
            str(self.source_ref), self.kind.value, str(self.target_ref),
            self.scope.key if self.scope else "", self.scope.description if self.scope else "",
            self.strength.value,
        )


@dataclass(frozen=True, slots=True)
class FrontierAdjacencyWitness:
    state_id: PersonalCapabilityStateId
    seed_concept_ref: CapabilityConceptRef
    seed_dimension_keys: tuple[str, ...]
    relation: ProgressionRelationWitness

    def __post_init__(self) -> None:
        if not isinstance(self.state_id, PersonalCapabilityStateId):
            raise InvalidProgressionFrontier("adjacency witness state_id must be PersonalCapabilityStateId")
        if not isinstance(self.seed_concept_ref, CapabilityConceptRef):
            raise InvalidProgressionFrontier("adjacency witness seed_concept_ref must be exact CapabilityConceptRef")
        if not isinstance(self.relation, ProgressionRelationWitness):
            raise InvalidProgressionFrontier("adjacency witness relation must be ProgressionRelationWitness")
        if self.relation.target_ref != self.seed_concept_ref:
            raise InvalidProgressionFrontier("adjacency witness relation target must equal seed concept ref")
        object.__setattr__(self, "seed_dimension_keys", _dimension_keys(self.seed_dimension_keys, "adjacency witness seed_dimension_keys", InvalidProgressionFrontier))

    @property
    def deterministic_key(self) -> tuple[str, ...]:
        return (str(self.state_id), str(self.seed_concept_ref), *self.seed_dimension_keys, *self.relation.deterministic_key)


@dataclass(frozen=True, slots=True)
class FrontierCandidate:
    concept_ref: CapabilityConceptRef
    explicit_focus: bool
    adjacency_witnesses: tuple[FrontierAdjacencyWitness, ...] = ()
    assessed_prerequisites: tuple[ProgressionRelationWitness, ...] = ()
    unassessed_prerequisites: tuple[ProgressionRelationWitness, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.concept_ref, CapabilityConceptRef):
            raise InvalidProgressionFrontier("frontier candidate concept_ref must be exact CapabilityConceptRef")
        if not isinstance(self.explicit_focus, bool):
            raise InvalidProgressionFrontier("frontier candidate explicit_focus must be bool")
        specs = (
            ("adjacency_witnesses", self.adjacency_witnesses, FrontierAdjacencyWitness),
            ("assessed_prerequisites", self.assessed_prerequisites, ProgressionRelationWitness),
            ("unassessed_prerequisites", self.unassessed_prerequisites, ProgressionRelationWitness),
        )
        normalized = {}
        for name, raw, expected in specs:
            if isinstance(raw, (str, bytes)):
                raise InvalidProgressionFrontier(f"{name} must be an iterable")
            try:
                items = tuple(raw)
            except TypeError as exc:
                raise InvalidProgressionFrontier(f"{name} must be iterable") from exc
            if any(not isinstance(item, expected) for item in items):
                raise InvalidProgressionFrontier(f"{name} must contain {expected.__name__} values")
            keys = [item.deterministic_key for item in items]
            if len(set(keys)) != len(keys):
                raise InvalidProgressionFrontier(f"{name} contains duplicate witnesses")
            normalized[name] = items
        if not self.explicit_focus and not normalized["adjacency_witnesses"]:
            raise InvalidProgressionFrontier("frontier candidate requires explicit focus or an adjacency witness")
        for witness in normalized["adjacency_witnesses"]:
            if witness.relation.source_ref != self.concept_ref:
                raise InvalidProgressionFrontier("candidate adjacency relation source must equal candidate concept ref")
        for witness in (*normalized["assessed_prerequisites"], *normalized["unassessed_prerequisites"]):
            if witness.kind is not RelationKind.REQUIRES:
                raise InvalidProgressionFrontier("candidate prerequisite witnesses must use REQUIRES")
            if witness.source_ref != self.concept_ref:
                raise InvalidProgressionFrontier("candidate prerequisite source must equal candidate concept ref")
        assessed_keys = {item.deterministic_key for item in normalized["assessed_prerequisites"]}
        unassessed_keys = {item.deterministic_key for item in normalized["unassessed_prerequisites"]}
        if assessed_keys & unassessed_keys:
            raise InvalidProgressionFrontier("one prerequisite relation cannot be both assessed and unassessed")
        object.__setattr__(self, "adjacency_witnesses", tuple(sorted(normalized["adjacency_witnesses"], key=lambda x: x.deterministic_key)))
        object.__setattr__(self, "assessed_prerequisites", tuple(sorted(normalized["assessed_prerequisites"], key=lambda x: x.deterministic_key)))
        object.__setattr__(self, "unassessed_prerequisites", tuple(sorted(normalized["unassessed_prerequisites"], key=lambda x: x.deterministic_key)))


class PrerequisiteDimensionGapKind(str, Enum):
    NO_SELECTED_STATE = "no_selected_state"
    UNKNOWN = "unknown"
    INSUFFICIENT = "insufficient"


@dataclass(frozen=True, order=True, slots=True)
class PrerequisiteDimensionGap:
    dimension_key: str
    kind: PrerequisiteDimensionGapKind
    conflict_status: DimensionConflictStatus | None = None

    def __post_init__(self) -> None:
        _key(self.dimension_key, "prerequisite gap dimension key", InvalidProgressionFrontier)
        if not isinstance(self.kind, PrerequisiteDimensionGapKind):
            raise InvalidProgressionFrontier("prerequisite gap kind must be PrerequisiteDimensionGapKind")
        if self.conflict_status is not None and not isinstance(self.conflict_status, DimensionConflictStatus):
            raise InvalidProgressionFrontier("prerequisite gap conflict_status must be DimensionConflictStatus or None")
        if self.kind is PrerequisiteDimensionGapKind.NO_SELECTED_STATE:
            if self.conflict_status is not None:
                raise InvalidProgressionFrontier("NO_SELECTED_STATE gap cannot carry conflict status")
        elif self.conflict_status is None:
            raise InvalidProgressionFrontier("state-backed prerequisite gap must preserve conflict status")


@dataclass(frozen=True, slots=True)
class PrerequisiteEvidenceGap:
    target_ref: CapabilityConceptRef
    prerequisite_ref: CapabilityConceptRef
    relation: ProgressionRelationWitness
    frame_ref: CompetenceFrameRef
    state_id: PersonalCapabilityStateId | None
    dimension_gaps: tuple[PrerequisiteDimensionGap, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.target_ref, CapabilityConceptRef) or not isinstance(self.prerequisite_ref, CapabilityConceptRef):
            raise InvalidProgressionFrontier("prerequisite gap target/prerequisite must be exact CapabilityConceptRef values")
        if not isinstance(self.relation, ProgressionRelationWitness):
            raise InvalidProgressionFrontier("prerequisite gap relation must be ProgressionRelationWitness")
        if self.relation.kind is not RelationKind.REQUIRES:
            raise InvalidProgressionFrontier("prerequisite evidence gaps may be created only from REQUIRES")
        if self.relation.source_ref != self.target_ref or self.relation.target_ref != self.prerequisite_ref:
            raise InvalidProgressionFrontier("prerequisite gap relation endpoints must match target/prerequisite")
        if not isinstance(self.frame_ref, CompetenceFrameRef):
            raise InvalidProgressionFrontier("prerequisite gap frame_ref must be exact CompetenceFrameRef")
        if self.state_id is not None and not isinstance(self.state_id, PersonalCapabilityStateId):
            raise InvalidProgressionFrontier("prerequisite gap state_id must be PersonalCapabilityStateId or None")
        if isinstance(self.dimension_gaps, (str, bytes)):
            raise InvalidProgressionFrontier("dimension_gaps must be an iterable")
        try:
            gaps = tuple(self.dimension_gaps)
        except TypeError as exc:
            raise InvalidProgressionFrontier("dimension_gaps must be iterable") from exc
        if not gaps or any(not isinstance(item, PrerequisiteDimensionGap) for item in gaps):
            raise InvalidProgressionFrontier("prerequisite evidence gap requires PrerequisiteDimensionGap values")
        keys = [item.dimension_key for item in gaps]
        if len(set(keys)) != len(keys):
            raise InvalidProgressionFrontier("duplicate prerequisite dimension gaps are not allowed")
        if self.state_id is None and any(item.kind is not PrerequisiteDimensionGapKind.NO_SELECTED_STATE for item in gaps):
            raise InvalidProgressionFrontier("gap without selected state must use NO_SELECTED_STATE")
        if self.state_id is not None and any(item.kind is PrerequisiteDimensionGapKind.NO_SELECTED_STATE for item in gaps):
            raise InvalidProgressionFrontier("state-backed gap cannot use NO_SELECTED_STATE")
        object.__setattr__(self, "dimension_gaps", tuple(sorted(gaps)))

    @property
    def deterministic_key(self) -> tuple[str, ...]:
        return (
            str(self.target_ref), str(self.prerequisite_ref), *self.relation.deterministic_key,
            str(self.frame_ref), str(self.state_id) if self.state_id else "",
            *(f"{gap.dimension_key}:{gap.kind.value}" for gap in self.dimension_gaps),
        )


@dataclass(frozen=True, order=True, slots=True)
class ExplorationOpportunity:
    concept_ref: CapabilityConceptRef
    rationale: str

    def __post_init__(self) -> None:
        if not isinstance(self.concept_ref, CapabilityConceptRef):
            raise InvalidProgressionFrontier("exploration opportunity concept_ref must be exact CapabilityConceptRef")
        object.__setattr__(self, "rationale", _clean_text(self.rationale, "exploration opportunity rationale", InvalidProgressionFrontier))


@dataclass(frozen=True, slots=True)
class ProgressionFrontier:
    frontier_id: ProgressionFrontierId
    subject_ref: CapabilitySubjectRef
    as_of: datetime
    generated_at: datetime
    policy_ref: ProgressionPolicyRef
    deriver_ref: ProgressionDeriverRef
    requester_ref: ProgressionRequesterRef
    focuses: tuple[ProgressionFocus, ...]
    seed_bindings: tuple[FrontierSeedBinding, ...]
    prerequisite_bindings: tuple[PrerequisiteCheckBinding, ...]
    exploration_inputs: tuple[ExplorationInput, ...]
    candidates: tuple[FrontierCandidate, ...]
    prerequisite_gaps: tuple[PrerequisiteEvidenceGap, ...]
    exploration_opportunities: tuple[ExplorationOpportunity, ...]
    rationale: str

    def __post_init__(self) -> None:
        if not isinstance(self.frontier_id, ProgressionFrontierId):
            raise InvalidProgressionFrontier("frontier_id must be ProgressionFrontierId")
        if not isinstance(self.subject_ref, CapabilitySubjectRef):
            raise InvalidProgressionFrontier("subject_ref must be CapabilitySubjectRef")
        if not isinstance(self.policy_ref, ProgressionPolicyRef):
            raise InvalidProgressionFrontier("policy_ref must be ProgressionPolicyRef")
        if not isinstance(self.deriver_ref, ProgressionDeriverRef):
            raise InvalidProgressionFrontier("deriver_ref must be ProgressionDeriverRef")
        if not isinstance(self.requester_ref, ProgressionRequesterRef):
            raise InvalidProgressionFrontier("requester_ref must be ProgressionRequesterRef")
        as_of = _time(self.as_of, "frontier as_of", InvalidProgressionFrontier)
        generated_at = _time(self.generated_at, "frontier generated_at", InvalidProgressionFrontier)
        if generated_at < as_of:
            raise InvalidProgressionFrontier("generated_at must not precede as_of")
        specs = (
            ("focuses", self.focuses, ProgressionFocus), ("seed_bindings", self.seed_bindings, FrontierSeedBinding),
            ("prerequisite_bindings", self.prerequisite_bindings, PrerequisiteCheckBinding),
            ("exploration_inputs", self.exploration_inputs, ExplorationInput), ("candidates", self.candidates, FrontierCandidate),
            ("prerequisite_gaps", self.prerequisite_gaps, PrerequisiteEvidenceGap),
            ("exploration_opportunities", self.exploration_opportunities, ExplorationOpportunity),
        )
        normalized = {}
        for name, raw, expected in specs:
            if isinstance(raw, (str, bytes)):
                raise InvalidProgressionFrontier(f"{name} must be an iterable")
            try:
                items = tuple(raw)
            except TypeError as exc:
                raise InvalidProgressionFrontier(f"{name} must be iterable") from exc
            if any(not isinstance(item, expected) for item in items):
                raise InvalidProgressionFrontier(f"{name} must contain {expected.__name__} values")
            normalized[name] = items
        candidate_refs = [item.concept_ref for item in normalized["candidates"]]
        if len(set(candidate_refs)) != len(candidate_refs):
            raise InvalidProgressionFrontier("duplicate frontier candidate refs are not allowed")
        gap_keys = [item.deterministic_key for item in normalized["prerequisite_gaps"]]
        if len(set(gap_keys)) != len(gap_keys):
            raise InvalidProgressionFrontier("duplicate prerequisite evidence gaps are not allowed")
        exploration_refs = [item.concept_ref for item in normalized["exploration_opportunities"]]
        if len(set(exploration_refs)) != len(exploration_refs):
            raise InvalidProgressionFrontier("duplicate exploration opportunity refs are not allowed")
        object.__setattr__(self, "as_of", as_of)
        object.__setattr__(self, "generated_at", generated_at)
        object.__setattr__(self, "focuses", tuple(normalized["focuses"]))
        object.__setattr__(self, "seed_bindings", tuple(normalized["seed_bindings"]))
        object.__setattr__(self, "prerequisite_bindings", tuple(normalized["prerequisite_bindings"]))
        object.__setattr__(self, "exploration_inputs", tuple(normalized["exploration_inputs"]))
        object.__setattr__(self, "candidates", tuple(sorted(normalized["candidates"], key=lambda x: x.concept_ref)))
        object.__setattr__(self, "prerequisite_gaps", tuple(sorted(normalized["prerequisite_gaps"], key=lambda x: x.deterministic_key)))
        object.__setattr__(self, "exploration_opportunities", tuple(sorted(normalized["exploration_opportunities"], key=lambda x: x.concept_ref)))
        object.__setattr__(self, "rationale", _clean_text(self.rationale, "frontier rationale", InvalidProgressionFrontier))

    def to_dict(self):
        from .serialization import frontier_to_dict
        return frontier_to_dict(self)

    @classmethod
    def from_dict(cls, payload):
        from .serialization import frontier_from_dict
        return frontier_from_dict(payload)

    def to_json(self) -> str:
        from .serialization import frontier_to_json
        return frontier_to_json(self)

    @classmethod
    def from_json(cls, payload: str) -> "ProgressionFrontier":
        from .serialization import frontier_from_json
        return frontier_from_json(payload)


@dataclass(frozen=True, slots=True)
class ProgressionFrontierSet:
    subject_ref: CapabilitySubjectRef
    frontiers: tuple[ProgressionFrontier, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.subject_ref, CapabilitySubjectRef):
            raise InvalidProgressionSet("subject_ref must be CapabilitySubjectRef")
        if isinstance(self.frontiers, (str, bytes)):
            raise InvalidProgressionSet("frontiers must be an iterable")
        try:
            frontiers = tuple(self.frontiers)
        except TypeError as exc:
            raise InvalidProgressionSet("frontiers must be iterable") from exc
        if any(not isinstance(item, ProgressionFrontier) for item in frontiers):
            raise InvalidProgressionSet("frontiers must contain ProgressionFrontier values")
        if any(item.subject_ref != self.subject_ref for item in frontiers):
            raise InvalidProgressionSet("all frontiers in one set must belong to exactly one subject")
        ids = [item.frontier_id for item in frontiers]
        if len(set(ids)) != len(ids):
            raise InvalidProgressionSet("duplicate progression frontier ids are not allowed")
        object.__setattr__(self, "frontiers", tuple(sorted(frontiers, key=lambda x: (x.as_of, x.generated_at, str(x.frontier_id)))))

    def to_dict(self):
        from .serialization import frontier_set_to_dict
        return frontier_set_to_dict(self)

    @classmethod
    def from_dict(cls, payload):
        from .serialization import frontier_set_from_dict
        return frontier_set_from_dict(payload)

    def to_json(self) -> str:
        from .serialization import frontier_set_to_json
        return frontier_set_to_json(self)

    @classmethod
    def from_json(cls, payload: str) -> "ProgressionFrontierSet":
        from .serialization import frontier_set_from_json
        return frontier_set_from_json(payload)
