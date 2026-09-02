# PR9 Player Window — Second Adversarial Pass v1

This document records the second adversarial review of PR9 `PlayerWindow` after the first integrity/authority pass and its exact-head local green gate.

The pass does not revisit the first-pass selected-state repair. It attacks the next layer: selected PR7 history/Legend governance, source-snapshot substitution, display-summary provenance boundaries, historical reconstruction limits, rendered-artifact integrity, and privacy/export behavior of the first local HTML product.

## Scope

The pass attacks:

- selected history that is structurally valid but invalid against PR7 family or epistemic governance;
- selected Legend projections that are structurally valid but invalid against PR7 history-source governance;
- unselected invalid history records influencing a selected Player Window;
- same-ref semantic substitution across supplied source snapshots;
- same opaque history ID with substituted projected content;
- historical `PlayerWindow.as_of` being overread as an authenticated historical semantic snapshot;
- PR8 provenance being flattened into presentation text and then treated as a new canonical source;
- verified `PlayerWindow` status being overread as integrity protection for rendered HTML bytes;
- local/no-network HTML being overread as safe-to-share or publication-authorized output;
- accidental inclusion of raw PR2 evidence payload/context in the rendered product.

## Production repair — selected PR7 governance before verified PR9 presentation

The first-pass verifier already validates exactly the selected PR3 states before PR9 re-derivation. The same source-governance rule must apply to selected PR7 records.

`validate_player_window_v1(...)` now constructs an exact selected history subset from:

```text
selected_achievement_ids
selected_milestone_ids
```

and validates that subset with:

```text
PersonalHistoryRecordSet.validate_against_family_catalog(...)
PersonalHistoryRecordSet.validate_against_epistemics(...)
```

If a selected milestone depends on an achievement instance, the selected subset constructor preserves the PR7 closure rule: the source achievement must also be present in the selected visible history set for a verified window.

For an explicitly selected Legend, the verifier constructs an exact one-Legend subset and applies:

```text
PersonalLegendSet.validate_against_history(selected_history_set)
```

before PR9 re-derivation.

Unselected history and Legend records are not included in these selected subsets.

Frozen:

```text
SELECTED PR7 HISTORY GOVERNANCE
PRECEDES
VERIFIED PR9 PRESENTATION

SELECTED LEGEND GOVERNANCE
PRECEDES
VERIFIED PR9 NARRATIVE PRESENTATION

UNSELECTED HISTORY != WINDOW INPUT
UNSELECTED LEGEND != WINDOW INPUT
```

## Selected history consistency is not history authenticity

The repair proves that selected PR7 records satisfy the governing contracts against the supplied snapshots. It does not authenticate those snapshots.

A test constructs two `AchievementFamilyCatalog` snapshots containing materially different family definitions under the same exact family ref and same projected family name. A Player Window derived against one snapshot can still verify against the other because:

```text
EXACT FAMILY REF != CONTENT HASH
EXACT FAMILY REF != SIGNATURE
SUPPLIED FAMILY CATALOG != AUTHENTICATED ARCHIVE
```

This is the same frozen PR7/PR8 source-authenticity boundary, now demonstrated at the product layer.

PR9 must not manufacture an issuer, signature, archive timestamp, or semantic-content digest merely to make the HTML appear stronger than its sources.

## Projected-content substitution is detected

The authenticity limit does not make the verifier useless.

If a supplied selected history record keeps the same opaque achievement ID but changes content that PR9 actually projects, such as `context`, exact re-derivation changes the expected `PlayerWindow` and verification rejects the previously stored window.

Therefore:

```text
SAME OPAQUE HISTORY ID != SAME PROJECTED CONTENT

PROJECTED-CONTENT SUBSTITUTION
!=
VERIFIED PR9 WINDOW
```

The guarantee is deterministic consistency with supplied source objects, not proof of their external origin.

## Legend source replay remains a PR7 error

A structurally valid `PersonalLegend` can contain the same history source in multiple entries until it is checked against a history set. PR7 deliberately places the cross-entry replay rule in `PersonalLegendSet.validate_against_history(...)`.

PR9 now preserves that governance boundary rather than silently presenting the structurally valid but source-replaying Legend.

Frozen:

```text
STRUCTURALLY VALID LEGEND != GOVERNED LEGEND
GOVERNED LEGEND != SUBJECT IDENTITY
```

## Historical `as_of` is a personal-record boundary, not semantic archive proof

`PlayerWindow.as_of` constrains which selected personal records may be represented. It does not add historical timestamps or archive authenticity to PR1/PR3/PR7/PR8 semantic snapshots.

A historical Player Window can therefore be consistently verified against an alternate same-ref semantic snapshot when the changed semantic fields are outside the PR9 projected content and all upstream exact-ref checks still pass.

Frozen:

```text
HISTORICAL PLAYER WINDOW as_of
!=
PROOF OF HISTORICAL SEMANTIC SNAPSHOT

HISTORICAL RECONSTRUCTION
REQUIRES
ARCHIVED SOURCE SNAPSHOTS
```

Authenticated historical replay is a future archive/governance problem, not a PR9 UI feature.

## PR8 display summaries are not a replacement provenance model

PR9 intentionally renders bounded human-readable frontier summaries such as direct-adjacency and prerequisite relation descriptions. These summaries are presentation copies.

The source-visible anchor remains:

```text
selected_frontier_id
+
supplied ProgressionFrontier
+
validate_progression_frontier_v1(...)
```

The Player Window also preserves structured candidate concept refs and typed prerequisite gap frame/state/dimension data. It does not claim that `adjacency_reasons` strings are a lossless serialized PR8 frontier.

Frozen:

```text
DISPLAY SUMMARY != SOURCE FRONTIER
DISPLAY SUMMARY != CANONICAL PROVENANCE
DO NOT PARSE PRESENTATION TEXT AS AUTHORITY
```

A future interactive UI needing richer machine-readable frontier details should consume the verified PR8 source, or introduce an explicit typed display witness, rather than reverse-engineering PR9 strings.

## Verified Window is not verified rendered artifact bytes

`validate_player_window_v1(...)` verifies the `PlayerWindow` object. `render_player_window_html_v1(...)` produces a deterministic representation from that object, but PR9 does not add a content digest or signature over the resulting HTML bytes.

After rendering, arbitrary external mutation of the file is outside the Player Window verifier.

Frozen:

```text
VERIFIED PLAYER WINDOW != SIGNED HTML ARTIFACT
RENDERED HTML != VERIFIED WINDOW
HTML BYTES != SOURCE RECORD
```

No `rendered_html_digest` or `artifact_signature` field is introduced in PR9 v1. Adding an unauthenticated local hash would not prove issuer identity, publication permission, or provenance authenticity.

## Privacy and export boundary

The local HTML renderer is network-silent and self-contained. That prevents automatic remote exfiltration; it does not make the generated file safe to publish or share.

The HTML contains intentionally selected private capability/history/narrative/frontier content. Copying the file is an export of that selected personal projection.

Frozen:

```text
LOCAL != PUBLIC
NO NETWORK REQUEST != SAFE TO SHARE
HTML FILE COPY == DATA EXPORT
VIEWER REF != EXPORT AUTHORIZATION
LOCAL HTML != PUBLICATION PERMISSION
```

PR9 does not implement sharing, publication, consent, access-control, or redaction workflows.

The renderer remains bounded: the Civilization Bootstrap demo regression proves that raw PR2 `EvidenceRecord.summary` and `EvidenceContext.description` are not copied into the HTML. Scoped claim text and other explicitly projected fields may still be private and must be treated accordingly.

## Final second-pass invariant block

```text
SELECTED PR7 HISTORY GOVERNANCE PRECEDES VERIFIED PR9 PRESENTATION
SELECTED LEGEND GOVERNANCE PRECEDES VERIFIED PR9 NARRATIVE PRESENTATION
UNSELECTED HISTORY != WINDOW INPUT
UNSELECTED LEGEND != WINDOW INPUT

STRUCTURALLY VALID HISTORY != GOVERNED HISTORY
STRUCTURALLY VALID LEGEND != GOVERNED LEGEND

SAME OPAQUE HISTORY ID != SAME PROJECTED CONTENT
EXACT FAMILY REF != CONTENT HASH
EXACT FAMILY REF != SIGNATURE
SUPPLIED SOURCE SNAPSHOT != AUTHENTICATED SOURCE SNAPSHOT

HISTORICAL PLAYER WINDOW as_of != PROOF OF HISTORICAL SEMANTIC SNAPSHOT
HISTORICAL RECONSTRUCTION REQUIRES ARCHIVED SOURCE SNAPSHOTS

DISPLAY SUMMARY != SOURCE FRONTIER
DISPLAY SUMMARY != CANONICAL PROVENANCE
DO NOT PARSE PRESENTATION TEXT AS AUTHORITY

VERIFIED PLAYER WINDOW != SIGNED HTML ARTIFACT
RENDERED HTML != VERIFIED WINDOW
HTML BYTES != SOURCE RECORD

LOCAL != PUBLIC
NO NETWORK REQUEST != SAFE TO SHARE
HTML FILE COPY == DATA EXPORT
VIEWER REF != EXPORT AUTHORIZATION
LOCAL HTML != PUBLICATION PERMISSION
```

## Non-goals retained

The second pass does not introduce:

- source-snapshot signatures or authenticated archives;
- content-addressed semantic refs;
- HTML signing or artifact attestation;
- publication/share authorization;
- redaction workflows;
- access control;
- remote hosting;
- telemetry;
- a new canonical frontier provenance representation;
- a generic export framework.

The purpose remains narrow: a first local product projection that preserves upstream governance honestly and states where its guarantees stop.
