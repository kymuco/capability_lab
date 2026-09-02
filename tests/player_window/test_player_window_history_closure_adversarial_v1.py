from datetime import datetime, timedelta, timezone

import pytest

from capability_lab.domains import (
    build_civilization_bootstrap_frame_catalog_v1,
    build_civilization_bootstrap_seed_catalog_v0,
)
from capability_lab.epistemics import CapabilitySubjectRef, EpistemicRecordSet
from capability_lab.history import (
    AchievementBasisKind,
    AchievementBasisRef,
    AchievementFamily,
    AchievementFamilyCatalog,
    AchievementFamilyId,
    AchievementInstance,
    AchievementInstanceId,
    AchievementQualificationPolicyRef,
    AchievementQualifierRef,
    HistoryMechanismKind,
    MilestoneRecorderRef,
    MilestoneRecordingPolicyRef,
    MilestoneSourceKind,
    MilestoneSourceRef,
    PersonalHistoryRecordSet,
    PersonalLegendSet,
    PersonalMilestoneEvent,
    PersonalMilestoneEventId,
)
from capability_lab.player_window import (
    InvalidPlayerWindow,
    PlayerWindowId,
    PlayerWindowMechanismKind,
    PlayerWindowRequest,
    PlayerWindowRequesterRef,
    PlayerWindowViewerRef,
    derive_player_window_v1,
    validate_player_window_v1,
)
from capability_lab.progression import ProgressionFrontierSet
from capability_lab.state import PersonalCapabilityStateSet


T0 = datetime(2020, 1, 2, 12, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("subject_pr9_history_closure")


def _sources():
    family = AchievementFamily(
        AchievementFamilyId("test", "history_closure"),
        "History Closure Achievement",
        "A bounded family used to test visible milestone history closure.",
    )
    achievement = AchievementInstance(
        AchievementInstanceId("achievement_pr9_history_closure"),
        SUBJECT,
        family.ref,
        T0,
        T0 + timedelta(minutes=1),
        AchievementQualificationPolicyRef.parse("test:history_closure@1"),
        AchievementQualifierRef(HistoryMechanismKind.HUMAN, "test:qualifier"),
        (AchievementBasisRef(AchievementBasisKind.EXTERNAL_ARTIFACT, "artifact:history_closure"),),
        "Visible source achievement.",
    )
    milestone = PersonalMilestoneEvent(
        PersonalMilestoneEventId("milestone_pr9_history_closure"),
        SUBJECT,
        "Milestone sourced by the achievement",
        "A milestone whose explicit PR7 source is the selected achievement instance.",
        "Recorded only for source-closure testing.",
        T0 + timedelta(minutes=2),
        T0 + timedelta(minutes=3),
        MilestoneRecorderRef(HistoryMechanismKind.HUMAN, "test:recorder"),
        MilestoneRecordingPolicyRef.parse("test:history_closure@1"),
        (
            MilestoneSourceRef(
                MilestoneSourceKind.ACHIEVEMENT_INSTANCE,
                str(achievement.achievement_id),
            ),
        ),
    )
    return (
        AchievementFamilyCatalog((family,)),
        PersonalHistoryRecordSet(SUBJECT, (achievement,), (milestone,)),
        achievement,
        milestone,
    )


def _derive(history_set, family_catalog, achievement_ids, milestone_ids):
    return derive_player_window_v1(
        capability_catalog=build_civilization_bootstrap_seed_catalog_v0(),
        competence_frame_catalog=build_civilization_bootstrap_frame_catalog_v1(),
        epistemic_records=EpistemicRecordSet(),
        state_set=PersonalCapabilityStateSet(SUBJECT),
        achievement_family_catalog=family_catalog,
        history_set=history_set,
        legend_set=PersonalLegendSet(SUBJECT),
        frontier_set=ProgressionFrontierSet(SUBJECT),
        request=PlayerWindowRequest(
            PlayerWindowId("window_pr9_history_closure"),
            SUBJECT,
            T0 + timedelta(minutes=4),
            T0 + timedelta(minutes=5),
            PlayerWindowRequesterRef(PlayerWindowMechanismKind.HUMAN, "test:requester"),
            PlayerWindowViewerRef(PlayerWindowMechanismKind.HUMAN, "test:viewer"),
            selected_achievement_ids=achievement_ids,
            selected_milestone_ids=milestone_ids,
        ),
    )


def _verify(window, history_set, family_catalog):
    validate_player_window_v1(
        capability_catalog=build_civilization_bootstrap_seed_catalog_v0(),
        competence_frame_catalog=build_civilization_bootstrap_frame_catalog_v1(),
        epistemic_records=EpistemicRecordSet(),
        state_set=PersonalCapabilityStateSet(SUBJECT),
        achievement_family_catalog=family_catalog,
        history_set=history_set,
        legend_set=PersonalLegendSet(SUBJECT),
        frontier_set=ProgressionFrontierSet(SUBJECT),
        window=window,
    )


def test_verified_milestone_window_requires_visible_selected_achievement_source_closure() -> None:
    family_catalog, history_set, achievement, milestone = _sources()
    hidden_source_window = _derive(
        history_set,
        family_catalog,
        (),
        (milestone.milestone_id,),
    )

    with pytest.raises(InvalidPlayerWindow):
        _verify(hidden_source_window, history_set, family_catalog)

    closed_window = _derive(
        history_set,
        family_catalog,
        (achievement.achievement_id,),
        (milestone.milestone_id,),
    )
    _verify(closed_window, history_set, family_catalog)
