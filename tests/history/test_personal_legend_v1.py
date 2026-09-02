from datetime import datetime, timedelta, timezone

import pytest

import capability_lab
from capability_lab.epistemics import CapabilitySubjectRef
from capability_lab.history import (
    AchievementBasisKind,
    AchievementBasisRef,
    AchievementFamily,
    AchievementFamilyId,
    AchievementInstance,
    AchievementInstanceId,
    AchievementQualificationPolicyRef,
    AchievementQualifierRef,
    HistoryMechanismKind,
    InvalidLegendSet,
    LegendGeneratorRef,
    LegendProjectionPolicyRef,
    LegendSourceKind,
    LegendSourceRef,
    MilestoneRecorderRef,
    MilestoneRecordingPolicyRef,
    PersonalHistoryRecordSet,
    PersonalLegend,
    PersonalLegendEntry,
    PersonalLegendId,
    PersonalLegendSet,
    PersonalMilestoneEvent,
    PersonalMilestoneEventId,
)


T0 = datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("subject_pr7_legend")
FAMILY = AchievementFamily(
    AchievementFamilyId("civilization_bootstrap", "bounded_system_build"),
    "Bounded System Build",
    "Completed a bounded end-to-end technical system build.",
)
ACHIEVEMENT = AchievementInstance(
    AchievementInstanceId("achievement_pr7_legend"),
    SUBJECT,
    FAMILY.ref,
    T0,
    T0 + timedelta(minutes=5),
    AchievementQualificationPolicyRef.parse("core:achievement_qualification@1"),
    AchievementQualifierRef(HistoryMechanismKind.HUMAN, "test:qualifier"),
    (AchievementBasisRef(AchievementBasisKind.EXTERNAL_ARTIFACT, "artifact:pr7_legend"),),
    "Bounded technical build context.",
)
MILESTONE = PersonalMilestoneEvent(
    PersonalMilestoneEventId("milestone_pr7_legend"),
    SUBJECT,
    "First end-to-end system that felt complete",
    "A personally meaningful transition associated with the completed bounded build.",
    "The event marked a change in how complete technical systems were approached.",
    T0 + timedelta(hours=1),
    T0 + timedelta(hours=2),
    MilestoneRecorderRef(HistoryMechanismKind.HUMAN, "test:recorder"),
    MilestoneRecordingPolicyRef.parse("core:personal_milestone_recording@1"),
)
HISTORY = PersonalHistoryRecordSet(SUBJECT, (ACHIEVEMENT,), (MILESTONE,))


def _legend(legend_id: str, title: str, entries) -> PersonalLegend:
    return PersonalLegend(
        PersonalLegendId(legend_id),
        SUBJECT,
        T0 + timedelta(days=1),
        T0 + timedelta(days=2),
        LegendProjectionPolicyRef.parse("core:personal_legend_projection@1"),
        LegendGeneratorRef(HistoryMechanismKind.MODEL, "test:model_legend"),
        title,
        "A derived narrative over selected history records, not a canonical self-description.",
        tuple(entries),
    )


def test_legend_uses_history_sources_only_and_preserves_authored_entry_order() -> None:
    first = PersonalLegendEntry(
        (LegendSourceRef(LegendSourceKind.PERSONAL_MILESTONE_EVENT, str(MILESTONE.milestone_id)),),
        "Meaningful transition",
        "The milestone is interpreted as a transition in the development history.",
    )
    second = PersonalLegendEntry(
        (LegendSourceRef(LegendSourceKind.ACHIEVEMENT_INSTANCE, str(ACHIEVEMENT.achievement_id)),),
        "Concrete accomplishment",
        "The underlying achievement remains an independently inspectable historical record.",
    )
    legend = _legend("legend_pr7_order", "A builder narrative", (first, second))
    legend_set = PersonalLegendSet(SUBJECT, (legend,))
    legend_set.validate_against_history(HISTORY)

    assert legend.entries == (first, second)


def test_multiple_alternative_legends_can_coexist_without_canonical_status() -> None:
    achievement_entry = PersonalLegendEntry(
        (LegendSourceRef(LegendSourceKind.ACHIEVEMENT_INSTANCE, str(ACHIEVEMENT.achievement_id)),),
        "Build",
        "One interpretation emphasizes the concrete build.",
    )
    milestone_entry = PersonalLegendEntry(
        (LegendSourceRef(LegendSourceKind.PERSONAL_MILESTONE_EVENT, str(MILESTONE.milestone_id)),),
        "Transition",
        "Another interpretation emphasizes the personally meaningful transition.",
    )
    legends = PersonalLegendSet(
        SUBJECT,
        (
            _legend("legend_pr7_builder", "Builder", (achievement_entry,)),
            _legend("legend_pr7_transition", "Transitions", (milestone_entry,)),
        ),
    )
    legends.validate_against_history(HISTORY)

    assert len(legends.legends) == 2
    assert not hasattr(legends, "canonical_legend")
    assert not hasattr(legends, "current_legend")


def test_legend_rejects_unknown_or_future_history_sources() -> None:
    unknown = _legend(
        "legend_pr7_unknown",
        "Unknown source",
        (
            PersonalLegendEntry(
                (LegendSourceRef(LegendSourceKind.ACHIEVEMENT_INSTANCE, "missing_achievement"),),
                "Unknown",
                "Must fail exact history validation.",
            ),
        ),
    )
    with pytest.raises(InvalidLegendSet):
        PersonalLegendSet(SUBJECT, (unknown,)).validate_against_history(HISTORY)

    early = PersonalLegend(
        PersonalLegendId("legend_pr7_early"),
        SUBJECT,
        T0 - timedelta(seconds=1),
        T0 + timedelta(days=2),
        LegendProjectionPolicyRef.parse("core:personal_legend_projection@1"),
        LegendGeneratorRef(HistoryMechanismKind.MODEL, "test:model_legend"),
        "Premature history",
        "This projection is earlier than its source event.",
        (
            PersonalLegendEntry(
                (LegendSourceRef(LegendSourceKind.ACHIEVEMENT_INSTANCE, str(ACHIEVEMENT.achievement_id)),),
                "Future source",
                "Must fail the as_of boundary.",
            ),
        ),
    )
    with pytest.raises(InvalidLegendSet):
        PersonalLegendSet(SUBJECT, (early,)).validate_against_history(HISTORY)


def test_public_api_has_no_history_to_score_or_state_shortcuts() -> None:
    forbidden = {
        "unlock_achievement",
        "auto_award",
        "award_if_state_above",
        "achievement_points",
        "achievement_score",
        "rarity_score",
        "leaderboard",
        "human_level",
        "auto_milestone",
        "legend_to_claim",
        "legend_to_state",
        "legend_to_evidence",
    }
    assert forbidden.isdisjoint(set(capability_lab.__all__))
    assert all(not hasattr(capability_lab, name) for name in forbidden)
