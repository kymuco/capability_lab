from dataclasses import replace
from datetime import datetime, timezone

import pytest

from capability_lab.epistemics import (
    ActorRef,
    CapabilitySubjectRef,
    ClaimScope,
    EpistemicRecordSet,
    EvidenceContext,
    EvidenceId,
    EvidenceKind,
    EvidenceRecord,
    ProvenanceSource,
    ProvenanceSourceKind,
    ProvenanceStep,
    ProvenanceTrail,
)
from capability_lab.interpretation import (
    ExternalEvidenceInterpretationProposalId,
    ExternalEvidenceInterpretationProposerKind,
    ExternalEvidenceInterpretationProposerRef,
    ExternalEvidenceInterpretationReviewId,
    ExternalEvidenceInterpretationReviewLedger,
    ExternalEvidenceInterpretationReviewerKind,
    ExternalEvidenceInterpretationReviewerRef,
    ExternalEvidenceInterpretationReviewVerdict,
    InvalidExternalEvidenceInterpretation,
    admit_external_evidence_claim_interpretation_review_v1,
    external_evidence_claim_interpretation_review_ledger_from_json,
    external_evidence_claim_interpretation_review_ledger_sha256_v1,
    external_evidence_claim_interpretation_review_ledger_to_json,
    propose_external_evidence_claim_interpretation_v1,
    require_accepted_external_evidence_claim_interpretation_review_v1,
    resolve_external_evidence_claim_interpretation_terminal_review_v1,
    review_external_evidence_claim_interpretation_v1,
    validate_external_evidence_interpretation_review_ledger_successor_v1,
)
from capability_lab.observations import REVIEWED_EXTERNAL_OBSERVATION_TO_EVIDENCE_POLICY_V1
from capability_lab.semantics import (
    CapabilityCatalog,
    CapabilityConcept,
    CapabilityId,
    CapabilityNamespace,
)


def _time(hour: int) -> datetime:
    return datetime(2026, 8, 29, hour, 0, tzinfo=timezone.utc)


def _catalog() -> CapabilityCatalog:
    return CapabilityCatalog(
        namespaces=(
            CapabilityNamespace(
                namespace_id="research",
                display_name="Research",
                description="Research capabilities.",
            ),
        ),
        concepts=(
            CapabilityConcept(
                capability_id=CapabilityId.parse("research:signal_reasoning"),
                name="Signal reasoning",
                definition="Reason about structured technical signals and evidence.",
            ),
        ),
    )


def _external_evidence() -> EvidenceRecord:
    evidence_id = EvidenceId("external_observation:" + "a" * 64)
    return EvidenceRecord(
        evidence_id=evidence_id,
        subject_ref=CapabilitySubjectRef("subject-1"),
        kind=EvidenceKind.ARTIFACT,
        summary="Exact reviewed external observation.",
        context=EvidenceContext(
            description="Reviewed external observation.",
            scope_tags=("external_observation",),
        ),
        observed_at=_time(10),
        recorded_at=_time(11),
        provenance=ProvenanceTrail(
            sources=(
                ProvenanceSource(ProvenanceSourceKind.EXTERNAL_RECORD, str(evidence_id)),
            ),
            steps=(
                ProvenanceStep(
                    operation_key="external_observation_materialize",
                    occurred_at=_time(11),
                    actor_ref=ActorRef("reviewer-1"),
                    mechanism_ref=str(REVIEWED_EXTERNAL_OBSERVATION_TO_EVIDENCE_POLICY_V1),
                    note="Reviewed PR12.1 materialization.",
                ),
            ),
        ),
        outcome=None,
        payload_refs=("artifact-1",),
    )


def _basis():
    evidence = _external_evidence()
    snapshot = EpistemicRecordSet(evidence_records=(evidence,))
    catalog = _catalog()
    candidate = propose_external_evidence_claim_interpretation_v1(
        epistemic_snapshot=snapshot,
        evidence_id=evidence.evidence_id,
        catalog=catalog,
        concept_ref=catalog.concepts[0].ref,
        claim_statement="The subject can reason about bounded signal evidence.",
        claim_scope=ClaimScope(
            "Bounded interpretation of supplied signal evidence.",
            ("bounded_reasoning",),
        ),
        proposer_ref=ExternalEvidenceInterpretationProposerRef(
            ExternalEvidenceInterpretationProposerKind.MODEL,
            "model-proposer-1",
        ),
        proposal_id=ExternalEvidenceInterpretationProposalId("interpretation-1"),
        proposed_at=_time(12),
        rationale="The artifact appears relevant to the exact capability scope.",
    )
    return snapshot, catalog, candidate


def _review(candidate, snapshot, catalog, *, review_id: str, verdict):
    return review_external_evidence_claim_interpretation_v1(
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review_id=ExternalEvidenceInterpretationReviewId(review_id),
        reviewer_ref=ExternalEvidenceInterpretationReviewerRef(
            ExternalEvidenceInterpretationReviewerKind.HUMAN,
            "human-reviewer-1",
        ),
        verdict=verdict,
        reviewed_at=_time(13),
        rationale=f"Terminal human decision: {verdict.value}.",
    )


def test_exact_review_admission_is_idempotent():
    snapshot, catalog, candidate = _basis()
    review = _review(
        candidate,
        snapshot,
        catalog,
        review_id="review-1",
        verdict=ExternalEvidenceInterpretationReviewVerdict.ACCEPT,
    )
    empty = ExternalEvidenceInterpretationReviewLedger()
    admitted = admit_external_evidence_claim_interpretation_review_v1(
        review_ledger=empty,
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review=review,
    )
    replayed = admit_external_evidence_claim_interpretation_review_v1(
        review_ledger=admitted,
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review=review,
    )

    assert admitted.reviews == (review,)
    assert replayed is admitted


def test_conflicting_second_terminal_verdict_for_same_proposal_fails_closed():
    snapshot, catalog, candidate = _basis()
    accepted = _review(
        candidate,
        snapshot,
        catalog,
        review_id="review-accept",
        verdict=ExternalEvidenceInterpretationReviewVerdict.ACCEPT,
    )
    rejected = _review(
        candidate,
        snapshot,
        catalog,
        review_id="review-reject",
        verdict=ExternalEvidenceInterpretationReviewVerdict.REJECT,
    )
    ledger = admit_external_evidence_claim_interpretation_review_v1(
        review_ledger=ExternalEvidenceInterpretationReviewLedger(),
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review=accepted,
    )

    with pytest.raises(
        InvalidExternalEvidenceInterpretation,
        match="different terminal review",
    ):
        admit_external_evidence_claim_interpretation_review_v1(
            review_ledger=ledger,
            epistemic_snapshot=snapshot,
            catalog=catalog,
            candidate=candidate,
            review=rejected,
        )


def test_direct_ledger_construction_rejects_two_reviews_for_one_proposal():
    snapshot, catalog, candidate = _basis()
    first = _review(
        candidate,
        snapshot,
        catalog,
        review_id="review-a",
        verdict=ExternalEvidenceInterpretationReviewVerdict.ACCEPT,
    )
    second = _review(
        candidate,
        snapshot,
        catalog,
        review_id="review-b",
        verdict=ExternalEvidenceInterpretationReviewVerdict.REJECT,
    )

    with pytest.raises(
        InvalidExternalEvidenceInterpretation,
        match="already has a terminal review",
    ):
        ExternalEvidenceInterpretationReviewLedger(reviews=(first, second))


def test_review_id_cannot_be_rebound_to_another_proposal():
    snapshot, catalog, first_candidate = _basis()
    second_candidate = replace(
        first_candidate,
        proposal_id=ExternalEvidenceInterpretationProposalId("interpretation-2"),
        rationale="Second independently identified proposal.",
    )
    first = _review(
        first_candidate,
        snapshot,
        catalog,
        review_id="shared-review-id",
        verdict=ExternalEvidenceInterpretationReviewVerdict.ACCEPT,
    )
    second = _review(
        second_candidate,
        snapshot,
        catalog,
        review_id="shared-review-id",
        verdict=ExternalEvidenceInterpretationReviewVerdict.ACCEPT,
    )
    ledger = admit_external_evidence_claim_interpretation_review_v1(
        review_ledger=ExternalEvidenceInterpretationReviewLedger(),
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=first_candidate,
        review=first,
    )

    with pytest.raises(
        InvalidExternalEvidenceInterpretation,
        match="review_id is already bound",
    ):
        admit_external_evidence_claim_interpretation_review_v1(
            review_ledger=ledger,
            epistemic_snapshot=snapshot,
            catalog=catalog,
            candidate=second_candidate,
            review=second,
        )


def test_review_ledger_successor_is_append_only_exact_prefix():
    snapshot, catalog, first_candidate = _basis()
    second_candidate = replace(
        first_candidate,
        proposal_id=ExternalEvidenceInterpretationProposalId("interpretation-2"),
        rationale="Second independently identified proposal.",
    )
    first = _review(
        first_candidate,
        snapshot,
        catalog,
        review_id="review-1",
        verdict=ExternalEvidenceInterpretationReviewVerdict.ACCEPT,
    )
    second = _review(
        second_candidate,
        snapshot,
        catalog,
        review_id="review-2",
        verdict=ExternalEvidenceInterpretationReviewVerdict.REJECT,
    )
    first_ledger = admit_external_evidence_claim_interpretation_review_v1(
        review_ledger=ExternalEvidenceInterpretationReviewLedger(),
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=first_candidate,
        review=first,
    )
    second_ledger = admit_external_evidence_claim_interpretation_review_v1(
        review_ledger=first_ledger,
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=second_candidate,
        review=second,
    )

    validate_external_evidence_interpretation_review_ledger_successor_v1(
        first_ledger,
        second_ledger,
    )

    with pytest.raises(
        InvalidExternalEvidenceInterpretation,
        match="exact prior review prefix",
    ):
        validate_external_evidence_interpretation_review_ledger_successor_v1(
            first_ledger,
            ExternalEvidenceInterpretationReviewLedger(reviews=(second, first)),
        )

    with pytest.raises(
        InvalidExternalEvidenceInterpretation,
        match="may not remove",
    ):
        validate_external_evidence_interpretation_review_ledger_successor_v1(
            second_ledger,
            first_ledger,
        )


def test_terminal_resolution_requires_review_to_be_admitted_in_ledger():
    snapshot, catalog, candidate = _basis()
    review = _review(
        candidate,
        snapshot,
        catalog,
        review_id="review-1",
        verdict=ExternalEvidenceInterpretationReviewVerdict.ACCEPT,
    )

    with pytest.raises(
        InvalidExternalEvidenceInterpretation,
        match="no exact terminal review",
    ):
        resolve_external_evidence_claim_interpretation_terminal_review_v1(
            review_ledger=ExternalEvidenceInterpretationReviewLedger(),
            epistemic_snapshot=snapshot,
            catalog=catalog,
            candidate=candidate,
        )

    ledger = admit_external_evidence_claim_interpretation_review_v1(
        review_ledger=ExternalEvidenceInterpretationReviewLedger(),
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review=review,
    )
    assert (
        resolve_external_evidence_claim_interpretation_terminal_review_v1(
            review_ledger=ledger,
            epistemic_snapshot=snapshot,
            catalog=catalog,
            candidate=candidate,
        )
        == review
    )


def test_terminal_resolution_rejects_malformed_candidate_with_governance_error():
    snapshot, catalog, _ = _basis()

    with pytest.raises(
        InvalidExternalEvidenceInterpretation,
        match="candidate must use exact ExternalEvidenceClaimInterpretationCandidate",
    ):
        resolve_external_evidence_claim_interpretation_terminal_review_v1(
            review_ledger=ExternalEvidenceInterpretationReviewLedger(),
            epistemic_snapshot=snapshot,
            catalog=catalog,
            candidate=object(),
        )


def test_accepted_requirement_rejects_terminal_reject_verdict():
    snapshot, catalog, candidate = _basis()
    rejected = _review(
        candidate,
        snapshot,
        catalog,
        review_id="review-reject",
        verdict=ExternalEvidenceInterpretationReviewVerdict.REJECT,
    )
    ledger = admit_external_evidence_claim_interpretation_review_v1(
        review_ledger=ExternalEvidenceInterpretationReviewLedger(),
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review=rejected,
    )

    with pytest.raises(
        InvalidExternalEvidenceInterpretation,
        match="REJECT, not ACCEPT",
    ):
        require_accepted_external_evidence_claim_interpretation_review_v1(
            review_ledger=ledger,
            epistemic_snapshot=snapshot,
            catalog=catalog,
            candidate=candidate,
        )


def test_accepted_requirement_returns_exact_admitted_accept_review():
    snapshot, catalog, candidate = _basis()
    accepted = _review(
        candidate,
        snapshot,
        catalog,
        review_id="review-accept",
        verdict=ExternalEvidenceInterpretationReviewVerdict.ACCEPT,
    )
    ledger = admit_external_evidence_claim_interpretation_review_v1(
        review_ledger=ExternalEvidenceInterpretationReviewLedger(),
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review=accepted,
    )

    assert (
        require_accepted_external_evidence_claim_interpretation_review_v1(
            review_ledger=ledger,
            epistemic_snapshot=snapshot,
            catalog=catalog,
            candidate=candidate,
        )
        == accepted
    )


def test_review_ledger_serialization_and_digest_are_deterministic():
    snapshot, catalog, candidate = _basis()
    review = _review(
        candidate,
        snapshot,
        catalog,
        review_id="review-1",
        verdict=ExternalEvidenceInterpretationReviewVerdict.ACCEPT,
    )
    ledger = admit_external_evidence_claim_interpretation_review_v1(
        review_ledger=ExternalEvidenceInterpretationReviewLedger(),
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review=review,
    )
    payload = external_evidence_claim_interpretation_review_ledger_to_json(ledger)
    restored = external_evidence_claim_interpretation_review_ledger_from_json(payload)

    assert restored == ledger
    assert payload == external_evidence_claim_interpretation_review_ledger_to_json(restored)
    assert (
        external_evidence_claim_interpretation_review_ledger_sha256_v1(ledger)
        == external_evidence_claim_interpretation_review_ledger_sha256_v1(restored)
    )
