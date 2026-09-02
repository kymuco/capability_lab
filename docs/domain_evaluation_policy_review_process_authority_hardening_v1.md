# PR12.7 Review-Admission Process Authority Hardening v1

## Purpose

This hardening closes the process- and module-reexecution gaps found during final PR12.7 review.

A runtime review admission must not become valid merely because a serialized ledger is structurally correct, nor may parent-process authority survive through `fork()`. The same rule must remain true after `importlib.reload(governance)` or after removing the governance module from `sys.modules` and importing a fresh module instance.

The corrected invariant is:

```text
REVIEW ADMISSION AUTHORITY
=
EXACT GOVERNED REVIEW TRANSITION
+
EXACT RUNTIME CAPABILITY OBJECT
+
ISSUING PROCESS ID
```

and therefore:

```text
PARENT-PROCESS REVIEW AUTHORITY != CHILD-PROCESS REVIEW AUTHORITY
GOVERNANCE MODULE REEXECUTION != AUTHORITY HARDENING REMOVAL
```

## Stable process guard

`review_process_authority.py` owns the non-serializable process guard outside any one governance module instance. It records a strong reference to the exact `DomainEvaluationPolicyReviewAdmission` object together with the PID that issued it.

The semantic capability still binds the exact policy/review transition:

- policy ref;
- specification digest;
- review id and review digest;
- predecessor review-ledger digest;
- exact one-review transition-successor digest;
- exact current review-ledger digest.

The process guard adds only issuer-process authority and does not change that semantic payload.

## Every governance execution is hardened

`governance_import_hardening.py` installs one narrow import finder for exactly:

```text
capability_lab.evaluation_policy.governance
```

Its loader never executes structural governance source into the retained live module. Each execution first builds a detached unregistered generation, then applies both PR12.7 runtime-authority hardeners to that generation before publication.

Final publication is guarded by one stable process-local `RLock` owned outside the governance module. Under that single critical section the loader publishes the already-hardened live namespace, updates the live generation pointer, and updates the stable package-level current-generation pointer. Package-level serializer selection takes the same lock. Thus a concurrent reader cannot pair newly exposed N+1 governance values with stale current generation N; it waits for the complete switch.

The stable current-generation pointer is also retained outside `sys.modules`. During a replacement import, Python may insert a new initializing governance module into `sys.modules` before its loader finishes. Package-level generation selection deliberately ignores that transient module and continues using the previous complete immutable generation until the replacement reaches the final locked publication point.

This happens for and remains safe across:

```text
first import
importlib.reload(governance)
del sys.modules[governance_name] + fresh import
concurrent reload publication
concurrent replacement-module initialization
```

Thus review PID binding is not a one-time package-initializer monkeypatch. A reloaded or replacement governance generation receives the same hardened issuer and strict validator before becoming the complete published generation.

## Fork behavior

The package registers an `after_in_child` hook that first reinitializes the governance publication `RLock`, then clears the stable review-process and registry-authority tables. The callback performs no imports. PID validation remains an independent enforcement mechanism even when a caller retains an older detached governance module instance.

The lock reset matters because `fork()` may occur while another parent thread owns the publication lock. Only the calling thread survives in the child, so inheriting the original locked object could otherwise deadlock later serialization or governance publication.

A stronger recovery is required if fork snapshots the parent after N+1 live namespace values have been copied but before the stable generation pointer advances from N. The publishing thread does not survive in the child, so the transition cannot finish there. The child hook therefore restores the live governance module from the exact last-complete immutable generation and its compatibility pointer before clearing runtime authorities. This converts an inherited partial publication back into one coherent fail-safe generation.

Thus:

```text
parent-issued admission + retained/reloaded module + fork child
-> FAIL

fork while another parent thread owns publication lock
-> child gets fresh publication lock
-> package-level serialization remains usable

fork during partial N -> N+1 publication
-> child restores complete N live namespace + pointer
-> no permanent mixed-generation state

exact terminal-review replay in child
-> fresh child-local review admission
-> PASS

parent process after child exits
-> original parent authority remains valid
```

The dedicated regressions include ordinary reload-before-fork, retained old-module process authority, fork while the publication lock is owned by another parent thread, and a deterministic fork taken exactly while live N+1 values are exposed but stable package generation remains N.

## Preserved identities

No serializable identity changes:

- PR12.6 policy specification JSON/digest unchanged;
- PR12.7 policy review JSON/digest unchanged;
- review-ledger JSON/digest unchanged;
- `DomainEvaluationPolicyReviewAdmission` remains non-serializable;
- registry JSON/digest unchanged;
- policy-admission receipt JSON/digest unchanged.

The PID and import-hardening machinery are runtime authority metadata only and are not inserted into deterministic semantic hashes.

## Threat model

This is a process-local public-API guard. It is not an attempt to make arbitrary hostile mutation of Python module internals, `sys.meta_path`, or process memory secure.

```text
PROCESS-BOUND REVIEW ADMISSION != REVIEWER AUTHENTICATION
PROCESS-BOUND REVIEW ADMISSION != SIGNATURE
PROCESS-BOUND REVIEW ADMISSION != TRUSTED TIME
PROCESS-BOUND REVIEW ADMISSION != POLICY APPLICATION
PROCESS-BOUND REVIEW ADMISSION != CLAIM SUPPORT
PROCESS-BOUND REVIEW ADMISSION != CLAIM TRUTH
PROCESS-BOUND REVIEW ADMISSION != CAPABILITY STATE
```

Cross-process durable authority still requires an authenticated deployment-level persistence/trust mechanism. Canonical JSON and deterministic SHA-256 values remain audit/integrity data, not authorization tokens.
