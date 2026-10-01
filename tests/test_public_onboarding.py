from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
DOCS_INDEX = ROOT / "docs" / "index.md"
GETTING_STARTED = ROOT / "docs" / "getting-started.md"
ZENSICAL = ROOT / "zensical.toml"


def test_readme_explains_human_problem_before_architecture():
    text = README.read_text(encoding="utf-8")

    assert "A real-world capability profile built from evidence, not arbitrary scores." in text
    assert "skill tree or player profile that has to show its work" in text
    assert "## A simple example" in text
    assert "Electrical engineering: 87%" in text
    assert "## When would I use it?" in text
    assert "## What it is not" in text
    assert "[Start in 5 minutes](docs/getting-started.md)" in text

    assert text.index("## A simple example") < text.index("## How it works")


def test_docs_landing_is_conceptual_and_has_clear_start_path():
    text = DOCS_INDEX.read_text(encoding="utf-8")

    assert "Know what the evidence actually supports." in text
    assert "A real-world skill tree that has to show its work" in text
    assert "Capability Lab in 5 minutes" in text
    assert 'href="getting-started/"' in text
    assert "Electrical engineering: 87%" in text
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
