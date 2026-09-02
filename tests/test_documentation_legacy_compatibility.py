from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEGACY_ROOT = ROOT / "docs" / "legacy" / "pr10_0"
BRIDGE_ROOT = LEGACY_ROOT / "docs"


def test_frozen_pr10_readme_remains_unmodified_by_compatibility_bridge():
    text = (LEGACY_ROOT / "README.md").read_text(encoding="utf-8")

    assert "The implemented foundation runs through **PR9" in text
    assert "](docs/constitution.md)" in text
    assert "PR12.15" not in text


def test_legacy_compatibility_routes_are_hidden_from_navigation_and_search():
    routes = tuple(BRIDGE_ROOT.rglob("*.md"))
    assert len(routes) == 24

    for route in routes:
        text = route.read_text(encoding="utf-8")
        assert "# Archived link compatibility route" in text
        assert "  - navigation" in text
        assert "  - toc" in text
        assert "search:\n  exclude: true" in text
        assert "frozen PR10.0 documentation snapshot" in text
