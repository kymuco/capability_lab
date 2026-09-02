"""Deterministic PR9 Player Window derivation."""

from __future__ import annotations

from capability_lab.epistemics import EpistemicRecordSet
from capability_lab.history import AchievementFamilyCatalog, PersonalHistoryRecordSet, PersonalLegendSet
from capability_lab.progression import ProgressionFrontierSet
from capability_lab.semantics import CapabilityCatalog
from capability_lab.state import CompetenceFrameCatalog, PersonalCapabilityStateSet

from .core import (
    InvalidPlayerWindowRequest,
    PlayerWindow,
    PlayerWindowAchievementEntry,
    PlayerWindowCapabilityEntry,
    PlayerWindowClaimEntry,
    PlayerWindowDimensionEntry,
    PlayerWindowEvaluationEntry,
    PlayerWindowExplorationEntry,
    PlayerWindowFrontierCandidateEntry,
    PlayerWindowFrontierPanel,
    PlayerWindowGapDimensionEntry,
    PlayerWindowGeneratorRef,
    PlayerWindowLegendEntry,
    PlayerWindowLegendPanel,
    PlayerWindowMechanismKind,
    PlayerWindowMilestoneEntry,
    PlayerWindowPolicyRef,
    PlayerWindowPrerequisiteGapEntry,
    PlayerWindowRequest,
)


DETERMINISTIC_PLAYER_WINDOW_POLICY_V1 = PlayerWindowPolicyRef(
    "core", "deterministic_player_window", 1
)
DETERMINISTIC_PLAYER_WINDOW_GENERATOR_V1 = PlayerWindowGeneratorRef(
    PlayerWindowMechanismKind.RULE,
    "capability_lab:deterministic_player_window_v1",
)


def _exact_concept(catalog: CapabilityCatalog, ref):
    for concept in catalog.concepts:
        if concept.capability_id == ref.capability_id:
            if concept.revision != ref.revision:
                raise InvalidPlayerWindowRequest(
                    f"selected source references unavailable concept revision: {ref}"
                )
            return concept
    raise InvalidPlayerWindowRequest(f"selected source references missing concept: {ref}")


def _exact_frame(catalog: CompetenceFrameCatalog, ref):
    for frame in catalog.frames:
        if frame.frame_id == ref.frame_id:
            if frame.revision != ref.revision:
                raise InvalidPlayerWindowRequest(
                    f"selected state references unavailable frame revision: {ref}"
                )
            return frame
    raise InvalidPlayerWindowRequest(f"selected state references missing frame: {ref}")


def _exact_family(catalog: AchievementFamilyCatalog, ref):
    for family in catalog.families:
        if family.family_id == ref.family_id:
            if family.revision != ref.revision:
                raise InvalidPlayerWindowRequest(
                    f"selected achievement references unavailable family revision: {ref}"
                )
            return family
    raise InvalidPlayerWindowRequest(
        f"selected achievement references missing family: {ref}"
    )


def _relation_text(relation) -> str:
    scope = ""
    if relation.scope is not None:
        scope = f"; scope={relation.scope.key}: {relation.scope.description}"
    strength = ""
    if getattr(relation.strength, "value", "unspecified") != "unspecified":
        strength = f"; strength={relation.strength.value}"
    return f"{relation.kind.value} {relation.target_ref}{scope}{strength}"


def derive_player_window_v1(
    *,
    capability_catalog: CapabilityCatalog,
    competence_frame_catalog: CompetenceFrameCatalog,
    epistemic_records: EpistemicRecordSet,
    state_set: PersonalCapabilityStateSet,
    achievement_family_catalog: AchievementFamilyCatalog,
    history_set: PersonalHistoryRecordSet,
    legend_set: PersonalLegendSet,
    frontier_set: ProgressionFrontierSet,
    request: PlayerWindowRequest,
) -> PlayerWindow:
    """Compose explicitly selected governed records into one deterministic read model."""

    if not isinstance(request, PlayerWindowRequest):
        raise InvalidPlayerWindowRequest("request must be PlayerWindowRequest")
    if not isinstance(capability_catalog, CapabilityCatalog):
        raise InvalidPlayerWindowRequest("capability_catalog must be CapabilityCatalog")
    if not isinstance(competence_frame_catalog, CompetenceFrameCatalog):
        raise InvalidPlayerWindowRequest("competence_frame_catalog must be CompetenceFrameCatalog")
    if not isinstance(epistemic_records, EpistemicRecordSet):
        raise InvalidPlayerWindowRequest("epistemic_records must be EpistemicRecordSet")
    if not isinstance(state_set, PersonalCapabilityStateSet):
        raise InvalidPlayerWindowRequest("state_set must be PersonalCapabilityStateSet")
    if not isinstance(achievement_family_catalog, AchievementFamilyCatalog):
        raise InvalidPlayerWindowRequest("achievement_family_catalog must be AchievementFamilyCatalog")
    if not isinstance(history_set, PersonalHistoryRecordSet):
        raise InvalidPlayerWindowRequest("history_set must be PersonalHistoryRecordSet")
    if not isinstance(legend_set, PersonalLegendSet):
        raise InvalidPlayerWindowRequest("legend_set must be PersonalLegendSet")
    if not isinstance(frontier_set, ProgressionFrontierSet):
        raise InvalidPlayerWindowRequest("frontier_set must be ProgressionFrontierSet")

    for label, subject in (
        ("state_set", state_set.subject_ref),
        ("history_set", history_set.subject_ref),
        ("legend_set", legend_set.subject_ref),
        ("frontier_set", frontier_set.subject_ref),
    ):
        if subject != request.subject_ref:
            raise InvalidPlayerWindowRequest(f"{label} belongs to a different subject")

    states = {item.state_id: item for item in state_set.states}
    claims = {item.claim_id: item for item in epistemic_records.claims}
    evaluations = {item.evaluation_id: item for item in epistemic_records.evaluations}
    achievements = {item.achievement_id: item for item in history_set.achievement_instances}
    milestones = {item.milestone_id: item for item in history_set.milestone_events}
    legends = {item.legend_id: item for item in legend_set.legends}
    frontiers = {item.frontier_id: item for item in frontier_set.frontiers}

    capability_entries = []
    for state_id in request.selected_state_ids:
        state = states.get(state_id)
        if state is None:
            raise InvalidPlayerWindowRequest(f"selected state does not exist: {state_id}")
        if state.subject_ref != request.subject_ref:
            raise InvalidPlayerWindowRequest("selected state belongs to a different subject")
        if state.as_of > request.as_of:
            raise InvalidPlayerWindowRequest("selected state as_of exceeds player window as_of")
        if state.derived_at > request.generated_at:
            raise InvalidPlayerWindowRequest("selected state was derived after player window generation")
        concept = _exact_concept(capability_catalog, state.concept_ref)
        frame = _exact_frame(competence_frame_catalog, state.frame_ref)
        definitions = {item.key: item for item in frame.dimensions}
        state_dimensions = {item.dimension_key: item for item in state.dimensions}
        if set(definitions) != set(state_dimensions):
            raise InvalidPlayerWindowRequest(
                "selected state must expose every dimension of its exact frame in Player Window"
            )
        dimension_entries = []
        for key in sorted(definitions):
            definition = definitions[key]
            dimension = state_dimensions[key]
            claim_entries = []
            for claim_id in dimension.supported_claim_ids:
                claim = claims.get(claim_id)
                if claim is None:
                    raise InvalidPlayerWindowRequest(
                        f"selected state references missing supported claim: {claim_id}"
                    )
                if claim.subject_ref != request.subject_ref or claim.concept_ref != state.concept_ref:
                    raise InvalidPlayerWindowRequest("selected state's supported claim crosses subject/concept boundary")
                claim_entries.append(
                    PlayerWindowClaimEntry(
                        claim_id=claim.claim_id,
                        statement=claim.statement,
                        scope_description=claim.scope.description,
                        scope_tags=claim.scope.tags,
                    )
                )
            evaluation_entries = []
            for evaluation_id in dimension.basis_evaluation_ids:
                evaluation = evaluations.get(evaluation_id)
                if evaluation is None:
                    raise InvalidPlayerWindowRequest(
                        f"selected state references missing basis evaluation: {evaluation_id}"
                    )
                claim = claims.get(evaluation.claim_id)
                if claim is None or claim.subject_ref != request.subject_ref or claim.concept_ref != state.concept_ref:
                    raise InvalidPlayerWindowRequest("selected state's evaluation basis crosses subject/concept boundary")
                if evaluation.evaluated_at > state.as_of:
                    raise InvalidPlayerWindowRequest("selected state contains evaluation after its as_of boundary")
                evaluation_entries.append(
                    PlayerWindowEvaluationEntry(
                        evaluation_id=evaluation.evaluation_id,
                        conclusion=evaluation.conclusion,
                        conflict_status=evaluation.conflict_status,
                        policy_ref=str(evaluation.policy_ref),
                        evaluator_kind=evaluation.evaluator_ref.kind.value,
                        evaluator_ref=evaluation.evaluator_ref.ref,
                    )
                )
            dimension_entries.append(
                PlayerWindowDimensionEntry(
                    dimension_key=key,
                    name=definition.name,
                    description=definition.description,
                    standing=dimension.standing,
                    conflict_status=dimension.conflict_status,
                    rationale=dimension.rationale,
                    claims=tuple(claim_entries),
                    evaluations=tuple(evaluation_entries),
                )
            )
        capability_entries.append(
            PlayerWindowCapabilityEntry(
                state_id=state.state_id,
                concept_ref=state.concept_ref,
                concept_name=concept.name,
                concept_definition=concept.definition,
                frame_ref=state.frame_ref,
                frame_name=frame.name,
                state_policy_ref=str(state.derivation_policy_ref),
                state_deriver_kind=state.deriver_ref.kind.value,
                state_deriver_ref=state.deriver_ref.ref,
                as_of=state.as_of,
                derived_at=state.derived_at,
                dimensions=tuple(dimension_entries),
            )
        )

    achievement_entries = []
    for achievement_id in request.selected_achievement_ids:
        item = achievements.get(achievement_id)
        if item is None:
            raise InvalidPlayerWindowRequest(f"selected achievement does not exist: {achievement_id}")
        if item.subject_ref != request.subject_ref:
            raise InvalidPlayerWindowRequest("selected achievement belongs to a different subject")
        if item.achieved_at > request.as_of or item.recorded_at > request.generated_at:
            raise InvalidPlayerWindowRequest("selected achievement violates player window time boundary")
        family = _exact_family(achievement_family_catalog, item.family_ref)
        achievement_entries.append(
            PlayerWindowAchievementEntry(
                achievement_id=item.achievement_id,
                family_ref=str(item.family_ref),
                family_name=family.name,
                achieved_at=item.achieved_at,
                recorded_at=item.recorded_at,
                context=item.context,
                variant=item.variant,
                record_note=item.record_note,
                qualification_policy_ref=str(item.qualification_policy_ref),
                qualifier_kind=item.qualifier_ref.kind.value,
                qualifier_ref=item.qualifier_ref.ref,
            )
        )

    milestone_entries = []
    for milestone_id in request.selected_milestone_ids:
        item = milestones.get(milestone_id)
        if item is None:
            raise InvalidPlayerWindowRequest(f"selected milestone does not exist: {milestone_id}")
        if item.subject_ref != request.subject_ref:
            raise InvalidPlayerWindowRequest("selected milestone belongs to a different subject")
        if item.occurred_at > request.as_of or item.recorded_at > request.generated_at:
            raise InvalidPlayerWindowRequest("selected milestone violates player window time boundary")
        milestone_entries.append(
            PlayerWindowMilestoneEntry(
                milestone_id=item.milestone_id,
                title=item.title,
                description=item.description,
                significance_note=item.significance_note,
                occurred_at=item.occurred_at,
                recorded_at=item.recorded_at,
                recorder_kind=item.recorder_ref.kind.value,
                recorder_ref=item.recorder_ref.ref,
                recording_policy_ref=str(item.recording_policy_ref),
            )
        )

    legend_panel = None
    if request.selected_legend_id is not None:
        legend = legends.get(request.selected_legend_id)
        if legend is None:
            raise InvalidPlayerWindowRequest(f"selected Legend does not exist: {request.selected_legend_id}")
        if legend.subject_ref != request.subject_ref:
            raise InvalidPlayerWindowRequest("selected Legend belongs to a different subject")
        if legend.as_of > request.as_of or legend.generated_at > request.generated_at:
            raise InvalidPlayerWindowRequest("selected Legend violates player window time boundary")
        visible_history_ids = {
            *(str(item) for item in request.selected_achievement_ids),
            *(str(item) for item in request.selected_milestone_ids),
        }
        legend_entries = []
        for entry in legend.entries:
            source_refs = tuple(source.ref for source in entry.source_refs)
            if any(ref not in visible_history_ids for ref in source_refs):
                raise InvalidPlayerWindowRequest(
                    "visible Legend must not hide any cited source history record"
                )
            legend_entries.append(
                PlayerWindowLegendEntry(
                    source_refs=source_refs,
                    heading=entry.heading,
                    narrative=entry.narrative,
                )
            )
        legend_panel = PlayerWindowLegendPanel(
            legend_id=legend.legend_id,
            title=legend.title,
            summary=legend.summary,
            as_of=legend.as_of,
            generated_at=legend.generated_at,
            policy_ref=str(legend.legend_policy_ref),
            generator_kind=legend.generator_ref.kind.value,
            generator_ref=legend.generator_ref.ref,
            entries=tuple(legend_entries),
        )

    frontier_panel = None
    if request.selected_frontier_id is not None:
        frontier = frontiers.get(request.selected_frontier_id)
        if frontier is None:
            raise InvalidPlayerWindowRequest(f"selected frontier does not exist: {request.selected_frontier_id}")
        if frontier.subject_ref != request.subject_ref:
            raise InvalidPlayerWindowRequest("selected frontier belongs to a different subject")
        if frontier.as_of != request.as_of:
            raise InvalidPlayerWindowRequest("selected frontier as_of must exactly equal player window as_of")
        if frontier.generated_at > request.generated_at:
            raise InvalidPlayerWindowRequest("selected frontier was generated after player window generation")
        visible_state_ids = set(request.selected_state_ids)
        hidden_basis = {binding.state_id for binding in frontier.seed_bindings if binding.state_id not in visible_state_ids}
        hidden_basis.update(
            binding.state_id
            for binding in frontier.prerequisite_bindings
            if binding.state_id is not None and binding.state_id not in visible_state_ids
        )
        hidden_basis.update(
            gap.state_id
            for gap in frontier.prerequisite_gaps
            if gap.state_id is not None and gap.state_id not in visible_state_ids
        )
        if hidden_basis:
            raise InvalidPlayerWindowRequest(
                "visible frontier must not hide selected personal-state basis"
            )
        candidate_entries = []
        for candidate in frontier.candidates:
            concept = _exact_concept(capability_catalog, candidate.concept_ref)
            reasons = []
            for witness in candidate.adjacency_witnesses:
                reasons.append(
                    f"{_relation_text(witness.relation)}; seed_state={witness.state_id}; seed_dimensions={','.join(witness.seed_dimension_keys)}"
                )
            candidate_entries.append(
                PlayerWindowFrontierCandidateEntry(
                    concept_ref=candidate.concept_ref,
                    concept_name=concept.name,
                    explicit_focus=candidate.explicit_focus,
                    adjacency_reasons=tuple(reasons),
                    assessed_prerequisites=tuple(_relation_text(item) for item in candidate.assessed_prerequisites),
                    unassessed_prerequisites=tuple(_relation_text(item) for item in candidate.unassessed_prerequisites),
                )
            )
        gap_entries = []
        for gap in frontier.prerequisite_gaps:
            target = _exact_concept(capability_catalog, gap.target_ref)
            prerequisite = _exact_concept(capability_catalog, gap.prerequisite_ref)
            gap_entries.append(
                PlayerWindowPrerequisiteGapEntry(
                    target_ref=gap.target_ref,
                    target_name=target.name,
                    prerequisite_ref=gap.prerequisite_ref,
                    prerequisite_name=prerequisite.name,
                    relation_description=_relation_text(gap.relation),
                    frame_ref=gap.frame_ref,
                    state_id=gap.state_id,
                    dimension_gaps=tuple(
                        PlayerWindowGapDimensionEntry(
                            dimension_key=item.dimension_key,
                            kind=item.kind,
                            conflict_status=item.conflict_status,
                        )
                        for item in gap.dimension_gaps
                    ),
                )
            )
        exploration_entries = []
        for opportunity in frontier.exploration_opportunities:
            concept = _exact_concept(capability_catalog, opportunity.concept_ref)
            exploration_entries.append(
                PlayerWindowExplorationEntry(
                    concept_ref=opportunity.concept_ref,
                    concept_name=concept.name,
                    rationale=opportunity.rationale,
                )
            )
        frontier_panel = PlayerWindowFrontierPanel(
            frontier_id=frontier.frontier_id,
            policy_ref=str(frontier.policy_ref),
            deriver_kind=frontier.deriver_ref.kind.value,
            deriver_ref=frontier.deriver_ref.ref,
            requester_kind=frontier.requester_ref.kind.value,
            requester_ref=frontier.requester_ref.ref,
            rationale=frontier.rationale,
            candidates=tuple(candidate_entries),
            prerequisite_gaps=tuple(gap_entries),
            exploration=tuple(exploration_entries),
        )

    return PlayerWindow(
        window_id=request.window_id,
        subject_ref=request.subject_ref,
        as_of=request.as_of,
        generated_at=request.generated_at,
        policy_ref=DETERMINISTIC_PLAYER_WINDOW_POLICY_V1,
        generator_ref=DETERMINISTIC_PLAYER_WINDOW_GENERATOR_V1,
        requester_ref=request.requester_ref,
        viewer_ref=request.viewer_ref,
        selected_state_ids=request.selected_state_ids,
        selected_achievement_ids=request.selected_achievement_ids,
        selected_milestone_ids=request.selected_milestone_ids,
        selected_legend_id=request.selected_legend_id,
        selected_frontier_id=request.selected_frontier_id,
        capabilities=tuple(capability_entries),
        achievements=tuple(achievement_entries),
        milestones=tuple(milestone_entries),
        legend=legend_panel,
        frontier=frontier_panel,
        rationale=(
            "Deterministic source-visible Player Window over explicitly selected PR3 state, "
            "PR7 history/Legend, and PR8 frontier records. Display selection is not truth, "
            "importance, completeness, recommendation, permission, or subject endorsement."
        ),
    )
