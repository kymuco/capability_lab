# Progression Frontier, Prerequisite Evidence Gap and Exploration Projection v1

Status: **PR8 implementation contract**

## Outcome

PR8 introduces Capability Lab's first deterministic person-scoped advisory progression projection. It composes explicitly selected governed capability-state dimensions, direct shared capability relations, explicit request-local focus, and explicit preserved exploration into inspectable frontier candidates, prerequisite evidence gaps, and exploration opportunities.

It does not infer goals, whole-person capability, readiness, priority, difficulty, optimal paths, safety, permission, professional authority, or human value.

```text
PROGRESSION FRONTIER != RECOMMENDATION
FRONTIER CANDIDATE != NEXT REQUIRED STEP
FRONTIER CANDIDATE != READINESS
FRONTIER CANDIDATE != PERMISSION
```

## Layer boundary

```text
CapabilityCatalog
      +
explicitly selected PersonalCapabilityState dimensions
      +
explicit ProgressionFocus
      +
explicit ExplorationInput
      |
      v
core:deterministic_progression_frontier@1
      |
      +--> FrontierCandidate
      +--> PrerequisiteEvidenceGap
      +--> ExplorationOpportunity
      |
      X
no claim/state/history/permission mutation
```

PR8 reads already-governed state representation. It may validate the selected state's exact PR1/PR2/PR3 basis, but it does not reinterpret raw evidence or create new personal capability state.

```text
PR8 READS GOVERNED STATE
PR8 DOES NOT RE-EVALUATE RAW EVIDENCE
PR8 DOES NOT DERIVE PERSONAL CAPABILITY STATE
```

## Explicit state selection

A `FrontierSeedBinding` identifies one exact `PersonalCapabilityStateId` and one or more explicit dimension keys. Every selected dimension must be `SUPPORTED` in that exact state.

The binding does not aggregate the state into a whole-capability truth.

```text
FRONTIER SEED BINDING != WHOLE-CAPABILITY SUPPORT
SUPPORTED DIMENSION != SUPPORTED PERSON
SEED DIMENSION SELECTION != TRUTH
SEED DIMENSION SELECTION != AUTHORITY
```

`SUPPORTED + UNRESOLVED` remains selectable because support standing and conflict are independent PR3 axes. The exact source state remains inspectable and preserves its conflict status.

No latest-state rule exists. Only states referenced by the request are allowed to influence the baseline; unselected state records are inert.

```text
UNSELECTED STATE != FRONTIER INPUT
LATEST STATE != AUTOMATIC FRONTIER INPUT
```

## Direct one-hop frontier semantics

Baseline v1 uses only direct relations. It does not perform path search, transitive closure, shortest-path analysis, centrality analysis, or curriculum optimization.

For a selected seed capability `S`, a capability `C` may enter the frontier when the accepted catalog contains a direct relation whose source is `C`, target is `S`, and kind is one of:

```text
C SPECIALIZES S
C REQUIRES S
C SUPPORTED_BY S
C ENABLED_BY S
```

This follows PR1's dependency orientation: the source is the capability being described and the target is its prerequisite/supporting/enabling capability.

`OVERLAPS` and empirical-development relations do not produce baseline-v1 frontier adjacency.

```text
DIRECT RELATION != OPTIMAL PATH
ONE-HOP FRONTIER != CURRICULUM
PATH LENGTH != DIFFICULTY
SPECIALIZES != HARDER
SPECIALIZES != NEXT LEVEL
```

Each adjacency preserves a `ProgressionRelationWitness` with exact concept revisions and the direct relation's kind, scope, and strength. A witness is audit material, not a new accepted `CapabilityRelation`.

Multiple witnesses explain why a candidate is visible; they are not votes or weights.

```text
MULTIPLE ADJACENCY WITNESSES != HIGHER PRIORITY
RELATION STRENGTH != FRONTIER PRIORITY
RELATION STRENGTH != DIFFICULTY
```

## Explicit focus

A `ProgressionFocus` is request-local advisory input. It may make a concept visible as a frontier candidate even when there is no direct adjacency from a selected seed.

It is intentionally not a durable goal, interest, identity attribute, or permission record.

```text
PROGRESSION FOCUS != GOAL
PROGRESSION FOCUS != INTEREST
PROGRESSION FOCUS != IDENTITY
PROGRESSION FOCUS != PERMISSION
MODEL-SUPPLIED FOCUS != SUBJECT GOAL
```

`ProgressionRequesterRef` records whether the caller supplied the focus through a human, rule, model, hybrid, or external-system mechanism. Requester identity does not confer authority or subject endorsement.

## Prerequisite evidence gaps

Only direct categorical `REQUIRES` relations may produce `PrerequisiteEvidenceGap` records.

```text
SUPPORTED_BY != REQUIRES
STRONG SUPPORTED_BY != PREREQUISITE
ENABLED_BY != PREREQUISITE
SPECIALIZES != PREREQUISITE
```

PR8 never infers a competence dimension from `RelationScope.key`. Relation scopes remain PR1 relation-local semantics.

A `PrerequisiteCheckBinding` explicitly binds one exact candidate→prerequisite `REQUIRES` relation to:

- one exact competence frame;
- one or more required frame-local dimension keys;
- optionally one explicitly selected prerequisite state.

```text
RELATION SCOPE != COMPETENCE DIMENSION
SCOPE-DIMENSION BINDING != GLOBAL MAPPING
SCOPE-DIMENSION BINDING != SUPPORT
```

The absence of a binding does not mean the prerequisite is satisfied. It remains explicitly `unassessed` on the frontier candidate.

An explicit binding whose `state_id=None` means the caller chose a scope/dimension interpretation but supplied no prerequisite state. The corresponding dimensions produce `NO_SELECTED_STATE` gaps.

These are intentionally distinct cases:

```text
NO BINDING
    -> UNASSESSED PREREQUISITE

EXPLICIT BINDING + NO STATE
    -> NO_SELECTED_STATE GAP

UNASSESSED PREREQUISITE != SATISFIED PREREQUISITE
NO GAP OUTPUT != NO GAP
```

When an exact prerequisite state is supplied:

- `SUPPORTED` dimension → no gap for that dimension;
- `UNKNOWN` dimension → `UNKNOWN` evidence gap;
- `INSUFFICIENT` dimension → `INSUFFICIENT` evidence gap.

State conflict remains separately inspectable and is preserved on state-backed gap dimensions where a gap exists.

A gap describes missing represented governed support under the explicit binding. It does not assert absence of the underlying human capability.

```text
PREREQUISITE EVIDENCE GAP != MISSING CAPABILITY
UNKNOWN != MISSING CAPABILITY
INSUFFICIENT != LOW CAPABILITY
```

A gap never removes the candidate from the frontier and never becomes access control.

```text
PREREQUISITE GAP != PROHIBITION
PREREQUISITE GAP != ACCESS CONTROL
PREREQUISITE GAP != CANNOT ATTEMPT
NO GAP != READY
NO GAP != SAFE
NO GAP != PERMITTED
```

## Exploration

PR8 v1 preserves explicitly supplied exploration opportunities. It does not automatically manufacture exploration by graph distance, low connectivity, novelty, or inferred personality.

```text
EXPLORATION PRESERVATION != AUTOMATIC EXPLORATION GENERATION
ABSENCE OF GRAPH EDGE != SEMANTIC UNRELATEDNESS
EXPLORATION OPPORTUNITY != RECOMMENDATION
```

An `ExplorationInput` must remain distinct from the selected seed concepts, explicit focus concepts, and derived frontier candidates in the same run. This keeps the exploration channel visibly separate from the inferred frontier.

A model may supply an exploration input, but model origin does not make it the subject's interest.

```text
MODEL EXPLORATION != SUBJECT INTEREST
MODEL EXPLORATION != AUTHORITY
```

## History, Legend and proposal separation

PR7 history and Legend records are deliberately absent from the PR8 derivation input. Historical accomplishment does not automatically establish current readiness, and selective narrative must not become a future-opportunity filter.

```text
ACHIEVEMENT != CURRENT READINESS
LEGEND != FRONTIER INPUT
LEGEND != GOAL
LEGEND != RECOMMENDATION BASIS
```

Likewise, PR6 candidate semantics do not enter the frontier. Only accepted `CapabilityCatalog` concepts and relations participate.

```text
PROPOSAL != ACCEPTED FRONTIER SEMANTICS
```

## Time boundary

`ProgressionFrontierRequest.as_of` is the represented subject-state boundary; `generated_at` is when the projection is produced.

```text
as_of <= generated_at
selected_state.as_of <= frontier.as_of
selected_state.derived_at <= frontier.generated_at
```

Historical projection is therefore possible with an explicitly selected older state. PR8 does not apply recency decay or prefer newer states automatically.

The supplied current `CapabilityCatalog` / `CompetenceFrameCatalog` are exact validation inputs. `as_of` does not prove that those semantic snapshots were the historically authoritative snapshots at that time.

```text
HISTORICAL FRONTIER as_of != PROOF OF HISTORICAL CATALOG CONTENT
```

A future durable semantic archive may provide stronger historical-snapshot authenticity.

## Determinism and ordering

The baseline has fixed declared identities:

```text
policy  = core:deterministic_progression_frontier@1
deriver = rule:capability_lab:deterministic_progression_frontier_v1
```

Caller-supplied collection order is canonicalized. Frontier candidates, gaps, and exploration opportunities serialize deterministically.

Canonical order is not recommendation order.

```text
INPUT ORDER != PRIORITY
FRONTIER ORDER != PRIORITY
FIRST ITEM != BEST ITEM
```

PR8 contains no score, rank, distance, difficulty, utility, probability, success estimate, urgency, or global human level.

## Audit reconstruction

`ProgressionFrontier` preserves the effective request inputs used by the baseline:

- requester ref;
- explicit focuses;
- selected seed bindings;
- prerequisite bindings;
- explicit exploration inputs.

This makes the output reconstructible without hidden latest-state, goal-inference, or ranking behavior.

```text
EFFECTIVE PROGRESSION INPUT MUST REMAIN AUDIT-RECONSTRUCTIBLE
```

## Serialization and persistence boundary

`ProgressionFrontierRequest`, `ProgressionFrontier`, and `ProgressionFrontierSet` use strict deterministic schema-v1 JSON with duplicate-key rejection and one explicit extended ISO-8601 timestamp profile.

Serialization does not imply recommendation authority, publication, acceptance, consent, or persistent canonical status.

```text
REQUESTER != AUTHORITY
DERIVER != AUTHORITY
POLICY REF != AUTHENTICATED POLICY
FRONTIER ID != CONTENT HASH
SNAPSHOT-LOCAL UNIQUENESS != GLOBAL UNIQUENESS
SERIALIZED FRONTIER != PUBLISHED FRONTIER
```

Multiple alternative frontiers for one subject may coexist. PR8 defines no canonical frontier and no latest-frontier-wins rule.

## Non-goals

PR8 v1 does not implement:

- a path optimizer, shortest-path engine, curriculum planner, or transitive prerequisite closure;
- ranking, scoring, priority, difficulty, distance, readiness, expected utility, or success probability;
- automatic latest-state selection or recency weighting;
- automatic goal/interest inference;
- model/LLM runtime;
- automatic exploration generation from graph geometry;
- history/achievement/Legend-based priority boosts;
- proposal materialization;
- challenge/task generation;
- professional safety, licensing, permission, or authority inference;
- persistence/synchronization/global ID governance;
- Player Window UI.

## Normative invariants

```text
PROGRESSION FRONTIER != RECOMMENDATION
FRONTIER CANDIDATE != NEXT REQUIRED STEP
FRONTIER CANDIDATE != READINESS
FRONTIER CANDIDATE != PERMISSION

PR8 READS GOVERNED STATE
PR8 DOES NOT RE-EVALUATE RAW EVIDENCE
PR8 DOES NOT DERIVE PERSONAL CAPABILITY STATE

UNSELECTED STATE != FRONTIER INPUT
LATEST STATE != AUTOMATIC FRONTIER INPUT
FRONTIER SEED BINDING != WHOLE-CAPABILITY SUPPORT
SUPPORTED DIMENSION != SUPPORTED PERSON

DIRECT RELATION != OPTIMAL PATH
ONE-HOP FRONTIER != CURRICULUM
PATH LENGTH != DIFFICULTY

SUPPORTED_BY != REQUIRES
STRONG SUPPORTED_BY != PREREQUISITE
ENABLED_BY != PREREQUISITE
RELATION SCOPE != COMPETENCE DIMENSION
SCOPE-DIMENSION BINDING != GLOBAL MAPPING

PREREQUISITE EVIDENCE GAP != MISSING CAPABILITY
UNKNOWN != MISSING CAPABILITY
INSUFFICIENT != LOW CAPABILITY
UNASSESSED PREREQUISITE != SATISFIED PREREQUISITE
PREREQUISITE GAP != PROHIBITION
NO GAP != READY
NO GAP != SAFE
NO GAP != PERMITTED

MULTIPLE ADJACENCY WITNESSES != HIGHER PRIORITY
RELATION STRENGTH != FRONTIER PRIORITY
FRONTIER ORDER != PRIORITY

PROGRESSION FOCUS != GOAL
PROGRESSION FOCUS != IDENTITY
MODEL-SUPPLIED FOCUS != SUBJECT GOAL

EXPLORATION OPPORTUNITY != RECOMMENDATION
EXPLORATION PRESERVATION != AUTOMATIC EXPLORATION GENERATION

ACHIEVEMENT != CURRENT READINESS
LEGEND != FRONTIER INPUT
PROPOSAL != ACCEPTED FRONTIER SEMANTICS

REQUESTER != AUTHORITY
DERIVER != AUTHORITY
POLICY REF != AUTHENTICATED POLICY
SERIALIZED FRONTIER != PUBLISHED FRONTIER
```
