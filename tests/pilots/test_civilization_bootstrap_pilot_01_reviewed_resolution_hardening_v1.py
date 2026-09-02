from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from capability_lab.epistemics import (
    CapabilitySubjectRef,
    ContextFactor,
    ContextFactorKind,
    EvidenceId,
    EvidenceKind,
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
    PilotMaterializedEvidenceBasisEntry,
    PilotReviewedMaterializationResolutionBinding,
    PilotReviewedMaterializationResolutionReceipt,
    initialize_private_workspace,
    pilot_evidence_materialization_candidate_sha256,
    propose_pilot_capture_evidence_materialization_v1,
    record_text_capture,
    resolve_reviewed_pilot_evidence_materialization_with_receipt_v1,
    validate_pilot_materialized_evidence_independence_preconditions_v1,
    validate_pilot_reviewed_materialization_resolution_binding_v1,
)


T0 = datetime(2026, 1, 21, 12, 0, tzinfo=timezone.utc)


def _reviewer():
    return PilotEvidenceMaterializationReviewerRef(
        PilotEvidenceMaterializationReviewerKind.HUMAN,
        "reviewer_resolution_hardening",
    )


def _workspace(tmp_path, *, name, session_id, probe_id, capture_id, minute):
    root = tmp_path / name
    initialize_private_workspace(
        root,
        session_id=session_id,
        subject_ref=CapabilitySubjectRef("subject_resolution_hardening"),
        created_at=T0,
    )
    record_text_capture(
        root,
        capture_id=capture_id,
        probe_id=probe_id,
        text_content=f"Synthetic {probe_id} observation.",
        captured_at=T0 + timedelta(minutes=minute),
    )
    return root


def _candidate_review(
    root,
    *,
    capture_id,
    materialization_id,
    evidence_id,
    review_id,
    proposed_minute,
    reviewed_minute,
    verdict=PilotEvidenceMaterializationVerdict.MATERIALIZE,
):
    candidate = propose_pilot_capture_evidence_materialization_v1(
        root,
        capture_id=capture_id,
        materialization_id=PilotEvidenceMaterializationId(materialization_id),
        proposed_evidence_id=EvidenceId(evidence_id),
        proposed_at=T0 + timedelta(minutes=proposed_minute),
    )
    review = PilotEvidenceMaterializationReview(
        review_id=PilotEvidenceMaterializationReviewId(review_id),
        materialization_id=candidate.materialization_id,
        candidate_sha256=pilot_evidence_materialization_candidate_sha256(candidate),
        policy_ref=REVIEWED_PILOT_CAPTURE_TO_EVIDENCE_POLICY_V1,
        reviewer_ref=_reviewer(),
        verdict=verdict,
        reviewed_at=T0 + timedelta(minutes=reviewed_minute),
        rationale="Exact bounded reviewed materialization decision.",
    )
    return candidate, review


def _resolved(tmp_path):
    root = _workspace(
        tmp_path,
        name="resolution_a",
        session_id="session_resolution_a",
        probe_id="conceptual_explanation",
        capture_id="capture_resolution_a",
        minute=1,
    )
    candidate, review = _candidate_review(
        root,
        capture_id="capture_resolution_a",
        materialization_id="materialization_resolution_a",
        evidence_id="evidence_resolution_a",
        review_id="review_resolution_a",
        proposed_minute=2,
        reviewed_minute=3,
    )
    evidence, receipt = resolve_reviewed_pilot_evidence_materialization_with_receipt_v1(
        root,
        candidate=candidate,
        review=review,
        resolved_at=T0 + timedelta(minutes=4),
    )
    assert evidence is not None
    assert receipt is not None
    binding = PilotReviewedMaterializationResolutionBinding(review, receipt)
    return candidate, review, evidence, receipt, binding


def test_materialize_issues_exact_receipt_and_binding_validates(tmp_path):
    candidate, _review, evidence, _receipt, binding = _resolved(tmp_path)
    validate_pilot_reviewed_materialization_resolution_binding_v1(
        candidate,
        evidence,
        binding,
    )


def test_do_not_materialize_issues_neither_evidence_nor_receipt(tmp_path):
    root = _workspace(
        tmp_path,
        name="resolution_do_not",
        session_id="session_resolution_do_not",
        probe_id="diagnosis_reasoning",
        capture_id="capture_resolution_do_not",
        minute=1,
    )
    candidate, review = _candidate_review(
        root,
        capture_id="capture_resolution_do_not",
        materialization_id="materialization_resolution_do_not",
        evidence_id="evidence_resolution_do_not",
        review_id="review_resolution_do_not",
        proposed_minute=2,
        reviewed_minute=3,
        verdict=PilotEvidenceMaterializationVerdict.DO_NOT_MATERIALIZE,
    )
    evidence, receipt = resolve_reviewed_pilot_evidence_materialization_with_receipt_v1(
        root,
        candidate=candidate,
        review=review,
        resolved_at=T0 + timedelta(minutes=4),
    )
    assert evidence is None
    assert receipt is None


def test_receipt_rejects_changed_review_after_resolution(tmp_path):
    candidate, review, evidence, receipt, _binding = _resolved(tmp_path)
    changed_review = replace(review, rationale="Changed after the resolver-issued receipt.")
    changed_binding = PilotReviewedMaterializationResolutionBinding(
        changed_review,
        receipt,
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="review_sha256 does not match exact selected review",
    ):
        validate_pilot_reviewed_materialization_resolution_binding_v1(
            candidate,
            evidence,
            changed_binding,
        )


def test_receipt_rejects_post_resolution_evidence_mutation(tmp_path):
    candidate, _review, evidence, _receipt, binding = _resolved(tmp_path)
    changed_context = replace(
        evidence.context,
        factors=evidence.context.factors
        + (ContextFactor(ContextFactorKind.TOOL, "late_mutation_tool"),),
    )
    changed_evidence = replace(evidence, context=changed_context)
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="evidence_sha256 does not match exact current EvidenceRecord",
    ):
        validate_pilot_reviewed_materialization_resolution_binding_v1(
            candidate,
            changed_evidence,
            binding,
        )


def test_binding_rejects_semantic_evidence_kind_upgrade(tmp_path):
    candidate, _review, evidence, _receipt, binding = _resolved(tmp_path)
    upgraded = replace(evidence, kind=EvidenceKind.REAL_WORLD_DEMONSTRATION)
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="kind does not match the frozen neutral Pilot 01 mapping",
    ):
        validate_pilot_reviewed_materialization_resolution_binding_v1(
            candidate,
            upgraded,
            binding,
        )


def test_public_receipt_constructor_rejects_non_resolver_issuance_witness(tmp_path):
    _candidate, _review, evidence, receipt, _binding = _resolved(tmp_path)
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="requires a private resolver-issued payload witness",
    ):
        PilotReviewedMaterializationResolutionReceipt(
            materialization_id=receipt.materialization_id,
            candidate_sha256=receipt.candidate_sha256,
            review_id=receipt.review_id,
            review_sha256=receipt.review_sha256,
            evidence_id=evidence.evidence_id,
            evidence_sha256=receipt.evidence_sha256,
            resolved_at=receipt.resolved_at,
            _issuance_witness=object(),
        )


def test_receipt_replace_cannot_rebind_resolver_issuance(tmp_path):
    _candidate, _review, _evidence, receipt, _binding = _resolved(tmp_path)
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="issuance witness does not match the exact current receipt payload",
    ):
        replace(receipt, evidence_sha256="0" * 64)


def test_issuance_witness_replace_requires_fresh_private_issuer_capability(tmp_path):
    _candidate, _review, _evidence, receipt, _binding = _resolved(tmp_path)
    with pytest.raises(
        ValueError,
        match=r"InitVar '_issuer_token' must be specified with replace\(\)",
    ):
        replace(receipt._issuance_witness, payload_sha256="0" * 64)


def test_binding_rechecks_witness_after_low_level_receipt_mutation(tmp_path):
    _candidate, review, _evidence, receipt, _binding = _resolved(tmp_path)
    object.__setattr__(receipt, "evidence_sha256", "0" * 64)
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="issuance witness does not match the exact current receipt payload",
    ):
        PilotReviewedMaterializationResolutionBinding(review, receipt)


def test_lowest_multi_basis_gate_rejects_duplicate_evidence_id(tmp_path):
    root_a = _workspace(
        tmp_path,
        name="identity_a",
        session_id="session_identity_a",
        probe_id="conceptual_explanation",
        capture_id="capture_identity_a",
        minute=1,
    )
    root_b = _workspace(
        tmp_path,
        name="identity_b",
        session_id="session_identity_b",
        probe_id="calculation_work",
        capture_id="capture_identity_b",
        minute=2,
    )
    candidate_a, review_a = _candidate_review(
        root_a,
        capture_id="capture_identity_a",
        materialization_id="materialization_identity_a",
        evidence_id="evidence_identity_shared",
        review_id="review_identity_a",
        proposed_minute=3,
        reviewed_minute=4,
    )
    candidate_b, review_b = _candidate_review(
        root_b,
        capture_id="capture_identity_b",
        materialization_id="materialization_identity_b",
        evidence_id="evidence_identity_shared",
        review_id="review_identity_b",
        proposed_minute=5,
        reviewed_minute=6,
    )
    evidence_a, _ = resolve_reviewed_pilot_evidence_materialization_with_receipt_v1(
        root_a,
        candidate=candidate_a,
        review=review_a,
        resolved_at=T0 + timedelta(minutes=7),
    )
    evidence_b, _ = resolve_reviewed_pilot_evidence_materialization_with_receipt_v1(
        root_b,
        candidate=candidate_b,
        review=review_b,
        resolved_at=T0 + timedelta(minutes=8),
    )
    assert evidence_a is not None and evidence_b is not None

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="duplicate EvidenceId appears in the lower PR10.1 materialized basis",
    ):
        validate_pilot_materialized_evidence_independence_preconditions_v1(
            (
                PilotMaterializedEvidenceBasisEntry(candidate_a, evidence_a),
                PilotMaterializedEvidenceBasisEntry(candidate_b, evidence_b),
            )
        )
