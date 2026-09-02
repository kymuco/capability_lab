# PR12.7.1 — PR12.3 Terminal-Review Authority Hardening / PR12.4 Materialization Gate v1

## Purpose

PR12.7.1 closes an authority-confusion gap in the existing PR12.3 → PR12.4 path without changing persisted PR12.2, PR12.3, or PR12.4 semantic identities.

Before this hardening, the following structural path was possible:

```text
publicly constructible exact ACCEPT review
        |
        v
ExternalEvidenceInterpretationReviewLedger(reviews=(review,))
        |
        v
require_accepted_external_evidence_claim_interpretation_review_v1
        |
        v
PR12.4 CapabilityClaim materialization
```

The populated ledger was structurally valid, but the caller could skip `admit_external_evidence_claim_interpretation_review_v1` entirely.

The hardened invariant is:

```text
RAW REVIEW
!= POPULATED REVIEW LEDGER
!= TERMINAL REVIEW ADMISSION AUTHORITY
```

## Audit data versus runtime authority

`ExternalEvidenceClaimInterpretationReview` and `ExternalEvidenceInterpretationReviewLedger` remain canonical serializable audit artifacts.

Their schema-v1 JSON, deterministic review digest, and deterministic review-ledger digest are unchanged by PR12.7.1.

A populated ledger can therefore be reconstructed from trusted persistence for audit and structural replay. That reconstruction does **not** implicitly restore downstream materialization authority.

```text
review JSON                 = audit data
review-ledger JSON          = audit data
ledger digest               = deterministic integrity
runtime terminal authority  = issued only by explicit admission/replay
```

`resolve_external_evidence_claim_interpretation_terminal_review_v1` is deliberately structural. It resolves and validates an exact review from supplied audit data, but it does not grant downstream `ACCEPT` authority by itself.

## Runtime terminal-review admission authority

`admit_external_evidence_claim_interpretation_review_v1` keeps its existing return shape: it returns the canonical successor review ledger, or the same ledger on exact idempotent replay.

In addition, the function now records process-local validator authority for the exact returned ledger object and exact proposal transition. The runtime issuance binds:

- exact ledger object identity;
- issuing process id;
- exact current review-ledger digest;
- exact predecessor review-ledger digest immediately before this proposal's terminal review;
- exact one-review transition-successor digest immediately after that review was appended;
- exact PR12.2 candidate digest;
- exact PR12.3 review digest;
- exact review id / proposal identity.

The predecessor and transition-successor are reconstructed from the exact position of the terminal review in the current append-only ledger. On replay through a later grown ledger, the original one-review transition remains fixed while the current-ledger digest additionally binds the complete present audit snapshot.

`require_accepted_external_evidence_claim_interpretation_review_v1` first performs the existing structural candidate/review validation, then requires this exact runtime issuance, replays the predecessor/transition/current-ledger bindings, and only then requires the terminal verdict to be `ACCEPT`.

Therefore:

```text
manual populated ledger                   -> no authority
JSON-restored populated ledger             -> no authority
exact admit/replay on that ledger          -> runtime authority
exact admitted ACCEPT                      -> downstream allowed
exact admitted REJECT                      -> downstream denied
```

## Explicit replay after persistence

Persistence preserves audit content, not process-local authority.

After loading canonical PR12.3 review-ledger JSON, a consumer that wants PR12.4 materialization authority must explicitly replay:

```text
admit_external_evidence_claim_interpretation_review_v1(
    review_ledger=loaded_ledger,
    ... exact candidate ...,
    ... exact review ...,
)
```

For an exact already-present review, this replay is idempotent for ledger content:

```text
review count before replay == review count after replay
ledger JSON before replay   == ledger JSON after replay
ledger digest before replay == ledger digest after replay
```

The replay only re-establishes process-local validator authority for that exact audit and exact terminal-transition basis.

## Process boundary

The runtime authority is explicitly process-local.

Each issuance records the process id that performed admission/replay. A POSIX `fork()` child inherits Python memory but has a different `os.getpid()`, so a parent-issued authority record is rejected in the child.

```text
PARENT-PROCESS AUTHORITY != CHILD-PROCESS AUTHORITY
```

The child may explicitly replay the exact already-admitted review against its inherited canonical ledger to obtain child-local authority without adding a second review.

Spawn/serialization also does not restore authority implicitly because ordinary review/ledger serialization contains no runtime issuance state.

This is a public-API/process-local governance boundary. It is **not**:

- a cryptographic capability;
- a signature;
- authenticated reviewer identity;
- hostile-process memory protection;
- a trusted timestamp;
- globally-current-ledger proof;
- distributed consensus.

## PR12.4 gate

PR12.4 already routes both materialization and full materialization replay through `require_accepted_external_evidence_claim_interpretation_review_v1`.

PR12.7.1 therefore hardens both paths without changing the PR12.4 public materialization signature or deterministic claim construction:

```text
exact PR12.2 candidate
+
canonical PR12.3 review ledger
+
process-local exact terminal-review admission authority
+
terminal ACCEPT
        |
        v
existing deterministic PR12.4 claim materialization
```

A raw `ACCEPT`, manually populated ledger, or deserialized populated ledger can no longer materialize a claim until explicit terminal-review admission/replay occurs.

## Preserved semantic identity

PR12.7.1 intentionally does not change:

- PR12.2 candidate canonical serialization;
- PR12.2 candidate digest;
- PR12.3 review canonical serialization;
- PR12.3 review digest;
- PR12.3 review-ledger canonical serialization;
- PR12.3 review-ledger digest;
- PR12.4 deterministic claim semantics;
- PR12.4 deterministic claim id;
- PR12.4 materialization receipt schema or digest;
- PR11.3 epistemic snapshot succession semantics.

For the same genuinely admitted exact `ACCEPT` basis, materialization before and after an audit JSON round-trip plus explicit replay produces the same deterministic claim and materialization receipt.

## Stale and changed ledgers

Authority is bound simultaneously to the exact current ledger object/current ledger digest and to the exact historical predecessor → one-review transition for the terminal review.

If a new terminal review is appended, the successor ledger is a different exact audit snapshot. Existing authority issued for a predecessor ledger is not silently promoted to the new ledger.

To use an older exact review through the grown ledger, the consumer must explicitly replay that exact review against the grown canonical ledger. The replay does not append a duplicate review; it re-establishes authority for the exact grown current ledger while preserving and re-validating the older review's original predecessor/transition-successor prefix.

Post-construction mutation that changes ledger content, review ordering, or the terminal transition changes one or more bound digests and invalidates previously issued authority.

## REJECT remains terminal but non-materializing

A genuine `REJECT` may pass terminal-review admission and therefore have valid terminal lineage authority. That does not convert it into downstream `ACCEPT` authority.

```text
ADMITTED REJECT != ACCEPT
ADMITTED REJECT != contradiction
ADMITTED REJECT != negative evidence
ADMITTED REJECT != incapability
```

PR12.4 still requires exact `ACCEPT` before creating a `CapabilityClaim`.

## Authority limits

PR12.7.1 changes governance authority only. It does not introduce or widen:

```text
review admission != claim truth
review admission != EvidenceBearing
review admission != reliability
review admission != evidence sufficiency
review admission != ClaimEvaluation
review admission != policy application
review admission != PersonalCapabilityState
review admission != progression
review admission != presentation
```

## Position in the generic path

The hardened sequence is:

```text
PR12.2 exact interpretation proposal
        |
        v
PR12.3 declared HUMAN review artifact
        |
        v
PR12.7.1 explicit terminal-review admission / replay
        |
        v
process-local exact review authority
        |
   ACCEPT only
        v
PR12.4 deterministic CapabilityClaim materialization
```

This hardening is intentionally completed before PR12.8 so the future complete evidence-candidate / anti-cherry-picking layer is not built on top of a structurally bypassable interpretation-review boundary.
