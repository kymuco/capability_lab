from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
ISSUE_TEMPLATE = ROOT / ".github" / "ISSUE_TEMPLATE"


def test_readme_has_compact_modern_public_front_door():
    text = README.read_text(encoding="utf-8")

    assert "**Evidence-grounded capability modeling under explicit governance boundaries.**" in text
    assert "actions/workflows/ci.yml/badge.svg" in text
    assert "actions/workflows/docs.yml/badge.svg" in text
    assert "Python-3.11%2B" in text
    assert "PolyForm%20Noncommercial" in text
    assert "stable research subsystem" in text
    assert "development is demand-driven" in text
    assert "Observation is not evidence." in text


def test_readme_architecture_visual_preserves_governed_boundaries():
    text = README.read_text(encoding="utf-8")

    assert "```mermaid" in text
    assert 'H["Human review"]' in text
    assert 'E["Neutral evidence"]' in text
    assert 'A["Explicit acceptance"]' in text
    assert 'S["Current-state selection"]' in text
    assert 'G["Advisory progression + current profile"]' in text
    assert 'R["Governed product/read snapshot"]' in text

    assert "!= CURRENT-STATE SELECTION AUTHORITY" in text
    assert "!= PROGRESSION AUTHORITY" in text
    assert "!= CAPABILITY UPDATE AUTHORITY" in text
    assert "!= PERMISSION OR PROFESSIONAL AUTHORITY" in text


def test_readme_license_history_wording_matches_public_license_history():
    text = README.read_text(encoding="utf-8")

    assert "Earlier versions were previously distributed under Apache-2.0." in text
    assert "remain in force for those copies" in text
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
