from __future__ import annotations

from pathlib import Path
import re
import tomllib


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CONFIG = ROOT / "zensical.toml"
README = ROOT / "README.md"
CSS = DOCS / "stylesheets" / "capability.css"

EXPECTED_FEATURES = {
    "navigation.instant",
    "navigation.tracking",
    "navigation.sections",
    "navigation.path",
    "navigation.top",
    "navigation.footer",
    "toc.follow",
    "search.highlight",
    "content.code.copy",
    "content.tooltips",
}
EXPECTED_HOMEPAGE_PRIMITIVES = {
    "cl-hero",
    "cl-eyebrow",
    "cl-actions",
    "cl-proof",
    "cl-path-grid",
    "cl-path-card",
    "cl-equation",
    "cl-boundary",
}
CANONICAL_WRAPPERS = {
    DOCS / "project" / "commercial-licensing.md": '{{ include_contract("COMMERCIAL-LICENSING.md") }}',
    DOCS / "project" / "license-history.md": '{{ include_contract("LICENSE-HISTORY.md") }}',
    DOCS / "project" / "publication.md": '{{ include_contract("PUBLICATION.md") }}',
    DOCS / "security.md": '{{ include_contract("SECURITY.md") }}',
}


def _config() -> dict:
    return tomllib.loads(CONFIG.read_text(encoding="utf-8"))


def _nav_targets(value):
    if isinstance(value, str):
        yield value
        return
    if isinstance(value, list):
        for item in value:
            yield from _nav_targets(item)
        return
    if isinstance(value, dict):
        for item in value.values():
            yield from _nav_targets(item)


def test_documentation_site_configuration_is_public_checkpoint_contract():
    project = _config()["project"]

    assert project["site_name"] == "Capability Lab"
    assert project["site_url"] == "https://kymuco.github.io/capability_lab/"
    assert project["repo_url"] == "https://github.com/kymuco/capability_lab"
    assert project["docs_dir"] == "docs"
    assert project["site_dir"] == "site"
    assert project["strict"] is True
    assert project["extra_css"] == ["stylesheets/capability.css"]
    assert project["copyright"] == "Capability Lab · PolyForm Noncommercial 1.0.0"
    assert set(project["watch"]) == {
        "COMMERCIAL-LICENSING.md",
        "LICENSE-HISTORY.md",
        "PUBLICATION.md",
        "SECURITY.md",
    }

    theme = project["theme"]
    assert theme["variant"] == "modern"
    assert theme["font"] is False
    assert set(theme["features"]) == EXPECTED_FEATURES


def test_documentation_dependencies_are_optional_and_pinned():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = pyproject["project"]

    assert project["dependencies"] == []
    assert project["optional-dependencies"]["docs"] == ["zensical==0.0.57"]
    assert "zensical" not in " ".join(project["optional-dependencies"]["dev"]).lower()


def test_every_navigation_target_exists_inside_docs_root():
    project = _config()["project"]
    targets = tuple(_nav_targets(project["nav"]))
    assert targets

    for target in targets:
        path = (DOCS / target).resolve()
        assert DOCS.resolve() in path.parents or path == DOCS.resolve()
        assert path.is_file(), target


def test_homepage_contains_intentional_documentation_product_primitives():
    homepage = (DOCS / "index.md").read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")

    for primitive in EXPECTED_HOMEPAGE_PRIMITIVES:
        assert primitive in homepage
        assert f".{primitive}" in css

    assert "Capability claims you can inspect." in homepage
    assert "product/read projection" in homepage
    assert "permission or authority" in homepage


def test_root_readme_is_a_front_door_not_pr_chronology():
    readme = README.read_text(encoding="utf-8")

    assert "https://kymuco.github.io/capability_lab/" in readme
    assert "Observation is not evidence." in readme
    assert "PolyForm Noncommercial License 1.0.0" in readme
    assert "COMMERCIAL-LICENSING.md" in readme
    assert "LICENSE-HISTORY.md" in readme
    assert "## Implemented sequence" not in readme
    assert readme.count("**PR12.") < 3


def test_root_contract_wrappers_remain_thin_and_canonical():
    macros = (ROOT / "docs_macros.py").read_text(encoding="utf-8")

    for path, expected in CANONICAL_WRAPPERS.items():
        contract_name = expected.split('"', 2)[1]
        assert f'"{contract_name}"' in macros
        assert path.read_text(encoding="utf-8").strip() == expected


def test_curated_portal_links_do_not_escape_docs_root():
    curated = (
        DOCS / "index.md",
        DOCS / "overview.md",
        DOCS / "governed-pipeline.md",
        DOCS / "consumer-boundary.md",
        DOCS / "reference" / "archive.md",
        DOCS / "STYLE.md",
    )
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")

    for source in curated:
        text = source.read_text(encoding="utf-8")
        for raw_target in link_pattern.findall(text):
            target = raw_target.split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            resolved = (source.parent / target).resolve()
            assert DOCS.resolve() in resolved.parents or resolved == DOCS.resolve(), (
                source,
                raw_target,
            )


def test_pages_workflow_builds_prs_and_deploys_only_main_pushes():
    workflow = (ROOT / ".github" / "workflows" / "docs.yml").read_text(encoding="utf-8")

    assert "pull_request:" in workflow
    assert "zensical build --clean --strict" in workflow
    assert "actions/checkout@v7" in workflow
    assert "actions/setup-python@v7" in workflow
    assert "actions/upload-pages-artifact@v5" in workflow
    assert "actions/configure-pages@v6" in workflow
    assert "actions/deploy-pages@v5" in workflow
    assert "github.event_name == 'push'" in workflow
    assert "refs/heads/main" in workflow
