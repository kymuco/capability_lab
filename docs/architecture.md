# Capability Lab Architecture

Status: **generic governed write/evaluation path implemented through PR12.12; end-to-end composition through fresh PR11.8 current-state authority verified by PR12.13 and through PR11.9–PR11.11 governed product/read composition audited by PR12.14**

This file is the current release-level architecture index. Detailed contracts live in the PR-specific documents under `docs/`; the pre-PR10.1 long-form architecture snapshot remains preserved at `docs/legacy/pr10_0/architecture.md`.

## Constitutional separation

Capability Lab models evidence and governed capability state without turning observation, model output, scores, recommendations, or presentation into authority over a person.

The core separation is:

```text
observation
!= evidence
!= interpretation proposal
!= human review
!= terminal/runtime admission
!= claim
!= evidence disposition
!= claim evaluation
!= derived capability state
!= persisted state
!= accepted state
!= current state
!= progression advice
!= product/read projection
!= permission / licensing / human worth
```

Each arrow in the architecture is an explicit boundary. A later layer may consume a validated earlier artifact, but it must not retroactively grant authority to the earlier artifact.

## Two composed halves

The implemented system now has two mature halves:

```text
GENERIC WRITE / EVALUATION                         GOVERNED STATE / READ

external activity
      |
PR12.0 observation
      |
PR12.1 reviewed neutral evidence
      |
PR12.2-12.4 reviewed bounded claim
      |
PR12.5 conservative evidence-level evaluation
      |
PR12.6-12.11 governed domain-policy basis
      |
PR12.12 directional ClaimEvaluation
      |                                              
      +---------------- PR11.3 persistence ----------------+
                                                         |
                                                   PR11.4 complete portfolio
                                                         |
                                                   PR11.5 derived state
                                                         |
                                                   PR11.6 persisted state
                                                         |
                                                   PR11.7 accepted state
                                                         |
                                                   PR11.8 current state
                                                         |
                                      +------------------+------------------+
                                      |                                     |
                               PR11.10 current profile              PR11.9 progression
                                      |                                     |
                                      +------------------+------------------+
                                                         |
                                                   PR11.11 product/read
```

PR12.13 proves the generic write/evaluation half and the governed state half compose without a new production shortcut layer. PR12.14 extends that executable proof through the already-existing PR11.9 progression, PR11.10 complete current profile, and PR11.11 governed product/read boundary without introducing product-side state selection or write-back authority.

## PR10 / Pilot boundary

The Civilization Bootstrap Pilot remains a concrete stress test with its own private raw workspace and reviewed capture-to-evidence path.

```text
private raw capture
!= public EvidenceRecord
```

PR10.1 requires explicit reviewed materialization before Pilot capture becomes neutral PR2 evidence. Its dependence governance may record reviewed causal/dependence structure, but:

```text
DEPENDENCE PASS != CLAIM SUPPORT
DEPENDENCE PASS != INDEPENDENT REPLICATION
DEPENDENCE PASS != REPRESENTATIVE SAMPLING
```

The generic PR12 path does not depend on Pilot production authority.

## PR11 governed state chain

PR11.1–PR11.8 established the governed evidence/evaluation-to-current-state chain:

```text
PR11.1  governed single-evidence ClaimEvaluation
PR11.2  governed multi-evidence ClaimEvaluation
PR11.3  immutable epistemic succession
PR11.4  complete ClaimEvaluation portfolio
PR11.5  governed complete-portfolio-to-state handoff
PR11.6  immutable PersonalCapabilityState persistence
PR11.7  explicit persisted-state acceptance
PR11.8  explicit governed current-state selection + authority replay
```

The boundaries remain independent:

```text
EVALUATED != DERIVED
DERIVED != PERSISTED
PERSISTED != ACCEPTED
ACCEPTED != CURRENT
CURRENT != LATEST
CURRENT != BEST
CURRENT != MASTERY
CURRENT != READINESS
CURRENT != PERMISSION
```

### PR11.3 — immutable persistence

Evidence, claims, and evaluations are append-only by identity. Retained same-id bytes may not mutate. Persistence does not choose which evaluation is current, preferred, or strongest.

### PR11.4 — complete evaluation portfolio

Portfolio membership is determined by exact subject, exact capability concept revision, temporal scope, and persisted history. Conclusion, evaluator identity, policy, reliability, and coverage do not filter membership.

A caller may not select only a preferred or latest subset:

```text
COMPLETE PORTFOLIO != LATEST EVALUATION
COMPLETE PORTFOLIO != BEST EVALUATION
```

### PR11.5 — complete-basis state derivation

PR11.5 revalidates the exact PR11.4 portfolio and requires an explicit claim-to-dimension binding for every in-scope claim. It then uses the unchanged deterministic PR4 semantics.

An `INSUFFICIENT` evaluation is not a negative vote. A dimension can be `SUPPORTED` when its complete bound basis contains a real `SUPPORTED` evaluation. Unresolved directional conflict remains visible in the dimension conflict status.

### PR11.6 / PR11.7 / PR11.8

State derivation, persistence, acceptance, and current selection are separate authorities.

PR11.8 also separates structural current-history resolution from authority. `resolve_current_personal_capability_state_selection_v1(...)` identifies a structural chain head. Governed current authority requires fresh `validate_personal_capability_current_state_selection_v1(...)` replay against the exact state and acceptance lineage.

## PR11.9–PR11.11 governed read/advisory path

PR11.9 admits progression inputs only through fresh PR11.8 current-state authority replay. Its request describes concept/frame/dimension scopes but does not accept a caller-selected current state id. It does not create readiness, permission, or mastery authority.

PR11.10 derives the complete set of governed current-selection scope heads in the full subject history and preserves explicit `CLEAR` separately from absent scope. It exposes no caller-selected scope subset.

PR11.11 composes PR11.10 current-state authority with PR11.9 progression into the safe HDE/product-facing read snapshot, then delegates presentation to unchanged PR9 semantics. It freshly derives both governed sources from the same history and exact PR11.8 authority bases; callers do not provide a prebuilt frontier, a prebuilt current portfolio, or selected state ids.

```text
VISIBLE != CURRENT
HIDDEN != DELETED
CLEAR != ABSENT
PRESENTATION != AUTHORITY
PRODUCT VIEW != WRITE-BACK AUTHORITY
```

A complete current SELECT state whose semantic `state.as_of` is later than the requested product snapshot `as_of` causes rejection rather than silent historical filtering.

## PR12.0–PR12.5 — generic external observation to conservative evaluation

### PR12.0 — external observation

External source events become immutable `ExternalObservationEnvelope` values in a subject-scoped ledger.

```text
EXTERNAL OBSERVATION != EVIDENCE
DECLARED SUBJECT != AUTHENTICATED SUBJECT
PAYLOAD HASH != AUTHORSHIP / CORRECTNESS / CAPABILITY
```

### PR12.1 — reviewed neutral evidence

One exact admitted observation may become a neutral PR2 `EvidenceRecord` only after an explicit declared-HUMAN materialization review.

```text
MATERIALIZE != SUCCESS
MATERIALIZE != SUPPORT
DO_NOT_MATERIALIZE != FAILURE
```

### PR12.2–PR12.4 — bounded claim interpretation

PR12.2 proposes an exact evidence-to-concept/bounded-claim interpretation. PR12.3 records a terminal HUMAN `ACCEPT` or `REJECT` and governs its review-ledger admission. PR12.4 requires the exact accepted basis and deterministically materializes a PR2 `CapabilityClaim`.

```text
PROPOSAL != CLAIM TRUTH
ACCEPT != CLAIM TRUTH
REJECT != CONTRADICTION
CLAIM EXISTENCE != CAPABILITY SUPPORT
```

### PR12.5 — conservative evidence-level evaluation

A declared HUMAN may assess exact evidence bearing and reliability for the materialized claim. Without a domain sufficiency rule, PR12.5 remains claim-wide `INSUFFICIENT | ABSTAINED`.

```text
EvidenceBearing.SUPPORTS    != EvaluationConclusion.SUPPORTED
EvidenceBearing.CONTRADICTS != EvaluationConclusion.CONTRADICTED
```

## PR12.6–PR12.12 — governed domain-sufficient evaluation

PR12.6–PR12.12 add the reusable generic domain-policy path without collapsing specification, approval, semantic mapping, and evaluation into one authority.

```text
PR12.6  declarative DomainEvaluationPolicySpecification
        |
PR12.7  explicit HUMAN policy review
        + process-local admitted-policy authority
        |
PR12.8  complete same-subject evidence candidate universe
        |
PR12.9  complete explicit EvidenceAssessment disposition coverage
        |
PR12.10 lineage/dependence audit
        |
PR12.11 complete semantic requirement mapping proposal
        + terminal HUMAN mapping review
        + process-local mapping-review authority
        + deterministic requirement application
        |
PR12.12 deterministic domain-sufficient directional ClaimEvaluation
```

### Frozen sufficiency rule

PR12.6 defines exactly:

```text
all_required_requirements_explicitly_covered
```

At least one requirement must be required for sufficiency, preventing vacuous empty-policy sufficiency.

PR12.11 may only compute whether all required requirements are explicitly `COVERED`. It does not decide claim direction.

```text
REQUIREMENT COVERAGE != CLAIM TRUTH
REQUIREMENT MAPPING != DIRECTIONAL EVIDENCE SELECTION
```

### PR12.8 / PR12.9 completeness

PR12.8 includes every same-subject evidence record admissible at the exact snapshot/as-of boundary. Membership is intentionally non-evaluative.

PR12.9 requires one explicit disposition for the entire candidate universe. Evidence cannot silently disappear because it is inconvenient to the eventual conclusion.

### PR12.10 non-inference

Lineage is mandatory audit context but is not converted into:

```text
independent evidence count
replication count
weight
confidence
majority vote
positive independence
```

### PR12.11 semantic mapping

One evidence record may semantically cover multiple admitted-policy requirements, and multiple evidence records may cover one requirement. That does not create cardinality or independence semantics.

Only a terminal approved HUMAN mapping review plus current process-local mapping-review authority permits final requirement application.

### PR12.12 direction

PR12.12 fully replays PR12.11 and the upstream PR12.7–PR12.10 authority/basis chain. Direction is computed from the **entire exact PR12.9 disposition universe**, not from only mapped evidence.

The deterministic v1 table is:

| Required coverage | Directional basis | Coverage | Conflict | Conclusion |
|---|---|---|---|---|
| incomplete | any | `PARTIAL` | unresolved only if both directions exist | `INSUFFICIENT` |
| complete | supports only | `SUFFICIENT_FOR_CLAIM` | `NONE` | `SUPPORTED` |
| complete | contradicts only | `SUFFICIENT_FOR_CLAIM` | `NONE` | `CONTRADICTED` |
| complete | supports + contradicts | `SUFFICIENT_FOR_CLAIM` | `UNRESOLVED` | `MIXED` |
| complete | no directional bearing | `SUFFICIENT_FOR_CLAIM` | `NONE` | `ABSTAINED` |

PR12.12 v1 never emits `RESOLVED_BY_POLICY` and introduces no reliability threshold, evidence weight, majority rule, recency rule, replication count, or confidence score.

The resulting `ClaimEvaluation` has a deterministic domain-separated identity. Its separate audit receipt binds the exact upstream policy/disposition/lineage/application/review basis. Serialized receipts are audit data, not runtime authority.

## PR12.13 — end-to-end current-state composition audit

PR12.13 adds no production API or inference rule. Its executable integration suite proves the existing public APIs compose from a generic external observation to fresh PR11.8 current-state authority.

The principal historical proof is:

```text
PR12.5  PARTIAL / INSUFFICIENT evaluation
PR12.12 SUFFICIENT_FOR_CLAIM / SUPPORTED evaluation

        |
PR11.3 retains both immutable records
        |
PR11.4 includes both in the complete portfolio
        |
PR11.5 basis includes both
        |
reasoning dimension = SUPPORTED
```

PR11.4 explicitly rejects dropping the older PR12.5 evaluation.

PR12.13 also proves:

- a free-standing PR12.12 evaluation has no PR11.4 membership before PR11.3 persistence;
- changing retained evaluation bytes under the same id fails PR11.3;
- appending historical evaluation data stales an old PR11.4 portfolio;
- PR11.5 still requires complete claim-to-dimension bindings;
- a derived but unpersisted state cannot be accepted;
- a persisted but unaccepted state is absent from PR11.8 candidates;
- an accepted state is not current without explicit selection;
- structural current history is not current authority without fresh PR11.8 replay.

### Conflict preservation proof

A second generic scenario establishes:

```text
complete requirements
+ SUPPORTS evidence
+ CONTRADICTS evidence
        |
PR12.12 = MIXED / UNRESOLVED
        |
PR11.4 complete basis
        |
PR11.5 dimension = INSUFFICIENT / UNRESOLVED
```

No state layer silently resolves the conflict.

See [`generic_capability_inference_e2e_audit_v1.md`](generic_capability_inference_e2e_audit_v1.md) for the executable audit contract and observed integration boundaries.

## PR12.14 — end-to-end product/read composition audit

PR12.14 adds no production API or inference rule. It extends the exact generic PR12.13 trace from fresh PR11.8 current authority through the already-existing PR11.9–PR11.11 read/advisory stack.

The positive proof is:

```text
real PR12-derived current SELECT
        |
state-less PR11.9 progression request
        |
fresh PR11.8 replay -> exact selected state
        |
PR11.9 governed progression
        |
PR11.10 complete current-selection history-head portfolio
        |
PR11.11 fresh PR11.9 + PR11.10 reconciliation
        |
unchanged PR9 presentation
```

The audit also records two important fail-closed details:

1. PR11.8 does not permit a root `CLEAR` for a scope with no accepted candidate state. A valid `CLEAR` is audited only after a real governed `SELECT`; PR11.10 preserves that head as `CLEAR`, while PR11.9 distinguishes it from `ABSENT`.
2. PR11.11 historical filtering is governed by the selected state's semantic `state.as_of`, not its later derivation time. A product request earlier than `state.as_of` is rejected rather than silently hiding that current state.

Serialized PR11.11 snapshots remain audit artifacts and must survive fresh live-source validation. Historical current-selection appends stale older product snapshots even when the appended governance act is not later than the old snapshot's generation time.

```text
PRODUCT REQUEST != STATE SELECTOR
SERIALIZED PRODUCT SNAPSHOT != CURRENT AUTHORITY
CLEAR != ABSENT
PRODUCT VIEW != CAPABILITY WRITE-BACK
PROGRESSION != READINESS / PERMISSION / MASTERY
```

See [`generic_governed_product_read_e2e_audit_v1.md`](generic_governed_product_read_e2e_audit_v1.md).

## HDE integration boundary

The stable read/advisory boundary remains PR11.11. The generic write path can now be traced through that boundary, but only through all explicit review, policy, persistence, acceptance, current-selection, and fresh-replay gates above.

```text
READ / ADVISORY HDE INTEGRATION                              = READY
REVIEWED OBSERVATION -> NEUTRAL EVIDENCE                     = READY
EVIDENCE -> REVIEWED BOUNDED CLAIM                            = READY
GENERIC HUMAN EVIDENCE-LEVEL ClaimEvaluation                  = READY
DECLARATIVE DOMAIN POLICY + HUMAN POLICY ADMISSION            = READY
COMPLETE DISPOSITION / LINEAGE / REQUIREMENT MAPPING          = READY
DOMAIN-SUFFICIENT DIRECTIONAL ClaimEvaluation                 = READY
PR12 -> PR11.8 GOVERNED CURRENT-STATE COMPOSITION             = VERIFIED BY PR12.13
PR12 -> PR11.11 GOVERNED PRODUCT/READ COMPOSITION             = AUDITED BY PR12.14
AUTOMATIC CLOSED-LOOP CAPABILITY UPDATE                       = NOT AUTHORIZED
```

`VERIFIED` / `AUDITED` means the explicit governed transitions compose. It does not mean an HDE adapter, model, external source, progression layer, or product surface may bypass review, persistence, acceptance, selection, or authority replay.

```text
HDE ACTIVITY != EVIDENCE
HDE OUTPUT != CAPABILITY UPDATE
HDE VIEW != CAPABILITY AUTHORITY
SUPPORTED != MASTERY
CURRENT != READINESS
CURRENT != PERMISSION
PRODUCT VIEW != WRITE-BACK AUTHORITY
```

## Release-level invariants

The architecture should fail closed against the following shortcuts:

```text
latest evaluation wins
mapped evidence only determines direction
more evidence automatically means stronger support
shared lineage automatically means independent replication
persisted state automatically becomes accepted
accepted state automatically becomes current
structural current history automatically becomes authority
product request selects current state
presentation omission erases governance history
current capability state automatically grants permission/readiness/mastery
```

If a future layer needs one of those semantics, it must introduce an explicit versioned policy and its own governance boundary rather than silently infer it from existing records.
