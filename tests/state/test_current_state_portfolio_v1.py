import ast
from datetime import timedelta
from pathlib import Path

import pytest

from capability_lab.epistemics import CapabilitySubjectRef
from capability_lab.state import (
    CurrentStateSelectionAction,
    InvalidPersonalCapabilityCurrentStatePortfolio,
    PersonalCapabilityCurrentStatePortfolio,
    PersonalCapabilityCurrentStateSelectionHistory,
    PersonalCapabilityStateId,
    PersonalCapabilityStateSet,
    derive_personal_capability_current_state_portfolio_v1,
    personal_capability_current_state_portfolio_sha256_v1,
    select_current_personal_capability_state_v1,
    validate_personal_capability_current_state_portfolio_v1,
)

from test_current_state_selection_v1 import (
    CONCEPT,
    FRAME,
    OTHER_CONCEPT,
    OTHER_FRAME,
    SUBJECT,
    T0,
    _request,
    _select_a_fixture,
)
from test_current_state_selection_authority_v1 import (
    _basis,
    _cross_scope_authority_fixture,
    _root_basis,
)


def _clear_fixture():
    fixture, history_a = _select_a_fixture()
    history_clear = select_current_personal_capability_state_v1(
        state_snapshot=fixture[2],
        acceptance_predecessor=fixture[8],
        acceptance_successor=fixture[8],
        selection_history=history_a,
        request=_request(
            CurrentStateSelectionAction.CLEAR,
            selected_minutes=6,
        ),
    )
    clear = max(history_clear.selections, key=lambda item: item.selected_at)
    bases = (
        _root_basis(fixture, history_a),
        _basis(clear, fixture[2], fixture[8], fixture[8]),
    )
    return fixture, history_clear, bases


def test_empty_history_produces_empty_subject_portfolio() -> None:
    history = PersonalCapabilityCurrentStateSelectionHistory(SUBJECT)
    portfolio = derive_personal_capability_current_state_portfolio_v1(
        history=history,
        authority_bases=(),
        generated_at=T0 + timedelta(minutes=10),
    )
    assert portfolio.subject_ref == SUBJECT
    assert portfolio.entries == ()
    assert portfolio.current_state_set.states == ()
    assert len(personal_capability_current_state_portfolio_sha256_v1(portfolio)) == 64


def test_one_select_scope_admits_exact_governed_state_not_newer_accepted_state() -> None:
    fixture, history = _select_a_fixture()
    portfolio = derive_personal_capability_current_state_portfolio_v1(
        history=history,
        authority_bases=(_root_basis(fixture, history),),
        generated_at=T0 + timedelta(minutes=10),
    )
    assert len(portfolio.entries) == 1
    entry = portfolio.entries[0]
    assert entry.concept_ref == CONCEPT
    assert entry.frame_ref == FRAME
    assert entry.action is CurrentStateSelectionAction.SELECT
    assert entry.selected_state_id == fixture[0].state_id
    assert tuple(state.state_id for state in portfolio.current_state_set.states) == (
        fixture[0].state_id,
    )
    assert fixture[1].state_id not in {
        state.state_id for state in portfolio.current_state_set.states
    }


def test_complete_portfolio_automatically_contains_every_governed_history_scope() -> None:
    history, bases, _ = _cross_scope_authority_fixture(stale_target=False)
    portfolio = derive_personal_capability_current_state_portfolio_v1(
        history=history,
        authority_bases=bases,
        generated_at=T0 + timedelta(minutes=10),
    )
    assert {(item.concept_ref, item.frame_ref) for item in portfolio.entries} == {
        (CONCEPT, FRAME),
        (OTHER_CONCEPT, OTHER_FRAME),
    }
    assert len(portfolio.current_state_set.states) == 2
    assert all(
        item.action is CurrentStateSelectionAction.SELECT
        for item in portfolio.entries
    )


def test_clear_remains_visible_while_selected_state_leaves_current_state_set() -> None:
    _, history, bases = _clear_fixture()
    portfolio = derive_personal_capability_current_state_portfolio_v1(
        history=history,
        authority_bases=bases,
        generated_at=T0 + timedelta(minutes=10),
    )
    assert len(portfolio.entries) == 1
    entry = portfolio.entries[0]
    assert entry.action is CurrentStateSelectionAction.CLEAR
    assert entry.selected_state_id is None
    assert entry.selected_state_sha256 is None
    assert portfolio.current_state_set.states == ()


def test_authority_basis_input_order_does_not_change_portfolio_or_digest() -> None:
    history, bases, _ = _cross_scope_authority_fixture(stale_target=False)
    first = derive_personal_capability_current_state_portfolio_v1(
        history=history,
        authority_bases=bases,
        generated_at=T0 + timedelta(minutes=10),
    )
    second = derive_personal_capability_current_state_portfolio_v1(
        history=history,
        authority_bases=tuple(reversed(bases)),
        generated_at=T0 + timedelta(minutes=10),
    )
    assert first == second
    assert personal_capability_current_state_portfolio_sha256_v1(first) == (
        personal_capability_current_state_portfolio_sha256_v1(second)
    )


def test_fresh_validation_replays_authority_and_exact_complete_portfolio() -> None:
    history, bases, _ = _cross_scope_authority_fixture(stale_target=False)
    portfolio = derive_personal_capability_current_state_portfolio_v1(
        history=history,
        authority_bases=bases,
        generated_at=T0 + timedelta(minutes=10),
    )
    assert (
        validate_personal_capability_current_state_portfolio_v1(
            history=history,
            authority_bases=bases,
            portfolio=portfolio,
        )
        is None
    )


def test_fresh_validation_rejects_omission_of_select_scope() -> None:
    history, bases, _ = _cross_scope_authority_fixture(stale_target=False)
    portfolio = derive_personal_capability_current_state_portfolio_v1(
        history=history,
        authority_bases=bases,
        generated_at=T0 + timedelta(minutes=10),
    )
    kept_entry = portfolio.entries[0]
    kept_state = next(
        state
        for state in portfolio.current_state_set.states
        if state.state_id == kept_entry.selected_state_id
    )
    omitted = PersonalCapabilityCurrentStatePortfolio(
        subject_ref=portfolio.subject_ref,
        generated_at=portfolio.generated_at,
        current_selection_history_sha256=portfolio.current_selection_history_sha256,
        entries=(kept_entry,),
        current_state_set=PersonalCapabilityStateSet(
            portfolio.subject_ref,
            (kept_state,),
        ),
    )
    with pytest.raises(
        InvalidPersonalCapabilityCurrentStatePortfolio,
        match="does not equal fresh complete governed derivation",
    ):
        validate_personal_capability_current_state_portfolio_v1(
            history=history,
            authority_bases=bases,
            portfolio=omitted,
        )


def test_historical_history_append_stales_portfolio_without_future_time_guard() -> None:
    history, bases, _ = _cross_scope_authority_fixture(stale_target=False)
    root = min(history.selections, key=lambda item: item.selected_at)
    root_basis = next(item for item in bases if item.selection == root)
    initial_history = PersonalCapabilityCurrentStateSelectionHistory(
        SUBJECT,
        (root,),
    )
    old = derive_personal_capability_current_state_portfolio_v1(
        history=initial_history,
        authority_bases=(root_basis,),
        generated_at=T0 + timedelta(minutes=10),
    )
    assert all(
        selection.selected_at <= old.generated_at
        for selection in history.selections
    )
    with pytest.raises(
        InvalidPersonalCapabilityCurrentStatePortfolio,
        match="does not equal fresh complete governed derivation",
    ):
        validate_personal_capability_current_state_portfolio_v1(
            history=history,
            authority_bases=bases,
            portfolio=old,
        )


def test_corrupted_subject_primitive_stays_inside_pr11_10_error_boundary() -> None:
    subject = CapabilitySubjectRef("pr11_10_corrupted_subject")
    history = PersonalCapabilityCurrentStateSelectionHistory(subject)
    portfolio = derive_personal_capability_current_state_portfolio_v1(
        history=history,
        authority_bases=(),
        generated_at=T0 + timedelta(minutes=10),
    )
    corrupted = CapabilitySubjectRef(subject.value)
    object.__setattr__(corrupted, "value", "")
    object.__setattr__(portfolio, "subject_ref", corrupted)
    with pytest.raises(
        InvalidPersonalCapabilityCurrentStatePortfolio,
        match="must survive strict semantic reconstruction",
    ):
        validate_personal_capability_current_state_portfolio_v1(
            history=history,
            authority_bases=(),
            portfolio=portfolio,
        )


def test_corrupted_selected_state_id_stays_inside_pr11_10_error_boundary() -> None:
    fixture, history = _select_a_fixture()
    portfolio = derive_personal_capability_current_state_portfolio_v1(
        history=history,
        authority_bases=(_root_basis(fixture, history),),
        generated_at=T0 + timedelta(minutes=10),
    )
    entry = portfolio.entries[0]
    corrupted = PersonalCapabilityStateId(entry.selected_state_id.value)
    object.__setattr__(corrupted, "value", "")
    object.__setattr__(entry, "selected_state_id", corrupted)
    with pytest.raises(
        InvalidPersonalCapabilityCurrentStatePortfolio,
        match="must survive strict semantic reconstruction",
    ):
        validate_personal_capability_current_state_portfolio_v1(
            history=history,
            authority_bases=(_root_basis(fixture, history),),
            portfolio=portfolio,
        )


def test_production_import_surface_freezes_exact_modules_and_symbols() -> None:
    root = Path(__file__).parents[2]
    tree = ast.parse(
        (root / "src/capability_lab/state/current_state_portfolio.py").read_text()
    )
    imports = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.extend(
                ("import", alias.name)
                for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom):
            imports.append(
                (
                    "from",
                    node.level,
                    node.module,
                    tuple(alias.name for alias in node.names),
                )
            )

    assert imports == [
        ("from", 0, "__future__", ("annotations",)),
        ("from", 0, "dataclasses", ("dataclass",)),
        ("from", 0, "datetime", ("datetime", "timezone")),
        ("import", "hashlib"),
        ("import", "json"),
        ("from", 0, "capability_lab.epistemics", ("CapabilitySubjectRef",)),
        ("from", 0, "capability_lab.semantics", ("CapabilityConceptRef",)),
        (
            "from",
            1,
            "acceptance",
            ("personal_capability_state_content_sha256_v1",),
        ),
        (
            "from",
            1,
            "core",
            (
                "CompetenceFrameRef",
                "PersonalCapabilityState",
                "PersonalCapabilityStateId",
                "PersonalCapabilityStateSet",
                "StateError",
            ),
        ),
        (
            "from",
            1,
            "current_selection",
            (
                "CurrentStateSelectionAction",
                "PersonalCapabilityCurrentStateSelection",
                "PersonalCapabilityCurrentStateSelectionHistory",
                "personal_capability_current_state_selection_history_sha256_v1",
                "personal_capability_current_state_selection_sha256_v1",
            ),
        ),
        (
            "from",
            1,
            "current_selection_authority",
            (
                "PersonalCapabilityCurrentStateSelectionAuthorityBasis",
                "validate_personal_capability_current_state_selection_v1",
            ),
        ),
        (
            "from",
            1,
            "snapshot_transition",
            ("personal_capability_state_set_sha256_v1",),
        ),
    ]
