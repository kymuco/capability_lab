from dataclasses import fields
from datetime import datetime, timedelta, timezone
import json

import pytest

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
    InvalidProposalError,
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
)
from capability_lab.semantics import CapabilityId


T0 = datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc)
GENERATOR = ProposalGeneratorRef(ProposalMechanismKind.MODEL, "test:model_second_adversarial")
GEN_POLICY = ProposalGenerationPolicyRef.parse("core:proposal_generation@1")
REVIEWER = ProposalReviewerRef(ProposalMechanismKind.HUMAN, "test:reviewer_second_adversarial")
REVIEW_POLICY = ProposalReviewPolicyRef.parse("core:proposal_review@1")
SUBJECT = CapabilitySubjectRef("subject_second_adversarial")


def _proposal(
    *,
    proposal_id: str = "proposal_second_adversarial",
    key: str = "candidate_second_adversarial",
    basis_refs=(),
    subject_ref=None,
) -> CapabilityProposal:
    return CapabilityProposal(
        proposal_id=CapabilityProposalId(proposal_id),
        kind=ProposalKind.CREATE_CONCEPT,
        payload=ConceptCreateCandidate(
            ConceptCandidateSpec(
                CapabilityId.parse(f"civilization_bootstrap:{key}"),
                key.replace("_", " ").title(),
                f"Bounded candidate definition for {key}.",
            )
        ),
        subject_ref=subject_ref,
        generator_ref=GENERATOR,
        generation_policy_ref=GEN_POLICY,
        created_at=T0,
        rationale="Second-pass candidate rationale.",
        basis_refs=basis_refs,
    )


def _review(proposal: CapabilityProposal, *, review_id: str = "review_second_adversarial") -> ProposalReview:
    return ProposalReview(
        review_id=ProposalReviewId(review_id),
        proposal_id=proposal.proposal_id,
        reviewer_ref=REVIEWER,
        review_policy_ref=REVIEW_POLICY,
        reviewed_at=T0 + timedelta(minutes=1),
        verdict=ProposalReviewVerdict.RECOMMEND_ACCEPT,
        rationale="Recommendation remains non-authoritative.",
    )


def _snapshot_with_review() -> CapabilityProposalSet:
    proposal = _proposal()
    return CapabilityProposalSet(None, (proposal,), (_review(proposal),))


@pytest.mark.parametrize(
    "timestamp",
    (
        "20260815T120000Z",
        "2026-08-15T12:00:00+0000",
        "2026-08-15T12:00:00.1234567Z",
        "2026-08-15T12:00:00",
    ),
)
def test_proposal_json_rejects_noncanonical_timestamp_profiles(timestamp: str) -> None:
    payload = json.loads(_snapshot_with_review().to_json())
    payload["proposals"][0]["created_at"] = timestamp

    with pytest.raises(InvalidProposalError, match="extended ISO-8601"):
        CapabilityProposalSet.from_json(json.dumps(payload))


def test_review_timestamp_uses_the_same_strict_ingestion_profile() -> None:
    payload = json.loads(_snapshot_with_review().to_json())
    payload["reviews"][0]["reviewed_at"] = "20260815T120100Z"

    with pytest.raises(InvalidProposalError, match="extended ISO-8601"):
        CapabilityProposalSet.from_json(json.dumps(payload))


def test_valid_offset_timestamps_are_canonicalized_to_utc_json() -> None:
    payload = json.loads(_snapshot_with_review().to_json())
    payload["proposals"][0]["created_at"] = "2026-08-15T18:00:00+06:00"
    payload["reviews"][0]["reviewed_at"] = "2026-08-15T18:01:00+06:00"

    restored = CapabilityProposalSet.from_json(json.dumps(payload))
    canonical = json.loads(restored.to_json())

    assert canonical["proposals"][0]["created_at"] == "2026-08-15T12:00:00Z"
    assert canonical["reviews"][0]["reviewed_at"] == "2026-08-15T12:01:00Z"


def test_policy_refs_are_syntactic_identifiers_not_authenticated_policy_content() -> None:
    generation_fields = {item.name for item in fields(ProposalGenerationPolicyRef)}
    review_fields = {item.name for item in fields(ProposalReviewPolicyRef)}

    assert generation_fields == {"namespace", "key", "revision"}
    assert review_fields == {"namespace", "key", "revision"}
    for ref in (GEN_POLICY, REVIEW_POLICY):
        assert not hasattr(ref, "content_hash")
        assert not hasattr(ref, "authenticated")
        assert not hasattr(ref, "authority")
        assert not hasattr(ref, "policy_content")


def _private_evidence() -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=EvidenceId("private_evidence_second_adversarial"),
        subject_ref=SUBJECT,
        kind=EvidenceKind.PROJECT,
        summary="Private project observation.",
        context=EvidenceContext("Private project context."),
        observed_at=T0,
        recorded_at=T0,
        provenance=ProvenanceTrail(
            (ProvenanceSource(ProvenanceSourceKind.ACTOR, "test:observer_second_adversarial"),)
        ),
    )


@pytest.mark.parametrize(
    "basis_kind",
    (ProposalBasisKind.EXTERNAL_ARTIFACT, ProposalBasisKind.OTHER),
)
def test_external_or_other_basis_cannot_relabel_internal_private_record_id(basis_kind) -> None:
    evidence = _private_evidence()
    records = EpistemicRecordSet(evidence_records=(evidence,))
    proposal = _proposal(
        basis_refs=(ProposalBasisRef(basis_kind, str(evidence.evidence_id)),),
    )
    snapshot = CapabilityProposalSet(None, (proposal,), ())

    with pytest.raises(InvalidProposalSetError, match="may not relabel"):
        snapshot.validate_against_epistemics(records)


def test_unknown_external_artifact_ref_remains_opaque_not_proven_public_or_shareable() -> None:
    basis = ProposalBasisRef(
        ProposalBasisKind.EXTERNAL_ARTIFACT,
        "artifact://opaque-external-reference",
    )
    proposal = _proposal(basis_refs=(basis,))
    snapshot = CapabilityProposalSet(None, (proposal,), ())

    snapshot.validate_against_epistemics(EpistemicRecordSet())

    assert snapshot.proposals[0].basis_refs == (basis,)
    assert not hasattr(basis, "is_public")
    assert not hasattr(basis, "is_private")
    assert not hasattr(basis, "shareable")
    assert not hasattr(basis, "privacy_classification")


def test_proposal_id_uniqueness_is_snapshot_local_not_a_global_content_hash() -> None:
    first = _proposal(proposal_id="reused_proposal_id", key="candidate_snapshot_a")
    second = _proposal(proposal_id="reused_proposal_id", key="candidate_snapshot_b")

    first_snapshot = CapabilityProposalSet(None, (first,), ())
    second_snapshot = CapabilityProposalSet(None, (second,), ())

    assert first_snapshot.proposals[0].proposal_id == second_snapshot.proposals[0].proposal_id
    assert first_snapshot.proposals[0].payload != second_snapshot.proposals[0].payload

    with pytest.raises(InvalidProposalSetError, match="duplicate proposal id"):
        CapabilityProposalSet(None, (first, second), ())


def test_review_id_uniqueness_is_snapshot_local_not_global_identity_proof() -> None:
    first_proposal = _proposal(proposal_id="proposal_for_review_a", key="candidate_review_a")
    second_proposal = _proposal(proposal_id="proposal_for_review_b", key="candidate_review_b")
    first_review = _review(first_proposal, review_id="reused_review_id")
    second_review = _review(second_proposal, review_id="reused_review_id")

    first_snapshot = CapabilityProposalSet(None, (first_proposal,), (first_review,))
    second_snapshot = CapabilityProposalSet(None, (second_proposal,), (second_review,))

    assert first_snapshot.reviews[0].review_id == second_snapshot.reviews[0].review_id
    assert first_snapshot.reviews[0].proposal_id != second_snapshot.reviews[0].proposal_id

    with pytest.raises(InvalidProposalSetError, match="duplicate proposal review id"):
        CapabilityProposalSet(
            None,
            (first_proposal, second_proposal),
            (first_review, second_review),
        )


def test_roundtripped_persistence_shape_does_not_gain_acceptance_or_authority_fields() -> None:
    snapshot = _snapshot_with_review()
    restored = CapabilityProposalSet.from_json(snapshot.to_json())

    assert restored == snapshot
    for name in (
        "accepted_proposals",
        "authoritative_proposals",
        "materialized_proposals",
        "effective_verdict",
        "current_status",
        "is_persisted_authority",
    ):
        assert not hasattr(restored, name)
