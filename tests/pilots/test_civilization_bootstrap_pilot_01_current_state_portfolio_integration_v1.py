from datetime import timedelta

from capability_lab.state import (
    CurrentStateSelectionAction,
    PersonalCapabilityCurrentStateSelectionAuthorityBasis,
    derive_personal_capability_current_state_portfolio_v1,
    select_current_personal_capability_state_v1,
    validate_personal_capability_current_state_portfolio_v1,
)

from test_civilization_bootstrap_pilot_01_current_state_selection_integration_v1 import (
    _select_real_a,
    _selection_request,
)


def _root_basis(fixture, history):
    return PersonalCapabilityCurrentStateSelectionAuthorityBasis(
        selection=history.selections[0],
        state_snapshot=fixture[3],
        acceptance_predecessor=fixture[8],
        acceptance_successor=fixture[9],
        acceptance_admissions=(fixture[6], fixture[7]),
    )


def _real_clear(tmp_path, *, suffix):
    fixture, history_a = _select_real_a(tmp_path, suffix=suffix)
    state_a, state_b, history_ab, accepted_ab = (
        fixture[1],
        fixture[2],
        fixture[3],
        fixture[9],
    )
    history_clear = select_current_personal_capability_state_v1(
        state_snapshot=history_ab,
        acceptance_predecessor=accepted_ab,
        acceptance_successor=accepted_ab,
        selection_history=history_a,
        request=_selection_request(
            state_a,
            action=CurrentStateSelectionAction.CLEAR,
            selected_at=state_b.derived_at + timedelta(minutes=4),
        ),
    )
    clear = max(history_clear.selections, key=lambda item: item.selected_at)
    bases = (
        _root_basis(fixture, history_a),
        PersonalCapabilityCurrentStateSelectionAuthorityBasis(
            selection=clear,
            state_snapshot=history_ab,
            acceptance_predecessor=accepted_ab,
            acceptance_successor=accepted_ab,
        ),
    )
    return fixture, history_clear, bases


def test_real_older_a_remains_complete_current_portfolio_state_despite_newer_b(tmp_path) -> None:
    fixture, history_a = _select_real_a(tmp_path, suffix="portfolio_anti_latest")
    state_a, state_b = fixture[1], fixture[2]
    portfolio = derive_personal_capability_current_state_portfolio_v1(
        history=history_a,
        authority_bases=(_root_basis(fixture, history_a),),
        generated_at=state_b.derived_at + timedelta(minutes=5),
    )
    assert state_a.as_of < state_b.as_of
    assert state_a.derived_at < state_b.derived_at
    assert len(portfolio.entries) == 1
    assert portfolio.entries[0].action is CurrentStateSelectionAction.SELECT
    assert portfolio.entries[0].selected_state_id == state_a.state_id
    assert tuple(item.state_id for item in portfolio.current_state_set.states) == (
        state_a.state_id,
    )


def test_real_clear_is_visible_and_removes_state_from_current_state_set(tmp_path) -> None:
    fixture, history_clear, bases = _real_clear(tmp_path, suffix="portfolio_clear")
    state_b = fixture[2]
    portfolio = derive_personal_capability_current_state_portfolio_v1(
        history=history_clear,
        authority_bases=bases,
        generated_at=state_b.derived_at + timedelta(minutes=5),
    )
    assert len(portfolio.entries) == 1
    assert portfolio.entries[0].action is CurrentStateSelectionAction.CLEAR
    assert portfolio.entries[0].selected_state_id is None
    assert portfolio.current_state_set.states == ()


def test_real_current_state_portfolio_fresh_revalidation_passes(tmp_path) -> None:
    fixture, history_clear, bases = _real_clear(tmp_path, suffix="portfolio_validate")
    state_b = fixture[2]
    portfolio = derive_personal_capability_current_state_portfolio_v1(
        history=history_clear,
        authority_bases=bases,
        generated_at=state_b.derived_at + timedelta(minutes=5),
    )
    assert (
        validate_personal_capability_current_state_portfolio_v1(
            history=history_clear,
            authority_bases=bases,
            portfolio=portfolio,
        )
        is None
    )
