"""PR11.10 complete subject current-state portfolio governance v1."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json

from capability_lab.epistemics import CapabilitySubjectRef
from capability_lab.semantics import CapabilityConceptRef

from .acceptance import personal_capability_state_content_sha256_v1
from .core import (
    CompetenceFrameRef,
    PersonalCapabilityState,
    PersonalCapabilityStateId,
    PersonalCapabilityStateSet,
    StateError,
)
from .current_selection import (
    CurrentStateSelectionAction,
    PersonalCapabilityCurrentStateSelection,
    PersonalCapabilityCurrentStateSelectionHistory,
    personal_capability_current_state_selection_history_sha256_v1,
    personal_capability_current_state_selection_sha256_v1,
)
from .current_selection_authority import (
    PersonalCapabilityCurrentStateSelectionAuthorityBasis,
    validate_personal_capability_current_state_selection_v1,
)
from .snapshot_transition import personal_capability_state_set_sha256_v1


class CurrentStatePortfolioError(StateError):
    """Base error for complete governed current-state portfolio operations."""


class InvalidPersonalCapabilityCurrentStatePortfolio(CurrentStatePortfolioError):
    """The supplied portfolio input or artifact is invalid."""


_PORTFOLIO_HASH_DOMAIN_V1 = (
    b"capability_lab/personal_capability_current_state_portfolio@1\x00"
)
_SHA256_HEX_DIGITS = frozenset("0123456789abcdef")


def _fail(message: str) -> None:
    raise InvalidPersonalCapabilityCurrentStatePortfolio(message)


def _exact(value: object, expected_type: type, field_name: str):
    if type(value) is not expected_type:
        _fail(f"{field_name} must use exact type {expected_type.__name__}")
    return value


def _sha256(value: object, field_name: str) -> str:
    value = _exact(value, str, field_name)
    if len(value) != 64 or any(
        character not in _SHA256_HEX_DIGITS for character in value
    ):
        _fail(f"{field_name} must be 64 lowercase hexadecimal SHA-256 characters")
    return value


def _subject(value: object, field_name: str) -> CapabilitySubjectRef:
    value = _exact(value, CapabilitySubjectRef, field_name)
    _exact(value.value, str, f"{field_name}.value")
    try:
        restored = CapabilitySubjectRef(value.value)
    except (TypeError, ValueError) as exc:
        raise InvalidPersonalCapabilityCurrentStatePortfolio(
            f"{field_name} must survive strict semantic reconstruction: {exc}"
        ) from exc
    if restored != value:
        _fail(f"{field_name} must equal strict semantic reconstruction")
    return value


def _concept(value: object, field_name: str) -> CapabilityConceptRef:
    value = _exact(value, CapabilityConceptRef, field_name)
    try:
        restored = CapabilityConceptRef.parse(str(value))
    except (TypeError, ValueError) as exc:
        raise InvalidPersonalCapabilityCurrentStatePortfolio(
            f"{field_name} must survive strict semantic round-trip: {exc}"
        ) from exc
    if restored != value:
        _fail(f"{field_name} must equal strict semantic round-trip")
    return value


def _frame(value: object, field_name: str) -> CompetenceFrameRef:
    value = _exact(value, CompetenceFrameRef, field_name)
    try:
        restored = CompetenceFrameRef.parse(str(value))
    except (TypeError, ValueError) as exc:
        raise InvalidPersonalCapabilityCurrentStatePortfolio(
            f"{field_name} must survive strict semantic round-trip: {exc}"
        ) from exc
    if restored != value:
        _fail(f"{field_name} must equal strict semantic round-trip")
    return value


def _state_id(value: object, field_name: str) -> PersonalCapabilityStateId:
    value = _exact(value, PersonalCapabilityStateId, field_name)
    _exact(value.value, str, f"{field_name}.value")
    try:
        restored = PersonalCapabilityStateId(value.value)
    except (TypeError, ValueError) as exc:
        raise InvalidPersonalCapabilityCurrentStatePortfolio(
            f"{field_name} must survive strict semantic reconstruction: {exc}"
        ) from exc
    if restored != value:
        _fail(f"{field_name} must equal strict semantic reconstruction")
    return value


def _time(value: object, field_name: str) -> datetime:
    value = _exact(value, datetime, field_name)
    if value.tzinfo is not timezone.utc:
        _fail(f"{field_name} must be timezone-aware and already normalized to UTC")
    return value


def _state_set_sha256(value: object, field_name: str) -> str:
    value = _exact(value, PersonalCapabilityStateSet, field_name)
    try:
        return personal_capability_state_set_sha256_v1(value)
    except (TypeError, ValueError) as exc:
        raise InvalidPersonalCapabilityCurrentStatePortfolio(
            f"{field_name} failed strict persisted-state validation: {exc}"
        ) from exc


def _state_content_sha256(
    *,
    snapshot: PersonalCapabilityStateSet,
    state_id: PersonalCapabilityStateId,
    field_name: str,
) -> str:
    try:
        return personal_capability_state_content_sha256_v1(
            snapshot=snapshot,
            state_id=state_id,
        )
    except (TypeError, ValueError) as exc:
        raise InvalidPersonalCapabilityCurrentStatePortfolio(
            f"{field_name} failed exact state-content validation: {exc}"
        ) from exc


def _selection_sha256(
    selection: PersonalCapabilityCurrentStateSelection,
    field_name: str,
) -> str:
    try:
        return personal_capability_current_state_selection_sha256_v1(selection)
    except (TypeError, ValueError) as exc:
        raise InvalidPersonalCapabilityCurrentStatePortfolio(
            f"{field_name} failed strict current-selection validation: {exc}"
        ) from exc


def _entry_sort_key(
    entry: "PersonalCapabilityCurrentStatePortfolioEntry",
) -> tuple[str, str]:
    return (str(entry.concept_ref), str(entry.frame_ref))


@dataclass(frozen=True, slots=True)
class PersonalCapabilityCurrentStatePortfolioEntry:
    concept_ref: CapabilityConceptRef
    frame_ref: CompetenceFrameRef
    action: CurrentStateSelectionAction
    current_selection_sha256: str
    selected_state_id: PersonalCapabilityStateId | None
    selected_state_sha256: str | None

    def __post_init__(self) -> None:
        _concept(self.concept_ref, "portfolio entry concept_ref")
        _frame(self.frame_ref, "portfolio entry frame_ref")
        _exact(self.action, CurrentStateSelectionAction, "portfolio entry action")
        _sha256(
            self.current_selection_sha256,
            "portfolio entry current_selection_sha256",
        )
        if self.action is CurrentStateSelectionAction.SELECT:
            _state_id(self.selected_state_id, "portfolio entry selected_state_id")
            _sha256(
                self.selected_state_sha256,
                "portfolio entry selected_state_sha256",
            )
        elif self.action is CurrentStateSelectionAction.CLEAR:
            if (
                self.selected_state_id is not None
                or self.selected_state_sha256 is not None
            ):
                _fail("CLEAR portfolio entry must not carry selected-state identity")
        else:
            _fail("portfolio entry uses unsupported current-selection action")


def _validated_entry(
    value: object,
) -> PersonalCapabilityCurrentStatePortfolioEntry:
    value = _exact(
        value,
        PersonalCapabilityCurrentStatePortfolioEntry,
        "current-state portfolio entry",
    )
    restored = PersonalCapabilityCurrentStatePortfolioEntry(
        concept_ref=value.concept_ref,
        frame_ref=value.frame_ref,
        action=value.action,
        current_selection_sha256=value.current_selection_sha256,
        selected_state_id=value.selected_state_id,
        selected_state_sha256=value.selected_state_sha256,
    )
    if restored != value:
        _fail("current-state portfolio entry must equal strict semantic reconstruction")
    return value


@dataclass(frozen=True, slots=True)
class PersonalCapabilityCurrentStatePortfolio:
    subject_ref: CapabilitySubjectRef
    generated_at: datetime
    current_selection_history_sha256: str
    entries: tuple[PersonalCapabilityCurrentStatePortfolioEntry, ...]
    current_state_set: PersonalCapabilityStateSet

    def __post_init__(self) -> None:
        _subject(self.subject_ref, "current-state portfolio subject_ref")
        _time(self.generated_at, "current-state portfolio generated_at")
        _sha256(
            self.current_selection_history_sha256,
            "current_selection_history_sha256",
        )
        if type(self.entries) is not tuple:
            _fail("current-state portfolio entries must be exact tuple")
        validated_entries = tuple(_validated_entry(item) for item in self.entries)
        ordered = tuple(sorted(validated_entries, key=_entry_sort_key))
        scopes = tuple((item.concept_ref, item.frame_ref) for item in ordered)
        if len(set(scopes)) != len(scopes):
            _fail(
                "current-state portfolio may contain each concept/frame scope at most once"
            )
        object.__setattr__(self, "entries", ordered)

        _state_set_sha256(self.current_state_set, "current_state_set")
        if self.current_state_set.subject_ref != self.subject_ref:
            _fail("current_state_set belongs to a different subject")

        states_by_id = {
            state.state_id: state for state in self.current_state_set.states
        }
        selected_entries = tuple(
            item
            for item in ordered
            if item.action is CurrentStateSelectionAction.SELECT
        )
        selected_ids = tuple(item.selected_state_id for item in selected_entries)
        if len(set(selected_ids)) != len(selected_ids):
            _fail("SELECT portfolio entries must not reuse one state identity")
        if set(states_by_id) != set(selected_ids):
            _fail(
                "current_state_set must contain exactly the states named by SELECT entries"
            )

        for entry in selected_entries:
            state = states_by_id[entry.selected_state_id]
            if state.subject_ref != self.subject_ref:
                _fail("selected current state belongs to a different subject")
            if (
                state.concept_ref != entry.concept_ref
                or state.frame_ref != entry.frame_ref
            ):
                _fail("selected current state must match its exact portfolio scope")
            state_sha256 = _state_content_sha256(
                snapshot=self.current_state_set,
                state_id=state.state_id,
                field_name="selected current state",
            )
            if state_sha256 != entry.selected_state_sha256:
                _fail(
                    "selected_state_sha256 must match exact current_state_set content"
                )


def _validated_portfolio(
    value: object,
) -> PersonalCapabilityCurrentStatePortfolio:
    value = _exact(
        value,
        PersonalCapabilityCurrentStatePortfolio,
        "current-state portfolio",
    )
    restored = PersonalCapabilityCurrentStatePortfolio(
        subject_ref=value.subject_ref,
        generated_at=value.generated_at,
        current_selection_history_sha256=value.current_selection_history_sha256,
        entries=value.entries,
        current_state_set=value.current_state_set,
    )
    if restored != value:
        _fail("current-state portfolio must equal strict semantic reconstruction")
    return value


def _history_sha256(
    history: object,
) -> tuple[PersonalCapabilityCurrentStateSelectionHistory, str]:
    history = _exact(
        history,
        PersonalCapabilityCurrentStateSelectionHistory,
        "selection_history",
    )
    try:
        digest = personal_capability_current_state_selection_history_sha256_v1(history)
    except (TypeError, ValueError) as exc:
        raise InvalidPersonalCapabilityCurrentStatePortfolio(
            f"selection_history failed strict validation: {exc}"
        ) from exc
    return history, digest


def _validated_authority_bases(
    authority_bases: object,
) -> tuple[PersonalCapabilityCurrentStateSelectionAuthorityBasis, ...]:
    if type(authority_bases) is not tuple:
        _fail("authority_bases must be exact tuple")
    if any(
        type(item) is not PersonalCapabilityCurrentStateSelectionAuthorityBasis
        for item in authority_bases
    ):
        _fail("authority_bases must contain exact PR11.8 authority-basis values")
    return authority_bases


def _scope_heads(
    history: PersonalCapabilityCurrentStateSelectionHistory,
) -> tuple[PersonalCapabilityCurrentStateSelection, ...]:
    grouped: dict[
        tuple[CapabilityConceptRef, CompetenceFrameRef],
        list[PersonalCapabilityCurrentStateSelection],
    ] = {}
    for selection in history.selections:
        grouped.setdefault(
            (selection.concept_ref, selection.frame_ref),
            [],
        ).append(selection)

    heads = []
    for scope in sorted(
        grouped,
        key=lambda item: (str(item[0]), str(item[1])),
    ):
        scoped = grouped[scope]
        predecessor_sha256s = {
            item.predecessor_selection_sha256
            for item in scoped
            if item.predecessor_selection_sha256 is not None
        }
        candidates = tuple(
            item
            for item in scoped
            if _selection_sha256(item, "current-selection scope member")
            not in predecessor_sha256s
        )
        if len(candidates) != 1:
            _fail("each governed current-selection scope must have exactly one head")
        heads.append(candidates[0])
    return tuple(heads)


def _basis_by_selection_sha256(
    *,
    history: PersonalCapabilityCurrentStateSelectionHistory,
    authority_bases: tuple[
        PersonalCapabilityCurrentStateSelectionAuthorityBasis, ...
    ],
) -> dict[str, PersonalCapabilityCurrentStateSelectionAuthorityBasis]:
    result: dict[
        str,
        PersonalCapabilityCurrentStateSelectionAuthorityBasis,
    ] = {}
    for basis in authority_bases:
        selection_sha256 = _selection_sha256(
            basis.selection,
            "authority basis selection",
        )
        if selection_sha256 in result:
            _fail("authority_bases must contain exactly one basis per selection")
        result[selection_sha256] = basis

    expected = {
        _selection_sha256(selection, "selection history member")
        for selection in history.selections
    }
    if set(result) != expected:
        _fail("authority_bases must cover exactly the subject selection history")
    return result


def _selected_state_from_basis(
    *,
    selection: PersonalCapabilityCurrentStateSelection,
    basis: PersonalCapabilityCurrentStateSelectionAuthorityBasis,
) -> PersonalCapabilityState:
    matches = tuple(
        state
        for state in basis.state_snapshot.states
        if state.state_id == selection.selected_state_id
    )
    if len(matches) != 1:
        _fail(
            "SELECT head state must exist exactly once in its authority-basis snapshot"
        )
    state = matches[0]
    if state.subject_ref != selection.subject_ref:
        _fail("SELECT head state belongs to a different subject")
    if (
        state.concept_ref != selection.concept_ref
        or state.frame_ref != selection.frame_ref
    ):
        _fail("SELECT head state crosses its governed concept/frame scope")
    state_sha256 = _state_content_sha256(
        snapshot=basis.state_snapshot,
        state_id=state.state_id,
        field_name="SELECT head state",
    )
    if state_sha256 != selection.selected_state_sha256:
        _fail("SELECT head state content does not match its PR11.8 selection binding")
    return state


def derive_personal_capability_current_state_portfolio_v1(
    *,
    history: PersonalCapabilityCurrentStateSelectionHistory,
    authority_bases: tuple[
        PersonalCapabilityCurrentStateSelectionAuthorityBasis, ...
    ] = (),
    generated_at: datetime,
) -> PersonalCapabilityCurrentStatePortfolio:
    """Derive every governed current-selection head without caller scope selection."""

    history, history_sha256 = _history_sha256(history)
    authority_bases = _validated_authority_bases(authority_bases)
    generated_at = _time(generated_at, "generated_at")

    if any(
        selection.selected_at > generated_at for selection in history.selections
    ):
        _fail(
            "selection history contains governance act after portfolio generated_at"
        )

    if not history.selections:
        if authority_bases:
            _fail(
                "authority_bases must be empty when current-selection history is empty"
            )
        return PersonalCapabilityCurrentStatePortfolio(
            subject_ref=history.subject_ref,
            generated_at=generated_at,
            current_selection_history_sha256=history_sha256,
            entries=(),
            current_state_set=PersonalCapabilityStateSet(history.subject_ref),
        )

    heads = _scope_heads(history)
    anchor = heads[0]
    try:
        validated_anchor = (
            validate_personal_capability_current_state_selection_v1(
                authority_bases=authority_bases,
                history=history,
                concept_ref=anchor.concept_ref,
                frame_ref=anchor.frame_ref,
            )
        )
    except (TypeError, ValueError) as exc:
        raise InvalidPersonalCapabilityCurrentStatePortfolio(
            "subject-wide PR11.8 current-state authority replay rejected "
            f"portfolio history: {exc}"
        ) from exc

    if (
        anchor.action is CurrentStateSelectionAction.SELECT
        and validated_anchor != anchor
    ):
        _fail(
            "PR11.8 authority replay did not return the exact deterministic "
            "anchor head"
        )
    if (
        anchor.action is CurrentStateSelectionAction.CLEAR
        and validated_anchor is not None
    ):
        _fail(
            "PR11.8 authority replay must resolve a CLEAR anchor as no selected state"
        )

    basis_by_sha256 = _basis_by_selection_sha256(
        history=history,
        authority_bases=authority_bases,
    )
    entries = []
    selected_states = []

    for head in heads:
        selection_sha256 = _selection_sha256(
            head,
            "current-selection head",
        )
        if head.action is CurrentStateSelectionAction.SELECT:
            basis = basis_by_sha256[selection_sha256]
            state = _selected_state_from_basis(
                selection=head,
                basis=basis,
            )
            selected_states.append(state)
            entries.append(
                PersonalCapabilityCurrentStatePortfolioEntry(
                    concept_ref=head.concept_ref,
                    frame_ref=head.frame_ref,
                    action=head.action,
                    current_selection_sha256=selection_sha256,
                    selected_state_id=head.selected_state_id,
                    selected_state_sha256=head.selected_state_sha256,
                )
            )
        elif head.action is CurrentStateSelectionAction.CLEAR:
            entries.append(
                PersonalCapabilityCurrentStatePortfolioEntry(
                    concept_ref=head.concept_ref,
                    frame_ref=head.frame_ref,
                    action=head.action,
                    current_selection_sha256=selection_sha256,
                    selected_state_id=None,
                    selected_state_sha256=None,
                )
            )
        else:
            _fail("current-selection head uses unsupported action")

    return PersonalCapabilityCurrentStatePortfolio(
        subject_ref=history.subject_ref,
        generated_at=generated_at,
        current_selection_history_sha256=history_sha256,
        entries=tuple(entries),
        current_state_set=PersonalCapabilityStateSet(
            history.subject_ref,
            tuple(selected_states),
        ),
    )


def validate_personal_capability_current_state_portfolio_v1(
    *,
    history: PersonalCapabilityCurrentStateSelectionHistory,
    authority_bases: tuple[
        PersonalCapabilityCurrentStateSelectionAuthorityBasis, ...
    ] = (),
    portfolio: PersonalCapabilityCurrentStatePortfolio,
) -> None:
    """Fresh-replay authority and require exact complete portfolio equality."""

    portfolio = _validated_portfolio(portfolio)
    expected = derive_personal_capability_current_state_portfolio_v1(
        history=history,
        authority_bases=authority_bases,
        generated_at=portfolio.generated_at,
    )
    if expected != portfolio:
        _fail(
            "current-state portfolio does not equal fresh complete governed derivation"
        )


def personal_capability_current_state_portfolio_sha256_v1(
    portfolio: PersonalCapabilityCurrentStatePortfolio,
) -> str:
    """Return deterministic domain-separated content identity for one portfolio."""

    portfolio = _validated_portfolio(portfolio)
    state_set_sha256 = _state_set_sha256(
        portfolio.current_state_set,
        "current_state_set",
    )
    payload = {
        "subject_ref": portfolio.subject_ref.value,
        "generated_at": portfolio.generated_at.isoformat().replace(
            "+00:00",
            "Z",
        ),
        "current_selection_history_sha256": (
            portfolio.current_selection_history_sha256
        ),
        "entries": [
            {
                "concept_ref": str(entry.concept_ref),
                "frame_ref": str(entry.frame_ref),
                "action": entry.action.value,
                "current_selection_sha256": entry.current_selection_sha256,
                "selected_state_id": (
                    entry.selected_state_id.value
                    if entry.selected_state_id is not None
                    else None
                ),
                "selected_state_sha256": entry.selected_state_sha256,
            }
            for entry in portfolio.entries
        ],
        "current_state_set_sha256": state_set_sha256,
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    digest = hashlib.sha256()
    digest.update(_PORTFOLIO_HASH_DOMAIN_V1)
    digest.update(encoded)
    return digest.hexdigest()
