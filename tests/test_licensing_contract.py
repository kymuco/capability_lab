from __future__ import annotations

from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]
LICENSE = ROOT / "LICENSE"
LICENSE_HISTORY = ROOT / "LICENSE-HISTORY.md"
COMMERCIAL = ROOT / "COMMERCIAL-LICENSING.md"
CONTRIBUTING = ROOT / "CONTRIBUTING.md"
PUBLICATION = ROOT / "PUBLICATION.md"
README = ROOT / "README.md"
PYPROJECT = ROOT / "pyproject.toml"
ZENSICAL = ROOT / "zensical.toml"

POLYFORM_ID = "PolyForm-Noncommercial-1.0.0"
POLYFORM_URL = "https://polyformproject.org/licenses/noncommercial/1.0.0"
PUBLIC_ROOT = "febe79f9630858c2e01e3ed57ae1bfd7736227ba"


def test_root_license_is_polyform_noncommercial_with_required_notice():
    text = LICENSE.read_text(encoding="utf-8")

    assert text.startswith("# PolyForm Noncommercial License 1.0.0\n")
    assert f"<{POLYFORM_URL}>" in text
    assert "## Noncommercial Purposes" in text
    assert "Any noncommercial purpose is a permitted purpose." in text
    assert "## Personal Uses" in text
    assert "## Noncommercial Organizations" in text
    assert "## Fair Use" in text
    assert "## No Other Rights" in text
    assert "Required Notice: Copyright 2026 Ikymuco" in text
    assert "Apache License\nVersion 2.0" not in text


def test_package_metadata_has_distinct_source_available_distribution_identity():
    pyproject = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    project = pyproject["project"]

    assert pyproject["build-system"]["requires"] == ["setuptools>=77.0.3"]
    assert project["version"] == "0.2.0.dev0"
    assert project["license"] == POLYFORM_ID
    assert project["license-files"] == ["LICENSE"]
    assert project["dependencies"] == []
    assert all(
        not classifier.startswith("License ::")
        for classifier in project["classifiers"]
    )


def test_commercial_rights_are_separate_without_size_threshold_or_fair_use_overreach():
    text = COMMERCIAL.read_text(encoding="utf-8")

    assert "separate written commercial license" in text
    assert "There is no automatic commercial-license exception" in text
    assert "company revenue" in text
    assert "employee or contractor count" in text
    assert "startup stage" in text
    assert "not automatic public grants" in text
    assert "does not itself grant commercial rights" in text
    assert "expressly preserves fair-use rights" in text
    assert "does not narrow fair use or other rights" in text


def test_license_history_is_public_facing_and_nonretroactive():
    text = LICENSE_HISTORY.read_text(encoding="utf-8")
    normalized = " ".join(text.split())

    assert "Earlier versions of Capability Lab were previously distributed" in text
    assert "Apache License 2.0" in text
    assert "remain in force for those copies" in text
    assert "current public lineage" in text.lower()
    assert POLYFORM_ID in text
    assert "do not extend to revisions first distributed" in normalized

    assert "private master" not in text.lower()
    assert "PR #28" not in text
    assert "future public" not in text.lower()


def test_publication_record_describes_the_current_clean_public_lineage():
    text = PUBLICATION.read_text(encoding="utf-8")

    assert "current **public source-available" in text
    assert "public Git history intentionally begins from a clean" in text
    assert "PUBLIC GIT HISTORY" in text
    assert "!= COMPLETE RESEARCH CHRONOLOGY" in text
    assert "HISTORICAL DOCUMENT REFERENCES" in text
    assert "!= PUBLISHED COMMIT ANCESTRY" in text
    assert "stable research-subsystem checkpoint" in text
    assert "SOURCE-AVAILABLE" in text
    assert "!= OSI OPEN SOURCE" in text

    assert "private master" not in text.lower()
    assert "future public" not in text.lower()
    assert "remains a separate release action" not in text


def test_publication_1_records_frozen_public_root_without_rewriting_license_history():
    text = PUBLICATION.read_text(encoding="utf-8")
    normalized = " ".join(text.split())

    assert "## PUBLICATION-1 release baseline" in text
    assert PUBLIC_ROOT in text
    assert "exactly one reachable Git root" in normalized
    assert "frozen root to have zero parents" in normalized
    assert "GitHub's noreply identity" in normalized
    assert "owner-authored commits after the root" in normalized
    assert "repository-integrity contract" in normalized
    assert "does not replace the software license" in normalized


def test_contributor_policy_does_not_treat_public_license_as_relicensing_authority():
    text = CONTRIBUTING.read_text(encoding="utf-8")

    assert "substantive third-party" in text
    assert "contributions are not accepted for inclusion" in text
    assert "substantive code," in text
    assert "tests, documentation, examples" in text
    assert "PolyForm Noncommercial license is itself a" in text
    assert "contributor agreement" in text
    assert "merged until the required contributor-rights terms are in place" in text
    assert "retained Git history" not in text


def test_public_front_doors_describe_current_source_available_model():
    readme = README.read_text(encoding="utf-8")
    zensical = tomllib.loads(ZENSICAL.read_text(encoding="utf-8"))["project"]

    assert "source-available" in readme.lower()
    assert "not OSI open source" in readme
    assert "COMMERCIAL-LICENSING.md" in readme
    assert "LICENSE-HISTORY.md" in readme
    assert zensical["copyright"] == "Capability Lab · PolyForm Noncommercial 1.0.0"
    assert "Commercial licensing" in str(zensical["nav"])
    assert "License history" in str(zensical["nav"])
