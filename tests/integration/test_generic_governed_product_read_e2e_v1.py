from dataclasses import fields, replace
from pathlib import Path

import pytest

from capability_lab.history import (
    AchievementFamilyCatalog,
    PersonalHistoryRecordSet,
    PersonalLegendSet,
)
from capability_lab.player_window import (
    CurrentStateGovernedPlayerWindow,
    CurrentStatePlayerWindowRequest,
    InvalidCurrentStateGovernedPlayerWindow,
    InvalidPlayerWindow,
    PlayerWindowId,
    PlayerWindowMechanismKind,
    PlayerWindowRequesterRef,
    PlayerWindowViewerRef,
    current_state_governed_player_window_sha256_v1,
    derive_current_state_governed_player_window_v1,
    validate_current_state_governed_player_window_v1,
)
from capability_lab.progression import (
    CurrentStateProgressionAuthorityStatus,
    CurrentStateProgressionFrontierRequest,
    CurrentStateProgressionSeed,
    ProgressionAuthorityHandoffError,
    ProgressionFrontierId,
    ProgressionMechanismKind,
    ProgressionRequesterRef,
    current_state_governed_progression_frontier_sha256_v1,
    derive_progression_frontier_from_current_state_v1,
    validate_current_state_governed_progression_frontier_v1,
)
from capability_lab.state import (
    CompetenceFrameCatalog,
    CurrentStateSelectionAction,
    CurrentStateSelectionMechanismKind,
    CurrentStateSelectionPolicyRef,
    CurrentStateSelectorRef,
    InvalidPersonalCapabilityCurrentStatePortfolio,
    PersonalCapabilityCurrentStateSelectionAuthorityBasis,
    PersonalCapabilityCurrentStateSelectionHistory,
    PersonalCapabilityCurrentStateSelectionRequest,
    PersonalCapabilityStateId,
    derive_personal_capability_current_state_portfolio_v1,
    personal_capability_current_state_portfolio_sha256_v1,
    select_current_personal_capability_state_v1,
    validate_personal_capability_current_state_portfolio_v1,
)

from test_generic_capability_inference_e2e_v1 import _at, _positive_basis


PROGRESSION_REQUESTER = ProgressionRequesterRef(
    ProgressionMechanismKind.HUMAN,
    "human-pr12-14-progression-requester",
)
WINDOW_REQUESTER = PlayerWindowRequesterRef(
    PlayerWindowMechanismKind.HUMAN,
    "human-pr12-14-window-requester",
)
VIEWER = PlayerWindowViewerRef(
    PlayerWindowMechanismKind.HUMAN,
    "human-pr12-14-viewer",
)
CLEAR_POLICY = CurrentStateSelectionPolicyRef.parse(
    "research:pr12_14_clear_current_scope@1"
)
CLEAR_SELECTOR = CurrentStateSelectorRef(
    CurrentStateSelectionMechanismKind.HUMAN,
    "human-pr12-14-clear-selector",
)


def _case():
    basis = _positive_basis()
    frames = CompetenceFrameCatalog((basis["frame"],))
    progression_request = CurrentStateProgressionFrontierRequest(
        frontier_id=ProgressionFrontierId("frontier_pr12_14_generic_product_read"),
        as_of=_at(14),
        generated_at=_at(14),
        requester_ref=PROGRESSION_REQUESTER,
        seeds=(
            CurrentStateProgressionSeed(
                concept_ref=basis["state"].concept_ref,
                frame_ref=basis["state"].frame_ref,
                dimension_keys=("reasoning",),
            ),
        ),
    )
    window_request = CurrentStatePlayerWindowRequest(
        window_id=PlayerWindowId("window_pr12_14_generic_product_read"),
        generated_at=_at(14),
        requester_ref=WINDOW_REQUESTER,
        viewer_ref=VIEWER,
        progression_request=progression_request,
    )
    return {
        **basis,
        "frames": frames,
        "progression_request": progression_request,
        "window_request": window_request,
        "family_catalog": AchievementFamilyCatalog(()),
        "history_set": PersonalHistoryRecordSet(basis["state"].subject_ref, (), ()),
        "legend_set": PersonalLegendSet(basis["state"].subject_ref),
    }


def _clear_current(case, *, selected_at=None):
    history = select_current_personal_capability_state_v1(
        state_snapshot=case["persisted_states"],
        acceptance_predecessor=case["accepted_states"],
        acceptance_successor=case["accepted_states"],
        acceptance_admissions=(),
        selection_history=case["selection_history"],
        request=PersonalCapabilityCurrentStateSelectionRequest(
            concept_ref=case["state"].concept_ref,
            frame_ref=case["state"].frame_ref,
            action=CurrentStateSelectionAction.CLEAR,
            selected_state_id=None,
            selection_policy_ref=CLEAR_POLICY,
            selector_ref=CLEAR_SELECTOR,
            selected_at=_at(13) if selected_at is None else selected_at,
            rationale="Human explicitly clears the previously governed current scope.",
        ),
    )
    clear_selection = history.selections[-1]
    clear_basis = PersonalCapabilityCurrentStateSelectionAuthorityBasis(
        selection=clear_selection,
        state_snapshot=case["persisted_states"],
        acceptance_predecessor=case["accepted_states"],
        acceptance_successor=case["accepted_states"],
        acceptance_admissions=(),
    )
    return history, (case["authority_basis"], clear_basis), clear_selection


def _derive_progression(case, *, history=None, bases=None, request=None):
    return derive_progression_frontier_from_current_state_v1(
        capability_catalog=case["catalog"],
        frame_catalog=case["frames"],
        records=case["final_epistemics"],
        selection_history=history or case["selection_history"],
        authority_bases=(
            (case["authority_basis"],) if bases is None else bases
        ),
        request=request or case["progression_request"],
    )


def _derive_portfolio(case, *, history=None, bases=None, generated_at=None):
    return derive_personal_capability_current_state_portfolio_v1(
        history=history or case["selection_history"],
        authority_bases=((case["authority_basis"],) if bases is None else bases),
        generated_at=generated_at or _at(14),
    )


def _derive_window(case, *, history=None, bases=None, request=None):
    return derive_current_state_governed_player_window_v1(
        capability_catalog=case["catalog"],
        competence_frame_catalog=case["frames"],
        epistemic_records=case["final_epistemics"],
        selection_history=history or case["selection_history"],
        authority_bases=((case["authority_basis"],) if bases is None else bases),
        achievement_family_catalog=case["family_catalog"],
        history_set=case["history_set"],
        legend_set=case["legend_set"],
        request=request or case["window_request"],
    )


def _validate_window(case, snapshot, *, history=None, bases=None):
    return validate_current_state_governed_player_window_v1(
        capability_catalog=case["catalog"],
        competence_frame_catalog=case["frames"],
        epistemic_records=case["final_epistemics"],
        selection_history=history or case["selection_history"],
        authority_bases=((case["authority_basis"],) if bases is None else bases),
        achievement_family_catalog=case["family_catalog"],
        history_set=case["history_set"],
        legend_set=case["legend_set"],
        snapshot=snapshot,
    )


def test_generic_external_observation_reaches_governed_product_read_snapshot():
    case = _case()
    governed_progression = _derive_progression(case)
    portfolio = _derive_portfolio(case)
    snapshot = _derive_window(case)

    assert governed_progression.authority_bindings[0].status is CurrentStateProgressionAuthorityStatus.SELECT
    assert governed_progression.authority_bindings[0].selected_state_id == case["state"].state_id
    assert governed_progression.frontier.seed_bindings[0].state_id == case["state"].state_id

    assert len(portfolio.entries) == 1
    assert portfolio.entries[0].action is CurrentStateSelectionAction.SELECT
    assert portfolio.entries[0].selected_state_id == case["state"].state_id
    assert tuple(state.state_id for state in portfolio.current_state_set.states) == (
        case["state"].state_id,
    )

    assert snapshot.current_state_entries == portfolio.entries
    assert snapshot.window.selected_state_ids == (case["state"].state_id,)
    assert snapshot.frontier_authority_bindings == governed_progression.authority_bindings
    assert snapshot.window.selected_frontier_id == case["progression_request"].frontier_id
    assert snapshot.window.frontier is not None
    assert snapshot.current_state_portfolio_sha256 == personal_capability_current_state_portfolio_sha256_v1(portfolio)
    assert snapshot.governed_frontier_sha256 == current_state_governed_progression_frontier_sha256_v1(governed_progression)
    assert len(current_state_governed_player_window_sha256_v1(snapshot)) == 64

    validate_current_state_governed_progression_frontier_v1(
        capability_catalog=case["catalog"],
        frame_catalog=case["frames"],
        records=case["final_epistemics"],
        selection_history=case["selection_history"],
        authority_bases=(case["authority_basis"],),
        governed_frontier=governed_progression,
    )
    validate_personal_capability_current_state_portfolio_v1(
        history=case["selection_history"],
        authority_bases=(case["authority_basis"],),
        portfolio=portfolio,
    )
    assert _validate_window(case, snapshot) is None


def test_pr11_9_and_pr11_11_requests_expose_no_state_or_prebuilt_authority_selection_surface():
    progression_fields = {item.name for item in fields(CurrentStateProgressionFrontierRequest)}
    seed_fields = {item.name for item in fields(CurrentStateProgressionSeed)}
    window_fields = {item.name for item in fields(CurrentStatePlayerWindowRequest)}

    assert "subject_ref" not in progression_fields
    assert "state_id" not in seed_fields
    assert "selected_state_id" not in seed_fields
    assert {
        "current_state_portfolio",
        "governed_frontier",
        "selected_state_ids",
        "selected_frontier",
        "subject_ref",
    }.isdisjoint(window_fields)


def test_progression_request_rejects_generated_at_before_as_of_before_product_composition():
    case = _case()
    with pytest.raises(ProgressionAuthorityHandoffError, match="generated_at must not precede as_of"):
        CurrentStateProgressionFrontierRequest(
            frontier_id=ProgressionFrontierId("frontier_pr12_14_invalid_time_order"),
            as_of=_at(14),
            generated_at=_at(13),
            requester_ref=PROGRESSION_REQUESTER,
            seeds=(
                CurrentStateProgressionSeed(
                    concept_ref=case["state"].concept_ref,
                    frame_ref=case["state"].frame_ref,
                    dimension_keys=("reasoning",),
                ),
            ),
        )


def test_missing_pr11_8_authority_basis_rejects_all_downstream_governed_derivations():
    case = _case()
    with pytest.raises(ProgressionAuthorityHandoffError):
        _derive_progression(case, bases=())
    with pytest.raises(InvalidPersonalCapabilityCurrentStatePortfolio):
        _derive_portfolio(case, bases=())
    with pytest.raises(InvalidCurrentStateGovernedPlayerWindow):
        _derive_window(case, bases=())


def test_future_current_governance_relative_to_product_generated_at_fails_closed():
    case = _case()
    history, bases, clear_selection = _clear_current(case, selected_at=_at(15))
    assert clear_selection.selected_at > case["window_request"].generated_at
    with pytest.raises(InvalidCurrentStateGovernedPlayerWindow, match="generated_at"):
        _derive_window(case, history=history, bases=bases)


def test_clear_after_real_select_remains_clear_not_absent_and_cannot_seed_progression():
    case = _case()
    history, bases, clear_selection = _clear_current(case)
    portfolio = _derive_portfolio(case, history=history, bases=bases)

    assert clear_selection.action is CurrentStateSelectionAction.CLEAR
    assert len(portfolio.entries) == 1
    assert portfolio.entries[0].action is CurrentStateSelectionAction.CLEAR
    assert portfolio.entries[0].selected_state_id is None
    assert portfolio.current_state_set.states == ()

    with pytest.raises(ProgressionAuthorityHandoffError, match="scope resolved as clear"):
        _derive_progression(case, history=history, bases=bases)

    with pytest.raises(ProgressionAuthorityHandoffError, match="scope resolved as absent"):
        _derive_progression(
            case,
            history=PersonalCapabilityCurrentStateSelectionHistory(case["state"].subject_ref),
            bases=(),
        )


def test_pr11_10_clear_history_rejects_incomplete_authority_basis_coverage():
    case = _case()
    history, bases, _ = _clear_current(case)
    portfolio = _derive_portfolio(case, history=history, bases=bases)

    with pytest.raises(InvalidPersonalCapabilityCurrentStatePortfolio):
        validate_personal_capability_current_state_portfolio_v1(
            history=history,
            authority_bases=(case["authority_basis"],),
            portfolio=portfolio,
        )


def test_historical_clear_append_stales_cached_pr11_10_and_pr11_11_artifacts_even_before_generated_at():
    case = _case()
    old_portfolio = _derive_portfolio(case)
    old_snapshot = _derive_window(case)
    history, bases, clear_selection = _clear_current(case)
    assert clear_selection.selected_at <= old_snapshot.request.generated_at

    with pytest.raises(InvalidPersonalCapabilityCurrentStatePortfolio):
        validate_personal_capability_current_state_portfolio_v1(
            history=history,
            authority_bases=bases,
            portfolio=old_portfolio,
        )
    with pytest.raises(InvalidCurrentStateGovernedPlayerWindow):
        _validate_window(case, old_snapshot, history=history, bases=bases)


def test_product_as_of_before_selected_state_semantics_fails_closed_during_fresh_composition():
    case = _case()
    assert case["state"].as_of == _at(9)
    progression = CurrentStateProgressionFrontierRequest(
        frontier_id=ProgressionFrontierId("frontier_pr12_14_historical_filter_attack"),
        as_of=_at(8),
        generated_at=_at(14),
        requester_ref=PROGRESSION_REQUESTER,
        seeds=(
            CurrentStateProgressionSeed(
                concept_ref=case["state"].concept_ref,
                frame_ref=case["state"].frame_ref,
                dimension_keys=("reasoning",),
            ),
        ),
    )
    request = CurrentStatePlayerWindowRequest(
        window_id=PlayerWindowId("window_pr12_14_historical_filter_attack"),
        generated_at=_at(14),
        requester_ref=WINDOW_REQUESTER,
        viewer_ref=VIEWER,
        progression_request=progression,
    )
    with pytest.raises(
        InvalidCurrentStateGovernedPlayerWindow,
        match="selected progression state may not represent a time after frontier as_of",
    ):
        _derive_window(case, request=request)


def test_pr11_11_rejects_wrong_frontier_digest_against_fresh_sources():
    case = _case()
    snapshot = _derive_window(case)
    forged = replace(snapshot, governed_frontier_sha256="0" * 64)
    with pytest.raises(InvalidCurrentStateGovernedPlayerWindow):
        _validate_window(case, forged)


def test_pr11_11_rejects_wrong_current_portfolio_digest_against_fresh_sources():
    case = _case()
    snapshot = _derive_window(case)
    forged = replace(snapshot, current_state_portfolio_sha256="0" * 64)
    with pytest.raises(InvalidCurrentStateGovernedPlayerWindow):
        _validate_window(case, forged)


def test_pr11_11_rejects_tampered_frontier_authority_bindings():
    case = _case()
    snapshot = _derive_window(case)
    forged = replace(snapshot, frontier_authority_bindings=())
    with pytest.raises(InvalidCurrentStateGovernedPlayerWindow):
        _validate_window(case, forged)


def test_raw_player_window_cannot_hide_or_invent_current_select_state():
    case = _case()
    snapshot = _derive_window(case)
    with pytest.raises(
        InvalidPlayerWindow,
        match="capability entries must exactly match selected_state_ids",
    ):
        replace(snapshot.window, selected_state_ids=())

    invented = PersonalCapabilityStateId("state_pr12_14_invented")
    with pytest.raises(
        InvalidPlayerWindow,
        match="capability entries must exactly match selected_state_ids",
    ):
        replace(
            snapshot.window,
            selected_state_ids=(case["state"].state_id, invented),
        )


def test_pr11_11_serialization_replay_remains_audit_data_and_revalidates_against_live_sources():
    case = _case()
    snapshot = _derive_window(case)
    restored = CurrentStateGovernedPlayerWindow.from_json(snapshot.to_json())
    assert restored == snapshot
    assert current_state_governed_player_window_sha256_v1(restored) == (
        current_state_governed_player_window_sha256_v1(snapshot)
    )
    assert _validate_window(case, restored) is None


def test_product_projection_does_not_mutate_current_history_or_state_and_exposes_no_write_back_fields():
    case = _case()
    history_before = case["selection_history"]
    states_before = case["persisted_states"]
    snapshot = _derive_window(case)

    assert case["selection_history"] == history_before
    assert case["persisted_states"] == states_before
    forbidden = {
        "permission",
        "permissions",
        "mastery",
        "readiness",
        "professional_authority",
        "human_worth",
        "write_back",
        "state_update",
        "current_selection_request",
    }
    for artifact in (snapshot, snapshot.window, snapshot.window.frontier):
        assert forbidden.isdisjoint(set(getattr(artifact, "__dataclass_fields__", {})))


def test_integration_source_has_no_pilot_or_authority_fabrication_shortcuts():
    source = Path(__file__).read_text()
    forbidden_fragments = (
        "capability_lab." + "pilots",
        "object." + "__new__",
        "object." + "__setattr__",
        "monkey" + "patch",
    )
    assert all(fragment not in source for fragment in forbidden_fragments)
