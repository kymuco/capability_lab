# PR7 Second Adversarial History Review v1

Status: **Normative second adversarial supplement for PR7**

This pass attacks identity, temporal backfill, archive authenticity, narrative-source amplification, and model-qualified history after the first adversarial history-integrity gate.

It does not add a global ID registry, event fingerprinting service, semantic archive service, signature system, qualification authority engine, or correction/retraction workflow.

## 1. Cross-type opaque-ID collisions

PR7 uses typed opaque identifiers:

```text
AchievementInstanceId
PersonalMilestoneEventId
PersonalLegendId
```

Type information prevents many direct API confusions, but the string values may also appear in logs, persistence keys, provenance checks, UI routes, import maps, and other generic infrastructure.

The first implementation enforced uniqueness only inside each record type. Therefore one person snapshot could contain:

```text
AchievementInstanceId("history_01")
PersonalMilestoneEventId("history_01")
```

without failing.

That makes an untyped `history_01` reference ambiguous even though the in-memory Python types differ.

Repair:

- achievement and milestone ID strings may not collide inside one `PersonalHistoryRecordSet`;
- when a `PersonalLegendSet` is validated against history, Legend ID strings may not collide with achievement/milestone IDs in that validated personal snapshot.

```text
TYPED ID != LICENSE FOR SAME-STRING COLLISION
ONE PERSONAL SNAPSHOT -> CROSS-TYPE ID STRINGS MUST BE DISTINCT
```

This is still snapshot-local. PR7 has no global ID registry and does not claim no-reuse across independent stores.

## 2. Repeated-performance and event-window ambiguity

PR2 can represent repeated-performance evidence with an observation window. PR7 achievement replay protection, however, is intentionally based on exact event-bearing basis identity rather than timestamps or inferred window overlap.

The same exact event-bearing basis cannot become two achievements of one stable family merely because the caller changes `achieved_at`:

```text
SAME EVENT BASIS + DIFFERENT achieved_at != TWO ACCOMPLISHMENTS
```

Conversely, equal timestamps do not prove that two distinct event-bearing refs describe the same event:

```text
SAME TIMESTAMP != SAME EVENT
SAME OBSERVATION WINDOW != PROVEN SAME EVENT
```

PR7 therefore does not deduplicate by timestamps, context text, summaries, or overlapping observation windows. Such heuristics would collapse legitimate repeated performances when clocks are coarse or events overlap.

A single `EvidenceRecord` or external artifact may describe multiple real performances. PR7 v1 has no per-performance sub-identity inside one event-bearing basis and therefore fails closed: the same basis cannot manufacture multiple countable achievement instances of one stable family.

Different evidence/artifact refs may still describe the same real event. PR7 cannot prove otherwise without preserved event lineage.

```text
DIFFERENT EVIDENCE IDS != PROOF OF DIFFERENT REAL EVENTS
DIFFERENT ARTIFACT REFS != PROOF OF DIFFERENT REAL EVENTS
EVENT IDENTITY != TIMESTAMP HEURISTIC
```

A future persistence/import layer may introduce explicit event identity or lineage if repeated-performance use requires stronger counting semantics.

## 3. Milestone backfill causality

A milestone has two distinct temporal questions:

1. when did the historical event occur?
2. what documentary material existed when the immutable milestone record was written?

Those must not be conflated.

For event-bearing evidence:

```text
EvidenceRecord.observed_at <= milestone.occurred_at
EvidenceRecord.recorded_at <= milestone.recorded_at
```

For an achievement used as a milestone source:

```text
AchievementInstance.achieved_at <= milestone.occurred_at
AchievementInstance.recorded_at <= milestone.recorded_at
```

The first adversarial implementation checked only `achievement.achieved_at`, which allowed a milestone record to cite an achievement record that would not be created until later.

Repair:

```text
SOURCE ACHIEVEMENT RECORD MUST EXIST BY MILESTONE recorded_at
```

Claims and evaluations are documentary context rather than event-bearing observations. They may therefore be created after the event itself during honest historical backfill, but they must exist by the milestone recording boundary:

```text
CapabilityClaim.created_at <= milestone.recorded_at
ClaimEvaluation.evaluated_at <= milestone.recorded_at
```

This permits:

```text
historical event
    ↓
later documentary claim/evaluation
    ↓
immutable backfilled milestone record
```

while rejecting:

```text
milestone record written
    ↓
future claim/evaluation
    ↓
retroactively inserted as if it existed at recording time
```

Frozen boundary:

```text
EVENT TIME != DOCUMENTARY SOURCE CREATION TIME
HONEST BACKFILL != FUTURE-SOURCE LAUNDERING
```

## 4. Family revision and archive authenticity

PR7 exact refs provide revision identity:

```text
civilization_bootstrap:some_achievement@1
```

They are not content hashes, signatures, or authenticated archive objects.

Two independent catalogs can technically contain different material family semantics under the same exact string ref. Their deterministic JSON snapshots differ, but the ref itself cannot prove which content is authentic.

```text
EXACT FAMILY REF != CONTENT HASH
EXACT FAMILY REF != SIGNATURE
EXACT FAMILY REF != AUTHENTICATED ARCHIVE ENTRY
SAME REF ACROSS STORES != PROOF OF SAME CONTENT
```

This pass intentionally does not add a local SHA field to `AchievementInstance`. A digest would provide content binding only if the system also defines exactly what bytes are hashed, how historical snapshots are retained, how algorithm/version transitions work, and what authority authenticates the digest. A bare hash should not be mistaken for semantic or issuer authenticity.

PR7 already provides deterministic `AchievementFamilyCatalog.to_json()` serialization. A future durable archive can therefore content-address retained snapshots under an explicit archive contract without changing the meaning of `AchievementFamilyRef` itself.

```text
DETERMINISTIC SERIALIZATION ENABLES CONTENT ADDRESSING
CONTENT ADDRESSING != AUTHORITY
CONTENT HASH != SIGNATURE
```

For PR7 v1, historical interpretation still requires retaining the exact semantic snapshot that the historical ref was intended to denote.

## 5. Legend source amplification and repeated citation

A `PersonalLegend` is selective and interpretive, but one underlying history record should not be made to look like multiple independent cited sources merely by repeating it in several entries of the same Legend.

The first implementation prevented duplicate refs inside one `PersonalLegendEntry`, but the same ref could be repeated across several entries.

Repair: within one validated Legend, each exact `LegendSourceRef` may appear in at most one entry.

```text
REPEATED CITATION != MULTIPLE HISTORY SOURCES
ONE SOURCE != N INDEPENDENT SOURCES BY NARRATIVE REPETITION
```

A single entry may still cite multiple distinct history records. Different Legends may independently cite the same history record because alternative projections are expected to coexist.

This repair does not claim that one citation gives one unit of importance. PR7 still exposes no source count score, importance score, narrative weight, or completeness metric.

```text
SOURCE COUNT != IMPORTANCE
SOURCE COUNT != EVIDENCE WEIGHT
LEGEND CITATION != CAPABILITY SUPPORT
```

## 6. Model-qualified history non-authority

`AchievementQualifierRef` may use `HistoryMechanismKind.MODEL`.

That remains intentional.

A model can participate in a declared qualification process under an exact policy ref, just as PR2 can preserve a model evaluation under an evaluation policy. Mechanism kind does not itself grant authority.

```text
MODEL QUALIFIER != AUTHORITY
MODEL QUALIFIER != SUBJECT ENDORSEMENT
MODEL QUALIFIER != AUTOMATIC TRUTH
STRUCTURALLY VALID ACHIEVEMENT != AUTHENTICATED GOVERNANCE ACCEPTANCE
```

`AchievementInstance` intentionally has no:

```text
accepted
is_authoritative
subject_endorsed
authority_score
```

and `AchievementQualificationPolicyRef` has no content hash, signature, or authenticated issuer semantics.

The durable application layer remains responsible for deciding which records are admitted into an authoritative local history store under explicit governance. PR7 core only preserves the declared record semantics and validates its local structural/cross-record invariants.

The same boundary applies to milestone recorders and Legend generators.

## 7. Cross-snapshot identity remains a persistence problem

The new cross-type collision repair applies inside one validated personal snapshot. It does not turn opaque IDs into globally unique identifiers.

```text
LOCAL CROSS-TYPE DISTINCTNESS != GLOBAL ID REGISTRY
OPAQUE ID != CONTENT HASH
SAME ID ACROSS INDEPENDENT SNAPSHOTS != SAME RECORD
```

Import/sync must eventually detect same-ID/different-content conflicts rather than silently choosing latest, oldest, or arbitrary content.

## 8. Frozen second-pass invariants

```text
ACHIEVEMENT ID STRING != MILESTONE ID STRING
LEGEND ID STRING != HISTORY ID STRING
    within one validated personal snapshot

SAME EVENT BASIS + DIFFERENT achieved_at != TWO ACCOMPLISHMENTS
SAME TIMESTAMP != SAME EVENT
DIFFERENT EVENT REFS != PROOF OF DIFFERENT REAL EVENTS

EVENT-BEARING SOURCE EVENT TIME <= MILESTONE occurred_at
SOURCE RECORD TIME <= MILESTONE recorded_at
DOCUMENTARY CLAIM/EVALUATION MAY POSTDATE EVENT
DOCUMENTARY CLAIM/EVALUATION MUST EXIST BY MILESTONE recorded_at

EXACT FAMILY REF != CONTENT HASH
EXACT FAMILY REF != SIGNATURE
DETERMINISTIC FAMILY JSON != AUTHENTICATED ARCHIVE BY ITSELF

REPEATED LEGEND CITATION != MULTIPLE HISTORY SOURCES
ONE LEGEND SOURCE MAY APPEAR IN AT MOST ONE ENTRY OF ONE VALIDATED LEGEND

MODEL QUALIFIER != AUTHORITY
MODEL QUALIFIER != SUBJECT ENDORSEMENT
STRUCTURAL VALIDITY != GOVERNANCE AUTHENTICATION
```

## 9. Non-goals of this second pass

This pass does not add:

- global opaque-ID allocation;
- cross-snapshot collision reconciliation;
- event fingerprints;
- repeated-performance sub-event IDs;
- timestamp/window duplicate heuristics;
- family semantic signatures;
- content-hash fields on historical records;
- authenticated archive issuers;
- policy registry/authentication;
- subject-endorsement workflow;
- Legend fairness/completeness scoring;
- history authority scores;
- correction/retraction records;
- mutable history storage;
- sync or publication governance.
