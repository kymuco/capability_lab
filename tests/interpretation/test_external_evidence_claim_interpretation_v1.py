from dataclasses import fields, replace
from datetime import datetime, timezone
import inspect
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
    EXTERNAL_EVIDENCE_CLAIM_INTERPRETATION_POLICY_V1,
    ExternalEvidenceClaimInterpretationCandidate,
    ExternalEvidenceInterpretationProposalId,
    ExternalEvidenceInterpretationProposerKind,
    ExternalEvidenceInterpretationProposerRef,
    InvalidExternalEvidenceInterpretation,
    external_evidence_claim_interpretation_candidate_from_dict,
    external_evidence_claim_interpretation_candidate_from_json,
    external_evidence_claim_interpretation_candidate_sha256_v1,
    external_evidence_claim_interpretation_candidate_to_dict,
    external_evidence_claim_interpretation_candidate_to_json,
    propose_external_evidence_claim_interpretation_v1,
    validate_external_evidence_claim_interpretation_candidate_v1,
)
from capability_lab.observations import REVIEWED_EXTERNAL_OBSERVATION_TO_EVIDENCE_POLICY_V1
from capability_lab.semantics import (
    CapabilityCatalog,
    CapabilityConcept,
    CapabilityConceptRef,
    CapabilityId,
    CapabilityNamespace,
)


def _time(hour: int) -> datetime:
    return datetime(2026, 8, 29, hour, 0, tzinfo=timezone.utc)


def _concept(revision: int = 1) -> CapabilityConcept:
    return CapabilityConcept(
        capability_id=CapabilityId.parse("research:signal_reasoning"),
        name="Signal reasoning",
        definition="Reason about structured technical signals and evidence.",
        revision=revision,
    )


def _catalog(revision: int = 1) -> CapabilityCatalog:
    return CapabilityCatalog(
        namespaces=(
            CapabilityNamespace(
                namespace_id="research",
                display_name="Research",
                description="Research capabilities.",
            ),
        ),
        concepts=(_concept(revision),),
    )


def _external_evidence(
    digest_char: str = "a",
    *,
    subject: str = "subject-1",
    summary: str = "Exact reviewed external observation.",
) -> EvidenceRecord:
    evidence_id = EvidenceId(f"external_observation:{digest_char * 64}")
    return EvidenceRecord(
        evidence_id=evidence_id,
        subject_ref=CapabilitySubjectRef(subject),
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


def _candidate(
    *,
    evidence: EvidenceRecord | None = None,
    catalog: CapabilityCatalog | None = None,
    concept_ref: CapabilityConceptRef | None = None,
):
    evidence = evidence or _external_evidence()
    catalog = catalog or _catalog()
    concept_ref = concept_ref or catalog.concepts[0].ref
    snapshot = EpistemicRecordSet(evidence_records=(evidence,))
    candidate = propose_external_evidence_claim_interpretation_v1(
        epistemic_snapshot=snapshot,
        evidence_id=evidence.evidence_id,
        catalog=catalog,
        concept_ref=concept_ref,
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


def test_pr12_2_proposes_exact_non_authoritative_interpretation():
    evidence = _external_evidence()
    snapshot, catalog, candidate = _candidate(evidence=evidence)

    assert candidate.policy_ref == EXTERNAL_EVIDENCE_CLAIM_INTERPRETATION_POLICY_V1
    assert candidate.evidence_id == evidence.evidence_id
    assert candidate.subject_ref == evidence.subject_ref
    assert candidate.concept_ref == catalog.concepts[0].ref
    assert candidate.claim_scope.tags == ("bounded_reasoning",)

    validate_external_evidence_claim_interpretation_candidate_v1(
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
    )


def test_subject_is_derived_and_not_caller_selectable():
    signature = inspect.signature(propose_external_evidence_claim_interpretation_v1)
    assert "subject_ref" not in signature.parameters

    snapshot, catalog, candidate = _candidate()
    rebound = replace(candidate, subject_ref=CapabilitySubjectRef("subject-2"))
    with pytest.raises(
        InvalidExternalEvidenceInterpretation,
        match="subject_ref does not match",
    ):
        validate_external_evidence_claim_interpretation_candidate_v1(
            epistemic_snapshot=snapshot,
            catalog=catalog,
            candidate=rebound,
        )


def test_exact_evidence_bytes_are_bound_not_only_evidence_id():
    evidence = _external_evidence()
    _, catalog, candidate = _candidate(evidence=evidence)
    mutated = replace(evidence, summary="Mutated bytes under the same EvidenceId.")
    mutated_snapshot = EpistemicRecordSet(evidence_records=(mutated,))

    with pytest.raises(
        InvalidExternalEvidenceInterpretation,
        match="evidence_sha256 does not match",
    ):
        validate_external_evidence_claim_interpretation_candidate_v1(
            epistemic_snapshot=mutated_snapshot,
            catalog=catalog,
            candidate=candidate,
        )


def test_unrelated_later_epistemic_append_does_not_stale_candidate():
    first = _external_evidence("a")
    second = _external_evidence("b")
    snapshot, catalog, candidate = _candidate(evidence=first)
    later = EpistemicRecordSet(evidence_records=(first, second))

    validate_external_evidence_claim_interpretation_candidate_v1(
        epistemic_snapshot=snapshot,
        catalog=catalog,
        candidate=candidate,
    )
    validate_external_evidence_claim_interpretation_candidate_v1(
        epistemic_snapshot=later,
        catalog=catalog,
        candidate=candidate,
    )


def test_exact_concept_revision_is_required():
    snapshot, _, candidate = _candidate(catalog=_catalog(1))
    with pytest.raises(
        InvalidExternalEvidenceInterpretation,
        match="exact concept revision",
    ):
        validate_external_evidence_claim_interpretation_candidate_v1(
            epistemic_snapshot=snapshot,
            catalog=_catalog(2),
            candidate=candidate,
        )


def test_candidate_digest_commits_exact_concept_and_scope():
    _, _, first = _candidate()
    second_catalog = _catalog(2)
    _, _, second = _candidate(
        catalog=second_catalog,
        concept_ref=second_catalog.concepts[0].ref,
    )
    scoped = replace(
        first,
        claim_scope=ClaimScope(
            "Different bounded claim scope.",
            ("bounded_reasoning", "diagnosis"),
        ),
    )

    assert (
        external_evidence_claim_interpretation_candidate_sha256_v1(first)
        != external_evidence_claim_interpretation_candidate_sha256_v1(second)
    )
    assert (
        external_evidence_claim_interpretation_candidate_sha256_v1(first)
        != external_evidence_claim_interpretation_candidate_sha256_v1(scoped)
    )


def test_proposal_cannot_predate_evidence_recording():
    evidence = _external_evidence()
    snapshot = EpistemicRecordSet(evidence_records=(evidence,))
    catalog = _catalog()

    with pytest.raises(
        InvalidExternalEvidenceInterpretation,
        match="must not predate",
    ):
        propose_external_evidence_claim_interpretation_v1(
            epistemic_snapshot=snapshot,
            evidence_id=evidence.evidence_id,
            catalog=catalog,
            concept_ref=catalog.concepts[0].ref,
            claim_statement="Bounded claim.",
            claim_scope=ClaimScope("Bounded scope."),
            proposer_ref=ExternalEvidenceInterpretationProposerRef(
                ExternalEvidenceInterpretationProposerKind.HUMAN,
                "human-proposer-1",
            ),
            proposal_id=ExternalEvidenceInterpretationProposalId("interpretation-early"),
            proposed_at=_time(10),
            rationale="Too early.",
        )


def test_selected_record_must_retain_pr12_1_external_evidence_shape():
    evidence = _external_evidence()
    broken = replace(
        evidence,
        provenance=ProvenanceTrail(
            sources=evidence.provenance.sources,
            steps=(
                replace(
                    evidence.provenance.steps[0],
                    mechanism_ref="capability_lab:other_policy@1",
                ),
            ),
        ),
    )
    snapshot = EpistemicRecordSet(evidence_records=(broken,))
    catalog = _catalog()

    with pytest.raises(
        InvalidExternalEvidenceInterpretation,
        match="frozen PR12.1 materialization policy",
    ):
        propose_external_evidence_claim_interpretation_v1(
            epistemic_snapshot=snapshot,
            evidence_id=broken.evidence_id,
            catalog=catalog,
            concept_ref=catalog.concepts[0].ref,
            claim_statement="Bounded claim.",
            claim_scope=ClaimScope("Bounded scope."),
            proposer_ref=ExternalEvidenceInterpretationProposerRef(
                ExternalEvidenceInterpretationProposerKind.MODEL,
                "model-proposer-1",
            ),
            proposal_id=ExternalEvidenceInterpretationProposalId("interpretation-broken"),
            proposed_at=_time(12),
            rationale="Should reject.",
        )


def test_candidate_surface_contains_no_evaluation_or_state_authority():
    names = {item.name for item in fields(ExternalEvidenceClaimInterpretationCandidate)}
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


def test_v1_proposer_kinds_are_only_human_and_model():
    assert set(ExternalEvidenceInterpretationProposerKind) == {
        ExternalEvidenceInterpretationProposerKind.HUMAN,
        ExternalEvidenceInterpretationProposerKind.MODEL,
    }
    with pytest.raises(ValueError):
        ExternalEvidenceInterpretationProposerKind("RULE")


def test_strict_serialization_round_trip_and_digest_are_deterministic():
    _, _, candidate = _candidate()

    as_dict = external_evidence_claim_interpretation_candidate_to_dict(candidate)
    as_json = external_evidence_claim_interpretation_candidate_to_json(candidate)

    assert external_evidence_claim_interpretation_candidate_from_dict(as_dict) == candidate
    assert external_evidence_claim_interpretation_candidate_from_json(as_json) == candidate
    assert as_json == external_evidence_claim_interpretation_candidate_to_json(candidate)
    assert (
        external_evidence_claim_interpretation_candidate_sha256_v1(candidate)
        == external_evidence_claim_interpretation_candidate_sha256_v1(
            external_evidence_claim_interpretation_candidate_from_json(as_json)
        )
    )


def test_strict_serialization_rejects_unknown_missing_and_duplicate_keys():
    _, _, candidate = _candidate()
    payload = external_evidence_claim_interpretation_candidate_to_dict(candidate)

    unknown = dict(payload)
    unknown["bearing"] = "supports"
    with pytest.raises(
        InvalidExternalEvidenceInterpretation,
        match="unknown=",
    ):
        external_evidence_claim_interpretation_candidate_from_dict(unknown)

    missing = dict(payload)
    missing.pop("concept_ref")
    with pytest.raises(
        InvalidExternalEvidenceInterpretation,
        match="missing=",
    ):
        external_evidence_claim_interpretation_candidate_from_dict(missing)

    duplicate = (
        '{"schema_version":1,"schema_version":1,'
        '"proposal_id":"x","policy_ref":"capability_lab:external_evidence_claim_interpretation_proposal@1",'
        '"evidence_id":"external_observation:' + "a" * 64 + '",'
        '"evidence_sha256":"' + "b" * 64 + '",'
        '"subject_ref":"subject-1","concept_ref":"research:signal_reasoning@1",'
        '"claim_statement":"x","claim_scope":{"description":"x","tags":[]},'
        '"proposer_ref":{"kind":"MODEL","ref":"model-1"},'
        '"proposed_at":"2026-08-29T12:00:00Z","rationale":"x"}'
    )
    with pytest.raises(
        InvalidExternalEvidenceInterpretation,
        match="duplicate JSON object keys",
    ):
        external_evidence_claim_interpretation_candidate_from_json(duplicate)


def test_json_output_is_canonical_sorted_compact_ascii():
    _, _, candidate = _candidate()
    payload = external_evidence_claim_interpretation_candidate_to_dict(candidate)
    expected = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    assert external_evidence_claim_interpretation_candidate_to_json(candidate) == expected
