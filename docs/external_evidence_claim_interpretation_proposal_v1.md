# PR12.2 — Governed External Evidence → Claim Interpretation Proposal v1

## Purpose

PR12.2 introduces the first generic interpretation boundary after PR12.1.

It allows one exact external `EvidenceRecord` already retained in an
`EpistemicRecordSet` to be proposed as relevant to one exact
`CapabilityConceptRef` and one bounded claim statement/scope.

It does **not** create a `CapabilityClaim` and does not decide what the evidence
means for that claim.

```text
PR12.1 neutral external EvidenceRecord
        |
        v
PR11.3 retained epistemic snapshot
        |
        v
PR12.2 interpretation proposal
        |
        X no CapabilityClaim
        X no EvidenceAssessment
        X no ClaimEvaluation
        X no state
        X no progression authority
```

The central invariant is:

```text
EXTERNAL EVIDENCE INTERPRETATION PROPOSAL
=
ONE EXACT RETAINED EvidenceRecord
+
ONE EXACT CapabilityConceptRef
+
ONE PROPOSED claim statement/scope
+
ONE DECLARED proposer
+
ONE FROZEN PR12.2 POLICY
```

## Authority boundary

```text
PROPOSAL != CLAIM TRUTH
PROPOSAL != EvidenceBearing.SUPPORTS
PROPOSAL != EvidenceReliability
PROPOSAL != EVALUATION
PROPOSAL != CAPABILITY
PROPOSAL != STATE
PROPOSAL != READINESS
PROPOSAL != MASTERY
PROPOSAL != PERMISSION
```

PR12.2 deliberately exposes no fields for `EvidenceBearing`,
`EvidenceReliability`, evaluation conclusion, coverage/conflict status,
claim id, state id, score, mastery, readiness, or permission.

PR12.3 is reserved for an explicit future review/acceptance boundary.

## Exact retained-evidence binding

The caller supplies an immutable `EpistemicRecordSet` and an exact `EvidenceId`.

The proposal function finds the selected record inside that snapshot and derives:

```text
subject_ref
evidence_id
evidence_sha256
```

The subject is therefore not caller-selectable.

`evidence_sha256` reuses the existing PR12.1 canonical
`external_observation_materialized_evidence_sha256_v1` digest. A later record
with the same `EvidenceId` but different bytes cannot satisfy verification.

The proposal does **not** bind the hash of the complete epistemic snapshot.

```text
candidate for evidence A
+
unrelated later retained evidence B
->
candidate A remains valid

mutated/replaced evidence A
->
candidate A rejects
```

This mirrors the exact-item rather than global-container staleness discipline of
PR12.0 and PR12.1.

## PR12.1 external-evidence shape

PR12.2 accepts only a retained record that structurally preserves the frozen
PR12.1 external-observation materialization shape:

- `EvidenceId = external_observation:<sha256>`;
- exactly one `EXTERNAL_RECORD` provenance source equal to that exact identity;
- exact `external_observation` scope tag;
- `outcome = None`;
- exactly one `external_observation_materialize` provenance step;
- materialization mechanism equals the frozen PR12.1 policy;
- materialization step time equals `EvidenceRecord.recorded_at`.

This is a structural downstream admission check. It does not invent a new
signature/PKI claim and does not reinterpret the evidence.

## Exact concept revision

The caller supplies a `CapabilityCatalog` and exact `CapabilityConceptRef`.

PR12.2 requires the capability lineage to be present exactly at that revision.

```text
requested concept@1
+
catalog contains concept@2
->
REJECT
```

There is no silent latest-revision substitution.

## Proposed claim semantics

The proposal may contain:

```text
claim_statement
ClaimScope(description, tags)
```

These are proposed interpretation semantics only.

PR12.2 deliberately does not allocate a `CapabilityClaimId`. It therefore
cannot silently turn its proposed wording into an accepted person-scoped claim.

## Proposer provenance

PR12.2 v1 permits only two declared proposer kinds:

```text
HUMAN
MODEL
```

The proposer ref is descriptive provenance.

```text
DECLARED HUMAN != AUTHENTICATED HUMAN IDENTITY
DECLARED MODEL != TRUSTED MODEL OUTPUT
MODEL PROPOSAL != CLAIM AUTHORITY
```

## Time

```text
candidate.proposed_at >= selected EvidenceRecord.recorded_at
```

The proposal cannot predate the evidence it interprets.

## Deterministic digest

Candidate serialization is strict schema v1 and the candidate digest is
domain-separated by:

```text
capability_lab/external_evidence_claim_interpretation_candidate@1\0
```

The digest commits the exact:

- proposal id;
- frozen policy ref;
- evidence identity and digest;
- derived subject;
- exact concept revision;
- claim statement;
- claim scope;
- proposer;
- proposal time;
- rationale.

Changing any committed interpretation semantic changes the digest.

## Strict serialization

The schema requires exact fields and rejects:

- missing fields;
- unknown fields;
- duplicate JSON keys;
- non-finite JSON constants;
- malformed timestamps;
- invalid enum/type reconstruction.

Serialization is deterministic canonical JSON with sorted keys and compact
separators.

## Position in the governed loop

After PR12.2:

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
PR12.2 exact evidence -> claim interpretation proposal
        |
        X no accepted interpretation yet
        X no ClaimEvaluation yet
        X no state update yet
```

The next intended boundary is PR12.3: explicit review of an exact PR12.2
interpretation candidate.
