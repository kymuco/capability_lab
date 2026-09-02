# PR12.1 — Reviewed External Observation → Neutral Evidence v1

## Purpose

PR12.1 is the first governed transition from the generic PR12.0 external-observation layer into the existing PR2 epistemic layer.

```text
PR12.0 admitted ExternalObservationEnvelope
        |
        v
exact materialization candidate
        |
        v
explicit HUMAN review
        |
        +----------------------+
        |                      |
   MATERIALIZE         DO_NOT_MATERIALIZE
        |                      |
        v                      v
neutral EvidenceRecord         no EvidenceRecord
        |                      |
        +----------+-----------+
                   |
          resolver-issued
          terminal receipt
```

The central invariant is:

```text
MATERIALIZED EXTERNAL EVIDENCE
=
ONE EXACT ADMITTED PR12.0 OBSERVATION
+
ONE FROZEN NEUTRAL MAPPING
+
ONE EXACT HUMAN REVIEW
+
ONE RESOLVER-ISSUED TERMINAL RECEIPT
```

## Authority boundaries

```text
MATERIALIZE != CLAIM SUPPORT
MATERIALIZE != POSITIVE EVIDENCE
MATERIALIZE != SUCCESS
MATERIALIZE != CAPABILITY

DO_NOT_MATERIALIZE != FAILURE
DO_NOT_MATERIALIZE != CONTRADICTION
DO_NOT_MATERIALIZE != NEGATIVE EVIDENCE
DO_NOT_MATERIALIZE != PERMANENT TOMBSTONE
```

PR12.1 does not create CapabilityClaim, ClaimEvaluation, PersonalCapabilityState, progression authority, readiness, permission, mastery, or Player Window authority.

## No caller-selected evidence semantics

The public proposal API accepts only:

```text
ledger
observation_id
materialization_id
proposed_at
```

It does not accept:

```text
EvidenceId
EvidenceKind
EvidenceOutcome
summary
context
concept_ref
claim_id
score
mastery
readiness
permission
```

All evidence semantics are derived by the frozen PR12.1 mapping.

The public resolver accepts only:

```text
ledger
candidate
review
```

It has no caller-selected `resolved_at`. The exact reviewed decision is the terminal time authority for PR12.1 v1.

## Deterministic EvidenceId

One exact PR12.0 observation has one PR2 EvidenceId:

```text
external_observation:<external_observation_sha256_v1>
```

Therefore:

```text
SAME EXACT OBSERVATION
-> SAME EvidenceId
```

A caller may create a later review attempt, but cannot multiply one source observation into evidence-1/evidence-2/evidence-3 by choosing new IDs.

Once one resolved EvidenceRecord has been appended to an EpistemicRecordSet, existing PR11.3 append-only succession prevents replacing that retained ID with different record bytes.

## Idempotent exact-review resolution

Resolution of one exact candidate plus one exact review is deterministic.

```text
SAME ADMITTED OBSERVATION
+ SAME EXACT CANDIDATE
+ SAME EXACT REVIEW
-> SAME EvidenceRecord | None
+ SAME TERMINAL RECEIPT
```

`EvidenceRecord.recorded_at` and receipt `resolved_at` are both exactly `review.reviewed_at`. A runtime retry therefore cannot create different immutable evidence bytes merely because wall-clock time advanced.

A distinct later human review is a distinct governance act; if it produces different bytes for the same deterministic EvidenceId, unchanged PR11.3 append-only epistemic succession prevents replacement of an already retained record.

```text
RETRY != NEW RESOLUTION
CALLER CLOCK != RESOLUTION AUTHORITY
EXACT REVIEW -> DETERMINISTIC TERMINAL BYTES
```

## Exact source binding without global-ledger staleness

A candidate binds the exact observation digest plus its exact subject/source/source-event/form/origin metadata.

It deliberately does not bind the hash of the full continuously growing observation ledger.

```text
candidate for observation A
+
unrelated later observation B
-> candidate A remains valid
```

But mutation/rebinding of observation A rejects.

```text
UNRELATED LEDGER APPEND != STALE CANDIDATE
MUTATED SOURCE OBSERVATION -> REJECT
```

Resolution accepts a validated `ExternalObservationLedger`, not an arbitrary standalone observation. This prevents bypassing the PR12.0 admission boundary.

## Human review

PR12.1 v1 accepts one declared reviewer kind:

```text
HUMAN
```

The review binds:

```text
materialization_id
candidate_sha256
frozen policy_ref
reviewer_ref
verdict
reviewed_at
rationale
```

The candidate digest is domain-separated:

```text
capability_lab/external_observation_evidence_candidate@1\0
```

The review digest is domain-separated:

```text
capability_lab/external_observation_evidence_review@1\0
```

```text
DECLARED HUMAN REVIEWER != AUTHENTICATED HUMAN IDENTITY
```

PR12.1 does not claim identity authentication or trusted timestamps.

## Frozen neutral EvidenceKind mapping

```text
ARTIFACT      -> EvidenceKind.ARTIFACT
CONVERSATION  -> EvidenceKind.CONVERSATION_OBSERVATION
TEXT          -> EvidenceKind.OTHER
EVENT         -> EvidenceKind.OTHER
BUNDLE        -> EvidenceKind.OTHER
OTHER         -> EvidenceKind.OTHER
```

No source event is upgraded to PROJECT, REAL_WORLD_DEMONSTRATION, REPEATED_PERFORMANCE, SUPERVISED_EXERCISE, or SELF_REPORT by this boundary.

```text
ARTIFACT FORM != PROJECT EVIDENCE
EVENT EXISTS != REAL_WORLD_DEMONSTRATION
TEXT EXISTS != SELF_REPORT
BUNDLE EXISTS != PROJECT
```

## Outcome is always absent

Every PR12.1 materialized record has:

```text
EvidenceRecord.outcome = None
```

Even source events named `success`, `completed`, `passed`, or similar do not grant PR12.1 authority to construct `EvidenceOutcome.SUCCESS`.

```text
SOURCE SAYS SUCCESS != EvidenceOutcome.SUCCESS
```

## Time mapping

The source observation times are preserved exactly:

```text
EvidenceRecord.observation_started_at
= observation.observation_started_at

EvidenceRecord.observed_at
= observation.observed_at

EvidenceRecord.recorded_at
= review.reviewed_at

terminal receipt.resolved_at
= review.reviewed_at
```

The temporal chain is:

```text
observation_started_at?
<= observed_at
<= captured_at
<= proposed_at
<= reviewed_at == resolved_at
```

The equality is intentional: PR12.1 v1 uses the exact reviewed decision as the deterministic terminal timestamp rather than accepting a retry-sensitive resolver clock.

## Context and assistance preservation

PR12.0 context factor kinds map mechanically 1:1 to the corresponding PR2 ContextFactorKind:

```text
tool
assistance
accommodation
collaboration
reference_material
automation
environment
other
```

This preserves AI/tool/automation/collaboration conditions without interpreting them.

The EvidenceContext uses only the neutral scope tag:

```text
external_observation
```

No capability/topic tags are inferred.

## Payload references and exact source provenance

EvidenceRecord payload refs are the source observation payload reference identifiers.

Exact payload hashes, media types, and sizes remain in the PR12.0 source observation. Evidence provenance points back to the exact source observation digest:

```text
ProvenanceSourceKind.EXTERNAL_RECORD
external_observation:<observation_sha256>
```

The materialization provenance step records the exact materialization id, candidate digest, review id, observation id, and observation digest.

```text
PAYLOAD REF != PAYLOAD CORRECTNESS
OBSERVATION DIGEST != AUTHORSHIP
PROVENANCE != CAPABILITY JUDGMENT
```

## Terminal receipts for both verdicts

Unlike the early Pilot materialization shape, PR12.1 issues a terminal receipt for both review outcomes.

For `MATERIALIZE`:

```text
evidence_id     = exact deterministic EvidenceId
evidence_sha256 = exact canonical EvidenceRecord digest
```

For `DO_NOT_MATERIALIZE`:

```text
evidence_id     = None
evidence_sha256 = None
```

The receipt binds:

```text
materialization_id
candidate_sha256
review_id
review_sha256
verdict
observation_sha256
optional evidence identity/digest
resolved_at = exact review.reviewed_at
```

The evidence digest domain is:

```text
capability_lab/external_observation_materialized_evidence_record@1\0
```

The receipt carries a private resolver-issued witness whose payload digest uses:

```text
capability_lab/external_observation_evidence_resolution_witness@1\0
```

Direct public receipt construction is not valid resolver issuance. Reusing a real witness with `dataclasses.replace(...)` for a different receipt payload fails validation.

```text
TERMINAL RECEIPT != SIGNATURE
TERMINAL RECEIPT != AUTHENTICATED REVIEWER
TERMINAL RECEIPT != TRUSTED TIME
TERMINAL RECEIPT != EVIDENCE
```

## Strict serialization

Candidate and human review artifacts support strict schema-v1 dict/JSON round trips with:

```text
exact fields
schema_version = 1
duplicate-key rejection
unknown/missing-field rejection
non-finite-number rejection
explicit timezone-aware timestamps
strict typed semantic reconstruction
```

Resolver receipts are not deserialized into authority. Their private issuance witness exists only through the resolver path.

## PR11.3 handoff

PR12.1 stops after producing:

```text
EvidenceRecord | None
+
terminal resolution receipt
```

It does not mutate the epistemic snapshot.

For `MATERIALIZE`, the next existing governance path is:

```text
predecessor EpistemicRecordSet
+
exact PR12.1 EvidenceRecord
        |
        v
successor EpistemicRecordSet
        |
        v
PR11.3 validate_epistemic_snapshot_successor_v1
```

PR11.3 remains responsible for append-only epistemic persistence.

## Closed-loop position

After PR12.1 the write/read chain becomes:

```text
external / future HDE work
        |
        v
PR12.0 observation admission
        |
        v
PR12.1 human-reviewed neutral evidence
        |
        v
PR11.3 immutable epistemic append
        |
        v
existing evaluation / state / acceptance / current chain
        |
        v
PR11.11 governed product read snapshot
```

But the following remains false:

```text
HDE OBSERVATION -> AUTOMATIC CAPABILITY UPDATE
```

Evidence still requires later governed claim evaluation before it can affect capability state.
