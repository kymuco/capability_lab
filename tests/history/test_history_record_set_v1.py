from datetime import datetime, timedelta, timezone

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
    MilestoneRecorderRef,
    MilestoneRecordingPolicyRef,
    MilestoneSourceKind,
    MilestoneSourceRef,
    PersonalHistoryRecordSet,
    PersonalMilestoneEvent,
    PersonalMilestoneEventId,
)


T0 = datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("subject_pr7_history")
OTHER = CapabilitySubjectRef("subject_pr7_other")
FAMILY = AchievementFamily(
    AchievementFamilyId("civilization_bootstrap", "bounded_dc_circuit_project"),
    "Bounded DC Circuit Project",
    "Completed and checked a bounded low-voltage DC circuit project under an explicit project context.",
)


def _evidence(subject=SUBJECT, evidence_id="evidence_pr7_history") -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=EvidenceId(evidence_id),
        subject_ref=subject,
        kind=EvidenceKind.PROJECT,
        summary="Completed a bounded circuit project.",
        context=EvidenceContext("Low-voltage bounded project context."),
        observed_at=T0,
        recorded_at=T0 + timedelta(minutes=1),
        provenance=ProvenanceTrail(
            (ProvenanceSource(ProvenanceSourceKind.ACTOR, "test:pr7_observer"),)
        ),
    )


def _achievement(basis: AchievementBasisRef) -> AchievementInstance:
    return AchievementInstance(
        achievement_id=AchievementInstanceId("achievement_pr7_history"),
        subject_ref=SUBJECT,
        family_ref=FAMILY.ref,
        achieved_at=T0,
        recorded_at=T0 + timedelta(hours=1),
        qualification_policy_ref=AchievementQualificationPolicyRef.parse(
            "civilization_bootstrap:bounded_achievement_qualification@1"
        ),
        qualifier_ref=AchievementQualifierRef(
            HistoryMechanismKind.HUMAN,
            "test:pr7_qualifier",
        ),
        basis_refs=(basis,),
        context="Bounded project context.",
    )


def test_history_set_is_one_subject_and_validates_exact_family_revision() -> None:
    achievement = _achievement(
        AchievementBasisRef(AchievementBasisKind.EVIDENCE_RECORD, "evidence_pr7_history")
    )
    history = PersonalHistoryRecordSet(SUBJECT, (achievement,), ())
    history.validate_against_family_catalog(AchievementFamilyCatalog((FAMILY,)))

    revised = AchievementFamily(
        FAMILY.family_id,
        FAMILY.name,
        FAMILY.definition,
        revision=2,
    )
    with pytest.raises(InvalidHistoryRecordSet):
        history.validate_against_family_catalog(AchievementFamilyCatalog((revised,)))


def test_internal_evidence_basis_must_exist_and_match_subject() -> None:
    achievement = _achievement(
        AchievementBasisRef(AchievementBasisKind.EVIDENCE_RECORD, "evidence_pr7_history")
    )
    history = PersonalHistoryRecordSet(SUBJECT, (achievement,), ())

    with pytest.raises(InvalidHistoryRecordSet):
        history.validate_against_epistemics(EpistemicRecordSet())

    with pytest.raises(InvalidHistoryRecordSet):
        history.validate_against_epistemics(
            EpistemicRecordSet(evidence_records=(_evidence(OTHER),))
        )

    history.validate_against_epistemics(
        EpistemicRecordSet(evidence_records=(_evidence(),))
    )


def test_known_private_internal_id_cannot_be_relabelled_external() -> None:
    evidence = _evidence()
    achievement = _achievement(
        AchievementBasisRef(
            AchievementBasisKind.EXTERNAL_ARTIFACT,
            str(evidence.evidence_id),
        )
    )
    history = PersonalHistoryRecordSet(SUBJECT, (achievement,), ())

    with pytest.raises(InvalidHistoryRecordSet):
        history.validate_against_epistemics(
            EpistemicRecordSet(evidence_records=(evidence,))
        )


def test_achievement_to_milestone_link_is_explicit_and_causal() -> None:
    evidence = _evidence()
    achievement = _achievement(
        AchievementBasisRef(AchievementBasisKind.EVIDENCE_RECORD, str(evidence.evidence_id))
    )
    milestone = PersonalMilestoneEvent(
        milestone_id=PersonalMilestoneEventId("milestone_pr7_history"),
        subject_ref=SUBJECT,
        title="First complete bounded circuit project",
        description="The project became a personally meaningful transition point.",
        significance_note="It was the first end-to-end circuit project preserved in personal history.",
        occurred_at=T0 + timedelta(hours=2),
        recorded_at=T0 + timedelta(hours=3),
        recorder_ref=MilestoneRecorderRef(
            HistoryMechanismKind.HUMAN,
            "test:pr7_recorder",
        ),
        recording_policy_ref=MilestoneRecordingPolicyRef.parse(
            "core:personal_milestone_recording@1"
        ),
        source_refs=(
            MilestoneSourceRef(
                MilestoneSourceKind.ACHIEVEMENT_INSTANCE,
                str(achievement.achievement_id),
            ),
        ),
    )
    history = PersonalHistoryRecordSet(SUBJECT, (achievement,), (milestone,))
    history.validate_against_epistemics(
        EpistemicRecordSet(evidence_records=(evidence,))
    )

    assert achievement.achievement_id != milestone.milestone_id
    assert milestone.source_refs[0].ref == str(achievement.achievement_id)


def test_history_set_rejects_cross_subject_records() -> None:
    foreign = PersonalMilestoneEvent(
        milestone_id=PersonalMilestoneEventId("milestone_pr7_other"),
        subject_ref=OTHER,
        title="Foreign milestone",
        description="A milestone for another subject.",
        significance_note="Must not enter this subject's history snapshot.",
        occurred_at=T0,
        recorded_at=T0,
        recorder_ref=MilestoneRecorderRef(HistoryMechanismKind.HUMAN, "test:recorder"),
        recording_policy_ref=MilestoneRecordingPolicyRef.parse("core:personal_milestone_recording@1"),
    )
    with pytest.raises(InvalidHistoryRecordSet):
        PersonalHistoryRecordSet(SUBJECT, (), (foreign,))
