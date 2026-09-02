from dataclasses import replace
from datetime import datetime, timedelta, timezone

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
    FrontierSeedBinding,
    InvalidProgressionRequest,
    PrerequisiteCheckBinding,
    PrerequisiteDimensionGapKind,
    ProgressionFocus,
    ProgressionFrontierId,
    ProgressionFrontierRequest,
    ProgressionMechanismKind,
    ProgressionRequesterRef,
    derive_progression_frontier_v1,
    validate_progression_frontier_v1,
)
from capability_lab.semantics import (
    CapabilityCatalog,
    CapabilityRelation,
    RelationKind,
    RelationScope,
)
from capability_lab.state import (
    DimensionConflictStatus,
    DimensionStanding,
    PersonalCapabilityStateId,
    PersonalCapabilityStateSet,
)


T0 = datetime(2026, 8, 15, 16, 30, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("subject_pr8_second_adversarial")
FRAME = CIVILIZATION_BOOTSTRAP_TECHNICAL_COMPETENCE_FRAME_V1


def _concept(catalog, key):
    return next(item for item in catalog.concepts if item.capability_id.key == key)


def _provenance() -> ProvenanceTrail:
    return ProvenanceTrail(
        (ProvenanceSource(ProvenanceSourceKind.ACTOR, "test:pr8_second_adversarial"),)
    )


def _records_for_concept(concept_ref, *, prefix: str, contradictory: bool = False):
    evidence_id = EvidenceId(f"evidence_{prefix}")
    claim_id = CapabilityClaimId(f"claim_{prefix}")
    support_eval_id = ClaimEvaluationId(f"eval_{prefix}_support")
    evidence = EvidenceRecord(
        evidence_id,
        SUBJECT,
        EvidenceKind.PROJECT,
        "Bounded project evidence for an explicitly scoped progression-state test.",
        EvidenceContext("Controlled progression adversarial fixture."),
        T0,
        T0 + timedelta(minutes=1),
        _provenance(),
    )
    claim = CapabilityClaim(
        claim_id,
        SUBJECT,
        concept_ref,
        "Can explain the bounded concept under explicit assumptions.",
        ClaimScope("Conceptual knowledge only for an adversarial progression fixture."),
        T0 + timedelta(minutes=2),
        _provenance(),
    )
    support = ClaimEvaluation(
        support_eval_id,
        claim_id,
        EvaluationPolicyRef.parse("core:pr8_second_adversarial@1"),
        EvaluatorRef(EvaluatorKind.HUMAN, "test:pr8_reviewer"),
        T0 + timedelta(minutes=3),
        (
            EvidenceAssessment(
                evidence_id,
                EvidenceBearing.SUPPORTS,
                EvidenceReliability.HIGH,
                "Evidence supports the bounded claim.",
                "No broader capability inference is made.",
            ),
        ),
        CoverageAssessment(CoverageStatus.SUFFICIENT_FOR_CLAIM, "Sufficient for the bounded claim."),
        ConflictStatus.NONE,
        EvaluationConclusion.SUPPORTED,
        "Supported for the bounded claim.",
    )
    evaluations = [support]
    selected = [support_eval_id]
    if contradictory:
        contradict_eval_id = ClaimEvaluationId(f"eval_{prefix}_contradict")
        contradict = ClaimEvaluation(
            contradict_eval_id,
            claim_id,
            EvaluationPolicyRef.parse("core:pr8_second_adversarial@1"),
            EvaluatorRef(EvaluatorKind.HUMAN, "test:pr8_reviewer"),
            T0 + timedelta(minutes=4),
            (
                EvidenceAssessment(
                    evidence_id,
                    EvidenceBearing.CONTRADICTS,
                    EvidenceReliability.HIGH,
                    "A conflicting evaluation is intentionally selected for the same claim.",
                    "The conflict is preserved rather than collapsed into a score.",
                ),
            ),
            CoverageAssessment(CoverageStatus.SUFFICIENT_FOR_CLAIM, "Sufficient to express the contradiction."),
            ConflictStatus.NONE,
            EvaluationConclusion.CONTRADICTED,
            "Contradicted under the same bounded claim for conflict testing.",
        )
        evaluations.append(contradict)
        selected.append(contradict_eval_id)
    return (
        EpistemicRecordSet((evidence,), (claim,), tuple(evaluations)),
        claim_id,
        tuple(selected),
    )


def _state(concept_ref, *, state_id: str, prefix: str, contradictory: bool = False):
    records, claim_id, selected = _records_for_concept(
        concept_ref,
        prefix=prefix,
        contradictory=contradictory,
    )
    state = derive_supported_state_v1(
        records=records,
        frame=FRAME,
        request=DeterministicStateDerivationRequest(
            PersonalCapabilityStateId(state_id),
            SUBJECT,
            concept_ref,
            FRAME.ref,
            T0 + timedelta(minutes=5),
            T0 + timedelta(minutes=5),
            selected,
            (ClaimDimensionBinding(claim_id, ("conceptual_knowledge",)),),
        ),
    )
    return records, state


def _request(*, frontier_id: str, seed_bindings=(), focuses=(), prerequisite_bindings=(), as_of=None):
    return ProgressionFrontierRequest(
        ProgressionFrontierId(frontier_id),
        SUBJECT,
        as_of or T0 + timedelta(minutes=10),
        T0 + timedelta(minutes=10),
        ProgressionRequesterRef(ProgressionMechanismKind.HUMAN, "test:pr8_subject"),
        focuses=focuses,
        seed_bindings=seed_bindings,
        prerequisite_bindings=prerequisite_bindings,
    )


def test_exact_focus_may_not_collapse_into_selected_seed_concept() -> None:
    catalog = build_civilization_bootstrap_seed_catalog_v0()
    basic = _concept(catalog, "basic_electricity")
    records, state = _state(basic.ref, state_id="state_pr8_focus_seed", prefix="pr8_focus_seed")
    request = _request(
        frontier_id="frontier_pr8_focus_seed_overlap",
        seed_bindings=(FrontierSeedBinding(state.state_id, ("conceptual_knowledge",)),),
        focuses=(ProgressionFocus(basic.ref, "This intentionally overlaps the selected seed."),),
    )
    with pytest.raises(InvalidProgressionRequest):
        derive_progression_frontier_v1(
            capability_catalog=catalog,
            frame_catalog=build_civilization_bootstrap_frame_catalog_v1(),
            records=records,
            state_set=PersonalCapabilityStateSet(SUBJECT, (state,)),
            request=request,
        )


def test_two_seed_states_for_same_exact_concept_cannot_amplify_witnesses() -> None:
    catalog = build_civilization_bootstrap_seed_catalog_v0()
    basic = _concept(catalog, "basic_electricity")
    records, first = _state(basic.ref, state_id="state_pr8_repeat_a", prefix="pr8_repeat")
    second = derive_supported_state_v1(
        records=records,
        frame=FRAME,
        request=DeterministicStateDerivationRequest(
            PersonalCapabilityStateId("state_pr8_repeat_b"),
            SUBJECT,
            basic.ref,
            FRAME.ref,
            T0 + timedelta(minutes=6),
            T0 + timedelta(minutes=6),
            tuple(item.evaluation_id for item in records.evaluations),
            (ClaimDimensionBinding(records.claims[0].claim_id, ("conceptual_knowledge",)),),
        ),
    )
    request = _request(
        frontier_id="frontier_pr8_repeated_seed_state",
        seed_bindings=(
            FrontierSeedBinding(first.state_id, ("conceptual_knowledge",)),
            FrontierSeedBinding(second.state_id, ("conceptual_knowledge",)),
        ),
    )
    with pytest.raises(InvalidProgressionRequest):
        derive_progression_frontier_v1(
            capability_catalog=catalog,
            frame_catalog=build_civilization_bootstrap_frame_catalog_v1(),
            records=records,
            state_set=PersonalCapabilityStateSet(SUBJECT, (first, second)),
            request=request,
        )


def test_partial_requires_binding_preserves_unassessed_prerequisite() -> None:
    catalog = build_civilization_bootstrap_seed_catalog_v0()
    basic = _concept(catalog, "basic_electricity")
    measurement = _concept(catalog, "electrical_measurement")
    target = _concept(catalog, "low_voltage_power_distribution")
    existing_requires = next(
        item
        for item in catalog.relations
        if item.kind is RelationKind.REQUIRES
        and item.source_id == target.capability_id
        and item.target_id == basic.capability_id
    )
    second_requires = CapabilityRelation(
        target.capability_id,
        measurement.capability_id,
        RelationKind.REQUIRES,
        RelationScope(
            "bench_validation",
            "Adversarial second prerequisite used only to test partial explicit coverage.",
        ),
    )
    expanded = CapabilityCatalog(
        catalog.namespaces,
        catalog.concepts,
        catalog.relations + (second_requires,),
    )
    records, state = _state(basic.ref, state_id="state_pr8_partial_requires", prefix="pr8_partial_requires")
    request = _request(
        frontier_id="frontier_pr8_partial_requires",
        seed_bindings=(FrontierSeedBinding(state.state_id, ("conceptual_knowledge",)),),
        prerequisite_bindings=(
            PrerequisiteCheckBinding(
                target.ref,
                basic.ref,
                existing_requires.scope,
                FRAME.ref,
                ("conceptual_knowledge",),
                None,
            ),
        ),
    )
    frontier = derive_progression_frontier_v1(
        capability_catalog=expanded,
        frame_catalog=build_civilization_bootstrap_frame_catalog_v1(),
        records=records,
        state_set=PersonalCapabilityStateSet(SUBJECT, (state,)),
        request=request,
    )
    candidate = next(item for item in frontier.candidates if item.concept_ref == target.ref)
    assert {item.target_ref for item in candidate.assessed_prerequisites} == {basic.ref}
    assert {item.target_ref for item in candidate.unassessed_prerequisites} == {measurement.ref}
    assert len(frontier.prerequisite_gaps) == 1
    assert frontier.prerequisite_gaps[0].dimension_gaps[0].kind is PrerequisiteDimensionGapKind.NO_SELECTED_STATE
    assert not hasattr(candidate, "coverage_complete")
    assert not hasattr(frontier, "prerequisites_complete")


def test_supported_unresolved_seed_is_explicitly_usable_without_conflict_ranking() -> None:
    catalog = build_civilization_bootstrap_seed_catalog_v0()
    basic = _concept(catalog, "basic_electricity")
    records, state = _state(
        basic.ref,
        state_id="state_pr8_conflicted_supported",
        prefix="pr8_conflicted_supported",
        contradictory=True,
    )
    dimension = next(item for item in state.dimensions if item.dimension_key == "conceptual_knowledge")
    assert dimension.standing is DimensionStanding.SUPPORTED
    assert dimension.conflict_status is DimensionConflictStatus.UNRESOLVED

    frontier = derive_progression_frontier_v1(
        capability_catalog=catalog,
        frame_catalog=build_civilization_bootstrap_frame_catalog_v1(),
        records=records,
        state_set=PersonalCapabilityStateSet(SUBJECT, (state,)),
        request=_request(
            frontier_id="frontier_pr8_conflicted_supported",
            seed_bindings=(FrontierSeedBinding(state.state_id, ("conceptual_knowledge",)),),
        ),
    )
    assert any(
        witness.state_id == state.state_id
        for candidate in frontier.candidates
        for witness in candidate.adjacency_witnesses
    )
    validate_progression_frontier_v1(
        capability_catalog=catalog,
        frame_catalog=build_civilization_bootstrap_frame_catalog_v1(),
        records=records,
        state_set=PersonalCapabilityStateSet(SUBJECT, (state,)),
        frontier=frontier,
    )
    for forbidden in ("conflict_penalty", "conflict_score", "priority", "rank"):
        assert not hasattr(frontier, forbidden)


def test_focus_may_overlap_a_derived_candidate_without_becoming_a_rank_signal() -> None:
    catalog = build_civilization_bootstrap_seed_catalog_v0()
    basic = _concept(catalog, "basic_electricity")
    target = _concept(catalog, "low_voltage_power_distribution")
    records, state = _state(basic.ref, state_id="state_pr8_focus_candidate", prefix="pr8_focus_candidate")
    frontier = derive_progression_frontier_v1(
        capability_catalog=catalog,
        frame_catalog=build_civilization_bootstrap_frame_catalog_v1(),
        records=records,
        state_set=PersonalCapabilityStateSet(SUBJECT, (state,)),
        request=_request(
            frontier_id="frontier_pr8_focus_candidate",
            seed_bindings=(FrontierSeedBinding(state.state_id, ("conceptual_knowledge",)),),
            focuses=(ProgressionFocus(target.ref, "Keep the already adjacent target explicitly visible."),),
        ),
    )
    candidate = next(item for item in frontier.candidates if item.concept_ref == target.ref)
    assert candidate.explicit_focus is True
    assert candidate.adjacency_witnesses
    assert not hasattr(candidate, "priority")
    assert not hasattr(candidate, "recommendation_strength")


def test_verifier_is_consistency_check_not_snapshot_authentication() -> None:
    catalog = build_civilization_bootstrap_seed_catalog_v0()
    focus = _concept(catalog, "potable_water_treatment")
    request = _request(
        frontier_id="frontier_pr8_snapshot_substitution",
        focuses=(ProgressionFocus(focus.ref, "Explicit focus for snapshot-authenticity boundary testing."),),
    )
    frontier = derive_progression_frontier_v1(
        capability_catalog=catalog,
        frame_catalog=build_civilization_bootstrap_frame_catalog_v1(),
        records=EpistemicRecordSet(),
        state_set=PersonalCapabilityStateSet(SUBJECT, ()),
        request=request,
    )

    altered_focus = replace(
        focus,
        definition="Materially substituted definition under the same exact ref for an authenticity-boundary test.",
    )
    altered_catalog = CapabilityCatalog(
        catalog.namespaces,
        tuple(altered_focus if item.capability_id == focus.capability_id else item for item in catalog.concepts),
        catalog.relations,
    )
    assert altered_catalog.to_json() != catalog.to_json()

    validate_progression_frontier_v1(
        capability_catalog=altered_catalog,
        frame_catalog=build_civilization_bootstrap_frame_catalog_v1(),
        records=EpistemicRecordSet(),
        state_set=PersonalCapabilityStateSet(SUBJECT, ()),
        frontier=frontier,
    )
    assert not hasattr(frontier, "catalog_digest")
    assert not hasattr(frontier, "snapshot_signature")
    assert not hasattr(frontier, "authenticated_source_snapshot")


def test_historical_as_of_does_not_authenticate_historical_catalog_snapshot() -> None:
    catalog = build_civilization_bootstrap_seed_catalog_v0()
    focus = _concept(catalog, "radio_communication")
    historical_as_of = datetime(2020, 1, 1, tzinfo=timezone.utc)
    request = ProgressionFrontierRequest(
        ProgressionFrontierId("frontier_pr8_historical_as_of_limit"),
        SUBJECT,
        historical_as_of,
        T0 + timedelta(minutes=10),
        ProgressionRequesterRef(ProgressionMechanismKind.HUMAN, "test:pr8_subject"),
        focuses=(ProgressionFocus(focus.ref, "Historical projection boundary test."),),
    )
    frontier = derive_progression_frontier_v1(
        capability_catalog=catalog,
        frame_catalog=build_civilization_bootstrap_frame_catalog_v1(),
        records=EpistemicRecordSet(),
        state_set=PersonalCapabilityStateSet(SUBJECT, ()),
        request=request,
    )
    assert frontier.as_of == historical_as_of
    assert not hasattr(frontier, "catalog_as_of")
    assert not hasattr(frontier, "catalog_snapshot_ref")
