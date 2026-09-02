from dataclasses import fields, replace
from datetime import datetime, timezone
import json

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
    EXTERNAL_EVIDENCE_CLAIM_INTERPRETATION_HUMAN_REVIEW_POLICY_V1,
    ExternalEvidenceInterpretationProposalId,
    ExternalEvidenceInterpretationProposerKind,
    ExternalEvidenceInterpretationProposerRef,
    ExternalEvidenceInterpretationReviewId,
    ExternalEvidenceInterpretationReviewerKind,
    ExternalEvidenceInterpretationReviewerRef,
    ExternalEvidenceInterpretationReviewVerdict,
    InvalidExternalEvidenceInterpretation,
    external_evidence_claim_interpretation_review_from_dict,
    external_evidence_claim_interpretation_review_from_json,
    external_evidence_claim_interpretation_review_sha256_v1,
    external_evidence_claim_interpretation_review_to_dict,
    external_evidence_claim_interpretation_review_to_json,
    propose_external_evidence_claim_interpretation_v1,
    review_external_evidence_claim_interpretation_v1,
    validate_external_evidence_claim_interpretation_review_v1,
)
from capability_lab.observations import REVIEWED_EXTERNAL_OBSERVATION_TO_EVIDENCE_POLICY_V1
from capability_lab.semantics import (
    CapabilityCatalog,
    CapabilityConcept,
    CapabilityId,
    CapabilityNamespace,
)


def _time(hour: int) -> datetime:
    return datetime(2026, 8, 29, hour, 0, tzinfo=timezone.utc)


def _catalog(revision: int = 1) -> CapabilityCatalog:
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
                revision=revision,
            ),
        ),
    )


def _external_evidence(
    digest_char: str = "a",
    *,
    summary: str = "Exact reviewed external observation.",
) -> EvidenceRecord:
    evidence_id = EvidenceId(f"external_observation:{digest_char * 64}")
    return EvidenceRecord(
        evidence_id=evidence_id,
        subject_ref=CapabilitySubjectRef("subject-1"),
        kind=EvidenceKind.ARTIFACT,
        summary=summary,
        context=EvidenceContext(
            description="Reviewed external observation.",
            scope_tags=("external_observation",),
        ),
        observed_at=_time(10),
        recorded_at=_time(11),
        provenance=ProvenanceTrail(
            sources=(
                ProvenanceSource(
                    ProvenanceSourceKind.EXTERNAL_RECORD,
                    str(evidence_id),
                ),
            ),
            steps=(
                ProvenanceStep(
                    operation_key="external_observation_materialize",
                    occurred_at=_time(11),
                    actor_ref=ActorRef("reviewer-1"),
                    mechanism_ref=str(
                        REVIEWED_EXTERNAL_OBSERVATION_TO_EVIDENCE_POLICY_V1
                    ),
                    note="Reviewed PR12.1 materialization.",
                ),
            ),
        ),
        outcome=None,
        payload_refs=("artifact-1",),
    )


def _candidate(*, evidence=None, catalog=None):
    evidence = evidence or _external_evidence()
    catalog = catalog or _catalog()
    snapshot = EpistemicRecordSet(evidence_records=(evidence,))
    candidate = propose_external_evidence_claim_interpretation_v1(
        epistemic_snapshot=snapshot,
        evidence_id=evidence.evidence_id,
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
        proposal_id=ExternalEvidenceInterpretationProposalId("interpretation-1"),
        proposed_at=_time(12),
        rationale="The artifact appears relevant to the exact capability scope.",
    )
    return snapshot, catalog, candidate


def _review(*, verdict=ExternalEvidenceInterpretationReviewVerdict.ACCEPT):
    snapshot, catalog, candidate = _candidate()
    review = review_external_evidence_claim_interpretation_v1(
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review_id=ExternalEvidenceInterpretationReviewId("review-1"),
        reviewer_ref=ExternalEvidenceInterpretationReviewerRef(
            ExternalEvidenceInterpretationReviewerKind.HUMAN,
            "human-reviewer-1",
        ),
        verdict=verdict,
        reviewed_at=_time(13),
        rationale="Human reviewed the exact proposed interpretation boundary.",
    )
    return snapshot, catalog, candidate, review


def test_accept_review_binds_exact_candidate_without_claim_authority():
    snapshot, catalog, candidate, review = _review()

    assert review.policy_ref == EXTERNAL_EVIDENCE_CLAIM_INTERPRETATION_HUMAN_REVIEW_POLICY_V1
    assert review.proposal_id == candidate.proposal_id
    assert review.verdict is ExternalEvidenceInterpretationReviewVerdict.ACCEPT

    validate_external_evidence_claim_interpretation_review_v1(
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review=review,
    )


def test_reject_is_valid_terminal_review_not_negative_evidence():
    snapshot, catalog, candidate, review = _review(
        verdict=ExternalEvidenceInterpretationReviewVerdict.REJECT
    )
    validate_external_evidence_claim_interpretation_review_v1(
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review=review,
    )
    assert review.verdict is ExternalEvidenceInterpretationReviewVerdict.REJECT


def test_review_surface_has_no_evaluation_state_or_permission_authority():
    _, _, _, review = _review()
    names = {item.name for item in fields(type(review))}
    forbidden = {
        "claim_id",
        "bearing",
        "reliability",
        "evaluation_id",
        "evaluation_conclusion",
        "coverage_status",
        "conflict_status",
        "state_id",
        "score",
        "mastery",
        "readiness",
        "permission",
    }
    assert names.isdisjoint(forbidden)


def test_v1_reviewer_is_human_only():
    assert set(ExternalEvidenceInterpretationReviewerKind) == {
        ExternalEvidenceInterpretationReviewerKind.HUMAN
    }
    with pytest.raises(ValueError):
        ExternalEvidenceInterpretationReviewerKind("MODEL")


def test_review_rejects_candidate_mutation_after_human_decision():
    snapshot, catalog, candidate, review = _review()
    mutated = replace(candidate, rationale="Changed candidate after the review.")

    with pytest.raises(
        InvalidExternalEvidenceInterpretation,
        match="candidate_sha256 does not match exact candidate",
    ):
        validate_external_evidence_claim_interpretation_review_v1(
            epistemic_snapshot=snapshot,
            catalog=catalog,
            candidate=mutated,
            review=review,
        )


def test_review_rejects_same_evidence_id_with_mutated_evidence_bytes():
    evidence = _external_evidence()
    snapshot, catalog, candidate = _candidate(evidence=evidence)
    review = review_external_evidence_claim_interpretation_v1(
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
        review_id=ExternalEvidenceInterpretationReviewId("review-evidence"),
        reviewer_ref=ExternalEvidenceInterpretationReviewerRef(
            ExternalEvidenceInterpretationReviewerKind.HUMAN,
            "human-reviewer-1",
        ),
        verdict=ExternalEvidenceInterpretationReviewVerdict.ACCEPT,
        reviewed_at=_time(13),
        rationale="Reviewed exact evidence bytes.",
    )
    mutated_snapshot = EpistemicRecordSet(
        evidence_records=(replace(evidence, summary="Mutated same-id evidence."),)
    )

    with pytest.raises(
        InvalidExternalEvidenceInterpretation,
        match="evidence_sha256 does not match",
    ):
        validate_external_evidence_claim_interpretation_review_v1(
            epistemic_snapshot=mutated_snapshot,
            catalog=catalog,
            candidate=candidate,
            review=review,
        )


def test_unrelated_later_epistemic_append_does_not_stale_review():
    snapshot, catalog, candidate, review = _review()
    later = EpistemicRecordSet(
        evidence_records=(snapshot.evidence_records[0], _external_evidence("b"))
    )

    validate_external_evidence_claim_interpretation_review_v1(
        epistemic_snapshot=later,
        catalog=catalog,
        candidate=candidate,
        review=review,
    )


def test_review_rejects_concept_revision_rebinding():
    snapshot, _, candidate, review = _review()
    with pytest.raises(
        InvalidExternalEvidenceInterpretation,
        match="exact concept revision",
    ):
        validate_external_evidence_claim_interpretation_review_v1(
            epistemic_snapshot=snapshot,
            catalog=_catalog(2),
            candidate=candidate,
            review=review,
        )


def test_review_rejects_proposal_id_rebinding():
    snapshot, catalog, candidate, review = _review()
    rebound = replace(
        review,
        proposal_id=ExternalEvidenceInterpretationProposalId("interpretation-other"),
    )
    with pytest.raises(
        InvalidExternalEvidenceInterpretation,
        match="proposal_id does not match",
    ):
        validate_external_evidence_claim_interpretation_review_v1(
            epistemic_snapshot=snapshot,
            catalog=catalog,
            candidate=candidate,
            review=rebound,
        )


def test_review_cannot_predate_candidate():
    snapshot, catalog, candidate = _candidate()
    with pytest.raises(
        InvalidExternalEvidenceInterpretation,
        match="must not precede candidate proposed_at",
    ):
        review_external_evidence_claim_interpretation_v1(
            epistemic_snapshot=snapshot,
            catalog=catalog,
            candidate=candidate,
            review_id=ExternalEvidenceInterpretationReviewId("review-early"),
            reviewer_ref=ExternalEvidenceInterpretationReviewerRef(
                ExternalEvidenceInterpretationReviewerKind.HUMAN,
                "human-reviewer-1",
            ),
            verdict=ExternalEvidenceInterpretationReviewVerdict.ACCEPT,
            reviewed_at=_time(11),
            rationale="Too early.",
        )


def test_review_digest_commits_verdict_reviewer_time_and_rationale():
    _, _, _, accepted = _review()
    rejected = replace(
        accepted,
        verdict=ExternalEvidenceInterpretationReviewVerdict.REJECT,
    )
    other_reviewer = replace(
        accepted,
        reviewer_ref=ExternalEvidenceInterpretationReviewerRef(
            ExternalEvidenceInterpretationReviewerKind.HUMAN,
            "human-reviewer-2",
        ),
    )
    later = replace(accepted, reviewed_at=_time(14))
    reason = replace(accepted, rationale="Different exact rationale.")

    base = external_evidence_claim_interpretation_review_sha256_v1(accepted)
    assert base != external_evidence_claim_interpretation_review_sha256_v1(rejected)
    assert base != external_evidence_claim_interpretation_review_sha256_v1(other_reviewer)
    assert base != external_evidence_claim_interpretation_review_sha256_v1(later)
    assert base != external_evidence_claim_interpretation_review_sha256_v1(reason)


def test_review_serialization_round_trip_is_deterministic():
    _, _, _, review = _review()
    as_dict = external_evidence_claim_interpretation_review_to_dict(review)
    as_json = external_evidence_claim_interpretation_review_to_json(review)

    assert external_evidence_claim_interpretation_review_from_dict(as_dict) == review
    assert external_evidence_claim_interpretation_review_from_json(as_json) == review
    assert as_json == external_evidence_claim_interpretation_review_to_json(review)
    assert (
        external_evidence_claim_interpretation_review_sha256_v1(review)
        == external_evidence_claim_interpretation_review_sha256_v1(
            external_evidence_claim_interpretation_review_from_json(as_json)
        )
    )


def test_review_serialization_rejects_unknown_missing_and_duplicate_keys():
    _, _, _, review = _review()
    payload = external_evidence_claim_interpretation_review_to_dict(review)

    unknown = dict(payload)
    unknown["bearing"] = "SUPPORTS"
    with pytest.raises(InvalidExternalEvidenceInterpretation, match="unknown="):
        external_evidence_claim_interpretation_review_from_dict(unknown)

    missing = dict(payload)
    missing.pop("candidate_sha256")
    with pytest.raises(InvalidExternalEvidenceInterpretation, match="missing="):
        external_evidence_claim_interpretation_review_from_dict(missing)

    duplicate = (
        '{"schema_version":1,"schema_version":1,'
        '"review_id":"review-1",'
        '"policy_ref":"capability_lab:external_evidence_claim_interpretation_human_review@1",'
        '"proposal_id":"interpretation-1",'
        '"candidate_sha256":"' + "a" * 64 + '",'
        '"reviewer_ref":{"kind":"HUMAN","ref":"human-reviewer-1"},'
        '"verdict":"ACCEPT","reviewed_at":"2026-08-29T13:00:00Z",'
        '"rationale":"x"}'
    )
    with pytest.raises(
        InvalidExternalEvidenceInterpretation,
        match="duplicate JSON object keys",
    ):
        external_evidence_claim_interpretation_review_from_json(duplicate)


def test_review_json_is_canonical_sorted_compact_ascii():
    _, _, _, review = _review()
    payload = external_evidence_claim_interpretation_review_to_dict(review)
    expected = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    assert external_evidence_claim_interpretation_review_to_json(review) == expected
