from datetime import datetime, timedelta, timezone

import pytest

from capability_lab.epistemics import CapabilitySubjectRef
from capability_lab.history import (
    AchievementBasisKind,
    AchievementBasisRef,
    AchievementCriterion,
    AchievementFamily,
    AchievementFamilyCatalog,
    AchievementFamilyId,
    AchievementFamilyLifecycle,
    AchievementFamilyRef,
    AchievementInstance,
    AchievementInstanceId,
    AchievementQualificationPolicyRef,
    AchievementQualifierRef,
    HistoryMechanismKind,
    InvalidAchievementFamily,
    InvalidAchievementInstance,
    MilestoneRecorderRef,
    MilestoneRecordingPolicyRef,
    PersonalMilestoneEvent,
    PersonalMilestoneEventId,
)


T0 = datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("subject_pr7_core")
FAMILY = AchievementFamily(
    AchievementFamilyId("civilization_bootstrap", "bounded_sensor_system_build"),
    "Bounded Sensor System Build",
    "Completed an end-to-end sensor system with an observable physical measurement path under an explicit bounded context.",
    qualification_criteria=(
        AchievementCriterion("observable_output", "The system exposes an observable end-to-end output."),
        AchievementCriterion("physical_measurement_path", "The implementation includes a functioning physical measurement path."),
    ),
    aliases=("Sensor System Build",),
)


def test_achievement_family_is_shared_revisioned_semantics() -> None:
    assert FAMILY.ref == AchievementFamilyRef.parse(
        "civilization_bootstrap:bounded_sensor_system_build@1"
    )
    assert [item.key for item in FAMILY.qualification_criteria] == [
        "observable_output",
        "physical_measurement_path",
    ]
    assert AchievementFamilyCatalog((FAMILY,)).families == (FAMILY,)


def test_deprecated_family_requires_note_and_active_family_forbids_note() -> None:
    with pytest.raises(InvalidAchievementFamily):
        AchievementFamily(
            AchievementFamilyId("civilization_bootstrap", "old_family"),
            "Old Family",
            "Historical shared accomplishment semantics.",
            lifecycle=AchievementFamilyLifecycle.DEPRECATED,
        )
    with pytest.raises(InvalidAchievementFamily):
        AchievementFamily(
            AchievementFamilyId("civilization_bootstrap", "active_family"),
            "Active Family",
            "Current shared accomplishment semantics.",
            deprecation_note="Not allowed while active.",
        )


def test_achievement_requires_event_or_artifact_grounding_not_state_like_inference() -> None:
    common = dict(
        achievement_id=AchievementInstanceId("achievement_pr7_core"),
        subject_ref=SUBJECT,
        family_ref=FAMILY.ref,
        achieved_at=T0,
        recorded_at=T0 + timedelta(minutes=10),
        qualification_policy_ref=AchievementQualificationPolicyRef.parse(
            "civilization_bootstrap:bounded_achievement_qualification@1"
        ),
        qualifier_ref=AchievementQualifierRef(
            HistoryMechanismKind.HUMAN,
            "test:pr7_qualifier",
        ),
        context="A bounded bench implementation context.",
    )
    with pytest.raises(InvalidAchievementInstance):
        AchievementInstance(
            **common,
            basis_refs=(
                AchievementBasisRef(
                    AchievementBasisKind.CAPABILITY_CLAIM,
                    "claim_pr7_only",
                ),
            ),
        )

    achievement = AchievementInstance(
        **common,
        basis_refs=(
            AchievementBasisRef(
                AchievementBasisKind.EXTERNAL_ARTIFACT,
                "artifact:pr7_sensor_build",
            ),
        ),
    )
    assert achievement.family_ref == FAMILY.ref


def test_personal_milestone_may_record_failure_without_achievement_family() -> None:
    milestone = PersonalMilestoneEvent(
        milestone_id=PersonalMilestoneEventId("milestone_pr7_failure"),
        subject_ref=SUBJECT,
        title="First reconstruction attempt that changed the verification approach",
        description="A bounded reconstruction attempt failed and exposed a verification gap.",
        significance_note="The failure materially changed the later verification strategy.",
        occurred_at=T0,
        recorded_at=T0 + timedelta(days=1),
        recorder_ref=MilestoneRecorderRef(
            HistoryMechanismKind.HUMAN,
            "test:pr7_recorder",
        ),
        recording_policy_ref=MilestoneRecordingPolicyRef.parse(
            "core:personal_milestone_recording@1"
        ),
        tags=("failure", "verification_change"),
    )

    assert milestone.source_refs == ()
    assert milestone.tags == ("failure", "verification_change")
