# Civilization Bootstrap Pilot 01 — Reviewed Coordination Completeness and Hidden-Control-Origin Closure

Status: **PR10.1 adversarial closure**

This closure adds bounded human-reviewed completeness governance for the cross-observation coordination/control layer.

The previous PR10.1 stack can already govern:

```text
source identity -> source ancestry -> reviewed source completeness
mechanism identity -> mechanism ancestry -> reviewed mechanism completeness
coordination identity -> coordination ancestry
```

The remaining false-replication geometry is:

```text
observation A -> declared controller A
observation B -> declared selector B

declared coordination closures are disjoint

BUT

both observations also depend on hidden controller X
```

or the declarations are complete but a common control-origin edge was omitted from the lineage graph.

Therefore:

```text
NO DECLARED COMMON CONTROL ORIGIN != NO COMMON CONTROL ORIGIN
EMPTY / DISJOINT COORDINATION GRAPH != COMPLETE COORDINATION GRAPH
```

## Two completeness dimensions

Coordination/control origin review has two independent dimensions:

```text
COORDINATION_DECLARATIONS
COORDINATION_LINEAGE_GRAPH
```

Each is represented by:

```text
PilotCoordinationCompletenessStatus

COMPLETE_FOR_SCOPE
INCOMPLETE
UNKNOWN
```

Both dimensions must be `COMPLETE_FOR_SCOPE`.

```text
COMPLETE DECLARATIONS + UNKNOWN GRAPH != REVIEWED CONTROL-ORIGIN SEPARATION
UNKNOWN DECLARATIONS + COMPLETE GRAPH != REVIEWED CONTROL-ORIGIN SEPARATION
```

`UNKNOWN` and `INCOMPLETE` both fail closed.

## Exact review record

PR10.1 adds:

```text
PilotCoordinationLineageCompletenessReview
```

with:

```text
review_id
scope_sha256
graph_sha256
coordination_declarations_status
coordination_lineage_graph_status
reviewer_ref
reviewed_at
rationale
```

The review remains private governance metadata. It does not modify raw Pilot capture, EvidenceRecord, CapabilityClaim, Evaluation, PR3 state, achievements, progression, or Player Window behavior.

## Exact graph binding

```text
pilot_observation_coordination_lineage_graph_sha256_v1(graph)
```

hashes the exact canonical coordination-lineage graph under:

```text
capability_lab/pilot_observation_coordination_lineage_graph_review_binding@1
```

The digest binds:

```text
relation_kind
coordination kind/ref
upstream coordination kind/ref
```

Thus:

```text
REVIEW OF GRAPH A != AUTHORITY FOR GRAPH B
```

Even an isolated added relation changes the digest.

## Exact scope binding

```text
pilot_observation_coordination_origin_scope_sha256_v1(entries)
```

binds the review to the exact observation/source/mechanism/coordination basis. For every entry it includes:

```text
candidate_sha256
evidence_id
exact PilotCaptureRecord source key
upstream source declarations
observation mechanism declarations
coordination/control declarations
```

So a coordination completeness review becomes stale if any lower provenance layer changes, even when the coordination refs themselves remain unchanged.

```text
REVIEW OF COORDINATION DECLARATION A != REVIEW OF DECLARATION B
REVIEW OF MECHANISM BASIS A != REVIEW OF CHANGED MECHANISM BASIS B
REVIEW OF SOURCE BASIS A != REVIEW OF CHANGED SOURCE BASIS B
```

Input observation ordering is canonicalized before hashing.

## Human-reviewed bounded semantics

The review uses the existing explicitly declared HUMAN reviewer metadata.

Still:

```text
DECLARED HUMAN REVIEWER != AUTHENTICATED HUMAN IDENTITY
scope_sha256 + graph_sha256 != CRYPTOGRAPHIC SIGNATURE
```

`COMPLETE_FOR_SCOPE` means only that the human review record declares the bounded representation complete for the exact reviewed purpose. It does not mean global provenance completeness, reviewer infallibility, or future-scope coverage.

## New strongest gate

The new strongest gate is:

```text
validate_pilot_materialized_evidence_reviewed_coordination_origin_preconditions_v1(...)
```

It first calls:

```text
validate_pilot_materialized_evidence_coordination_ancestry_preconditions_v1(...)
```

which already composes the full prior ladder:

```text
exact capture reuse
same Pilot session
same elicitation/test form
same exact upstream source
source alias/ancestry/common origin
reviewed source declaration completeness
reviewed source graph completeness
same exact mechanism
mechanism alias/ancestry/common origin
reviewed mechanism declaration completeness
reviewed mechanism graph completeness
same exact coordination identity
coordination alias/delegation/derivation/state-continuation ancestry
declared common control origin
```

Only after all structural gates pass does the new validator require:

```text
review.scope_sha256 == exact current observation/source/mechanism/coordination scope
review.graph_sha256 == exact current coordination-lineage graph
coordination_declarations_status == COMPLETE_FOR_SCOPE
coordination_lineage_graph_status == COMPLETE_FOR_SCOPE
```

Any mismatch, `UNKNOWN`, or `INCOMPLETE` fails closed.

## Three-way boundary

```text
KNOWN COMMON COORDINATION / CONTROL ORIGIN
    -> structural REJECT

UNKNOWN / INCOMPLETE COORDINATION COVERAGE
    -> governance REJECT

REVIEWED COMPLETE_FOR_SCOPE
+ no declared coordination convergence
    -> reviewed coordination-origin precondition PASS
```

## Known dependence dominates completeness

Completeness never overrides a positive structural dependence.

If:

```text
controller A DELEGATED_FROM root
selector B DERIVED_FROM root
```

then the ancestry gate rejects before completeness can authorize anything.

```text
COMPLETE REVIEW != PERMISSION TO IGNORE KNOWN DEPENDENCE
```

Likewise, exact shared controller identity is rejected by the earlier exact-coordination gate first.

## Stale-review replay resistance

Changed graph:

```text
review(graph A) + graph B -> REJECT
```

Changed coordination declaration:

```text
review(coordination A) + coordination B -> REJECT
```

Changed source/mechanism basis with unchanged coordination refs:

```text
review(basis A + coordination C) + basis B + coordination C -> REJECT
```

The coordination review therefore cannot float free of the exact evidence/provenance basis it reviewed.

## Conservative PASS semantics

Passing means only that the structural source/mechanism/coordination gates passed and both bounded coordination completeness dimensions were reviewed `COMPLETE_FOR_SCOPE` for the exact scope and graph.

It does not mean:

```text
statistical independence
causal independence in every hidden dimension
randomized experimental independence
authority to claim independent replication
authority to create CapabilityClaim support
authority to update PR3 state
```

Therefore:

```text
REVIEWED COORDINATION-ORIGIN PRECONDITION PASS != INDEPENDENT REPLICATION
```

## New invariants

```text
NO DECLARED COMMON CONTROL ORIGIN != NO COMMON CONTROL ORIGIN
EMPTY COORDINATION GRAPH != COMPLETE COORDINATION GRAPH
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

## Resulting stack

After this closure:

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
```

## Non-goals and next boundary

This closure does not add automatic hidden-controller discovery, heuristic policy matching, reviewer authentication, evidence weighting, CapabilityClaim creation, Evaluation, PR3 state derivation, achievements, progression, or Player Window logic.

The next unresolved dependence class is no longer ordinary provenance identity/ancestry/completeness. A likely next boundary is temporal/intervention coupling: two observations may have fully separated reviewed source, mechanism, and coordination origins while still sharing one intervention episode, adaptive learning state, subject-history carryover, or common temporal window that makes them non-independent.
