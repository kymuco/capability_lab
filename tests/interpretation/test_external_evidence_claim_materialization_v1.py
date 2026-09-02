from dataclasses import replace
from datetime import datetime, timezone
import inspect

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
    external_evidence_interpretation_claim_materialization_receipt_from_dict,
    external_evidence_interpretation_claim_materialization_receipt_from_json,
    external_evidence_interpretation_claim_materialization_receipt_sha256_v1,
    materialize_accepted_external_evidence_interpretation_claim_v1,
    propose_external_evidence_claim_interpretation_v1,
    review_external_evidence_claim_interpretation_v1,
    validate_external_evidence_interpretation_claim_materialization_v1,
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


def _external_evidence() -> EvidenceRecord:
    evidence_id = EvidenceId("external_observation:" + "a" * 64)
    return EvidenceRecord(
        evidence_id=evidence_id,
        subject_ref=CapabilitySubjectRef("subject-1"),
        kind=EvidenceKind.ARTIFACT,
        summary="Exact reviewed external observation.",
        context=EvidenceContext(
            description="Reviewed external observation.",
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
                    actor_ref=ActorRef("reviewer-1"),
                    mechanism_ref=str(REVIEWED_EXTERNAL_OBSERVATION_TO_EVIDENCE_POLICY_V1),
                    note="Reviewed PR12.1 materialization.",
                ),
            ),
        ),
        outcome=None,
        payload_refs=("artifact-1",),
    )


def _candidate(snapshot, catalog, *, proposal_id="interpretation-1", rationale=None):
    return propose_external_evidence_claim_interpretation_v1(
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
            "model-proposer-1",
        ),
        proposal_id=ExternalEvidenceInterpretationProposalId(proposal_id),
        proposed_at=_time(12),
        rationale=rationale or "The artifact appears relevant to the exact capability scope.",
    )


def _review(snapshot, catalog, candidate, *, review_id="review-1", verdict=None):
    return review_external_evidence_claim_interpretation_v1(
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review_id=ExternalEvidenceInterpretationReviewId(review_id),
        reviewer_ref=ExternalEvidenceInterpretationReviewerRef(
            ExternalEvidenceInterpretationReviewerKind.HUMAN,
            "human-reviewer-1",
        ),
        verdict=verdict or ExternalEvidenceInterpretationReviewVerdict.ACCEPT,
        reviewed_at=_time(13),
        rationale="Exact human interpretation decision.",
    )


def _basis(*, verdict=None):
    evidence = _external_evidence()
    snapshot = EpistemicRecordSet(evidence_records=(evidence,))
    catalog = _catalog()
    candidate = _candidate(snapshot, catalog)
    review = _review(snapshot, catalog, candidate, verdict=verdict)
    ledger = admit_external_evidence_claim_interpretation_review_v1(
        review_ledger=ExternalEvidenceInterpretationReviewLedger(),
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review=review,
    )
    return snapshot, catalog, candidate, review, ledger


def test_exact_accept_materializes_deterministic_capability_claim_and_pr11_3_successor():
    snapshot, catalog, candidate, review, ledger = _basis()
    result = materialize_accepted_external_evidence_interpretation_claim_v1(
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review_ledger=ledger,
    )

    assert result.claim.subject_ref == candidate.subject_ref
    assert result.claim.concept_ref == candidate.concept_ref
    assert result.claim.statement == candidate.claim_statement
    assert result.claim.scope == candidate.claim_scope
    assert result.claim.created_at == review.reviewed_at
    assert str(result.claim.claim_id).startswith("external_interpretation:")
    assert result.successor_snapshot.evidence_records == snapshot.evidence_records
    assert result.successor_snapshot.evaluations == snapshot.evaluations == ()
    assert result.successor_snapshot.claims == (result.claim,)
    assert result.succession_receipt.added_claim_ids == (result.claim.claim_id,)
    assert result.succession_receipt.added_evidence_ids == ()
    assert result.succession_receipt.added_evaluation_ids == ()


def test_exact_retry_from_same_predecessor_is_byte_identical():
    snapshot, catalog, candidate, _, ledger = _basis()
    first = materialize_accepted_external_evidence_interpretation_claim_v1(
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review_ledger=ledger,
    )
    second = materialize_accepted_external_evidence_interpretation_claim_v1(
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review_ledger=ledger,
    )

    assert first == second
    assert first.successor_snapshot.to_json() == second.successor_snapshot.to_json()
    assert first.materialization_receipt.to_json() == second.materialization_receipt.to_json()


def test_raw_review_without_terminal_ledger_admission_cannot_materialize():
    snapshot, catalog, candidate, _, _ = _basis()
    with pytest.raises(
        InvalidExternalEvidenceInterpretation,
        match="no exact terminal review",
    ):
        materialize_accepted_external_evidence_interpretation_claim_v1(
            epistemic_snapshot=snapshot,
            catalog=catalog,
            candidate=candidate,
            review_ledger=ExternalEvidenceInterpretationReviewLedger(),
        )


def test_terminal_reject_cannot_materialize_claim():
    snapshot, catalog, candidate, _, ledger = _basis(
        verdict=ExternalEvidenceInterpretationReviewVerdict.REJECT
    )
    with pytest.raises(
        InvalidExternalEvidenceInterpretation,
        match="REJECT, not ACCEPT",
    ):
        materialize_accepted_external_evidence_interpretation_claim_v1(
            epistemic_snapshot=snapshot,
            catalog=catalog,
            candidate=candidate,
            review_ledger=ledger,
        )


def test_candidate_statement_mutation_after_accept_fails_closed():
    snapshot, catalog, candidate, _, ledger = _basis()
    tampered = replace(
        candidate,
        claim_statement="The subject is an expert signal researcher.",
    )
    with pytest.raises(InvalidExternalEvidenceInterpretation):
        materialize_accepted_external_evidence_interpretation_claim_v1(
            epistemic_snapshot=snapshot,
            catalog=catalog,
            candidate=tampered,
            review_ledger=ledger,
        )


def test_same_evidence_id_with_changed_bytes_fails_closed():
    snapshot, catalog, candidate, _, ledger = _basis()
    changed = replace(snapshot.evidence_records[0], summary="Changed evidence bytes.")
    tampered_snapshot = EpistemicRecordSet(evidence_records=(changed,))
    with pytest.raises(InvalidExternalEvidenceInterpretation):
        materialize_accepted_external_evidence_interpretation_claim_v1(
            epistemic_snapshot=tampered_snapshot,
            catalog=catalog,
            candidate=candidate,
            review_ledger=ledger,
        )


def test_materialization_api_exposes_no_claim_semantic_or_identity_override_inputs():
    parameters = set(
        inspect.signature(
            materialize_accepted_external_evidence_interpretation_claim_v1
        ).parameters
    )
    assert parameters == {
        "epistemic_snapshot",
        "catalog",
        "candidate",
        "review_ledger",
    }
    assert not ({"claim_id", "statement", "scope", "created_at"} & parameters)


def test_materialized_claim_provenance_never_binds_evidence_record():
    snapshot, catalog, candidate, _, ledger = _basis()
    result = materialize_accepted_external_evidence_interpretation_claim_v1(
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review_ledger=ledger,
    )
    assert all(
        source.kind is not ProvenanceSourceKind.EVIDENCE_RECORD
        for source in result.claim.provenance.sources
    )
    assert result.claim.provenance.steps[0].actor_ref == ActorRef("human-reviewer-1")


def test_unrelated_review_ledger_append_requires_replay_but_preserves_materialization_identity():
    snapshot, catalog, candidate, review, ledger = _basis()
    baseline = materialize_accepted_external_evidence_interpretation_claim_v1(
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review_ledger=ledger,
    )
    other = _candidate(
        snapshot,
        catalog,
        proposal_id="interpretation-2",
        rationale="Independent unrelated proposal identity.",
    )
    other_review = _review(
        snapshot,
        catalog,
        other,
        review_id="review-2",
    )
    extended = admit_external_evidence_claim_interpretation_review_v1(
        review_ledger=ledger,
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=other,
        review=other_review,
    )

    with pytest.raises(
        InvalidExternalEvidenceInterpretation,
        match="no runtime admission authority",
    ):
        materialize_accepted_external_evidence_interpretation_claim_v1(
            epistemic_snapshot=snapshot,
            catalog=catalog,
            candidate=candidate,
            review_ledger=extended,
        )

    replayed = admit_external_evidence_claim_interpretation_review_v1(
        review_ledger=extended,
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review=review,
    )
    assert replayed is extended
    assert len(replayed.reviews) == 2

    replay = materialize_accepted_external_evidence_interpretation_claim_v1(
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review_ledger=replayed,
    )
    assert replay.claim == baseline.claim
    assert replay.materialization_receipt == baseline.materialization_receipt


def test_unrelated_epistemic_append_does_not_change_deterministic_claim_identity():
    snapshot, catalog, candidate, _, ledger = _basis()
    baseline = materialize_accepted_external_evidence_interpretation_claim_v1(
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review_ledger=ledger,
    )
    unrelated = CapabilityClaim(
        claim_id=CapabilityClaimId("unrelated-claim"),
        subject_ref=CapabilitySubjectRef("subject-1"),
        concept_ref=catalog.concepts[0].ref,
        statement="An unrelated already retained proposition.",
        scope=ClaimScope("Unrelated retained scope.", ("unrelated",)),
        created_at=_time(12),
        provenance=ProvenanceTrail(
            sources=(ProvenanceSource(ProvenanceSourceKind.SYSTEM, "capability_lab"),),
        ),
    )
    extended_snapshot = EpistemicRecordSet(
        evidence_records=snapshot.evidence_records,
        claims=(unrelated,),
    )
    replay = materialize_accepted_external_evidence_interpretation_claim_v1(
        epistemic_snapshot=extended_snapshot,
        catalog=catalog,
        candidate=candidate,
        review_ledger=ledger,
    )
    assert replay.claim.claim_id == baseline.claim.claim_id
    assert replay.claim == baseline.claim
    assert unrelated in replay.successor_snapshot.claims


def test_exact_materialization_receipt_round_trip_and_digest_are_deterministic():
    snapshot, catalog, candidate, _, ledger = _basis()
    result = materialize_accepted_external_evidence_interpretation_claim_v1(
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review_ledger=ledger,
    )
    payload = result.materialization_receipt.to_json()
    restored = external_evidence_interpretation_claim_materialization_receipt_from_json(
        payload
    )
    assert restored == result.materialization_receipt
    assert restored.to_json() == payload
    assert (
        external_evidence_interpretation_claim_materialization_receipt_sha256_v1(restored)
        == external_evidence_interpretation_claim_materialization_receipt_sha256_v1(
            result.materialization_receipt
        )
    )


def test_receipt_serialization_rejects_unknown_missing_and_duplicate_fields():
    snapshot, catalog, candidate, _, ledger = _basis()
    receipt = materialize_accepted_external_evidence_interpretation_claim_v1(
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review_ledger=ledger,
    ).materialization_receipt
    obj = receipt.to_dict()

    unknown = dict(obj)
    unknown["authority"] = "forged"
    with pytest.raises(InvalidExternalEvidenceInterpretation, match="unknown"):
        external_evidence_interpretation_claim_materialization_receipt_from_dict(
            unknown
        )

    missing = dict(obj)
    missing.pop("claim_sha256")
    with pytest.raises(InvalidExternalEvidenceInterpretation, match="missing"):
        external_evidence_interpretation_claim_materialization_receipt_from_dict(
            missing
        )

    duplicate = receipt.to_json().replace(
        '"schema_version":1',
        '"schema_version":1,"schema_version":1',
        1,
    )
    with pytest.raises(InvalidExternalEvidenceInterpretation, match="duplicate JSON"):
        external_evidence_interpretation_claim_materialization_receipt_from_json(
            duplicate
        )


def test_forged_materialization_receipt_is_rejected_by_replay_validator():
    snapshot, catalog, candidate, _, ledger = _basis()
    result = materialize_accepted_external_evidence_interpretation_claim_v1(
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review_ledger=ledger,
    )
    forged = replace(
        result,
        materialization_receipt=replace(
            result.materialization_receipt,
            claim_sha256="0" * 64,
        ),
    )
    with pytest.raises(
        InvalidExternalEvidenceInterpretation,
        match="materialization_receipt does not match",
    ):
        validate_external_evidence_interpretation_claim_materialization_v1(
            epistemic_snapshot=snapshot,
            catalog=catalog,
            candidate=candidate,
            review_ledger=ledger,
            materialization=forged,
        )


def test_materialized_claim_cannot_be_rematerialized_into_its_own_successor():
    snapshot, catalog, candidate, _, ledger = _basis()
    result = materialize_accepted_external_evidence_interpretation_claim_v1(
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review_ledger=ledger,
    )
    with pytest.raises(
        InvalidExternalEvidenceInterpretation,
        match="already exists",
    ):
        materialize_accepted_external_evidence_interpretation_claim_v1(
            epistemic_snapshot=result.successor_snapshot,
            catalog=catalog,
            candidate=candidate,
            review_ledger=ledger,
        )


def test_malformed_candidate_fails_closed_before_materialization():
    snapshot, catalog, _, _, ledger = _basis()
    with pytest.raises(
        InvalidExternalEvidenceInterpretation,
        match="exact ExternalEvidenceClaimInterpretationCandidate",
    ):
        materialize_accepted_external_evidence_interpretation_claim_v1(
            epistemic_snapshot=snapshot,
            catalog=catalog,
            candidate=object(),
            review_ledger=ledger,
        )
