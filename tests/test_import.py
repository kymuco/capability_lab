def test_package_imports() -> None:
    import capability_lab

    assert capability_lab.__version__ == "0.1.0.dev0"
    assert capability_lab.CapabilityId.parse("core:example").key == "example"
    assert str(capability_lab.CapabilityConceptRef.parse("core:example@1")) == "core:example@1"
    assert str(capability_lab.EvidenceId("ev_01")) == "ev_01"
    assert str(capability_lab.CapabilityClaimId("claim_01")) == "claim_01"
    assert str(capability_lab.ClaimEvaluationId("eval_01")) == "eval_01"
    assert str(capability_lab.PersonalCapabilityStateId("state_01")) == "state_01"
    assert str(capability_lab.CompetenceFrameId.parse("core:technical")) == "core:technical"
    assert str(capability_lab.CompetenceFrameRef.parse("core:technical@1")) == "core:technical@1"
    assert str(capability_lab.StateDerivationPolicyRef.parse("core:state_policy@1")) == "core:state_policy@1"
    assert capability_lab.DimensionConflictStatus.UNRESOLVED.value == "unresolved"
    assert str(capability_lab.DETERMINISTIC_SUPPORTED_STATE_POLICY_V1) == "core:deterministic_supported_state@1"
    assert capability_lab.DETERMINISTIC_SUPPORTED_STATE_DERIVER_V1.kind.value == "rule"
    assert callable(capability_lab.derive_supported_state_v1)
    assert capability_lab.CIVILIZATION_BOOTSTRAP_SEED_VERSION == "v0"
    assert capability_lab.CIVILIZATION_BOOTSTRAP_NAMESPACE.namespace_id == "civilization_bootstrap"
    assert str(capability_lab.CIVILIZATION_BOOTSTRAP_TECHNICAL_COMPETENCE_FRAME_V1.ref) == "civilization_bootstrap:technical_competence@1"
    assert callable(capability_lab.build_civilization_bootstrap_seed_catalog_v0)
    assert callable(capability_lab.build_civilization_bootstrap_frame_catalog_v1)
    assert str(capability_lab.CapabilityProposalId("proposal_01")) == "proposal_01"
    assert capability_lab.ProposalMechanismKind.MODEL.value == "model"
    assert capability_lab.ProposalReviewVerdict.RECOMMEND_ACCEPT.value == "recommend_accept"
    assert capability_lab.ProposalKind.CREATE_CLAIM.value == "create_claim"
    assert str(capability_lab.AchievementFamilyId.parse("core:achievement")) == "core:achievement"
    assert str(capability_lab.AchievementFamilyRef.parse("core:achievement@1")) == "core:achievement@1"
    assert str(capability_lab.AchievementInstanceId("achievement_01")) == "achievement_01"
    assert str(capability_lab.PersonalMilestoneEventId("milestone_01")) == "milestone_01"
    assert str(capability_lab.PersonalLegendId("legend_01")) == "legend_01"
    assert capability_lab.HistoryMechanismKind.MODEL.value == "model"
    assert str(capability_lab.ProgressionFrontierId("frontier_01")) == "frontier_01"
    assert str(capability_lab.DETERMINISTIC_PROGRESSION_FRONTIER_POLICY_V1) == "core:deterministic_progression_frontier@1"
    assert capability_lab.DETERMINISTIC_PROGRESSION_FRONTIER_DERIVER_V1.kind.value == "rule"
    assert capability_lab.PrerequisiteDimensionGapKind.NO_SELECTED_STATE.value == "no_selected_state"
    assert callable(capability_lab.derive_progression_frontier_v1)
    assert callable(capability_lab.validate_progression_frontier_v1)
    assert str(capability_lab.PlayerWindowId("window_01")) == "window_01"
    assert str(capability_lab.DETERMINISTIC_PLAYER_WINDOW_POLICY_V1) == "core:deterministic_player_window@1"
    assert capability_lab.DETERMINISTIC_PLAYER_WINDOW_GENERATOR_V1.kind.value == "rule"
    assert callable(capability_lab.derive_player_window_v1)
    assert callable(capability_lab.validate_player_window_v1)
    assert callable(capability_lab.render_player_window_html_v1)
