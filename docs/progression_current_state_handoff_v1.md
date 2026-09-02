# Governed Current-State-to-Progression Authority Handoff v1

Status: **PR11.9 normative governance contract**

PR11.9 closes the caller-controlled personal-state selection gap between the PR11.8 current-state authority boundary and the existing PR8 deterministic progression frontier.

PR8 remains unchanged and remains a raw deterministic advisory primitive. PR11.9 adds one narrow governed admission layer that decides which exact personal states, if any, may be supplied to that primitive.

```text
PR11.8 FULL CURRENT-STATE AUTHORITY REPLAY
        ↓
EXACT CURRENT SELECT / CLEAR / ABSENCE
        ↓
PR11.9 PERSONAL-STATE INPUT ADMISSION
        ↓
UNCHANGED PR8 DETERMINISTIC FRONTIER
        ↓
SEPARATE GOVERNED FRONTIER ARTIFACT
```

## Primary invariant

```text
GOVERNED PROGRESSION FRONTIER
=
PR8 DETERMINISTIC FRONTIER
WHOSE EVERY PERSONAL-STATE INPUT
WAS DERIVED FROM
PR11.8 FULL AUTHORITY REPLAY
```

PR11.9 grants no new semantic authority beyond personal-state input admission:

```text
PROGRESSION INPUT AUTHORITY != RECOMMENDATION AUTHORITY
PROGRESSION INPUT AUTHORITY != READINESS
PROGRESSION INPUT AUTHORITY != PERMISSION
PROGRESSION INPUT AUTHORITY != SAFETY
PROGRESSION INPUT AUTHORITY != MASTERY
```

A governed frontier is still an advisory PR8 projection.

## Existing raw PR8 boundary

PR8 accepts explicit `FrontierSeedBinding.state_id` and optional `PrerequisiteCheckBinding.state_id` values. It validates those exact states against source snapshots and enforces supported seed dimensions, but PR8 itself does not establish acceptance/current-state authority.

That raw API remains public and unchanged because it is a useful deterministic primitive and test surface.

```text
RAW PR8
CALLER MAY NAME state_id

RAW PR8 VERIFIED
!=
PR11.9 GOVERNED
```

PR11.9 therefore does not modify:

```text
progression/core.py
progression/derivation.py
progression/verification.py
progression/serialization.py
```

## Governed request removes caller state identity

PR11.9 introduces state-less personal-scope specifications:

```text
CurrentStateProgressionSeed
    concept_ref
    frame_ref
    dimension_keys

CurrentStatePrerequisiteCheck
    target_ref
    prerequisite_ref
    relation_scope
    frame_ref
    required_dimension_keys
```

Neither type contains `state_id`.

The governed request also omits `subject_ref`:

```text
SUBJECT
!= CALLER INPUT

SUBJECT
=
selection_history.subject_ref
```

The caller may choose the exact concept/frame/dimension scope to inspect, explicit PR8 focus, and explicit exploration input. The caller may not choose which personal state identity represents that scope.

```text
CALLER MAY CHOOSE
    concept/frame scope
    dimensions
    explicit focus
    explicit exploration
    request-local prerequisite mapping

CALLER MAY NOT CHOOSE
    progression personal state_id
```

A governed request must contain at least one personal-state scope through a seed or prerequisite check. Focus-only or exploration-only projection remains raw PR8, not PR11.9 authority handoff.

## Scope resolution through PR11.8 only

For every exact requested `(concept_ref, frame_ref)` scope, PR11.9 invokes:

```python
validate_personal_capability_current_state_selection_v1(...)
```

A bare structural resolver, latest persisted state, accepted state, or caller state ID is never a substitute.

Before any requested-scope resolution, PR11.9 also establishes the authority of the supplied subject history itself:

```text
selection_history empty
    → authority_bases must be empty

selection_history non-empty
    → authority_bases must cover the complete exact subject selection history
    → PR11.8 authority replay runs through one deterministic existing scope
    → only then may requested scopes resolve as SELECT / CLEAR / ABSENT
```

This preflight is required even when every requested scope is `ABSENT`. An unrelated subject selection may therefore participate in the governed history digest only if its complete PR11.8 authority basis is supplied and the subject-wide acceptance lineage replays successfully.

PR11.9 records one exact `CurrentStateProgressionAuthorityBinding` per requested scope with status:

```text
SELECT
CLEAR
ABSENT
```

### SELECT

`SELECT` binds:

```text
exact concept/frame
exact current selection SHA-256
exact selected state ID
exact selected state content SHA-256
```

The selected state is extracted only from the exact PR11.8 authority basis corresponding to the validated SELECT record. Its subject, concept, frame and content digest are checked again at the handoff boundary.

### CLEAR

`CLEAR` binds the exact structural head digest after PR11.8 full authority replay returns no current state.

It carries no state ID.

### ABSENT

An exact scope with no selection chain binds `ABSENT` and carries neither selection nor state identity.

PR11.8 requires empty authority bases for an absent requested scope. PR11.9 preserves that per-scope call contract: after the subject-history preflight succeeds, an individual absent requested scope is internally validated with `authority_bases=()`.

The outer PR11.9 authority input follows the history, not the requested-scope set:

```text
EMPTY SUBJECT HISTORY
→ OUTER authority_bases = ()

NON-EMPTY SUBJECT HISTORY
→ OUTER authority_bases = COMPLETE EXACT SUBJECT-HISTORY BASES
```

Therefore an all-requested-`ABSENT` request with non-empty unrelated subject history still requires and replays the full subject-wide authority evidence before any governed frontier can be issued.

## Seed semantics

A governed seed requires:

```text
PR11.8 result = SELECT
```

`CLEAR` or `ABSENT` cannot become a positive seed.

```text
NO CURRENT STATE
=>
NO GOVERNED SEED
```

After a SELECT is admitted, PR11.9 constructs the ordinary PR8 `FrontierSeedBinding` internally. Existing PR8 semantics remain authoritative for dimension standing:

```text
CURRENT != SUPPORTED SEED
```

Therefore a current state may honestly contain `UNKNOWN`, `INSUFFICIENT`, or unresolved conflict. PR11.9 does not upgrade those semantics.

PR8 continues to reject non-`SUPPORTED` seed dimensions. Existing `SUPPORTED + UNRESOLVED` behavior remains unchanged and conflict remains inspectable.

## Prerequisite semantics

A governed prerequisite check does not require a positive current state.

```text
PR11.8 SELECT
    → raw PR8 prerequisite state_id = exact current state

PR11.8 CLEAR / ABSENT
    → raw PR8 prerequisite state_id = None
```

This turns the PR8 `NO_SELECTED_STATE` representation into a governed absence/current-clear result rather than a caller omission.

```text
NO_SELECTED_STATE
!= MISSING HUMAN CAPABILITY
NO_SELECTED_STATE
!= FAILURE
```

If a current prerequisite state exists, PR8 preserves its exact dimension semantics:

```text
SUPPORTED    → no gap for that dimension
UNKNOWN      → UNKNOWN gap
INSUFFICIENT → INSUFFICIENT gap
```

No gap still does not imply readiness, safety, permission, or recommendation.

## Minimal authorized state snapshot

PR11.9 does not accept a caller-supplied `PersonalCapabilityStateSet`.

After all requested scopes are resolved, it constructs an internal minimal state snapshot containing only exact authority-resolved SELECT states required by the governed request.

```text
PR8 PERSONAL STATE INPUT
=
MINIMAL SET OF AUTHORITY-RESOLVED CURRENT STATES

NOT
CALLER-SUPPLIED STATE UNIVERSE
```

If the same exact state ID is reached from more than one requested scope, it must denote exact equal state content or the handoff fails closed.

## Time boundary

PR8 already preserves:

```text
state.as_of <= frontier.as_of
state.derived_at <= frontier.generated_at
```

PR11.9 additionally requires:

```text
EVERY selection.selected_at
IN supplied subject history
<= request.generated_at
```

Future governance may not authorize an earlier-generated frontier.

```text
FUTURE SELECT / CLEAR
MAY NOT AUTHORIZE
PAST HANDOFF GENERATION
```

PR11.9 deliberately does not require `selection.selected_at <= frontier.as_of`. Historical projection remains possible when a later governance act explicitly chooses an older state, provided that governance already existed by actual `generated_at`.

## Raw and governed frontier separation

PR11.9 returns:

```text
CurrentStateGovernedProgressionFrontier
    request
    current_selection_history_sha256
    authority_bindings
    frontier  # ordinary PR8 ProgressionFrontier
```

A plain PR8 `ProgressionFrontier` therefore cannot impersonate a governed artifact by type or API surface.

The artifact constructor checks that:

- authority bindings cover exactly every requested personal-state scope;
- SELECT/CLEAR/ABSENT fields are internally coherent;
- raw PR8 frontier identity/time/requester/focus/exploration matches the governed request;
- raw PR8 seed state IDs equal authority-derived current SELECT states;
- raw PR8 prerequisite state IDs equal current SELECT states or `None` for CLEAR/ABSENT.

Structural artifact validity is not downstream authority by itself.

## Fresh revalidation

Downstream code must use:

```python
validate_current_state_governed_progression_frontier_v1(...)
```

The validator fresh-runs the complete handoff:

```text
subject-history PR11.8 authority preflight
        ↓
current PR11.8 requested-scope authority replay
        ↓
exact scope resolution
        ↓
minimal authorized state set
        ↓
unchanged PR8 derivation
        ↓
PR8 source-backed verification
        ↓
exact PR11.9 artifact equality
```

Therefore:

```text
STRUCTURALLY CONSTRUCTED GOVERNED ARTIFACT
!= FRESHLY VALIDATED GOVERNED ARTIFACT
```

A later SELECT, CLEAR, or unrelated subject selection changes the bound current-selection history snapshot and makes the older artifact stale against that newer supplied history.

Historical validation remains possible only with the exact historical selection-history and authority evidence that existed at the artifact boundary.

## Content digest

PR11.9 exposes:

```python
current_state_governed_progression_frontier_sha256_v1(...)
```

with domain:

```text
capability_lab/current_state_governed_progression_frontier@1\0
```

The digest covers:

- governed request;
- current-selection history digest;
- exact per-scope authority bindings;
- complete strict PR8 frontier payload.

It is content identity/integrity material, not a signature, authentication proof, publication act, or permission token.

## Real Pilot 01 integration

The real Pilot path intentionally preserves a non-positive state:

```text
PR10.1 reviewed evidence
        ↓
PR11.2 real multi-evidence evaluation = INSUFFICIENT
        ↓
PR11.3 append-only epistemic history
        ↓
PR11.4 complete evaluation portfolio
        ↓
PR11.5 governed state
basic_electricity / reasoning = INSUFFICIENT
        ↓
PR11.6 immutable persistence
        ↓
PR11.7 explicit acceptance
        ↓
PR11.8 explicit current SELECT
        ↓
PR11.9 authority handoff
        ↓
PR8 prerequisite check for
low_voltage_power_distribution REQUIRES basic_electricity
        ↓
INSUFFICIENT prerequisite evidence gap
```

The integration deliberately selects an older accepted state A while newer accepted state B also exists. PR11.9 must use A because A is current; B does not win by persistence, derivation, or acceptance recency.

A second integration proves:

```text
CURRENT INSUFFICIENT
!= POSITIVE SEED
```

and a third proves:

```text
SELECT A → CLEAR
        ↓
prerequisite current state = None
        ↓
NO_SELECTED_STATE gap
```

## Exact production boundary

PR11.9 production authority is localized to:

```text
src/capability_lab/progression/current_state_handoff.py
```

Its import surface is frozen by an exact AST regression.

PR11.9 modifies no PR8 algorithm, current-selection algorithm, acceptance algorithm, derivation algorithm, epistemic layer, Player Window, or Pilot production module.

## Fail-closed matrix

PR11.9 fails closed for at least:

```text
caller state_id surface in governed seed             ABSENT BY TYPE DESIGN
caller subject_ref surface                           ABSENT BY TYPE DESIGN
state-free focus/exploration-only governed wrapper   REJECT
wrong/subclass governed request                      REJECT
post-construction corrupted concept/frame ref        REJECT
wrong/subclass authority_bases                       REJECT
empty history + non-empty authority_bases            REJECT
non-empty history + missing/incomplete bases          REJECT via subject preflight
all requested scopes ABSENT + unrelated history      REPLAY FULL SUBJECT AUTHORITY FIRST
missing/duplicate/extra PR11.8 basis                 REJECT via PR11.8
cross-scope acceptance rollback                      REJECT via PR11.8
future selection after generated_at                  REJECT
seed scope ABSENT                                    REJECT
seed scope CLEAR                                     REJECT
seed current dimension UNKNOWN                       REJECT via unchanged PR8
seed current dimension INSUFFICIENT                  REJECT via unchanged PR8
prerequisite scope ABSENT                            state_id=None
prerequisite scope CLEAR                             state_id=None
prerequisite UNKNOWN                                 UNKNOWN gap
prerequisite INSUFFICIENT                            INSUFFICIENT gap
forged selected state substitution                   REJECT
raw PR8 frontier used as governed artifact           REJECT
forged history digest                                REJECT on fresh replay
forged authority binding                             REJECT
forged PR8 candidates/gaps/policy/deriver            REJECT via PR8 verification
stale artifact after later selection                 REJECT
```

## Negative boundary

```text
PR11.9 != NEW PROGRESSION ALGORITHM
PR11.9 != RECOMMENDER
PR11.9 != CURRICULUM
PR11.9 != RANKING
PR11.9 != SCORE
PR11.9 != DIFFICULTY
PR11.9 != READINESS
PR11.9 != SAFETY
PR11.9 != PERMISSION
PR11.9 != LICENSING
PR11.9 != MASTERY
PR11.9 != GOAL INFERENCE
PR11.9 != INTEREST INFERENCE
PR11.9 != STATE DERIVATION
PR11.9 != STATE ACCEPTANCE
PR11.9 != CURRENT-STATE SELECTION
PR11.9 != ACTOR AUTHENTICATION
```

## Final architecture

```text
EVIDENCE
  ↓
CLAIM
  ↓
EVALUATION
  ↓
COMPLETE EVALUATION PORTFOLIO
  ↓
GOVERNED STATE DERIVATION
  ↓
IMMUTABLE STATE HISTORY
  ↓
EXPLICIT ACCEPTANCE
  ↓
COMPLETE ACCEPTED-STATE UNIVERSE
  ↓
EXPLICIT CURRENT SELECTION
  ↓
FULL CURRENT AUTHORITY REPLAY
  ↓
PR11.9 PERSONAL-STATE INPUT ADMISSION
  ↓
UNCHANGED PR8 DETERMINISTIC FRONTIER
  ↓
GOVERNED PROGRESSION FRONTIER
```

```text
CURRENT STATE
!= PROGRESSION FRONTIER

RAW PROGRESSION FRONTIER
!= GOVERNED PROGRESSION FRONTIER

GOVERNED PROGRESSION FRONTIER
!= RECOMMENDATION

RECOMMENDATION
!= PERMISSION
```
