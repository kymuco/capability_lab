from datetime import datetime, timedelta, timezone

import pytest

from capability_lab.epistemics import (
    CapabilityClaimId,
    CapabilitySubjectRef,
    ClaimEvaluation,
    ClaimEvaluationId,
    ConflictStatus,
    ContextFactor,
    ContextFactorKind,
    CoverageAssessment,
    CoverageStatus,
    EpistemicRecordSet,
    EvaluationConclusion,
    EvaluationPolicyRef,
    EvaluatorKind,
    EvaluatorRef,
    EvidenceAssessment,
    EvidenceBearing,
    EvidenceContext,
    EvidenceId,
    EvidenceKind,
    EvidenceRecord,
    EvidenceReliability,
    InvalidEvaluationError,
    InvalidEvidenceError,
    ProvenanceSource,
    ProvenanceSourceKind,
    ProvenanceTrail,
)


T0 = datetime(2026, 8, 14, 9, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("subject_01")


def actor_trail() -> ProvenanceTrail:
    return ProvenanceTrail(
        sources=(ProvenanceSource(ProvenanceSourceKind.ACTOR, "operator"),)
    )


def test_automation_is_explicit_context_not_hidden_in_other() -> None:
    factor = ContextFactor(ContextFactorKind.AUTOMATION, "Automatic test harness")
    context = EvidenceContext("Tool-assisted task.", factors=(factor,))
    assert context.factors == (factor,)


def test_duplicate_context_factor_is_rejected() -> None:
    factor = ContextFactor(ContextFactorKind.TOOL, "Multimeter")
    with pytest.raises(InvalidEvidenceError, match="duplicate context factors"):
        EvidenceContext("Bench context.", factors=(factor, factor))


def test_repeated_performance_requires_explicit_observation_window() -> None:
    with pytest.raises(InvalidEvidenceError, match="requires observation_started_at"):
        EvidenceRecord(
            evidence_id=EvidenceId("ev_repeat"),
            subject_ref=SUBJECT,
            kind=EvidenceKind.REPEATED_PERFORMANCE,
            summary="Repeated bounded performance.",
            context=EvidenceContext("Repeated task context."),
            observed_at=T0 + timedelta(days=7),
            recorded_at=T0 + timedelta(days=7, minutes=1),
            provenance=actor_trail(),
        )


def test_observation_window_start_cannot_follow_terminal_observation() -> None:
    with pytest.raises(InvalidEvidenceError, match="must not follow observed_at"):
        EvidenceRecord(
            evidence_id=EvidenceId("ev_window"),
            subject_ref=SUBJECT,
            kind=EvidenceKind.REPEATED_PERFORMANCE,
            summary="Repeated bounded performance.",
            context=EvidenceContext("Repeated task context."),
            observation_started_at=T0 + timedelta(days=8),
            observed_at=T0 + timedelta(days=7),
            recorded_at=T0 + timedelta(days=8, minutes=1),
            provenance=actor_trail(),
        )


def test_repeated_performance_window_roundtrips_exactly() -> None:
    record = EvidenceRecord(
        evidence_id=EvidenceId("ev_repeat"),
        subject_ref=SUBJECT,
        kind=EvidenceKind.REPEATED_PERFORMANCE,
        summary="Repeated bounded performance.",
        context=EvidenceContext("Repeated task context."),
        observation_started_at=T0,
        observed_at=T0 + timedelta(days=7),
        recorded_at=T0 + timedelta(days=7, minutes=1),
        provenance=actor_trail(),
    )
    records = EpistemicRecordSet(evidence_records=(record,))
    restored = EpistemicRecordSet.from_json(records.to_json())
    assert restored == records
    assert restored.evidence_records[0].observation_started_at == T0
    assert restored.evidence_records[0].observed_at == T0 + timedelta(days=7)


def assessment(eid: str, bearing: EvidenceBearing) -> EvidenceAssessment:
    return EvidenceAssessment(
        EvidenceId(eid),
        bearing,
        EvidenceReliability.LOW,
        "Limited coverage.",
        "Directional bearing exists but overall sufficiency is unresolved.",
    )


def conflicted_evaluation(conclusion: EvaluationConclusion) -> ClaimEvaluation:
    return ClaimEvaluation(
        evaluation_id=ClaimEvaluationId("eval_conflict"),
        claim_id=CapabilityClaimId("claim_conflict"),
        policy_ref=EvaluationPolicyRef.parse("core:manual_evidence_review@1"),
        evaluator_ref=EvaluatorRef(EvaluatorKind.HUMAN, "local:reviewer"),
        evaluated_at=T0,
        evidence_assessments=(
            assessment("ev_support", EvidenceBearing.SUPPORTS),
            assessment("ev_contradict", EvidenceBearing.CONTRADICTS),
        ),
        coverage=CoverageAssessment(CoverageStatus.PARTIAL, "Coverage remains insufficient."),
        conflict_status=ConflictStatus.UNRESOLVED,
        conclusion=conclusion,
        rationale="Conflict is visible and not sufficient for a directional conclusion.",
    )


def test_unresolved_conflict_can_remain_insufficient() -> None:
    item = conflicted_evaluation(EvaluationConclusion.INSUFFICIENT)
    assert item.conflict_status is ConflictStatus.UNRESOLVED
    assert item.conclusion is EvaluationConclusion.INSUFFICIENT


def test_unresolved_conflict_can_abstain() -> None:
    item = conflicted_evaluation(EvaluationConclusion.ABSTAINED)
    assert item.conflict_status is ConflictStatus.UNRESOLVED
    assert item.conclusion is EvaluationConclusion.ABSTAINED


def test_resolved_conflict_still_requires_directional_conclusion() -> None:
    with pytest.raises(InvalidEvaluationError, match="directional conclusion"):
        ClaimEvaluation(
            evaluation_id=ClaimEvaluationId("eval_resolved"),
            claim_id=CapabilityClaimId("claim_conflict"),
            policy_ref=EvaluationPolicyRef.parse("core:manual_evidence_review@1"),
            evaluator_ref=EvaluatorRef(EvaluatorKind.HUMAN, "local:reviewer"),
            evaluated_at=T0,
            evidence_assessments=(
                assessment("ev_support", EvidenceBearing.SUPPORTS),
                assessment("ev_contradict", EvidenceBearing.CONTRADICTS),
            ),
            coverage=CoverageAssessment(CoverageStatus.PARTIAL, "Partial coverage."),
            conflict_status=ConflictStatus.RESOLVED_BY_POLICY,
            conclusion=EvaluationConclusion.INSUFFICIENT,
            rationale="Invalid attempted resolution.",
        )


def test_large_provenance_chain_does_not_depend_on_python_recursion_depth() -> None:
    records = []
    count = 1800
    for index in range(count):
        evidence_id = EvidenceId(f"ev_{index:04d}")
        if index == 0:
            provenance = actor_trail()
        else:
            provenance = ProvenanceTrail(
                sources=(
                    ProvenanceSource(
                        ProvenanceSourceKind.EVIDENCE_RECORD,
                        f"ev_{index - 1:04d}",
                    ),
                )
            )
        records.append(
            EvidenceRecord(
                evidence_id=evidence_id,
                subject_ref=SUBJECT,
                kind=EvidenceKind.PROJECT,
                summary=f"Derived observation {index}.",
                context=EvidenceContext("Synthetic provenance stress context."),
                observed_at=T0,
                recorded_at=T0 + timedelta(seconds=index + 1),
                provenance=provenance,
            )
        )

    result = EpistemicRecordSet(evidence_records=tuple(records))
    assert len(result.evidence_records) == count
