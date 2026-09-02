# Civilization Bootstrap Pilot 01 — Temporal / Intervention / Carryover Lineage and Common-Origin Closure

Status: **PR10.1 adversarial closure**

The exact temporal-dependence layer can already reject:

```text
observation A -> intervention episode X
observation B -> intervention episode X
```

It also recognizes exact shared:

```text
ADAPTIVE_STATE
CARRYOVER_STATE
EXPOSURE_EPISODE
HISTORY_STATE
```

That is still insufficient when exact refs differ but share one declared causal origin.

Example:

```text
observation A -> adaptive_state:A
observation B -> carryover_state:B

A != B

BUT

adaptive_state:A DERIVED_FROM intervention_root:X
carryover_state:B STATE_CONTINUATION_OF intervention_root:X
```

Therefore:

```text
DIFFERENT TEMPORAL REFS
!=
DIFFERENT TEMPORAL / INTERVENTION ORIGINS
```

## Separate causal layer

This layer remains separate from source, mechanism, and coordination provenance.

```text
SOURCE
    input/provenance origin

MECHANISM
    acquisition/production origin

COORDINATION
    cross-observation selection/control origin

TEMPORAL / INTERVENTION
    causal episode/state/history/carryover origin
```

A pair of observations may pass every reviewed source/mechanism/coordination gate and still inherit dependence from one intervention or adaptive-history chain.

## Explicit temporal lineage relations

PR10.1 adds:

```text
PilotObservationTemporalLineageGraph
```

with only:

```text
ALIAS_OF
DERIVED_FROM
STATE_CONTINUATION_OF
CARRYOVER_FROM
```

`ALIAS_OF` is symmetric.

The other three are directed:

```text
downstream temporal/intervention identity -> upstream causal origin
```

Examples:

```text
adaptive_state:after_2
    STATE_CONTINUATION_OF
adaptive_state:after_1
```

```text
carryover_state:session_b
    CARRYOVER_FROM
intervention_episode:training_x
```

```text
exposure_episode:derived_measurement
    DERIVED_FROM
history_state:shared_exposure_root
```

The relation vocabulary intentionally excludes:

```text
PRECEDES
FOLLOWS
OVERLAPS
SAME_WINDOW
CLOSE_IN_TIME
INSTANCE_OF
```

because:

```text
A HAPPENED BEFORE B
!=
B CAUSALLY CARRIES STATE FROM A
```

and:

```text
A AND B OCCURRED IN THE SAME WINDOW
!=
A AND B SHARE ONE TEMPORAL CAUSAL ORIGIN
```

No temporal lineage is inferred from timestamps.

## Alias contraction and DAG governance

Aliases are canonicalized into equivalence classes before directed validation.

The graph rejects:

```text
self-relations
exact duplicate relations
reverse duplicate aliases
conflicting directed relation kinds on one exact pair
directed relations inside one alias class
directed cycles after alias contraction
```

Example:

```text
A ALIAS_OF A2
A2 DERIVED_FROM B
B CARRYOVER_FROM A
```

contracts to:

```text
[A,A2] -> B -> [A,A2]
```

and fails closed.

Likewise:

```text
A ALIAS_OF B
A STATE_CONTINUATION_OF B
```

is invalid because the directed relation collapses inside one alias class.

## Directional closure

PR10.1 adds:

```text
pilot_observation_temporal_lineage_closure_keys_v1(...)
```

Traversal rules:

```text
ALIAS_OF
    <->

DERIVED_FROM
STATE_CONTINUATION_OF
CARRYOVER_FROM
    downstream -> upstream
```

So:

```text
child CARRYOVER_FROM parent
```

means:

```text
closure(child)
    contains child + parent + upstream ancestors

closure(parent)
    does not traverse down to child
```

This is deliberate. Descendant observations do not become reachable merely because an ancestor exists.

The closure returns the existing hashed temporal dependence keys:

```text
pilot_observation_temporal:<sha256>
```

instead of raw refs.

Still:

```text
HASHED KEY != AUTHENTICATION
HASHED KEY != ANONYMIZATION GUARANTEE
```

## Stronger temporal structural gate

The new gate is:

```text
validate_pilot_materialized_evidence_temporal_ancestry_preconditions_v1(...)
```

It first invokes:

```text
validate_pilot_materialized_evidence_shared_temporal_preconditions_v1(...)
```

Therefore the entire prior stack remains mandatory:

```text
exact capture dependence
same-session lineage
same elicitation/test form
same exact upstream source
source ancestry/common origin
reviewed source completeness
same exact mechanism
mechanism ancestry/common origin
reviewed mechanism completeness
same exact coordination authority
coordination ancestry/common origin
reviewed coordination completeness
same exact temporal/intervention/carryover identity
```

Only after all earlier gates pass does temporal lineage expand.

If two observations' temporal closures intersect:

```text
KNOWN COMMON TEMPORAL / INTERVENTION ORIGIN
    -> REJECT
```

Examples:

```text
A ALIAS_OF B
    -> REJECT
```

```text
A CARRYOVER_FROM B
    -> REJECT
```

```text
A DERIVED_FROM root
B STATE_CONTINUATION_OF root
    -> REJECT
```

```text
A CARRYOVER_FROM middle
middle DERIVED_FROM root
B DERIVED_FROM root
    -> REJECT
```

Cross-kind lineage is valid only when explicitly declared.

For example:

```text
ADAPTIVE_STATE:state_a
    DERIVED_FROM
INTERVENTION_EPISODE:root

CARRYOVER_STATE:state_b
    STATE_CONTINUATION_OF
INTERVENTION_EPISODE:root
```

This exact geometry is dependent.

It does **not** imply that all adaptive states and carryover states are related.

## Same time is still not a lineage edge

The implementation does not create lineage from:

```text
same proposed_at
same captured_at
same calendar day
same wall-clock interval
same subject
same environment
same protocol
chronological adjacency
overlapping intervals
```

A real carryover must be represented explicitly with a relation such as:

```text
CARRYOVER_FROM
```

A state continuation must be represented explicitly as:

```text
STATE_CONTINUATION_OF
```

This keeps the temporal layer causal rather than merely chronological.

## Multiple refs inside one observation

One observation may declare several temporal identities.

If two of its own refs converge through the graph, that does not create a cross-observation collision by itself.

The validator first unions each observation's temporal closure into one set, then compares that set against previous observations.

Therefore:

```text
two aliases inside observation A
!=
two independent observations
```

but also:

```text
internal alias overlap inside A
!=
cross-observation rejection
```

until another observation intersects the same closure.

## Conservative PASS

These may pass the new structural layer:

```text
A DERIVED_FROM root_A
B DERIVED_FROM root_B
```

when declared closures are disjoint.

But:

```text
DISJOINT DECLARED TEMPORAL CLOSURES
!=
INDEPENDENT TEMPORAL ORIGINS
```

Likewise:

```text
EMPTY TEMPORAL LINEAGE GRAPH
!=
NO SHARED TEMPORAL ORIGIN
```

and:

```text
DIFFERENT TEMPORAL REFS
!=
INDEPENDENT INTERVENTION HISTORIES
```

The graph contains only explicit known relations.

Missing temporal declarations and missing lineage edges remain epistemically unresolved.

## Positive earlier dependence still dominates

Distinct temporal refs cannot repair an earlier dependence.

If the two observations already share one exact controller:

```text
controller:X
```

then the reviewed coordination stack rejects before temporal lineage is considered.

Likewise, exact shared temporal identity is rejected by the exact temporal gate before lineage expansion.

Therefore:

```text
DISTINCT TEMPORAL DESCENDANTS
!=
PERMISSION TO IGNORE EARLIER DEPENDENCE
```

and:

```text
TEMPORAL LINEAGE GRAPH
!=
OVERRIDE MECHANISM
```

## New invariants

```text
DIFFERENT TEMPORAL REFS
!=
DIFFERENT TEMPORAL CAUSAL ORIGINS
```

```text
ALIAS / DERIVATION / STATE CONTINUATION / CARRYOVER
=>
KNOWN DECLARED TEMPORAL DEPENDENCE
```

```text
SAME CLOCK TIME
!=
SAME TEMPORAL CAUSAL IDENTITY
```

```text
TEMPORAL ORDER
!=
TEMPORAL LINEAGE
```

```text
EMPTY TEMPORAL GRAPH
!=
COMPLETE TEMPORAL GRAPH
```

```text
PASSING TEMPORAL-ANCESTRY PRECONDITIONS
!=
TEMPORAL COMPLETENESS
```

```text
PASS
!=
STATISTICAL INDEPENDENCE
```

```text
PASS
!=
AUTHORITY TO CLAIM INDEPENDENT REPLICATION
```

## Resulting stack

After this closure:

```text
SOURCE
  exact identity
  -> ancestry
  -> reviewed completeness

MECHANISM
  exact identity
  -> ancestry
  -> reviewed completeness

COORDINATION
  exact identity
  -> ancestry
  -> reviewed completeness

TEMPORAL / INTERVENTION
  exact identity
  -> ancestry
  -> [completeness still unresolved]
```

## Non-goals

This closure does not add:

```text
timestamp-based dependence inference
automatic intervention discovery
automatic carryover detection
subject-learning estimation
temporal similarity heuristics
probabilistic state reconstruction
reviewed temporal completeness
evidence weighting
independent-replication claims
CapabilityClaim creation
Evaluation
PR3 state
achievements
progression
Player Window behavior
```

## Next unresolved boundary

The next false-replication geometry is hidden temporal lineage.

Example:

```text
observation A -> declared adaptive state A
observation B -> declared carryover state B

declared temporal closures are disjoint

BUT

both also depend on hidden intervention root X
```

or:

```text
A -> hidden carryover predecessor X
B -> hidden carryover predecessor X
```

with missing relations.

The next controlled layer should therefore govern two independent dimensions:

```text
TEMPORAL DECLARATION COMPLETENESS
TEMPORAL LINEAGE GRAPH COMPLETENESS
```

with:

```text
exact observation/source/mechanism/coordination/temporal scope binding
+
exact temporal-lineage graph binding
```

and the same conservative rule used elsewhere:

```text
COMPLETE_FOR_SCOPE
!=
GLOBAL COMPLETENESS
```

Even after that future review:

```text
PASS
!=
STATISTICAL INDEPENDENCE
PASS
!=
AUTHORITY TO CLAIM INDEPENDENT REPLICATION
```
