from datetime import datetime, timedelta, timezone

import capability_lab
import pytest

from capability_lab.epistemics import (
    CapabilitySubjectRef,
    EpistemicRecordSet,
    EvidenceContext,
    EvidenceId,
    EvidenceKind,
    EvidenceRecord,
    ProvenanceSource,
    ProvenanceSourceKind,
    ProvenanceTrail,
)
from capability_lab.history import (
    AchievementBasisKind,
    AchievementBasisRef,
    AchievementCriterion,
    AchievementFamily,
    AchievementFamilyCatalog,
    AchievementFamilyId,
    AchievementFamilyRef,
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
    PersonalHistoryRecordSet,
    PersonalLegend,
    PersonalLegendEntry,
    PersonalLegendId,
    PersonalLegendSet,
    PersonalMilestoneEvent,
    PersonalMilestoneEventId,
)


T0 = datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("subject_pr7_integrity")
FAMILY_ID = AchievementFamilyId("civilization_bootstrap", "bounded_integrity_build")
FAMILY_V1 = AchievementFamily(
    FAMILY_ID,
    "Bounded Integrity Build",
    "Completed one bounded functional build with an inspectable event-bearing basis.",
    qualification_criteria=(
        AchievementCriterion("functional_result", "A bounded functional result exists."),
    ),
    revision=1,
)
QUALIFIER = AchievementQualifierRef(HistoryMechanismKind.HUMAN, "test:pr7_integrity_qualifier")
QUAL_POLICY = AchievementQualificationPolicyRef.parse(
    "civilization_bootstrap:bounded_achievement_qualification@1"
)


def _achievement(
    achievement_id: str,
    *,
    artifact_ref: str = "artifact:pr7_integrity_build",
    achieved_at: datetime = T0,
    recorded_at: datetime = T0 + timedelta(minutes=10),
    family_ref: AchievementFamilyRef = FAMILY_V1.ref,
) -> AchievementInstance:
    return AchievementInstance(
        achievement_id=AchievementInstanceId(achievement_id),
        subject_ref=SUBJECT,
        family_ref=family_ref,
        achieved_at=achieved_at,
        recorded_at=recorded_at,
        qualification_policy_ref=QUAL_POLICY,
        qualifier_ref=QUALIFIER,
        basis_refs=(
            AchievementBasisRef(AchievementBasisKind.EXTERNAL_ARTIFACT, artifact_ref),
        ),
        context="Bounded adversarial history-integrity context.",
    )


def _milestone(
    milestone_id: str,
    *,
    occurred_at: datetime,
    recorded_at: datetime,
    title: str,
) -> PersonalMilestoneEvent:
    return PersonalMilestoneEvent(
        milestone_id=PersonalMilestoneEventId(milestone_id),
        subject_ref=SUBJECT,
        title=title,
        description="A person-scoped historical event used to test selective narrative projection.",
        significance_note="The recorder preserved this event as significant under the declared policy.",
        occurred_at=occurred_at,
        recorded_at=recorded_at,
        recorder_ref=MilestoneRecorderRef(
            HistoryMechanismKind.MODEL,
            "test:pr7_integrity_recorder",
        ),
        recording_policy_ref=MilestoneRecordingPolicyRef.parse(
            "core:personal_milestone_recording@1"
        ),
    )


def _legend(
    legend_id: str,
    source: LegendSourceRef,
    *,
    as_of: datetime,
    generated_at: datetime,
    title: str,
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
            "test:pr7_integrity_legend",
        ),
        title=title,
        summary="A deliberately selective source-backed narrative projection.",
        entries=(
            PersonalLegendEntry(
                (source,),
                "Selected history",
                "This entry interprets only its cited source and does not claim completeness.",
            ),
        ),
    )


def test_same_event_basis_cannot_be_replayed_as_multiple_instances_of_one_family() -> None:
    first = _achievement("achievement_pr7_replay_a")
    replay = _achievement("achievement_pr7_replay_b")

    with pytest.raises(InvalidHistoryRecordSet, match="replayed"):
        PersonalHistoryRecordSet(SUBJECT, (first, replay), ())


def test_same_event_basis_may_support_different_achievement_family_identities() -> None:
    first = _achievement("achievement_pr7_cross_family_a")
    other_family = AchievementFamilyRef.parse(
        "civilization_bootstrap:bounded_integrity_diagnosis@1"
    )
    second = _achievement(
        "achievement_pr7_cross_family_b",
        family_ref=other_family,
    )

    history = PersonalHistoryRecordSet(SUBJECT, (first, second), ())
    assert len(history.achievement_instances) == 2


def test_exact_family_revision_fails_closed_instead_of_retroactive_latest_substitution() -> None:
    achievement = _achievement("achievement_pr7_family_revision")
    history = PersonalHistoryRecordSet(SUBJECT, (achievement,), ())
    family_v2 = AchievementFamily(
        FAMILY_ID,
        "Bounded Integrity Build",
        "A materially revisited current family definition for the adversarial test.",
        qualification_criteria=(
            AchievementCriterion("functional_result", "A bounded functional result exists."),
        ),
        revision=2,
    )

    with pytest.raises(InvalidHistoryRecordSet, match="exact revision"):
        history.validate_against_family_catalog(AchievementFamilyCatalog((family_v2,)))


def test_legend_cannot_use_history_record_created_after_legend_generation() -> None:
    milestone = _milestone(
        "milestone_pr7_future_record",
        occurred_at=T0,
        recorded_at=T0 + timedelta(days=2),
        title="Backfilled milestone",
    )
    history = PersonalHistoryRecordSet(SUBJECT, (), (milestone,))
    legend = _legend(
        "legend_pr7_future_record",
        LegendSourceRef(
            LegendSourceKind.PERSONAL_MILESTONE_EVENT,
            str(milestone.milestone_id),
        ),
        as_of=T0,
        generated_at=T0 + timedelta(days=1),
        title="Impossible future-record legend",
    )

    with pytest.raises(InvalidLegendSet, match="recorded after"):
        PersonalLegendSet(SUBJECT, (legend,)).validate_against_history(history)


def test_historical_reconstruction_may_use_later_backfill_if_it_existed_by_generation_time() -> None:
    milestone = _milestone(
        "milestone_pr7_honest_backfill",
        occurred_at=T0,
        recorded_at=T0 + timedelta(days=2),
        title="Later honest backfill",
    )
    history = PersonalHistoryRecordSet(SUBJECT, (), (milestone,))
    legend = _legend(
        "legend_pr7_honest_backfill",
        LegendSourceRef(
            LegendSourceKind.PERSONAL_MILESTONE_EVENT,
            str(milestone.milestone_id),
        ),
        as_of=T0,
        generated_at=T0 + timedelta(days=3),
        title="Historical reconstruction",
    )

    PersonalLegendSet(SUBJECT, (legend,)).validate_against_history(history)


def test_history_record_cannot_feed_the_evidence_that_grounds_it() -> None:
    achievement_id = AchievementInstanceId("achievement_pr7_feedback")
    evidence = EvidenceRecord(
        evidence_id=EvidenceId("evidence_pr7_feedback"),
        subject_ref=SUBJECT,
        kind=EvidenceKind.PROJECT,
        summary="A project record whose provenance improperly points back to PR7 history.",
        context=EvidenceContext("Adversarial feedback-loop context."),
        observed_at=T0,
        recorded_at=T0 + timedelta(minutes=1),
        provenance=ProvenanceTrail(
            (
                ProvenanceSource(
                    ProvenanceSourceKind.ARTIFACT,
                    str(achievement_id),
                ),
            )
        ),
    )
    achievement = AchievementInstance(
        achievement_id=achievement_id,
        subject_ref=SUBJECT,
        family_ref=FAMILY_V1.ref,
        achieved_at=T0,
        recorded_at=T0 + timedelta(minutes=10),
        qualification_policy_ref=QUAL_POLICY,
        qualifier_ref=QUALIFIER,
        basis_refs=(
            AchievementBasisRef(
                AchievementBasisKind.EVIDENCE_RECORD,
                str(evidence.evidence_id),
            ),
        ),
        context="Feedback-loop adversarial context.",
    )
    history = PersonalHistoryRecordSet(SUBJECT, (achievement,), ())

    with pytest.raises(InvalidHistoryRecordSet, match="history-to-evidence"):
        history.validate_against_epistemics(EpistemicRecordSet(evidence_records=(evidence,)))


def test_milestone_significance_note_is_attributed_record_content_not_authority_or_score() -> None:
    milestone = _milestone(
        "milestone_pr7_significance",
        occurred_at=T0,
        recorded_at=T0 + timedelta(minutes=1),
        title="Model-recorded significance",
    )

    assert milestone.recorder_ref.kind is HistoryMechanismKind.MODEL
    assert not hasattr(milestone, "importance_score")
    assert not hasattr(milestone, "subject_endorsed")
    assert not hasattr(milestone, "is_authoritative")


def test_two_selective_legends_can_coexist_without_one_becoming_complete_history() -> None:
    milestone_a = _milestone(
        "milestone_pr7_selective_a",
        occurred_at=T0,
        recorded_at=T0 + timedelta(minutes=1),
        title="First selected event",
    )
    milestone_b = _milestone(
        "milestone_pr7_selective_b",
        occurred_at=T0 + timedelta(hours=1),
        recorded_at=T0 + timedelta(hours=1, minutes=1),
        title="Second selected event",
    )
    history = PersonalHistoryRecordSet(SUBJECT, (), (milestone_a, milestone_b))
    legend_a = _legend(
        "legend_pr7_selective_a",
        LegendSourceRef(
            LegendSourceKind.PERSONAL_MILESTONE_EVENT,
            str(milestone_a.milestone_id),
        ),
        as_of=T0 + timedelta(hours=2),
        generated_at=T0 + timedelta(hours=3),
        title="First selective view",
    )
    legend_b = _legend(
        "legend_pr7_selective_b",
        LegendSourceRef(
            LegendSourceKind.PERSONAL_MILESTONE_EVENT,
            str(milestone_b.milestone_id),
        ),
        as_of=T0 + timedelta(hours=2),
        generated_at=T0 + timedelta(hours=3),
        title="Second selective view",
    )
    legends = PersonalLegendSet(SUBJECT, (legend_a, legend_b))

    legends.validate_against_history(history)
    assert len(legends.legends) == 2


def test_history_ids_are_snapshot_local_opaque_ids_not_content_hashes() -> None:
    first = PersonalHistoryRecordSet(
        SUBJECT,
        (_achievement("achievement_pr7_snapshot_local", artifact_ref="artifact:one"),),
        (),
    )
    second = PersonalHistoryRecordSet(
        SUBJECT,
        (_achievement("achievement_pr7_snapshot_local", artifact_ref="artifact:two"),),
        (),
    )

    assert first.achievement_instances[0].achievement_id == second.achievement_instances[0].achievement_id
    assert first.to_json() != second.to_json()


def test_public_api_exposes_no_history_to_epistemics_or_in_place_retraction_shortcut() -> None:
    forbidden = {
        "achievement_to_evidence",
        "milestone_to_evidence",
        "legend_to_evidence",
        "legend_to_claim",
        "legend_to_state",
        "revoke_achievement",
        "delete_achievement",
        "delete_milestone",
        "correct_history_in_place",
        "canonical_legend",
        "official_legend",
    }

    assert forbidden.isdisjoint(set(capability_lab.__all__))
    assert all(not hasattr(capability_lab, name) for name in forbidden)
