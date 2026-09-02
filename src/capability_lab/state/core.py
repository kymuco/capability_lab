"""PR3 personal capability state and competence-frame primitives."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import re
import unicodedata

from capability_lab.epistemics import (
    CapabilityClaimId,
    CapabilitySubjectRef,
    ClaimEvaluationId,
    ConflictStatus as EvaluationConflictStatus,
    EpistemicRecordSet,
    EvaluationConclusion,
)
from capability_lab.epistemics.core import EpistemicError, canonical_time
from capability_lab.semantics import CapabilityCatalog, CapabilityConceptRef


class StateError(ValueError):
    """Base validation error for PR3 state records."""


class InvalidStateId(StateError):
    pass


class InvalidCompetenceFrame(StateError):
    pass


class InvalidPersonalCapabilityState(StateError):
    pass


class InvalidStateSet(StateError):
    pass


_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_NAMESPACE_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*$")
_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_REF_RE = re.compile(
    r"^([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*):"
    r"([a-z][a-z0-9_]*)@([1-9][0-9]*)$"
)


def _clean_text(value: object, field_name: str, error_type: type[StateError]) -> str:
    if not isinstance(value, str):
        raise error_type(f"{field_name} must be a string")
    cleaned = unicodedata.normalize("NFC", value).strip()
    if not cleaned:
        raise error_type(f"{field_name} must be non-empty")
    return cleaned


def _opaque_id(
    value: object,
    field_name: str,
    error_type: type[StateError] = InvalidStateId,
) -> str:
    if not isinstance(value, str) or _ID_RE.fullmatch(value) is None:
        raise error_type(f"{field_name} must be a canonical opaque ASCII identifier")
    return value


def _revision(value: object, field_name: str, error_type: type[StateError]) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise error_type(f"{field_name} must be an integer >= 1")
    return value


def _namespace(value: object, field_name: str, error_type: type[StateError]) -> str:
    if not isinstance(value, str) or _NAMESPACE_RE.fullmatch(value) is None:
        raise error_type(f"{field_name} must use canonical namespace syntax")
    return value


def _key(value: object, field_name: str, error_type: type[StateError]) -> str:
    if not isinstance(value, str) or _KEY_RE.fullmatch(value) is None:
        raise error_type(f"{field_name} must use canonical lowercase key syntax")
    return value


def _state_time(value: object, field_name: str) -> datetime:
    try:
        return canonical_time(value, field_name)
    except EpistemicError as exc:
        raise InvalidPersonalCapabilityState(str(exc)) from exc


@dataclass(frozen=True, order=True, slots=True)
class PersonalCapabilityStateId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _opaque_id(self.value, "state id"))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, order=True, slots=True)
class CompetenceFrameId:
    namespace: str
    key: str

    def __post_init__(self) -> None:
        _namespace(self.namespace, "frame namespace", InvalidCompetenceFrame)
        _key(self.key, "frame key", InvalidCompetenceFrame)

    @classmethod
    def parse(cls, value: object) -> "CompetenceFrameId":
        if not isinstance(value, str) or value.count(":") != 1:
            raise InvalidCompetenceFrame("frame id must use '<namespace>:<key>'")
        namespace, key = value.split(":", 1)
        return cls(namespace, key)

    def __str__(self) -> str:
        return f"{self.namespace}:{self.key}"


@dataclass(frozen=True, order=True, slots=True)
class CompetenceFrameRef:
    frame_id: CompetenceFrameId
    revision: int

    def __post_init__(self) -> None:
        if not isinstance(self.frame_id, CompetenceFrameId):
            raise InvalidCompetenceFrame("frame ref frame_id must be CompetenceFrameId")
        _revision(self.revision, "frame revision", InvalidCompetenceFrame)

    @classmethod
    def parse(cls, value: object) -> "CompetenceFrameRef":
        if not isinstance(value, str):
            raise InvalidCompetenceFrame("frame ref must be a string")
        match = _REF_RE.fullmatch(value)
        if match is None:
            raise InvalidCompetenceFrame(
                "frame ref must use '<namespace>:<key>@<revision>'"
            )
        return cls(
            CompetenceFrameId(match.group(1), match.group(2)),
            int(match.group(3)),
        )

    def __str__(self) -> str:
        return f"{self.frame_id}@{self.revision}"


@dataclass(frozen=True, order=True, slots=True)
class StateDerivationPolicyRef:
    namespace: str
    key: str
    revision: int

    def __post_init__(self) -> None:
        _namespace(
            self.namespace,
            "state derivation policy namespace",
            InvalidPersonalCapabilityState,
        )
        _key(
            self.key,
            "state derivation policy key",
            InvalidPersonalCapabilityState,
        )
        _revision(
            self.revision,
            "state derivation policy revision",
            InvalidPersonalCapabilityState,
        )

    @classmethod
    def parse(cls, value: object) -> "StateDerivationPolicyRef":
        if not isinstance(value, str):
            raise InvalidPersonalCapabilityState(
                "state derivation policy ref must be a string"
            )
        match = _REF_RE.fullmatch(value)
        if match is None:
            raise InvalidPersonalCapabilityState(
                "state derivation policy ref must use '<namespace>:<key>@<revision>'"
            )
        return cls(match.group(1), match.group(2), int(match.group(3)))

    def __str__(self) -> str:
        return f"{self.namespace}:{self.key}@{self.revision}"


@dataclass(frozen=True, order=True, slots=True)
class CompetenceDimensionDefinition:
    key: str
    name: str
    description: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "key",
            _key(self.key, "dimension key", InvalidCompetenceFrame),
        )
        object.__setattr__(
            self,
            "name",
            _clean_text(self.name, "dimension name", InvalidCompetenceFrame),
        )
        object.__setattr__(
            self,
            "description",
            _clean_text(
                self.description,
                "dimension description",
                InvalidCompetenceFrame,
            ),
        )


@dataclass(frozen=True, slots=True)
class CompetenceFrame:
    frame_id: CompetenceFrameId
    revision: int
    name: str
    description: str
    dimensions: tuple[CompetenceDimensionDefinition, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.frame_id, CompetenceFrameId):
            raise InvalidCompetenceFrame("frame_id must be CompetenceFrameId")
        revision = _revision(self.revision, "frame revision", InvalidCompetenceFrame)
        name = _clean_text(self.name, "frame name", InvalidCompetenceFrame)
        description = _clean_text(
            self.description,
            "frame description",
            InvalidCompetenceFrame,
        )
        if isinstance(self.dimensions, (str, bytes)):
            raise InvalidCompetenceFrame("dimensions must be an iterable")
        try:
            dimensions = tuple(self.dimensions)
        except TypeError as exc:
            raise InvalidCompetenceFrame("dimensions must be iterable") from exc
        if not dimensions:
            raise InvalidCompetenceFrame(
                "competence frame requires at least one dimension"
            )
        if any(
            not isinstance(item, CompetenceDimensionDefinition)
            for item in dimensions
        ):
            raise InvalidCompetenceFrame(
                "dimensions must contain CompetenceDimensionDefinition values"
            )
        keys = [item.key for item in dimensions]
        if len(set(keys)) != len(keys):
            raise InvalidCompetenceFrame(
                "duplicate dimension keys are not allowed within one frame"
            )
        object.__setattr__(self, "revision", revision)
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "description", description)
        object.__setattr__(
            self,
            "dimensions",
            tuple(sorted(dimensions, key=lambda item: item.key)),
        )

    @property
    def ref(self) -> CompetenceFrameRef:
        return CompetenceFrameRef(self.frame_id, self.revision)


@dataclass(frozen=True, slots=True)
class CompetenceFrameCatalog:
    """Deterministic shared frame snapshot, not a universal human ontology."""

    frames: tuple[CompetenceFrame, ...] = ()

    def __post_init__(self) -> None:
        if isinstance(self.frames, (str, bytes)):
            raise InvalidCompetenceFrame("frames must be an iterable")
        try:
            frames = tuple(self.frames)
        except TypeError as exc:
            raise InvalidCompetenceFrame("frames must be iterable") from exc
        if any(not isinstance(item, CompetenceFrame) for item in frames):
            raise InvalidCompetenceFrame(
                "frames must contain CompetenceFrame values"
            )
        frames = tuple(sorted(frames, key=lambda item: item.frame_id))
        ids = [item.frame_id for item in frames]
        if len(set(ids)) != len(ids):
            raise InvalidCompetenceFrame(
                "a frame catalog may contain at most one current revision per frame id"
            )
        object.__setattr__(self, "frames", frames)

    def to_dict(self):
        from .serialization import frame_catalog_to_dict

        return frame_catalog_to_dict(self)

    @classmethod
    def from_dict(cls, payload):
        from .serialization import frame_catalog_from_dict

        return frame_catalog_from_dict(payload)

    def to_json(self) -> str:
        from .serialization import dumps_canonical

        return dumps_canonical(self.to_dict())

    @classmethod
    def from_json(cls, payload: str) -> "CompetenceFrameCatalog":
        from .serialization import loads_frame_catalog

        return loads_frame_catalog(payload)


class StateDeriverKind(str, Enum):
    HUMAN = "human"
    RULE = "rule"
    MODEL = "model"
    HYBRID = "hybrid"
    EXTERNAL_SYSTEM = "external_system"


@dataclass(frozen=True, order=True, slots=True)
class StateDeriverRef:
    kind: StateDeriverKind
    ref: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, StateDeriverKind):
            raise InvalidPersonalCapabilityState(
                "state deriver kind must be StateDeriverKind"
            )
        object.__setattr__(
            self,
            "ref",
            _opaque_id(
                self.ref,
                "state deriver ref",
                InvalidPersonalCapabilityState,
            ),
        )


class DimensionStanding(str, Enum):
    """Support-content standing; conflict is represented independently."""

    UNKNOWN = "unknown"
    INSUFFICIENT = "insufficient"
    SUPPORTED = "supported"


class DimensionConflictStatus(str, Enum):
    """Dimension-level conflict state independent from support standing."""

    NONE = "none"
    RESOLVED_BY_POLICY = "resolved_by_policy"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True, slots=True)
class CompetenceDimensionState:
    dimension_key: str
    standing: DimensionStanding
    supported_claim_ids: tuple[CapabilityClaimId, ...] = ()
    basis_evaluation_ids: tuple[ClaimEvaluationId, ...] = ()
    rationale: str = ""
    conflict_status: DimensionConflictStatus = DimensionConflictStatus.NONE

    def __post_init__(self) -> None:
        key = _key(
            self.dimension_key,
            "dimension state key",
            InvalidPersonalCapabilityState,
        )
        if not isinstance(self.standing, DimensionStanding):
            raise InvalidPersonalCapabilityState(
                "dimension standing must be DimensionStanding"
            )
        if not isinstance(self.conflict_status, DimensionConflictStatus):
            raise InvalidPersonalCapabilityState(
                "dimension conflict_status must be DimensionConflictStatus"
            )
        if isinstance(self.supported_claim_ids, (str, bytes)) or isinstance(
            self.basis_evaluation_ids,
            (str, bytes),
        ):
            raise InvalidPersonalCapabilityState(
                "dimension claim/evaluation references must be iterables"
            )
        try:
            claims = tuple(self.supported_claim_ids)
            evaluations = tuple(self.basis_evaluation_ids)
        except TypeError as exc:
            raise InvalidPersonalCapabilityState(
                "dimension claim/evaluation references must be iterable"
            ) from exc
        if any(not isinstance(item, CapabilityClaimId) for item in claims):
            raise InvalidPersonalCapabilityState(
                "supported_claim_ids must contain CapabilityClaimId values"
            )
        if any(not isinstance(item, ClaimEvaluationId) for item in evaluations):
            raise InvalidPersonalCapabilityState(
                "basis_evaluation_ids must contain ClaimEvaluationId values"
            )
        if len(set(claims)) != len(claims):
            raise InvalidPersonalCapabilityState(
                "duplicate supported claim references are not allowed"
            )
        if len(set(evaluations)) != len(evaluations):
            raise InvalidPersonalCapabilityState(
                "duplicate basis evaluation references are not allowed"
            )
        rationale = _clean_text(
            self.rationale,
            "dimension rationale",
            InvalidPersonalCapabilityState,
        )

        if self.standing is DimensionStanding.UNKNOWN:
            if claims or evaluations:
                raise InvalidPersonalCapabilityState(
                    "UNKNOWN dimension must not carry supported claims or basis evaluations"
                )
            if self.conflict_status is not DimensionConflictStatus.NONE:
                raise InvalidPersonalCapabilityState(
                    "UNKNOWN dimension must not declare dimension conflict"
                )

        if self.standing is DimensionStanding.INSUFFICIENT:
            if claims:
                raise InvalidPersonalCapabilityState(
                    "INSUFFICIENT dimension must not claim supported content"
                )
            if not evaluations:
                raise InvalidPersonalCapabilityState(
                    "INSUFFICIENT dimension requires at least one basis evaluation"
                )

        if self.standing is DimensionStanding.SUPPORTED:
            if not claims:
                raise InvalidPersonalCapabilityState(
                    "SUPPORTED dimension requires at least one supported claim"
                )
            if not evaluations:
                raise InvalidPersonalCapabilityState(
                    "SUPPORTED dimension requires at least one basis evaluation"
                )

        if (
            self.conflict_status is not DimensionConflictStatus.NONE
            and not evaluations
        ):
            raise InvalidPersonalCapabilityState(
                "dimension conflict requires at least one basis evaluation"
            )

        object.__setattr__(self, "dimension_key", key)
        object.__setattr__(self, "supported_claim_ids", tuple(sorted(claims)))
        object.__setattr__(
            self,
            "basis_evaluation_ids",
            tuple(sorted(evaluations)),
        )
        object.__setattr__(self, "rationale", rationale)


@dataclass(frozen=True, slots=True)
class PersonalCapabilityState:
    state_id: PersonalCapabilityStateId
    subject_ref: CapabilitySubjectRef
    concept_ref: CapabilityConceptRef
    frame_ref: CompetenceFrameRef
    derivation_policy_ref: StateDerivationPolicyRef
    deriver_ref: StateDeriverRef
    as_of: datetime
    derived_at: datetime
    dimensions: tuple[CompetenceDimensionState, ...]
    rationale: str

    def __post_init__(self) -> None:
        if not isinstance(self.state_id, PersonalCapabilityStateId):
            raise InvalidPersonalCapabilityState(
                "state_id must be PersonalCapabilityStateId"
            )
        if not isinstance(self.subject_ref, CapabilitySubjectRef):
            raise InvalidPersonalCapabilityState(
                "subject_ref must be CapabilitySubjectRef"
            )
        if not isinstance(self.concept_ref, CapabilityConceptRef):
            raise InvalidPersonalCapabilityState(
                "concept_ref must be exact CapabilityConceptRef"
            )
        if not isinstance(self.frame_ref, CompetenceFrameRef):
            raise InvalidPersonalCapabilityState(
                "frame_ref must be exact CompetenceFrameRef"
            )
        if not isinstance(self.derivation_policy_ref, StateDerivationPolicyRef):
            raise InvalidPersonalCapabilityState(
                "derivation_policy_ref must be StateDerivationPolicyRef"
            )
        if not isinstance(self.deriver_ref, StateDeriverRef):
            raise InvalidPersonalCapabilityState(
                "deriver_ref must be StateDeriverRef"
            )
        as_of = _state_time(self.as_of, "state as_of")
        derived_at = _state_time(self.derived_at, "state derived_at")
        if derived_at < as_of:
            raise InvalidPersonalCapabilityState(
                "derived_at must not precede as_of"
            )
        if isinstance(self.dimensions, (str, bytes)):
            raise InvalidPersonalCapabilityState("dimensions must be an iterable")
        try:
            dimensions = tuple(self.dimensions)
        except TypeError as exc:
            raise InvalidPersonalCapabilityState(
                "dimensions must be iterable"
            ) from exc
        if not dimensions:
            raise InvalidPersonalCapabilityState(
                "personal capability state requires at least one dimension"
            )
        if any(
            not isinstance(item, CompetenceDimensionState)
            for item in dimensions
        ):
            raise InvalidPersonalCapabilityState(
                "dimensions must contain CompetenceDimensionState values"
            )
        keys = [item.dimension_key for item in dimensions]
        if len(set(keys)) != len(keys):
            raise InvalidPersonalCapabilityState(
                "duplicate dimension state keys are not allowed"
            )
        object.__setattr__(self, "as_of", as_of)
        object.__setattr__(self, "derived_at", derived_at)
        object.__setattr__(
            self,
            "dimensions",
            tuple(sorted(dimensions, key=lambda item: item.dimension_key)),
        )
        object.__setattr__(
            self,
            "rationale",
            _clean_text(
                self.rationale,
                "state rationale",
                InvalidPersonalCapabilityState,
            ),
        )


@dataclass(frozen=True, slots=True)
class PersonalCapabilityStateSet:
    """Private one-subject collection of immutable derived state records."""

    subject_ref: CapabilitySubjectRef
    states: tuple[PersonalCapabilityState, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.subject_ref, CapabilitySubjectRef):
            raise InvalidStateSet(
                "state set subject_ref must be CapabilitySubjectRef"
            )
        if isinstance(self.states, (str, bytes)):
            raise InvalidStateSet("states must be an iterable")
        try:
            states = tuple(self.states)
        except TypeError as exc:
            raise InvalidStateSet("states must be iterable") from exc
        if any(not isinstance(item, PersonalCapabilityState) for item in states):
            raise InvalidStateSet(
                "states must contain PersonalCapabilityState values"
            )
        if any(item.subject_ref != self.subject_ref for item in states):
            raise InvalidStateSet(
                "all states in a state set must belong to exactly one subject"
            )
        ids = [item.state_id for item in states]
        if len(set(ids)) != len(ids):
            raise InvalidStateSet(
                "duplicate personal capability state ids are not allowed"
            )
        states = tuple(
            sorted(
                states,
                key=lambda item: (
                    str(item.concept_ref),
                    str(item.frame_ref),
                    str(item.derivation_policy_ref),
                    item.as_of,
                    item.derived_at,
                    str(item.state_id),
                ),
            )
        )
        object.__setattr__(self, "states", states)

    def validate_against_epistemics(self, records: EpistemicRecordSet) -> None:
        if not isinstance(records, EpistemicRecordSet):
            raise InvalidStateSet("records must be EpistemicRecordSet")
        claims = {item.claim_id: item for item in records.claims}
        evaluations = {
            item.evaluation_id: item for item in records.evaluations
        }

        for state in self.states:
            basis_by_dimension: dict[str, tuple] = {}
            state_directional_by_claim: dict[
                CapabilityClaimId, set[EvaluationConclusion]
            ] = {}
            state_unresolved_claims: set[CapabilityClaimId] = set()

            for dimension in state.dimensions:
                basis = []
                for evaluation_id in dimension.basis_evaluation_ids:
                    evaluation = evaluations.get(evaluation_id)
                    if evaluation is None:
                        raise InvalidStateSet(
                            f"state references missing claim evaluation: {evaluation_id}"
                        )
                    claim = claims.get(evaluation.claim_id)
                    if claim is None:
                        raise InvalidStateSet(
                            "basis evaluation references missing claim: "
                            f"{evaluation.claim_id}"
                        )
                    if claim.subject_ref != state.subject_ref:
                        raise InvalidStateSet(
                            "state basis evaluation belongs to a different subject"
                        )
                    if claim.concept_ref != state.concept_ref:
                        raise InvalidStateSet(
                            "state basis evaluation belongs to a different capability concept revision"
                        )
                    if evaluation.evaluated_at > state.as_of:
                        raise InvalidStateSet(
                            "state may not use an evaluation produced after its as_of boundary"
                        )
                    basis.append(evaluation)
                    if (
                        evaluation.conflict_status
                        is EvaluationConflictStatus.UNRESOLVED
                    ):
                        state_unresolved_claims.add(evaluation.claim_id)
                    if evaluation.conclusion in {
                        EvaluationConclusion.SUPPORTED,
                        EvaluationConclusion.CONTRADICTED,
                    }:
                        state_directional_by_claim.setdefault(
                            evaluation.claim_id,
                            set(),
                        ).add(evaluation.conclusion)
                basis_by_dimension[dimension.dimension_key] = tuple(basis)

            state_conflicted_claims = set(state_unresolved_claims)
            for claim_id, conclusions in state_directional_by_claim.items():
                if {
                    EvaluationConclusion.SUPPORTED,
                    EvaluationConclusion.CONTRADICTED,
                }.issubset(conclusions):
                    state_conflicted_claims.add(claim_id)

            for dimension in state.dimensions:
                basis = basis_by_dimension[dimension.dimension_key]
                dimension_claim_ids = {
                    evaluation.claim_id for evaluation in basis
                }
                if (
                    dimension_claim_ids & state_conflicted_claims
                    and dimension.conflict_status is DimensionConflictStatus.NONE
                ):
                    raise InvalidStateSet(
                        "dimension must not hide unresolved or cross-evaluation conflict "
                        "for a claim represented elsewhere in the same state basis"
                    )

                for claim_id in dimension.supported_claim_ids:
                    claim = claims.get(claim_id)
                    if claim is None:
                        raise InvalidStateSet(
                            f"state references missing supported claim: {claim_id}"
                        )
                    if claim.subject_ref != state.subject_ref:
                        raise InvalidStateSet(
                            "supported claim belongs to a different subject"
                        )
                    if claim.concept_ref != state.concept_ref:
                        raise InvalidStateSet(
                            "supported claim belongs to a different capability concept revision"
                        )
                    if not any(
                        evaluation.claim_id == claim_id
                        and evaluation.conclusion is EvaluationConclusion.SUPPORTED
                        for evaluation in basis
                    ):
                        raise InvalidStateSet(
                            "every supported state claim requires a basis ClaimEvaluation with SUPPORTED conclusion"
                        )

    def validate_against_capability_catalog(
        self,
        catalog: CapabilityCatalog,
    ) -> None:
        if not isinstance(catalog, CapabilityCatalog):
            raise InvalidStateSet("catalog must be CapabilityCatalog")
        concepts = {item.capability_id: item for item in catalog.concepts}
        for state in self.states:
            concept = concepts.get(state.concept_ref.capability_id)
            if concept is None:
                raise InvalidStateSet(
                    "state references capability absent from catalog: "
                    f"{state.concept_ref}"
                )
            if concept.revision != state.concept_ref.revision:
                raise InvalidStateSet(
                    f"state requires exact capability revision {state.concept_ref}; "
                    f"current catalog has {concept.ref}"
                )

    def validate_against_frame_catalog(
        self,
        catalog: CompetenceFrameCatalog,
    ) -> None:
        if not isinstance(catalog, CompetenceFrameCatalog):
            raise InvalidStateSet("catalog must be CompetenceFrameCatalog")
        frames = {item.frame_id: item for item in catalog.frames}
        for state in self.states:
            frame = frames.get(state.frame_ref.frame_id)
            if frame is None:
                raise InvalidStateSet(
                    "state references competence frame absent from catalog: "
                    f"{state.frame_ref}"
                )
            if frame.revision != state.frame_ref.revision:
                raise InvalidStateSet(
                    f"state requires exact frame revision {state.frame_ref}; "
                    f"current catalog has {frame.ref}"
                )
            expected = {item.key for item in frame.dimensions}
            actual = {item.dimension_key for item in state.dimensions}
            if actual != expected:
                missing = sorted(expected - actual)
                extra = sorted(actual - expected)
                raise InvalidStateSet(
                    "state dimensions must exactly match frame; "
                    f"missing={missing!r}, extra={extra!r}"
                )

    def to_dict(self):
        from .serialization import state_set_to_dict

        return state_set_to_dict(self)

    @classmethod
    def from_dict(cls, payload):
        from .serialization import state_set_from_dict

        return state_set_from_dict(payload)

    def to_json(self) -> str:
        from .serialization import dumps_canonical

        return dumps_canonical(self.to_dict())

    @classmethod
    def from_json(cls, payload: str) -> "PersonalCapabilityStateSet":
        from .serialization import loads_state_set

        return loads_state_set(payload)
