from datetime import datetime, timezone

import pytest

from capability_lab.epistemics import (
    ActorRef,
    CapabilityClaim,
    CapabilityClaimId,
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


def _evidence() -> EvidenceRecord:
    evidence_id = EvidenceId("external_observation:" + "e" * 64)
    return EvidenceRecord(
        evidence_id=evidence_id,
        subject_ref=CapabilitySubjectRef("subject-legacy-duplicate"),
        kind=EvidenceKind.ARTIFACT,
        summary="Reviewed legacy duplicate regression evidence.",
        context=EvidenceContext(
            description="Reviewed legacy duplicate regression evidence.",
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
                    actor_ref=ActorRef("reviewer-legacy-evidence"),
                    mechanism_ref=str(REVIEWED_EXTERNAL_OBSERVATION_TO_EVIDENCE_POLICY_V1),
                    note="Reviewed PR12.1 materialization.",
                ),
            ),
        ),
        outcome=None,
    )


def _legacy_claim(*, catalog: CapabilityCatalog, statement: str) -> CapabilityClaim:
    return CapabilityClaim(
        claim_id=CapabilityClaimId("legacy:manual-signal-claim"),
        subject_ref=CapabilitySubjectRef("subject-legacy-duplicate"),
        concept_ref=catalog.concepts[0].ref,
        statement=statement,
        scope=ClaimScope(
            "Bounded interpretation of supplied signal evidence.",
            ("bounded_reasoning",),
        ),
        created_at=_time(9),
        provenance=ProvenanceTrail(
            sources=(
                ProvenanceSource(ProvenanceSourceKind.SYSTEM, "legacy-manual-path"),
            ),
            steps=(
                ProvenanceStep(
                    operation_key="legacy_manual_claim_create",
                    occurred_at=_time(9),
                    actor_ref=ActorRef("legacy-reviewer"),
                    mechanism_ref="legacy:manual_claim@1",
                    note="Pre-existing manual claim used only for semantic collision regression.",
                ),
            ),
        ),
    )


def _accepted_basis(snapshot: EpistemicRecordSet, catalog: CapabilityCatalog):
    candidate = propose_external_evidence_claim_interpretation_v1(
        epistemic_snapshot=snapshot,
        evidence_id=snapshot.evidence_records[0].evidence_id,
        catalog=catalog,
        concept_ref=catalog.concepts[0].ref,
        claim_statement="The subject can reason about bounded signal evidence.",
        claim_scope=ClaimScope(
            "Bounded interpretation of supplied signal evidence.",
            ("bounded_reasoning",),
        ),
        proposer_ref=ExternalEvidenceInterpretationProposerRef(
            ExternalEvidenceInterpretationProposerKind.MODEL,
            "model-legacy-duplicate",
        ),
        proposal_id=ExternalEvidenceInterpretationProposalId(
            "legacy-semantic-duplicate-proposal"
        ),
        proposed_at=_time(12),
        rationale="Exact candidate for legacy semantic collision regression.",
    )
    review = review_external_evidence_claim_interpretation_v1(
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review_id=ExternalEvidenceInterpretationReviewId(
            "legacy-semantic-duplicate-review"
        ),
        reviewer_ref=ExternalEvidenceInterpretationReviewerRef(
            ExternalEvidenceInterpretationReviewerKind.HUMAN,
            "human-legacy-duplicate",
        ),
        verdict=ExternalEvidenceInterpretationReviewVerdict.ACCEPT,
        reviewed_at=_time(13),
        rationale="Accept exact bounded proposition.",
    )
    ledger = admit_external_evidence_claim_interpretation_review_v1(
        review_ledger=ExternalEvidenceInterpretationReviewLedger(),
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review=review,
    )
    return candidate, ledger


def test_preexisting_semantically_identical_legacy_claim_under_different_id_fails_closed():
    catalog = _catalog()
    legacy = _legacy_claim(
        catalog=catalog,
        statement="The subject can reason about bounded signal evidence.",
    )
    snapshot = EpistemicRecordSet(
        evidence_records=(_evidence(),),
        claims=(legacy,),
    )
    candidate, ledger = _accepted_basis(snapshot, catalog)

    with pytest.raises(
        InvalidExternalEvidenceInterpretation,
        match="semantically identical CapabilityClaim already exists",
    ):
        materialize_accepted_external_evidence_interpretation_claim_v1(
            epistemic_snapshot=snapshot,
            catalog=catalog,
            candidate=candidate,
            review_ledger=ledger,
        )


def test_preexisting_different_proposition_does_not_block_materialization():
    catalog = _catalog()
    legacy = _legacy_claim(
        catalog=catalog,
        statement="The subject has encountered bounded signal evidence.",
    )
    snapshot = EpistemicRecordSet(
        evidence_records=(_evidence(),),
        claims=(legacy,),
    )
    candidate, ledger = _accepted_basis(snapshot, catalog)

    result = materialize_accepted_external_evidence_interpretation_claim_v1(
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review_ledger=ledger,
    )

    assert legacy in result.successor_snapshot.claims
    assert result.claim in result.successor_snapshot.claims
    assert len(result.successor_snapshot.claims) == 2
    assert result.claim.claim_id != legacy.claim_id
    assert result.claim.statement != legacy.statement
