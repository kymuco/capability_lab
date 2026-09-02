# Civilization Bootstrap Pilot 01 — Reviewed Temporal Completeness and Hidden Temporal-Origin Closure

Status: **PR10.1 adversarial closure**

This closure completes the temporal/intervention/carryover family with bounded
human-reviewed completeness governance.

Before this step PR10.1 already had:

```text
SOURCE
  exact identity
  -> explicit ancestry
  -> reviewed bounded completeness

MECHANISM
  exact identity
  -> explicit ancestry
  -> reviewed bounded completeness

COORDINATION / CONTROL
  exact identity
  -> explicit ancestry
  -> reviewed bounded completeness

TEMPORAL / INTERVENTION / CARRYOVER
  exact identity
  -> explicit ancestry
```

The remaining false-replication geometry is:

```text
observation A -> declared temporal A
observation B -> declared temporal B

declared temporal closures are disjoint

BUT

both depend on hidden intervention/history origin X
```

or the temporal declarations are complete but a dependence-relevant lineage edge
was omitted.

Therefore:

```text
NO DECLARED COMMON TEMPORAL ORIGIN != NO COMMON TEMPORAL ORIGIN
EMPTY / DISJOINT TEMPORAL GRAPH != COMPLETE TEMPORAL GRAPH
```

## Two completeness dimensions

Temporal origin review has two independent dimensions:

```text
TEMPORAL_DECLARATIONS
TEMPORAL_LINEAGE_GRAPH
```

Each uses:

```text
PilotTemporalCompletenessStatus

COMPLETE_FOR_SCOPE
INCOMPLETE
UNKNOWN
```

Both must be `COMPLETE_FOR_SCOPE`.

`UNKNOWN` and `INCOMPLETE` fail closed.

## Exact review record

PR10.1 adds:

```text
PilotTemporalLineageCompletenessReview
```

with:

```text
review_id
scope_sha256
graph_sha256
temporal_declarations_status
temporal_lineage_graph_status
reviewer_ref
reviewed_at
rationale
```

It is private governance metadata, not an EvidenceRecord, CapabilityClaim,
Evaluation, PR3 state mutation, achievement, progression update, or Player
Window mutation.

## Exact graph binding

```text
pilot_observation_temporal_lineage_graph_sha256_v1(graph)
```

binds review to the canonical temporal-lineage graph under:

```text
capability_lab/pilot_observation_temporal_lineage_graph_review_binding@1
```

The digest covers:

```text
relation_kind
temporal kind/ref
upstream temporal kind/ref
```

Therefore:

```text
REVIEW OF GRAPH A != AUTHORITY FOR GRAPH B
```

The existing graph canonicalization still applies: symmetric alias orientation
does not manufacture a different graph identity.

## Exact scope binding

```text
pilot_observation_temporal_origin_scope_sha256_v1(entries)
```

binds review to each exact observation basis:

```text
candidate_sha256
evidence_id
exact capture source key
upstream source declarations
mechanism declarations
coordination declarations
temporal declarations
```

This means a temporal completeness review becomes stale if any lower basis
changes even when temporal refs do not.

Examples:

```text
same temporal refs + changed capture source -> stale review
same temporal refs + changed upstream source -> stale review
same temporal refs + changed mechanism -> stale review
same temporal refs + changed coordination -> stale review
changed temporal declaration -> stale review
```

Input observation ordering is canonicalized before hashing.

## Human-reviewed bounded semantics

The reviewer is the existing explicitly declared HUMAN reviewer metadata.

Still:

```text
DECLARED HUMAN REVIEWER != AUTHENTICATED HUMAN IDENTITY
scope_sha256 + graph_sha256 != CRYPTOGRAPHIC SIGNATURE
```

`COMPLETE_FOR_SCOPE` means only that the review record declares the represented
temporal declaration set or graph complete for the exact bounded review scope.

It does not mean global causal completeness or statistical independence.

## Strongest temporal gate

The new gate is:

```text
validate_pilot_materialized_evidence_reviewed_temporal_origin_preconditions_v1(...)
```

It first calls:

```text
validate_pilot_materialized_evidence_temporal_ancestry_preconditions_v1(...)
```

so the complete prior ladder remains mandatory:

```text
exact capture
same session
same elicitation

exact upstream source
source ancestry/common origin
reviewed source completeness

exact mechanism
mechanism ancestry/common origin
reviewed mechanism completeness

exact coordination/control authority
coordination ancestry/common origin
reviewed coordination completeness

exact temporal/intervention/carryover identity
temporal ancestry/common origin
```

Only after those gates pass does temporal completeness require:

```text
review.scope_sha256 == exact current temporal-origin scope
review.graph_sha256 == exact current temporal-lineage graph
temporal_declarations_status == COMPLETE_FOR_SCOPE
temporal_lineage_graph_status == COMPLETE_FOR_SCOPE
```

Any mismatch, `UNKNOWN`, or `INCOMPLETE` fails closed.

## Three-way boundary

```text
KNOWN COMMON TEMPORAL / INTERVENTION / CARRYOVER ORIGIN
    -> structural REJECT

UNKNOWN / INCOMPLETE TEMPORAL COVERAGE
    -> governance REJECT

REVIEWED COMPLETE_FOR_SCOPE
+ no declared temporal convergence
    -> bounded temporal-origin precondition PASS
```

Completeness never overrides known dependence.

If:

```text
adaptive_state:A DERIVED_FROM intervention:root
carryover_state:B STATE_CONTINUATION_OF intervention:root
```

the temporal ancestry gate rejects before completeness can matter.

Likewise exact shared temporal identity rejects first.

```text
COMPLETE REVIEW != PERMISSION TO IGNORE KNOWN DEPENDENCE
```

## Empty declarations and graphs

An empty temporal declaration may pass this layer only if a human explicitly
reviewed that exact bounded declaration set as `COMPLETE_FOR_SCOPE`.

That means only:

> no additional temporal identities are declared necessary for this exact
> bounded review scope.

It does not mean:

```text
NO TEMPORAL STATE EXISTS GLOBALLY
```

The same rule applies to an empty temporal lineage graph.

## No chronology inference

This closure preserves the explicit causal boundary:

```text
same timestamp
same minute
same day
same chronological window
A before B
A after B
overlap
```

do not imply:

```text
same temporal causal origin
carryover
state continuation
derivation
```

No lineage edge is inferred from chronology.

## Resulting four-family symmetry

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
```

This is a structural/governance ladder, not an independence certificate.

## Conservative PASS

Passing the strongest temporal gate still does not establish:

```text
statistical independence
random assignment
independent treatment allocation
independent experimental units
absence of latent confounding
absence of shared external shocks
independent replication
authority to weight evidence as independent
authority to create CapabilityClaim support
authority to update PR3 state
```

Therefore:

```text
REVIEWED TEMPORAL-ORIGIN PRECONDITION PASS
!=
INDEPENDENT REPLICATION
```

## New invariants

```text
NO DECLARED COMMON TEMPORAL ORIGIN != NO COMMON TEMPORAL ORIGIN
EMPTY TEMPORAL GRAPH != COMPLETE TEMPORAL GRAPH
UNKNOWN != INDEPENDENT
INCOMPLETE != INDEPENDENT
COMPLETE_FOR_SCOPE != GLOBAL COMPLETENESS
REVIEW OF SCOPE A != AUTHORITY FOR SCOPE B
REVIEW OF GRAPH A != AUTHORITY FOR GRAPH B
REVIEW DIGEST BINDING != SIGNATURE
COMPLETE REVIEW != PERMISSION TO IGNORE KNOWN DEPENDENCE
PASS != STATISTICAL INDEPENDENCE
PASS != AUTHORITY TO CLAIM INDEPENDENT REPLICATION
```

## Non-goals

This closure does not add:

```text
automatic temporal-state discovery
timestamp-based carryover inference
hidden-confounder discovery
randomization validation
assignment-provenance validation
experimental-unit modeling
evidence weighting
CapabilityClaim creation
Evaluation
PR3 state derivation
reviewer authentication
digital signatures
```

## Next unresolved boundary

All four current causal families now have:

```text
identity -> ancestry -> reviewed bounded completeness
```

The next distinct false-replication class is likely **experimental allocation /
intervention assignment provenance**.

Two observations can pass every current gate while assignment decisions are
still correlated through one allocation state, block, adaptive-randomization
state, or shared treatment-assignment episode.

That should be represented as a separate causal family rather than overloaded
into coordination or temporal metadata.
