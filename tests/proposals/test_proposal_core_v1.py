from datetime import datetime, timedelta, timezone

import pytest

from capability_lab.epistemics import CapabilitySubjectRef, ClaimScope
from capability_lab.proposals import (
    CapabilityProposal,
    CapabilityProposalId,
    CapabilityProposalSet,
    ClaimCreateCandidate,
    ConceptCandidateSpec,
    ConceptCreateCandidate,
    ConceptMergeCandidate,
    ConceptRevisionCandidate,
    ConceptSplitCandidate,
    InvalidProposalError,
    InvalidProposalSetError,
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
    ConceptLifecycle,
    RelationKind,
    RelationScope,
    RelationStrength,
)


T0 = datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc)
GENERATOR = ProposalGeneratorRef(ProposalMechanismKind.MODEL, "test:model_generator")
GEN_POLICY = ProposalGenerationPolicyRef.parse("core:proposal_generation@1")
REVIEWER = ProposalReviewerRef(ProposalMechanismKind.HUMAN, "test:human_reviewer")
REVIEW_POLICY = ProposalReviewPolicyRef.parse("core:proposal_review@1")


def _concept_spec(key: str) -> ConceptCandidateSpec:
    return ConceptCandidateSpec(
        CapabilityId.parse(f"civilization_bootstrap:{key}"),
        key.replace("_", " ").title(),
        f"Bounded candidate definition for {key}.",
    )


def _proposal(kind, payload, *, proposal_id="proposal_01", subject_ref=None, supersedes=None):
    return CapabilityProposal(
        proposal_id=CapabilityProposalId(proposal_id),
        kind=kind,
        payload=payload,
        subject_ref=subject_ref,
        generator_ref=GENERATOR,
        generation_policy_ref=GEN_POLICY,
        created_at=T0,
        rationale="Inspectable candidate rationale, not proof or authority.",
        supersedes_proposal_id=(
            None if supersedes is None else CapabilityProposalId(supersedes)
        ),
    )


def test_six_candidate_families_are_representable_without_core_record_materialization() -> None:
    proposals = (
        _proposal(
            ProposalKind.CREATE_CONCEPT,
            ConceptCreateCandidate(_concept_spec("candidate_new_concept")),
            proposal_id="proposal_create",
        ),
        _proposal(
            ProposalKind.REVISE_CONCEPT,
            ConceptRevisionCandidate(
                CapabilityConceptRef.parse("civilization_bootstrap:basic_circuits@1"),
                "Basic Circuits Revised Candidate",
                "Candidate revised semantics; no new revision is reserved by this object.",
                proposed_lifecycle=ConceptLifecycle.ACTIVE,
            ),
            proposal_id="proposal_revise",
        ),
        _proposal(
            ProposalKind.SPLIT_CONCEPT,
            ConceptSplitCandidate(
                CapabilityConceptRef.parse("civilization_bootstrap:basic_circuits@1"),
                (_concept_spec("candidate_split_a"), _concept_spec("candidate_split_b")),
            ),
            proposal_id="proposal_split",
        ),
        _proposal(
            ProposalKind.MERGE_CONCEPTS,
            ConceptMergeCandidate(
                (
                    CapabilityConceptRef.parse("civilization_bootstrap:basic_circuits@1"),
                    CapabilityConceptRef.parse("civilization_bootstrap:electrical_measurement@1"),
                ),
                _concept_spec("candidate_merged_concept"),
            ),
            proposal_id="proposal_merge",
        ),
        _proposal(
            ProposalKind.CREATE_RELATION,
            RelationCreateCandidate(
                CapabilityConceptRef.parse("civilization_bootstrap:analog_electronics@1"),
                CapabilityConceptRef.parse("civilization_bootstrap:dimensional_analysis@1"),
                RelationKind.SUPPORTED_BY,
                scope=RelationScope(
                    "conceptual_analysis",
                    "For bounded candidate analysis only.",
                ),
                strength=RelationStrength.MODERATE,
            ),
            proposal_id="proposal_relation",
        ),
        _proposal(
            ProposalKind.CREATE_CLAIM,
            ClaimCreateCandidate(
                CapabilityConceptRef.parse("civilization_bootstrap:basic_circuits@1"),
                "Can reason about a bounded DC resistor circuit.",
                ClaimScope("Bounded low-voltage DC resistor analysis."),
            ),
            proposal_id="proposal_claim",
            subject_ref=CapabilitySubjectRef("subject_01"),
        ),
    )

    assert {item.kind for item in proposals} == set(ProposalKind)
    assert all(type(item.payload).__name__.endswith("Candidate") for item in proposals)


def test_claim_candidate_requires_person_scope() -> None:
    payload = ClaimCreateCandidate(
        CapabilityConceptRef.parse("civilization_bootstrap:basic_circuits@1"),
        "Can reason about a bounded circuit.",
        ClaimScope("Bounded circuit analysis."),
    )

    with pytest.raises(InvalidProposalError, match="person-scoped"):
        _proposal(ProposalKind.CREATE_CLAIM, payload)


def test_recommend_accept_is_review_fact_not_proposal_mutation_or_status() -> None:
    proposal = _proposal(
        ProposalKind.CREATE_CONCEPT,
        ConceptCreateCandidate(_concept_spec("candidate_reviewed_concept")),
    )
    review = ProposalReview(
        review_id=ProposalReviewId("review_01"),
        proposal_id=proposal.proposal_id,
        reviewer_ref=REVIEWER,
        review_policy_ref=REVIEW_POLICY,
        reviewed_at=T0 + timedelta(minutes=5),
        verdict=ProposalReviewVerdict.RECOMMEND_ACCEPT,
        rationale="Recommendation only; governance/materialization is outside PR6.",
    )
    snapshot = CapabilityProposalSet(None, (proposal,), (review,))

    assert snapshot.proposals == (proposal,)
    assert snapshot.reviews == (review,)
    assert not hasattr(proposal, "status")
    assert not hasattr(proposal, "is_approved")


def test_conflicting_reviews_remain_representable_without_vote_or_latest_wins() -> None:
    proposal = _proposal(
        ProposalKind.CREATE_CONCEPT,
        ConceptCreateCandidate(_concept_spec("candidate_contested_concept")),
    )
    reviews = (
        ProposalReview(
            ProposalReviewId("review_accept"),
            proposal.proposal_id,
            REVIEWER,
            REVIEW_POLICY,
            T0 + timedelta(minutes=2),
            ProposalReviewVerdict.RECOMMEND_ACCEPT,
            "One reviewer recommends acceptance.",
        ),
        ProposalReview(
            ProposalReviewId("review_reject"),
            proposal.proposal_id,
            ProposalReviewerRef(ProposalMechanismKind.MODEL, "test:model_reviewer"),
            REVIEW_POLICY,
            T0 + timedelta(minutes=3),
            ProposalReviewVerdict.RECOMMEND_REJECT,
            "Another reviewer recommends rejection.",
        ),
    )

    snapshot = CapabilityProposalSet(None, (proposal,), reviews)

    assert {item.verdict for item in snapshot.reviews} == {
        ProposalReviewVerdict.RECOMMEND_ACCEPT,
        ProposalReviewVerdict.RECOMMEND_REJECT,
    }
    assert not hasattr(snapshot, "accepted_proposals")
    assert not hasattr(snapshot, "approval_count")


def test_proposal_revision_is_new_record_and_lineage_must_be_acyclic() -> None:
    first = _proposal(
        ProposalKind.CREATE_CONCEPT,
        ConceptCreateCandidate(_concept_spec("candidate_lineage_a")),
        proposal_id="proposal_a",
    )
    second = CapabilityProposal(
        proposal_id=CapabilityProposalId("proposal_b"),
        kind=ProposalKind.CREATE_CONCEPT,
        payload=ConceptCreateCandidate(_concept_spec("candidate_lineage_b")),
        subject_ref=None,
        generator_ref=GENERATOR,
        generation_policy_ref=GEN_POLICY,
        created_at=T0 + timedelta(minutes=1),
        rationale="Replacement candidate.",
        supersedes_proposal_id=first.proposal_id,
    )

    snapshot = CapabilityProposalSet(None, (second, first), ())
    assert tuple(item.proposal_id.value for item in snapshot.proposals) == (
        "proposal_a",
        "proposal_b",
    )

    cycle_a = CapabilityProposal(
        CapabilityProposalId("cycle_a"),
        ProposalKind.CREATE_CONCEPT,
        ConceptCreateCandidate(_concept_spec("candidate_cycle_a")),
        None,
        GENERATOR,
        GEN_POLICY,
        T0,
        "Cycle candidate A.",
        supersedes_proposal_id=CapabilityProposalId("cycle_b"),
    )
    cycle_b = CapabilityProposal(
        CapabilityProposalId("cycle_b"),
        ProposalKind.CREATE_CONCEPT,
        ConceptCreateCandidate(_concept_spec("candidate_cycle_b")),
        None,
        GENERATOR,
        GEN_POLICY,
        T0,
        "Cycle candidate B.",
        supersedes_proposal_id=CapabilityProposalId("cycle_a"),
    )

    with pytest.raises(InvalidProposalSetError, match="acyclic"):
        CapabilityProposalSet(None, (cycle_a, cycle_b), ())
