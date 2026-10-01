from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
DOCS_INDEX = ROOT / "docs" / "index.md"
GETTING_STARTED = ROOT / "docs" / "getting-started.md"
SNAPSHOT = ROOT / ".github" / "assets" / "capability-lab-player-window-snapshot.svg"
ZENSICAL = ROOT / "zensical.toml"


def test_readme_explains_human_problem_before_architecture():
    text = README.read_text(encoding="utf-8")

    assert "A real-world capability profile built from evidence, not arbitrary scores." in text
    assert "What was observed?" in text
    assert "What does the evidence support?" in text
    assert "What remains uncertain?" in text
    assert "What may be worth exploring next?" in text
    assert "[Capability Lab in 5 minutes](docs/getting-started.md)" in text
    assert "## Why Capability Lab" in text
    assert "## What exists today" in text
    assert "## Start here" in text

    snapshot_position = text.index(".github/assets/capability-lab-player-window-snapshot.svg")
    why_position = text.index("## Why Capability Lab")
    architecture_position = text.index("## How it works")
    assert snapshot_position < why_position < architecture_position


def test_readme_example_is_grounded_in_included_player_window_demo():
    from capability_lab.player_window.demo import (
        build_civilization_bootstrap_player_window_demo_v1,
    )
    from capability_lab.state import DimensionStanding

    readme = README.read_text(encoding="utf-8")
    snapshot = SNAPSHOT.read_text(encoding="utf-8")
    window = build_civilization_bootstrap_player_window_demo_v1()

    assert len(window.capabilities) == 1
    capability = window.capabilities[0]
    assert capability.concept_ref.capability_id.key == "basic_electricity"

    dimensions = {item.dimension_key: item for item in capability.dimensions}
    assert dimensions["conceptual_knowledge"].standing is DimensionStanding.SUPPORTED
    assert dimensions["calculation"].standing is DimensionStanding.UNKNOWN

    assert window.frontier is not None
    assert any(
        item.concept_ref.capability_id.key == "low_voltage_power_distribution"
        for item in window.frontier.candidates
    )
    assert any(
        item.concept_ref.capability_id.key == "potable_water_treatment"
        for item in window.frontier.exploration
    )

    for phrase in (
        "Basic Electricity",
        "Low-Voltage Power Distribution",
        "Potable Water Treatment",
    ):
        assert phrase in readme
        assert phrase in snapshot

    assert "conceptual_knowledge" in snapshot
    assert "SUPPORTED" in snapshot
    assert "PROGRESSION FRONTIER" in snapshot
    assert "NO GLOBAL SCORE" in snapshot
    assert "linearGradient" not in snapshot

    assert "dependency-free" in readme
    assert "presentation fixture" in readme
    assert "generic integration path" in readme


def test_docs_landing_uses_the_included_demo_without_claiming_it_is_the_generic_write_proof():
    text = DOCS_INDEX.read_text(encoding="utf-8")

    assert "Know what the evidence actually supports." in text
    assert "A real-world skill tree that has to show its work" in text
    assert "Capability Lab in 5 minutes" in text
    assert 'href="getting-started/"' in text
    assert "Basic Electricity" in text
    assert "Low-Voltage Power Distribution" in text
    assert "Potable Water Treatment" in text
    assert "presentation demo is intentionally separate from the generic governed write-path proof" in text
    assert "PR11." not in text
    assert "PR12." not in text


def test_five_minute_introduction_stays_plain_language():
    text = GETTING_STARTED.read_text(encoding="utf-8")

    assert text.startswith("# Capability Lab in 5 minutes")
    assert "What does the evidence actually support about what a person can do" in text
    assert "real-world skill tree or player profile that has to show its work" in text
    assert "through evidence rather than XP" in text
    assert "observation != evidence" in text
    assert "unknown != failure" in text
    assert "progression != prescription" in text
    assert "capability != permission" in text
    assert "It does not define the person." in text
    assert "PR11." not in text
    assert "PR12." not in text


def test_documentation_navigation_exposes_start_here_early():
    text = ZENSICAL.read_text(encoding="utf-8")

    assert 'site_description = "A real-world capability profile built from evidence, not arbitrary scores."' in text
    assert '{ "Start here · 5 minutes" = "getting-started.md" }' in text

    overview_position = text.index('{ "Overview" = "index.md" }')
    start_position = text.index('{ "Start here · 5 minutes" = "getting-started.md" }')
    model_position = text.index('{ "Understand the model" = "overview.md" }')
    assert overview_position < start_position < model_position
