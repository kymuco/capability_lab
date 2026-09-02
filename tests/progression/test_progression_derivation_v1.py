from datetime import datetime, timedelta, timezone

import pytest

from capability_lab.domains import (
    build_civilization_bootstrap_frame_catalog_v1,
    build_civilization_bootstrap_seed_catalog_v0,
)
from capability_lab.epistemics import CapabilitySubjectRef, EpistemicRecordSet
from capability_lab.progression import (
    ExplorationInput,
    InvalidProgressionRequest,
    ProgressionFocus,
    ProgressionFrontierId,
    ProgressionFrontierRequest,
    ProgressionMechanismKind,
    ProgressionRequesterRef,
    derive_progression_frontier_v1,
)
from capability_lab.semantics import CapabilityConceptRef
from capability_lab.state import (
    CompetenceDimensionState,
    DimensionConflictStatus,
    DimensionStanding,
    PersonalCapabilityState,
    PersonalCapabilityStateId,
    PersonalCapabilityStateSet,
    StateDerivationPolicyRef,
    StateDeriverKind,
    StateDeriverRef,
)


T0 = datetime(2026, 8, 15, 18, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("subject_pr8_derivation")


def _concept(catalog, key):
    return next(item for item in catalog.concepts if item.capability_id.key == key)


def _focus_request(concept_ref, *, frontier_id="frontier_focus_only", exploration_inputs=()):
    return ProgressionFrontierRequest(
        ProgressionFrontierId(frontier_id),
        SUBJECT,
        T0,
        T0 + timedelta(minutes=1),
        ProgressionRequesterRef(ProgressionMechanismKind.MODEL, "test:pr8_focus_model"),
        focuses=(ProgressionFocus(concept_ref, "Explicit request-local focus."),),
        exploration_inputs=exploration_inputs,
    )


def test_explicit_focus_can_enter_frontier_without_graph_adjacency() -> None:
    catalog = build_civilization_bootstrap_seed_catalog_v0()
    focus = _concept(catalog, "potable_water_treatment")
    frontier = derive_progression_frontier_v1(
        capability_catalog=catalog,
        frame_catalog=build_civilization_bootstrap_frame_catalog_v1(),
        records=EpistemicRecordSet(),
        state_set=PersonalCapabilityStateSet(SUBJECT, ()),
        request=_focus_request(focus.ref),
    )
    candidate = next(item for item in frontier.candidates if item.concept_ref == focus.ref)
    assert candidate.explicit_focus is True
    assert candidate.adjacency_witnesses == ()
    for forbidden in ("score", "rank", "priority", "difficulty", "distance", "readiness"):
        assert not hasattr(candidate, forbidden)
        assert not hasattr(frontier, forbidden)


def test_unselected_state_is_inert_even_when_it_would_fail_current_catalog_revision_validation() -> None:
    catalog = build_civilization_bootstrap_seed_catalog_v0()
    frame_catalog = build_civilization_bootstrap_frame_catalog_v1()
    focus = _concept(catalog, "radio_communication")
    frame = frame_catalog.frames[0]
    stale_ref = CapabilityConceptRef(focus.capability_id, focus.revision + 99)
    unselected = PersonalCapabilityState(
        PersonalCapabilityStateId("state_pr8_unselected_stale"),
        SUBJECT,
        stale_ref,
        frame.ref,
        StateDerivationPolicyRef.parse("core:test_unselected_state@1"),
        StateDeriverRef(StateDeriverKind.RULE, "test:unselected_state"),
        T0 - timedelta(days=1),
        T0 - timedelta(days=1),
        (
            CompetenceDimensionState(
                frame.dimensions[0].key,
                DimensionStanding.UNKNOWN,
                rationale="No basis; this state is intentionally unselected.",
                conflict_status=DimensionConflictStatus.NONE,
            ),
        ),
        "A valid standalone stale state that must remain inert when unselected.",
    )
    request = _focus_request(focus.ref)
    without = derive_progression_frontier_v1(
        capability_catalog=catalog,
        frame_catalog=frame_catalog,
        records=EpistemicRecordSet(),
        state_set=PersonalCapabilityStateSet(SUBJECT, ()),
        request=request,
    )
    with_unselected = derive_progression_frontier_v1(
        capability_catalog=catalog,
        frame_catalog=frame_catalog,
        records=EpistemicRecordSet(),
        state_set=PersonalCapabilityStateSet(SUBJECT, (unselected,)),
        request=request,
    )
    assert with_unselected == without


def test_exploration_must_remain_distinct_from_focus_frontier() -> None:
    catalog = build_civilization_bootstrap_seed_catalog_v0()
    concept = _concept(catalog, "potable_water_treatment")
    request = _focus_request(
        concept.ref,
        frontier_id="frontier_exploration_collision",
        exploration_inputs=(ExplorationInput(concept.ref, "This intentionally collides with focus."),),
    )
    with pytest.raises(InvalidProgressionRequest):
        derive_progression_frontier_v1(
            capability_catalog=catalog,
            frame_catalog=build_civilization_bootstrap_frame_catalog_v1(),
            records=EpistemicRecordSet(),
            state_set=PersonalCapabilityStateSet(SUBJECT, ()),
            request=request,
        )
