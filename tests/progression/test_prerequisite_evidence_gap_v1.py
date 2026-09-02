from datetime import datetime, timezone

from capability_lab.domains import (
    build_civilization_bootstrap_frame_catalog_v1,
    build_civilization_bootstrap_seed_catalog_v0,
)
from capability_lab.epistemics import CapabilitySubjectRef, EpistemicRecordSet
from capability_lab.progression import (
    PrerequisiteCheckBinding,
    PrerequisiteDimensionGapKind,
    ProgressionFocus,
    ProgressionFrontierId,
    ProgressionFrontierRequest,
    ProgressionMechanismKind,
    ProgressionRequesterRef,
    derive_progression_frontier_v1,
)
from capability_lab.semantics import RelationKind
from capability_lab.state import PersonalCapabilityStateSet


T0 = datetime(2026, 8, 15, 19, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("subject_pr8_gap_distinction")


def _concept(catalog, key):
    return next(item for item in catalog.concepts if item.capability_id.key == key)


def _derive(*, prerequisite_bindings=()):
    catalog = build_civilization_bootstrap_seed_catalog_v0()
    frame_catalog = build_civilization_bootstrap_frame_catalog_v1()
    target = _concept(catalog, "low_voltage_power_distribution")
    request = ProgressionFrontierRequest(
        ProgressionFrontierId(
            "frontier_pr8_unassessed"
            if not prerequisite_bindings
            else "frontier_pr8_no_selected_state"
        ),
        SUBJECT,
        T0,
        T0,
        ProgressionRequesterRef(ProgressionMechanismKind.HUMAN, "test:pr8_subject"),
        focuses=(
            ProgressionFocus(
                target.ref,
                "Explicitly inspect the target without inferring a goal or recommendation.",
            ),
        ),
        prerequisite_bindings=prerequisite_bindings,
    )
    return catalog, frame_catalog, derive_progression_frontier_v1(
        capability_catalog=catalog,
        frame_catalog=frame_catalog,
        records=EpistemicRecordSet(),
        state_set=PersonalCapabilityStateSet(SUBJECT, ()),
        request=request,
    )


def test_requires_without_binding_is_unassessed_not_a_gap() -> None:
    catalog, _, frontier = _derive()
    target = _concept(catalog, "low_voltage_power_distribution")
    candidate = next(item for item in frontier.candidates if item.concept_ref == target.ref)

    assert candidate.assessed_prerequisites == ()
    assert len(candidate.unassessed_prerequisites) == 1
    assert candidate.unassessed_prerequisites[0].kind is RelationKind.REQUIRES
    assert frontier.prerequisite_gaps == ()


def test_explicit_binding_without_state_produces_no_selected_state_gap() -> None:
    catalog = build_civilization_bootstrap_seed_catalog_v0()
    frame_catalog = build_civilization_bootstrap_frame_catalog_v1()
    target = _concept(catalog, "low_voltage_power_distribution")
    prerequisite = _concept(catalog, "basic_electricity")
    relation = next(
        item
        for item in catalog.relations
        if item.kind is RelationKind.REQUIRES
        and item.source_id == target.capability_id
        and item.target_id == prerequisite.capability_id
    )
    binding = PrerequisiteCheckBinding(
        target.ref,
        prerequisite.ref,
        relation.scope,
        frame_catalog.frames[0].ref,
        ("conceptual_knowledge", "calculation"),
        None,
    )
    _, _, frontier = _derive(prerequisite_bindings=(binding,))
    candidate = next(item for item in frontier.candidates if item.concept_ref == target.ref)

    assert len(candidate.assessed_prerequisites) == 1
    assert candidate.unassessed_prerequisites == ()
    assert len(frontier.prerequisite_gaps) == 1
    gap = frontier.prerequisite_gaps[0]
    assert gap.state_id is None
    assert {item.dimension_key for item in gap.dimension_gaps} == {
        "conceptual_knowledge",
        "calculation",
    }
    assert all(
        item.kind is PrerequisiteDimensionGapKind.NO_SELECTED_STATE
        for item in gap.dimension_gaps
    )
