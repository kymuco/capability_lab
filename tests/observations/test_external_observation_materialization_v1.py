from dataclasses import replace
from datetime import timedelta

import pytest

from capability_lab.epistemics import EvidenceKind
from capability_lab.observations import (
    ExternalObservationEvidenceMaterializationId,
    ExternalObservationEvidenceMaterializationReview,
    ExternalObservationEvidenceMaterializationVerdict,
    ExternalObservationEvidenceReviewId,
    ExternalObservationEvidenceReviewerKind,
    ExternalObservationEvidenceReviewerRef,
    ExternalObservationEvidenceResolutionBinding,
    ExternalObservationForm,
    ExternalObservationLedger,
    InvalidExternalObservationEvidenceMaterialization,
    REVIEWED_EXTERNAL_OBSERVATION_TO_EVIDENCE_POLICY_V1,
    admit_external_observation_v1,
    external_observation_evidence_candidate_from_json,
    external_observation_evidence_candidate_to_json,
    external_observation_evidence_id_v1,
    external_observation_evidence_materialization_candidate_sha256_v1,
    external_observation_evidence_review_from_json,
    external_observation_evidence_review_sha256_v1,
    external_observation_evidence_review_to_json,
    propose_external_observation_evidence_materialization_v1,
    resolve_reviewed_external_observation_evidence_materialization_v1,
    validate_external_observation_evidence_resolution_binding_v1,
)

from test_external_observation_v1 import SUBJECT, T0, _observation


def _ledger(observation=None):
    observation = observation or _observation()
    return admit_external_observation_v1(
        ledger=ExternalObservationLedger(subject_ref=SUBJECT),
        observation=observation,
    )


def _candidate(ledger=None, *, materialization_id="mat-1"):
    ledger = ledger or _ledger()
    observation = ledger.observations[0]
    return propose_external_observation_evidence_materialization_v1(
        ledger=ledger,
        observation_id=observation.observation_id,
        materialization_id=ExternalObservationEvidenceMaterializationId(
            materialization_id
        ),
        proposed_at=observation.captured_at + timedelta(seconds=1),
    )


def _review(candidate, *, verdict=ExternalObservationEvidenceMaterializationVerdict.MATERIALIZE,
            review_id="review-1", seconds=1):
    return ExternalObservationEvidenceMaterializationReview(
        review_id=ExternalObservationEvidenceReviewId(review_id),
        materialization_id=candidate.materialization_id,
        candidate_sha256=external_observation_evidence_materialization_candidate_sha256_v1(
            candidate
        ),
        policy_ref=REVIEWED_EXTERNAL_OBSERVATION_TO_EVIDENCE_POLICY_V1,
        reviewer_ref=ExternalObservationEvidenceReviewerRef(
            ExternalObservationEvidenceReviewerKind.HUMAN,
            "human-reviewer",
        ),
        verdict=verdict,
        reviewed_at=candidate.proposed_at + timedelta(seconds=seconds),
        rationale="Human chose whether this exact observation should become neutral evidence.",
    )


def test_candidate_is_source_derived_and_strictly_serializable():
    ledger = _ledger()
    candidate = _candidate(ledger)
    observation = ledger.observations[0]
    assert candidate.observation_id == observation.observation_id
    assert candidate.subject_ref == observation.subject_ref
    assert candidate.source_ref == observation.source_ref
    assert candidate.source_event_id == observation.source_event_id
    assert candidate.materialized_evidence_id == external_observation_evidence_id_v1(observation)
    restored = external_observation_evidence_candidate_from_json(
        external_observation_evidence_candidate_to_json(candidate)
    )
    assert restored == candidate
    assert external_observation_evidence_materialization_candidate_sha256_v1(restored) == external_observation_evidence_materialization_candidate_sha256_v1(candidate)


def test_same_observation_has_one_evidence_id_across_materialization_attempts():
    ledger = _ledger()
    first = _candidate(ledger, materialization_id="mat-1")
    second = _candidate(ledger, materialization_id="mat-2")
    assert first.materialized_evidence_id == second.materialized_evidence_id


def test_unrelated_later_observation_does_not_stale_candidate():
    ledger = _ledger()
    candidate = _candidate(ledger)
    later = _observation(
        observation_id="obs-2", source_event_id="evt-2",
        observed_at=T0 + timedelta(minutes=5),
        captured_at=T0 + timedelta(minutes=5, seconds=1),
    )
    later_ledger = admit_external_observation_v1(ledger=ledger, observation=later)
    review = _review(candidate)
    evidence, receipt = resolve_reviewed_external_observation_evidence_materialization_v1(
        ledger=later_ledger, candidate=candidate, review=review,
    )
    assert evidence is not None
    assert receipt.observation_sha256 == candidate.observation_sha256


def test_materialize_artifact_is_neutral_and_source_visible():
    ledger = _ledger()
    candidate = _candidate(ledger)
    review = _review(candidate)
    evidence, receipt = resolve_reviewed_external_observation_evidence_materialization_v1(
        ledger=ledger, candidate=candidate, review=review,
    )
    observation = ledger.observations[0]
    assert evidence is not None
    assert evidence.evidence_id == candidate.materialized_evidence_id
    assert evidence.kind is EvidenceKind.ARTIFACT
    assert evidence.outcome is None
    assert evidence.observation_started_at == observation.observation_started_at
    assert evidence.observed_at == observation.observed_at
    assert evidence.recorded_at == review.reviewed_at
    assert receipt.resolved_at == review.reviewed_at
    assert evidence.payload_refs == tuple(item.ref for item in observation.payload_refs)
    assert tuple(item.kind.value for item in evidence.context.factors) == ("assistance", "tool")
    assert "origin declared mixed" in evidence.summary
    assert evidence.provenance.sources[0].ref == f"external_observation:{candidate.observation_sha256}"
    assert receipt.evidence_id == evidence.evidence_id
    assert receipt.evidence_sha256 is not None
    validate_external_observation_evidence_resolution_binding_v1(
        ledger=ledger, candidate=candidate, evidence=evidence,
        binding=ExternalObservationEvidenceResolutionBinding(review, receipt),
    )


def test_same_exact_review_resolves_idempotently():
    ledger = _ledger()
    candidate = _candidate(ledger)
    review = _review(candidate)
    first = resolve_reviewed_external_observation_evidence_materialization_v1(
        ledger=ledger, candidate=candidate, review=review,
    )
    second = resolve_reviewed_external_observation_evidence_materialization_v1(
        ledger=ledger, candidate=candidate, review=review,
    )
    assert first == second
    evidence, receipt = first
    assert evidence.recorded_at == review.reviewed_at
    assert receipt.resolved_at == review.reviewed_at


@pytest.mark.parametrize(
    ("form", "expected"),
    [
        (ExternalObservationForm.CONVERSATION, EvidenceKind.CONVERSATION_OBSERVATION),
        (ExternalObservationForm.TEXT, EvidenceKind.OTHER),
        (ExternalObservationForm.EVENT, EvidenceKind.OTHER),
        (ExternalObservationForm.BUNDLE, EvidenceKind.OTHER),
        (ExternalObservationForm.OTHER, EvidenceKind.OTHER),
    ],
)
def test_frozen_neutral_kind_mapping(form, expected):
    observation = _observation(form=form)
    ledger = _ledger(observation)
    candidate = _candidate(ledger)
    review = _review(candidate)
    evidence, _ = resolve_reviewed_external_observation_evidence_materialization_v1(
        ledger=ledger, candidate=candidate, review=review,
    )
    assert evidence.kind is expected
    assert evidence.outcome is None


def test_do_not_materialize_has_terminal_receipt_but_no_evidence():
    ledger = _ledger()
    candidate = _candidate(ledger)
    review = _review(candidate, verdict=ExternalObservationEvidenceMaterializationVerdict.DO_NOT_MATERIALIZE)
    evidence, receipt = resolve_reviewed_external_observation_evidence_materialization_v1(
        ledger=ledger, candidate=candidate, review=review,
    )
    assert evidence is None
    assert receipt.verdict is ExternalObservationEvidenceMaterializationVerdict.DO_NOT_MATERIALIZE
    assert receipt.evidence_id is None
    assert receipt.evidence_sha256 is None
    assert receipt.resolved_at == review.reviewed_at
    validate_external_observation_evidence_resolution_binding_v1(
        ledger=ledger, candidate=candidate, evidence=None,
        binding=ExternalObservationEvidenceResolutionBinding(review, receipt),
    )


def test_review_round_trip_and_digest_are_exact():
    candidate = _candidate()
    review = _review(candidate)
    restored = external_observation_evidence_review_from_json(
        external_observation_evidence_review_to_json(review)
    )
    assert restored == review
    assert external_observation_evidence_review_sha256_v1(restored) == external_observation_evidence_review_sha256_v1(review)


def test_review_must_bind_exact_candidate_digest():
    ledger = _ledger()
    candidate = _candidate(ledger)
    review = replace(_review(candidate), candidate_sha256="f" * 64)
    with pytest.raises(InvalidExternalObservationEvidenceMaterialization, match="candidate_sha256"):
        resolve_reviewed_external_observation_evidence_materialization_v1(
            ledger=ledger, candidate=candidate, review=review,
        )


def test_review_must_not_predate_proposal():
    ledger = _ledger()
    candidate = _candidate(ledger)
    review = _review(candidate)
    object.__setattr__(review, "reviewed_at", candidate.proposed_at - timedelta(seconds=1))
    with pytest.raises(InvalidExternalObservationEvidenceMaterialization, match="reviewed_at"):
        resolve_reviewed_external_observation_evidence_materialization_v1(
            ledger=ledger, candidate=candidate, review=review,
        )


def test_candidate_cannot_resolve_against_ledger_where_observation_is_absent():
    candidate = _candidate(_ledger())
    empty = ExternalObservationLedger(subject_ref=SUBJECT)
    review = _review(candidate)
    with pytest.raises(InvalidExternalObservationEvidenceMaterialization, match="absent or ambiguous"):
        resolve_reviewed_external_observation_evidence_materialization_v1(
            ledger=empty, candidate=candidate, review=review,
        )
