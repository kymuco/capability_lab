from datetime import datetime, timedelta, timezone

import capability_lab

from capability_lab.domains import build_civilization_bootstrap_seed_catalog_v0
from capability_lab.epistemics import (
    CapabilitySubjectRef,
    ClaimScope,
    EpistemicRecordSet,
    EvidenceContext,
    EvidenceId,
    EvidenceKind,
    EvidenceRecord,
    ProvenanceSource,
    ProvenanceSourceKind,
    ProvenanceTrail,
)
from capability_lab.proposals import (
    CapabilityProposal,
    CapabilityProposalId,
    CapabilityProposalSet,
    ClaimCreateCandidate,
    ProposalBasisKind,
    ProposalBasisRef,
    ProposalGenerationPolicyRef,
    ProposalGeneratorRef,
    ProposalKind,
    ProposalMechanismKind,
    ProposalReview,
    ProposalReviewId,
    ProposalReviewPolicyRef,
    ProposalReviewerRef,
    ProposalReviewVerdict,
    RelationCreateCandidate,
)
from capability_lab.semantics import (
    CapabilityConceptRef,
    RelationKind,
    RelationScope,
    RelationStrength,
)


T0 = datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc)
MODEL = ProposalGeneratorRef(ProposalMechanismKind.MODEL, "test:model_pr6_smoke")
GEN_POLICY = ProposalGenerationPolicyRef.parse("civilization_bootstrap:ontology_proposal@1")
HUMAN = ProposalReviewerRef(ProposalMechanismKind.HUMAN, "test:human_pr6_reviewer")
REVIEW_POLICY = ProposalReviewPolicyRef.parse("civilization_bootstrap:proposal_review@1")


def _review(proposal: CapabilityProposal, review_id: str) -> ProposalReview:
    return ProposalReview(
        ProposalReviewId(review_id),
        proposal.proposal_id,
        HUMAN,
        REVIEW_POLICY,
        T0 + timedelta(minutes=5),
        ProposalReviewVerdict.RECOMMEND_ACCEPT,
        "Recommendation is inspectable but cannot materialize an accepted object in PR6.",
    )


def test_model_ontology_proposal_and_recommend_accept_do_not_mutate_pr5_catalog() -> None:
    catalog = build_civilization_bootstrap_seed_catalog_v0()
    before = catalog.to_json()
    proposal = CapabilityProposal(
        CapabilityProposalId("proposal_pr6_relation"),
        ProposalKind.CREATE_RELATION,
        RelationCreateCandidate(
            CapabilityConceptRef.parse("civilization_bootstrap:analog_electronics@1"),
            CapabilityConceptRef.parse("civilization_bootstrap:dimensional_analysis@1"),
            RelationKind.SUPPORTED_BY,
            scope=RelationScope(
                "conceptual_analysis",
                "Candidate scoped support assertion for review only.",
            ),
            strength=RelationStrength.MODERATE,
        ),
        None,
        MODEL,
        GEN_POLICY,
        T0,
        "The model suggests an additional direct support relation for review.",
        basis_refs=(
            ProposalBasisRef(
                ProposalBasisKind.CAPABILITY_CONCEPT,
                "civilization_bootstrap:analog_electronics@1",
            ),
            ProposalBasisRef(
                ProposalBasisKind.CAPABILITY_CONCEPT,
                "civilization_bootstrap:dimensional_analysis@1",
            ),
        ),
    )
    snapshot = CapabilityProposalSet(None, (proposal,), (_review(proposal, "review_pr6_relation"),))

    snapshot.validate_against_capability_catalog(catalog)

    assert catalog.to_json() == before
    assert all(
        not (
            relation.source_id.key == "analog_electronics"
            and relation.kind is RelationKind.SUPPORTED_BY
            and relation.target_id.key == "dimensional_analysis"
        )
        for relation in catalog.relations
    )


def test_model_claim_proposal_with_private_evidence_does_not_create_claim_evaluation_or_state() -> None:
    catalog = build_civilization_bootstrap_seed_catalog_v0()
    subject = CapabilitySubjectRef("subject_pr6_smoke")
    evidence = EvidenceRecord(
        evidence_id=EvidenceId("evidence_pr6_smoke"),
        subject_ref=subject,
        kind=EvidenceKind.PROJECT,
        summary="Completed a bounded DC resistor analysis exercise.",
        context=EvidenceContext("Private low-voltage project context."),
        observed_at=T0 - timedelta(minutes=10),
        recorded_at=T0 - timedelta(minutes=9),
        provenance=ProvenanceTrail(
            (ProvenanceSource(ProvenanceSourceKind.ACTOR, "test:pr6_observer"),)
        ),
    )
    records = EpistemicRecordSet(evidence_records=(evidence,))
    proposal = CapabilityProposal(
        CapabilityProposalId("proposal_pr6_claim"),
        ProposalKind.CREATE_CLAIM,
        ClaimCreateCandidate(
            CapabilityConceptRef.parse("civilization_bootstrap:basic_circuits@1"),
            "Can analyze a bounded DC resistor circuit under stated component assumptions.",
            ClaimScope("Low-voltage DC resistor analysis with stated topology and values."),
        ),
        subject,
        MODEL,
        ProposalGenerationPolicyRef.parse("civilization_bootstrap:claim_proposal@1"),
        T0,
        "The private observation motivates a candidate proposition, not an accepted claim.",
        basis_refs=(
            ProposalBasisRef(ProposalBasisKind.EVIDENCE_RECORD, str(evidence.evidence_id)),
        ),
    )
    snapshot = CapabilityProposalSet(subject, (proposal,), (_review(proposal, "review_pr6_claim"),))

    snapshot.validate_against_capability_catalog(catalog)
    snapshot.validate_against_epistemics(records)

    assert records.claims == ()
    assert records.evaluations == ()
    assert not hasattr(snapshot, "personal_capability_state")
    assert not hasattr(snapshot, "accepted_claims")


def test_public_api_exposes_no_implicit_materialization_or_authority_shortcut() -> None:
    forbidden = {
        "apply_proposal",
        "accept_proposal",
        "approve_proposal",
        "materialize_proposal",
        "promote_proposal",
        "proposal_to_claim",
        "proposal_to_concept",
        "auto_accept",
        "authority_score",
        "approval_count",
        "acceptance_score",
    }

    assert forbidden.isdisjoint(set(capability_lab.__all__))
    assert all(not hasattr(capability_lab, name) for name in forbidden)
