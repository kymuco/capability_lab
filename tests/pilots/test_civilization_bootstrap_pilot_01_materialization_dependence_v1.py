from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from capability_lab.epistemics import CapabilitySubjectRef, EpistemicRecordSet, EvidenceId
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
    pilot_materialized_evidence_dependence_key_v1,
    propose_pilot_capture_evidence_materialization_v1,
    record_text_capture,
    resolve_reviewed_pilot_evidence_materialization_v1,
    validate_pilot_materialized_evidence_no_same_source_amplification_v1,
)


T0 = datetime(2026, 1, 4, 11, 0, tzinfo=timezone.utc)


def _workspace(tmp_path):
    root = tmp_path / "cb01"
    initialize_private_workspace(
        root,
        session_id="session_dependence_01",
        subject_ref=CapabilitySubjectRef("subject_dependence_01"),
        created_at=T0,
    )
    record_text_capture(
        root,
        capture_id="conceptual_01",
        probe_id="conceptual_explanation",
        text_content="Synthetic conceptual capture.",
        captured_at=T0 + timedelta(minutes=1),
    )
    record_text_capture(
        root,
        capture_id="calculation_01",
        probe_id="calculation_work",
        text_content="Synthetic calculation capture.",
        captured_at=T0 + timedelta(minutes=2),
    )
    return root


def _materialize(
    root,
    *,
    capture_id: str,
    materialization_id: str,
    evidence_id: str,
    review_id: str,
    proposed_at: datetime,
    reviewed_at: datetime,
    resolved_at: datetime,
):
    candidate = propose_pilot_capture_evidence_materialization_v1(
        root,
        capture_id=capture_id,
        materialization_id=PilotEvidenceMaterializationId(materialization_id),
        proposed_evidence_id=EvidenceId(evidence_id),
        proposed_at=proposed_at,
    )
    review = PilotEvidenceMaterializationReview(
        review_id=PilotEvidenceMaterializationReviewId(review_id),
        materialization_id=candidate.materialization_id,
        candidate_sha256=pilot_evidence_materialization_candidate_sha256(candidate),
        policy_ref=REVIEWED_PILOT_CAPTURE_TO_EVIDENCE_POLICY_V1,
        reviewer_ref=PilotEvidenceMaterializationReviewerRef(
            PilotEvidenceMaterializationReviewerKind.HUMAN,
            "reviewer_dependence_01",
        ),
        verdict=PilotEvidenceMaterializationVerdict.MATERIALIZE,
        reviewed_at=reviewed_at,
        rationale="Materialize the exact capture without capability inference.",
    )
    evidence = resolve_reviewed_pilot_evidence_materialization_v1(
        root,
        candidate=candidate,
        review=review,
        resolved_at=resolved_at,
    )
    assert evidence is not None
    return candidate, evidence


def test_distinct_materializations_of_same_capture_share_one_dependence_key(tmp_path) -> None:
    root = _workspace(tmp_path)
    candidate_a, evidence_a = _materialize(
        root,
        capture_id="conceptual_01",
        materialization_id="materialization_dependence_a",
        evidence_id="evidence_dependence_a",
        review_id="review_dependence_a",
        proposed_at=T0 + timedelta(minutes=3),
        reviewed_at=T0 + timedelta(minutes=4),
        resolved_at=T0 + timedelta(minutes=5),
    )
    candidate_b, evidence_b = _materialize(
        root,
        capture_id="conceptual_01",
        materialization_id="materialization_dependence_b",
        evidence_id="evidence_dependence_b",
        review_id="review_dependence_b",
        proposed_at=T0 + timedelta(minutes=6),
        reviewed_at=T0 + timedelta(minutes=7),
        resolved_at=T0 + timedelta(minutes=8),
    )

    assert evidence_a.evidence_id != evidence_b.evidence_id
    assert candidate_a.materialization_id != candidate_b.materialization_id
    assert candidate_a.source_capture_sha256 == candidate_b.source_capture_sha256
    assert (
        pilot_materialized_evidence_dependence_key_v1(evidence_a)
        == pilot_materialized_evidence_dependence_key_v1(evidence_b)
        == candidate_a.source_capture_ref
    )

    # PR2 intentionally permits archival coexistence. That is not independence.
    records = EpistemicRecordSet(evidence_records=(evidence_a, evidence_b))
    assert len(records.evidence_records) == 2

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="same-source materializations are dependent",
    ):
        validate_pilot_materialized_evidence_no_same_source_amplification_v1(
            records.evidence_records
        )


def test_distinct_capture_sources_pass_exact_same_source_gate_without_claiming_independence(
    tmp_path,
) -> None:
    root = _workspace(tmp_path)
    _candidate_a, evidence_a = _materialize(
        root,
        capture_id="conceptual_01",
        materialization_id="materialization_distinct_a",
        evidence_id="evidence_distinct_a",
        review_id="review_distinct_a",
        proposed_at=T0 + timedelta(minutes=3),
        reviewed_at=T0 + timedelta(minutes=4),
        resolved_at=T0 + timedelta(minutes=5),
    )
    _candidate_b, evidence_b = _materialize(
        root,
        capture_id="calculation_01",
        materialization_id="materialization_distinct_b",
        evidence_id="evidence_distinct_b",
        review_id="review_distinct_b",
        proposed_at=T0 + timedelta(minutes=6),
        reviewed_at=T0 + timedelta(minutes=7),
        resolved_at=T0 + timedelta(minutes=8),
    )

    assert (
        pilot_materialized_evidence_dependence_key_v1(evidence_a)
        != pilot_materialized_evidence_dependence_key_v1(evidence_b)
    )
    validated = validate_pilot_materialized_evidence_no_same_source_amplification_v1(
        (evidence_b, evidence_a)
    )
    assert validated == tuple(sorted((evidence_a, evidence_b), key=lambda item: item.evidence_id))


def test_dependence_key_fails_closed_on_structurally_inconsistent_payload_ref(tmp_path) -> None:
    root = _workspace(tmp_path)
    _candidate, evidence = _materialize(
        root,
        capture_id="conceptual_01",
        materialization_id="materialization_tamper_01",
        evidence_id="evidence_tamper_01",
        review_id="review_tamper_01",
        proposed_at=T0 + timedelta(minutes=3),
        reviewed_at=T0 + timedelta(minutes=4),
        resolved_at=T0 + timedelta(minutes=5),
    )
    tampered = replace(evidence, payload_refs=("pilot_capture:" + "0" * 64,))

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="payload_refs must exactly repeat",
    ):
        pilot_materialized_evidence_dependence_key_v1(tampered)
