from dataclasses import replace
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from capability_lab.epistemics import (
    CapabilityClaimId,
    CapabilitySubjectRef,
    ClaimEvaluationId,
    ConflictStatus,
    CoverageAssessment,
    CoverageStatus,
    EvaluationConclusion,
    EvaluatorKind,
    EvaluatorRef,
    EvidenceBearing,
    EvidenceId,
    EvidenceReliability,
    ProvenanceSource,
    ProvenanceSourceKind,
    ProvenanceTrail,
)
from capability_lab.pilots.civilization_bootstrap_01 import (
    InvalidPilotEvidenceMaterialization,
)
import capability_lab.pilots.civilization_bootstrap_01.claim_evaluation_multi as multi_module
from capability_lab.pilots.civilization_bootstrap_01.claim_evaluation import (
    InvalidPilotClaimEvaluation,
    instantiate_civilization_bootstrap_pilot_01_capability_claim_v1,
)
from capability_lab.pilots.civilization_bootstrap_01.claim_evaluation_multi import (
    PilotHumanMultiEvidenceAssessmentDecision,
    PilotHumanMultiEvidenceEvaluationDecision,
    evaluate_reviewed_civilization_bootstrap_pilot_01_multi_evidence_v1,
)
from capability_lab.pilots.civilization_bootstrap_01.evaluation_policy import (
    InvalidPilotEvaluationPolicy,
    PILOT_01_EXECUTION_CLAIM_KEY,
    PILOT_01_REASONING_CLAIM_KEY,
    build_civilization_bootstrap_pilot_01_evaluation_policy_v1,
)


T0 = datetime(2026, 1, 23, 12, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("subject_pr11_2")


def _policy():
    return build_civilization_bootstrap_pilot_01_evaluation_policy_v1()


def _claim(*, claim_key=PILOT_01_REASONING_CLAIM_KEY, subject_ref=SUBJECT):
    return instantiate_civilization_bootstrap_pilot_01_capability_claim_v1(
        claim_key=claim_key,
        subject_ref=subject_ref,
        claim_id=CapabilityClaimId(f"claim_{claim_key}"),
        created_at=T0 + timedelta(minutes=5),
        provenance=ProvenanceTrail(
            sources=(
                ProvenanceSource(
                    ProvenanceSourceKind.SYSTEM,
                    "pilot_01_pr11_2_claim_definition",
                ),
            ),
        ),
        policy=_policy(),
    )


def _entry(evidence_id, probe_id, *, subject_ref=SUBJECT, recorded_minute=10):
    evidence = SimpleNamespace(
        evidence_id=EvidenceId(evidence_id),
        subject_ref=subject_ref,
        recorded_at=T0 + timedelta(minutes=recorded_minute),
    )
    candidate = SimpleNamespace(
        probe_id=probe_id,
        subject_ref=subject_ref,
    )
    basis = SimpleNamespace(candidate=candidate, evidence=evidence)
    upstream = SimpleNamespace(basis_entry=basis)
    mechanism = SimpleNamespace(upstream_lineage_entry=upstream)
    coordination = SimpleNamespace(mechanism_entry=mechanism)
    temporal = SimpleNamespace(coordination_entry=coordination)
    allocation = SimpleNamespace(temporal_entry=temporal)
    return SimpleNamespace(allocation_entry=allocation)


def _basis(entry):
    return (
        entry.allocation_entry.temporal_entry.coordination_entry.mechanism_entry
        .upstream_lineage_entry.basis_entry
    )


def _reasoning_entries():
    return (
        _entry("evidence_conceptual", "conceptual_explanation", recorded_minute=10),
        _entry("evidence_calculation", "calculation_work", recorded_minute=11),
        _entry("evidence_diagnosis", "diagnosis_reasoning", recorded_minute=12),
    )


def _dependence_case(entries, *, latest_review_minute=25):
    entries = tuple(entries)
    bindings = tuple(
        SimpleNamespace(
            receipt=SimpleNamespace(
                evidence_id=_basis(entry).evidence.evidence_id,
                resolved_at=_basis(entry).evidence.recorded_at,
            )
        )
        for entry in entries
    )
    review_minutes = tuple(range(latest_review_minute - 5, latest_review_minute + 1))
    reviews = tuple(
        SimpleNamespace(reviewed_at=T0 + timedelta(minutes=minute))
        for minute in review_minutes
    )
    return {
        "selection_entries": entries,
        "materialization_resolution_bindings": bindings,
        "source_lineage_graph": object(),
        "source_completeness_review": reviews[0],
        "mechanism_lineage_graph": object(),
        "mechanism_completeness_review": reviews[1],
        "coordination_lineage_graph": object(),
        "coordination_completeness_review": reviews[2],
        "temporal_lineage_graph": object(),
        "temporal_completeness_review": reviews[3],
        "allocation_lineage_graph": object(),
        "allocation_completeness_review": reviews[4],
        "selection_lineage_graph": object(),
        "selection_completeness_review": reviews[5],
    }


def _assessment(entry, *, bearing=EvidenceBearing.SUPPORTS, reliability=EvidenceReliability.MODERATE):
    evidence_id = _basis(entry).evidence.evidence_id
    return PilotHumanMultiEvidenceAssessmentDecision(
        evidence_id=evidence_id,
        bearing=bearing,
        reliability=reliability,
        coverage_note=f"Human coverage note for {evidence_id}.",
        rationale=f"Human evidence rationale for {evidence_id}.",
    )


def _decision(
    *,
    claim,
    entries,
    claim_key=PILOT_01_REASONING_CLAIM_KEY,
    bearings=None,
    coverage_status=CoverageStatus.SUFFICIENT_FOR_CLAIM,
    conflict_status=ConflictStatus.NONE,
    conclusion=EvaluationConclusion.SUPPORTED,
    evaluated_minute=30,
):
    entries = tuple(entries)
    bearings = bearings or {}
    assessments = tuple(
        _assessment(
            entry,
            bearing=bearings.get(
                _basis(entry).evidence.evidence_id,
                EvidenceBearing.SUPPORTS,
            ),
        )
        for entry in entries
    )
    return PilotHumanMultiEvidenceEvaluationDecision(
        evaluation_id=ClaimEvaluationId(f"evaluation_multi_{claim_key}"),
        claim_key=claim_key,
        claim_id=claim.claim_id,
        policy_ref=_policy().policy_ref,
        evaluator_ref=EvaluatorRef(EvaluatorKind.HUMAN, "human_reviewer_pr11_2"),
        evaluated_at=T0 + timedelta(minutes=evaluated_minute),
        assessment_decisions=assessments,
        coverage=CoverageAssessment(
            coverage_status,
            "Explicit human claim-level coverage judgment.",
        ),
        conflict_status=conflict_status,
        conclusion=conclusion,
        evaluation_rationale="Explicit human multi-evidence evaluation rationale.",
    )


def _stub_terminal(monkeypatch):
    seen = {}

    def _terminal(selection_entries, **kwargs):
        seen["entries"] = tuple(selection_entries)
        seen["kwargs"] = kwargs
        return tuple(selection_entries)

    monkeypatch.setattr(
        multi_module,
        "validate_pilot_materialized_evidence_reviewed_dependence_preconditions_v1",
        _terminal,
    )
    return seen


def _evaluate(*, claim, decision, case, policy=None):
    return evaluate_reviewed_civilization_bootstrap_pilot_01_multi_evidence_v1(
        claim_key=decision.claim_key,
        claim=claim,
        policy=_policy() if policy is None else policy,
        decision=decision,
        **case,
    )


def test_three_reasoning_probes_can_form_one_sufficient_supported_evaluation_after_terminal_gate(monkeypatch):
    entries = _reasoning_entries()
    case = _dependence_case(entries)
    claim = _claim()
    decision = _decision(claim=claim, entries=entries)
    seen = _stub_terminal(monkeypatch)

    evaluation = _evaluate(claim=claim, decision=decision, case=case)

    assert evaluation.claim_id == claim.claim_id
    assert evaluation.coverage.status is CoverageStatus.SUFFICIENT_FOR_CLAIM
    assert evaluation.conclusion is EvaluationConclusion.SUPPORTED
    assert tuple(item.evidence_id for item in evaluation.evidence_assessments) == tuple(
        sorted(_basis(entry).evidence.evidence_id for entry in entries)
    )
    assert seen["entries"] == entries
    assert seen["kwargs"]["materialization_resolution_bindings"] == case[
        "materialization_resolution_bindings"
    ]


def test_two_reasoning_probes_may_remain_partial_and_insufficient(monkeypatch):
    entries = _reasoning_entries()[:2]
    case = _dependence_case(entries)
    claim = _claim()
    decision = _decision(
        claim=claim,
        entries=entries,
        coverage_status=CoverageStatus.PARTIAL,
        conclusion=EvaluationConclusion.INSUFFICIENT,
    )
    _stub_terminal(monkeypatch)

    evaluation = _evaluate(claim=claim, decision=decision, case=case)
    assert evaluation.coverage.status is CoverageStatus.PARTIAL
    assert evaluation.conclusion is EvaluationConclusion.INSUFFICIENT


def test_missing_required_reasoning_probe_cannot_claim_sufficient_coverage(monkeypatch):
    entries = _reasoning_entries()[:2]
    case = _dependence_case(entries)
    claim = _claim()
    decision = _decision(claim=claim, entries=entries)
    _stub_terminal(monkeypatch)

    with pytest.raises(
        InvalidPilotClaimEvaluation,
        match="requires relevant assessed evidence for every exact PR11.0 sufficiency probe",
    ):
        _evaluate(claim=claim, decision=decision, case=case)


def test_repeated_same_probe_does_not_substitute_for_missing_reasoning_probe(monkeypatch):
    entries = (
        _entry("evidence_conceptual", "conceptual_explanation"),
        _entry("evidence_calculation_a", "calculation_work"),
        _entry("evidence_calculation_b", "calculation_work"),
    )
    case = _dependence_case(entries)
    claim = _claim()
    decision = _decision(claim=claim, entries=entries)
    _stub_terminal(monkeypatch)

    with pytest.raises(InvalidPilotClaimEvaluation, match="diagnosis_reasoning"):
        _evaluate(claim=claim, decision=decision, case=case)


def test_not_relevant_required_probe_does_not_count_as_sufficient_coverage(monkeypatch):
    entries = _reasoning_entries()
    case = _dependence_case(entries)
    claim = _claim()
    diagnosis_id = _basis(entries[2]).evidence.evidence_id
    decision = _decision(
        claim=claim,
        entries=entries,
        bearings={diagnosis_id: EvidenceBearing.NOT_RELEVANT},
    )
    _stub_terminal(monkeypatch)

    with pytest.raises(InvalidPilotClaimEvaluation, match="diagnosis_reasoning"):
        _evaluate(claim=claim, decision=decision, case=case)


def test_conflicting_reasoning_evidence_can_remain_unresolved_and_mixed(monkeypatch):
    entries = _reasoning_entries()
    case = _dependence_case(entries)
    claim = _claim()
    calculation_id = _basis(entries[1]).evidence.evidence_id
    decision = _decision(
        claim=claim,
        entries=entries,
        bearings={calculation_id: EvidenceBearing.CONTRADICTS},
        conflict_status=ConflictStatus.UNRESOLVED,
        conclusion=EvaluationConclusion.MIXED,
    )
    _stub_terminal(monkeypatch)

    evaluation = _evaluate(claim=claim, decision=decision, case=case)
    assert evaluation.conflict_status is ConflictStatus.UNRESOLVED
    assert evaluation.conclusion is EvaluationConclusion.MIXED


def test_pr11_2_rejects_directional_resolved_by_policy_without_frozen_resolution_rule():
    entries = _reasoning_entries()
    claim = _claim()
    with pytest.raises(
        InvalidPilotClaimEvaluation,
        match="defines no directional conflict-resolution rule",
    ):
        _decision(
            claim=claim,
            entries=entries,
            conflict_status=ConflictStatus.RESOLVED_BY_POLICY,
            conclusion=EvaluationConclusion.SUPPORTED,
        )


def test_terminal_pass_itself_does_not_manufacture_support(monkeypatch):
    entries = _reasoning_entries()
    case = _dependence_case(entries)
    claim = _claim()
    bearings = {
        _basis(entry).evidence.evidence_id: EvidenceBearing.INDETERMINATE
        for entry in entries
    }
    decision = _decision(
        claim=claim,
        entries=entries,
        bearings=bearings,
        conclusion=EvaluationConclusion.INSUFFICIENT,
    )
    _stub_terminal(monkeypatch)

    evaluation = _evaluate(claim=claim, decision=decision, case=case)
    assert all(
        item.bearing is EvidenceBearing.INDETERMINATE
        for item in evaluation.evidence_assessments
    )
    assert evaluation.conclusion is EvaluationConclusion.INSUFFICIENT


def test_decision_must_cover_terminal_basis_one_to_one(monkeypatch):
    entries = _reasoning_entries()
    case = _dependence_case(entries)
    claim = _claim()
    decision = _decision(claim=claim, entries=entries[:2])
    _stub_terminal(monkeypatch)

    with pytest.raises(InvalidPilotClaimEvaluation, match="exact one-to-one coverage"):
        _evaluate(claim=claim, decision=decision, case=case)


def test_duplicate_assessment_decision_evidence_id_is_rejected():
    entries = _reasoning_entries()
    claim = _claim()
    first = _assessment(entries[0])
    with pytest.raises(InvalidPilotClaimEvaluation, match="each EvidenceId exactly once"):
        PilotHumanMultiEvidenceEvaluationDecision(
            evaluation_id=ClaimEvaluationId("evaluation_duplicate_assessment"),
            claim_key=PILOT_01_REASONING_CLAIM_KEY,
            claim_id=claim.claim_id,
            policy_ref=_policy().policy_ref,
            evaluator_ref=EvaluatorRef(EvaluatorKind.HUMAN, "human_reviewer_pr11_2"),
            evaluated_at=T0 + timedelta(minutes=30),
            assessment_decisions=(first, first),
            coverage=CoverageAssessment(CoverageStatus.PARTIAL, "Partial."),
            conflict_status=ConflictStatus.NONE,
            conclusion=EvaluationConclusion.INSUFFICIENT,
            evaluation_rationale="Duplicate decision regression.",
        )


def test_unassessed_reliability_is_rejected_for_each_evidence():
    entry = _reasoning_entries()[0]
    with pytest.raises(InvalidPilotClaimEvaluation, match="UNASSESSED is not permitted"):
        _assessment(entry, reliability=EvidenceReliability.UNASSESSED)


def test_reasoning_evaluation_rejects_execution_probe_in_same_basis(monkeypatch):
    entries = (
        _reasoning_entries()[0],
        _entry("evidence_execution", "execution_artifact"),
    )
    case = _dependence_case(entries)
    claim = _claim()
    decision = _decision(
        claim=claim,
        entries=entries,
        coverage_status=CoverageStatus.PARTIAL,
        conclusion=EvaluationConclusion.INSUFFICIENT,
    )
    _stub_terminal(monkeypatch)

    with pytest.raises(InvalidPilotClaimEvaluation, match="probe is not bound"):
        _evaluate(claim=claim, decision=decision, case=case)


def test_multi_evidence_evaluation_rejects_cross_subject_basis(monkeypatch):
    entries = (
        _reasoning_entries()[0],
        _entry(
            "evidence_other_subject",
            "calculation_work",
            subject_ref=CapabilitySubjectRef("other_subject"),
        ),
    )
    case = _dependence_case(entries)
    claim = _claim()
    decision = _decision(
        claim=claim,
        entries=entries,
        coverage_status=CoverageStatus.PARTIAL,
        conclusion=EvaluationConclusion.INSUFFICIENT,
    )
    _stub_terminal(monkeypatch)

    with pytest.raises(InvalidPilotClaimEvaluation, match="subject_ref does not match"):
        _evaluate(claim=claim, decision=decision, case=case)


def test_partial_multi_evidence_coverage_cannot_emit_directional_or_mixed_claim_conclusion(monkeypatch):
    entries = _reasoning_entries()[:2]
    case = _dependence_case(entries)
    claim = _claim()
    decision = _decision(
        claim=claim,
        entries=entries,
        coverage_status=CoverageStatus.PARTIAL,
        conclusion=EvaluationConclusion.SUPPORTED,
    )
    _stub_terminal(monkeypatch)

    with pytest.raises(InvalidPilotClaimEvaluation, match="must remain INSUFFICIENT or ABSTAINED"):
        _evaluate(claim=claim, decision=decision, case=case)


def test_evaluation_cannot_precede_latest_terminal_dependence_review(monkeypatch):
    entries = _reasoning_entries()
    case = _dependence_case(entries, latest_review_minute=35)
    claim = _claim()
    decision = _decision(claim=claim, entries=entries, evaluated_minute=30)
    _stub_terminal(monkeypatch)

    with pytest.raises(
        InvalidPilotClaimEvaluation,
        match="must not precede the latest PR10.1 terminal dependence completeness review",
    ):
        _evaluate(claim=claim, decision=decision, case=case)


def test_real_terminal_cardinality_failure_propagates_before_multi_evidence_aggregation():
    claim = _claim()
    fake_entries = (
        _entry("evidence_a", "conceptual_explanation"),
        _entry("evidence_b", "calculation_work"),
    )
    decision = _decision(
        claim=claim,
        entries=fake_entries,
        coverage_status=CoverageStatus.PARTIAL,
        conclusion=EvaluationConclusion.INSUFFICIENT,
    )
    empty_case = _dependence_case(())

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="require at least two materialized observation slots",
    ):
        _evaluate(claim=claim, decision=decision, case=empty_case)


def test_non_exact_pr11_0_policy_is_rejected_before_multi_evidence_evaluation(monkeypatch):
    entries = _reasoning_entries()
    case = _dependence_case(entries)
    claim = _claim()
    decision = _decision(claim=claim, entries=entries)
    _stub_terminal(monkeypatch)
    changed_policy = replace(
        _policy(),
        dependence_rule="Drifted dependence rule under same nominal policy ref.",
    )

    with pytest.raises(InvalidPilotEvaluationPolicy):
        _evaluate(
            claim=claim,
            decision=decision,
            case=case,
            policy=changed_policy,
        )


def test_two_execution_artifacts_can_form_sufficient_supported_evaluation_only_via_pr11_2(monkeypatch):
    entries = (
        _entry("evidence_execution_a", "execution_artifact"),
        _entry("evidence_execution_b", "execution_artifact"),
    )
    case = _dependence_case(entries)
    claim = _claim(claim_key=PILOT_01_EXECUTION_CLAIM_KEY)
    decision = _decision(
        claim=claim,
        entries=entries,
        claim_key=PILOT_01_EXECUTION_CLAIM_KEY,
    )
    _stub_terminal(monkeypatch)

    evaluation = _evaluate(claim=claim, decision=decision, case=case)
    assert len(evaluation.evidence_assessments) == 2
    assert evaluation.coverage.status is CoverageStatus.SUFFICIENT_FOR_CLAIM
    assert evaluation.conclusion is EvaluationConclusion.SUPPORTED
