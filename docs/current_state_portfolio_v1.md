# PR11.10 — Complete Subject Current-State Portfolio v1

## Purpose

PR11.10 composes the complete governed current-state view for one subject from PR11.8 current-selection history and authority bases.

It introduces no new state derivation, acceptance, selection, progression, recommendation, readiness, permission, mastery, ranking, or HDE authority.

```text
CURRENT-STATE PORTFOLIO
=
EXACT COMPLETE SET
OF GOVERNED CURRENT-SELECTION HEADS
FOR EVERY CONCEPT+FRAME SCOPE PRESENT
IN THE SUBJECT CURRENT-SELECTION HISTORY
AFTER FULL PR11.8 SUBJECT-WIDE AUTHORITY REPLAY
```

## Completeness boundary

`complete` means no governed scope already present in current-selection history may be omitted.

It does not mean every capability a person has, every capability in a catalog, or every capability that might exist.

```text
SCOPE ABSENT FROM CURRENT-SELECTION HISTORY
!= UNKNOWN
!= INSUFFICIENT
!= LOW
!= NEGATIVE EVIDENCE
!= PERSON LACKS CAPABILITY
```

PR11.10 has no caller scope-selection surface. The caller supplies no `concept_ref`, `frame_ref`, requested scope set, concept filter, frame filter, or selected state IDs.

```text
subject_ref <- selection_history.subject_ref
scope universe <- all exact concept_ref+frame_ref scopes in selection_history
current state identity <- PR11.8 governed head only
```

## Output model

`PersonalCapabilityCurrentStatePortfolioEntry` binds one exact governed scope head:

```text
concept_ref
frame_ref
action = SELECT | CLEAR
current_selection_sha256
selected_state_id | None
selected_state_sha256 | None
```

`PersonalCapabilityCurrentStatePortfolio` contains:

```text
subject_ref
generated_at
current_selection_history_sha256
complete canonical entries
minimal current_state_set
```

The minimal state set contains exactly the states referenced by SELECT heads and no state for CLEAR heads.

```text
scope A -> SELECT state_A
scope B -> CLEAR
scope C -> SELECT state_C

entries = [A SELECT, B CLEAR, C SELECT]
current_state_set = [state_A, state_C]
```

Therefore:

```text
CLEAR != ABSENT
```

A CLEAR head remains explicit evidence that governance deliberately removed current-state authority for that scope.

## Authority flow

PR11.10 does not reimplement PR11.8 authority.

```text
strict current-selection history validation
        ↓
complete history SHA-256
        ↓
generated_at temporal guard
        ↓
complete scope-head enumeration
        ↓
deterministic existing anchor scope
        ↓
ONE PR11.8 validate_personal_capability_current_state_selection_v1(...)
with FULL subject authority_bases
        ↓
full PR11.8 subject-wide acceptance-authority replay
        ↓
all selection acts established as governed
        ↓
SELECT heads resolve exact state content from their exact authority basis
CLEAR heads remain explicit
        ↓
complete current-state portfolio
```

The anchor is only an invocation route into PR11.8 full subject-wide replay. It does not privilege that scope.

For empty current-selection history:

```text
authority_bases must be ()
entries = ()
current_state_set = empty one-subject PersonalCapabilityStateSet
```

## Exact selected-state binding

For each SELECT head PR11.10 resolves the selected state from the exact PR11.8 authority basis for that selection and requires:

```text
exact state_id exists once
subject_ref matches
concept_ref matches
frame_ref matches
recomputed exact state content SHA-256
== selection.selected_state_sha256
```

The caller cannot supply a state universe or replace an explicit current state with a newer accepted state.

```text
CURRENT != LATEST
```

## Time boundary

`generated_at` is canonical UTC and means when this complete governed view is produced.

Every selection in the supplied history must satisfy:

```text
selection.selected_at <= portfolio.generated_at
```

PR11.10 does not require each state's `as_of` to equal portfolio `generated_at`.

```text
portfolio.generated_at = view production boundary
state.as_of             = knowledge boundary represented by that state
```

A future governance act may not authorize an earlier portfolio.

## Fresh validation and staleness

`validate_personal_capability_current_state_portfolio_v1(...)` strictly reconstructs the supplied artifact, fresh-runs PR11.8 subject-wide authority, re-derives the complete portfolio, and requires exact equality.

Any append to current-selection history changes the history fingerprint and therefore makes an older artifact stale against the new history. If that append occurs after the artifact `generated_at`, validation fails at the temporal boundary before equality comparison.

Omitting a CLEAR entry, omitting a SELECT entry, adding a scope absent from history, replacing an explicitly current state, or changing selected state content all fail fresh validation.

## Digest

`personal_capability_current_state_portfolio_sha256_v1(...)` uses the domain:

```text
capability_lab/personal_capability_current_state_portfolio@1\0
```

The payload binds subject, generated time, full current-selection-history SHA-256, every canonical portfolio entry, and the strict PR11.6 current-state-set SHA-256.

The digest is deterministic integrity identity. It is not a signature, authenticated history, trusted timestamp, publication authority, or HDE permission.

## Core non-authority boundaries

```text
CURRENT != LATEST
CURRENT != BEST
CURRENT != PREFERRED
CURRENT != TRUE
CURRENT != MASTERY
CURRENT != READINESS
CURRENT != PERMISSION

PORTFOLIO != PERSON
PORTFOLIO != PERSONAL IDENTITY
PORTFOLIO != COMPLETE HUMAN CAPABILITY MODEL

PORTFOLIO ORDER != PRIORITY
PORTFOLIO SIZE != HUMAN LEVEL
NUMBER OF SELECT STATES != SCORE

CLEAR != ABSENT
ABSENT SCOPE != UNKNOWN / INSUFFICIENT / NEGATIVE EVIDENCE

CURRENT-STATE PORTFOLIO != PROGRESSION FRONTIER
CURRENT-STATE PORTFOLIO != PLAYER WINDOW
CURRENT-STATE PORTFOLIO != HDE AUTHORITY
```

## Layer boundary

PR11.10 is implemented only as a state-layer composition authority over existing PR11.8 contracts.

Production imports are frozen to state/semantic/epistemic identities required for exact replay and state binding. It imports no progression, Player Window, history, proposals, Pilot production, HDE, model runtime, or LLM runtime.

PR11.8 and PR11.9 production files remain unchanged.

## Real Pilot 01 integration

The integration extends the existing real chain:

```text
PR10.1 reviewed evidence
→ PR11.2 ClaimEvaluation
→ PR11.3 immutable epistemics
→ PR11.4 complete evaluation portfolio
→ PR11.5 governed deterministic state
→ PR11.6 immutable state persistence
→ PR11.7 explicit state acceptance
→ PR11.8 governed current selection
→ PR11.10 complete current-state portfolio
```

Pilot coverage preserves an older explicitly current state even when a newer accepted state exists, preserves CLEAR as an explicit portfolio entry while removing the state from `current_state_set`, and fresh-revalidates the resulting exact artifact.

## Intended downstream handoff

PR11.10 provides the complete governed current-state input required by the later product/HDE read snapshot boundary.

That future layer may compose PR11.10 current state, PR11.9 governed progression, and source-visible presentation primitives, but it must not move scope/state selection authority back into HDE.
