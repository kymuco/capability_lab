# PR12.5 — Governed Generic External Evidence-to-ClaimEvaluation Human Assessment v1

## Purpose

PR12.5 introduces the first generic write-side transition from one exact PR12.4 materialized `CapabilityClaim` and its exact retained external `EvidenceRecord` into a real PR2 `ClaimEvaluation`.

The boundary is deliberately conservative. It allows a declared human evaluator to say how **one exact evidence record bears on one exact claim** and how reliable that evidence appears, but it does not pretend that Capability Lab has a generic domain-independent rule for deciding whether that one record is sufficient to establish or refute the whole claim.

```text
PR12.1 exact external EvidenceRecord
        |
        + PR12.2 exact interpretation candidate
        + PR12.3 exact terminal ACCEPT
        + PR12.4 exact materialized CapabilityClaim
        |
        v
explicit declared-HUMAN evidence assessment
        |
        v
PR12.5 conservative ClaimEvaluation
        |
        v
PR11.3 immutable evaluation admission
```

## Core distinction

PR2 separates an evidence-level assessment from a claim-wide conclusion.

```text
EvidenceBearing.SUPPORTS
!=
EvaluationConclusion.SUPPORTED

EvidenceBearing.CONTRADICTS
!=
EvaluationConclusion.CONTRADICTED
```

`EvidenceBearing` answers a local question:

> How does this exact evidence record bear on this exact claim?

`EvaluationConclusion` answers a stronger claim-wide question:

> Given the governed evidence basis and a sufficiency policy, what conclusion is justified for the claim as a whole?

PR12.5 has the first answer but intentionally does not invent the second.

## Frozen generic policy

The policy ref is:

```text
capability_lab:generic_external_evidence_human_evaluation@1
```

This generic policy contains **no domain-specific sufficiency rubric**. It therefore cannot establish that one external artifact, conversation observation, event, text record, or other PR12.1 materialized observation is enough to support or contradict an arbitrary capability claim in full.

The declared human evaluator must explicitly choose exactly one evidence-level bearing:

```text
SUPPORTS
CONTRADICTS
INDETERMINATE
NOT_RELEVANT
```

and exactly one assessed reliability:

```text
LOW
MODERATE
HIGH
```

`EvidenceReliability.UNASSESSED` is rejected for a completed PR12.5 human assessment.

The generic claim-wide surface is intentionally restricted:

```text
coverage:
    UNASSESSED | PARTIAL

conflict_status:
    NONE

conclusion:
    INSUFFICIENT | ABSTAINED
```

Forbidden under PR12.5:

```text
CoverageStatus.SUFFICIENT_FOR_CLAIM
EvaluationConclusion.SUPPORTED
EvaluationConclusion.CONTRADICTED
EvaluationConclusion.MIXED
ConflictStatus.RESOLVED_BY_POLICY
ConflictStatus.UNRESOLVED
```

A future domain policy may define real sufficiency, aggregation, and conflict-resolution criteria. PR12.5 must not fabricate those criteria merely because an interpretation was accepted or an evidence record points in a direction.

## Exact upstream governance basis

PR12.5 does not accept an arbitrary claim/evidence pair.

The caller supplies:

```text
materialization_predecessor_snapshot
current_epistemic_snapshot
catalog
candidate
review_ledger
materialization
decision
```

The boundary replays the exact PR12.4 materialization validator from its original predecessor/candidate/review-ledger/catalog basis. This transitively revalidates the PR12.2 external-evidence interpretation candidate and the PR12.3 terminal `ACCEPT`.

Therefore the evaluation cannot survive:

- mutation of the selected external evidence bytes;
- subject rebinding;
- concept-revision substitution;
- mutation of the accepted claim semantics;
- forged or stale PR12.4 materialization content;
- replacement of the exact terminal review basis.

```text
PR12.3 ACCEPT
!= EvidenceBearing.SUPPORTS

PR12.4 CLAIM EXISTS
!= CLAIM TRUE

PR12.5 HUMAN ASSESSMENT
= a new, separate epistemic act
```

## Current epistemic snapshot

The current evaluation snapshot need not be byte-identical to the snapshot produced by PR12.4.

It must be a valid PR11.3 append-only successor of the exact PR12.4 successor:

```text
PR12.4 successor
        |
        + zero or more unrelated append-only epistemic additions
        |
        v
current_epistemic_snapshot
```

PR11.3 also permits the equality case, so evaluation may occur immediately on the exact PR12.4 successor.

The exact selected evidence and exact materialized claim must still be retained byte-for-byte. Unrelated later evidence, claims, or evaluations do not change the deterministic PR12.5 evaluation identity.

## Decision surface

`ExternalEvidenceHumanClaimEvaluationDecision` contains only the declared human judgment:

```text
evaluator_ref
evaluated_at
bearing
reliability
coverage_status
conclusion
evidence_coverage_note
claim_coverage_notes
evidence_rationale
evaluation_rationale
```

It contains no caller-selected:

```text
evidence_id
claim_id
evaluation_id
policy_ref
conflict_status
state id
score
mastery
readiness
permission
```

The exact evidence and claim are resolved from the governed upstream chain. Conflict is fixed to `NONE`, policy is frozen, and evaluation identity is derived rather than allocated by the caller.

The evaluator kind must be exactly `EvaluatorKind.HUMAN`.

```text
DECLARED HUMAN EVALUATOR
!= AUTHENTICATED HUMAN IDENTITY
```

Authentication remains a deployment/runtime concern outside this data-model boundary.

## Deterministic immutable evaluation identity

A PR2 `ClaimEvaluation` stores:

```text
evaluation_id
claim_id
policy_ref
evaluator_ref
evaluated_at
evidence_assessments
coverage
conflict_status
conclusion
rationale
```

PR12.5 derives `ClaimEvaluationId` from a domain-separated canonical representation of **every deterministic stored evaluation field except the id itself**.

The id therefore commits:

- exact materialized `claim_id`;
- frozen PR12.5 policy ref;
- declared HUMAN evaluator ref;
- evaluation time;
- exact selected `EvidenceId`;
- evidence bearing;
- assessed reliability;
- evidence coverage note and rationale;
- claim coverage status and notes;
- fixed conflict status `NONE`;
- conservative claim conclusion;
- evaluation rationale.

It does not include whole growing snapshot or review-ledger digests.

The invariant is:

```text
same ClaimEvaluationId
=> same deterministic ClaimEvaluation bytes
```

A retry with the same exact decision and governed basis produces the same evaluation identity and bytes.

## Duplicate handling

PR12.5 rejects two duplicate forms before append:

1. the deterministic `evaluation_id` is already retained;
2. byte-semantic evaluation content is already retained under another legacy/manual evaluation id.

```text
SAME IMMUTABLE EVALUATION CONTENT
!= PERMISSION TO DUPLICATE HISTORY
```

PR12.5 does **not** prohibit multiple genuinely different human evaluations of the same claim and evidence. Different evaluators, times, bearings, reliabilities, coverage judgments, conclusions, or rationales may create distinct immutable `ClaimEvaluation` records.

That multiplicity is epistemic history, not an error. Later portfolio/domain governance decides how multiple evaluations are interpreted; PR12.5 does not silently choose a winner.

## PR11.3 admission

The current snapshot is preserved exactly except for one new evaluation:

```text
successor.evidence_records = current.evidence_records
successor.claims           = current.claims
successor.evaluations      = current.evaluations + exact new evaluation
```

The successor must pass `validate_epistemic_snapshot_successor_v1` and the validator-issued receipt must show:

```text
added_evidence_ids   = ()
added_claim_ids      = ()
added_evaluation_ids = exactly one PR12.5 evaluation id
```

PR12.5 does not create or mutate `PersonalCapabilityState`, state histories, acceptance, current selection, progression, Player Window, readiness, mastery, permission, or professional authority.

## Admission receipt

`ExternalEvidenceClaimEvaluationAdmissionReceipt` records the exact audit/persistence basis for one PR12.5 transition:

```text
policy_ref
proposal_id
candidate_sha256
review_id
review_sha256
claim_materialization_receipt_sha256
evidence_id
evidence_sha256
claim_id
claim_sha256
evaluation_id
evaluation_sha256
predecessor_snapshot_sha256
successor_snapshot_sha256
evaluated_at
```

The receipt is strict schema-v1 deterministic JSON. Unknown fields, missing fields, duplicate JSON keys, malformed typed ids, malformed hashes, non-finite JSON constants, or non-timezone-aware timestamps fail closed.

The receipt commits exact upstream and current-transition facts but does not recreate validator authority from serialized bytes.

```text
RECEIPT DIGEST != SIGNATURE
RECEIPT DIGEST != AUTHENTICATED EVALUATOR
RECEIPT DIGEST != TRUSTED TIME
RECEIPT DIGEST != GLOBAL/CURRENT SNAPSHOT AUTHORITY
SERIALIZED RECEIPT != PR11.3 VALIDATOR AUTHORITY
```

Full validation replays the upstream PR12.4 governance, current append-only lineage, deterministic evaluation construction, duplicate guard, exact successor, and PR11.3 validator.

## Explicit non-authority

```text
PR12.1 MATERIALIZE != CLAIM SUPPORT
PR12.2 PROPOSAL != CLAIM TRUTH
PR12.3 ACCEPT != CLAIM TRUTH
PR12.3 ACCEPT != EvidenceBearing.SUPPORTS
PR12.4 CLAIM MATERIALIZATION != CLAIM TRUTH

PR12.5 EvidenceBearing.SUPPORTS
!= EvaluationConclusion.SUPPORTED

PR12.5 EvidenceBearing.CONTRADICTS
!= EvaluationConclusion.CONTRADICTED

PR12.5 ClaimEvaluation
!= PersonalCapabilityState

PR12.5 ClaimEvaluation
!= readiness / mastery / permission / score
```

PR12.5 makes generic external evidence **assessable** without making generic evidence **sufficient**.

That is the intended boundary.

## Next boundary

A later PR must explicitly introduce domain sufficiency and/or governed multi-evidence aggregation before generic external evaluations can emit directional claim-wide conclusions. Only after such conclusions are governed should the existing PR11.4+ portfolio/state path be considered for generic closed-loop use.
