# Civilization Bootstrap Pilot 01 — Reviewed Evidence → ClaimEvaluation Boundary v1

Status: **PR11.1 implementation contract**

Base:

```text
main @ b04e69912676dd8a1964b149f831823764c8ea73
```

PR11.1 is the first Pilot 01 layer that creates real PR2 `CapabilityClaim` and
`ClaimEvaluation` records from the already reviewed PR10.1 evidence path under
the exact PR11.0 evaluation-policy revision.

## Core flow

```text
exact PR11.0 PilotClaimTemplate
        +
explicit subject / claim id / time / provenance
        ↓
real PR2 CapabilityClaim

exact PR10.1 reviewed EvidenceRecord
        +
resolver-issued reviewed-materialization binding
        +
exact PR11.0 policy
        +
explicit HUMAN evaluation decision
        ↓
real PR2 EvidenceAssessment
        ↓
real PR2 ClaimEvaluation
```

PR11.1 still stops before state:

```text
ClaimEvaluation != PersonalCapabilityState
Evaluator != state authority
PR11.1 != derivation
PR11.1 != progression
PR11.1 != PlayerWindow
```

## Why PR11.1 is single-evidence

PR11.0 deliberately separated the claim/rubric policy from evaluation, and
PR10.1 deliberately separated materialized evidence from assumptions of
independence. PR11.1 therefore takes the smallest real evaluation step: one
reviewed evidence record at a time.

```text
ONE reviewed EvidenceRecord
    -> one explicit human EvidenceAssessment
    -> one ClaimEvaluation

MULTIPLE EvidenceRecord
    -> PR11.2
```

PR11.2 remains responsible for:

- multi-evidence aggregation;
- duplicate/correlated support governance;
- PR10.1 terminal dependence composition;
- conflicting evidence;
- multi-record coverage sufficiency;
- policy-specific conflict resolution.

This prevents PR11.1 from silently treating multiple observations as independent
support before the dedicated multi-evidence boundary exists.

## Exact policy requirement

Every PR11.1 claim/evaluation path calls:

```text
validate_exact_civilization_bootstrap_pilot_01_evaluation_policy_v1(...)
```

Therefore a nominally matching policy ref is insufficient. The frozen PR11.0
protocol fingerprint, exact canonical protocol, exact canonical evaluation
policy, and frozen policy fingerprint must still agree.

```text
POLICY REF != EXACT POLICY CONTENT
PROTOCOL REF != EXACT PROTOCOL CONTENT
```

## CapabilityClaim instantiation

`instantiate_civilization_bootstrap_pilot_01_capability_claim_v1(...)` creates a
real PR2 `CapabilityClaim` only from an exact PR11.0 claim template.

The caller must explicitly provide:

- `CapabilitySubjectRef`;
- `CapabilityClaimId`;
- creation time;
- claim provenance;
- exact PR11.0 policy;
- exact `claim_key`.

The template supplies only:

- exact `CapabilityConceptRef`;
- proposition statement;
- `ClaimScope`.

Evidence is not inserted into claim provenance.

```text
CLAIM TEMPLATE -> exact proposition
EVIDENCE        -> ClaimEvaluation
```

## Explicit human decision

`PilotHumanSingleEvidenceEvaluationDecision` carries the human evaluator's
explicit choices:

- target claim key/id;
- target evidence id;
- exact policy ref;
- `EvaluatorRef`;
- evaluated time;
- `EvidenceBearing`;
- `EvidenceReliability`;
- `CoverageAssessment`;
- conflict status;
- evaluation conclusion;
- coverage/evidence/evaluation rationale.

PR11.1 requires:

```text
EvaluatorKind.HUMAN
```

It does not infer bearing, reliability, coverage, or conclusion from:

- `EvidenceKind`;
- materialization success;
- receipt validity;
- probe identity;
- rubric text;
- provenance.

The rubric remains human-review guidance, not a classifier.

The frozen PR11.0 reliability rule also requires reliability to be actually
assessed by that human evaluator. The generic PR2 enum contains `UNASSESSED` for
other workflows, but PR11.1 may not use it as a completed Pilot 01 decision:

```text
UNASSESSED != EXPLICIT HUMAN RELIABILITY ASSESSMENT
```

A Pilot 01 single-evidence decision therefore requires one explicit assessed
reliability value (`LOW`, `MODERATE`, or `HIGH`). Receipt validity, evidence kind,
probe identity, and materialization success still cannot choose that value for
the evaluator.

## Reviewed-evidence binding

Before evaluation, PR11.1 reuses:

```text
validate_pilot_reviewed_materialization_resolution_binding_v1(...)
```

This requires the current candidate, selected materialization review,
resolver-issued receipt, and complete current `EvidenceRecord` bytes to agree.

Therefore:

```text
mutated EvidenceRecord after receipt -> REJECT
changed review after receipt         -> REJECT
candidate/evidence mismatch          -> REJECT
```

A valid materialization receipt still does not imply support; it only proves the
local structural reviewed-materialization binding.

## Claim-relative probe binding

PR11.1 accepts an evidence item only when the exact PR11.0 rubric for the
candidate's `probe_id` is bound to the selected `claim_key`.

Thus:

```text
bounded_reasoning
    conceptual_explanation
    calculation_work
    diagnosis_reasoning

bounded_execution
    execution_artifact
```

are kept separate during real evaluation.

## Single-evidence coverage rule

For a claim whose PR11.0 sufficiency definition requires more than one probe,
one evidence record cannot establish claim-wide sufficient coverage.

For `bounded_reasoning`:

```text
one reasoning probe
    -> local EvidenceBearing may be SUPPORTS / CONTRADICTS / ...
    -> coverage cannot be SUFFICIENT_FOR_CLAIM
    -> claim-wide conclusion remains INSUFFICIENT or ABSTAINED
```

This preserves the important distinction:

```text
SUPPORTING EVIDENCE != SUFFICIENT CLAIM COVERAGE
```

For `bounded_execution`, the exact PR11.0 sufficiency basis is one
`execution_artifact`. Therefore a single reviewed execution observation may be
marked `SUFFICIENT_FOR_CLAIM` by the explicit human evaluator and may support a
directional claim conclusion if the underlying PR2 invariants also hold.

Missing optional execution still creates no negative evaluation because PR11.1
requires an actual reviewed evidence record.

## Causal chronology

PR11.1 fails closed if evaluation time precedes:

- claim creation;
- reviewed `EvidenceRecord.recorded_at`;
- reviewed-materialization receipt `resolved_at`.

The pilot-specific path is intentionally stronger than the generic historical
backfill allowance in PR2 because PR11.1 evaluates an already materialized local
record.

## Authority boundary

PR11.1 is the first Pilot 01 implementation file intentionally allowed to import
`CapabilityClaim` and `ClaimEvaluation`. The authority regression localizes that
import expansion to `claim_evaluation.py`.

It still imports no:

```text
capability_lab.derivation
capability_lab.history
capability_lab.progression
capability_lab.proposals
capability_lab.player_window
```

and does not expose a raw-capture CLI evaluation shortcut.

```text
CAPTURE != EVIDENCE
EVIDENCE != CLAIM SUPPORT
CLAIM != EVALUATION
EVALUATION != STATE
HUMAN EVALUATOR != STATE AUTHORITY
```

The human decision record is structural local governance metadata. It is not a
signature, authenticated global reviewer identity, trusted timestamp, or proof
that the named human historically performed the evaluation.
