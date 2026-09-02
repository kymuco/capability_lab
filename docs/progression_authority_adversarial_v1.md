# PR8 progression-authority adversarial review v1

## Status

This supplement records the first adversarial authority review of PR8 — Progression Frontier, Prerequisite Evidence Gap and Exploration Projection v1.

The review attacks ways an advisory projection could be overread or forged into a recommendation, prerequisite truth, whole-person capability statement, readiness decision, ranking, or self-confirming development path.

## Central boundary

```text
COULD BE CONSIDERED != SHOULD DO
PROGRESSION FRONTIER != RECOMMENDATION
```

## Blocker 1 — structurally valid frontier could be forged independently of its stored effective inputs

Initial PR8 strict serialization guaranteed schema validity and deterministic roundtrip, but a caller could deserialize a structurally valid `ProgressionFrontier` whose stored focuses/seed bindings/prerequisite bindings/exploration inputs looked plausible while candidates, gaps, witnesses, policy, deriver, or rationale had been changed.

That made this implication invalid:

```text
DESERIALIZED FRONTIER
    ->
ACTUALLY PRODUCED BY deterministic_progression_frontier_v1
```

### Repair

PR8 now exposes `validate_progression_frontier_v1(...)`.

The verifier:

1. reconstructs an exact `ProgressionFrontierRequest` from the frontier's stored effective inputs;
2. re-runs `derive_progression_frontier_v1(...)` against the supplied capability catalog, frame catalog, epistemic snapshot, and state snapshot;
3. requires exact equality between the re-derived frontier and the supplied frontier;
4. contains lower-layer validation failures inside the `InvalidProgressionFrontier` verification error domain.

Therefore:

```text
STRUCTURALLY VALID FRONTIER != VERIFIED DERIVATION
DESERIALIZED FRONTIER != VERIFIED DERIVATION
SERIALIZED FRONTIER != VERIFIED DERIVATION

VERIFIED PR8 FRONTIER
    =
EXACT RE-DERIVATION FROM STORED EFFECTIVE INPUTS
AND SUPPLIED SOURCE SNAPSHOTS
```

The verifier is deterministic source-backed validation, not a signature, content-address, issuer authentication service, acceptance workflow, or publication authority.

## Relation-direction inversion attack

Frozen PR1 dependency direction remains:

```text
source = capability being described
 target = dependency/supporting capability
```

For a selected supported seed `S`, PR8 may surface candidate `C` only when the direct accepted relation is oriented:

```text
C -> S
```

for one of the bounded adjacency kinds.

A dependency edge is not traversed in the opposite direction merely because the graph is connected.

```text
DEPENDENCY EDGE != UNDIRECTED PROGRESSION EDGE
RELATION DIRECTION != PRESENTATION DIRECTION
```

Executable regression uses the real Civilization Bootstrap relation:

```text
low_voltage_power_distribution
    REQUIRES
basic_electricity
```

and verifies that supported `basic_electricity` can surface `low_voltage_power_distribution`, not vice versa.

## `SUPPORTED_BY -> REQUIRES` laundering attack

`PrerequisiteCheckBinding` is only consumed while inspecting an actual accepted `REQUIRES` edge of an actual frontier candidate.

A caller cannot provide the endpoints/scope of a `SUPPORTED_BY` relation and thereby manufacture a `PrerequisiteEvidenceGap`.

```text
SUPPORTED_BY != REQUIRES
STRONG SUPPORTED_BY != REQUIRES
PREREQUISITE BINDING != RELATION-KIND OVERRIDE
```

A binding that does not correspond to a real `REQUIRES` edge of an actual frontier candidate fails closed as unused/invalid input.

## Whole-capability aggregation attack

A state may contain, for the same capability concept:

```text
conceptual_knowledge = SUPPORTED
calculation          = UNKNOWN
```

Selecting `conceptual_knowledge` as a frontier seed does not make `calculation` supported. Attempting to seed from the UNKNOWN dimension fails closed even though another dimension in the same state is supported.

```text
ONE SUPPORTED DIMENSION != WHOLE-CAPABILITY SUPPORT
SUPPORTED DIMENSION A != SUPPORTED DIMENSION B
FRONTIER SEED BINDING != CAPABILITY AGGREGATION
```

## Prerequisite-binding laundering boundary

PR8 deliberately does not infer a global mapping from `RelationScope` to competence dimensions.

A `PrerequisiteCheckBinding` explicitly states which exact frame and dimension keys a caller wants the deterministic projection to inspect for one exact `REQUIRES` relation.

The binding can be checked for structural and snapshot consistency, but PR8 v1 does not authenticate the semantic wisdom of that caller-selected mapping.

```text
RELATION SCOPE != COMPETENCE DIMENSION
PREREQUISITE BINDING != GLOBAL SEMANTIC MAPPING
PREREQUISITE BINDING != AUTHORITY
REQUESTER-SUPPLIED DIMENSION SET != UNIVERSAL PREREQUISITE TRUTH
```

This is why a resulting gap means only:

> under this explicit request-local binding, the selected governed state lacks represented support for one or more named dimensions.

It does not mean the person lacks the prerequisite capability.

## Gap-as-prohibition/readiness attack

PR8 exposes no fields or helpers for:

```text
ready
readiness
permitted
prohibited
can_attempt
must_not_attempt
```

A prerequisite evidence gap remains attached advisory information and does not remove the candidate.

```text
PREREQUISITE EVIDENCE GAP != MISSING CAPABILITY
PREREQUISITE EVIDENCE GAP != PROHIBITION
PREREQUISITE EVIDENCE GAP != ACCESS CONTROL
NO GAP != READY
NO GAP != SAFE
NO GAP != PERMITTED
```

## Hidden latest-state attack

Only exact state IDs named by `FrontierSeedBinding` or state-backed `PrerequisiteCheckBinding` are selected.

Unselected older/newer/stale states are inert even when present in the same `PersonalCapabilityStateSet`.

```text
LATEST STATE != AUTOMATIC FRONTIER INPUT
NEWEST STATE != AUTHORITY
UNSELECTED STATE != FRONTIER INPUT
```

PR8 v1 performs no recency weighting or newest-wins selection.

## Witness-count ranking attack

Multiple direct adjacency witnesses are preserved only as inspectable reasons why a candidate is present.

PR8 exposes no witness-count score, priority, rank, recommendation strength, distance, or utility value.

```text
MULTIPLE WITNESSES != HIGHER PRIORITY
WITNESS COUNT != RECOMMENDATION STRENGTH
RELATION STRENGTH != FRONTIER PRIORITY
CANONICAL ORDER != RANKING
```

## Exploration self-confirmation attack

`ExplorationInput` is explicit request input. PR8 does not accept a previous frontier, history, achievement record, or Legend as derivation input and does not automatically promote prior exploration into later focus or adjacency seeds.

An exploration-only request therefore produces exploration opportunities and no frontier candidates.

A caller may explicitly choose to submit the same concept again in a later request, but that is a new attributed input, not hidden feedback from PR8.

```text
EXPLORATION OPPORTUNITY != FUTURE SEED
EXPLORATION OPPORTUNITY != SUBJECT INTEREST
PREVIOUS FRONTIER != AUTOMATIC NEXT-FRONTIER INPUT
EXPLICIT RE-SUBMISSION != HIDDEN SELF-CONFIRMATION
```

## Model/requester non-authority

`ProgressionRequesterRef(kind=MODEL, ...)` records who supplied request-local focus/exploration assumptions. It does not change those assumptions into goals, interests, identity, or authority.

```text
MODEL-SUPPLIED FOCUS != SUBJECT GOAL
MODEL-SUPPLIED EXPLORATION != SUBJECT INTEREST
REQUESTER != AUTHORITY
DERIVER != AUTHORITY
```

## Frozen verification and persistence limits

```text
POLICY REF != AUTHENTICATED POLICY CONTENT
DERIVER REF != AUTHENTICATED GLOBAL IDENTITY
FRONTIER ID != CONTENT HASH
SNAPSHOT-LOCAL UNIQUENESS != GLOBAL UNIQUENESS
STRICT JSON != SOURCE AUTHENTICATION
VERIFIED DERIVATION != GOVERNANCE ACCEPTANCE
SERIALIZED FRONTIER != PUBLISHED FRONTIER
```

A future durable store may preserve source snapshot digests, signatures, policy content, or acceptance decisions under separate contracts. PR8 does not imply those guarantees.

## Non-goals of this review

This review does not add ranking, scoring, path search, semantic embeddings, LLM runtime, global scope-to-dimension mappings, recommendation authority, permission/safety inference, persistence, sync, signatures, content-addressed snapshots, Player Window presentation policy, or a generic recommender framework.
