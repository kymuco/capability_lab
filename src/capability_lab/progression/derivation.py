"""Deterministic PR8 progression-frontier baseline v1."""

from __future__ import annotations

from capability_lab.epistemics import EpistemicRecordSet
from capability_lab.semantics import CapabilityCatalog, RelationKind
from capability_lab.state import CompetenceFrameCatalog, DimensionStanding, PersonalCapabilityStateSet

from .core import (
    ExplorationOpportunity,
    FrontierAdjacencyWitness,
    FrontierCandidate,
    InvalidProgressionRequest,
    PrerequisiteDimensionGap,
    PrerequisiteDimensionGapKind,
    PrerequisiteEvidenceGap,
    ProgressionDeriverRef,
    ProgressionFrontier,
    ProgressionFrontierRequest,
    ProgressionMechanismKind,
    ProgressionPolicyRef,
    ProgressionRelationWitness,
)


DETERMINISTIC_PROGRESSION_FRONTIER_POLICY_V1 = ProgressionPolicyRef.parse(
    "core:deterministic_progression_frontier@1"
)
DETERMINISTIC_PROGRESSION_FRONTIER_DERIVER_V1 = ProgressionDeriverRef(
    ProgressionMechanismKind.RULE,
    "capability_lab:deterministic_progression_frontier_v1",
)

_ALLOWED_ADJACENCY_KINDS = {
    RelationKind.SPECIALIZES,
    RelationKind.REQUIRES,
    RelationKind.SUPPORTED_BY,
    RelationKind.ENABLED_BY,
}


def derive_progression_frontier_v1(
    *,
    capability_catalog: CapabilityCatalog,
    frame_catalog: CompetenceFrameCatalog,
    records: EpistemicRecordSet,
    state_set: PersonalCapabilityStateSet,
    request: ProgressionFrontierRequest,
) -> ProgressionFrontier:
    """Derive a one-hop advisory frontier with no ranking, scoring, or hidden path search."""

    if not isinstance(capability_catalog, CapabilityCatalog):
        raise InvalidProgressionRequest("capability_catalog must be CapabilityCatalog")
    if not isinstance(frame_catalog, CompetenceFrameCatalog):
        raise InvalidProgressionRequest("frame_catalog must be CompetenceFrameCatalog")
    if not isinstance(records, EpistemicRecordSet):
        raise InvalidProgressionRequest("records must be EpistemicRecordSet")
    if not isinstance(state_set, PersonalCapabilityStateSet):
        raise InvalidProgressionRequest("state_set must be PersonalCapabilityStateSet")
    if not isinstance(request, ProgressionFrontierRequest):
        raise InvalidProgressionRequest("request must be ProgressionFrontierRequest")
    if state_set.subject_ref != request.subject_ref:
        raise InvalidProgressionRequest(
            "state_set and progression request must belong to the same subject"
        )

    concepts_by_id = {item.capability_id: item for item in capability_catalog.concepts}
    frames_by_id = {item.frame_id: item for item in frame_catalog.frames}
    states_by_id = {item.state_id: item for item in state_set.states}

    def exact_concept(ref, label: str):
        concept = concepts_by_id.get(ref.capability_id)
        if concept is None:
            raise InvalidProgressionRequest(f"{label} references capability absent from catalog: {ref}")
        if concept.revision != ref.revision:
            raise InvalidProgressionRequest(
                f"{label} requires exact capability revision {ref}; current catalog has {concept.ref}"
            )
        return concept

    for focus in request.focuses:
        exact_concept(focus.concept_ref, "focus")
    for exploration in request.exploration_inputs:
        exact_concept(exploration.concept_ref, "exploration input")
    for binding in request.prerequisite_bindings:
        exact_concept(binding.target_ref, "prerequisite binding target")
        exact_concept(binding.prerequisite_ref, "prerequisite binding prerequisite")
        frame = frames_by_id.get(binding.frame_ref.frame_id)
        if frame is None:
            raise InvalidProgressionRequest(
                f"prerequisite binding references frame absent from catalog: {binding.frame_ref}"
            )
        if frame.revision != binding.frame_ref.revision:
            raise InvalidProgressionRequest(
                f"prerequisite binding requires exact frame {binding.frame_ref}; current catalog has {frame.ref}"
            )
        frame_keys = {item.key for item in frame.dimensions}
        unknown = set(binding.required_dimension_keys) - frame_keys
        if unknown:
            raise InvalidProgressionRequest(
                "prerequisite binding references dimensions absent from exact frame: "
                f"{sorted(unknown)!r}"
            )

    referenced_state_ids = {item.state_id for item in request.seed_bindings}
    referenced_state_ids.update(
        item.state_id for item in request.prerequisite_bindings if item.state_id is not None
    )
    selected_states = []
    for state_id in sorted(referenced_state_ids):
        state = states_by_id.get(state_id)
        if state is None:
            raise InvalidProgressionRequest(f"selected progression state does not exist: {state_id}")
        if state.subject_ref != request.subject_ref:
            raise InvalidProgressionRequest("selected progression state belongs to another subject")
        if state.as_of > request.as_of:
            raise InvalidProgressionRequest(
                "selected progression state may not represent a time after frontier as_of"
            )
        if state.derived_at > request.generated_at:
            raise InvalidProgressionRequest(
                "selected progression state may not be produced after frontier generated_at"
            )
        selected_states.append(state)

    selected_state_set = PersonalCapabilityStateSet(
        subject_ref=request.subject_ref,
        states=tuple(selected_states),
    )
    selected_state_set.validate_against_epistemics(records)
    selected_state_set.validate_against_capability_catalog(capability_catalog)
    selected_state_set.validate_against_frame_catalog(frame_catalog)

    seed_state_by_id = {}
    seed_concept_refs = set()
    for binding in request.seed_bindings:
        state = states_by_id[binding.state_id]
        dimensions = {item.dimension_key: item for item in state.dimensions}
        unknown_keys = set(binding.dimension_keys) - set(dimensions)
        if unknown_keys:
            raise InvalidProgressionRequest(
                "seed binding references dimensions absent from selected state: "
                f"{sorted(unknown_keys)!r}"
            )
        non_supported = [
            key
            for key in binding.dimension_keys
            if dimensions[key].standing is not DimensionStanding.SUPPORTED
        ]
        if non_supported:
            raise InvalidProgressionRequest(
                "frontier seed bindings may select only SUPPORTED dimensions: "
                f"{sorted(non_supported)!r}"
            )
        if state.concept_ref in seed_concept_refs:
            raise InvalidProgressionRequest(
                "one exact capability concept may have at most one frontier seed state per request"
            )
        seed_state_by_id[binding.state_id] = state
        seed_concept_refs.add(state.concept_ref)

    focus_refs = {item.concept_ref for item in request.focuses}
    focus_seed_overlap = focus_refs & seed_concept_refs
    if focus_seed_overlap:
        raise InvalidProgressionRequest(
            "explicit focus must remain distinct from selected seed concepts: "
            f"{sorted(str(item) for item in focus_seed_overlap)!r}"
        )

    candidate_data = {}

    def candidate_bucket(ref):
        return candidate_data.setdefault(ref, {"explicit_focus": False, "adjacency": []})

    for focus in request.focuses:
        candidate_bucket(focus.concept_ref)["explicit_focus"] = True

    for binding in request.seed_bindings:
        state = seed_state_by_id[binding.state_id]
        for relation in capability_catalog.relations:
            if relation.kind not in _ALLOWED_ADJACENCY_KINDS:
                continue
            if relation.target_id != state.concept_ref.capability_id:
                continue
            source = concepts_by_id[relation.source_id]
            target = concepts_by_id[relation.target_id]
            witness = ProgressionRelationWitness(
                source_ref=source.ref,
                target_ref=target.ref,
                kind=relation.kind,
                scope=relation.scope,
                strength=relation.strength,
            )
            candidate_bucket(source.ref)["adjacency"].append(
                FrontierAdjacencyWitness(
                    state_id=state.state_id,
                    seed_concept_ref=state.concept_ref,
                    seed_dimension_keys=binding.dimension_keys,
                    relation=witness,
                )
            )

    binding_by_relation_key = {}
    for binding in request.prerequisite_bindings:
        key = (
            str(binding.target_ref),
            str(binding.prerequisite_ref),
            binding.relation_scope.key if binding.relation_scope else "",
            binding.relation_scope.description if binding.relation_scope else "",
        )
        if key in binding_by_relation_key:
            raise InvalidProgressionRequest(
                "each exact REQUIRES relation may have at most one prerequisite binding per request"
            )
        binding_by_relation_key[key] = binding

    prerequisite_gaps = []
    candidates = []
    used_binding_keys = set()

    for concept_ref in sorted(candidate_data):
        data = candidate_data[concept_ref]
        assessed = []
        unassessed = []
        for relation in capability_catalog.relations:
            if relation.kind is not RelationKind.REQUIRES:
                continue
            if relation.source_id != concept_ref.capability_id:
                continue
            source = concepts_by_id[relation.source_id]
            prerequisite = concepts_by_id[relation.target_id]
            witness = ProgressionRelationWitness(
                source_ref=source.ref,
                target_ref=prerequisite.ref,
                kind=relation.kind,
                scope=relation.scope,
                strength=relation.strength,
            )
            relation_key = (
                str(source.ref),
                str(prerequisite.ref),
                relation.scope.key if relation.scope else "",
                relation.scope.description if relation.scope else "",
            )
            check = binding_by_relation_key.get(relation_key)
            if check is None:
                unassessed.append(witness)
                continue
            used_binding_keys.add(relation_key)
            assessed.append(witness)
            gaps = []
            if check.state_id is None:
                gaps = [
                    PrerequisiteDimensionGap(
                        dimension_key=key,
                        kind=PrerequisiteDimensionGapKind.NO_SELECTED_STATE,
                    )
                    for key in check.required_dimension_keys
                ]
            else:
                state = states_by_id[check.state_id]
                if state.concept_ref != check.prerequisite_ref:
                    raise InvalidProgressionRequest(
                        "prerequisite state must match exact prerequisite concept revision"
                    )
                if state.frame_ref != check.frame_ref:
                    raise InvalidProgressionRequest(
                        "prerequisite state must use the exact frame named by the binding"
                    )
                dimensions = {item.dimension_key: item for item in state.dimensions}
                for key in check.required_dimension_keys:
                    dimension = dimensions[key]
                    if dimension.standing is DimensionStanding.UNKNOWN:
                        gaps.append(
                            PrerequisiteDimensionGap(
                                dimension_key=key,
                                kind=PrerequisiteDimensionGapKind.UNKNOWN,
                                conflict_status=dimension.conflict_status,
                            )
                        )
                    elif dimension.standing is DimensionStanding.INSUFFICIENT:
                        gaps.append(
                            PrerequisiteDimensionGap(
                                dimension_key=key,
                                kind=PrerequisiteDimensionGapKind.INSUFFICIENT,
                                conflict_status=dimension.conflict_status,
                            )
                        )
            if gaps:
                prerequisite_gaps.append(
                    PrerequisiteEvidenceGap(
                        target_ref=check.target_ref,
                        prerequisite_ref=check.prerequisite_ref,
                        relation=witness,
                        frame_ref=check.frame_ref,
                        state_id=check.state_id,
                        dimension_gaps=tuple(gaps),
                    )
                )

        candidates.append(
            FrontierCandidate(
                concept_ref=concept_ref,
                explicit_focus=data["explicit_focus"],
                adjacency_witnesses=tuple(data["adjacency"]),
                assessed_prerequisites=tuple(assessed),
                unassessed_prerequisites=tuple(unassessed),
            )
        )

    unused = set(binding_by_relation_key) - used_binding_keys
    if unused:
        raise InvalidProgressionRequest(
            "prerequisite bindings must refer to REQUIRES relations of actual frontier candidates: "
            f"{sorted(unused)!r}"
        )

    candidate_refs = {item.concept_ref for item in candidates}
    blocked_exploration_refs = seed_concept_refs | candidate_refs | focus_refs
    exploration_opportunities = []
    for exploration in request.exploration_inputs:
        if exploration.concept_ref in blocked_exploration_refs:
            raise InvalidProgressionRequest(
                "exploration input must remain distinct from selected seed/focus/frontier concepts"
            )
        exploration_opportunities.append(
            ExplorationOpportunity(
                concept_ref=exploration.concept_ref,
                rationale=exploration.rationale,
            )
        )

    return ProgressionFrontier(
        frontier_id=request.frontier_id,
        subject_ref=request.subject_ref,
        as_of=request.as_of,
        generated_at=request.generated_at,
        policy_ref=DETERMINISTIC_PROGRESSION_FRONTIER_POLICY_V1,
        deriver_ref=DETERMINISTIC_PROGRESSION_FRONTIER_DERIVER_V1,
        requester_ref=request.requester_ref,
        focuses=request.focuses,
        seed_bindings=request.seed_bindings,
        prerequisite_bindings=request.prerequisite_bindings,
        exploration_inputs=request.exploration_inputs,
        candidates=tuple(candidates),
        prerequisite_gaps=tuple(prerequisite_gaps),
        exploration_opportunities=tuple(exploration_opportunities),
        rationale=(
            "Deterministic one-hop advisory frontier from explicitly selected supported "
            "state dimensions, direct shared relations, explicit focus, and explicit exploration."
        ),
    )
