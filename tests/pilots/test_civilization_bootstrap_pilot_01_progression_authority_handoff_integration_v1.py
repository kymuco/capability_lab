from datetime import timedelta

import pytest

from capability_lab.domains import build_civilization_bootstrap_seed_catalog_v0
from capability_lab.progression import (
    CurrentStatePrerequisiteCheck,
    CurrentStateProgressionAuthorityStatus,
    CurrentStateProgressionFrontierRequest,
    CurrentStateProgressionSeed,
    PrerequisiteDimensionGapKind,
    ProgressionAuthorityHandoffError,
    ProgressionFocus,
    ProgressionFrontierId,
    ProgressionMechanismKind,
    ProgressionRequesterRef,
    derive_progression_frontier_from_current_state_v1,
)
from capability_lab.semantics import RelationKind
from capability_lab.state import (
    CompetenceFrameCatalog,
    CurrentStateSelectionAction,
    CurrentStateSelectionMechanismKind,
    CurrentStateSelectionPolicyRef,
    CurrentStateSelectorRef,
    DimensionStanding,
    PersonalCapabilityCurrentStateSelectionAuthorityBasis,
    PersonalCapabilityCurrentStateSelectionHistory,
    PersonalCapabilityCurrentStateSelectionRequest,
    PersonalCapabilityStateAcceptanceAdmission,
    PersonalCapabilityStateAcceptanceSet,
    PersonalCapabilityStateSet,
    select_current_personal_capability_state_v1,
    accept_persisted_personal_capability_state_v1,
)

from test_civilization_bootstrap_pilot_01_complete_portfolio_derivation_integration_v1 import (
    _frame,
    _reasoning,
)
from test_civilization_bootstrap_pilot_01_state_acceptance_integration_v1 import (
    _acceptance_request,
    _derive_correction,
    _derive_initial,
)


SELECTION_POLICY = CurrentStateSelectionPolicyRef.parse(
    "pilot:pr11_9_progression_current_state@1"
)
SELECTOR = CurrentStateSelectorRef(
    CurrentStateSelectionMechanismKind.HUMAN,
    "civilization_bootstrap_pr11_9_current_selector",
)
REQUESTER = ProgressionRequesterRef(
    ProgressionMechanismKind.HUMAN,
    "civilization_bootstrap_pr11_9_progression_requester",
)


def _real_case(tmp_path, *, suffix):
    snapshot, evaluation, claim, _, state_a = _derive_initial(
        tmp_path,
        f"state_pilot_01_pr11_9_{suffix}_a",
    )
    correction, epistemic_successor, _, state_b = _derive_correction(
        snapshot,
        evaluation,
        claim,
        suffix=f"pr11_9_{suffix}_b",
        state_id=f"state_pilot_01_pr11_9_{suffix}_b",
    )
    state_history_a = PersonalCapabilityStateSet(claim.subject_ref, (state_a,))
    state_history_ab = PersonalCapabilityStateSet(
        claim.subject_ref,
        (state_a, state_b),
    )

    acceptance_a = accept_persisted_personal_capability_state_v1(
        predecessor=state_history_a,
        successor=state_history_ab,
        request=_acceptance_request(
            state_a,
            accepted_at=state_b.derived_at + timedelta(minutes=1),
        ),
    )
    acceptance_b = accept_persisted_personal_capability_state_v1(
        predecessor=state_history_a,
        successor=state_history_ab,
        request=_acceptance_request(
            state_b,
            accepted_at=state_b.derived_at + timedelta(minutes=2),
        ),
    )
    admission_a = PersonalCapabilityStateAcceptanceAdmission(
        acceptance=acceptance_a,
        persistence_predecessor=state_history_a,
        persistence_successor=state_history_ab,
    )
    admission_b = PersonalCapabilityStateAcceptanceAdmission(
        acceptance=acceptance_b,
        persistence_predecessor=state_history_a,
        persistence_successor=state_history_ab,
    )
    empty_acceptances = PersonalCapabilityStateAcceptanceSet(claim.subject_ref)
    accepted_ab = PersonalCapabilityStateAcceptanceSet(
        claim.subject_ref,
        (acceptance_a, acceptance_b),
    )
    selected_at = state_b.derived_at + timedelta(minutes=3)
    selection_history = select_current_personal_capability_state_v1(
        state_snapshot=state_history_ab,
        acceptance_predecessor=empty_acceptances,
        acceptance_successor=accepted_ab,
        acceptance_admissions=(admission_a, admission_b),
        selection_history=PersonalCapabilityCurrentStateSelectionHistory(
            claim.subject_ref
        ),
        request=PersonalCapabilityCurrentStateSelectionRequest(
            concept_ref=state_a.concept_ref,
            frame_ref=state_a.frame_ref,
            action=CurrentStateSelectionAction.SELECT,
            selected_state_id=state_a.state_id,
            selection_policy_ref=SELECTION_POLICY,
            selector_ref=SELECTOR,
            selected_at=selected_at,
            rationale=(
                "Pilot deliberately keeps the older accepted state A current so PR11.9 "
                "proves anti-latest progression input admission."
            ),
        ),
    )
    select_basis = PersonalCapabilityCurrentStateSelectionAuthorityBasis(
        selection=selection_history.selections[0],
        state_snapshot=state_history_ab,
        acceptance_predecessor=empty_acceptances,
        acceptance_successor=accepted_ab,
        acceptance_admissions=(admission_a, admission_b),
    )

    catalog = build_civilization_bootstrap_seed_catalog_v0()
    target = next(
        concept
        for concept in catalog.concepts
        if concept.capability_id.key == "low_voltage_power_distribution"
    )
    relation = next(
        item
        for item in catalog.relations
        if item.kind is RelationKind.REQUIRES
        and item.source_id == target.capability_id
        and item.target_id == state_a.concept_ref.capability_id
    )
    frame = _frame()
    return {
        "catalog": catalog,
        "frames": CompetenceFrameCatalog((frame,)),
        "records": epistemic_successor,
        "claim": claim,
        "correction": correction,
        "state_a": state_a,
        "state_b": state_b,
        "state_history": state_history_ab,
        "accepted": accepted_ab,
        "history": selection_history,
        "bases": (select_basis,),
        "selected_at": selected_at,
        "target": target,
        "relation": relation,
    }


def _prerequisite_request(case, *, generated_at):
    return CurrentStateProgressionFrontierRequest(
        frontier_id=ProgressionFrontierId("frontier_pilot_01_pr11_9_prerequisite"),
        as_of=case["state_b"].as_of,
        generated_at=generated_at,
        requester_ref=REQUESTER,
        focuses=(
            ProgressionFocus(
                case["target"].ref,
                "Explicit Pilot focus for the real low-voltage REQUIRES relation.",
            ),
        ),
        prerequisite_checks=(
            CurrentStatePrerequisiteCheck(
                target_ref=case["target"].ref,
                prerequisite_ref=case["state_a"].concept_ref,
                relation_scope=case["relation"].scope,
                frame_ref=case["state_a"].frame_ref,
                required_dimension_keys=("reasoning",),
            ),
        ),
    )


def _derive(case, request, *, history=None, bases=None):
    return derive_progression_frontier_from_current_state_v1(
        capability_catalog=case["catalog"],
        frame_catalog=case["frames"],
        records=case["records"],
        selection_history=history or case["history"],
        authority_bases=case["bases"] if bases is None else bases,
        request=request,
    )


def test_real_pr11_2_to_pr11_9_path_uses_explicit_older_current_state_not_latest(tmp_path) -> None:
    case = _real_case(tmp_path, suffix="anti_latest")
    state_a = case["state_a"]
    state_b = case["state_b"]
    assert state_a.derived_at < state_b.derived_at
    assert _reasoning(state_a).standing is DimensionStanding.INSUFFICIENT

    governed = _derive(
        case,
        _prerequisite_request(case, generated_at=case["selected_at"]),
    )

    binding = governed.authority_bindings[0]
    assert binding.status is CurrentStateProgressionAuthorityStatus.SELECT
    assert binding.selected_state_id == state_a.state_id
    assert binding.selected_state_id != state_b.state_id
    assert governed.frontier.prerequisite_bindings[0].state_id == state_a.state_id
    assert len(governed.frontier.prerequisite_gaps) == 1
    dimension_gap = governed.frontier.prerequisite_gaps[0].dimension_gaps[0]
    assert dimension_gap.dimension_key == "reasoning"
    assert dimension_gap.kind is PrerequisiteDimensionGapKind.INSUFFICIENT


def test_real_current_insufficient_state_cannot_be_laundered_into_positive_seed(tmp_path) -> None:
    case = _real_case(tmp_path, suffix="insufficient_seed")
    request = CurrentStateProgressionFrontierRequest(
        frontier_id=ProgressionFrontierId("frontier_pilot_01_pr11_9_seed"),
        as_of=case["state_b"].as_of,
        generated_at=case["selected_at"],
        requester_ref=REQUESTER,
        seeds=(
            CurrentStateProgressionSeed(
                concept_ref=case["state_a"].concept_ref,
                frame_ref=case["state_a"].frame_ref,
                dimension_keys=("reasoning",),
            ),
        ),
    )
    with pytest.raises(
        ProgressionAuthorityHandoffError,
        match="frontier seed bindings may select only SUPPORTED dimensions",
    ):
        _derive(case, request)


def test_real_clear_turns_prerequisite_state_into_no_selected_state_gap(tmp_path) -> None:
    case = _real_case(tmp_path, suffix="clear")
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
            rationale="Pilot explicitly clears current-state progression input authority.",
        ),
    )
    clear_basis = PersonalCapabilityCurrentStateSelectionAuthorityBasis(
        selection=cleared.selections[-1],
        state_snapshot=case["state_history"],
        acceptance_predecessor=case["accepted"],
        acceptance_successor=case["accepted"],
        acceptance_admissions=(),
    )

    governed = _derive(
        case,
        _prerequisite_request(case, generated_at=cleared_at),
        history=cleared,
        bases=case["bases"] + (clear_basis,),
    )
    binding = governed.authority_bindings[0]
    assert binding.status is CurrentStateProgressionAuthorityStatus.CLEAR
    assert binding.selected_state_id is None
    assert governed.frontier.prerequisite_bindings[0].state_id is None
    dimension_gap = governed.frontier.prerequisite_gaps[0].dimension_gaps[0]
    assert dimension_gap.kind is PrerequisiteDimensionGapKind.NO_SELECTED_STATE
