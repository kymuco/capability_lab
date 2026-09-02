from copy import deepcopy
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
from capability_lab.semantics import CapabilityCatalog, CapabilityConcept, CapabilityConceptRef, CapabilityId, CapabilityNamespace


T0 = datetime(2026, 8, 14, 9, 0, tzinfo=timezone.utc)
ALICE = CapabilitySubjectRef("alice")
BOB = CapabilitySubjectRef("bob")


def trail(*sources: ProvenanceSource) -> ProvenanceTrail:
    return ProvenanceTrail(sources=sources or (ProvenanceSource(ProvenanceSourceKind.ACTOR, "operator"),))


def evidence(eid: str, subject=ALICE, provenance=None) -> EvidenceRecord:
    return EvidenceRecord(
        EvidenceId(eid), subject, EvidenceKind.PROJECT, f"Observation {eid}.",
        EvidenceContext("Bounded bench context.", ("low_voltage_dc",)),
        T0, T0 + timedelta(minutes=1), provenance or trail(),
    )


def claim(subject=ALICE, revision=1) -> CapabilityClaim:
    return CapabilityClaim(
        CapabilityClaimId("claim_motor"), subject,
        CapabilityConceptRef(CapabilityId("civilization_bootstrap", "electric_motor_construction"), revision),
        "Subject can construct a basic brushed DC motor.",
        ClaimScope("Low-voltage brushed DC motor with ordinary reference material.", ("low_voltage_dc",)),
        T0 + timedelta(minutes=2), trail(),
    )


def evaluation(eid: str = "ev_a") -> ClaimEvaluation:
    return ClaimEvaluation(
        ClaimEvaluationId("eval_motor"), CapabilityClaimId("claim_motor"),
        EvaluationPolicyRef.parse("core:manual_evidence_review@1"),
        EvaluatorRef(EvaluatorKind.HUMAN, "reviewer"),
        T0 + timedelta(minutes=3),
        (EvidenceAssessment(EvidenceId(eid), EvidenceBearing.SUPPORTS, EvidenceReliability.HIGH, "Bounded match.", "Direct relevant demonstration."),),
        CoverageAssessment(CoverageStatus.PARTIAL, "One bounded context."),
        ConflictStatus.NONE, EvaluationConclusion.SUPPORTED,
        "Supported only within stated scope.",
    )


def test_subject_mismatch_between_evidence_and_claim_is_rejected() -> None:
    with pytest.raises(InvalidRecordSetError, match="subject must match"):
        EpistemicRecordSet(
            evidence_records=(evidence("ev_a", BOB),),
            claims=(claim(ALICE),),
            evaluations=(evaluation(),),
        )


def test_missing_evidence_reference_is_rejected() -> None:
    with pytest.raises(InvalidRecordSetError, match="missing evidence"):
        EpistemicRecordSet(claims=(claim(),), evaluations=(evaluation("missing"),))


def test_missing_claim_reference_is_rejected() -> None:
    with pytest.raises(InvalidRecordSetError, match="missing claim"):
        EpistemicRecordSet(evidence_records=(evidence("ev_a"),), evaluations=(evaluation(),))


def test_derived_evidence_may_reference_source_evidence() -> None:
    source = evidence("ev_source")
    derived = evidence(
        "ev_derived",
        provenance=trail(ProvenanceSource(ProvenanceSourceKind.EVIDENCE_RECORD, "ev_source")),
    )
    records = EpistemicRecordSet(evidence_records=(derived, source))
    assert [str(item.evidence_id) for item in records.evidence_records] == ["ev_derived", "ev_source"]


def test_dangling_derived_evidence_source_is_rejected() -> None:
    derived = evidence(
        "ev_derived",
        provenance=trail(ProvenanceSource(ProvenanceSourceKind.EVIDENCE_RECORD, "missing")),
    )
    with pytest.raises(InvalidRecordSetError, match="missing source evidence"):
        EpistemicRecordSet(evidence_records=(derived,))


def test_derived_evidence_cycle_is_rejected() -> None:
    a = evidence("ev_a", provenance=trail(ProvenanceSource(ProvenanceSourceKind.EVIDENCE_RECORD, "ev_b")))
    b = evidence("ev_b", provenance=trail(ProvenanceSource(ProvenanceSourceKind.EVIDENCE_RECORD, "ev_a")))
    with pytest.raises(InvalidRecordSetError, match="acyclic"):
        EpistemicRecordSet(evidence_records=(a, b))


def test_record_set_roundtrip_is_deterministic() -> None:
    first = EpistemicRecordSet(
        evidence_records=(evidence("ev_b"), evidence("ev_a")),
        claims=(claim(),),
        evaluations=(evaluation("ev_a"),),
    )
    second = EpistemicRecordSet(
        evidence_records=(evidence("ev_a"), evidence("ev_b")),
        claims=(claim(),),
        evaluations=(evaluation("ev_a"),),
    )
    assert first.to_json() == second.to_json()
    assert EpistemicRecordSet.from_json(first.to_json()) == first


def test_unknown_top_level_field_is_rejected() -> None:
    records = EpistemicRecordSet(evidence_records=(evidence("ev_a"),))
    payload = records.to_dict()
    payload["confidence"] = 0.9
    with pytest.raises(InvalidRecordSetError, match="unknown fields"):
        EpistemicRecordSet.from_dict(payload)


def test_unknown_nested_field_is_rejected() -> None:
    records = EpistemicRecordSet(evidence_records=(evidence("ev_a"),))
    payload = records.to_dict()
    payload["evidence_records"][0]["capability_id"] = "civilization_bootstrap:electric_motor_construction"
    with pytest.raises(InvalidRecordSetError, match="unknown fields"):
        EpistemicRecordSet.from_dict(payload)


def test_duplicate_json_keys_are_rejected() -> None:
    payload = '{"schema":"capability_epistemics/v1","schema":"capability_epistemics/v1","evidence_records":[],"claims":[],"evaluations":[]}'
    with pytest.raises(InvalidRecordSetError, match="duplicate JSON object key"):
        EpistemicRecordSet.from_json(payload)


def test_nonstandard_json_numeric_constant_is_rejected() -> None:
    payload = '{"schema":"capability_epistemics/v1","evidence_records":[],"claims":[],"evaluations":[],"x":NaN}'
    with pytest.raises(InvalidRecordSetError, match="non-standard JSON"):
        EpistemicRecordSet.from_json(payload)


def test_serialization_does_not_create_shareability_flag() -> None:
    payload = EpistemicRecordSet(evidence_records=(evidence("ev_a"),)).to_dict()
    assert "public" not in payload
    assert "shareable" not in payload


def test_exact_claim_revision_matches_catalog() -> None:
    concept = CapabilityConcept(
        CapabilityId("civilization_bootstrap", "electric_motor_construction"),
        "Electric motor construction", "Construct a bounded electric motor.", revision=1,
    )
    catalog = CapabilityCatalog(
        namespaces=(CapabilityNamespace("civilization_bootstrap", "Civilization Bootstrap"),),
        concepts=(concept,),
    )
    EpistemicRecordSet(claims=(claim(revision=1),)).validate_against_catalog(catalog)


def test_stale_claim_revision_never_silently_upgrades_to_latest_catalog() -> None:
    concept = CapabilityConcept(
        CapabilityId("civilization_bootstrap", "electric_motor_construction"),
        "Electric motor construction", "Revised bounded definition.", revision=2,
    )
    catalog = CapabilityCatalog(
        namespaces=(CapabilityNamespace("civilization_bootstrap", "Civilization Bootstrap"),),
        concepts=(concept,),
    )
    with pytest.raises(InvalidRecordSetError, match="exact concept revision"):
        EpistemicRecordSet(claims=(claim(revision=1),)).validate_against_catalog(catalog)


def test_epistemic_record_set_contains_no_personal_state() -> None:
    records = EpistemicRecordSet()
    assert not hasattr(records, "personal_capability_state")
    assert not hasattr(records, "mastery")
