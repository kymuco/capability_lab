from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from capability_lab.epistemics import CapabilitySubjectRef, EvidenceId
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
    materialization_candidate_to_json,
    materialization_review_to_json,
    pilot_evidence_materialization_candidate_sha256,
    propose_pilot_capture_evidence_materialization_v1,
    record_text_capture,
    resolve_reviewed_pilot_evidence_materialization_v1,
)


T0 = datetime(2026, 1, 2, 9, 0, tzinfo=timezone.utc)
RAW_PRIVATE_TEXT = "private synthetic response content that must stay in capture storage"


def _records(tmp_path):
    root = tmp_path / "cb01"
    initialize_private_workspace(
        root,
        session_id="session_privacy_01",
        subject_ref=CapabilitySubjectRef("subject_privacy_01"),
        created_at=T0,
    )
    record_text_capture(
        root,
        capture_id="conceptual_privacy_01",
        probe_id="conceptual_explanation",
        text_content=RAW_PRIVATE_TEXT,
        captured_at=T0 + timedelta(minutes=1),
    )
    candidate = propose_pilot_capture_evidence_materialization_v1(
        root,
        capture_id="conceptual_privacy_01",
        materialization_id=PilotEvidenceMaterializationId("materialization_privacy_01"),
        proposed_evidence_id=EvidenceId("evidence_privacy_01"),
        proposed_at=T0 + timedelta(minutes=2),
    )
    review = PilotEvidenceMaterializationReview(
        review_id=PilotEvidenceMaterializationReviewId("review_privacy_01"),
        materialization_id=candidate.materialization_id,
        candidate_sha256=pilot_evidence_materialization_candidate_sha256(candidate),
        policy_ref=REVIEWED_PILOT_CAPTURE_TO_EVIDENCE_POLICY_V1,
        reviewer_ref=PilotEvidenceMaterializationReviewerRef(
            PilotEvidenceMaterializationReviewerKind.HUMAN,
            "reviewer_privacy_01",
        ),
        verdict=PilotEvidenceMaterializationVerdict.MATERIALIZE,
        reviewed_at=T0 + timedelta(minutes=3),
        rationale="Review metadata must not copy the raw private response.",
    )
    return root, candidate, review


def test_candidate_source_capture_fingerprint_is_reverified_at_resolution(tmp_path) -> None:
    root, candidate, review = _records(tmp_path)
    tampered = replace(candidate, source_capture_sha256="0" * 64)
    tampered_review = replace(
        review,
        candidate_sha256=pilot_evidence_materialization_candidate_sha256(tampered),
    )

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="source_capture_sha256 does not match exact capture bytes",
    ):
        resolve_reviewed_pilot_evidence_materialization_v1(
            root,
            candidate=tampered,
            review=tampered_review,
            resolved_at=T0 + timedelta(minutes=4),
        )


def test_candidate_and_review_serialization_do_not_copy_raw_private_capture_text(tmp_path) -> None:
    _root, candidate, review = _records(tmp_path)

    assert RAW_PRIVATE_TEXT not in materialization_candidate_to_json(candidate)
    assert RAW_PRIVATE_TEXT not in materialization_review_to_json(review)


def test_repeated_resolution_of_same_exact_inputs_is_deterministic_not_extra_support(tmp_path) -> None:
    root, candidate, review = _records(tmp_path)
    resolved_at = T0 + timedelta(minutes=4)

    first = resolve_reviewed_pilot_evidence_materialization_v1(
        root,
        candidate=candidate,
        review=review,
        resolved_at=resolved_at,
    )
    second = resolve_reviewed_pilot_evidence_materialization_v1(
        root,
        candidate=candidate,
        review=review,
        resolved_at=resolved_at,
    )

    assert first == second
    assert first is not None
    assert first.payload_refs == (candidate.source_capture_ref,)
