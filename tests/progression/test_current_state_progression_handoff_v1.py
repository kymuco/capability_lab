from dataclasses import fields
from datetime import timedelta

import pytest

from capability_lab.progression import (
    CurrentStateGovernedProgressionFrontier,
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
    current_state_governed_progression_frontier_sha256_v1,
    derive_progression_frontier_from_current_state_v1,
    validate_current_state_governed_progression_frontier_v1,
)
from capability_lab.semantics import RelationKind
from capability_lab.state import (
    CurrentStateSelectionAction,
    CurrentStateSelectionMechanismKind,
    CurrentStateSelectionPolicyRef,
    CurrentStateSelectorRef,
    PersonalCapabilityCurrentStateSelectionAuthorityBasis,
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
    select_current_personal_capability_state_v1,
)

from test_progression_authority_adversarial_v1 import _supported_basic_state


ACCEPTANCE_POLICY = StateAcceptancePolicyRef.parse("test:pr11_9_acceptance@1")
ACCEPTER = StateAccepterRef(
    StateAcceptanceMechanismKind.HUMAN,
    "test:pr11_9_state_acceptor",
)
SELECTION_POLICY = CurrentStateSelectionPolicyRef.parse("test:pr11_9_current@1")
SELECTOR = CurrentStateSelectorRef(
    CurrentStateSelectionMechanismKind.HUMAN,
    "test:pr11_9_current_selector",
)
REQUESTER = ProgressionRequesterRef(
    ProgressionMechanismKind.HUMAN,
    "test:pr11_9_progression_requester",
)


def _current_basic_case():
    catalog, frames, records, state, basic = _supported_basic_state()
    empty_states = PersonalCapabilityStateSet(state.subject_ref)
    state_snapshot = PersonalCapabilityStateSet(state.subject_ref, (state,))
    acceptance = accept_persisted_personal_capability_state_v1(
        predecessor=empty_states,
        successor=state_snapshot,
        request=PersonalCapabilityStateAcceptanceRequest(
            state_id=state.state_id,
            acceptance_policy_ref=ACCEPTANCE_POLICY,
            accepter_ref=ACCEPTER,
            accepted_at=state.derived_at + timedelta(minutes=1),
            rationale="Explicit PR11.9 test acceptance of exact persisted state.",
        ),
    )
    admission = PersonalCapabilityStateAcceptanceAdmission(
        acceptance=acceptance,
        persistence_predecessor=empty_states,
        persistence_successor=state_snapshot,
    )
    empty_acceptances = PersonalCapabilityStateAcceptanceSet(state.subject_ref)
    accepted = PersonalCapabilityStateAcceptanceSet(
        state.subject_ref,
        (acceptance,),
    )
    selected_at = state.derived_at + timedelta(minutes=2)
    history = select_current_personal_capability_state_v1(
        state_snapshot=state_snapshot,
        acceptance_predecessor=empty_acceptances,
        acceptance_successor=accepted,
        acceptance_admissions=(admission,),
        selection_history=PersonalCapabilityCurrentStateSelectionHistory(
            state.subject_ref
        ),
        request=PersonalCapabilityCurrentStateSelectionRequest(
            concept_ref=state.concept_ref,
            frame_ref=state.frame_ref,
            action=CurrentStateSelectionAction.SELECT,
            selected_state_id=state.state_id,
            selection_policy_ref=SELECTION_POLICY,
            selector_ref=SELECTOR,
            selected_at=selected_at,
            rationale="Explicitly select the exact accepted state as current.",
        ),
    )
    basis = PersonalCapabilityCurrentStateSelectionAuthorityBasis(
        selection=history.selections[0],
        state_snapshot=state_snapshot,
        acceptance_predecessor=empty_acceptances,
        acceptance_successor=accepted,
        acceptance_admissions=(admission,),
    )
    return {
        "catalog": catalog,
        "frames": frames,
        "records": records,
        "state": state,
        "basic": basic,
        "state_snapshot": state_snapshot,
        "empty_acceptances": empty_acceptances,
        "accepted": accepted,
        "history": history,
        "bases": (basis,),
        "selected_at": selected_at,
    }


def _clear(case):
    state = case["state"]
    cleared_at = case["selected_at"] + timedelta(minutes=1)
    history = select_current_personal_capability_state_v1(
        state_snapshot=case["state_snapshot"],
        acceptance_predecessor=case["accepted"],
        acceptance_successor=case["accepted"],
        selection_history=case["history"],
        request=PersonalCapabilityCurrentStateSelectionRequest(
            concept_ref=state.concept_ref,
            frame_ref=state.frame_ref,
            action=CurrentStateSelectionAction.CLEAR,
            selected_state_id=None,
            selection_policy_ref=SELECTION_POLICY,
            selector_ref=SELECTOR,
            selected_at=cleared_at,
            rationale="Explicitly clear current state for PR11.9 regression.",
        ),
    )
    basis = PersonalCapabilityCurrentStateSelectionAuthorityBasis(
        selection=history.selections[-1],
        state_snapshot=case["state_snapshot"],
        acceptance_predecessor=case["accepted"],
        acceptance_successor=case["accepted"],
        acceptance_admissions=(),
    )
    return history, case["bases"] + (basis,), cleared_at


def _seed_request(case, *, generated_at=None, dimension_keys=("conceptual_knowledge",)):
    state = case["state"]
    return CurrentStateProgressionFrontierRequest(
        frontier_id=ProgressionFrontierId("frontier_pr11_9_current_seed"),
        as_of=state.as_of,
        generated_at=generated_at or case["selected_at"],
        requester_ref=REQUESTER,
        seeds=(
            CurrentStateProgressionSeed(
                concept_ref=state.concept_ref,
                frame_ref=state.frame_ref,
                dimension_keys=dimension_keys,
            ),
        ),
    )


def _requires_relation(case):
    target = next(
        concept
        for concept in case["catalog"].concepts
        if concept.capability_id.key == "low_voltage_power_distribution"
    )
    relation = next(
        item
        for item in case["catalog"].relations
        if item.kind is RelationKind.REQUIRES
        and item.source_id == target.capability_id
        and item.target_id == case["basic"].capability_id
    )
    return target, relation


def _prerequisite_request(case, *, generated_at, dimension_key):
    target, relation = _requires_relation(case)
    return CurrentStateProgressionFrontierRequest(
        frontier_id=ProgressionFrontierId(
            f"frontier_pr11_9_prerequisite_{dimension_key}"
        ),
        as_of=case["state"].as_of,
        generated_at=generated_at,
        requester_ref=REQUESTER,
        focuses=(
            ProgressionFocus(
                target.ref,
                "Explicit focus exposes the real REQUIRES relation for the check.",
            ),
        ),
        prerequisite_checks=(
            CurrentStatePrerequisiteCheck(
                target_ref=target.ref,
                prerequisite_ref=case["state"].concept_ref,
                relation_scope=relation.scope,
                frame_ref=case["state"].frame_ref,
                required_dimension_keys=(dimension_key,),
            ),
        ),
    )


_DEFAULT_BASES = object()


def _derive(case, request, *, history=None, bases=_DEFAULT_BASES):
    return derive_progression_frontier_from_current_state_v1(
        capability_catalog=case["catalog"],
        frame_catalog=case["frames"],
        records=case["records"],
        selection_history=history or case["history"],
        authority_bases=case["bases"] if bases is _DEFAULT_BASES else bases,
        request=request,
    )


def test_governed_seed_has_no_caller_state_id_and_uses_exact_current_select() -> None:
    case = _current_basic_case()
    assert "state_id" not in {item.name for item in fields(CurrentStateProgressionSeed)}
    assert "subject_ref" not in {
        item.name for item in fields(CurrentStateProgressionFrontierRequest)
    }

    governed = _derive(case, _seed_request(case))
    binding = governed.authority_bindings[0]
    assert binding.status is CurrentStateProgressionAuthorityStatus.SELECT
    assert binding.selected_state_id == case["state"].state_id
    assert governed.frontier.seed_bindings[0].state_id == case["state"].state_id
    assert any(
        candidate.concept_ref.capability_id.key == "low_voltage_power_distribution"
        for candidate in governed.frontier.candidates
    )
    validate_current_state_governed_progression_frontier_v1(
        capability_catalog=case["catalog"],
        frame_catalog=case["frames"],
        records=case["records"],
        selection_history=case["history"],
        authority_bases=case["bases"],
        governed_frontier=governed,
    )
    digest = current_state_governed_progression_frontier_sha256_v1(governed)
    assert len(digest) == 64
    assert digest == current_state_governed_progression_frontier_sha256_v1(governed)


def test_governed_seed_rejects_absent_or_cleared_current_scope() -> None:
    case = _current_basic_case()
    request = _seed_request(case)

    with pytest.raises(ProgressionAuthorityHandoffError, match="scope resolved as absent"):
        _derive(
            case,
            request,
            history=PersonalCapabilityCurrentStateSelectionHistory(
                case["state"].subject_ref
            ),
            bases=(),
        )

    cleared, bases, cleared_at = _clear(case)
    cleared_request = _seed_request(case, generated_at=cleared_at)
    with pytest.raises(ProgressionAuthorityHandoffError, match="scope resolved as clear"):
        _derive(case, cleared_request, history=cleared, bases=bases)


def test_current_prerequisite_supported_dimension_uses_authority_selected_state() -> None:
    case = _current_basic_case()
    request = _prerequisite_request(
        case,
        generated_at=case["selected_at"],
        dimension_key="conceptual_knowledge",
    )
    governed = _derive(case, request)
    assert governed.frontier.prerequisite_bindings[0].state_id == case["state"].state_id
    assert governed.frontier.prerequisite_gaps == ()


def test_current_prerequisite_unknown_dimension_remains_unknown_gap_not_readiness() -> None:
    case = _current_basic_case()
    request = _prerequisite_request(
        case,
        generated_at=case["selected_at"],
        dimension_key="calculation",
    )
    governed = _derive(case, request)
    assert len(governed.frontier.prerequisite_gaps) == 1
    gap = governed.frontier.prerequisite_gaps[0]
    assert gap.state_id == case["state"].state_id
    assert gap.dimension_gaps[0].kind is PrerequisiteDimensionGapKind.UNKNOWN
    assert not hasattr(governed, "ready")
    assert not hasattr(governed, "permitted")


def test_cleared_prerequisite_becomes_governed_no_selected_state_gap() -> None:
    case = _current_basic_case()
    cleared, bases, cleared_at = _clear(case)
    request = _prerequisite_request(
        case,
        generated_at=cleared_at,
        dimension_key="conceptual_knowledge",
    )
    governed = _derive(case, request, history=cleared, bases=bases)
    assert governed.authority_bindings[0].status is CurrentStateProgressionAuthorityStatus.CLEAR
    assert governed.frontier.prerequisite_bindings[0].state_id is None
    assert (
        governed.frontier.prerequisite_gaps[0].dimension_gaps[0].kind
        is PrerequisiteDimensionGapKind.NO_SELECTED_STATE
    )


def test_future_selection_cannot_authorize_earlier_generated_frontier() -> None:
    case = _current_basic_case()
    generated_at = case["selected_at"] - timedelta(seconds=1)
    request = _seed_request(case, generated_at=generated_at)
    with pytest.raises(
        ProgressionAuthorityHandoffError,
        match="governance act after progression generated_at",
    ):
        _derive(case, request)