from datetime import datetime, timedelta, timezone

from capability_lab.derivation import (
    ClaimDimensionBinding,
    DeterministicStateDerivationRequest,
    derive_supported_state_v1,
)
from capability_lab.domains import (
    CIVILIZATION_BOOTSTRAP_TECHNICAL_COMPETENCE_FRAME_V1,
    build_civilization_bootstrap_frame_catalog_v1,
    build_civilization_bootstrap_seed_catalog_v0,
)
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
from capability_lab.state import (
    DimensionConflictStatus,
    DimensionStanding,
    PersonalCapabilityStateId,
    PersonalCapabilityStateSet,
)


T0 = datetime(2026, 8, 15, 10, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("subject_pr5_smoke")
CLAIM_ID = CapabilityClaimId("claim_pr5_basic_circuits")
EVALUATION_ID = ClaimEvaluationId("eval_pr5_basic_circuits")
EVIDENCE_ID = EvidenceId("evidence_pr5_basic_circuits")


def _provenance() -> ProvenanceTrail:
    return ProvenanceTrail(
        (ProvenanceSource(ProvenanceSourceKind.ACTOR, "pr5_smoke_reviewer"),)
    )


def _dimension(state, key: str):
    return next(item for item in state.dimensions if item.dimension_key == key)


def test_real_basic_circuits_concept_flows_pr2_to_pr4_to_pr3() -> None:
    catalog = build_civilization_bootstrap_seed_catalog_v0()
    frame = CIVILIZATION_BOOTSTRAP_TECHNICAL_COMPETENCE_FRAME_V1
    concept = next(
        concept
        for concept in catalog.concepts
        if concept.capability_id.key == "basic_circuits"
    )

    evidence = EvidenceRecord(
        evidence_id=EVIDENCE_ID,
        subject_ref=SUBJECT,
        kind=EvidenceKind.PROJECT,
        summary="Analyzed and checked a bounded DC resistor circuit exercise.",
        context=EvidenceContext(
            "Bench exercise with stated resistor values, a low-voltage source, reference equations, and a digital multimeter."
        ),
        observed_at=T0 - timedelta(minutes=40),
        recorded_at=T0 - timedelta(minutes=39),
        provenance=_provenance(),
    )
    claim = CapabilityClaim(
        claim_id=CLAIM_ID,
        subject_ref=SUBJECT,
        concept_ref=concept.ref,
        statement="Can analyze a bounded DC resistor circuit and predict voltage/current relationships under stated component assumptions.",
        scope=ClaimScope(
            "Low-voltage DC resistor circuits with explicit topology, nominal component values, and access to ordinary calculation/reference tools."
        ),
        created_at=T0 - timedelta(minutes=30),
        provenance=_provenance(),
    )
    evaluation = ClaimEvaluation(
        evaluation_id=EVALUATION_ID,
        claim_id=CLAIM_ID,
        policy_ref=EvaluationPolicyRef.parse("civilization_bootstrap:bounded_project_evaluation@1"),
        evaluator_ref=EvaluatorRef(EvaluatorKind.HUMAN, "pr5_smoke_reviewer"),
        evaluated_at=T0 - timedelta(minutes=10),
        evidence_assessments=(
            EvidenceAssessment(
                EVIDENCE_ID,
                EvidenceBearing.SUPPORTS,
                EvidenceReliability.HIGH,
                "The exercise directly covers the bounded circuit-analysis claim.",
                "Predictions and measurements were mutually consistent within the stated exercise assumptions.",
            ),
        ),
        coverage=CoverageAssessment(
            CoverageStatus.SUFFICIENT_FOR_CLAIM,
            "Sufficient only for the explicitly bounded claim scope.",
        ),
        conflict_status=ConflictStatus.NONE,
        conclusion=EvaluationConclusion.SUPPORTED,
        rationale="The selected project evidence supports the bounded circuit-analysis proposition under this evaluation policy.",
    )
    records = EpistemicRecordSet(
        evidence_records=(evidence,),
        claims=(claim,),
        evaluations=(evaluation,),
    )

    request = DeterministicStateDerivationRequest(
        state_id=PersonalCapabilityStateId("state_pr5_basic_circuits"),
        subject_ref=SUBJECT,
        concept_ref=concept.ref,
        frame_ref=frame.ref,
        as_of=T0,
        derived_at=T0,
        selected_evaluation_ids=(EVALUATION_ID,),
        claim_dimension_bindings=(
            ClaimDimensionBinding(
                CLAIM_ID,
                ("conceptual_knowledge", "calculation"),
            ),
        ),
    )

    state = derive_supported_state_v1(
        records=records,
        frame=frame,
        request=request,
    )

    for key in ("conceptual_knowledge", "calculation"):
        dimension = _dimension(state, key)
        assert dimension.standing is DimensionStanding.SUPPORTED
        assert dimension.supported_claim_ids == (CLAIM_ID,)
        assert dimension.basis_evaluation_ids == (EVALUATION_ID,)
        assert dimension.conflict_status is DimensionConflictStatus.NONE

    for key in ("execution", "diagnosis", "transfer", "independence", "explanation"):
        dimension = _dimension(state, key)
        assert dimension.standing is DimensionStanding.UNKNOWN
        assert dimension.supported_claim_ids == ()
        assert dimension.basis_evaluation_ids == ()

    state_set = PersonalCapabilityStateSet(SUBJECT, (state,))
    state_set.validate_against_epistemics(records)
    state_set.validate_against_capability_catalog(catalog)
    state_set.validate_against_frame_catalog(
        build_civilization_bootstrap_frame_catalog_v1()
    )
