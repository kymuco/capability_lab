"""Source-backed verification for deterministic PR9 Player Window projections."""

from __future__ import annotations

from capability_lab.epistemics import EpistemicRecordSet
from capability_lab.history import (
    AchievementFamilyCatalog,
    PersonalHistoryRecordSet,
    PersonalLegendSet,
)
from capability_lab.progression import ProgressionFrontierSet, validate_progression_frontier_v1
from capability_lab.semantics import CapabilityCatalog
from capability_lab.state import CompetenceFrameCatalog, PersonalCapabilityStateSet

from .core import InvalidPlayerWindow, PlayerWindow, PlayerWindowRequest
from .derivation import derive_player_window_v1


def validate_player_window_v1(
    *,
    capability_catalog: CapabilityCatalog,
    competence_frame_catalog: CompetenceFrameCatalog,
    epistemic_records: EpistemicRecordSet,
    state_set: PersonalCapabilityStateSet,
    achievement_family_catalog: AchievementFamilyCatalog,
    history_set: PersonalHistoryRecordSet,
    legend_set: PersonalLegendSet,
    frontier_set: ProgressionFrontierSet,
    window: PlayerWindow,
) -> None:
    """Verify exact PR9 re-derivation and selected upstream source governance.

    Structural deserialization proves only schema/object validity. This verifier first
    validates exactly the selected PR3 state records against their PR1/PR2/frame basis,
    validates exactly the selected PR7 history/Legend records against their family,
    epistemic, and history-source contracts, then validates any selected PR8 frontier
    by exact PR8 re-derivation, and finally re-derives the PR9 read model itself.
    Unselected state/history/Legend records remain inert.

    The verifier proves deterministic consistency with supplied snapshots; it does not
    authenticate those snapshots, viewer authority, publication permission, rendered
    artifact bytes, or source provenance.
    """
    if not isinstance(window, PlayerWindow):
        raise InvalidPlayerWindow("window must be PlayerWindow")
    try:
        selected_state_ids = set(window.selected_state_ids)
        selected_states = tuple(
            item for item in state_set.states if item.state_id in selected_state_ids
        )
        if len(selected_states) != len(selected_state_ids):
            raise InvalidPlayerWindow(
                "one or more selected states are absent from supplied state_set"
            )
        selected_state_set = PersonalCapabilityStateSet(
            window.subject_ref,
            selected_states,
        )
        selected_state_set.validate_against_epistemics(epistemic_records)
        selected_state_set.validate_against_capability_catalog(capability_catalog)
        selected_state_set.validate_against_frame_catalog(competence_frame_catalog)

        selected_achievement_ids = set(window.selected_achievement_ids)
        selected_milestone_ids = set(window.selected_milestone_ids)
        selected_achievements = tuple(
            item
            for item in history_set.achievement_instances
            if item.achievement_id in selected_achievement_ids
        )
        selected_milestones = tuple(
            item
            for item in history_set.milestone_events
            if item.milestone_id in selected_milestone_ids
        )
        if len(selected_achievements) != len(selected_achievement_ids):
            raise InvalidPlayerWindow(
                "one or more selected achievements are absent from supplied history_set"
            )
        if len(selected_milestones) != len(selected_milestone_ids):
            raise InvalidPlayerWindow(
                "one or more selected milestones are absent from supplied history_set"
            )
        selected_history_set = PersonalHistoryRecordSet(
            window.subject_ref,
            selected_achievements,
            selected_milestones,
        )
        selected_history_set.validate_against_family_catalog(achievement_family_catalog)
        selected_history_set.validate_against_epistemics(epistemic_records)

        selected_legends = ()
        if window.selected_legend_id is not None:
            selected_legends = tuple(
                item
                for item in legend_set.legends
                if item.legend_id == window.selected_legend_id
            )
            if len(selected_legends) != 1:
                raise InvalidPlayerWindow(
                    "selected Legend is absent from supplied legend_set"
                )
        selected_legend_set = PersonalLegendSet(
            window.subject_ref,
            selected_legends,
        )
        selected_legend_set.validate_against_history(selected_history_set)

        if window.selected_frontier_id is not None:
            frontier = next(
                (
                    item
                    for item in frontier_set.frontiers
                    if item.frontier_id == window.selected_frontier_id
                ),
                None,
            )
            if frontier is None:
                raise InvalidPlayerWindow(
                    "selected frontier is absent from supplied frontier_set"
                )
            validate_progression_frontier_v1(
                capability_catalog=capability_catalog,
                frame_catalog=competence_frame_catalog,
                records=epistemic_records,
                state_set=selected_state_set,
                frontier=frontier,
            )

        request = PlayerWindowRequest(
            window_id=window.window_id,
            subject_ref=window.subject_ref,
            as_of=window.as_of,
            generated_at=window.generated_at,
            requester_ref=window.requester_ref,
            viewer_ref=window.viewer_ref,
            selected_state_ids=window.selected_state_ids,
            selected_achievement_ids=window.selected_achievement_ids,
            selected_milestone_ids=window.selected_milestone_ids,
            selected_legend_id=window.selected_legend_id,
            selected_frontier_id=window.selected_frontier_id,
        )
        expected = derive_player_window_v1(
            capability_catalog=capability_catalog,
            competence_frame_catalog=competence_frame_catalog,
            epistemic_records=epistemic_records,
            state_set=selected_state_set,
            achievement_family_catalog=achievement_family_catalog,
            history_set=selected_history_set,
            legend_set=selected_legend_set,
            frontier_set=frontier_set,
            request=request,
        )
    except ValueError as exc:
        raise InvalidPlayerWindow(
            "player window effective inputs cannot be verified against supplied source snapshots"
        ) from exc
    if expected != window:
        raise InvalidPlayerWindow(
            "player window does not exactly match deterministic PR9 derivation from its "
            "stored explicit source selection and supplied source snapshots"
        )
