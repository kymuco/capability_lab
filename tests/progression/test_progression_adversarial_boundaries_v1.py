import capability_lab.progression as progression


def test_public_progression_api_exposes_no_hidden_recommendation_or_mutation_shortcuts() -> None:
    forbidden = {
        "rank_frontier",
        "score_frontier",
        "recommend_next",
        "best_next_step",
        "shortest_path",
        "optimal_path",
        "auto_select_latest_state",
        "infer_goal",
        "infer_interest",
        "frontier_to_state",
        "frontier_to_claim",
        "frontier_to_evidence",
        "frontier_to_history",
        "legend_to_frontier",
        "achievement_to_frontier",
        "proposal_to_frontier",
        "grant_permission",
        "deny_permission",
    }
    assert forbidden.isdisjoint(set(progression.__all__))


def test_frontier_types_have_no_scalar_priority_readiness_or_human_level_fields() -> None:
    for cls_name in (
        "FrontierCandidate",
        "PrerequisiteEvidenceGap",
        "ExplorationOpportunity",
        "ProgressionFrontier",
    ):
        annotations = getattr(getattr(progression, cls_name), "__annotations__", {})
        for forbidden in (
            "score",
            "rank",
            "priority",
            "difficulty",
            "distance",
            "readiness",
            "probability",
            "success_probability",
            "human_level",
        ):
            assert forbidden not in annotations
