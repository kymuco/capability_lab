"""PR11.8 authority replay for current-state selection chain heads."""

from __future__ import annotations

from dataclasses import dataclass

from .acceptance import personal_capability_state_content_sha256_v1
from .acceptance_set import (
    PersonalCapabilityStateAcceptanceAdmission,
    PersonalCapabilityStateAcceptanceSet,
    validate_personal_capability_state_acceptance_set_successor_v1,
)
from .core import CompetenceFrameRef, PersonalCapabilityStateSet
from .current_selection import (
    CurrentStateSelectionAction,
    InvalidCurrentStateSelection,
    PersonalCapabilityCurrentStateSelection,
    PersonalCapabilityCurrentStateSelectionHistory,
    build_complete_current_state_candidate_portfolio_v1,
    current_state_candidate_portfolio_sha256_v1,
    personal_capability_current_state_selection_history_sha256_v1,
    personal_capability_current_state_selection_sha256_v1,
)
from .snapshot_transition import personal_capability_state_set_sha256_v1
from capability_lab.semantics import CapabilityConceptRef


def _fail(message: str) -> None:
    raise InvalidCurrentStateSelection(message)


def _strict_concept_ref(value: object, field_name: str) -> CapabilityConceptRef:
    if type(value) is not CapabilityConceptRef:
        _fail(f"{field_name} must use exact type CapabilityConceptRef")
    try:
        restored = CapabilityConceptRef.parse(str(value))
    except (TypeError, ValueError) as exc:
        raise InvalidCurrentStateSelection(
            f"{field_name} must survive strict semantic round-trip: {exc}"
        ) from exc
    if restored != value:
        _fail(f"{field_name} must equal its strict semantic round-trip")
    return value


def _strict_frame_ref(value: object, field_name: str) -> CompetenceFrameRef:
    if type(value) is not CompetenceFrameRef:
        _fail(f"{field_name} must use exact type CompetenceFrameRef")
    try:
        restored = CompetenceFrameRef.parse(str(value))
    except (TypeError, ValueError) as exc:
        raise InvalidCurrentStateSelection(
            f"{field_name} must survive strict semantic round-trip: {exc}"
        ) from exc
    if restored != value:
        _fail(f"{field_name} must equal its strict semantic round-trip")
    return value


@dataclass(frozen=True, slots=True)
class PersonalCapabilityCurrentStateSelectionAuthorityBasis:
    """Exact durable issuance basis for one selection record during authority replay."""

    selection: PersonalCapabilityCurrentStateSelection
    state_snapshot: PersonalCapabilityStateSet
    acceptance_predecessor: PersonalCapabilityStateAcceptanceSet
    acceptance_successor: PersonalCapabilityStateAcceptanceSet
    acceptance_admissions: tuple[PersonalCapabilityStateAcceptanceAdmission, ...] = ()

    def __post_init__(self) -> None:
        if type(self.selection) is not PersonalCapabilityCurrentStateSelection:
            _fail("authority basis selection must use exact selection type")
        if type(self.state_snapshot) is not PersonalCapabilityStateSet:
            _fail("authority basis state_snapshot must use exact PersonalCapabilityStateSet")
        if type(self.acceptance_predecessor) is not PersonalCapabilityStateAcceptanceSet:
            _fail("authority basis acceptance_predecessor must use exact acceptance-set type")
        if type(self.acceptance_successor) is not PersonalCapabilityStateAcceptanceSet:
            _fail("authority basis acceptance_successor must use exact acceptance-set type")
        if type(self.acceptance_admissions) is not tuple:
            _fail("authority basis acceptance_admissions must be exact tuple")
        if any(
            type(item) is not PersonalCapabilityStateAcceptanceAdmission
            for item in self.acceptance_admissions
        ):
            _fail("authority basis acceptance_admissions must contain exact admission values")


def _head_for_scope(
    *,
    history: PersonalCapabilityCurrentStateSelectionHistory,
    concept_ref: CapabilityConceptRef,
    frame_ref: CompetenceFrameRef,
) -> PersonalCapabilityCurrentStateSelection | None:
    personal_capability_current_state_selection_history_sha256_v1(history)
    scoped = tuple(
        item
        for item in history.selections
        if item.concept_ref == concept_ref and item.frame_ref == frame_ref
    )
    if not scoped:
        return None
    predecessor_hashes = {
        item.predecessor_selection_sha256
        for item in scoped
        if item.predecessor_selection_sha256 is not None
    }
    heads = tuple(
        item
        for item in scoped
        if personal_capability_current_state_selection_sha256_v1(item)
        not in predecessor_hashes
    )
    if len(heads) != 1:
        _fail("current selection scope must have exactly one structural chain head")
    return heads[0]


def _selection_by_sha256(
    history: PersonalCapabilityCurrentStateSelectionHistory,
    sha256: str,
) -> PersonalCapabilityCurrentStateSelection:
    matches = tuple(
        item
        for item in history.selections
        if personal_capability_current_state_selection_sha256_v1(item) == sha256
    )
    if len(matches) != 1:
        _fail("current selection predecessor hash must identify exactly one history record")
    return matches[0]


def _chain_for_scope(
    *,
    history: PersonalCapabilityCurrentStateSelectionHistory,
    concept_ref: CapabilityConceptRef,
    frame_ref: CompetenceFrameRef,
) -> tuple[PersonalCapabilityCurrentStateSelection, ...]:
    head = _head_for_scope(
        history=history,
        concept_ref=concept_ref,
        frame_ref=frame_ref,
    )
    if head is None:
        return ()

    reverse_chain = []
    cursor = head
    while True:
        reverse_chain.append(cursor)
        predecessor_sha256 = cursor.predecessor_selection_sha256
        if predecessor_sha256 is None:
            break
        cursor = _selection_by_sha256(history, predecessor_sha256)
        if cursor.concept_ref != concept_ref or cursor.frame_ref != frame_ref:
            _fail("current selection authority ancestry may not cross concept/frame scope")
    return tuple(reversed(reverse_chain))


def _validated_basis_map(
    *,
    selections: tuple[PersonalCapabilityCurrentStateSelection, ...],
    authority_bases: tuple[PersonalCapabilityCurrentStateSelectionAuthorityBasis, ...],
) -> dict[str, PersonalCapabilityCurrentStateSelectionAuthorityBasis]:
    if type(authority_bases) is not tuple:
        _fail("authority_bases must be exact tuple")
    if any(
        type(item) is not PersonalCapabilityCurrentStateSelectionAuthorityBasis
        for item in authority_bases
    ):
        _fail("authority_bases must contain exact authority-basis values")

    basis_by_sha256: dict[str, PersonalCapabilityCurrentStateSelectionAuthorityBasis] = {}
    for basis in authority_bases:
        selection_sha256 = personal_capability_current_state_selection_sha256_v1(
            basis.selection
        )
        if selection_sha256 in basis_by_sha256:
            _fail("authority_bases must contain exactly one basis per selection")
        basis_by_sha256[selection_sha256] = basis

    selection_sha256s = {
        personal_capability_current_state_selection_sha256_v1(selection)
        for selection in selections
    }
    if set(basis_by_sha256) != selection_sha256s:
        _fail("authority_bases must cover exactly the subject selection history")
    return basis_by_sha256


def _replay_one_selection(
    *,
    selection: PersonalCapabilityCurrentStateSelection,
    basis: PersonalCapabilityCurrentStateSelectionAuthorityBasis,
) -> None:
    if basis.selection != selection:
        _fail("authority basis selection must exactly match selection history")

    state_snapshot_sha256 = personal_capability_state_set_sha256_v1(basis.state_snapshot)
    if basis.state_snapshot.subject_ref != selection.subject_ref:
        _fail("authority basis state snapshot belongs to another subject")

    receipt = validate_personal_capability_state_acceptance_set_successor_v1(
        state_snapshot=basis.state_snapshot,
        predecessor=basis.acceptance_predecessor,
        successor=basis.acceptance_successor,
        admissions=basis.acceptance_admissions,
    )

    if selection.state_snapshot_sha256 != state_snapshot_sha256:
        _fail("selection state_snapshot_sha256 does not match its exact replay basis")
    if selection.acceptance_set_sha256 != receipt.successor_sha256:
        _fail(
            "selection acceptance_set_sha256 does not match its replayed "
            "acceptance-lineage successor"
        )

    portfolio = build_complete_current_state_candidate_portfolio_v1(
        state_snapshot=basis.state_snapshot,
        acceptance_set=basis.acceptance_successor,
        concept_ref=selection.concept_ref,
        frame_ref=selection.frame_ref,
        as_of=selection.selected_at,
    )
    if not portfolio.entries:
        _fail("current selection scope has no accepted candidate states at selected_at")
    if selection.candidate_portfolio_sha256 != current_state_candidate_portfolio_sha256_v1(
        portfolio
    ):
        _fail(
            "current selection candidate_portfolio_sha256 does not match complete "
            "recomputed candidate universe"
        )

    if selection.action is CurrentStateSelectionAction.SELECT:
        if selection.selected_state_id not in portfolio.candidate_state_ids:
            _fail("current SELECT target is absent from recomputed candidate universe")
        state_sha256 = personal_capability_state_content_sha256_v1(
            snapshot=basis.state_snapshot,
            state_id=selection.selected_state_id,
        )
        if selection.selected_state_sha256 != state_sha256:
            _fail(
                "current selection selected_state_sha256 does not match exact state content"
            )
    elif selection.action is not CurrentStateSelectionAction.CLEAR:
        _fail("current selection uses unsupported action")


def _replay_subject_authority(
    *,
    history: PersonalCapabilityCurrentStateSelectionHistory,
    authority_bases: tuple[PersonalCapabilityCurrentStateSelectionAuthorityBasis, ...],
) -> None:
    """Replay every subject selection against one canonical acceptance lineage.

    Current-selection topology remains scope-local. Acceptance authority does not:
    acceptance sets are one-subject universes, so every selection act for the
    subject participates in one time-ordered predecessor/successor lineage.
    Acts sharing selected_at must bind the exact same transition; otherwise the
    authority order is ambiguous and fails closed.
    """

    basis_by_sha256 = _validated_basis_map(
        selections=history.selections,
        authority_bases=authority_bases,
    )
    chronological = tuple(
        sorted(
            history.selections,
            key=lambda item: (
                item.selected_at,
                personal_capability_current_state_selection_sha256_v1(item),
            ),
        )
    )

    previous_successor: PersonalCapabilityStateAcceptanceSet | None = None
    index = 0
    while index < len(chronological):
        selected_at = chronological[index].selected_at
        group = []
        while index < len(chronological) and chronological[index].selected_at == selected_at:
            group.append(chronological[index])
            index += 1

        first_sha256 = personal_capability_current_state_selection_sha256_v1(group[0])
        first_basis = basis_by_sha256[first_sha256]
        group_predecessor = first_basis.acceptance_predecessor
        group_successor = first_basis.acceptance_successor

        if previous_successor is None:
            if group_predecessor.acceptances:
                _fail(
                    "first subject-wide current selection must establish its acceptance "
                    "universe from an empty predecessor with fresh admissions"
                )
        elif group_predecessor != previous_successor:
            _fail(
                "subject-wide acceptance lineage predecessor must exactly equal the "
                "universe validated for the previous selection timestamp"
            )

        for selection in group:
            selection_sha256 = personal_capability_current_state_selection_sha256_v1(selection)
            basis = basis_by_sha256[selection_sha256]
            if (
                basis.acceptance_predecessor != group_predecessor
                or basis.acceptance_successor != group_successor
            ):
                _fail(
                    "selection acts sharing selected_at must bind one exact "
                    "subject-wide acceptance transition"
                )
            _replay_one_selection(selection=selection, basis=basis)

        previous_successor = group_successor


def validate_personal_capability_current_state_selection_v1(
    *,
    authority_bases: tuple[PersonalCapabilityCurrentStateSelectionAuthorityBasis, ...] = (),
    history: PersonalCapabilityCurrentStateSelectionHistory,
    concept_ref: CapabilityConceptRef,
    frame_ref: CompetenceFrameRef,
) -> PersonalCapabilityCurrentStateSelection | None:
    """Fresh-replay subject-wide acceptance authority and return one scope head.

    Structural current-selection topology is scope-local and is not authority by
    itself. When the requested scope exists, this validator requires the exact
    durable issuance basis for every selection in the subject history, replays all
    acts against one canonical subject-wide acceptance lineage, and only then
    returns the requested SELECT head (or None for CLEAR).
    """

    if type(history) is not PersonalCapabilityCurrentStateSelectionHistory:
        _fail("history must use exact type PersonalCapabilityCurrentStateSelectionHistory")
    _strict_concept_ref(concept_ref, "concept_ref")
    _strict_frame_ref(frame_ref, "frame_ref")
    if type(authority_bases) is not tuple:
        _fail("authority_bases must be exact tuple")
    if any(
        type(item) is not PersonalCapabilityCurrentStateSelectionAuthorityBasis
        for item in authority_bases
    ):
        _fail("authority_bases must contain exact authority-basis values")

    chain = _chain_for_scope(
        history=history,
        concept_ref=concept_ref,
        frame_ref=frame_ref,
    )
    if not chain:
        if authority_bases:
            _fail("absent current-selection scope must use empty authority_bases")
        return None

    _replay_subject_authority(
        history=history,
        authority_bases=authority_bases,
    )

    head = chain[-1]
    if head.action is CurrentStateSelectionAction.CLEAR:
        return None
    if head.action is CurrentStateSelectionAction.SELECT:
        return head
    _fail("current selection head uses unsupported action")
