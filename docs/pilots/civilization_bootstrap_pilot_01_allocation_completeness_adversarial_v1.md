# Civilization Bootstrap Pilot 01 — Reviewed Allocation Completeness and Hidden Allocation-Origin Closure

Status: **PR10.1 adversarial closure**

This closure completes the experimental allocation / assignment family with
bounded human-reviewed completeness governance.

Before this step PR10.1 already has:

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
  -> reviewed bounded completeness

ALLOCATION / ASSIGNMENT / RANDOMIZATION
  exact identity
  -> explicit ancestry
```

The remaining allocation false-replication geometry is:

```text
observation A -> declared allocation A
observation B -> declared allocation B

A != B
declared allocation-lineage closures are disjoint

BUT

one relevant allocation identity was not declared
```

or:

```text
allocation A
allocation B

declared graph says no convergence

BUT

a known clone / derivation / state-continuation edge was omitted
```

Therefore:

```text
NO DECLARED COMMON ALLOCATION ORIGIN
!=
NO COMMON ALLOCATION ORIGIN

EMPTY / DISJOINT ALLOCATION GRAPH
!=
COMPLETE ALLOCATION GRAPH

DISTINCT ALLOCATION REFS
!=
INDEPENDENT RANDOMIZATION
```

## Two independent completeness dimensions

Allocation-origin review has two independent dimensions:

```text
ALLOCATION_DECLARATIONS
ALLOCATION_LINEAGE_GRAPH
```

Both use:

```text
PilotAllocationCompletenessStatus

COMPLETE_FOR_SCOPE
INCOMPLETE
UNKNOWN
```

Both must be `COMPLETE_FOR_SCOPE`.

```text
COMPLETE DECLARATIONS + UNKNOWN GRAPH
!=
REVIEWED ALLOCATION-ORIGIN SEPARATION

UNKNOWN DECLARATIONS + COMPLETE GRAPH
!=
REVIEWED ALLOCATION-ORIGIN SEPARATION
```

`UNKNOWN` and `INCOMPLETE` both fail closed.

They are different states because review may know that the representation is
incomplete, or may simply be unable to establish completeness.

Neither state is interpreted as negative evidence about the person or as a
failed Pilot observation.

## Exact review record

PR10.1 adds:

```text
PilotAllocationLineageCompletenessReview
```

with:

```text
review_id
scope_sha256
graph_sha256
allocation_declarations_status
allocation_lineage_graph_status
reviewer_ref
reviewed_at
rationale
```

The record is private governance metadata.

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

## Exact allocation graph binding

```text
pilot_observation_allocation_lineage_graph_sha256_v1(graph)
```

hashes the exact canonical allocation-lineage graph under:

```text
capability_lab/pilot_observation_allocation_lineage_graph_review_binding@1
```

The payload binds, for every canonical relation:

```text
relation_kind
allocation kind/ref
upstream allocation kind/ref
```

Because `PilotObservationAllocationLineageGraph` already canonicalizes
`ALIAS_OF`, reverse alias orientation hashes identically:

```text
A ALIAS_OF B
```

and:

```text
B ALIAS_OF A
```

represent the same canonical graph.

But adding, removing, or changing a causal relation changes `graph_sha256`.

Therefore:

```text
REVIEW OF GRAPH A
!=
AUTHORITY FOR GRAPH B
```

## Exact scope binding

```text
pilot_observation_allocation_origin_scope_sha256_v1(entries)
```

binds the review to the entire lower causal/provenance basis plus the allocation
declarations.

Per observation it includes:

```text
candidate_sha256
evidence_id
exact_capture_source
upstream_sources
mechanisms
coordinations
temporals
allocations
```

This intentionally makes an allocation completeness review stale when any
relevant lower basis changes.

Examples:

```text
same allocations
+ changed exact PilotCaptureRecord source
-> stale review
```

```text
same allocations
+ changed upstream source
-> stale review
```

```text
same allocations
+ changed acquisition/governance mechanism
-> stale review
```

```text
same allocations
+ changed coordination/control declaration
-> stale review
```

```text
same allocations
+ changed temporal/intervention declaration
-> stale review
```

```text
changed allocation declaration
-> stale review
```

The observation list is canonicalized by evidence identity before hashing.

Therefore input order does not create a new reviewed scope.

## Why lower-layer binding matters

Without lower-layer binding this unsafe replay would be possible:

```text
review(
  source basis A,
  mechanism A,
  control A,
  temporal A,
  allocation X
)

later evaluate(
  source basis B,
  mechanism B,
  control B,
  temporal B,
  allocation X
)

reuse old allocation review
```

That would allow an allocation completeness record to float free from the
actual observations it reviewed.

PR10.1 explicitly forbids that.

```text
REVIEW OF ALLOCATION DECLARATIONS
IS ALSO REVIEW OF THEIR EXACT BOUNDED BASIS
```

This does not mean the reviewer verified every fact in the world.

It means the structural record cannot silently migrate to another basis.

## Human-reviewed bounded semantics

The review requires the existing explicit `HUMAN` reviewer metadata.

Still:

```text
DECLARED HUMAN REVIEWER
!=
AUTHENTICATED HUMAN IDENTITY

scope_sha256 + graph_sha256
!=
CRYPTOGRAPHIC SIGNATURE
```

The reviewer metadata remains a declared governance fact.

This closure does not introduce:

```text
digital signatures
PKI
identity proofing
multi-party authorization
reviewer reputation
probabilistic confidence
```

`COMPLETE_FOR_SCOPE` means only:

> For the exact reviewed observations and purpose, the human review record
> declares the represented allocation identities or allocation-lineage graph
> complete for that bounded scope.

It does not mean:

```text
global allocation provenance completeness
reviewer infallibility
hidden-variable elimination
proof of randomization
proof of exchangeability
proof of statistical independence
future-scope completeness
```

## Strongest gate

The new strongest gate is:

```text
validate_pilot_materialized_evidence_reviewed_allocation_origin_preconditions_v1(...)
```

It first requires:

```text
validate_pilot_materialized_evidence_allocation_ancestry_preconditions_v1(...)
```

That gate already composes:

```text
exact capture dependence
same-session dependence
same elicitation dependence

source exact identity
source ancestry/common origin
reviewed source declaration completeness
reviewed source graph completeness

mechanism exact identity
mechanism ancestry/common origin
reviewed mechanism declaration completeness
reviewed mechanism graph completeness

coordination exact identity
coordination ancestry/common origin
reviewed coordination declaration completeness
reviewed coordination graph completeness

temporal exact identity
temporal ancestry/common origin
reviewed temporal declaration completeness
reviewed temporal graph completeness

allocation exact identity
allocation alias/derivation/clone/state-continuation ancestry
declared common allocation/randomization origin
```

Only after that structural ladder passes does allocation completeness evaluate:

```text
review.scope_sha256
    ==
current exact observation/source/mechanism/coordination/temporal/allocation scope

review.graph_sha256
    ==
current exact allocation-lineage graph

allocation_declarations_status
    ==
COMPLETE_FOR_SCOPE

allocation_lineage_graph_status
    ==
COMPLETE_FOR_SCOPE
```

Any mismatch, `UNKNOWN`, or `INCOMPLETE` fails closed.

## Three-way boundary

The resulting semantics are:

```text
KNOWN COMMON ALLOCATION / RANDOMIZATION ORIGIN
    -> structural REJECT

UNKNOWN / INCOMPLETE ALLOCATION COVERAGE
    -> governance REJECT

REVIEWED COMPLETE_FOR_SCOPE
+ no declared allocation convergence
    -> reviewed allocation-origin precondition PASS
```

These are deliberately different outcomes.

A completeness record cannot override a known dependence.

## Known dependence dominates completeness

Suppose:

```text
RANDOMIZATION_STATE:A
    CLONED_FROM
RANDOMIZATION_STATE:root

ADAPTIVE_ALLOCATION_STATE:B
    DERIVED_FROM
RANDOMIZATION_STATE:root
```

Then:

```text
allocation ancestry gate
    -> REJECT
```

before completeness status is considered.

Even a record saying:

```text
allocation_declarations_status = COMPLETE_FOR_SCOPE
allocation_lineage_graph_status = COMPLETE_FOR_SCOPE
```

cannot bless a known common root.

Invariant:

```text
COMPLETE REVIEW
!=
PERMISSION TO IGNORE KNOWN DEPENDENCE
```

The same applies to exact shared allocation identity.

## Stale-review replay resistance

Changed graph:

```text
review(graph A) + graph B
-> REJECT
```

Changed allocation declaration:

```text
review(allocation A) + allocation B
-> REJECT
```

Changed temporal basis with unchanged allocation ref:

```text
review(temporal A + allocation X)
+
temporal B + allocation X
-> REJECT
```

Changed coordination/mechanism/source/capture basis behaves the same way.

The review therefore remains attached to the exact bounded causal basis.

## Empty declarations remain conservative

An empty allocation declaration still means:

```text
NO ALLOCATION REFS WERE SUPPLIED
```

It does not mean:

```text
NO ALLOCATION PROCESS EXISTED
NO RANDOMIZATION STATE EXISTED
NO MATCHING BLOCK EXISTED
NO CLUSTER ASSIGNMENT EXISTED
```

The completeness layer is what determines whether that empty declaration is
reviewed complete for the bounded scope.

So:

```text
empty declaration
+ UNKNOWN completeness
-> REJECT
```

while:

```text
empty declaration
+ explicit human COMPLETE_FOR_SCOPE review
+ complete reviewed allocation graph
+ all prior gates pass
-> bounded allocation-origin precondition PASS
```

That pass still does not prove randomization.

## Design similarity is still not lineage

This closure does not weaken the previous allocation-lineage boundary.

The following remain insufficient to create an allocation lineage edge:

```text
same treatment arm
same treatment label
same nominal probability
same randomization algorithm
same allocation policy definition
same code family
same experiment family
same timestamp
same nominal study
```

If a real dependence exists, it must be represented with a bounded allocation
identity or explicit ancestry relation such as:

```text
ALIAS_OF
DERIVED_FROM
CLONED_FROM
STATE_CONTINUATION_OF
```

Completeness governance then reviews whether those declarations are complete
for the bounded purpose.

## Conservative PASS semantics

Passing the new strongest gate means only:

```text
all prior structural/governance gates passed
+
allocation declarations reviewed COMPLETE_FOR_SCOPE
+
allocation lineage graph reviewed COMPLETE_FOR_SCOPE
+
review bound to exact current scope
+
review bound to exact current graph
```

It does not mean:

```text
independent randomization
statistical independence
causal independence
exchangeability
absence of interference
independent subjects
independent experimental replication
valid p-values
valid evidence weighting
```

And it does not authorize:

```text
CapabilityClaim creation
Evaluation
PR3 state update
achievement unlock
progression update
Player Window change
```

Therefore:

```text
REVIEWED ALLOCATION-ORIGIN PRECONDITION PASS
!=
INDEPENDENT REPLICATION
```

## Resulting five-family structure

After this closure:

```text
SOURCE
  identity
  -> ancestry
  -> reviewed bounded completeness

MECHANISM
  identity
  -> ancestry
  -> reviewed bounded completeness

COORDINATION / CONTROL
  identity
  -> ancestry
  -> reviewed bounded completeness

TEMPORAL / INTERVENTION / CARRYOVER
  identity
  -> ancestry
  -> reviewed bounded completeness

ALLOCATION / ASSIGNMENT / RANDOMIZATION
  identity
  -> ancestry
  -> reviewed bounded completeness
```

The pattern is now symmetric across five distinct causal families.

That symmetry is useful, but it does not imply that these five families exhaust
all possible dependence mechanisms.

## New invariants

```text
NO DECLARED COMMON ALLOCATION ORIGIN
!=
NO COMMON ALLOCATION ORIGIN

EMPTY ALLOCATION GRAPH
!=
COMPLETE ALLOCATION GRAPH

UNKNOWN
!=
INDEPENDENT

INCOMPLETE
!=
INDEPENDENT

COMPLETE_FOR_SCOPE
!=
GLOBAL COMPLETENESS

REVIEW OF SCOPE A
!=
AUTHORITY FOR SCOPE B

REVIEW OF GRAPH A
!=
AUTHORITY FOR GRAPH B

REVIEW DIGEST BINDING
!=
SIGNATURE

COMPLETE REVIEW
!=
PERMISSION TO IGNORE KNOWN DEPENDENCE

DISTINCT ALLOCATION REFS
!=
INDEPENDENT RANDOMIZATION

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
automatic allocation-process discovery
heuristic inference from treatment labels
heuristic inference from probability values
randomization tests
exchangeability proofs
causal effect estimation
interference modeling
subject independence
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

## Next causal boundary

Once allocation completeness is governed, a distinct unresolved family is
**sampling / selection / cohort-construction dependence**.

Two observations may pass all five current families while still having:

```text
observation A -> sample/selection frame X
observation B -> sample/selection frame X
```

or distinct sample refs that derive from one selection episode, shared cohort
construction state, shared resampling/bootstrap draw, shared inclusion policy
execution, or one bounded recruitment/selection batch.

That should not be overloaded into experimental allocation.

Allocation answers:

> How were already-considered observational units assigned to conditions?

Selection/sampling answers:

> How did those observational units enter the observed set in the first place?

Those are different causal questions and should remain separate families.

Before adding that family, the current allocation-completeness commit should
still go through the normal local exact-HEAD test, hard review, and PR closure
workflow.
