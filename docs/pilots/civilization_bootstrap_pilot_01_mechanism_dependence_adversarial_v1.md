# Civilization Bootstrap Pilot 01 — Explicit Acquisition/Governance Mechanism Dependence

Status: **PR10.1 adversarial closure**

This closure addresses the next false-replication boundary after reviewed source-origin completeness.

Earlier PR10.1 gates can reject exact capture reuse, same-session lineage, repeated elicitation lineage, exact shared upstream sources, source alias/ancestry/common-origin dependence, and incomplete reviewed source-origin coverage.

The remaining geometry is different:

```text
observation A -> source A
observation B -> source B
source-origin review = COMPLETE_FOR_SCOPE
source ancestry = separated

BUT

observation A -> mechanism X
observation B -> mechanism X
```

Therefore:

```text
SOURCE-SEPARATED != MECHANISM-SEPARATED
REVIEWED SOURCE ORIGIN != INDEPENDENT REPLICATION
```

## Explicit mechanism declarations

PR10.1 adds `PilotObservationMechanismKind` with:

```text
OPERATOR
MODEL_RUN
ACQUISITION_PIPELINE
ENVIRONMENT
TOOL_EXECUTION
REVIEW_PROCESS
OTHER
```

and `PilotObservationMechanismRef(kind, ref)` where `ref` is a canonical opaque ASCII identifier.

A mechanism is dependence evidence only when explicitly declared. Existing fields are not silently promoted:

```text
same reviewer_ref != same review mechanism
same tool name != same tool execution
same model family != same model run
same operator name != same bounded acquisition mechanism
```

## Candidate-bound metadata

`PilotMaterializationMechanismDeclaration` contains:

```text
candidate_sha256
mechanisms[]
```

`build_pilot_materialization_mechanism_declaration_v1(...)` binds the declaration to the exact materialization candidate digest.

```text
DECLARATION FOR CANDIDATE A != DECLARATION FOR CANDIDATE B
```

An empty declaration is valid but means only that no mechanism refs were supplied:

```text
EMPTY DECLARATION != NO SHARED MECHANISM
```

## Exact dependence key

`pilot_observation_mechanism_dependence_key_v1(...)` hashes the exact typed `{kind, ref}` pair under a dedicated domain and returns:

```text
pilot_observation_mechanism:<sha256>
```

Equality means the same exact declared typed mechanism identity. Different keys do not prove distinct causal mechanisms or independence. Validator errors use the hashed key rather than echoing raw mechanism refs.

## Mechanism entry and gate

`PilotMaterializedEvidenceMechanismEntry` pairs one exact source-lineage entry with its exact candidate-bound mechanism declaration.

The new gate is:

```text
validate_pilot_materialized_evidence_shared_mechanism_preconditions_v1(...)
```

It first composes the existing reviewed source-origin gate. Only after all earlier exact-source/session/elicitation/source-ancestry/completeness checks pass does it inspect mechanism declarations.

If two observations share one exact mechanism key, the gate rejects:

```text
A -> MODEL_RUN:run_x
B -> MODEL_RUN:run_x
=> REJECT
```

and likewise:

```text
A -> ACQUISITION_PIPELINE:pipeline_x
B -> ACQUISITION_PIPELINE:pipeline_x
=> REJECT
```

The historical EvidenceRecords remain valid; only the stronger interpretation that they satisfy shared-mechanism independence preconditions is rejected.

## Conservative PASS semantics

Distinct exact mechanism refs may pass this equality gate:

```text
A -> TOOL_EXECUTION:run_a
B -> TOOL_EXECUTION:run_b
```

but:

```text
DIFFERENT MECHANISM REFS != INDEPENDENT MECHANISMS
```

The refs could still be aliases, descendants of one pipeline, executions under one hidden supervisor, or otherwise related.

Likewise:

```text
SHARED-MECHANISM PRECONDITION PASS != INDEPENDENT REPLICATION
```

## New invariants

```text
SOURCE INDEPENDENCE PRECONDITIONS != MECHANISM INDEPENDENCE PRECONDITIONS
SAME EXACT DECLARED MECHANISM => KNOWN COMMON MECHANISM DEPENDENCE
SAME TOOL NAME != SAME TOOL EXECUTION
SAME REVIEWER REF != SAME REVIEW PROCESS
EMPTY MECHANISM DECLARATION != NO MECHANISM
DIFFERENT MECHANISM KEYS != INDEPENDENT MECHANISMS
```

## Non-goals

This closure does not add automatic mechanism discovery, inference from tool/reviewer metadata, environment fingerprinting, operator authentication, mechanism signatures, mechanism alias/ancestry graphs, mechanism-declaration completeness review, probabilistic dependence estimation, evidence weighting, independent-replication claims, capability evaluation, PR3 state derivation, achievements, progression, or Player Window behavior.

## Next unresolved boundary

Exact mechanism equality still cannot detect:

```text
mechanism A != mechanism B
BUT
mechanism A and mechanism B share an alias, ancestor, supervisor, pipeline, or hidden origin
```

and mechanism declarations themselves may be incomplete.

The next controlled layer should therefore address explicit mechanism-to-mechanism lineage and/or reviewed mechanism-disclosure completeness rather than heuristic similarity.
