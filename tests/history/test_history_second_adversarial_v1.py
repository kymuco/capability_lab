from datetime import datetime, timedelta, timezone

import pytest

from capability_lab.epistemics import CapabilitySubjectRef, EpistemicRecordSet
from capability_lab.history import (
    AchievementBasisKind,
    AchievementBasisRef,
    AchievementCriterion,
    AchievementFamily,
    AchievementFamilyCatalog,
    AchievementFamilyId,
    AchievementInstance,
    AchievementInstanceId,
    AchievementQualificationPolicyRef,
    AchievementQualifierRef,
    HistoryMechanismKind,
    InvalidHistoryRecordSet,
    InvalidLegendSet,
    LegendGeneratorRef,
    LegendProjectionPolicyRef,
    LegendSourceKind,
    LegendSourceRef,
    MilestoneRecorderRef,
    MilestoneRecordingPolicyRef,
    MilestoneSourceKind,
    MilestoneSourceRef,
    PersonalHistoryRecordSet,
    PersonalLegend,
    PersonalLegendEntry,
    PersonalLegendId,
    PersonalLegendSet,
    PersonalMilestoneEvent,
    PersonalMilestoneEventId,
)


T0 = datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("subject_pr7_second_adversarial")
FAMILY_ID = AchievementFamilyId("civilization_bootstrap", "bounded_repeated_performance")
FAMILY = AchievementFamily(
    FAMILY_ID,
    "Bounded Repeated Performance",
    "Completed one bounded performance with an inspectable event-bearing basis.",
    qualification_criteria=(
        AchievementCriterion("observable_result", "The bounded performance produced an observable result."),
    ),
)
QUAL_POLICY = AchievementQualificationPolicyRef.parse(
    "civilization_bootstrap:bounded_achievement_qualification@1"
)


def _achievement(
    achievement_id: str,
    *,
    artifact_ref: str,
    achieved_at: datetime = T0,
    recorded_at: datetime | None = None,
    qualifier_kind: HistoryMechanismKind = HistoryMechanismKind.HUMAN,
) -> AchievementInstance:
    if recorded_at is None:
        recorded_at = achieved_at + timedelta(minutes=10)
    return AchievementInstance(
        achievement_id=AchievementInstanceId(achievement_id),
        subject_ref=SUBJECT,
        family_ref=FAMILY.ref,
        achieved_at=achieved_at,
        recorded_at=recorded_at,
        qualification_policy_ref=QUAL_POLICY,
        qualifier_ref=AchievementQualifierRef(
            qualifier_kind,
            "test:pr7_second_qualifier",
        ),
        basis_refs=(
            AchievementBasisRef(AchievementBasisKind.EXTERNAL_ARTIFACT, artifact_ref),
        ),
        context="Bounded repeated-performance adversarial context.",
    )


def _milestone(
    milestone_id: str,
    *,
    occurred_at: datetime,
    recorded_at: datetime,
    achievement_source: AchievementInstance | None = None,
) -> PersonalMilestoneEvent:
    sources = ()
    if achievement_source is not None:
        sources = (
            MilestoneSourceRef(
                MilestoneSourceKind.ACHIEVEMENT_INSTANCE,
                str(achievement_source.achievement_id),
            ),
        )
    return PersonalMilestoneEvent(
        milestone_id=PersonalMilestoneEventId(milestone_id),
        subject_ref=SUBJECT,
        title="Bounded milestone",
        description="A person-scoped event used to test PR7 backfill causality.",
        significance_note="Recorded as significant under the declared policy without implying authority.",
        occurred_at=occurred_at,
        recorded_at=recorded_at,
        recorder_ref=MilestoneRecorderRef(
            HistoryMechanismKind.HUMAN,
            "test:pr7_second_recorder",
        ),
        recording_policy_ref=MilestoneRecordingPolicyRef.parse(
            "core:personal_milestone_recording@1"
        ),
        source_refs=sources,
    )


def _legend(
    legend_id: str,
    *,
    entries: tuple[PersonalLegendEntry, ...],
    as_of: datetime,
    generated_at: datetime,
) -> PersonalLegend:
    return PersonalLegend(
        legend_id=PersonalLegendId(legend_id),
        subject_ref=SUBJECT,
        as_of=as_of,
        generated_at=generated_at,
        legend_policy_ref=LegendProjectionPolicyRef.parse(
            "core:personal_legend_projection@1"
        ),
        generator_ref=LegendGeneratorRef(
            HistoryMechanismKind.MODEL,
            "test:pr7_second_legend",
        ),
        title="Selective history projection",
        summary="A source-backed narrative projection used for adversarial validation.",
        entries=entries,
    )


def test_achievement_and_milestone_ids_may_not_collide_inside_one_history_snapshot() -> None:
    achievement = _achievement(
        "history_cross_type_collision",
        artifact_ref="artifact:cross_type_collision",
    )
    milestone = _milestone(
        "history_cross_type_collision",
        occurred_at=T0,
        recorded_at=T0 + timedelta(minutes=20),
    )

    with pytest.raises(InvalidHistoryRecordSet, match="must not collide"):
        PersonalHistoryRecordSet(SUBJECT, (achievement,), (milestone,))


def test_legend_id_may_not_collide_with_history_id_in_validated_personal_snapshot() -> None:
    achievement = _achievement(
        "history_legend_collision",
        artifact_ref="artifact:legend_collision",
    )
    history = PersonalHistoryRecordSet(SUBJECT, (achievement,), ())
    source = LegendSourceRef(
        LegendSourceKind.ACHIEVEMENT_INSTANCE,
        str(achievement.achievement_id),
    )
    legend = _legend(
        "history_legend_collision",
        entries=(
            PersonalLegendEntry((source,), "One source", "One interpretation of the cited history."),
        ),
        as_of=T0,
        generated_at=T0 + timedelta(minutes=30),
    )

    with pytest.raises(InvalidLegendSet, match="must not collide"):
        PersonalLegendSet(SUBJECT, (legend,)).validate_against_history(history)


def test_same_event_basis_cannot_become_two_instances_merely_by_changing_event_time() -> None:
    first = _achievement(
        "achievement_repeated_window_a",
        artifact_ref="artifact:one_record_covering_repeated_window",
        achieved_at=T0,
    )
    second = _achievement(
        "achievement_repeated_window_b",
        artifact_ref="artifact:one_record_covering_repeated_window",
        achieved_at=T0 + timedelta(hours=1),
    )

    with pytest.raises(InvalidHistoryRecordSet, match="replayed"):
        PersonalHistoryRecordSet(SUBJECT, (first, second), ())


def test_equal_event_timestamps_do_not_prove_event_identity_when_event_refs_are_distinct() -> None:
    first = _achievement(
        "achievement_same_clock_a",
        artifact_ref="artifact:distinct_performance_a",
        achieved_at=T0,
    )
    second = _achievement(
        "achievement_same_clock_b",
        artifact_ref="artifact:distinct_performance_b",
        achieved_at=T0,
    )

    history = PersonalHistoryRecordSet(SUBJECT, (first, second), ())
    assert len(history.achievement_instances) == 2


def test_milestone_cannot_cite_achievement_recorded_after_the_milestone_record() -> None:
    achievement = _achievement(
        "achievement_future_record_for_milestone",
        artifact_ref="artifact:future_record_for_milestone",
        achieved_at=T0,
        recorded_at=T0 + timedelta(days=3),
    )
    milestone = _milestone(
        "milestone_future_achievement_record",
        occurred_at=T0 + timedelta(days=1),
        recorded_at=T0 + timedelta(days=2),
        achievement_source=achievement,
    )
    history = PersonalHistoryRecordSet(SUBJECT, (achievement,), (milestone,))

    with pytest.raises(InvalidHistoryRecordSet, match="must exist by milestone recorded_at"):
        history.validate_against_epistemics(EpistemicRecordSet())


def test_milestone_historical_backfill_may_cite_achievement_that_existed_by_recording_time() -> None:
    achievement = _achievement(
        "achievement_honest_milestone_backfill",
        artifact_ref="artifact:honest_milestone_backfill",
        achieved_at=T0,
        recorded_at=T0 + timedelta(days=1),
    )
    milestone = _milestone(
        "milestone_honest_backfill",
        occurred_at=T0 + timedelta(hours=2),
        recorded_at=T0 + timedelta(days=2),
        achievement_source=achievement,
    )
    history = PersonalHistoryRecordSet(SUBJECT, (achievement,), (milestone,))

    history.validate_against_epistemics(EpistemicRecordSet())


def test_same_exact_family_ref_across_independent_snapshots_is_not_content_authentication() -> None:
    alternate = AchievementFamily(
        FAMILY_ID,
        "Bounded Repeated Performance",
        "Different material wording under the same exact ref demonstrates that refs are not content hashes.",
        qualification_criteria=(
            AchievementCriterion("observable_result", "A materially different criterion description."),
        ),
        revision=1,
    )
    first_catalog = AchievementFamilyCatalog((FAMILY,))
    second_catalog = AchievementFamilyCatalog((alternate,))

    assert FAMILY.ref == alternate.ref
    assert first_catalog.to_json() != second_catalog.to_json()
    assert not hasattr(FAMILY.ref, "content_hash")
    assert not hasattr(FAMILY.ref, "signature")


def test_one_history_source_cannot_be_amplified_across_multiple_entries_of_one_legend() -> None:
    achievement = _achievement(
        "achievement_legend_amplification",
        artifact_ref="artifact:legend_amplification",
    )
    history = PersonalHistoryRecordSet(SUBJECT, (achievement,), ())
    source = LegendSourceRef(
        LegendSourceKind.ACHIEVEMENT_INSTANCE,
        str(achievement.achievement_id),
    )
    legend = _legend(
        "legend_repeated_source",
        entries=(
            PersonalLegendEntry((source,), "First framing", "First interpretation of one source."),
            PersonalLegendEntry((source,), "Second framing", "Second interpretation of the same source."),
        ),
        as_of=T0,
        generated_at=T0 + timedelta(minutes=30),
    )

    with pytest.raises(InvalidLegendSet, match="cited repeatedly"):
        PersonalLegendSet(SUBJECT, (legend,)).validate_against_history(history)


def test_model_qualified_achievement_is_declared_mechanism_not_authority_or_endorsement() -> None:
    achievement = _achievement(
        "achievement_model_qualified",
        artifact_ref="artifact:model_qualified",
        qualifier_kind=HistoryMechanismKind.MODEL,
    )

    assert achievement.qualifier_ref.kind is HistoryMechanismKind.MODEL
    assert not hasattr(achievement, "accepted")
    assert not hasattr(achievement, "is_authoritative")
    assert not hasattr(achievement, "subject_endorsed")
    assert not hasattr(achievement.qualification_policy_ref, "content_hash")
    assert not hasattr(achievement.qualification_policy_ref, "signature")
