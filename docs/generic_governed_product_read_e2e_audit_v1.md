# PR12.14 — Generic Governed Product/Read End-to-End Audit v1

## Status

PR12.14 is an integration/audit boundary. It introduces **no new production authority, inference algorithm, state selector, progression selector, product write-back path, or automatic closed loop**.

Its purpose is to prove that the already-governed generic write/evaluation path and current-state path can reach the existing PR11.9–PR11.11 advisory/read surface entirely through their public APIs:

```text
PR12.0 external observation
→ PR12.1 HUMAN-reviewed neutral EvidenceRecord
→ PR11.3 evidence persistence
→ PR12.2 interpretation proposal
→ PR12.3 HUMAN terminal review/admission
→ PR12.4 deterministic CapabilityClaim
→ PR11.3 claim persistence
→ PR12.5 HUMAN PARTIAL / INSUFFICIENT ClaimEvaluation
→ PR11.3 evaluation persistence
→ PR12.6 declarative domain policy
→ PR12.7 HUMAN policy approval/runtime authority
→ PR12.8 complete candidate evidence universe
→ PR12.9 complete explicit dispositions
→ PR12.10 lineage/non-inference audit
→ PR12.11 HUMAN semantic requirement mapping/runtime admission
→ PR12.12 deterministic domain-sufficient ClaimEvaluation
→ PR11.3 evaluation persistence
→ PR11.4 complete evaluation portfolio
→ PR11.5 complete-portfolio state derivation
→ PR11.6 state persistence
→ PR11.7 explicit state acceptance
→ PR11.8 explicit current SELECT + fresh authority replay
→ PR11.9 governed progression handoff
→ PR11.10 complete current-state portfolio
→ PR11.11 governed product/read snapshot
```

PR12.13 already proves the chain through PR11.8. PR12.14 deliberately reuses that exact generic integration fixture and audits only the downstream composition that had not yet been exercised by the generic path.

## Primary boundary

```text
PRODUCT / READ PROJECTION
!= CURRENT-STATE SELECTION AUTHORITY
!= PROGRESSION AUTHORITY
!= CAPABILITY UPDATE AUTHORITY
!= AUTOMATIC CLOSED LOOP
```

PR11.11 is a read composition boundary. It does not choose a state, accept a state, mutate current-selection history, mutate epistemic records, or write a new capability evaluation.

## Positive governed trace

The positive case begins with the real PR12-derived state from PR12.13:

```text
PR12.5 evaluation   = PARTIAL / INSUFFICIENT
PR12.12 evaluation  = SUFFICIENT_FOR_CLAIM / SUPPORTED
PR11.5 dimension    = SUPPORTED
PR11.7 state        = explicitly accepted
PR11.8 scope head   = explicit HUMAN SELECT
```

PR12.14 then constructs a **state-less** `CurrentStateProgressionFrontierRequest`. The seed names only:

- exact capability concept revision;
- exact competence-frame revision;
- requested dimension keys.

It contains no `state_id`, no `selected_state_id`, and no subject selector. PR11.9 derives the subject from the governed selection history and fresh-replays the exact PR11.8 authority basis before supplying the state to unchanged PR8 progression semantics.

The observed binding is:

```text
requested concept/frame scope
→ fresh PR11.8 replay
→ SELECT
→ exact PR12-derived PersonalCapabilityStateId
→ PR8 FrontierSeedBinding
```

The caller therefore cannot substitute a convenient accepted, persisted, newer, older, or otherwise preferred state into progression.

## PR11.10 complete current profile

PR11.10 is independently derived from the same complete current-selection history and exact authority bases.

The API exposes no scope subset. The resulting portfolio binds the entire current-selection-history digest and every governed scope head.

For the positive PR12.14 trace the complete profile contains exactly the PR12-derived `SELECT` state. The selected-state set and the portfolio entry are independently hashed and then compared with the values embedded by PR11.11.

```text
CALLER REQUEST != CURRENT PROFILE FILTER
LATEST ACCEPTED STATE != CURRENT STATE
PRESENTED STATE != CURRENT AUTHORITY
```

## PR11.11 fresh dual reconstruction

`CurrentStatePlayerWindowRequest` contains presentation controls plus one state-less PR11.9 request. It does **not** contain:

```text
subject_ref
selected_state_id / selected_state_ids
prebuilt current-state portfolio
prebuilt governed frontier
selected frontier object
current-selection request
```

PR11.11 freshly derives both governed sources:

```text
same current-selection history + same PR11.8 authority bases
        |
        +-------------------------------+
        |                               |
        v                               v
fresh PR11.10 portfolio          fresh PR11.9 frontier
        |                               |
        +---------------+---------------+
                        |
              exact history reconciliation
              exact SELECT/CLEAR/ABSENT reconciliation
                        |
                        v
                 unchanged PR9 renderer
                        |
                        v
          CurrentStateGovernedPlayerWindow
```

The audit independently derives PR11.9 and PR11.10 first, then proves the stored PR11.11 digests and authority projections equal those fresh results.

The raw `PlayerWindow.selected_state_ids` must contain **every and only** PR11.10 `SELECT` state. A product layer cannot hide a governed current state by presentation selection and cannot invent an additional current state.

## CLEAR is not ABSENT

The audit initially attempted to create a root `CLEAR` on a completely separate scope that had never contained an accepted candidate state. PR11.8 correctly rejected that attempt:

```text
current selection scope has no accepted candidate states at selected_at
```

This is a useful fail-closed result, not a production defect. PR12.14 therefore does not weaken or bypass that rule.

The executable CLEAR audit instead performs the valid governed sequence:

```text
accepted candidate state exists
→ explicit PR11.8 SELECT
→ later explicit PR11.8 CLEAR of that same governed scope
```

Fresh PR11.10 then preserves the scope head as:

```text
CurrentStateSelectionAction.CLEAR
selected_state_id = None
current_state_set.states = ()
```

Fresh PR11.9 distinguishes it from a scope with no history:

```text
CLEAR scope  -> authority status CLEAR  -> cannot be a progression seed
no scope     -> authority status ABSENT -> cannot be a progression seed
```

Therefore:

```text
CLEAR != ABSENT
NO CURRENT STATE != NO GOVERNANCE HISTORY
PRESENTATION ABSENCE != GOVERNANCE ABSENCE
```

## Temporal semantics and defense-in-depth

The audit intentionally probed historical product reads.

A first attempt used a snapshot `as_of` equal to the current state's exact epistemic `as_of` but earlier than the time at which that state object was derived. The composed path correctly allowed it. This demonstrates that the historical boundary is about **what epistemic time the state represents**, not merely when the derivation computation occurred.

For the PR12.13 generic state:

```text
state.as_of = t9
```

Therefore `product as_of = t9` is temporally admissible with respect to the current-state semantics even though the state object was derived later.

When the audit moves the product/progression `as_of` back to `t8`, the same current state is rejected. In this generic trace the rejection happens **earlier than the final PR11.11 complete-profile guard** because the same state is also the requested PR11.9 progression seed:

```text
PR11.11 fresh composition
→ PR11.9 fresh PR11.8 replay
→ unchanged PR8 progression
→ selected progression state.as_of = t9 > frontier as_of = t8
→ reject
```

The owning error is:

```text
selected progression state may not represent a time after frontier as_of
```

PR11.11 also retains its own complete-profile defense-in-depth check:

```text
any PR11.10 current SELECT state.as_of > product request.as_of
→ reject rather than silently filter current profile
```

That second guard matters for complete-profile SELECT states that are not necessarily among the PR11.9 requested progression scopes. The generic single-scope positive trace reaches the earlier PR8 guard first because its current state is also the progression seed.

Thus:

```text
DERIVATION TIME != STATE SEMANTIC AS_OF
PROGRESSION AS_OF < SELECTED SEED STATE.AS_OF -> FAIL CLOSED
PRODUCT AS_OF < COMPLETE CURRENT STATE.AS_OF  -> FAIL CLOSED
```

## Stale-history rejection

PR11.11 artifacts are not durable current-authority tokens.

The audit builds a valid product snapshot from a `SELECT` history, then appends a valid `CLEAR` governance act **before the old snapshot's generated_at**. Fresh validation of the old snapshot against the enlarged history fails.

So staleness is not merely a future-time check:

```text
old snapshot + newly supplied historical governance append
!= still-current product snapshot
```

Fresh reconstruction is required.

## Serialized snapshot is audit data

`CurrentStateGovernedPlayerWindow` supports strict serialization. The audit proves canonical JSON round-trip preserves exact artifact identity and digest.

But restored bytes are not accepted as current authority on their own. The restored artifact is passed back through `validate_current_state_governed_player_window_v1(...)`, which freshly re-derives PR11.9 and PR11.10 from live governed source inputs and requires exact equality.

```text
SERIALIZED PRODUCT SNAPSHOT != CURRENT AUTHORITY
SERIALIZED PRODUCT SNAPSHOT != PROGRESSION AUTHORITY
RESTORATION != FRESH GOVERNANCE REPLAY
```

## Missing authority fails every downstream layer

With the real PR11.8 current-selection history present but its authority basis omitted:

- PR11.9 rejects progression derivation;
- PR11.10 rejects complete-current-profile derivation;
- PR11.11 rejects product/read derivation.

Structural history is therefore insufficient all the way to the product boundary.

```text
STRUCTURAL CURRENT HEAD != GOVERNED CURRENT AUTHORITY
```

## Product projection does not write back

The audit snapshots the exact current-selection history and persisted state set before PR11.11 derivation and proves they remain unchanged afterwards.

The governed product artifact, raw player window, and progression frontier expose no fields granting:

- permission;
- readiness;
- mastery;
- professional authority;
- human worth;
- state write-back;
- current-selection mutation.

Progression remains advisory.

```text
PROGRESSION != READINESS
PROGRESSION != PERMISSION
PRODUCT VIEW != CAPABILITY UPDATE
```

## Independence from Pilot-specific production code

The PR12.14 integration module reuses only the merged PR12.13 **test helper** that constructs the generic governed current-state basis. All downstream transitions call public production APIs.

The integration source contains no:

- `capability_lab.pilots` production import;
- `object.__new__` authority fabrication;
- `object.__setattr__` mutation shortcut;
- monkeypatch shortcut.

No production wrapper is added merely to make the end-to-end demonstration convenient.

## What PR12.14 proves

PR12.14 proves the generic chain can reach the existing product/read boundary while preserving every authority separation already established by PR11 and PR12:

```text
GENERIC EXTERNAL OBSERVATION
→ governed evidence
→ governed claim
→ governed domain-sufficient evaluation
→ governed current state
→ governed advisory progression
→ complete current profile
→ governed product/read snapshot
```

It does **not** prove or authorize:

```text
external event -> automatic capability update
automatic HUMAN-review replacement
automatic current-state selection
automatic progression execution
product-driven state mutation
readiness / licensing / permission authority
```

## Release boundary

The release-level statement after PR12.14 is:

```text
GENERIC EXTERNAL OBSERVATION -> GOVERNED PRODUCT/READ SNAPSHOT = EXECUTABLY PROVEN
PR11.9 progression input authority                              = FRESH PR11.8 REPLAY
PR11.10 current profile                                        = COMPLETE OVER HISTORY HEADS
PR11.11 product snapshot                                       = FRESH PR11.9 + PR11.10 RECONCILIATION
AUTOMATIC CLOSED-LOOP CAPABILITY UPDATE                        = NOT AUTHORIZED
PRODUCT VIEW                                                    != AUTHORITY
PROGRESSION                                                     = ADVISORY
```
