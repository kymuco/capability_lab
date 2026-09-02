from datetime import datetime, timedelta, timezone

import pytest

from capability_lab.epistemics import (
    ActorRef,
    CapabilityClaim,
    CapabilityClaimId,
    CapabilitySubjectRef,
    ClaimEvaluation,
    ClaimEvaluationId,
    ClaimScope,
    ConflictStatus,
    ContextFactor,
    ContextFactorKind,
    CoverageAssessment,
    CoverageStatus,
    EvaluationConclusion,
    EvaluationPolicyRef,
    EvaluatorKind,
    EvaluatorRef,
    EvidenceAssessment,
    EvidenceBearing,
    EvidenceContext,
    EvidenceId,
    EvidenceKind,
    EvidenceOutcome,
    EvidenceOutcomeStatus,
    EvidenceRecord,
    EvidenceReliability,
    InvalidClaimError,
    InvalidEvaluationError,
    InvalidEvidenceError,
    ProvenanceSource,
    ProvenanceSourceKind,
    ProvenanceStep,
    ProvenanceTrail,
)
from capability_lab.semantics import CapabilityConceptRef, CapabilityId


T0 = datetime(2026, 8, 14, 9, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("subject_01")


def provenance(ref: str = "operator_01") -> ProvenanceTrail:
    return ProvenanceTrail(
        sources=(ProvenanceSource(ProvenanceSourceKind.ACTOR, ref),),
        steps=(
            ProvenanceStep(
                "manual_capture",
                T0,
                actor_ref=ActorRef(ref),
                mechanism_ref="capability_lab",
            ),
        ),
    )


def evidence(evidence_id: str = "ev_01", *, subject: CapabilitySubjectRef = SUBJECT) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=EvidenceId(evidence_id),
        subject_ref=subject,
        kind=EvidenceKind.PROJECT,
        summary="Assembled a brushed DC motor from standard parts.",
        context=EvidenceContext(
            "Low-voltage bench build with ordinary tools and reference material.",
            scope_tags=("low_voltage_dc",),
            factors=(
                ContextFactor(ContextFactorKind.TOOL, "Multimeter"),
                ContextFactor(ContextFactorKind.REFERENCE_MATERIAL, "Motor datasheet"),
            ),
        ),
        observed_at=T0,
        recorded_at=T0 + timedelta(minutes=2),
        provenance=provenance(),
        outcome=EvidenceOutcome(EvidenceOutcomeStatus.SUCCESS, "Motor operated under load."),
        payload_refs=("artifact:motor_build_01",),
    )


def claim(*, subject: CapabilitySubjectRef = SUBJECT) -> CapabilityClaim:
    return CapabilityClaim(
        claim_id=CapabilityClaimId("claim_01"),
        subject_ref=subject,
        concept_ref=CapabilityConceptRef.parse("civilization_bootstrap:electric_motor_construction@1"),
        statement="Subject can construct a basic brushed DC motor from standard parts.",
        scope=ClaimScope(
            "Low-voltage brushed DC motor using ordinary hand tools with reference documentation allowed.",
            ("low_voltage_dc", "reference_allowed"),
        ),
        created_at=T0 + timedelta(minutes=5),
        provenance=provenance(),
    )


def evaluation(*assessments: EvidenceAssessment, conclusion=EvaluationConclusion.SUPPORTED, conflict=ConflictStatus.NONE) -> ClaimEvaluation:
    return ClaimEvaluation(
        evaluation_id=ClaimEvaluationId("eval_01"),
        claim_id=CapabilityClaimId("claim_01"),
        policy_ref=EvaluationPolicyRef.parse("core:manual_evidence_review@1"),
        evaluator_ref=EvaluatorRef(EvaluatorKind.HUMAN, "reviewer_01"),
        evaluated_at=T0 + timedelta(minutes=10),
        evidence_assessments=assessments,
        coverage=CoverageAssessment(CoverageStatus.PARTIAL, "One bounded low-voltage build observed."),
        conflict_status=conflict,
        conclusion=conclusion,
        rationale="Conclusion is limited to the stated claim scope.",
    )


def test_evidence_record_has_no_capability_reference() -> None:
    record = evidence()
    assert not hasattr(record, "concept_ref")


def test_assistance_is_context_not_penalty() -> None:
    context = EvidenceContext(
        "Assisted execution.",
        factors=(ContextFactor(ContextFactorKind.ASSISTANCE, "One conceptual hint"),),
    )
    assert context.factors[0].kind is ContextFactorKind.ASSISTANCE


def test_failure_is_valid_evidence_outcome() -> None:
    outcome = EvidenceOutcome(EvidenceOutcomeStatus.FAILURE, "Unfamiliar winding design did not operate.")
    assert outcome.status is EvidenceOutcomeStatus.FAILURE
    assert not hasattr(outcome, "capability_level")


def test_naive_evidence_time_is_rejected() -> None:
    with pytest.raises(Exception, match="timezone-aware"):
        EvidenceRecord(
            EvidenceId("ev_naive"), SUBJECT, EvidenceKind.PROJECT, "Observed work.",
            EvidenceContext("Bench context."), datetime(2026, 8, 14, 9, 0),
            T0, provenance(),
        )


def test_recorded_at_before_observed_at_is_rejected() -> None:
    with pytest.raises(InvalidEvidenceError, match="must not precede"):
        EvidenceRecord(
            EvidenceId("ev_time"), SUBJECT, EvidenceKind.PROJECT, "Observed work.",
            EvidenceContext("Bench context."), T0, T0 - timedelta(seconds=1), provenance(),
        )


def test_claim_requires_exact_concept_revision_ref() -> None:
    with pytest.raises(InvalidClaimError, match="exact CapabilityConceptRef"):
        CapabilityClaim(
            CapabilityClaimId("claim_bad"), SUBJECT,
            CapabilityId("civilization_bootstrap", "electric_motor_construction"),  # type: ignore[arg-type]
            "Subject can construct a motor.", ClaimScope("Low-voltage scope."), T0, provenance(),
        )


def test_claim_does_not_bundle_evidence() -> None:
    item = claim()
    assert not hasattr(item, "evidence_refs")
    assert not hasattr(item, "conclusion")


def test_policy_ref_requires_exact_revision() -> None:
    assert str(EvaluationPolicyRef.parse("core:manual_evidence_review@2")) == "core:manual_evidence_review@2"
    with pytest.raises(InvalidEvaluationError):
        EvaluationPolicyRef.parse("core:manual_evidence_review")
    with pytest.raises(InvalidEvaluationError):
        EvaluationPolicyRef.parse("core:manual_evidence_review@01")


def test_evidence_kind_does_not_encode_reliability() -> None:
    item = evidence()
    assert item.kind is EvidenceKind.PROJECT
    assert not hasattr(item, "reliability")


def test_supported_requires_supporting_evidence() -> None:
    assessment = EvidenceAssessment(
        EvidenceId("ev_01"), EvidenceBearing.INDETERMINATE, EvidenceReliability.HIGH,
        "Only one context observed.", "Evidence does not resolve the proposition.",
    )
    with pytest.raises(InvalidEvaluationError, match="requires at least one supporting"):
        evaluation(assessment)


def test_empty_evaluation_can_be_insufficient() -> None:
    item = evaluation(conclusion=EvaluationConclusion.INSUFFICIENT)
    assert item.evidence_assessments == ()


def test_duplicate_evidence_assessment_is_rejected() -> None:
    assessment = EvidenceAssessment(
        EvidenceId("ev_01"), EvidenceBearing.SUPPORTS, EvidenceReliability.HIGH,
        "Observed bounded build.", "Successful relevant demonstration.",
    )
    with pytest.raises(InvalidEvaluationError, match="at most once"):
        evaluation(assessment, assessment)


def test_unresolved_conflict_can_be_mixed() -> None:
    support = EvidenceAssessment(
        EvidenceId("ev_01"), EvidenceBearing.SUPPORTS, EvidenceReliability.HIGH,
        "Relevant successful build.", "Supports the bounded proposition.",
    )
    contradiction = EvidenceAssessment(
        EvidenceId("ev_02"), EvidenceBearing.CONTRADICTS, EvidenceReliability.HIGH,
        "Relevant failed repeat.", "Contradicts stable repeatability.",
    )
    item = evaluation(
        support, contradiction,
        conclusion=EvaluationConclusion.MIXED,
        conflict=ConflictStatus.UNRESOLVED,
    )
    assert item.conflict_status is ConflictStatus.UNRESOLVED


def test_conflict_cannot_be_hidden_as_none() -> None:
    support = EvidenceAssessment(
        EvidenceId("ev_01"), EvidenceBearing.SUPPORTS, EvidenceReliability.MODERATE,
        "Relevant success.", "Supports claim.",
    )
    contradiction = EvidenceAssessment(
        EvidenceId("ev_02"), EvidenceBearing.CONTRADICTS, EvidenceReliability.MODERATE,
        "Relevant failure.", "Contradicts claim.",
    )
    with pytest.raises(InvalidEvaluationError, match="explicit conflict status"):
        evaluation(support, contradiction, conclusion=EvaluationConclusion.SUPPORTED)
