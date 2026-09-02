# Civilization Bootstrap Pilot 01 — Sampling / Selection / Cohort-Construction Lineage and Common-Origin Closure

Status: **PR10.1 adversarial closure**

This closure extends the sampling / selection / cohort-construction causal
family from exact identity to explicit ancestry/common-origin governance.

The previous selection boundary can reject:

```text
observation A -> selection identity X
observation B -> selection identity X
```

but cannot reject:

```text
observation A -> selection A
observation B -> selection B

A != B

BUT

A and B are aliases, derived cohorts, resamples, clones, or state
continuations of one bounded selection origin
```

Therefore:

```text
DISTINCT SELECTION REFS
!=
DISTINCT SELECTION ORIGINS
```

## Relation vocabulary

PR10.1 adds:

```text
PilotObservationSelectionRelationKind

ALIAS_OF
DERIVED_FROM
RESAMPLED_FROM
CLONED_FROM
STATE_CONTINUATION_OF
```

Semantics:

```text
ALIAS_OF
    symmetric

DERIVED_FROM
RESAMPLED_FROM
CLONED_FROM
STATE_CONTINUATION_OF
    downstream -> upstream
```

The following are deliberately **not** lineage relations:

```text
same population label
same cohort name
same sampling algorithm
same inclusion-rule definition
same recruitment method
same generic dataset name
same study family
same timestamp
same nominal experiment
```

Similarity of design is not explicit causal ancestry.

## Examples

### Derived cohorts from one sampling frame

```text
COHORT_CONSTRUCTION_STATE:A
    DERIVED_FROM
SAMPLING_FRAME_INSTANCE:root

COHORT_CONSTRUCTION_STATE:B
    DERIVED_FROM
SAMPLING_FRAME_INSTANCE:root
```

The two observations converge on the same selection origin and are rejected.

### Two resampling draws from one bounded draw origin

```text
RESAMPLING_DRAW:A
    RESAMPLED_FROM
COHORT_CONSTRUCTION_STATE:root

RESAMPLING_DRAW:B
    RESAMPLED_FROM
COHORT_CONSTRUCTION_STATE:root
```

Again:

```text
A != B
```

but their upstream selection closure intersects, so structural separation fails.

### Alias

```text
RECRUITMENT_BATCH:batch_public
    ALIAS_OF
RECRUITMENT_BATCH:batch_internal
```

Two observations carrying those two refs are not two independent selection
origins.

### State continuation

```text
COHORT_CONSTRUCTION_STATE:session_02
    STATE_CONTINUATION_OF
COHORT_CONSTRUCTION_STATE:session_01
```

A new opaque identifier does not erase causal continuity.

## Graph model

PR10.1 adds:

```text
PilotObservationSelectionRelation
PilotObservationSelectionLineageGraph
```

The graph is private causal-governance metadata.

It does not modify:

```text
PilotCaptureRecord
EvidenceRecord
CapabilityClaim
Evaluation
PR3 capability state
Achievement
Progression
Player Window
```

`ALIAS_OF` classes are contracted before directed-cycle validation.

The graph rejects:

```text
self relations
exact duplicate relations
reverse duplicate aliases
conflicting directed relation kinds
directed edges inside one alias class
directed cycles
cycles revealed only after alias contraction
```

This prevents malformed lineage declarations from silently creating ambiguous
closure semantics.

## Upstream-only closure

PR10.1 adds:

```text
pilot_observation_selection_lineage_closure_keys_v1(...)
```

For one selection identity the closure contains:

```text
the identity itself
all aliases
all explicitly reachable upstream ancestors
all transitive upstream ancestors
```

Directed relations are never traversed downstream.

For:

```text
draw
  RESAMPLED_FROM
cohort
  DERIVED_FROM
frame
```

closure(draw) contains:

```text
draw
cohort
frame
```

but closure(frame) does not contain `cohort` or `draw`.

This is important because lineage denotes known origin dependence, not generic
graph connectedness.

## Cross-kind ancestry is allowed

A selection process can legitimately cross identity kinds:

```text
RESAMPLING_DRAW
    RESAMPLED_FROM
COHORT_CONSTRUCTION_STATE
    DERIVED_FROM
SAMPLING_FRAME_INSTANCE
```

Dependence is causal, not restricted to matching enum kinds.

## Per-observation union

One observation may declare multiple selection identities.

Their lineage closures are unioned before cross-observation comparison.

Therefore aliases or related refs **within one observation** do not manufacture
a false self-collision.

The reject condition is intersection between different observations.

## Strongest gate

The new strongest gate is:

```text
validate_pilot_materialized_evidence_selection_ancestry_preconditions_v1(...)
```

It first requires:

```text
validate_pilot_materialized_evidence_shared_selection_preconditions_v1(...)
```

That prior gate already composes the full lower ladder:

```text
exact capture dependence
session dependence
elicitation dependence

source identity
source ancestry
reviewed source completeness

mechanism identity
mechanism ancestry
reviewed mechanism completeness

coordination identity
coordination ancestry
reviewed coordination completeness

temporal identity
temporal ancestry
reviewed temporal completeness

allocation identity
allocation ancestry
reviewed allocation completeness

selection exact identity
```

Only then does selection ancestry/common-origin analysis run.

Therefore:

```text
SELECTION SEPARATION
!=
PERMISSION TO IGNORE LOWER-LAYER DEPENDENCE
```

## Structural rejection

For each observation, PR10.1 computes the union of all declared selection
lineage closure keys.

If two observations intersect on any key:

```text
observation A closure ∩ observation B closure != empty
```

then:

```text
selection-ancestry precondition -> REJECT
```

The diagnostic uses the privacy-reducing hashed selection key rather than
echoing raw selection refs.

## Empty graph semantics

```text
PilotObservationSelectionLineageGraph()
```

means only:

```text
NO SELECTION LINEAGE RELATIONS WERE SUPPLIED
```

It does **not** mean:

```text
NO SELECTION LINEAGE EXISTS
NO SHARED COHORT ORIGIN EXISTS
NO RESAMPLING DEPENDENCE EXISTS
INDEPENDENT RECRUITMENT
INDEPENDENT SAMPLING
```

That unresolved completeness problem belongs to the next governance layer.

## Conservative PASS semantics

Passing the new gate means only:

```text
all prior reviewed structural/governance gates passed
+
no exact selection identity was shared
+
the supplied selection lineage graph exposed no common alias/upstream origin
```

It does not establish:

```text
complete selection provenance
independent sampling
independent recruitment
non-overlapping subjects
independent cohorts
independent bootstrap draws
statistical independence
exchangeability
absence of selection bias
independent replication
```

And it does not authorize:

```text
CapabilityClaim creation
Evaluation
PR3 state update
achievement unlock
progression update
Player Window change
independent evidence weighting
```

Therefore:

```text
SELECTION-ANCESTRY PRECONDITION PASS
!=
INDEPENDENT REPLICATION
```

## Resulting causal ladder

After this closure:

```text
SOURCE
  identity -> ancestry -> reviewed bounded completeness

MECHANISM
  identity -> ancestry -> reviewed bounded completeness

COORDINATION / CONTROL
  identity -> ancestry -> reviewed bounded completeness

TEMPORAL / INTERVENTION / CARRYOVER
  identity -> ancestry -> reviewed bounded completeness

ALLOCATION / ASSIGNMENT / RANDOMIZATION
  identity -> ancestry -> reviewed bounded completeness

SAMPLING / SELECTION / COHORT CONSTRUCTION
  identity -> ancestry
```

The remaining selection-family gap is bounded reviewed completeness.

## New invariants

```text
DIFFERENT SELECTION REFS
!=
DIFFERENT SELECTION ORIGINS

NEW COHORT ID
!=
NEW COHORT ORIGIN

NEW RESAMPLING DRAW ID
!=
INDEPENDENT RESAMPLING ORIGIN

NEW RECRUITMENT BATCH ID
!=
INDEPENDENT RECRUITMENT ORIGIN

ALIAS / DERIVATION / RESAMPLING / CLONE / STATE CONTINUATION
=> KNOWN DECLARED SELECTION DEPENDENCE

SAME POPULATION LABEL
!=
SELECTION LINEAGE

SAME SAMPLING ALGORITHM
!=
SELECTION LINEAGE

EMPTY SELECTION GRAPH
!=
COMPLETE SELECTION GRAPH

PASS
!=
STATISTICAL INDEPENDENCE

PASS
!=
AUTHORITY TO CLAIM INDEPENDENT REPLICATION
```

## Non-goals

This closure does not add:

```text
automatic cohort-overlap discovery
subject identity matching
heuristic inference from population labels
heuristic inference from dataset names
sampling-bias estimation
exchangeability proofs
bootstrap independence tests
causal effect estimation
reviewer authentication
signatures
evidence weighting
CapabilityClaim support
Evaluation
PR3 state derivation
achievements
progression
Player Window behavior
```

## Next boundary

The next layer should complete this sixth causal family with:

**Reviewed Selection Declaration Completeness, Selection Lineage Graph
Completeness and Hidden Selection-Origin Uncertainty Closure**

It should preserve the same three-way distinction:

```text
KNOWN COMMON SELECTION ORIGIN
    -> structural REJECT

UNKNOWN / INCOMPLETE SELECTION COVERAGE
    -> governance REJECT

REVIEWED COMPLETE_FOR_SCOPE
+ no declared selection convergence
    -> bounded selection-origin precondition PASS
```

That future PASS must still remain weaker than statistical independence or
independent replication.
