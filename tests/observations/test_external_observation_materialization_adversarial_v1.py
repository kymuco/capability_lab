import ast
import inspect
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from capability_lab.epistemics import EvidenceOutcome, EvidenceOutcomeStatus
from capability_lab.observations import (
    ExternalObservationEvidenceMaterializationId,
    ExternalObservationEvidenceMaterializationReview,
    ExternalObservationEvidenceMaterializationVerdict,
    ExternalObservationEvidenceReviewId,
    ExternalObservationEvidenceReviewerKind,
    ExternalObservationEvidenceReviewerRef,
    ExternalObservationEvidenceResolutionBinding,
    ExternalObservationEvidenceResolutionReceipt,
    InvalidExternalObservationEvidenceMaterialization,
    REVIEWED_EXTERNAL_OBSERVATION_TO_EVIDENCE_POLICY_V1,
    external_observation_evidence_candidate_from_json,
    external_observation_evidence_candidate_to_json,
    external_observation_evidence_materialization_candidate_sha256_v1,
    external_observation_evidence_review_from_json,
    external_observation_evidence_review_to_json,
    propose_external_observation_evidence_materialization_v1,
    resolve_reviewed_external_observation_evidence_materialization_v1,
    validate_external_observation_evidence_resolution_binding_v1,
)

from test_external_observation_materialization_v1 import _candidate, _ledger, _review


def _resolved():
    ledger = _ledger()
    candidate = _candidate(ledger)
    review = _review(candidate)
    evidence, receipt = resolve_reviewed_external_observation_evidence_materialization_v1(
        ledger=ledger, candidate=candidate, review=review,
    )
    return ledger, candidate, review, evidence, receipt


def test_public_proposal_surface_has_no_evidence_semantic_authority():
    names = set(inspect.signature(propose_external_observation_evidence_materialization_v1).parameters)
    forbidden = {
        "evidence_id", "proposed_evidence_id", "kind", "evidence_kind",
        "outcome", "summary", "context", "concept_ref", "claim_id",
        "score", "mastery", "readiness", "permission",
    }
    assert names.isdisjoint(forbidden)


def test_public_resolver_surface_has_no_caller_resolution_time_authority():
    names = set(inspect.signature(resolve_reviewed_external_observation_evidence_materialization_v1).parameters)
    assert names == {"ledger", "candidate", "review"}
    assert "resolved_at" not in names


def test_materialization_core_import_freeze_has_no_claim_state_or_hde_authority():
    import capability_lab.observations.materialization as module
    source_path = Path(inspect.getsourcefile(module))
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imported.setdefault(node.module, []).extend(alias.name for alias in node.names)
    assert set(imported["capability_lab.epistemics"]) == {
        "ActorRef", "CapabilitySubjectRef", "ContextFactor", "ContextFactorKind",
        "EvidenceContext", "EvidenceId", "EvidenceKind", "EvidenceRecord",
        "ProvenanceSource", "ProvenanceSourceKind", "ProvenanceStep", "ProvenanceTrail",
    }
    for forbidden in (
        "CapabilityClaim", "ClaimEvaluation", "PersonalCapabilityState",
        "player_window", "hde_core",
    ):
        assert forbidden not in source


def test_candidate_json_rejects_unknown_field_and_duplicate_key():
    candidate = _candidate()
    payload = external_observation_evidence_candidate_to_json(candidate)
    with pytest.raises(InvalidExternalObservationEvidenceMaterialization):
        external_observation_evidence_candidate_from_json(payload[:-1] + ',"kind":"artifact"}')
    duplicate = payload.replace('"schema_version":1', '"schema_version":1,"schema_version":1', 1)
    with pytest.raises(InvalidExternalObservationEvidenceMaterialization, match="duplicate JSON"):
        external_observation_evidence_candidate_from_json(duplicate)


def test_review_json_rejects_unknown_field_and_duplicate_key():
    review = _review(_candidate())
    payload = external_observation_evidence_review_to_json(review)
    with pytest.raises(InvalidExternalObservationEvidenceMaterialization):
        external_observation_evidence_review_from_json(payload[:-1] + ',"bearing":"supports"}')
    duplicate = payload.replace('"verdict":"MATERIALIZE"', '"verdict":"MATERIALIZE","verdict":"MATERIALIZE"', 1)
    with pytest.raises(InvalidExternalObservationEvidenceMaterialization, match="duplicate JSON"):
        external_observation_evidence_review_from_json(duplicate)


def test_changed_admitted_observation_bytes_reject_old_candidate():
    original_ledger = _ledger()
    candidate = _candidate(original_ledger)
    changed = replace(original_ledger.observations[0], source_event_id="evt-changed")
    changed_ledger = type(original_ledger)(
        subject_ref=original_ledger.subject_ref,
        observations=(changed,),
    )
    review = _review(candidate)
    with pytest.raises(InvalidExternalObservationEvidenceMaterialization):
        resolve_reviewed_external_observation_evidence_materialization_v1(
            ledger=changed_ledger, candidate=candidate, review=review,
        )


def test_corrupted_derived_evidence_id_in_candidate_fails_strictly():
    candidate = _candidate()
    object.__setattr__(candidate.materialized_evidence_id, "value", "bad id with spaces")
    with pytest.raises(
        InvalidExternalObservationEvidenceMaterialization,
        match="candidate failed strict semantic reconstruction",
    ):
        external_observation_evidence_materialization_candidate_sha256_v1(candidate)


def test_string_reviewer_kind_is_not_accepted_as_human():
    with pytest.raises(InvalidExternalObservationEvidenceMaterialization):
        ExternalObservationEvidenceReviewerRef("HUMAN", "person")


def test_tampered_evidence_summary_or_outcome_rejects_binding():
    ledger, candidate, review, evidence, receipt = _resolved()
    binding = ExternalObservationEvidenceResolutionBinding(review, receipt)
    changed_summary = replace(evidence, summary="A capability interpretation.")
    with pytest.raises(InvalidExternalObservationEvidenceMaterialization, match="neutral mapping"):
        validate_external_observation_evidence_resolution_binding_v1(
            ledger=ledger, candidate=candidate, evidence=changed_summary, binding=binding,
        )
    changed_outcome = replace(
        evidence,
        outcome=EvidenceOutcome(EvidenceOutcomeStatus.SUCCESS, "Source said success."),
    )
    with pytest.raises(InvalidExternalObservationEvidenceMaterialization):
        validate_external_observation_evidence_resolution_binding_v1(
            ledger=ledger, candidate=candidate, evidence=changed_outcome, binding=binding,
        )


def test_dataclasses_replace_cannot_rebind_real_receipt():
    _, _, _, _, receipt = _resolved()
    with pytest.raises(InvalidExternalObservationEvidenceMaterialization):
        replace(receipt, evidence_sha256="0" * 64)
    with pytest.raises(InvalidExternalObservationEvidenceMaterialization):
        replace(receipt, verdict=ExternalObservationEvidenceMaterializationVerdict.DO_NOT_MATERIALIZE)


def test_direct_public_receipt_without_private_witness_is_rejected():
    _, candidate, review, evidence, receipt = _resolved()
    with pytest.raises(InvalidExternalObservationEvidenceMaterialization):
        ExternalObservationEvidenceResolutionReceipt(
            materialization_id=candidate.materialization_id,
            candidate_sha256=receipt.candidate_sha256,
            review_id=review.review_id,
            review_sha256=receipt.review_sha256,
            verdict=review.verdict,
            observation_sha256=candidate.observation_sha256,
            evidence_id=evidence.evidence_id,
            evidence_sha256=receipt.evidence_sha256,
            resolved_at=receipt.resolved_at,
            _issuance_witness=None,
        )


def test_do_not_materialize_receipt_cannot_claim_evidence():
    ledger = _ledger()
    candidate = _candidate(ledger)
    review = _review(candidate, verdict=ExternalObservationEvidenceMaterializationVerdict.DO_NOT_MATERIALIZE)
    evidence, receipt = resolve_reviewed_external_observation_evidence_materialization_v1(
        ledger=ledger, candidate=candidate, review=review,
    )
    assert evidence is None
    with pytest.raises(InvalidExternalObservationEvidenceMaterialization):
        replace(receipt, evidence_id=candidate.materialized_evidence_id)


def test_review_for_other_materialization_id_rejects():
    ledger = _ledger()
    candidate = _candidate(ledger)
    review = ExternalObservationEvidenceMaterializationReview(
        review_id=ExternalObservationEvidenceReviewId("review-wrong"),
        materialization_id=ExternalObservationEvidenceMaterializationId("other-mat"),
        candidate_sha256=external_observation_evidence_materialization_candidate_sha256_v1(candidate),
        policy_ref=REVIEWED_EXTERNAL_OBSERVATION_TO_EVIDENCE_POLICY_V1,
        reviewer_ref=ExternalObservationEvidenceReviewerRef(
            ExternalObservationEvidenceReviewerKind.HUMAN, "human-reviewer"
        ),
        verdict=ExternalObservationEvidenceMaterializationVerdict.MATERIALIZE,
        reviewed_at=candidate.proposed_at + timedelta(seconds=1),
        rationale="Wrong slot on purpose.",
    )
    with pytest.raises(InvalidExternalObservationEvidenceMaterialization, match="materialization_id"):
        resolve_reviewed_external_observation_evidence_materialization_v1(
            ledger=ledger, candidate=candidate, review=review,
        )
