"""PR9 Player Window read-model primitives."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import re
import unicodedata

from capability_lab.epistemics import CapabilityClaimId, CapabilitySubjectRef, ClaimEvaluationId, ConflictStatus, EvaluationConclusion
from capability_lab.epistemics.core import EpistemicError, canonical_time
from capability_lab.history import AchievementInstanceId, PersonalLegendId, PersonalMilestoneEventId
from capability_lab.progression import ProgressionFrontierId, PrerequisiteDimensionGapKind
from capability_lab.semantics import CapabilityConceptRef
from capability_lab.state import CompetenceFrameRef, DimensionConflictStatus, DimensionStanding, PersonalCapabilityStateId


class PlayerWindowError(ValueError):
    """Base validation error for PR9 Player Window projections."""


class InvalidPlayerWindowId(PlayerWindowError):
    pass


class InvalidPlayerWindowRequest(PlayerWindowError):
    pass


class InvalidPlayerWindow(PlayerWindowError):
    pass


class InvalidPlayerWindowSet(PlayerWindowError):
    pass


_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_NAMESPACE_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*$")
_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_REF_RE = re.compile(r"^([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*):([a-z][a-z0-9_]*)@([1-9][0-9]*)$")


def _clean_text(value: object, field_name: str, error_type: type[PlayerWindowError]) -> str:
    if not isinstance(value, str):
        raise error_type(f"{field_name} must be a string")
    cleaned = unicodedata.normalize("NFC", value).strip()
    if not cleaned:
        raise error_type(f"{field_name} must be non-empty")
    return cleaned


def _optional_text(value: object, field_name: str, error_type: type[PlayerWindowError]) -> str | None:
    if value is None:
        return None
    return _clean_text(value, field_name, error_type)


def _opaque_id(value: object, field_name: str, error_type: type[PlayerWindowError]) -> str:
    if not isinstance(value, str) or _ID_RE.fullmatch(value) is None:
        raise error_type(f"{field_name} must be a canonical opaque ASCII identifier")
    return value


def _time(value: object, field_name: str, error_type: type[PlayerWindowError]) -> datetime:
    try:
        return canonical_time(value, field_name)
    except EpistemicError as exc:
        raise error_type(str(exc)) from exc


def _typed_tuple(value: object, expected: type, field_name: str, error_type: type[PlayerWindowError], *, allow_empty: bool = True):
    if isinstance(value, (str, bytes)):
        raise error_type(f"{field_name} must be an iterable")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise error_type(f"{field_name} must be iterable") from exc
    if not allow_empty and not items:
        raise error_type(f"{field_name} requires at least one item")
    if any(not isinstance(item, expected) for item in items):
        raise error_type(f"{field_name} must contain {expected.__name__} values")
    return items


def _unique_sorted(items: tuple, field_name: str, error_type: type[PlayerWindowError], key=str):
    keys = [key(item) for item in items]
    if len(set(keys)) != len(keys):
        raise error_type(f"duplicate {field_name} values are not allowed")
    return tuple(sorted(items, key=key))


@dataclass(frozen=True, order=True, slots=True)
class PlayerWindowId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _opaque_id(self.value, "player window id", InvalidPlayerWindowId))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, order=True, slots=True)
class PlayerWindowPolicyRef:
    namespace: str
    key: str
    revision: int

    def __post_init__(self) -> None:
        if not isinstance(self.namespace, str) or _NAMESPACE_RE.fullmatch(self.namespace) is None:
            raise InvalidPlayerWindow("player window policy namespace must use canonical syntax")
        if not isinstance(self.key, str) or _KEY_RE.fullmatch(self.key) is None:
            raise InvalidPlayerWindow("player window policy key must use canonical syntax")
        if isinstance(self.revision, bool) or not isinstance(self.revision, int) or self.revision < 1:
            raise InvalidPlayerWindow("player window policy revision must be integer >= 1")

    @classmethod
    def parse(cls, value: object) -> "PlayerWindowPolicyRef":
        if not isinstance(value, str):
            raise InvalidPlayerWindow("player window policy ref must be a string")
        match = _REF_RE.fullmatch(value)
        if match is None:
            raise InvalidPlayerWindow("player window policy ref must use '<namespace>:<key>@<revision>'")
        return cls(match.group(1), match.group(2), int(match.group(3)))

    def __str__(self) -> str:
        return f"{self.namespace}:{self.key}@{self.revision}"


class PlayerWindowMechanismKind(str, Enum):
    HUMAN = "human"
    RULE = "rule"
    MODEL = "model"
    HYBRID = "hybrid"
    EXTERNAL_SYSTEM = "external_system"


@dataclass(frozen=True, order=True, slots=True)
class PlayerWindowRequesterRef:
    kind: PlayerWindowMechanismKind
    ref: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, PlayerWindowMechanismKind):
            raise InvalidPlayerWindowRequest("requester kind must be PlayerWindowMechanismKind")
        object.__setattr__(self, "ref", _opaque_id(self.ref, "requester ref", InvalidPlayerWindowRequest))


@dataclass(frozen=True, order=True, slots=True)
class PlayerWindowViewerRef:
    kind: PlayerWindowMechanismKind
    ref: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, PlayerWindowMechanismKind):
            raise InvalidPlayerWindowRequest("viewer kind must be PlayerWindowMechanismKind")
        object.__setattr__(self, "ref", _opaque_id(self.ref, "viewer ref", InvalidPlayerWindowRequest))


@dataclass(frozen=True, order=True, slots=True)
class PlayerWindowGeneratorRef:
    kind: PlayerWindowMechanismKind
    ref: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, PlayerWindowMechanismKind):
            raise InvalidPlayerWindow("generator kind must be PlayerWindowMechanismKind")
        object.__setattr__(self, "ref", _opaque_id(self.ref, "generator ref", InvalidPlayerWindow))


@dataclass(frozen=True, slots=True)
class PlayerWindowRequest:
    window_id: PlayerWindowId
    subject_ref: CapabilitySubjectRef
    as_of: datetime
    generated_at: datetime
    requester_ref: PlayerWindowRequesterRef
    viewer_ref: PlayerWindowViewerRef
    selected_state_ids: tuple[PersonalCapabilityStateId, ...] = ()
    selected_achievement_ids: tuple[AchievementInstanceId, ...] = ()
    selected_milestone_ids: tuple[PersonalMilestoneEventId, ...] = ()
    selected_legend_id: PersonalLegendId | None = None
    selected_frontier_id: ProgressionFrontierId | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.window_id, PlayerWindowId):
            raise InvalidPlayerWindowRequest("window_id must be PlayerWindowId")
        if not isinstance(self.subject_ref, CapabilitySubjectRef):
            raise InvalidPlayerWindowRequest("subject_ref must be CapabilitySubjectRef")
        if not isinstance(self.requester_ref, PlayerWindowRequesterRef):
            raise InvalidPlayerWindowRequest("requester_ref must be PlayerWindowRequesterRef")
        if not isinstance(self.viewer_ref, PlayerWindowViewerRef):
            raise InvalidPlayerWindowRequest("viewer_ref must be PlayerWindowViewerRef")
        as_of = _time(self.as_of, "player window as_of", InvalidPlayerWindowRequest)
        generated_at = _time(self.generated_at, "player window generated_at", InvalidPlayerWindowRequest)
        if generated_at < as_of:
            raise InvalidPlayerWindowRequest("generated_at must not precede as_of")
        states = _unique_sorted(_typed_tuple(self.selected_state_ids, PersonalCapabilityStateId, "selected_state_ids", InvalidPlayerWindowRequest), "selected state id", InvalidPlayerWindowRequest)
        achievements = _unique_sorted(_typed_tuple(self.selected_achievement_ids, AchievementInstanceId, "selected_achievement_ids", InvalidPlayerWindowRequest), "selected achievement id", InvalidPlayerWindowRequest)
        milestones = _unique_sorted(_typed_tuple(self.selected_milestone_ids, PersonalMilestoneEventId, "selected_milestone_ids", InvalidPlayerWindowRequest), "selected milestone id", InvalidPlayerWindowRequest)
        if self.selected_legend_id is not None and not isinstance(self.selected_legend_id, PersonalLegendId):
            raise InvalidPlayerWindowRequest("selected_legend_id must be PersonalLegendId or None")
        if self.selected_frontier_id is not None and not isinstance(self.selected_frontier_id, ProgressionFrontierId):
            raise InvalidPlayerWindowRequest("selected_frontier_id must be ProgressionFrontierId or None")
        if not (states or achievements or milestones or self.selected_legend_id or self.selected_frontier_id):
            raise InvalidPlayerWindowRequest("player window requires at least one explicitly selected source")
        object.__setattr__(self, "as_of", as_of)
        object.__setattr__(self, "generated_at", generated_at)
        object.__setattr__(self, "selected_state_ids", states)
        object.__setattr__(self, "selected_achievement_ids", achievements)
        object.__setattr__(self, "selected_milestone_ids", milestones)

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
    def from_json(cls, payload: str) -> "PlayerWindowRequest":
        from .serialization import request_from_json
        return request_from_json(payload)


@dataclass(frozen=True, order=True, slots=True)
class PlayerWindowClaimEntry:
    claim_id: CapabilityClaimId
    statement: str
    scope_description: str
    scope_tags: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.claim_id, CapabilityClaimId):
            raise InvalidPlayerWindow("claim entry claim_id must be CapabilityClaimId")
        object.__setattr__(self, "statement", _clean_text(self.statement, "claim statement", InvalidPlayerWindow))
        object.__setattr__(self, "scope_description", _clean_text(self.scope_description, "claim scope", InvalidPlayerWindow))
        tags = tuple(self.scope_tags)
        if any(not isinstance(item, str) for item in tags) or len(set(tags)) != len(tags):
            raise InvalidPlayerWindow("claim scope_tags must be unique strings")
        object.__setattr__(self, "scope_tags", tuple(sorted(tags)))


@dataclass(frozen=True, order=True, slots=True)
class PlayerWindowEvaluationEntry:
    evaluation_id: ClaimEvaluationId
    conclusion: EvaluationConclusion
    conflict_status: ConflictStatus
    policy_ref: str
    evaluator_kind: str
    evaluator_ref: str

    def __post_init__(self) -> None:
        if not isinstance(self.evaluation_id, ClaimEvaluationId):
            raise InvalidPlayerWindow("evaluation entry evaluation_id must be ClaimEvaluationId")
        if not isinstance(self.conclusion, EvaluationConclusion) or not isinstance(self.conflict_status, ConflictStatus):
            raise InvalidPlayerWindow("evaluation entry requires valid conclusion/conflict status")
        for name in ("policy_ref", "evaluator_kind", "evaluator_ref"):
            object.__setattr__(self, name, _clean_text(getattr(self, name), name, InvalidPlayerWindow))


@dataclass(frozen=True, slots=True)
class PlayerWindowDimensionEntry:
    dimension_key: str
    name: str
    description: str
    standing: DimensionStanding
    conflict_status: DimensionConflictStatus
    rationale: str
    claims: tuple[PlayerWindowClaimEntry, ...]
    evaluations: tuple[PlayerWindowEvaluationEntry, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.dimension_key, str) or _KEY_RE.fullmatch(self.dimension_key) is None:
            raise InvalidPlayerWindow("dimension_key must use canonical syntax")
        if not isinstance(self.standing, DimensionStanding) or not isinstance(self.conflict_status, DimensionConflictStatus):
            raise InvalidPlayerWindow("dimension entry requires valid standing/conflict status")
        for name in ("name", "description", "rationale"):
            object.__setattr__(self, name, _clean_text(getattr(self, name), name, InvalidPlayerWindow))
        claims = _unique_sorted(_typed_tuple(self.claims, PlayerWindowClaimEntry, "claims", InvalidPlayerWindow), "claim entry", InvalidPlayerWindow, key=lambda item: str(item.claim_id))
        evaluations = _unique_sorted(_typed_tuple(self.evaluations, PlayerWindowEvaluationEntry, "evaluations", InvalidPlayerWindow), "evaluation entry", InvalidPlayerWindow, key=lambda item: str(item.evaluation_id))
        object.__setattr__(self, "claims", claims)
        object.__setattr__(self, "evaluations", evaluations)


@dataclass(frozen=True, slots=True)
class PlayerWindowCapabilityEntry:
    state_id: PersonalCapabilityStateId
    concept_ref: CapabilityConceptRef
    concept_name: str
    concept_definition: str
    frame_ref: CompetenceFrameRef
    frame_name: str
    state_policy_ref: str
    state_deriver_kind: str
    state_deriver_ref: str
    as_of: datetime
    derived_at: datetime
    dimensions: tuple[PlayerWindowDimensionEntry, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.state_id, PersonalCapabilityStateId) or not isinstance(self.concept_ref, CapabilityConceptRef) or not isinstance(self.frame_ref, CompetenceFrameRef):
            raise InvalidPlayerWindow("capability entry requires exact state/concept/frame refs")
        for name in ("concept_name", "concept_definition", "frame_name", "state_policy_ref", "state_deriver_kind", "state_deriver_ref"):
            object.__setattr__(self, name, _clean_text(getattr(self, name), name, InvalidPlayerWindow))
        as_of = _time(self.as_of, "capability entry as_of", InvalidPlayerWindow)
        derived_at = _time(self.derived_at, "capability entry derived_at", InvalidPlayerWindow)
        if derived_at < as_of:
            raise InvalidPlayerWindow("capability entry derived_at must not precede as_of")
        dimensions = _typed_tuple(self.dimensions, PlayerWindowDimensionEntry, "dimensions", InvalidPlayerWindow, allow_empty=False)
        if len({item.dimension_key for item in dimensions}) != len(dimensions):
            raise InvalidPlayerWindow("duplicate capability dimension entries are not allowed")
        object.__setattr__(self, "as_of", as_of)
        object.__setattr__(self, "derived_at", derived_at)
        object.__setattr__(self, "dimensions", tuple(sorted(dimensions, key=lambda item: item.dimension_key)))


@dataclass(frozen=True, order=True, slots=True)
class PlayerWindowAchievementEntry:
    achievement_id: AchievementInstanceId
    family_ref: str
    family_name: str
    achieved_at: datetime
    recorded_at: datetime
    context: str
    variant: str | None
    record_note: str | None
    qualification_policy_ref: str
    qualifier_kind: str
    qualifier_ref: str

    def __post_init__(self) -> None:
        if not isinstance(self.achievement_id, AchievementInstanceId):
            raise InvalidPlayerWindow("achievement entry requires AchievementInstanceId")
        for name in ("family_ref", "family_name", "context", "qualification_policy_ref", "qualifier_kind", "qualifier_ref"):
            object.__setattr__(self, name, _clean_text(getattr(self, name), name, InvalidPlayerWindow))
        object.__setattr__(self, "variant", _optional_text(self.variant, "variant", InvalidPlayerWindow))
        object.__setattr__(self, "record_note", _optional_text(self.record_note, "record_note", InvalidPlayerWindow))
        achieved_at = _time(self.achieved_at, "achievement achieved_at", InvalidPlayerWindow)
        recorded_at = _time(self.recorded_at, "achievement recorded_at", InvalidPlayerWindow)
        if recorded_at < achieved_at:
            raise InvalidPlayerWindow("achievement recorded_at must not precede achieved_at")
        object.__setattr__(self, "achieved_at", achieved_at)
        object.__setattr__(self, "recorded_at", recorded_at)


@dataclass(frozen=True, order=True, slots=True)
class PlayerWindowMilestoneEntry:
    milestone_id: PersonalMilestoneEventId
    title: str
    description: str
    significance_note: str
    occurred_at: datetime
    recorded_at: datetime
    recorder_kind: str
    recorder_ref: str
    recording_policy_ref: str

    def __post_init__(self) -> None:
        if not isinstance(self.milestone_id, PersonalMilestoneEventId):
            raise InvalidPlayerWindow("milestone entry requires PersonalMilestoneEventId")
        for name in ("title", "description", "significance_note", "recorder_kind", "recorder_ref", "recording_policy_ref"):
            object.__setattr__(self, name, _clean_text(getattr(self, name), name, InvalidPlayerWindow))
        occurred_at = _time(self.occurred_at, "milestone occurred_at", InvalidPlayerWindow)
        recorded_at = _time(self.recorded_at, "milestone recorded_at", InvalidPlayerWindow)
        if recorded_at < occurred_at:
            raise InvalidPlayerWindow("milestone recorded_at must not precede occurred_at")
        object.__setattr__(self, "occurred_at", occurred_at)
        object.__setattr__(self, "recorded_at", recorded_at)


@dataclass(frozen=True, slots=True)
class PlayerWindowLegendEntry:
    source_refs: tuple[str, ...]
    heading: str
    narrative: str

    def __post_init__(self) -> None:
        refs = tuple(self.source_refs)
        if not refs or any(not isinstance(item, str) or not item.strip() for item in refs) or len(set(refs)) != len(refs):
            raise InvalidPlayerWindow("legend entry source_refs must be unique non-empty strings")
        object.__setattr__(self, "source_refs", tuple(sorted(refs)))
        object.__setattr__(self, "heading", _clean_text(self.heading, "legend heading", InvalidPlayerWindow))
        object.__setattr__(self, "narrative", _clean_text(self.narrative, "legend narrative", InvalidPlayerWindow))


@dataclass(frozen=True, slots=True)
class PlayerWindowLegendPanel:
    legend_id: PersonalLegendId
    title: str
    summary: str
    as_of: datetime
    generated_at: datetime
    policy_ref: str
    generator_kind: str
    generator_ref: str
    entries: tuple[PlayerWindowLegendEntry, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.legend_id, PersonalLegendId):
            raise InvalidPlayerWindow("legend panel requires PersonalLegendId")
        for name in ("title", "summary", "policy_ref", "generator_kind", "generator_ref"):
            object.__setattr__(self, name, _clean_text(getattr(self, name), name, InvalidPlayerWindow))
        as_of = _time(self.as_of, "legend panel as_of", InvalidPlayerWindow)
        generated_at = _time(self.generated_at, "legend panel generated_at", InvalidPlayerWindow)
        if generated_at < as_of:
            raise InvalidPlayerWindow("legend panel generated_at must not precede as_of")
        entries = _typed_tuple(self.entries, PlayerWindowLegendEntry, "legend entries", InvalidPlayerWindow, allow_empty=False)
        object.__setattr__(self, "as_of", as_of)
        object.__setattr__(self, "generated_at", generated_at)
        object.__setattr__(self, "entries", entries)


@dataclass(frozen=True, order=True, slots=True)
class PlayerWindowFrontierCandidateEntry:
    concept_ref: CapabilityConceptRef
    concept_name: str
    explicit_focus: bool
    adjacency_reasons: tuple[str, ...]
    assessed_prerequisites: tuple[str, ...]
    unassessed_prerequisites: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.concept_ref, CapabilityConceptRef) or not isinstance(self.explicit_focus, bool):
            raise InvalidPlayerWindow("frontier candidate entry requires exact concept_ref and bool explicit_focus")
        object.__setattr__(self, "concept_name", _clean_text(self.concept_name, "frontier concept name", InvalidPlayerWindow))
        for name in ("adjacency_reasons", "assessed_prerequisites", "unassessed_prerequisites"):
            values = tuple(getattr(self, name))
            if any(not isinstance(item, str) or not item.strip() for item in values) or len(set(values)) != len(values):
                raise InvalidPlayerWindow(f"{name} must contain unique non-empty strings")
            object.__setattr__(self, name, tuple(sorted(values)))


@dataclass(frozen=True, order=True, slots=True)
class PlayerWindowGapDimensionEntry:
    dimension_key: str
    kind: PrerequisiteDimensionGapKind
    conflict_status: DimensionConflictStatus | None

    def __post_init__(self) -> None:
        if not isinstance(self.dimension_key, str) or _KEY_RE.fullmatch(self.dimension_key) is None:
            raise InvalidPlayerWindow("gap dimension_key must use canonical syntax")
        if not isinstance(self.kind, PrerequisiteDimensionGapKind):
            raise InvalidPlayerWindow("gap kind must be PrerequisiteDimensionGapKind")
        if self.conflict_status is not None and not isinstance(self.conflict_status, DimensionConflictStatus):
            raise InvalidPlayerWindow("gap conflict_status must be DimensionConflictStatus or None")


@dataclass(frozen=True, slots=True)
class PlayerWindowPrerequisiteGapEntry:
    target_ref: CapabilityConceptRef
    target_name: str
    prerequisite_ref: CapabilityConceptRef
    prerequisite_name: str
    relation_description: str
    frame_ref: CompetenceFrameRef
    state_id: PersonalCapabilityStateId | None
    dimension_gaps: tuple[PlayerWindowGapDimensionEntry, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.target_ref, CapabilityConceptRef) or not isinstance(self.prerequisite_ref, CapabilityConceptRef) or not isinstance(self.frame_ref, CompetenceFrameRef):
            raise InvalidPlayerWindow("prerequisite gap entry requires exact target/prerequisite/frame refs")
        if self.state_id is not None and not isinstance(self.state_id, PersonalCapabilityStateId):
            raise InvalidPlayerWindow("prerequisite gap state_id must be PersonalCapabilityStateId or None")
        for name in ("target_name", "prerequisite_name", "relation_description"):
            object.__setattr__(self, name, _clean_text(getattr(self, name), name, InvalidPlayerWindow))
        gaps = _typed_tuple(self.dimension_gaps, PlayerWindowGapDimensionEntry, "dimension_gaps", InvalidPlayerWindow, allow_empty=False)
        if len({item.dimension_key for item in gaps}) != len(gaps):
            raise InvalidPlayerWindow("duplicate prerequisite gap dimensions are not allowed")
        object.__setattr__(self, "dimension_gaps", tuple(sorted(gaps)))


@dataclass(frozen=True, order=True, slots=True)
class PlayerWindowExplorationEntry:
    concept_ref: CapabilityConceptRef
    concept_name: str
    rationale: str

    def __post_init__(self) -> None:
        if not isinstance(self.concept_ref, CapabilityConceptRef):
            raise InvalidPlayerWindow("exploration entry requires exact concept ref")
        object.__setattr__(self, "concept_name", _clean_text(self.concept_name, "exploration concept name", InvalidPlayerWindow))
        object.__setattr__(self, "rationale", _clean_text(self.rationale, "exploration rationale", InvalidPlayerWindow))


@dataclass(frozen=True, slots=True)
class PlayerWindowFrontierPanel:
    frontier_id: ProgressionFrontierId
    policy_ref: str
    deriver_kind: str
    deriver_ref: str
    requester_kind: str
    requester_ref: str
    rationale: str
    candidates: tuple[PlayerWindowFrontierCandidateEntry, ...]
    prerequisite_gaps: tuple[PlayerWindowPrerequisiteGapEntry, ...]
    exploration: tuple[PlayerWindowExplorationEntry, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.frontier_id, ProgressionFrontierId):
            raise InvalidPlayerWindow("frontier panel requires ProgressionFrontierId")
        for name in ("policy_ref", "deriver_kind", "deriver_ref", "requester_kind", "requester_ref", "rationale"):
            object.__setattr__(self, name, _clean_text(getattr(self, name), name, InvalidPlayerWindow))
        candidates = _unique_sorted(_typed_tuple(self.candidates, PlayerWindowFrontierCandidateEntry, "frontier candidates", InvalidPlayerWindow), "frontier candidate", InvalidPlayerWindow, key=lambda item: str(item.concept_ref))
        gaps = _typed_tuple(self.prerequisite_gaps, PlayerWindowPrerequisiteGapEntry, "prerequisite gaps", InvalidPlayerWindow)
        exploration = _unique_sorted(_typed_tuple(self.exploration, PlayerWindowExplorationEntry, "exploration entries", InvalidPlayerWindow), "exploration entry", InvalidPlayerWindow, key=lambda item: str(item.concept_ref))
        object.__setattr__(self, "candidates", candidates)
        object.__setattr__(self, "prerequisite_gaps", tuple(sorted(gaps, key=lambda item: (str(item.target_ref), str(item.prerequisite_ref), str(item.frame_ref), str(item.state_id or "")))))
        object.__setattr__(self, "exploration", exploration)


@dataclass(frozen=True, slots=True)
class PlayerWindow:
    window_id: PlayerWindowId
    subject_ref: CapabilitySubjectRef
    as_of: datetime
    generated_at: datetime
    policy_ref: PlayerWindowPolicyRef
    generator_ref: PlayerWindowGeneratorRef
    requester_ref: PlayerWindowRequesterRef
    viewer_ref: PlayerWindowViewerRef
    selected_state_ids: tuple[PersonalCapabilityStateId, ...]
    selected_achievement_ids: tuple[AchievementInstanceId, ...]
    selected_milestone_ids: tuple[PersonalMilestoneEventId, ...]
    selected_legend_id: PersonalLegendId | None
    selected_frontier_id: ProgressionFrontierId | None
    capabilities: tuple[PlayerWindowCapabilityEntry, ...]
    achievements: tuple[PlayerWindowAchievementEntry, ...]
    milestones: tuple[PlayerWindowMilestoneEntry, ...]
    legend: PlayerWindowLegendPanel | None
    frontier: PlayerWindowFrontierPanel | None
    rationale: str

    def __post_init__(self) -> None:
        if not isinstance(self.window_id, PlayerWindowId) or not isinstance(self.subject_ref, CapabilitySubjectRef):
            raise InvalidPlayerWindow("window requires PlayerWindowId and CapabilitySubjectRef")
        if not isinstance(self.policy_ref, PlayerWindowPolicyRef) or not isinstance(self.generator_ref, PlayerWindowGeneratorRef):
            raise InvalidPlayerWindow("window requires valid policy/generator refs")
        if not isinstance(self.requester_ref, PlayerWindowRequesterRef) or not isinstance(self.viewer_ref, PlayerWindowViewerRef):
            raise InvalidPlayerWindow("window requires requester/viewer refs")
        as_of = _time(self.as_of, "player window as_of", InvalidPlayerWindow)
        generated_at = _time(self.generated_at, "player window generated_at", InvalidPlayerWindow)
        if generated_at < as_of:
            raise InvalidPlayerWindow("generated_at must not precede as_of")
        capabilities = _unique_sorted(_typed_tuple(self.capabilities, PlayerWindowCapabilityEntry, "capabilities", InvalidPlayerWindow), "capability entry", InvalidPlayerWindow, key=lambda item: str(item.state_id))
        achievements = _unique_sorted(_typed_tuple(self.achievements, PlayerWindowAchievementEntry, "achievements", InvalidPlayerWindow), "achievement entry", InvalidPlayerWindow, key=lambda item: str(item.achievement_id))
        milestones = _unique_sorted(_typed_tuple(self.milestones, PlayerWindowMilestoneEntry, "milestones", InvalidPlayerWindow), "milestone entry", InvalidPlayerWindow, key=lambda item: str(item.milestone_id))
        if self.legend is not None and not isinstance(self.legend, PlayerWindowLegendPanel):
            raise InvalidPlayerWindow("legend must be PlayerWindowLegendPanel or None")
        if self.frontier is not None and not isinstance(self.frontier, PlayerWindowFrontierPanel):
            raise InvalidPlayerWindow("frontier must be PlayerWindowFrontierPanel or None")
        if tuple(item.state_id for item in capabilities) != tuple(sorted(self.selected_state_ids, key=str)):
            raise InvalidPlayerWindow("capability entries must exactly match selected_state_ids")
        if tuple(item.achievement_id for item in achievements) != tuple(sorted(self.selected_achievement_ids, key=str)):
            raise InvalidPlayerWindow("achievement entries must exactly match selected_achievement_ids")
        if tuple(item.milestone_id for item in milestones) != tuple(sorted(self.selected_milestone_ids, key=str)):
            raise InvalidPlayerWindow("milestone entries must exactly match selected_milestone_ids")
        if (self.legend.legend_id if self.legend else None) != self.selected_legend_id:
            raise InvalidPlayerWindow("legend panel must exactly match selected_legend_id")
        if (self.frontier.frontier_id if self.frontier else None) != self.selected_frontier_id:
            raise InvalidPlayerWindow("frontier panel must exactly match selected_frontier_id")
        object.__setattr__(self, "as_of", as_of)
        object.__setattr__(self, "generated_at", generated_at)
        object.__setattr__(self, "selected_state_ids", tuple(sorted(self.selected_state_ids, key=str)))
        object.__setattr__(self, "selected_achievement_ids", tuple(sorted(self.selected_achievement_ids, key=str)))
        object.__setattr__(self, "selected_milestone_ids", tuple(sorted(self.selected_milestone_ids, key=str)))
        object.__setattr__(self, "capabilities", capabilities)
        object.__setattr__(self, "achievements", achievements)
        object.__setattr__(self, "milestones", milestones)
        object.__setattr__(self, "rationale", _clean_text(self.rationale, "player window rationale", InvalidPlayerWindow))

    def to_dict(self):
        from .serialization import window_to_dict
        return window_to_dict(self)

    @classmethod
    def from_dict(cls, payload):
        from .serialization import window_from_dict
        return window_from_dict(payload)

    def to_json(self) -> str:
        from .serialization import window_to_json
        return window_to_json(self)

    @classmethod
    def from_json(cls, payload: str) -> "PlayerWindow":
        from .serialization import window_from_json
        return window_from_json(payload)


@dataclass(frozen=True, slots=True)
class PlayerWindowSet:
    subject_ref: CapabilitySubjectRef
    windows: tuple[PlayerWindow, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.subject_ref, CapabilitySubjectRef):
            raise InvalidPlayerWindowSet("window set subject_ref must be CapabilitySubjectRef")
        windows = _typed_tuple(self.windows, PlayerWindow, "windows", InvalidPlayerWindowSet)
        if any(item.subject_ref != self.subject_ref for item in windows):
            raise InvalidPlayerWindowSet("all windows in a set must belong to one subject")
        ids = [item.window_id for item in windows]
        if len(set(ids)) != len(ids):
            raise InvalidPlayerWindowSet("duplicate player window ids are not allowed")
        object.__setattr__(self, "windows", tuple(sorted(windows, key=lambda item: str(item.window_id))))

    def to_dict(self):
        from .serialization import window_set_to_dict
        return window_set_to_dict(self)

    @classmethod
    def from_dict(cls, payload):
        from .serialization import window_set_from_dict
        return window_set_from_dict(payload)

    def to_json(self) -> str:
        from .serialization import window_set_to_json
        return window_set_to_json(self)

    @classmethod
    def from_json(cls, payload: str) -> "PlayerWindowSet":
        from .serialization import window_set_from_json
        return window_set_from_json(payload)
