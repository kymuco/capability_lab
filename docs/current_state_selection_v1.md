# Governed Current Personal Capability State Selection v1

Status: **PR11.8 normative governance contract**

PR11.8 defines how explicitly accepted immutable `PersonalCapabilityState` records become eligible
for one explicit current-state governance act, and how downstream code independently proves that
this current-state authority is rooted in a complete governed acceptance lineage.

```text
PR11.6 IMMUTABLE PERSISTED STATE HISTORY
        ↓
PR11.7 EXPLICIT ACCEPTANCE FACTS
        ↓
PR11.8 APPEND-ONLY SUBJECT-WIDE ACCEPTANCE UNIVERSE
        ↓
COMPLETE ACCEPTED-STATE CANDIDATE PORTFOLIO
        ↓
EXPLICIT SELECT / CLEAR
        ↓
SCOPE-LOCAL HASH-LINKED NO-FORK SELECTION HISTORY
        ↓
SUBJECT-WIDE ACCEPTANCE-AUTHORITY REPLAY
        ↓
VALIDATED SCOPE HEAD
```

PR11.8 does not derive states, issue acceptance, rank states, infer currentness from timestamps, or
authorize progression.

## Primary invariant

```text
CURRENT
=
UNIQUE HEAD
OF AN EXPLICIT GOVERNED SCOPE-LOCAL SELECTION CHAIN
WHOSE AUTHORITY BASIS
PARTICIPATES IN ONE SUBJECT-WIDE ACCEPTANCE LINEAGE
FRESH-REPLAYED FROM EMPTY ACCEPTANCE GENESIS
```

The following never establish currentness by themselves:

```text
latest persisted state
latest state.as_of
latest state.derived_at
latest acceptance.accepted_at
highest policy revision
accepter mechanism kind
number of acceptance facts
state id lexical order
serialization order
```

```text
CURRENT != LATEST-WINS
CURRENT != BEST
CURRENT != PREFERRED
CURRENT != TRUE
CURRENT != MASTERY
CURRENT != PROGRESSION AUTHORITY
```

## Acceptance-set universe

PR11.7 models every acceptance as a complete immutable value record. PR11.8 introduces:

```text
PersonalCapabilityStateAcceptanceSet
    subject_ref
    acceptances
```

The set contains exact `PersonalCapabilityStateAcceptance` values. Exact duplicates are forbidden.
Different policy, accepter, acceptance time, rationale, or PR11.7 issuance basis remains a distinct
acceptance fact.

The acceptance set is **subject-wide**, not concept/frame-local. It has no score, vote, consensus,
preference, ranking, or current-state semantics.

## Append-only acceptance succession

Acceptance history cannot remain complete if previously governed acceptance facts can disappear.

```text
VALID ACCEPTANCE-SET SUCCESSOR
=
RETENTION
+
APPEND
```

The validator is:

```python
validate_personal_capability_state_acceptance_set_successor_v1(
    *,
    state_snapshot,
    predecessor,
    successor,
    admissions=(),
)
```

Removal is invalid. Mutation is represented as removal plus addition and is therefore invalid.
Every retained and added acceptance must still bind exact persisted state content in the supplied
state snapshot.

### New acceptance admission

A newly added acceptance additionally requires:

```text
PersonalCapabilityStateAcceptanceAdmission
    acceptance
    persistence_predecessor
    persistence_successor
```

The acceptance-set validator fresh-replays the PR11.7 issuance basis through:

```python
validate_personal_capability_state_acceptance_v1(...)
```

Thus:

```text
NEW ACCEPTANCE ADMISSION
=
FRESH PR11.7 ISSUANCE-BASIS REPLAY

RETAINED ACCEPTANCE VALIDATION
=
DURABLE EXACT-STATE BINDING
```

Actor/account authentication remains outside this typed governance layer, consistent with PR11.7.

## Complete current-state candidate portfolio

The anti-cherry-picking rule is:

```text
CALLER MAY CHOOSE THE EXPLICIT TARGET STATE
CALLER MAY NOT CHOOSE WHICH ACCEPTED STATES EXIST
```

The validator-issued portfolio is built through:

```python
build_complete_current_state_candidate_portfolio_v1(
    *,
    state_snapshot,
    acceptance_set,
    concept_ref,
    frame_ref,
    as_of,
)
```

It contains every eligible accepted state in the exact scope. A caller-constructed portfolio value
is not accepted by the portfolio hashing surface.

Current-state scope is exact:

```text
subject_ref + exact concept_ref + exact frame_ref
```

Candidate membership intentionally does not rank or filter by derivation policy, deriver,
acceptance policy, accepter, acceptance count, standing, or conflict status. Multiple acceptances
remain provenance, not votes.

`as_of` controls temporal eligibility only:

```text
acceptance.accepted_at <= as_of  → eligible
acceptance.accepted_at > as_of   → future acceptance excluded
```

Once eligible, later timestamps do not rank states.

## Selection request and record

Two actions exist:

```text
SELECT
CLEAR
```

`SELECT` requires an exact `selected_state_id`. `CLEAR` requires `selected_state_id=None`.

`CLEAR` removes downstream current-state authority without deleting or rejecting state, acceptance,
or history.

Each `PersonalCapabilityCurrentStateSelection` binds:

```text
subject_ref
concept_ref
frame_ref
action
selected_state_id
selected_state_sha256
candidate_portfolio_sha256
state_snapshot_sha256
acceptance_set_sha256
predecessor_selection_sha256
selection_policy_ref
selector_ref
selected_at
rationale
```

The selection digest is domain-separated and canonical.

## Scope-local no-fork selection topology

For each exact `(concept_ref, frame_ref)` scope, selection records form one rooted linear hash-linked
chain.

```text
SELECT A
   ↓
SELECT B
   ↓
CLEAR
   ↓
SELECT C
```

Forks, cycles, disconnected scope chains, and cross-scope predecessor links are invalid.

Tuple order does not establish current authority. Scope-chain topology does.

Structural resolution is provided by:

```python
resolve_current_personal_capability_state_selection_v1(...)
```

and returns the structural SELECT head or `None` for absent/CLEAR. Structural resolution alone is
not downstream authority.

## Durable authority basis

Authority replay uses:

```text
PersonalCapabilityCurrentStateSelectionAuthorityBasis
    selection
    state_snapshot
    acceptance_predecessor
    acceptance_successor
    acceptance_admissions
```

When the requested current-selection scope exists, downstream authority requires **one exact basis
for every selection act in the subject history**, not merely every act in the requested scope.

```text
TARGET SCOPE EXISTS
        ↓
ALL SUBJECT SELECTION ACTS REQUIRE EXACT BASES
```

Missing, duplicate, or extra bases fail closed.

This wider evidence requirement is necessary because selection topology is scope-local while the
acceptance universe is subject-wide. A selection act in another concept/frame scope may append an
acceptance that changes the complete candidate universe for the target scope.

## Subject-wide canonical acceptance lineage

All supplied authority bases are replayed as one subject-wide acceptance lineage ordered by the
explicit `selection.selected_at` values already bound into the immutable selection records.

For each selection timestamp:

1. every selection act at that timestamp must bind the same exact
   `acceptance_predecessor → acceptance_successor` transition;
2. every act independently fresh-replays that transition and its admissions;
3. the earliest timestamp must start from an empty acceptance predecessor;
4. each later timestamp's predecessor must exactly equal the previous timestamp's successor.

Therefore:

```text
SCOPE-LOCAL CURRENT TOPOLOGY
!=
SCOPE-LOCAL ACCEPTANCE AUTHORITY
```

and:

```text
ONE SUBJECT
→ ONE CANONICAL ACCEPTANCE LINEAGE
```

Acts sharing a timestamp but presenting different acceptance transitions are ambiguous and fail
closed instead of inventing an authority order.

This prevents cross-scope rollback/cherry-picking such as:

```text
scope A: universe {A}
        ↓
scope B: universe {A,B}
        ↓
scope A: tries to reuse stale universe {A}
        ↓
REJECT
```

Without subject-wide replay, filtering authority ancestry to scope A would hide scope B's append and
allow B to disappear from a later complete-candidate portfolio.

## Per-selection fresh replay

Each subject selection act independently revalidates:

```text
exact authority-basis selection == exact history selection
exact state snapshot structure and subject
acceptance-set append-only succession
fresh PR11.7 admissions for newly visible acceptances
selection.state_snapshot_sha256
selection.acceptance_set_sha256
complete candidate portfolio at selection.selected_at
selection.candidate_portfolio_sha256
SELECT target membership
SELECT exact selected-state content SHA-256
```

Thus a later valid-looking selection cannot launder invalid genesis, a forged intermediate
candidate portfolio, an acceptance rollback, or a cross-scope omission.

```text
VALID HEAD
DOES NOT LAUNDER
INVALID SUBJECT-WIDE AUTHORITY ANCESTRY
```

## Exact scope-reference validation

Authority requests validate more than outer Python types.

Before any scope lookup, exact `CapabilityConceptRef` and `CompetenceFrameRef` values must survive
their strict parse/string round-trip. Post-construction corruption such as an invalid revision is
therefore rejected before the validator can return `None` for an absent scope.

```text
MALFORMED EXACT-TYPE REF
!=
LEGITIMATELY ABSENT SCOPE
```

The same fail-closed distinction applies to `authority_bases`: an absent scope accepts only the exact
empty tuple `()`. Falsey lookalikes such as `None`, `[]`, or a tuple subclass are malformed input.

## Authority return contract

```text
no chain     → None, only after exact request/input validation
valid CLEAR  → None, only after full required authority replay
valid SELECT → exact fully authority-replayed SELECT head
```

PR11.9 must consume this validator rather than a bare structural resolver result or caller-selected
state ID.

## Structural issuance API

```python
select_current_personal_capability_state_v1(
    *,
    state_snapshot,
    acceptance_predecessor,
    acceptance_successor,
    acceptance_admissions=(),
    selection_history,
    request,
)
```

The issuance surface validates one supplied acceptance transition, builds the complete candidate
portfolio for the requested scope, derives that scope's predecessor head, and appends one immutable
selection act.

Issuance remains structural provenance rather than downstream authority. Because separate scope
chains can be appended independently, only the downstream authority validator establishes that all
acts are compatible with one subject-wide acceptance lineage.

## Anti-latest-wins

PR11.8 preserves cases where later states, later acceptances, higher policy revisions, different
accepter kinds, or more acceptance facts exist while an explicit governed selection still chooses an
earlier accepted state.

```text
NEW STATE APPEND      != CURRENT TRANSITION
NEW ACCEPTANCE APPEND != CURRENT TRANSITION
```

Only an explicit selection act moves one scope's current head. Subject-wide acceptance replay limits
which accepted candidates may be omitted; it does not choose the current state.

## UNKNOWN / INSUFFICIENT / conflict

PR11.8 does not reinterpret PR11.7 acceptance semantics. An accepted state containing `UNKNOWN`,
`INSUFFICIENT`, or unresolved conflict may be a candidate and may be explicitly current.

```text
CURRENT UNKNOWN
=
CURRENT GOVERNED ASSESSMENT IS HONESTLY UNKNOWN
```

It does not imply mastery or positive capability.

## Progression boundary

PR11.8 does not modify progression APIs and does not authorize progression.

```text
PR11.8 PASS
!=
PROGRESSION AUTHORITY
```

Intended handoff:

```text
SUBJECT-WIDE COMPLETE ACCEPTANCE UNIVERSE
        ↓
COMPLETE SCOPE CANDIDATES
        ↓
EXPLICIT SCOPE-LOCAL NO-FORK CURRENT SELECTION
        ↓
SUBJECT-WIDE AUTHORITY REPLAY
        ↓
PR11.9 PROGRESSION AUTHORITY HANDOFF
```

## Negative boundary

```text
PR11.8 != STATE DERIVATION
PR11.8 != STATE PERSISTENCE
PR11.8 != ACCEPTANCE ISSUANCE AUTHORITY
PR11.8 != ACCEPTANCE REJECTION
PR11.8 != ACCEPTANCE REVOCATION
PR11.8 != EPISTEMIC TRUTH
PR11.8 != MASTERY
PR11.8 != BEST-STATE RANKING
PR11.8 != PREFERRED-STATE RANKING
PR11.8 != LATEST-WINS
PR11.8 != SCORE / WEIGHT / VOTE
PR11.8 != PROGRESSION AUTHORITY
PR11.8 != CRYPTOGRAPHIC ACTOR AUTHENTICATION
```

## Fail-closed requirements

Authority validation fails closed for at least:

```text
wrong/subclass history type
wrong/subclass concept/frame type
exact-type but semantically corrupted concept/frame ref
wrong/subclass authority_bases container/items
absent scope with malformed/non-empty authority_bases
missing/duplicate/extra authority basis
preloaded nonempty subject acceptance genesis
same-timestamp conflicting acceptance transitions
subject-wide cross-scope acceptance rollback/subset
forged state snapshot digest
forged acceptance-set digest
forged candidate-portfolio digest
SELECT target absent from recomputed complete portfolio
forged selected-state content digest
unsupported action
```

## External completeness boundary

PR11.8 proves completeness relative to the canonical governed state/acceptance/selection evidence
supplied to it. It cannot discover records that external persistence omitted entirely.

The runtime must therefore durably retain:

```text
canonical subject selection history
exact per-selection authority bases
canonical append-only acceptance facts
exact persisted state snapshots required for replay
```

## PR11.9 handoff

PR11.9 may treat a current state as progression input only after
`validate_personal_capability_current_state_selection_v1(...)` succeeds on the required subject-wide
authority evidence.

A structural head, a latest state, a caller-selected ID, or a locally valid scope chain is not a
progression authority substitute.
