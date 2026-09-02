from dataclasses import replace
from datetime import datetime, timezone
import ast
import inspect
import json

import pytest

from capability_lab.epistemics import (
    CapabilityClaim,
    CapabilityClaimId,
    CapabilitySubjectRef,
    ClaimScope,
    ConflictStatus,
    CoverageStatus,
    EpistemicRecordSet,
    EvaluationConclusion,
    EvaluationPolicyRef,
    EvaluatorKind,
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
    ClaimDomainPolicyDirectionalEvaluationReceipt,
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
    InvalidDomainPolicyDirectionalEvaluation,
    admit_claim_policy_requirement_mapping_review_v1,
    admit_domain_evaluation_policy_review_v1,
    admit_domain_evaluation_policy_v1,
    apply_admitted_domain_policy_requirements_v1,
    build_claim_domain_policy_directional_evaluation_v1,
    build_claim_domain_policy_requirement_mapping_proposal_v1,
    claim_domain_policy_directional_evaluation_receipt_from_json,
    claim_domain_policy_directional_evaluation_receipt_to_json,
    domain_evaluation_policy_registry_from_json,
    domain_evaluation_policy_registry_to_json,
    domain_evaluation_policy_specification_sha256_v1,
    review_claim_domain_policy_requirement_mapping_proposal_v1,
    review_domain_evaluation_policy_specification_v1,
    validate_claim_domain_policy_directional_evaluation_v1,
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


def _claim(
    *,
    statement: str = "The subject can reason about bounded signal evidence.",
) -> CapabilityClaim:
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


def _assessment(
    evidence_id: str,
    bearing: EvidenceBearing,
    reliability: EvidenceReliability = EvidenceReliability.UNASSESSED,
) -> EvidenceAssessment:
    return EvidenceAssessment(
        evidence_id=EvidenceId(evidence_id),
        bearing=bearing,
        reliability=reliability,
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


def _entries(*, complete: bool) -> tuple[DomainPolicyRequirementApplicationEntry, ...]:
    return (
        DomainPolicyRequirementApplicationEntry(
            "diagnostic_reasoning",
            DomainPolicyRequirementApplicationDisposition.COVERED,
            (EvidenceId("e1"),),
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
            (
                DomainPolicyRequirementApplicationDisposition.COVERED
                if complete
                else DomainPolicyRequirementApplicationDisposition.NOT_COVERED
            ),
            (EvidenceId("e2"),) if complete else (),
            (
                "Explanation aspect explicitly covered."
                if complete
                else "Required explanation coverage remains absent."
            ),
        ),
    )


def _basis(
    *,
    bearings: tuple[EvidenceBearing, EvidenceBearing, EvidenceBearing] = (
        EvidenceBearing.SUPPORTS,
        EvidenceBearing.SUPPORTS,
        EvidenceBearing.INDETERMINATE,
    ),
    complete: bool = True,
    reliabilities: tuple[
        EvidenceReliability, EvidenceReliability, EvidenceReliability
    ] = (
        EvidenceReliability.UNASSESSED,
        EvidenceReliability.UNASSESSED,
        EvidenceReliability.UNASSESSED,
    ),
    shared_lineage: bool = False,
):
    claim = _claim()
    first = _evidence("e1", recorded_hour=11)
    second = _evidence("e2", recorded_hour=12)
    third_sources = None
    if shared_lineage:
        third_sources = (
            ProvenanceSource(ProvenanceSourceKind.EVIDENCE_RECORD, "e1"),
        )
    third = _evidence("e3", recorded_hour=13, sources=third_sources)
    records = EpistemicRecordSet(
        evidence_records=(first, second, third),
        claims=(claim,),
    )
    coverage = build_claim_evidence_disposition_coverage_v1(
        records=records,
        claim_id=claim.claim_id,
        as_of=_time(14),
        dispositions=tuple(
            _assessment(f"e{index}", bearing, reliability)
            for index, (bearing, reliability) in enumerate(
                zip(bearings, reliabilities),
                start=1,
            )
        ),
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
        requirement_applications=_entries(complete=complete),
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
    evaluation, receipt = build_claim_domain_policy_directional_evaluation_v1(
        records=records,
        claim_id=claim.claim_id,
        as_of=_time(14),
        coverage=coverage,
        lineage=lineage,
        registry=registry,
        proposal=proposal,
        review_ledger=review_ledger,
        review_admission=review_admission,
        application=application,
    )
    return {
        "records": records,
        "claim": claim,
        "coverage": coverage,
        "lineage": lineage,
        "specification": specification,
        "registry": registry,
        "proposal": proposal,
        "review": review,
        "review_ledger": review_ledger,
        "review_admission": review_admission,
        "application": application,
        "evaluation": evaluation,
        "receipt": receipt,
    }


def _validate(basis, *, evaluation=None, receipt=None, application=None, registry=None):
    return validate_claim_domain_policy_directional_evaluation_v1(
        records=basis["records"],
        claim_id=basis["claim"].claim_id,
        as_of=_time(14),
        coverage=basis["coverage"],
        lineage=basis["lineage"],
        registry=basis["registry"] if registry is None else registry,
        proposal=basis["proposal"],
        review_ledger=basis["review_ledger"],
        review_admission=basis["review_admission"],
        application=basis["application"] if application is None else application,
        evaluation=basis["evaluation"] if evaluation is None else evaluation,
        receipt=basis["receipt"] if receipt is None else receipt,
    )


@pytest.mark.parametrize(
    ("bearings", "expected_conclusion", "expected_conflict"),
    [
        (
            (
                EvidenceBearing.SUPPORTS,
                EvidenceBearing.SUPPORTS,
                EvidenceBearing.INDETERMINATE,
            ),
            EvaluationConclusion.SUPPORTED,
            ConflictStatus.NONE,
        ),
        (
            (
                EvidenceBearing.CONTRADICTS,
                EvidenceBearing.CONTRADICTS,
                EvidenceBearing.INDETERMINATE,
            ),
            EvaluationConclusion.CONTRADICTED,
            ConflictStatus.NONE,
        ),
        (
            (
                EvidenceBearing.SUPPORTS,
                EvidenceBearing.SUPPORTS,
                EvidenceBearing.CONTRADICTS,
            ),
            EvaluationConclusion.MIXED,
            ConflictStatus.UNRESOLVED,
        ),
        (
            (
                EvidenceBearing.INDETERMINATE,
                EvidenceBearing.INDETERMINATE,
                EvidenceBearing.NOT_RELEVANT,
            ),
            EvaluationConclusion.ABSTAINED,
            ConflictStatus.NONE,
        ),
    ],
)
def test_complete_required_coverage_uses_conservative_direction_table(
    bearings,
    expected_conclusion,
    expected_conflict,
):
    basis = _basis(bearings=bearings)
    evaluation = basis["evaluation"]
    assert evaluation.coverage.status is CoverageStatus.SUFFICIENT_FOR_CLAIM
    assert evaluation.conclusion is expected_conclusion
    assert evaluation.conflict_status is expected_conflict
    assert evaluation.conflict_status is not ConflictStatus.RESOLVED_BY_POLICY


@pytest.mark.parametrize(
    ("bearings", "expected_conflict"),
    [
        (
            (
                EvidenceBearing.SUPPORTS,
                EvidenceBearing.SUPPORTS,
                EvidenceBearing.INDETERMINATE,
            ),
            ConflictStatus.NONE,
        ),
        (
            (
                EvidenceBearing.SUPPORTS,
                EvidenceBearing.CONTRADICTS,
                EvidenceBearing.INDETERMINATE,
            ),
            ConflictStatus.UNRESOLVED,
        ),
    ],
)
def test_incomplete_required_coverage_is_always_insufficient(
    bearings,
    expected_conflict,
):
    basis = _basis(bearings=bearings, complete=False)
    evaluation = basis["evaluation"]
    assert evaluation.coverage.status is CoverageStatus.PARTIAL
    assert evaluation.conclusion is EvaluationConclusion.INSUFFICIENT
    assert evaluation.conflict_status is expected_conflict


def test_unmapped_contradictory_evidence_cannot_be_cherry_picked_away():
    basis = _basis(
        bearings=(
            EvidenceBearing.SUPPORTS,
            EvidenceBearing.SUPPORTS,
            EvidenceBearing.CONTRADICTS,
        )
    )
    evaluation = basis["evaluation"]
    assert EvidenceId("e3") not in {
        evidence_id
        for entry in basis["application"].requirement_applications
        for evidence_id in entry.evidence_ids
    }
    assert tuple(item.evidence_id for item in evaluation.evidence_assessments) == (
        EvidenceId("e1"),
        EvidenceId("e2"),
        EvidenceId("e3"),
    )
    assert evaluation.conclusion is EvaluationConclusion.MIXED
    assert evaluation.conflict_status is ConflictStatus.UNRESOLVED


def test_reliability_is_directionally_orthogonal():
    low = _basis(
        reliabilities=(
            EvidenceReliability.LOW,
            EvidenceReliability.LOW,
            EvidenceReliability.LOW,
        )
    )
    high = _basis(
        reliabilities=(
            EvidenceReliability.HIGH,
            EvidenceReliability.HIGH,
            EvidenceReliability.HIGH,
        )
    )
    assert low["evaluation"].conclusion is high["evaluation"].conclusion
    assert low["evaluation"].coverage.status is high["evaluation"].coverage.status
    assert low["evaluation"].conflict_status is high["evaluation"].conflict_status


def test_shared_lineage_does_not_create_directional_strength_or_counts():
    basis = _basis(shared_lineage=True)
    evaluation = basis["evaluation"]
    assert evaluation.conclusion is EvaluationConclusion.SUPPORTED
    for name in (
        "support_count",
        "contradiction_count",
        "replication_count",
        "independent_evidence_count",
        "confidence",
        "weight",
    ):
        assert not hasattr(basis["receipt"], name)


def test_evaluation_assessments_are_exact_complete_pr12_9_universe():
    basis = _basis()
    assert basis["evaluation"].evidence_assessments == basis["coverage"].dispositions


def test_evaluator_and_time_are_fixed_by_governed_replay():
    basis = _basis()
    evaluation = basis["evaluation"]
    assert evaluation.evaluator_ref.kind is EvaluatorKind.RULE
    assert evaluation.evaluator_ref.ref == "capability_lab:pr12_12_domain_directional_rule_v1"
    assert evaluation.evaluated_at == basis["review"].reviewed_at


def test_exact_replay_is_byte_and_identity_deterministic():
    basis = _basis()
    evaluation2, receipt2 = build_claim_domain_policy_directional_evaluation_v1(
        records=basis["records"],
        claim_id=basis["claim"].claim_id,
        as_of=_time(14),
        coverage=basis["coverage"],
        lineage=basis["lineage"],
        registry=basis["registry"],
        proposal=basis["proposal"],
        review_ledger=basis["review_ledger"],
        review_admission=basis["review_admission"],
        application=basis["application"],
    )
    assert evaluation2 == basis["evaluation"]
    assert evaluation2.evaluation_id == basis["evaluation"].evaluation_id
    assert receipt2 == basis["receipt"]
    assert receipt2.to_json() == basis["receipt"].to_json()


def test_builder_exposes_no_directional_override_parameters():
    names = set(inspect.signature(build_claim_domain_policy_directional_evaluation_v1).parameters)
    forbidden = {
        "evaluation_id",
        "policy_ref",
        "evaluator_ref",
        "evaluated_at",
        "coverage_status",
        "conflict_status",
        "conclusion",
        "rationale",
        "selected_evidence_ids",
        "weights",
        "threshold",
        "confidence",
    }
    assert names.isdisjoint(forbidden)


def test_receipt_round_trips_canonically_but_requires_live_replay_for_authority():
    basis = _basis()
    payload = basis["receipt"].to_json()
    restored = claim_domain_policy_directional_evaluation_receipt_from_json(payload)
    assert restored == basis["receipt"]
    assert claim_domain_policy_directional_evaluation_receipt_to_json(restored) == payload
    evaluation, validated = _validate(basis, receipt=restored)
    assert evaluation == basis["evaluation"]
    assert validated == restored


def test_receipt_json_rejects_duplicate_unknown_and_noncanonical_encoding():
    basis = _basis()
    payload = basis["receipt"].to_json()

    duplicate = payload.replace(
        '{"as_of":',
        '{"as_of":"' + basis["receipt"].to_dict()["as_of"] + '","as_of":',
        1,
    )
    with pytest.raises(InvalidDomainPolicyDirectionalEvaluation):
        claim_domain_policy_directional_evaluation_receipt_from_json(duplicate)

    data = basis["receipt"].to_dict()
    data["unknown"] = "x"
    with pytest.raises(InvalidDomainPolicyDirectionalEvaluation, match="unknown field"):
        ClaimDomainPolicyDirectionalEvaluationReceipt.from_dict(data)

    pretty = json.dumps(basis["receipt"].to_dict(), indent=2, sort_keys=True)
    with pytest.raises(InvalidDomainPolicyDirectionalEvaluation, match="canonical"):
        ClaimDomainPolicyDirectionalEvaluationReceipt.from_json(pretty)


def test_forged_directional_evaluation_fails_complete_replay():
    basis = _basis(
        bearings=(
            EvidenceBearing.SUPPORTS,
            EvidenceBearing.CONTRADICTS,
            EvidenceBearing.INDETERMINATE,
        )
    )
    forged = replace(
        basis["evaluation"],
        conclusion=EvaluationConclusion.INSUFFICIENT,
    )
    with pytest.raises(InvalidDomainPolicyDirectionalEvaluation, match="complete governed PR12.12"):
        _validate(basis, evaluation=forged)


def test_forged_receipt_conclusion_fails_complete_replay():
    basis = _basis()
    forged = replace(
        basis["receipt"],
        conclusion=EvaluationConclusion.ABSTAINED,
    )
    with pytest.raises(InvalidDomainPolicyDirectionalEvaluation, match="receipt does not match"):
        _validate(basis, receipt=forged)


def test_forged_receipt_evaluation_digest_fails_complete_replay():
    basis = _basis()
    forged = replace(
        basis["receipt"],
        evaluation_sha256="0" * 64,
    )
    with pytest.raises(InvalidDomainPolicyDirectionalEvaluation, match="receipt does not match"):
        _validate(basis, receipt=forged)


def test_forged_pr12_11_application_is_rejected_transitively():
    basis = _basis()
    forged = replace(
        basis["application"],
        required_requirement_coverage_complete=False,
    )
    with pytest.raises(
        InvalidDomainPolicyDirectionalEvaluation,
        match="PR12.11 governed application replay failed",
    ):
        build_claim_domain_policy_directional_evaluation_v1(
            records=basis["records"],
            claim_id=basis["claim"].claim_id,
            as_of=_time(14),
            coverage=basis["coverage"],
            lineage=basis["lineage"],
            registry=basis["registry"],
            proposal=basis["proposal"],
            review_ledger=basis["review_ledger"],
            review_admission=basis["review_admission"],
            application=forged,
        )


def test_json_restored_policy_registry_has_no_runtime_authority():
    basis = _basis()
    restored = domain_evaluation_policy_registry_from_json(
        domain_evaluation_policy_registry_to_json(basis["registry"])
    )
    with pytest.raises(
        InvalidDomainPolicyDirectionalEvaluation,
        match="PR12.11 governed application replay failed",
    ):
        _validate(basis, registry=restored)


def test_changed_claim_statement_invalidates_directional_replay():
    basis = _basis()
    changed = _claim(statement="The subject can reason about a changed proposition.")
    changed_records = EpistemicRecordSet(
        evidence_records=basis["records"].evidence_records,
        claims=(changed,),
    )
    with pytest.raises(InvalidDomainPolicyDirectionalEvaluation):
        validate_claim_domain_policy_directional_evaluation_v1(
            records=changed_records,
            claim_id=changed.claim_id,
            as_of=_time(14),
            coverage=basis["coverage"],
            lineage=basis["lineage"],
            registry=basis["registry"],
            proposal=basis["proposal"],
            review_ledger=basis["review_ledger"],
            review_admission=basis["review_admission"],
            application=basis["application"],
            evaluation=basis["evaluation"],
            receipt=basis["receipt"],
        )


def test_all_not_relevant_cannot_forge_complete_required_coverage():
    claim = _claim()
    records = EpistemicRecordSet(
        evidence_records=(
            _evidence("e1", recorded_hour=11),
            _evidence("e2", recorded_hour=12),
            _evidence("e3", recorded_hour=13),
        ),
        claims=(claim,),
    )
    coverage = build_claim_evidence_disposition_coverage_v1(
        records=records,
        claim_id=claim.claim_id,
        as_of=_time(14),
        dispositions=tuple(
            _assessment(f"e{index}", EvidenceBearing.NOT_RELEVANT)
            for index in range(1, 4)
        ),
    )
    lineage = build_claim_evidence_lineage_dependence_v1(
        records=records,
        claim_id=claim.claim_id,
        as_of=_time(14),
        coverage=coverage,
    )
    specification = _specification()
    registry = _admit_policy(specification)
    with pytest.raises(Exception, match="NOT_RELEVANT evidence cannot satisfy"):
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
            requirement_applications=_entries(complete=True),
        )


def test_production_import_surface_excludes_state_and_downstream_authority():
    import capability_lab.evaluation_policy.directional_evaluation as module

    source = inspect.getsource(module)
    tree = ast.parse(source)
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add(node.module or "")
    forbidden_fragments = {
        "capability_lab.state",
        "capability_lab.derivation",
        "capability_lab.progression",
        "capability_lab.player_window",
        "capability_lab.proposals",
        "capability_lab.history",
        "capability_lab.pilots",
        "capability_lab.domains",
    }
    assert imports.isdisjoint(forbidden_fragments)


def test_receipt_has_no_state_progression_or_strength_fields():
    basis = _basis()
    names = set(basis["receipt"].to_dict())
    forbidden = {
        "state",
        "mastery",
        "readiness",
        "progression",
        "score",
        "permission",
        "supersedes",
        "confidence",
        "support_count",
        "contradiction_count",
        "independent_evidence_count",
    }
    assert names.isdisjoint(forbidden)
