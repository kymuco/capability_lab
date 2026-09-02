# PR12.13 — Generic End-to-End Capability Inference Audit v1

Status: executable integration contract and audit evidence  
Architecture issue: #54  
Base: `main @ 6101718993fa41bdbeca328359eb4ef2299c3c98`

## Purpose

PR12.13 does not add a new evaluator, policy, persistence primitive, state rule,
or current-state authority. It proves that the already-implemented generic PR12
write/evaluation chain composes with the already-implemented PR11 governed state
chain using their public APIs and their existing authority boundaries.

The audited path is:

```text
external source event
        |
        v
PR12.0 ExternalObservationEnvelope
        |
exact idempotent admission
        v
ExternalObservationLedger
        |
PR12.1 source-derived candidate
        |
explicit HUMAN MATERIALIZE review
        v
neutral EvidenceRecord
        |
PR11.3 exact append-only persistence
        v
retained evidence snapshot
        |
PR12.2 evidence -> bounded claim proposal
        |
PR12.3 HUMAN terminal ACCEPT + review-ledger authority
        v
PR12.4 deterministic CapabilityClaim
        |
PR11.3 exact append-only persistence
        v
PR12.5 explicit HUMAN evidence assessment
        |
PARTIAL / INSUFFICIENT ClaimEvaluation
        |
PR11.3 exact append-only persistence
        v
PR12.6 declarative domain policy
        |
PR12.7 HUMAN review + runtime policy authority
        v
PR12.8 complete same-subject evidence candidate universe
        |
PR12.9 complete explicit dispositions
        |
PR12.10 complete lineage/non-inference audit
        |
PR12.11 complete HUMAN semantic requirement mapping
        + terminal runtime-only mapping-review authority
        v
PR12.12 deterministic domain-sufficient ClaimEvaluation
        |
PR11.3 exact append-only persistence
        v
PR11.4 complete ClaimEvaluation portfolio
        |
PR11.5 complete-portfolio state derivation
        |
PR11.6 immutable state persistence
        |
PR11.7 explicit persisted-state acceptance
        |
PR11.8 explicit SELECT
        |
fresh PR11.8 authority replay
        v
governed current state
```

The executable proof lives in:

`tests/integration/test_generic_capability_inference_e2e_v1.py`

## Non-authority rule

The central rule of this PR is:

```text
END-TO-END AUDIT
!= NEW AUTHORITY
!= NEW INFERENCE ALGORITHM
!= CONVENIENCE ORCHESTRATOR THAT SKIPS GATES
```

There is intentionally no new production wrapper such as:

```text
infer_capability_from_observation(...)
update_current_state_from_external_activity(...)
auto_accept_capability(...)
```

Each transition remains separately visible and separately governed.

## Positive trace

The positive audit uses one generic `research:signal_reasoning@1` concept and one
external artifact observation. It is deliberately not a Civilization Bootstrap
Pilot production path.

### Observation -> neutral evidence

An external artifact is first admitted only as `ExternalObservationEnvelope`.
It becomes a PR2 `EvidenceRecord` only after the exact PR12.1 candidate is
reviewed by a declared HUMAN with `MATERIALIZE`.

The resulting evidence remains neutral:

```text
MATERIALIZE != SUCCESS
MATERIALIZE != SUPPORT
MATERIALIZE != CAPABILITY
```

PR11.3 then proves that this exact evidence identity/content entered the
append-only epistemic snapshot.

### Evidence -> claim

PR12.2 proposes a bounded claim interpretation. PR12.3 records a declared HUMAN
terminal `ACCEPT` and admits that exact review into the governed review ledger.
PR12.4 materializes the deterministic `CapabilityClaim` and hands it through
PR11.3.

```text
proposal != claim truth
ACCEPT != claim truth
claim existence != capability support
```

### PR12.5 historical evaluation remains conservative

The exact materialized claim/evidence pair receives a PR12.5 HUMAN assessment:

```text
bearing    = SUPPORTS
reliability = HIGH
coverage   = PARTIAL
conclusion = INSUFFICIENT
```

This is intentional. PR12.5 has no domain sufficiency authority.

That evaluation is persisted through PR11.3 and remains part of immutable
history after PR12.12 later produces a domain-sufficient result.

## Domain sufficiency path

The same bounded claim receives one exact admitted PR12.6 domain policy with two
required semantic requirements. PR12.7 supplies explicit HUMAN review and
runtime policy authority.

PR12.8 then constructs the complete same-subject evidence universe at the exact
snapshot/as-of boundary. In the positive case the universe contains exactly the
single retained PR12.1 evidence record.

PR12.9 explicitly dispositions it as `SUPPORTS`. PR12.10 records its lineage
basis without converting lineage into weight, count, replication, or positive
independence.

PR12.11 maps the same evidence record to both required semantic requirements.
That is permitted semantic coverage and does not claim two independent pieces
of evidence.

```text
one evidence -> two semantic requirements
!= two evidence records
!= two votes
!= two replications
```

After exact HUMAN mapping review/admission, the PR12.11 application reports:

```text
required_requirement_coverage_complete = true
```

PR12.12 then evaluates the entire PR12.9 disposition universe and emits:

```text
coverage   = SUFFICIENT_FOR_CLAIM
conflict   = NONE
conclusion = SUPPORTED
```

## Immutable history and no latest-wins

The most important integration result is that the old PR12.5 evaluation is not
replaced by the PR12.12 evaluation.

The exact history is:

```text
PR12.5  -> PARTIAL / INSUFFICIENT
PR12.12 -> SUFFICIENT_FOR_CLAIM / SUPPORTED
```

PR11.3 requires the final epistemic successor to retain the PR12.5 evaluation
and append the PR12.12 evaluation under a distinct deterministic identity.

PR11.4 then constructs the complete portfolio and returns both evaluation ids.
The audit explicitly attempts to select only the PR12.12 `SUPPORTED` evaluation;
PR11.4 rejects the omission.

Therefore:

```text
COMPLETE PORTFOLIO != LATEST EVALUATION
SUPPORTED NEW RESULT != DELETE OLD INSUFFICIENT RESULT
```

## PR11.5 state derivation

PR11.5 accepts only the exact PR11.4 complete portfolio and an explicit
claim-to-dimension binding. The audit binds the claim to one minimal `reasoning`
dimension.

The complete state basis contains both historical evaluations.

Under the unchanged PR4 deterministic policy:

```text
at least one real SUPPORTED evaluation in complete bound basis
-> dimension standing SUPPORTED

INSUFFICIENT evaluation
!= negative vote
```

The audit confirms:

```text
reasoning.standing        = SUPPORTED
reasoning.conflict_status = NONE
reasoning.basis_evaluation_ids
    = {PR12.5 evaluation, PR12.12 evaluation}
```

The audit also verifies that omitting the claim-to-dimension binding fails
closed even though a `SUPPORTED` evaluation exists.

## Persistence, acceptance, and current are three authorities

PR12.13 exercises the separation already frozen by PR11.6–PR11.8.

### PR11.6 persistence

The derived state enters an immutable `PersonalCapabilityStateSet` only after
PR11.6 validates the append-only transition.

A derived state that is absent from persisted state history cannot be accepted.

### PR11.7 acceptance

The exact persisted state receives an explicit HUMAN acceptance fact.

```text
PERSISTED != ACCEPTED
ACCEPTED != CURRENT
```

A persisted but unaccepted state is absent from the PR11.8 accepted candidate
universe.

### PR11.8 current selection

Even after acceptance, an empty current-selection history resolves to no current
state. A separate explicit HUMAN `SELECT` is required.

The audit then distinguishes structural resolution from authority:

```text
resolve_current_personal_capability_state_selection_v1(...)
    = structural chain head only

validate_personal_capability_current_state_selection_v1(...)
    = fresh authority replay
```

Calling the authority validator without the exact durable selection/acceptance
basis fails closed. Supplying the exact `PersonalCapabilityCurrentStateSelectionAuthorityBasis`
replays the subject-wide acceptance lineage and returns the governed current
selection.

## Conflict preservation

A second audit scenario starts from the same generic pre-domain snapshot but adds
a second reviewed external evidence record. PR12.9 explicitly assigns:

```text
first evidence  -> SUPPORTS
second evidence -> CONTRADICTS
```

Both required requirements remain semantically covered, so PR12.11 coverage is
complete. PR12.12 must therefore preserve the directional conflict:

```text
coverage   = SUFFICIENT_FOR_CLAIM
conflict   = UNRESOLVED
conclusion = MIXED
```

That mixed evaluation is persisted and passed through a complete PR11.4
portfolio containing the older PR12.5 `INSUFFICIENT` evaluation plus the new
`MIXED` evaluation.

No `SUPPORTED` ClaimEvaluation exists in that scenario. The unchanged PR11.5 / PR4
state result is therefore:

```text
reasoning.standing        = INSUFFICIENT
reasoning.conflict_status = UNRESOLVED
```

This demonstrates that downstream state derivation does not silently resolve a
PR12.12 conflict.

## Adversarial integration coverage

The executable audit additionally verifies:

1. a free-standing PR12.12 evaluation has no PR11.4 membership before PR11.3 persistence;
2. injecting that unpersisted evaluation id into the selected portfolio fails;
3. changing PR12.12 bytes under its retained `ClaimEvaluationId` fails PR11.3;
4. a later historical evaluation append makes the old PR11.4 portfolio stale;
5. rebuilding PR11.4 includes the newly appended historical evaluation;
6. selecting only the newer PR12.12 evaluation fails complete-portfolio validation;
7. missing claim-to-dimension binding fails PR11.5;
8. unpersisted derived state cannot be accepted;
9. persisted but unaccepted state is not a PR11.8 candidate;
10. accepted state is not current without explicit selection;
11. structural current resolution is not treated as authority;
12. fresh PR11.8 authority replay succeeds only with the exact authority basis;
13. no audited artifact emits permission, readiness, mastery, professional authority, or human-worth fields.

## What the audit proves

For the implemented v1 contracts, the repository now demonstrates a real generic
write-to-current-state path:

```text
external observation
-> reviewed evidence
-> reviewed claim interpretation
-> immutable claim
-> conservative historical evaluation
-> governed domain policy
-> complete evidence disposition/mapping
-> deterministic directional evaluation
-> complete immutable evaluation history
-> derived state
-> persisted state
-> explicitly accepted state
-> explicitly selected current state
-> fresh current-state authority replay
```

No Pilot-specific production evaluator or state shortcut is needed for this path.

## What it does not prove

This audit does not mean:

```text
external activity automatically updates capability
observation authenticates identity or authorship
MATERIALIZE means success
SUPPORTS means truth
SUPPORTED means mastery
state derivation means acceptance
acceptance means current
current means best/latest
current means readiness
current means permission
current means professional authority
current state describes human worth
```

It also does not create automatic closed-loop HDE profiling. Every human-review,
persistence, acceptance, and current-selection boundary remains explicit.

## Release criterion

PR12.13 is complete when:

```text
full generic observation -> governed current-state trace     PASS
PR12.5 + PR12.12 immutable history preservation              PASS
PR11.4 complete-history anti-cherry-picking                   PASS
PR11.5 exact complete-basis handoff                           PASS
PR11.6 persistence != acceptance                              PASS
PR11.7 acceptance != current                                  PASS
PR11.8 structural current != authority                        PASS
PR11.8 fresh authority replay                                 PASS
MIXED / UNRESOLVED downstream preservation                    PASS
no new production shortcut authority                         PASS
hosted full-suite CI                                          PASS
P1 unresolved                                                 0
P2 unresolved                                                 0
```
