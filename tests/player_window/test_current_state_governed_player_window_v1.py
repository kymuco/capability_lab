from dataclasses import fields
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
    PersonalHistoryRecordSet,
    PersonalLegendSet,
)
from capability_lab.player_window import (
    CurrentStateGovernedPlayerWindow,
    CurrentStatePlayerWindowRequest,
    PlayerWindowId,
    PlayerWindowMechanismKind,
    PlayerWindowRequesterRef,
    PlayerWindowViewerRef,
    current_state_governed_player_window_sha256_v1,
    derive_current_state_governed_player_window_v1,
    validate_current_state_governed_player_window_v1,
)
from capability_lab.progression import (
    CurrentStatePrerequisiteCheck,
    CurrentStateProgressionAuthorityStatus,
    CurrentStateProgressionFrontierRequest,
    CurrentStateProgressionSeed,
    PrerequisiteDimensionGapKind,
    ProgressionFocus,
    ProgressionFrontierId,
    ProgressionMechanismKind,
    ProgressionRequesterRef,
)
from capability_lab.semantics import RelationKind
from capability_lab.state import (
    CurrentStateSelectionAction,
    CurrentStateSelectionMechanismKind,
    CurrentStateSelectionPolicyRef,
    CurrentStateSelectorRef,
    PersonalCapabilityCurrentStateSelectionAuthorityBasis,
    PersonalCapabilityCurrentStateSelectionHistory,
    PersonalCapabilityCurrentStateSelectionRequest,
    PersonalCapabilityStateAcceptanceAdmission,
    PersonalCapabilityStateAcceptanceRequest,
    PersonalCapabilityStateAcceptanceSet,
    PersonalCapabilityStateId,
    PersonalCapabilityStateSet,
    StateAcceptanceMechanismKind,
    StateAcceptancePolicyRef,
    StateAccepterRef,
    accept_persisted_personal_capability_state_v1,
    select_current_personal_capability_state_v1,
)


T0 = datetime(2026, 8, 27, 1, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("pr11_11_subject")
ACCEPTANCE_POLICY = StateAcceptancePolicyRef.parse("test:pr11_11_acceptance@1")
ACCEPTER = StateAccepterRef(
    StateAcceptanceMechanismKind.HUMAN,
    "test:pr11_11_acceptor",
)
SELECTION_POLICY = CurrentStateSelectionPolicyRef.parse("test:pr11_11_current@1")
SELECTOR = CurrentStateSelectorRef(
    CurrentStateSelectionMechanismKind.HUMAN,
    "test:pr11_11_selector",
)
PROGRESSION_REQUESTER = ProgressionRequesterRef(
    ProgressionMechanismKind.HUMAN,
    "test:pr11_11_progression",
)
WINDOW_REQUESTER = PlayerWindowRequesterRef(
    PlayerWindowMechanismKind.HUMAN,
    "test:pr11_11_window_requester",
)
VIEWER = PlayerWindowViewerRef(
    PlayerWindowMechanismKind.HUMAN,
    "test:pr11_11_viewer",
)


def _provenance():
    return ProvenanceTrail(
        (ProvenanceSource(ProvenanceSourceKind.ACTOR, "test:pr11_11_actor"),)
    )


def _evaluation(evidence_id, claim_id, evaluation_id, *, minutes):
    return ClaimEvaluation(
        evaluation_id,
        claim_id,
        EvaluationPolicyRef.parse("test:pr11_11_evaluation@1"),
        EvaluatorRef(EvaluatorKind.HUMAN, "test:pr11_11_reviewer"),
        T0 + timedelta(minutes=minutes),
        (
            EvidenceAssessment(
                evidence_id,
                EvidenceBearing.SUPPORTS,
                EvidenceReliability.HIGH,
                "Direct bounded support for the exact test claim.",
                "Support remains bounded to this exact test scope.",
            ),
        ),
        CoverageAssessment(
            CoverageStatus.SUFFICIENT_FOR_CLAIM,
            "Sufficient only for this bounded test claim.",
        ),
        ConflictStatus.NONE,
        EvaluationConclusion.SUPPORTED,
        "Supported under the exact test evaluation policy.",
    )


def _acceptance_request(state, *, minutes):
    return PersonalCapabilityStateAcceptanceRequest(
        state_id=state.state_id,
        acceptance_policy_ref=ACCEPTANCE_POLICY,
        accepter_ref=ACCEPTER,
        accepted_at=T0 + timedelta(minutes=minutes),
        rationale="Explicit test acceptance for PR11.11 authority replay.",
    )


def _selection_request(state, *, minutes, action=CurrentStateSelectionAction.SELECT):
    return PersonalCapabilityCurrentStateSelectionRequest(
        concept_ref=state.concept_ref,
        frame_ref=state.frame_ref,
        action=action,
        selected_state_id=(
            state.state_id
            if action is CurrentStateSelectionAction.SELECT
            else None
        ),
        selection_policy_ref=SELECTION_POLICY,
        selector_ref=SELECTOR,
        selected_at=T0 + timedelta(minutes=minutes),
        rationale="Explicit governed current-state selection for PR11.11.",
    )


def _case():
    catalog = build_civilization_bootstrap_seed_catalog_v0()
    frames = build_civilization_bootstrap_frame_catalog_v1()
    frame = CIVILIZATION_BOOTSTRAP_TECHNICAL_COMPETENCE_FRAME_V1
    basic = next(
        item
        for item in catalog.concepts
        if item.capability_id.key == "basic_electricity"
    )
    water = next(
        item
        for item in catalog.concepts
        if item.capability_id.key == "potable_water_treatment"
    )
    target = next(
        item
        for item in catalog.concepts
        if item.capability_id.key == "low_voltage_power_distribution"
    )
    requires = next(
        item
        for item in catalog.relations
        if item.kind is RelationKind.REQUIRES
        and item.source_id == target.capability_id
        and item.target_id == basic.capability_id
    )

    evidence_a = EvidenceRecord(
        EvidenceId("evidence_pr11_11_basic"),
        SUBJECT,
        EvidenceKind.PROJECT,
        "Bounded basic-electricity demonstration.",
        EvidenceContext("PR11.11 deterministic test fixture."),
        T0,
        T0 + timedelta(minutes=1),
        _provenance(),
    )
    evidence_b = EvidenceRecord(
        EvidenceId("evidence_pr11_11_water"),
        SUBJECT,
        EvidenceKind.PROJECT,
        "Bounded potable-water-treatment explanation.",
        EvidenceContext("PR11.11 second current scope fixture."),
        T0,
        T0 + timedelta(minutes=1),
        _provenance(),
    )
    claim_a = CapabilityClaim(
        CapabilityClaimId("claim_pr11_11_basic"),
        SUBJECT,
        basic.ref,
        "Can explain bounded basic-electricity relationships.",
        ClaimScope("Bounded conceptual test scope."),
        T0 + timedelta(minutes=2),
        _provenance(),
    )
    claim_b = CapabilityClaim(
        CapabilityClaimId("claim_pr11_11_water"),
        SUBJECT,
        water.ref,
        "Can explain a bounded potable-water-treatment concept.",
        ClaimScope("Bounded conceptual test scope."),
        T0 + timedelta(minutes=2),
        _provenance(),
    )
    eval_a = _evaluation(
        evidence_a.evidence_id,
        claim_a.claim_id,
        ClaimEvaluationId("evaluation_pr11_11_basic"),
        minutes=5,
    )
    eval_b = _evaluation(
        evidence_b.evidence_id,
        claim_b.claim_id,
        ClaimEvaluationId("evaluation_pr11_11_water"),
        minutes=6,
    )
    records = EpistemicRecordSet(
        (evidence_a, evidence_b),
        (claim_a, claim_b),
        (eval_a, eval_b),
    )
    state_a = derive_supported_state_v1(
        records=records,
        frame=frame,
        request=DeterministicStateDerivationRequest(
            PersonalCapabilityStateId("state_pr11_11_basic"),
            SUBJECT,
            basic.ref,
            frame.ref,
            T0 + timedelta(minutes=10),
            T0 + timedelta(minutes=10),
            (eval_a.evaluation_id,),
            (
                ClaimDimensionBinding(
                    claim_a.claim_id,
                    ("conceptual_knowledge",),
                ),
            ),
        ),
    )
    state_b = derive_supported_state_v1(
        records=records,
        frame=frame,
        request=DeterministicStateDerivationRequest(
            PersonalCapabilityStateId("state_pr11_11_water"),
            SUBJECT,
            water.ref,
            frame.ref,
            T0 + timedelta(minutes=11),
            T0 + timedelta(minutes=11),
            (eval_b.evaluation_id,),
            (
                ClaimDimensionBinding(
                    claim_b.claim_id,
                    ("conceptual_knowledge",),
                ),
            ),
        ),
    )

    empty_states = PersonalCapabilityStateSet(SUBJECT)
    states_a = PersonalCapabilityStateSet(SUBJECT, (state_a,))
    states_ab = PersonalCapabilityStateSet(SUBJECT, (state_a, state_b))
    acceptance_a = accept_persisted_personal_capability_state_v1(
        predecessor=empty_states,
        successor=states_a,
        request=_acceptance_request(state_a, minutes=14),
    )
    acceptance_b = accept_persisted_personal_capability_state_v1(
        predecessor=states_a,
        successor=states_ab,
        request=_acceptance_request(state_b, minutes=15),
    )
    admission_a = PersonalCapabilityStateAcceptanceAdmission(
        acceptance=acceptance_a,
        persistence_predecessor=empty_states,
        persistence_successor=states_a,
    )
    admission_b = PersonalCapabilityStateAcceptanceAdmission(
        acceptance=acceptance_b,
        persistence_predecessor=states_a,
        persistence_successor=states_ab,
    )
    empty_acceptances = PersonalCapabilityStateAcceptanceSet(SUBJECT)
    acceptances_a = PersonalCapabilityStateAcceptanceSet(
        SUBJECT,
        (acceptance_a,),
    )
    acceptances_ab = PersonalCapabilityStateAcceptanceSet(
        SUBJECT,
        (acceptance_a, acceptance_b),
    )

    history_a = select_current_personal_capability_state_v1(
        state_snapshot=states_ab,
        acceptance_predecessor=empty_acceptances,
        acceptance_successor=acceptances_a,
        acceptance_admissions=(admission_a,),
        selection_history=PersonalCapabilityCurrentStateSelectionHistory(SUBJECT),
        request=_selection_request(state_a, minutes=20),
    )
    history_ab = select_current_personal_capability_state_v1(
        state_snapshot=states_ab,
        acceptance_predecessor=acceptances_a,
        acceptance_successor=acceptances_ab,
        acceptance_admissions=(admission_b,),
        selection_history=history_a,
        request=_selection_request(state_b, minutes=21),
    )
    bases = (
        PersonalCapabilityCurrentStateSelectionAuthorityBasis(
            selection=history_ab.selections[0],
            state_snapshot=states_ab,
            acceptance_predecessor=empty_acceptances,
            acceptance_successor=acceptances_a,
            acceptance_admissions=(admission_a,),
        ),
        PersonalCapabilityCurrentStateSelectionAuthorityBasis(
            selection=history_ab.selections[1],
            state_snapshot=states_ab,
            acceptance_predecessor=acceptances_a,
            acceptance_successor=acceptances_ab,
            acceptance_admissions=(admission_b,),
        ),
    )

    family = AchievementFamily(
        AchievementFamilyId("test", "pr11_11_basic_project"),
        "PR11.11 Basic Project",
        "One bounded event used only to exercise presentation visibility.",
        qualification_criteria=(
            AchievementCriterion(
                "bounded_event",
                "A bounded event exists.",
            ),
        ),
    )
    family_catalog = AchievementFamilyCatalog((family,))
    achievement = AchievementInstance(
        AchievementInstanceId("achievement_pr11_11_basic"),
        SUBJECT,
        family.ref,
        T0 + timedelta(minutes=3),
        T0 + timedelta(minutes=30),
        AchievementQualificationPolicyRef.parse("test:pr11_11_achievement@1"),
        AchievementQualifierRef(
            HistoryMechanismKind.HUMAN,
            "test:pr11_11_history_reviewer",
        ),
        (
            AchievementBasisRef(
                AchievementBasisKind.EVIDENCE_RECORD,
                str(evidence_a.evidence_id),
            ),
            AchievementBasisRef(
                AchievementBasisKind.CLAIM_EVALUATION,
                str(eval_a.evaluation_id),
            ),
        ),
        "Presentation-only history record for PR11.11.",
    )
    history_set = PersonalHistoryRecordSet(SUBJECT, (achievement,), ())
    history_set.validate_against_family_catalog(family_catalog)
    history_set.validate_against_epistemics(records)

    return {
        "catalog": catalog,
        "frames": frames,
        "records": records,
        "state_a": state_a,
        "state_b": state_b,
        "states_ab": states_ab,
        "history": history_ab,
        "bases": bases,
        "accepted": acceptances_ab,
        "family_catalog": family_catalog,
        "history_set": history_set,
        "legend_set": PersonalLegendSet(SUBJECT),
        "achievement": achievement,
        "target": target,
        "requires": requires,
    }


def _seed_progression_request(case, *, as_of=None, generated_at=None):
    generated_at = generated_at or T0 + timedelta(minutes=40)
    return CurrentStateProgressionFrontierRequest(
        frontier_id=ProgressionFrontierId("frontier_pr11_11_seed"),
        as_of=as_of or T0 + timedelta(minutes=40),
        generated_at=generated_at,
        requester_ref=PROGRESSION_REQUESTER,
        seeds=(
            CurrentStateProgressionSeed(
                concept_ref=case["state_a"].concept_ref,
                frame_ref=case["state_a"].frame_ref,
                dimension_keys=("conceptual_knowledge",),
            ),
        ),
    )


def _prerequisite_progression_request(case, *, generated_at=None):
    generated_at = generated_at or T0 + timedelta(minutes=40)
    return CurrentStateProgressionFrontierRequest(
        frontier_id=ProgressionFrontierId("frontier_pr11_11_prerequisite"),
        as_of=T0 + timedelta(minutes=40),
        generated_at=generated_at,
        requester_ref=PROGRESSION_REQUESTER,
        focuses=(
            ProgressionFocus(
                case["target"].ref,
                "Expose exact REQUIRES relation for CLEAR/SELECT projection.",
            ),
        ),
        prerequisite_checks=(
            CurrentStatePrerequisiteCheck(
                target_ref=case["target"].ref,
                prerequisite_ref=case["state_a"].concept_ref,
                relation_scope=case["requires"].scope,
                frame_ref=case["state_a"].frame_ref,
                required_dimension_keys=("conceptual_knowledge",),
            ),
        ),
    )


def _request(case, *, progression=None, visible_achievement_ids=()):
    progression = progression or _seed_progression_request(case)
    return CurrentStatePlayerWindowRequest(
        window_id=PlayerWindowId("window_pr11_11"),
        generated_at=progression.generated_at,
        requester_ref=WINDOW_REQUESTER,
        viewer_ref=VIEWER,
        progression_request=progression,
        visible_achievement_ids=visible_achievement_ids,
    )


def _derive(case, request, *, history=None, bases=None):
    return derive_current_state_governed_player_window_v1(
        capability_catalog=case["catalog"],
        competence_frame_catalog=case["frames"],
        epistemic_records=case["records"],
        selection_history=history or case["history"],
        authority_bases=case["bases"] if bases is None else bases,
        achievement_family_catalog=case["family_catalog"],
        history_set=case["history_set"],
        legend_set=case["legend_set"],
        request=request,
    )


def _clear_a(case, *, minutes=24):
    history = select_current_personal_capability_state_v1(
        state_snapshot=case["states_ab"],
        acceptance_predecessor=case["accepted"],
        acceptance_successor=case["accepted"],
        selection_history=case["history"],
        request=_selection_request(
            case["state_a"],
            minutes=minutes,
            action=CurrentStateSelectionAction.CLEAR,
        ),
    )
    clear = max(history.selections, key=lambda item: item.selected_at)
    basis = PersonalCapabilityCurrentStateSelectionAuthorityBasis(
        selection=clear,
        state_snapshot=case["states_ab"],
        acceptance_predecessor=case["accepted"],
        acceptance_successor=case["accepted"],
        acceptance_admissions=(),
    )
    return history, case["bases"] + (basis,)


def test_public_request_has_no_state_or_frontier_selection_authority_surface() -> None:
    names = {item.name for item in fields(CurrentStatePlayerWindowRequest)}
    assert "subject_ref" not in names
    assert "selected_state_ids" not in names
    assert "selected_frontier_id" not in names
    assert "state_set" not in names
    assert "frontier_set" not in names
    assert "current_state_portfolio" not in names
    assert "governed_frontier" not in names


def test_two_current_scopes_are_both_visible_even_when_frontier_uses_only_one() -> None:
    case = _case()
    snapshot = _derive(case, _request(case))

    assert len(snapshot.current_state_entries) == 2
    assert set(snapshot.window.selected_state_ids) == {
        case["state_a"].state_id,
        case["state_b"].state_id,
    }
    assert {item.state_id for item in snapshot.window.capabilities} == {
        case["state_a"].state_id,
        case["state_b"].state_id,
    }
    assert len(snapshot.frontier_authority_bindings) == 1
    binding = snapshot.frontier_authority_bindings[0]
    assert binding.status is CurrentStateProgressionAuthorityStatus.SELECT
    assert binding.selected_state_id == case["state_a"].state_id
    assert snapshot.window.selected_frontier_id == (
        snapshot.request.progression_request.frontier_id
    )


def test_presentation_visibility_can_hide_history_without_changing_authority() -> None:
    case = _case()
    hidden = _derive(case, _request(case))
    visible = _derive(
        case,
        _request(
            case,
            visible_achievement_ids=(case["achievement"].achievement_id,),
        ),
    )

    assert hidden.window.achievements == ()
    assert len(visible.window.achievements) == 1
    assert hidden.current_selection_history_sha256 == visible.current_selection_history_sha256
    assert hidden.current_state_portfolio_sha256 == visible.current_state_portfolio_sha256
    assert hidden.governed_frontier_sha256 == visible.governed_frontier_sha256
    assert hidden.current_state_entries == visible.current_state_entries
    assert hidden.frontier_authority_bindings == visible.frontier_authority_bindings


def test_clear_remains_explicit_while_raw_pr9_omits_cleared_capability() -> None:
    case = _case()
    history, bases = _clear_a(case)
    progression = _prerequisite_progression_request(case)
    snapshot = _derive(
        case,
        _request(case, progression=progression),
        history=history,
        bases=bases,
    )

    by_scope = {
        (item.concept_ref, item.frame_ref): item
        for item in snapshot.current_state_entries
    }
    cleared = by_scope[(case["state_a"].concept_ref, case["state_a"].frame_ref)]
    assert cleared.action is CurrentStateSelectionAction.CLEAR
    assert case["state_a"].state_id not in snapshot.window.selected_state_ids
    assert case["state_b"].state_id in snapshot.window.selected_state_ids

    binding = snapshot.frontier_authority_bindings[0]
    assert binding.status is CurrentStateProgressionAuthorityStatus.CLEAR
    assert binding.selected_state_id is None
    assert snapshot.window.frontier.prerequisite_gaps[0].state_id is None
    assert (
        snapshot.window.frontier.prerequisite_gaps[0].dimension_gaps[0].kind
        is PrerequisiteDimensionGapKind.NO_SELECTED_STATE
    )


def test_canonical_round_trip_digest_and_fresh_validation() -> None:
    case = _case()
    snapshot = _derive(case, _request(case))
    restored = CurrentStateGovernedPlayerWindow.from_json(snapshot.to_json())

    assert restored == snapshot
    assert CurrentStatePlayerWindowRequest.from_json(
        snapshot.request.to_json()
    ) == snapshot.request
    digest = current_state_governed_player_window_sha256_v1(snapshot)
    assert len(digest) == 64
    assert digest == current_state_governed_player_window_sha256_v1(restored)
    assert (
        validate_current_state_governed_player_window_v1(
            capability_catalog=case["catalog"],
            competence_frame_catalog=case["frames"],
            epistemic_records=case["records"],
            selection_history=case["history"],
            authority_bases=case["bases"],
            achievement_family_catalog=case["family_catalog"],
            history_set=case["history_set"],
            legend_set=case["legend_set"],
            snapshot=restored,
        )
        is None
    )
