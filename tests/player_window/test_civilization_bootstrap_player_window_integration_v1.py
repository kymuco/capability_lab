from capability_lab.player_window.demo import build_civilization_bootstrap_player_window_demo_v1
from capability_lab.state import DimensionStanding


def test_real_civilization_bootstrap_sources_reach_first_local_product_projection() -> None:
    window = build_civilization_bootstrap_player_window_demo_v1()

    assert len(window.capabilities) == 1
    capability = window.capabilities[0]
    assert capability.concept_ref.capability_id.key == "basic_electricity"

    dimensions = {item.dimension_key: item for item in capability.dimensions}
    assert set(dimensions) == {
        "calculation",
        "conceptual_knowledge",
        "diagnosis",
        "execution",
        "explanation",
        "independence",
        "transfer",
    }
    assert dimensions["conceptual_knowledge"].standing is DimensionStanding.SUPPORTED
    assert dimensions["calculation"].standing is DimensionStanding.UNKNOWN
    assert dimensions["conceptual_knowledge"].claims

    assert len(window.achievements) == 1
    assert len(window.milestones) == 1
    assert window.legend is not None
    visible_history = {
        str(window.achievements[0].achievement_id),
        str(window.milestones[0].milestone_id),
    }
    assert set(window.legend.entries[0].source_refs) == visible_history

    assert window.frontier is not None
    assert any(
        item.concept_ref.capability_id.key == "low_voltage_power_distribution"
        for item in window.frontier.candidates
    )
    assert any(
        item.concept_ref.capability_id.key == "potable_water_treatment"
        for item in window.frontier.exploration
    )
    assert window.frontier.prerequisite_gaps
    assert window.frontier.prerequisite_gaps[0].state_id == capability.state_id
