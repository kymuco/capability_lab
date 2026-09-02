from dataclasses import replace
from datetime import datetime, timezone

import pytest

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
    domain_evaluation_policy_specification_sha256_v1,
    review_claim_domain_policy_requirement_mapping_proposal_v1,
    review_domain_evaluation_policy_specification_v1,
    validate_claim_domain_policy_requirement_application_v1,
    validate_claim_domain_policy_requirement_mapping_proposal_v1,
)
from capability_lab.semantics import CapabilityConceptRef, CapabilityId


def _time(hour: int) -> datetime:
    return datetime(2026, 9, 1, hour, 0, tzinfo=timezone.utc)


def _concept() -> CapabilityConceptRef:
    return CapabilityConceptRef(CapabilityId.parse("research:signal_reasoning"), 1)


def _scope() -> ClaimScope:
    return ClaimScope(
        "Bounded signal interpretation.",
        ("bounded_reasoning", "signal_evidence"),
    )


def _claim(*, statement: str = "The subject can reason about bounded signal evidence.") -> CapabilityClaim:
    return CapabilityClaim(
        claim_id=CapabilityClaimId("claim_1"),
        subject_ref=CapabilitySubjectRef("subject_1"),
        concept_ref=_concept(),
        statement=statement,
        scope=_scope(),
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


def _assessment(evidence_id: str) -> EvidenceAssessment:
    return EvidenceAssessment(
        evidence_id=EvidenceId(evidence_id),
        bearing=EvidenceBearing.SUPPORTS,
        reliability=EvidenceReliability.UNASSESSED,
        coverage_note=f"Coverage {evidence_id}.",
        rationale=f"Disposition {evidence_id}.",
    )


def _specification() -> DomainEvaluationPolicySpecification:
    return DomainEvaluationPolicySpecification(
        policy_ref=EvaluationPolicyRef("research", "signal_reasoning_human_review", 1),
        concept_ref=_concept(),
        claim_scope=_scope(),
        requirements=(
            DomainEvaluationPolicyRequirement(
                "diagnostic_reasoning",
                "Diagnoses one bounded signal case.",
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


def _admit_policy(specification: DomainEvaluationPolicySpecification):
    review = review_domain_evaluation_policy_specification_v1(
        specification=specification,
        review_id=DomainEvaluationPolicyReviewId("policy-review-1"),
        reviewer_ref=DomainEvaluationPolicyReviewerRef(
            DomainEvaluationPolicyReviewerKind.HUMAN,
            "human:policy_reviewer",
        ),
        verdict=DomainEvaluationPolicyReviewVerdict.APPROVE,
        reviewed_at=_time(7),
        rationale="Reviewed exact policy specification.",
    )
    ledger, admission = admit_domain_evaluation_policy_review_v1(
        review_ledger=DomainEvaluationPolicyReviewLedger(),
        specification=specification,
        review=review,
    )
    registry, _ = admit_domain_evaluation_policy_v1(
        registry=DomainEvaluationPolicyRegistry(),
        review_ledger=ledger,
        review_admission=admission,
        specification=specification,
        admitted_at=_time(8),
    )
    return registry


def _entries(*, diagnostic_ids=("e1",), explanation_ids=("e2",)):
    return (
        DomainPolicyRequirementApplicationEntry(
            "diagnostic_reasoning",
            DomainPolicyRequirementApplicationDisposition.COVERED,
            tuple(EvidenceId(item) for item in diagnostic_ids),
            "Diagnostic aspect explicitly covered.",
        ),
        DomainPolicyRequirementApplicationEntry(
            "edge_case_awareness",
            DomainPolicyRequirementApplicationDisposition.UNRESOLVED,
            (),
            "Optional edge-case coverage unresolved.",
        ),
        DomainPolicyRequirementApplicationEntry(
            "explanation_quality",
            DomainPolicyRequirementApplicationDisposition.COVERED,
            tuple(EvidenceId(item) for item in explanation_ids),
            "Explanation aspect explicitly covered.",
        ),
    )


def _basis(*, shared_lineage: bool = False):
    claim = _claim()
    first = _evidence("e1", recorded_hour=11)
    second_sources = None
    if shared_lineage:
        second_sources = (
            ProvenanceSource(ProvenanceSourceKind.EVIDENCE_RECORD, "e1"),
        )
    second = _evidence("e2", recorded_hour=12, sources=second_sources)
    records = EpistemicRecordSet(
        evidence_records=(first, second),
        claims=(claim,),
    )
    coverage = build_claim_evidence_disposition_coverage_v1(
        records=records,
        claim_id=claim.claim_id,
        as_of=_time(14),
        dispositions=(_assessment("e1"), _assessment("e2")),
    )
    lineage = build_claim_evidence_lineage_dependence_v1(
        records=records,
        claim_id=claim.claim_id,
        as_of=_time(14),
        coverage=coverage,
    )
    specification = _specification()
    registry = _admit_policy(specification)
    proposal = build_claim_domain_policy_requirement_mapping_proposal_v1(
        records=records,
        claim_id=claim.claim_id,
        as_of=_time(14),
        coverage=coverage,
        lineage=lineage,
        registry=registry,
        policy_ref=specification.policy_ref,
        specification_sha256=domain_evaluation_policy_specification_sha256_v1(
            specification
        ),
        requirement_applications=_entries(),
    )
    review = review_claim_domain_policy_requirement_mapping_proposal_v1(
        proposal=proposal,
        review_id=ClaimPolicyRequirementMappingReviewId("mapping-review-1"),
        reviewer_ref=ClaimPolicyRequirementMappingReviewerRef(
            ClaimPolicyRequirementMappingReviewerKind.HUMAN,
            "human:mapping_reviewer",
        ),
        verdict=ClaimPolicyRequirementMappingReviewVerdict.APPROVE,
        reviewed_at=_time(15),
        rationale="Reviewed exact mapping proposal.",
    )
    review_ledger, review_admission = admit_claim_policy_requirement_mapping_review_v1(
        review_ledger=ClaimPolicyRequirementMappingReviewLedger(),
        proposal=proposal,
        review=review,
    )
    application = apply_admitted_domain_policy_requirements_v1(
        records=records,
        claim_id=claim.claim_id,
        as_of=_time(14),
        coverage=coverage,
        lineage=lineage,
        registry=registry,
        proposal=proposal,
        review_ledger=review_ledger,
        review_admission=review_admission,
    )
    return (
        records,
        claim,
        coverage,
        lineage,
        specification,
        registry,
        proposal,
        review_ledger,
        review_admission,
        application,
    )


def test_missing_required_requirement_entry_is_rejected_explicitly():
    records, claim, coverage, lineage, specification, registry, *_ = _basis()
    entries = tuple(
        entry
        for entry in _entries()
        if entry.requirement_key != "diagnostic_reasoning"
    )
    with pytest.raises(
        InvalidDomainPolicyRequirementApplication,
        match="omits admitted policy requirement",
    ):
        build_claim_domain_policy_requirement_mapping_proposal_v1(
            records=records,
            claim_id=claim.claim_id,
            as_of=_time(14),
            coverage=coverage,
            lineage=lineage,
            registry=registry,
            policy_ref=specification.policy_ref,
            specification_sha256=domain_evaluation_policy_specification_sha256_v1(
                specification
            ),
            requirement_applications=entries,
        )


def test_changed_claim_statement_invalidates_stale_mapping_proposal_basis():
    records, claim, coverage, lineage, _, registry, proposal, *_ = _basis()
    changed_claim = _claim(statement="The subject can reason about a changed proposition.")
    changed_records = EpistemicRecordSet(
        evidence_records=records.evidence_records,
        claims=(changed_claim,),
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


def test_proven_shared_lineage_does_not_change_requirement_coverage_or_create_count_strength():
    *_, application = _basis(shared_lineage=True)
    assert application.required_requirement_coverage_complete is True
    assert all(
        not hasattr(application, name)
        for name in (
            "independent_evidence_count",
            "replication_count",
            "support_count",
            "coverage_weight",
        )
    )


def test_review_time_before_policy_admission_is_rejected_as_its_own_boundary():
    *_, proposal, _, _, _ = _basis()
    future_policy_basis = replace(proposal, policy_admitted_at=_time(16))
    with pytest.raises(
        InvalidDomainPolicyRequirementApplication,
        match="policy admitted_at",
    ):
        review_claim_domain_policy_requirement_mapping_proposal_v1(
            proposal=future_policy_basis,
            review_id=ClaimPolicyRequirementMappingReviewId("too-early-review"),
            reviewer_ref=ClaimPolicyRequirementMappingReviewerRef(
                ClaimPolicyRequirementMappingReviewerKind.HUMAN,
                "human:mapping_reviewer",
            ),
            verdict=ClaimPolicyRequirementMappingReviewVerdict.APPROVE,
            reviewed_at=_time(15),
            rationale="This review predates the claimed policy admission time.",
        )


def test_final_application_boolean_forgery_fails_complete_replay():
    (
        records,
        claim,
        coverage,
        lineage,
        _,
        registry,
        proposal,
        review_ledger,
        review_admission,
        application,
    ) = _basis()
    forged = replace(
        application,
        required_requirement_coverage_complete=not application.required_requirement_coverage_complete,
    )
    with pytest.raises(
        InvalidDomainPolicyRequirementApplication,
        match="complete governed PR12.11 replay",
    ):
        validate_claim_domain_policy_requirement_application_v1(
            records=records,
            claim_id=claim.claim_id,
            as_of=_time(14),
            coverage=coverage,
            lineage=lineage,
            registry=registry,
            proposal=proposal,
            review_ledger=review_ledger,
            review_admission=review_admission,
            application=forged,
        )


def test_final_application_mapping_forgery_fails_complete_replay():
    (
        records,
        claim,
        coverage,
        lineage,
        _,
        registry,
        proposal,
        review_ledger,
        review_admission,
        application,
    ) = _basis()
    forged_entries = (
        replace(
            application.requirement_applications[0],
            rationale="Changed after HUMAN approval.",
        ),
        *application.requirement_applications[1:],
    )
    forged = replace(application, requirement_applications=forged_entries)
    with pytest.raises(
        InvalidDomainPolicyRequirementApplication,
        match="complete governed PR12.11 replay",
    ):
        validate_claim_domain_policy_requirement_application_v1(
            records=records,
            claim_id=claim.claim_id,
            as_of=_time(14),
            coverage=coverage,
            lineage=lineage,
            registry=registry,
            proposal=proposal,
            review_ledger=review_ledger,
            review_admission=review_admission,
            application=forged,
        )


def test_behavioral_evidence_id_subclass_cannot_enter_mapping_entry():
    class EvilEvidenceId(EvidenceId):
        pass

    with pytest.raises(
        InvalidDomainPolicyRequirementApplication,
        match="exact EvidenceId",
    ):
        DomainPolicyRequirementApplicationEntry(
            "diagnostic_reasoning",
            DomainPolicyRequirementApplicationDisposition.COVERED,
            (EvilEvidenceId("e1"),),
            "Subclass storage must fail closed.",
        )
