from dataclasses import replace
from datetime import datetime, timedelta, timezone
import inspect

import pytest

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
from capability_lab.progression import (
    ExplorationInput,
    FrontierSeedBinding,
    InvalidProgressionFrontier,
    InvalidProgressionRequest,
    PrerequisiteCheckBinding,
    ProgressionFocus,
    ProgressionFrontier,
    ProgressionFrontierId,
    ProgressionFrontierRequest,
    ProgressionMechanismKind,
    ProgressionPolicyRef,
    ProgressionRequesterRef,
    derive_progression_frontier_v1,
    validate_progression_frontier_v1,
)
from capability_lab.semantics import RelationKind
from capability_lab.state import DimensionStanding, PersonalCapabilityStateId, PersonalCapabilityStateSet


T0 = datetime(2026, 8, 15, 19, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("subject_pr8_authority")


def _concept(catalog, key):
    return next(item for item in catalog.concepts if item.capability_id.key == key)


def _provenance() -> ProvenanceTrail:
    return ProvenanceTrail(
        (ProvenanceSource(ProvenanceSourceKind.ACTOR, "test:pr8_authority_reviewer"),)
    )


def _supported_basic_state():
    catalog = build_civilization_bootstrap_seed_catalog_v0()
    frame = CIVILIZATION_BOOTSTRAP_TECHNICAL_COMPETENCE_FRAME_V1
    basic = _concept(catalog, "basic_electricity")
    evidence_id = EvidenceId("evidence_pr8_authority_basic")
    claim_id = CapabilityClaimId("claim_pr8_authority_basic")
    evaluation_id = ClaimEvaluationId("eval_pr8_authority_basic")
    evidence = EvidenceRecord(
        evidence_id,
        SUBJECT,
        EvidenceKind.PROJECT,
        "Observed a bounded low-voltage basic-electricity analysis exercise.",
        EvidenceContext("Bounded conceptual analysis with explicit assumptions."),
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
        T0 + timedelta(minutes=2),
        _provenance(),
    )
    evaluation = ClaimEvaluation(
        evaluation_id,
        claim_id,
        EvaluationPolicyRef.parse("civilization_bootstrap:pr8_authority_seed@1"),
        EvaluatorRef(EvaluatorKind.HUMAN, "test:pr8_authority_reviewer"),
        T0 + timedelta(minutes=3),
        (
            EvidenceAssessment(
                evidence_id,
                EvidenceBearing.SUPPORTS,
                EvidenceReliability.HIGH,
                "The observation bears directly on the bounded conceptual claim.",
                "Support remains bounded to the stated claim scope.",
            ),
        ),
        CoverageAssessment(
            CoverageStatus.SUFFICIENT_FOR_CLAIM,
            "Sufficient only for the bounded conceptual claim.",
        ),
        ConflictStatus.NONE,
        EvaluationConclusion.SUPPORTED,
        "Supported under the explicit bounded evaluation policy.",
    )
    records = EpistemicRecordSet((evidence,), (claim,), (evaluation,))
    state = derive_supported_state_v1(
        records=records,
        frame=frame,
        request=DeterministicStateDerivationRequest(
            PersonalCapabilityStateId("state_pr8_authority_basic"),
            SUBJECT,
            basic.ref,
            frame.ref,
            T0 + timedelta(minutes=4),
            T0 + timedelta(minutes=4),
            (evaluation_id,),
            (ClaimDimensionBinding(claim_id, ("conceptual_knowledge",)),),
        ),
    )
    return catalog, build_civilization_bootstrap_frame_catalog_v1(), records, state, basic


def _focus_only_frontier():
    catalog = build_civilization_bootstrap_seed_catalog_v0()
    frames = build_civilization_bootstrap_frame_catalog_v1()
    focus = _concept(catalog, "potable_water_treatment")
    records = EpistemicRecordSet()
    states = PersonalCapabilityStateSet(SUBJECT, ())
    request = ProgressionFrontierRequest(
        ProgressionFrontierId("frontier_pr8_verification"),
        SUBJECT,
        T0,
        T0 + timedelta(minutes=1),
        ProgressionRequesterRef(ProgressionMechanismKind.MODEL, "test:pr8_focus_model"),
        focuses=(ProgressionFocus(focus.ref, "Explicit request-local focus only."),),
    )
    frontier = derive_progression_frontier_v1(
        capability_catalog=catalog,
        frame_catalog=frames,
        records=records,
        state_set=states,
        request=request,
    )
    return catalog, frames, records, states, frontier


def test_dependency_direction_is_candidate_source_to_selected_seed_target() -> None:
    catalog, frames, records, state, basic = _supported_basic_state()
    target = _concept(catalog, "low_voltage_power_distribution")
    frontier = derive_progression_frontier_v1(
        capability_catalog=catalog,
        frame_catalog=frames,
        records=records,
        state_set=PersonalCapabilityStateSet(SUBJECT, (state,)),
        request=ProgressionFrontierRequest(
            ProgressionFrontierId("frontier_pr8_direction"),
            SUBJECT,
            T0 + timedelta(minutes=5),
            T0 + timedelta(minutes=5),
            ProgressionRequesterRef(ProgressionMechanismKind.HUMAN, "test:pr8_subject"),
            seed_bindings=(FrontierSeedBinding(state.state_id, ("conceptual_knowledge",)),),
        ),
    )
    refs = {item.concept_ref for item in frontier.candidates}
    assert target.ref in refs
    assert basic.ref not in refs
    witness = next(
        witness
        for candidate in frontier.candidates
        if candidate.concept_ref == target.ref
        for witness in candidate.adjacency_witnesses
        if witness.relation.kind is RelationKind.REQUIRES
    )
    assert witness.relation.source_ref == target.ref
    assert witness.relation.target_ref == basic.ref


def test_one_supported_dimension_does_not_authorize_an_unknown_dimension_as_seed() -> None:
    catalog, frames, records, state, _ = _supported_basic_state()
    assert next(d for d in state.dimensions if d.dimension_key == "conceptual_knowledge").standing is DimensionStanding.SUPPORTED
    assert next(d for d in state.dimensions if d.dimension_key == "calculation").standing is DimensionStanding.UNKNOWN
    request = ProgressionFrontierRequest(
        ProgressionFrontierId("frontier_pr8_no_whole_capability_aggregation"),
        SUBJECT,
        T0 + timedelta(minutes=5),
        T0 + timedelta(minutes=5),
        ProgressionRequesterRef(ProgressionMechanismKind.HUMAN, "test:pr8_subject"),
        seed_bindings=(FrontierSeedBinding(state.state_id, ("calculation",)),),
    )
    with pytest.raises(InvalidProgressionRequest):
        derive_progression_frontier_v1(
            capability_catalog=catalog,
            frame_catalog=frames,
            records=records,
            state_set=PersonalCapabilityStateSet(SUBJECT, (state,)),
            request=request,
        )


def test_supported_by_relation_cannot_be_laundered_into_prerequisite_gap() -> None:
    catalog = build_civilization_bootstrap_seed_catalog_v0()
    frames = build_civilization_bootstrap_frame_catalog_v1()
    target = _concept(catalog, "microcontroller_sensor_systems")
    prerequisite = _concept(catalog, "embedded_programming")
    supported_by = next(
        relation
        for relation in catalog.relations
        if relation.kind is RelationKind.SUPPORTED_BY
        and relation.source_id == target.capability_id
        and relation.target_id == prerequisite.capability_id
    )
    request = ProgressionFrontierRequest(
        ProgressionFrontierId("frontier_pr8_supported_by_laundering"),
        SUBJECT,
        T0,
        T0 + timedelta(minutes=1),
        ProgressionRequesterRef(ProgressionMechanismKind.RULE, "test:pr8_binding_attacker"),
        focuses=(ProgressionFocus(target.ref, "Make the target an explicit frontier candidate."),),
        prerequisite_bindings=(
            PrerequisiteCheckBinding(
                target.ref,
                prerequisite.ref,
                supported_by.scope,
                frames.frames[0].ref,
                ("conceptual_knowledge",),
                None,
            ),
        ),
    )
    with pytest.raises(InvalidProgressionRequest):
        derive_progression_frontier_v1(
            capability_catalog=catalog,
            frame_catalog=frames,
            records=EpistemicRecordSet(),
            state_set=PersonalCapabilityStateSet(SUBJECT, ()),
            request=request,
        )


def test_structural_deserialization_is_not_source_backed_verification() -> None:
    catalog, frames, records, states, frontier = _focus_only_frontier()
    validate_progression_frontier_v1(
        capability_catalog=catalog,
        frame_catalog=frames,
        records=records,
        state_set=states,
        frontier=ProgressionFrontier.from_json(frontier.to_json()),
    )

    payload = frontier.to_dict()
    payload["frontier"]["candidates"] = []
    tampered = ProgressionFrontier.from_dict(payload)
    assert tampered.focuses == frontier.focuses
    assert tampered.candidates == ()
    with pytest.raises(InvalidProgressionFrontier):
        validate_progression_frontier_v1(
            capability_catalog=catalog,
            frame_catalog=frames,
            records=records,
            state_set=states,
            frontier=tampered,
        )


def test_tampered_policy_or_deriver_cannot_pass_source_backed_verification() -> None:
    catalog, frames, records, states, frontier = _focus_only_frontier()
    tampered_policy = replace(
        frontier,
        policy_ref=ProgressionPolicyRef.parse("core:some_other_progression_policy@1"),
    )
    with pytest.raises(InvalidProgressionFrontier):
        validate_progression_frontier_v1(
            capability_catalog=catalog,
            frame_catalog=frames,
            records=records,
            state_set=states,
            frontier=tampered_policy,
        )


def test_gap_and_witnesses_expose_no_prohibition_readiness_or_ranking_fields() -> None:
    for cls in (ProgressionFrontier,):
        annotations = getattr(cls, "__annotations__", {})
        for forbidden in (
            "ready",
            "readiness",
            "permitted",
            "prohibited",
            "score",
            "rank",
            "priority",
            "difficulty",
            "recommendation_strength",
            "witness_count_score",
        ):
            assert forbidden not in annotations


def test_exploration_is_explicit_preservation_not_self_confirming_frontier_input() -> None:
    catalog = build_civilization_bootstrap_seed_catalog_v0()
    frames = build_civilization_bootstrap_frame_catalog_v1()
    concept = _concept(catalog, "potable_water_treatment")
    frontier = derive_progression_frontier_v1(
        capability_catalog=catalog,
        frame_catalog=frames,
        records=EpistemicRecordSet(),
        state_set=PersonalCapabilityStateSet(SUBJECT, ()),
        request=ProgressionFrontierRequest(
            ProgressionFrontierId("frontier_pr8_exploration_only"),
            SUBJECT,
            T0,
            T0 + timedelta(minutes=1),
            ProgressionRequesterRef(ProgressionMechanismKind.MODEL, "test:pr8_exploration_model"),
            exploration_inputs=(ExplorationInput(concept.ref, "Explicitly preserve this unrelated direction."),),
        ),
    )
    assert frontier.candidates == ()
    assert [item.concept_ref for item in frontier.exploration_opportunities] == [concept.ref]
    parameters = inspect.signature(derive_progression_frontier_v1).parameters
    assert "frontier" not in parameters
    assert "history" not in parameters
    assert "legend" not in parameters
