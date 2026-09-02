from datetime import datetime, timezone

import pytest

from capability_lab.domains import build_civilization_bootstrap_seed_catalog_v0
from capability_lab.proposals import (
    CapabilityProposal,
    CapabilityProposalId,
    CapabilityProposalSet,
    ConceptCandidateSpec,
    ConceptMergeCandidate,
    ConceptSplitCandidate,
    InvalidProposalSetError,
    ProposalGenerationPolicyRef,
    ProposalGeneratorRef,
    ProposalKind,
    ProposalMechanismKind,
)
from capability_lab.semantics import CapabilityConceptRef, CapabilityId


T0 = datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc)
GENERATOR = ProposalGeneratorRef(ProposalMechanismKind.MODEL, "test:model_namespace")
POLICY = ProposalGenerationPolicyRef.parse("core:proposal_generation@1")


def _spec(capability_id: str) -> ConceptCandidateSpec:
    return ConceptCandidateSpec(
        CapabilityId.parse(capability_id),
        "Candidate Output",
        "Candidate output for namespace-governance regression coverage.",
    )


def _proposal(proposal_id: str, kind: ProposalKind, payload) -> CapabilityProposal:
    return CapabilityProposal(
        CapabilityProposalId(proposal_id),
        kind,
        payload,
        None,
        GENERATOR,
        POLICY,
        T0,
        "Candidate does not implicitly create namespace governance.",
    )


def test_split_output_cannot_implicitly_create_unknown_namespace() -> None:
    proposal = _proposal(
        "proposal_split_unknown_namespace",
        ProposalKind.SPLIT_CONCEPT,
        ConceptSplitCandidate(
            CapabilityConceptRef.parse("civilization_bootstrap:basic_circuits@1"),
            (
                _spec("civilization_bootstrap:candidate_split_valid_namespace"),
                _spec("unregistered_namespace:candidate_split_unknown_namespace"),
            ),
        ),
    )

    with pytest.raises(InvalidProposalSetError, match="does not create namespaces"):
        CapabilityProposalSet(None, (proposal,), ()).validate_against_capability_catalog(
            build_civilization_bootstrap_seed_catalog_v0()
        )


def test_merge_output_cannot_implicitly_create_unknown_namespace() -> None:
    proposal = _proposal(
        "proposal_merge_unknown_namespace",
        ProposalKind.MERGE_CONCEPTS,
        ConceptMergeCandidate(
            (
                CapabilityConceptRef.parse("civilization_bootstrap:basic_circuits@1"),
                CapabilityConceptRef.parse("civilization_bootstrap:electrical_measurement@1"),
            ),
            _spec("unregistered_namespace:candidate_merge_unknown_namespace"),
        ),
    )

    with pytest.raises(InvalidProposalSetError, match="does not create namespaces"):
        CapabilityProposalSet(None, (proposal,), ()).validate_against_capability_catalog(
            build_civilization_bootstrap_seed_catalog_v0()
        )
