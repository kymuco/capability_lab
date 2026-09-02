# Governed Personal Capability State Acceptance v1

Status: **PR11.7 normative governance contract**

PR11.7 introduces the first explicit governance act over immutable person-scoped capability
states.

PR11.5 derives a state from a governed complete evaluation portfolio. PR11.6 preserves state
identity and exact state content across append-only state-history snapshots. Neither layer says
that a persisted state is accepted for later governance use.

PR11.7 closes exactly that gap.

```text
PR11.5 GOVERNED DERIVATION
        ↓
PR11.6 IMMUTABLE PERSISTED STATE HISTORY
        ↓
PR11.7 EXPLICIT GOVERNED STATE ACCEPTANCE
```

PR11.7 does not select a current state, prefer one accepted state over another, supersede old
states, or authorize progression.

## Primary invariant

```text
PERSISTED STATE
!= ACCEPTED STATE

EXPLICIT GOVERNANCE ACCEPTANCE
+
VALID PR11.6 PERSISTENCE BASIS
=
ACCEPTED STATE GOVERNANCE FACT
```

Acceptance always applies to one exact immutable `PersonalCapabilityState` record.

```text
ACCEPTANCE
=
EXPLICIT GOVERNANCE ACT
OVER
ONE EXACT IMMUTABLY PERSISTED STATE
```

It does not accept an abstract person, capability concept, standing, or loose proposition.

## Constitutional meaning

A PR11.7 acceptance means only:

> under the named acceptance policy, the named accepter explicitly accepts this exact persisted
> state record as a governed state record suitable for later governance layers to consider.

It does not mean:

```text
accepted state = canonical truth about a person
accepted state = capability itself
accepted state = mastery
accepted state = identity
accepted state = authority
accepted state = permission
accepted state = license
```

The acceptance record remains an assessment/governance fact with explicit provenance.

## Acceptance does not select

The central negative boundary is:

```text
ACCEPTED
!= CURRENT

ACCEPTED
!= PREFERRED

ACCEPTED
!= SUPERSEDED / NOT SUPERSEDED

ACCEPTED
!= PROGRESSION AUTHORITY
```

PR11.7 may produce acceptances for multiple states that coexist in one history.

```text
ACCEPT(A)
ACCEPT(B)
```

is valid and says nothing about which one should be used as the current state.

That selection belongs to PR11.8.

## Positive-only v1 semantics

PR11.7 intentionally models only explicit positive acceptance facts.

There is no acceptance verdict enum with `ACCEPT`, `REJECT`, `ABSTAIN`, or `REVOKE`.

```text
ABSENCE OF ACCEPTANCE
!= REJECTION
```

This avoids silently introducing unresolved policy questions such as:

```text
Does REJECT cancel an earlier ACCEPT?
Does a newer decision win?
Does one mechanism outrank another?
Does one policy revision supersede another?
How is revocation represented?
```

Those are separate governance-history questions and are outside PR11.7 v1.

## No acceptance identity registry

PR11.7 does not introduce a caller-chosen `StateAcceptanceId`.

The acceptance object is a complete immutable value record. Introducing an opaque acceptance id
would immediately require another cross-snapshot identity-to-content registry analogous to
PR11.6.

Exact duplicate acceptance values are therefore the same acceptance fact at the v1 value layer.
Different policy, accepter, time, rationale, state id, or persistence basis yields a different
acceptance value.

## Public value model

PR11.7 adds:

```text
StateAcceptanceMechanismKind
StateAcceptancePolicyRef
StateAccepterRef
PersonalCapabilityStateAcceptanceRequest
PersonalCapabilityStateAcceptance
```

### StateAcceptanceMechanismKind

```text
HUMAN
RULE
MODEL
HYBRID
EXTERNAL_SYSTEM
```

This is intentionally distinct from `StateDeriverKind`.

```text
DERIVER ROLE != ACCEPTER ROLE
```

The enum order does not encode priority or authority hierarchy.

### StateAcceptancePolicyRef

Canonical syntax:

```text
<namespace>:<key>@<revision>
```

Policy identity is explicit and versioned.

### StateAccepterRef

The accepter carries:

```text
kind
ref
```

The ref is an opaque canonical identifier. It is provenance, not an authenticated principal or
permission token.

```text
ACCEPTER REF
!= AUTHENTICATED PRINCIPAL
!= PERMISSION
```

Authentication/authorization of real actors remains an external runtime concern.

## Acceptance request

The request is:

```text
PersonalCapabilityStateAcceptanceRequest
    state_id
    acceptance_policy_ref
    accepter_ref
    accepted_at
    rationale
```

The request intentionally does not contain a caller-supplied `subject_ref`.

The subject is derived from the freshly validated persisted state history, preventing a request
from relabeling a state as belonging to another subject.

The request contains no:

```text
current_state_id
preferred_state_id
supersedes_state_id
progression_state_id
score
weight
confidence
```

## Acceptance record

The immutable output record is:

```text
PersonalCapabilityStateAcceptance
    subject_ref
    state_id
    accepted_state_sha256
    persistence_predecessor_sha256
    persistence_successor_sha256
    acceptance_policy_ref
    accepter_ref
    accepted_at
    rationale
```

The record separates two kinds of binding.

### Persistence-basis audit binding

```text
persistence_predecessor_sha256
persistence_successor_sha256
```

These identify the exact PR11.6 transition that was freshly validated when the acceptance was
issued.

### Durable state-content binding

```text
state_id
accepted_state_sha256
```

This binds acceptance to one exact state independently of unrelated later appends to the state
history.

## Why whole-snapshot hash is not enough

Suppose:

```text
S1 = {A}
ACCEPT(A)
```

Later a valid PR11.6 append occurs:

```text
S2 = {A, B}
```

The whole snapshot hash changes:

```text
hash(S1) != hash(S2)
```

but A has not changed.

Acceptance of A must therefore remain bound to A rather than becoming stale merely because B was
appended.

```text
WHOLE SNAPSHOT BINDING
=
AUDIT BASIS

PER-STATE CONTENT BINDING
=
DURABLE ACCEPTANCE BASIS
```

## Per-state content fingerprint

PR11.7 exposes:

```python
personal_capability_state_content_sha256_v1(
    *,
    snapshot: PersonalCapabilityStateSet,
    state_id: PersonalCapabilityStateId,
) -> str
```

The function first applies the hardened PR11.6 exact state-graph boundary to the supplied snapshot
and requires the state id to exist.

It then isolates the exact state into a one-state subject-scoped `PersonalCapabilityStateSet`,
strictly round-trips that state through PR3 serialization/parsing, and hashes canonical JSON with
the domain:

```text
capability_lab/personal_capability_state@1\x00
```

Conceptually:

```text
SHA256(
    b"capability_lab/personal_capability_state@1\x00"
    ||
    canonical_one_state_set_json
)
```

The state id is part of the serialized state and is therefore material to the digest.

The digest intentionally has the property:

```text
hash(A in {A})
=
hash(A in {A,B})
=
hash(A in {A,B,C})
```

provided PR11.6 guarantees that A remains exact.

## Strict semantic round-trip before acceptance

PR11.6 hardens exact type identity before persistence equality/hash authority. PR11.7 adds one
more acceptance-specific defense: the state being accepted must survive strict PR3 JSON
serialization and parsing exactly.

This detects post-construction tampering that still uses exact built-in/core classes but injects
invalid values such as:

```text
revision = 0
non-canonical dimension key
naive datetime
empty required rationale
other values rejected by PR3 constructors
```

The strict round-trip is local to the accepted state. It does not introduce epistemic, semantic
catalog, derivation-engine, progression, or Player Window authority.

```text
EXACT PYTHON TYPE
!= SUFFICIENT ACCEPTANCE SEMANTICS
```

## Issuing acceptance

The authority-bearing operation is:

```python
accept_persisted_personal_capability_state_v1(
    *,
    predecessor: PersonalCapabilityStateSet,
    successor: PersonalCapabilityStateSet,
    request: PersonalCapabilityStateAcceptanceRequest,
) -> PersonalCapabilityStateAcceptance
```

Algorithm:

1. Require an exact canonical acceptance request graph.
2. Re-run `validate_personal_capability_state_set_successor_v1(...)` on the supplied predecessor
   and successor.
3. Do not accept a caller-supplied PR11.6 receipt as proof.
4. Require the requested state id to exist in the validated successor.
5. Strictly round-trip the accepted state through PR3 serialization/parsing.
6. Require `accepted_at >= state.derived_at`.
7. Compute the durable per-state content fingerprint.
8. Bind the acceptance to the freshly returned PR11.6 predecessor/successor hashes.
9. Derive `subject_ref` from the persisted successor rather than from caller input.
10. Return the immutable acceptance record.

## PR11.6 receipt non-authority is preserved

The API intentionally does not accept:

```text
receipt=...
```

as input.

PR11.6 explicitly defines its receipt as a structural value rather than validator-origin
provenance. PR11.7 therefore re-runs the PR11.6 validator on exact snapshots.

```text
POSSESSION OF PR11.6 RECEIPT
!= ACCEPTANCE BASIS
```

## Retained states may be accepted

Acceptance is not restricted to newly appended state ids.

Given:

```text
predecessor = {A}
successor   = {A, B}
```

PR11.7 may explicitly accept either A or B.

This supports delayed review.

A no-op PR11.6 transition is also a valid persistence basis:

```text
{A} -> {A}
```

so an already persisted state can be explicitly accepted later.

```text
ACCEPTABLE STATE
=
ANY EXACT STATE PRESENT IN A VALID SUCCESSOR
```

not only a state in `added_state_ids`.

## Acceptance does not propagate

If A is accepted and a recomputation B is appended under a fresh id:

```text
ACCEPT(A)
+
{A} -> {A,B}
```

then:

```text
B IS NOT ACCEPTED
```

B requires its own explicit acceptance act.

```text
ACCEPTANCE DOES NOT FOLLOW RECOMPUTATION
```

This remains true even if A and B share concept, frame, policy, standing, or most of their basis.

## Temporal semantics

The only v1 acceptance-time ordering rule is:

```text
accepted_at >= state.derived_at
```

A state cannot be accepted before it exists as a derived record.

PR11.7 does not require:

```text
accepted_at == state.as_of
accepted_at == state.derived_at
```

Historical reconstruction remains valid:

```text
state.as_of      = 2020-01-01
state.derived_at = 2026-08-21T10:00Z
accepted_at      = 2026-08-21T11:00Z
```

Likewise:

```text
LATER accepted_at != MORE CURRENT
LATER as_of       != MORE PREFERRED
```

Current/preferred selection remains PR11.8.

## UNKNOWN and non-positive states may be accepted

Acceptance is not a positive-capability verdict.

A state containing:

```text
UNKNOWN
```

may be accepted when governance concludes that `UNKNOWN` is the honest supported assessment at
that boundary.

Likewise a state may contain:

```text
INSUFFICIENT
UNRESOLVED conflict
```

and still be explicitly accepted.

```text
ACCEPTED UNKNOWN
=
THE GOVERNANCE LAYER ACCEPTS UNKNOWN AS THE ASSESSMENT
```

not:

```text
THE GOVERNANCE LAYER ASSERTS THE CAPABILITY EXISTS
```

PR11.7 therefore performs no filter equivalent to:

```text
all dimensions must be SUPPORTED
```

## PR11.5 is a real basis, not a universal prerequisite

The Real Pilot accepts states produced through the full PR11.5 complete-portfolio handoff.

Production PR11.7 does not permanently require that every accepted state be produced by PR11.5.

The existing state model supports human, rule, model, hybrid, and external derivation mechanisms.
A future acceptance policy may require particular derivation provenance, but that policy-specific
rule is not a universal PR11.7 type invariant.

```text
PR11.5 DERIVATION
CAN BE ACCEPTANCE BASIS

PR11.5 DERIVATION
!= UNIVERSAL REQUIRED ACCEPTANCE BASIS
```

## Multiple acceptances

The same exact state may receive multiple acceptance facts under different:

```text
acceptance policies
accepters
accepted_at values
rationales
```

PR11.7 does not aggregate them into a score, vote, confidence, or priority.

```text
MULTIPLE ACCEPTANCES
!= CONSENSUS SCORE
!= HIGHER CONFIDENCE
!= CURRENT STATE
```

Similarly, A and B may both be accepted.

That is an input condition for later selection governance, not a conflict that PR11.7 resolves.

## Revalidation APIs

PR11.7 provides two distinct checks.

### Exact issuance-basis replay

```python
validate_personal_capability_state_acceptance_v1(
    *,
    predecessor,
    successor,
    acceptance,
)
```

This re-runs the exact PR11.6 transition, recomputes the state-content digest, and requires every
stored binding in the acceptance to match.

### Durable binding in a later snapshot

```python
validate_personal_capability_state_acceptance_binding_v1(
    *,
    snapshot,
    acceptance,
)
```

This verifies that the accepted state still exists with the exact accepted content in a later
append-only state snapshot.

It intentionally does not replay the original whole-snapshot issuance basis.

```text
DURABLE BINDING VALIDATION
!= REPLAY OF ACCEPTANCE ISSUANCE
```

This distinction allows acceptance A to remain usable after unrelated B/C appends while retaining
original predecessor/successor hashes for audit.

## Acceptance record provenance boundary

`PersonalCapabilityStateAcceptance` is a typed governance record, not a cryptographic signature.

The accepter ref identifies declared provenance. PR11.7 does not authenticate the human/model/rule
process represented by that ref.

A runtime requiring cryptographic or account-level authorization must enforce that separately.

```text
TYPED ACCEPTANCE RECORD
!= CRYPTOGRAPHIC PROOF OF ACTOR IDENTITY
```

This is consistent with other typed provenance records in Capability Lab.

## No current-state semantics

The acceptance record contains no:

```text
current_state_id
preferred_state_id
selected_state_ids
latest_state_id
superseded_state_ids
```

No acceptance algorithm sorts candidates by:

```text
accepted_at
as_of
derived_at
append order
state id
policy revision
accepter kind
```

to infer currentness.

## No supersession semantics

Acceptance A does not make earlier or later states obsolete.

Acceptance B does not supersede A unless a future explicit governance layer says so.

```text
ACCEPT(A) + ACCEPT(B)
!= B SUPERSEDES A
```

PR11.8 may select a current state under explicit rules without rewriting PR11.7 history.

## No progression or presentation authority

PR11.7 does not call progression or Player Window APIs and exposes no progression/presentation
selection field.

```text
PR11.7 PASS
!= PROGRESSION AUTHORITY
!= PlayerWindow AUTHORITY
```

PR11.9 remains the planned accepted/current-state to progression authority handoff.

## Real Pilot 01 integration

PR11.7 extends the real chain:

```text
real PR10.1 reviewed dependence
        ↓
real PR11.2 ClaimEvaluation
        ↓
PR11.3 immutable epistemic succession
        ↓
PR11.4 complete evaluation portfolio
        ↓
PR11.5 governed deterministic state derivation
        ↓
PR11.6 immutable state persistence
        ↓
PR11.7 explicit state acceptance
```

The Pilot proves five behaviors.

### Initial acceptance

A real PR11.5-derived state enters an empty state history through PR11.6 and is then explicitly
accepted by PR11.7.

### Correction does not auto-propagate acceptance

A correction appends a new `ClaimEvaluation`, rebuilds the complete portfolio, derives state B,
and appends B while retaining A.

Acceptance A remains bound to exact A content after the append.

B is not accepted merely because it was appended.

### Explicit B acceptance

B receives its own acceptance only through a new explicit PR11.7 call.

### Delayed acceptance of retained A

A may receive an acceptance during a later valid `{A}->{A,B}` persistence transition.

### Multiple accepted states still have no current state

After both A and B are accepted:

```text
accepted candidates = {A, B}
current             = undefined by PR11.7
preferred           = undefined by PR11.7
supersession        = undefined by PR11.7
progression         = unauthorized by PR11.7 alone
```

This is the intended handoff to PR11.8.

## Adversarial requirements

PR11.7 tests must include at least:

```text
state absent from successor
invalid PR11.6 successor
same-id mutation inherited from PR11.6
request behavioral subclass
state-id subclass
policy subclass
accepter subclass
mechanism-kind substitution
str/int subclasses in nested policy/accepter values
datetime subclass
non-UTC post-construction request timestamp
non-canonical rationale post-construction
acceptance record subclass
subject-ref subclass
digest str subclass
invalid exact-int state revision after object.__setattr__
invalid exact-str dimension key after object.__setattr__
naive exact-datetime state time after object.__setattr__
empty exact-str required state rationale after object.__setattr__
acceptance A surviving unrelated B append
acceptance not propagating A -> B
UNKNOWN acceptance
INSUFFICIENT acceptance
unresolved-conflict acceptance
no current/preferred/progression fields
```

## Production dependency boundary

New production authority is localized to:

```text
src/capability_lab/state/acceptance.py
```

Its dependencies are limited to:

```text
standard library:
    dataclasses
    datetime
    enum
    hashlib
    re
    unicodedata

capability_lab.epistemics:
    CapabilitySubjectRef

state.core:
    PersonalCapabilityState
    PersonalCapabilityStateId
    PersonalCapabilityStateSet
    StateError

state.snapshot_transition:
    PersonalCapabilityStateSetSuccessionReceipt
    personal_capability_state_set_sha256_v1
    validate_personal_capability_state_set_successor_v1
```

It imports no:

```text
derivation
history
progression
proposals
player_window
domains/model runtime
LLM runtime
```

The production layer does not call epistemic record-set validation, semantic catalog validation,
frame catalog validation, or PR11.5 derivation engines.

## Six-file release scope

PR11.7 v1 is intended to modify exactly:

```text
docs/state_acceptance_v1.md
src/capability_lab/state/__init__.py
src/capability_lab/state/acceptance.py
tests/state/test_state_acceptance_v1.py
tests/state/test_state_acceptance_adversarial_v1.py
tests/pilots/test_civilization_bootstrap_pilot_01_state_acceptance_integration_v1.py
```

It intentionally does not modify:

```text
state/core.py
state/serialization.py
state/snapshot_transition.py
derivation/*
epistemics/*
history/*
progression/*
proposals/*
player_window/*
Pilot production
```

## Final v1 boundary

```text
PR11.7 ACCEPTANCE
=
EXPLICIT GOVERNANCE ACT
+
FRESH PR11.6 SUCCESSION VALIDATION
+
STRICT ACCEPTED-STATE SEMANTIC ROUND-TRIP
+
EXACT PERSISTED STATE CONTENT BINDING
+
EXPLICIT POLICY / ACCEPTER / TIME / RATIONALE
```

and:

```text
PR11.7 ACCEPTANCE
!= TRUTH
!= MASTERY
!= CURRENT
!= PREFERRED
!= SUPERSESSION
!= REJECTION / REVOCATION
!= PROGRESSION AUTHORITY
!= LICENSE
!= PERMISSION
```

The next layer, PR11.8, may therefore operate on a clean candidate universe:

```text
CURRENT CANDIDATE
⊆ ACCEPTED STATES
⊆ PERSISTED STATES
```

without allowing persistence order or derivation output alone to become current-state authority.
