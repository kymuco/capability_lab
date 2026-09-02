from datetime import timedelta

from capability_lab.history import (
    AchievementFamilyCatalog,
    PersonalHistoryRecordSet,
    PersonalLegendSet,
)
from capability_lab.player_window import (
    CurrentStatePlayerWindowRequest,
    PlayerWindowId,
    PlayerWindowMechanismKind,
    PlayerWindowRequesterRef,
    PlayerWindowViewerRef,
    derive_current_state_governed_player_window_v1,
    validate_current_state_governed_player_window_v1,
)
from capability_lab.progression import (
    CurrentStateProgressionAuthorityStatus,
    PrerequisiteDimensionGapKind,
)
from capability_lab.state import (
    CurrentStateSelectionAction,
    PersonalCapabilityCurrentStateSelectionAuthorityBasis,
    PersonalCapabilityCurrentStateSelectionRequest,
    select_current_personal_capability_state_v1,
)

from test_civilization_bootstrap_pilot_01_progression_authority_handoff_integration_v1 import (
    SELECTION_POLICY,
    SELECTOR,
    _prerequisite_request,
    _real_case,
)


WINDOW_REQUESTER = PlayerWindowRequesterRef(
    PlayerWindowMechanismKind.HUMAN,
    "civilization_bootstrap_pr11_11_window_requester",
)
VIEWER = PlayerWindowViewerRef(
    PlayerWindowMechanismKind.HUMAN,
    "civilization_bootstrap_pr11_11_viewer",
)


def _request(case, *, generated_at=None):
    generated_at = generated_at or case["selected_at"]
    progression = _prerequisite_request(case, generated_at=generated_at)
    return CurrentStatePlayerWindowRequest(
        window_id=PlayerWindowId("player_window_pilot_01_pr11_11"),
        generated_at=generated_at,
        requester_ref=WINDOW_REQUESTER,
        viewer_ref=VIEWER,
        progression_request=progression,
    )


def _derive(case, request, *, history=None, bases=None):
    empty_history = PersonalHistoryRecordSet(case["claim"].subject_ref)
    empty_legend = PersonalLegendSet(case["claim"].subject_ref)
    return derive_current_state_governed_player_window_v1(
        capability_catalog=case["catalog"],
        competence_frame_catalog=case["frames"],
        epistemic_records=case["records"],
        selection_history=history or case["history"],
        authority_bases=case["bases"] if bases is None else bases,
        achievement_family_catalog=AchievementFamilyCatalog(),
        history_set=empty_history,
        legend_set=empty_legend,
        request=request,
    )


def test_real_pr10_1_to_pr11_11_read_path_preserves_explicit_older_current_state(tmp_path) -> None:
    case = _real_case(tmp_path, suffix="product_anti_latest")
    state_a = case["state_a"]
    state_b = case["state_b"]

    snapshot = _derive(case, _request(case))

    assert state_a.derived_at < state_b.derived_at
    assert len(snapshot.current_state_entries) == 1
    entry = snapshot.current_state_entries[0]
    assert entry.action is CurrentStateSelectionAction.SELECT
    assert entry.selected_state_id == state_a.state_id
    assert snapshot.window.selected_state_ids == (state_a.state_id,)
    assert tuple(item.state_id for item in snapshot.window.capabilities) == (
        state_a.state_id,
    )
    assert state_b.state_id not in snapshot.window.selected_state_ids


def test_real_pr11_9_frontier_is_bound_into_same_current_state_snapshot_and_revalidates(tmp_path) -> None:
    case = _real_case(tmp_path, suffix="product_frontier")
    request = _request(case)
    snapshot = _derive(case, request)

    assert snapshot.window.frontier is not None
    assert snapshot.window.selected_frontier_id == request.progression_request.frontier_id
    assert snapshot.current_selection_history_sha256
    assert snapshot.current_state_portfolio_sha256
    assert snapshot.governed_frontier_sha256
    binding = snapshot.frontier_authority_bindings[0]
    assert binding.status is CurrentStateProgressionAuthorityStatus.SELECT
    assert binding.selected_state_id == case["state_a"].state_id

    empty_history = PersonalHistoryRecordSet(case["claim"].subject_ref)
    empty_legend = PersonalLegendSet(case["claim"].subject_ref)
    assert (
        validate_current_state_governed_player_window_v1(
            capability_catalog=case["catalog"],
            competence_frame_catalog=case["frames"],
            epistemic_records=case["records"],
            selection_history=case["history"],
            authority_bases=case["bases"],
            achievement_family_catalog=AchievementFamilyCatalog(),
            history_set=empty_history,
            legend_set=empty_legend,
            snapshot=snapshot,
        )
        is None
    )


def test_real_clear_survives_current_and_progression_authority_into_product_snapshot(tmp_path) -> None:
    case = _real_case(tmp_path, suffix="product_clear")
    cleared_at = case["selected_at"] + timedelta(minutes=1)
    cleared = select_current_personal_capability_state_v1(
        state_snapshot=case["state_history"],
        acceptance_predecessor=case["accepted"],
        acceptance_successor=case["accepted"],
        selection_history=case["history"],
        request=PersonalCapabilityCurrentStateSelectionRequest(
            concept_ref=case["state_a"].concept_ref,
            frame_ref=case["state_a"].frame_ref,
            action=CurrentStateSelectionAction.CLEAR,
            selected_state_id=None,
            selection_policy_ref=SELECTION_POLICY,
            selector_ref=SELECTOR,
            selected_at=cleared_at,
            rationale="Pilot explicitly clears current state before PR11.11 projection.",
        ),
    )
    clear_basis = PersonalCapabilityCurrentStateSelectionAuthorityBasis(
        selection=cleared.selections[-1],
        state_snapshot=case["state_history"],
        acceptance_predecessor=case["accepted"],
        acceptance_successor=case["accepted"],
        acceptance_admissions=(),
    )

    snapshot = _derive(
        case,
        _request(case, generated_at=cleared_at),
        history=cleared,
        bases=case["bases"] + (clear_basis,),
    )

    assert len(snapshot.current_state_entries) == 1
    assert snapshot.current_state_entries[0].action is CurrentStateSelectionAction.CLEAR
    assert snapshot.window.capabilities == ()
    assert snapshot.window.selected_state_ids == ()
    binding = snapshot.frontier_authority_bindings[0]
    assert binding.status is CurrentStateProgressionAuthorityStatus.CLEAR
    assert binding.selected_state_id is None
    assert snapshot.window.frontier is not None
    gap = snapshot.window.frontier.prerequisite_gaps[0]
    assert gap.state_id is None
    assert (
        gap.dimension_gaps[0].kind
        is PrerequisiteDimensionGapKind.NO_SELECTED_STATE
    )
