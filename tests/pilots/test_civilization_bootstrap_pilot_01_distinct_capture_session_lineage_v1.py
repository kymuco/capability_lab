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
    PilotMaterializedEvidenceBasisEntry,
    initialize_private_workspace,
    pilot_evidence_materialization_candidate_sha256,
    pilot_materialization_candidate_session_lineage_key_v1,
    pilot_materialized_evidence_dependence_key_v1,
    propose_pilot_capture_evidence_materialization_v1,
    record_text_capture,
    resolve_reviewed_pilot_evidence_materialization_v1,
    validate_pilot_materialized_evidence_independence_preconditions_v1,
    validate_pilot_materialized_evidence_no_same_source_amplification_v1,
)


T0 = datetime(2026, 1, 5, 12, 0, tzinfo=timezone.utc)


def _workspace(tmp_path, *, name: str, session_id: str, subject_ref: str):
    root = tmp_path / name
    initialize_private_workspace(
        root,
        session_id=session_id,
        subject_ref=CapabilitySubjectRef(subject_ref),
        created_at=T0,
    )
    record_text_capture(
        root,
        capture_id="conceptual_01",
        probe_id="conceptual_explanation",
        text_content="Synthetic conceptual observation.",
        captured_at=T0 + timedelta(minutes=1),
    )
    record_text_capture(
        root,
        capture_id="calculation_01",
        probe_id="calculation_work",
        text_content="Synthetic calculation observation.",
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
            "reviewer_correlation_01",
        ),
        verdict=PilotEvidenceMaterializationVerdict.MATERIALIZE,
        reviewed_at=reviewed_at,
        rationale="Materialize one exact observation without independence inference.",
    )
    evidence = resolve_reviewed_pilot_evidence_materialization_v1(
        root,
        candidate=candidate,
        review=review,
        resolved_at=resolved_at,
    )
    assert evidence is not None
    return candidate, evidence


def test_distinct_capture_hashes_in_same_session_share_session_lineage(tmp_path) -> None:
    root = _workspace(
        tmp_path,
        name="same_session",
        session_id="session_correlation_01",
        subject_ref="subject_correlation_01",
    )
    candidate_a, evidence_a = _materialize(
        root,
        capture_id="conceptual_01",
        materialization_id="materialization_correlation_a",
        evidence_id="evidence_correlation_a",
        review_id="review_correlation_a",
        proposed_at=T0 + timedelta(minutes=3),
        reviewed_at=T0 + timedelta(minutes=4),
        resolved_at=T0 + timedelta(minutes=5),
    )
    candidate_b, evidence_b = _materialize(
        root,
        capture_id="calculation_01",
        materialization_id="materialization_correlation_b",
        evidence_id="evidence_correlation_b",
        review_id="review_correlation_b",
        proposed_at=T0 + timedelta(minutes=6),
        reviewed_at=T0 + timedelta(minutes=7),
        resolved_at=T0 + timedelta(minutes=8),
    )

    assert candidate_a.source_capture_sha256 != candidate_b.source_capture_sha256
    assert (
        pilot_materialized_evidence_dependence_key_v1(evidence_a)
        != pilot_materialized_evidence_dependence_key_v1(evidence_b)
    )
    assert (
        pilot_materialization_candidate_session_lineage_key_v1(candidate_a)
        == pilot_materialization_candidate_session_lineage_key_v1(candidate_b)
    )

    assert validate_pilot_materialized_evidence_no_same_source_amplification_v1(
        (evidence_a, evidence_b)
    ) == (evidence_a, evidence_b)

    entry_a = PilotMaterializedEvidenceBasisEntry(candidate_a, evidence_a)
    entry_b = PilotMaterializedEvidenceBasisEntry(candidate_b, evidence_b)
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="same-session observations are structurally correlated",
    ):
        validate_pilot_materialized_evidence_independence_preconditions_v1(
            (entry_a, entry_b)
        )


def test_basis_entry_binds_exact_candidate_so_session_cannot_be_relabelled(tmp_path) -> None:
    root = _workspace(
        tmp_path,
        name="candidate_binding",
        session_id="session_binding_01",
        subject_ref="subject_binding_01",
    )
    candidate, evidence = _materialize(
        root,
        capture_id="conceptual_01",
        materialization_id="materialization_binding_01",
        evidence_id="evidence_binding_01",
        review_id="review_binding_01",
        proposed_at=T0 + timedelta(minutes=3),
        reviewed_at=T0 + timedelta(minutes=4),
        resolved_at=T0 + timedelta(minutes=5),
    )
    relabelled = replace(candidate, session_id="session_forged_independence")

    assert relabelled.source_capture_sha256 == candidate.source_capture_sha256
    assert (
        pilot_materialization_candidate_session_lineage_key_v1(relabelled)
        != pilot_materialization_candidate_session_lineage_key_v1(candidate)
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="candidate_sha256 does not match exact candidate",
    ):
        PilotMaterializedEvidenceBasisEntry(relabelled, evidence)


def test_distinct_sessions_clear_only_known_session_lineage_precondition(tmp_path) -> None:
    root_a = _workspace(
        tmp_path,
        name="session_a",
        session_id="session_independence_a",
        subject_ref="subject_independence_01",
    )
    root_b = _workspace(
        tmp_path,
        name="session_b",
        session_id="session_independence_b",
        subject_ref="subject_independence_01",
    )
    candidate_a, evidence_a = _materialize(
        root_a,
        capture_id="conceptual_01",
        materialization_id="materialization_session_a",
        evidence_id="evidence_session_a",
        review_id="review_session_a",
        proposed_at=T0 + timedelta(minutes=3),
        reviewed_at=T0 + timedelta(minutes=4),
        resolved_at=T0 + timedelta(minutes=5),
    )
    candidate_b, evidence_b = _materialize(
        root_b,
        capture_id="conceptual_01",
        materialization_id="materialization_session_b",
        evidence_id="evidence_session_b",
        review_id="review_session_b",
        proposed_at=T0 + timedelta(minutes=3),
        reviewed_at=T0 + timedelta(minutes=4),
        resolved_at=T0 + timedelta(minutes=5),
    )

    entry_a = PilotMaterializedEvidenceBasisEntry(candidate_a, evidence_a)
    entry_b = PilotMaterializedEvidenceBasisEntry(candidate_b, evidence_b)
    assert entry_a.session_lineage_key != entry_b.session_lineage_key

    assert validate_pilot_materialized_evidence_independence_preconditions_v1(
        (entry_b, entry_a)
    ) == (entry_a, entry_b)


def test_session_lineage_key_is_domain_separated_and_does_not_embed_raw_session_id(
    tmp_path,
) -> None:
    root = _workspace(
        tmp_path,
        name="lineage_key",
        session_id="session_sensitive_identifier_01",
        subject_ref="subject_lineage_01",
    )
    candidate, _evidence = _materialize(
        root,
        capture_id="conceptual_01",
        materialization_id="materialization_lineage_01",
        evidence_id="evidence_lineage_01",
        review_id="review_lineage_01",
        proposed_at=T0 + timedelta(minutes=3),
        reviewed_at=T0 + timedelta(minutes=4),
        resolved_at=T0 + timedelta(minutes=5),
    )
    key = pilot_materialization_candidate_session_lineage_key_v1(candidate)

    assert key.startswith("pilot_session_lineage:")
    assert len(key.removeprefix("pilot_session_lineage:")) == 64
    assert candidate.session_id not in key


def test_malformed_materialization_note_fails_closed_before_basis_use(tmp_path) -> None:
    root = _workspace(
        tmp_path,
        name="note_tamper",
        session_id="session_note_01",
        subject_ref="subject_note_01",
    )
    candidate, evidence = _materialize(
        root,
        capture_id="conceptual_01",
        materialization_id="materialization_note_01",
        evidence_id="evidence_note_01",
        review_id="review_note_01",
        proposed_at=T0 + timedelta(minutes=3),
        reviewed_at=T0 + timedelta(minutes=4),
        resolved_at=T0 + timedelta(minutes=5),
    )
    step = evidence.provenance.steps[0]
    tampered_step = replace(step, note="candidate_sha256 missing")
    tampered = replace(
        evidence,
        provenance=replace(evidence.provenance, steps=(tampered_step,)),
    )

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="provenance note is not canonical",
    ):
        PilotMaterializedEvidenceBasisEntry(candidate, tampered)
