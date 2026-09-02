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
from capability_lab.history import (
    AchievementBasisKind,
    AchievementBasisRef,
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
    PersonalHistoryRecordSet,
    PersonalLegend,
    PersonalLegendEntry,
    PersonalLegendId,
    PersonalLegendSet,
)
from capability_lab.player_window import (
    InvalidPlayerWindow,
    InvalidPlayerWindowRequest,
    PlayerWindowId,
    PlayerWindowMechanismKind,
    PlayerWindowRequest,
    PlayerWindowRequesterRef,
    PlayerWindowSet,
    PlayerWindowViewerRef,
    derive_player_window_v1,
    render_player_window_html_v1,
    validate_player_window_v1,
)
from capability_lab.progression import (
    ExplorationInput,
    FrontierSeedBinding,
    PrerequisiteCheckBinding,
    ProgressionFrontierId,
    ProgressionFrontierRequest,
    ProgressionFrontierSet,
    ProgressionMechanismKind,
    ProgressionRequesterRef,
    derive_progression_frontier_v1,
)
from capability_lab.semantics import RelationKind
from capability_lab.state import (
    DimensionConflictStatus,
    PersonalCapabilityStateId,
    PersonalCapabilityStateSet,
)


T0 = datetime(2026, 8, 16, 10, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("subject_pr9_adversarial")


def _provenance() -> ProvenanceTrail:
    return ProvenanceTrail(
        (ProvenanceSource(ProvenanceSourceKind.ACTOR, "test:pr9_adversarial"),)
    )


def _state_sources():
    catalog = build_civilization_bootstrap_seed_catalog_v0()
    frame_catalog = build_civilization_bootstrap_frame_catalog_v1()
    frame = CIVILIZATION_BOOTSTRAP_TECHNICAL_COMPETENCE_FRAME_V1
    basic = next(
        item for item in catalog.concepts if item.capability_id.key == "basic_electricity"
    )
    target = next(
        item
        for item in catalog.concepts
        if item.capability_id.key == "low_voltage_power_distribution"
    )
    exploration = next(
        item
        for item in catalog.concepts
        if item.capability_id.key == "potable_water_treatment"
    )
    requires = next(
        item
        for item in catalog.relations
        if item.kind is RelationKind.REQUIRES
        and item.source_id == target.capability_id
        and item.target_id == basic.capability_id
    )

    evidence_id = EvidenceId("evidence_pr9_integrity")
    claim_id = CapabilityClaimId("claim_pr9_integrity")
    evaluation_id = ClaimEvaluationId("eval_pr9_integrity_support")
    evidence = EvidenceRecord(
        evidence_id,
        SUBJECT,
        EvidenceKind.PROJECT,
        "Bounded low-voltage conceptual exercise.",
        EvidenceContext("Local bounded conceptual exercise."),
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
        EvaluationPolicyRef.parse("civilization_bootstrap:pr9_integrity@1"),
        EvaluatorRef(EvaluatorKind.HUMAN, "test:pr9_adversarial"),
        T0 + timedelta(minutes=10),
        (
            EvidenceAssessment(
                evidence_id,
                EvidenceBearing.SUPPORTS,
                EvidenceReliability.HIGH,
                "Directly bears on the bounded claim.",
                "Support is bounded to the stated scope.",
            ),
        ),
        CoverageAssessment(
            CoverageStatus.SUFFICIENT_FOR_CLAIM,
            "Sufficient only for the bounded claim.",
        ),
        ConflictStatus.NONE,
        EvaluationConclusion.SUPPORTED,
        "Supported under the bounded integrity-test policy.",
    )
    records = EpistemicRecordSet((evidence,), (claim,), (evaluation,))
    state = derive_supported_state_v1(
        records=records,
        frame=frame,
        request=DeterministicStateDerivationRequest(
            PersonalCapabilityStateId("state_pr9_integrity"),
            SUBJECT,
            basic.ref,
            frame.ref,
            T0 + timedelta(minutes=15),
            T0 + timedelta(minutes=15),
            (evaluation_id,),
            (ClaimDimensionBinding(claim_id, ("conceptual_knowledge",)),),
        ),
    )
    state_set = PersonalCapabilityStateSet(SUBJECT, (state,))
    frontier = derive_progression_frontier_v1(
        capability_catalog=catalog,
        frame_catalog=frame_catalog,
        records=records,
        state_set=state_set,
        request=ProgressionFrontierRequest(
            ProgressionFrontierId("frontier_pr9_integrity"),
            SUBJECT,
            T0 + timedelta(minutes=20),
            T0 + timedelta(minutes=20),
            ProgressionRequesterRef(
                ProgressionMechanismKind.HUMAN,
                "test:pr9_subject",
            ),
            seed_bindings=(
                FrontierSeedBinding(state.state_id, ("conceptual_knowledge",)),
            ),
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
                    "Keep one explicit exploration direction visible.",
                ),
            ),
        ),
    )
    return {
        "catalog": catalog,
        "frame_catalog": frame_catalog,
        "frame": frame,
        "records": records,
        "state": state,
        "state_set": state_set,
        "frontier": frontier,
        "frontier_set": ProgressionFrontierSet(SUBJECT, (frontier,)),
    }


def _empty_history_sources():
    return (
        AchievementFamilyCatalog(),
        PersonalHistoryRecordSet(SUBJECT),
        PersonalLegendSet(SUBJECT),
    )


def _window_request(*, state_ids=(), frontier_id=None, requester_kind=PlayerWindowMechanismKind.HUMAN, viewer_kind=PlayerWindowMechanismKind.HUMAN):
    return PlayerWindowRequest(
        PlayerWindowId("window_pr9_integrity"),
        SUBJECT,
        T0 + timedelta(minutes=20),
        T0 + timedelta(minutes=25),
        PlayerWindowRequesterRef(requester_kind, "test:window_requester"),
        PlayerWindowViewerRef(viewer_kind, "test:window_viewer"),
        selected_state_ids=state_ids,
        selected_frontier_id=frontier_id,
    )


def _derive_state_window(sources, *, state_set=None, records=None, request=None, frontier_set=None):
    family_catalog, history_set, legend_set = _empty_history_sources()
    return derive_player_window_v1(
        capability_catalog=sources["catalog"],
        competence_frame_catalog=sources["frame_catalog"],
        epistemic_records=records or sources["records"],
        state_set=state_set or sources["state_set"],
        achievement_family_catalog=family_catalog,
        history_set=history_set,
        legend_set=legend_set,
        frontier_set=frontier_set or ProgressionFrontierSet(SUBJECT),
        request=request
        or _window_request(state_ids=(sources["state"].state_id,)),
    )


def _verify_state_window(sources, window, *, state_set=None, records=None, frontier_set=None):
    family_catalog, history_set, legend_set = _empty_history_sources()
    validate_player_window_v1(
        capability_catalog=sources["catalog"],
        competence_frame_catalog=sources["frame_catalog"],
        epistemic_records=records or sources["records"],
        state_set=state_set or sources["state_set"],
        achievement_family_catalog=family_catalog,
        history_set=history_set,
        legend_set=legend_set,
        frontier_set=frontier_set or ProgressionFrontierSet(SUBJECT),
        window=window,
    )


def test_hidden_frontier_state_basis_is_rejected_before_projection() -> None:
    sources = _state_sources()
    with pytest.raises(InvalidPlayerWindowRequest):
        _derive_state_window(
            sources,
            request=_window_request(frontier_id=sources["frontier"].frontier_id),
            frontier_set=sources["frontier_set"],
        )


def test_positive_only_partial_state_cannot_be_projected_against_full_frame() -> None:
    sources = _state_sources()
    supported_dimension = next(
        item
        for item in sources["state"].dimensions
        if item.dimension_key == "conceptual_knowledge"
    )
    partial_state = replace(sources["state"], dimensions=(supported_dimension,))
    partial_set = PersonalCapabilityStateSet(SUBJECT, (partial_state,))
    with pytest.raises(InvalidPlayerWindowRequest):
        _derive_state_window(sources, state_set=partial_set)


def test_structurally_valid_display_tampering_is_rejected_by_source_backed_verifier() -> None:
    sources = _state_sources()
    window = _derive_state_window(sources)
    capability = replace(window.capabilities[0], concept_name="Mastered Electricity")
    tampered = replace(window, capabilities=(capability,))

    assert tampered.capabilities[0].concept_name == "Mastered Electricity"
    with pytest.raises(InvalidPlayerWindow):
        _verify_state_window(sources, tampered)


def test_unverified_frontier_cannot_be_laundered_into_verified_player_window() -> None:
    sources = _state_sources()
    tampered_frontier = replace(
        sources["frontier"],
        rationale="Tampered frontier output that was not produced by PR8 derivation.",
    )
    tampered_frontier_set = ProgressionFrontierSet(SUBJECT, (tampered_frontier,))
    request = _window_request(
        state_ids=(sources["state"].state_id,),
        frontier_id=tampered_frontier.frontier_id,
    )
    window = _derive_state_window(
        sources,
        request=request,
        frontier_set=tampered_frontier_set,
    )

    with pytest.raises(InvalidPlayerWindow):
        _verify_state_window(
            sources,
            window,
            frontier_set=tampered_frontier_set,
        )


def test_selected_state_governance_catches_hidden_cross_evaluation_conflict() -> None:
    sources = _state_sources()
    original_evaluation = sources["records"].evaluations[0]
    evidence_id = original_evaluation.evidence_assessments[0].evidence_id
    contradicted_id = ClaimEvaluationId("eval_pr9_integrity_contradicted")
    contradicted = ClaimEvaluation(
        contradicted_id,
        original_evaluation.claim_id,
        original_evaluation.policy_ref,
        original_evaluation.evaluator_ref,
        T0 + timedelta(minutes=11),
        (
            EvidenceAssessment(
                evidence_id,
                EvidenceBearing.CONTRADICTS,
                EvidenceReliability.HIGH,
                "A contradictory bounded assessment for the adversarial fixture.",
                "This creates a directional conflict for the same claim.",
            ),
        ),
        CoverageAssessment(
            CoverageStatus.SUFFICIENT_FOR_CLAIM,
            "Sufficient to contradict the same bounded claim.",
        ),
        ConflictStatus.NONE,
        EvaluationConclusion.CONTRADICTED,
        "Contradicted under the same bounded policy.",
    )
    records = EpistemicRecordSet(
        sources["records"].evidence_records,
        sources["records"].claims,
        (*sources["records"].evaluations, contradicted),
    )
    dimensions = []
    for dimension in sources["state"].dimensions:
        if dimension.dimension_key == "conceptual_knowledge":
            dimensions.append(
                replace(
                    dimension,
                    basis_evaluation_ids=(
                        *dimension.basis_evaluation_ids,
                        contradicted_id,
                    ),
                    conflict_status=DimensionConflictStatus.NONE,
                )
            )
        else:
            dimensions.append(dimension)
    hidden_conflict_state = replace(
        sources["state"],
        dimensions=tuple(dimensions),
    )
    hidden_conflict_set = PersonalCapabilityStateSet(
        SUBJECT,
        (hidden_conflict_state,),
    )
    window = _derive_state_window(
        sources,
        state_set=hidden_conflict_set,
        records=records,
    )

    with pytest.raises(InvalidPlayerWindow):
        _verify_state_window(
            sources,
            window,
            state_set=hidden_conflict_set,
            records=records,
        )


def test_unselected_newer_invalid_state_is_inert_for_window_and_verification() -> None:
    sources = _state_sources()
    baseline = _derive_state_window(sources)
    supported_dimension = next(
        item
        for item in sources["state"].dimensions
        if item.dimension_key == "conceptual_knowledge"
    )
    newer_partial = replace(
        sources["state"],
        state_id=PersonalCapabilityStateId("state_pr9_unselected_newer_partial"),
        as_of=T0 + timedelta(hours=2),
        derived_at=T0 + timedelta(hours=2),
        dimensions=(supported_dimension,),
    )
    expanded_set = PersonalCapabilityStateSet(
        SUBJECT,
        (sources["state"], newer_partial),
    )
    repeated = _derive_state_window(sources, state_set=expanded_set)

    assert repeated == baseline
    _verify_state_window(sources, repeated, state_set=expanded_set)


def test_model_requester_and_non_subject_viewer_remain_attribution_not_authority() -> None:
    sources = _state_sources()
    request = _window_request(
        state_ids=(sources["state"].state_id,),
        requester_kind=PlayerWindowMechanismKind.MODEL,
        viewer_kind=PlayerWindowMechanismKind.EXTERNAL_SYSTEM,
    )
    window = _derive_state_window(sources, request=request)
    html = render_player_window_html_v1(window)

    assert "Requester" in html and "model:test:window_requester" in html
    assert "Viewer" in html and "external_system:test:window_viewer" in html
    assert "not publication or authorization" in html
    assert "subject-selected" not in html.lower()
    assert "authorized viewer" not in html.lower()


def test_history_only_rendering_does_not_launder_accomplishment_into_readiness() -> None:
    family = AchievementFamily(
        AchievementFamilyId("test", "bounded_history"),
        "Bounded Historical Accomplishment",
        "One historical accomplishment used only to test Player Window wording.",
    )
    family_catalog = AchievementFamilyCatalog((family,))
    achievement = AchievementInstance(
        AchievementInstanceId("achievement_pr9_history_only"),
        SUBJECT,
        family.ref,
        T0,
        T0 + timedelta(minutes=1),
        AchievementQualificationPolicyRef.parse("test:history_projection@1"),
        AchievementQualifierRef(HistoryMechanismKind.HUMAN, "test:qualifier"),
        (AchievementBasisRef(AchievementBasisKind.EXTERNAL_ARTIFACT, "artifact:bounded_event"),),
        "Historical accomplishment only; not current readiness.",
    )
    history_set = PersonalHistoryRecordSet(SUBJECT, (achievement,), ())
    request = PlayerWindowRequest(
        PlayerWindowId("window_pr9_history_only"),
        SUBJECT,
        T0 + timedelta(minutes=2),
        T0 + timedelta(minutes=2),
        PlayerWindowRequesterRef(PlayerWindowMechanismKind.HUMAN, "test:requester"),
        PlayerWindowViewerRef(PlayerWindowMechanismKind.HUMAN, "test:viewer"),
        selected_achievement_ids=(achievement.achievement_id,),
    )
    window = derive_player_window_v1(
        capability_catalog=build_civilization_bootstrap_seed_catalog_v0(),
        competence_frame_catalog=build_civilization_bootstrap_frame_catalog_v1(),
        epistemic_records=EpistemicRecordSet(),
        state_set=PersonalCapabilityStateSet(SUBJECT),
        achievement_family_catalog=family_catalog,
        history_set=history_set,
        legend_set=PersonalLegendSet(SUBJECT),
        frontier_set=ProgressionFrontierSet(SUBJECT),
        request=request,
    )
    html = render_player_window_html_v1(window)

    assert "historical accomplishment" in html
    assert "not current readiness" in html
    assert "ready for" not in html.lower()
    assert "readiness score" not in html.lower()


def test_visible_legend_cannot_hide_its_exact_history_source() -> None:
    family = AchievementFamily(
        AchievementFamilyId("test", "legend_source"),
        "Legend Source Achievement",
        "Historical source for hidden-source adversarial testing.",
    )
    family_catalog = AchievementFamilyCatalog((family,))
    achievement = AchievementInstance(
        AchievementInstanceId("achievement_pr9_legend_source"),
        SUBJECT,
        family.ref,
        T0,
        T0 + timedelta(minutes=1),
        AchievementQualificationPolicyRef.parse("test:legend_source@1"),
        AchievementQualifierRef(HistoryMechanismKind.HUMAN, "test:qualifier"),
        (AchievementBasisRef(AchievementBasisKind.EXTERNAL_ARTIFACT, "artifact:legend_source"),),
        "Exact historical source.",
    )
    history_set = PersonalHistoryRecordSet(SUBJECT, (achievement,), ())
    legend = PersonalLegend(
        PersonalLegendId("legend_pr9_hidden_source"),
        SUBJECT,
        T0 + timedelta(minutes=2),
        T0 + timedelta(minutes=3),
        LegendProjectionPolicyRef.parse("test:legend_projection@1"),
        LegendGeneratorRef(HistoryMechanismKind.MODEL, "test:legend_model"),
        "Selected narrative",
        "Narrative projection over one exact history source.",
        (
            PersonalLegendEntry(
                (
                    LegendSourceRef(
                        LegendSourceKind.ACHIEVEMENT_INSTANCE,
                        str(achievement.achievement_id),
                    ),
                ),
                "Narrative heading",
                "Narrative text.",
            ),
        ),
    )
    legend_set = PersonalLegendSet(SUBJECT, (legend,))
    legend_set.validate_against_history(history_set)
    request = PlayerWindowRequest(
        PlayerWindowId("window_pr9_hidden_legend_source"),
        SUBJECT,
        T0 + timedelta(minutes=3),
        T0 + timedelta(minutes=4),
        PlayerWindowRequesterRef(PlayerWindowMechanismKind.HUMAN, "test:requester"),
        PlayerWindowViewerRef(PlayerWindowMechanismKind.HUMAN, "test:viewer"),
        selected_legend_id=legend.legend_id,
    )

    with pytest.raises(InvalidPlayerWindowRequest):
        derive_player_window_v1(
            capability_catalog=build_civilization_bootstrap_seed_catalog_v0(),
            competence_frame_catalog=build_civilization_bootstrap_frame_catalog_v1(),
            epistemic_records=EpistemicRecordSet(),
            state_set=PersonalCapabilityStateSet(SUBJECT),
            achievement_family_catalog=family_catalog,
            history_set=history_set,
            legend_set=legend_set,
            frontier_set=ProgressionFrontierSet(SUBJECT),
            request=request,
        )


def test_gap_and_no_gap_language_never_becomes_blocked_or_ready() -> None:
    sources = _state_sources()
    request = _window_request(
        state_ids=(sources["state"].state_id,),
        frontier_id=sources["frontier"].frontier_id,
    )
    window = _derive_state_window(
        sources,
        request=request,
        frontier_set=sources["frontier_set"],
    )
    html = render_player_window_html_v1(window)

    assert "Prerequisite evidence gap" in html
    assert "does not mean capability absence, prohibition, readiness, safety, or permission" in html
    assert "Blocked" not in html
    assert "Ready" not in html
    assert "cleared prerequisite" not in html.lower()


def test_html_css_and_url_shaped_source_text_stays_in_text_context() -> None:
    sources = _state_sources()
    window = _derive_state_window(sources)
    malicious = replace(
        window.capabilities[0],
        concept_name='</style><style>body{display:none}</style> https://evil.example javascript:alert(1)',
    )
    tampered = replace(window, capabilities=(malicious,))
    html = render_player_window_html_v1(tampered)

    assert "&lt;/style&gt;&lt;style&gt;" in html
    assert "<style>body{display:none}</style>" not in html
    assert 'href="https://evil.example"' not in html
    assert 'src="https://evil.example"' not in html
    assert 'href="javascript:' not in html.lower()
    assert 'src="javascript:' not in html.lower()


def test_player_window_set_keeps_alternatives_without_latest_wins() -> None:
    sources = _state_sources()
    first = _derive_state_window(sources)
    second = replace(
        first,
        window_id=PlayerWindowId("window_pr9_integrity_alternative"),
        generated_at=first.generated_at + timedelta(minutes=1),
    )
    windows = PlayerWindowSet(SUBJECT, (second, first))

    assert {item.window_id for item in windows.windows} == {
        first.window_id,
        second.window_id,
    }
    assert not hasattr(windows, "latest")
    assert not hasattr(windows, "canonical")
    assert not hasattr(windows, "current")
