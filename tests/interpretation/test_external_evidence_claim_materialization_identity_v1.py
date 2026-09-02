from datetime import datetime, timezone

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
    admit_external_evidence_claim_interpretation_review_v1,
    materialize_accepted_external_evidence_interpretation_claim_v1,
    propose_external_evidence_claim_interpretation_v1,
    review_external_evidence_claim_interpretation_v1,
)
from capability_lab.observations import REVIEWED_EXTERNAL_OBSERVATION_TO_EVIDENCE_POLICY_V1
from capability_lab.semantics import (
    CapabilityCatalog,
    CapabilityConcept,
    CapabilityId,
    CapabilityNamespace,
)


def _time(hour: int) -> datetime:
    return datetime(2026, 8, 30, hour, 0, tzinfo=timezone.utc)


def _snapshot_and_catalog():
    evidence_id = EvidenceId("external_observation:" + "c" * 64)
    evidence = EvidenceRecord(
        evidence_id=evidence_id,
        subject_ref=CapabilitySubjectRef("subject-identity"),
        kind=EvidenceKind.ARTIFACT,
        summary="Reviewed identity regression evidence.",
        context=EvidenceContext(
            description="Reviewed identity regression evidence.",
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
                    actor_ref=ActorRef("reviewer-identity"),
                    mechanism_ref=str(REVIEWED_EXTERNAL_OBSERVATION_TO_EVIDENCE_POLICY_V1),
                    note="Reviewed PR12.1 materialization.",
                ),
            ),
        ),
        outcome=None,
    )
    snapshot = EpistemicRecordSet(evidence_records=(evidence,))
    catalog = CapabilityCatalog(
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
    return snapshot, catalog


def _accepted(
    snapshot,
    catalog,
    *,
    proposal_id,
    review_id,
    rationale,
    statement=None,
    reviewed_at_hour=13,
    reviewer_ref="human-identity",
):
    candidate = propose_external_evidence_claim_interpretation_v1(
        epistemic_snapshot=snapshot,
        evidence_id=snapshot.evidence_records[0].evidence_id,
        catalog=catalog,
        concept_ref=catalog.concepts[0].ref,
        claim_statement=statement
        or "The subject can reason about bounded signal evidence.",
        claim_scope=ClaimScope(
            "Bounded interpretation of supplied signal evidence.",
            ("bounded_reasoning",),
        ),
        proposer_ref=ExternalEvidenceInterpretationProposerRef(
            ExternalEvidenceInterpretationProposerKind.MODEL,
            "model-identity",
        ),
        proposal_id=ExternalEvidenceInterpretationProposalId(proposal_id),
        proposed_at=_time(12),
        rationale=rationale,
    )
    review = review_external_evidence_claim_interpretation_v1(
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review_id=ExternalEvidenceInterpretationReviewId(review_id),
        reviewer_ref=ExternalEvidenceInterpretationReviewerRef(
            ExternalEvidenceInterpretationReviewerKind.HUMAN,
            reviewer_ref,
        ),
        verdict=ExternalEvidenceInterpretationReviewVerdict.ACCEPT,
        reviewed_at=_time(reviewed_at_hour),
        rationale=f"Accept {review_id}.",
    )
    ledger = admit_external_evidence_claim_interpretation_review_v1(
        review_ledger=ExternalEvidenceInterpretationReviewLedger(),
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review=review,
    )
    result = materialize_accepted_external_evidence_interpretation_claim_v1(
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review_ledger=ledger,
    )
    return candidate, review, result


def test_same_claim_semantics_do_not_fragment_identity_across_non_record_proposal_or_review_metadata():
    snapshot, catalog = _snapshot_and_catalog()
    first_candidate, first_review, first = _accepted(
        snapshot,
        catalog,
        proposal_id="identity-proposal-a",
        review_id="identity-review-a",
        rationale="First proposal path.",
    )
    second_candidate, second_review, second = _accepted(
        snapshot,
        catalog,
        proposal_id="identity-proposal-b",
        review_id="identity-review-b",
        rationale="Second proposal path with different metadata.",
    )

    assert first_candidate != second_candidate
    assert first_review != second_review
    assert first.materialization_receipt.candidate_sha256 != second.materialization_receipt.candidate_sha256
    assert first.materialization_receipt.review_sha256 != second.materialization_receipt.review_sha256
    assert first.claim.claim_id == second.claim.claim_id
    assert first.claim == second.claim


def test_changed_claim_semantics_change_deterministic_claim_identity():
    snapshot, catalog = _snapshot_and_catalog()
    _, _, first = _accepted(
        snapshot,
        catalog,
        proposal_id="identity-proposal-a",
        review_id="identity-review-a",
        rationale="Baseline proposition.",
    )
    _, _, changed = _accepted(
        snapshot,
        catalog,
        proposal_id="identity-proposal-c",
        review_id="identity-review-c",
        rationale="Different proposition.",
        statement="The subject can independently validate bounded signal evidence.",
    )

    assert first.claim.claim_id != changed.claim.claim_id


def test_review_derived_claim_byte_change_changes_record_identity():
    snapshot, catalog = _snapshot_and_catalog()
    _, _, first = _accepted(
        snapshot,
        catalog,
        proposal_id="identity-proposal-time-a",
        review_id="identity-review-time-a",
        rationale="Same proposition, first materialization facts.",
        reviewed_at_hour=13,
        reviewer_ref="human-identity-a",
    )
    _, _, changed = _accepted(
        snapshot,
        catalog,
        proposal_id="identity-proposal-time-b",
        review_id="identity-review-time-b",
        rationale="Same proposition, different materialization facts.",
        reviewed_at_hour=14,
        reviewer_ref="human-identity-b",
    )

    assert first.claim.subject_ref == changed.claim.subject_ref
    assert first.claim.concept_ref == changed.claim.concept_ref
    assert first.claim.statement == changed.claim.statement
    assert first.claim.scope == changed.claim.scope
    assert first.claim.created_at != changed.claim.created_at
    assert first.claim.provenance != changed.claim.provenance
    assert first.claim.claim_id != changed.claim.claim_id
    assert first.claim != changed.claim
