# PR12.12 — Conservative Domain-Sufficient Directional ClaimEvaluation v1

Status: implementation contract  
Architecture issue: #52  
Base: `main @ 31449efebeb675f37dcc5cc166a1e5f0c680f291`

## Purpose

PR12.12 is the first generic PR12 layer allowed to emit a real claim-wide
`ClaimEvaluation`.

It does not introduce a new learned evaluator, score, confidence threshold,
majority rule, or policy-specific conflict resolver. It deterministically
materializes the direction already implied by:

1. the complete PR12.9 evidence-disposition universe;
2. the PR12.10 lineage/non-inference audit;
3. one exact runtime-authorized PR12.7 domain policy;
4. one exact HUMAN-approved PR12.11 requirement mapping;
5. the frozen PR12.6 sufficiency semantics.

The frozen sufficiency rule remains:

```text
all required policy requirements explicitly COVERED
```

PR12.12 does not reinterpret it.

## Authority chain

```text
exact PR12.7 runtime-authorized policy
        +
complete exact PR12.9 dispositions
        +
exact PR12.10 lineage/non-inference basis
        +
complete PR12.11 mapping proposal
        +
terminal HUMAN APPROVE
        +
current process-local PR12.11 review admission
        +
exact PR12.11 application receipt
        ↓
full governed replay
        ↓
deterministic PR2 ClaimEvaluation
        +
strict PR12.12 audit receipt
```

PR12.12 adds no new HUMAN decision and no new runtime permission capability.
Its conclusion is a pure deterministic consequence of already-governed inputs.

A serialized PR12.12 receipt is audit data, not authority. Validation fully
replays the upstream governance chain.

## Anti-cherry-picking invariant

The most important new boundary is:

```text
PR12.11 requirement mapping
!=
directional evidence selection
```

PR12.11 answers which evidence semantically covers which policy requirement.
It is not allowed to choose which relevant evidence counts directionally.

PR12.12 therefore places **every exact PR12.9 disposition** into the emitted
`ClaimEvaluation.evidence_assessments`.

Consequences:

```text
mapped SUPPORTS + unmapped CONTRADICTS -> conflict remains visible
unmapped CONTRADICTS                   -> cannot be discarded
unmapped SUPPORTS                      -> cannot be discarded
NOT_RELEVANT                           -> contributes no direction
INDETERMINATE                          -> relevant but non-directional
```

This prevents the HUMAN semantic mapping boundary from becoming a hidden
cherry-picking mechanism.

## Deterministic conclusion table

Let:

```text
complete = PR12.11.required_requirement_coverage_complete
support  = any complete PR12.9 disposition is SUPPORTS
contra   = any complete PR12.9 disposition is CONTRADICTS
```

Then:

| Requirement coverage | Directional basis | CoverageStatus | ConflictStatus | EvaluationConclusion |
|---|---|---|---|---|
| incomplete | any | PARTIAL | UNRESOLVED only if support+contra, else NONE | INSUFFICIENT |
| complete | support only | SUFFICIENT_FOR_CLAIM | NONE | SUPPORTED |
| complete | contra only | SUFFICIENT_FOR_CLAIM | NONE | CONTRADICTED |
| complete | support + contra | SUFFICIENT_FOR_CLAIM | UNRESOLVED | MIXED |
| complete | neither | SUFFICIENT_FOR_CLAIM | NONE | ABSTAINED |

No v1 path emits `ConflictStatus.RESOLVED_BY_POLICY`.

PR12.6 defines no conflict-resolution rule, so PR12.12 must preserve a real
support/contradiction conflict instead of deciding a winner.

### Complete + no direction

PR2 requires `SUFFICIENT_FOR_CLAIM` to contain at least one relevant assessment.

That is compatible with the table. PR12.11 forbids `NOT_RELEVANT` evidence from
covering a requirement. Therefore a valid complete mapping with neither SUPPORTS
nor CONTRADICTS necessarily contains at least one mapped `INDETERMINATE`
assessment. An all-`NOT_RELEVANT` universe cannot legitimately obtain complete
required coverage.

## Reliability and lineage

PR12.12 deliberately ignores reliability when choosing direction:

```text
LOW SUPPORTS
HIGH SUPPORTS
UNASSESSED SUPPORTS
```

all contribute the same boolean fact:

```text
has_support = true
```

Likewise PR12.10 lineage is mandatory upstream audit context but is not converted
into:

- independent evidence counts;
- replication counts;
- weights;
- confidence;
- majority voting;
- positive independence.

Shared lineage may be important to a later policy version, but PR12.6 defines no
such directional rule in v1.

## Real PR2 ClaimEvaluation

The emitted evaluation is a normal immutable PR2 `ClaimEvaluation`.

Its fields are governed as follows:

```text
claim_id
    = exact PR12.11 claim

policy_ref
    = exact runtime-authorized admitted policy

evaluator_ref
    = RULE:capability_lab:pr12_12_domain_directional_rule_v1

evaluated_at
    = exact terminal PR12.11 HUMAN mapping review reviewed_at

evidence_assessments
    = complete exact PR12.9 dispositions

coverage
conflict_status
conclusion
    = deterministic table above

rationale
    = fixed PR12.12 rule rationale
```

No caller parameter exists for any of those directional decisions.

## Deterministic identity

The `ClaimEvaluationId` is derived from a domain-separated SHA-256 digest of
every stored evaluation field except the id itself.

This means:

```text
same exact governed basis -> same evaluation content -> same evaluation id
```

Callers cannot mint semantically duplicate evaluations by selecting a different
timestamp, evaluator, rationale, conclusion, or arbitrary id.

The full evaluation also receives a separate domain-separated SHA-256 audit
digest.

## PR12.12 receipt

`ClaimDomainPolicyDirectionalEvaluationReceipt` binds:

```text
snapshot_sha256
claim_id
subject_ref
concept_ref
claim_scope
as_of
policy_ref
specification_sha256
disposition_coverage_sha256
lineage_dependence_sha256
requirement_application_sha256
mapping_review_id
mapping_review_sha256
mapping_reviewed_at
evaluation_id
evaluation_sha256
coverage_status
conflict_status
conclusion
```

The receipt has strict canonical dict/JSON serialization:

- exact key set;
- exact scalar types;
- duplicate JSON object keys rejected;
- unknown/missing fields rejected;
- noncanonical JSON rejected;
- nonstandard JSON constants rejected;
- exact enum values required.

The receipt is not a capability or authorization token.

## Replay validation

`validate_claim_domain_policy_directional_evaluation_v1(...)` does not trust the
supplied evaluation or receipt.

It:

1. strict-validates their stored types;
2. fully replays PR12.11;
3. thereby replays PR12.9, PR12.10, PR12.7 authority and policy applicability;
4. revalidates the exact current HUMAN mapping-review admission;
5. rebuilds the expected evaluation;
6. rebuilds the expected receipt;
7. requires exact typed equality.

A forged conclusion, forged application-completeness boolean, forged evaluation
digest, changed claim, stale policy authority, or stale mapping-review authority
therefore fails closed.

## Persistence boundary

PR12.12 creates a real `ClaimEvaluation`, but it does not silently mutate an
`EpistemicRecordSet`.

Persistence remains a separate append-only operation under PR11.3.

Likewise PR12.12 does not:

```text
select a preferred historical evaluation
supersede an older evaluation
derive PersonalCapabilityState
approve a state transition
derive progression
emit readiness/mastery
authorize an action
render Player Window presentation
```

Those boundaries remain downstream and separately governed.

## Public API

The PR12.12 surface is exported from `capability_lab.evaluation_policy`:

```python
ClaimDomainPolicyDirectionalEvaluationReceipt
DomainPolicyDirectionalEvaluationError
InvalidDomainPolicyDirectionalEvaluation

build_claim_domain_policy_directional_evaluation_v1(...)
validate_claim_domain_policy_directional_evaluation_v1(...)

claim_domain_policy_directional_claim_evaluation_sha256_v1(...)
claim_domain_policy_directional_evaluation_receipt_sha256_v1(...)

claim_domain_policy_directional_evaluation_receipt_to_dict(...)
claim_domain_policy_directional_evaluation_receipt_from_dict(...)
claim_domain_policy_directional_evaluation_receipt_to_json(...)
claim_domain_policy_directional_evaluation_receipt_from_json(...)
```

It is deliberately not exported from the package root.

## Explicit non-goals

```text
PR12.12 != LEARNED EVALUATOR
PR12.12 != CONFIDENCE MODEL
PR12.12 != EVIDENCE WEIGHTING
PR12.12 != RELIABILITY THRESHOLD
PR12.12 != MAJORITY VOTE
PR12.12 != RECENCY WEIGHTING
PR12.12 != REPLICATION COUNTING
PR12.12 != POSITIVE INDEPENDENCE INFERENCE
PR12.12 != CONFLICT RESOLUTION POLICY

PR12.12 != EVALUATION SUPERSESSION
PR12.12 != CURRENT-EVALUATION SELECTION
PR12.12 != PersonalCapabilityState
PR12.12 != DERIVATION
PR12.12 != PROGRESSION
PR12.12 != READINESS
PR12.12 != MASTERY
PR12.12 != SCORE
PR12.12 != PERMISSION
PR12.12 != PlayerWindow
```

## Release criterion

PR12.12 is complete when the repository can demonstrate that one exact
PR12.7–PR12.11 governed basis produces one deterministic PR2
`ClaimEvaluation`, preserving all relevant contradictory evidence and refusing
to infer any strength, preference, state, or progression beyond the frozen
domain-policy semantics.
