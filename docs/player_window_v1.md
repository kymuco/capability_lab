# Player Window Read Model and Local Prototype v1

Status: **PR9 implementation contract**

## Outcome

PR9 introduces Capability Lab's first private deterministic product read model and dependency-free local HTML prototype. It composes explicitly selected PR3 capability state, PR7 achievement/milestone history and optional Legend, plus one explicitly selected PR8 frontier into an inspectable `PlayerWindow` without changing the semantics of any source layer.

```text
PLAYER WINDOW != PERSONAL DEVELOPMENT MODEL
PLAYER WINDOW != PERSON
PLAYER WINDOW != CURRENT TRUTH
PLAYER WINDOW != AUTHORITY
```

The purpose of PR9 is not to create a smarter evaluator. Its purpose is to make the distinctions already protected by PR1–PR8 visible to a person using the system.

```text
PR9 COMPOSES GOVERNED RECORDS
PR9 DOES NOT RE-DERIVE THEIR MEANING
```

## Layer boundary

```text
CapabilityCatalog / CompetenceFrameCatalog
                    |
          explicitly selected PR3 state
                    +
          explicitly selected PR7 history
                    +
             optional selected Legend
                    +
          optional selected PR8 frontier
                    |
                    v
      core:deterministic_player_window@1
                    |
                    v
               PlayerWindow
           immutable read model
                    |
                    v
       render_player_window_html_v1
                    |
                    v
       self-contained local HTML
                    |
                    X
 no state/history/frontier mutation or publication
```

The renderer accepts only a completed `PlayerWindow`. It has no source catalogs/record sets and therefore cannot select latest records, infer priorities, calculate growth, or change backend meaning.

```text
RENDERER != DERIVER
```

## Explicit source selection

`PlayerWindowRequest` explicitly names:

- `PlayerWindowId`;
- `CapabilitySubjectRef`;
- `as_of` and `generated_at`;
- `PlayerWindowRequesterRef`;
- `PlayerWindowViewerRef`;
- selected `PersonalCapabilityStateId` values;
- selected `AchievementInstanceId` values;
- selected `PersonalMilestoneEventId` values;
- optional exact `PersonalLegendId`;
- optional exact `ProgressionFrontierId`.

At least one source must be selected. PR9 contains no automatic current/latest source selection.

```text
LATEST STATE != AUTOMATIC WINDOW STATE
LATEST LEGEND != AUTOMATIC WINDOW LEGEND
LATEST FRONTIER != AUTOMATIC WINDOW FRONTIER

UNSELECTED STATE != WINDOW INPUT
UNSELECTED HISTORY != WINDOW INPUT
UNSELECTED LEGEND != WINDOW INPUT
UNSELECTED FRONTIER != WINDOW INPUT
```

Selection is presentation input, not truth, completeness, importance, or subject endorsement.

```text
DISPLAYED != CANONICAL
OMITTED != ABSENT
WINDOW SELECTION != IMPORTANCE
WINDOW SELECTION != COMPLETENESS
WINDOW SELECTION != SUBJECT ENDORSEMENT
```

## Subject, requester and viewer

The modeled subject, projection requester, and intended viewer remain distinct roles.

`PlayerWindowMechanismKind` supports `HUMAN`, `RULE`, `MODEL`, `HYBRID`, and `EXTERNAL_SYSTEM` for requester/viewer/generator attribution. The frozen PR9 baseline uses a rule generator:

```text
policy    = core:deterministic_player_window@1
generator = rule:capability_lab:deterministic_player_window_v1
```

Mechanism identity does not grant authority or permission.

```text
REQUESTER != AUTHORITY
VIEWER != SUBJECT
VIEWER REF != AUTHORIZATION
MODEL WINDOW REQUESTER != SUBJECT CURATION
```

PR9 does not implement authentication, authorization, consent, publication, or sharing policy.

## Capability-state projection

A selected `PersonalCapabilityState` is projected as one `PlayerWindowCapabilityEntry` containing:

- exact source state id;
- exact capability concept revision plus concept name/definition;
- exact competence frame revision plus frame name;
- state policy and deriver attribution;
- state temporal boundaries;
- every dimension from the exact selected competence frame.

PR9 does not allow dimension-level cherry-picking inside a selected state. The exact frame and selected state must have the same complete dimension-key set.

```text
SELECTED STATE -> COMPLETE FRAME DIMENSION VISIBILITY
STATE SELECTION != DIMENSION CHERRY-PICKING
```

Each dimension preserves:

- frame-local dimension key/name/description;
- `DimensionStanding`;
- independent `DimensionConflictStatus`;
- state rationale;
- bounded supported-claim statement/scope summaries;
- basis evaluation ids/conclusion/conflict/policy/evaluator summaries.

The Player Window does not copy raw evidence payloads or become an alternative epistemic database.

## UI language for state

PR9 freezes non-authoritative display wording:

- `SUPPORTED` -> `Supported — scoped`;
- `INSUFFICIENT` -> `Insufficient represented support`;
- `UNKNOWN` -> `Unknown`.

Conflict is never hidden in the compact status. `SUPPORTED + UNRESOLVED` renders as `Supported — scoped — unresolved conflict`.

```text
SUPPORTED != MASTERED
INSUFFICIENT != LOW
UNKNOWN != ZERO
SUPPORTED + UNRESOLVED != CONFLICT-FREE SUPPORT
COMPACT UI != PERMISSION TO HIDE CONFLICT
```

No percentage, mastery level, novice/intermediate/expert label, or global score is derived.

## No growth inference in v1

PR9 deliberately does not implement the optional `recent growth` concept permitted by the early vocabulary. Immutable state differences have not yet been given a governed growth-comparison policy.

```text
STATE DIFFERENCE != GROWTH
LATER STATE != IMPROVEMENT
MORE SUPPORTED DIMENSIONS != HUMAN PROGRESS SCORE
```

A future growth projection requires its own explicit comparison semantics instead of a UI heuristic.

## History projection

Selected `AchievementInstance` records remain historical accomplishment, not current readiness. Player Window displays exact family identity/name, event/record times, bounded context, optional variant/note, and declared qualification policy/mechanism.

Selected `PersonalMilestoneEvent` records remain independent history. The UI labels `significance_note` as **Recorded significance note** rather than implying that it is the subject's endorsed interpretation.

```text
ACHIEVEMENT != CURRENT READINESS
HISTORY != STATE
ACHIEVEMENT COUNT != CAPABILITY SCORE
MILESTONE COUNT != HUMAN PROGRESS SCORE
SIGNIFICANCE NOTE != SUBJECT ENDORSEMENT
```

PR9 contains no XP, rarity, points, tier, rank, or auto-award semantics.

## Legend projection and visible source history

A selected `PersonalLegend` is displayed under the explicit heading **Narrative projection**. It is never labeled identity, true story, official history, or current state.

The Legend may be shown only if every exact history record cited by every Legend entry is also selected into the visible history section of the same Player Window.

```text
VISIBLE NARRATIVE MUST NOT HIDE ITS SOURCE HISTORY
LEGEND != HISTORY
LEGEND != PERSON IDENTITY
SELECTED LEGEND != CANONICAL LEGEND
LATEST LEGEND != AUTOMATIC SELECTION
```

This is a product-level inspectability rule: narrative cannot be made visible while its exact source history is hidden from the same projection.

## Frontier projection and visible state basis

A selected `ProgressionFrontier` is displayed as an advisory **Could be considered** panel.

PR9 preserves:

- exact frontier id and policy/requester/deriver attribution;
- candidate exact concept/name;
- explicit-focus attribution;
- direct adjacency reasons including seed state and selected seed dimensions;
- assessed and unassessed categorical prerequisites;
- prerequisite evidence gaps;
- explicit exploration opportunities.

A selected frontier must use exactly the Player Window `as_of` boundary. It may not be generated after the Player Window itself.

Every exact state id used by the selected frontier as:

- a `FrontierSeedBinding` state;
- a state-backed `PrerequisiteCheckBinding`;
- a state-backed `PrerequisiteEvidenceGap`;

must also be selected into the visible Player Window capability section.

```text
VISIBLE FRONTIER MUST NOT HIDE ITS PERSONAL-STATE BASIS
```

Candidate ordering remains canonical read-model ordering, not priority.

```text
FRONTIER CANDIDATE != RECOMMENDATION
FRONTIER CANDIDATE != NEXT REQUIRED STEP
DISPLAY ORDER != PRIORITY
WITNESS COUNT != RECOMMENDATION STRENGTH
```

## Prerequisite gaps

Player Window preserves PR8 gap semantics. A gap is labeled **Prerequisite evidence gap** and includes the exact target/prerequisite names/refs, relation description, exact frame, optional selected prerequisite state, and dimension-local gap kinds.

The local HTML explicitly states:

> Evidence gap does not mean capability absence, prohibition, readiness, safety, or permission.

```text
PREREQUISITE EVIDENCE GAP != MISSING CAPABILITY
PREREQUISITE GAP != PROHIBITION
PREREQUISITE GAP != ACCESS CONTROL
NO GAP != READY
NO GAP != SAFE
NO GAP != PERMITTED
```

An unassessed prerequisite remains labeled as not assessed in the selected frontier rather than silently satisfied.

## Exploration

PR8 `ExplorationOpportunity` values appear under **Explicit exploration**. PR9 does not rename them recommended directions or infer interest/personality from them.

```text
EXPLORATION OPPORTUNITY != RECOMMENDATION
MODEL EXPLORATION != SUBJECT INTEREST
```

## No Human Level in PR9 v1

The constitution permits an explicitly decorative local progression indicator under strict restrictions. PR9 v1 intentionally does not implement one.

```text
CONSTITUTIONALLY ALLOWED != JUSTIFIED FOR PR9
PLAYER WINDOW != HUMAN LEVEL
PLAYER WINDOW != XP SYSTEM
```

The first product surface is game-inspired in presentation structure, not game-scored in semantics.

PR9 also does not compute personal domain percentages from PR5 editorial families:

```text
EDITORIAL FAMILY != PERSONAL DOMAIN STATE
GROUP MEMBERSHIP != DOMAIN SCORE
```

## Time boundary

```text
window.as_of <= window.generated_at
selected_state.as_of <= window.as_of
selected_state.derived_at <= window.generated_at
achievement.achieved_at <= window.as_of
achievement.recorded_at <= window.generated_at
milestone.occurred_at <= window.as_of
milestone.recorded_at <= window.generated_at
legend.as_of <= window.as_of
legend.generated_at <= window.generated_at
frontier.as_of == window.as_of
frontier.generated_at <= window.generated_at
```

Exact frontier `as_of` equality prevents an apparently current Player Window from silently presenting a frontier derived for another represented state boundary.

## Strict serialization

`PlayerWindowRequest`, `PlayerWindow`, and `PlayerWindowSet` use deterministic schema-v1 JSON.

Strict ingestion rejects:

- unknown/missing object keys;
- duplicate JSON keys;
- non-finite JSON constants;
- invalid refs/enums;
- malformed or timezone-free timestamps;
- non-integer schema versions, including `true` and `1.0`.

Serialization remains representation only.

```text
STRUCTURALLY VALID WINDOW != VERIFIED WINDOW
DESERIALIZED WINDOW != VERIFIED WINDOW
SERIALIZED WINDOW != SHAREABLE WINDOW
```

## Verification

`validate_player_window_v1(...)` is the explicit source-backed verification boundary.

If the Player Window includes a PR8 frontier, verification first calls `validate_progression_frontier_v1(...)` against the supplied semantic/frame/epistemic/state snapshots. It then reconstructs the exact `PlayerWindowRequest`, reruns `derive_player_window_v1(...)`, and requires full equality.

```text
selected PR8 frontier
      -> PR8 exact re-derivation verification
stored PR9 source selection
      -> PR9 exact read-model re-derivation
```

This proves deterministic consistency with supplied snapshots, not their authenticity.

```text
VERIFIED WINDOW != AUTHENTICATED SOURCE SNAPSHOT
VERIFIED WINDOW != VIEWER AUTHORIZATION
VERIFIED WINDOW != PUBLICATION PERMISSION
```

## Local HTML product surface

`render_player_window_html_v1(window)` accepts only one already-derived `PlayerWindow` and returns a complete static HTML document.

The renderer is dependency-free and includes:

- embedded CSS only;
- no JavaScript requirement;
- no server;
- no database;
- no analytics/telemetry;
- no remote font, image, stylesheet, or CDN;
- `noindex,nofollow` metadata;
- a restrictive Content Security Policy;
- HTML escaping for every source-derived string.

```text
SOURCE TEXT != TRUSTED HTML
LOCAL HTML != PUBLICATION
RENDERED HTML != VERIFIED WINDOW
```

Rendering does not itself run verification. Callers that need source-backed assurance must validate the Player Window before rendering; the bundled demo does so.

## Civilization Bootstrap local demo

PR9 provides:

```text
python -m capability_lab.player_window.demo --output player_window.html
```

The demo constructs a real bounded Civilization Bootstrap chain:

```text
PR5 Basic Electricity semantics
      -> PR2 evidence / claim / evaluation
      -> PR4 deterministic supported state
      -> PR3 complete multidimensional state
      +  PR7 achievement / milestone / Legend
      +  PR8 verified frontier / evidence gap / explicit exploration
      -> PR9 PlayerWindow
      -> PR9 verification
      -> self-contained local HTML
```

The demo intentionally shows:

- `conceptual_knowledge = SUPPORTED` with scoped claim text;
- `calculation = UNKNOWN` rather than `0`;
- the remaining exact frame dimensions;
- one bounded historical achievement;
- one personal milestone with attributed significance note;
- one source-visible narrative projection;
- `low_voltage_power_distribution` as `Could be considered`;
- an `UNKNOWN` calculation prerequisite evidence gap;
- `potable_water_treatment` as explicit exploration.

## Non-goals

PR9 v1 does not implement:

- Human Level, XP, score, rank, tier, rarity, progression percentage, or leaderboard;
- automatic growth detection or state-comparison semantics;
- automatic latest/current state, Legend, history, or frontier selection;
- domain scores or inferred personal domain membership;
- a recommender, curriculum planner, or path optimizer;
- interactive claim/state/history editing;
- correction/retraction workflow;
- persistence/database/server;
- authentication/authorization/consent system;
- synchronization or publication;
- public profiles;
- HDE adapters;
- model/LLM runtime;
- generic dashboard/component framework;
- source-snapshot signatures/authentication.

## Normative invariants

```text
PLAYER WINDOW != PERSONAL DEVELOPMENT MODEL
PLAYER WINDOW != PERSON
PLAYER WINDOW != CURRENT TRUTH
PLAYER WINDOW != AUTHORITY

PR9 COMPOSES GOVERNED RECORDS
PR9 DOES NOT RE-DERIVE THEIR MEANING
RENDERER != DERIVER

DISPLAYED != CANONICAL
OMITTED != ABSENT
WINDOW SELECTION != IMPORTANCE
WINDOW SELECTION != COMPLETENESS
WINDOW SELECTION != SUBJECT ENDORSEMENT

LATEST STATE != AUTOMATIC WINDOW STATE
LATEST LEGEND != AUTOMATIC WINDOW LEGEND
LATEST FRONTIER != AUTOMATIC WINDOW FRONTIER

SELECTED STATE -> COMPLETE FRAME DIMENSION VISIBILITY
STATE SELECTION != DIMENSION CHERRY-PICKING

SUPPORTED != MASTERED
INSUFFICIENT != LOW
UNKNOWN != ZERO
SUPPORTED + UNRESOLVED != CONFLICT-FREE SUPPORT

STATE DIFFERENCE != GROWTH
MORE SUPPORTED DIMENSIONS != HUMAN PROGRESS SCORE

ACHIEVEMENT != CURRENT READINESS
HISTORY != STATE
SIGNIFICANCE NOTE != SUBJECT ENDORSEMENT

VISIBLE NARRATIVE MUST NOT HIDE ITS SOURCE HISTORY
LEGEND != PERSON IDENTITY

VISIBLE FRONTIER MUST NOT HIDE ITS PERSONAL-STATE BASIS
FRONTIER CANDIDATE != RECOMMENDATION
PREREQUISITE GAP != MISSING CAPABILITY
PREREQUISITE GAP != PROHIBITION
NO GAP != READY
EXPLORATION OPPORTUNITY != RECOMMENDATION

DISPLAY ORDER != PRIORITY
CHRONOLOGICAL ORDER != IMPORTANCE

PLAYER WINDOW != HUMAN LEVEL
PLAYER WINDOW != XP SYSTEM

REQUESTER != AUTHORITY
VIEWER != SUBJECT
VIEWER REF != AUTHORIZATION

STRUCTURALLY VALID WINDOW != VERIFIED WINDOW
DESERIALIZED WINDOW != VERIFIED WINDOW
VERIFIED WINDOW != AUTHENTICATED SOURCE SNAPSHOT

SOURCE TEXT != TRUSTED HTML
LOCAL HTML != PUBLICATION
SERIALIZED WINDOW != SHAREABLE WINDOW
```
