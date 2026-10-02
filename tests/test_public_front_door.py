from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
ISSUE_TEMPLATE = ROOT / ".github" / "ISSUE_TEMPLATE"


def test_readme_has_compact_modern_public_front_door():
    text = README.read_text(encoding="utf-8")

    assert "A real-world capability profile built from evidence, not arbitrary scores." in text
    assert "**Evidence-grounded capability modeling under explicit governance boundaries.**" in text
    assert ".github/assets/capability-lab-player-window-snapshot.svg" in text
    assert "Civilization Bootstrap Player Window" in text
    assert "Basic Electricity" in text
    assert "Low-Voltage Power Distribution" in text
    assert "Potable Water Treatment" in text
    assert "actions/workflows/ci.yml/badge.svg" in text
    assert "actions/workflows/docs.yml/badge.svg" in text
    assert "Python-3.11%2B" in text
    assert "PolyForm%20Noncommercial" in text
    assert "stable research subsystem" in text.lower()
    assert "development is demand-driven" in text
    assert "Observation is not evidence." in text

    assert text.index(".github/assets/capability-lab-player-window-snapshot.svg") < text.index(
        "actions/workflows/ci.yml/badge.svg"
    )
    assert text.index("actions/workflows/ci.yml/badge.svg") < text.index("## How it works")


def test_readme_architecture_visual_preserves_governed_boundaries():
    text = README.read_text(encoding="utf-8")
    strip = (ROOT / "docs" / "assets" / "capability-lab-architecture-strip.svg").read_text(
        encoding="utf-8"
    )

    assert "docs/assets/capability-lab-architecture-strip.svg" in text
    assert "docs/assets/capability-lab-architecture-stack.svg" in text
    assert 'media="(max-width: 640px)"' in text
    assert "```mermaid" not in text

    for phrase in (
        "OBSERVE &amp; INTERPRET",
        "ESTABLISH CURRENT STATE",
        "ADVISE &amp; PRESENT",
        "External observation",
        "Human-reviewed evidence",
        "Governed evaluation",
        "Acceptance + current selection",
        "Advisory progression",
        "Governed read snapshot",
    ):
        assert phrase in strip

    assert 'height="260"' in strip
    assert "linearGradient" not in strip
    assert "zoom" not in strip.lower()
    assert "pan" not in strip.lower()
    assert strip.count("READ SNAPSHOT != CAPABILITY AUTHORITY != PERMISSION") == 1
    assert "COMPACT MENTAL MODEL" not in strip

    assert "!= CURRENT-STATE SELECTION AUTHORITY" in text
    assert "!= PROGRESSION AUTHORITY" in text
    assert "!= CAPABILITY UPDATE AUTHORITY" in text
    assert "!= PERMISSION OR PROFESSIONAL AUTHORITY" in text


def test_readme_license_history_wording_matches_public_license_history():
    text = README.read_text(encoding="utf-8")

    assert "Earlier versions were previously distributed under Apache-2.0." in text
    assert "remain in force for those copies" in text
    assert "docs/project/license-history.md" in text
    assert "exact final Apache checkpoint" not in text
    assert "exact Apache checkpoint" not in text


def test_issue_forms_exist_and_keep_sensitive_reports_out_of_public_issues():
    config = (ISSUE_TEMPLATE / "config.yml").read_text(encoding="utf-8")
    bug = (ISSUE_TEMPLATE / "bug.yml").read_text(encoding="utf-8")
    docs = (ISSUE_TEMPLATE / "documentation.yml").read_text(encoding="utf-8")
    research = (ISSUE_TEMPLATE / "research.yml").read_text(encoding="utf-8")

    assert "blank_issues_enabled: false" in config
    assert "/security/policy" in config
    assert "Do not include credentials" in bug
    assert "synthetic or non-sensitive data" in bug
    assert "private or sensitive payloads" in docs
    assert "substantive third-party authored material is not accepted for inclusion" in research
    assert "cannot be merged" in research
    assert "until that rights process is in place" in research
    assert "cannot be merged automatically" not in research
    assert "does not grant contributor or relicensing rights" in research
    assert "not a contributor-rights agreement" in research
    assert "private or sensitive payloads" in research
