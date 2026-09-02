"""Dependency-free Civilization Bootstrap Player Window demo."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

from capability_lab.derivation import ClaimDimensionBinding, DeterministicStateDerivationRequest, derive_supported_state_v1
from capability_lab.domains import (
    CIVILIZATION_BOOTSTRAP_TECHNICAL_COMPETENCE_FRAME_V1,
    build_civilization_bootstrap_frame_catalog_v1,
    build_civilization_bootstrap_seed_catalog_v0,
)
from capability_lab.epistemics import (
    CapabilityClaim, CapabilityClaimId, CapabilitySubjectRef, ClaimEvaluation, ClaimEvaluationId,
    ClaimScope, ConflictStatus, CoverageAssessment, CoverageStatus, EpistemicRecordSet,
    EvaluationConclusion, EvaluationPolicyRef, EvaluatorKind, EvaluatorRef, EvidenceAssessment,
    EvidenceBearing, EvidenceContext, EvidenceId, EvidenceKind, EvidenceRecord, EvidenceReliability,
    ProvenanceSource, ProvenanceSourceKind, ProvenanceTrail,
)
from capability_lab.history import (
    AchievementBasisKind, AchievementBasisRef, AchievementCriterion, AchievementFamily,
    AchievementFamilyCatalog, AchievementFamilyId, AchievementInstance, AchievementInstanceId,
    AchievementQualificationPolicyRef, AchievementQualifierRef, HistoryMechanismKind,
    LegendGeneratorRef, LegendProjectionPolicyRef, LegendSourceKind, LegendSourceRef,
    MilestoneRecorderRef, MilestoneRecordingPolicyRef, MilestoneSourceKind, MilestoneSourceRef,
    PersonalHistoryRecordSet, PersonalLegend, PersonalLegendEntry, PersonalLegendId, PersonalLegendSet,
    PersonalMilestoneEvent, PersonalMilestoneEventId,
)
from capability_lab.progression import (
    ExplorationInput, FrontierSeedBinding, PrerequisiteCheckBinding, ProgressionFrontierId,
    ProgressionFrontierRequest, ProgressionFrontierSet, ProgressionMechanismKind,
    ProgressionRequesterRef, derive_progression_frontier_v1,
)
from capability_lab.semantics import RelationKind
from capability_lab.state import PersonalCapabilityStateId, PersonalCapabilityStateSet

from .core import (
    PlayerWindowId, PlayerWindowMechanismKind, PlayerWindowRequest,
    PlayerWindowRequesterRef, PlayerWindowViewerRef,
)
from .derivation import derive_player_window_v1
from .html import render_player_window_html_v1
from .verification import validate_player_window_v1


T0 = datetime(2026, 8, 16, 10, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("civilization_bootstrap_demo_subject")


def _provenance() -> ProvenanceTrail:
    return ProvenanceTrail((ProvenanceSource(ProvenanceSourceKind.ACTOR, "demo:local_subject"),))


def build_civilization_bootstrap_player_window_demo_v1():
    capability_catalog = build_civilization_bootstrap_seed_catalog_v0()
    frame_catalog = build_civilization_bootstrap_frame_catalog_v1()
    frame = CIVILIZATION_BOOTSTRAP_TECHNICAL_COMPETENCE_FRAME_V1
    basic = next(item for item in capability_catalog.concepts if item.capability_id.key == "basic_electricity")
    target = next(item for item in capability_catalog.concepts if item.capability_id.key == "low_voltage_power_distribution")
    exploration = next(item for item in capability_catalog.concepts if item.capability_id.key == "potable_water_treatment")
    requires = next(
        item for item in capability_catalog.relations
        if item.kind is RelationKind.REQUIRES
        and item.source_id == target.capability_id
        and item.target_id == basic.capability_id
    )

    evidence_id = EvidenceId("evidence_demo_basic_electricity")
    claim_id = CapabilityClaimId("claim_demo_basic_electricity")
    evaluation_id = ClaimEvaluationId("eval_demo_basic_electricity")
    evidence = EvidenceRecord(
        evidence_id, SUBJECT, EvidenceKind.PROJECT,
        "Analyzed and checked a bounded low-voltage DC setup with explicit assumptions.",
        EvidenceContext("Local bench-style conceptual exercise with ordinary reference tools."),
        T0, T0 + timedelta(minutes=1), _provenance(),
    )
    claim = CapabilityClaim(
        claim_id, SUBJECT, basic.ref,
        "Can explain bounded basic-electricity relationships under explicit assumptions.",
        ClaimScope("Bounded low-voltage conceptual analysis only."),
        T0 + timedelta(minutes=5), _provenance(),
    )
    evaluation = ClaimEvaluation(
        evaluation_id, claim_id,
        EvaluationPolicyRef.parse("civilization_bootstrap:bounded_player_window_demo@1"),
        EvaluatorRef(EvaluatorKind.HUMAN, "demo:local_reviewer"),
        T0 + timedelta(minutes=10),
        (EvidenceAssessment(
            evidence_id, EvidenceBearing.SUPPORTS, EvidenceReliability.HIGH,
            "The project bears directly on this bounded conceptual claim.",
            "Support is limited to the stated low-voltage conceptual scope.",
        ),),
        CoverageAssessment(CoverageStatus.SUFFICIENT_FOR_CLAIM, "Sufficient for the bounded claim only."),
        ConflictStatus.NONE, EvaluationConclusion.SUPPORTED,
        "Supported under the named bounded demo evaluation policy.",
    )
    records = EpistemicRecordSet((evidence,), (claim,), (evaluation,))
    state = derive_supported_state_v1(
        records=records,
        frame=frame,
        request=DeterministicStateDerivationRequest(
            PersonalCapabilityStateId("state_demo_basic_electricity"), SUBJECT, basic.ref, frame.ref,
            T0 + timedelta(minutes=15), T0 + timedelta(minutes=15), (evaluation_id,),
            (ClaimDimensionBinding(claim_id, ("conceptual_knowledge",)),),
        ),
    )
    state_set = PersonalCapabilityStateSet(SUBJECT, (state,))

    family = AchievementFamily(
        AchievementFamilyId("civilization_bootstrap", "bounded_basic_electricity_project"),
        "Bounded Basic Electricity Project",
        "Completed and checked one bounded low-voltage electricity project with inspectable event evidence.",
        qualification_criteria=(
            AchievementCriterion("bounded_event", "A bounded project event was completed."),
            AchievementCriterion("inspectable_check", "An observable checking path was preserved."),
        ),
    )
    family_catalog = AchievementFamilyCatalog((family,))
    achievement = AchievementInstance(
        AchievementInstanceId("achievement_demo_basic_electricity"), SUBJECT, family.ref,
        T0, T0 + timedelta(minutes=30),
        AchievementQualificationPolicyRef.parse("civilization_bootstrap:bounded_demo_achievement@1"),
        AchievementQualifierRef(HistoryMechanismKind.HUMAN, "demo:local_reviewer"),
        (
            AchievementBasisRef(AchievementBasisKind.EVIDENCE_RECORD, str(evidence_id)),
            AchievementBasisRef(AchievementBasisKind.CLAIM_EVALUATION, str(evaluation_id)),
        ),
        "The bounded project event is preserved as historical accomplishment, separately from current state.",
    )
    milestone = PersonalMilestoneEvent(
        PersonalMilestoneEventId("milestone_demo_first_electricity_project"), SUBJECT,
        "First preserved bounded electricity project",
        "The project became a separately preserved development-history event.",
        "Recorded as the first end-to-end bounded electricity project in this local demo history.",
        T0 + timedelta(minutes=40), T0 + timedelta(minutes=45),
        MilestoneRecorderRef(HistoryMechanismKind.HUMAN, "demo:local_subject"),
        MilestoneRecordingPolicyRef.parse("core:personal_milestone_recording@1"),
        (MilestoneSourceRef(MilestoneSourceKind.ACHIEVEMENT_INSTANCE, str(achievement.achievement_id)),),
    )
    history_set = PersonalHistoryRecordSet(SUBJECT, (achievement,), (milestone,))
    history_set.validate_against_family_catalog(family_catalog)
    history_set.validate_against_epistemics(records)

    legend = PersonalLegend(
        PersonalLegendId("legend_demo_first_electricity_project"), SUBJECT,
        T0 + timedelta(minutes=60), T0 + timedelta(minutes=70),
        LegendProjectionPolicyRef.parse("core:personal_legend_projection@1"),
        LegendGeneratorRef(HistoryMechanismKind.MODEL, "demo:local_narrative_model"),
        "A first bounded electricity project",
        "A selected narrative projection over visible source history; not identity, state, or the history store itself.",
        (PersonalLegendEntry(
            (
                LegendSourceRef(LegendSourceKind.ACHIEVEMENT_INSTANCE, str(achievement.achievement_id)),
                LegendSourceRef(LegendSourceKind.PERSONAL_MILESTONE_EVENT, str(milestone.milestone_id)),
            ),
            "From demonstration to preserved history",
            "The same bounded project is visible as a qualified accomplishment and a separately recorded personal milestone.",
        ),),
    )
    legend_set = PersonalLegendSet(SUBJECT, (legend,))
    legend_set.validate_against_history(history_set)

    frontier = derive_progression_frontier_v1(
        capability_catalog=capability_catalog, frame_catalog=frame_catalog, records=records, state_set=state_set,
        request=ProgressionFrontierRequest(
            ProgressionFrontierId("frontier_demo_player_window"), SUBJECT,
            T0 + timedelta(minutes=60), T0 + timedelta(minutes=60),
            ProgressionRequesterRef(ProgressionMechanismKind.HUMAN, "demo:local_subject"),
            seed_bindings=(FrontierSeedBinding(state.state_id, ("conceptual_knowledge",)),),
            prerequisite_bindings=(PrerequisiteCheckBinding(
                target.ref, basic.ref, requires.scope, frame.ref,
                ("conceptual_knowledge", "calculation"), state.state_id,
            ),),
            exploration_inputs=(ExplorationInput(
                exploration.ref,
                "Keep a life-systems direction explicitly visible outside the current electrical frontier.",
            ),),
        ),
    )
    frontier_set = ProgressionFrontierSet(SUBJECT, (frontier,))

    window = derive_player_window_v1(
        capability_catalog=capability_catalog,
        competence_frame_catalog=frame_catalog,
        epistemic_records=records,
        state_set=state_set,
        achievement_family_catalog=family_catalog,
        history_set=history_set,
        legend_set=legend_set,
        frontier_set=frontier_set,
        request=PlayerWindowRequest(
            PlayerWindowId("player_window_demo_v1"), SUBJECT,
            T0 + timedelta(minutes=60), T0 + timedelta(minutes=80),
            PlayerWindowRequesterRef(PlayerWindowMechanismKind.HUMAN, "demo:local_subject"),
            PlayerWindowViewerRef(PlayerWindowMechanismKind.HUMAN, "demo:local_subject"),
            selected_state_ids=(state.state_id,),
            selected_achievement_ids=(achievement.achievement_id,),
            selected_milestone_ids=(milestone.milestone_id,),
            selected_legend_id=legend.legend_id,
            selected_frontier_id=frontier.frontier_id,
        ),
    )
    validate_player_window_v1(
        capability_catalog=capability_catalog,
        competence_frame_catalog=frame_catalog,
        epistemic_records=records,
        state_set=state_set,
        achievement_family_catalog=family_catalog,
        history_set=history_set,
        legend_set=legend_set,
        frontier_set=frontier_set,
        window=window,
    )
    return window


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render the local Civilization Bootstrap Player Window demo.")
    parser.add_argument("--output", default="player_window.html", help="Output HTML path.")
    args = parser.parse_args(argv)
    window = build_civilization_bootstrap_player_window_demo_v1()
    output = Path(args.output)
    output.write_text(render_player_window_html_v1(window), encoding="utf-8")
    print(output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
