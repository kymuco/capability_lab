# PR8 Second Adversarial Progression Review v1

## Purpose

This review attacks the deterministic PR8 progression projection after the first
progression-authority pass. The target is not recommendation quality. The target is
whether subtle snapshot, coverage, overlap, temporal, or witness semantics could make
an advisory projection look more authoritative or more complete than its inputs justify.

The reviewed baseline remains:

```text
explicit selected governed state dimensions
        +
direct accepted PR1 relations
        +
explicit request-local focus
        +
explicit prerequisite checks
        +
explicit exploration preservation
        ↓
ProgressionFrontier
```

The projection remains advisory:

```text
COULD BE CONSIDERED != SHOULD DO
```

## Finding 1 — focus/seed collapse

Before this pass, the same exact capability concept could be used both as an explicit
frontier seed and as an explicit focus. Because focus creates a `FrontierCandidate`,
a capability already serving as progression basis could reappear as projected frontier
output without any semantic change in level, scope, or capability identity.

That collapses two distinct roles:

```text
SEED BASIS != PROJECTED DIRECTION
```

### Repair

During source-backed derivation, exact focus concepts must remain distinct from exact
selected seed concepts.

```text
FOCUS == EXACT SEED CONCEPT -> REJECT
```

This does not infer a latest or preferred state. The caller still explicitly chooses the
single state to use as the seed for that concept.

A focus may still overlap a concept that independently appears as a direct adjacent
frontier candidate. In that case the candidate truthfully preserves both facts:

```text
explicit_focus = true
adjacency witness exists
```

but neither fact creates rank or priority.

## Finding 2 — repeated-state witness amplification

Before this pass, two different `PersonalCapabilityStateId` values for the same exact
capability concept could both be selected as frontier seeds. The same direct semantic
edge could then appear twice as adjacency provenance, differing only by state id.

That creates a presentation-amplification hazard even though PR8 has no numeric score.

### Repair

Within one progression request:

```text
ONE EXACT SEED CONCEPT -> AT MOST ONE SEED STATE
```

This is deliberately not a latest-state rule:

```text
AT MOST ONE != AUTOMATICALLY CHOOSE NEWEST
```

The caller must explicitly choose which state is the seed.

Distinct seed concepts may still independently produce multiple witnesses for one
candidate. Those are genuinely distinct semantic bases and remain inspectable
provenance, not ranking.

## Partial prerequisite-binding coverage

A candidate can have more than one categorical `REQUIRES` relation. A caller may
supply an explicit `PrerequisiteCheckBinding` for only a subset.

PR8 must preserve that distinction exactly:

```text
BOUND REQUIRES -> assessed_prerequisites
UNBOUND REQUIRES -> unassessed_prerequisites
```

A gap is derived only for an assessed relation whose requested dimensions are not
represented as supported under the selected state.

Therefore:

```text
NO GAP FOR UNASSESSED PREREQUISITE != SATISFIED
PARTIAL ASSESSMENT != COMPLETE PREREQUISITE COVERAGE
```

PR8 v1 intentionally has no `coverage_complete`, `all_prerequisites_satisfied`, or
similar authority-bearing convenience field.

## Conflict-bearing supported seeds

PR3 deliberately separates support standing from conflict status. A dimension can be:

```text
standing = SUPPORTED
conflict_status = UNRESOLVED
```

PR8 permits such a dimension as an explicit seed because the support-content standing
is still `SUPPORTED`. It does not silently resolve, penalize, rank, or suppress the
conflict.

The exact state id and selected dimension keys remain in the adjacency witness, and
source-backed verification requires the supplied PR3 state snapshot.

```text
SUPPORTED + UNRESOLVED != CONFLICT-FREE SUPPORT
UNRESOLVED CONFLICT != PRIORITY PENALTY
UNRESOLVED CONFLICT != AUTOMATIC SEED REJECTION
```

Any UI that needs to display the conflict must inspect the exact referenced state basis;
PR8 does not duplicate or reinterpret PR3 conflict semantics.

## Cross-snapshot semantic substitution

The first adversarial pass added exact source-backed re-derivation verification. That
proves that a frontier is consistent with the supplied semantic, epistemic, frame, and
state snapshots.

It does not authenticate where those snapshots came from.

Two independently supplied catalogs can contain the same exact concept refs and the
same relations while carrying materially different concept text under the same ref. If
the changed text does not alter the deterministic inputs used by the frontier algorithm,
the same frontier can re-derive against both snapshots.

This is an explicit limit:

```text
VERIFIED AGAINST SUPPLIED SNAPSHOT != AUTHENTICATED SOURCE SNAPSHOT
EXACT CONCEPT REF != CONTENT HASH
CATALOG JSON != SIGNATURE
CONSISTENCY != PROVENANCE AUTHENTICITY
```

PR8 does not add a local SHA field and call that authenticity. A future durable archive
may content-address exact snapshots, and a future governance layer may authenticate
publisher/issuer identity, but those are separate contracts.

## Historical `as_of` reconstruction limit

`ProgressionFrontier.as_of` bounds the selected personal state basis. It does not prove
that the supplied capability catalog or competence-frame catalog existed in exactly that
form at `as_of`.

A historical frontier can therefore be consistently reconstructed using a supplied
snapshot, but PR8 cannot claim:

> this was the exact shared semantic snapshot available at that historical time.

Without an archived authenticated snapshot contract:

```text
HISTORICAL FRONTIER as_of
!=
HISTORICAL CATALOG AUTHENTICITY
```

The same distinction applies to frame snapshots.

## Source-snapshot authenticity boundary of the verifier

`validate_progression_frontier_v1(...)` is a deterministic consistency verifier. It:

1. reconstructs the exact stored effective request;
2. validates selected source records/states against supplied snapshots;
3. reruns the frozen PR8 derivation;
4. requires exact equality with the supplied frontier.

It does not:

```text
authenticate catalog publisher
verify a digital signature
prove an archive timestamp
prove global snapshot identity
prove that same-ref content was never substituted
```

Accordingly:

```text
SOURCE-BACKED VERIFICATION != SOURCE AUTHENTICATION
```

## Additional invariants frozen by this pass

```text
SEED BASIS != PROJECTED DIRECTION
FOCUS == EXACT SEED CONCEPT -> REJECT
ONE EXACT SEED CONCEPT -> AT MOST ONE SEED STATE
AT MOST ONE SEED STATE != LATEST-STATE POLICY

PARTIAL PREREQUISITE ASSESSMENT != COMPLETE COVERAGE
UNASSESSED PREREQUISITE != SATISFIED PREREQUISITE
NO GAP != ALL PREREQUISITES SATISFIED

SUPPORTED + UNRESOLVED != CONFLICT-FREE SUPPORT
CONFLICT STATUS != FRONTIER PRIORITY

MULTIPLE DISTINCT SEMANTIC WITNESSES != HIGHER PRIORITY
REPEATED STATE IDENTITY != ADDITIONAL SEMANTIC SUPPORT

VERIFIER CONSISTENCY != SNAPSHOT AUTHENTICITY
EXACT REF != CONTENT HASH
HISTORICAL as_of != HISTORICAL CATALOG PROOF
```

## Non-goals preserved

This pass does not introduce:

- latest-state selection;
- recency weighting;
- witness scoring;
- prerequisite-completeness scoring;
- automatic conflict resolution;
- catalog or frame signatures;
- content-addressed persistence;
- historical semantic archive infrastructure;
- recommendation ranking;
- permission or safety inference;
- history/Legend feedback into progression.

## Adversarial regression surface

The executable review is primarily in:

```text
tests/progression/test_progression_second_adversarial_v1.py
```

It covers:

- exact focus/seed overlap rejection;
- repeated seed-state amplification rejection;
- partial `REQUIRES` binding with explicit unassessed remainder;
- `SUPPORTED + UNRESOLVED` seed semantics;
- legitimate focus plus adjacency on the same derived candidate;
- same-ref cross-snapshot semantic substitution as an explicit authenticity limit;
- historical `as_of` without false historical-catalog claims.
