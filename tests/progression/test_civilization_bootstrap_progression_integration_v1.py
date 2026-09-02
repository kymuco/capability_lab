from datetime import datetime, timedelta, timezone

from capability_lab.derivation import ClaimDimensionBinding, DeterministicStateDerivationRequest, derive_supported_state_v1
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
from capability_lab.progression import (
    ExplorationInput,
    FrontierSeedBinding,
    PrerequisiteCheckBinding,
    PrerequisiteDimensionGapKind,
    ProgressionFrontierId,
    ProgressionFrontierRequest,
    ProgressionMechanismKind,
    ProgressionRequesterRef,
    derive_progression_frontier_v1,
)
from capability_lab.semantics import RelationKind
from capability_lab.state import DimensionStanding, PersonalCapabilityStateId, PersonalCapabilityStateSet


T0 = datetime(2026, 8, 15, 15, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("subject_pr8_smoke")


def _provenance() -> ProvenanceTrail:
    return ProvenanceTrail((ProvenanceSource(ProvenanceSourceKind.ACTOR, "test:pr8_reviewer"),))


def _concept(catalog, key):
    return next(item for item in catalog.concepts if item.capability_id.key == key)


def _dimension(state, key):
    return next(item for item in state.dimensions if item.dimension_key == key)


def test_real_civilization_bootstrap_frontier_gap_and_exploration() -> None:
    catalog = build_civilization_bootstrap_seed_catalog_v0()
    frame = CIVILIZATION_BOOTSTRAP_TECHNICAL_COMPETENCE_FRAME_V1
    frame_catalog = build_civilization_bootstrap_frame_catalog_v1()
    basic = _concept(catalog, "basic_electricity")
    target = _concept(catalog, "low_voltage_power_distribution")
    exploration = _concept(catalog, "potable_water_treatment")

    requires = next(
        item for item in catalog.relations
        if item.kind is RelationKind.REQUIRES
        and item.source_id == target.capability_id
        and item.target_id == basic.capability_id
    )

    evidence_id = EvidenceId("evidence_pr8_basic_electricity")
    claim_id = CapabilityClaimId("claim_pr8_basic_electricity")
    evaluation_id = ClaimEvaluationId("eval_pr8_basic_electricity")
    evidence = EvidenceRecord(
        evidence_id,
        SUBJECT,
        EvidenceKind.PROJECT,
        "Analyzed a bounded low-voltage electricity setup with explicit assumptions.",
        EvidenceContext("Bounded low-voltage conceptual analysis with ordinary reference tools."),
        T0,
        T0 + timedelta(minutes=1),
        _provenance(),
    )
    claim = CapabilityClaim(
        claim_id,
        SUBJECT,
        basic.ref,
        "Can explain bounded basic-electricity relationships under explicit assumptions.",
        ClaimScope("Bounded conceptual analysis only."),
        T0 + timedelta(minutes=5),
        _provenance(),
    )
    evaluation = ClaimEvaluation(
        evaluation_id,
        claim_id,
        EvaluationPolicyRef.parse("civilization_bootstrap:bounded_progression_seed@1"),
        EvaluatorRef(EvaluatorKind.HUMAN, "test:pr8_reviewer"),
        T0 + timedelta(minutes=10),
        (
            EvidenceAssessment(
                evidence_id,
                EvidenceBearing.SUPPORTS,
                EvidenceReliability.HIGH,
                "The project bears directly on the bounded conceptual claim.",
                "The claim is supported only within its stated scope.",
            ),
        ),
        CoverageAssessment(CoverageStatus.SUFFICIENT_FOR_CLAIM, "Sufficient for this bounded claim."),
        ConflictStatus.NONE,
        EvaluationConclusion.SUPPORTED,
        "Supported under the named bounded policy.",
    )
    records = EpistemicRecordSet((evidence,), (claim,), (evaluation,))
    state = derive_supported_state_v1(
        records=records,
        frame=frame,
        request=DeterministicStateDerivationRequest(
            PersonalCapabilityStateId("state_pr8_basic_electricity"),
            SUBJECT,
            basic.ref,
            frame.ref,
            T0 + timedelta(minutes=15),
            T0 + timedelta(minutes=15),
            (evaluation_id,),
            (ClaimDimensionBinding(claim_id, ("conceptual_knowledge",)),),
        ),
    )
    assert _dimension(state, "conceptual_knowledge").standing is DimensionStanding.SUPPORTED
    assert _dimension(state, "calculation").standing is DimensionStanding.UNKNOWN

    frontier = derive_progression_frontier_v1(
        capability_catalog=catalog,
        frame_catalog=frame_catalog,
        records=records,
        state_set=PersonalCapabilityStateSet(SUBJECT, (state,)),
        request=ProgressionFrontierRequest(
            ProgressionFrontierId("frontier_pr8_smoke"),
            SUBJECT,
            T0 + timedelta(minutes=20),
            T0 + timedelta(minutes=20),
            ProgressionRequesterRef(ProgressionMechanismKind.HUMAN, "test:pr8_subject"),
            seed_bindings=(FrontierSeedBinding(state.state_id, ("conceptual_knowledge",)),),
            prerequisite_bindings=(
                PrerequisiteCheckBinding(
                    target.ref,
                    basic.ref,
                    requires.scope,
                    frame.ref,
                    ("conceptual_knowledge", "calculation"),
                    state.state_id,
                ),
            ),
            exploration_inputs=(
                ExplorationInput(
                    exploration.ref,
                    "Keep a life-systems direction visible outside the electrical frontier.",
                ),
            ),
        ),
    )

    candidate = next(item for item in frontier.candidates if item.concept_ref == target.ref)
    assert candidate.explicit_focus is False
    assert any(w.relation.kind is RelationKind.REQUIRES for w in candidate.adjacency_witnesses)
    assert candidate.assessed_prerequisites
    assert not candidate.unassessed_prerequisites

    gap = next(item for item in frontier.prerequisite_gaps if item.target_ref == target.ref)
    assert [item.dimension_key for item in gap.dimension_gaps] == ["calculation"]
    assert gap.dimension_gaps[0].kind is PrerequisiteDimensionGapKind.UNKNOWN

    assert target.ref in {item.concept_ref for item in frontier.candidates}
    assert frontier.exploration_opportunities[0].concept_ref == exploration.ref
