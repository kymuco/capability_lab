from datetime import datetime, timedelta, timezone

import pytest

from capability_lab.epistemics import (
    CapabilityClaim,
    CapabilityClaimId,
    CapabilitySubjectRef,
    ClaimEvaluation,
    ClaimEvaluationId,
    ClaimScope,
    ConflictStatus,
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
    InvalidRecordSetError,
    ProvenanceSource,
    ProvenanceSourceKind,
    ProvenanceTrail,
)
from capability_lab.semantics import CapabilityConceptRef


T0 = datetime(2026, 8, 14, 9, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("subject_01")


def trail() -> ProvenanceTrail:
    return ProvenanceTrail(
        sources=(ProvenanceSource(ProvenanceSourceKind.ACTOR, "operator"),)
    )


def records() -> EpistemicRecordSet:
    evidence = EvidenceRecord(
        evidence_id=EvidenceId("ev_01"),
        subject_ref=SUBJECT,
        kind=EvidenceKind.PROJECT,
        summary="Observed bounded project work.",
        context=EvidenceContext("Bench context.", ("low_voltage_dc",)),
        observed_at=T0,
        recorded_at=T0 + timedelta(minutes=1),
        provenance=trail(),
        payload_refs=("artifact:motor_01",),
    )
    claim = CapabilityClaim(
        claim_id=CapabilityClaimId("claim_01"),
        subject_ref=SUBJECT,
        concept_ref=CapabilityConceptRef.parse(
            "civilization_bootstrap:electric_motor_construction@1"
        ),
        statement="Subject can construct a bounded brushed DC motor.",
        scope=ClaimScope("Low-voltage scope."),
        created_at=T0 + timedelta(minutes=2),
        provenance=trail(),
    )
    evaluation = ClaimEvaluation(
        evaluation_id=ClaimEvaluationId("eval_01"),
        claim_id=claim.claim_id,
        policy_ref=EvaluationPolicyRef.parse("core:manual_evidence_review@1"),
        evaluator_ref=EvaluatorRef(EvaluatorKind.HUMAN, "reviewer"),
        evaluated_at=T0 + timedelta(minutes=3),
        evidence_assessments=(
            EvidenceAssessment(
                evidence.evidence_id,
                EvidenceBearing.SUPPORTS,
                EvidenceReliability.MODERATE,
                "Bounded observation.",
                "Relevant to stated scope.",
            ),
        ),
        coverage=CoverageAssessment(CoverageStatus.PARTIAL, "One context."),
        conflict_status=ConflictStatus.NONE,
        conclusion=EvaluationConclusion.SUPPORTED,
        rationale="Supported within stated scope.",
    )
    return EpistemicRecordSet(
        evidence_records=(evidence,),
        claims=(claim,),
        evaluations=(evaluation,),
    )


def test_payload_refs_string_is_not_accepted_as_array() -> None:
    payload = records().to_dict()
    payload["evidence_records"][0]["payload_refs"] = "artifact:motor_01"
    with pytest.raises(InvalidRecordSetError, match="must be an array"):
        EpistemicRecordSet.from_dict(payload)


def test_provenance_steps_string_is_not_accepted_as_array() -> None:
    payload = records().to_dict()
    payload["evidence_records"][0]["provenance"]["steps"] = "capture"
    with pytest.raises(InvalidRecordSetError, match="must be an array"):
        EpistemicRecordSet.from_dict(payload)


def test_evidence_assessments_string_is_not_accepted_as_array() -> None:
    payload = records().to_dict()
    payload["evaluations"][0]["evidence_assessments"] = "ev_01"
    with pytest.raises(InvalidRecordSetError, match="must be an array"):
        EpistemicRecordSet.from_dict(payload)


def test_invalid_nested_enum_is_rejected() -> None:
    payload = records().to_dict()
    payload["evaluations"][0]["evidence_assessments"][0]["bearing"] = "proves"
    with pytest.raises(InvalidRecordSetError, match="invalid evidence bearing"):
        EpistemicRecordSet.from_dict(payload)


def test_wrong_schema_is_rejected() -> None:
    payload = records().to_dict()
    payload["schema"] = "capability_epistemics/v999"
    with pytest.raises(InvalidRecordSetError, match="unsupported epistemic schema"):
        EpistemicRecordSet.from_dict(payload)
