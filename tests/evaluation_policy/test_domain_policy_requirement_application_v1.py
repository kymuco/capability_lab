from dataclasses import fields, replace
from datetime import datetime, timezone
import ast
import inspect
import json
import os

import pytest

import capability_lab.evaluation_policy.requirement_application as application_module
from capability_lab.epistemics import (
    CapabilityClaim,
    CapabilityClaimId,
    CapabilitySubjectRef,
    ClaimScope,
    EpistemicRecordSet,
    EvaluationPolicyRef,
    EvidenceAssessment,
    EvidenceBearing,
    EvidenceContext,
    EvidenceId,
    EvidenceKind,
    EvidenceRecord,
    EvidenceReliability,
    ProvenanceSource,
    ProvenanceSourceKind,
    ProvenanceTrail,
    build_claim_evidence_disposition_coverage_v1,
    build_claim_evidence_lineage_dependence_v1,
)
from capability_lab.evaluation_policy import (
    ClaimDomainPolicyRequirementApplicationReceipt,
    ClaimDomainPolicyRequirementMappingProposal,
    ClaimPolicyRequirementMappingReviewAdmission,
    ClaimPolicyRequirementMappingReviewId,
    ClaimPolicyRequirementMappingReviewerKind,
    ClaimPolicyRequirementMappingReviewerRef,
    ClaimPolicyRequirementMappingReviewLedger,
    ClaimPolicyRequirementMappingReviewVerdict,
    DomainEvaluationPolicyRegistry,
    DomainEvaluationPolicyRequirement,
    DomainEvaluationPolicyReviewId,
    DomainEvaluationPolicyReviewerKind,
    DomainEvaluationPolicyReviewerRef,
    DomainEvaluationPolicyReviewLedger,
    DomainEvaluationPolicyReviewVerdict,
    DomainEvaluationPolicySpecification,
    DomainPolicyRequirementApplicationDisposition,
    DomainPolicyRequirementApplicationEntry,
    InvalidDomainPolicyRequirementApplication,
    admit_claim_policy_requirement_mapping_review_v1,
    admit_domain_evaluation_policy_review_v1,
    admit_domain_evaluation_policy_v1,
    apply_admitted_domain_policy_requirements_v1,
    build_claim_domain_policy_requirement_mapping_proposal_v1,
    claim_domain_policy_requirement_application_receipt_from_json,
    claim_domain_policy_requirement_mapping_proposal_from_json,
    claim_domain_policy_requirement_mapping_proposal_sha256_v1,
    claim_policy_requirement_mapping_review_from_json,
    claim_policy_requirement_mapping_review_ledger_from_json,
    domain_evaluation_policy_specification_sha256_v1,
    review_claim_domain_policy_requirement_mapping_proposal_v1,
    review_domain_evaluation_policy_specification_v1,
    validate_claim_domain_policy_requirement_application_v1,
    validate_claim_domain_policy_requirement_mapping_proposal_v1,
    validate_claim_policy_requirement_mapping_review_admission_v1,
)
from capability_lab.semantics import CapabilityConceptRef, CapabilityId


def _time(hour: int) -> datetime:
    return datetime(2026, 9, 1, hour, 0, tzinfo=timezone.utc)


def _concept(revision: int = 1) -> CapabilityConceptRef:
    return CapabilityConceptRef(CapabilityId.parse("research:signal_reasoning"), revision)


def _scope(description: str = "Bounded signal interpretation.") -> ClaimScope:
    return ClaimScope(description, ("bounded_reasoning", "signal_evidence"))


def _claim(*, concept=None, scope=None) -> CapabilityClaim:
    return CapabilityClaim(
        claim_id=CapabilityClaimId("claim_1"),
        subject_ref=CapabilitySubjectRef("subject_1"),
        concept_ref=concept or _concept(),
        statement="The subject can reason about bounded signal evidence.",
        scope=scope or _scope(),
        created_at=_time(9),
        provenance=ProvenanceTrail(
            sources=(ProvenanceSource(ProvenanceSourceKind.SYSTEM, "claim_system"),)
        ),
    )


def _evidence(
    evidence_id: str,
    *,
    recorded_hour: int,
    sources: tuple[ProvenanceSource, ...] | None = None,
) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=EvidenceId(evidence_id),
        subject_ref=CapabilitySubjectRef("subject_1"),
        kind=EvidenceKind.ARTIFACT,
        summary=f"Evidence {evidence_id}.",
        context=EvidenceContext("Bounded signal case.", ("signal_evidence",)),
        observed_at=_time(recorded_hour - 1),
        recorded_at=_time(recorded_hour),
        provenance=ProvenanceTrail(
            sources=sources
            or (ProvenanceSource(ProvenanceSourceKind.SYSTEM, f"system_{evidence_id}"),)
        ),
    )


def _assessment(
    evidence_id: str,
    *,
    bearing: EvidenceBearing = EvidenceBearing.SUPPORTS,
    reliability: EvidenceReliability = EvidenceReliability.UNASSESSED,
) -> EvidenceAssessment:
    return EvidenceAssessment(
        evidence_id=EvidenceId(evidence_id),
        bearing=bearing,
        reliability=reliability,
        coverage_note=f"Coverage {evidence_id}.",
        rationale=f"Disposition {evidence_id}.",
    )


def _records(*, claim=None, evidence=None):
    target = claim or _claim()
    items = evidence
    if items is None:
        items = (_evidence("e1", recorded_hour=11), _evidence("e2", recorded_hour=12))
    return EpistemicRecordSet(evidence_records=items, claims=(target,)), target


def _coverage_lineage(records, claim, *, dispositions=None):
    if dispositions is None:
        dispositions = tuple(_assessment(item.evidence_id.value) for item in records.evidence_records)
    coverage = build_claim_evidence_disposition_coverage_v1(
        records=records,
        claim_id=claim.claim_id,
        as_of=_time(14),
        dispositions=dispositions,
    )
    lineage = build_claim_evidence_lineage_dependence_v1(
        records=records,
        claim_id=claim.claim_id,
        as_of=_time(14),
        coverage=coverage,
    )
    return coverage, lineage


def _spec(*, policy_revision=1, concept=None, scope=None, changed=False):
    return DomainEvaluationPolicySpecification(
        policy_ref=EvaluationPolicyRef("research", "signal_reasoning_human_review", policy_revision),
        concept_ref=concept or _concept(),
        claim_scope=scope or _scope(),
        requirements=(
            DomainEvaluationPolicyRequirement(
                "diagnostic_reasoning",
                "Diagnoses one bounded signal case." if not changed else "Diagnoses the case and an alternative.",
                True,
            ),
            DomainEvaluationPolicyRequirement(
                "edge_case_awareness",
                "Identifies relevant edge-case limits.",
                False,
            ),
            DomainEvaluationPolicyRequirement(
                "explanation_quality",
                "Explains the relevant signal structure accurately.",
                True,
            ),
        ),
    )


def _admit_policy(specification, *, admitted_hour=8):
    review = review_domain_evaluation_policy_specification_v1(
        specification=specification,
        review_id=DomainEvaluationPolicyReviewId(f"policy-review-{specification.policy_ref.revision}"),
        reviewer_ref=DomainEvaluationPolicyReviewerRef(
            DomainEvaluationPolicyReviewerKind.HUMAN,
            "human:policy_reviewer",
        ),
        verdict=DomainEvaluationPolicyReviewVerdict.APPROVE,
        reviewed_at=_time(7),
        rationale="Reviewed exact policy specification.",
    )
    review_ledger, review_admission = admit_domain_evaluation_policy_review_v1(
        review_ledger=DomainEvaluationPolicyReviewLedger(),
        specification=specification,
        review=review,
    )
    registry, _ = admit_domain_evaluation_policy_v1(
        registry=DomainEvaluationPolicyRegistry(),
        review_ledger=review_ledger,
        review_admission=review_admission,
        specification=specification,
        admitted_at=_time(admitted_hour),
    )
    return registry


def _entry(key, disposition, evidence_ids=()):
    return DomainPolicyRequirementApplicationEntry(
        requirement_key=key,
        disposition=disposition,
        evidence_ids=tuple(EvidenceId(item) for item in evidence_ids),
        rationale=f"Human mapping judgment for {key}.",
    )


def _entries(*, diagnostic="covered", edge="unresolved", explanation="covered", explanation_ids=("e2",)):
    lookup = {
        "covered": DomainPolicyRequirementApplicationDisposition.COVERED,
        "not_covered": DomainPolicyRequirementApplicationDisposition.NOT_COVERED,
        "unresolved": DomainPolicyRequirementApplicationDisposition.UNRESOLVED,
    }

    def build(key, state, ids):
        return _entry(key, lookup[state], ids if state == "covered" else ())

    return (
        build("diagnostic_reasoning", diagnostic, ("e1",)),
        build("edge_case_awareness", edge, ("e2",)),
        build("explanation_quality", explanation, explanation_ids),
    )


def _proposal_basis(*, records=None, claim=None, coverage=None, lineage=None, specification=None, registry=None, entries=None):
    if records is None or claim is None:
        records, claim = _records()
    if coverage is None or lineage is None:
        coverage, lineage = _coverage_lineage(records, claim)
    specification = specification or _spec(concept=claim.concept_ref, scope=claim.scope)
    registry = registry or _admit_policy(specification)
    proposal = build_claim_domain_policy_requirement_mapping_proposal_v1(
        records=records,
        claim_id=claim.claim_id,
        as_of=_time(14),
        coverage=coverage,
        lineage=lineage,
        registry=registry,
        policy_ref=specification.policy_ref,
        specification_sha256=domain_evaluation_policy_specification_sha256_v1(specification),
        requirement_applications=entries or _entries(),
    )
    return records, claim, coverage, lineage, specification, registry, proposal


def _review_and_admit(proposal, *, verdict=ClaimPolicyRequirementMappingReviewVerdict.APPROVE, ledger=None, review_id="mapping-review-1", reviewed_hour=15):
    review = review_claim_domain_policy_requirement_mapping_proposal_v1(
        proposal=proposal,
        review_id=ClaimPolicyRequirementMappingReviewId(review_id),
        reviewer_ref=ClaimPolicyRequirementMappingReviewerRef(
            ClaimPolicyRequirementMappingReviewerKind.HUMAN,
            "human:mapping_reviewer",
        ),
        verdict=verdict,
        reviewed_at=_time(reviewed_hour),
        rationale="Reviewed exact requirement mapping proposal.",
    )
    ledger = ledger or ClaimPolicyRequirementMappingReviewLedger()
    successor, admission = admit_claim_policy_requirement_mapping_review_v1(
        review_ledger=ledger,
        proposal=proposal,
        review=review,
    )
    return successor, admission, review


def _full(*, entries=None, dispositions=None):
    records, claim = _records()
    coverage, lineage = _coverage_lineage(records, claim, dispositions=dispositions)
    specification = _spec(concept=claim.concept_ref, scope=claim.scope)
    registry = _admit_policy(specification)
    _, _, _, _, _, _, proposal = _proposal_basis(
        records=records,
        claim=claim,
        coverage=coverage,
        lineage=lineage,
        specification=specification,
        registry=registry,
        entries=entries,
    )
    ledger, admission, review = _review_and_admit(proposal)
    application = apply_admitted_domain_policy_requirements_v1(
        records=records,
        claim_id=claim.claim_id,
        as_of=_time(14),
        coverage=coverage,
        lineage=lineage,
        registry=registry,
        proposal=proposal,
        review_ledger=ledger,
        review_admission=admission,
    )
    return records, claim, coverage, lineage, specification, registry, proposal, ledger, admission, review, application


def test_exact_authorized_policy_complete_mapping_human_approve_applies():
    *basis, application = _full()
    assert application.required_requirement_coverage_complete is True
    assert tuple(item.requirement_key for item in application.requirement_applications) == (
        "diagnostic_reasoning", "edge_case_awareness", "explanation_quality"
    )


def test_every_requirement_including_optional_requires_explicit_entry():
    entries = tuple(item for item in _entries() if item.requirement_key != "edge_case_awareness")
    with pytest.raises(InvalidDomainPolicyRequirementApplication, match="omits admitted policy requirement"):
        _proposal_basis(entries=entries)


def test_unknown_and_duplicate_requirement_keys_fail_closed():
    with pytest.raises(InvalidDomainPolicyRequirementApplication, match="unknown policy requirement"):
        _proposal_basis(entries=_entries() + (_entry("invented", DomainPolicyRequirementApplicationDisposition.UNRESOLVED),))
    with pytest.raises(InvalidDomainPolicyRequirementApplication, match="exactly one entry"):
        _proposal_basis(entries=_entries() + (_entry("diagnostic_reasoning", DomainPolicyRequirementApplicationDisposition.UNRESOLVED),))


def test_covered_requires_evidence_and_other_states_forbid_evidence():
    with pytest.raises(InvalidDomainPolicyRequirementApplication, match="at least one evidence id"):
        _entry("diagnostic_reasoning", DomainPolicyRequirementApplicationDisposition.COVERED)
    for state in (
        DomainPolicyRequirementApplicationDisposition.NOT_COVERED,
        DomainPolicyRequirementApplicationDisposition.UNRESOLVED,
    ):
        with pytest.raises(InvalidDomainPolicyRequirementApplication, match="require empty evidence_ids"):
            _entry("diagnostic_reasoning", state, ("e1",))


@pytest.mark.parametrize("bearing", [EvidenceBearing.SUPPORTS, EvidenceBearing.CONTRADICTS, EvidenceBearing.INDETERMINATE])
def test_support_contradiction_and_indeterminate_can_all_cover_semantic_requirement(bearing):
    dispositions = (_assessment("e1", bearing=bearing), _assessment("e2"))
    *_, application = _full(dispositions=dispositions)
    assert application.required_requirement_coverage_complete is True


def test_not_relevant_cannot_satisfy_requirement():
    records, claim = _records()
    coverage, lineage = _coverage_lineage(
        records,
        claim,
        dispositions=(_assessment("e1", bearing=EvidenceBearing.NOT_RELEVANT), _assessment("e2")),
    )
    with pytest.raises(InvalidDomainPolicyRequirementApplication, match="NOT_RELEVANT"):
        _proposal_basis(records=records, claim=claim, coverage=coverage, lineage=lineage)


def test_reliability_does_not_change_mapping_coverage_semantics():
    for reliability in EvidenceReliability:
        dispositions = (
            _assessment("e1", reliability=reliability),
            _assessment("e2", reliability=reliability),
        )
        *_, application = _full(dispositions=dispositions)
        assert application.required_requirement_coverage_complete is True


def test_one_evidence_can_cover_multiple_requirements_without_weight_field():
    entries = _entries(explanation_ids=("e1",))
    *_, application = _full(entries=entries)
    assert application.requirement_applications[0].evidence_ids == (EvidenceId("e1"),)
    assert application.requirement_applications[2].evidence_ids == (EvidenceId("e1"),)
    assert "weight" not in {field.name for field in fields(DomainPolicyRequirementApplicationEntry)}


def test_multiple_evidence_can_jointly_cover_one_requirement_without_count_semantics():
    entries = _entries(explanation_ids=("e1", "e2"))
    *_, application = _full(entries=entries)
    assert application.required_requirement_coverage_complete is True
    assert not {"count", "score", "weight", "independent"} & {
        field.name for field in fields(ClaimDomainPolicyRequirementApplicationReceipt)
    }


def test_required_not_covered_and_unresolved_make_required_coverage_incomplete():
    for state in ("not_covered", "unresolved"):
        *_, application = _full(entries=_entries(diagnostic=state))
        assert application.required_requirement_coverage_complete is False


def test_optional_not_covered_or_unresolved_does_not_affect_required_coverage():
    for state in ("not_covered", "unresolved"):
        *_, application = _full(entries=_entries(edge=state))
        assert application.required_requirement_coverage_complete is True


def test_raw_mapping_proposal_is_not_application_authority():
    records, claim, coverage, lineage, _, registry, proposal = _proposal_basis()
    signature = inspect.signature(apply_admitted_domain_policy_requirements_v1)
    assert "review_admission" in signature.parameters
    with pytest.raises(TypeError, match="review_ledger"):
        apply_admitted_domain_policy_requirements_v1(
            records=records,
            claim_id=claim.claim_id,
            as_of=_time(14),
            coverage=coverage,
            lineage=lineage,
            registry=registry,
            proposal=proposal,
        )


def test_raw_human_approve_review_without_terminal_admission_is_not_authority():
    records, claim, coverage, lineage, _, registry, proposal = _proposal_basis()
    review = review_claim_domain_policy_requirement_mapping_proposal_v1(
        proposal=proposal,
        review_id=ClaimPolicyRequirementMappingReviewId("raw-review"),
        reviewer_ref=ClaimPolicyRequirementMappingReviewerRef(ClaimPolicyRequirementMappingReviewerKind.HUMAN, "human:reviewer"),
        verdict=ClaimPolicyRequirementMappingReviewVerdict.APPROVE,
        reviewed_at=_time(15),
        rationale="Raw approval is audit data only.",
    )
    raw_ledger = ClaimPolicyRequirementMappingReviewLedger(reviews=(review,))
    with pytest.raises(TypeError, match="review_admission"):
        apply_admitted_domain_policy_requirements_v1(
            records=records,
            claim_id=claim.claim_id,
            as_of=_time(14),
            coverage=coverage,
            lineage=lineage,
            registry=registry,
            proposal=proposal,
            review_ledger=raw_ledger,
        )


def test_forged_review_admission_fails_process_authority_check():
    _, _, _, _, _, _, proposal = _proposal_basis()
    ledger, _, review = _review_and_admit(proposal)
    forged = object.__new__(ClaimPolicyRequirementMappingReviewAdmission)
    object.__setattr__(forged, "claim_id", proposal.claim_id)
    object.__setattr__(forged, "policy_ref", proposal.policy_ref)
    object.__setattr__(forged, "mapping_proposal_sha256", claim_domain_policy_requirement_mapping_proposal_sha256_v1(proposal))
    object.__setattr__(forged, "review_id", review.review_id)
    object.__setattr__(forged, "review_sha256", application_module.claim_policy_requirement_mapping_review_sha256_v1(review))
    object.__setattr__(forged, "predecessor_review_ledger_sha256", application_module.claim_policy_requirement_mapping_review_ledger_sha256_v1(ClaimPolicyRequirementMappingReviewLedger()))
    object.__setattr__(forged, "successor_review_ledger_sha256", application_module.claim_policy_requirement_mapping_review_ledger_sha256_v1(ledger))
    object.__setattr__(forged, "review_ledger_sha256", application_module.claim_policy_requirement_mapping_review_ledger_sha256_v1(ledger))
    with pytest.raises(InvalidDomainPolicyRequirementApplication, match="was not issued"):
        validate_claim_policy_requirement_mapping_review_admission_v1(
            review_ledger=ledger,
            proposal=proposal,
            review_admission=forged,
        )


def test_exact_review_replay_is_ledger_idempotent_and_issues_fresh_authority():
    *_, proposal = _proposal_basis()
    ledger, admission1, review = _review_and_admit(proposal)
    replay, admission2 = admit_claim_policy_requirement_mapping_review_v1(
        review_ledger=ledger,
        proposal=proposal,
        review=review,
    )
    assert replay == ledger
    assert admission1 is not admission2
    assert validate_claim_policy_requirement_mapping_review_admission_v1(
        review_ledger=replay,
        proposal=proposal,
        review_admission=admission2,
    ) == review


def test_reject_review_can_be_admitted_but_cannot_apply():
    records, claim, coverage, lineage, _, registry, proposal = _proposal_basis()
    ledger, admission, _ = _review_and_admit(
        proposal,
        verdict=ClaimPolicyRequirementMappingReviewVerdict.REJECT,
    )
    with pytest.raises(InvalidDomainPolicyRequirementApplication, match="REJECT"):
        apply_admitted_domain_policy_requirements_v1(
            records=records,
            claim_id=claim.claim_id,
            as_of=_time(14),
            coverage=coverage,
            lineage=lineage,
            registry=registry,
            proposal=proposal,
            review_ledger=ledger,
            review_admission=admission,
        )


def test_conflicting_terminal_review_for_same_proposal_fails_closed():
    *_, proposal = _proposal_basis()
    ledger, _, _ = _review_and_admit(proposal)
    conflicting = review_claim_domain_policy_requirement_mapping_proposal_v1(
        proposal=proposal,
        review_id=ClaimPolicyRequirementMappingReviewId("mapping-review-conflict"),
        reviewer_ref=ClaimPolicyRequirementMappingReviewerRef(ClaimPolicyRequirementMappingReviewerKind.HUMAN, "human:reviewer"),
        verdict=ClaimPolicyRequirementMappingReviewVerdict.REJECT,
        reviewed_at=_time(15),
        rationale="Conflicting review.",
    )
    with pytest.raises(InvalidDomainPolicyRequirementApplication, match="different terminal review"):
        admit_claim_policy_requirement_mapping_review_v1(
            review_ledger=ledger,
            proposal=proposal,
            review=conflicting,
        )


def test_review_time_must_follow_as_of_and_policy_admission():
    *_, proposal = _proposal_basis()
    for hour, match in ((13, "proposal as_of"), (7, "proposal as_of")):
        with pytest.raises(InvalidDomainPolicyRequirementApplication, match=match):
            _review_and_admit(proposal, reviewed_hour=hour)


def test_review_authority_becomes_stale_after_review_ledger_growth():
    records, claim, coverage, lineage, specification, registry, proposal1 = _proposal_basis()
    ledger1, admission1, _ = _review_and_admit(proposal1, review_id="review-1")
    proposal2 = build_claim_domain_policy_requirement_mapping_proposal_v1(
        records=records,
        claim_id=claim.claim_id,
        as_of=_time(14),
        coverage=coverage,
        lineage=lineage,
        registry=registry,
        policy_ref=specification.policy_ref,
        specification_sha256=domain_evaluation_policy_specification_sha256_v1(specification),
        requirement_applications=_entries(edge="covered"),
    )
    review2 = review_claim_domain_policy_requirement_mapping_proposal_v1(
        proposal=proposal2,
        review_id=ClaimPolicyRequirementMappingReviewId("review-2"),
        reviewer_ref=ClaimPolicyRequirementMappingReviewerRef(ClaimPolicyRequirementMappingReviewerKind.HUMAN, "human:reviewer"),
        verdict=ClaimPolicyRequirementMappingReviewVerdict.APPROVE,
        reviewed_at=_time(16),
        rationale="Second exact proposal.",
    )
    ledger2, _ = admit_claim_policy_requirement_mapping_review_v1(
        review_ledger=ledger1,
        proposal=proposal2,
        review=review2,
    )
    with pytest.raises(InvalidDomainPolicyRequirementApplication, match="stale"):
        validate_claim_policy_requirement_mapping_review_admission_v1(
            review_ledger=ledger2,
            proposal=proposal1,
            review_admission=admission1,
        )


def test_json_restored_policy_registry_without_runtime_authority_is_rejected():
    records, claim = _records()
    coverage, lineage = _coverage_lineage(records, claim)
    specification = _spec(concept=claim.concept_ref, scope=claim.scope)
    registry = _admit_policy(specification)
    restored = DomainEvaluationPolicyRegistry.from_json(registry.to_json())
    with pytest.raises(InvalidDomainPolicyRequirementApplication, match="runtime admission authority"):
        build_claim_domain_policy_requirement_mapping_proposal_v1(
            records=records,
            claim_id=claim.claim_id,
            as_of=_time(14),
            coverage=coverage,
            lineage=lineage,
            registry=restored,
            policy_ref=specification.policy_ref,
            specification_sha256=domain_evaluation_policy_specification_sha256_v1(specification),
            requirement_applications=_entries(),
        )


def test_wrong_policy_digest_scope_and_concept_revision_are_rejected():
    records, claim = _records()
    coverage, lineage = _coverage_lineage(records, claim)
    specification = _spec(concept=claim.concept_ref, scope=claim.scope)
    registry = _admit_policy(specification)
    with pytest.raises(InvalidDomainPolicyRequirementApplication, match="admitted policy resolution failed"):
        build_claim_domain_policy_requirement_mapping_proposal_v1(
            records=records, claim_id=claim.claim_id, as_of=_time(14), coverage=coverage, lineage=lineage,
            registry=registry, policy_ref=specification.policy_ref, specification_sha256="0" * 64,
            requirement_applications=_entries(),
        )
    for mismatch in (
        _spec(policy_revision=2, concept=_concept(2), scope=claim.scope),
        _spec(policy_revision=2, concept=claim.concept_ref, scope=_scope("Different exact scope.")),
    ):
        mismatch_registry = _admit_policy(mismatch)
        with pytest.raises(InvalidDomainPolicyRequirementApplication, match="does not apply"):
            build_claim_domain_policy_requirement_mapping_proposal_v1(
                records=records, claim_id=claim.claim_id, as_of=_time(14), coverage=coverage, lineage=lineage,
                registry=mismatch_registry, policy_ref=mismatch.policy_ref,
                specification_sha256=domain_evaluation_policy_specification_sha256_v1(mismatch),
                requirement_applications=_entries(),
            )


def test_evidence_outside_exact_pr12_9_universe_is_rejected():
    entries = (
        _entry("diagnostic_reasoning", DomainPolicyRequirementApplicationDisposition.COVERED, ("outside",)),
        _entry("edge_case_awareness", DomainPolicyRequirementApplicationDisposition.UNRESOLVED),
        _entry("explanation_quality", DomainPolicyRequirementApplicationDisposition.COVERED, ("e2",)),
    )
    with pytest.raises(InvalidDomainPolicyRequirementApplication, match="outside exact PR12.9"):
        _proposal_basis(entries=entries)


def test_tampered_pr12_9_and_pr12_10_basis_fail_replay():
    records, claim = _records()
    coverage, lineage = _coverage_lineage(records, claim)
    with pytest.raises(InvalidDomainPolicyRequirementApplication, match="PR12.9"):
        _proposal_basis(records=records, claim=claim, coverage=replace(coverage, snapshot_sha256="0" * 64), lineage=lineage)
    with pytest.raises(InvalidDomainPolicyRequirementApplication, match="PR12.10"):
        _proposal_basis(records=records, claim=claim, coverage=coverage, lineage=replace(lineage, disposition_coverage_sha256="0" * 64))


def test_stale_proposal_fails_after_snapshot_or_claim_change():
    records, claim, coverage, lineage, _, registry, proposal = _proposal_basis()
    changed_records = EpistemicRecordSet(
        evidence_records=records.evidence_records + (_evidence("e3", recorded_hour=13),),
        claims=records.claims,
    )
    with pytest.raises(InvalidDomainPolicyRequirementApplication):
        validate_claim_domain_policy_requirement_mapping_proposal_v1(
            records=changed_records,
            claim_id=claim.claim_id,
            as_of=_time(14),
            coverage=coverage,
            lineage=lineage,
            registry=registry,
            proposal=proposal,
        )


def test_changed_policy_content_invalidates_stale_proposal():
    records, claim, coverage, lineage, specification, _, proposal = _proposal_basis()
    changed = _spec(policy_revision=2, concept=claim.concept_ref, scope=claim.scope, changed=True)
    changed_registry = _admit_policy(changed)
    with pytest.raises(InvalidDomainPolicyRequirementApplication, match="admitted policy resolution failed"):
        validate_claim_domain_policy_requirement_mapping_proposal_v1(
            records=records,
            claim_id=claim.claim_id,
            as_of=_time(14),
            coverage=coverage,
            lineage=lineage,
            registry=changed_registry,
            proposal=proposal,
        )


def test_proposal_review_ledger_and_application_json_are_strict_canonical_audit_data():
    records, claim, coverage, lineage, _, registry, proposal, ledger, admission, review, application = _full()
    assert claim_domain_policy_requirement_mapping_proposal_from_json(proposal.to_json()) == proposal
    assert claim_policy_requirement_mapping_review_from_json(review.to_json()) == review
    assert claim_policy_requirement_mapping_review_ledger_from_json(ledger.to_json()) == ledger
    restored_application = claim_domain_policy_requirement_application_receipt_from_json(application.to_json())
    assert validate_claim_domain_policy_requirement_application_v1(
        records=records,
        claim_id=claim.claim_id,
        as_of=_time(14),
        coverage=coverage,
        lineage=lineage,
        registry=registry,
        proposal=proposal,
        review_ledger=ledger,
        review_admission=admission,
        application=restored_application,
    ) == application


def test_json_duplicate_unknown_and_noncanonical_encoding_fail_closed():
    *_, proposal = _proposal_basis()
    encoded = proposal.to_json()
    duplicate = encoded[:-1] + ',"schema_version":1}'
    with pytest.raises(InvalidDomainPolicyRequirementApplication, match="duplicate JSON object key"):
        claim_domain_policy_requirement_mapping_proposal_from_json(duplicate)
    payload = proposal.to_dict()
    payload["unknown"] = True
    with pytest.raises(InvalidDomainPolicyRequirementApplication, match="unknown field"):
        ClaimDomainPolicyRequirementMappingProposal.from_dict(payload)
    pretty = json.dumps(proposal.to_dict(), indent=2, sort_keys=True)
    with pytest.raises(InvalidDomainPolicyRequirementApplication, match="canonical encoding"):
        claim_domain_policy_requirement_mapping_proposal_from_json(pretty)


def test_post_construction_mutation_is_detected_by_complete_replay():
    records, claim, coverage, lineage, _, registry, proposal = _proposal_basis()
    object.__setattr__(proposal, "specification_sha256", "0" * 64)
    with pytest.raises(InvalidDomainPolicyRequirementApplication):
        validate_claim_domain_policy_requirement_mapping_proposal_v1(
            records=records,
            claim_id=claim.claim_id,
            as_of=_time(14),
            coverage=coverage,
            lineage=lineage,
            registry=registry,
            proposal=proposal,
        )


def test_no_claim_wide_conclusion_or_state_authority_in_public_receipt():
    names = {field.name for field in fields(ClaimDomainPolicyRequirementApplicationReceipt)}
    assert "conclusion" not in names
    assert "coverage_status" not in names
    assert "score" not in names
    assert "mastery" not in names
    assert "readiness" not in names


def test_no_automatic_mapper_or_cardinality_independence_inputs_in_builder():
    signature = inspect.signature(build_claim_domain_policy_requirement_mapping_proposal_v1)
    assert "requirement_applications" in signature.parameters
    forbidden = {
        "classifier", "model", "minimum_count", "source_count", "independence_count",
        "majority", "weight", "score", "recency_weight",
    }
    assert forbidden.isdisjoint(signature.parameters)


def test_requirement_application_import_surface_excludes_downstream_authority():
    source = inspect.getsource(application_module)
    tree = ast.parse(source)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    for forbidden in ("derivation", "history", "progression", "player_window", "pilot", "hde"):
        assert not any(forbidden in module for module in imported)


@pytest.mark.skipif(not hasattr(os, "fork"), reason="POSIX fork required")
def test_fork_child_cannot_reuse_parent_mapping_review_authority_but_can_replay():
    records, claim, coverage, lineage, specification, registry, proposal = _proposal_basis()
    ledger, parent_admission, review = _review_and_admit(proposal)
    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(read_fd)
        result = []
        try:
            validate_claim_policy_requirement_mapping_review_admission_v1(
                review_ledger=ledger,
                proposal=proposal,
                review_admission=parent_admission,
            )
            result.append("parent_reused")
        except InvalidDomainPolicyRequirementApplication:
            result.append("parent_blocked")
        try:
            child_registry = _admit_policy(specification)
            replay_ledger, child_admission = admit_claim_policy_requirement_mapping_review_v1(
                review_ledger=ledger,
                proposal=proposal,
                review=review,
            )
            apply_admitted_domain_policy_requirements_v1(
                records=records,
                claim_id=claim.claim_id,
                as_of=_time(14),
                coverage=coverage,
                lineage=lineage,
                registry=child_registry,
                proposal=proposal,
                review_ledger=replay_ledger,
                review_admission=child_admission,
            )
            result.append("child_replayed")
        except Exception as exc:
            result.append(f"child_failed:{type(exc).__name__}:{exc}")
        os.write(write_fd, "|".join(result).encode("utf-8"))
        os.close(write_fd)
        os._exit(0)
    os.close(write_fd)
    payload = os.read(read_fd, 4096).decode("utf-8")
    os.close(read_fd)
    _, status = os.waitpid(pid, 0)
    assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
    assert payload == "parent_blocked|child_replayed"
