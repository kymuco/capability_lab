import os
from dataclasses import replace
from datetime import datetime, timezone

import pytest

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
    InvalidExternalEvidenceInterpretation,
    admit_external_evidence_claim_interpretation_review_v1,
    external_evidence_claim_interpretation_review_ledger_from_json,
    external_evidence_claim_interpretation_review_ledger_to_json,
    materialize_accepted_external_evidence_interpretation_claim_v1,
    propose_external_evidence_claim_interpretation_v1,
    require_accepted_external_evidence_claim_interpretation_review_v1,
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
    return datetime(2026, 8, 31, hour, 0, tzinfo=timezone.utc)


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
    evidence_id = EvidenceId("external_observation:" + "c" * 64)
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


def _candidate(snapshot, catalog, *, proposal_id="interpretation-authority-1"):
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
        rationale=f"Exact proposal {proposal_id} for authority hardening.",
    )


def _review(snapshot, catalog, candidate, *, review_id="review-authority-1", verdict=None):
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
        rationale="Exact terminal human review for authority hardening.",
    )


def _basis():
    snapshot = EpistemicRecordSet(evidence_records=(_external_evidence(),))
    catalog = _catalog()
    candidate = _candidate(snapshot, catalog)
    review = _review(snapshot, catalog, candidate)
    return snapshot, catalog, candidate, review


def _materialize(snapshot, catalog, candidate, ledger):
    return materialize_accepted_external_evidence_interpretation_claim_v1(
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review_ledger=ledger,
    )


def test_direct_populated_accept_ledger_is_audit_data_not_materialization_authority():
    snapshot, catalog, candidate, review = _basis()
    manual = ExternalEvidenceInterpretationReviewLedger(reviews=(review,))

    with pytest.raises(
        InvalidExternalEvidenceInterpretation,
        match="no runtime admission authority",
    ):
        _materialize(snapshot, catalog, candidate, manual)


def test_json_restored_ledger_requires_explicit_admission_replay_and_preserves_claim_identity():
    snapshot, catalog, candidate, review = _basis()
    admitted = admit_external_evidence_claim_interpretation_review_v1(
        review_ledger=ExternalEvidenceInterpretationReviewLedger(),
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review=review,
    )
    original = _materialize(snapshot, catalog, candidate, admitted)

    restored = external_evidence_claim_interpretation_review_ledger_from_json(
        external_evidence_claim_interpretation_review_ledger_to_json(admitted)
    )
    assert restored == admitted
    assert restored is not admitted

    with pytest.raises(
        InvalidExternalEvidenceInterpretation,
        match="no runtime admission authority",
    ):
        _materialize(snapshot, catalog, candidate, restored)

    replayed = admit_external_evidence_claim_interpretation_review_v1(
        review_ledger=restored,
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review=review,
    )
    assert replayed is restored
    assert len(replayed.reviews) == 1

    after_replay = _materialize(snapshot, catalog, candidate, replayed)
    assert after_replay.claim == original.claim
    assert after_replay.successor_snapshot == original.successor_snapshot
    assert after_replay.materialization_receipt == original.materialization_receipt


def test_authority_is_bound_to_exact_current_ledger_and_replay_restores_after_growth():
    snapshot, catalog, first_candidate, first_review = _basis()
    first_ledger = admit_external_evidence_claim_interpretation_review_v1(
        review_ledger=ExternalEvidenceInterpretationReviewLedger(),
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=first_candidate,
        review=first_review,
    )
    assert require_accepted_external_evidence_claim_interpretation_review_v1(
        review_ledger=first_ledger,
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=first_candidate,
    ) == first_review

    second_candidate = _candidate(
        snapshot,
        catalog,
        proposal_id="interpretation-authority-2",
    )
    second_review = _review(
        snapshot,
        catalog,
        second_candidate,
        review_id="review-authority-2",
        verdict=ExternalEvidenceInterpretationReviewVerdict.REJECT,
    )
    grown = admit_external_evidence_claim_interpretation_review_v1(
        review_ledger=first_ledger,
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=second_candidate,
        review=second_review,
    )
    assert len(grown.reviews) == 2

    with pytest.raises(
        InvalidExternalEvidenceInterpretation,
        match="no runtime admission authority",
    ):
        require_accepted_external_evidence_claim_interpretation_review_v1(
            review_ledger=grown,
            epistemic_snapshot=snapshot,
            catalog=catalog,
            candidate=first_candidate,
        )

    replayed = admit_external_evidence_claim_interpretation_review_v1(
        review_ledger=grown,
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=first_candidate,
        review=first_review,
    )
    assert replayed is grown
    assert len(replayed.reviews) == 2
    assert require_accepted_external_evidence_claim_interpretation_review_v1(
        review_ledger=replayed,
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=first_candidate,
    ) == first_review


def test_admitted_reject_has_terminal_authority_but_never_accept_authority():
    snapshot, catalog, candidate, _ = _basis()
    rejected = _review(
        snapshot,
        catalog,
        candidate,
        review_id="review-reject",
        verdict=ExternalEvidenceInterpretationReviewVerdict.REJECT,
    )
    ledger = admit_external_evidence_claim_interpretation_review_v1(
        review_ledger=ExternalEvidenceInterpretationReviewLedger(),
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review=rejected,
    )

    with pytest.raises(
        InvalidExternalEvidenceInterpretation,
        match="REJECT, not ACCEPT",
    ):
        _materialize(snapshot, catalog, candidate, ledger)


def test_post_admission_ledger_corruption_invalidates_runtime_authority():
    snapshot, catalog, first_candidate, first_review = _basis()
    ledger = admit_external_evidence_claim_interpretation_review_v1(
        review_ledger=ExternalEvidenceInterpretationReviewLedger(),
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=first_candidate,
        review=first_review,
    )
    second_candidate = _candidate(
        snapshot,
        catalog,
        proposal_id="interpretation-corruption-2",
    )
    second_review = _review(
        snapshot,
        catalog,
        second_candidate,
        review_id="review-corruption-2",
        verdict=ExternalEvidenceInterpretationReviewVerdict.REJECT,
    )

    # Bypass frozen dataclass assignment deliberately.  The mutated value remains
    # structurally valid audit data, so the runtime issuance digest must catch it.
    object.__setattr__(ledger, "reviews", ledger.reviews + (second_review,))

    with pytest.raises(
        InvalidExternalEvidenceInterpretation,
        match="stale for the supplied review ledger",
    ):
        require_accepted_external_evidence_claim_interpretation_review_v1(
            review_ledger=ledger,
            epistemic_snapshot=snapshot,
            catalog=catalog,
            candidate=first_candidate,
        )


@pytest.mark.skipif(not hasattr(os, "fork"), reason="POSIX fork process-boundary regression")
def test_parent_terminal_review_authority_is_not_usable_in_fork_child():
    snapshot, catalog, candidate, review = _basis()
    ledger = admit_external_evidence_claim_interpretation_review_v1(
        review_ledger=ExternalEvidenceInterpretationReviewLedger(),
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review=review,
    )
    parent_result = _materialize(snapshot, catalog, candidate, ledger)

    child_pid = os.fork()
    if child_pid == 0:
        try:
            try:
                _materialize(snapshot, catalog, candidate, ledger)
            except InvalidExternalEvidenceInterpretation as exc:
                if "different process" not in str(exc):
                    os._exit(21)
            else:
                os._exit(22)

            replayed = admit_external_evidence_claim_interpretation_review_v1(
                review_ledger=ledger,
                epistemic_snapshot=snapshot,
                catalog=catalog,
                candidate=candidate,
                review=review,
            )
            if replayed is not ledger or len(replayed.reviews) != 1:
                os._exit(23)
            child_result = _materialize(snapshot, catalog, candidate, replayed)
            if child_result.claim != parent_result.claim:
                os._exit(24)
            if child_result.materialization_receipt != parent_result.materialization_receipt:
                os._exit(25)
        except BaseException:
            os._exit(26)
        os._exit(0)

    _, status = os.waitpid(child_pid, 0)
    assert os.waitstatus_to_exitcode(status) == 0

    # Child-local replay mutates only the child's copied issuance table.
    assert _materialize(snapshot, catalog, candidate, ledger) == parent_result
