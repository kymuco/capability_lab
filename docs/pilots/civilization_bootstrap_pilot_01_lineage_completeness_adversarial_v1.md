# Civilization Bootstrap Pilot 01 — Reviewed Lineage Completeness, Hidden-Origin Uncertainty and False-Independence Boundary Closure

Status: **PR10.1 adversarial closure**

This closure addresses the first dependence boundary that cannot be solved by adding another equality or reachability rule.

Earlier PR10.1 layers can now reject:

```text
same exact PilotCaptureRecord
same Pilot session lineage
same frozen elicitation/test form
same exact declared upstream source
alias/copy/transform/derivation ancestry
declared common upstream ancestor
```

The unresolved geometry is different:

```text
observation A -> declared root A
observation B -> declared root B

declared closure(A) ∩ declared closure(B) = {}
```

while the actual governance data may simply be incomplete:

```text
root A -> hidden origin X
root B -> hidden origin X

but those edges or sources were never declared
```

Therefore:

```text
DISCONNECTED DECLARED ROOTS
!=
INDEPENDENT ROOTS
```

and:

```text
EMPTY GRAPH
!=
COMPLETE GRAPH
```

## Why another graph traversal cannot close this boundary

The source-ancestry gate can only traverse relations represented in `PilotUpstreamSourceLineageGraph`.

If a source, alias, copy relation, transform edge, derivation edge, or ancestor is absent from the reviewed metadata, graph traversal has no legitimate basis to invent it.

PR10.1 therefore does not add fuzzy source matching, semantic source similarity, probabilistic hidden-parent inference, URL heuristics, model-based ancestry guesses, or automatic "root means independent" semantics.

```text
NO EDGE FOUND
!=
NO EDGE EXISTS
```

The correct boundary is governance over **what was reviewed for completeness**.

## Two independent completeness dimensions

A complete source-lineage graph is not sufficient if the observation-level source declarations are incomplete.

For example:

```text
observation A declares source_a
observation B declares source_b
```

can coexist with an undeclared source:

```text
observation A also used hidden_source_x
observation B also used hidden_source_x
```

even if every relation among `source_a` and `source_b` was perfectly captured.

PR10.1 therefore reviews two separate dimensions:

```text
UPSTREAM_SOURCE_DECLARATIONS
SOURCE_LINEAGE_GRAPH
```

Each receives one of:

```text
COMPLETE_FOR_SCOPE
INCOMPLETE
UNKNOWN
```

through:

```text
PilotLineageCompletenessStatus
```

The distinction is deliberate.

```text
COMPLETE DECLARATIONS + UNKNOWN GRAPH
!= REVIEWED ORIGIN SEPARATION

UNKNOWN DECLARATIONS + COMPLETE GRAPH
!= REVIEWED ORIGIN SEPARATION
```

The strongest reviewed source-origin precondition requires both dimensions to be `COMPLETE_FOR_SCOPE`.

## Exact review binding

PR10.1 adds:

```text
PilotUpstreamLineageCompletenessReview
```

with:

```text
review_id
scope_sha256
graph_sha256
upstream_source_declarations_status
source_lineage_graph_status
reviewer_ref
reviewed_at
rationale
```

The review is bound to two exact canonical snapshots.

### Exact graph digest

```text
pilot_upstream_source_lineage_graph_sha256_v1(graph)
```

computes a domain-separated SHA-256 over the canonical graph relations, including relation kind, source kind/ref, and upstream kind/ref.

Because `PilotUpstreamSourceLineageGraph` already canonicalizes relation order, aliases, and graph structure, equivalent canonical graph objects yield one stable review-binding digest.

A review of Graph A cannot authorize Graph B merely because both graphs happen to make the current observations look disconnected.

```text
REVIEW OF GRAPH A
!=
COMPLETENESS REVIEW OF GRAPH B
```

### Exact evaluated source-origin scope digest

```text
pilot_upstream_source_origin_scope_sha256_v1(entries)
```

binds the review to the exact set of evaluated materialized observations and their candidate-bound upstream-source declarations.

The digest includes, per entry:

```text
candidate_sha256
evidence_id
exact PilotCaptureRecord source
declared upstream source kind/ref pairs
```

and is deterministically independent of caller input ordering.

Therefore:

```text
REVIEW OF SOURCES {A,B}
!=
REVIEW OF SOURCES {A,C}
```

and:

```text
REVIEW OF OBSERVATIONS {1,2}
!=
REVIEW OF OBSERVATIONS {1,2,3}
```

A source declaration cannot be changed after review without invalidating the scope binding.

## Human-reviewed metadata, not authentication

The completeness review requires an explicitly declared human reviewer ref, reusing the existing PR10.1 human-reviewer metadata type.

That means:

```text
DECLARED HUMAN REVIEWER
!= AUTHENTICATED HUMAN IDENTITY
```

The review is also not signed.

```text
scope_sha256
graph_sha256
!=
signature
```

The digests provide exact content binding, not proof that the reviewer really performed the review, was competent, was correct, was exhaustive in the real world, or that no hidden source exists outside the review process.

This closure prevents accidental or structurally invalid reuse of completeness authority. It does not create cryptographic trust.

## Strongest reviewed source-origin gate

PR10.1 now exposes:

```text
validate_pilot_materialized_evidence_reviewed_source_origin_preconditions_v1(...)
```

The gate first runs the complete structural ladder:

```text
exact capture reuse
    -> REJECT

same session lineage
    -> REJECT

same frozen elicitation lineage
    -> REJECT

same exact declared upstream source
    -> REJECT

declared alias/ancestor/common ancestor
    -> REJECT
```

It then requires:

```text
review.scope_sha256 == exact evaluated scope digest
review.graph_sha256 == exact graph digest
```

and:

```text
upstream_source_declarations_status == COMPLETE_FOR_SCOPE
source_lineage_graph_status == COMPLETE_FOR_SCOPE
```

Any `INCOMPLETE` or `UNKNOWN` state fails closed.

Therefore the new three-way boundary is:

```text
KNOWN COMMON ORIGIN
    -> structural REJECT

UNKNOWN / INCOMPLETE ORIGIN COVERAGE
    -> governance REJECT

REVIEWED COMPLETE_FOR_SCOPE
+ no declared convergence
    -> reviewed source-origin precondition PASS
```

## What COMPLETE_FOR_SCOPE means

`COMPLETE_FOR_SCOPE` is intentionally bounded.

For `upstream_source_declarations_status`, it means the review record declares that the exact observation set's relevant upstream sources were completely represented for the bounded reviewed purpose.

For `source_lineage_graph_status`, it means the review record declares that the relevant alias/copy/transform/derivation ancestry needed for that bounded source-origin assessment was completely represented for the exact graph snapshot.

It does **not** mean:

```text
the global provenance universe is complete
```

or:

```text
all future observations are covered
```

or:

```text
no undiscoverable hidden mechanism exists
```

The scope and graph digests prevent that bounded declaration from silently expanding.

## PASS semantics remain conservative

Passing the reviewed source-origin gate means:

```text
all earlier structural dependence gates passed
AND
the exact evaluated source declarations were reviewed COMPLETE_FOR_SCOPE
AND
the exact source-lineage graph was reviewed COMPLETE_FOR_SCOPE
AND
the exact reviewed graph exposes no common declared origin
```

It still does **not** mean statistical independence, epistemic certainty, authenticated real-world provenance, or automatic authority for evidence weighting and independent-replication claims.

```text
REVIEWED SOURCE-ORIGIN PRECONDITION PASS
!=
AUTHORITY TO CLAIM INDEPENDENT REPLICATION
```

## Stale-review replay resistance

The closure explicitly prevents two replay classes.

### Graph replay

```text
review(graph A)
+
graph B
```

fails when:

```text
sha256(graph A) != sha256(graph B)
```

even if Graph B only adds a currently irrelevant isolated relation.

This matters because a completeness review concerns the exact graph snapshot, not merely today's intersection result.

### Scope replay

```text
review(observations/sources A)
+
changed observation/source declarations B
```

fails when:

```text
scope_sha256(A) != scope_sha256(B)
```

This includes source declaration replacement, adding/removing an observation, changing exact materialization candidate identity, changing the exact Pilot capture source, or changing declared upstream-source identity.

## Explicit ancestry still dominates completeness review

A `COMPLETE_FOR_SCOPE` review cannot override an already represented dependency.

If the graph says:

```text
source_a COPY_OF root
source_b TRANSFORM_OF root
```

then source-ancestry validation rejects before completeness status can help.

```text
COMPLETE REVIEW
!=
PERMISSION TO IGNORE KNOWN DEPENDENCE
```

Completeness resolves the **unknown-coverage boundary**. It never reverses positive dependence evidence.

## New invariants

```text
NO DECLARED COMMON ANCESTOR
!=
NO COMMON ANCESTOR
```

```text
GRAPH COMPLETE
WITHOUT SOURCE-DISCLOSURE COMPLETE
!=
REVIEWED ORIGIN SEPARATION
```

```text
SOURCE-DISCLOSURE COMPLETE
WITHOUT GRAPH COMPLETE
!=
REVIEWED ORIGIN SEPARATION
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
REVIEWED SOURCE-ORIGIN PRECONDITION PASS
!=
STATISTICAL OR EPISTEMIC INDEPENDENCE
```

## Non-goals

This closure does not add automatic hidden-origin discovery, source-content inspection, semantic source matching, probabilistic lineage completion, graph completion algorithms, global provenance completeness claims, signatures, authenticated reviewer identity, reviewer quorum, persistence/sync of completeness reviews, evidence weighting, capability claim creation, claim evaluation, PR3 state derivation, achievements, progression, or Player Window logic.

The next unresolved boundary is now above source-origin coverage itself: a reviewed-complete provenance scope can still be produced by one operator, review process, model, environment, or acquisition mechanism. Those shared **governance/acquisition mechanisms** may correlate otherwise source-separated observations and require their own explicit dependence boundary rather than being folded into source ancestry.
