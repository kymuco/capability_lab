"""PR11.9 governed current-state-to-progression authority handoff v1."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import re

from capability_lab.epistemics import EpistemicRecordSet
from capability_lab.semantics import CapabilityCatalog, CapabilityConceptRef, RelationScope
from capability_lab.state import (
    CompetenceFrameCatalog,
    CompetenceFrameRef,
    CurrentStateSelectionAction,
    PersonalCapabilityCurrentStateSelection,
    PersonalCapabilityCurrentStateSelectionAuthorityBasis,
    PersonalCapabilityCurrentStateSelectionHistory,
    PersonalCapabilityState,
    PersonalCapabilityStateId,
    PersonalCapabilityStateSet,
    StateError,
    personal_capability_current_state_selection_history_sha256_v1,
    personal_capability_current_state_selection_sha256_v1,
    personal_capability_state_content_sha256_v1,
    validate_personal_capability_current_state_selection_v1,
)
from .core import (
    ExplorationInput,
    FrontierSeedBinding,
    PrerequisiteCheckBinding,
    ProgressionError,
    ProgressionFocus,
    ProgressionFrontier,
    ProgressionFrontierId,
    ProgressionFrontierRequest,
    ProgressionRequesterRef,
)
from .derivation import derive_progression_frontier_v1
from .verification import validate_progression_frontier_v1


class ProgressionAuthorityHandoffError(ProgressionError):
    """PR11.9 cannot authorize the requested personal-state input handoff."""


_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_HEX = frozenset("0123456789abcdef")
_HASH_DOMAIN = b"capability_lab/current_state_governed_progression_frontier@1\x00"


def _fail(message: str) -> None:
    raise ProgressionAuthorityHandoffError(message)


def _exact(value: object, expected: type, label: str):
    if type(value) is not expected:
        _fail(f"{label} must use exact type {expected.__name__}")
    return value


def _time(value: object, label: str) -> datetime:
    value = _exact(value, datetime, label)
    if value.tzinfo is None or value.utcoffset() is None:
        _fail(f"{label} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _sha(value: object, label: str) -> str:
    if type(value) is not str or len(value) != 64 or any(c not in _HEX for c in value):
        _fail(f"{label} must be 64 lowercase hexadecimal SHA-256 characters")
    return value


def _concept(value: object, label: str) -> CapabilityConceptRef:
    value = _exact(value, CapabilityConceptRef, label)
    try:
        restored = CapabilityConceptRef.parse(str(value))
    except (TypeError, ValueError) as exc:
        raise ProgressionAuthorityHandoffError(
            f"{label} must survive strict semantic round-trip: {exc}"
        ) from exc
    if restored != value:
        _fail(f"{label} must equal its strict semantic round-trip")
    return value


def _frame(value: object, label: str) -> CompetenceFrameRef:
    value = _exact(value, CompetenceFrameRef, label)
    try:
        restored = CompetenceFrameRef.parse(str(value))
    except (TypeError, ValueError) as exc:
        raise ProgressionAuthorityHandoffError(
            f"{label} must survive strict semantic round-trip: {exc}"
        ) from exc
    if restored != value:
        _fail(f"{label} must equal its strict semantic round-trip")
    return value


def _keys(value: object, label: str) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        _fail(f"{label} must be non-empty exact tuple")
    if any(type(item) is not str or _KEY_RE.fullmatch(item) is None for item in value):
        _fail(f"{label} must contain canonical lowercase keys")
    if len(set(value)) != len(value):
        _fail(f"{label} must not contain duplicates")
    return tuple(sorted(value))


def _scope(value: object, label: str) -> RelationScope | None:
    if value is None:
        return None
    value = _exact(value, RelationScope, label)
    try:
        restored = RelationScope(value.key, value.description)
    except (TypeError, ValueError) as exc:
        raise ProgressionAuthorityHandoffError(
            f"{label} must survive strict semantic reconstruction: {exc}"
        ) from exc
    if restored != value:
        _fail(f"{label} must equal strict semantic reconstruction")
    return value


def _strict_frontier_id(value: object) -> ProgressionFrontierId:
    value = _exact(value, ProgressionFrontierId, "frontier_id")
    try:
        restored = ProgressionFrontierId(value.value)
    except (TypeError, ValueError) as exc:
        raise ProgressionAuthorityHandoffError(
            f"frontier_id must survive strict semantic reconstruction: {exc}"
        ) from exc
    if restored != value:
        _fail("frontier_id must equal strict semantic reconstruction")
    return value


def _strict_requester(value: object) -> ProgressionRequesterRef:
    value = _exact(value, ProgressionRequesterRef, "requester_ref")
    try:
        restored = ProgressionRequesterRef(value.kind, value.ref)
    except (TypeError, ValueError) as exc:
        raise ProgressionAuthorityHandoffError(
            f"requester_ref must survive strict semantic reconstruction: {exc}"
        ) from exc
    if restored != value:
        _fail("requester_ref must equal strict semantic reconstruction")
    return value


def _strict_focus(value: object) -> ProgressionFocus:
    value = _exact(value, ProgressionFocus, "focus")
    concept_ref = _concept(value.concept_ref, "focus concept_ref")
    try:
        restored = ProgressionFocus(concept_ref, value.rationale)
    except (TypeError, ValueError) as exc:
        raise ProgressionAuthorityHandoffError(
            f"focus must survive strict semantic reconstruction: {exc}"
        ) from exc
    if restored != value:
        _fail("focus must equal strict semantic reconstruction")
    return value


def _strict_exploration(value: object) -> ExplorationInput:
    value = _exact(value, ExplorationInput, "exploration input")
    concept_ref = _concept(value.concept_ref, "exploration concept_ref")
    try:
        restored = ExplorationInput(concept_ref, value.rationale)
    except (TypeError, ValueError) as exc:
        raise ProgressionAuthorityHandoffError(
            f"exploration input must survive strict semantic reconstruction: {exc}"
        ) from exc
    if restored != value:
        _fail("exploration input must equal strict semantic reconstruction")
    return value


@dataclass(frozen=True, slots=True)
class CurrentStateProgressionSeed:
    concept_ref: CapabilityConceptRef
    frame_ref: CompetenceFrameRef
    dimension_keys: tuple[str, ...]

    def __post_init__(self) -> None:
        _concept(self.concept_ref, "seed concept_ref")
        _frame(self.frame_ref, "seed frame_ref")
        object.__setattr__(self, "dimension_keys", _keys(self.dimension_keys, "seed dimension_keys"))

    @property
    def scope_key(self):
        return self.concept_ref, self.frame_ref


@dataclass(frozen=True, slots=True)
class CurrentStatePrerequisiteCheck:
    target_ref: CapabilityConceptRef
    prerequisite_ref: CapabilityConceptRef
    relation_scope: RelationScope | None
    frame_ref: CompetenceFrameRef
    required_dimension_keys: tuple[str, ...]

    def __post_init__(self) -> None:
        _concept(self.target_ref, "prerequisite target_ref")
        _concept(self.prerequisite_ref, "prerequisite prerequisite_ref")
        if self.target_ref == self.prerequisite_ref:
            _fail("prerequisite target and prerequisite refs must differ")
        _scope(self.relation_scope, "prerequisite relation_scope")
        _frame(self.frame_ref, "prerequisite frame_ref")
        object.__setattr__(
            self,
            "required_dimension_keys",
            _keys(self.required_dimension_keys, "prerequisite required_dimension_keys"),
        )

    @property
    def scope_key(self):
        return self.prerequisite_ref, self.frame_ref

    @property
    def relation_key(self):
        return (
            str(self.target_ref),
            str(self.prerequisite_ref),
            self.relation_scope.key if self.relation_scope else "",
            self.relation_scope.description if self.relation_scope else "",
        )


def _strict_seed(value: object) -> CurrentStateProgressionSeed:
    value = _exact(value, CurrentStateProgressionSeed, "seed")
    restored = CurrentStateProgressionSeed(
        value.concept_ref,
        value.frame_ref,
        value.dimension_keys,
    )
    if restored != value:
        _fail("seed must equal strict semantic reconstruction")
    return value


def _strict_prerequisite_check(value: object) -> CurrentStatePrerequisiteCheck:
    value = _exact(value, CurrentStatePrerequisiteCheck, "prerequisite check")
    restored = CurrentStatePrerequisiteCheck(
        value.target_ref,
        value.prerequisite_ref,
        value.relation_scope,
        value.frame_ref,
        value.required_dimension_keys,
    )
    if restored != value:
        _fail("prerequisite check must equal strict semantic reconstruction")
    return value


@dataclass(frozen=True, slots=True)
class CurrentStateProgressionFrontierRequest:
    frontier_id: ProgressionFrontierId
    as_of: datetime
    generated_at: datetime
    requester_ref: ProgressionRequesterRef
    focuses: tuple[ProgressionFocus, ...] = ()
    seeds: tuple[CurrentStateProgressionSeed, ...] = ()
    prerequisite_checks: tuple[CurrentStatePrerequisiteCheck, ...] = ()
    exploration_inputs: tuple[ExplorationInput, ...] = ()

    def __post_init__(self) -> None:
        _strict_frontier_id(self.frontier_id)
        as_of = _time(self.as_of, "governed progression as_of")
        generated_at = _time(self.generated_at, "governed progression generated_at")
        if generated_at < as_of:
            _fail("generated_at must not precede as_of")
        _strict_requester(self.requester_ref)
        for label, values, expected in (
            ("focuses", self.focuses, ProgressionFocus),
            ("seeds", self.seeds, CurrentStateProgressionSeed),
            ("prerequisite_checks", self.prerequisite_checks, CurrentStatePrerequisiteCheck),
            ("exploration_inputs", self.exploration_inputs, ExplorationInput),
        ):
            if type(values) is not tuple or any(type(item) is not expected for item in values):
                _fail(f"{label} must be exact tuple of exact {expected.__name__} values")
        for item in self.focuses:
            _strict_focus(item)
        for item in self.exploration_inputs:
            _strict_exploration(item)
        for item in self.seeds:
            _strict_seed(item)
        for item in self.prerequisite_checks:
            _strict_prerequisite_check(item)
        if not (self.focuses or self.seeds or self.exploration_inputs):
            _fail("governed progression request requires seed, explicit focus, or exploration input")
        if not (self.seeds or self.prerequisite_checks):
            _fail("governed progression handoff requires at least one personal-state scope")
        if len({item.concept_ref for item in self.focuses}) != len(self.focuses):
            _fail("duplicate focus concept refs are not allowed")
        if len({item.scope_key for item in self.seeds}) != len(self.seeds):
            _fail("each exact concept/frame scope may be seeded at most once")
        if len({item.relation_key for item in self.prerequisite_checks}) != len(self.prerequisite_checks):
            _fail("each exact prerequisite relation may be checked at most once")
        if len({item.concept_ref for item in self.exploration_inputs}) != len(self.exploration_inputs):
            _fail("duplicate exploration concept refs are not allowed")
        overlap = {item.concept_ref for item in self.seeds} & {item.concept_ref for item in self.focuses}
        if overlap:
            _fail(f"explicit focus must remain distinct from governed seed concepts: {sorted(map(str, overlap))!r}")
        object.__setattr__(self, "as_of", as_of)
        object.__setattr__(self, "generated_at", generated_at)
        object.__setattr__(self, "focuses", tuple(sorted(self.focuses, key=lambda x: x.concept_ref)))
        object.__setattr__(self, "seeds", tuple(sorted(self.seeds, key=lambda x: (str(x.concept_ref), str(x.frame_ref)))))
        object.__setattr__(self, "prerequisite_checks", tuple(sorted(self.prerequisite_checks, key=lambda x: x.relation_key)))
        object.__setattr__(self, "exploration_inputs", tuple(sorted(self.exploration_inputs, key=lambda x: x.concept_ref)))


def _strict_request(value: object) -> CurrentStateProgressionFrontierRequest:
    value = _exact(value, CurrentStateProgressionFrontierRequest, "request")
    restored = CurrentStateProgressionFrontierRequest(
        value.frontier_id,
        value.as_of,
        value.generated_at,
        value.requester_ref,
        value.focuses,
        value.seeds,
        value.prerequisite_checks,
        value.exploration_inputs,
    )
    if restored != value:
        _fail("request must equal strict semantic reconstruction")
    return value


class CurrentStateProgressionAuthorityStatus(str, Enum):
    SELECT = "select"
    CLEAR = "clear"
    ABSENT = "absent"


@dataclass(frozen=True, slots=True)
class CurrentStateProgressionAuthorityBinding:
    concept_ref: CapabilityConceptRef
    frame_ref: CompetenceFrameRef
    status: CurrentStateProgressionAuthorityStatus
    current_selection_sha256: str | None = None
    selected_state_id: PersonalCapabilityStateId | None = None
    selected_state_sha256: str | None = None

    def __post_init__(self) -> None:
        _concept(self.concept_ref, "authority binding concept_ref")
        _frame(self.frame_ref, "authority binding frame_ref")
        _exact(self.status, CurrentStateProgressionAuthorityStatus, "authority binding status")
        if self.status is CurrentStateProgressionAuthorityStatus.SELECT:
            _sha(self.current_selection_sha256, "current_selection_sha256")
            _exact(self.selected_state_id, PersonalCapabilityStateId, "selected_state_id")
            _sha(self.selected_state_sha256, "selected_state_sha256")
        elif self.status is CurrentStateProgressionAuthorityStatus.CLEAR:
            _sha(self.current_selection_sha256, "current_selection_sha256")
            if self.selected_state_id is not None or self.selected_state_sha256 is not None:
                _fail("CLEAR authority binding may not carry selected state")
        elif self.status is CurrentStateProgressionAuthorityStatus.ABSENT:
            if self.current_selection_sha256 is not None or self.selected_state_id is not None or self.selected_state_sha256 is not None:
                _fail("ABSENT authority binding may not carry selection or state identity")

    @property
    def scope_key(self):
        return self.concept_ref, self.frame_ref


@dataclass(frozen=True, slots=True)
class CurrentStateGovernedProgressionFrontier:
    request: CurrentStateProgressionFrontierRequest
    current_selection_history_sha256: str
    authority_bindings: tuple[CurrentStateProgressionAuthorityBinding, ...]
    frontier: ProgressionFrontier

    def __post_init__(self) -> None:
        _strict_request(self.request)
        _sha(self.current_selection_history_sha256, "current_selection_history_sha256")
        if type(self.authority_bindings) is not tuple or any(
            type(item) is not CurrentStateProgressionAuthorityBinding for item in self.authority_bindings
        ):
            _fail("authority_bindings must be exact tuple of exact authority bindings")
        for item in self.authority_bindings:
            restored = CurrentStateProgressionAuthorityBinding(
                item.concept_ref,
                item.frame_ref,
                item.status,
                item.current_selection_sha256,
                item.selected_state_id,
                item.selected_state_sha256,
            )
            if restored != item:
                _fail("authority binding must equal strict semantic reconstruction")
        if len({item.scope_key for item in self.authority_bindings}) != len(self.authority_bindings):
            _fail("authority_bindings may contain each exact scope at most once")
        requested = {item.scope_key for item in self.request.seeds} | {
            item.scope_key for item in self.request.prerequisite_checks
        }
        if {item.scope_key for item in self.authority_bindings} != requested:
            _fail("authority_bindings must cover exactly every requested personal-state scope")
        _exact(self.frontier, ProgressionFrontier, "governed frontier raw frontier")
        for label, actual, expected in (
            ("frontier_id", self.frontier.frontier_id, self.request.frontier_id),
            ("as_of", self.frontier.as_of, self.request.as_of),
            ("generated_at", self.frontier.generated_at, self.request.generated_at),
            ("requester_ref", self.frontier.requester_ref, self.request.requester_ref),
            ("focuses", self.frontier.focuses, self.request.focuses),
            ("exploration_inputs", self.frontier.exploration_inputs, self.request.exploration_inputs),
        ):
            if actual != expected:
                _fail(f"raw frontier {label} does not match governed request")
        by_scope = {item.scope_key: item for item in self.authority_bindings}
        expected_seeds = []
        for seed in self.request.seeds:
            binding = by_scope[seed.scope_key]
            if binding.status is not CurrentStateProgressionAuthorityStatus.SELECT:
                _fail("governed seed scope must resolve to authority-valid SELECT")
            expected_seeds.append(FrontierSeedBinding(binding.selected_state_id, seed.dimension_keys))
        if self.frontier.seed_bindings != tuple(sorted(expected_seeds, key=lambda x: str(x.state_id))):
            _fail("raw frontier seed bindings do not match authority-derived current states")
        expected_checks = []
        for check in self.request.prerequisite_checks:
            binding = by_scope[check.scope_key]
            state_id = binding.selected_state_id if binding.status is CurrentStateProgressionAuthorityStatus.SELECT else None
            expected_checks.append(
                PrerequisiteCheckBinding(
                    check.target_ref,
                    check.prerequisite_ref,
                    check.relation_scope,
                    check.frame_ref,
                    check.required_dimension_keys,
                    state_id,
                )
            )
        if self.frontier.prerequisite_bindings != tuple(sorted(expected_checks, key=lambda x: x.deterministic_key)):
            _fail("raw frontier prerequisite bindings do not match authority-derived current states")
        object.__setattr__(
            self,
            "authority_bindings",
            tuple(sorted(self.authority_bindings, key=lambda x: (str(x.concept_ref), str(x.frame_ref)))),
        )


def _head(history, concept_ref, frame_ref):
    scoped = tuple(x for x in history.selections if x.concept_ref == concept_ref and x.frame_ref == frame_ref)
    if not scoped:
        return None
    predecessor_hashes = {x.predecessor_selection_sha256 for x in scoped if x.predecessor_selection_sha256 is not None}
    heads = tuple(
        x for x in scoped
        if personal_capability_current_state_selection_sha256_v1(x) not in predecessor_hashes
    )
    if len(heads) != 1:
        _fail("requested current-state scope must have exactly one structural chain head")
    return heads[0]


def _preflight_subject_authority(history, authority_bases) -> None:
    """Require subject-wide PR11.8 authority before any requested-scope resolution."""
    if not history.selections:
        if authority_bases:
            _fail("authority_bases must be empty when current-selection history is empty")
        return

    anchor = min(
        history.selections,
        key=lambda item: (
            str(item.concept_ref),
            str(item.frame_ref),
            item.selected_at,
            personal_capability_current_state_selection_sha256_v1(item),
        ),
    )
    try:
        validate_personal_capability_current_state_selection_v1(
            authority_bases=authority_bases,
            history=history,
            concept_ref=anchor.concept_ref,
            frame_ref=anchor.frame_ref,
        )
    except StateError as exc:
        raise ProgressionAuthorityHandoffError(
            f"subject-wide current-state authority preflight rejected progression history: {exc}"
        ) from exc


def _basis_for(authority_bases, selection):
    digest = personal_capability_current_state_selection_sha256_v1(selection)
    matches = tuple(
        b for b in authority_bases
        if personal_capability_current_state_selection_sha256_v1(b.selection) == digest
    )
    if len(matches) != 1:
        _fail("authority-valid SELECT must map to exactly one supplied authority basis")
    return matches[0]


def _state_for(basis, selection) -> PersonalCapabilityState:
    if selection.selected_state_id is None:
        _fail("authority-valid SELECT must carry selected_state_id")
    matches = tuple(x for x in basis.state_snapshot.states if x.state_id == selection.selected_state_id)
    if len(matches) != 1:
        _fail("authority-valid selected state must exist exactly once in replay snapshot")
    state = matches[0]
    if state.subject_ref != selection.subject_ref or state.concept_ref != selection.concept_ref or state.frame_ref != selection.frame_ref:
        _fail("authority-derived state scope does not match current selection")
    digest = personal_capability_state_content_sha256_v1(snapshot=basis.state_snapshot, state_id=state.state_id)
    if digest != selection.selected_state_sha256:
        _fail("authority-derived state content does not match current selection binding")
    return state


def _resolve_scope(history, authority_bases, concept_ref, frame_ref):
    structural_head = _head(history, concept_ref, frame_ref)
    try:
        validated = validate_personal_capability_current_state_selection_v1(
            authority_bases=authority_bases if structural_head is not None else (),
            history=history,
            concept_ref=concept_ref,
            frame_ref=frame_ref,
        )
    except StateError as exc:
        raise ProgressionAuthorityHandoffError(
            f"current-state authority replay rejected progression scope: {exc}"
        ) from exc
    if validated is not None:
        state = _state_for(_basis_for(authority_bases, validated), validated)
        return CurrentStateProgressionAuthorityBinding(
            concept_ref,
            frame_ref,
            CurrentStateProgressionAuthorityStatus.SELECT,
            personal_capability_current_state_selection_sha256_v1(validated),
            state.state_id,
            validated.selected_state_sha256,
        ), state
    if structural_head is None:
        return CurrentStateProgressionAuthorityBinding(
            concept_ref, frame_ref, CurrentStateProgressionAuthorityStatus.ABSENT
        ), None
    if structural_head.action is not CurrentStateSelectionAction.CLEAR:
        _fail("authority validator returned no current state for non-CLEAR structural head")
    return CurrentStateProgressionAuthorityBinding(
        concept_ref,
        frame_ref,
        CurrentStateProgressionAuthorityStatus.CLEAR,
        personal_capability_current_state_selection_sha256_v1(structural_head),
    ), None


def derive_progression_frontier_from_current_state_v1(
    *,
    capability_catalog: CapabilityCatalog,
    frame_catalog: CompetenceFrameCatalog,
    records: EpistemicRecordSet,
    selection_history: PersonalCapabilityCurrentStateSelectionHistory,
    authority_bases: tuple[PersonalCapabilityCurrentStateSelectionAuthorityBasis, ...],
    request: CurrentStateProgressionFrontierRequest,
) -> CurrentStateGovernedProgressionFrontier:
    """Admit only PR11.8-authorized personal states into unchanged PR8."""
    _exact(capability_catalog, CapabilityCatalog, "capability_catalog")
    _exact(frame_catalog, CompetenceFrameCatalog, "frame_catalog")
    _exact(records, EpistemicRecordSet, "records")
    _exact(selection_history, PersonalCapabilityCurrentStateSelectionHistory, "selection_history")
    _strict_request(request)
    if type(authority_bases) is not tuple or any(
        type(item) is not PersonalCapabilityCurrentStateSelectionAuthorityBasis for item in authority_bases
    ):
        _fail("authority_bases must be exact tuple of exact authority-basis values")
    try:
        history_sha = personal_capability_current_state_selection_history_sha256_v1(selection_history)
    except StateError as exc:
        raise ProgressionAuthorityHandoffError(f"invalid current-selection history: {exc}") from exc
    if any(item.selected_at > request.generated_at for item in selection_history.selections):
        _fail("selection history contains governance act after progression generated_at")

    _preflight_subject_authority(selection_history, authority_bases)

    requested_scopes = {item.scope_key for item in request.seeds} | {
        item.scope_key for item in request.prerequisite_checks
    }
    bindings = []
    by_scope = {}
    state_by_id = {}
    for scope in sorted(requested_scopes, key=lambda x: (str(x[0]), str(x[1]))):
        binding, state = _resolve_scope(selection_history, authority_bases, *scope)
        bindings.append(binding)
        by_scope[scope] = binding
        if state is not None:
            old = state_by_id.get(state.state_id)
            if old is not None and old != state:
                _fail("one authority-derived state identity maps to conflicting exact content")
            state_by_id[state.state_id] = state

    raw_seeds = []
    for seed in request.seeds:
        binding = by_scope[seed.scope_key]
        if binding.status is not CurrentStateProgressionAuthorityStatus.SELECT:
            _fail(
                "governed progression seed requires authority-valid current SELECT; "
                f"scope resolved as {binding.status.value}"
            )
        raw_seeds.append(FrontierSeedBinding(binding.selected_state_id, seed.dimension_keys))
    raw_checks = []
    for check in request.prerequisite_checks:
        binding = by_scope[check.scope_key]
        raw_checks.append(
            PrerequisiteCheckBinding(
                check.target_ref,
                check.prerequisite_ref,
                check.relation_scope,
                check.frame_ref,
                check.required_dimension_keys,
                binding.selected_state_id if binding.status is CurrentStateProgressionAuthorityStatus.SELECT else None,
            )
        )
    state_set = PersonalCapabilityStateSet(
        selection_history.subject_ref,
        tuple(sorted(state_by_id.values(), key=lambda x: x.state_id)),
    )
    try:
        raw_request = ProgressionFrontierRequest(
            request.frontier_id,
            selection_history.subject_ref,
            request.as_of,
            request.generated_at,
            request.requester_ref,
            request.focuses,
            tuple(raw_seeds),
            tuple(raw_checks),
            request.exploration_inputs,
        )
        frontier = derive_progression_frontier_v1(
            capability_catalog=capability_catalog,
            frame_catalog=frame_catalog,
            records=records,
            state_set=state_set,
            request=raw_request,
        )
        validate_progression_frontier_v1(
            capability_catalog=capability_catalog,
            frame_catalog=frame_catalog,
            records=records,
            state_set=state_set,
            frontier=frontier,
        )
    except ProgressionAuthorityHandoffError:
        raise
    except (ProgressionError, ValueError) as exc:
        raise ProgressionAuthorityHandoffError(
            f"unchanged PR8 progression rejected governed current-state handoff: {exc}"
        ) from exc
    return CurrentStateGovernedProgressionFrontier(request, history_sha, tuple(bindings), frontier)


def validate_current_state_governed_progression_frontier_v1(
    *,
    capability_catalog: CapabilityCatalog,
    frame_catalog: CompetenceFrameCatalog,
    records: EpistemicRecordSet,
    selection_history: PersonalCapabilityCurrentStateSelectionHistory,
    authority_bases: tuple[PersonalCapabilityCurrentStateSelectionAuthorityBasis, ...],
    governed_frontier: CurrentStateGovernedProgressionFrontier,
) -> None:
    """Fresh-replay PR11.8 and PR8 and require exact PR11.9 artifact equality."""
    _exact(governed_frontier, CurrentStateGovernedProgressionFrontier, "governed_frontier")
    expected = derive_progression_frontier_from_current_state_v1(
        capability_catalog=capability_catalog,
        frame_catalog=frame_catalog,
        records=records,
        selection_history=selection_history,
        authority_bases=authority_bases,
        request=governed_frontier.request,
    )
    if expected != governed_frontier:
        _fail("governed frontier does not exactly match fresh PR11.8 authority replay and unchanged PR8 deterministic derivation")


def _request_payload(request):
    return {
        "frontier_id": str(request.frontier_id),
        "as_of": _time(request.as_of, "request as_of").isoformat().replace("+00:00", "Z"),
        "generated_at": _time(request.generated_at, "request generated_at").isoformat().replace("+00:00", "Z"),
        "requester_ref": {"kind": request.requester_ref.kind.value, "ref": request.requester_ref.ref},
        "focuses": [{"concept_ref": str(x.concept_ref), "rationale": x.rationale} for x in request.focuses],
        "seeds": [
            {"concept_ref": str(x.concept_ref), "frame_ref": str(x.frame_ref), "dimension_keys": list(x.dimension_keys)}
            for x in request.seeds
        ],
        "prerequisite_checks": [
            {
                "target_ref": str(x.target_ref),
                "prerequisite_ref": str(x.prerequisite_ref),
                "relation_scope": None if x.relation_scope is None else {
                    "key": x.relation_scope.key,
                    "description": x.relation_scope.description,
                },
                "frame_ref": str(x.frame_ref),
                "required_dimension_keys": list(x.required_dimension_keys),
            }
            for x in request.prerequisite_checks
        ],
        "exploration_inputs": [{"concept_ref": str(x.concept_ref), "rationale": x.rationale} for x in request.exploration_inputs],
    }


def current_state_governed_progression_frontier_sha256_v1(
    governed_frontier: CurrentStateGovernedProgressionFrontier,
) -> str:
    """Domain-separated content digest for one PR11.9 governed artifact."""
    _exact(governed_frontier, CurrentStateGovernedProgressionFrontier, "governed_frontier")
    payload = {
        "request": _request_payload(governed_frontier.request),
        "current_selection_history_sha256": governed_frontier.current_selection_history_sha256,
        "authority_bindings": [
            {
                "concept_ref": str(x.concept_ref),
                "frame_ref": str(x.frame_ref),
                "status": x.status.value,
                "current_selection_sha256": x.current_selection_sha256,
                "selected_state_id": str(x.selected_state_id) if x.selected_state_id is not None else None,
                "selected_state_sha256": x.selected_state_sha256,
            }
            for x in governed_frontier.authority_bindings
        ],
        "frontier": governed_frontier.frontier.to_dict(),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    digest = hashlib.sha256()
    digest.update(_HASH_DOMAIN)
    digest.update(encoded)
    return digest.hexdigest()
