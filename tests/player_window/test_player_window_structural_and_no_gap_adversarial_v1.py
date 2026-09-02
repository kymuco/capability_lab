from dataclasses import replace
from datetime import datetime, timezone

import pytest

from capability_lab.domains import (
    build_civilization_bootstrap_frame_catalog_v1,
    build_civilization_bootstrap_seed_catalog_v0,
)
from capability_lab.epistemics import CapabilitySubjectRef, EpistemicRecordSet
from capability_lab.history import (
    AchievementFamilyCatalog,
    PersonalHistoryRecordSet,
    PersonalLegendSet,
)
from capability_lab.player_window import (
    InvalidPlayerWindow,
    PlayerWindowId,
    PlayerWindowMechanismKind,
    PlayerWindowRequest,
    PlayerWindowRequesterRef,
    PlayerWindowViewerRef,
    derive_player_window_v1,
    render_player_window_html_v1,
    validate_player_window_v1,
)
from capability_lab.player_window.demo import (
    build_civilization_bootstrap_player_window_demo_v1,
)
from capability_lab.progression import (
    ProgressionFocus,
    ProgressionFrontierId,
    ProgressionFrontierRequest,
    ProgressionFrontierSet,
    ProgressionMechanismKind,
    ProgressionRequesterRef,
    derive_progression_frontier_v1,
)
from capability_lab.state import PersonalCapabilityStateSet


T0 = datetime(2026, 8, 16, 12, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("subject_pr9_no_gap")


def test_structural_window_requires_visible_entries_to_match_selected_ids_exactly() -> None:
    window = build_civilization_bootstrap_player_window_demo_v1()

    with pytest.raises(InvalidPlayerWindow):
        replace(window, capabilities=())
    with pytest.raises(InvalidPlayerWindow):
        replace(window, achievements=())
    with pytest.raises(InvalidPlayerWindow):
        replace(window, milestones=())
    with pytest.raises(InvalidPlayerWindow):
        replace(window, legend=None)
    with pytest.raises(InvalidPlayerWindow):
        replace(window, frontier=None)


def test_frontier_without_evidence_gaps_never_becomes_ready_or_cleared_status() -> None:
    catalog = build_civilization_bootstrap_seed_catalog_v0()
    frame_catalog = build_civilization_bootstrap_frame_catalog_v1()
    focus = next(
        item for item in catalog.concepts if item.capability_id.key == "technical_inquiry"
    )
    records = EpistemicRecordSet()
    state_set = PersonalCapabilityStateSet(SUBJECT)
    frontier = derive_progression_frontier_v1(
        capability_catalog=catalog,
        frame_catalog=frame_catalog,
        records=records,
        state_set=state_set,
        request=ProgressionFrontierRequest(
            ProgressionFrontierId("frontier_pr9_no_gap"),
            SUBJECT,
            T0,
            T0,
            ProgressionRequesterRef(
                ProgressionMechanismKind.HUMAN,
                "test:no_gap_requester",
            ),
            focuses=(
                ProgressionFocus(
                    focus.ref,
                    "Explicit focus used only to test no-gap presentation semantics.",
                ),
            ),
        ),
    )
    assert not frontier.prerequisite_gaps
    frontier_set = ProgressionFrontierSet(SUBJECT, (frontier,))
    family_catalog = AchievementFamilyCatalog()
    history_set = PersonalHistoryRecordSet(SUBJECT)
    legend_set = PersonalLegendSet(SUBJECT)
    window = derive_player_window_v1(
        capability_catalog=catalog,
        competence_frame_catalog=frame_catalog,
        epistemic_records=records,
        state_set=state_set,
        achievement_family_catalog=family_catalog,
        history_set=history_set,
        legend_set=legend_set,
        frontier_set=frontier_set,
        request=PlayerWindowRequest(
            PlayerWindowId("window_pr9_no_gap"),
            SUBJECT,
            T0,
            T0,
            PlayerWindowRequesterRef(
                PlayerWindowMechanismKind.HUMAN,
                "test:no_gap_requester",
            ),
            PlayerWindowViewerRef(
                PlayerWindowMechanismKind.HUMAN,
                "test:no_gap_viewer",
            ),
            selected_frontier_id=frontier.frontier_id,
        ),
    )
    validate_player_window_v1(
        capability_catalog=catalog,
        competence_frame_catalog=frame_catalog,
        epistemic_records=records,
        state_set=state_set,
        achievement_family_catalog=family_catalog,
        history_set=history_set,
        legend_set=legend_set,
        frontier_set=frontier_set,
        window=window,
    )
    html = render_player_window_html_v1(window)

    assert "Prerequisite evidence gap" not in html
    assert "Ready" not in html
    assert "ready for" not in html.lower()
    assert "cleared" not in html.lower()
    assert "all prerequisites satisfied" not in html.lower()
