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


def _external_evidence(hex_char: str, summary: str) -> EvidenceRecord:
    evidence_id = EvidenceId("external_observation:" + hex_char * 64)
    return EvidenceRecord(
        evidence_id=evidence_id,
        subject_ref=CapabilitySubjectRef("subject-cross-evidence"),
        kind=EvidenceKind.ARTIFACT,
        summary=summary,
        context=EvidenceContext(
            description=f"Reviewed source for {summary}",
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
                    actor_ref=ActorRef("reviewer-cross-evidence"),
                    mechanism_ref=str(REVIEWED_EXTERNAL_OBSERVATION_TO_EVIDENCE_POLICY_V1),
                    note="Reviewed PR12.1 materialization.",
                ),
            ),
        ),
        outcome=None,
    )


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


def _materialize(snapshot, catalog, evidence_id, *, proposal_id, review_id):
    candidate = propose_external_evidence_claim_interpretation_v1(
        epistemic_snapshot=snapshot,
        evidence_id=evidence_id,
        catalog=catalog,
        concept_ref=catalog.concepts[0].ref,
        claim_statement="The subject can reason about bounded signal evidence.",
        claim_scope=ClaimScope(
            "Bounded interpretation of supplied signal evidence.",
            ("bounded_reasoning",),
        ),
        proposer_ref=ExternalEvidenceInterpretationProposerRef(
            ExternalEvidenceInterpretationProposerKind.MODEL,
            "model-cross-evidence",
        ),
        proposal_id=ExternalEvidenceInterpretationProposalId(proposal_id),
        proposed_at=_time(12),
        rationale=f"Interpret exact evidence {evidence_id}.",
    )
    review = review_external_evidence_claim_interpretation_v1(
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review_id=ExternalEvidenceInterpretationReviewId(review_id),
        reviewer_ref=ExternalEvidenceInterpretationReviewerRef(
            ExternalEvidenceInterpretationReviewerKind.HUMAN,
            "human-cross-evidence",
        ),
        verdict=ExternalEvidenceInterpretationReviewVerdict.ACCEPT,
        reviewed_at=_time(13),
        rationale=f"Accept exact proposal {proposal_id}.",
    )
    ledger = admit_external_evidence_claim_interpretation_review_v1(
        review_ledger=ExternalEvidenceInterpretationReviewLedger(),
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review=review,
    )
    return materialize_accepted_external_evidence_interpretation_claim_v1(
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review_ledger=ledger,
    )


def test_distinct_evidence_for_same_proposition_does_not_fragment_claim_identity():
    first_evidence = _external_evidence("d", "First independently retained artifact.")
    second_evidence = _external_evidence("e", "Second independently retained artifact.")
    snapshot = EpistemicRecordSet(
        evidence_records=(first_evidence, second_evidence),
    )
    catalog = _catalog()

    first = _materialize(
        snapshot,
        catalog,
        first_evidence.evidence_id,
        proposal_id="cross-evidence-proposal-a",
        review_id="cross-evidence-review-a",
    )
    second = _materialize(
        snapshot,
        catalog,
        second_evidence.evidence_id,
        proposal_id="cross-evidence-proposal-b",
        review_id="cross-evidence-review-b",
    )

    assert first.materialization_receipt.candidate_sha256 != second.materialization_receipt.candidate_sha256
    assert first.materialization_receipt.review_sha256 != second.materialization_receipt.review_sha256
    assert first.claim.claim_id == second.claim.claim_id
    assert first.claim.subject_ref == second.claim.subject_ref
    assert first.claim.concept_ref == second.claim.concept_ref
    assert first.claim.statement == second.claim.statement
    assert first.claim.scope == second.claim.scope
