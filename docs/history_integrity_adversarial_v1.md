# PR7 Adversarial History-Integrity Review v1

Status: **Normative adversarial supplement for PR7**

This review attacks the PR7 history layer after the first exact-head implementation gate. It does not add a mutable history workflow, global registry, policy-authentication service, or correction/retraction engine.

## 1. Historical integrity is not current-state integrity

PR7 preserves a separate history layer:

```text
CURRENT STATE != HISTORY
CURRENT READINESS LOSS != ACHIEVEMENT ERASURE
ACHIEVEMENT != CURRENT READINESS
```

An achievement records an accomplishment under an exact family ref and declared qualification context. It does not assert permanent readiness.

## 2. Retroactive family redefinition

`AchievementInstance.family_ref` is exact and revisioned. Validation against an `AchievementFamilyCatalog` fails closed when the supplied catalog contains the same stable family id at another revision.

```text
FAMILY @1 != FAMILY @2
EXACT FAMILY REF != LATEST FAMILY REF
CURRENT FAMILY CATALOG != HISTORICAL REVISION ARCHIVE
```

PR7 v1 deliberately does not claim that an exact family-ref string is a content hash or globally authenticated semantic identity. A durable system must retain/import the exact semantic snapshot needed to interpret historical refs and must not reuse the same exact ref for materially different content.

```text
EXACT REF != CONTENT HASH
SAME REF ACROSS INDEPENDENT STORES != PROOF OF SAME CONTENT
HISTORICAL INTERPRETATION REQUIRES RETAINED EXACT SEMANTICS
```

A material change to what an accomplishment means should not be disguised as a same-revision edit. Depending on semantic continuity, it requires a new revision or a new stable family identity.

## 3. Qualification-time boundary

PR7 v1 does not introduce a separate mutable qualification-decision object or a second `qualified_at` timestamp. The immutable `AchievementInstance.recorded_at` boundary is the time by which the declared qualification record and all internal qualification basis must exist.

Historical backfill remains valid:

```text
achieved_at < recorded_at
```

A later claim/evaluation may help qualify an earlier accomplishment if it exists by `recorded_at`. A basis created after `recorded_at` is rejected.

```text
ACHIEVEMENT TIME != QUALIFICATION RECORD TIME
LATE REVIEW != RETROACTIVE EVENT TIME
BASIS AFTER recorded_at != VALID QUALIFICATION BASIS
```

PR7 does not claim to preserve a separate earlier moment at which a human or model privately reached the decision before the immutable record was written. A future workflow may add such an event if that distinction becomes operationally necessary.

## 4. Blocker repair — achievement replay

The first implementation allowed two different `AchievementInstanceId` records to reuse the same event-bearing `EvidenceRecord` or `EXTERNAL_ARTIFACT` basis for the same stable `AchievementFamilyId`.

That could inflate history without a second distinguishable accomplishment.

Repair: within one `PersonalHistoryRecordSet`, the same exact event-bearing basis ref cannot be reused by multiple achievement instances of one stable family identity, even across family revisions.

```text
NEW ACHIEVEMENT ID != NEW ACCOMPLISHMENT
SAME EVENT BASIS + SAME STABLE FAMILY != TWO ACHIEVEMENTS
REPLAYED BASIS != REPEATED ACCOMPLISHMENT
```

The same event may still legitimately support different achievement-family identities. If one evidence record describes several distinct repeated events, PR7 v1 has no per-event disambiguator and therefore fails closed rather than manufacturing countable instances.

This guarantee is snapshot-local. Replaying the same event in two independently assembled snapshots cannot be detected without persistence/import reconciliation.

## 5. Milestone significance is attributed content, not authority

`PersonalMilestoneEvent.significance_note` is part of the immutable record attributed to its `MilestoneRecorderRef` and recording policy.

It is not automatically a statement endorsed by the subject and is not a scalar importance measurement.

```text
SIGNIFICANCE NOTE != SUBJECT ENDORSEMENT
RECORDER != AUTHORITY
MODEL-RECORDED SIGNIFICANCE != SUBJECT-ASSERTED SIGNIFICANCE
MILESTONE SIGNIFICANCE != GLOBAL IMPORTANCE
```

PR7 intentionally exposes no `importance_score`, prestige tier, milestone points, or canonical significance rank.

## 6. Blocker repair — future-record Legend laundering

The first implementation enforced:

```text
source event time <= legend.as_of
```

but did not require the cited history record to exist by the time the Legend was generated. That allowed a Legend with `generated_at=2026` to cite a milestone recorded in 2027 as long as the milestone described an earlier event.

Repair: a Legend source must satisfy both:

```text
source achieved_at/occurred_at <= legend.as_of
source recorded_at <= legend.generated_at
```

This still permits honest historical reconstruction. A milestone that happened in 2024, was backfilled in 2026, and is used by a Legend generated in 2027 with `as_of=2024` is valid.

```text
AS_OF != KNOWLEDGE-AVAILABLE-AT
HISTORICAL BACKFILL != FUTURE-RECORD LAUNDERING
```

## 7. Selective-history distortion

A `PersonalLegend` is intentionally selective. Different valid Legends may choose different subsets and orderings from the same underlying history.

```text
LEGEND != COMPLETE HISTORY
LEGEND OMISSION != HISTORY DELETION
LEGEND SELECTION != GLOBAL IMPORTANCE
LEGEND ORDER != GLOBAL IMPORTANCE
PERSONAL LEGEND != OFFICIAL SELF-NARRATIVE
```

PR7 can validate that every Legend entry cites real history and respects time boundaries. It cannot prove that natural-language narrative is fair, complete, emotionally appropriate, or free of framing bias.

Those are projection/review/UI concerns, not facts derivable from local source-reference validation.

No `canonical_legend`, `official_legend`, latest-wins rule, or completeness flag is inferred by core PR7.

## 8. Blocker repair — history-to-evidence feedback

`AchievementInstance`, `PersonalMilestoneEvent`, and `PersonalLegend` are not PR2 evidence records.

The first implementation nevertheless permitted an opaque history id to be copied into a generic PR2 provenance/payload ref. That allowed a cycle such as:

```text
AchievementInstance
        ↓ relabeled as ARTIFACT
EvidenceRecord
        ↓ achievement basis
AchievementInstance
```

Repair: when PR7 history is cross-validated against a supplied `EpistemicRecordSet`, exact achievement/milestone ids may not appear as evidence or claim provenance source refs, and may not appear as evidence payload refs.

```text
HISTORY RECORD != EVIDENCE SOURCE BY RELABELING
HISTORY ID != GENERIC ARTIFACT ESCAPE HATCH
HISTORY -> EVIDENCE -> HISTORY != VALID PR7 CYCLE
```

This is intentionally snapshot-local. PR7 cannot detect someone exporting history text to a new external artifact id and later importing that new artifact as evidence without preserved lineage. Such provenance laundering belongs to future persistence/import governance.

## 9. Cross-snapshot ID reuse

Achievement, milestone, and Legend ids are opaque identifiers with uniqueness enforced inside their corresponding snapshot collections.

They are not content hashes and PR7 has no global registry.

```text
SNAPSHOT-LOCAL UNIQUENESS != GLOBAL UNIQUENESS
OPAQUE HISTORY ID != CONTENT HASH
SAME ID ACROSS SNAPSHOTS != SAME MATERIAL RECORD
```

A future durable store/import/sync layer must prevent historical id reuse for materially different content and reconcile collisions explicitly.

## 10. Correction and retraction pressure

PR7 history records are immutable, but immutability does not mean that a false or fraudulently qualified record can never be corrected.

```text
IMMUTABLE HISTORY != IRRETRACTABLE FALSEHOOD
READINESS DECAY != ACHIEVEMENT RETRACTION
QUALIFICATION CORRECTION != CURRENT-STATE CHANGE
```

PR7 v1 deliberately does not define `HistoryCorrection`, `AchievementRetraction`, effective-history precedence, deletion, or in-place mutation.

A future correction/retraction layer should be append-only and provenance-preserving. It must distinguish at least:

- the historical event actually did not happen;
- the event happened but did not satisfy the declared family/policy;
- later evidence changed current readiness only;
- the record payload itself was entered incorrectly;
- a privacy/removal policy affects visibility without pretending the event never occurred.

Until that governance exists, core PR7 exposes no `revoke_achievement`, `delete_achievement`, `correct_history_in_place`, or equivalent shortcut.

## 11. Frozen adversarial invariants

```text
NEW ID != NEW ACCOMPLISHMENT
REPLAYED EVENT BASIS != REPEATED ACCOMPLISHMENT

EXACT FAMILY REF != LATEST FAMILY REF
EXACT FAMILY REF != CONTENT HASH
CURRENT FAMILY CATALOG != HISTORICAL REVISION ARCHIVE

recorded_at IS THE PR7 v1 QUALIFICATION-RECORD BOUNDARY
BASIS AFTER recorded_at != VALID QUALIFICATION BASIS

SIGNIFICANCE NOTE != SUBJECT ENDORSEMENT
MODEL-RECORDED SIGNIFICANCE != SUBJECT-ASSERTED SIGNIFICANCE

LEGEND != COMPLETE HISTORY
LEGEND OMISSION != HISTORY DELETION
LEGEND SELECTION != GLOBAL IMPORTANCE

SOURCE EVENT TIME <= LEGEND as_of
SOURCE RECORD TIME <= LEGEND generated_at

HISTORY RECORD != EVIDENCE RECORD
HISTORY ID != EVIDENCE/PROVENANCE ESCAPE HATCH
HISTORY -> EVIDENCE -> HISTORY != VALID CYCLE

SNAPSHOT-LOCAL UNIQUENESS != GLOBAL UNIQUENESS
OPAQUE HISTORY ID != CONTENT HASH

IMMUTABLE HISTORY != IRRETRACTABLE FALSEHOOD
CORRECTION/RETRACTION != IN-PLACE MUTATION
```

## 12. Non-goals of this repair pass

This adversarial pass does not add:

- a historical semantic archive service;
- family-ref content hashing or signatures;
- a qualification workflow engine;
- global event identity/fingerprinting;
- a cross-snapshot ID registry;
- semantic duplicate detection across differently named external artifacts;
- natural-language Legend truth/fairness scoring;
- subject-endorsement workflow;
- correction/retraction precedence;
- persistence transactions;
- sync reconciliation;
- publication or public-profile governance.
