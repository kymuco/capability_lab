# Architecture

Status: **PR0 architecture boundary refined through PR10.0 Pilot 01 private raw-capture semantics**

Capability Lab separates shared capability semantics, person-scoped evidence and governed claims/evaluations, derived personal state, curated domain semantics, non-authoritative proposals, immutable personal history, deterministic advisory/narrative projections, a deterministic private product read model, and a private raw-pilot capture layer that explicitly stops before evidence materialization.

The central epistemic boundary is:

```text
Raw pilot capture does not directly become EvidenceRecord authority.
Evidence does not directly become capability truth.
Claims do not define the person.
Evaluations do not own personal state.
State does not define the person.
Proposals do not become accepted objects by construction.
History does not become current state by construction.
Legends do not rewrite history.
Progression frontiers do not prescribe goals, readiness, or permission.
Player Window does not become the personal development model or person truth.
Projections do not own state.
Presentation does not become authority.
```

## Core flow

```text
PilotProtocol @ exact revision
          |
          v
 private Pilot 01 workspace
          |
          v
   PilotCaptureRecord
          X no automatic EvidenceRecord / claim / evaluation / state

Source Event / Artifact -> EvidenceRecord --------+
                                                |
CapabilityConceptRef -> CapabilityClaim ---------+--> ClaimEvaluation
                                                |         |
EvaluationPolicyRef -----------------------------+         |
EvaluatorRef ------------------------------------+         |
                                                          v
                                             StateDerivationPolicyRef
                                             StateDeriverRef
                                             CompetenceFrameRef
                                                          |
                                                          v
                                             PersonalCapabilityState
                                                          |
                    explicit selected state dimensions   |
                    + direct accepted relations           |
                    + request-local focus/exploration     |
                                                          v
                                             ProgressionFrontier
                                             /       |        \
                                  FrontierCandidate  |  ExplorationOpportunity
                                                    |
                                       PrerequisiteEvidenceGap
                                                    X no state/history/permission mutation

CapabilityCatalog / EpistemicRecordSet
                |
                | inspected by proposal workflow
                v
        ProposalGeneratorRef
        ProposalGenerationPolicyRef
                |
                v
        CapabilityProposal
                |
                v
          ProposalReview
                |
                X  no implicit apply/materialize/accept

AchievementFamily ---------> AchievementInstance ----+
                                                     |
PersonalMilestoneEvent -------------------------------+--> PersonalHistoryRecordSet
                                                               |
                                                               v
                                                         PersonalLegend
                                                               X no history/state rewrite

explicit selected PR3 state --------------------------+
explicit selected PR7 history / optional Legend ------+
explicit selected verified PR8 frontier --------------+--> PlayerWindow
                                                               |
                                                               v
                                                  local HTML renderer
                                                               X no mutation/publication authority
```

`PilotCaptureRecord` is intentionally upstream of PR2. It is private raw participant material under one frozen protocol/session/workspace context and is not an `EvidenceRecord` by construction. `EvidenceRecord` intentionally does not identify what capability it proves. `CapabilityClaim` is a stable proposition about one subject and one exact `CapabilityConceptRef`; it does not bundle an evidence set or conclusion. `ClaimEvaluation` records how a particular evaluator under an exact evaluation policy interpreted particular evidence relative to that claim.

`PersonalCapabilityState` is a separate immutable derived layer. It records current supported state content under an exact state-derivation policy and exact competence frame without becoming canonical truth about the person.

PR3 defines this representation and its invariants. PR4 provides the first deterministic baseline that derives such state from explicitly selected governed evaluations plus explicit frame-scoped claim-to-dimension bindings. PR5 supplies the first real curated domain snapshot and exact domain competence frame without changing the PR1–PR4 person-state boundaries. PR6 adds a separate immutable proposal/review layer whose candidate objects and review recommendations cannot materialize accepted semantic, epistemic, state, permission, or publication records by construction. PR7 adds shared achievement-family semantics, private person-scoped achievement/milestone history, and source-backed Personal Legend projections while preserving `HISTORY != CURRENT STATE` and `LEGEND != HISTORY`. PR8 adds a deterministic, non-ranking advisory progression layer over explicitly selected supported state dimensions plus direct shared relations, request-local focus, explicit prerequisite checks, and explicit exploration preservation while preserving `COULD BE CONSIDERED != SHOULD DO`. PR9 adds the first deterministic source-visible product read model over explicitly selected PR3/PR7/PR8 records and a dependency-free local HTML renderer while preserving `PLAYER WINDOW != PERSONAL DEVELOPMENT MODEL` and `PRESENTATION != AUTHORITY`. PR10.0 adds a frozen Civilization Bootstrap Basic Electricity pilot protocol, strict raw-capture schema, local private workspace, fail-closed transactional mutation boundary, and deterministic workspace snapshot identity while preserving `PILOT CAPTURE != EVIDENCE`.

## Subject and actor boundary

Person-scoped records refer to a `CapabilitySubjectRef`. The subject is not assumed to be the same actor as the operator, pilot runner operator, evaluator, state deriver, evidence contributor, proposal generator/reviewer, history qualifier/recorder, legend generator, progression requester/deriver, Player Window requester, or Player Window viewer.

```text
CapabilitySubjectRef
      |
      +-- pilot captures / evidence / claims / state / private proposals / history / legends / frontiers / Player Windows about this person

Operator             -> operates workflow
PilotRunnerOperator  -> invokes private capture commands; not evaluator authority
Evaluator            -> evaluates evidence/claims
StateDeriver         -> executes a state derivation policy
Contributor          -> contributes evidence/attestation
ProposalGenerator    -> creates a candidate proposal
ProposalReviewer     -> records a review recommendation
Qualifier            -> records declared achievement qualification context
MilestoneRecorder    -> records an attributed milestone event
LegendGenerator      -> produces a source-backed narrative projection
ProgressionRequester -> supplies explicit request-local frontier/focus/exploration inputs
ProgressionDeriver   -> executes the progression derivation policy
WindowRequester      -> explicitly selects records for one Player Window projection
WindowViewer         -> declared intended viewer context; not authorization
```

One actor may occupy several roles, but authorization must not be inferred merely from role overlap. Capturing a participant response, contributing evidence, evaluating a claim, deriving state, generating/reviewing a proposal, qualifying an achievement, recording a milestone, generating a legend, requesting a progression projection, deriving a frontier, requesting a Player Window, or being named as its viewer does not automatically grant unrestricted access to a subject's private development model or authority to mutate, publish, export, or interpret records beyond the relevant layer.

A subject reference is an opaque record identity, not a person profile, authority grant, capability identifier, or claim about the subject. Equal opaque refs from independent stores require explicit identity mapping or a shared identity regime before they are treated as the same person.

## Shared semantics and competence frames

`CapabilityConcept` is reusable semantic vocabulary. Claims whose interpretation depends on that vocabulary reference an exact `CapabilityConceptRef`, including revision.

PR3 adds `CompetenceFrame`, a shared versioned decomposition used to interpret person-scoped capability state across explicit dimensions. A frame dimension is identified by:

```text
CompetenceFrameRef + dimension_key
```

Dimension keys are not universal human traits. Different domains may use different frames and may reuse the same local dimension key with different meanings.

```text
COMPETENCE FRAME != UNIVERSAL HUMAN ONTOLOGY
EXACT FRAME REVISION != LATEST FRAME REVISION
```

Frames do not contain mastery weights, score ranges, rank, or universal importance coefficients in v1.

## Evidence and evaluation flow

Evidence is stored separately from claims, evaluations, and derived state so later policy changes can reevaluate the same proposition without rewriting historical observations.

```text
source event / artifact / assessment
              |
              v
        EvidenceRecord
              |
              +--------------------+
                                   |
CapabilityConceptRef -> CapabilityClaim
                                   |
                 EvaluationPolicyRef
                 EvaluatorRef      |
                                   v
                           ClaimEvaluation
                                   |
                    governed state derivation
                                   |
                                   v
                      PersonalCapabilityState
```

A failed attempt belongs at the evidence/outcome layer. It must not automatically become a low-capability state. A success likewise does not automatically become mastery.

Tools, collaboration, accessibility accommodations, assistance, reference material, automation, and environmental conditions belong in evidence context where relevant. Their presence changes what may be claimed; it is not automatic disqualification.

Observed evidence context is not the same thing as claim scope. Evaluation determines whether evidence observed under specific conditions bears on a proposition with a stated scope.

Derived evidence preserves source-evidence provenance. Transformations must not silently rewrite source records.

## Epistemic attributes and state dimensions

PR2 preserves distinctions between:

- evidence bearing relative to a claim;
- evidence reliability under an evaluation;
- claim coverage/scope;
- timestamps from which recency can later be derived;
- unresolved or policy-resolved conflict;
- evaluator and exact evaluation policy identity.

A single unexplained `confidence` scalar must not silently replace these concepts.

PR3 preserves a similar separation at the state layer. Each competence dimension has a support-content standing and a separate conflict status:

```text
DimensionStanding
  UNKNOWN
  INSUFFICIENT
  SUPPORTED

DimensionConflictStatus
  NONE
  RESOLVED_BY_POLICY
  UNRESOLVED
```

This is deliberate:

```text
CONFLICT != SUFFICIENCY
SUPPORTED CONTENT != ABSENCE OF CONFLICT
UNKNOWN != ZERO
INSUFFICIENT != LOW
SUPPORTED != MASTERY
```

A dimension may therefore be `SUPPORTED + UNRESOLVED` or `INSUFFICIENT + UNRESOLVED`. PR3 must not collapse unresolved conflict into the support standing.

## State basis and non-authority

`PersonalCapabilityState` does not interpret raw evidence. Its basis passes through `CapabilityClaim` and `ClaimEvaluation`.

```text
EvidenceRecord
      X
      | direct state interpretation forbidden
      v
PersonalCapabilityState
```

Supported state content is expressed through scoped `CapabilityClaim` ids. Every supported claim must have a basis `ClaimEvaluation` with `SUPPORTED` conclusion for the same subject and exact concept revision.

Basis evaluations may also preserve insufficiency, contradiction, abstention, or conflict. An unresolved conflict already visible in basis material must not be silently represented as conflict-free state.

```text
STATE POLICY MAY SELECT
STATE POLICY MAY COMPOSE
STATE POLICY MAY NOT INVENT SUPPORTED CLAIM CONTENT
```

`StateDerivationPolicyRef` is distinct from `EvaluationPolicyRef`:

```text
EVALUATION POLICY != STATE DERIVATION POLICY
```

`StateDeriverRef` identifies the mechanism that executed derivation but does not confer authority. A model deriver is not automatic truth.

Structural validity of a state record is also not, by itself, workflow approval:

```text
VALID STATE RECORD != GOVERNANCE ACCEPTANCE
MODEL-DERIVED STATE != ACCEPTED STATE BY CONSTRUCTION
```

A workflow may authorize a model, rule, human, or hybrid deriver under an explicit state-derivation policy, but the mere ability to construct or deserialize a valid state record does not create that authorization.

## Deterministic derivation baseline v1

PR4 implements one explicit state-derivation policy:

```text
core:deterministic_supported_state@1
```

The baseline consumes an exact `EpistemicRecordSet`, exact `CompetenceFrame`, and a `DeterministicStateDerivationRequest`. The request names the exact selected `ClaimEvaluationId` records and explicit `ClaimDimensionBinding` values that are allowed to influence the run.

```text
PR4 COMPOSES EVALUATIONS
PR4 DOES NOT RE-EVALUATE EVIDENCE

SELECTED EVALUATION != TRUTH
SELECTION != AUTHORITY
```

The baseline does not infer claim-to-dimension placement from text or tags, does not admit every structurally valid evaluation automatically, and does not weight evidence, evaluator identity, evaluation-policy identity, coverage, reliability, recency, or evaluation counts.

For each dimension, selected basis is mapped mechanically to `UNKNOWN`, `INSUFFICIENT`, or `SUPPORTED`. State-level conflict is limited to `NONE` or `UNRESOLVED`; baseline v1 never emits `RESOLVED_BY_POLICY` because it contains no state-level conflict-resolution rule.

A claim bound to multiple dimensions carries the same complete selected evaluation basis into every one of those dimensions. This prevents conflict from being hidden by partitioning one claim's evaluations across dimensions.

Unselected evaluations are inert. Equivalent exact inputs are canonicalized so input ordering cannot change the output. The baseline is stateless: cross-snapshot record-ID immutability and no-ID-reuse remain persistence/import governance responsibilities.

```text
DETERMINISM != CROSS-SNAPSHOT ID IMMUTABILITY
DERIVATION != PERSISTENCE GOVERNANCE
```

## Time and recomputation

State is time-scoped.

`as_of` identifies the historical/current boundary represented by a state record. No basis evaluation later than `as_of` may affect that state.

`derived_at` records when the immutable state record was produced. Historical reconstruction is allowed when `derived_at >= as_of`.

A material recomputation creates a new state record rather than mutating historical state:

```text
RECOMPUTATION != MUTATION
```

This allows current readiness to change without erasing later achievement or milestone history.

PR4 can reproduce the same state only when supplied the same exact material records, exact frame, and canonical request. A stateless derivation function cannot prove that a caller has never reused a `PersonalCapabilityStateId` or that an opaque evaluation ID was never rewritten in another independent snapshot; persistent storage/import layers must enforce those historical identity contracts.

## State collections and exact validation

`PersonalCapabilityStateSet` is structurally one-subject and private by default. `EpistemicRecordSet` may contain multiple subjects for import/validation workflows, but state collections do not mix subject models by default.

State records may exist independently of current semantic snapshots. Explicit validation requires exact revisions:

```text
state concept@2 != current concept@4
state frame@1   != current frame@3
```

Frame validation also requires the state to contain exactly one dimension entry for every dimension in the exact referenced frame. Unknown dimensions are represented explicitly rather than silently omitted.

Multiple immutable historical or alternative state records may coexist. A state id may not be reused for materially different content across persistence snapshots, even though PR3 only enforces uniqueness within one in-memory collection.

## Epistemic snapshots

`EpistemicRecordSet` remains the immutable deterministic PR2 snapshot of evidence records, claims, and evaluations. It validates cross-record identity, provenance, subject isolation, temporal causality, and evaluation references, but it is not a database, publication surface, Commons object, or personal capability state.

A record set may contain more than one subject for import/validation workflows, while cross-subject evidence evaluation and internal derivation remain invalid. Epistemic record IDs denote immutable historical records; later persistence layers must not reuse an ID for materially different content across snapshots.

Historical epistemic records may exist independently of the current `CapabilityCatalog`. Explicit validation against a supplied capability catalog requires an exact concept revision match and never silently substitutes the latest revision. Likewise, an `EvaluationPolicyRef` is an exact declared policy revision label within its governance regime, not a content hash or authority grant.

```text
EPISTEMIC RECORD SET != PERSONAL CAPABILITY STATE
SERIALIZABLE EPISTEMICS != PUBLISHED EPISTEMICS
```

## Provenance boundary

Person-scoped evidence and claims preserve explicit provenance.

Generic provenance source kinds may identify actors, artifacts, external records, systems, evidence records, or claims, but internal epistemic references are layer-restricted:

```text
EvidenceRecord -> EvidenceRecord    allowed
EvidenceRecord -> CapabilityClaim   forbidden
CapabilityClaim -> CapabilityClaim  allowed
CapabilityClaim -> EvidenceRecord   forbidden
```

Evaluated evidence belongs to `ClaimEvaluation`, not to claim identity. Internal derivation is subject-isolated, must not point to a later parent, and must remain acyclic. Provenance steps are ordered history and cannot postdate the record boundary they produce.

```text
PROVENANCE != VALIDITY
PROVENANCE != RELIABILITY
```

For evaluation time, causality follows underlying observation time: an evaluation cannot predate its claim or assessed evidence `observed_at`. A later `recorded_at` is allowed for legitimate historical backfill.

## Relation boundary

Capability graph relations represent different kinds of knowledge and must remain distinguishable.

```text
STRUCTURAL
  specializes / generalizes / overlaps

DEPENDENCY
  requires / supported_by / enabled_by

EMPIRICAL DEVELOPMENT
  commonly_precedes / commonly_cooccurs / transfer_observed_to
```

All stored dependency edges point from the capability being described toward its dependency/supporting capability. `requires` and `enabled_by` are categorical in v1; ordinal weak/moderate/strong strength belongs only to `supported_by`.

Empirical path observations must not silently become prerequisite requirements, causal claims, or optimal-path claims.

## Civilization Bootstrap seed domain boundary

PR5 introduces a deterministic curated semantic snapshot in the `civilization_bootstrap` namespace. Seed v0 contains 63 active `CapabilityConcept` records at semantic revision `@1`, a deliberately sparse 57-edge graph, and the exact domain frame `civilization_bootstrap:technical_competence@1`.

The seed is not a universal curriculum or human ranking. Editorial families are curation/documentation structure and do not become `SPECIALIZES` edges merely to keep a visual tree connected. Only direct semantic narrowing is represented structurally.

```text
EDITORIAL FAMILY MEMBERSHIP != SPECIALIZES
GRAPH GROUPING != SEMANTIC IS-A
CONCEPT EXISTS != SUBJECT HAS CAPABILITY
DEPENDENCY EDGE != PERSONAL CAPABILITY INFERENCE
```

PR5 keeps dependency semantics conservative:

- `SUPPORTED_BY` means scoped material support, not necessity;
- `STRONG SUPPORTED_BY` does not become `REQUIRES`;
- relation strength is edge-local and scope-local, not probability, difficulty, learning priority, node importance, or capability score;
- repeated `RelationScope.key` strings remain relation-local qualifiers and do not establish a global scope registry or automatic comparability;
- chains of support relations do not create transitive required paths or propagate personal state.

```text
RELATION STRENGTH != DIFFICULTY
RELATION STRENGTH != LEARNING PRIORITY
EDGE STRENGTH != NODE STRENGTH
SAME RELATION SCOPE KEY != GLOBAL SCOPE IDENTITY
SUPPORTED_BY PATH != REQUIRED PATH
```

Seed v0 contains no empirical-development relations because curriculum intuition is not provenance-backed development evidence. The exact catalog and competence-frame snapshots round-trip through the frozen strict PR1/PR3 schemas, and equivalent builders serialize deterministically.

The first real vertical integration uses `civilization_bootstrap:basic_circuits@1` through PR2 evidence/claim/evaluation, explicit PR4 dimension binding, and PR3 state. Graph position and dependencies do not create claims, evaluations, or supported dimensions by themselves.

## Capability proposal and review boundary

PR6 introduces immutable `CapabilityProposal` and `ProposalReview` records as a candidate/review layer. Proposal payloads use dedicated candidate specs rather than accepted `CapabilityConcept`, `CapabilityRelation`, or `CapabilityClaim` records.

Supported candidate families are exactly:

```text
CREATE_CONCEPT
REVISE_CONCEPT
SPLIT_CONCEPT
MERGE_CONCEPTS
CREATE_RELATION
CREATE_CLAIM
```

A proposal may be generated by a human, rule, model, hybrid, or external-system mechanism under an exact `ProposalGenerationPolicyRef`. A review likewise records `ProposalReviewerRef`, exact `ProposalReviewPolicyRef`, a timestamp, rationale, and one recommendation verdict:

```text
RECOMMEND_ACCEPT
RECOMMEND_REJECT
REQUEST_REVISION
ABSTAIN
```

These are facts and recommendations, not authority transitions:

```text
PROPOSAL != ACCEPTED OBJECT
CANDIDATE SPEC != CORE RECORD
REVIEWER != AUTHORITY
RECOMMEND_ACCEPT != MATERIALIZATION
MULTIPLE REVIEWS != VOTE
LATEST REVIEW != AUTHORITY
```

`CapabilityProposalSet` is one-scope. Shared proposals cannot contain person-scoped internal PR2 basis; private sets bind to exactly one subject. Internal evidence, claims, and evaluations must remain typed proposal basis refs and preserve subject/privacy checks. Generic relation provenance and `EXTERNAL_ARTIFACT` / `OTHER` basis labels cannot be used to relabel known internal PR2 record IDs and escape those checks.

```text
SHARED TARGET != SHAREABLE PROPOSAL
BASIS KIND LABEL != PRIVACY ESCAPE HATCH
EXTERNAL_ARTIFACT != PUBLIC ARTIFACT
NO INTERNAL MATCH != SHAREABLE
```

Catalog validation is exact-revision aware. Suggested create/split/merge IDs may use only namespaces already present in the supplied catalog; suggestion does not reserve the ID or create namespace authority. Reviews remain attached to exactly one proposal ID and do not transfer to superseding proposals.

Proposal/review policy refs and mechanism refs are opaque declared identities rather than authenticated authority:

```text
POLICY REF != POLICY CONTENT
POLICY REF != AUTHENTICATED POLICY
MECHANISM REF != AUTHENTICATED GLOBAL IDENTITY
```

PR6 serialization accepts one explicit extended ISO-8601 timestamp profile and canonicalizes valid offsets to UTC. Serialization/deserialization preserves proposal facts but does not create acceptance. `CapabilityProposalId` and `ProposalReviewId` uniqueness is enforced within one snapshot only; PR6 is stateless and cannot prove cross-snapshot no-reuse.

```text
SERIALIZED != ACCEPTED
DESERIALIZED != APPROVED
OPAQUE ID != CONTENT HASH
SNAPSHOT-LOCAL UNIQUENESS != GLOBAL UNIQUENESS
RECORD VALIDATION != PERSISTENCE GOVERNANCE
```

PR6 exposes no proposal application/materialization API, persistence engine, policy registry, global ID registry, vote aggregation, model runtime, or publication workflow.

## Achievement, milestone, and Legend history boundary

PR7 separates shared accomplishment semantics, immutable person-scoped historical records, current readiness, and narrative projection.

```text
AchievementFamily -> AchievementInstance

AchievementInstance -------+
PersonalMilestoneEvent -----+--> PersonalHistoryRecordSet
                                      |
                                      v
                                PersonalLegend
```

`AchievementFamily` is shared revisioned accomplishment semantics. An `AchievementInstance` references an exact family revision and records one person-scoped historical accomplishment under an explicit qualification policy/mechanism and event-bearing basis. It is not evidence, a capability claim, current state, XP, or a permanent readiness assertion.

```text
ACHIEVEMENT FAMILY != ACHIEVEMENT INSTANCE
ACHIEVEMENT INSTANCE != PERSONAL CAPABILITY STATE
ACHIEVEMENT INSTANCE != EVIDENCE RECORD
SUPPORTED STATE != ACHIEVEMENT EVENT
CURRENT READINESS LOSS != ACHIEVEMENT ERASURE
```

Every v1 achievement requires at least one event-bearing `EvidenceRecord` or opaque `EXTERNAL_ARTIFACT` basis. PR3 state is not an achievement basis. Inside one history snapshot, the same exact event-bearing basis cannot be replayed as multiple achievement instances of one stable family identity merely by changing achievement id, timestamp, or family revision.

`PersonalMilestoneEvent` is independent personal history. It may record success, failure, decisions, transitions, abandoned paths, or unique events without any `AchievementFamily`. `significance_note` is attributed recorder content, not a scalar importance score or automatic subject endorsement.

```text
ACHIEVEMENT INSTANCE != PERSONAL MILESTONE
MILESTONE != TROPHY
MILESTONE SIGNIFICANCE != GLOBAL IMPORTANCE
RECORDER != AUTHORITY
```

`PersonalHistoryRecordSet` is deterministic, private, and one-subject. Achievement and milestone ids may not collide within the same validated personal snapshot. Known PR2 record ids cannot be relabeled as external/other history basis, and exact history ids cannot be relabeled into PR2 provenance/payload refs to create a `history -> evidence -> history` feedback cycle.

History causality distinguishes event time from record time. Event-bearing evidence must describe an event no later than the historical event, while documentary claims/evaluations may be backfilled later but must exist by the history record's `recorded_at` boundary. A milestone citing an achievement requires both the underlying achievement event and its immutable achievement record to exist by the corresponding milestone boundaries.

`PersonalLegend` is a source-backed narrative projection over achievement/milestone history, not the historical source of truth. Each entry cites only exact history ids; Legend cannot cite PR2 evidence, state, or another Legend directly. Source event time must respect `as_of`, source record time must exist by `generated_at`, and one exact source cannot be amplified across multiple entries of one Legend. Alternative Legends may coexist.

```text
LEGEND != HISTORY
LEGEND != EVIDENCE
LEGEND != CLAIM
LEGEND != STATE
LEGEND != PERSON IDENTITY
LEGEND SOURCE != LEGEND
LEGEND OMISSION != HISTORY DELETION
PERSONAL LEGEND != CANONICAL SELF-NARRATIVE
```

Achievement/milestone/Legend ids are opaque and only snapshot-local. Exact `AchievementFamilyRef` is revision identity, not a content hash, signature, or authenticated archive entry. Deterministic catalog serialization can support future content-addressed archives but does not create authenticity by itself. `MODEL` qualifier/recorder/generator mechanism kind likewise does not grant authority or subject endorsement.

PR7 source history is immutable but does not pretend false history is irretractable. Correction/retraction, effective-history precedence, persistent global id reconciliation, authenticated historical semantic archives, publication, and visibility governance remain future append-only/persistence boundaries rather than in-place mutation APIs.

## Progression frontier and evidence-gap boundary

PR8 introduces the first executable person-scoped advisory progression projection. It consumes accepted shared semantics, an exact competence-frame snapshot, governed epistemic records for validating explicitly selected PR3 states, and an explicit `ProgressionFrontierRequest`. It does not consume raw evidence as a recommendation signal, does not auto-select current/latest state, and does not read PR7 history or Legend as a progression input.

```text
selected SUPPORTED state dimensions
          +
direct one-hop accepted relations
          +
explicit request-local focus
          +
explicit preserved exploration
          |
          v
 ProgressionFrontier
```

The frozen rule policy is:

```text
core:deterministic_progression_frontier@1
```

Only direct `SPECIALIZES`, `REQUIRES`, `SUPPORTED_BY`, and `ENABLED_BY` relations participate in v1 adjacency. Dependency direction remains PR1 direction: the candidate capability is the relation source and the selected supporting/dependency capability is the target. `OVERLAPS` and empirical-development relations are not progression adjacency in this baseline. There is no path search, transitive prerequisite closure, graph distance, centrality, difficulty estimate, or ranking.

```text
PROGRESSION FRONTIER != RECOMMENDATION
FRONTIER CANDIDATE != NEXT REQUIRED STEP
FRONTIER CANDIDATE != READINESS
FRONTIER CANDIDATE != PERMISSION
DIRECT RELATION != OPTIMAL PATH
ONE-HOP FRONTIER != CURRICULUM
MULTIPLE WITNESSES != HIGHER PRIORITY
RELATION STRENGTH != FRONTIER PRIORITY
```

A `FrontierSeedBinding` names one exact selected `PersonalCapabilityStateId` and exact dimension keys. Each selected seed dimension must be `SUPPORTED`, but a supported dimension does not become whole-capability support. `SUPPORTED + UNRESOLVED` remains seedable under PR3 semantics; PR8 does not resolve, rank, or penalize conflict. At most one state for one exact seed concept may be selected per request, preventing state-id-only witness amplification without introducing automatic latest-state choice.

`ProgressionFocus` is request-local advisory input. It is not a persisted Goal, Interest, identity statement, or subject endorsement. An exact selected seed concept cannot simultaneously be focus because seed basis and projected direction remain separate. A genuinely adjacent candidate may also be explicitly focused; the two reasons remain inspectable without becoming score or priority.

Only a real categorical `REQUIRES` relation may produce prerequisite evidence-gap semantics. A `PrerequisiteCheckBinding` explicitly maps one exact candidate/prerequisite/relation-scope tuple to one exact frame and required dimension keys for this request. The mapping is caller-supplied inspectable input, not a global semantic truth or authenticated scope→dimension registry.

```text
SUPPORTED_BY != REQUIRES
STRONG SUPPORTED_BY != PREREQUISITE
RELATION SCOPE != COMPETENCE DIMENSION
PREREQUISITE EVIDENCE GAP != MISSING CAPABILITY
PREREQUISITE GAP != PROHIBITION / ACCESS CONTROL
NO GAP != READY / SAFE / PERMITTED
UNASSESSED PREREQUISITE != SATISFIED PREREQUISITE
```

If a `REQUIRES` relation has no binding, it remains explicit in `unassessed_prerequisites`. A supplied binding with no selected state produces `NO_SELECTED_STATE`; state-backed checks may produce `UNKNOWN` or `INSUFFICIENT` dimension gaps. Partial binding coverage therefore remains visibly partial. Gaps do not remove a candidate from the frontier.

`ExplorationInput` is explicit preservation, not an automatic novelty recommender. Exploration concepts must remain distinct from selected seeds, focus, and already derived candidates. An exploration-only input becomes `ExplorationOpportunity` and does not become a frontier candidate. PR8 takes no previous frontier/history/Legend input, so a prior projection cannot silently feed itself into the next projection.

`ProgressionFrontier` preserves the effective request inputs alongside derived candidates, gaps, and opportunities so a projection can be audited. Strict serialization/deserialization validates deterministic schema and structural object rules only. It does not prove that the object was generated by the frozen derivation.

`validate_progression_frontier_v1(...)` is the explicit source-backed verification boundary: it reconstructs a request from the stored effective inputs, re-runs the frozen PR8 derivation against the supplied `CapabilityCatalog`, `CompetenceFrameCatalog`, `EpistemicRecordSet`, and `PersonalCapabilityStateSet`, and requires exact output equality.

```text
STRUCTURALLY VALID FRONTIER != VERIFIED DERIVATION
DESERIALIZED FRONTIER != VERIFIED DERIVATION
VERIFIED DERIVATION != AUTHENTICATED SOURCE SNAPSHOT
EXACT CONCEPT REF != CONTENT HASH / SIGNATURE
```

Verification proves deterministic consistency with the supplied snapshots. It does not authenticate publisher identity, semantic/frame snapshot provenance, archival timestamps, signatures, or same-ref content across independent stores. Likewise `frontier.as_of` constrains selected personal-state time but does not prove that the supplied semantic/frame snapshots existed in that form at the historical date. Authenticated historical reconstruction remains a future archive/persistence boundary.

`ProgressionFrontierSet` is a deterministic private one-subject collection of alternative frontier projections. Multiple frontiers may coexist; latest does not become authority. PR8 exposes no score/rank/priority/difficulty/readiness/probability, generic recommender, permission engine, task generator, persistence/sync, policy registry, authenticated semantic archive, or Player Window UI.

## Player Window product projection boundary

PR9 introduces the first executable product-facing projection without making a UI or rendered artifact a new semantic/state layer.

```text
explicit selected PR3 states
          +
explicit selected PR7 achievements/milestones
          +
optional selected PR7 Legend
          +
optional selected PR8 frontier
          |
          v
  PlayerWindowRequest
          |
          v
   PlayerWindow
          |
          v
render_player_window_html_v1(...)
```

`PlayerWindowRequest` names exact source IDs and exact subject/time/requester/viewer context. It contains no ranking weights, current/latest selectors, growth thresholds, score fields, inferred goals, or domain priorities. Multiple alternative `PlayerWindow` records may coexist in `PlayerWindowSet`; later generation time does not make one canonical.

Every selected PR3 state is projected with the complete dimensions of its exact `CompetenceFrameRef`. This prevents positive-only dimension cherry-picking. PR9 preserves `UNKNOWN`, `INSUFFICIENT`, `SUPPORTED`, and dimension conflict as separate display semantics rather than translating them to zero, weakness, mastery, or readiness.

Selected source visibility is a product-integrity boundary:

```text
VISIBLE LEGEND MUST NOT HIDE ITS SOURCE HISTORY
VISIBLE FRONTIER MUST NOT HIDE ITS PERSONAL-STATE BASIS
SELECTED MILESTONE HISTORY CLOSURE MUST PRESERVE SELECTED ACHIEVEMENT SOURCES
DISPLAYED != CANONICAL
OMITTED != ABSENT
WINDOW SELECTION != IMPORTANCE / COMPLETENESS / SUBJECT ENDORSEMENT
```

PR9 verification is explicitly layered. `validate_player_window_v1(...)` first builds subsets containing exactly selected PR3 state and validates those records against PR2 epistemics, capability semantics, and exact frame semantics. It then builds exactly selected PR7 history/Legend subsets and validates them against achievement-family, epistemic, and history-source contracts. If a frontier is selected, it is validated through PR8 exact source-backed re-derivation. Finally PR9 reconstructs the effective `PlayerWindowRequest`, re-runs `derive_player_window_v1(...)`, and requires exact output equality.

```text
SELECTED SOURCE MUST SATISFY ITS GOVERNING CONTRACT
UNSELECTED STATE / HISTORY / LEGEND != WINDOW INPUT
STRUCTURALLY VALID WINDOW != VERIFIED WINDOW
DESERIALIZED WINDOW != VERIFIED WINDOW
VERIFIED WINDOW != AUTHENTICATED SOURCE SNAPSHOT
```

Verification proves deterministic consistency with supplied source snapshots. It does not authenticate same-ref source content, source publisher identity, archive timestamp, signatures, or policy content. A historical `window.as_of` scopes selected person records but does not prove that supplied semantic/family snapshots existed in the same form at that date.

PR9 intentionally uses bounded display summaries for some upstream provenance. Human-readable frontier relation summaries are presentation copies; they are not a new canonical provenance format and must not be parsed as authority. Exact source frontier identity and typed source records remain upstream.

```text
DISPLAY SUMMARY != SOURCE FRONTIER
DISPLAY SUMMARY != CANONICAL PROVENANCE
DO NOT PARSE PRESENTATION TEXT AS AUTHORITY
```

The HTML renderer is a leaf layer: it accepts only `PlayerWindow`, not source catalogs/sets, so it cannot choose latest/best/current records or re-derive meaning. It HTML-escapes source text, embeds CSS, uses no JavaScript or remote assets/analytics, carries no server/database requirement, and emits a restrictive CSP. Renderer output is not itself source-backed verification.

```text
RENDERER != DERIVER
SOURCE TEXT != TRUSTED HTML
RENDERED HTML != VERIFIED WINDOW
VERIFIED PLAYER WINDOW != SIGNED HTML ARTIFACT
HTML BYTES != SOURCE RECORD
```

The first product artifact is private local data. Network silence is useful but does not create sharing consent or export authorization. Copying the HTML file exports the selected projection. PR9 therefore adds no public-profile, sharing, redaction, consent, artifact-signature, persistence, or authorization workflow.

```text
LOCAL != PUBLIC
NO NETWORK REQUEST != SAFE TO SHARE
HTML FILE COPY == DATA EXPORT
VIEWER REF != EXPORT AUTHORIZATION
LOCAL HTML != PUBLICATION PERMISSION
```

The bundled Civilization Bootstrap demo exercises the full governed chain and validates the Player Window before rendering:

```bash
python -m capability_lab.player_window.demo --output player_window.html
```

PR9 exposes no Human Level, XP, rank, score, growth metric, inferred domain score, recommender, automatic source selection, server, model runtime, persistence layer, or general UI framework.

## Pilot 01 private raw-capture and transaction boundary

PR10.0 introduces the first real-session input layer without changing PR2 evidence semantics. The frozen `civilization_bootstrap:pilot_01_basic_electricity@1` protocol defines three required text probes and an optional execution probe whose participant-provided text/file captures may be plural.

```text
versioned protocol
      |
      v
private workspace
      |
      v
PilotCaptureRecord / PilotCaptureSet
      X
no automatic EvidenceRecord / ClaimEvaluation / State / Frontier / PlayerWindow
```

A repository-local pilot workspace is permitted only below `<repo>/.local/`, which is git-ignored. Workspace validity is closed-world: exact metadata/protocol/notice, canonical capture JSON, non-symlink internal structure, and exact artifact/capture linkage must all agree. `SUBJECT_PROVIDED` is declared origin, not human-authorship authentication.

The public package/CLI mutation surface routes through `transactional.py`. It validates the complete existing workspace before append, stages initialization/capture material before final publication, refuses overwrite, revalidates post-write state, and never treats a new valid capture as repair for older corruption. Required probes allow at most one capture; the optional execution probe remains plural so real notes/photos/artifacts are not discarded to manufacture a simpler geometry.

Artifact capture spans two final paths, so PR10.0 deliberately does not claim portable two-path atomicity. A process/host crash may leave an orphan artifact directory between the two publications. Such a state fails closed, is not silently journal-recovered into participant history, and blocks further append until explicitly reviewed outside the PR10.0 runner.

Public validation performs two complete reads and computes a domain-separated `snapshot_sha256` over relative workspace shape and exact bytes. If the two reads differ, validation rejects the unstable snapshot. A returned report is not a lock and cannot guarantee that another process will not mutate the workspace after return.

```text
PILOT CAPTURE != EVIDENCE
RUNNER != EVALUATOR
CAPTURE COMPLETENESS != CAPABILITY
INCOMPLETE CAPTURE SET != PARTICIPANT FAILURE

VALID WORKSPACE != AUTHENTICATED SESSION
DECLARED HUMAN ORIGIN != AUTHENTICATED HUMAN AUTHORSHIP
SNAPSHOT SHA-256 != TRUSTED TIMESTAMP
SNAPSHOT SHA-256 != ORIGINALITY
SNAPSHOT SHA-256 != EVIDENCE AUTHORITY

DETERMINISTIC REPLAY != PROOF OF SAME REAL-WORLD EVENT
VALIDATION REPORT != LOCK
```

The first live Pilot 01 session should therefore stop at a validated private raw snapshot. Any `PilotCaptureRecord -> EvidenceRecord` transition belongs to a later explicit reviewed boundary that can be designed from actual session material rather than hidden inside capture tooling.

## Model boundary

Language models and other learned evaluators may interpret evidence and produce proposals or `ClaimEvaluation` records, future model derivers may execute explicit state-derivation policies, PR7 may record model mechanisms for achievement qualification, milestone recording, or Legend generation, a PR8 request may identify a model as the declared progression requester, and a PR9 request may identify a model as the declared Player Window requester. PR10.0 adds no model/generator/evaluator path to its participant-capture runner. Model output does not directly become accepted person truth, subject goal, canonical display selection, or authority.

```text
Pilot 01 participant capture
     X no model generation/evaluation/materialization path in PR10.0

EvidenceRecord + CapabilityClaim
     |
     v
model / evaluator
     |
     v
ClaimEvaluation or CapabilityProposal
     |
 governed state derivation / future governance review
     |
     v
PersonalCapabilityState / future accepted semantic transition

PersonalHistoryRecordSet
     |
     v
model / legend generator
     |
     v
PersonalLegend
     X no history/state rewrite

explicit model-supplied progression request
     |
     v
ProgressionFrontier
     X not subject goal / recommendation / permission

explicit model-supplied Player Window request
     |
     v
PlayerWindow
     X not subject curation / canonical truth / publication authority
```

A model operating as a PR2 evaluator under an exact evaluation policy may produce a real `ClaimEvaluation` for an already-governed claim; that is distinct from a PR6 model proposal for a candidate object. A PR7 record may declare a model qualifier/recorder/generator under an exact policy ref without thereby authenticating the policy, endorsing the record on behalf of the subject, or making the model authoritative. A PR8 `MODEL` requester likewise means only that the model supplied explicit request-local focus/exploration/bindings; it does not mean those inputs are the subject's goals or interests. A PR9 `MODEL` requester means only that the model supplied an explicit record selection for one projection; it does not make the selection subject-authored, complete, current, or publishable. None of these pathways gives the model authority merely because the output is structurally valid or deterministically verified.

Consequential transitions must remain governed, auditable, provenance-preserving, and tied to identifiable exact policies. PR4 intentionally introduces one deterministic baseline without making determinism a permanent architectural requirement. PR6 intentionally stops before materialization rather than inventing an implicit acceptance workflow. PR7 intentionally stops before persistence acceptance, correction/retraction precedence, publication, or authenticated-history governance. PR8 intentionally stops before ranking/recommendation authority, path optimization, permission, persistence, authenticated source snapshots, and UI presentation. PR9 intentionally stops before interactive editing, source mutation, publication/sharing consent, authenticated rendered artifacts, persistence, or a general UI framework. PR10.0 intentionally stops before evidence materialization, grading/evaluation, capability inference, authenticated human provenance, durable multi-process transactions, or automated recovery of ambiguous participant history.

## Personal development model

`PersonalDevelopmentModel` is the private subject-scoped model containing capability states, claims, evidence references, milestones/achievements, and projections relevant to Capability Lab.

The term `Model` is deliberate: this structure is partial, revisable, and not a complete representation of the person.

`PlayerWindow` is only a selected read model over governed source records. It is not the `PersonalDevelopmentModel`, does not claim completeness, and does not own source state/history/frontier records.

Pilot 01 raw captures are upstream private session material, not members of the personal development model by construction. A later reviewed materialization workflow may decide whether selected captures justify PR2 evidence records.

Incidental observation of another person is not sufficient authority to create or retain a persistent `PersonalDevelopmentModel` by default.

## Future commons

A future `HumanCapabilityCommons` may host reusable concepts, relations, aliases, cultural interpretations, competence-frame semantics, achievement families, and bounded aggregate path knowledge.

Personal or provisional concepts require an explicit promotion path before becoming governed shared concepts. Shared Commons membership does not publish a subject's private evidence, raw pilot captures, or personal graph.

Aggregate development paths are descriptive by default. A common path is not automatically required, causal, optimal, or appropriate for a particular subject.

## Privacy and synchronization boundary

Capability Lab is local-first. Private subject-scoped raw pilot captures, evidence, proposals, state, history, Legends, progression frontiers, and Player Windows are private by default.

Pilot 01 workspaces inside the repository must live below ignored `.local/`; copying a workspace is still a data export. Workspace serialization/canonicalization/fingerprinting does not imply human-authorship authentication, consent, publication, sharing, synchronization, evidence status, or capability interpretation.

Serialization does not imply consent, publication, sharing, synchronization, approval, endorsement, authority, verified derivation, or authenticated source provenance. Rendering a local Player Window does not change that boundary. A network-silent HTML artifact is still a copy of selected private projection data; moving/copying it outside the local trust boundary is a data export, not an implied permission transition.

Future encrypted backup, multi-device synchronization, cross-writer ID uniqueness, explicit publication, export consent/redaction, policy-registry authenticity, authenticated historical semantic archives, authenticated rendered artifacts, correction/retraction visibility, authenticated pilot provenance, durable transaction journals, or privacy-preserving aggregation require separate scoped governance. Server presence must not silently imply Commons visibility or third-party access.

## HDE boundary

Capability Lab remains independently testable. It does not own HDE identity, canonical HDE memory, action authorization, companion evolution, or Continuum records.

Future adapters may consume approved records and emit raw pilot inputs only through an explicitly authorized capture workflow, evidence references, proposals, claim evaluations, state inputs, historical candidates, explicit progression requests, Player Window requests, or development projections without bypassing the ownership and review boundaries of either system.

An HDE adapter must not reinterpret a structurally valid Pilot 01 workspace as PR2 evidence or authenticated human provenance merely because the bytes are canonical or the workspace fingerprint is stable.
