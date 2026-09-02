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
    ConceptRevisionCandidate,
    InvalidProposalSetError,
    ProposalBasisKind,
    ProposalBasisRef,
    ProposalGenerationPolicyRef,
    ProposalGeneratorRef,
    ProposalKind,
    ProposalMechanismKind,
    RelationCreateCandidate,
)
from capability_lab.semantics import (
    CapabilityConceptRef,
    RelationKind,
    RelationScope,
    RelationStrength,
)


T0 = datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc)
GENERATOR = ProposalGeneratorRef(ProposalMechanismKind.MODEL, "test:model_validation")
POLICY = ProposalGenerationPolicyRef.parse("core:proposal_generation@1")
SUBJECT_A = CapabilitySubjectRef("subject_a")
SUBJECT_B = CapabilitySubjectRef("subject_b")


def _proposal(payload, kind, *, subject_ref=None, basis_refs=()):
    return CapabilityProposal(
        CapabilityProposalId("proposal_validation"),
        kind,
        payload,
        subject_ref,
        GENERATOR,
        POLICY,
        T0,
        "Validation candidate.",
        basis_refs=basis_refs,
    )


def _evidence(subject_ref, evidence_id: str) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=EvidenceId(evidence_id),
        subject_ref=subject_ref,
        kind=EvidenceKind.PROJECT,
        summary="Private bounded project observation.",
        context=EvidenceContext("Private project context."),
        observed_at=T0,
        recorded_at=T0,
        provenance=ProvenanceTrail(
            (ProvenanceSource(ProvenanceSourceKind.ACTOR, "test:observer"),)
        ),
    )


def test_stale_exact_revision_fails_closed_against_catalog() -> None:
    proposal = _proposal(
        ConceptRevisionCandidate(
            CapabilityConceptRef.parse("civilization_bootstrap:basic_circuits@2"),
            "Basic Circuits Candidate",
            "Candidate change based on a revision that is not present in the supplied catalog.",
        ),
        ProposalKind.REVISE_CONCEPT,
    )
    snapshot = CapabilityProposalSet(None, (proposal,), ())

    with pytest.raises(InvalidProposalSetError, match="exact concept revision"):
        snapshot.validate_against_capability_catalog(
            build_civilization_bootstrap_seed_catalog_v0()
        )


def test_relation_candidate_that_already_exists_is_not_silently_readded() -> None:
    proposal = _proposal(
        RelationCreateCandidate(
            CapabilityConceptRef.parse("civilization_bootstrap:analog_electronics@1"),
            CapabilityConceptRef.parse("civilization_bootstrap:basic_circuits@1"),
            RelationKind.SUPPORTED_BY,
            scope=RelationScope(
                "conceptual_analysis",
                "For bounded conceptual analysis rather than universal prerequisite claims.",
            ),
            strength=RelationStrength.STRONG,
        ),
        ProposalKind.CREATE_RELATION,
    )
    snapshot = CapabilityProposalSet(None, (proposal,), ())

    with pytest.raises(InvalidProposalSetError, match="duplicates an existing catalog relation"):
        snapshot.validate_against_capability_catalog(
            build_civilization_bootstrap_seed_catalog_v0()
        )


def test_shared_proposal_cannot_cite_private_internal_evidence() -> None:
    evidence = _evidence(SUBJECT_A, "evidence_private_a")
    records = EpistemicRecordSet(evidence_records=(evidence,))
    proposal = _proposal(
        ConceptRevisionCandidate(
            CapabilityConceptRef.parse("civilization_bootstrap:basic_circuits@1"),
            "Basic Circuits Candidate",
            "Candidate semantics derived while inspecting private subject evidence.",
        ),
        ProposalKind.REVISE_CONCEPT,
        basis_refs=(
            ProposalBasisRef(ProposalBasisKind.EVIDENCE_RECORD, str(evidence.evidence_id)),
        ),
    )
    snapshot = CapabilityProposalSet(None, (proposal,), ())

    with pytest.raises(InvalidProposalSetError, match="person-scoped proposal"):
        snapshot.validate_against_epistemics(records)


def test_person_scoped_proposal_cannot_use_another_subjects_internal_basis() -> None:
    evidence = _evidence(SUBJECT_B, "evidence_private_b")
    records = EpistemicRecordSet(evidence_records=(evidence,))
    proposal = _proposal(
        ConceptRevisionCandidate(
            CapabilityConceptRef.parse("civilization_bootstrap:basic_circuits@1"),
            "Basic Circuits Candidate",
            "Candidate semantics for subject A cannot cite subject B private evidence internally.",
        ),
        ProposalKind.REVISE_CONCEPT,
        subject_ref=SUBJECT_A,
        basis_refs=(
            ProposalBasisRef(ProposalBasisKind.EVIDENCE_RECORD, str(evidence.evidence_id)),
        ),
    )
    snapshot = CapabilityProposalSet(SUBJECT_A, (proposal,), ())

    with pytest.raises(InvalidProposalSetError, match="subject must match"):
        snapshot.validate_against_epistemics(records)
