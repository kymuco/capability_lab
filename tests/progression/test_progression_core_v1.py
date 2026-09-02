from datetime import datetime, timezone

import pytest

from capability_lab.domains import build_civilization_bootstrap_seed_catalog_v0
from capability_lab.epistemics import CapabilitySubjectRef
from capability_lab.progression import (
    ExplorationInput,
    InvalidProgressionFrontier,
    InvalidProgressionRequest,
    PrerequisiteDimensionGap,
    PrerequisiteDimensionGapKind,
    PrerequisiteEvidenceGap,
    ProgressionFocus,
    ProgressionFrontierId,
    ProgressionFrontierRequest,
    ProgressionMechanismKind,
    ProgressionRelationWitness,
    ProgressionRequesterRef,
)
from capability_lab.semantics import RelationKind, RelationStrength
from capability_lab.state import CompetenceFrameRef, DimensionConflictStatus


T0 = datetime(2026, 8, 15, 16, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("subject_pr8_core")


def _concept(key):
    catalog = build_civilization_bootstrap_seed_catalog_v0()
    return next(item for item in catalog.concepts if item.capability_id.key == key)


def test_progression_request_requires_explicit_seed_focus_or_exploration() -> None:
    with pytest.raises(InvalidProgressionRequest):
        ProgressionFrontierRequest(
            ProgressionFrontierId("frontier_empty"),
            SUBJECT,
            T0,
            T0,
            ProgressionRequesterRef(ProgressionMechanismKind.HUMAN, "test:requester"),
        )


def test_focus_and_exploration_are_request_local_not_goal_or_rank_objects() -> None:
    focus = ProgressionFocus(_concept("basic_circuits").ref, "Inspect this direction in this projection.")
    exploration = ExplorationInput(_concept("potable_water_treatment").ref, "Keep this unrelated direction visible.")
    request = ProgressionFrontierRequest(
        ProgressionFrontierId("frontier_focus_exploration"),
        SUBJECT,
        T0,
        T0,
        ProgressionRequesterRef(ProgressionMechanismKind.MODEL, "test:model_requester"),
        focuses=(focus,),
        exploration_inputs=(exploration,),
    )
    assert request.focuses == (focus,)
    assert request.exploration_inputs == (exploration,)
    for forbidden in ("goal", "interest", "priority", "rank", "score", "difficulty", "readiness"):
        assert not hasattr(focus, forbidden)
        assert not hasattr(exploration, forbidden)
        assert not hasattr(request, forbidden)


def test_prerequisite_gap_cannot_be_constructed_from_supported_by() -> None:
    target = _concept("microcontroller_sensor_systems")
    prerequisite = _concept("embedded_programming")
    relation = ProgressionRelationWitness(
        target.ref,
        prerequisite.ref,
        RelationKind.SUPPORTED_BY,
        strength=RelationStrength.STRONG,
    )
    with pytest.raises(InvalidProgressionFrontier):
        PrerequisiteEvidenceGap(
            target.ref,
            prerequisite.ref,
            relation,
            CompetenceFrameRef.parse("civilization_bootstrap:technical_competence@1"),
            None,
            (PrerequisiteDimensionGap("execution", PrerequisiteDimensionGapKind.NO_SELECTED_STATE),),
        )


def test_state_backed_gap_preserves_conflict_axis_without_turning_it_into_ranking() -> None:
    gap = PrerequisiteDimensionGap(
        "execution",
        PrerequisiteDimensionGapKind.INSUFFICIENT,
        DimensionConflictStatus.UNRESOLVED,
    )
    assert gap.conflict_status is DimensionConflictStatus.UNRESOLVED
    assert not hasattr(gap, "severity")
    assert not hasattr(gap, "priority")
