# Achievement / Milestone / Legend History v1

Status: **Normative PR7 contract**

PR7 adds a historical development layer without turning history into current capability state, XP, authority, or a canonical narrative about the person.

## Outcome

PR7 introduces:

- shared, revisioned `AchievementFamily` semantics;
- private person-scoped immutable `AchievementInstance` records;
- private `PersonalMilestoneEvent` records that need not map to any shared achievement family;
- private one-subject `PersonalHistoryRecordSet` snapshots;
- derived `PersonalLegend` narrative projections and `PersonalLegendSet` collections.

The central boundaries are:

```text
HISTORY != CURRENT STATE
LEGEND != HISTORY
```

## Achievement family semantics

`AchievementFamily` is shared accomplishment semantics. It is not a statement that any person earned the accomplishment.

An exact family identity is:

```text
AchievementFamilyId + revision
```

represented by `AchievementFamilyRef` using canonical `<namespace>:<key>@<revision>` syntax.

`AchievementCriterion` describes a qualification criterion. It is semantic description, not a point value, weight, threshold, difficulty score, learning prerequisite, or automatic award algorithm.

```text
ACHIEVEMENT FAMILY != ACHIEVEMENT INSTANCE
ACHIEVEMENT FAMILY != CAPABILITY CONCEPT
FAMILY CRITERIA != AUTO-QUALIFICATION ENGINE
CRITERION COUNT != DIFFICULTY
```

Family revisions do not retroactively rewrite the meaning recorded by historical instances. Explicit validation requires the exact family revision supplied by the historical record; silent latest-revision substitution is forbidden.

## Achievement instances

`AchievementInstance` is a person-scoped immutable historical accomplishment. It records:

- exact `AchievementFamilyRef`;
- `CapabilitySubjectRef`;
- `achieved_at` and `recorded_at`;
- exact `AchievementQualificationPolicyRef`;
- `AchievementQualifierRef` and mechanism kind;
- typed qualification basis refs;
- bounded context, optional variant, and optional record note.

Every v1 achievement requires at least one event-bearing `EvidenceRecord` or `EXTERNAL_ARTIFACT` basis. Claims and claim evaluations may additionally participate in qualification, but a current PR3 capability state is not an achievement basis in v1.

```text
ACHIEVEMENT INSTANCE != CAPABILITY
ACHIEVEMENT INSTANCE != CAPABILITY CLAIM
ACHIEVEMENT INSTANCE != PERSONAL CAPABILITY STATE
ACHIEVEMENT INSTANCE != EVIDENCE RECORD

SUPPORTED STATE != ACHIEVEMENT EVENT
CURRENT READINESS != HISTORICAL ACCOMPLISHMENT
CURRENT READINESS LOSS != ACHIEVEMENT ERASURE
```

Historical backfill is valid: an accomplishment may happen before the achievement record is created or before a later claim evaluation confirms its qualification. Internal basis records must nevertheless exist by `recorded_at`, and event-bearing evidence may not describe an observation later than `achieved_at`.

An achievement does not automatically become a PR2 evidence record. Any future transformation from historical achievement into epistemic evidence requires an explicit governed provenance path.

## Qualifier non-authority

`AchievementQualifierRef` may identify a human, rule, model, hybrid, or external system mechanism.

```text
QUALIFIER != AUTHORITY
MODEL QUALIFIER != AUTOMATIC TRUTH
QUALIFICATION POLICY REF != AUTHENTICATED POLICY CONTENT
```

PR7 records declared qualification context. It does not provide a policy registry, signature system, license, permission, or publication authority.

## Personal milestone events

`PersonalMilestoneEvent` preserves person-scoped development history that may be unique and may have no shared `AchievementFamily`.

Milestones may represent success, failure, a decision, a transition, an abandoned path, a first experience, or another event that is meaningful to preserve.

```text
ACHIEVEMENT INSTANCE != PERSONAL MILESTONE
MILESTONE != TROPHY
MILESTONE != CAPABILITY STATE
MILESTONE SIGNIFICANCE != GLOBAL IMPORTANCE
```

An achievement may become an explicit source of a milestone through `MilestoneSourceRef`, but there is no automatic achievement-to-milestone conversion. A milestone may also exist with no source refs when the event is self-contained and does not make a capability assertion.

`significance_note` is attributed narrative metadata, not a scalar importance score or a measure of human value.

## Personal history record set

`PersonalHistoryRecordSet` is a deterministic, private, one-subject source-of-history snapshot containing achievement instances and milestone events.

```text
PERSONAL HISTORY SET != MULTI-SUBJECT DATABASE
SHARED ACHIEVEMENT FAMILY != SHARED PERSONAL ACHIEVEMENT
SERIALIZED HISTORY != PUBLISHED HISTORY
```

Cross-validation against PR2 epistemics preserves subject isolation and typed internal refs. Known private internal evidence/claim/evaluation ids may not be relabeled as `EXTERNAL_ARTIFACT` or `OTHER` to bypass privacy validation.

An unknown external ref remains opaque:

```text
EXTERNAL ARTIFACT != PUBLIC ARTIFACT
NO INTERNAL MATCH != SHAREABLE
```

Record ids are opaque and unique within one snapshot. PR7 does not claim cross-snapshot global no-reuse or content-addressed identity; those remain persistence/import governance responsibilities.

## Personal legend

`PersonalLegend` is a derived narrative projection. It is deliberately separate from `PersonalHistoryRecordSet`.

A legend contains an exact subject, `as_of` boundary, generation time, exact projection-policy ref, generator ref, title, summary, and an authored ordered sequence of `PersonalLegendEntry` values.

Each legend entry may cite only:

- `AchievementInstanceId`;
- `PersonalMilestoneEventId`.

PR7 deliberately does not allow direct legend sources from evidence, claims, evaluations, state, or another legend.

```text
LEGEND != HISTORY
LEGEND != EVIDENCE
LEGEND != CLAIM
LEGEND != STATE
LEGEND != PERSON IDENTITY
LEGEND SOURCE != LEGEND
LEGEND DOES NOT BYPASS HISTORY
```

Source history must exist and its event time must not be later than the legend `as_of` boundary. Historical reconstruction is allowed: a legend may be generated later for an earlier `as_of` boundary.

Legend entry order is authored projection semantics and is therefore not canonicalized by source id. History record sets themselves remain canonically ordered.

A legend may omit history records without deleting them:

```text
LEGEND OMISSION != HISTORY DELETION
LEGEND ORDER != GLOBAL IMPORTANCE
LEGEND NARRATIVE != SOURCE FACT
```

Multiple alternative legends over the same history may coexist. PR7 defines no `canonical_legend`, `true_legend`, or latest-legend-wins rule.

```text
PERSONAL LEGEND != CANONICAL SELF-NARRATIVE
```

## Model narrative boundary

A model may generate a `PersonalLegend` under an exact `LegendProjectionPolicyRef` because the result is a non-authoritative projection over preserved history.

```text
LEGEND GENERATOR != AUTHORITY
MODEL NARRATIVE != HISTORY
MODEL NARRATIVE != PERSON IDENTITY
```

Generating or serializing a legend does not create capability claims, evidence, state, achievements, milestones, permission, or publication authority.

## No score or automatic award surface

PR7 intentionally provides no:

```text
unlock_achievement
auto_award
award_if_state_above
achievement_points
achievement_score
rarity_score
leaderboard
human_level
auto_milestone
legend_to_claim
legend_to_state
legend_to_evidence
```

The absence is intentional:

```text
ACHIEVEMENT COUNT != CAPABILITY SCORE
MILESTONE COUNT != HUMAN PROGRESS SCORE
RARITY != HUMAN VALUE
```

Producing visible badges or history entries must not become the terminal optimization objective of development activity.

## Time and serialization

PR7 constructors require timezone-aware datetimes and canonicalize to UTC.

Strict JSON ingestion accepts exactly:

```text
YYYY-MM-DDTHH:MM:SS[.ffffff](Z|±HH:MM)
```

Valid offsets canonicalize to UTC. Unknown or missing fields, duplicate JSON keys, invalid enums/refs, naive timestamps, non-canonical timestamp syntax, and non-finite JSON constants are rejected.

Independent strict serialization surfaces are provided for:

- `AchievementFamilyCatalog`;
- `PersonalHistoryRecordSet`;
- standalone `PersonalLegend`;
- `PersonalLegendSet`.

Serialization is representation, not governance:

```text
SERIALIZED HISTORY != ACCEPTED PUBLIC HISTORY
DESERIALIZED LEGEND != CANONICAL NARRATIVE
PERSISTED HISTORY != AUTHORITY
```

## State independence

PR7 history does not mutate PR3 or PR4 state and is not an input to PR4 deterministic supported-state derivation v1.

A real Civilization Bootstrap integration uses the same bounded project event for PR2 evidence/claim/evaluation, PR4 state support, and separately qualified PR7 historical accomplishment. A later PR4 projection with no selected basis may become fully `UNKNOWN` while the historical achievement and milestone remain intact.

```text
CURRENT STATE CHANGE != HISTORY MUTATION
ACHIEVEMENT HISTORY != STATE DERIVATION INPUT
```

## Correction and retraction boundary

PR7 v1 makes source history immutable but deliberately does not pretend that a mistaken or fraudulent historical record is forever beyond correction.

```text
IMMUTABLE HISTORY != IRRETRACTABLE FALSEHOOD
READINESS DECAY != ACHIEVEMENT REVOCATION
QUALIFICATION CORRECTION != READINESS DECAY
```

A future append-only correction/retraction governance layer must define correction identity, precedence, effective-history projections, conflicting corrections, and audit provenance. PR7 v1 does not implement hidden mutation or deletion as a substitute for that missing policy.

## Non-goals

PR7 does not add:

- generic event/plugin frameworks;
- achievement proposal types in PR6;
- automatic qualification or award engines;
- state-to-achievement inference;
- achievement-to-evidence inference;
- automatic achievement-to-milestone promotion;
- correction/retraction workflow;
- persistence database, synchronization, publication, or Commons sharing;
- XP, ranks, rarity scoring, leaderboard, tiers, or Human Level;
- frontier/recommendation logic from PR8;
- Player Window UI from PR9.
