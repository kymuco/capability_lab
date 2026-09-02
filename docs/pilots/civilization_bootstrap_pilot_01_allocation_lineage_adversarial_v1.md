# Civilization Bootstrap Pilot 01 — Allocation / Randomization-State Lineage and Common-Origin Closure

Status: **PR10.1 adversarial closure**

This closure extends the new experimental-allocation family from exact identity
to explicit ancestry/common-origin governance.

The previous exact-allocation boundary can reject:

```text
observation A -> allocation identity X
observation B -> allocation identity X
```

But distinct exact refs are not enough:

```text
observation A -> randomization_state:A
observation B -> randomization_state:B

A != B

BUT

A CLONED_FROM randomization_state:root
B CLONED_FROM randomization_state:root
```

or:

```text
assignment_episode:A
    STATE_CONTINUATION_OF adaptive_allocation_state:root

allocation_block:B
    DERIVED_FROM adaptive_allocation_state:root
```

These are separate exact identities with one declared common allocation origin.

Therefore:

```text
DIFFERENT ALLOCATION REFS != DIFFERENT ALLOCATION ORIGINS
DIFFERENT RANDOMIZATION STATE IDS != INDEPENDENT RANDOMIZATION
DIFFERENT ASSIGNMENT EPISODES != INDEPENDENT ASSIGNMENT
```

## Relation vocabulary

PR10.1 adds:

```text
PilotObservationAllocationRelationKind

ALIAS_OF
DERIVED_FROM
CLONED_FROM
STATE_CONTINUATION_OF
```

Semantics:

```text
ALIAS_OF
    symmetric

DERIVED_FROM
CLONED_FROM
STATE_CONTINUATION_OF
    downstream -> upstream
```

The vocabulary is intentionally narrow.

It does **not** contain:

```text
SAME_ARM
SAME_TREATMENT
SAME_PROBABILITY
USES_ALGORITHM
INSTANCE_OF
SAME_EXPERIMENT_FAMILY
```

These similarities are not sufficient evidence that two observations share one
allocation/randomization causal origin.

For example:

```text
observation A -> treatment arm "control"
observation B -> treatment arm "control"
```

does not by itself create an allocation-lineage relation.

Likewise:

```text
same nominal probability 0.5
same RNG implementation
same block-randomization algorithm
same allocation policy definition
```

do not identify one exact randomization state or common allocation ancestor.

## Canonical lineage graph

The new graph is:

```text
PilotObservationAllocationLineageGraph
```

containing:

```text
PilotObservationAllocationRelation(
    relation_kind,
    allocation,
    upstream,
)
```

`ALIAS_OF` is canonicalized independent of input orientation.

Thus:

```text
A ALIAS_OF B
```

and:

```text
B ALIAS_OF A
```

represent the same relation.

Supplying both is rejected as a duplicate/reverse-alias relation rather than
silently double-counted.

## Alias contraction

Before directed ancestry is validated, alias-connected allocation refs are
contracted into one equivalence class.

This catches invalid structures such as:

```text
A ALIAS_OF A2
A2 DERIVED_FROM A
```

because after alias contraction the directed edge becomes a self-edge.

It also catches cycles that are only visible after alias contraction:

```text
A ALIAS_OF A2
A2 DERIVED_FROM B
B STATE_CONTINUATION_OF A
```

which becomes:

```text
[A, A2] -> B -> [A, A2]
```

and is rejected.

## Directed relation conflicts

One exact directed pair cannot simultaneously be declared with incompatible
lineage meanings.

For example:

```text
state_child DERIVED_FROM state_root
state_child CLONED_FROM state_root
```

is rejected as conflicting relation kinds.

The same check is repeated after alias contraction, because two superficially
different refs may collapse to the same directed pair.

## DAG requirement

After alias contraction, directed allocation lineage must be acyclic.

This is an ancestry/common-origin graph, not a general causal process graph.

```text
A DERIVED_FROM B
B STATE_CONTINUATION_OF A
```

is therefore invalid.

## Upstream-only closure

PR10.1 adds:

```text
pilot_observation_allocation_lineage_closure_keys_v1(...)
```

Traversal rules:

```text
ALIAS_OF
    both directions

DERIVED_FROM
CLONED_FROM
STATE_CONTINUATION_OF
    downstream -> upstream only
```

For:

```text
child CLONED_FROM parent
```

we have:

```text
closure(child)
    child
    parent
    ancestors(parent)

closure(parent)
    parent
    ancestors(parent)
```

The closure of the parent does not walk downstream into the child.

This prevents one descendant from contaminating every observation that happens
to share an upstream parent graph node merely because a reverse traversal was
performed.

## Cross-kind common roots

Lineage edges may cross allocation kinds when that relation is explicitly
known.

For example:

```text
ADAPTIVE_ALLOCATION_STATE:A
    DERIVED_FROM
RANDOMIZATION_STATE:root

ASSIGNMENT_EPISODE:B
    STATE_CONTINUATION_OF
RANDOMIZATION_STATE:root
```

Both observation closures contain the exact same root key.

Therefore they are known allocation-dependent for the bounded structural gate.

No cross-kind relation is inferred automatically.

## Cloned randomization states

A particularly important false-replication geometry is:

```text
RANDOMIZATION_STATE:A
    CLONED_FROM
RANDOMIZATION_STATE:root

RANDOMIZATION_STATE:B
    CLONED_FROM
RANDOMIZATION_STATE:root
```

Even though `A != B`, both are declared descendants of one randomization state.

PR10.1 rejects treating these as structurally separated allocation origins.

This does not claim that every software clone creates statistical dependence in
every possible experiment. It says only that when the experiment's provenance
explicitly declares a shared allocation/randomization origin, the system must
not label the observations structurally independent at this boundary.

## New strongest gate

The new structural gate is:

```text
validate_pilot_materialized_evidence_allocation_ancestry_preconditions_v1(...)
```

It first requires the previous exact-allocation gate:

```text
validate_pilot_materialized_evidence_shared_allocation_preconditions_v1(...)
```

That gate already composes the complete reviewed lower ladder:

```text
exact capture reuse
session lineage
elicitation lineage

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

exact allocation identity
```

Only after all prior gates pass does allocation ancestry add:

```text
allocation aliases
allocation derivation
randomization-state cloning
allocation-state continuation
common allocation/randomization ancestor
```

## Per-observation union

An observation may declare multiple allocation refs.

If two refs belonging to the same observation are aliases or share an ancestor,
that does not create a fake second observation.

For each observation:

```text
union all allocation-lineage closure keys
```

and only then compare that union against other observations.

Therefore:

```text
one observation:
    randomization_state:A
    randomization_state:A_alias
    A ALIAS_OF A_alias
```

does not self-collide.

## Empty graph semantics

An empty lineage graph means only:

```text
NO ADDITIONAL ALLOCATION LINEAGE RELATIONS WERE SUPPLIED
```

It does not mean:

```text
NO HIDDEN COMMON ALLOCATION ORIGIN
INDEPENDENT RANDOMIZATION
INDEPENDENT ASSIGNMENT
INDEPENDENT REPLICATION
```

This matters because the completeness layer has not yet been added for the
allocation family.

## Conservative PASS semantics

Passing the new gate means only:

```text
all reviewed lower causal/provenance gates passed
+
no exact allocation identity was shared
+
the supplied allocation lineage graph exposed no common alias/upstream origin
```

It does not mean:

```text
allocation declarations are complete
allocation lineage graph is complete
randomization provenance is globally complete
statistical independence
independent treatment assignment
valid experimental randomization
independent replication
permission to weight evidence as independent
```

Therefore:

```text
ALLOCATION-ANCESTRY PRECONDITION PASS
!=
INDEPENDENT RANDOMIZATION
```

and:

```text
ALLOCATION-ANCESTRY PRECONDITION PASS
!=
INDEPENDENT REPLICATION
```

## Structural ladder after this closure

```text
SOURCE
  exact identity
  -> ancestry
  -> reviewed bounded completeness

MECHANISM
  exact identity
  -> ancestry
  -> reviewed bounded completeness

COORDINATION / CONTROL
  exact identity
  -> ancestry
  -> reviewed bounded completeness

TEMPORAL / INTERVENTION / CARRYOVER
  exact identity
  -> ancestry
  -> reviewed bounded completeness

EXPERIMENTAL ALLOCATION / ASSIGNMENT
  exact identity
  -> ancestry
  -> completeness still unresolved
```

## New invariants

```text
DIFFERENT ALLOCATION REFS != DIFFERENT ALLOCATION ORIGINS
DIFFERENT RANDOMIZATION STATE IDS != INDEPENDENT RANDOMIZATION
SAME ARM != SAME ALLOCATION IDENTITY
SAME ALGORITHM != SAME RANDOMIZATION STATE
SAME NOMINAL PROBABILITY != SAME ALLOCATION ORIGIN
ALIAS IS SYMMETRIC
ANCESTRY IS UPSTREAM-ONLY
CLONED RANDOMIZATION STATES MAY SHARE ONE DECLARED ORIGIN
COMMON DECLARED ALLOCATION ANCESTOR -> STRUCTURAL REJECT
EMPTY ALLOCATION LINEAGE GRAPH != NO COMMON ALLOCATION ORIGIN
PASS != STATISTICAL INDEPENDENCE
PASS != INDEPENDENT RANDOMIZATION
PASS != AUTHORITY TO CLAIM INDEPENDENT REPLICATION
```

## Non-goals and next boundary

This closure does not add:

```text
automatic randomization-state discovery
heuristic inference from treatment arms
probabilistic common-origin inference
seed analysis
randomness quality testing
balance testing
experimental effect estimation
reviewer authentication
CapabilityClaim creation
Evaluation
PR3 state derivation
achievement/progression logic
Player Window changes
```

The next unresolved boundary is allocation completeness.

Two observations may have distinct exact allocation refs and a supplied lineage
graph with no convergence, while declarations or lineage edges are still
unknown/incomplete.

The next correct layer is therefore:

```text
Reviewed Allocation Declaration Completeness
+
Allocation Lineage Graph Completeness
+
Hidden Allocation-Origin Uncertainty Closure
```

bound to the exact full lower basis and exact allocation-lineage graph.
