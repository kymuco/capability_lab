# Deterministic Derivation Historical Boundary v1

Status: **PR4 normative supplement**

PR4's deterministic supported-state baseline is a stateless pure derivation function. Its reproducibility guarantee is intentionally scoped to exact input content:

```text
same exact EpistemicRecordSet
+ same exact CompetenceFrame
+ same canonical DeterministicStateDerivationRequest
+ same algorithm revision
=> exactly equal PersonalCapabilityState
```

This guarantee must not be overread as a persistent identity registry.

```text
DETERMINISM != CROSS-SNAPSHOT ID IMMUTABILITY
DERIVATION != PERSISTENCE GOVERNANCE
```

## Historical reconstruction

Historical reconstruction requires every selected `ClaimEvaluationId` and its referenced claim to remain available with the same immutable material content used by the original derivation. If a selected evaluation is absent from a later/incomplete `EpistemicRecordSet`, PR4 rejects reconstruction rather than silently substituting another evaluation.

```text
MISSING SELECTED EVALUATION != UNKNOWN
MISSING SELECTED EVALUATION != LATEST SUBSTITUTE
```

Unselected additions remain inert. A later epistemic snapshot may contain additional evidence, claims, or evaluations without changing an earlier state as long as the exact derivation request still selects the same immutable evaluation records.

## Opaque record ids are not content hashes

`ClaimEvaluationId` and `PersonalCapabilityStateId` are nominal opaque record identifiers. PR4 does not infer material identity merely from string equality.

Two independently assembled snapshots can be structurally valid while reusing the same opaque `ClaimEvaluationId` for different material evaluation content. Doing so violates the stronger PR2 persistence/import governance contract, but a stateless PR4 call cannot discover that historical reuse without a registry or prior snapshot.

Accordingly:

```text
SAME OPAQUE EVALUATION ID
!=
SAME EXACT EVALUATION CONTENT
```

The deterministic guarantee compares exact record content, not only identifier strings.

## State-id reuse and recomputation

`DeterministicStateDerivationRequest.state_id` is supplied by the caller so PR4 never generates randomness. The function validates one derivation run but does not maintain a historical state-id registry.

If a caller supplies the same `PersonalCapabilityStateId` with materially different selected evaluations, bindings, time boundary, frame, concept, or other effective input, PR4 can construct a materially different state carrying that same nominal id. Persisting both as one historical identity would violate the PR3 contract:

```text
RECOMPUTATION != MUTATION
SAME STATE ID MUST NOT BE REUSED FOR MATERIALLY DIFFERENT STATE CONTENT
```

Enforcement across snapshots belongs to persistence/import/synchronization governance, where prior state records are available for comparison. PR4 must not add a hidden global registry, database, clock, or mutable process state merely to enforce a responsibility owned by a different layer.

```text
STATELESS DERIVATION CANNOT PROVE GLOBAL ID UNIQUENESS
PERSISTENCE MUST ENFORCE CROSS-SNAPSHOT NO-ID-REUSE
```

A governed recomputation that materially changes state therefore requires a fresh state id before persistence, even though the pure derivation function cannot enforce that requirement across independent calls by itself.

## Snapshot retention

A persisted historical state remains an immutable record even if a later working epistemic snapshot omits some of its basis evaluations. However, validating or reproducing that state requires access to the matching historical epistemic material.

PR4 does not introduce archival storage, snapshot digests, content-addressed evaluation identities, or a historical registry. Those remain future persistence/integrity concerns.

## Non-goals

This boundary does not add:

- a state-id registry;
- cross-snapshot evaluation-id reuse detection;
- database persistence;
- archival snapshot storage;
- content-addressed evaluation identities;
- automatic state-id generation;
- silent fallback to latest evaluations;
- mutation of historical state.
