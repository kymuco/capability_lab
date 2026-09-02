# Civilization Bootstrap Pilot 01 — Multi-Evidence ClaimEvaluation Governance v1

Status: **PR11.2 implementation contract**

Base:

```text
main @ c2425ec6b1c5a91d6b5550f4f440a0cb2d4cb668
```

PR11.2 extends the merged PR11.1 reviewed-evidence evaluation boundary from one
reviewed `EvidenceRecord` to one explicitly governed multi-record basis.

It still creates only existing PR2 epistemic records:

```text
reviewed EvidenceRecord[]
        +
exact PR10.1 terminal reviewed-dependence preconditions
        +
exact frozen PR11.0 evaluation policy
        +
explicit HUMAN per-evidence assessments
        +
explicit HUMAN claim-level decision
        ↓
real PR2 ClaimEvaluation
```

PR11.2 still stops before state:

```text
ClaimEvaluation != PersonalCapabilityState
Evaluator != state authority
PR11.2 != derivation
PR11.2 != progression
PR11.2 != PlayerWindow
```

## Why a separate multi-evidence boundary exists

PR11.1 intentionally evaluates one reviewed evidence item at a time. It cannot
claim multi-probe reasoning sufficiency and cannot silently turn repeated
observations into stronger evidence.

PR11.0 already freezes the required dependence rule:

```text
MULTIPLE MATERIALIZED EvidenceRecord
!= INDEPENDENT / REPEATED SUPPORT

MULTI-RECORD SUFFICIENCY
requires exact PR10.1 terminal reviewed-dependence PASS

DEPENDENCE PASS
!= CLAIM SUPPORT
```

PR11.2 is the first layer allowed to combine more than one reviewed evidence
record into one `ClaimEvaluation`, so it must enforce that rule directly.

## Exact terminal dependence gate

Every PR11.2 evaluation calls:

```text
validate_pilot_materialized_evidence_reviewed_dependence_preconditions_v1(...)
```

for the exact selected basis before constructing any `EvidenceAssessment` or
`ClaimEvaluation`.

That terminal gate already requires:

- at least two materialized observation slots;
- unique `EvidenceId` identities;
- exact one-to-one resolver-issued reviewed-materialization receipts;
- complete reviewed source-lineage governance;
- complete reviewed mechanism governance;
- complete reviewed coordination governance;
- complete reviewed temporal governance;
- complete reviewed allocation governance;
- complete reviewed selection governance;
- no shared exact identity in the governed dependence families;
- causal review chronology.

PR11.2 does not reinterpret a terminal PASS as proof of statistical independence.
It is only a fail-closed prerequisite for combining the exact records under this
Pilot 01 policy revision.

```text
TERMINAL DEPENDENCE PASS
!= STATISTICAL INDEPENDENCE
!= SUPPORT
!= RELIABILITY
!= COVERAGE
!= STATE AUTHORITY
```

## Explicit human per-evidence decisions

`PilotHumanMultiEvidenceAssessmentDecision` contains exactly one explicit human
assessment for one `EvidenceId`:

- `EvidenceBearing`;
- `EvidenceReliability`;
- evidence-relative coverage note;
- evidence rationale.

Every evidence item must receive an explicitly assessed reliability value:

```text
LOW | MODERATE | HIGH
```

and PR11.2 rejects:

```text
EvidenceReliability.UNASSESSED
```

Materialization success, receipt validity, terminal dependence PASS, probe
identity, or another evidence item's reliability cannot select that value.

## Exact one-to-one evaluation basis

`PilotHumanMultiEvidenceEvaluationDecision.assessment_decisions` must contain at
least two items and must bind each `EvidenceId` exactly once.

After the terminal gate passes, PR11.2 requires exact set equality between:

```text
terminal basis EvidenceId set
==
human assessment decision EvidenceId set
```

Therefore:

```text
missing assessment decision   -> REJECT
duplicate assessment decision -> REJECT
extra assessment decision     -> REJECT
```

No reviewed observation may disappear from the combined evaluation, and no
unreviewed identity may be injected into it.

## Claim-relative probe binding

Every terminal basis entry must belong to the selected exact PR11.0 claim rubric.

For `bounded_reasoning` the only valid probes are:

```text
conceptual_explanation
calculation_work
diagnosis_reasoning
```

For `bounded_execution` the valid probe is:

```text
execution_artifact
```

A reasoning and execution basis cannot be mixed inside one `ClaimEvaluation`.
All candidates and all materialized evidence records must also match the exact
`CapabilityClaim.subject_ref`.

## Multi-probe coverage

For `bounded_reasoning`, `SUFFICIENT_FOR_CLAIM` requires relevant assessed
evidence for every exact PR11.0 sufficiency probe:

```text
conceptual_explanation
+ calculation_work
+ diagnosis_reasoning
```

Repeated evidence for one probe does not substitute for a missing probe:

```text
conceptual + calculation + calculation
!= sufficient bounded_reasoning coverage
```

An assessment with `EvidenceBearing.NOT_RELEVANT` does not count as coverage of a
required probe because the evaluator explicitly judged that record not to bear on
the selected proposition.

`INDETERMINATE` remains relevant evidence: it may mean the probe was actually
observed but cannot support a stable directional judgment. Therefore sufficient
coverage does not automatically imply a directional conclusion.

For non-sufficient coverage, PR11.2 preserves the PR11.1 claim-wide rule:

```text
coverage = PARTIAL / UNASSESSED
-> conclusion = INSUFFICIENT or ABSTAINED
```

No `SUPPORTED`, `CONTRADICTED`, or `MIXED` claim-wide conclusion is emitted from
an incomplete claim basis.

## Repeated execution observations

`bounded_execution` has exactly one PR11.0 sufficiency probe,
`execution_artifact`.

PR11.1 already permits one actual reviewed execution artifact to establish
sufficient coverage through an explicit human judgment. PR11.2 additionally
permits multiple reviewed execution observations to appear in one evaluation,
but only after the exact multi-record terminal dependence gate passes.

```text
2 execution artifacts
!= 2x confidence
```

The generic evaluation contains both explicit assessments; PR11.2 introduces no
hidden weighting, vote, confidence multiplier, or majority rule.

## Conflict governance

Generic PR2 supports `ConflictStatus.RESOLVED_BY_POLICY`, but the exact frozen
PR11.0 Pilot 01 policy defines no directional conflict-resolution rule.

PR11.2 therefore refuses to invent one:

```text
RESOLVED_BY_POLICY -> REJECT
```

When the exact basis contains both `SUPPORTS` and `CONTRADICTS`, the human may
represent the conflict as:

```text
ConflictStatus.UNRESOLVED
+ MIXED / INSUFFICIENT / ABSTAINED
```

subject to the existing generic PR2 invariants.

This keeps policy authority explicit:

```text
HUMAN JUDGMENT != AUTHORITY TO INVENT POLICY
```

A future exact policy revision may define a directional conflict-resolution rule;
PR11.2 v1 does not.

## Terminal PASS does not manufacture support

PR11.2 never derives `EvidenceBearing` from the dependence gate.

For example, a terminal-valid three-probe reasoning basis may still contain:

```text
INDETERMINATE
INDETERMINATE
INDETERMINATE
```

and legitimately end in `INSUFFICIENT` despite complete probe coverage.

The dependence gate answers only whether the exact multi-record basis has passed
the current structural/reviewed dependence preconditions. It does not answer the
capability question.

## Causal chronology

Because PR11.2 relies on reviewed dependence governance, the evaluation must not
predate any input it relies on.

`evaluated_at` must be at or after:

- `CapabilityClaim.created_at`;
- every selected reviewed `EvidenceRecord.recorded_at`;
- every selected materialization receipt `resolved_at`;
- every source/mechanism/coordination/temporal/allocation/selection completeness
  review used by the terminal gate.

This is intentionally stronger than merely checking evidence chronology:

```text
EVALUATION USING DEPENDENCE REVIEW
cannot predate that dependence review
```

## Authority boundary

PR11.2 adds one dedicated implementation module:

```text
claim_evaluation_multi.py
```

Only that file receives the additional PR2 epistemic imports necessary to create
a multi-evidence `ClaimEvaluation`.

It imports no:

```text
capability_lab.derivation
capability_lab.history
capability_lab.progression
capability_lab.proposals
capability_lab.player_window
```

The Pilot 01 package root and raw capture CLI do not export a multi-evidence
evaluation shortcut.

```text
CAPTURE != EVIDENCE
EVIDENCE != SUPPORT
DEPENDENCE PASS != SUPPORT
DEPENDENCE PASS != INDEPENDENCE
CLAIM != EVALUATION
EVALUATION != STATE
HUMAN EVALUATOR != STATE AUTHORITY
```

## Deferred boundaries

PR11.2 deliberately does not solve:

- persistence/history identity-to-bytes immutability across snapshots;
- automatic evaluator weighting;
- statistical independence estimation;
- majority voting;
- score aggregation;
- mastery thresholds;
- state derivation;
- progression;
- PlayerWindow rendering.

The previously identified persistence requirement remains:

```text
SAME EvidenceId != permission to replace EvidenceRecord bytes
persisted EvidenceId -> immutable identity-to-content binding
```

That belongs to the future store/history layer, not this evaluation boundary.
