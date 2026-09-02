from dataclasses import fields
from datetime import timedelta

from capability_lab.state import (
    CurrentStateSelectionAction,
    CurrentStateSelectionMechanismKind,
    CurrentStateSelectionPolicyRef,
    CurrentStateSelectorRef,
    PersonalCapabilityCurrentStateSelection,
    PersonalCapabilityCurrentStateSelectionHistory,
    PersonalCapabilityCurrentStateSelectionRequest,
    PersonalCapabilityStateAcceptanceAdmission,
    PersonalCapabilityStateAcceptanceRequest,
    PersonalCapabilityStateAcceptanceSet,
    PersonalCapabilityStateSet,
    StateAcceptanceMechanismKind,
    StateAcceptancePolicyRef,
    StateAccepterRef,
    accept_persisted_personal_capability_state_v1,
    build_complete_current_state_candidate_portfolio_v1,
    resolve_current_personal_capability_state_selection_v1,
    select_current_personal_capability_state_v1,
    validate_personal_capability_state_acceptance_set_successor_v1,
)

from test_civilization_bootstrap_pilot_01_state_acceptance_integration_v1 import (
    _acceptance_request,
    _derive_correction,
    _derive_initial,
)


SELECTION_POLICY = CurrentStateSelectionPolicyRef.parse(
    "pilot:governed_current_state_selection@1"
)
SELECTOR = CurrentStateSelectorRef(
    CurrentStateSelectionMechanismKind.HUMAN,
    "civilization_bootstrap_current_state_governor",
)


def _real_two_accepted(tmp_path, *, suffix):
    snapshot, evaluation, claim, _, state_a = _derive_initial(
        tmp_path,
        f"state_pilot_01_pr11_8_{suffix}_a",
    )
    _, _, _, state_b = _derive_correction(
        snapshot,
        evaluation,
        claim,
        suffix=f"pr11_8_{suffix}_b",
        state_id=f"state_pilot_01_pr11_8_{suffix}_b",
    )
    empty_states = PersonalCapabilityStateSet(claim.subject_ref)
    history_a = PersonalCapabilityStateSet(claim.subject_ref, (state_a,))
    history_ab = PersonalCapabilityStateSet(claim.subject_ref, (state_a, state_b))

    acceptance_a = accept_persisted_personal_capability_state_v1(
        predecessor=history_a,
        successor=history_ab,
        request=_acceptance_request(
            state_a,
            accepted_at=state_b.derived_at + timedelta(minutes=1),
        ),
    )
    acceptance_b = accept_persisted_personal_capability_state_v1(
        predecessor=history_a,
        successor=history_ab,
        request=_acceptance_request(
            state_b,
            accepted_at=state_b.derived_at + timedelta(minutes=2),
        ),
    )
    admission_a = PersonalCapabilityStateAcceptanceAdmission(
        acceptance=acceptance_a,
        persistence_predecessor=history_a,
        persistence_successor=history_ab,
    )
    admission_b = PersonalCapabilityStateAcceptanceAdmission(
        acceptance=acceptance_b,
        persistence_predecessor=history_a,
        persistence_successor=history_ab,
    )
    empty_acceptances = PersonalCapabilityStateAcceptanceSet(claim.subject_ref)
    accepted_ab = PersonalCapabilityStateAcceptanceSet(
        claim.subject_ref,
        (acceptance_a, acceptance_b),
    )
    return (
        claim,
        state_a,
        state_b,
        history_ab,
        acceptance_a,
        acceptance_b,
        admission_a,
        admission_b,
        empty_acceptances,
        accepted_ab,
        empty_states,
    )


def _selection_request(state, *, action, selected_at, selected_state_id=None):
    return PersonalCapabilityCurrentStateSelectionRequest(
        concept_ref=state.concept_ref,
        frame_ref=state.frame_ref,
        action=action,
        selected_state_id=selected_state_id,
        selection_policy_ref=SELECTION_POLICY,
        selector_ref=SELECTOR,
        selected_at=selected_at,
        rationale="Pilot explicitly governs the current-state authority boundary.",
    )


def _select_real_a(tmp_path, *, suffix):
    fixture = _real_two_accepted(tmp_path, suffix=suffix)
    state_a, state_b = fixture[1], fixture[2]
    history_ab = fixture[3]
    empty_acceptances, accepted_ab = fixture[8], fixture[9]
    selection_history = PersonalCapabilityCurrentStateSelectionHistory(
        fixture[0].subject_ref
    )
    selected_at = state_b.derived_at + timedelta(minutes=3)
    history_a = select_current_personal_capability_state_v1(
        state_snapshot=history_ab,
        acceptance_predecessor=empty_acceptances,
        acceptance_successor=accepted_ab,
        acceptance_admissions=(fixture[6], fixture[7]),
        selection_history=selection_history,
        request=_selection_request(
            state_a,
            action=CurrentStateSelectionAction.SELECT,
            selected_state_id=state_a.state_id,
            selected_at=selected_at,
        ),
    )
    return fixture, history_a


def test_real_pr11_7_a_and_b_form_complete_pr11_8_candidate_universe(tmp_path) -> None:
    fixture = _real_two_accepted(tmp_path, suffix="complete")
    state_a, state_b, history_ab, accepted_ab = (
        fixture[1],
        fixture[2],
        fixture[3],
        fixture[9],
    )
    portfolio = build_complete_current_state_candidate_portfolio_v1(
        state_snapshot=history_ab,
        acceptance_set=accepted_ab,
        concept_ref=state_a.concept_ref,
        frame_ref=state_a.frame_ref,
        as_of=state_b.derived_at + timedelta(minutes=3),
    )
    assert set(portfolio.candidate_state_ids) == {state_a.state_id, state_b.state_id}
    assert portfolio.validator_issued is True


def test_real_newer_b_does_not_win_when_governance_explicitly_selects_a(tmp_path) -> None:
    fixture, history_a = _select_real_a(tmp_path, suffix="anti_latest")
    state_a, state_b = fixture[1], fixture[2]
    acceptance_a, acceptance_b = fixture[4], fixture[5]
    current = resolve_current_personal_capability_state_selection_v1(
        history=history_a,
        concept_ref=state_a.concept_ref,
        frame_ref=state_a.frame_ref,
    )
    assert state_a.as_of < state_b.as_of
    assert state_a.derived_at < state_b.derived_at
    assert acceptance_a.accepted_at < acceptance_b.accepted_at
    assert current is not None
    assert current.selected_state_id == state_a.state_id


def test_real_new_acceptance_fact_does_not_move_current_without_new_selection(tmp_path) -> None:
    fixture, history_a = _select_real_a(tmp_path, suffix="acceptance_append")
    claim, state_a, state_b, history_ab = fixture[0], fixture[1], fixture[2], fixture[3]
    accepted_ab = fixture[9]
    second_acceptance_b = accept_persisted_personal_capability_state_v1(
        predecessor=history_ab,
        successor=history_ab,
        request=PersonalCapabilityStateAcceptanceRequest(
            state_id=state_b.state_id,
            acceptance_policy_ref=StateAcceptancePolicyRef.parse(
                "pilot:secondary_current_candidate_acceptance@1"
            ),
            accepter_ref=StateAccepterRef(
                StateAcceptanceMechanismKind.RULE,
                "civilization_bootstrap_secondary_acceptance_rule",
            ),
            accepted_at=state_b.derived_at + timedelta(minutes=4),
            rationale="Second governed acceptance fact must not auto-move current.",
        ),
    )
    admission = PersonalCapabilityStateAcceptanceAdmission(
        acceptance=second_acceptance_b,
        persistence_predecessor=history_ab,
        persistence_successor=history_ab,
    )
    accepted_ab2 = PersonalCapabilityStateAcceptanceSet(
        claim.subject_ref,
        accepted_ab.acceptances + (second_acceptance_b,),
    )
    validate_personal_capability_state_acceptance_set_successor_v1(
        state_snapshot=history_ab,
        predecessor=accepted_ab,
        successor=accepted_ab2,
        admissions=(admission,),
    )
    current = resolve_current_personal_capability_state_selection_v1(
        history=history_a,
        concept_ref=state_a.concept_ref,
        frame_ref=state_a.frame_ref,
    )
    assert current is not None and current.selected_state_id == state_a.state_id


def test_real_explicit_reselection_moves_current_from_a_to_b(tmp_path) -> None:
    fixture, history_a = _select_real_a(tmp_path, suffix="reselect")
    state_a, state_b, history_ab, accepted_ab = (
        fixture[1],
        fixture[2],
        fixture[3],
        fixture[9],
    )
    history_b = select_current_personal_capability_state_v1(
        state_snapshot=history_ab,
        acceptance_predecessor=accepted_ab,
        acceptance_successor=accepted_ab,
        selection_history=history_a,
        request=_selection_request(
            state_b,
            action=CurrentStateSelectionAction.SELECT,
            selected_state_id=state_b.state_id,
            selected_at=state_b.derived_at + timedelta(minutes=4),
        ),
    )
    current = resolve_current_personal_capability_state_selection_v1(
        history=history_b,
        concept_ref=state_a.concept_ref,
        frame_ref=state_a.frame_ref,
    )
    assert current is not None and current.selected_state_id == state_b.state_id
    assert len(history_b.selections) == 2


def test_real_clear_removes_current_authority_without_rewriting_state_or_acceptance(
    tmp_path,
) -> None:
    fixture, history_a = _select_real_a(tmp_path, suffix="clear")
    state_a, state_b, history_ab, accepted_ab = (
        fixture[1],
        fixture[2],
        fixture[3],
        fixture[9],
    )
    cleared = select_current_personal_capability_state_v1(
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
    assert resolve_current_personal_capability_state_selection_v1(
        history=cleared,
        concept_ref=state_a.concept_ref,
        frame_ref=state_a.frame_ref,
    ) is None
    assert {item.state_id for item in history_ab.states} == {
        state_a.state_id,
        state_b.state_id,
    }
    assert len(accepted_ab.acceptances) == 2


def test_real_current_selection_still_exposes_no_progression_authority(tmp_path) -> None:
    _, history_a = _select_real_a(tmp_path, suffix="boundary")
    selection = history_a.selections[0]
    names = {field.name for field in fields(PersonalCapabilityCurrentStateSelection)}
    assert selection.action is CurrentStateSelectionAction.SELECT
    assert "progression_authority" not in names
    assert "progression_frontier_id" not in names
    assert "progression_state_id" not in names
