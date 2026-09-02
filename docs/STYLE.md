# Capability Lab documentation standard

Capability Lab documentation is part of the system's governance surface. A page that blurs evidence,
state, advice, authority, or licensing can misrepresent the software even when the code is correct.

The documentation product therefore optimizes for **precision first, then progressive disclosure**.

## The first 30 seconds

A reader arriving at a top-level page should quickly be able to answer:

1. What is this part of Capability Lab for?
2. What does it accept or derive?
3. What does it explicitly *not* authorize?
4. Where is the exact normative or executable proof?

Do not lead a public-facing page with PR chronology when a task or concept can orient the reader faster.

## Progressive disclosure

Use this order where practical:

```text
purpose
→ mental model
→ happy-path flow
→ authority / failure boundaries
→ exact contracts
→ historical detail
```

Deep PR-specific documents may remain exhaustive. Curated portal pages should route readers into that depth
rather than duplicating every invariant.

## Put boundaries beside claims

When documentation says that a layer can derive, select, project, recommend, expose, or license something,
place the nearest important non-authority or non-license statement in the same section.

Examples:

```text
SUPPORTED != MASTERY
CURRENT != PERMISSION
progression = advisory
product/read snapshot != write-back authority
serialized artifact != live authority
public source access != commercial-use permission
current license != retroactive rewrite of historical grants
```

Do not hide these distinctions in a distant disclaimer.

## Canonical sources stay canonical

The curated portal must not create competing versions of normative contracts.

- `docs/constitution.md`, `docs/architecture.md`, and `docs/vocabulary.md` remain canonical foundations.
- PR-specific contract documents remain the detailed history and source of exact semantics.
- root `SECURITY.md`, `PUBLICATION.md`, `COMMERCIAL-LICENSING.md`, and `LICENSE-HISTORY.md` remain canonical project records; docs wrappers include them rather than copying them.
- root `LICENSE` remains the canonical current software-license text and is not duplicated into a curated docs page.
- executable integration tests remain the strongest evidence that architecture layers actually compose.
- executable licensing/documentation contract tests guard repository-facing metadata and canonical wrappers; they do not replace legal review of license terms.

## Writing style

Prefer:

- short declarative sentences;
- exact names after a plain-language introduction;
- diagrams for flow, not decoration;
- tables only when dimensions genuinely compare;
- examples that preserve governance semantics;
- explicit failure behavior where it matters.

Avoid:

- universal human rankings;
- anthropomorphic certainty about what a person "is";
- marketing superlatives unsupported by executable behavior;
- using "current", "accepted", "supported", "verified", or "authorized" interchangeably;
- paraphrasing a software license in a way that silently creates broader or narrower rights;
- decorative complexity that competes with the contract.

## Visual language

The site uses system fonts, restrained accent color, generous whitespace, and strong hierarchy.
Light and dark modes are equal first-class surfaces.

Custom visual primitives should remain semantic:

- `.cl-hero` — one-page value proposition;
- `.cl-proof` — compact invariant/proof strip;
- `.cl-path-grid` / `.cl-path-card` — task routing;
- `.cl-equation` — layer-separation statements;
- `.cl-boundary` — authority or safety boundary.

Any new primitive must work on narrow screens and preserve keyboard focus visibility.

## Quality gate

Documentation changes should pass:

```bash
python -m pip install -e ".[dev,docs]"
zensical build --clean --strict
python -m pytest -q
```

Broken internal links, invalid navigation targets, stale canonical wrappers, missing visual primitives,
misleading current-license language, or a docs dependency leaking into runtime dependencies are release-blocking documentation defects.
