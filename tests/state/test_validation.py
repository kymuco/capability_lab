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
    ProvenanceSource,
    ProvenanceSourceKind,
    ProvenanceTrail,
)
from capability_lab.semantics import (
    CapabilityCatalog,
    CapabilityConcept,
    CapabilityConceptRef,
    CapabilityId,
    CapabilityNamespace,
)
from capability_lab.state import (
    CompetenceDimensionDefinition,
    CompetenceDimensionState,
    CompetenceFrame,
    CompetenceFrameCatalog,
    CompetenceFrameId,
    CompetenceFrameRef,
    DimensionStanding,
    InvalidStateSet,
    PersonalCapabilityState,
    PersonalCapabilityStateId,
    PersonalCapabilityStateSet,
    StateDerivationPolicyRef,
    StateDeriverKind,
    StateDeriverRef,
)

T0 = datetime(2026, 8, 15, 6, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("subject_01")
CONCEPT = CapabilityConceptRef.parse("civilization_bootstrap:electric_motor_construction@1")
FRAME = CompetenceFrame(
    CompetenceFrameId.parse("civilization_bootstrap:technical_competence"),
    1,
    "Technical competence",
    "Bounded technical-generalist frame fixture.",
    (
        CompetenceDimensionDefinition("execution", "Execution", "Construction and execution."),
        CompetenceDimensionDefinition("diagnosis", "Diagnosis", "Diagnosis and fault isolation."),
    ),
)
POLICY = StateDerivationPolicyRef.parse("core:manual_supported_state@1")
DERIVER = StateDeriverRef(StateDeriverKind.HUMAN, "operator")


def provenance() -> ProvenanceTrail:
    return ProvenanceTrail((ProvenanceSource(ProvenanceSourceKind.ACTOR, "operator"),))


def epistemics(*, subject=SUBJECT, concept=CONCEPT, conclusion=EvaluationConclusion.SUPPORTED, evaluated_at=T0) -> EpistemicRecordSet:
    evidence = EvidenceRecord(
        evidence_id=EvidenceId("ev_motor"),
        subject_ref=subject,
        kind=EvidenceKind.PROJECT,
        summary="Constructed a bounded low-voltage brushed motor fixture.",
        context=EvidenceContext("Bench environment with ordinary tools and reference material."),
        observed_at=T0 - timedelta(minutes=10),
        recorded_at=T0 - timedelta(minutes=9),
        provenance=provenance(),
    )
    claim = CapabilityClaim(
        claim_id=CapabilityClaimId("claim_execution"),
        subject_ref=subject,
        concept_ref=concept,
        statement="Can construct a basic brushed DC motor from standard parts with reference material.",
        scope=ClaimScope("Low-voltage brushed DC motor, ordinary tools, reference documentation allowed."),
        created_at=T0 - timedelta(minutes=8),
        provenance=provenance(),
    )
    bearing = EvidenceBearing.SUPPORTS if conclusion is EvaluationConclusion.SUPPORTED else EvidenceBearing.INDETERMINATE
    evaluation = ClaimEvaluation(
        evaluation_id=ClaimEvaluationId("eval_execution"),
        claim_id=claim.claim_id,
        policy_ref=EvaluationPolicyRef.parse("core:manual_evidence_review@1"),
        evaluator_ref=EvaluatorRef(EvaluatorKind.HUMAN, "operator"),
        evaluated_at=evaluated_at,
        evidence_assessments=(
            EvidenceAssessment(
                evidence.evidence_id,
                bearing,
                EvidenceReliability.HIGH,
                "The observation covers the bounded execution claim.",
                "The project directly bears on the scoped proposition.",
            ),
        ),
        coverage=CoverageAssessment(CoverageStatus.SUFFICIENT_FOR_CLAIM, "Relevant bounded execution coverage."),
        conflict_status=ConflictStatus.NONE,
        conclusion=conclusion,
        rationale="Governed evaluation of the bounded project evidence.",
    )
    return EpistemicRecordSet((evidence,), (claim,), (evaluation,))


def state(*, subject=SUBJECT, concept=CONCEPT, as_of=T0, dimensions=None) -> PersonalCapabilityState:
    if dimensions is None:
        dimensions = (
            CompetenceDimensionState(
                "execution",
                DimensionStanding.SUPPORTED,
                (CapabilityClaimId("claim_execution"),),
                (ClaimEvaluationId("eval_execution"),),
                "A bounded execution claim is supported.",
            ),
            CompetenceDimensionState("diagnosis", DimensionStanding.UNKNOWN, rationale="No diagnosis basis."),
        )
    return PersonalCapabilityState(
        PersonalCapabilityStateId("state_motor"),
        subject,
        concept,
        FRAME.ref,
        POLICY,
        DERIVER,
        as_of,
        T0 + timedelta(minutes=5),
        dimensions,
        "Bounded current supported state.",
    )


def test_valid_state_cross_validates_all_three_layers() -> None:
    records = epistemics()
    states = PersonalCapabilityStateSet(SUBJECT, (state(),))
    capability_catalog = CapabilityCatalog(
        namespaces=(CapabilityNamespace("civilization_bootstrap", "Civilization Bootstrap"),),
        concepts=(
            CapabilityConcept(
                CapabilityId.parse("civilization_bootstrap:electric_motor_construction"),
                "Electric motor construction",
                "Construct bounded electric-motor systems in stated contexts.",
                revision=1,
            ),
        ),
    )
    frame_catalog = CompetenceFrameCatalog((FRAME,))

    states.validate_against_epistemics(records)
    states.validate_against_capability_catalog(capability_catalog)
    states.validate_against_frame_catalog(frame_catalog)


def test_supported_state_cannot_invent_support_from_insufficient_evaluation() -> None:
    records = epistemics(conclusion=EvaluationConclusion.INSUFFICIENT)
    states = PersonalCapabilityStateSet(SUBJECT, (state(),))
    with pytest.raises(InvalidStateSet, match="requires a basis ClaimEvaluation with SUPPORTED"):
        states.validate_against_epistemics(records)


def test_state_cannot_use_other_subject_claims() -> None:
    records = epistemics(subject=CapabilitySubjectRef("subject_other"))
    states = PersonalCapabilityStateSet(SUBJECT, (state(),))
    with pytest.raises(InvalidStateSet, match="different subject"):
        states.validate_against_epistemics(records)


def test_state_cannot_silently_upgrade_claim_concept_revision() -> None:
    records = epistemics(concept=CapabilityConceptRef.parse("civilization_bootstrap:electric_motor_construction@2"))
    states = PersonalCapabilityStateSet(SUBJECT, (state(),))
    with pytest.raises(InvalidStateSet, match="different capability concept revision"):
        states.validate_against_epistemics(records)


def test_future_evaluation_cannot_affect_past_state() -> None:
    records = epistemics(evaluated_at=T0 + timedelta(minutes=1))
    states = PersonalCapabilityStateSet(SUBJECT, (state(as_of=T0),))
    with pytest.raises(InvalidStateSet, match="after its as_of"):
        states.validate_against_epistemics(records)


def test_frame_validation_requires_exact_full_dimension_set() -> None:
    incomplete = state(
        dimensions=(
            CompetenceDimensionState(
                "execution",
                DimensionStanding.SUPPORTED,
                (CapabilityClaimId("claim_execution"),),
                (ClaimEvaluationId("eval_execution"),),
                "Supported execution only.",
            ),
        )
    )
    states = PersonalCapabilityStateSet(SUBJECT, (incomplete,))
    with pytest.raises(InvalidStateSet, match="exactly match frame"):
        states.validate_against_frame_catalog(CompetenceFrameCatalog((FRAME,)))


def test_frame_validation_rejects_silent_latest_revision_substitution() -> None:
    later = CompetenceFrame(FRAME.frame_id, 2, FRAME.name, FRAME.description, FRAME.dimensions)
    states = PersonalCapabilityStateSet(SUBJECT, (state(),))
    with pytest.raises(InvalidStateSet, match="exact frame revision"):
        states.validate_against_frame_catalog(CompetenceFrameCatalog((later,)))


def test_capability_catalog_validation_rejects_silent_latest_revision_substitution() -> None:
    later_catalog = CapabilityCatalog(
        namespaces=(CapabilityNamespace("civilization_bootstrap", "Civilization Bootstrap"),),
        concepts=(
            CapabilityConcept(
                CapabilityId.parse("civilization_bootstrap:electric_motor_construction"),
                "Electric motor construction",
                "Later semantic revision fixture.",
                revision=2,
            ),
        ),
    )
    states = PersonalCapabilityStateSet(SUBJECT, (state(),))
    with pytest.raises(InvalidStateSet, match="exact capability revision"):
        states.validate_against_capability_catalog(later_catalog)
