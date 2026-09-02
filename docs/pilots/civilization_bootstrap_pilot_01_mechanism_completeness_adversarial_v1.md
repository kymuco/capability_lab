# Civilization Bootstrap Pilot 01 — Reviewed Mechanism Completeness, Hidden-Mechanism Uncertainty and False-Replication Boundary Closure

Status: **PR10.1 adversarial closure**

The previous PR10.1 layer can detect exact shared observation mechanisms and explicit mechanism alias/clone/derivation/state-continuation ancestry.

That still leaves one false-replication geometry:

```text
observation A -> declared mechanism A
observation B -> declared mechanism B

declared mechanism closures are disjoint

BUT

both observations also used hidden mechanism X
```

or:

```text
mechanism A -> hidden common origin X
mechanism B -> hidden common origin X

but the lineage edges were never declared
```

Therefore:

```text
NO DECLARED COMMON MECHANISM
!=
NO COMMON MECHANISM
```

and:

```text
EMPTY / DISJOINT MECHANISM GRAPH
!=
COMPLETE MECHANISM GRAPH
```

## Why graph traversal is not enough

`PilotObservationMechanismLineageGraph` can only traverse explicitly represented mechanism relations.

It must not invent hidden parents from:

```text
same model family
same tool name
same environment label
same operator name
same pipeline version
semantic similarity
string similarity
```

So the next boundary is not another reachability rule. It is governance over what was reviewed for completeness.

## Two completeness dimensions

Mechanism-origin review has two independent dimensions:

```text
MECHANISM_DECLARATIONS
MECHANISM_LINEAGE_GRAPH
```

Each is reviewed as:

```text
COMPLETE_FOR_SCOPE
INCOMPLETE
UNKNOWN
```

through:

```text
PilotMechanismCompletenessStatus
```

Both dimensions are required.

```text
COMPLETE MECHANISM DECLARATIONS
+ UNKNOWN MECHANISM GRAPH
!=
REVIEWED MECHANISM-ORIGIN SEPARATION
```

and:

```text
UNKNOWN MECHANISM DECLARATIONS
+ COMPLETE MECHANISM GRAPH
!=
REVIEWED MECHANISM-ORIGIN SEPARATION
```

## Exact mechanism completeness review

PR10.1 adds:

```text
PilotMechanismLineageCompletenessReview
```

with:

```text
review_id
scope_sha256
graph_sha256
mechanism_declarations_status
mechanism_lineage_graph_status
reviewer_ref
reviewed_at
rationale
```

The review remains private governance metadata.

It does not change raw Pilot capture, materialization candidate/review schemas, EvidenceRecord, claims, evaluations, state, achievements, progression, or Player Window logic.

## Exact graph binding

```text
pilot_observation_mechanism_lineage_graph_sha256_v1(graph)
```

computes a domain-separated SHA-256 over the exact canonical mechanism-lineage graph.

The digest binds:

```text
relation_kind
mechanism kind/ref
upstream mechanism kind/ref
```

Because the graph canonicalizes ordering and alias orientation first:

```text
REVIEW OF GRAPH A
!=
AUTHORITY FOR GRAPH B
```

Even adding an isolated relation produces a different review-binding digest.

## Exact scope binding

```text
pilot_observation_mechanism_origin_scope_sha256_v1(entries)
```

binds the review to the exact evaluated materialized observation/source/mechanism basis.

For every entry the digest contains:

```text
candidate_sha256
evidence_id
exact PilotCaptureRecord source key
declared upstream source kind/ref pairs
declared observation mechanism kind/ref pairs
```

This deliberately binds mechanism completeness to its underlying source basis too.

Therefore:

```text
REVIEW OF MECHANISM DECLARATION A
!=
REVIEW OF CHANGED MECHANISM DECLARATION B
```

and:

```text
REVIEW OF SOURCE BASIS A
!=
REVIEW OF CHANGED SOURCE BASIS B
```

even when the mechanism declarations happen to remain byte-for-byte unchanged.

Input ordering does not change the canonical scope digest.

## Strongest mechanism-origin gate

The new gate is:

```text
validate_pilot_materialized_evidence_reviewed_mechanism_origin_preconditions_v1(...)
```

It first composes the entire existing ladder:

```text
exact capture reuse
same Pilot session
same elicitation/test form
same exact upstream source
source alias/ancestry/common ancestor
reviewed source disclosure completeness
reviewed source lineage-graph completeness
same exact mechanism
mechanism alias/clone/derivation/state-continuation ancestry
declared common mechanism ancestor
```

Any earlier positive dependence remains a rejection.

Only after those checks pass does the new gate require:

```text
mechanism_review.scope_sha256 == exact current observation/source/mechanism scope
mechanism_review.graph_sha256 == exact current mechanism-lineage graph
```

and:

```text
mechanism_declarations_status == COMPLETE_FOR_SCOPE
mechanism_lineage_graph_status == COMPLETE_FOR_SCOPE
```

Any `INCOMPLETE` or `UNKNOWN` state fails closed.

## Three-way boundary

The resulting mechanism layer is:

```text
KNOWN COMMON MECHANISM
    -> structural REJECT

UNKNOWN / INCOMPLETE MECHANISM COVERAGE
    -> governance REJECT

REVIEWED COMPLETE_FOR_SCOPE
+ no declared mechanism convergence
    -> reviewed mechanism-origin precondition PASS
```

## COMPLETE_FOR_SCOPE semantics

For `mechanism_declarations_status`, `COMPLETE_FOR_SCOPE` means the human review record declares that relevant observation-level mechanisms were completely represented for the exact bounded reviewed scope.

For `mechanism_lineage_graph_status`, `COMPLETE_FOR_SCOPE` means the human review record declares that relevant dependence-bearing mechanism lineage was completely represented for the exact graph snapshot and bounded purpose.

It does not mean:

```text
global mechanism provenance is complete
all possible hidden mechanisms are impossible
future observations are covered
the reviewer is infallible
the reviewer identity is authenticated
the review is cryptographically signed
```

## Review metadata is not proof

The reviewer must be explicitly declared HUMAN using the existing PR10.1 reviewer metadata type.

Still:

```text
DECLARED HUMAN REVIEWER
!=
AUTHENTICATED HUMAN IDENTITY
```

and:

```text
scope_sha256 + graph_sha256
!=
SIGNATURE
```

The hashes bind exact content. They do not prove real-world exhaustiveness.

## Stale-review replay resistance

### Changed graph

```text
review(graph A) + graph B
```

fails when graph digests differ.

### Changed mechanism declaration

```text
review(mechanisms A) + mechanisms B
```

fails because the scope digest changes.

### Changed underlying source basis

Even if mechanism declarations are unchanged:

```text
review(source basis A + mechanisms M)
+
source basis B + mechanisms M
```

fails because upstream source declarations are part of the mechanism scope digest.

This prevents a mechanism completeness review from floating free of the exact evidence/provenance basis it reviewed.

## Known ancestry still dominates completeness

A completeness review cannot override a positive known dependence.

If:

```text
mechanism A DERIVED_FROM root
mechanism B STATE_CONTINUATION_OF root
```

then the mechanism ancestry gate rejects before completeness status can authorize anything.

```text
COMPLETE REVIEW
!=
PERMISSION TO IGNORE KNOWN DEPENDENCE
```

## New invariants

```text
NO DECLARED COMMON MECHANISM
!=
NO COMMON MECHANISM
```

```text
EMPTY MECHANISM GRAPH
!=
COMPLETE MECHANISM GRAPH
```

```text
COMPLETE MECHANISM GRAPH
WITHOUT COMPLETE MECHANISM DISCLOSURE
!=
REVIEWED MECHANISM-ORIGIN SEPARATION
```

```text
COMPLETE MECHANISM DISCLOSURE
WITHOUT COMPLETE MECHANISM GRAPH
!=
REVIEWED MECHANISM-ORIGIN SEPARATION
```

```text
UNKNOWN
!=
INDEPENDENT
```

```text
INCOMPLETE
!=
INDEPENDENT
```

```text
COMPLETE_FOR_SCOPE
!=
GLOBAL COMPLETENESS
```

```text
REVIEW OF SCOPE A
!=
AUTHORITY FOR SCOPE B
```

```text
REVIEW OF GRAPH A
!=
AUTHORITY FOR GRAPH B
```

```text
REVIEW DIGEST BINDING
!=
SIGNATURE
```

```text
REVIEWED MECHANISM-ORIGIN PRECONDITION PASS
!=
STATISTICAL INDEPENDENCE
```

```text
REVIEWED MECHANISM-ORIGIN PRECONDITION PASS
!=
AUTHORITY TO CLAIM INDEPENDENT REPLICATION
```

## Non-goals

This closure does not add:

```text
automatic hidden-mechanism discovery
heuristic mechanism matching
probabilistic mechanism completion
operator authentication
model-family correlation inference
environment fingerprinting
reviewer quorum
cryptographic signatures
persistence/sync for completeness reviews
evidence weighting
independent-replication claim creation
capability evaluation
PR3 state derivation
achievements
progression
Player Window behavior
```

## Next unresolved boundary

After this closure, source provenance and mechanism provenance both have:

```text
exact identity dependence
explicit ancestry dependence
reviewed bounded completeness
```

The next unresolved question is no longer simple provenance reachability.

Two observations can still satisfy all current structural and reviewed-completeness gates while sharing a higher-order **coordination / experimental-control / decision authority** that is not well represented as an observation mechanism itself.

Examples include:

```text
one controller choosing both samples
one policy deciding both collection conditions
one adaptive process selecting both test cases
one adjudication authority shaping both accepted observations
```

That boundary should be modeled explicitly rather than silently overloaded onto operator or review-process mechanism refs.
