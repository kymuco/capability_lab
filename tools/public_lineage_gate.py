from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass


EXPECTED_ROOT = "febe79f9630858c2e01e3ed57ae1bfd7736227ba"
NOREPLY_SUFFIX = "@users.noreply.github.com"
OWNER_NAMES = frozenset({"kymuco", "ikymuco"})


@dataclass(frozen=True)
class LineageFacts:
    roots: tuple[str, ...]
    root_parents: tuple[str, ...]
    author_email: str
    committer_email: str
    owner_identity_violations: tuple[str, ...] = ()


def _git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _owner_identity_violations() -> tuple[str, ...]:
    output = _git(
        "log",
        "--format=%H%x09%an%x09%ae%x09%cn%x09%ce",
        f"{EXPECTED_ROOT}..HEAD",
    )
    violations: list[str] = []

    for line in output.splitlines():
        if not line.strip():
            continue
        sha, author_name, author_email, committer_name, committer_email = line.split(
            "\t", 4
        )
        identities = (
            ("author", author_name, author_email),
            ("committer", committer_name, committer_email),
        )
        for role, name, email in identities:
            if name.casefold() in OWNER_NAMES and not email.endswith(NOREPLY_SUFFIX):
                # Deliberately do not echo the non-noreply address into CI logs.
                violations.append(f"{sha}:{role}:{name}")

    return tuple(violations)


def collect_lineage_facts() -> LineageFacts:
    roots = tuple(
        line.strip()
        for line in _git("rev-list", "--max-parents=0", "HEAD").splitlines()
        if line.strip()
    )
    root_parents = tuple(
        value
        for value in _git("show", "-s", "--format=%P", EXPECTED_ROOT).split()
        if value
    )
    author_email = _git("show", "-s", "--format=%ae", EXPECTED_ROOT)
    committer_email = _git("show", "-s", "--format=%ce", EXPECTED_ROOT)
    return LineageFacts(
        roots=roots,
        root_parents=root_parents,
        author_email=author_email,
        committer_email=committer_email,
        owner_identity_violations=_owner_identity_violations(),
    )


def evaluate_lineage(facts: LineageFacts) -> tuple[str, ...]:
    failures: list[str] = []

    if facts.roots != (EXPECTED_ROOT,):
        failures.append(
            "public lineage must have exactly one root and it must equal "
            f"{EXPECTED_ROOT}; observed={facts.roots!r}"
        )
    if facts.root_parents:
        failures.append(
            "frozen public root must have zero parents; "
            f"observed={facts.root_parents!r}"
        )
    if not facts.author_email.endswith(NOREPLY_SUFFIX):
        failures.append("public root author email must use GitHub noreply identity")
    if not facts.committer_email.endswith(NOREPLY_SUFFIX):
        failures.append("public root committer email must use GitHub noreply identity")
    if facts.owner_identity_violations:
        failures.append(
            "owner-authored public-lineage commits must use GitHub noreply identity; "
            f"violations={facts.owner_identity_violations!r}"
        )

    return tuple(failures)


def main() -> int:
    facts = collect_lineage_facts()
    failures = evaluate_lineage(facts)
    payload = {
        "ok": not failures,
        "expected_root": EXPECTED_ROOT,
        "observed_roots": list(facts.roots),
        "root_parent_count": len(facts.root_parents),
        "root_author_noreply": facts.author_email.endswith(NOREPLY_SUFFIX),
        "root_committer_noreply": facts.committer_email.endswith(NOREPLY_SUFFIX),
        "owner_identity_violation_count": len(facts.owner_identity_violations),
        "failures": list(failures),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
