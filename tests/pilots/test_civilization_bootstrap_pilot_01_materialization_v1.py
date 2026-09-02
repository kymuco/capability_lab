from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from capability_lab.epistemics import (
    CapabilitySubjectRef,
    EvidenceId,
    EvidenceKind,
    ProvenanceSourceKind,
)
from capability_lab.pilots.civilization_bootstrap_01 import (
    REVIEWED_PILOT_CAPTURE_TO_EVIDENCE_POLICY_V1,
    InvalidPilotEvidenceMaterialization,
    PilotEvidenceMaterializationId,
    PilotEvidenceMaterializationReview,
    PilotEvidenceMaterializationReviewId,
    PilotEvidenceMaterializationReviewerKind,
    PilotEvidenceMaterializationReviewerRef,
    PilotEvidenceMaterializationVerdict,
    initialize_private_workspace,
    pilot_evidence_materialization_candidate_sha256,
    propose_pilot_capture_evidence_materialization_v1,
    record_artifact_capture,
    record_text_capture,
    resolve_reviewed_pilot_evidence_materialization_v1,
    validate_private_workspace,
)


T0 = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


def _workspace(tmp_path):
    root = tmp_path / "cb01"
    initialize_private_workspace(
        root,
        session_id="session_01",
        subject_ref=CapabilitySubjectRef("subject_01"),
        created_at=T0,
    )
    record_text_capture(
        root,
        capture_id="conceptual_01",
        probe_id="conceptual_explanation",
        text_content="I do not know.",
        captured_at=T0 + timedelta(minutes=1),
        declared_tools=(),
    )
    return root


def _candidate(
    root,
    *,
    capture_id="conceptual_01",
    materialization_id="materialization_01",
    evidence_id="evidence_01",
    proposed_at=None,
):
    return propose_pilot_capture_evidence_materialization_v1(
        root,
        capture_id=capture_id,
        materialization_id=PilotEvidenceMaterializationId(materialization_id),
        proposed_evidence_id=EvidenceId(evidence_id),
        proposed_at=proposed_at or T0 + timedelta(minutes=2),
    )


def _review(
    candidate,
    *,
    verdict=PilotEvidenceMaterializationVerdict.MATERIALIZE,
    reviewed_at=None,
):
    return PilotEvidenceMaterializationReview(
        review_id=PilotEvidenceMaterializationReviewId("review_01"),
        materialization_id=candidate.materialization_id,
        candidate_sha256=pilot_evidence_materialization_candidate_sha256(candidate),
        policy_ref=REVIEWED_PILOT_CAPTURE_TO_EVIDENCE_POLICY_V1,
        reviewer_ref=PilotEvidenceMaterializationReviewerRef(
            PilotEvidenceMaterializationReviewerKind.HUMAN,
            "reviewer_01",
        ),
        verdict=verdict,
        reviewed_at=reviewed_at or T0 + timedelta(minutes=3),
        rationale=(
            "Preserve only the bounded source observation without correctness "
            "or capability inference."
        ),
    )


def test_materialize_text_capture_as_neutral_pr2_evidence_without_outcome_inference(
    tmp_path,
) -> None:
    root = _workspace(tmp_path)
    before = validate_private_workspace(root)
    candidate = _candidate(root)
    evidence = resolve_reviewed_pilot_evidence_materialization_v1(
        root,
        candidate=candidate,
        review=_review(candidate),
        resolved_at=T0 + timedelta(minutes=4),
    )
    after = validate_private_workspace(root)

    assert evidence is not None
    assert str(evidence.evidence_id) == "evidence_01"
    assert str(evidence.subject_ref) == "subject_01"
    assert candidate.subject_ref == CapabilitySubjectRef("subject_01")
    assert evidence.kind is EvidenceKind.OTHER
    assert evidence.outcome is None
    assert evidence.observed_at == T0 + timedelta(minutes=1)
    assert evidence.recorded_at == T0 + timedelta(minutes=4)
    assert evidence.provenance.steps[0].occurred_at == T0 + timedelta(minutes=4)
    assert evidence.provenance.sources[0].kind is ProvenanceSourceKind.EXTERNAL_RECORD
    assert evidence.provenance.sources[0].ref == candidate.source_capture_ref
    assert evidence.payload_refs == (candidate.source_capture_ref,)
    assert before.snapshot_sha256 == after.snapshot_sha256

    rendered = (evidence.summary + " " + evidence.context.description).lower()
    assert "i do not know" not in rendered
    for forbidden in (
        "failure",
        "failed",
        "incorrect",
        "insufficient",
        "supported",
        "mastery",
    ):
        assert forbidden not in rendered


def test_do_not_materialize_produces_no_negative_evidence(tmp_path) -> None:
    root = _workspace(tmp_path)
    candidate = _candidate(root)
    before = validate_private_workspace(root).snapshot_sha256

    result = resolve_reviewed_pilot_evidence_materialization_v1(
        root,
        candidate=candidate,
        review=_review(
            candidate,
            verdict=PilotEvidenceMaterializationVerdict.DO_NOT_MATERIALIZE,
        ),
        resolved_at=T0 + timedelta(minutes=4),
    )

    assert result is None
    assert validate_private_workspace(root).snapshot_sha256 == before


def test_absent_optional_execution_capture_cannot_be_materialized_as_negative_evidence(
    tmp_path,
) -> None:
    root = _workspace(tmp_path)

    with pytest.raises(InvalidPilotEvidenceMaterialization, match="absent or ambiguous"):
        _candidate(root, capture_id="execution_artifact")


def test_candidate_is_invalidated_when_workspace_changes_after_proposal(tmp_path) -> None:
    root = _workspace(tmp_path)
    candidate = _candidate(root)
    record_text_capture(
        root,
        capture_id="execution_note_01",
        probe_id="execution_artifact",
        text_content="Optional execution context added after the candidate was proposed.",
        captured_at=T0 + timedelta(minutes=2, seconds=30),
    )

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="snapshot no longer matches",
    ):
        resolve_reviewed_pilot_evidence_materialization_v1(
            root,
            candidate=candidate,
            review=_review(candidate, reviewed_at=T0 + timedelta(minutes=4)),
            resolved_at=T0 + timedelta(minutes=5),
        )


def test_file_capture_materializes_as_artifact_without_success_or_failure_outcome(
    tmp_path,
) -> None:
    root = _workspace(tmp_path)
    source = tmp_path / "measurement.txt"
    source.write_text("declared measurement note", encoding="utf-8")
    record_artifact_capture(
        root,
        capture_id="execution_artifact_01",
        probe_id="execution_artifact",
        source_file=source,
        captured_at=T0 + timedelta(minutes=2),
    )
    candidate = propose_pilot_capture_evidence_materialization_v1(
        root,
        capture_id="execution_artifact_01",
        materialization_id=PilotEvidenceMaterializationId(
            "materialization_artifact_01"
        ),
        proposed_evidence_id=EvidenceId("evidence_artifact_01"),
        proposed_at=T0 + timedelta(minutes=3),
    )
    review = PilotEvidenceMaterializationReview(
        review_id=PilotEvidenceMaterializationReviewId("review_artifact_01"),
        materialization_id=candidate.materialization_id,
        candidate_sha256=pilot_evidence_materialization_candidate_sha256(candidate),
        policy_ref=REVIEWED_PILOT_CAPTURE_TO_EVIDENCE_POLICY_V1,
        reviewer_ref=PilotEvidenceMaterializationReviewerRef(
            PilotEvidenceMaterializationReviewerKind.HUMAN,
            "reviewer_01",
        ),
        verdict=PilotEvidenceMaterializationVerdict.MATERIALIZE,
        reviewed_at=T0 + timedelta(minutes=4),
        rationale="Materialize the exact artifact observation only.",
    )

    evidence = resolve_reviewed_pilot_evidence_materialization_v1(
        root,
        candidate=candidate,
        review=review,
        resolved_at=T0 + timedelta(minutes=5),
    )

    assert evidence is not None
    assert evidence.kind is EvidenceKind.ARTIFACT
    assert evidence.outcome is None
    assert evidence.recorded_at == T0 + timedelta(minutes=5)
    assert evidence.payload_refs == (candidate.source_capture_ref,)


def test_review_must_match_exact_candidate_and_cannot_predate_proposal(tmp_path) -> None:
    root = _workspace(tmp_path)
    candidate = _candidate(root)
    wrong_id_review = PilotEvidenceMaterializationReview(
        review_id=PilotEvidenceMaterializationReviewId("review_wrong"),
        materialization_id=PilotEvidenceMaterializationId("materialization_other"),
        candidate_sha256=pilot_evidence_materialization_candidate_sha256(candidate),
        policy_ref=REVIEWED_PILOT_CAPTURE_TO_EVIDENCE_POLICY_V1,
        reviewer_ref=PilotEvidenceMaterializationReviewerRef(
            PilotEvidenceMaterializationReviewerKind.HUMAN,
            "reviewer_01",
        ),
        verdict=PilotEvidenceMaterializationVerdict.MATERIALIZE,
        reviewed_at=T0 + timedelta(minutes=3),
        rationale="Wrong candidate on purpose.",
    )
    with pytest.raises(InvalidPilotEvidenceMaterialization, match="does not match candidate"):
        resolve_reviewed_pilot_evidence_materialization_v1(
            root,
            candidate=candidate,
            review=wrong_id_review,
            resolved_at=T0 + timedelta(minutes=4),
        )

    early_review = _review(
        candidate,
        reviewed_at=T0 + timedelta(minutes=1, seconds=30),
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="must not precede candidate proposed_at",
    ):
        resolve_reviewed_pilot_evidence_materialization_v1(
            root,
            candidate=candidate,
            review=early_review,
            resolved_at=T0 + timedelta(minutes=4),
        )


def test_same_materialization_id_cannot_replay_review_onto_changed_evidence_id(
    tmp_path,
) -> None:
    root = _workspace(tmp_path)
    candidate = _candidate(root)
    review = _review(candidate)
    replay_target = replace(candidate, proposed_evidence_id=EvidenceId("evidence_other"))

    assert replay_target.materialization_id == candidate.materialization_id
    assert (
        pilot_evidence_materialization_candidate_sha256(replay_target)
        != review.candidate_sha256
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="candidate_sha256 does not match exact candidate",
    ):
        resolve_reviewed_pilot_evidence_materialization_v1(
            root,
            candidate=replay_target,
            review=review,
            resolved_at=T0 + timedelta(minutes=4),
        )


def test_same_materialization_id_cannot_replay_review_onto_changed_proposal_time(
    tmp_path,
) -> None:
    root = _workspace(tmp_path)
    candidate = _candidate(root)
    review = _review(candidate)
    replay_target = replace(candidate, proposed_at=candidate.proposed_at + timedelta(seconds=1))

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="candidate_sha256 does not match exact candidate",
    ):
        resolve_reviewed_pilot_evidence_materialization_v1(
            root,
            candidate=replay_target,
            review=review,
            resolved_at=T0 + timedelta(minutes=4),
        )


def test_same_materialization_id_cannot_replay_review_onto_other_capture(tmp_path) -> None:
    root = _workspace(tmp_path)
    record_text_capture(
        root,
        capture_id="calculation_01",
        probe_id="calculation_work",
        text_content="No worked response.",
        captured_at=T0 + timedelta(minutes=1, seconds=30),
    )
    candidate_a = _candidate(root)
    candidate_b = _candidate(
        root,
        capture_id="calculation_01",
        materialization_id=str(candidate_a.materialization_id),
        evidence_id="evidence_calculation_01",
        proposed_at=T0 + timedelta(minutes=2),
    )
    review_a = _review(candidate_a)

    assert candidate_a.materialization_id == candidate_b.materialization_id
    assert candidate_a.source_capture_sha256 != candidate_b.source_capture_sha256
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="candidate_sha256 does not match exact candidate",
    ):
        resolve_reviewed_pilot_evidence_materialization_v1(
            root,
            candidate=candidate_b,
            review=review_a,
            resolved_at=T0 + timedelta(minutes=4),
        )


def test_review_resolution_cannot_predate_selected_review(tmp_path) -> None:
    root = _workspace(tmp_path)
    candidate = _candidate(root)
    review = _review(candidate, reviewed_at=T0 + timedelta(minutes=3))

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="resolved_at must not precede review reviewed_at",
    ):
        resolve_reviewed_pilot_evidence_materialization_v1(
            root,
            candidate=candidate,
            review=review,
            resolved_at=T0 + timedelta(minutes=2, seconds=30),
        )


def test_declared_human_reviewer_is_the_only_v1_mechanism_kind() -> None:
    assert tuple(PilotEvidenceMaterializationReviewerKind) == (
        PilotEvidenceMaterializationReviewerKind.HUMAN,
    )
