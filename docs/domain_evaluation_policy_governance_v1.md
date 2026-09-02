# Governed Domain Evaluation Policy Approval and Immutable Registry v1

PR12.7 adds governance for admitting one exact PR12.6 domain evaluation policy specification. It does **not** apply policy to evidence, evaluate claims, derive capability state, select a globally current policy, or authenticate a registry.

## Boundary

```text
POLICY SPECIFICATION != ADMITTED POLICY
POLICY REVIEW != POLICY APPLICATION
POLICY APPROVAL != CLAIM SUPPORT
POLICY APPROVAL != CLAIM TRUTH
POLICY REGISTRY != EVALUATOR
ADMITTED POLICY != CAPABILITY STATE
RAW APPROVAL != TERMINAL GOVERNANCE
SERIALIZED REVIEW LEDGER != TERMINAL REVIEW AUTHORITY
REVIEW ADMISSION CAPABILITY != SERIALIZABLE AUDIT ARTIFACT
```

The only new authority in this boundary is the ability to record that one exact declarative policy content revision has passed an explicit HUMAN terminal-review admission transition and has been appended to one immutable registry lineage for later governed use.

## Exact review basis

A `DomainEvaluationPolicyReview` binds one exact `EvaluationPolicyRef`, the exact PR12.6 canonical `specification_sha256`, one declared `HUMAN` reviewer reference, one review id, `APPROVE` or `REJECT`, canonical review time, and a non-empty rationale.

The review is validated by replaying the exact PR12.6 specification digest. A policy reference by itself is never sufficient review identity.

```text
POLICY REF != POLICY CONTENT
SAME POLICY REF + DIFFERENT DIGEST != SAME REVIEW BASIS
```

Review timestamps establish only local governance chronology. They are not trusted timestamps, signatures, authentication, professional credentials, or external authorization.

## Terminal review ledger and sealed runtime admission

`DomainEvaluationPolicyReviewLedger` is a canonical append-only **structural/audit value**. Its review identity is the exact pair:

```text
(EvaluationPolicyRef, specification_sha256)
```

Within one valid structural lineage, the exact same review may replay idempotently; a conflicting second terminal review for the same exact policy content fails closed; one review id may not be rebound to another policy specification; and removing or changing an admitted prefix is not a valid successor transition.

A populated ledger is deliberately **not authority by itself**. In particular, neither of these establishes registry-admission authority:

```text
DomainEvaluationPolicyReviewLedger(reviews=(raw_approval,))
DomainEvaluationPolicyReviewLedger.from_json(serialized_populated_ledger)
```

The terminal-review transition is instead performed by `admit_domain_evaluation_policy_review_v1`. That function returns two distinct outputs:

```text
canonical successor review ledger
+
runtime-only DomainEvaluationPolicyReviewAdmission capability
```

The sealed capability binds:

```text
policy_ref
specification_sha256
review_id
review_sha256
predecessor_review_ledger_sha256
transition_successor_review_ledger_sha256
exact current review_ledger_sha256
```

`DomainEvaluationPolicyReviewAdmission` has no ordinary public constructor and no dict/JSON serialization path. Registry admission requires both the exact review ledger and a capability issued by the terminal-review admission path. Direct construction, deserialization of a populated ledger, or a manually forged capability object therefore does not satisfy the public authority boundary.

The exact current-ledger binding is intentional. If the review ledger later grows or changes, an older capability is stale. The exact already-admitted review may be replayed through `admit_domain_evaluation_policy_review_v1` against the new canonical ledger to obtain fresh runtime authority without adding a duplicate review.

```text
RAW REVIEW
    |
    v
admit_domain_evaluation_policy_review_v1
    |
    +--> canonical audit ledger
    |
    +--> sealed runtime review-admission capability
              |
              v
      policy registry admission
```

`APPROVE` may proceed to registry admission only with that sealed transition authority. `REJECT` can have valid terminal-review authority but still creates no registry entry.

```text
APPROVE + sealed review admission -> may proceed
REJECT  + sealed review admission -> no registry entry
REJECT  != negative evidence
APPROVE != claim support
```

### Runtime authority and process boundaries

The sealed capability is a **process-local public-API authority boundary**, not cryptography. Review and ledger JSON remain portable audit data, but runtime authority is intentionally not restored merely by deserializing them. A host crossing a process boundary must explicitly replay the terminal-review admission function before attempting policy-registry admission.

Issued capabilities are retained by the PR12.7 runtime for process lifetime so exact object identity cannot be recycled into authority through ordinary Python object-id reuse. This small in-memory issuance table is intentionally not persistence and is not a global registry. Lifecycle/eviction policy for very long-running hosts is outside v1 and must not weaken exact issued-object validation.

PR12.7 does not claim protection against hostile Python code that intentionally mutates module-private implementation state or arbitrary process memory. Such a threat model requires an authenticated external trust boundary, capability sandbox, process isolation, signatures, or trusted persistence outside this PR.

```text
SEALED RUNTIME CAPABILITY != SIGNATURE
SEALED RUNTIME CAPABILITY != REVIEWER AUTHENTICATION
PRIVATE PYTHON STATE != SECURITY BOUNDARY AGAINST HOSTILE PROCESS CODE
```

## Immutable registry binding

Each admitted registry entry stores:

```text
policy_ref
specification_sha256
full canonical PR12.6 specification
review_id
review_sha256
admitted_at
predecessor_registry_sha256
```

The registry therefore binds one exact policy reference permanently to one exact policy content value within that lineage.

```text
same policy_ref + same exact content -> idempotent admission replay only
same policy_ref + different content  -> REJECT
changed content                      -> NEW EvaluationPolicyRef revision
```

There is no v1 policy overwrite, replacement, supersession, alias, compatibility range, fuzzy revision match, or latest-wins rule.

Each entry also binds the SHA-256 of the exact registry prefix that preceded it. Reconstructing a registry validates every predecessor link. Removal, reordering, or mutation of an earlier entry therefore breaks exact lineage replay.

The registry hash is a deterministic integrity identifier for one registry value. It is not a signature or proof that this is the globally authoritative registry.

## Exact resolution only

`resolve_admitted_domain_evaluation_policy_v1` requires both exact `EvaluationPolicyRef` and exact `specification_sha256`, then replays the embedded PR12.6 specification digest before returning the specification.

There is deliberately no API for latest policy, active policy, preferred revision, compatible revision, superseding policy, or automatic migration. Those are separate selection/activation authorities and are outside PR12.7.

## Admission receipt

A successful new admission produces `DomainEvaluationPolicyAdmissionReceipt` binding:

```text
policy_ref
specification_sha256
review_id
review_sha256
predecessor_registry_sha256
successor_registry_sha256
admitted_at
```

Full receipt validation requires the same sealed review-admission capability and replays the exact terminal `APPROVE`, predecessor registry, one-entry successor transition, appended registry entry, exact PR12.6 content, and both registry digests.

```text
RECEIPT != SIGNATURE
RECEIPT != AUTHENTICATION
RECEIPT != TRUSTED TIME
RECEIPT != GLOBAL-CURRENT REGISTRY PROOF
```

A receipt is an integrity and audit artifact for one deterministic transition.

## Serialization and runtime strictness

Review, review-ledger, registry, and receipt serialization use schema v1 and canonical compact JSON. The **runtime review-admission capability is deliberately excluded from serialization**. The boundary rejects unknown or missing fields, duplicate JSON object keys, wrong container types, non-string object keys at runtime-dict boundaries, malformed typed references, noncanonical timestamps, noncanonical embedded PR12.6 policy content, behavioral/subclassed scalar values where exact built-in storage is required, post-construction semantic corruption when strict replay is requested, and unissued or stale runtime review-admission capabilities.

This strictness is intentional. PR12.6 demonstrated that Python values with attacker-controlled `__eq__`, `__str__`, or scalar subclasses can otherwise widen an exact policy boundary. PR12.7 therefore canonicalizes before semantic equality and fails closed on non-exact runtime storage.

## No policy-application authority

PR12.7 does not import or expose an authority to choose or derive evidence or an evidence basis, a capability claim, evidence bearing or reliability, requirement coverage, conflict status, an evaluation conclusion, `ClaimEvaluation`, capability state, score, mastery, readiness, permission, progression, or presentation output.

```text
ADMITTED POLICY
!= APPLIED POLICY
!= CLAIM EVALUATION
!= CAPABILITY STATE
```

A later policy-application boundary must consume an exact admitted policy together with a complete governed claim-relative evidence basis and explicit governed mapping/judgment. It must not infer independent replication from record count.

## Deliberately unresolved downstream problem

PR12.7 does not make generic directional evaluation ready. Before a future domain-sufficient evaluator is safe, the generic path still needs a way to establish a **complete claim-relative evidence basis** so a caller cannot cherry-pick only favorable evidence. It also needs explicit governance for dependence/repetition where such semantics matter.

A safer continuation is therefore conceptually:

```text
PR12.7 admitted exact policy
-> complete governed claim-relative evidence basis
-> explicit dependence/repetition governance where required
-> exact policy application
-> directional ClaimEvaluation
-> existing complete portfolio/state path
```

This ordering preserves the existing rule:

```text
TWO EvidenceRecord VALUES != TWO INDEPENDENT OBSERVATIONS
```

## Non-goals

```text
PR12.7 != POLICY AUTHORING
PR12.7 != POLICY APPLICATION
PR12.7 != EVIDENCE MAPPING
PR12.7 != MULTI-EVIDENCE EVALUATION
PR12.7 != CONFLICT RESOLUTION
PR12.7 != EVIDENCE INDEPENDENCE GOVERNANCE
PR12.7 != ClaimEvaluation
PR12.7 != PersonalCapabilityState
PR12.7 != POLICY SUPERSESSION
PR12.7 != LATEST-WINS
PR12.7 != GLOBAL DISTRIBUTED REGISTRY CONSENSUS
PR12.7 != CRYPTOGRAPHIC REVIEWER AUTHENTICATION
PR12.7 != HOSTILE-PROCESS MEMORY SECURITY
```
