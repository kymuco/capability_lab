# PR12.8 — Complete Snapshot-Bound Claim Evidence Candidate Portfolio v1

## Purpose

PR12.8 introduces the first generic anti-cherry-picking boundary before domain-policy application.

For one exact `EpistemicRecordSet`, one exact existing `CapabilityClaimId`, and one exact inclusive `as_of` boundary, the runtime derives every evidence record that is a candidate for later disposition. The caller may not silently omit an available same-subject record or add an unavailable record.

This layer deliberately makes **no relevance or evidentiary judgment**.

```text
EVIDENCE CANDIDATE != RELEVANT EVIDENCE
EVIDENCE CANDIDATE != SUPPORT
EVIDENCE CANDIDATE != CONTRADICTION
EVIDENCE CANDIDATE != RELIABLE EVIDENCE
COMPLETE CANDIDATE PORTFOLIO != SUFFICIENT EVIDENCE
PORTFOLIO RECEIPT != CONTENT AUTHORITY
PORTFOLIO PROVENANCE != CONTENT AUTHORITY
PORTFOLIO MEMBERSHIP != POLICY COVERAGE
PORTFOLIO MEMBERSHIP != INDEPENDENCE
```

## Frozen membership rule

Given exact `(records, claim_id, as_of)`:

1. strict-reconstruct the supplied `EpistemicRecordSet`;
2. resolve exactly one stored claim with `claim_id`;
3. require `claim.created_at <= as_of`;
4. inspect every `EvidenceRecord` in the snapshot;
5. include a record iff `evidence.subject_ref == claim.subject_ref` and `evidence.recorded_at <= as_of`;
6. record same-subject evidence with `recorded_at > as_of` in `excluded_future_evidence_ids`;
7. ignore different-subject evidence for this claim portfolio;
8. sort all evidence identities canonically.

An empty portfolio is valid.

`recorded_at`, not merely `observed_at`, defines availability:

```text
observed earlier != governed record available earlier
recorded_at <= as_of -> candidate
recorded_at > as_of  -> excluded future evidence
```

## Forbidden membership filters

PR12.8 does not filter membership by evidence kind, evidence outcome, context description/tags, payload refs, provenance source kind, claim statement/scope, capability-concept heuristics, interpretation status, existing `ClaimEvaluation`, bearing, reliability, recency weighting inside the boundary, evaluator identity, domain policy, or repetition/dependence assumptions.

The broad same-subject rule is intentional. Later governance may explicitly disposition a candidate as `NOT_RELEVANT`; this layer may not silently erase it.

## Receipt semantics

`ClaimEvidenceCandidatePortfolioReceipt` contains:

```text
snapshot_sha256
claim_id
subject_ref
concept_ref
as_of
evidence_ids
excluded_future_evidence_ids
```

The receipt is ordinary deterministic audit/cache data. It is serializable and reconstructible. It is **not** a runtime permission, transition capability, trusted-origin token, reviewer credential, or cryptographic proof.

Unlike PR12.7/PR12.7.1, PR12.8 completeness is fully derivable from content:

```text
PR12.7 governed admission
cannot be inferred from registry shape
-> runtime transition authority required

PR12.8 portfolio completeness
is fully derivable from exact records + claim_id + as_of
-> deterministic rebuild is content authority
```

Therefore no PID table, object-identity issuance registry, fork capability, or non-serializable authority token exists in PR12.8.

## Revalidation

`validate_exact_claim_evidence_candidate_selection_v1` always rebuilds the expected complete portfolio from exact `(records, claim_id, as_of)`.

A receipt is optional. When supplied, it must strict-reconstruct and equal the independently rebuilt portfolio in full.

Consequences:

- caller-created exact receipts are acceptable only if their content is exactly what records-derived replay produces;
- JSON-restored receipts are acceptable only after the same replay;
- `dataclasses.replace(...)` does not grant authority;
- a subset receipt fails;
- a stale snapshot/claim/time receipt fails;
- receipt origin cannot widen selection.

Selection itself must be an exact tuple of exact `EvidenceId` values, contain no duplicates, and equal the complete rebuilt `evidence_ids` exactly.

```text
selected < expected -> FAIL (omission / cherry-picking)
selected > expected -> FAIL (future / other-subject / otherwise inadmissible extra)
selected = expected -> PASS
```

## Snapshot and claim binding

The receipt binds `epistemic_snapshot_sha256_v1(records)` plus the exact stored claim identity, subject, concept revision, and explicit `as_of`.

Changing any snapshot content invalidates an old receipt, even when the changed record is unrelated to the target subject. This is intentional: the receipt names one exact immutable epistemic snapshot.

A historical backfill inserted into a later snapshot with `recorded_at <= the same as_of` changes the snapshot digest and changes the rebuilt candidate portfolio. The backfilled record then becomes mandatory in the new selection.

## Strictness / corruption model

PR12.8 treats public API input as untrusted structural data and fails closed on subclasses where exact core value types are required, non-tuple selection/receipt containers, duplicate evidence ids, non-exact scalar fields in membership-critical identities/timestamps, post-construction receipt mutation, unknown/missing/duplicate JSON fields, noncanonical JSON id ordering, and stale snapshot/claim/time bindings.

The supplied `EpistemicRecordSet` is strict-reconstructed through canonical snapshot serialization before membership is derived.

This is deterministic public-API validation, not protection against arbitrary hostile code that can rewrite module globals or interpreter memory.

## Dependence remains unresolved

```text
TWO EvidenceRecord VALUES != TWO INDEPENDENT OBSERVATIONS
MULTIPLE SOURCES != INDEPENDENCE
REPEATED RECORDS != REPLICATION
COMPLETE PORTFOLIO != INDEPENDENT PORTFOLIO
```

Shared provenance, derived evidence, repeated measurements, common lineage, temporal correlation, and other dependence semantics are later governance work.

## Interaction with ClaimEvaluation

PR12.8 creates no `ClaimEvaluation` and does not require candidates to already have evaluations. A later layer may require an explicit disposition for every candidate, including `NOT_RELEVANT`, before policy application.

```text
absence of ClaimEvaluation != NOT_RELEVANT
```

PR12.8 does not create that equivalence.

## Public API

```python
build_complete_claim_evidence_candidate_portfolio_v1(
    *, records, claim_id, as_of,
)

validate_exact_claim_evidence_candidate_selection_v1(
    *, records, claim_id, as_of, selected_evidence_ids, portfolio=None,
)
```

Receipt serialization helpers are deterministic schema-v1 dict/JSON conversions. Serialization preserves data only; it does not preserve or create authority because no runtime authority exists at this layer.

## Non-goals

```text
PR12.8 != EVIDENCE RELEVANCE JUDGMENT
PR12.8 != EVIDENCE BEARING
PR12.8 != EVIDENCE RELIABILITY
PR12.8 != EVIDENCE INDEPENDENCE GOVERNANCE
PR12.8 != REQUIREMENT COVERAGE
PR12.8 != POLICY APPLICATION
PR12.8 != MULTI-EVIDENCE ClaimEvaluation
PR12.8 != CONFLICT RESOLUTION
PR12.8 != DOMAIN SUFFICIENCY
PR12.8 != PersonalCapabilityState
PR12.8 != PROGRESSION
PR12.8 != PRESENTATION
PR12.8 != RUNTIME ADMISSION AUTHORITY
PR12.8 != CRYPTOGRAPHIC AUTHENTICATION
```

## Intended continuation

```text
PR12.8 complete records-derived candidate portfolio
-> complete explicit candidate disposition / relevance coverage
-> dependence / repetition governance
-> exact admitted-policy requirement mapping/application
-> directional/domain-sufficient ClaimEvaluation
-> existing complete portfolio/state path
```
