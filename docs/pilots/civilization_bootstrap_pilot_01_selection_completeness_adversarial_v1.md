# Civilization Bootstrap Pilot 01 — Reviewed Selection Completeness

Status: **PR10.1 adversarial closure**

This closes the sampling / selection / cohort-construction family:

```text
exact identity -> explicit ancestry -> reviewed bounded completeness
```

The remaining false-replication geometry after ancestry is incomplete disclosure:
declared selection refs and lineage closures can be disjoint while a relevant
sampling-frame, cohort-construction, recruitment, resampling, or inclusion-policy
origin was omitted.

Two axes are reviewed independently:

```text
SELECTION_DECLARATIONS
SELECTION_LINEAGE_GRAPH
```

Both use `PilotSelectionCompletenessStatus` with `COMPLETE_FOR_SCOPE`,
`INCOMPLETE`, and `UNKNOWN`. Both must be `COMPLETE_FOR_SCOPE`; the other states
fail closed.

The review is bound to two independent digests:

```text
pilot_observation_selection_origin_scope_sha256_v1(...)
pilot_observation_selection_lineage_graph_sha256_v1(...)
```

The exact scope includes, per observation:

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

The selection graph digest binds every canonical selection relation. Changing any
per-observation field listed above changes the selection scope digest. Changing a
lower lineage graph or lower completeness review is detected by that lower
family's own exact scope/graph binding when the composed PR10.1 ladder executes;
those lower review objects are not copied into the selection scope digest.

The family gate is:

```text
validate_pilot_materialized_evidence_reviewed_selection_origin_preconditions_v1(...)
```

It calls the existing selection-ancestry gate first. Therefore known common
selection identity or ancestry always dominates completeness.

The terminal whole-PR10.1 dependence gate is separately defined as:

```text
validate_pilot_materialized_evidence_reviewed_dependence_preconditions_v1(...)
```

A selection-family PASS is not a substitute for that terminal composition
contract.

Three-way semantics:

```text
KNOWN COMMON SELECTION ORIGIN
    -> structural REJECT

UNKNOWN / INCOMPLETE SELECTION COVERAGE
    -> governance REJECT

COMPLETE_FOR_SCOPE + no declared convergence
    -> bounded selection-origin PRECONDITION PASS
```

Still:

```text
PASS != representative sampling
PASS != independent cohorts
PASS != absence of participant overlap
PASS != statistical independence
PASS != independent replication
```

After this closure, six families have the full three-step pattern: source,
mechanism, coordination/control, temporal/intervention/carryover,
allocation/randomization, and sampling/selection/cohort construction.

That symmetry is now an architectural stop point. Before adding another mirrored
family, PR10.1 should undergo a whole-ladder adversarial review and require a
concrete remaining false-replication geometry.
