# PR11.11 — Governed Product Read Snapshot v1

## Purpose

PR11.11 creates the first product/read boundary that is safe to expose to HDE without returning personal-state or progression-frontier authority to the caller.

```text
GOVERNED PRODUCT READ SNAPSHOT
=
PR9 DETERMINISTIC PLAYER WINDOW
WHOSE PERSONAL STATES
ARE EXACTLY THE COMPLETE PR11.10 CURRENT SELECT SET
AND WHOSE FRONTIER
IS EXACTLY PR11.9 GOVERNED PROGRESSION
DERIVED FROM THE SAME FRESH CURRENT-SELECTION HISTORY
```

PR11.11 introduces no new capability truth, state derivation, acceptance, current-state selection, progression algorithm, recommendation, readiness, permission, mastery, ranking, or HDE write authority.

## Authority versus visibility

Raw PR9 intentionally supports explicit source selection. That remains useful for presentation, but `selected_state_ids` and `selected_frontier_id` are not safe as an HDE-facing authority boundary.

PR11.11 separates the two kinds of choice:

```text
DISPLAY VISIBILITY MAY BE CALLER-SELECTED

CURRENT-STATE AUTHORITY
AND
PROGRESSION-FRONTIER AUTHORITY
MAY NOT BE CALLER-SELECTED
```

The PR11.11 request therefore contains presentation-only visibility for PR7 history and Legend, but contains no subject, state set, frontier set, selected state ids, selected frontier id, supplied PR11.10 portfolio, or supplied PR11.9 governed frontier.

```text
VISIBLE != CURRENT
VISIBLE != AUTHORITATIVE
HIDDEN != DELETED
NOT DISPLAYED != DID NOT HAPPEN
NO VISIBLE LEGEND != NO LEGEND EXISTS
```

## Public request

`CurrentStatePlayerWindowRequest` contains:

```text
window_id
generated_at
requester_ref
viewer_ref
progression_request
visible_achievement_ids
visible_milestone_ids
visible_legend_id
```

Its `progression_request` is the state-less PR11.9 `CurrentStateProgressionFrontierRequest`. The PR11.11 `generated_at` must exactly equal the nested progression `generated_at`; snapshot `as_of` is the nested progression `as_of`.

The public surface deliberately has no:

```text
subject_ref
state_set
frontier_set
selected_state_ids
selected_frontier_id
requested current-state scopes
current_state_portfolio
governed_frontier
latest / best / readiness / permission / mastery selector
```

## Fresh composition

PR11.11 does not trust prebuilt downstream artifacts supplied by the caller.

```text
selection_history + full PR11.8 authority_bases
        |
        +-----------------------------+
        |                             |
        v                             v
fresh PR11.10                    fresh PR11.9
complete current portfolio       governed progression frontier
        |                             |
        +-------------+---------------+
                      |
             same history digest
                      |
             exact authority reconciliation
                      |
       ALL PR11.10 SELECT states
                      +
       EXACT PR11.9 raw frontier
                      +
       presentation-only history visibility
                      |
                      v
            unchanged PR9 derivation
                      |
            unchanged PR9 verification
                      |
                      v
       CurrentStateGovernedPlayerWindow
```

This rejects composition mistakes such as a new portfolio with an old frontier, artifacts derived from different current-selection histories, or caller-picked otherwise-valid state/frontier records.

## Cross-artifact reconciliation

PR11.9 authority must be a consistent projection of PR11.10 complete current-state authority.

For every PR11.9 binding:

```text
PR11.9 SELECT
-> PR11.10 same scope SELECT
-> exact current_selection_sha256
-> exact selected_state_id
-> exact selected_state_sha256

PR11.9 CLEAR
-> PR11.10 same scope CLEAR
-> exact current_selection_sha256

PR11.9 ABSENT
-> exact scope absent from PR11.10 portfolio
```

PR11.10 may contain additional current scopes not used by the frontier. Those remain part of the complete product snapshot.

## Complete current-state visibility

The raw PR9 `selected_state_ids` are generated internally as every state in PR11.10 `current_state_set`.

```text
current A -> SELECT
current B -> SELECT
current C -> CLEAR
frontier uses only A

PR9 capabilities = A + B
PR11.11 current authority metadata = A SELECT + B SELECT + C CLEAR
```

PR8 remains unchanged. Its effective progression inputs are still its explicit seed and prerequisite bindings, so extra current states supplied for complete PR9 visibility are inert to frontier derivation.

CLEAR is retained separately because raw PR9 has no state panel for a cleared scope. Without the PR11.11 authority metadata, a consumer could not distinguish explicit CLEAR from a scope that never existed in current-selection history.

Likewise PR11.9 SELECT/CLEAR/ABSENT bindings remain visible because raw PR8 `state_id=None` alone does not distinguish CLEAR from ABSENT.

## Time boundary

One PR11.11 artifact has one generation boundary and one progression knowledge boundary:

```text
snapshot.generated_at == progression_request.generated_at
snapshot.as_of         == progression_request.as_of
```

Every current-selection act remains subject to PR11.9/PR11.10 generated-time governance.

In addition, every complete current SELECT state must satisfy:

```text
state.as_of <= snapshot.as_of
```

If a current state lies after the requested `as_of`, PR11.11 rejects the request. It never silently hides that current state to manufacture a historical-looking complete profile.

```text
CURRENT PROFILE COMPLETENESS
>
SILENT HISTORICAL FILTERING
```

## Output

`CurrentStateGovernedPlayerWindow` contains:

```text
request
subject_ref
current_selection_history_sha256
current_state_portfolio_sha256
governed_frontier_sha256
current_state_entries
frontier_authority_bindings
window
```

The raw `window` remains an unchanged PR9 `PlayerWindow`.

The outer artifact preserves the governed authority facts that PR9 deliberately does not model as presentation panels.

## Validation and staleness

`validate_current_state_governed_player_window_v1(...)` strict-reconstructs the artifact and then fresh-runs the complete composition:

```text
fresh PR11.10
-> fresh PR11.9
-> fresh cross-binding reconciliation
-> fresh PR9 derivation
-> fresh PR9 source-backed verification
-> exact PR11.11 equality
```

A later SELECT or CLEAR makes an old snapshot stale. A historically timestamped append also makes the old snapshot stale even when its `selected_at` is not after the old `generated_at`, because the fresh governed source derivation and history identity no longer match.

## Serialization and digest

PR11.11 provides strict schema-v1 deterministic serialization for the request and snapshot:

```text
to_dict / from_dict
to_json / from_json
```

JSON parsing rejects duplicate object keys and non-finite constants.

`current_state_governed_player_window_sha256_v1(...)` uses:

```text
capability_lab/current_state_governed_player_window@1\0
```

The digest binds the request, subject, current-selection history digest, PR11.10 portfolio digest, PR11.9 governed-frontier digest, current-state entries, frontier authority bindings, and exact canonical PR9 window representation.

```text
DIGEST != SIGNATURE
DIGEST != AUTHENTICATION
DIGEST != TRUSTED TIME
DIGEST != HDE PERMISSION
DIGEST != CAPABILITY TRUTH
```

## HDE boundary

After PR11.11, Capability Lab has a stable read/advisory object suitable for HDE integration.

HDE may consume the snapshot to show current capabilities, uncertainty/conflict, source-visible state basis, progression frontier, prerequisite evidence gaps, exploration opportunities, and selected history/Legend presentation.

HDE does not decide which personal state is current and does not choose an already-existing frontier to declare authoritative.

```text
READ / ADVISORY HDE INTEGRATION = READY

CLOSED-LOOP HDE -> CAPABILITY EVIDENCE = NOT YET READY
```

A later generic ingestion boundary must govern external/HDE observations before they may become neutral evidence. HDE activity, output, or observation does not become an `EvidenceRecord` merely because PR11.11 exists.

```text
HDE ACTIVITY != EVIDENCE
HDE OBSERVATION != EVIDENCE
HDE OUTPUT != CAPABILITY UPDATE
PRESENTATION != AUTHORITY
```

## Layer boundary

PR11.11 is a composition layer over existing public contracts.

Unchanged production primitives:

```text
PR8 progression derivation and verification
PR9 core / derivation / verification / serialization
PR11.8 current-selection authority
PR11.9 governed progression handoff
PR11.10 complete current-state portfolio
Pilot production
```

The PR11.11 production module imports no HDE package, LLM runtime, model runtime, agent runtime, recommendation engine, or permission system.
