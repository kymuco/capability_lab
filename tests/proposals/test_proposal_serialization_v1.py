from datetime import datetime, timedelta, timezone
import json

import pytest

from capability_lab.proposals import (
    CapabilityProposal,
    CapabilityProposalId,
    CapabilityProposalSet,
    ConceptCandidateSpec,
    ConceptCreateCandidate,
    InvalidProposalError,
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


def _snapshot() -> CapabilityProposalSet:
    proposal = CapabilityProposal(
        CapabilityProposalId("proposal_serialization"),
        ProposalKind.CREATE_CONCEPT,
        ConceptCreateCandidate(
            ConceptCandidateSpec(
                CapabilityId.parse("civilization_bootstrap:candidate_serialized"),
                "Candidate Serialized",
                "A candidate semantic object that is not an accepted CapabilityConcept.",
                ("Serialized Candidate",),
            )
        ),
        None,
        ProposalGeneratorRef(ProposalMechanismKind.MODEL, "test:model_serialization"),
        ProposalGenerationPolicyRef.parse("core:proposal_generation@1"),
        T0,
        "Serialization must preserve proposal facts without granting authority.",
        basis_refs=(
            ProposalBasisRef(
                ProposalBasisKind.CAPABILITY_CONCEPT,
                "civilization_bootstrap:basic_circuits@1",
            ),
            ProposalBasisRef(ProposalBasisKind.EXTERNAL_ARTIFACT, "artifact://design-note-01"),
        ),
    )
    review = ProposalReview(
        ProposalReviewId("review_serialization"),
        proposal.proposal_id,
        ProposalReviewerRef(ProposalMechanismKind.HUMAN, "test:reviewer_serialization"),
        ProposalReviewPolicyRef.parse("core:proposal_review@1"),
        T0 + timedelta(minutes=1),
        ProposalReviewVerdict.REQUEST_REVISION,
        "Review recommendation remains a separate immutable record.",
    )
    return CapabilityProposalSet(None, (proposal,), (review,))


def test_proposal_set_roundtrip_is_exact_and_deterministic() -> None:
    first = _snapshot()
    restored = CapabilityProposalSet.from_json(first.to_json())

    assert restored == first
    assert restored.to_json() == first.to_json()
    assert CapabilityProposalSet.from_dict(first.to_dict()) == first


def test_proposal_json_rejects_unknown_fields() -> None:
    payload = json.loads(_snapshot().to_json())
    payload["unexpected"] = True

    with pytest.raises(InvalidProposalError, match="fields must match schema exactly"):
        CapabilityProposalSet.from_json(json.dumps(payload))


def test_proposal_json_rejects_duplicate_object_keys() -> None:
    with pytest.raises(InvalidProposalError, match="duplicate JSON object key"):
        CapabilityProposalSet.from_json(
            '{"schema_version":1,"schema_version":1,"subject_ref":null,"proposals":[],"reviews":[]}'
        )


def test_proposal_json_rejects_unknown_kind_instead_of_guessing() -> None:
    payload = json.loads(_snapshot().to_json())
    payload["proposals"][0]["kind"] = "auto_accept_model_output"

    with pytest.raises(InvalidProposalError, match="unknown proposal kind"):
        CapabilityProposalSet.from_json(json.dumps(payload))
