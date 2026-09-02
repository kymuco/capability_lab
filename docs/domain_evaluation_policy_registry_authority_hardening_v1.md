# PR12.7 Registry Admission Authority Hardening v1

## Purpose

This hardening closes the registry authority-confusion gap discovered during the final adversarial review of PR12.7 and preserves that boundary across governance module reexecution.

A `DomainEvaluationPolicyRegistry` is intentionally serializable. Structural registry validation proves canonical content, exact predecessor links, and immutable policy-reference binding. It does **not** prove that the supplied registry object actually passed `admit_domain_evaluation_policy_v1` in the current runtime.

The corrected invariant is:

```text
POLICY REGISTRY JSON
!= STRUCTURALLY VALID POLICY REGISTRY
!= GOVERNED POLICY-ADMISSION AUTHORITY

GOVERNANCE MODULE REEXECUTION
!= RESTORE STRUCTURAL RESOLVER AS PUBLIC AUTHORITY
```

## Audit value versus runtime authority

The following remain canonical portable audit data:

```text
DomainEvaluationPolicyReview
DomainEvaluationPolicyReviewLedger
DomainEvaluationPolicyRegistry
DomainEvaluationPolicyAdmissionReceipt
```

Their schema-v1 serialization and deterministic digests remain unchanged.

Runtime authority is separate. The hardened `admit_domain_evaluation_policy_v1` first performs exact structural admission and full receipt replay, then records process-local authority for the exact returned registry object and exact admitted policy entry.

That authority binds:

- exact registry object identity;
- issuer process id;
- exact current registry digest;
- exact admitted entry index;
- exact `EvaluationPolicyRef` and PR12.6 specification digest;
- exact terminal review id and review digest;
- exact predecessor-registry digest;
- exact one-entry transition-successor registry digest.

The hardened `resolve_admitted_domain_evaluation_policy_v1` requires that runtime authority before returning policy content.

## Every governance execution is hardened

`governance_import_hardening.py` wraps the loader for exactly `capability_lab.evaluation_policy.governance`. The structural source is executed first in a detached unregistered generation, and both runtime-authority hardeners are applied to that detached generation **before** any of its definitions are published through the live module.

Final publication uses one stable process-local `RLock` owned by the hardening layer. The same critical section publishes the already-hardened live namespace, switches the live compatibility generation pointer, and switches the stable package-level current-generation pointer. Package-level serializer generation selection takes the same lock, so it observes either the previous complete generation or the replacement complete generation; it cannot select stale N while serializing an N+1 value exposed during publication.

The hardening layer also retains the last complete immutable governance generation outside the transient `sys.modules` entry. During `del sys.modules[governance_name] + fresh import`, another thread may see an initializing replacement module in `sys.modules`, but package-level serialization does not treat that transient module as authority. It continues on the previous complete generation until the replacement finishes hardening and reaches the locked publication point.

Therefore all of these preserve the same protected admission/resolution surface:

```text
first governance import
importlib.reload(governance)
del sys.modules[governance_name] + fresh import
concurrent reload publication
concurrent replacement-module initialization
```

A governance reload cannot expose the structural resolver as admitted-policy authority. A manually constructed or JSON-restored registry remains audit-only immediately after reload or module replacement.

`registry_authority.py` also retains its compatibility `admit_domain_evaluation_policy_v1` and `resolve_admitted_domain_evaluation_policy_v1` names. Those functions are dynamic delegators: they resolve the **current already-hardened governance module** on each call. They do not retain or recapture the structural core, so reloading `registry_authority` cannot create a recursive wrapper or bypass the governance loader hardening.

## Consequences

```text
manual Registry(entries=(...))              -> audit data only
Registry.from_json(...)                      -> audit data only
structurally equal copied Registry           -> audit data only
manual registry after governance reload      -> audit data only
actual governed admission result             -> runtime authority
JSON restore + explicit governed replay      -> fresh runtime authority
```

A serialization round trip intentionally drops runtime authority. Restoring authority requires replay of both governed layers:

```text
exact review-ledger audit data
-> admit_domain_evaluation_policy_review_v1
-> sealed review-admission authority
-> admit_domain_evaluation_policy_v1
-> exact registry-admission authority
```

Exact replay does not add another policy entry or change the original admission receipt. It only re-establishes process-local authority for the exact current registry object.

## Growing registries

Authority is registry-object and current-registry-digest specific. If a second policy is appended, the grown registry is a different exact registry value. Authority issued for a policy in the predecessor registry is not silently promoted to the grown registry.

To resolve an older policy from the grown registry, the caller explicitly replays its exact review admission and exact policy admission against the grown canonical registry. The structural policy entry remains unchanged; replay only establishes authority for that policy in the exact grown registry snapshot.

This avoids implicit latest/current or inherited-authority semantics.

## Process boundary

Registry authority records the issuing PID. A POSIX fork child cannot use parent-issued authority even if Python object identities and module state are inherited. The package fork hook reinitializes the governance publication `RLock` before clearing the stable runtime review and registry authority tables, so a child cannot inherit an orphaned lock owner when another parent thread was publishing a generation at fork time. The callback performs no imports.

If the fork snapshots an in-progress publication after N+1 live namespace values were copied but before the stable current-generation pointer advanced from N, the vanished parent publisher can never complete that transition in the child. The same child hook therefore restores the live governance module from the exact last-complete immutable generation N and restores its compatibility pointer before execution resumes. The child never keeps a permanent mixed `live N+1 / stable N` state.

A child may explicitly replay canonical audit data to obtain child-local authority.

```text
PARENT REGISTRY AUTHORITY != CHILD REGISTRY AUTHORITY
PARENT PUBLICATION LOCK OWNERSHIP != CHILD PUBLICATION LOCK OWNERSHIP
PARTIAL PARENT PUBLICATION != CHILD PUBLISHED GENERATION
```

## Threat model

This is process-local public-API governance. It is not cryptographic authentication and does not defend against hostile code deliberately mutating module-private Python state, `sys.meta_path`, loaders, or arbitrary process memory.

```text
RUNTIME REGISTRY AUTHORITY != SIGNATURE
RUNTIME REGISTRY AUTHORITY != TRUSTED PERSISTENCE
RUNTIME REGISTRY AUTHORITY != GLOBAL-CURRENT REGISTRY PROOF
RUNTIME REGISTRY AUTHORITY != DISTRIBUTED CONSENSUS
```

A deployment requiring cross-process durable authority must add an authenticated persistence or external trust boundary rather than treating deterministic JSON/hash values as authorization tokens.

## Preserved semantics

This hardening does not change:

- PR12.6 specification serialization or digest;
- PR12.7 review serialization or digest;
- PR12.7 review-ledger serialization or digest;
- registry serialization or digest;
- admission-receipt serialization or digest;
- same-ref immutable content binding;
- original `admitted_at` on exact replay;
- policy-application semantics, because PR12.7 still performs no application;
- evidence, `ClaimEvaluation`, capability state, progression, permission, or presentation authority.

The corrected chain is:

```text
PR12.6 exact policy specification
        |
        v
PR12.7 HUMAN review
        |
        v
sealed review-admission authority
        |
        v
structural registry admission
        |
        v
process-local exact registry authority
        |
        v
exact admitted-policy resolution
        |
        X no evidence selection
        X no policy application
        X no ClaimEvaluation
        X no capability state
```
