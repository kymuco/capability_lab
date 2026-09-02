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
    pilot_materialization_candidate_elicitation_lineage_key_v1,
    pilot_materialization_candidate_session_lineage_key_v1,
    propose_pilot_capture_evidence_materialization_v1,
    record_text_capture,
    resolve_reviewed_pilot_evidence_materialization_v1,
    validate_pilot_materialized_evidence_cross_session_replication_preconditions_v1,
    validate_pilot_materialized_evidence_independence_preconditions_v1,
)


T0 = datetime(2026, 1, 6, 12, 0, tzinfo=timezone.utc)


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
):
    candidate = propose_pilot_capture_evidence_materialization_v1(
        root,
        capture_id=capture_id,
        materialization_id=PilotEvidenceMaterializationId(materialization_id),
        proposed_evidence_id=EvidenceId(evidence_id),
        proposed_at=T0 + timedelta(minutes=3),
    )
    review = PilotEvidenceMaterializationReview(
        review_id=PilotEvidenceMaterializationReviewId(review_id),
        materialization_id=candidate.materialization_id,
        candidate_sha256=pilot_evidence_materialization_candidate_sha256(candidate),
        policy_ref=REVIEWED_PILOT_CAPTURE_TO_EVIDENCE_POLICY_V1,
        reviewer_ref=PilotEvidenceMaterializationReviewerRef(
            PilotEvidenceMaterializationReviewerKind.HUMAN,
            "reviewer_cross_session_01",
        ),
        verdict=PilotEvidenceMaterializationVerdict.MATERIALIZE,
        reviewed_at=T0 + timedelta(minutes=4),
        rationale="Materialize one exact observation without independence inference.",
    )
    evidence = resolve_reviewed_pilot_evidence_materialization_v1(
        root,
        candidate=candidate,
        review=review,
        resolved_at=T0 + timedelta(minutes=5),
    )
    assert evidence is not None
    return candidate, evidence


def test_same_probe_across_distinct_sessions_is_known_elicitation_correlation(tmp_path) -> None:
    root_a = _workspace(
        tmp_path,
        name="repeat_a",
        session_id="session_repeat_a",
        subject_ref="subject_repeat_01",
    )
    root_b = _workspace(
        tmp_path,
        name="repeat_b",
        session_id="session_repeat_b",
        subject_ref="subject_repeat_01",
    )
    candidate_a, evidence_a = _materialize(
        root_a,
        capture_id="conceptual_01",
        materialization_id="materialization_repeat_a",
        evidence_id="evidence_repeat_a",
        review_id="review_repeat_a",
    )
    candidate_b, evidence_b = _materialize(
        root_b,
        capture_id="conceptual_01",
        materialization_id="materialization_repeat_b",
        evidence_id="evidence_repeat_b",
        review_id="review_repeat_b",
    )

    entry_a = PilotMaterializedEvidenceBasisEntry(candidate_a, evidence_a)
    entry_b = PilotMaterializedEvidenceBasisEntry(candidate_b, evidence_b)

    assert candidate_a.source_capture_sha256 != candidate_b.source_capture_sha256
    assert entry_a.session_lineage_key != entry_b.session_lineage_key
    assert entry_a.elicitation_lineage_key == entry_b.elicitation_lineage_key

    # The older first-tier gate correctly never claimed that this PASS meant
    # cross-session independence.
    assert validate_pilot_materialized_evidence_independence_preconditions_v1(
        (entry_b, entry_a)
    ) == (entry_a, entry_b)

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="repeated same-probe observations share one test-form mechanism",
    ):
        validate_pilot_materialized_evidence_cross_session_replication_preconditions_v1(
            (entry_a, entry_b)
        )


def test_distinct_probes_across_distinct_sessions_clear_only_known_cross_session_gate(
    tmp_path,
) -> None:
    root_a = _workspace(
        tmp_path,
        name="different_probe_a",
        session_id="session_different_probe_a",
        subject_ref="subject_different_probe_01",
    )
    root_b = _workspace(
        tmp_path,
        name="different_probe_b",
        session_id="session_different_probe_b",
        subject_ref="subject_different_probe_01",
    )
    candidate_a, evidence_a = _materialize(
        root_a,
        capture_id="conceptual_01",
        materialization_id="materialization_different_probe_a",
        evidence_id="evidence_different_probe_a",
        review_id="review_different_probe_a",
    )
    candidate_b, evidence_b = _materialize(
        root_b,
        capture_id="calculation_01",
        materialization_id="materialization_different_probe_b",
        evidence_id="evidence_different_probe_b",
        review_id="review_different_probe_b",
    )

    entry_a = PilotMaterializedEvidenceBasisEntry(candidate_a, evidence_a)
    entry_b = PilotMaterializedEvidenceBasisEntry(candidate_b, evidence_b)

    assert entry_a.session_lineage_key != entry_b.session_lineage_key
    assert entry_a.elicitation_lineage_key != entry_b.elicitation_lineage_key
    assert validate_pilot_materialized_evidence_cross_session_replication_preconditions_v1(
        (entry_b, entry_a)
    ) == (entry_a, entry_b)


def test_elicitation_lineage_key_is_domain_separated_and_session_invariant(tmp_path) -> None:
    root_a = _workspace(
        tmp_path,
        name="key_a",
        session_id="session_sensitive_a",
        subject_ref="subject_key_01",
    )
    root_b = _workspace(
        tmp_path,
        name="key_b",
        session_id="session_sensitive_b",
        subject_ref="subject_key_01",
    )
    candidate_a, _evidence_a = _materialize(
        root_a,
        capture_id="conceptual_01",
        materialization_id="materialization_key_a",
        evidence_id="evidence_key_a",
        review_id="review_key_a",
    )
    candidate_b, _evidence_b = _materialize(
        root_b,
        capture_id="conceptual_01",
        materialization_id="materialization_key_b",
        evidence_id="evidence_key_b",
        review_id="review_key_b",
    )

    key_a = pilot_materialization_candidate_elicitation_lineage_key_v1(candidate_a)
    key_b = pilot_materialization_candidate_elicitation_lineage_key_v1(candidate_b)

    assert key_a == key_b
    assert key_a.startswith("pilot_elicitation_lineage:")
    assert len(key_a.removeprefix("pilot_elicitation_lineage:")) == 64
    assert candidate_a.session_id not in key_a
    assert candidate_a.probe_id not in key_a


def test_probe_relabel_cannot_forge_different_elicitation_lineage(tmp_path) -> None:
    root = _workspace(
        tmp_path,
        name="probe_binding",
        session_id="session_probe_binding_01",
        subject_ref="subject_probe_binding_01",
    )
    candidate, evidence = _materialize(
        root,
        capture_id="conceptual_01",
        materialization_id="materialization_probe_binding_01",
        evidence_id="evidence_probe_binding_01",
        review_id="review_probe_binding_01",
    )
    relabelled = replace(candidate, probe_id="calculation_work")

    assert (
        pilot_materialization_candidate_elicitation_lineage_key_v1(relabelled)
        != pilot_materialization_candidate_elicitation_lineage_key_v1(candidate)
    )
    assert (
        pilot_materialization_candidate_session_lineage_key_v1(relabelled)
        == pilot_materialization_candidate_session_lineage_key_v1(candidate)
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="candidate_sha256 does not match exact candidate",
    ):
        PilotMaterializedEvidenceBasisEntry(relabelled, evidence)
