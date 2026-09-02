# Civilization Bootstrap Pilot 01 — Coordination/Control Lineage and Common-Authority-Origin Closure

Status: **PR10.1 adversarial closure**

The exact coordination gate can reject:

```text
observation A -> controller X
observation B -> controller X
```

but distinct coordination refs can still share one known control origin:

```text
observation A -> controller A
observation B -> controller B

A != B

BUT

A DELEGATED_FROM root
B DERIVED_FROM root
```

Therefore:

```text
DIFFERENT COORDINATION REFS
!=
DIFFERENT CONTROL ORIGINS
```

## Separate causal layer

Coordination/control lineage remains separate from source and mechanism lineage.

```text
SOURCE
    input/provenance dependence

MECHANISM
    acquisition/production dependence

COORDINATION AUTHORITY
    cross-observation selection/control dependence
```

A shared higher-order controller may correlate observations even when source and mechanism origins are reviewed separated.

## Explicit relation kinds

`PilotObservationCoordinationLineageGraph` supports only:

```text
ALIAS_OF
DELEGATED_FROM
DERIVED_FROM
STATE_CONTINUATION_OF
```

`ALIAS_OF` is symmetric.

All other relations are directed:

```text
downstream coordination identity -> upstream control origin
```

Examples:

```text
policy_run_2 DELEGATED_FROM controller_root
selector_2 STATE_CONTINUATION_OF selector_1
adjudication_process DERIVED_FROM authority_root
```

These are dependence-relevant lineage facts, not generic classifications.

PR10.1 deliberately excludes:

```text
INSTANCE_OF
same policy family
same scheduler implementation
same selector algorithm
same reviewer_ref
same code version
same configuration schema
```

because:

```text
SAME POLICY DEFINITION
!=
SAME POLICY_EXECUTION
```

and:

```text
SAME IMPLEMENTATION
!=
SHARED CONTROLLER STATE
```

No edge is inferred from names or metadata.

## Alias contraction and DAG governance

Aliases form equivalence classes before directed validation.

The graph rejects:

```text
self-relations
exact duplicate relations
reverse duplicate aliases
conflicting directed relation kinds
directed relations inside one alias class
directed cycles after alias contraction
```

Example:

```text
A ALIAS_OF A2
A2 DERIVED_FROM B
B DELEGATED_FROM A
```

contracts to:

```text
[A,A2] -> B -> [A,A2]
```

and is rejected.

Likewise:

```text
A ALIAS_OF B
A STATE_CONTINUATION_OF B
```

fails because the directed edge collapses inside one alias class.

## Directional closure

PR10.1 adds:

```text
pilot_observation_coordination_lineage_closure_keys_v1(...)
```

Traversal is:

```text
ALIAS_OF
    <->

DELEGATED_FROM
DERIVED_FROM
STATE_CONTINUATION_OF
    downstream -> upstream
```

So:

```text
child DELEGATED_FROM parent
```

means:

```text
closure(child) contains child + parent + upstream ancestors
closure(parent) does not traverse down to child
```

The result uses existing domain-separated coordination dependence keys rather than raw refs.

```text
HASHED KEY != ANONYMIZATION
HASHED KEY != AUTHENTICATION
```

## Stronger structural gate

The new gate is:

```text
validate_pilot_materialized_evidence_coordination_ancestry_preconditions_v1(...)
```

It first calls:

```text
validate_pilot_materialized_evidence_shared_coordination_preconditions_v1(...)
```

so the entire existing ladder remains mandatory:

```text
exact capture
same session
same elicitation
same exact upstream source
source ancestry/common origin
reviewed source completeness
same exact mechanism
mechanism ancestry/common origin
reviewed mechanism completeness
same exact coordination authority
```

Only then does the new gate expand coordination lineage closures.

If two observations' closures intersect:

```text
KNOWN COMMON CONTROL ORIGIN
    -> REJECT
```

Examples:

```text
A ALIAS_OF B
    -> REJECT
```

```text
A DELEGATED_FROM B
    -> REJECT
```

```text
A DERIVED_FROM root
B STATE_CONTINUATION_OF root
    -> REJECT
```

```text
A DELEGATED_FROM middle
middle DERIVED_FROM root
B DERIVED_FROM root
    -> REJECT
```

Cross-kind lineage is allowed only when explicitly represented:

```text
POLICY_EXECUTION:policy_a
    DERIVED_FROM
CONTROLLER:root

ADAPTIVE_SELECTOR:selector_b
    STATE_CONTINUATION_OF
CONTROLLER:root
```

This exact geometry is dependent. It does not imply that policy executions and selectors are generally related.

## Conservative PASS

Disjoint declared roots may pass this gate:

```text
A DERIVED_FROM root_A
B DERIVED_FROM root_B
```

but:

```text
DISJOINT DECLARED CLOSURES
!=
INDEPENDENT CONTROL ORIGINS
```

Likewise:

```text
EMPTY COORDINATION LINEAGE GRAPH
!=
NO SHARED CONTROL ORIGIN
```

An empty graph means only that no relations were supplied.

No absence claim is manufactured.

## No heuristic lineage inference

The implementation does not infer coordination lineage from:

```text
name similarity
static policy identity
shared implementation
reviewer equality
temporal proximity
similar decisions
same subject
same environment
same machine
```

Positive earlier dependence still rejects through the composed gates, while missing coordination-lineage metadata remains unknown.

## New invariants

```text
DIFFERENT COORDINATION REFS
!=
DIFFERENT CONTROL ORIGINS
```

```text
ALIAS / DELEGATION / DERIVATION / STATE CONTINUATION
=>
KNOWN DECLARED CONTROL DEPENDENCE
```

```text
SOURCE-SEPARATED
+
MECHANISM-SEPARATED
+
DISTINCT COORDINATION REFS
+
COMMON DECLARED CONTROL ORIGIN
=>
NOT CONTROL-INDEPENDENT REPLICATION
```

```text
SAME STATIC POLICY
!=
SAME POLICY EXECUTION
```

```text
PASSING COORDINATION-ANCESTRY PRECONDITIONS
!=
COORDINATION COMPLETENESS
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

## Non-goals

This closure does not add:

```text
coordination lineage discovery
heuristic controller matching
policy-family correlation inference
selector-state introspection
authority authentication
signatures
coordination completeness review
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

After this closure, coordination/control provenance has:

```text
exact identity dependence
explicit ancestry dependence
```

but not reviewed bounded completeness.

The remaining false-replication geometry is:

```text
observation A -> declared controller A
observation B -> declared controller B

declared closures are disjoint

BUT

both also share hidden controller X
```

or:

```text
controller A -> hidden authority root X
controller B -> hidden authority root X
```

with undeclared edges.

The next controlled layer should therefore govern:

```text
COORDINATION DECLARATION COMPLETENESS
COORDINATION LINEAGE GRAPH COMPLETENESS
```

with exact observation/source/mechanism/coordination scope binding and exact graph binding.
