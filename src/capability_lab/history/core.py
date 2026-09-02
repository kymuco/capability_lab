"""Immutable achievement, milestone, and legend primitives for Capability Lab."""

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
    EvidenceId,
)


class HistoryError(ValueError):
    """Base validation error for PR7 history records."""


class InvalidHistoryId(HistoryError):
    pass


class InvalidAchievementFamily(HistoryError):
    pass


class InvalidAchievementInstance(HistoryError):
    pass


class InvalidMilestoneEvent(HistoryError):
    pass


class InvalidPersonalLegend(HistoryError):
    pass


_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_NAMESPACE_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*$")
_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_TAG_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_REF_RE = re.compile(
    r"^([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*):"
    r"([a-z][a-z0-9_]*)@([1-9][0-9]*)$"
)


def _clean_text(value: object, field_name: str, error_type: type[HistoryError]) -> str:
    if not isinstance(value, str):
        raise error_type(f"{field_name} must be a string")
    cleaned = unicodedata.normalize("NFC", value).strip()
    if not cleaned:
        raise error_type(f"{field_name} must be non-empty")
    return cleaned


def _clean_optional_text(
    value: object | None,
    field_name: str,
    error_type: type[HistoryError],
) -> str | None:
    if value is None:
        return None
    return _clean_text(value, field_name, error_type)


def _opaque_id(value: object, field_name: str) -> str:
    if not isinstance(value, str) or _ID_RE.fullmatch(value) is None:
        raise InvalidHistoryId(f"{field_name} must be a canonical opaque ASCII identifier")
    return value


def _namespace(value: object, field_name: str, error_type: type[HistoryError]) -> str:
    if not isinstance(value, str) or _NAMESPACE_RE.fullmatch(value) is None:
        raise error_type(f"{field_name} must use canonical namespace syntax")
    return value


def _key(value: object, field_name: str, error_type: type[HistoryError]) -> str:
    if not isinstance(value, str) or _KEY_RE.fullmatch(value) is None:
        raise error_type(f"{field_name} must use canonical lowercase key syntax")
    return value


def _revision(value: object, field_name: str, error_type: type[HistoryError]) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise error_type(f"{field_name} must be an integer >= 1")
    return value


def _canonical_time(
    value: object,
    field_name: str,
    error_type: type[HistoryError],
) -> datetime:
    if not isinstance(value, datetime):
        raise error_type(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise error_type(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _clean_aliases(value: object, name: str) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise InvalidAchievementFamily("aliases must be an iterable of strings, not a string")
    try:
        raw = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise InvalidAchievementFamily("aliases must be iterable") from exc
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in raw:
        alias = _clean_text(item, "achievement family alias", InvalidAchievementFamily)
        if alias == name:
            raise InvalidAchievementFamily("alias must not duplicate the primary family name")
        if alias in seen:
            raise InvalidAchievementFamily(f"duplicate achievement family alias: {alias!r}")
        seen.add(alias)
        cleaned.append(alias)
    return tuple(sorted(cleaned))


def _clean_tags(value: object, field_name: str, error_type: type[HistoryError]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise error_type(f"{field_name} must be an iterable of strings, not a string")
    try:
        raw = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise error_type(f"{field_name} must be iterable") from exc
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in raw:
        tag = _clean_text(item, field_name, error_type)
        if _TAG_RE.fullmatch(tag) is None:
            raise error_type(f"{field_name} values must use lowercase machine-tag syntax")
        if tag in seen:
            raise error_type(f"duplicate {field_name} value: {tag!r}")
        seen.add(tag)
        cleaned.append(tag)
    return tuple(sorted(cleaned))


@dataclass(frozen=True, order=True, slots=True)
class AchievementFamilyId:
    namespace: str
    key: str

    def __post_init__(self) -> None:
        _namespace(self.namespace, "achievement family namespace", InvalidAchievementFamily)
        _key(self.key, "achievement family key", InvalidAchievementFamily)

    @classmethod
    def parse(cls, value: object) -> "AchievementFamilyId":
        if not isinstance(value, str) or value.count(":") != 1:
            raise InvalidAchievementFamily("achievement family id must use '<namespace>:<key>'")
        namespace, key = value.split(":", 1)
        return cls(namespace, key)

    def __str__(self) -> str:
        return f"{self.namespace}:{self.key}"


@dataclass(frozen=True, order=True, slots=True)
class AchievementFamilyRef:
    family_id: AchievementFamilyId
    revision: int

    def __post_init__(self) -> None:
        if not isinstance(self.family_id, AchievementFamilyId):
            raise InvalidAchievementFamily("family ref family_id must be AchievementFamilyId")
        _revision(self.revision, "achievement family revision", InvalidAchievementFamily)

    @classmethod
    def parse(cls, value: object) -> "AchievementFamilyRef":
        if not isinstance(value, str):
            raise InvalidAchievementFamily("achievement family ref must be a string")
        match = _REF_RE.fullmatch(value)
        if match is None:
            raise InvalidAchievementFamily(
                "achievement family ref must use '<namespace>:<key>@<revision>'"
            )
        return cls(AchievementFamilyId(match.group(1), match.group(2)), int(match.group(3)))

    def __str__(self) -> str:
        return f"{self.family_id}@{self.revision}"


@dataclass(frozen=True, order=True, slots=True)
class AchievementCriterion:
    key: str
    description: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "key", _key(self.key, "achievement criterion key", InvalidAchievementFamily))
        object.__setattr__(
            self,
            "description",
            _clean_text(self.description, "achievement criterion description", InvalidAchievementFamily),
        )


class AchievementFamilyLifecycle(str, Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"


@dataclass(frozen=True, slots=True)
class AchievementFamily:
    """Shared versioned accomplishment semantics, not person-scoped history."""

    family_id: AchievementFamilyId
    name: str
    definition: str
    qualification_criteria: tuple[AchievementCriterion, ...] = ()
    aliases: tuple[str, ...] = ()
    revision: int = 1
    lifecycle: AchievementFamilyLifecycle = AchievementFamilyLifecycle.ACTIVE
    deprecation_note: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.family_id, AchievementFamilyId):
            raise InvalidAchievementFamily("family_id must be AchievementFamilyId")
        if not isinstance(self.lifecycle, AchievementFamilyLifecycle):
            raise InvalidAchievementFamily("lifecycle must be AchievementFamilyLifecycle")
        name = _clean_text(self.name, "achievement family name", InvalidAchievementFamily)
        definition = _clean_text(
            self.definition,
            "achievement family definition",
            InvalidAchievementFamily,
        )
        revision = _revision(self.revision, "achievement family revision", InvalidAchievementFamily)
        aliases = _clean_aliases(self.aliases, name)
        if isinstance(self.qualification_criteria, (str, bytes)):
            raise InvalidAchievementFamily("qualification_criteria must be an iterable")
        try:
            criteria = tuple(self.qualification_criteria)
        except TypeError as exc:
            raise InvalidAchievementFamily("qualification_criteria must be iterable") from exc
        if any(not isinstance(item, AchievementCriterion) for item in criteria):
            raise InvalidAchievementFamily(
                "qualification_criteria must contain AchievementCriterion values"
            )
        keys = [item.key for item in criteria]
        if len(set(keys)) != len(keys):
            raise InvalidAchievementFamily("duplicate achievement criterion keys are not allowed")
        criteria = tuple(sorted(criteria, key=lambda item: item.key))
        note = _clean_optional_text(
            self.deprecation_note,
            "achievement family deprecation_note",
            InvalidAchievementFamily,
        )
        if self.lifecycle is AchievementFamilyLifecycle.DEPRECATED and note is None:
            raise InvalidAchievementFamily("deprecated achievement families require deprecation_note")
        if self.lifecycle is AchievementFamilyLifecycle.ACTIVE and note is not None:
            raise InvalidAchievementFamily("active achievement families must not carry deprecation_note")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "definition", definition)
        object.__setattr__(self, "aliases", aliases)
        object.__setattr__(self, "qualification_criteria", criteria)
        object.__setattr__(self, "revision", revision)
        object.__setattr__(self, "deprecation_note", note)

    @property
    def ref(self) -> AchievementFamilyRef:
        return AchievementFamilyRef(self.family_id, self.revision)


@dataclass(frozen=True, slots=True)
class AchievementFamilyCatalog:
    """Deterministic shared current-family snapshot."""

    families: tuple[AchievementFamily, ...] = ()

    def __post_init__(self) -> None:
        if isinstance(self.families, (str, bytes)):
            raise InvalidAchievementFamily("families must be an iterable")
        try:
            families = tuple(self.families)
        except TypeError as exc:
            raise InvalidAchievementFamily("families must be iterable") from exc
        if any(not isinstance(item, AchievementFamily) for item in families):
            raise InvalidAchievementFamily("families must contain AchievementFamily values")
        families = tuple(sorted(families, key=lambda item: item.family_id))
        ids = [item.family_id for item in families]
        if len(set(ids)) != len(ids):
            raise InvalidAchievementFamily(
                "family catalog may contain at most one current revision per family id"
            )
        object.__setattr__(self, "families", families)

    def to_dict(self) -> dict:
        from .serialization import family_catalog_to_dict
        return family_catalog_to_dict(self)

    @classmethod
    def from_dict(cls, payload: object) -> "AchievementFamilyCatalog":
        from .serialization import family_catalog_from_dict
        return family_catalog_from_dict(payload)

    def to_json(self) -> str:
        from .serialization import family_catalog_to_json
        return family_catalog_to_json(self)

    @classmethod
    def from_json(cls, payload: object) -> "AchievementFamilyCatalog":
        from .serialization import family_catalog_from_json
        return family_catalog_from_json(payload)


@dataclass(frozen=True, order=True, slots=True)
class AchievementInstanceId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _opaque_id(self.value, "achievement instance id"))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, order=True, slots=True)
class PersonalMilestoneEventId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _opaque_id(self.value, "milestone event id"))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, order=True, slots=True)
class PersonalLegendId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _opaque_id(self.value, "personal legend id"))

    def __str__(self) -> str:
        return self.value


class HistoryMechanismKind(str, Enum):
    HUMAN = "human"
    RULE = "rule"
    MODEL = "model"
    HYBRID = "hybrid"
    EXTERNAL_SYSTEM = "external_system"


@dataclass(frozen=True, order=True, slots=True)
class AchievementQualifierRef:
    kind: HistoryMechanismKind
    ref: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, HistoryMechanismKind):
            raise InvalidAchievementInstance("qualifier kind must be HistoryMechanismKind")
        object.__setattr__(self, "ref", _opaque_id(self.ref, "achievement qualifier ref"))


@dataclass(frozen=True, order=True, slots=True)
class MilestoneRecorderRef:
    kind: HistoryMechanismKind
    ref: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, HistoryMechanismKind):
            raise InvalidMilestoneEvent("recorder kind must be HistoryMechanismKind")
        object.__setattr__(self, "ref", _opaque_id(self.ref, "milestone recorder ref"))


@dataclass(frozen=True, order=True, slots=True)
class LegendGeneratorRef:
    kind: HistoryMechanismKind
    ref: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, HistoryMechanismKind):
            raise InvalidPersonalLegend("legend generator kind must be HistoryMechanismKind")
        object.__setattr__(self, "ref", _opaque_id(self.ref, "legend generator ref"))


@dataclass(frozen=True, order=True, slots=True)
class AchievementQualificationPolicyRef:
    namespace: str
    key: str
    revision: int

    def __post_init__(self) -> None:
        _namespace(self.namespace, "qualification policy namespace", InvalidAchievementInstance)
        _key(self.key, "qualification policy key", InvalidAchievementInstance)
        _revision(self.revision, "qualification policy revision", InvalidAchievementInstance)

    @classmethod
    def parse(cls, value: object) -> "AchievementQualificationPolicyRef":
        if not isinstance(value, str):
            raise InvalidAchievementInstance("qualification policy ref must be a string")
        match = _REF_RE.fullmatch(value)
        if match is None:
            raise InvalidAchievementInstance(
                "qualification policy ref must use '<namespace>:<key>@<revision>'"
            )
        return cls(match.group(1), match.group(2), int(match.group(3)))

    def __str__(self) -> str:
        return f"{self.namespace}:{self.key}@{self.revision}"


@dataclass(frozen=True, order=True, slots=True)
class MilestoneRecordingPolicyRef:
    namespace: str
    key: str
    revision: int

    def __post_init__(self) -> None:
        _namespace(self.namespace, "milestone recording policy namespace", InvalidMilestoneEvent)
        _key(self.key, "milestone recording policy key", InvalidMilestoneEvent)
        _revision(self.revision, "milestone recording policy revision", InvalidMilestoneEvent)

    @classmethod
    def parse(cls, value: object) -> "MilestoneRecordingPolicyRef":
        if not isinstance(value, str):
            raise InvalidMilestoneEvent("milestone recording policy ref must be a string")
        match = _REF_RE.fullmatch(value)
        if match is None:
            raise InvalidMilestoneEvent(
                "milestone recording policy ref must use '<namespace>:<key>@<revision>'"
            )
        return cls(match.group(1), match.group(2), int(match.group(3)))

    def __str__(self) -> str:
        return f"{self.namespace}:{self.key}@{self.revision}"


@dataclass(frozen=True, order=True, slots=True)
class LegendProjectionPolicyRef:
    namespace: str
    key: str
    revision: int

    def __post_init__(self) -> None:
        _namespace(self.namespace, "legend policy namespace", InvalidPersonalLegend)
        _key(self.key, "legend policy key", InvalidPersonalLegend)
        _revision(self.revision, "legend policy revision", InvalidPersonalLegend)

    @classmethod
    def parse(cls, value: object) -> "LegendProjectionPolicyRef":
        if not isinstance(value, str):
            raise InvalidPersonalLegend("legend policy ref must be a string")
        match = _REF_RE.fullmatch(value)
        if match is None:
            raise InvalidPersonalLegend(
                "legend policy ref must use '<namespace>:<key>@<revision>'"
            )
        return cls(match.group(1), match.group(2), int(match.group(3)))

    def __str__(self) -> str:
        return f"{self.namespace}:{self.key}@{self.revision}"


class AchievementBasisKind(str, Enum):
    EVIDENCE_RECORD = "evidence_record"
    CAPABILITY_CLAIM = "capability_claim"
    CLAIM_EVALUATION = "claim_evaluation"
    EXTERNAL_ARTIFACT = "external_artifact"
    OTHER = "other"


@dataclass(frozen=True, order=True, slots=True)
class AchievementBasisRef:
    kind: AchievementBasisKind
    ref: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, AchievementBasisKind):
            raise InvalidAchievementInstance("achievement basis kind must be AchievementBasisKind")
        ref = _clean_text(self.ref, "achievement basis ref", InvalidAchievementInstance)
        try:
            if self.kind is AchievementBasisKind.EVIDENCE_RECORD:
                ref = str(EvidenceId(ref))
            elif self.kind is AchievementBasisKind.CAPABILITY_CLAIM:
                ref = str(CapabilityClaimId(ref))
            elif self.kind is AchievementBasisKind.CLAIM_EVALUATION:
                ref = str(ClaimEvaluationId(ref))
        except ValueError as exc:
            raise InvalidAchievementInstance(f"invalid {self.kind.value} basis ref: {ref!r}") from exc
        object.__setattr__(self, "ref", ref)


@dataclass(frozen=True, slots=True)
class AchievementInstance:
    """Person-scoped historical accomplishment; not current capability state."""

    achievement_id: AchievementInstanceId
    subject_ref: CapabilitySubjectRef
    family_ref: AchievementFamilyRef
    achieved_at: datetime
    recorded_at: datetime
    qualification_policy_ref: AchievementQualificationPolicyRef
    qualifier_ref: AchievementQualifierRef
    basis_refs: tuple[AchievementBasisRef, ...]
    context: str
    variant: str | None = None
    record_note: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.achievement_id, AchievementInstanceId):
            raise InvalidAchievementInstance("achievement_id must be AchievementInstanceId")
        if not isinstance(self.subject_ref, CapabilitySubjectRef):
            raise InvalidAchievementInstance("subject_ref must be CapabilitySubjectRef")
        if not isinstance(self.family_ref, AchievementFamilyRef):
            raise InvalidAchievementInstance("family_ref must be AchievementFamilyRef")
        if not isinstance(self.qualification_policy_ref, AchievementQualificationPolicyRef):
            raise InvalidAchievementInstance(
                "qualification_policy_ref must be AchievementQualificationPolicyRef"
            )
        if not isinstance(self.qualifier_ref, AchievementQualifierRef):
            raise InvalidAchievementInstance("qualifier_ref must be AchievementQualifierRef")
        achieved_at = _canonical_time(self.achieved_at, "achieved_at", InvalidAchievementInstance)
        recorded_at = _canonical_time(self.recorded_at, "recorded_at", InvalidAchievementInstance)
        if recorded_at < achieved_at:
            raise InvalidAchievementInstance("recorded_at must not precede achieved_at")
        if isinstance(self.basis_refs, (str, bytes)):
            raise InvalidAchievementInstance("basis_refs must be an iterable")
        try:
            basis_refs = tuple(self.basis_refs)
        except TypeError as exc:
            raise InvalidAchievementInstance("basis_refs must be iterable") from exc
        if any(not isinstance(item, AchievementBasisRef) for item in basis_refs):
            raise InvalidAchievementInstance("basis_refs must contain AchievementBasisRef values")
        if not basis_refs:
            raise InvalidAchievementInstance("achievement requires at least one basis ref")
        if len(set(basis_refs)) != len(basis_refs):
            raise InvalidAchievementInstance("duplicate achievement basis refs are not allowed")
        if not any(
            item.kind in {AchievementBasisKind.EVIDENCE_RECORD, AchievementBasisKind.EXTERNAL_ARTIFACT}
            for item in basis_refs
        ):
            raise InvalidAchievementInstance(
                "achievement requires event-bearing EvidenceRecord or EXTERNAL_ARTIFACT basis"
            )
        context = _clean_text(self.context, "achievement context", InvalidAchievementInstance)
        variant = _clean_optional_text(self.variant, "achievement variant", InvalidAchievementInstance)
        note = _clean_optional_text(self.record_note, "achievement record_note", InvalidAchievementInstance)
        object.__setattr__(self, "achieved_at", achieved_at)
        object.__setattr__(self, "recorded_at", recorded_at)
        object.__setattr__(self, "basis_refs", tuple(sorted(basis_refs)))
        object.__setattr__(self, "context", context)
        object.__setattr__(self, "variant", variant)
        object.__setattr__(self, "record_note", note)


class MilestoneSourceKind(str, Enum):
    EVIDENCE_RECORD = "evidence_record"
    CAPABILITY_CLAIM = "capability_claim"
    CLAIM_EVALUATION = "claim_evaluation"
    ACHIEVEMENT_INSTANCE = "achievement_instance"
    EXTERNAL_ARTIFACT = "external_artifact"
    OTHER = "other"


@dataclass(frozen=True, order=True, slots=True)
class MilestoneSourceRef:
    kind: MilestoneSourceKind
    ref: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, MilestoneSourceKind):
            raise InvalidMilestoneEvent("milestone source kind must be MilestoneSourceKind")
        ref = _clean_text(self.ref, "milestone source ref", InvalidMilestoneEvent)
        try:
            if self.kind is MilestoneSourceKind.EVIDENCE_RECORD:
                ref = str(EvidenceId(ref))
            elif self.kind is MilestoneSourceKind.CAPABILITY_CLAIM:
                ref = str(CapabilityClaimId(ref))
            elif self.kind is MilestoneSourceKind.CLAIM_EVALUATION:
                ref = str(ClaimEvaluationId(ref))
            elif self.kind is MilestoneSourceKind.ACHIEVEMENT_INSTANCE:
                ref = str(AchievementInstanceId(ref))
        except ValueError as exc:
            raise InvalidMilestoneEvent(f"invalid {self.kind.value} source ref: {ref!r}") from exc
        object.__setattr__(self, "ref", ref)


@dataclass(frozen=True, slots=True)
class PersonalMilestoneEvent:
    """Person-scoped meaningful history; may be positive, negative, or neutral."""

    milestone_id: PersonalMilestoneEventId
    subject_ref: CapabilitySubjectRef
    title: str
    description: str
    significance_note: str
    occurred_at: datetime
    recorded_at: datetime
    recorder_ref: MilestoneRecorderRef
    recording_policy_ref: MilestoneRecordingPolicyRef
    source_refs: tuple[MilestoneSourceRef, ...] = ()
    tags: tuple[str, ...] = ()
    started_at: datetime | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.milestone_id, PersonalMilestoneEventId):
            raise InvalidMilestoneEvent("milestone_id must be PersonalMilestoneEventId")
        if not isinstance(self.subject_ref, CapabilitySubjectRef):
            raise InvalidMilestoneEvent("subject_ref must be CapabilitySubjectRef")
        if not isinstance(self.recorder_ref, MilestoneRecorderRef):
            raise InvalidMilestoneEvent("recorder_ref must be MilestoneRecorderRef")
        if not isinstance(self.recording_policy_ref, MilestoneRecordingPolicyRef):
            raise InvalidMilestoneEvent(
                "recording_policy_ref must be MilestoneRecordingPolicyRef"
            )
        occurred_at = _canonical_time(self.occurred_at, "occurred_at", InvalidMilestoneEvent)
        recorded_at = _canonical_time(self.recorded_at, "recorded_at", InvalidMilestoneEvent)
        if recorded_at < occurred_at:
            raise InvalidMilestoneEvent("recorded_at must not precede occurred_at")
        started_at = None
        if self.started_at is not None:
            started_at = _canonical_time(self.started_at, "started_at", InvalidMilestoneEvent)
            if started_at > occurred_at:
                raise InvalidMilestoneEvent("started_at must not follow occurred_at")
        if isinstance(self.source_refs, (str, bytes)):
            raise InvalidMilestoneEvent("source_refs must be an iterable")
        try:
            source_refs = tuple(self.source_refs)
        except TypeError as exc:
            raise InvalidMilestoneEvent("source_refs must be iterable") from exc
        if any(not isinstance(item, MilestoneSourceRef) for item in source_refs):
            raise InvalidMilestoneEvent("source_refs must contain MilestoneSourceRef values")
        if len(set(source_refs)) != len(source_refs):
            raise InvalidMilestoneEvent("duplicate milestone source refs are not allowed")
        object.__setattr__(self, "title", _clean_text(self.title, "milestone title", InvalidMilestoneEvent))
        object.__setattr__(
            self,
            "description",
            _clean_text(self.description, "milestone description", InvalidMilestoneEvent),
        )
        object.__setattr__(
            self,
            "significance_note",
            _clean_text(self.significance_note, "milestone significance_note", InvalidMilestoneEvent),
        )
        object.__setattr__(self, "occurred_at", occurred_at)
        object.__setattr__(self, "recorded_at", recorded_at)
        object.__setattr__(self, "started_at", started_at)
        object.__setattr__(self, "source_refs", tuple(sorted(source_refs)))
        object.__setattr__(self, "tags", _clean_tags(self.tags, "milestone tags", InvalidMilestoneEvent))


class LegendSourceKind(str, Enum):
    ACHIEVEMENT_INSTANCE = "achievement_instance"
    PERSONAL_MILESTONE_EVENT = "personal_milestone_event"


@dataclass(frozen=True, order=True, slots=True)
class LegendSourceRef:
    kind: LegendSourceKind
    ref: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, LegendSourceKind):
            raise InvalidPersonalLegend("legend source kind must be LegendSourceKind")
        ref = _clean_text(self.ref, "legend source ref", InvalidPersonalLegend)
        try:
            if self.kind is LegendSourceKind.ACHIEVEMENT_INSTANCE:
                ref = str(AchievementInstanceId(ref))
            else:
                ref = str(PersonalMilestoneEventId(ref))
        except ValueError as exc:
            raise InvalidPersonalLegend(f"invalid legend source ref: {ref!r}") from exc
        object.__setattr__(self, "ref", ref)


@dataclass(frozen=True, slots=True)
class PersonalLegendEntry:
    source_refs: tuple[LegendSourceRef, ...]
    heading: str
    narrative: str

    def __post_init__(self) -> None:
        if isinstance(self.source_refs, (str, bytes)):
            raise InvalidPersonalLegend("legend entry source_refs must be an iterable")
        try:
            refs = tuple(self.source_refs)
        except TypeError as exc:
            raise InvalidPersonalLegend("legend entry source_refs must be iterable") from exc
        if not refs:
            raise InvalidPersonalLegend("legend entry requires at least one history source")
        if any(not isinstance(item, LegendSourceRef) for item in refs):
            raise InvalidPersonalLegend("legend entry sources must be LegendSourceRef values")
        if len(set(refs)) != len(refs):
            raise InvalidPersonalLegend("duplicate legend entry sources are not allowed")
        object.__setattr__(self, "source_refs", tuple(sorted(refs)))
        object.__setattr__(self, "heading", _clean_text(self.heading, "legend entry heading", InvalidPersonalLegend))
        object.__setattr__(
            self,
            "narrative",
            _clean_text(self.narrative, "legend entry narrative", InvalidPersonalLegend),
        )


@dataclass(frozen=True, slots=True)
class PersonalLegend:
    """Derived narrative projection over history; never the historical source of truth."""

    legend_id: PersonalLegendId
    subject_ref: CapabilitySubjectRef
    as_of: datetime
    generated_at: datetime
    legend_policy_ref: LegendProjectionPolicyRef
    generator_ref: LegendGeneratorRef
    title: str
    summary: str
    entries: tuple[PersonalLegendEntry, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.legend_id, PersonalLegendId):
            raise InvalidPersonalLegend("legend_id must be PersonalLegendId")
        if not isinstance(self.subject_ref, CapabilitySubjectRef):
            raise InvalidPersonalLegend("subject_ref must be CapabilitySubjectRef")
        if not isinstance(self.legend_policy_ref, LegendProjectionPolicyRef):
            raise InvalidPersonalLegend("legend_policy_ref must be LegendProjectionPolicyRef")
        if not isinstance(self.generator_ref, LegendGeneratorRef):
            raise InvalidPersonalLegend("generator_ref must be LegendGeneratorRef")
        as_of = _canonical_time(self.as_of, "legend as_of", InvalidPersonalLegend)
        generated_at = _canonical_time(self.generated_at, "legend generated_at", InvalidPersonalLegend)
        if generated_at < as_of:
            raise InvalidPersonalLegend("legend generated_at must not precede as_of")
        if isinstance(self.entries, (str, bytes)):
            raise InvalidPersonalLegend("legend entries must be an iterable")
        try:
            entries = tuple(self.entries)
        except TypeError as exc:
            raise InvalidPersonalLegend("legend entries must be iterable") from exc
        if not entries:
            raise InvalidPersonalLegend("personal legend requires at least one history-backed entry")
        if any(not isinstance(item, PersonalLegendEntry) for item in entries):
            raise InvalidPersonalLegend("legend entries must contain PersonalLegendEntry values")
        object.__setattr__(self, "as_of", as_of)
        object.__setattr__(self, "generated_at", generated_at)
        object.__setattr__(self, "title", _clean_text(self.title, "legend title", InvalidPersonalLegend))
        object.__setattr__(self, "summary", _clean_text(self.summary, "legend summary", InvalidPersonalLegend))
        object.__setattr__(self, "entries", entries)

    def to_dict(self) -> dict:
        from .serialization import legend_to_dict
        return legend_to_dict(self)

    @classmethod
    def from_dict(cls, payload: object) -> "PersonalLegend":
        from .serialization import legend_from_dict
        return legend_from_dict(payload)

    def to_json(self) -> str:
        from .serialization import legend_to_json
        return legend_to_json(self)

    @classmethod
    def from_json(cls, payload: object) -> "PersonalLegend":
        from .serialization import legend_from_json
        return legend_from_json(payload)
