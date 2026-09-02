"""PR11.8 complete accepted-candidate current-state selection governance v1."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import re
import unicodedata

from capability_lab.epistemics import CapabilitySubjectRef
from capability_lab.semantics import CapabilityConceptRef

from .acceptance import (
    PersonalCapabilityStateAcceptance,
    personal_capability_state_content_sha256_v1,
)
from .acceptance_set import (
    PersonalCapabilityStateAcceptanceAdmission,
    PersonalCapabilityStateAcceptanceSet,
    _acceptance_canonical_payload_v1,
    personal_capability_state_acceptance_set_sha256_v1,
    validate_personal_capability_state_acceptance_set_successor_v1,
)
from .core import (
    CompetenceFrameRef,
    PersonalCapabilityState,
    PersonalCapabilityStateId,
    PersonalCapabilityStateSet,
    StateError,
)
from .snapshot_transition import personal_capability_state_set_sha256_v1


class CurrentStateSelectionError(StateError):
    """Base error for governed current-state selection."""


class InvalidCurrentStateSelection(CurrentStateSelectionError):
    """The supplied current-state candidate, request, record, or history is invalid."""


_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_NAMESPACE_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*$")
_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_POLICY_RE = re.compile(
    r"^([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*):"
    r"([a-z][a-z0-9_]*)@([1-9][0-9]*)$"
)
_SHA256_HEX_DIGITS = frozenset("0123456789abcdef")
_CANDIDATE_PORTFOLIO_HASH_DOMAIN_V1 = (
    b"capability_lab/current_state_candidate_portfolio@1\x00"
)
_CURRENT_SELECTION_HASH_DOMAIN_V1 = (
    b"capability_lab/personal_capability_current_state_selection@1\x00"
)
_CURRENT_SELECTION_HISTORY_HASH_DOMAIN_V1 = (
    b"capability_lab/personal_capability_current_state_selection_history@1\x00"
)


def _fail(message: str) -> None:
    raise InvalidCurrentStateSelection(message)


def _exact_type(value: object, expected_type: type, field_name: str) -> None:
    if type(value) is not expected_type:
        _fail(f"{field_name} must use exact type {expected_type.__name__}")


def _exact_str(value: object, field_name: str) -> str:
    if type(value) is not str:
        _fail(f"{field_name} must be exact str")
    return value


def _opaque_id(value: object, field_name: str) -> str:
    value = _exact_str(value, field_name)
    if _ID_RE.fullmatch(value) is None:
        _fail(f"{field_name} must be a canonical opaque ASCII identifier")
    return value


def _canonical_text(value: object, field_name: str) -> str:
    value = _exact_str(value, field_name)
    cleaned = unicodedata.normalize("NFC", value).strip()
    if not cleaned:
        _fail(f"{field_name} must be non-empty")
    return cleaned


def _require_canonical_text(value: object, field_name: str) -> str:
    cleaned = _canonical_text(value, field_name)
    if value != cleaned:
        _fail(f"{field_name} must already be canonical NFC-trimmed text")
    return cleaned


def _canonical_time(value: object, field_name: str) -> datetime:
    _exact_type(value, datetime, field_name)
    if value.tzinfo is None or value.utcoffset() is None:
        _fail(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _require_canonical_time(value: object, field_name: str) -> datetime:
    canonical = _canonical_time(value, field_name)
    if value.tzinfo is not timezone.utc:
        _fail(f"{field_name} must already be normalized to UTC")
    return canonical


def _utc_text(value: datetime, field_name: str) -> str:
    value = _require_canonical_time(value, field_name)
    return value.isoformat().replace("+00:00", "Z")


def _validate_sha256(value: object, field_name: str) -> str:
    value = _exact_str(value, field_name)
    if len(value) != 64 or any(character not in _SHA256_HEX_DIGITS for character in value):
        _fail(f"{field_name} must be 64 lowercase hexadecimal SHA-256 characters")
    return value


def _subject(value: object, field_name: str) -> CapabilitySubjectRef:
    _exact_type(value, CapabilitySubjectRef, field_name)
    _opaque_id(value.value, f"{field_name}.value")
    return value


def _concept(value: object, field_name: str) -> CapabilityConceptRef:
    _exact_type(value, CapabilityConceptRef, field_name)
    try:
        restored = CapabilityConceptRef.parse(str(value))
    except (TypeError, ValueError) as exc:
        raise InvalidCurrentStateSelection(
            f"{field_name} must survive strict semantic round-trip: {exc}"
        ) from exc
    if restored != value:
        _fail(f"{field_name} must equal its strict semantic round-trip")
    return value


def _frame(value: object, field_name: str) -> CompetenceFrameRef:
    _exact_type(value, CompetenceFrameRef, field_name)
    try:
        restored = CompetenceFrameRef.parse(str(value))
    except (TypeError, ValueError) as exc:
        raise InvalidCurrentStateSelection(
            f"{field_name} must survive strict semantic round-trip: {exc}"
        ) from exc
    if restored != value:
        _fail(f"{field_name} must equal its strict semantic round-trip")
    return value


def _state_id(value: object, field_name: str) -> PersonalCapabilityStateId:
    _exact_type(value, PersonalCapabilityStateId, field_name)
    _opaque_id(value.value, f"{field_name}.value")
    return value


def _state_by_id(
    snapshot: PersonalCapabilityStateSet,
    state_id: PersonalCapabilityStateId,
) -> PersonalCapabilityState:
    for state in snapshot.states:
        if state.state_id == state_id:
            return state
    _fail(f"selected current state is absent from persisted snapshot: {state_id}")


def _json_sha256(domain: bytes, payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    digest = hashlib.sha256()
    digest.update(domain)
    digest.update(encoded)
    return digest.hexdigest()


class CurrentStateSelectionAction(str, Enum):
    SELECT = "select"
    CLEAR = "clear"


class CurrentStateSelectionMechanismKind(str, Enum):
    HUMAN = "human"
    RULE = "rule"
    MODEL = "model"
    HYBRID = "hybrid"
    EXTERNAL_SYSTEM = "external_system"


@dataclass(frozen=True, order=True, slots=True)
class CurrentStateSelectionPolicyRef:
    namespace: str
    key: str
    revision: int

    def __post_init__(self) -> None:
        namespace = _exact_str(self.namespace, "current selection policy namespace")
        key = _exact_str(self.key, "current selection policy key")
        if _NAMESPACE_RE.fullmatch(namespace) is None:
            _fail("current selection policy namespace must use canonical namespace syntax")
        if _KEY_RE.fullmatch(key) is None:
            _fail("current selection policy key must use canonical lowercase key syntax")
        if type(self.revision) is not int or self.revision < 1:
            _fail("current selection policy revision must be an exact integer >= 1")

    @classmethod
    def parse(cls, value: object) -> "CurrentStateSelectionPolicyRef":
        value = _exact_str(value, "current selection policy ref")
        match = _POLICY_RE.fullmatch(value)
        if match is None:
            _fail("current selection policy ref must use '<namespace>:<key>@<revision>'")
        return cls(match.group(1), match.group(2), int(match.group(3)))

    def __str__(self) -> str:
        return f"{self.namespace}:{self.key}@{self.revision}"


@dataclass(frozen=True, order=True, slots=True)
class CurrentStateSelectorRef:
    kind: CurrentStateSelectionMechanismKind
    ref: str

    def __post_init__(self) -> None:
        _exact_type(
            self.kind,
            CurrentStateSelectionMechanismKind,
            "current state selector kind",
        )
        _exact_str(self.kind.value, "current state selector kind value")
        object.__setattr__(
            self,
            "ref",
            _opaque_id(self.ref, "current state selector ref"),
        )


@dataclass(frozen=True, slots=True)
class CurrentStateCandidatePortfolioEntry:
    state_id: PersonalCapabilityStateId
    accepted_state_sha256: str
    acceptances: tuple[PersonalCapabilityStateAcceptance, ...]

    def __post_init__(self) -> None:
        _state_id(self.state_id, "candidate state_id")
        _validate_sha256(self.accepted_state_sha256, "candidate accepted_state_sha256")
        if type(self.acceptances) is not tuple or not self.acceptances:
            _fail("candidate acceptances must be a non-empty exact tuple")
        if any(type(item) is not PersonalCapabilityStateAcceptance for item in self.acceptances):
            _fail("candidate acceptances must contain exact acceptance values")
        if len(set(self.acceptances)) != len(self.acceptances):
            _fail("candidate acceptances must not contain duplicates")
        if any(item.state_id != self.state_id for item in self.acceptances):
            _fail("candidate acceptances must all bind the candidate state_id")
        if any(
            item.accepted_state_sha256 != self.accepted_state_sha256
            for item in self.acceptances
        ):
            _fail("candidate acceptances must all bind the same exact state content")
        ordered = tuple(
            sorted(
                self.acceptances,
                key=lambda item: json.dumps(
                    _acceptance_canonical_payload_v1(item),
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                ),
            )
        )
        object.__setattr__(self, "acceptances", ordered)


@dataclass(frozen=True, slots=True)
class CurrentStateCandidatePortfolioReceipt:
    state_snapshot_sha256: str
    acceptance_set_sha256: str
    subject_ref: CapabilitySubjectRef
    concept_ref: CapabilityConceptRef
    frame_ref: CompetenceFrameRef
    as_of: datetime
    entries: tuple[CurrentStateCandidatePortfolioEntry, ...] = ()

    def __post_init__(self) -> None:
        _validate_sha256(self.state_snapshot_sha256, "state_snapshot_sha256")
        _validate_sha256(self.acceptance_set_sha256, "acceptance_set_sha256")
        _subject(self.subject_ref, "candidate portfolio subject_ref")
        _concept(self.concept_ref, "candidate portfolio concept_ref")
        _frame(self.frame_ref, "candidate portfolio frame_ref")
        object.__setattr__(
            self,
            "as_of",
            _canonical_time(self.as_of, "candidate portfolio as_of"),
        )
        if type(self.entries) is not tuple:
            _fail("candidate portfolio entries must be exact tuple")
        if any(type(item) is not CurrentStateCandidatePortfolioEntry for item in self.entries):
            _fail("candidate portfolio entries must contain exact candidate entries")
        ids = tuple(item.state_id for item in self.entries)
        if len(set(ids)) != len(ids):
            _fail("candidate portfolio may contain each state at most once")
        object.__setattr__(
            self,
            "entries",
            tuple(sorted(self.entries, key=lambda item: item.state_id)),
        )

    @property
    def candidate_state_ids(self) -> tuple[PersonalCapabilityStateId, ...]:
        return tuple(item.state_id for item in self.entries)

    @property
    def validator_issued(self) -> bool:
        return type(self) is _ValidatorIssuedCurrentStateCandidatePortfolioReceipt


class _ValidatorIssuedCurrentStateCandidatePortfolioReceipt(
    CurrentStateCandidatePortfolioReceipt
):
    __slots__ = ()


def build_complete_current_state_candidate_portfolio_v1(
    *,
    state_snapshot: PersonalCapabilityStateSet,
    acceptance_set: PersonalCapabilityStateAcceptanceSet,
    concept_ref: CapabilityConceptRef,
    frame_ref: CompetenceFrameRef,
    as_of: datetime,
) -> CurrentStateCandidatePortfolioReceipt:
    """Build every accepted state in the exact subject/concept/frame/time scope."""

    state_snapshot_sha256 = personal_capability_state_set_sha256_v1(state_snapshot)
    _concept(concept_ref, "concept_ref")
    _frame(frame_ref, "frame_ref")
    boundary = _canonical_time(as_of, "candidate portfolio as_of")
    acceptance_set_sha256 = personal_capability_state_acceptance_set_sha256_v1(
        state_snapshot=state_snapshot,
        acceptance_set=acceptance_set,
    )
    if acceptance_set.subject_ref != state_snapshot.subject_ref:
        _fail("state snapshot and acceptance set must belong to the same subject")

    grouped: dict[
        PersonalCapabilityStateId,
        list[PersonalCapabilityStateAcceptance],
    ] = {}
    for acceptance in acceptance_set.acceptances:
        if acceptance.accepted_at > boundary:
            continue
        state = _state_by_id(state_snapshot, acceptance.state_id)
        if state.concept_ref != concept_ref or state.frame_ref != frame_ref:
            continue
        grouped.setdefault(state.state_id, []).append(acceptance)

    entries = []
    for state_id in sorted(grouped):
        state = _state_by_id(state_snapshot, state_id)
        state_sha256 = personal_capability_state_content_sha256_v1(
            snapshot=state_snapshot,
            state_id=state_id,
        )
        entries.append(
            CurrentStateCandidatePortfolioEntry(
                state_id=state.state_id,
                accepted_state_sha256=state_sha256,
                acceptances=tuple(grouped[state_id]),
            )
        )

    return _ValidatorIssuedCurrentStateCandidatePortfolioReceipt(
        state_snapshot_sha256=state_snapshot_sha256,
        acceptance_set_sha256=acceptance_set_sha256,
        subject_ref=state_snapshot.subject_ref,
        concept_ref=concept_ref,
        frame_ref=frame_ref,
        as_of=boundary,
        entries=tuple(entries),
    )


def current_state_candidate_portfolio_sha256_v1(
    portfolio: CurrentStateCandidatePortfolioReceipt,
) -> str:
    _exact_type(
        portfolio,
        _ValidatorIssuedCurrentStateCandidatePortfolioReceipt,
        "candidate portfolio",
    )
    payload = {
        "state_snapshot_sha256": portfolio.state_snapshot_sha256,
        "acceptance_set_sha256": portfolio.acceptance_set_sha256,
        "subject_ref": portfolio.subject_ref.value,
        "concept_ref": str(portfolio.concept_ref),
        "frame_ref": str(portfolio.frame_ref),
        "as_of": _utc_text(portfolio.as_of, "candidate portfolio as_of"),
        "entries": [
            {
                "state_id": entry.state_id.value,
                "accepted_state_sha256": entry.accepted_state_sha256,
                "acceptances": [
                    _acceptance_canonical_payload_v1(item)
                    for item in entry.acceptances
                ],
            }
            for entry in portfolio.entries
        ],
    }
    return _json_sha256(_CANDIDATE_PORTFOLIO_HASH_DOMAIN_V1, payload)


@dataclass(frozen=True, slots=True)
class PersonalCapabilityCurrentStateSelectionRequest:
    concept_ref: CapabilityConceptRef
    frame_ref: CompetenceFrameRef
    action: CurrentStateSelectionAction
    selected_state_id: PersonalCapabilityStateId | None
    selection_policy_ref: CurrentStateSelectionPolicyRef
    selector_ref: CurrentStateSelectorRef
    selected_at: datetime
    rationale: str

    def __post_init__(self) -> None:
        _concept(self.concept_ref, "current selection request concept_ref")
        _frame(self.frame_ref, "current selection request frame_ref")
        _exact_type(self.action, CurrentStateSelectionAction, "current selection action")
        _validate_selection_target(self.action, self.selected_state_id, "current selection request")
        _policy(self.selection_policy_ref, "current selection request selection_policy_ref")
        _selector(self.selector_ref, "current selection request selector_ref")
        object.__setattr__(
            self,
            "selected_at",
            _canonical_time(self.selected_at, "current selection request selected_at"),
        )
        object.__setattr__(
            self,
            "rationale",
            _canonical_text(self.rationale, "current selection request rationale"),
        )


@dataclass(frozen=True, slots=True)
class PersonalCapabilityCurrentStateSelection:
    subject_ref: CapabilitySubjectRef
    concept_ref: CapabilityConceptRef
    frame_ref: CompetenceFrameRef
    action: CurrentStateSelectionAction
    selected_state_id: PersonalCapabilityStateId | None
    selected_state_sha256: str | None
    candidate_portfolio_sha256: str
    state_snapshot_sha256: str
    acceptance_set_sha256: str
    predecessor_selection_sha256: str | None
    selection_policy_ref: CurrentStateSelectionPolicyRef
    selector_ref: CurrentStateSelectorRef
    selected_at: datetime
    rationale: str

    def __post_init__(self) -> None:
        _subject(self.subject_ref, "current selection subject_ref")
        _concept(self.concept_ref, "current selection concept_ref")
        _frame(self.frame_ref, "current selection frame_ref")
        _exact_type(self.action, CurrentStateSelectionAction, "current selection action")
        _validate_selection_target(self.action, self.selected_state_id, "current selection")
        if self.action is CurrentStateSelectionAction.SELECT:
            _validate_sha256(self.selected_state_sha256, "selected_state_sha256")
        elif self.selected_state_sha256 is not None:
            _fail("CLEAR current selection must not carry selected_state_sha256")
        _validate_sha256(self.candidate_portfolio_sha256, "candidate_portfolio_sha256")
        _validate_sha256(self.state_snapshot_sha256, "state_snapshot_sha256")
        _validate_sha256(self.acceptance_set_sha256, "acceptance_set_sha256")
        if self.predecessor_selection_sha256 is not None:
            _validate_sha256(
                self.predecessor_selection_sha256,
                "predecessor_selection_sha256",
            )
        _policy(self.selection_policy_ref, "current selection selection_policy_ref")
        _selector(self.selector_ref, "current selection selector_ref")
        object.__setattr__(
            self,
            "selected_at",
            _canonical_time(self.selected_at, "current selection selected_at"),
        )
        object.__setattr__(
            self,
            "rationale",
            _canonical_text(self.rationale, "current selection rationale"),
        )


@dataclass(frozen=True, slots=True)
class PersonalCapabilityCurrentStateSelectionHistory:
    subject_ref: CapabilitySubjectRef
    selections: tuple[PersonalCapabilityCurrentStateSelection, ...] = ()

    def __post_init__(self) -> None:
        _subject(self.subject_ref, "current selection history subject_ref")
        if type(self.selections) is not tuple:
            _fail("current selection history selections must be exact tuple")
        if any(
            type(item) is not PersonalCapabilityCurrentStateSelection
            for item in self.selections
        ):
            _fail("current selection history must contain exact selection records")
        if any(item.subject_ref != self.subject_ref for item in self.selections):
            _fail("current selection history contains selection for another subject")
        object.__setattr__(
            self,
            "selections",
            tuple(sorted(self.selections, key=_selection_sort_key)),
        )
        _validate_history_graph(self)


def _policy(value: object, field_name: str) -> CurrentStateSelectionPolicyRef:
    _exact_type(value, CurrentStateSelectionPolicyRef, field_name)
    if CurrentStateSelectionPolicyRef.parse(str(value)) != value:
        _fail(f"{field_name} must equal strict parse round-trip")
    return value


def _selector(value: object, field_name: str) -> CurrentStateSelectorRef:
    _exact_type(value, CurrentStateSelectorRef, field_name)
    _exact_type(value.kind, CurrentStateSelectionMechanismKind, f"{field_name}.kind")
    _opaque_id(value.ref, f"{field_name}.ref")
    return value


def _validate_selection_target(
    action: CurrentStateSelectionAction,
    selected_state_id: PersonalCapabilityStateId | None,
    field_name: str,
) -> None:
    if action is CurrentStateSelectionAction.SELECT:
        _state_id(selected_state_id, f"{field_name}.selected_state_id")
    elif action is CurrentStateSelectionAction.CLEAR:
        if selected_state_id is not None:
            _fail(f"{field_name} CLEAR action must use selected_state_id=None")
    else:
        _fail(f"{field_name} uses unsupported selection action")


def _validated_request(
    value: object,
) -> PersonalCapabilityCurrentStateSelectionRequest:
    _exact_type(value, PersonalCapabilityCurrentStateSelectionRequest, "current selection request")
    _concept(value.concept_ref, "current selection request concept_ref")
    _frame(value.frame_ref, "current selection request frame_ref")
    _exact_type(value.action, CurrentStateSelectionAction, "current selection request action")
    _validate_selection_target(value.action, value.selected_state_id, "current selection request")
    _policy(value.selection_policy_ref, "current selection request selection_policy_ref")
    _selector(value.selector_ref, "current selection request selector_ref")
    _require_canonical_time(value.selected_at, "current selection request selected_at")
    _require_canonical_text(value.rationale, "current selection request rationale")
    return value


def _validated_selection(
    value: object,
) -> PersonalCapabilityCurrentStateSelection:
    _exact_type(value, PersonalCapabilityCurrentStateSelection, "current selection")
    _subject(value.subject_ref, "current selection subject_ref")
    _concept(value.concept_ref, "current selection concept_ref")
    _frame(value.frame_ref, "current selection frame_ref")
    _exact_type(value.action, CurrentStateSelectionAction, "current selection action")
    _validate_selection_target(value.action, value.selected_state_id, "current selection")
    if value.action is CurrentStateSelectionAction.SELECT:
        _validate_sha256(value.selected_state_sha256, "selected_state_sha256")
    elif value.selected_state_sha256 is not None:
        _fail("CLEAR current selection must not carry selected_state_sha256")
    _validate_sha256(value.candidate_portfolio_sha256, "candidate_portfolio_sha256")
    _validate_sha256(value.state_snapshot_sha256, "state_snapshot_sha256")
    _validate_sha256(value.acceptance_set_sha256, "acceptance_set_sha256")
    if value.predecessor_selection_sha256 is not None:
        _validate_sha256(value.predecessor_selection_sha256, "predecessor_selection_sha256")
    _policy(value.selection_policy_ref, "current selection selection_policy_ref")
    _selector(value.selector_ref, "current selection selector_ref")
    _require_canonical_time(value.selected_at, "current selection selected_at")
    _require_canonical_text(value.rationale, "current selection rationale")
    return value


def _selection_scope(
    selection: PersonalCapabilityCurrentStateSelection,
) -> tuple[CapabilityConceptRef, CompetenceFrameRef]:
    return (selection.concept_ref, selection.frame_ref)


def _selection_sort_key(
    selection: PersonalCapabilityCurrentStateSelection,
) -> tuple[str, ...]:
    return (
        str(selection.concept_ref),
        str(selection.frame_ref),
        _utc_text(selection.selected_at, "current selection selected_at"),
        selection.action.value,
        selection.selected_state_id.value if selection.selected_state_id else "",
        selection.selected_state_sha256 or "",
        selection.candidate_portfolio_sha256,
        selection.predecessor_selection_sha256 or "",
        str(selection.selection_policy_ref),
        selection.selector_ref.kind.value,
        selection.selector_ref.ref,
        selection.rationale,
    )


def _selection_payload(
    selection: PersonalCapabilityCurrentStateSelection,
) -> dict[str, object]:
    selection = _validated_selection(selection)
    return {
        "subject_ref": selection.subject_ref.value,
        "concept_ref": str(selection.concept_ref),
        "frame_ref": str(selection.frame_ref),
        "action": selection.action.value,
        "selected_state_id": (
            selection.selected_state_id.value if selection.selected_state_id else None
        ),
        "selected_state_sha256": selection.selected_state_sha256,
        "candidate_portfolio_sha256": selection.candidate_portfolio_sha256,
        "state_snapshot_sha256": selection.state_snapshot_sha256,
        "acceptance_set_sha256": selection.acceptance_set_sha256,
        "predecessor_selection_sha256": selection.predecessor_selection_sha256,
        "selection_policy_ref": str(selection.selection_policy_ref),
        "selector_kind": selection.selector_ref.kind.value,
        "selector_ref": selection.selector_ref.ref,
        "selected_at": _utc_text(selection.selected_at, "current selection selected_at"),
        "rationale": selection.rationale,
    }


def personal_capability_current_state_selection_sha256_v1(
    selection: PersonalCapabilityCurrentStateSelection,
) -> str:
    return _json_sha256(_CURRENT_SELECTION_HASH_DOMAIN_V1, _selection_payload(selection))


def _validated_history(
    value: object,
    field_name: str,
) -> PersonalCapabilityCurrentStateSelectionHistory:
    _exact_type(value, PersonalCapabilityCurrentStateSelectionHistory, field_name)
    _subject(value.subject_ref, f"{field_name}.subject_ref")
    if type(value.selections) is not tuple:
        _fail(f"{field_name}.selections must be exact tuple")
    if any(type(item) is not PersonalCapabilityCurrentStateSelection for item in value.selections):
        _fail(f"{field_name}.selections must contain exact selection records")
    expected = tuple(sorted(value.selections, key=_selection_sort_key))
    if expected != value.selections:
        _fail(f"{field_name}.selections must be canonically ordered")
    if any(item.subject_ref != value.subject_ref for item in value.selections):
        _fail(f"{field_name} contains selection for another subject")
    for selection in value.selections:
        _validated_selection(selection)
    _validate_history_graph(value)
    return value


def _validate_history_graph(
    history: PersonalCapabilityCurrentStateSelectionHistory,
) -> None:
    selections = tuple(history.selections)
    hashes = {
        personal_capability_current_state_selection_sha256_v1(item): item
        for item in selections
    }
    if len(hashes) != len(selections):
        _fail("current selection history must not contain duplicate selection records")

    by_scope: dict[
        tuple[CapabilityConceptRef, CompetenceFrameRef],
        list[PersonalCapabilityCurrentStateSelection],
    ] = {}
    for selection in selections:
        by_scope.setdefault(_selection_scope(selection), []).append(selection)

    for scope, scoped in by_scope.items():
        scoped_hashes = {
            personal_capability_current_state_selection_sha256_v1(item): item
            for item in scoped
        }
        roots = [item for item in scoped if item.predecessor_selection_sha256 is None]
        if len(roots) != 1:
            _fail(
                "each current-selection scope must form one rooted no-fork chain; "
                f"scope={scope!r}"
            )
        child_by_parent: dict[str, PersonalCapabilityCurrentStateSelection] = {}
        for item in scoped:
            predecessor_hash = item.predecessor_selection_sha256
            if predecessor_hash is None:
                continue
            predecessor = hashes.get(predecessor_hash)
            if predecessor is None:
                _fail("current selection predecessor hash is absent from history")
            if _selection_scope(predecessor) != scope:
                _fail("current selection predecessor may not cross concept/frame scope")
            if predecessor_hash in child_by_parent:
                _fail("current selection history may not fork from one predecessor")
            if item.selected_at < predecessor.selected_at:
                _fail("current selection selected_at must not precede predecessor selection")
            child_by_parent[predecessor_hash] = item

        visited: set[str] = set()
        cursor = roots[0]
        while True:
            cursor_hash = personal_capability_current_state_selection_sha256_v1(cursor)
            if cursor_hash in visited:
                _fail("current selection history must not contain cycles")
            visited.add(cursor_hash)
            child = child_by_parent.get(cursor_hash)
            if child is None:
                break
            cursor = child
        if visited != set(scoped_hashes):
            _fail("current selection scope contains disconnected or cyclic selections")


def _selection_head(
    *,
    history: PersonalCapabilityCurrentStateSelectionHistory,
    concept_ref: CapabilityConceptRef,
    frame_ref: CompetenceFrameRef,
) -> PersonalCapabilityCurrentStateSelection | None:
    history = _validated_history(history, "selection_history")
    scoped = [
        item
        for item in history.selections
        if item.concept_ref == concept_ref and item.frame_ref == frame_ref
    ]
    if not scoped:
        return None
    parent_hashes = {
        item.predecessor_selection_sha256
        for item in scoped
        if item.predecessor_selection_sha256 is not None
    }
    heads = [
        item
        for item in scoped
        if personal_capability_current_state_selection_sha256_v1(item)
        not in parent_hashes
    ]
    if len(heads) != 1:
        _fail("current selection scope must have exactly one chain head")
    return heads[0]


def resolve_current_personal_capability_state_selection_v1(
    *,
    history: PersonalCapabilityCurrentStateSelectionHistory,
    concept_ref: CapabilityConceptRef,
    frame_ref: CompetenceFrameRef,
) -> PersonalCapabilityCurrentStateSelection | None:
    """Return SELECT head for one scope, or None when absent/CLEAR."""

    _concept(concept_ref, "concept_ref")
    _frame(frame_ref, "frame_ref")
    head = _selection_head(
        history=history,
        concept_ref=concept_ref,
        frame_ref=frame_ref,
    )
    if head is None or head.action is CurrentStateSelectionAction.CLEAR:
        return None
    return head


def personal_capability_current_state_selection_history_sha256_v1(
    history: PersonalCapabilityCurrentStateSelectionHistory,
) -> str:
    history = _validated_history(history, "selection_history")
    payload = {
        "subject_ref": history.subject_ref.value,
        "selection_sha256s": [
            personal_capability_current_state_selection_sha256_v1(item)
            for item in history.selections
        ],
    }
    return _json_sha256(_CURRENT_SELECTION_HISTORY_HASH_DOMAIN_V1, payload)


def validate_personal_capability_current_state_selection_history_successor_v1(
    *,
    predecessor: PersonalCapabilityCurrentStateSelectionHistory,
    successor: PersonalCapabilityCurrentStateSelectionHistory,
) -> PersonalCapabilityCurrentStateSelectionHistory:
    """Require immutable retention plus zero-or-one selection append."""

    predecessor = _validated_history(predecessor, "predecessor")
    successor = _validated_history(successor, "successor")
    if predecessor.subject_ref != successor.subject_ref:
        _fail("selection-history successor must preserve exact subject_ref")
    predecessor_values = set(predecessor.selections)
    successor_values = set(successor.selections)
    removed = predecessor_values - successor_values
    if removed:
        _fail("selection-history successor may not remove or mutate prior selection")
    added = successor_values - predecessor_values
    if len(added) > 1:
        _fail("one selection-history transition may append at most one selection act")
    return successor


def select_current_personal_capability_state_v1(
    *,
    state_snapshot: PersonalCapabilityStateSet,
    acceptance_predecessor: PersonalCapabilityStateAcceptanceSet,
    acceptance_successor: PersonalCapabilityStateAcceptanceSet,
    acceptance_admissions: tuple[PersonalCapabilityStateAcceptanceAdmission, ...] = (),
    selection_history: PersonalCapabilityCurrentStateSelectionHistory,
    request: PersonalCapabilityCurrentStateSelectionRequest,
) -> PersonalCapabilityCurrentStateSelectionHistory:
    """Append one explicit SELECT/CLEAR act over the complete accepted candidate universe."""

    request = _validated_request(request)
    personal_capability_state_set_sha256_v1(state_snapshot)
    selection_history = _validated_history(selection_history, "selection_history")
    if selection_history.subject_ref != state_snapshot.subject_ref:
        _fail("selection history and state snapshot must belong to the same subject")

    acceptance_receipt = validate_personal_capability_state_acceptance_set_successor_v1(
        state_snapshot=state_snapshot,
        predecessor=acceptance_predecessor,
        successor=acceptance_successor,
        admissions=acceptance_admissions,
    )
    if acceptance_receipt.subject_ref != state_snapshot.subject_ref:
        _fail("validated acceptance universe belongs to another subject")

    portfolio = build_complete_current_state_candidate_portfolio_v1(
        state_snapshot=state_snapshot,
        acceptance_set=acceptance_successor,
        concept_ref=request.concept_ref,
        frame_ref=request.frame_ref,
        as_of=request.selected_at,
    )
    if not portfolio.entries:
        _fail("current selection scope has no accepted candidate states at selected_at")

    predecessor_selection = _selection_head(
        history=selection_history,
        concept_ref=request.concept_ref,
        frame_ref=request.frame_ref,
    )
    if (
        predecessor_selection is not None
        and request.selected_at < predecessor_selection.selected_at
    ):
        _fail("current selection selected_at must not precede current chain head")
    predecessor_sha256 = (
        personal_capability_current_state_selection_sha256_v1(predecessor_selection)
        if predecessor_selection is not None
        else None
    )

    selected_state_sha256 = None
    if request.action is CurrentStateSelectionAction.SELECT:
        if request.selected_state_id not in portfolio.candidate_state_ids:
            _fail(
                "selected_state_id must belong to the complete accepted-state candidate universe"
            )
        selected_state_sha256 = personal_capability_state_content_sha256_v1(
            snapshot=state_snapshot,
            state_id=request.selected_state_id,
        )

    selection = PersonalCapabilityCurrentStateSelection(
        subject_ref=state_snapshot.subject_ref,
        concept_ref=request.concept_ref,
        frame_ref=request.frame_ref,
        action=request.action,
        selected_state_id=request.selected_state_id,
        selected_state_sha256=selected_state_sha256,
        candidate_portfolio_sha256=current_state_candidate_portfolio_sha256_v1(portfolio),
        state_snapshot_sha256=portfolio.state_snapshot_sha256,
        acceptance_set_sha256=portfolio.acceptance_set_sha256,
        predecessor_selection_sha256=predecessor_sha256,
        selection_policy_ref=request.selection_policy_ref,
        selector_ref=request.selector_ref,
        selected_at=request.selected_at,
        rationale=request.rationale,
    )
    successor_history = PersonalCapabilityCurrentStateSelectionHistory(
        subject_ref=selection_history.subject_ref,
        selections=selection_history.selections + (selection,),
    )
    return validate_personal_capability_current_state_selection_history_successor_v1(
        predecessor=selection_history,
        successor=successor_history,
    )
