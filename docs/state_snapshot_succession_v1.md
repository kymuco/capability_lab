# Personal Capability State Snapshot Succession v1

Status: **PR11.6 normative governance contract**

PR11.6 closes the persistence and identity gap that remains after PR11.5.

PR11.5 can deterministically produce a governed `PersonalCapabilityState` from the exact
complete PR11.4 portfolio, but neither PR3 nor PR4 maintains a cross-snapshot state-id registry.
A later process can therefore construct a structurally valid state that reuses an old
`PersonalCapabilityStateId` for different material content unless persistence governance rejects
it.

PR11.6 introduces that missing boundary.

```text
PR11.5 GOVERNED DERIVATION
        ↓
PersonalCapabilityState
        ↓
PR11.6 IMMUTABLE STATE SNAPSHOT SUCCESSION
        ↓
APPEND-ONLY STATE HISTORY
```

## Core invariant

```text
PERSISTED STATE IDENTITY
=
PERMANENT BINDING TO CANONICAL STATE CONTENT
```

For every state identity already present in a predecessor snapshot:

```text
same PersonalCapabilityStateId
+
same exact typed PersonalCapabilityState content
=> RETAINED / PASS
```

but:

```text
same PersonalCapabilityStateId
+
different material state content
=> REJECT
```

A material recomputation therefore requires a fresh state identity.

```text
RECOMPUTATION != MUTATION

MATERIAL STATE CHANGE
=> NEW PersonalCapabilityStateId
```

The previous state remains immutable historical content.

## Succession invariant

For one exact subject-scoped state history:

```text
VALID SUCCESSOR
=
ALL PREDECESSOR STATES RETAINED EXACTLY
+
OPTIONAL NEW STATE IDS
```

Equivalently:

```text
RETENTION + APPEND
```

The following transitions are valid:

```text
A -> A
A -> A + B
A + B -> A + B + C
empty(subject X) -> A(subject X)
```

The following transitions are invalid:

```text
A -> B
A + B -> B
A(content X) -> A(content Y)
subject X snapshot -> subject Y snapshot
```

A replacement under a fresh id does not authorize deletion of the old record:

```text
A -> B
```

is still a removal of `A`, even if `B` is a legitimate recomputation.

The correct transition is:

```text
A -> A + B
```

## Relationship to PR3

PR3 defines `PersonalCapabilityState` as an immutable derived state representation and
`PersonalCapabilityStateSet` as a one-subject collection. It enforces state-id uniqueness inside
one constructed set, but it intentionally does not maintain a cross-snapshot persistent identity
registry.

PR11.6 does not alter PR3 representation semantics or schemas. It adds a transition validator
around existing typed state snapshots.

```text
PR3  = STATE REPRESENTATION
PR4  = STATELESS DETERMINISTIC DERIVATION
PR11.5 = GOVERNED COMPLETE-PORTFOLIO HANDOFF
PR11.6 = CROSS-SNAPSHOT STATE PERSISTENCE GOVERNANCE
```

No state schema v2 is introduced.

## Material state content

For a retained `PersonalCapabilityStateId`, the whole typed `PersonalCapabilityState` value is
immutable.

This includes:

```text
subject_ref
concept_ref
frame_ref
derivation_policy_ref
deriver_ref
as_of
derived_at
dimensions
rationale
```

and, recursively, each dimension's:

```text
dimension_key
standing
conflict_status
supported_claim_ids
basis_evaluation_ids
rationale
```

PR11.6 does not maintain a hand-authored list of mutable versus immutable state fields. It
compares the complete normalized typed state record for equality.

Before any identity map, set, ordering, retained-state equality, snapshot hash, or canonical
serialization can establish persistence authority, PR11.6 also requires the entire persisted
state value graph to use exact concrete core types. This includes exact semantic refs and IDs,
frame/policy/deriver refs, state and dimension enums, timestamps, claim/evaluation IDs, tuples,
and primitive fields.

```text
PYTHON BEHAVIORAL SUBCLASS
!= PERSISTED CORE VALUE

POST-CONSTRUCTION TAMPERING
!= TYPE AUTHORITY
```

An unrelated object whose direct base is `object` is not sufficient. Every nested value is checked
against the specific concrete class required at that exact graph location. `StateDeriverKind`,
`DimensionStanding`, and `DimensionConflictStatus` are exact-type checked before equality or
serialization.

That means even a state recomputation that preserves the same outward standing but changes basis
is a material change:

```text
state_A
standing = SUPPORTED
basis = [eval_1]

state_A
standing = SUPPORTED
basis = [eval_1, eval_2]

=> REJECT
```

The legal representation is:

```text
state_A
standing = SUPPORTED
basis = [eval_1]

state_B
standing = SUPPORTED
basis = [eval_1, eval_2]

=> APPEND state_B, RETAIN state_A
```

## Subject scope

`PersonalCapabilityStateSet` is explicitly one-subject.

PR11.6 therefore requires:

```text
predecessor.subject_ref
=
successor.subject_ref
```

A snapshot for another subject is not a successor of the first snapshot, even if both snapshots
are empty.

This means there is intentionally no subject-free universal empty state snapshot.

```text
EMPTY STATE HISTORY
STILL HAS SUBJECT IDENTITY
```

## Canonical state snapshot hash

PR11.6 exposes:

```python
personal_capability_state_set_sha256_v1(snapshot)
```

The digest is:

```text
SHA256(
    b"capability_lab/personal_capability_state_set@1\x00"
    ||
    snapshot.to_json().encode("utf-8")
)
```

`PersonalCapabilityStateSet.to_json()` already uses the PR3 strict deterministic canonical
serialization contract:

```text
personal_capability_states/v1
```

No second state serialization format is introduced.

The hash is domain-separated from all epistemic and future acceptance hashes.

```text
STATE SNAPSHOT HASH
!= EPISTEMIC SNAPSHOT HASH
!= ACCEPTANCE HASH
```

The digest is useful for exact snapshot binding and receipts. It is not semantic authority.

```text
HASH MATCH
!= STATE ACCEPTANCE
!= CURRENT STATE
!= TRUTH
```

## API

New public symbols under `capability_lab.state`:

```text
StateSnapshotTransitionError
InvalidPersonalCapabilityStateSetSuccessor
PersonalCapabilityStateSetSuccessionReceipt
personal_capability_state_set_sha256_v1
validate_personal_capability_state_set_successor_v1
```

The validator is:

```python
validate_personal_capability_state_set_successor_v1(
    *,
    predecessor: PersonalCapabilityStateSet,
    successor: PersonalCapabilityStateSet,
) -> PersonalCapabilityStateSetSuccessionReceipt
```

## Succession receipt

The receipt contains only structural transition facts:

```text
predecessor_sha256
successor_sha256
subject_ref
retained_state_ids
added_state_ids
```

It contains no:

```text
accepted_state_id
current_state_id
preferred_state_id
selected_state_ids
superseded_state_ids
progression_state_ids
acceptance_policy_ref
accepter_ref
score
weight
confidence
```

The receipt is an ordinary structural value object. It contains no validator-origin marker,
private capability subtype, signature, or boolean authority surface. Constructing an equal-looking
receipt therefore proves nothing about whether the transition was actually validated.

```text
STRUCTURAL RECEIPT
!= VALIDATED TRANSITION PROVENANCE
!= STATE AUTHORITY
```

A future governance layer that consumes state succession must re-run the PR11.6 validator on the
exact predecessor and successor snapshots, or introduce its own independently hardened provenance
contract. It must not treat possession of a receipt object as authorization.

## Transition algorithm

The v1 transition is intentionally small.

1. Require exact `PersonalCapabilityStateSet` predecessor type.
2. Require exact `PersonalCapabilityStateSet` successor type.
3. Require exact `CapabilitySubjectRef` and subject continuity.
4. Require every snapshot entry to be exact `PersonalCapabilityState`, not a subclass.
5. Recursively require the expected exact concrete class for every persisted nested value,
   including refs, IDs, timestamps, dimensions, enum values, tuples, and primitives.
6. Only after exact graph validation, index predecessor and successor states by typed
   `PersonalCapabilityStateId`.
7. Reject every predecessor id missing from successor.
8. For every retained id, require full typed state equality.
9. Classify successor-only ids as additions.
10. Return domain-separated predecessor/successor hashes and canonical sorted id tuples.

The validator does not mutate either snapshot.

## Historical reconstruction and backfill

State append order does not define the time represented by a state.

A state can be reconstructed later for an earlier `as_of` boundary:

```text
state_A
as_of      = 2026-08-20
produced first

state_B
as_of      = 2020-01-01
derived_at = 2026-08-21
appended later
```

PR11.6 permits:

```text
{state_A}
->
{state_A, state_B}
```

provided `state_B` uses a fresh id and `state_A` remains exact.

```text
APPEND ORDER
!= AS_OF ORDER
!= DERIVED_AT ORDER
```

PR11.6 has no trusted persistence clock and does not invent latest-wins semantics.

## Canonical normalization

The state layer already canonicalizes typed content before PR11.6 compares it.

Examples include:

```text
state ordering in PersonalCapabilityStateSet
dimension ordering in PersonalCapabilityState
UTC normalization of timezone-aware state timestamps
canonical refs and typed ids
```

Therefore semantically identical typed records constructed in different input order compare
equal and hash identically after normalization.

PR11.6 compares typed normalized records, not raw source JSON bytes supplied by callers.

## What PR11.6 deliberately does not revalidate

PR11.6 does **not** require that every newly appended state was produced by PR11.5.

This is deliberate.

The state layer already permits structurally valid states derived by human, rule, model, hybrid,
or external systems. Persistence governance owns identity immutability, not derivation
authorization.

```text
STATE SUCCESSION PASS
!= GOVERNED DERIVATION PASS
```

Likewise PR11.6 does not call:

```text
validate_against_epistemics(...)
validate_against_capability_catalog(...)
validate_against_frame_catalog(...)
```

Those are explicit cross-layer validation operations with supplied external snapshots. PR11.6
does not silently import current epistemic or semantic catalogs and turn persistence into a
derivation verifier.

A structurally valid state may therefore enter an append-only state history under a fresh id
without PR11.6 claiming that the state is accepted or suitable for downstream use.

That remaining authority gap is intentional and belongs to PR11.7.

## No acceptance semantics

The central negative invariant is:

```text
VALID STATE RECORD
!= GOVERNANCE ACCEPTANCE
```

PR11.6 preserves it.

A persisted state is merely an immutable historical record in the state snapshot.

PR11.6 does not decide:

```text
which state is accepted
which state is current
which state is preferred
which state supersedes another
which state progression may use
which state Player Window may show
```

Even a newly appended state with a later `as_of` or `derived_at` is not automatically current.

```text
NEWER != CURRENT
LAST APPENDED != AUTHORITATIVE
LATEST derived_at != PREFERRED
```

## No supersession semantics

Old states are never marked obsolete by PR11.6.

A newer state can differ from an older state, including by:

```text
concept revision
frame revision
derivation policy
basis evaluations
standing
conflict status
as_of
```

as long as it receives a fresh state id and old history remains retained.

The coexistence of two states does not imply which one supersedes the other.

```text
COEXISTENCE != SUPERSESSION
```

Explicit state acceptance/current-selection governance is deferred.

## Real Pilot 01 integration

PR11.6 extends the real governance chain already exercised by PR11.5:

```text
real PR10.1 reviewed dependence
        ↓
real PR11.2 ClaimEvaluation
        ↓
PR11.3 immutable epistemic succession
        ↓
PR11.4 complete portfolio
        ↓
PR11.5 governed deterministic state
        ↓
PR11.6 immutable state succession
```

The integration proves five things.

### Initial state persistence

A real PR11.5-derived state can be appended to an empty subject-scoped state history under a
fresh `PersonalCapabilityStateId`.

### Correction creates new state identity

A correction appended under a new `ClaimEvaluationId` passes PR11.3, expands the rebuilt PR11.4
portfolio, reaches PR11.5, and produces a recomputed state under a **new** state id.

PR11.6 then accepts:

```text
{state_A}
->
{state_A, state_B}
```

### Same-id overwrite is rejected

If the recomputed state_B content is relabeled with `state_A.state_id`, PR11.6 rejects the
transition.

```text
state_A id + state_B content
=> REJECT
```

### Fresh id does not authorize deletion

If state_B has a legitimate fresh id but the successor drops state_A:

```text
{state_A}
->
{state_B}
```

PR11.6 rejects the transition.

### Historical reconstruction is appendable

A later-created state representing an earlier `as_of` boundary can be appended under a fresh
state id even when its `derived_at` is later than the already-persisted state.

This proves that persistence append order does not create accidental temporal preference
semantics.

## Authority localization

New production authority is localized to:

```text
src/capability_lab/state/snapshot_transition.py
```

Its exact imports are intentionally limited to the concrete types required to validate the
persisted state graph:

```text
__future__.annotations
dataclasses.dataclass
datetime.datetime
hashlib

capability_lab.epistemics:
    CapabilityClaimId
    CapabilitySubjectRef
    ClaimEvaluationId

capability_lab.semantics:
    CapabilityConceptRef
    CapabilityId

.state.core:
    CompetenceDimensionState
    CompetenceFrameId
    CompetenceFrameRef
    DimensionConflictStatus
    DimensionStanding
    PersonalCapabilityState
    PersonalCapabilityStateId
    PersonalCapabilityStateSet
    StateDerivationPolicyRef
    StateDeriverKind
    StateDeriverRef
    StateError
```

These imports provide **type identity only**. PR11.6 still imports no semantic catalogs,
epistemic record sets, evaluation portfolios, derivation engines, or downstream authority layers.

It imports no:

```text
derivation
epistemic record-set governance
evaluation portfolios
history
progression
proposals
player_window
domains
pilots
model runtime
LLM runtime
```

The import surface is frozen by an exact AST regression test.

## Release scope

PR11.6 remains a six-file change:

```text
docs/state_snapshot_succession_v1.md
src/capability_lab/state/__init__.py
src/capability_lab/state/snapshot_transition.py
tests/state/test_state_snapshot_transition_v1.py
tests/state/test_state_snapshot_transition_adversarial_v1.py
tests/pilots/test_civilization_bootstrap_pilot_01_state_snapshot_succession_integration_v1.py
```

Not modified:

```text
src/capability_lab/state/core.py
src/capability_lab/state/serialization.py
src/capability_lab/derivation/*
src/capability_lab/epistemics/*
src/capability_lab/history/*
src/capability_lab/progression/*
src/capability_lab/proposals/*
src/capability_lab/player_window/*
Pilot production
```

## Explicit non-goals

```text
PR11.6 != STATE DERIVATION
PR11.6 != DERIVATION PROVENANCE PROOF
PR11.6 != STATE ACCEPTANCE
PR11.6 != CURRENT STATE SELECTION
PR11.6 != PREFERRED STATE SELECTION
PR11.6 != STATE SUPERSESSION
PR11.6 != LATEST-WINS
PR11.6 != STATE TRUTH
PR11.6 != MASTERY
PR11.6 != PROGRESSION AUTHORITY
PR11.6 != PlayerWindow AUTHORITY
PR11.6 != ACHIEVEMENT QUALIFICATION
PR11.6 != SHARING / COMMONS PUBLICATION
PR11.6 != DATABASE IMPLEMENTATION
PR11.6 != STATE SCHEMA V2
```

## Release boundary

A PR11.6 succession PASS means only:

```text
1. predecessor and successor are exact one-subject state sets;
2. the subject identity did not change;
3. every persisted nested value used its exact expected concrete core type before authority-bearing operations;
4. every predecessor state id remains present;
5. every retained state id still denotes exactly equal typed state content;
6. successor-only state ids are append-only additions;
7. predecessor and successor are bound to deterministic state-snapshot hashes.
```

It does not mean that any state is accepted, current, preferred, true, mastered, or authorized
for progression.

```text
PR11.6 PASS
=
IMMUTABLE STATE-HISTORY SUCCESSION ONLY
```

The next governance layer can safely build acceptance semantics on top of stable state
identities because PR11.6 establishes the prerequisite:

```text
ONE PERSISTED PersonalCapabilityStateId
=
ONE PERMANENT PersonalCapabilityState CONTENT
```
