from dataclasses import fields
from datetime import datetime, timedelta, timezone

import pytest

from capability_lab.epistemics import CapabilityClaimId, CapabilitySubjectRef, ClaimEvaluationId
from capability_lab.semantics import CapabilityConceptRef
from capability_lab.state import (
    CompetenceDimensionState,
    CompetenceFrameRef,
    CurrentStateSelectionAction,
    CurrentStateSelectionMechanismKind,
    CurrentStateSelectionPolicyRef,
    CurrentStateSelectorRef,
    DimensionConflictStatus,
    DimensionStanding,
    InvalidCurrentStateSelection,
    PersonalCapabilityCurrentStateSelectionHistory,
    PersonalCapabilityCurrentStateSelectionRequest,
    PersonalCapabilityState,
    PersonalCapabilityStateAcceptanceAdmission,
    PersonalCapabilityStateAcceptanceRequest,
    PersonalCapabilityStateAcceptanceSet,
    PersonalCapabilityStateId,
    PersonalCapabilityStateSet,
    StateAcceptanceMechanismKind,
    StateAcceptancePolicyRef,
    StateAccepterRef,
    StateDerivationPolicyRef,
    StateDeriverKind,
    StateDeriverRef,
    accept_persisted_personal_capability_state_v1,
    build_complete_current_state_candidate_portfolio_v1,
    current_state_candidate_portfolio_sha256_v1,
    personal_capability_current_state_selection_sha256_v1,
    resolve_current_personal_capability_state_selection_v1,
    select_current_personal_capability_state_v1,
)


T0 = datetime(2026, 8, 22, 12, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("alice_pr11_8_current")
CONCEPT = CapabilityConceptRef.parse("core:current_selection_capability@1")
FRAME = CompetenceFrameRef.parse("core:current_selection_frame@1")
OTHER_CONCEPT = CapabilityConceptRef.parse("core:other_current_selection_capability@1")
OTHER_FRAME = CompetenceFrameRef.parse("core:other_current_selection_frame@1")
DERIVATION_POLICY = StateDerivationPolicyRef.parse("core:current_selection_derivation@1")
DERIVER = StateDeriverRef(StateDeriverKind.RULE, "current_selection_deriver")
ACCEPTANCE_POLICY = StateAcceptancePolicyRef.parse("core:current_selection_acceptance@1")
ACCEPTER = StateAccepterRef(StateAcceptanceMechanismKind.HUMAN, "current_selection_reviewer")
SELECTION_POLICY = CurrentStateSelectionPolicyRef.parse("core:explicit_current_selection@1")
SELECTOR = CurrentStateSelectorRef(
    CurrentStateSelectionMechanismKind.HUMAN,
    "current_selection_governor",
)
CLAIM = CapabilityClaimId("claim_pr11_8_current")
EVALUATION = ClaimEvaluationId("evaluation_pr11_8_current")


def _dimension(
    *,
    standing=DimensionStanding.SUPPORTED,
    conflict=DimensionConflictStatus.NONE,
):
    claims = (CLAIM,) if standing is DimensionStanding.SUPPORTED else ()
    evaluations = () if standing is DimensionStanding.UNKNOWN else (EVALUATION,)
    return CompetenceDimensionState(
        dimension_key="execution",
        standing=standing,
        supported_claim_ids=claims,
        basis_evaluation_ids=evaluations,
        rationale="Exact PR11.8 current-state dimension fixture.",
        conflict_status=conflict,
    )


def _state(
    state_id: str,
    *,
    concept=CONCEPT,
    frame=FRAME,
    as_of_minutes: int = 0,
    derived_minutes: int = 1,
    standing=DimensionStanding.SUPPORTED,
    conflict=DimensionConflictStatus.NONE,
):
    return PersonalCapabilityState(
        state_id=PersonalCapabilityStateId(state_id),
        subject_ref=SUBJECT,
        concept_ref=concept,
        frame_ref=frame,
        derivation_policy_ref=DERIVATION_POLICY,
        deriver_ref=DERIVER,
        as_of=T0 + timedelta(minutes=as_of_minutes),
        derived_at=T0 + timedelta(minutes=derived_minutes),
        dimensions=(_dimension(standing=standing, conflict=conflict),),
        rationale=f"Exact PR11.8 state {state_id}.",
    )


def _accept(
    state,
    *,
    predecessor,
    successor,
    accepted_minutes,
    policy=ACCEPTANCE_POLICY,
    accepter=ACCEPTER,
):
    acceptance = accept_persisted_personal_capability_state_v1(
        predecessor=predecessor,
        successor=successor,
        request=PersonalCapabilityStateAcceptanceRequest(
            state_id=state.state_id,
            acceptance_policy_ref=policy,
            accepter_ref=accepter,
            accepted_at=T0 + timedelta(minutes=accepted_minutes),
            rationale=f"Explicit acceptance for {state.state_id}.",
        ),
    )
    return acceptance, PersonalCapabilityStateAcceptanceAdmission(
        acceptance=acceptance,
        persistence_predecessor=predecessor,
        persistence_successor=successor,
    )


def _two_candidates():
    state_a = _state("state_a", as_of_minutes=0, derived_minutes=1)
    state_b = _state("state_b", as_of_minutes=2, derived_minutes=3)
    empty_states = PersonalCapabilityStateSet(SUBJECT)
    states_a = PersonalCapabilityStateSet(SUBJECT, (state_a,))
    states_ab = PersonalCapabilityStateSet(SUBJECT, (state_a, state_b))
    acceptance_a, admission_a = _accept(
        state_a,
        predecessor=empty_states,
        successor=states_a,
        accepted_minutes=2,
    )
    acceptance_b, admission_b = _accept(
        state_b,
        predecessor=states_a,
        successor=states_ab,
        accepted_minutes=4,
    )
    empty_acceptances = PersonalCapabilityStateAcceptanceSet(SUBJECT)
    acceptances_ab = PersonalCapabilityStateAcceptanceSet(
        SUBJECT,
        (acceptance_a, acceptance_b),
    )
    return (
        state_a,
        state_b,
        states_ab,
        acceptance_a,
        acceptance_b,
        admission_a,
        admission_b,
        empty_acceptances,
        acceptances_ab,
    )


def _request(
    action,
    *,
    state_id=None,
    selected_minutes=5,
    concept=CONCEPT,
    frame=FRAME,
):
    return PersonalCapabilityCurrentStateSelectionRequest(
        concept_ref=concept,
        frame_ref=frame,
        action=action,
        selected_state_id=state_id,
        selection_policy_ref=SELECTION_POLICY,
        selector_ref=SELECTOR,
        selected_at=T0 + timedelta(minutes=selected_minutes),
        rationale="Explicit governed current-state act.",
    )


def _select_a_fixture():
    fixture = _two_candidates()
    state_a = fixture[0]
    states_ab = fixture[2]
    admission_a, admission_b = fixture[5], fixture[6]
    empty_acceptances, acceptances_ab = fixture[7], fixture[8]
    empty_history = PersonalCapabilityCurrentStateSelectionHistory(SUBJECT)
    history_a = select_current_personal_capability_state_v1(
        state_snapshot=states_ab,
        acceptance_predecessor=empty_acceptances,
        acceptance_successor=acceptances_ab,
        acceptance_admissions=(admission_a, admission_b),
        selection_history=empty_history,
        request=_request(
            CurrentStateSelectionAction.SELECT,
            state_id=state_a.state_id,
            selected_minutes=5,
        ),
    )
    return fixture, history_a


def test_complete_candidate_portfolio_contains_every_accepted_state_in_scope() -> None:
    fixture = _two_candidates()
    states_ab, acceptances_ab = fixture[2], fixture[8]
    portfolio = build_complete_current_state_candidate_portfolio_v1(
        state_snapshot=states_ab,
        acceptance_set=acceptances_ab,
        concept_ref=CONCEPT,
        frame_ref=FRAME,
        as_of=T0 + timedelta(minutes=5),
    )
    assert portfolio.validator_issued is True
    assert portfolio.candidate_state_ids == (
        PersonalCapabilityStateId("state_a"),
        PersonalCapabilityStateId("state_b"),
    )
    assert len(current_state_candidate_portfolio_sha256_v1(portfolio)) == 64


def test_multiple_acceptances_for_one_state_do_not_create_multiple_candidates() -> None:
    fixture = _two_candidates()
    state_a, states_ab = fixture[0], fixture[2]
    acceptance_a, acceptance_b = fixture[3], fixture[4]
    second_a, _ = _accept(
        state_a,
        predecessor=states_ab,
        successor=states_ab,
        accepted_minutes=5,
        policy=StateAcceptancePolicyRef.parse("core:secondary_acceptance@2"),
        accepter=StateAccepterRef(StateAcceptanceMechanismKind.RULE, "secondary_rule"),
    )
    acceptance_set = PersonalCapabilityStateAcceptanceSet(
        SUBJECT,
        (acceptance_a, second_a, acceptance_b),
    )
    portfolio = build_complete_current_state_candidate_portfolio_v1(
        state_snapshot=states_ab,
        acceptance_set=acceptance_set,
        concept_ref=CONCEPT,
        frame_ref=FRAME,
        as_of=T0 + timedelta(minutes=6),
    )
    assert portfolio.candidate_state_ids.count(state_a.state_id) == 1
    entry_a = next(item for item in portfolio.entries if item.state_id == state_a.state_id)
    assert len(entry_a.acceptances) == 2


def test_future_acceptance_is_excluded_only_by_boundary_not_ranked() -> None:
    fixture = _two_candidates()
    states_ab, acceptances_ab = fixture[2], fixture[8]
    portfolio = build_complete_current_state_candidate_portfolio_v1(
        state_snapshot=states_ab,
        acceptance_set=acceptances_ab,
        concept_ref=CONCEPT,
        frame_ref=FRAME,
        as_of=T0 + timedelta(minutes=3),
    )
    assert portfolio.candidate_state_ids == (PersonalCapabilityStateId("state_a"),)


def test_wrong_concept_or_frame_is_out_of_scope_not_ranked_against_candidates() -> None:
    state_other = _state(
        "state_other",
        concept=OTHER_CONCEPT,
        frame=OTHER_FRAME,
        derived_minutes=5,
    )
    fixture = _two_candidates()
    states_ab = fixture[2]
    states_all = PersonalCapabilityStateSet(SUBJECT, states_ab.states + (state_other,))
    acceptance_other, _ = _accept(
        state_other,
        predecessor=states_ab,
        successor=states_all,
        accepted_minutes=6,
    )
    acceptance_set = PersonalCapabilityStateAcceptanceSet(
        SUBJECT,
        (fixture[3], fixture[4], acceptance_other),
    )
    portfolio = build_complete_current_state_candidate_portfolio_v1(
        state_snapshot=states_all,
        acceptance_set=acceptance_set,
        concept_ref=CONCEPT,
        frame_ref=FRAME,
        as_of=T0 + timedelta(minutes=7),
    )
    assert set(portfolio.candidate_state_ids) == {fixture[0].state_id, fixture[1].state_id}


def test_explicit_selection_can_choose_older_a_even_when_b_is_newer_everywhere() -> None:
    fixture, history = _select_a_fixture()
    state_a, state_b = fixture[0], fixture[1]
    current = resolve_current_personal_capability_state_selection_v1(
        history=history,
        concept_ref=CONCEPT,
        frame_ref=FRAME,
    )
    assert state_a.as_of < state_b.as_of
    assert state_a.derived_at < state_b.derived_at
    assert fixture[3].accepted_at < fixture[4].accepted_at
    assert current is not None
    assert current.selected_state_id == state_a.state_id


def test_single_candidate_still_requires_explicit_select_act() -> None:
    fixture = _two_candidates()
    state_a, states_ab, acceptance_a = fixture[0], fixture[2], fixture[3]
    only_a = PersonalCapabilityStateAcceptanceSet(SUBJECT, (acceptance_a,))
    portfolio = build_complete_current_state_candidate_portfolio_v1(
        state_snapshot=states_ab,
        acceptance_set=only_a,
        concept_ref=CONCEPT,
        frame_ref=FRAME,
        as_of=T0 + timedelta(minutes=5),
    )
    history = PersonalCapabilityCurrentStateSelectionHistory(SUBJECT)
    assert portfolio.candidate_state_ids == (state_a.state_id,)
    assert resolve_current_personal_capability_state_selection_v1(
        history=history,
        concept_ref=CONCEPT,
        frame_ref=FRAME,
    ) is None


def test_persisted_but_unaccepted_state_cannot_be_selected() -> None:
    fixture = _two_candidates()
    state_a, state_b, states_ab = fixture[0], fixture[1], fixture[2]
    empty_acceptances = PersonalCapabilityStateAcceptanceSet(SUBJECT)
    only_a = PersonalCapabilityStateAcceptanceSet(SUBJECT, (fixture[3],))
    with pytest.raises(
        InvalidCurrentStateSelection,
        match="complete accepted-state candidate universe",
    ):
        select_current_personal_capability_state_v1(
            state_snapshot=states_ab,
            acceptance_predecessor=empty_acceptances,
            acceptance_successor=only_a,
            acceptance_admissions=(fixture[5],),
            selection_history=PersonalCapabilityCurrentStateSelectionHistory(SUBJECT),
            request=_request(
                CurrentStateSelectionAction.SELECT,
                state_id=state_b.state_id,
                selected_minutes=5,
            ),
        )
    assert state_a.state_id != state_b.state_id


def test_select_b_after_a_creates_hash_linked_chain_and_moves_current() -> None:
    fixture, history_a = _select_a_fixture()
    state_b, states_ab, acceptances_ab = fixture[1], fixture[2], fixture[8]
    history_b = select_current_personal_capability_state_v1(
        state_snapshot=states_ab,
        acceptance_predecessor=acceptances_ab,
        acceptance_successor=acceptances_ab,
        selection_history=history_a,
        request=_request(
            CurrentStateSelectionAction.SELECT,
            state_id=state_b.state_id,
            selected_minutes=6,
        ),
    )
    current = resolve_current_personal_capability_state_selection_v1(
        history=history_b,
        concept_ref=CONCEPT,
        frame_ref=FRAME,
    )
    assert current is not None
    assert current.selected_state_id == state_b.state_id
    first = next(
        item
        for item in history_b.selections
        if item.selected_state_id == fixture[0].state_id
    )
    assert current.predecessor_selection_sha256 == (
        personal_capability_current_state_selection_sha256_v1(first)
    )


def test_clear_removes_current_authority_without_removing_state_or_acceptance() -> None:
    fixture, history_a = _select_a_fixture()
    states_ab, acceptances_ab = fixture[2], fixture[8]
    cleared = select_current_personal_capability_state_v1(
        state_snapshot=states_ab,
        acceptance_predecessor=acceptances_ab,
        acceptance_successor=acceptances_ab,
        selection_history=history_a,
        request=_request(CurrentStateSelectionAction.CLEAR, selected_minutes=6),
    )
    assert resolve_current_personal_capability_state_selection_v1(
        history=cleared,
        concept_ref=CONCEPT,
        frame_ref=FRAME,
    ) is None
    assert len(states_ab.states) == 2
    assert len(acceptances_ab.acceptances) == 2


def test_clear_then_select_b_is_explicit_reactivation_not_latest_wins() -> None:
    fixture, history_a = _select_a_fixture()
    states_ab, acceptances_ab = fixture[2], fixture[8]
    cleared = select_current_personal_capability_state_v1(
        state_snapshot=states_ab,
        acceptance_predecessor=acceptances_ab,
        acceptance_successor=acceptances_ab,
        selection_history=history_a,
        request=_request(CurrentStateSelectionAction.CLEAR, selected_minutes=6),
    )
    reselected = select_current_personal_capability_state_v1(
        state_snapshot=states_ab,
        acceptance_predecessor=acceptances_ab,
        acceptance_successor=acceptances_ab,
        selection_history=cleared,
        request=_request(
            CurrentStateSelectionAction.SELECT,
            state_id=fixture[1].state_id,
            selected_minutes=7,
        ),
    )
    current = resolve_current_personal_capability_state_selection_v1(
        history=reselected,
        concept_ref=CONCEPT,
        frame_ref=FRAME,
    )
    assert current is not None and current.selected_state_id == fixture[1].state_id


def test_new_acceptance_append_does_not_move_existing_current_without_selection_act() -> None:
    fixture, history_a = _select_a_fixture()
    state_c = _state("state_c", as_of_minutes=6, derived_minutes=7)
    states_ab = fixture[2]
    states_abc = PersonalCapabilityStateSet(SUBJECT, states_ab.states + (state_c,))
    acceptance_c, _ = _accept(
        state_c,
        predecessor=states_ab,
        successor=states_abc,
        accepted_minutes=8,
    )
    current = resolve_current_personal_capability_state_selection_v1(
        history=history_a,
        concept_ref=CONCEPT,
        frame_ref=FRAME,
    )
    assert acceptance_c.state_id == state_c.state_id
    assert current is not None and current.selected_state_id == fixture[0].state_id


def test_unknown_insufficient_and_unresolved_states_are_not_filtered_from_candidates() -> None:
    state_unknown = _state(
        "state_unknown",
        derived_minutes=1,
        standing=DimensionStanding.UNKNOWN,
    )
    state_insufficient = _state(
        "state_insufficient",
        as_of_minutes=2,
        derived_minutes=3,
        standing=DimensionStanding.INSUFFICIENT,
    )
    state_conflict = _state(
        "state_conflict",
        as_of_minutes=4,
        derived_minutes=5,
        conflict=DimensionConflictStatus.UNRESOLVED,
    )
    s0 = PersonalCapabilityStateSet(SUBJECT)
    s1 = PersonalCapabilityStateSet(SUBJECT, (state_unknown,))
    s2 = PersonalCapabilityStateSet(SUBJECT, (state_unknown, state_insufficient))
    s3 = PersonalCapabilityStateSet(
        SUBJECT,
        (state_unknown, state_insufficient, state_conflict),
    )
    a1, _ = _accept(state_unknown, predecessor=s0, successor=s1, accepted_minutes=2)
    a2, _ = _accept(state_insufficient, predecessor=s1, successor=s2, accepted_minutes=4)
    a3, _ = _accept(state_conflict, predecessor=s2, successor=s3, accepted_minutes=6)
    portfolio = build_complete_current_state_candidate_portfolio_v1(
        state_snapshot=s3,
        acceptance_set=PersonalCapabilityStateAcceptanceSet(SUBJECT, (a1, a2, a3)),
        concept_ref=CONCEPT,
        frame_ref=FRAME,
        as_of=T0 + timedelta(minutes=7),
    )
    assert set(portfolio.candidate_state_ids) == {
        state_unknown.state_id,
        state_insufficient.state_id,
        state_conflict.state_id,
    }


def test_selection_record_contains_no_ranking_or_progression_fields() -> None:
    forbidden = {
        "score",
        "weight",
        "confidence",
        "rank",
        "preferred_state_id",
        "latest_state_id",
        "progression_state_id",
        "progression_authority",
    }
    from capability_lab.state import PersonalCapabilityCurrentStateSelection

    assert forbidden.isdisjoint(
        field.name for field in fields(PersonalCapabilityCurrentStateSelection)
    )


def test_selector_role_is_distinct_from_deriver_and_accepter_role() -> None:
    assert CurrentStateSelectionMechanismKind.HUMAN.value == "human"
    assert type(SELECTOR.kind) is CurrentStateSelectionMechanismKind
    assert type(ACCEPTER.kind) is StateAcceptanceMechanismKind
    assert type(DERIVER.kind) is StateDeriverKind
