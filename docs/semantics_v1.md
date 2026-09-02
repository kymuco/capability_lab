# Shared Capability Semantics v1

Status: **PR1 implementation contract**

PR1 implements the first person-agnostic domain model in Capability Lab: stable capability lineages, exact semantic revision references, namespace-scoped collision boundaries, bounded concepts, typed relation families, and deterministic catalog snapshots.

## Boundary

This layer contains no person-scoped evidence, claims, evaluations, mastery state, achievements, recommendations, model inference, synchronization, or Commons moderation. `CapabilityCatalog` is a local immutable semantic graph snapshot, not `HumanCapabilityCommons`.

## Identity

```text
CAPABILITY ID != DISPLAY NAME
CAPABILITY ID != GRAPH PATH
CAPABILITY ID != CURRENT PARENT
NAMESPACE != AUTHORITY
NAMESPACE != QUALITY
ALIAS != ID
```

A capability lineage uses `<namespace>:<key>`. Dots inside a namespace are collision-management syntax, not capability hierarchy or trust level. Namespace identity prevents collisions only within a catalog or governance regime that agrees on ownership of that namespace; PR1 does not claim globally collision-proof identities across mutually untrusted catalogs.

`CapabilityConceptRef` identifies one exact declared semantic revision as `<namespace>:<key>@<revision>`. Revision syntax is canonical positive ASCII decimal without leading zeroes. The reference is exact only relative to the namespace/catalog governance that issued the record; it is not a cryptographic content address. Future provenance or snapshot-digest layers may strengthen cross-catalog verification.

A catalog snapshot contains at most one record for a `CapabilityId`; it is not a revision-history store. Any persisted record change that must remain historically distinguishable should advance revision. A material change to what evidence could support or contradict the capability meaning requires a new identity rather than merely a new revision. Splits and merges create new identities. `DEPRECATED` preserves old identity instead of deleting it.

Human-readable names and aliases are metadata, not a declaration that one language or cultural label is globally canonical. Aliases may be ambiguous across concepts; future lookup/search must surface ambiguity rather than silently treating an alias as identity. Full localization remains future work and must not require changing machine identity.

## Relation families

Stored kinds map to exactly one family:

- structural: `SPECIALIZES`, `OVERLAPS`;
- dependency: `REQUIRES`, `SUPPORTED_BY`, `ENABLED_BY`;
- empirical development: `COMMONLY_PRECEDES`, `COMMONLY_COOCCURS`, `TRANSFER_OBSERVED_TO`.

`GENERALIZES` is an inverse query interpretation of `SPECIALIZES`, not a stored duplicate edge.

All dependency relations use the same orientation: **source is the capability being described; target is the dependency/supporting capability**.

- `A REQUIRES B`: B is asserted necessary for A under the stated relation scope. Necessity is categorical in v1; `REQUIRES` does not carry ordinal strength.
- `A SUPPORTED_BY B`: B materially helps A without asserting necessity. This is the only v1 dependency kind that may use ordinal `WEAK`, `MODERATE`, or `STRONG` strength.
- `A ENABLED_BY B`: B opens or materially changes feasibility of A without asserting that it is the only route. This relation is categorical in v1 and does not carry ordinal strength.

Relation strength is semantic metadata, not probability; `RelationStrength.rank` defines the explicit ordering for graded support. Empirical relations require provenance and must not silently become dependency, causal, required-path, or optimal-path assertions.

`OVERLAPS` and `COMMONLY_COOCCURS` are symmetric and canonicalize endpoint order. Other v1 kinds are directional. Self-relations are rejected. `SPECIALIZES` must be acyclic; dependency cycles are not globally forbidden, so downstream algorithms must not assume that the dependency subgraph is a DAG.

`RelationScope` keys are relation-local qualifiers in v1. The same key on unrelated edges does not create a global scope identity.

Relations themselves are snapshot-scoped semantic records in v1; PR1 does not introduce persistent relation IDs or relation revision history. Historical consumers that require exact relation geometry must preserve the relevant catalog snapshot/provenance rather than assume the latest catalog has identical edges.

## Cross-namespace composition

Relations may cross namespaces when both endpoints exist in the catalog. Packs should reference reusable concepts instead of copying them merely to preserve a visual tree.

## Runtime and serialization validity

Type annotations are not validation. Public domain constructors reject invalid runtime types for identity-bearing enums, relation endpoints, scopes, lifecycle values, collection members, and other invariant-bearing fields.

Catalog ingestion is strict. Schema-v1 readers reject unknown fields, strings where arrays are required, duplicate JSON object keys, non-standard JSON numeric constants, malformed nested records, dangling endpoints, duplicate semantic edges, and `SPECIALIZES` cycles.

Equivalent valid catalogs built in different insertion orders serialize to the same compact JSON representation. The specialization-cycle check is iterative rather than recursion-depth-dependent, so long valid semantic chains do not fail merely because of Python's recursion limit.

## Explicit non-goals

PR1 does not implement `CapabilitySubject`, `EvidenceRecord`, `CapabilityClaim`, `ClaimEvaluation`, `PersonalCapabilityState`, scoring, progression, achievements, model inference, databases, synchronization, Commons governance, globally authoritative namespace allocation, content-addressed catalog snapshots, full localization infrastructure, or the full Civilization Bootstrap graph.

The small Civilization Bootstrap fixture exists only to prove that the semantic model can represent the initial wedge.
