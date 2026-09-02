from datetime import datetime, timedelta, timezone

from capability_lab.epistemics import CapabilitySubjectRef, EpistemicRecordSet, EvidenceId
from capability_lab.pilots.civilization_bootstrap_01 import (
    REVIEWED_PILOT_CAPTURE_TO_EVIDENCE_POLICY_V1,
    PilotEvidenceMaterializationId,
    PilotEvidenceMaterializationReview,
    PilotEvidenceMaterializationReviewId,
    PilotEvidenceMaterializationReviewerKind,
    PilotEvidenceMaterializationReviewerRef,
    PilotEvidenceMaterializationVerdict,
    initialize_private_workspace,
    pilot_evidence_materialization_candidate_sha256,
    propose_pilot_capture_evidence_materialization_v1,
    record_text_capture,
    resolve_reviewed_pilot_evidence_materialization_v1,
)


T0 = datetime(2026, 1, 3, 10, 0, tzinfo=timezone.utc)


def test_materialized_record_is_valid_pr2_epistemic_snapshot_input(tmp_path) -> None:
    root = tmp_path / "cb01"
    initialize_private_workspace(
        root,
        session_id="session_pr2_01",
        subject_ref=CapabilitySubjectRef("subject_pr2_01"),
        created_at=T0,
    )
    record_text_capture(
        root,
        capture_id="diagnosis_01",
        probe_id="diagnosis_reasoning",
        text_content="Synthetic bounded response.",
        captured_at=T0 + timedelta(minutes=1),
    )
    candidate = propose_pilot_capture_evidence_materialization_v1(
        root,
        capture_id="diagnosis_01",
        materialization_id=PilotEvidenceMaterializationId("materialization_pr2_01"),
        proposed_evidence_id=EvidenceId("evidence_pr2_01"),
        proposed_at=T0 + timedelta(minutes=2),
    )
    review = PilotEvidenceMaterializationReview(
        review_id=PilotEvidenceMaterializationReviewId("review_pr2_01"),
        materialization_id=candidate.materialization_id,
        candidate_sha256=pilot_evidence_materialization_candidate_sha256(candidate),
        policy_ref=REVIEWED_PILOT_CAPTURE_TO_EVIDENCE_POLICY_V1,
        reviewer_ref=PilotEvidenceMaterializationReviewerRef(
            PilotEvidenceMaterializationReviewerKind.HUMAN,
            "reviewer_pr2_01",
        ),
        verdict=PilotEvidenceMaterializationVerdict.MATERIALIZE,
        reviewed_at=T0 + timedelta(minutes=3),
        rationale="Create only a bounded PR2 source observation.",
    )
    evidence = resolve_reviewed_pilot_evidence_materialization_v1(
        root,
        candidate=candidate,
        review=review,
        resolved_at=T0 + timedelta(minutes=4),
    )

    assert evidence is not None
    record_set = EpistemicRecordSet(evidence_records=(evidence,))
    assert record_set.evidence_records == (evidence,)
    assert record_set.claims == ()
    assert record_set.evaluations == ()
