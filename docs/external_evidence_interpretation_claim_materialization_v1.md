# PR12.4 — Governed Accepted External Evidence Interpretation → CapabilityClaim Materialization v1

## PR12.7.1 authority hardening note

PR12.4 claim semantics, deterministic claim identity, materialization receipt schema/digest, and PR11.3 snapshot succession semantics remain unchanged. However, after PR12.7.1, a structurally populated or deserialized PR12.3 review ledger is audit data only. Both PR12.4 materialization and full materialization replay require `require_accepted_external_evidence_claim_interpretation_review_v1`, which now requires process-local terminal-review admission authority established by explicit `admit_external_evidence_claim_interpretation_review_v1` admission/replay.

```text
RAW ACCEPT != TERMINAL ADMISSION AUTHORITY
POPULATED REVIEW LEDGER != TERMINAL ADMISSION AUTHORITY
DESERIALIZED REVIEW LEDGER != TERMINAL ADMISSION AUTHORITY
EXPLICIT ADMISSION / REPLAY + ACCEPT -> eligible for PR12.4
```

See `external_evidence_claim_interpretation_review_authority_hardening_v1.md` for the exact runtime authority, process-boundary, predecessor/transition-successor, and replay invariants.

## Purpose

PR12.4 introduces the first generic transition from one exact terminally admitted PR12.3 `ACCEPT` into a real PR2 `CapabilityClaim` and immediately subjects that new claim to the existing PR11.3 append-only epistemic succession boundary.

The transition creates **claim identity only**: it makes an exact proposition representable as something that a later evaluation policy may assess. It does not decide whether the proposition is true and it does not assess how any evidence bears on it.

```text
PR12.1 neutral external EvidenceRecord
        |
        v
PR12.2 exact evidence -> interpretation candidate
        |
        v
PR12.3 terminal review-ledger ACCEPT
        |
        + PR12.7.1 exact runtime terminal-review authority
        v
PR12.4 deterministic CapabilityClaim
        |
        v
PR11.3 immutable epistemic snapshot successor
```

## Core invariant

```text
PR12.4 MATERIALIZATION
=
ONE EXACT VALID PR12.2 CANDIDATE
+
ONE EXACT TERMINAL PR12.3 ACCEPT
+
ONE EXACT PR12.7.1 TERMINAL-REVIEW ADMISSION AUTHORITY
+
ONE DETERMINISTIC IMMUTABLE CLAIM RECORD IDENTITY
+
ONE EXACT CLAIM SEMANTIC COPY
+
ONE SEMANTIC-DUPLICATE FAIL-CLOSED CHECK
+
ONE VALID PR11.3 SNAPSHOT SUCCESSION
```

```text
CLAIM EXISTS != CLAIM TRUE
CLAIM MATERIALIZED != EvidenceBearing.SUPPORTS
CLAIM MATERIALIZED != SUPPORTED
CLAIM MATERIALIZED != CAPABILITY PRESENT
CLAIM MATERIALIZED != CAPABILITY STATE
CLAIM MATERIALIZED != READINESS / MASTERY / PERMISSION
```

## Frozen policy

The materialization policy is:

```text
capability_lab:accepted_external_interpretation_claim_materialization@1
```

## Exact terminal acceptance requirement

`materialize_accepted_external_evidence_interpretation_claim_v1` does not accept a raw PR12.3 review object. It accepts the PR12.3 review ledger and routes through `require_accepted_external_evidence_claim_interpretation_review_v1`.

After PR12.7.1, structural presence of an `ACCEPT` review in that ledger is not sufficient. The supplied exact ledger object must have process-local terminal-review admission authority established by `admit_external_evidence_claim_interpretation_review_v1` for the exact candidate/review/current-ledger and exact predecessor → one-review terminal transition.

```text
raw review without ledger admission          -> FAIL
manual populated ACCEPT ledger               -> FAIL
JSON-restored ACCEPT ledger before replay    -> FAIL
explicit exact admission/replay + REJECT     -> FAIL
explicit exact admission/replay + ACCEPT     -> eligible for PR12.4
```

The PR12.3 structural resolver still replays the exact PR12.2 candidate validator, including retained evidence bytes, subject, exact capability concept revision and candidate digest. PR12.7.1 additionally requires runtime admission authority before `require_accepted...` returns the exact review. Mutation of those inputs or of the bound review-ledger transition fails closed.

The materialization receipt continues to bind the exact resolved review rather than embedding runtime authority or the whole review-ledger digest. Runtime authority is deliberately not serialized. Appending an unrelated later terminal review therefore requires explicit replay for the target review against the grown ledger before downstream use, but does not change deterministic claim identity or the materialization receipt for the same exact accepted review basis.

## No caller-selected claim semantics

The public materialization API exposes only:

```text
epistemic_snapshot
catalog
candidate
review_ledger
```

It exposes no caller parameter for:

```text
claim_id
subject_ref
concept_ref
statement
scope
created_at
EvidenceBearing
EvidenceReliability
ClaimEvaluation
state / score / mastery / readiness / permission
```

The materialized `CapabilityClaim` is an exact semantic copy of the accepted candidate:

```text
claim.subject_ref = candidate.subject_ref
claim.concept_ref = candidate.concept_ref
claim.statement   = candidate.claim_statement
claim.scope       = candidate.claim_scope
```

An accepted bounded proposition therefore cannot be silently widened during materialization.

## Semantic equivalence versus immutable record identity

PR12.4 distinguishes two different concepts that must not be collapsed.

**Claim semantics** are the proposition being evaluated:

```text
subject_ref
+ exact concept_ref revision
+ statement
+ scope description + tags
```

Evidence identity, proposal id, proposer rationale, review id, and review rationale are not part of those semantics. PR2 already requires evaluated evidence to belong to `ClaimEvaluation`, not to claim semantics or claim provenance.

A persisted `CapabilityClaim`, however, is an immutable **record**, not only an abstract proposition. It also contains:

```text
created_at
provenance source
provenance operation
provenance actor
provenance mechanism
provenance note
```

PR12.4 derives `created_at` and the actor provenance from the exact admitted terminal review. Two otherwise identical propositions reviewed at different times or by different declared reviewers therefore have different immutable claim bytes. They must not share one `CapabilityClaimId`.

The deterministic claim id is therefore content-stable for the complete materialized claim record, excluding only the id itself. Its domain-separated basis contains:

```text
frozen PR12.4 policy ref
+
exact claim semantics
+
terminal review reviewed_at
+
declared reviewer actor ref
+
frozen materialization provenance content
```

The resulting id has the form:

```text
external_interpretation:<sha256>
```

This gives the required invariant:

```text
same CapabilityClaimId
=> same deterministic materialized CapabilityClaim bytes
```

Proposal ids, proposer rationale, selected evidence identity, review id, and review rationale do not participate in the claim id because none of them are stored in the claim record itself. They remain committed by the PR12.4 materialization receipt as the governance/audit basis that permitted creation.

## Semantic duplicate governance

Content-stable record identity alone is not enough. A predecessor may already contain the same proposition under another id — for example a legacy/manual claim, or a claim produced in another governed path with different creation metadata.

Before append, PR12.4 therefore compares every retained claim by exact:

```text
subject_ref
concept_ref
statement
scope
```

If a semantically identical claim already exists under **any** id, materialization fails closed.

```text
same deterministic claim id already retained -> FAIL
same proposition under different claim id     -> FAIL
related but different proposition              -> allowed
```

PR12.4 does not silently reuse, replace, merge, supersede, or reconcile the existing claim. Any future reconciliation of independently created semantic duplicates requires its own explicit governance boundary.

This is intentionally lineage-local. PR12.4 does not claim that independently forked epistemic histories have a globally canonical claim record or globally canonical review lineage.

## Deterministic time

The claim time is not caller-selected:

```text
claim.created_at = terminal_review.reviewed_at
materialization_receipt.materialized_at = terminal_review.reviewed_at
```

The exact same predecessor/candidate/admitted-review inputs therefore produce byte-identical claim and receipt outputs after exact runtime review-admission authority has been established.

Because `created_at` is part of the immutable claim record, changing the terminal review time changes the deterministic claim record identity. The semantic-duplicate guard then prevents a later materialization of the same proposition from creating a second claim inside one predecessor lineage.

## Claim provenance separation

PR2 deliberately forbids a `CapabilityClaim` from binding an `EvidenceRecord` as claim provenance. Evidence is evaluated later through `ClaimEvaluation`; it is not part of claim identity.

PR12.4 preserves that invariant. The generated claim provenance contains a system materialization source plus a governance step identifying the declared human reviewer and frozen PR12.4 mechanism. It contains no `ProvenanceSourceKind.EVIDENCE_RECORD`.

The exact cross-layer binding is carried by the PR12.4 materialization receipt:

```text
proposal_id
candidate_sha256
review_id
review_sha256
claim_id
claim_sha256
predecessor_snapshot_sha256
successor_snapshot_sha256
materialized_at
```

Runtime terminal-review authority is intentionally not added to this persisted receipt; it is re-established by explicit PR12.7.1 admission/replay when the persisted audit basis is reused.

## PR11.3 immutable snapshot admission

PR12.4 does not invent a second epistemic persistence mechanism.

It constructs a successor `EpistemicRecordSet` by preserving all predecessor families exactly and adding one deterministic claim:

```text
successor.evidence_records = predecessor.evidence_records
successor.claims           = predecessor.claims + materialized claim
successor.evaluations      = predecessor.evaluations
```

The successor is then validated by `validate_epistemic_snapshot_successor_v1`.

The returned PR11.3 receipt must show:

```text
added_claim_ids      = exactly materialized claim id
added_evidence_ids   = ()
added_evaluation_ids = ()
```

No evidence or evaluation record is created by PR12.4.

## Unrelated append behavior

Claim record identity does not bind whole growing ledger/snapshot hashes, but PR12.7.1 runtime authority does bind the exact current review-ledger snapshot used for downstream authorization.

Therefore:

```text
unrelated PR12.3 review-ledger append
-> deterministic claim identity unchanged
-> old runtime authority is not promoted to grown ledger
-> exact target-review replay on grown ledger required

unrelated epistemic append before materialization
!= change claim record identity

same semantics + same review-derived claim bytes
through different evidence/proposal/review-id/rationale metadata
-> same claim record identity

same semantics + different review-derived created_at/provenance bytes
-> different record identity
-> semantic-duplicate guard prevents a second same proposition in one lineage
```

The PR12.4 receipt records the exact candidate, exact terminal review, and exact predecessor/successor snapshot digests for the particular persistence transition that occurred.

## Receipt serialization

`ExternalEvidenceInterpretationClaimMaterializationReceipt` uses strict schema-v1 deterministic JSON serialization.

It rejects:

- unknown fields;
- missing fields;
- duplicate JSON object keys;
- malformed typed ids, hashes, policy refs or times;
- non-finite JSON constants.

The in-memory `ExternalEvidenceInterpretationClaimMaterialization` contains the validator-issued private PR11.3 succession receipt. That validator authority is intentionally **not recreated from serialized bytes**. A materialization result is validated by replaying the PR12.2 candidate, requiring PR12.7.1 runtime authority for the exact PR12.3 terminal `ACCEPT`, rebuilding the deterministic claim, rebuilding the exact successor, and replaying the PR11.3 validator against the supplied governance inputs.

```text
SERIALIZED REVIEW LEDGER != PR12.7.1 TERMINAL REVIEW AUTHORITY
SERIALIZED RECEIPT != PR11.3 VALIDATOR AUTHORITY
RECEIPT DIGEST != SIGNATURE
RECEIPT DIGEST != TRUSTED TIME
RECEIPT DIGEST != GLOBAL/CURRENT SNAPSHOT AUTHORITY
```

## Explicit non-authority

PR12.4 creates no `EvidenceAssessment` and no `ClaimEvaluation`.

```text
PR12.3 ACCEPT != CLAIM TRUTH
PR12.7.1 REVIEW ADMISSION != CLAIM TRUTH
PR12.4 CLAIM MATERIALIZATION != CLAIM TRUTH
PR12.4 CLAIM MATERIALIZATION != EvidenceBearing.SUPPORTS
PR12.4 CLAIM MATERIALIZATION != EvidenceReliability
PR12.4 CLAIM MATERIALIZATION != EvaluationConclusion.SUPPORTED
PR12.4 CLAIM MATERIALIZATION != CAPABILITY STATE
PR12.4 CLAIM MATERIALIZATION != PROGRESSION AUTHORITY
```

PR12.5 remains the generic governed external-evidence evaluation boundary. It requires an exact materialized claim plus an exact evidence basis and explicit evaluation semantics; it must not infer `SUPPORTED` merely from PR12.3 acceptance, PR12.7.1 terminal admission, or PR12.4 claim existence.
