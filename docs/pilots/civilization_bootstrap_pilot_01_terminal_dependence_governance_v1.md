# Civilization Bootstrap Pilot 01 — Terminal Reviewed Dependence Governance

Status: **PR10.1 whole-ladder architectural hardening**

PR10.1 has six declared dependence families with the same bounded pattern:

```text
exact identity -> explicit ancestry -> reviewed completeness
```

The families are:

```text
source
mechanism
coordination/control
temporal/intervention/carryover
allocation/randomization
sampling/selection/cohort construction
```

## Terminal gate

The terminal PR10.1 dependence precondition is:

```text
validate_pilot_materialized_evidence_reviewed_dependence_preconditions_v1(...)
```

Lower family validators remain useful diagnostic primitives. Their PASS does not
mean that later PR10.1 families were checked.

```text
LOWER FAMILY PASS != TERMINAL PR10.1 PASS
```

The terminal gate delegates the complete structural/reviewed ladder to the
reviewed selection-origin gate, which composes every prior family.

## Multi-observation cardinality

The terminal gate is a cross-observation governance boundary. It therefore
requires at least two materialized observation slots.

```text
0 observations -> REJECT
1 observation  -> REJECT
2+ observations -> continue through terminal governance
```

An empty or singleton basis can still be inspected by lower family diagnostics,
but it cannot receive terminal PR10.1 dependence-precondition PASS. This prevents
a vacuous PASS from being reused as if a cross-observation dependence question had
actually been evaluated.

```text
SINGLE OBSERVATION
!= CROSS-OBSERVATION DEPENDENCE PRECONDITION
```

The two-slot minimum is only a structural domain requirement. It does not imply
that two observations are statistically independent or constitute replication.


## Exact reviewed-resolution binding

A terminal observation slot is no longer accepted from candidate + self-described
`EvidenceRecord` provenance alone. Every slot must have exact one-to-one coverage
by a `PilotReviewedMaterializationResolutionBinding` containing the selected
`PilotEvidenceMaterializationReview` and a resolver-issued
`PilotReviewedMaterializationResolutionReceipt`.

The receipt domain-separately binds:

```text
exact candidate_sha256
exact canonical review_sha256
exact review_id
exact EvidenceId
exact canonical full EvidenceRecord sha256
resolved_at
```

The binding validator additionally requires `MATERIALIZE`, exact reviewer/provenance
alignment, the frozen neutral Pilot 01 evidence-kind/summary/context mapping, and
receipt equality with the current complete `EvidenceRecord`. Therefore:

```text
SELF-DESCRIBED MATERIALIZATION NOTE != REVIEWED RESOLUTION
MATERIALIZE REVIEW ABSENT           -> TERMINAL REJECT
POST-RESOLUTION EvidenceRecord MUTATION -> TERMINAL REJECT
```

The receipt is structural governance metadata, not a signature, authenticated
reviewer identity, trusted timestamp, or proof of historical execution.

## Evidence identity uniqueness

The lowest multi-basis structural gate rejects duplicate `EvidenceId` values before
same-source/session analysis, and the terminal gate repeats the same check as
defense-in-depth before any reviewed scope digest is accepted.

```text
ONE EvidenceId != TWO CAUSAL OBSERVATION SLOTS
```

This prevents one logical evidence identity from representing multiple causal
basis entries and preserves deterministic ordering assumptions used by bounded
scope digests.

## Completeness-review temporal causality

All six completeness reviews concern an already-materialized evidence basis.
Each public reviewed family gate now enforces that its `reviewed_at` is no earlier
than the latest real `EvidenceRecord.recorded_at` in that family basis. The
terminal gate repeats the six-family aggregate chronology check as defense-in-depth.

```text
completeness reviewed_at < latest evidence recorded_at
    -> REJECT
```

This is an internal causal-order invariant only. It does not authenticate the
reviewer or timestamp.

## Selection-completeness public surface

The package public API includes the selection-completeness status, review record,
builders, exact scope/graph hashes, the reviewed selection-origin gate, and the
terminal dependence gate.

## Scope-hash wording

The selection completeness scope digest directly binds the per-observation
materialized/declared basis:

```text
candidate_sha256
evidence_id
exact_capture_source
upstream_sources
mechanisms
coordinations
temporals
allocations
selections
```

Changing a lower lineage graph or lower completeness review is not represented by
copying that graph/review into the selection scope digest. It is detected by that
lower family's own exact graph/scope binding when the terminal ladder executes.

## Whole-ladder regression

The terminal regression uses real Pilot 01 private workspaces, real capture
materialization, real PR2 `EvidenceRecord` values, real candidate-bound family
declarations, real lineage graphs, and real completeness review records.

It covers:

```text
real whole-ladder bounded PASS with exact reviewed-resolution receipts
missing reviewed-resolution receipt rejection
shared exact identity rejection in all six families
duplicate EvidenceId rejection
UNKNOWN completeness propagation from all six families
review chronology rejection for all six completeness families
empty terminal basis rejection
singleton terminal basis rejection
```

Existing family-specific suites continue to cover aliasing, directed ancestry,
transitive common-origin geometry, stale review bindings, graph validation, and
family-local adversarial semantics.

## Epistemic boundary

A terminal PASS means only:

> At least two materialized observations were supplied, and every currently
> declared PR10.1 dependence family passed its structural and reviewed bounded-
> governance preconditions for that exact evidence basis.

It does **not** mean:

```text
statistical independence
representative sampling
independent randomization
independent cohorts
absence of participant overlap
independent replication
capability support
successful performance
claim/evaluation authority
```

The terminal gate is a necessary governance precondition, not an independence
certificate.
