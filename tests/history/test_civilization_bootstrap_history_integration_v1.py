from datetime import datetime, timedelta, timezone

from capability_lab.derivation import (
    ClaimDimensionBinding,
    DeterministicStateDerivationRequest,
    derive_supported_state_v1,
)
from capability_lab.domains import (
    CIVILIZATION_BOOTSTRAP_TECHNICAL_COMPETENCE_FRAME_V1,
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
from capability_lab.history import (
    AchievementBasisKind,
    AchievementBasisRef,
    AchievementCriterion,
    AchievementFamily,
    AchievementFamilyCatalog,
    AchievementFamilyId,
    AchievementInstance,
    AchievementInstanceId,
    AchievementQualificationPolicyRef,
    AchievementQualifierRef,
    HistoryMechanismKind,
    LegendGeneratorRef,
    LegendProjectionPolicyRef,
    LegendSourceKind,
    LegendSourceRef,
    MilestoneRecorderRef,
    MilestoneRecordingPolicyRef,
    MilestoneSourceKind,
    MilestoneSourceRef,
    PersonalHistoryRecordSet,
    PersonalLegend,
    PersonalLegendEntry,
    PersonalLegendId,
    PersonalLegendSet,
    PersonalMilestoneEvent,
    PersonalMilestoneEventId,
)
from capability_lab.state import DimensionStanding, PersonalCapabilityStateId


T0 = datetime(2026, 8, 15, 10, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("subject_pr7_smoke")
EVIDENCE_ID = EvidenceId("evidence_pr7_basic_circuits")
CLAIM_ID = CapabilityClaimId("claim_pr7_basic_circuits")
EVALUATION_ID = ClaimEvaluationId("eval_pr7_basic_circuits")


def _provenance() -> ProvenanceTrail:
    return ProvenanceTrail(
        (ProvenanceSource(ProvenanceSourceKind.ACTOR, "test:pr7_smoke_reviewer"),)
    )


def _dimension(state, key: str):
    return next(item for item in state.dimensions if item.dimension_key == key)


def test_real_pr2_pr4_history_and_legend_remain_separate_layers() -> None:
    capability_catalog = build_civilization_bootstrap_seed_catalog_v0()
    frame = CIVILIZATION_BOOTSTRAP_TECHNICAL_COMPETENCE_FRAME_V1
    concept = next(
        item for item in capability_catalog.concepts if item.capability_id.key == "basic_circuits"
    )

    evidence = EvidenceRecord(
        EVIDENCE_ID,
        SUBJECT,
        EvidenceKind.PROJECT,
        "Built, measured, and checked a bounded low-voltage DC resistor circuit.",
        EvidenceContext(
            "Bench project with explicit topology, nominal resistor values, low-voltage source, and multimeter."
        ),
        T0,
        T0 + timedelta(minutes=1),
        _provenance(),
    )
    claim = CapabilityClaim(
        CLAIM_ID,
        SUBJECT,
        concept.ref,
        "Can analyze and check a bounded low-voltage DC resistor circuit under stated component assumptions.",
        ClaimScope("Explicit bounded resistor network with ordinary calculation and measurement tools."),
        T0 + timedelta(minutes=10),
        _provenance(),
    )
    evaluation = ClaimEvaluation(
        EVALUATION_ID,
        CLAIM_ID,
        EvaluationPolicyRef.parse("civilization_bootstrap:bounded_project_evaluation@1"),
        EvaluatorRef(EvaluatorKind.HUMAN, "test:pr7_smoke_reviewer"),
        T0 + timedelta(minutes=20),
        (
            EvidenceAssessment(
                EVIDENCE_ID,
                EvidenceBearing.SUPPORTS,
                EvidenceReliability.HIGH,
                "The project directly covers the bounded analysis/checking proposition.",
                "Predicted and measured relationships were consistent under the project assumptions.",
            ),
        ),
        CoverageAssessment(
            CoverageStatus.SUFFICIENT_FOR_CLAIM,
            "Sufficient only for the bounded claim scope.",
        ),
        ConflictStatus.NONE,
        EvaluationConclusion.SUPPORTED,
        "The bounded project supports this exact claim under the named evaluation policy.",
    )
    records = EpistemicRecordSet((evidence,), (claim,), (evaluation,))

    supported_state = derive_supported_state_v1(
        records=records,
        frame=frame,
        request=DeterministicStateDerivationRequest(
            PersonalCapabilityStateId("state_pr7_supported"),
            SUBJECT,
            concept.ref,
            frame.ref,
            T0 + timedelta(minutes=25),
            T0 + timedelta(minutes=25),
            (EVALUATION_ID,),
            (ClaimDimensionBinding(CLAIM_ID, ("conceptual_knowledge", "calculation")),),
        ),
    )
    assert _dimension(supported_state, "conceptual_knowledge").standing is DimensionStanding.SUPPORTED

    family = AchievementFamily(
        AchievementFamilyId("civilization_bootstrap", "bounded_dc_circuit_project"),
        "Bounded DC Circuit Project",
        "Completed and checked a functioning bounded low-voltage DC circuit project with inspectable implementation evidence.",
        qualification_criteria=(
            AchievementCriterion("functioning_circuit", "A functioning bounded physical circuit was completed."),
            AchievementCriterion("observable_check", "The result was checked through an observable measurement path."),
        ),
    )
    family_catalog = AchievementFamilyCatalog((family,))
    achievement = AchievementInstance(
        AchievementInstanceId("achievement_pr7_basic_circuits"),
        SUBJECT,
        family.ref,
        T0,
        T0 + timedelta(minutes=30),
        AchievementQualificationPolicyRef.parse(
            "civilization_bootstrap:bounded_project_achievement@1"
        ),
        AchievementQualifierRef(HistoryMechanismKind.HUMAN, "test:pr7_smoke_reviewer"),
        (
            AchievementBasisRef(AchievementBasisKind.EVIDENCE_RECORD, str(EVIDENCE_ID)),
            AchievementBasisRef(AchievementBasisKind.CLAIM_EVALUATION, str(EVALUATION_ID)),
        ),
        "The same bounded project event is preserved as a historical accomplishment, separately from current state.",
    )
    milestone = PersonalMilestoneEvent(
        PersonalMilestoneEventId("milestone_pr7_first_complete_circuit"),
        SUBJECT,
        "First complete bounded circuit project",
        "The completed circuit became a personally meaningful development event.",
        "It marked the first preserved end-to-end circuit accomplishment in this history.",
        T0 + timedelta(minutes=40),
        T0 + timedelta(minutes=45),
        MilestoneRecorderRef(HistoryMechanismKind.HUMAN, "test:pr7_subject_recorder"),
        MilestoneRecordingPolicyRef.parse("core:personal_milestone_recording@1"),
        (
            MilestoneSourceRef(
                MilestoneSourceKind.ACHIEVEMENT_INSTANCE,
                str(achievement.achievement_id),
            ),
        ),
    )
    history = PersonalHistoryRecordSet(SUBJECT, (achievement,), (milestone,))
    history.validate_against_family_catalog(family_catalog)
    history.validate_against_epistemics(records)
    history_before = history.to_json()

    legend = PersonalLegend(
        PersonalLegendId("legend_pr7_circuit_journey"),
        SUBJECT,
        T0 + timedelta(hours=1),
        T0 + timedelta(hours=2),
        LegendProjectionPolicyRef.parse("core:personal_legend_projection@1"),
        LegendGeneratorRef(HistoryMechanismKind.MODEL, "test:pr7_legend_model"),
        "First complete circuit",
        "A derived narrative over exact historical records; it is not the historical event store or capability state.",
        (
            PersonalLegendEntry(
                (
                    LegendSourceRef(
                        LegendSourceKind.ACHIEVEMENT_INSTANCE,
                        str(achievement.achievement_id),
                    ),
                    LegendSourceRef(
                        LegendSourceKind.PERSONAL_MILESTONE_EVENT,
                        str(milestone.milestone_id),
                    ),
                ),
                "From project to preserved history",
                "The project is represented both as an earned bounded accomplishment and as a separate personally meaningful milestone.",
            ),
        ),
    )
    PersonalLegendSet(SUBJECT, (legend,)).validate_against_history(history)

    later_unknown_state = derive_supported_state_v1(
        records=records,
        frame=frame,
        request=DeterministicStateDerivationRequest(
            PersonalCapabilityStateId("state_pr7_later_unknown"),
            SUBJECT,
            concept.ref,
            frame.ref,
            T0 + timedelta(days=365),
            T0 + timedelta(days=365),
            (),
            (),
        ),
    )
    assert all(item.standing is DimensionStanding.UNKNOWN for item in later_unknown_state.dimensions)

    assert history.to_json() == history_before
    assert history.achievement_instances == (achievement,)
    assert history.milestone_events == (milestone,)
    PersonalLegendSet(SUBJECT, (legend,)).validate_against_history(history)
