# Personal Capability State v1

Status: **PR3 normative representation contract**

PR3 introduces Capability Lab's first private, subject-scoped representation of current supported capability state. It defines what a valid state record may contain and how that record remains linked to governed epistemic material. It deliberately does **not** define the algorithm that derives state from evaluations; the first deterministic derivation policy belongs to PR4.

## Core boundary

```text
CapabilityConceptRef
        |
CapabilityClaim
        |
ClaimEvaluation
        |
        +---- CompetenceFrameRef
        +---- StateDerivationPolicyRef
        +---- StateDeriverRef
        |
        v
PersonalCapabilityState
```

The state layer preserves these distinctions:

```text
MODEL STATE != PERSON
STATE != CAPABILITY
STATE != CLAIM
STATE != EVALUATION

STATE IS DERIVED
STATE IS SUBJECT-SCOPED
STATE IS POLICY-SCOPED
STATE IS TIME-SCOPED
```

`PersonalCapabilityState` never interprets raw `EvidenceRecord` values directly. Its basis is `CapabilityClaim` / `ClaimEvaluation`; evidence remains reachable through the epistemic layer.

```text
STATE DOES NOT INTERPRET RAW EVIDENCE
STATE BASIS MUST PASS THROUGH ClaimEvaluation
```

## Competence frames

Human competence is not assumed to decompose into one universal fixed set of dimensions. PR3 therefore introduces versioned `CompetenceFrame` semantics.

A frame is identified by a stable `CompetenceFrameId` and an exact `CompetenceFrameRef`:

```text
<namespace>:<key>
<namespace>:<key>@<revision>
```

A frame contains one or more `CompetenceDimensionDefinition` records. Each dimension has a machine key, a human name, and an explicit description.

Example fixture:

```text
civilization_bootstrap:technical_competence@1

conceptual_knowledge
calculation
execution
diagnosis
transfer
independence
explanation
```

These keys are meaningful only relative to their exact frame revision.

```text
DIMENSION KEY != GLOBAL HUMAN DIMENSION
DIMENSION IDENTITY = CompetenceFrameRef + dimension_key
COMPETENCE FRAME != UNIVERSAL HUMAN ONTOLOGY
```

Frames do not contain weights, maximum scores, rank, or importance coefficients in v1.

A material persisted change to a frame requires a revision increase. A fundamentally different decomposition should normally use a new frame id rather than silently changing the meaning of an existing lineage.

```text
EXACT FRAME REVISION != LATEST FRAME REVISION
```

`CompetenceFrameRef` is an exact declared revision reference inside its governance regime. It is not a cryptographic content address, truth marker, or proof that the frame is universally correct.

`CompetenceFrameCatalog` is a deterministic shared semantic snapshot. Like `CapabilityCatalog`, it is not the Human Capability Commons and contains at most one current record per frame id.

## Dimension support standing

`CompetenceDimensionState.standing` uses three deliberately non-ordinal support-content states:

- `UNKNOWN`
- `INSUFFICIENT`
- `SUPPORTED`

They are not levels on a mastery ladder.

### UNKNOWN

No governed claim/evaluation basis is represented for the dimension in this state.

An `UNKNOWN` dimension contains neither supported claims nor basis evaluations and cannot declare dimension-level conflict.

```text
UNKNOWN != ZERO
UNKNOWN != NOVICE
```

The absence of a whole state record is different again:

```text
NO STATE RECORD != UNKNOWN STATE RECORD
```

No state record means the subject/concept/frame combination is not represented in this state collection. PR3 does not create implicit UNKNOWN states for every capability that exists.

### INSUFFICIENT

Relevant governed evaluation material exists, but the represented state policy does not accept any scoped claim as supported state content for that dimension.

An `INSUFFICIENT` dimension has at least one basis evaluation and no supported claim ids.

```text
INSUFFICIENT != UNKNOWN
INSUFFICIENT != LOW
```

`INSUFFICIENT` means insufficient basis for **supported state content under this state derivation policy**. It does not mean that all evidence is weak or that the underlying person has low capability.

### SUPPORTED

At least one explicit scoped `CapabilityClaim` is represented as supported content for the dimension, with at least one basis `ClaimEvaluation` whose conclusion for that claim is `SUPPORTED`.

```text
SUPPORTED DIMENSION != MASTERED DIMENSION
```

The semantic content of competence remains in the claim statement and scope. PR3 does not replace those scopes with an arbitrary ordinal such as level 2 or 73%.

## Dimension conflict is an independent axis

PR2 explicitly preserves the invariant:

```text
CONFLICT != SUFFICIENCY
```

PR3 must not undo that separation. Conflict therefore does **not** appear as another `DimensionStanding` value.

`CompetenceDimensionState.conflict_status` is independent from support standing:

- `NONE`
- `RESOLVED_BY_POLICY`
- `UNRESOLVED`

This permits combinations that a single standing enum could not represent honestly:

```text
SUPPORTED    + NONE
SUPPORTED    + RESOLVED_BY_POLICY
SUPPORTED    + UNRESOLVED

INSUFFICIENT + NONE
INSUFFICIENT + RESOLVED_BY_POLICY
INSUFFICIENT + UNRESOLVED
```

For example, a dimension may preserve a narrowly supported claim while another governed evaluation leaves a material conflict unresolved. Conversely, a dimension may have no accepted supported claim content while conflict remains unresolved.

```text
SUPPORTED CONTENT != ABSENCE OF CONFLICT
UNRESOLVED CONFLICT != INSUFFICIENT SUPPORT
CONTRADICTED CLAIM != LOW STATE
```

An `UNKNOWN` dimension has no basis and therefore always uses dimension conflict `NONE`.

`RESOLVED_BY_POLICY` at this layer means resolved by the exact **state derivation policy** identified by `StateDerivationPolicyRef`. It must not be confused with PR2's `ClaimEvaluation.conflict_status`, whose resolution belongs to an evaluation policy for one claim.

Cross-layer validation must not silently hide an unresolved conflict already visible in a basis `ClaimEvaluation`. Multiple evaluations of the same claim with opposing directional conclusions likewise cannot be represented as conflict-free basis material.

PR3 does not attempt to prove every possible semantic conflict between different claim propositions. A future derivation policy may identify dimension-level conflicts whose semantics are not mechanically inferable from PR2 record structure; the explicit state conflict field preserves a place to represent them without conflating them with support standing.

## PersonalCapabilityState

A state record contains:

- immutable `PersonalCapabilityStateId`;
- `CapabilitySubjectRef`;
- exact `CapabilityConceptRef`;
- exact `CompetenceFrameRef`;
- exact `StateDerivationPolicyRef`;
- `StateDeriverRef`;
- `as_of`;
- `derived_at`;
- one `CompetenceDimensionState` per frame dimension after frame validation;
- explanatory rationale.

There is intentionally no field named:

```text
overall_score
mastery
level
rank
percentage
xp
novice
intermediate
expert
```

```text
MULTI-DIMENSIONAL STATE != AGGREGATE LEVEL
NO CANONICAL MASTERY SCORE
```

## Time semantics

`as_of` is the time boundary for the state being represented. No basis evaluation later than `as_of` may affect that state.

`derived_at` records when the state record was actually derived. Historical reconstruction is valid:

```text
as_of      = earlier time
derived_at = later time
```

but `derived_at < as_of` is invalid.

Both constructor times must be timezone-aware and are canonicalized to UTC. State constructors expose state-domain validation errors rather than leaking epistemic implementation errors across the layer boundary.

This distinction lets later derivation policies model recency/current-readiness without storing a mystery `recency_score` in PR3.

```text
RECENCY = epistemic timestamps + as_of + derivation policy
```

## State derivation policy and deriver

`StateDerivationPolicyRef` is distinct from PR2's `EvaluationPolicyRef`.

```text
EVALUATION POLICY != STATE DERIVATION POLICY
```

Evaluation policy governs how evidence bears on one claim. State derivation policy governs how governed claim evaluations are selected and composed into a current state representation.

The ref uses exact `<namespace>:<key>@<revision>` syntax. It is not a content hash, truth marker, license, or authority grant.

`StateDeriverRef` identifies the mechanism that executed the derivation: human, rule, model, hybrid, or external system.

```text
DERIVER != AUTHORITY
MODEL DERIVER != AUTOMATIC TRUTH
```

A deriver ref is an opaque identity interpreted within the relevant storage/import governance. It is not globally authenticated merely because it appears in a state record.

A valid state object is a structurally governed representation, not proof that a workflow authorized or accepted that record. In particular:

```text
VALID STATE RECORD != GOVERNANCE ACCEPTANCE
MODEL-DERIVED STATE != ACCEPTED STATE BY CONSTRUCTION
```

A workflow may explicitly authorize a human, rule, model, hybrid, or external deriver under a state-derivation policy. PR3 does not infer that authorization from the deriver kind or from successful validation/deserialization.

PR3 records policy and deriver identity but implements no derivation algorithm. PR4 introduces the first deterministic baseline.

## State basis

Each dimension separates:

```text
supported_claim_ids
basis_evaluation_ids
```

Supported claim ids answer **what scoped propositions are represented as supported content**.

Basis evaluation ids answer **which governed evaluation records were used by this state representation**.

```text
SUPPORTED CLAIMS != STATE BASIS
```

A supported claim must exist in the epistemic record set, belong to the same subject and exact capability concept revision, and have a basis evaluation for that same claim with `SUPPORTED` conclusion.

Every basis evaluation must belong to the same subject and exact capability concept revision, and its `evaluated_at` must not exceed the state's `as_of` boundary.

PR3 allows a state derivation policy to select or compose evaluations. It does not allow the state layer to invert a contradiction into support without a supporting `ClaimEvaluation`.

```text
STATE POLICY MAY SELECT
STATE POLICY MAY COMPOSE
STATE POLICY MAY NOT INVENT SUPPORTED CLAIM CONTENT
```

One claim or evaluation may contribute to more than one competence dimension. This does not make those entries independent support.

```text
SAME CLAIM IN MULTIPLE DIMENSIONS != INDEPENDENT SUPPORT
SAME EVALUATION IN MULTIPLE DIMENSIONS != INDEPENDENT SUPPORT
```

## Exact semantic validation

`PersonalCapabilityStateSet.validate_against_capability_catalog()` requires the exact concept revision referenced by every state. It never silently replaces `concept@2` with a current `concept@4`.

`validate_against_frame_catalog()` likewise requires the exact frame revision and requires the dimension keys in the state to exactly equal the frame dimension keys.

This makes omission explicit: if `diagnosis` is part of the frame and currently unknown, the state must contain `diagnosis = UNKNOWN` rather than silently omitting it.

```text
FRAME DIMENSIONS == STATE DIMENSIONS
```

Historical state records may exist independently of whatever catalog revision is current. Explicit validation against a supplied current snapshot is intentionally exact.

## One-subject state sets

`PersonalCapabilityStateSet` is private and structurally restricted to exactly one `CapabilitySubjectRef`.

```text
STATE SET = ONE SUBJECT
```

This differs from `EpistemicRecordSet`, which may contain multiple subjects for import and validation workflows. The state layer is intentionally closer to a private personal development model and avoids mixed-subject bundles by default.

A `CapabilitySubjectRef` remains scoped to the identity/import governance interpreting it. Equal opaque strings from independent stores must not be assumed to refer to the same person without explicit identity mapping or a shared identity regime.

Multiple immutable historical or alternative state records for the same subject may coexist as long as their state ids are distinct. PR3 does not assume all future derivation policies are deterministic or that one state is globally canonical person truth.

## Immutability and recomputation

A material state recomputation creates a new immutable state record with a new state id. Existing historical state records are not rewritten in place.

```text
RECOMPUTATION != MUTATION
```

`PersonalCapabilityStateSet` enforces state-id uniqueness within one collection. Persistence and synchronization layers must preserve the stronger cross-snapshot rule that one `PersonalCapabilityStateId` is never reused for materially different state content.

This allows current readiness to change while later achievement/milestone layers preserve historical accomplishment.

## Serialization

PR3 defines two strict schemas:

```text
competence_frames/v1
personal_capability_states/v1
```

Serialization is deterministic and uses canonical UTC timestamps. Deserialization rejects unknown fields, duplicate JSON object keys, malformed enum values, invalid exact refs, non-standard numeric constants, and non-array containers where arrays are required.

Dimension conflict status is serialized explicitly and never inferred from the support standing.

`CompetenceFrameCatalog` ingestion reports malformed shared-frame payloads through `InvalidCompetenceFrame`; person-state collection ingestion uses state-domain errors such as `InvalidStateSet` / `InvalidPersonalCapabilityState` rather than conflating those public boundaries.

```text
SERIALIZABLE != SHAREABLE
```

State remains private by default. Serialization does not imply publication, synchronization, consent, or Commons visibility.

## PR3 non-goals

PR3 deliberately does not implement:

- evidence weighting;
- recency weighting/decay algorithms;
- claim-selection algorithms;
- conflict-resolution algorithms;
- automatic state transitions;
- the PR4 deterministic derivation baseline;
- universal competence levels;
- mastery scores or percentages;
- XP or global human level;
- progression frontier/recommendations;
- prerequisite-gap inference;
- achievements or milestones;
- Player Window projections;
- LLM state authority;
- persistence, synchronization, sharing, or Commons aggregation.

The boundary is:

```text
PR3 = STATE REPRESENTATION
PR4 = FIRST DETERMINISTIC STATE DERIVATION
```
