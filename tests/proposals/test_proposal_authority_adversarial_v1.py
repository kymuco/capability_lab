from datetime import datetime, timezone

import pytest

from capability_lab.domains import build_civilization_bootstrap_seed_catalog_v0
from capability_lab.epistemics import (
    CapabilitySubjectRef,
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
    ConceptCandidateSpec,
    ConceptCreateCandidate,
    InvalidProposalSetError,
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
    CapabilityId,
    RelationKind,
    RelationScope,
    RelationStrength,
)


T0 = datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc)
GENERATOR = ProposalGeneratorRef(ProposalMechanismKind.MODEL, "test:model_adversarial")
GEN_POLICY = ProposalGenerationPolicyRef.parse("core:proposal_generation@1")
REVIEWER = ProposalReviewerRef(ProposalMechanismKind.HUMAN, "test:reviewer_adversarial")
REVIEW_POLICY = ProposalReviewPolicyRef.parse("core:proposal_review@1")
SUBJECT = CapabilitySubjectRef("subject_adversarial")


def _concept_spec(capability_id: str) -> ConceptCandidateSpec:
    return ConceptCandidateSpec(
        CapabilityId.parse(capability_id),
        "Candidate Concept",
        "Bounded candidate semantics for adversarial proposal-authority review.",
    )


def _proposal(
    proposal_id: str,
    payload,
    *,
    subject_ref=None,
    supersedes=None,
    basis_refs=(),
) -> CapabilityProposal:
    return CapabilityProposal(
        proposal_id=CapabilityProposalId(proposal_id),
        kind=(
            ProposalKind.CREATE_RELATION
            if isinstance(payload, RelationCreateCandidate)
            else ProposalKind.CREATE_CONCEPT
        ),
        payload=payload,
        subject_ref=subject_ref,
        generator_ref=GENERATOR,
        generation_policy_ref=GEN_POLICY,
        created_at=T0,
        rationale="Candidate rationale remains non-authoritative.",
        basis_refs=basis_refs,
        supersedes_proposal_id=(
            None if supersedes is None else CapabilityProposalId(supersedes)
        ),
    )


def _review(review_id: str, proposal_id: str, verdict: ProposalReviewVerdict) -> ProposalReview:
    return ProposalReview(
        review_id=ProposalReviewId(review_id),
        proposal_id=CapabilityProposalId(proposal_id),
        reviewer_ref=REVIEWER,
        review_policy_ref=REVIEW_POLICY,
        reviewed_at=T0,
        verdict=verdict,
        rationale="Review fact only; same timestamp does not create authority or status.",
    )


def _evidence(evidence_id: str) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=EvidenceId(evidence_id),
        subject_ref=SUBJECT,
        kind=EvidenceKind.PROJECT,
        summary="Private project observation.",
        context=EvidenceContext("Private adversarial-test context."),
        observed_at=T0,
        recorded_at=T0,
        provenance=ProvenanceTrail(
            (ProvenanceSource(ProvenanceSourceKind.ACTOR, "test:observer"),)
        ),
    )


def test_create_concept_cannot_implicitly_create_unknown_namespace() -> None:
    proposal = _proposal(
        "proposal_unknown_namespace",
        ConceptCreateCandidate(_concept_spec("unregistered_namespace:candidate")),
    )
    snapshot = CapabilityProposalSet(None, (proposal,), ())

    with pytest.raises(InvalidProposalSetError, match="does not create namespaces"):
        snapshot.validate_against_capability_catalog(
            build_civilization_bootstrap_seed_catalog_v0()
        )


def test_same_suggested_id_across_independent_proposals_does_not_reserve_identity() -> None:
    first = _proposal(
        "proposal_same_id_a",
        ConceptCreateCandidate(
            _concept_spec("civilization_bootstrap:candidate_unreserved_identity")
        ),
    )
    second = _proposal(
        "proposal_same_id_b",
        ConceptCreateCandidate(
            _concept_spec("civilization_bootstrap:candidate_unreserved_identity")
        ),
    )
    snapshot = CapabilityProposalSet(None, (first, second), ())

    snapshot.validate_against_capability_catalog(
        build_civilization_bootstrap_seed_catalog_v0()
    )

    assert len(snapshot.proposals) == 2
    assert not hasattr(snapshot, "reserved_capability_ids")


def test_relation_candidate_cannot_launder_private_internal_record_into_provenance_refs() -> None:
    evidence = _evidence("evidence_private_relation_basis")
    records = EpistemicRecordSet(evidence_records=(evidence,))
    proposal = _proposal(
        "proposal_relation_private_launder",
        RelationCreateCandidate(
            CapabilityConceptRef.parse("civilization_bootstrap:analog_electronics@1"),
            CapabilityConceptRef.parse("civilization_bootstrap:dimensional_analysis@1"),
            RelationKind.SUPPORTED_BY,
            scope=RelationScope(
                "conceptual_analysis",
                "Candidate relation for adversarial provenance-boundary review.",
            ),
            strength=RelationStrength.MODERATE,
            provenance_refs=(str(evidence.evidence_id),),
        ),
        subject_ref=SUBJECT,
        basis_refs=(
            ProposalBasisRef(
                ProposalBasisKind.EVIDENCE_RECORD,
                str(evidence.evidence_id),
            ),
        ),
    )
    snapshot = CapabilityProposalSet(SUBJECT, (proposal,), ())

    with pytest.raises(InvalidProposalSetError, match="typed proposal basis refs"):
        snapshot.validate_against_epistemics(records)


def test_same_timestamp_supersession_and_review_use_explicit_links_not_latest_time_authority() -> None:
    first = _proposal(
        "proposal_parent",
        ConceptCreateCandidate(_concept_spec("civilization_bootstrap:candidate_parent")),
    )
    second = _proposal(
        "proposal_child",
        ConceptCreateCandidate(_concept_spec("civilization_bootstrap:candidate_child")),
        supersedes="proposal_parent",
    )
    review = _review(
        "review_parent_accept",
        "proposal_parent",
        ProposalReviewVerdict.RECOMMEND_ACCEPT,
    )

    snapshot = CapabilityProposalSet(None, (second, first), (review,))

    assert snapshot.proposals[0].proposal_id == CapabilityProposalId("proposal_child")
    assert snapshot.proposals[1].proposal_id == CapabilityProposalId("proposal_parent")
    assert snapshot.reviews == (review,)
    assert review.proposal_id == first.proposal_id
    assert review.proposal_id != second.proposal_id
    assert not hasattr(snapshot, "latest_review")
    assert not hasattr(snapshot, "accepted_proposal")


def test_review_of_superseded_proposal_does_not_transfer_to_successor() -> None:
    first = _proposal(
        "proposal_old",
        ConceptCreateCandidate(_concept_spec("civilization_bootstrap:candidate_old")),
    )
    second = _proposal(
        "proposal_new",
        ConceptCreateCandidate(_concept_spec("civilization_bootstrap:candidate_new")),
        supersedes="proposal_old",
    )
    reviews = (
        _review(
            "review_old_accept",
            "proposal_old",
            ProposalReviewVerdict.RECOMMEND_ACCEPT,
        ),
        _review(
            "review_new_revise",
            "proposal_new",
            ProposalReviewVerdict.REQUEST_REVISION,
        ),
    )

    snapshot = CapabilityProposalSet(None, (first, second), reviews)

    by_proposal = {
        proposal_id: tuple(
            review.verdict
            for review in snapshot.reviews
            if review.proposal_id == CapabilityProposalId(proposal_id)
        )
        for proposal_id in ("proposal_old", "proposal_new")
    }
    assert by_proposal["proposal_old"] == (ProposalReviewVerdict.RECOMMEND_ACCEPT,)
    assert by_proposal["proposal_new"] == (ProposalReviewVerdict.REQUEST_REVISION,)
    assert not hasattr(snapshot, "effective_verdict")
    assert not hasattr(snapshot, "current_status")
