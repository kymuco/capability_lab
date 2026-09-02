# Epistemic Snapshot Succession, Identity-to-Content Immutability and Append-Only Persistence Governance v1

Status: **PR11.3 implementation contract**

Base:

```text
main @ 3f38e546b1a1d39680d088d31b3f3c4f2928c826
```

PR11.3 introduces the first explicit transition contract between two
`EpistemicRecordSet` snapshots. It does not create a database, transaction log,
trusted timestamp, evaluation supersession policy, state selection policy, or
state derivation authority.

## Core boundary

```text
valid EpistemicRecordSet predecessor
        +
valid EpistemicRecordSet successor
        ↓
append-only identity/content succession validation
        ↓
EpistemicSnapshotSuccessionReceipt
```

The central rule is:

```text
PERSISTED IDENTITY
=
PERMANENT BINDING TO CANONICAL CONTENT
```

The rule is enforced independently for:

```text
EvidenceId
CapabilityClaimId
ClaimEvaluationId
```

For every identity present in the predecessor:

```text
same typed id + same canonical typed record -> PASS
same typed id + changed canonical typed record -> REJECT
missing predecessor id in successor -> REJECT
```

New valid records under new typed identities may be appended.

## Canonical content, not original JSON bytes

PR11.3 does not compare incidental source JSON formatting. Existing PR2 typed
records already normalize ordering, UTC datetimes, NFC text, and other canonical
fields. Existing strict serialization remains the only snapshot serializer:

```text
capability_epistemics/v1
```

The snapshot fingerprint is computed from:

```text
record_set_to_json(snapshot)
```

using the existing deterministic JSON representation.

Therefore:

```text
different JSON whitespace only -> same canonical snapshot
different object key order only -> same canonical snapshot
timezone-equivalent datetimes after typed normalization -> same canonical record
NFC-equivalent text after typed normalization -> same canonical record
```

PR11.3 protects canonical semantic content rather than the incidental bytes used
to submit that content.

## Snapshot fingerprint

PR11.3 defines one portable deterministic snapshot fingerprint:

```text
SHA256(
    b"capability_lab/epistemic_snapshot@1\x00"
    ||
    canonical_epistemic_json_utf8
)
```

The public result is exactly 64 lowercase hexadecimal characters.

Frozen empty-snapshot vector:

```text
canonical JSON:
{"claims":[],"evaluations":[],"evidence_records":[],"schema":"capability_epistemics/v1"}

sha256:
b775413096e9acc7f7d5514e904e44cafff4c29aa9af542bdeba3df3244c3a40
```

The hash is integrity evidence and a receipt token. It is **not** the logical
authority for identity/content equality. Retained records are compared as typed
canonical records. Correctness therefore does not depend on treating SHA-256
collision resistance as a semantic equality axiom.

## Public API

PR11.3 adds:

```python
epistemic_snapshot_sha256_v1(
    snapshot: EpistemicRecordSet,
) -> str
```

and:

```python
validate_epistemic_snapshot_successor_v1(
    *,
    predecessor: EpistemicRecordSet,
    successor: EpistemicRecordSet,
) -> EpistemicSnapshotSuccessionReceipt
```

The receipt contains only exact predecessor/successor fingerprints and sorted
typed identity sets:

```text
predecessor_sha256
successor_sha256

retained_evidence_ids
added_evidence_ids

retained_claim_ids
added_claim_ids

retained_evaluation_ids
added_evaluation_ids
```

It contains no state, score, confidence, selection, supersession, preferred
evaluation, or winning conclusion field.

`EpistemicSnapshotSuccessionReceipt` remains a structural dataclass, but a receipt
returned by `validate_epistemic_snapshot_successor_v1(...)` is explicitly marked
as validator-issued through `receipt.validator_issued == True`. Directly
constructed structural instances have `validator_issued == False` and therefore
must not be treated as evidence that the succession gate actually ran. This is a
provenance-of-validation guard, not authentication, signature, trusted
persistence, or protection against hostile Python runtime introspection.

```text
RECEIPT SHAPE != PROOF THAT THE VALIDATOR RAN
VALIDATOR-ISSUED RECEIPT -> validator_issued == True
```

## Append-only succession

PR11.3 allows:

```text
snapshot A -> identical snapshot A
snapshot A -> A + new EvidenceRecord
snapshot A -> A + new CapabilityClaim
snapshot A -> A + new ClaimEvaluation
snapshot A -> A + several mutually valid new records
```

No-op succession is intentionally valid to support idempotent persistence
verification and replay-safe validation.

PR11.3 rejects:

```text
delete retained record
replace retained record
reuse retained id with changed content
delete old record while adding replacement identity
```

Append permission never grants delete permission.

## Correction semantics

Corrections use new identities.

Invalid:

```text
eval_001 = SUPPORTED

later:
eval_001 = CONTRADICTED
```

Valid append-only history:

```text
eval_001 = SUPPORTED
eval_002 = CONTRADICTED
```

PR11.3 does not state that `eval_002` supersedes, wins over, invalidates, or
should be preferred to `eval_001`.

```text
NEWER EVALUATION != TRUER EVALUATION
APPENDED EVALUATION != SUPERSEDING EVALUATION
```

Evaluation portfolio admissibility and anti-cherry-picking are deferred to a
later boundary.

## Typed identity namespaces

PR11.3 preserves the existing PR2 typed identity model. String equality across
different ID classes does not create a new global collision rule.

For example:

```text
EvidenceId("x")
CapabilityClaimId("x")
```

remain distinct typed identities.

PR11.3 does not expand the PR2 ontology into one global cross-record ID
namespace.

## Historical backfill

PR11.3 has no trusted transition timestamp. Therefore a newly appended valid
record may describe historical observations or evaluations.

```text
snapshot succession time
!= event time
!= recorded_at
!= evaluated_at
```

The transition validator does not require timestamps on newly appended records
to be later than all predecessor timestamps. Existing typed-record and
pilot-specific chronology rules remain responsible for chronology within their
own authority boundaries.

A retained record's timestamp fields remain identity-bound and cannot be
silently rewritten.

## Relationship to PR11.2

PR11.2 creates governed multi-evidence `ClaimEvaluation` records after exact
reviewed dependence preconditions and explicit human decisions.

PR11.3 consumes those existing PR2 records without reopening PR11.2 semantics:

```text
PR11.2 ClaimEvaluation
        ↓
PR11.3 immutable snapshot succession
```

The PR11.2 production evaluator, evaluation policy, materialization path, and
terminal dependence path are unchanged.

A real Pilot 01 integration test must prove that a real PR11.2 multi-evidence
evaluation can be appended, retained idempotently, and rejected if the same
`ClaimEvaluationId` or terminal-basis `EvidenceId` later acquires changed
canonical content.

## Authority localization

The new generic production authority is isolated to:

```text
capability_lab.epistemics.snapshot_transition
```

It may depend only on PR2 epistemic records, the immutable record set, existing
serialization, and Python standard library hashing/dataclass machinery.

It imports no:

```text
capability_lab.derivation
capability_lab.state
capability_lab.history
capability_lab.progression
capability_lab.proposals
capability_lab.player_window
capability_lab.domains
capability_lab.pilots
```

Pilot 01 production modules must not import the new snapshot succession API.
Pilot 01 remains only an integration-test consumer.

The PR11.3 API is exported from:

```text
capability_lab.epistemics
```

but deliberately not added to the package-root `capability_lab` public surface
in this PR.

## Explicit non-goals

```text
PR11.3 != DATABASE
PR11.3 != FILE STORE
PR11.3 != TRANSACTION LOG
PR11.3 != TRUSTED TIMESTAMP
PR11.3 != AUTHENTICATION
PR11.3 != SIGNATURE
PR11.3 != MERKLE TREE
PR11.3 != DISTRIBUTED CONSENSUS

PR11.3 != EVALUATION SUPERSESSION
PR11.3 != LATEST-WINS
PR11.3 != MAJORITY VOTE
PR11.3 != EVALUATOR WEIGHTING
PR11.3 != RECENCY WEIGHTING
PR11.3 != EVALUATION PORTFOLIO SELECTION

PR11.3 != PersonalCapabilityState
PR11.3 != DERIVATION
PR11.3 != PROGRESSION
PR11.3 != PlayerWindow
```

A succession PASS means only:

```text
the supplied successor is a valid append-only canonical-content successor
of the supplied predecessor
```

It does not imply:

```text
truth
claim support
evaluation quality
trusted evaluator identity
supersession
state selection
state authority
```

## Intended diff

PR11.3 is intentionally limited to exactly six files:

```text
src/capability_lab/epistemics/snapshot_transition.py
src/capability_lab/epistemics/__init__.py
tests/epistemics/test_snapshot_transition_v1.py
tests/pilots/test_civilization_bootstrap_pilot_01_snapshot_succession_integration_v1.py
tests/pilots/test_civilization_bootstrap_pilot_01_authority_boundary_v1.py
docs/epistemics/epistemic_snapshot_succession_v1.md
```

No PR11.2 production evaluator file, state/derivation module, history module,
progression module, or PlayerWindow module is part of the intended diff.

## Release success criterion

After PR11.3, Capability Lab may state:

```text
Given predecessor EpistemicRecordSet A
and candidate successor EpistemicRecordSet B,

PR11.3 deterministically establishes that:

- no persisted EvidenceRecord disappeared;
- no persisted CapabilityClaim disappeared;
- no persisted ClaimEvaluation disappeared;
- no persisted typed identity acquired different canonical content;
- additional epistemic knowledge was appended under new typed identities;
- both exact canonical snapshots have stable domain-separated SHA-256 fingerprints.
```

Knowledge evolves by append-only epistemic history, not by silently rewriting
the meaning of an already persisted identity.
