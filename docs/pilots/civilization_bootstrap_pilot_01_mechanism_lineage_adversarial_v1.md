# Civilization Bootstrap Pilot 01 — Mechanism Lineage, Common-Origin Correlation and False-Replication Adversarial Closure

Status: **PR10.1 adversarial closure**

This closure addresses the next dependence boundary after exact shared acquisition/governance mechanism identity.

The previous PR10.1 mechanism layer can reject:

```text
observation A -> mechanism X
observation B -> mechanism X
```

But different mechanism refs can still descend from one known mechanism origin:

```text
observation A -> mechanism A
observation B -> mechanism B

mechanism A != mechanism B

BUT

mechanism A DERIVED_FROM root
mechanism B CLONED_FROM root
```

or:

```text
mechanism A ALIAS_OF mechanism B
```

or:

```text
mechanism A STATE_CONTINUATION_OF parent
mechanism B DERIVED_FROM parent
```

Therefore:

```text
DIFFERENT MECHANISM REFS != DIFFERENT MECHANISM ORIGINS
DIFFERENT MECHANISM KEYS != INDEPENDENT ACQUISITION
NEW RUN ID != NEW CAUSAL MECHANISM
```

## Separate mechanism-to-mechanism lineage graph

PR10.1 adds:

```text
PilotObservationMechanismLineageGraph
```

The graph is private governance metadata. It does not alter:

- PR10.0 raw capture;
- materialization candidates;
- materialization reviews;
- neutral PR2 `EvidenceRecord`;
- upstream-source declarations;
- source-lineage graph;
- source-lineage completeness review;
- exact mechanism declarations.

The graph records explicit, dependence-relevant relations among already-declared mechanism identities.

Supported relation kinds are:

```text
ALIAS_OF
CLONED_FROM
DERIVED_FROM
STATE_CONTINUATION_OF
```

For `CLONED_FROM`, `DERIVED_FROM`, and `STATE_CONTINUATION_OF`:

```text
downstream mechanism -> upstream mechanism
```

`ALIAS_OF` is symmetric.

These relation kinds are intentionally narrower than generic mechanism similarity.

```text
SAME MODEL FAMILY != MECHANISM LINEAGE
SAME PIPELINE VERSION != MECHANISM LINEAGE
SAME TOOL NAME != MECHANISM LINEAGE
SAME ENVIRONMENT LABEL != MECHANISM LINEAGE
SAME REVIEWER REF != MECHANISM LINEAGE
```

An edge must be explicitly declared because the governance process already knows that the relation is relevant to dependence assessment.

## Why generic INSTANCE_OF is excluded

Two observations can legitimately use separate executions of one implementation without sharing the same causal state or acquisition mechanism.

For example:

```text
tool_execution A INSTANCE_OF tool_v1
tool_execution B INSTANCE_OF tool_v1
```

does not by itself establish a common dependence origin.

Likewise:

```text
model_run A uses model_family X
model_run B uses model_family X
```

does not prove that the runs share state, context, cached output, operator input, or execution ancestry.

PR10.1 therefore does not introduce `INSTANCE_OF`, family membership, version similarity, semantic similarity, or heuristic lineage.

## Alias contraction and directed DAG validation

Alias edges form equivalence classes.

The graph first contracts:

```text
A ALIAS_OF B
```

and then validates the directed lineage graph between alias classes.

This allows normal aliases while rejecting hidden cycles such as:

```text
A ALIAS_OF B
B DERIVED_FROM C
C CLONED_FROM A
```

After alias contraction:

```text
[A,B] -> C -> [A,B]
```

which is rejected.

The graph also rejects:

- self-relations;
- exact duplicate relations;
- reverse duplicates of an alias pair;
- conflicting directed relation kinds for one ordered pair;
- directed relations that collapse within one alias class;
- directed cycles after alias contraction.

## Directional mechanism lineage closure

PR10.1 exposes:

```text
pilot_observation_mechanism_lineage_closure_keys_v1(mechanism, graph)
```

The closure always contains the exact mechanism itself.

Traversal is:

```text
ALIAS_OF
    <->

CLONED_FROM
DERIVED_FROM
STATE_CONTINUATION_OF
    downstream -> upstream
```

Therefore:

```text
child STATE_CONTINUATION_OF parent
```

means:

```text
closure(child)  contains child + parent + upstream ancestors
closure(parent) does not contain child
```

This prevents causal direction from being reversed.

All returned identities use the existing domain-separated mechanism dependence keys instead of raw refs.

```text
HASHED KEY != ANONYMIZATION
HASHED KEY != AUTHENTICATION
```

## Stronger mechanism-ancestry gate

The new strongest mechanism structural gate is:

```text
validate_pilot_materialized_evidence_mechanism_ancestry_preconditions_v1(...)
```

It first composes the full earlier ladder through:

```text
validate_pilot_materialized_evidence_shared_mechanism_preconditions_v1(...)
```

which already requires reviewed source-origin completeness and rejects exact repeated mechanism refs.

Then the new gate expands each declared mechanism through the supplied mechanism-lineage graph.

If two observations' mechanism ancestry closures intersect, they have a known common declared mechanism lineage and are rejected for the stronger independence interpretation.

Examples:

```text
mechanism A ALIAS_OF mechanism B
    -> REJECT
```

```text
mechanism A STATE_CONTINUATION_OF mechanism B
    -> REJECT
```

```text
mechanism A DERIVED_FROM root
mechanism B CLONED_FROM root
    -> REJECT
```

```text
mechanism A CLONED_FROM middle
middle DERIVED_FROM root
mechanism B STATE_CONTINUATION_OF root
    -> REJECT
```

The observations remain valid historical evidence. Only the stronger claim that they satisfy mechanism-ancestry independence preconditions is blocked.

## Common ancestor, not undirected connected component

The graph follows upstream lineage only, except aliases.

This matters because two mechanisms should not become dependent merely because they both feed a later downstream mechanism.

```text
parent -> child
```

is not traversed from parent to child.

PR10.1 detects:

- exact shared mechanism through the previous gate;
- aliases;
- ancestor/descendant reuse;
- siblings with one declared common mechanism ancestor;
- transitive clone/derivation/state-continuation ancestry.

## Empty and incomplete graph semantics

An empty graph is valid:

```text
PilotObservationMechanismLineageGraph(relations=())
```

Its meaning is only:

```text
NO MECHANISM-TO-MECHANISM RELATIONS WERE SUPPLIED
```

It does not mean:

```text
THE DECLARED MECHANISMS HAVE INDEPENDENT ORIGINS
```

Likewise:

```text
disjoint declared closures
```

means only that the supplied graph exposed no common lineage.

```text
NO DECLARED COMMON MECHANISM ANCESTOR != NO COMMON MECHANISM ANCESTOR
DISJOINT MECHANISM CLOSURES != STATISTICAL INDEPENDENCE
PASS != INDEPENDENT REPLICATION
```

## No automatic mechanism-lineage inference

PR10.1 deliberately does not infer:

```text
same reviewer -> same review mechanism
same model name -> related model runs
same pipeline version -> cloned acquisition
same machine -> shared environment state
similar mechanism refs -> aliases
similar output -> common mechanism
```

Those facts require explicit mechanism declarations and explicit lineage relations.

## New invariants

```text
DIFFERENT DECLARED MECHANISM REFS
!=
DIFFERENT CAUSAL MECHANISM ORIGINS
```

```text
ALIAS / CLONE / DERIVATION / STATE CONTINUATION
=>
KNOWN DECLARED MECHANISM DEPENDENCE
```

```text
TWO DISTINCT MECHANISMS
+
ONE DECLARED COMMON MECHANISM ANCESTOR
=>
NOT TWO MECHANISM-INDEPENDENT SUPPORT VOTES
```

```text
PASSING MECHANISM-ANCESTRY PRECONDITIONS
!=
MECHANISM COMPLETENESS
!=
STATISTICAL INDEPENDENCE
```

## Non-goals

This closure does not add:

- mechanism lineage discovery;
- family/version similarity inference;
- model-state inspection;
- pipeline content inspection;
- environment snapshot verification;
- reviewer identity authentication;
- signatures;
- mechanism completeness review;
- evidence weighting;
- capability claim creation;
- claim evaluation;
- PR3 state;
- achievements;
- progression;
- Player Window logic.

The next unresolved boundary is explicit: a mechanism declaration or mechanism-lineage graph may be incomplete even when all represented closures are disjoint. The next controlled layer should therefore govern exact reviewed mechanism-declaration and mechanism-graph completeness rather than invent hidden mechanism ancestors.
