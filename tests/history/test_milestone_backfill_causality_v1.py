from datetime import datetime, timedelta, timezone

import pytest

from capability_lab.epistemics import (
    CapabilityClaim,
    CapabilityClaimId,
    CapabilitySubjectRef,
    ClaimEvaluation,
    ClaimEvaluationId,
    ClaimScope,
    ConflictStatus,
    CoverageAssessment,
    CoverageStatus,
    EpistemicRecordSet,
    EvaluationConclusion,
    EvaluationPolicyRef,
    EvaluatorKind,
    EvaluatorRef,
    ProvenanceSource,
    ProvenanceSourceKind,
    ProvenanceTrail,
)
from capability_lab.history import (
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
from capability_lab.semantics import CapabilityConceptRef


T0 = datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("subject_pr7_backfill_causality")
CLAIM_ID = CapabilityClaimId("claim_pr7_backfill_causality")
EVAL_ID = ClaimEvaluationId("eval_pr7_backfill_causality")


def _provenance() -> ProvenanceTrail:
    return ProvenanceTrail(
        (
            ProvenanceSource(
                ProvenanceSourceKind.ACTOR,
                "test:pr7_backfill_reviewer",
            ),
        )
    )


def _claim(created_at: datetime) -> CapabilityClaim:
    return CapabilityClaim(
        claim_id=CLAIM_ID,
        subject_ref=SUBJECT,
        concept_ref=CapabilityConceptRef.parse("core:bounded_backfill_context@1"),
        statement="A bounded documentary claim created after the historical event but before its milestone record.",
        scope=ClaimScope("Documentary backfill context only."),
        created_at=created_at,
        provenance=_provenance(),
    )


def _evaluation(evaluated_at: datetime) -> ClaimEvaluation:
    return ClaimEvaluation(
        evaluation_id=EVAL_ID,
        claim_id=CLAIM_ID,
        policy_ref=EvaluationPolicyRef.parse("core:documentary_backfill_evaluation@1"),
        evaluator_ref=EvaluatorRef(EvaluatorKind.HUMAN, "test:pr7_backfill_reviewer"),
        evaluated_at=evaluated_at,
        evidence_assessments=(),
        coverage=CoverageAssessment(
            CoverageStatus.UNASSESSED,
            "No capability conclusion is needed for this milestone documentary-source test.",
        ),
        conflict_status=ConflictStatus.NONE,
        conclusion=EvaluationConclusion.ABSTAINED,
        rationale="The evaluation exists only as later documentary context for an earlier milestone event.",
    )


def _milestone(recorded_at: datetime) -> PersonalMilestoneEvent:
    return PersonalMilestoneEvent(
        milestone_id=PersonalMilestoneEventId("milestone_pr7_documentary_backfill"),
        subject_ref=SUBJECT,
        title="Historical event documented later",
        description="The event occurred before its later claim/evaluation context was recorded.",
        significance_note="Later documentary context does not move the event time forward.",
        occurred_at=T0,
        recorded_at=recorded_at,
        recorder_ref=MilestoneRecorderRef(
            HistoryMechanismKind.HUMAN,
            "test:pr7_backfill_recorder",
        ),
        recording_policy_ref=MilestoneRecordingPolicyRef.parse(
            "core:personal_milestone_recording@1"
        ),
        source_refs=(
            MilestoneSourceRef(MilestoneSourceKind.CAPABILITY_CLAIM, str(CLAIM_ID)),
            MilestoneSourceRef(MilestoneSourceKind.CLAIM_EVALUATION, str(EVAL_ID)),
        ),
    )


def test_later_documentary_claim_and_evaluation_may_support_honest_milestone_backfill() -> None:
    claim = _claim(T0 + timedelta(days=1))
    evaluation = _evaluation(T0 + timedelta(days=1, hours=1))
    milestone = _milestone(T0 + timedelta(days=2))
    history = PersonalHistoryRecordSet(SUBJECT, (), (milestone,))
    records = EpistemicRecordSet(claims=(claim,), evaluations=(evaluation,))

    history.validate_against_epistemics(records)


def test_documentary_claim_created_after_milestone_recording_boundary_is_rejected() -> None:
    milestone = _milestone(T0 + timedelta(days=2))
    claim = _claim(T0 + timedelta(days=3))
    # Keep the PR2 fixture itself causally valid: an evaluation cannot precede
    # the claim it evaluates. Both documentary records are intentionally after
    # the milestone recording boundary; this test targets the PR7 claim check.
    evaluation = _evaluation(T0 + timedelta(days=3, hours=1))
    history = PersonalHistoryRecordSet(SUBJECT, (), (milestone,))
    records = EpistemicRecordSet(claims=(claim,), evaluations=(evaluation,))

    with pytest.raises(InvalidHistoryRecordSet, match="claim must exist by milestone recorded_at"):
        history.validate_against_epistemics(records)
