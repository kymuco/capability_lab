# PR12.3 — Explicit Human Review of External Evidence → Claim Interpretation Proposals v1

## Purpose

PR12.3 adds the first generic human-review boundary above PR12.2 and makes the
review terminal only after governed admission into an immutable review-ledger
lineage.

PR12.2 can propose that one exact retained external `EvidenceRecord` is relevant
to one exact `CapabilityConceptRef` and one bounded claim statement/scope.
PR12.3 allows a declared human reviewer to accept or reject that **exact
proposal**, then admits at most one exact terminal review for that proposal into
one append-only review-ledger lineage.

It still does not create a `CapabilityClaim`, decide `EvidenceBearing`, assign
reliability, run a `ClaimEvaluation`, or update capability state.

```text
PR12.1 neutral external EvidenceRecord
        |
        v
PR11.3 immutable epistemic retention
        |
        v
PR12.2 interpretation candidate
        |
        v
PR12.3 declared HUMAN review artifact
        |
        v
immutable review-ledger admission
        |
   +----+----+
   |         |
 ACCEPT    REJECT
   |         |
   X no CapabilityClaim
   X no EvidenceBearing
   X no ClaimEvaluation
   X no state/progression authority
```

## Core invariant

```text
PR12.3 TERMINAL REVIEW ADMISSION
=
ONE EXACT VALID PR12.2 CANDIDATE
+
ONE EXACT CANDIDATE DIGEST
+
ONE DECLARED HUMAN REVIEWER
+
ONE ACCEPT | REJECT VERDICT
+
ONE FROZEN REVIEW POLICY
+
ONE APPEND-ONLY REVIEW-LEDGER LINEAGE
```

The frozen policy ref is:

```text
capability_lab:external_evidence_claim_interpretation_human_review@1
```

## Review artifact versus terminal admission

`ExternalEvidenceClaimInterpretationReview` is an immutable review artifact. It
binds the exact candidate and human decision, but a raw review object by itself
is not the terminal lineage authority.

Terminality is established by
`ExternalEvidenceInterpretationReviewLedger` and
`admit_external_evidence_claim_interpretation_review_v1`.

Within one valid ledger lineage:

```text
one proposal_id -> at most one terminal review
```

An exact replay of the already admitted review is idempotent. A different
review for the same proposal — including an opposite verdict — fails closed.
A `review_id` also cannot be rebound to another proposal.

```text
REJECT admitted for proposal P
+
later ACCEPT for the same P
-> REJECT conflicting second terminal review
```

This prevents a later consumer from carrying both contradictory terminal
reviews in one valid lineage and cherry-picking the convenient verdict.

The ledger itself is not an authenticated global store and its digest is not a
claim that a supplied snapshot is the uniquely current snapshot in the world.
PR12.3 guarantees append-only terminality **within the supplied validated ledger
lineage**. A deployment that needs globally canonical persistence must govern
which ledger lineage is authoritative rather than treating an arbitrary ledger
snapshot as trusted merely because it deserializes.

## Append-only succession

`validate_external_evidence_interpretation_review_ledger_successor_v1` requires
a successor ledger to preserve the complete exact predecessor review prefix.

```text
previous reviews: [A, B]
valid successor:  [A, B, C]
exact replay:     [A, B]
invalid:          [A]
invalid:          [B, A]
invalid:          [A, B']
```

A prior terminal decision therefore cannot be removed, reordered, rewritten,
or replaced inside a valid lineage.

The ledger has its own deterministic, domain-separated digest:

```text
capability_lab/external_evidence_claim_interpretation_review_ledger@1\0
```

The digest is content integrity only. It is not a signature, authorization
token, trusted-time proof, or globally canonical persistence proof.

## Verdict semantics

### ACCEPT

`ACCEPT` means only:

> the declared human reviewer admits this exact PR12.2 evidence → concept /
> claim-scope interpretation proposal for a later governed epistemic step.

It does **not** mean:

```text
ACCEPT != claim truth
ACCEPT != EvidenceBearing.SUPPORTS
ACCEPT != reliability
ACCEPT != sufficient evidence
ACCEPT != ClaimEvaluation
ACCEPT != capability
ACCEPT != state
ACCEPT != readiness
ACCEPT != mastery
ACCEPT != permission
```

A downstream consumer must resolve the exact terminal review from the ledger.
`require_accepted_external_evidence_claim_interpretation_review_v1` returns the
exact admitted review only when that sole terminal verdict is `ACCEPT`; it
rejects missing review admission and terminal `REJECT`.

### REJECT

`REJECT` means only that this exact proposal is not admitted for downstream
use.

```text
REJECT != EvidenceBearing.CONTRADICTS
REJECT != negative evidence
REJECT != failure
REJECT != incapability
REJECT != state downgrade
```

A rejected interpretation can be badly scoped, irrelevant, too broad,
premature, or otherwise unsuitable without saying anything negative about the
person.

## Exact candidate binding

Every review stores:

```text
proposal_id
candidate_sha256
```

`candidate_sha256` is the existing PR12.2 domain-separated canonical candidate
digest. It already commits:

- exact retained evidence identity and evidence bytes;
- derived subject;
- exact capability concept revision;
- proposed claim statement;
- claim scope;
- proposer identity/kind;
- proposal time;
- proposal rationale;
- frozen PR12.2 proposal policy.

Therefore a review cannot silently move to a modified proposal.

```text
review(candidate A)
+
mutate candidate claim scope / concept / proposer / rationale / time / evidence binding
->
review validation rejects
```

PR12.3 additionally checks `review.proposal_id == candidate.proposal_id` so the
human-facing proposal identity and exact canonical bytes must both agree.

## Candidate must remain valid

PR12.3 does not treat a previously hashed candidate as permanently valid.

Review construction, review validation, ledger admission, and terminal-review
resolution replay the PR12.2 candidate validator against the supplied:

```text
EpistemicRecordSet
CapabilityCatalog
```

This means terminal review use fails if, for example:

- selected evidence bytes no longer match the candidate;
- subject is rebound;
- selected evidence loses the PR12.1 external-evidence shape;
- catalog no longer contains the exact concept revision;
- any other PR12.2 invariant fails.

As in PR12.2, no whole-epistemic-snapshot digest is bound. Adding unrelated
later evidence does not stale an exact review, while mutation/replacement of the
selected `EvidenceRecord` does.

## Human reviewer boundary

PR12.3 v1 supports one reviewer kind:

```text
HUMAN
```

`MODEL`, `RULE`, `SERVICE`, or other reviewer kinds are not representable.

The reviewer ref is declared provenance only:

```text
DECLARED HUMAN REVIEWER != AUTHENTICATED HUMAN IDENTITY
REVIEW != SIGNATURE / PKI
REVIEWED_AT != TRUSTED TIME
```

Identity authentication can be added by a higher deployment layer without
changing the semantic meaning of PR12.3.

## Time

```text
review.reviewed_at >= candidate.proposed_at
```

PR12.2 already requires:

```text
candidate.proposed_at >= EvidenceRecord.recorded_at
```

so the full temporal ordering remains:

```text
EvidenceRecord.recorded_at
<= candidate.proposed_at
<= review.reviewed_at
```

## Deterministic review digest

The review digest is domain-separated by:

```text
capability_lab/external_evidence_claim_interpretation_review@1\0
```

and commits canonical schema-v1 review JSON containing:

- review id;
- frozen PR12.3 review policy;
- proposal id;
- exact PR12.2 candidate digest;
- declared human reviewer;
- verdict;
- review time;
- rationale.

Changing any of those fields changes the digest.

## Strict serialization

Both review artifacts and review ledgers use strict schema v1 serialization.
The schemas reject:

- unknown fields;
- missing fields;
- duplicate JSON object keys;
- duplicate review ids in a ledger;
- multiple terminal reviews for one proposal in one ledger;
- invalid policy refs;
- unsupported reviewer/verdict enum values;
- malformed timestamps;
- non-finite JSON constants;
- values that fail strict semantic reconstruction.

Canonical JSON uses sorted keys and compact separators.

## No accepted-claim object

PR12.3 deliberately does **not** introduce an `AcceptedCapabilityClaim`,
`AcceptedInterpretation`, or similar truth-bearing object.

Doing so here would risk collapsing:

```text
human acceptance of proposal scope
```

into:

```text
acceptance of claim truth
```

Those are different authorities.

The terminal PR12.3 artifact for downstream use is therefore:

```text
exact valid candidate
+
exact terminal review resolved from one valid review-ledger lineage
```

not a new claim/evaluation/state object.

## Position in the governed loop

After PR12.3:

```text
external / HDE activity
        |
        v
PR12.0 admitted observation
        |
        v
PR12.1 human-reviewed neutral evidence
        |
        v
PR11.3 immutable epistemic retention
        |
        v
PR12.2 evidence -> claim interpretation proposal
        |
        v
PR12.3 declared HUMAN review artifact
        |
        v
append-only one-terminal-review ledger admission
        |
   ACCEPT | REJECT
        |
        X no EvidenceBearing yet
        X no reliability judgment yet
        X no ClaimEvaluation yet
        X no state update yet
```

The intended next boundary is PR12.4: a generic governed evaluation/admission
step that requires the exact candidate and the exact admitted terminal
`ACCEPT` review resolved through PR12.3, rather than trusting a raw proposal or
raw review object.
