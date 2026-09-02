# Player Window Integrity and Authority Adversarial Review v1

Status: **PR9 first adversarial review contract**

This review attacks the first product-facing projection at the boundary where correct
backend records can be misrepresented by source selection, read-model composition,
verification, or local rendering.

The central threat model is:

```text
VALID-LOOKING PRESENTATION
!=
VALID SOURCE-BACKED PROJECTION
```

PR9 must preserve the semantic distinctions already established by PR1–PR8 when those
distinctions become visible to a person.

## Review result

The initial implementation already failed closed on:

- hidden PR8 seed/prerequisite-state basis;
- hidden Legend source history;
- selected-state dimension cherry-picking against the supplied exact frame;
- automatic latest state/Legend/frontier selection;
- score/rank/growth/readiness APIs;
- gap-as-blocked and achievement-as-readiness product language;
- source HTML execution through ordinary HTML/script injection;
- latest-wins semantics in `PlayerWindowSet`.

One source-governance blocker was found and repaired:

> PR9 source-backed verification originally re-derived from the supplied
> `PersonalCapabilityStateSet` without first validating the selected PR3 state records
> against PR2 epistemics and the exact PR1/frame snapshots.

That could let a structurally valid but epistemically inconsistent state be reproduced
by PR9 and therefore appear source-backed merely because both the stored window and the
re-derivation consumed the same corrupted state object.

The verifier now constructs a one-subject subset containing **only explicitly selected
state ids** and applies:

```text
PersonalCapabilityStateSet.validate_against_epistemics(...)
PersonalCapabilityStateSet.validate_against_capability_catalog(...)
PersonalCapabilityStateSet.validate_against_frame_catalog(...)
```

before frontier or Player Window verification.

This preserves both requirements:

```text
SELECTED SOURCE MUST SATISFY ITS GOVERNING CONTRACT
UNSELECTED STATE != WINDOW INPUT
```

## Structural validity vs source-backed validity

`PlayerWindow` intentionally contains enough local invariants to reject obvious source
selection mismatches:

- capability entries must exactly match `selected_state_ids`;
- achievement entries must exactly match `selected_achievement_ids`;
- milestone entries must exactly match `selected_milestone_ids`;
- Legend panel identity must exactly match `selected_legend_id`;
- frontier panel identity must exactly match `selected_frontier_id`.

However a structurally valid window may still contain altered display content. For
example, a concept name can be replaced while keeping the same exact source state id.
That is why strict serialization and dataclass construction are not source verification.

The adversarial regression deliberately creates such a structurally valid display
substitution and requires `validate_player_window_v1(...)` to reject it through exact
re-derivation.

```text
STRUCTURAL CONSISTENCY != SOURCE CONSISTENCY
STRUCTURALLY VALID WINDOW != VERIFIED WINDOW
DISPLAY TEXT != SOURCE AUTHENTICATION
```

The HTML renderer remains a representation leaf. It does not itself authenticate or
verify a window. The bundled local demo verifies before rendering.

```text
RENDERED HTML != VERIFIED WINDOW
RENDERING != VERIFICATION
```

## Hidden frontier basis

A selected frontier may not appear unless every exact personal-state id used as:

- `FrontierSeedBinding.state_id`;
- state-backed `PrerequisiteCheckBinding.state_id`;
- state-backed `PrerequisiteEvidenceGap.state_id`;

is also explicitly selected into the Player Window capability section.

The adversarial test selects the frontier while omitting its state basis and requires
PR9 derivation to reject the request.

```text
VISIBLE FRONTIER
MUST NOT HIDE ITS PERSONAL-STATE BASIS
```

This is inspectability, not readiness or recommendation authority.

## Unverified frontier laundering

A structurally valid `ProgressionFrontier` can be modified after derivation while keeping
its exact id and effective inputs. PR8 already distinguishes such an object from a
verified frontier.

The adversarial regression modifies a frontier's rationale, allows PR9 to structurally
compose it, and then requires `validate_player_window_v1(...)` to reject the resulting
window because PR9 verification first calls the PR8 source-backed verifier.

```text
STRUCTURALLY VALID FRONTIER
!=
VERIFIED PR8 FRONTIER

UNVERIFIED PR8 FRONTIER
!=
VERIFIED PR9 WINDOW
```

PR9 does not erase the PR8 verification boundary merely by projecting frontier content.

## Hidden Legend sources

A selected Legend is not allowed to become visible unless every exact history record
cited by every Legend entry is explicitly selected into the same Player Window history
section.

The adversarial regression selects a valid Legend while omitting its cited achievement
and requires derivation to reject it.

```text
VISIBLE NARRATIVE
MUST NOT HIDE ITS SOURCE HISTORY

LEGEND SOURCE OMISSION
!=
SOURCE IRRELEVANCE
```

## Positive-only / cherry-picked projection

A `PersonalCapabilityState` can be structurally constructed with a subset of frame
dimensions, but Player Window projection requires the selected state dimension-key set
to equal the supplied exact frame's full dimension-key set.

The adversarial regression keeps only the supported dimension and confirms that PR9
refuses to project the state against the full Civilization Bootstrap competence frame.

```text
POSITIVE-ONLY DIMENSION SUBSET
!=
FAITHFUL STATE PROJECTION

SELECTED STATE
->
COMPLETE SUPPLIED FRAME DIMENSION VISIBILITY
```

This does not prove authenticity of the supplied frame snapshot. Same-ref semantic
snapshot substitution remains a separate archive/authentication problem.

## Selected-state conflict and evaluation integrity

PR3 support standing and conflict status are independent axes. A hostile state can be
structurally formed with one supported and one contradicted evaluation for the same
claim while falsely leaving the dimension conflict status as `NONE`.

The repaired PR9 verifier validates the selected PR3 state against the supplied
`EpistemicRecordSet`, causing that hidden cross-evaluation conflict to fail closed.

```text
RE-DERIVABLE FROM CORRUPTED STATE OBJECT
!=
VALID GOVERNED STATE

SELECTED PR3 STATE GOVERNANCE
PRECEDES
VERIFIED PR9 PRESENTATION
```

The compact UI therefore cannot earn verified status by hiding a conflict that PR3
requires to be represented.

## Auto-latest influence

The adversarial regression adds a newer, deliberately partial and invalid **unselected**
state to the source set. The explicitly selected older state produces the same Player
Window, and verification still passes because only selected states enter the scoped
PR3 governance subset.

```text
NEWER STATE != AUTOMATIC WINDOW INPUT
UNSELECTED INVALID STATE != WINDOW FAILURE
LATEST != CURRENT TRUTH
```

This is a deliberate consequence of explicit source selection.

## History / readiness laundering

A history-only Player Window renders achievements under `historical accomplishment` and
the section is labeled `Historical records · not current readiness`.

It does not manufacture readiness state, readiness scores, or `ready for` language from
historical accomplishment.

```text
ACHIEVEMENT != CURRENT READINESS
HISTORY PRESENCE != READINESS
HISTORY COUNT != PROGRESS SCORE
```

## Gap / no-gap authority laundering

The frontier panel keeps PR8 language:

```text
Prerequisite evidence gap
```

and explicitly states that the gap does not mean capability absence, prohibition,
readiness, safety, or permission.

The renderer contains no `Blocked`, `Ready`, or cleared-prerequisite status.

```text
GAP != BLOCKED
NO GAP != READY
NO GAP != SAFE
NO GAP != PERMITTED
```

## Requester and viewer attribution

PR9 permits requester/viewer mechanism kinds including model and external-system
attribution. These are provenance fields only.

The adversarial regression renders a model requester and external-system viewer and
requires them to remain visibly attributed while the page still states that the local
artifact is not authorization.

```text
MODEL REQUESTER != SUBJECT CURATION
VIEWER REF != AUTHORIZATION
VIEWER KIND != ACCESS GRANT
```

PR9 still does not implement authentication, authorization, consent, or sharing policy.

## HTML, CSS and URL-shaped source text

Source content may legitimately contain text that looks like HTML, CSS, a URL, or a
`javascript:` URI. PR9 must not treat such text as executable markup or a network
resource.

All source-derived strings pass through HTML escaping and are inserted only in text
contexts. The static template contains no source-controlled `href` or `src` attributes.

The adversarial regression injects:

```text
</style><style>...</style>
https://evil.example
javascript:alert(1)
```

into a display field and requires it to remain escaped text with no generated external
link/resource attribute.

```text
URL-SHAPED TEXT != LINK
CSS-SHAPED TEXT != STYLE AUTHORITY
SOURCE TEXT != TRUSTED HTML
```

The CSP/no-script/no-remote-resource contract remains defense in depth rather than a
replacement for escaping.

## Alternative Player Windows

Multiple windows for the same subject may coexist. `PlayerWindowSet` canonicalizes only
by opaque window id and exposes no `latest`, `current`, or `canonical` selector.

The adversarial regression includes a later-generated alternative window and requires
both to remain peers.

```text
LATER WINDOW != CANONICAL WINDOW
MULTIPLE WINDOWS != LATEST WINS
WINDOW ORDER != IMPORTANCE
```

## Remaining intentional limits

This pass does not claim to solve:

- authenticity/signatures for capability, frame, history, epistemic, or frontier source snapshots;
- authorization to view/export a Player Window;
- persistence/import reconciliation;
- append-only history correction/retraction;
- authenticated historical semantic archives;
- generic safe HTML sanitization for arbitrary trusted markup, because PR9 accepts source text, not source markup.

Those limits must not be hidden behind the word `verified`.

## Frozen first-adversarial invariants

```text
VALID-LOOKING PRESENTATION != VALID SOURCE-BACKED PROJECTION

SELECTED SOURCE MUST SATISFY ITS GOVERNING CONTRACT
UNSELECTED STATE != WINDOW INPUT

STRUCTURAL CONSISTENCY != SOURCE CONSISTENCY
STRUCTURALLY VALID WINDOW != VERIFIED WINDOW
RENDERED HTML != VERIFIED WINDOW
RENDERING != VERIFICATION

VISIBLE FRONTIER MUST NOT HIDE ITS PERSONAL-STATE BASIS
UNVERIFIED PR8 FRONTIER != VERIFIED PR9 WINDOW

VISIBLE NARRATIVE MUST NOT HIDE ITS SOURCE HISTORY

POSITIVE-ONLY DIMENSION SUBSET != FAITHFUL STATE PROJECTION
SELECTED STATE -> COMPLETE SUPPLIED FRAME DIMENSION VISIBILITY

SELECTED PR3 STATE GOVERNANCE PRECEDES VERIFIED PR9 PRESENTATION

NEWER STATE != AUTOMATIC WINDOW INPUT
UNSELECTED INVALID STATE != WINDOW FAILURE

ACHIEVEMENT != CURRENT READINESS
HISTORY PRESENCE != READINESS

GAP != BLOCKED
NO GAP != READY
NO GAP != SAFE
NO GAP != PERMITTED

MODEL REQUESTER != SUBJECT CURATION
VIEWER REF != AUTHORIZATION

URL-SHAPED TEXT != LINK
CSS-SHAPED TEXT != STYLE AUTHORITY
SOURCE TEXT != TRUSTED HTML

LATER WINDOW != CANONICAL WINDOW
MULTIPLE WINDOWS != LATEST WINS
```
