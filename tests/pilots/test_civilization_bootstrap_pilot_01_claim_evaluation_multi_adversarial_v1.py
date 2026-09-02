from dataclasses import replace
from datetime import timedelta
from types import SimpleNamespace

import pytest

from capability_lab.epistemics import (
    CapabilityClaimId,
    CapabilitySubjectRef,
    EvaluationPolicyRef,
    EvaluatorKind,
    EvaluatorRef,
    EvidenceBearing,
    EvidenceId,
    EvidenceReliability,
)
from capability_lab.pilots.civilization_bootstrap_01.claim_evaluation import (
    InvalidPilotClaimEvaluation,
)
from capability_lab.pilots.civilization_bootstrap_01.claim_evaluation_multi import (
    PilotHumanMultiEvidenceAssessmentDecision,
)

from test_civilization_bootstrap_pilot_01_claim_evaluation_multi_v1 import (
    T0 as MULTI_T0,
    _claim,
    _decision,
    _dependence_case,
    _evaluate,
    _reasoning_entries,
    _stub_terminal,
)
from test_civilization_bootstrap_pilot_01_terminal_dependence_v1 import (
    _case as _terminal_case,
)


def test_real_terminal_pass_bridges_to_real_pr11_2_claim_evaluation(tmp_path):
    case = _terminal_case(tmp_path)
    entries = case["selection_entries"]
    claim = _claim(subject_ref=CapabilitySubjectRef("subject_terminal_01"))
    decision = _decision(
        claim=claim,
        entries=entries,
        coverage_status=claim.scope and __import__(
            "capability_lab.epistemics", fromlist=["CoverageStatus"]
        ).CoverageStatus.PARTIAL,
        conclusion=__import__(
            "capability_lab.epistemics", fromlist=["EvaluationConclusion"]
        ).EvaluationConclusion.INSUFFICIENT,
    )

    evaluation = _evaluate(claim=claim, decision=decision, case=case)

    assert evaluation.claim_id == claim.claim_id
    assert len(evaluation.evidence_assessments) == 2
    assert tuple(item.evidence_id for item in evaluation.evidence_assessments) == tuple(
        sorted(
            entry.allocation_entry.temporal_entry.coordination_entry.mechanism_entry
            .upstream_lineage_entry.basis_entry.evidence.evidence_id
            for entry in entries
        )
    )


def test_multi_decision_rejects_non_human_evaluator():
    entries = _reasoning_entries()
    claim = _claim()
    decision = _decision(claim=claim, entries=entries)

    with pytest.raises(InvalidPilotClaimEvaluation, match="explicit HUMAN EvaluatorRef"):
        replace(
            decision,
            evaluator_ref=EvaluatorRef(EvaluatorKind.MODEL, "model_reviewer_pr11_2"),
        )


def test_multi_evaluation_rejects_decision_claim_id_mismatch(monkeypatch):
    entries = _reasoning_entries()
    case = _dependence_case(entries)
    claim = _claim()
    decision = replace(
        _decision(claim=claim, entries=entries),
        claim_id=CapabilityClaimId("claim_other_pr11_2"),
    )
    _stub_terminal(monkeypatch)

    with pytest.raises(InvalidPilotClaimEvaluation, match="decision claim_id does not match"):
        _evaluate(claim=claim, decision=decision, case=case)


def test_multi_evaluation_rejects_decision_policy_ref_mismatch(monkeypatch):
    entries = _reasoning_entries()
    case = _dependence_case(entries)
    claim = _claim()
    decision = replace(
        _decision(claim=claim, entries=entries),
        policy_ref=EvaluationPolicyRef("civilization_bootstrap", "wrong_policy", 1),
    )
    _stub_terminal(monkeypatch)

    with pytest.raises(InvalidPilotClaimEvaluation, match="decision policy_ref does not match"):
        _evaluate(claim=claim, decision=decision, case=case)


def test_multi_evaluation_rejects_evaluation_before_latest_evidence(monkeypatch):
    entries = _reasoning_entries()
    case = _dependence_case(entries)
    claim = _claim()
    decision = _decision(
        claim=claim,
        entries=entries,
        evaluated_minute=11,
    )
    _stub_terminal(monkeypatch)

    with pytest.raises(
        InvalidPilotClaimEvaluation,
        match="must not precede the latest reviewed EvidenceRecord recorded_at",
    ):
        _evaluate(claim=claim, decision=decision, case=case)


def test_multi_evaluation_rejects_evaluation_before_latest_receipt(monkeypatch):
    entries = _reasoning_entries()
    case = _dependence_case(entries)
    claim = _claim()
    decision = _decision(claim=claim, entries=entries, evaluated_minute=30)
    original = case["materialization_resolution_bindings"]
    latest_evidence_id = original[-1].receipt.evidence_id
    case["materialization_resolution_bindings"] = original[:-1] + (
        SimpleNamespace(
            receipt=SimpleNamespace(
                evidence_id=latest_evidence_id,
                resolved_at=MULTI_T0 + timedelta(minutes=35),
            )
        ),
    )
    _stub_terminal(monkeypatch)

    with pytest.raises(
        InvalidPilotClaimEvaluation,
        match="must not precede the latest reviewed materialization receipt resolved_at",
    ):
        _evaluate(claim=claim, decision=decision, case=case)


def test_multi_evaluation_rejects_extra_assessment_evidence_id(monkeypatch):
    entries = _reasoning_entries()
    case = _dependence_case(entries)
    claim = _claim()
    decision = _decision(claim=claim, entries=entries)
    extra = PilotHumanMultiEvidenceAssessmentDecision(
        evidence_id=EvidenceId("evidence_extra_pr11_2"),
        bearing=EvidenceBearing.INDETERMINATE,
        reliability=EvidenceReliability.MODERATE,
        coverage_note="Explicit human coverage note for extra evidence.",
        rationale="Explicit human rationale for extra evidence.",
    )
    decision = replace(
        decision,
        assessment_decisions=decision.assessment_decisions + (extra,),
    )
    _stub_terminal(monkeypatch)

    with pytest.raises(InvalidPilotClaimEvaluation, match="exact one-to-one coverage"):
        _evaluate(claim=claim, decision=decision, case=case)
