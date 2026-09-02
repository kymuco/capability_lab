import ast
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from capability_lab.epistemics import CapabilitySubjectRef
from capability_lab.semantics import CapabilityConceptRef
from capability_lab.state import (
    CompetenceFrameRef,
    CurrentStateCandidatePortfolioReceipt,
    CurrentStateSelectionAction,
    CurrentStateSelectionMechanismKind,
    CurrentStateSelectionPolicyRef,
    CurrentStateSelectorRef,
    InvalidCurrentStateSelection,
    PersonalCapabilityCurrentStateSelection,
    PersonalCapabilityCurrentStateSelectionHistory,
    PersonalCapabilityCurrentStateSelectionRequest,
    PersonalCapabilityStateAcceptanceSet,
    PersonalCapabilityStateId,
    current_state_candidate_portfolio_sha256_v1,
    personal_capability_current_state_selection_sha256_v1,
    select_current_personal_capability_state_v1,
    validate_personal_capability_current_state_selection_history_successor_v1,
)

from test_current_state_selection_v1 import (
    CONCEPT,
    FRAME,
    OTHER_CONCEPT,
    OTHER_FRAME,
    SELECTION_POLICY,
    SELECTOR,
    SUBJECT,
    T0,
    _request,
    _select_a_fixture,
    _two_candidates,
)


class _RequestSubclass(PersonalCapabilityCurrentStateSelectionRequest):
    pass


class _SelectionSubclass(PersonalCapabilityCurrentStateSelection):
    pass


class _HistorySubclass(PersonalCapabilityCurrentStateSelectionHistory):
    pass


class _StringSubclass(str):
    pass


class _DateTimeSubclass(datetime):
    pass


def _child_from_history(history, *, state_id, selected_minutes):
    fixture = _two_candidates()
    return select_current_personal_capability_state_v1(
        state_snapshot=fixture[2],
        acceptance_predecessor=fixture[8],
        acceptance_successor=fixture[8],
        selection_history=history,
        request=_request(
            CurrentStateSelectionAction.SELECT,
            state_id=state_id,
            selected_minutes=selected_minutes,
        ),
    )


def test_request_subclass_is_rejected_by_authority_api() -> None:
    fixture = _two_candidates()
    base = _request(
        CurrentStateSelectionAction.SELECT,
        state_id=fixture[0].state_id,
        selected_minutes=5,
    )
    request = _RequestSubclass(
        concept_ref=base.concept_ref,
        frame_ref=base.frame_ref,
        action=base.action,
        selected_state_id=base.selected_state_id,
        selection_policy_ref=base.selection_policy_ref,
        selector_ref=base.selector_ref,
        selected_at=base.selected_at,
        rationale=base.rationale,
    )
    with pytest.raises(InvalidCurrentStateSelection, match="exact type"):
        select_current_personal_capability_state_v1(
            state_snapshot=fixture[2],
            acceptance_predecessor=fixture[7],
            acceptance_successor=fixture[8],
            acceptance_admissions=(fixture[5], fixture[6]),
            selection_history=PersonalCapabilityCurrentStateSelectionHistory(SUBJECT),
            request=request,
        )


def test_non_utc_post_construction_request_tampering_is_rejected() -> None:
    fixture = _two_candidates()
    request = _request(
        CurrentStateSelectionAction.SELECT,
        state_id=fixture[0].state_id,
        selected_minutes=5,
    )
    object.__setattr__(
        request,
        "selected_at",
        datetime(2026, 8, 22, 23, 0, tzinfo=timezone(timedelta(hours=6))),
    )
    with pytest.raises(InvalidCurrentStateSelection, match="normalized to UTC"):
        select_current_personal_capability_state_v1(
            state_snapshot=fixture[2],
            acceptance_predecessor=fixture[7],
            acceptance_successor=fixture[8],
            acceptance_admissions=(fixture[5], fixture[6]),
            selection_history=PersonalCapabilityCurrentStateSelectionHistory(SUBJECT),
            request=request,
        )


def test_datetime_subclass_post_construction_tampering_is_rejected() -> None:
    fixture = _two_candidates()
    request = _request(
        CurrentStateSelectionAction.SELECT,
        state_id=fixture[0].state_id,
        selected_minutes=5,
    )
    object.__setattr__(
        request,
        "selected_at",
        _DateTimeSubclass(2026, 8, 22, 12, 5, tzinfo=timezone.utc),
    )
    with pytest.raises(InvalidCurrentStateSelection, match="exact type datetime"):
        select_current_personal_capability_state_v1(
            state_snapshot=fixture[2],
            acceptance_predecessor=fixture[7],
            acceptance_successor=fixture[8],
            acceptance_admissions=(fixture[5], fixture[6]),
            selection_history=PersonalCapabilityCurrentStateSelectionHistory(SUBJECT),
            request=request,
        )


def test_str_subclass_rationale_post_construction_tampering_is_rejected() -> None:
    fixture = _two_candidates()
    request = _request(
        CurrentStateSelectionAction.SELECT,
        state_id=fixture[0].state_id,
        selected_minutes=5,
    )
    object.__setattr__(request, "rationale", _StringSubclass("tampered"))
    with pytest.raises(InvalidCurrentStateSelection, match="exact str"):
        select_current_personal_capability_state_v1(
            state_snapshot=fixture[2],
            acceptance_predecessor=fixture[7],
            acceptance_successor=fixture[8],
            acceptance_admissions=(fixture[5], fixture[6]),
            selection_history=PersonalCapabilityCurrentStateSelectionHistory(SUBJECT),
            request=request,
        )


def test_clear_request_with_state_id_is_rejected() -> None:
    fixture = _two_candidates()
    with pytest.raises(InvalidCurrentStateSelection, match="selected_state_id=None"):
        PersonalCapabilityCurrentStateSelectionRequest(
            concept_ref=CONCEPT,
            frame_ref=FRAME,
            action=CurrentStateSelectionAction.CLEAR,
            selected_state_id=fixture[0].state_id,
            selection_policy_ref=SELECTION_POLICY,
            selector_ref=SELECTOR,
            selected_at=T0 + timedelta(minutes=5),
            rationale="Invalid CLEAR target.",
        )


def test_select_request_without_state_id_is_rejected() -> None:
    with pytest.raises(InvalidCurrentStateSelection, match="PersonalCapabilityStateId"):
        PersonalCapabilityCurrentStateSelectionRequest(
            concept_ref=CONCEPT,
            frame_ref=FRAME,
            action=CurrentStateSelectionAction.SELECT,
            selected_state_id=None,
            selection_policy_ref=SELECTION_POLICY,
            selector_ref=SELECTOR,
            selected_at=T0 + timedelta(minutes=5),
            rationale="Invalid SELECT target.",
        )


def test_history_rejects_two_children_from_same_predecessor() -> None:
    fixture, history_a = _select_a_fixture()
    history_b = _child_from_history(
        history_a,
        state_id=fixture[1].state_id,
        selected_minutes=6,
    )
    history_a2 = _child_from_history(
        history_a,
        state_id=fixture[0].state_id,
        selected_minutes=7,
    )
    root = history_a.selections[0]
    child_b = next(item for item in history_b.selections if item is not root)
    child_a2 = next(item for item in history_a2.selections if item is not root)
    with pytest.raises(InvalidCurrentStateSelection, match="may not fork"):
        PersonalCapabilityCurrentStateSelectionHistory(
            SUBJECT,
            (root, child_b, child_a2),
        )


def test_history_rejects_cross_scope_predecessor() -> None:
    fixture, history_a = _select_a_fixture()
    history_b = _child_from_history(
        history_a,
        state_id=fixture[1].state_id,
        selected_minutes=6,
    )
    root = history_a.selections[0]
    child = next(item for item in history_b.selections if item != root)
    cross_scope = replace(
        child,
        concept_ref=OTHER_CONCEPT,
        frame_ref=OTHER_FRAME,
    )
    with pytest.raises(InvalidCurrentStateSelection, match="may not cross|rooted no-fork chain"):
        PersonalCapabilityCurrentStateSelectionHistory(
            SUBJECT,
            (root, cross_scope),
        )


def test_history_successor_rejects_removal_of_old_selection() -> None:
    fixture, history_a = _select_a_fixture()
    history_b = _child_from_history(
        history_a,
        state_id=fixture[1].state_id,
        selected_minutes=6,
    )
    with pytest.raises(InvalidCurrentStateSelection, match="may not remove or mutate"):
        validate_personal_capability_current_state_selection_history_successor_v1(
            predecessor=history_b,
            successor=history_a,
        )


def test_history_successor_rejects_mutation_of_old_selection() -> None:
    _, history_a = _select_a_fixture()
    original = history_a.selections[0]
    mutated = replace(original, rationale="Mutated historical governance act.")
    successor = PersonalCapabilityCurrentStateSelectionHistory(SUBJECT, (mutated,))
    with pytest.raises(InvalidCurrentStateSelection, match="may not remove or mutate"):
        validate_personal_capability_current_state_selection_history_successor_v1(
            predecessor=history_a,
            successor=successor,
        )


def test_history_transition_rejects_more_than_one_added_act_even_across_scopes() -> None:
    _, history_a = _select_a_fixture()
    first = history_a.selections[0]
    second_scope = replace(
        first,
        concept_ref=OTHER_CONCEPT,
        frame_ref=OTHER_FRAME,
        predecessor_selection_sha256=None,
    )
    successor = PersonalCapabilityCurrentStateSelectionHistory(
        SUBJECT,
        (first, second_scope),
    )
    with pytest.raises(InvalidCurrentStateSelection, match="at most one"):
        validate_personal_capability_current_state_selection_history_successor_v1(
            predecessor=PersonalCapabilityCurrentStateSelectionHistory(SUBJECT),
            successor=successor,
        )


def test_manual_candidate_portfolio_is_not_hash_authority() -> None:
    fake = CurrentStateCandidatePortfolioReceipt(
        state_snapshot_sha256="1" * 64,
        acceptance_set_sha256="2" * 64,
        subject_ref=SUBJECT,
        concept_ref=CONCEPT,
        frame_ref=FRAME,
        as_of=T0,
        entries=(),
    )
    assert fake.validator_issued is False
    with pytest.raises(InvalidCurrentStateSelection, match="exact type"):
        current_state_candidate_portfolio_sha256_v1(fake)


def test_selection_hash_frozen_known_answer_v1() -> None:
    selection = PersonalCapabilityCurrentStateSelection(
        subject_ref=CapabilitySubjectRef("alice_pr11_8_hash"),
        concept_ref=CapabilityConceptRef.parse("core:hash_capability@1"),
        frame_ref=CompetenceFrameRef.parse("core:hash_frame@1"),
        action=CurrentStateSelectionAction.SELECT,
        selected_state_id=PersonalCapabilityStateId("state_hash"),
        selected_state_sha256="1" * 64,
        candidate_portfolio_sha256="2" * 64,
        state_snapshot_sha256="3" * 64,
        acceptance_set_sha256="4" * 64,
        predecessor_selection_sha256=None,
        selection_policy_ref=CurrentStateSelectionPolicyRef.parse(
            "core:hash_selection@1"
        ),
        selector_ref=CurrentStateSelectorRef(
            CurrentStateSelectionMechanismKind.RULE,
            "hash_selector",
        ),
        selected_at=datetime(2026, 8, 22, 12, 0, tzinfo=timezone.utc),
        rationale="Frozen PR11.8 selection hash.",
    )
    assert personal_capability_current_state_selection_sha256_v1(selection) == (
        "c040bbf8df3863ed6ddc3ef90ce4fe281ef839656c1eab1862e5bc08dee3e726"
    )


def test_production_import_surfaces_are_exactly_frozen() -> None:
    root = Path(__file__).parents[2]
    expected = {
        "acceptance_set.py": {
            "normal": {"hashlib", "json"},
            "from": {
                ("__future__", 0, ("annotations",)),
                ("dataclasses", 0, ("dataclass",)),
                ("datetime", 0, ("datetime", "timezone")),
                ("capability_lab.epistemics", 0, ("CapabilitySubjectRef",)),
                (
                    "acceptance",
                    1,
                    (
                        "PersonalCapabilityStateAcceptance",
                        "validate_personal_capability_state_acceptance_binding_v1",
                        "validate_personal_capability_state_acceptance_v1",
                    ),
                ),
                ("core", 1, ("PersonalCapabilityStateSet", "StateError")),
                (
                    "snapshot_transition",
                    1,
                    ("personal_capability_state_set_sha256_v1",),
                ),
            },
        },
        "current_selection.py": {
            "normal": {"hashlib", "json", "re", "unicodedata"},
            "from": {
                ("__future__", 0, ("annotations",)),
                ("dataclasses", 0, ("dataclass",)),
                ("datetime", 0, ("datetime", "timezone")),
                ("enum", 0, ("Enum",)),
                ("capability_lab.epistemics", 0, ("CapabilitySubjectRef",)),
                ("capability_lab.semantics", 0, ("CapabilityConceptRef",)),
                (
                    "acceptance",
                    1,
                    (
                        "PersonalCapabilityStateAcceptance",
                        "personal_capability_state_content_sha256_v1",
                    ),
                ),
                (
                    "acceptance_set",
                    1,
                    (
                        "PersonalCapabilityStateAcceptanceAdmission",
                        "PersonalCapabilityStateAcceptanceSet",
                        "_acceptance_canonical_payload_v1",
                        "personal_capability_state_acceptance_set_sha256_v1",
                        "validate_personal_capability_state_acceptance_set_successor_v1",
                    ),
                ),
                (
                    "core",
                    1,
                    (
                        "CompetenceFrameRef",
                        "PersonalCapabilityState",
                        "PersonalCapabilityStateId",
                        "PersonalCapabilityStateSet",
                        "StateError",
                    ),
                ),
                (
                    "snapshot_transition",
                    1,
                    ("personal_capability_state_set_sha256_v1",),
                ),
            },
        },
    }
    for filename, frozen in expected.items():
        path = root / "src" / "capability_lab" / "state" / filename
        tree = ast.parse(path.read_text(encoding="utf-8"))
        normal = set()
        from_imports = set()
        for node in tree.body:
            if isinstance(node, ast.Import):
                normal.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                from_imports.add(
                    (
                        node.module,
                        node.level,
                        tuple(alias.name for alias in node.names),
                    )
                )
        assert normal == frozen["normal"]
        assert from_imports == frozen["from"]


def test_production_surface_contains_no_progression_or_presentation_imports() -> None:
    root = Path(__file__).parents[2] / "src" / "capability_lab" / "state"
    for filename in ("acceptance_set.py", "current_selection.py"):
        text = (root / filename).read_text(encoding="utf-8")
        assert "capability_lab.progression" not in text
        assert "player_window" not in text
        assert "proposals" not in text


def test_selection_subclass_is_rejected_by_history_constructor() -> None:
    _, history_a = _select_a_fixture()
    base = history_a.selections[0]
    selection = _SelectionSubclass(
        subject_ref=base.subject_ref,
        concept_ref=base.concept_ref,
        frame_ref=base.frame_ref,
        action=base.action,
        selected_state_id=base.selected_state_id,
        selected_state_sha256=base.selected_state_sha256,
        candidate_portfolio_sha256=base.candidate_portfolio_sha256,
        state_snapshot_sha256=base.state_snapshot_sha256,
        acceptance_set_sha256=base.acceptance_set_sha256,
        predecessor_selection_sha256=base.predecessor_selection_sha256,
        selection_policy_ref=base.selection_policy_ref,
        selector_ref=base.selector_ref,
        selected_at=base.selected_at,
        rationale=base.rationale,
    )
    with pytest.raises(InvalidCurrentStateSelection, match="exact selection records"):
        PersonalCapabilityCurrentStateSelectionHistory(SUBJECT, (selection,))


def test_history_subclass_is_rejected_by_resolver_path() -> None:
    fixture, history_a = _select_a_fixture()
    history = _HistorySubclass(
        subject_ref=history_a.subject_ref,
        selections=history_a.selections,
    )
    with pytest.raises(InvalidCurrentStateSelection, match="exact type"):
        select_current_personal_capability_state_v1(
            state_snapshot=fixture[2],
            acceptance_predecessor=fixture[8],
            acceptance_successor=fixture[8],
            selection_history=history,
            request=_request(
                CurrentStateSelectionAction.SELECT,
                state_id=fixture[1].state_id,
                selected_minutes=6,
            ),
        )


def test_empty_candidate_scope_fails_closed_even_for_clear() -> None:
    fixture = _two_candidates()
    with pytest.raises(InvalidCurrentStateSelection, match="no accepted candidate"):
        select_current_personal_capability_state_v1(
            state_snapshot=fixture[2],
            acceptance_predecessor=PersonalCapabilityStateAcceptanceSet(SUBJECT),
            acceptance_successor=PersonalCapabilityStateAcceptanceSet(SUBJECT),
            selection_history=PersonalCapabilityCurrentStateSelectionHistory(SUBJECT),
            request=_request(CurrentStateSelectionAction.CLEAR, selected_minutes=5),
        )
