# Civilization Bootstrap Pilot 01 — Exact Experimental Allocation / Assignment Dependence Closure

Status: **PR10.1 adversarial closure**

This closure introduces a new causal family after the reviewed temporal-origin
boundary.

Before this step, PR10.1 can already require bounded reviewed separation across:

```text
SOURCE
  exact identity
  -> ancestry
  -> reviewed completeness

MECHANISM
  exact identity
  -> ancestry
  -> reviewed completeness

COORDINATION / CONTROL
  exact identity
  -> ancestry
  -> reviewed completeness

TEMPORAL / INTERVENTION / CARRYOVER
  exact identity
  -> ancestry
  -> reviewed completeness
```

That still does not establish independent experimental allocation.

A remaining false-replication geometry is:

```text
observation A
  -> reviewed-disjoint source
  -> reviewed-disjoint mechanism
  -> reviewed-disjoint coordination
  -> reviewed-disjoint temporal origin

observation B
  -> reviewed-disjoint source
  -> reviewed-disjoint mechanism
  -> reviewed-disjoint coordination
  -> reviewed-disjoint temporal origin

BUT

A and B were allocated within the same constrained randomization block
```

or:

```text
A -> adaptive allocation state X
B -> adaptive allocation state X
```

or:

```text
A -> matched allocation set X
B -> matched allocation set X
```

Therefore:

```text
REVIEWED TEMPORAL-ORIGIN SEPARATION
!=
INDEPENDENT EXPERIMENTAL ALLOCATION
```

## Why allocation is a separate causal family

Allocation provenance is not the same thing as observation mechanism,
coordination authority, or temporal context.

For example:

```text
controller A != controller B
assignment pipeline A != assignment pipeline B
intervention episode A != intervention episode B
```

can all be true while both observations were produced under one fixed-size
randomization block whose assignments are coupled.

Likewise, two observations can have different acquisition mechanisms while
sharing one adaptive allocation state that changed future assignment
probabilities based on earlier outcomes.

This is dependence in the experimental-design layer.

It should not be overloaded into:

```text
source refs
mechanism refs
coordination refs
temporal refs
```

because doing so would erase a useful causal distinction.

## Exact allocation identities

The first allocation layer deliberately governs exact identity only.

PR10.1 adds:

```text
PilotObservationAllocationKind
PilotObservationAllocationRef
```

with bounded kinds:

```text
ALLOCATION_BLOCK
ASSIGNMENT_EPISODE
RANDOMIZATION_STATE
ADAPTIVE_ALLOCATION_STATE
CLUSTER_ASSIGNMENT_UNIT
MATCHED_ALLOCATION_SET
OTHER
```

These refs identify exact bounded allocation/design instances.

Examples:

```text
ALLOCATION_BLOCK:block_2026_08_17_01
ASSIGNMENT_EPISODE:assignment_tx_0042
RANDOMIZATION_STATE:rng_state_epoch_17
ADAPTIVE_ALLOCATION_STATE:bandit_state_009
CLUSTER_ASSIGNMENT_UNIT:school_cluster_12
MATCHED_ALLOCATION_SET:matched_pair_008
```

The refs are opaque identifiers. The implementation does not parse semantic
meaning out of their strings.

## What is intentionally not an allocation identity

The following are not automatically dependence-relevant exact identities:

```text
same treatment arm label
same control label
same treatment name
same nominal probability
same randomization algorithm
same allocation policy definition
same statistical design family
same timestamp
same subject
```

In particular:

```text
TREATMENT_ARM=A
TREATMENT_ARM=A
```

does not imply that two observations share one allocation event or randomization
state.

Similarly:

```text
50% assignment probability
50% assignment probability
```

does not imply a common allocation origin.

And:

```text
same randomization algorithm
```

does not identify the same bounded algorithm execution/state.

Those geometries may become relevant only through explicit instance metadata or
through another already-governed mechanism/control layer.

## Exact dependence key

PR10.1 adds:

```text
pilot_observation_allocation_dependence_key_v1(...)
```

under the domain:

```text
capability_lab/pilot_observation_experimental_allocation_dependence@1
```

The public dependence key is:

```text
pilot_observation_allocation:<sha256>
```

The digest binds both:

```text
allocation kind
allocation ref
```

Therefore the same opaque ref under different allocation kinds is not silently
treated as one identity.

Raw allocation refs are not echoed in cross-observation dependence errors.

## Candidate-bound declaration

Allocation metadata is represented by:

```text
PilotMaterializationAllocationDeclaration
```

with:

```text
candidate_sha256
allocations
```

and the builder:

```text
build_pilot_materialization_allocation_declaration_v1(...)
```

The declaration is bound to exact materialization-candidate bytes.

Thus:

```text
ALLOCATION DECLARATION FOR CANDIDATE A
!=
ALLOCATION DECLARATION FOR CANDIDATE B
```

even if both candidates refer to otherwise similar observations.

`allocations` is a canonical tuple.

Exact duplicate refs within one declaration are rejected.

## Empty declaration semantics

An empty declaration means exactly:

```text
NO ALLOCATION REFS WERE SUPPLIED
```

It does not mean:

```text
NO EXPERIMENTAL ALLOCATION OCCURRED
NO RANDOMIZATION DEPENDENCE EXISTS
NO MATCHED-SET DEPENDENCE EXISTS
NO CLUSTER-ASSIGNMENT DEPENDENCE EXISTS
INDEPENDENT RANDOMIZATION IS PROVEN
```

This distinction matters because the first allocation layer is an exact
structural gate, not yet a completeness regime.

## Allocation materialization entry

The new composition type is:

```text
PilotMaterializedEvidenceAllocationEntry
```

which contains:

```text
temporal_entry
allocation_declaration
```

The declaration must bind to the exact same candidate already represented by
the temporal entry.

This prevents metadata swapping:

```text
temporal basis for candidate A
+
allocation declaration for candidate B
-> REJECT
```

## New strongest exact-allocation gate

PR10.1 adds:

```text
validate_pilot_materialized_evidence_shared_allocation_preconditions_v1(...)
```

The gate first requires the existing strongest reviewed temporal-origin gate:

```text
validate_pilot_materialized_evidence_reviewed_temporal_origin_preconditions_v1(...)
```

Therefore the complete prior ladder remains mandatory.

Only after that ladder passes does the allocation gate compare exact declared
allocation identities across observations.

If two distinct observations expose the same exact allocation dependence key:

```text
observation A -> allocation X
observation B -> allocation X
```

then:

```text
REJECT
```

## Exact allocation geometries closed

### Shared constrained allocation block

```text
A -> ALLOCATION_BLOCK:block_01
B -> ALLOCATION_BLOCK:block_01
```

rejects.

A fixed-count randomized block can induce assignment dependence even when
observations are otherwise causally separated.

### Shared assignment episode

```text
A -> ASSIGNMENT_EPISODE:episode_01
B -> ASSIGNMENT_EPISODE:episode_01
```

rejects.

### Shared randomization state

```text
A -> RANDOMIZATION_STATE:state_01
B -> RANDOMIZATION_STATE:state_01
```

rejects.

This is an exact state-instance statement, not inference from a common RNG
library or algorithm.

### Shared adaptive allocation state

```text
A -> ADAPTIVE_ALLOCATION_STATE:adaptive_01
B -> ADAPTIVE_ALLOCATION_STATE:adaptive_01
```

rejects.

This captures designs where assignments are coupled through one evolving
allocation state.

### Shared cluster assignment unit

```text
A -> CLUSTER_ASSIGNMENT_UNIT:cluster_01
B -> CLUSTER_ASSIGNMENT_UNIT:cluster_01
```

rejects.

The observations share one assignment unit even if their downstream
measurements are distinct.

### Shared matched allocation set

```text
A -> MATCHED_ALLOCATION_SET:set_01
B -> MATCHED_ALLOCATION_SET:set_01
```

rejects.

Matched/pair allocation deliberately couples the observations at the design
layer.

## Distinct exact refs are not an independence certificate

If:

```text
A -> ALLOCATION_BLOCK:block_A
B -> ALLOCATION_BLOCK:block_B
```

the exact-identity gate may pass.

That means only:

```text
NO EXACT DECLARED ALLOCATION IDENTITY WAS REUSED
```

It does not mean:

```text
independent allocation origins
independent randomization
absence of shared allocation ancestry
absence of cloned randomization state
absence of common adaptive allocation origin
statistical independence
independent replication
```

Those are later boundaries.

## Earlier dependence dominates allocation separation

Distinct allocation refs cannot repair an earlier failure.

For example:

```text
source/mechanism/coordination pass
temporal completeness UNKNOWN
allocation A != allocation B
```

still rejects at the temporal completeness gate.

Likewise, known temporal ancestry remains a rejection regardless of allocation
separation.

Therefore:

```text
LATER CAUSAL SEPARATION
!=
PERMISSION TO IGNORE EARLIER KNOWN OR UNRESOLVED DEPENDENCE
```

## Conservative PASS semantics

Passing the exact allocation gate means only:

```text
the full reviewed source/mechanism/coordination/temporal ladder passed
AND
no exact declared allocation identity is repeated across observations
```

It does not mean:

```text
independent randomization
valid random assignment
allocation concealment
balanced treatment assignment
absence of selection bias
statistical independence
causal identifiability
independent replication
authority to weight evidence as independent
authority to create a CapabilityClaim
authority to update PR3 state
```

## New invariants

```text
REVIEWED TEMPORAL-ORIGIN SEPARATION
!=
INDEPENDENT EXPERIMENTAL ALLOCATION

SAME TREATMENT ARM
!=
SAME ALLOCATION IDENTITY

SAME NOMINAL ALLOCATION PROBABILITY
!=
SAME RANDOMIZATION STATE

SAME RANDOMIZATION ALGORITHM
!=
SAME RANDOMIZATION INSTANCE

SAME EXACT ALLOCATION IDENTITY
-> STRUCTURAL REJECT

DISTINCT ALLOCATION REFS
!=
INDEPENDENT ALLOCATION ORIGINS

EMPTY ALLOCATION DECLARATION
!=
NO ALLOCATION DEPENDENCE

PASS
!=
STATISTICAL INDEPENDENCE

PASS
!=
INDEPENDENT REPLICATION
```

## Test surface

Targeted adversarial regressions cover:

```text
shared ALLOCATION_BLOCK
shared ASSIGNMENT_EPISODE
shared RANDOMIZATION_STATE
shared ADAPTIVE_ALLOCATION_STATE
shared CLUSTER_ASSIGNMENT_UNIT
shared MATCHED_ALLOCATION_SET
distinct exact allocation refs
empty declarations
prior temporal-completeness rejection
candidate binding
canonical declaration ordering
duplicate exact refs
kind-sensitive dependence keys
privacy-reducing keys
strict enum/ref validation
wrong allocation-entry type
absence of treatment-arm/probability/algorithm pseudo-identities
```

## Non-goals

This closure does not add:

```text
allocation ancestry
randomization-state lineage
allocation completeness review
automatic randomization reconstruction
statistical randomization tests
balance diagnostics
propensity estimation
treatment-effect estimation
causal-effect identification
CapabilityClaim support
Evaluation
PR3 state mutation
achievements
progression
Player Window changes
```

## Next boundary

The next allocation-specific false-replication geometry is ancestry/common
origin:

```text
A -> allocation state A
B -> allocation state B

A != B

BUT

A DERIVED_FROM common allocation root X
B STATE_CONTINUATION_OF common allocation root X
```

or:

```text
block A CLONED_FROM block root
block B CLONED_FROM block root
```

The next correct layer is therefore an explicit allocation lineage graph,
followed later by reviewed allocation declaration/graph completeness.

That should remain separate from temporal lineage because allocation ancestry is
experimental-design provenance, not merely temporal carryover.
