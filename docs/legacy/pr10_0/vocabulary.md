# Vocabulary

Status: **PR0 vocabulary refined through PR10.0 Pilot 01 private raw-capture and transaction semantics**

This vocabulary separates shared semantics, person-scoped raw pilot capture, evidence, reviewable propositions, governed evaluations, derived state, curated domain semantics, non-authoritative proposals/reviews, immutable personal history, narrative/advisory projections, and a deterministic private product read model.

A recurring rule applies throughout the project:

```text
PILOT CAPTURE != EVIDENCE
PILOT RESPONSE != CLAIM
RUNNER != EVALUATOR
EVIDENCE != CAPABILITY
CLAIM != CAPABILITY
EVALUATION != CAPABILITY
MODEL STATE != PERSON
PROPOSAL != ACCEPTED OBJECT
HISTORY != CURRENT STATE
LEGEND != HISTORY
PROGRESSION FRONTIER != RECOMMENDATION
PLAYER WINDOW != PERSONAL DEVELOPMENT MODEL
PRESENTATION != AUTHORITY
```

## CapabilitySubject
The person about whom person-scoped raw pilot captures, evidence, capability claims, state, milestones, achievements, Legends, progression frontiers, Player Windows, or a development model refer.

PR2 represents this role through an opaque `CapabilitySubjectRef`, and PR10.0 reuses the same ref type for one private pilot workspace/capture set. A subject reference is not a person profile, capability identifier, authenticated identity, or authority grant. Equal opaque refs from independent stores do not automatically prove common real-world identity without explicit identity mapping or shared identity governance.

The `CapabilitySubject` is not assumed to be the same actor as the software operator, pilot runner operator, evaluator, state deriver, evidence contributor, proposal generator/reviewer, achievement qualifier, milestone recorder, Legend generator, progression requester/deriver, Player Window requester, or Player Window viewer. One actor may hold multiple roles in a workflow, but implementations must keep those roles distinguishable for authorization and provenance.

## CapabilityConcept
A reusable semantic concept describing a capability that can potentially be evidenced in identifiable contexts. It contains no assertion that a particular person has that capability.

A `CapabilityId` identifies the stable concept lineage within its namespace governance. A `CapabilityConceptRef` identifies one exact declared revision of that lineage. Neither is canonical truth about a person, and neither is a cryptographic content address.

A concept must not silently encode total human value, identity, intelligence, morality, desirability, or social status as if those were bounded capabilities.

## CapabilityRelation
A typed relation between `CapabilityConcept` records. Relation semantics must be explicit and must distinguish different kinds of knowledge.

PR1 relation families are:

- **structural** — `specializes`, `overlaps`; `generalizes` is the inverse view of `specializes`;
- **dependency** — `requires`, `supported_by`, `enabled_by`;
- **empirical development** — `commonly_precedes`, `commonly_cooccurs`, `transfer_observed_to`.

All dependency edges point from the capability being described to the dependency/supporting capability. `requires` and `enabled_by` are categorical in v1; ordinal weak/moderate/strong strength is reserved for `supported_by`. Dependency relations may carry relation-local context/scope. Empirical development relations require provenance and must not silently become prerequisites, causal claims, or claims that a common path is an optimal path.

## RelationStrength
The edge-local qualitative strength attached only to a `SUPPORTED_BY` relation in semantics v1: `WEAK`, `MODERATE`, or `STRONG` (plus `UNSPECIFIED` where no graded support is declared).

Its ordering describes the strength of that direct scoped support assertion. It is not probability, necessity, difficulty, learning priority, human importance, node centrality, or a capability score. A `STRONG SUPPORTED_BY` relation remains non-categorical and does not become `REQUIRES`.

```text
EDGE STRENGTH != TARGET CAPABILITY STRENGTH
EDGE STRENGTH != SOURCE CAPABILITY STRENGTH
STRONG SUPPORTED_BY != REQUIRES
```

## RelationScope
A relation-local qualifier describing the bounded context in which a dependency assertion is intended to hold.

Equal `RelationScope.key` strings on different relations do not create a global scope identity, policy object, or automatic cross-edge comparability. PR5 deliberately reuses authoring keys such as `conceptual_analysis` and `bench_validation` while preserving each complete relation as the semantic unit.

```text
SAME RELATION SCOPE KEY != GLOBAL SCOPE IDENTITY
SUPPORTED_BY PATH != REQUIRED PATH
```

## Civilization Bootstrap Seed v0
The first curated real-domain semantic snapshot, implemented by PR5 in the `civilization_bootstrap` namespace.

It contains 63 active capability concepts at semantic revision `@1`, a deliberately sparse 57-edge structural/dependency graph, and the exact domain competence frame `civilization_bootstrap:technical_competence@1`. The pack label `v0` identifies the curated seed snapshot and is distinct from each concept's exact semantic revision.

The seed is a revisable semantic hypothesis, not a universal curriculum, complete civilization ontology, global human/generalist score, professional authority model, or empirical learning-path dataset. Editorial family membership is documentation/curation structure and is not encoded as `SPECIALIZES` unless a genuine narrower/broader capability relation is defensible.

```text
SEED PACK v0 != CAPABILITY CONCEPT @1
EDITORIAL FAMILY MEMBERSHIP != SPECIALIZES
CONCEPT EXISTS != SUBJECT HAS CAPABILITY
DEPENDENCY EDGE != PERSONAL CAPABILITY INFERENCE
```

PR5 contains no empirical-development relations because curriculum intuition is not provenance-backed development evidence. Its real `basic_circuits@1` integration still requires explicit PR2 claims/evaluations and PR4 claim-to-dimension binding before any PR3 personal state is supported.

## EvidenceRecord
A person-scoped record of an observation, artifact, assessment, attestation, outcome, or demonstration.

An `EvidenceRecord` intentionally contains no capability mapping. Evidence does not know what it proves: the same observation may support one claim, contradict another, and be indeterminate for a third.

Evidence kind describes how the observation arose; it does not assign reliability. Reliability is claim-relative evaluation metadata, not an intrinsic score on the record.

Evidence context may include tools, assistance, accessibility accommodations, collaboration, reference material, automation, environmental conditions, and other factors relevant to later interpretation. Those factors are context, not automatic penalties.

Evidence outcome may describe success, partial outcome, failure, or not-applicable status. Success is not mastery and failure is not a capability level.

Point evidence uses `observed_at`. A bounded observation series may additionally use `observation_started_at`, with `observed_at` as its terminal/latest represented observation. `REPEATED_PERFORMANCE` requires this explicit start so longitudinal evidence does not silently collapse into one ambiguous timestamp.

## ProvenanceTrail
A trace of where an epistemic record came from and which explicit transformation steps produced it.

Provenance sources may identify actors, artifacts, external records, systems, source evidence, or claims, but internal epistemic derivation is layer-restricted: evidence may derive only from evidence and claims may derive only from claims. Evaluated evidence belongs to `ClaimEvaluation`, not claim provenance.

Internal derivation is subject-isolated and causal. Internal parents must exist before their derived record, transformation steps cannot begin before an explicitly referenced internal parent existed, and same-layer provenance graphs must remain acyclic. Cycle validation is iterative rather than dependent on Python recursion depth.

Derived evidence preserves its source evidence instead of overwriting it. Provenance is not validity, reliability, truth, or a tamper-proof guarantee.

## CapabilityClaim
A stable, reviewable proposition about a `CapabilitySubjectRef` and one exact `CapabilityConceptRef` under an explicit `ClaimScope`.

A claim is not the capability itself, is not an evidence bundle, and contains no support verdict. The same claim may be evaluated repeatedly as evidence changes or under different policies without changing the proposition identity.

Observed evidence context is distinct from claim scope. Evaluation determines whether evidence observed under specific conditions bears on the proposition's stated scope.

Historical claims retain their exact concept revision. A claim referring to `concept@2` must not silently upgrade to `concept@4` merely because a later catalog is current.

## EvaluationPolicyRef
An exact, versioned reference identifying the policy under which a `ClaimEvaluation` was produced. PR2 uses canonical `<namespace>:<key>@<revision>` syntax.

Policy identity is not truth. An `EvaluationPolicyRef` is an exact declared revision within its policy namespace governance, not a cryptographic content hash or authority grant. Different policies may legitimately yield different governed evaluations from the same underlying evidence while preserving their provenance.

## EvaluatorRef
An explicit reference identifying the evaluator mechanism for a `ClaimEvaluation`: human, rule, model, or external system.

The ref is opaque within the record/import governance that interprets it; it is not globally collision-proof or authenticated merely because it is present. Evaluator identity does not itself confer authority. In particular, a model-generated evaluation does not directly become accepted personal capability state.

## EvidenceAssessment
A claim-relative interpretation of one `EvidenceRecord` within one `ClaimEvaluation`.

It separates:

- evidence bearing — supports, contradicts, indeterminate, or not relevant;
- qualitative evidence reliability — unassessed, low, moderate, or high;
- a coverage note;
- rationale.

Evidence reliability is not probability, claim support, coverage, or recency.

## ClaimEvaluation
A governed record of how specified evidence bears on one `CapabilityClaim` under one exact `EvaluationPolicyRef` and one `EvaluatorRef`.

PR2 conclusions are `SUPPORTED`, `CONTRADICTED`, `MIXED`, `INSUFFICIENT`, and `ABSTAINED`. Coverage and conflict status remain separate fields instead of being collapsed into an unexplained confidence scalar.

Conflicting evidence remains visible. Supporting and contradicting assessments cannot silently coexist under `ConflictStatus.NONE`. `RESOLVED_BY_POLICY` requires actual conflict and a directional `SUPPORTED` or `CONTRADICTED` conclusion. `UNRESOLVED` also requires actual directional conflict, but it may conclude `MIXED`, `INSUFFICIENT`, or `ABSTAINED`; conflict therefore does not imply sufficiency.

A `ClaimEvaluation` is not `PersonalCapabilityState`. PR2 records epistemic interpretation; PR3 defines derived current-state representation.

## EpistemicRecordSet
An immutable deterministic snapshot of `EvidenceRecord`, `CapabilityClaim`, and `ClaimEvaluation` records with cross-record validation.

It rejects duplicate record IDs, dangling evaluation references, evidence/claim subject mismatches, invalid cross-layer provenance, dangling or future-pointing internal parents, provenance cycles, impossible transformation timing, and evaluations that predate their claim or assessed observations. It is not a database, publication surface, Commons object, or personal capability state.

Historical record sets may exist without the current capability catalog. Explicit catalog validation requires an exact concept revision match and never silently substitutes the latest revision.

The record set only enforces ID uniqueness within one snapshot. Persistent storage and synchronization must later preserve the stronger contract that a historical record ID is never reused for materially different content across snapshots.

Serialization of an `EpistemicRecordSet` does not imply consent, publication, synchronization, or shareability. Person-scoped epistemic records remain private by default.

## CompetenceFrame
A reusable, versioned semantic decomposition used to represent capability state across explicit dimensions without asserting one universal decomposition of human competence.

A stable `CompetenceFrameId` identifies the frame lineage and an exact `CompetenceFrameRef` identifies one declared revision. A frame ref is not a content hash, authority grant, or proof that the decomposition is objectively unique.

Each `CompetenceDimensionDefinition` has a frame-local key, name, and description. Dimension identity is:

```text
CompetenceFrameRef + dimension_key
```

The same key may have different semantics in different frames. PR3 frames contain no weights, mastery thresholds, score ranges, or universal importance coefficients.

`CompetenceFrameCatalog` is a deterministic current semantic snapshot with at most one current revision per frame id. Historical state may still refer to an older exact frame revision and must not silently upgrade to the catalog's latest revision.

## DimensionStanding
The support-content status of one `CompetenceDimensionState`.

PR3 values are:

- `UNKNOWN` — no governed basis represented for this dimension;
- `INSUFFICIENT` — governed basis exists but no scoped claim is accepted as supported state content under the state derivation policy;
- `SUPPORTED` — at least one explicit scoped claim is represented as supported state content and has a basis `ClaimEvaluation(SUPPORTED)`.

These values are deliberately non-ordinal:

```text
UNKNOWN != ZERO
INSUFFICIENT != LOW
SUPPORTED != MASTERY
```

## DimensionConflictStatus
The dimension-level conflict status represented independently from `DimensionStanding`.

PR3 values are:

- `NONE`;
- `RESOLVED_BY_POLICY`;
- `UNRESOLVED`.

This preserves the PR2 invariant:

```text
CONFLICT != SUFFICIENCY
```

A dimension may therefore be `SUPPORTED + UNRESOLVED` or `INSUFFICIENT + UNRESOLVED`. `UNKNOWN` has no basis and therefore cannot declare conflict.

At the state layer, `RESOLVED_BY_POLICY` refers to resolution by the exact `StateDerivationPolicyRef`, not by the PR2 evaluation policy of an individual `ClaimEvaluation`.

## CompetenceDimensionState
The state-layer representation of one exact frame dimension for one capability state.

It contains:

- frame-local `dimension_key`;
- `DimensionStanding`;
- independent `DimensionConflictStatus`;
- scoped `supported_claim_ids`;
- `basis_evaluation_ids`;
- rationale.

The same claim or evaluation may contribute to multiple dimensions, but repetition across dimensions does not create independent evidentiary support.

## StateDerivationPolicyRef
An exact versioned reference identifying the policy under which governed `ClaimEvaluation` records are selected and composed into `PersonalCapabilityState`.

It is distinct from `EvaluationPolicyRef`:

```text
EVALUATION POLICY != STATE DERIVATION POLICY
```

The ref is not a content hash, truth marker, license, permission, or authority grant. PR3 records the ref on state; PR4 implements the first concrete deterministic policy, `core:deterministic_supported_state@1`.

## StateDeriverRef
An opaque reference identifying the mechanism that executed state derivation: human, rule, model, hybrid, or external system.

A deriver reference is interpreted within its storage/import governance and is not globally authenticated merely because it is present.

```text
DERIVER != AUTHORITY
MODEL DERIVER != AUTOMATIC TRUTH
```

PR4's baseline identifies itself as a rule deriver; that mechanism identity does not grant workflow authority or acceptance.

## ClaimDimensionBinding
A PR4 derivation input that explicitly maps one `CapabilityClaimId` to one or more dimension keys in the exact `CompetenceFrameRef` named by the derivation request.

A binding is not stored on `CapabilityClaim`, is not inferred from claim text or tags, and is not evidence, support, or authority. The same claim may bind to several dimensions; PR4 then carries that claim's complete selected evaluation basis into every bound dimension.

```text
CLAIM != COMPETENCE DIMENSION
BINDING != EVALUATION
BINDING != SUPPORT
```

## DeterministicStateDerivationRequest
The complete caller-supplied run input for PR4's stateless deterministic baseline, excluding the fixed implementation policy and deriver identities.

It identifies:

- the output `PersonalCapabilityStateId`;
- `CapabilitySubjectRef`;
- exact `CapabilityConceptRef`;
- exact `CompetenceFrameRef`;
- `as_of` and `derived_at`;
- exact selected `ClaimEvaluationId` records;
- explicit `ClaimDimensionBinding` values.

The request does not carry raw evidence ids, weights, confidence, mastery, preferred evaluator kind, or a caller-chosen derivation policy ref.

Selection is an explicit input but not a truth or authority claim:

```text
SELECTED EVALUATION != TRUTH
SELECTION != AUTHORITY
```

## Deterministic Supported-State Baseline v1
The PR4 rule policy `core:deterministic_supported_state@1` that mechanically composes explicitly selected governed evaluations into PR3 state.

It does not re-evaluate raw evidence, weight evaluators or evidence, vote, prefer the newest evaluation, apply recency decay, classify claims into dimensions, or resolve state-level conflict.

For each dimension:

- no selected bound basis → `UNKNOWN`;
- selected bound basis with no `SUPPORTED` conclusion → `INSUFFICIENT`;
- at least one selected bound `SUPPORTED` conclusion → `SUPPORTED`;
- an explicitly unresolved evaluation or same-claim selected `SUPPORTED` + `CONTRADICTED` pair → `UNRESOLVED` conflict.

Baseline v1 never emits state-level `RESOLVED_BY_POLICY`.

Equivalent exact inputs are canonicalized for deterministic output, but deterministic derivation does not establish cross-snapshot ID immutability:

```text
DETERMINISM != CROSS-SNAPSHOT ID IMMUTABILITY
DERIVATION != PERSISTENCE GOVERNANCE
```

## PersonalCapabilityState
A private, subject-scoped immutable **derived state** representing current supported claim content for one exact `CapabilityConceptRef` under one exact `CompetenceFrameRef` and `StateDerivationPolicyRef`.

It is not the shared `CapabilityConcept`, not a permanent truth about the subject, and not a UI/read-model projection.

A state records `as_of` and `derived_at`. The `as_of` boundary excludes later evaluations; `derived_at` may be later for honest historical reconstruction but may not precede `as_of`.

There is no canonical mastery score, percentage, XP value, novice/intermediate/expert rank, or aggregate human level in the state model. Competence content remains in the scopes of supported claims.

State never interprets raw evidence directly. Supported state claims must be traceable through basis `ClaimEvaluation` records for the same subject and exact capability concept revision.

State recomputation creates a new immutable record rather than rewriting historical state:

```text
RECOMPUTATION != MUTATION
```

## PersonalCapabilityStateSet
A private one-subject collection of immutable `PersonalCapabilityState` records.

It may contain historical or alternative state records with distinct state ids and does not claim that one record is globally canonical person truth.

It cross-validates basis claims/evaluations, exact capability revisions, exact competence-frame revisions, full frame dimension coverage, subject isolation, and state time boundaries. An unresolved conflict already visible in basis material cannot be silently represented as conflict-free state.

The set enforces state-id uniqueness within one collection. Later persistence/synchronization must preserve the stronger rule that a historical state id is never reused for materially different content across snapshots.

Serialization does not imply consent, publication, synchronization, or shareability.

## ConceptCandidateSpec
A PR6 candidate semantic specification containing a suggested `CapabilityId`, name, definition, and aliases for a possible future concept.

It is not a `CapabilityConcept`, does not reserve the suggested id, does not allocate semantic revision `@1`, and cannot create a namespace. Explicit catalog validation requires the suggested id to use a namespace already present in the supplied catalog.

```text
CANDIDATE SPEC != CAPABILITY CONCEPT
SUGGESTED ID != RESERVED ID
CONCEPT PROPOSAL != NAMESPACE PROPOSAL
```

## CapabilityProposal
An immutable PR6 candidate record that preserves a proposal id, one of six exact proposal kinds, a dedicated candidate payload, optional person scope, generator identity, exact generation-policy ref, creation time, rationale, typed basis refs, and optional supersession lineage.

PR6 proposal kinds are:

- `CREATE_CONCEPT`;
- `REVISE_CONCEPT`;
- `SPLIT_CONCEPT`;
- `MERGE_CONCEPTS`;
- `CREATE_RELATION`;
- `CREATE_CLAIM`.

Candidate payloads are not accepted core records. A model/human/rule/hybrid/external-system proposal remains a proposal regardless of mechanism kind, structural validity, serialization, persistence, review count, or recommendation outcome.

```text
PROPOSAL != ACCEPTED OBJECT
MODEL OUTPUT != AUTHORITY
HUMAN OUTPUT != AUTHORITY
CLAIM PROPOSAL != CAPABILITY CLAIM
RELATION PROPOSAL != CAPABILITY RELATION
```

A proposal may supersede another proposal by exact `CapabilityProposalId`, creating immutable lineage rather than mutating the parent. Reviews of the parent do not transfer to the successor.

## ProposalGenerationPolicyRef
An exact syntactic `<namespace>:<key>@<revision>` reference naming the declared policy under which a proposal was generated.

The ref is not policy content, a cryptographic content hash, a signature, an authenticated registry entry, or an authority grant. Equal policy-ref strings in independent stores do not prove equal policy content without shared registry/import governance.

```text
POLICY REF != POLICY CONTENT
POLICY REF != AUTHENTICATED POLICY
```

## ProposalGeneratorRef / ProposalReviewerRef
Opaque mechanism references whose `ProposalMechanismKind` is one of `HUMAN`, `RULE`, `MODEL`, `HYBRID`, or `EXTERNAL_SYSTEM`.

Mechanism kind and opaque ref identify the declared generator/reviewer context only. They are not globally authenticated identities and do not confer authority.

```text
GENERATOR != AUTHORITY
REVIEWER != AUTHORITY
MECHANISM REF != AUTHENTICATED GLOBAL IDENTITY
```

## ProposalBasisRef
A typed PR6 audit reference recording material inspected or motivating a proposal. Internal basis kinds include capability concepts, PR2 evidence records, claims, and claim evaluations; external/other refs remain opaque.

Basis is not evidence assessment or proof. Internal person-scoped evidence/claim/evaluation basis must match proposal subject scope. A known internal PR2 record cannot be relabeled as `EXTERNAL_ARTIFACT` or `OTHER`, and relation provenance cannot be used as a private-basis escape hatch.

An external ref that is absent from the supplied epistemic snapshot remains unclassified; absence from the snapshot is not evidence that it is public, consented, or shareable.

```text
PROPOSAL BASIS != EVIDENCE ASSESSMENT
EXTERNAL_ARTIFACT != PUBLIC ARTIFACT
NO INTERNAL MATCH != SHAREABLE
BASIS KIND LABEL != PRIVACY ESCAPE HATCH
```

## ProposalReview
A separate immutable PR6 review record referencing exactly one `CapabilityProposalId`, one reviewer ref, exact review-policy ref, review time, rationale, and one recommendation verdict:

- `RECOMMEND_ACCEPT`;
- `RECOMMEND_REJECT`;
- `REQUEST_REVISION`;
- `ABSTAIN`.

The verdict is a review fact, not an acceptance transition. Contradictory reviews may coexist; PR6 does not vote, prefer the latest review, prefer human over model, or derive a current status.

```text
RECOMMEND_ACCEPT != MATERIALIZATION
MULTIPLE REVIEWS != VOTE
LATEST REVIEW != AUTHORITY
REVIEW COUNT != ACCEPTANCE
```

## ProposalReviewPolicyRef
An exact syntactic `<namespace>:<key>@<revision>` reference naming the declared policy under which a `ProposalReview` was produced.

Like generation-policy refs, it is not authenticated policy content, a content hash, permission, or authority.

## CapabilityProposalSet
An immutable deterministic PR6 snapshot of proposals and reviews under exactly one shared/private scope.

A shared set has `subject_ref=None`; a private set binds to exactly one `CapabilitySubjectRef`. Shared and private proposals cannot be mixed, and multiple private subjects cannot share one set. Internal PR2 basis is validated against subject scope, exact semantic references may be validated against a supplied catalog, and supersession lineage must remain acyclic.

Proposal/review ids are unique only within one set. They are opaque ids rather than content hashes, and PR6 cannot enforce global no-reuse across independently assembled snapshots.

Serialization uses strict deterministic schema ingestion, including one explicit extended ISO-8601 timestamp profile with timezone and UTC canonicalization. Serialization/deserialization does not create acceptance, publication, authority, or persistence governance.

```text
SHARED TARGET != SHAREABLE PROPOSAL
SNAPSHOT-LOCAL UNIQUENESS != GLOBAL UNIQUENESS
OPAQUE ID != CONTENT HASH
SERIALIZED != ACCEPTED
PERSISTED != AUTHORITATIVE
```

## StateTransition
An auditable transition affecting person-scoped state after governed validation, evaluation, and/or review. The transition mechanism may be deterministic, probabilistic, human-reviewed, or hybrid, but must preserve provenance and policy identity.

PR3 defines valid state records. PR4 provides the first deterministic derivation path into that representation. PR6 deliberately does not define proposal materialization, a general transition engine, persistence workflow, acceptance workflow, or global historical identity registry.

## PersonalDevelopmentModel
The private subject-scoped model containing capability states, evidence references, governed claims, development history, achievements/milestones, and derived narrative/progression/product projections used by Capability Lab.

This is intentionally called a `Model`: it is partial, revisable, and does not claim to represent the whole person.

`PlayerWindow` is a selected read model over this governed material, not the model itself. PR10.0 raw pilot captures are upstream session material and do not enter the `PersonalDevelopmentModel` merely because they are structurally valid.

Incidental observation of another person is not sufficient authority to create or retain such a persistent model by default.

## HumanCapabilityCommons
A future shared layer containing reusable capability concepts, relations, competence-frame semantics, achievement families, aliases, cultural interpretations, and privacy-preserving aggregate knowledge about development paths.

It is not a database of raw pilot captures, raw personal graphs, or private development history. Aggregate path observations are descriptive by default; common does not mean required, causal, or optimal.

## AchievementFamily
A shared, versioned PR7 semantic definition of a repeatable accomplishment pattern.

A stable `AchievementFamilyId` identifies the family lineage and an exact `AchievementFamilyRef` identifies one declared revision using `<namespace>:<key>@<revision>`. `AchievementCriterion` values describe qualification semantics; they are not point values, weights, difficulty levels, learning prerequisites, or an auto-award algorithm.

```text
ACHIEVEMENT FAMILY != ACHIEVEMENT INSTANCE
ACHIEVEMENT FAMILY != CAPABILITY CONCEPT
FAMILY CRITERIA != AUTO-QUALIFICATION ENGINE
CRITERION COUNT != DIFFICULTY
```

An exact family ref prevents silent latest-revision substitution but is not a content hash, signature, authenticated archive entry, or proof that two independent stores carry identical content. `AchievementFamilyCatalog` is a deterministic current semantic snapshot, not a historical revision archive.

## AchievementInstance
A private subject-scoped immutable PR7 historical record of one accomplishment under one exact `AchievementFamilyRef`.

It records `achieved_at`, `recorded_at`, exact `AchievementQualificationPolicyRef`, `AchievementQualifierRef`, typed qualification basis, bounded context, and optional variant/note. At least one event-bearing `EvidenceRecord` or `EXTERNAL_ARTIFACT` basis is required. PR3 current state is not an achievement basis.

```text
ACHIEVEMENT INSTANCE != CAPABILITY
ACHIEVEMENT INSTANCE != CAPABILITY CLAIM
ACHIEVEMENT INSTANCE != PERSONAL CAPABILITY STATE
ACHIEVEMENT INSTANCE != EVIDENCE RECORD
SUPPORTED STATE != ACHIEVEMENT EVENT
CURRENT READINESS LOSS != ACHIEVEMENT ERASURE
```

Within one `PersonalHistoryRecordSet`, the same exact event-bearing basis cannot be replayed as multiple achievement instances of one stable family identity merely by changing achievement id, family revision, or timestamp. This is a snapshot-local anti-replay rule, not a global real-world event fingerprint. Equal timestamps/windows do not prove event identity, and distinct evidence/artifact refs do not prove distinct real events.

`AchievementQualifierRef` may identify a human, rule, model, hybrid, or external-system mechanism. Mechanism kind and policy ref record declared qualification context; they do not authenticate authority, policy content, subject endorsement, or truth.

## AchievementQualificationPolicyRef
An exact syntactic PR7 policy reference naming the declared qualification policy for an `AchievementInstance`.

It is not policy content, a signature, a content hash, an authority grant, or proof that qualification was accepted by a durable application workflow.

## AchievementQualifierRef
An opaque PR7 mechanism reference whose `HistoryMechanismKind` may be `HUMAN`, `RULE`, `MODEL`, `HYBRID`, or `EXTERNAL_SYSTEM`.

```text
QUALIFIER != AUTHORITY
MODEL QUALIFIER != AUTOMATIC TRUTH
MODEL QUALIFIER != SUBJECT ENDORSEMENT
```

## PersonalMilestoneEvent
A private subject-scoped immutable historical event preserved because it may be meaningful to the person's development history. It may represent success, failure, a decision, a transition, an abandoned path, a first experience, or another unique event and may never map to a shared `AchievementFamily`.

It records `occurred_at`, `recorded_at`, attributed `MilestoneRecorderRef`, exact `MilestoneRecordingPolicyRef`, optional typed sources, tags, and a narrative `significance_note`.

```text
ACHIEVEMENT INSTANCE != PERSONAL MILESTONE
MILESTONE != TROPHY
MILESTONE != CAPABILITY STATE
MILESTONE SIGNIFICANCE != GLOBAL IMPORTANCE
SIGNIFICANCE NOTE != SUBJECT ENDORSEMENT
```

Event-bearing evidence sources must describe an observation no later than the milestone event and must exist by the milestone record boundary. Documentary claim/evaluation sources may honestly be created after the event but must exist by `recorded_at`. A milestone citing an achievement requires the achievement event to precede/equal the milestone event and the achievement record to exist by the milestone's `recorded_at`.

## MilestoneRecorderRef
An opaque PR7 mechanism reference identifying the declared recorder. Recorder mechanism kind is attributed metadata, not authority or subject endorsement.

## PersonalHistoryRecordSet
The deterministic private one-subject PR7 source-of-history snapshot containing `AchievementInstance` and `PersonalMilestoneEvent` records.

It enforces subject isolation, within-snapshot id uniqueness, cross-type achievement/milestone id separation, achievement anti-replay by exact event-bearing basis inside one stable family, internal source existence, exact family revision validation, and PR2/history causality when supplied corresponding snapshots.

Known PR2 ids cannot be relabeled as external/other history basis, and exact history ids cannot be relabeled into PR2 evidence/claim provenance or evidence payload refs to create a feedback loop.

```text
HISTORY RECORD != EVIDENCE RECORD
HISTORY ID != EVIDENCE/PROVENANCE ESCAPE HATCH
HISTORY -> EVIDENCE -> HISTORY != VALID PR7 CYCLE
PERSONAL HISTORY SET != MULTI-SUBJECT DATABASE
SERIALIZED HISTORY != PUBLISHED HISTORY
```

History ids are opaque and unique only inside their validated snapshot. PR7 does not provide a global registry, content-addressed identity, persistence reconciliation, or correction/retraction precedence.

## PersonalLegendEntry
One authored narrative entry inside a `PersonalLegend`.

Each entry requires at least one exact `LegendSourceRef` and may cite only `AchievementInstanceId` or `PersonalMilestoneEventId`. It cannot directly cite evidence, claims, evaluations, current state, or another Legend. Source order within an entry is canonicalized, while entry order across the Legend remains authored projection semantics.

## PersonalLegend
A private derived PR7 narrative projection that selects and interprets achievement/milestone history without rewriting the underlying records.

It records exact subject, historical `as_of`, `generated_at`, exact `LegendProjectionPolicyRef`, `LegendGeneratorRef`, title, summary, and an authored ordered sequence of source-backed entries. Every cited source must exist; source event time must be no later than `as_of`, source record time must be no later than `generated_at`, and one exact history source cannot be repeated across multiple entries of the same validated Legend.

```text
LEGEND != HISTORY
LEGEND != EVIDENCE
LEGEND != CLAIM
LEGEND != STATE
LEGEND != PERSON IDENTITY
LEGEND SOURCE != LEGEND
LEGEND OMISSION != HISTORY DELETION
LEGEND SELECTION != GLOBAL IMPORTANCE
PERSONAL LEGEND != CANONICAL SELF-NARRATIVE
```

A Legend is intentionally selective. Two valid Legends may choose different subsets/orderings from one history. Repeated citation is not multiple independent source support. Natural-language fairness/completeness is not proven by structural validation.

## PersonalLegendSet
A private one-subject collection of alternative `PersonalLegend` projections.

Legend ids are unique within the set and may not collide with achievement/milestone id strings in the combined validated personal snapshot. Different Legends may reuse the same historical source. PR7 defines no `canonical_legend`, latest-wins rule, completeness flag, or official narrative.

## LegendProjectionPolicyRef / LegendGeneratorRef
The exact declared policy ref and opaque mechanism ref under which a Legend was generated.

A model may generate a Legend, but mechanism/policy identity does not make narrative authoritative, subject-endorsed, historically complete, or a source of evidence/state.

```text
LEGEND GENERATOR != AUTHORITY
MODEL NARRATIVE != HISTORY
MODEL NARRATIVE != PERSON IDENTITY
```

## History correction/retraction boundary
PR7 history records are immutable, but immutability does not imply that an incorrect or fraudulently qualified record can never be corrected.

```text
IMMUTABLE HISTORY != IRRETRACTABLE FALSEHOOD
READINESS DECAY != ACHIEVEMENT RETRACTION
CORRECTION / RETRACTION != IN-PLACE MUTATION
```

PR7 v1 intentionally defines no `HistoryCorrection`, `AchievementRetraction`, deletion, effective-history precedence, or publication/visibility workflow. A future correction/retraction layer should be append-only and provenance-preserving.

## ProgressionMechanismKind
The PR8 mechanism category attached to a progression requester or deriver: `HUMAN`, `RULE`, `MODEL`, `HYBRID`, or `EXTERNAL_SYSTEM`.

Mechanism kind is declared context, not authority, identity proof, recommendation strength, or subject endorsement.

## ProgressionRequesterRef
An opaque PR8 mechanism reference identifying who/what supplied the explicit `ProgressionFrontierRequest` inputs.

The requester may be a human, rule, model, hybrid, or external system. Requester identity does not make request-local focus a subject goal or exploration input a recommendation.

```text
REQUESTER != AUTHORITY
MODEL REQUESTER != SUBJECT GOAL
```

## ProgressionDeriverRef
An opaque PR8 mechanism reference identifying the mechanism that executed frontier derivation.

PR8's frozen baseline uses a rule deriver. Deriver identity does not grant authority or make the projection canonical.

## ProgressionPolicyRef
An exact syntactic PR8 policy reference identifying the progression derivation policy. The implemented v1 baseline is `core:deterministic_progression_frontier@1`.

Like other policy refs, it is not policy content, a signature, authenticated registry entry, permission, or authority grant.

## ProgressionFocus
A request-local exact `CapabilityConceptRef` plus rationale identifying a direction the caller explicitly wants kept visible in one PR8 projection.

It is not a persistent Goal, Interest, identity claim, permission, or proof of subject endorsement. A focus may coincide with an independently derived adjacent candidate, preserving two inspectable reasons for visibility, but may not equal an exact selected seed concept.

```text
PROGRESSION FOCUS != GOAL
PROGRESSION FOCUS != INTEREST
PROGRESSION FOCUS != IDENTITY
MODEL-SUPPLIED FOCUS != SUBJECT GOAL
```

## FrontierSeedBinding
A PR8 request input selecting exact dimension keys from one exact `PersonalCapabilityStateId` as the permitted seed basis for direct one-hop adjacency.

Each selected dimension must have `DimensionStanding.SUPPORTED`. This does not aggregate the state into whole-capability support. `SUPPORTED + UNRESOLVED` remains explicitly seedable without conflict ranking or silent resolution.

One request may select at most one seed state for one exact seed `CapabilityConceptRef`; this prevents state-id-only witness amplification while leaving state choice explicit rather than auto-selecting latest.

```text
FRONTIER SEED BINDING != WHOLE-CAPABILITY SUPPORT
SUPPORTED DIMENSION != SUPPORTED PERSON
LATEST STATE != AUTOMATIC FRONTIER INPUT
```

## PrerequisiteCheckBinding
A PR8 request-local explicit mapping from one exact candidate/prerequisite `REQUIRES` relation and exact `RelationScope` to one exact `CompetenceFrameRef`, required dimension keys, and optionally one exact selected prerequisite state.

The binding is inspectable caller input. It is not a global mapping between relation scope and competence dimensions, not support, and not authority. A binding can be consumed only for a real categorical `REQUIRES` relation of an actual frontier candidate.

```text
RELATION SCOPE != COMPETENCE DIMENSION
SCOPE-DIMENSION BINDING != GLOBAL MAPPING
SUPPORTED_BY != REQUIRES
STRONG SUPPORTED_BY != PREREQUISITE
```

## ProgressionFrontierRequest
The immutable complete request-local input for PR8's deterministic progression baseline.

It identifies the output `ProgressionFrontierId`, subject, `as_of`, `generated_at`, `ProgressionRequesterRef`, explicit `ProgressionFocus` values, exact `FrontierSeedBinding` values, explicit `PrerequisiteCheckBinding` values, and explicit `ExplorationInput` values.

The request does not contain raw evidence weights, automatic current-state selection, history/Legend inputs, rank/priority fields, a caller-chosen derivation policy, or a hidden goal inference mechanism.

## ProgressionRelationWitness
An immutable PR8 projection witness preserving the exact candidate/source concept ref, exact supporting/prerequisite target ref, relation kind, complete relation scope, and relation strength where applicable.

It is an audit copy of the relation semantics used for one projection, not a new accepted `CapabilityRelation` and not a recommendation score.

## FrontierAdjacencyWitness
An immutable PR8 witness explaining one candidate's direct adjacency from one exact selected state, exact seed concept, exact selected dimension keys, and one `ProgressionRelationWitness`.

Several witnesses may explain the same candidate. Witness multiplicity is provenance, not vote, rank, confidence, or priority.

```text
MULTIPLE ADJACENCY WITNESSES != HIGHER PRIORITY
WITNESS COUNT != RECOMMENDATION STRENGTH
```

## FrontierCandidate
One exact capability concept made visible in a `ProgressionFrontier` because it is explicitly focused, directly one-hop adjacent to a selected seed through an allowed relation, or both.

A candidate preserves its `explicit_focus` flag, adjacency witnesses, assessed categorical prerequisites, and unassessed categorical prerequisites. It contains no score, rank, difficulty, distance, readiness, probability, success estimate, permission, or recommendation strength.

```text
FRONTIER CANDIDATE != NEXT REQUIRED STEP
FRONTIER CANDIDATE != READINESS
FRONTIER CANDIDATE != PERMISSION
FRONTIER ORDER != PRIORITY
```

## PrerequisiteDimensionGapKind
The PR8 dimension-local evidence-gap state for an explicitly bound categorical prerequisite:

- `NO_SELECTED_STATE` — the binding explicitly names required dimensions but no prerequisite state was selected;
- `UNKNOWN` — the selected exact state represents the required dimension as `UNKNOWN`;
- `INSUFFICIENT` — the selected exact state represents governed basis without supported content for that dimension.

These are evidence/state representation gaps, not levels of missing ability.

## PrerequisiteEvidenceGap
A deterministic PR8 advisory projection produced only for a real `REQUIRES` relation with an explicit `PrerequisiteCheckBinding` whose selected required dimensions contain at least one gap.

It preserves exact target/prerequisite refs, exact relation witness, exact frame ref, optional selected state id, and dimension-local gap records. It does **not** assert that the subject lacks the prerequisite capability, cannot attempt the target, is unsafe, or is unpermitted.

If a `REQUIRES` relation has no binding, the candidate records it in `unassessed_prerequisites` instead of manufacturing a gap. Partial assessment therefore remains visibly partial.

```text
PREREQUISITE EVIDENCE GAP != MISSING CAPABILITY
UNASSESSED PREREQUISITE != SATISFIED PREREQUISITE
PREREQUISITE GAP != PROHIBITION
PREREQUISITE GAP != ACCESS CONTROL
NO GAP != READY
NO GAP != SAFE
NO GAP != PERMITTED
```

## ExplorationInput
A PR8 request-local exact concept ref plus rationale explicitly supplied by the caller to preserve a direction outside the seed/focus/derived-candidate channels.

It is not generated from graph distance, low connectivity, novelty score, inferred interest, history, or a previous frontier.

## ExplorationOpportunity
The PR8 output corresponding to one valid explicit `ExplorationInput`.

It preserves the requested exact concept and rationale without converting it into a frontier candidate, recommendation, rank signal, inferred interest, or goal. Exploration input must remain distinct from selected seed concepts, explicit focus, and already derived frontier candidates.

```text
EXPLORATION OPPORTUNITY != RECOMMENDATION
EXPLORATION PRESERVATION != AUTOMATIC EXPLORATION GENERATION
ABSENCE OF GRAPH EDGE != SEMANTIC UNRELATEDNESS
```

## ProgressionFrontier
A private subject-scoped immutable PR8 advisory projection containing the frozen policy/deriver identity, requester identity, effective request inputs, direct `FrontierCandidate` records, `PrerequisiteEvidenceGap` records, explicit `ExplorationOpportunity` records, and rationale.

It is derived only from explicitly selected supported state dimensions, direct accepted PR1 relations, explicit request-local focus, explicit prerequisite bindings, and explicit exploration inputs. It does not read history/Legend, auto-select latest state, infer goals, search paths, rank candidates, or mutate underlying records.

```text
PROGRESSION FRONTIER != RECOMMENDATION
DIRECT RELATION != OPTIMAL PATH
ONE-HOP FRONTIER != CURRICULUM
RELATION STRENGTH != FRONTIER PRIORITY
HISTORY / LEGEND != FRONTIER INPUT
```

An exact selected seed concept may use at most one selected seed state in one request. A seed cannot simultaneously be the exact explicit focus. These rules prevent state-id-only witness amplification and seed→candidate collapse without introducing latest-state authority.

`frontier.as_of` bounds selected personal-state time. It does not prove that supplied semantic or competence-frame snapshots existed in the same form at that historical date.

## ProgressionFrontierSet
A deterministic private one-subject collection of immutable `ProgressionFrontier` projections.

Multiple alternative frontiers may coexist. Frontier ids are snapshot-local opaque identities; latest does not become canonical truth or recommendation authority.

## Progression frontier serialization and verification
PR8 defines strict deterministic serialization for `ProgressionFrontierRequest`, `ProgressionFrontier`, and `ProgressionFrontierSet` with one explicit schema version and extended timezone-aware ISO-8601 profile.

Structural deserialization validates schema and record invariants only. It does not prove that the derived fields were produced by the frozen baseline.

`validate_progression_frontier_v1(...)` is the explicit source-backed verifier. It reconstructs the request from the frontier's preserved effective inputs, re-runs `derive_progression_frontier_v1(...)` against the supplied `CapabilityCatalog`, `CompetenceFrameCatalog`, `EpistemicRecordSet`, and `PersonalCapabilityStateSet`, and requires exact equality.

```text
STRUCTURALLY VALID FRONTIER != VERIFIED DERIVATION
DESERIALIZED FRONTIER != VERIFIED DERIVATION
VERIFIED DERIVATION != AUTHENTICATED SOURCE SNAPSHOT
EXACT CONCEPT REF != CONTENT HASH
```

Verification proves deterministic consistency with supplied snapshots, not publisher identity, archive authenticity, digital signature, policy authenticity, or absence of same-ref content substitution across independent stores.

## Projection
A derived read model or advisory representation generated from governed records/state for a particular use.

A projection is not the source of truth and must not silently mutate underlying evidence, claims, evaluations, state, or immutable history. Structural validity, serialization, deterministic verification, or rendering does not automatically make a projection authoritative or publishable.

## PlayerWindowMechanismKind
The PR9 mechanism category used by `PlayerWindowRequesterRef`, `PlayerWindowViewerRef`, and the fixed Player Window generator context: `HUMAN`, `RULE`, `MODEL`, `HYBRID`, or `EXTERNAL_SYSTEM`.

Mechanism kind is attribution only. It does not prove identity, authority, subject endorsement, viewer authorization, or publication permission.

## PlayerWindowRequesterRef
An opaque PR9 mechanism reference identifying who/what supplied the explicit source selection for one `PlayerWindowRequest`.

A model requester does not make the selection the subject's curation, current truth, canonical view, or complete record set.

```text
REQUESTER != AUTHORITY
MODEL REQUESTER != SUBJECT CURATION
```

## PlayerWindowViewerRef
An opaque PR9 mechanism reference describing the declared intended viewer context for one Player Window projection.

It is not an access-control decision, authenticated identity, sharing consent, export permission, or proof that the viewer is the capability subject.

```text
VIEWER != SUBJECT
VIEWER REF != AUTHORIZATION
VIEWER REF != EXPORT AUTHORIZATION
```

## PlayerWindowRequest
The immutable explicit source-selection input for PR9's deterministic Player Window baseline.

It identifies the output `PlayerWindowId`, subject, `as_of`, `generated_at`, requester/viewer refs, exact selected `PersonalCapabilityStateId` values, exact selected achievement and milestone ids, and optional selected Legend/frontier ids.

It contains no automatic latest/current selector, source ranking, score, priority, growth threshold, Human Level, inferred goal, domain percentage, or caller-chosen projection policy. At least one source must be selected.

```text
LATEST STATE != AUTOMATIC WINDOW STATE
LATEST LEGEND != AUTOMATIC WINDOW LEGEND
LATEST FRONTIER != AUTOMATIC WINDOW FRONTIER
WINDOW SOURCE SELECTION != TRUTH / IMPORTANCE / COMPLETENESS
```

## Player Window display entries
PR9 defines immutable bounded display entries for selected capability state, supported claim/evaluation context, achievement/milestone history, Legend narrative entries, frontier candidates, prerequisite gaps, and explicit exploration.

These records preserve exact source IDs/refs and enough source-visible context for inspection without copying the entire private epistemic database into the product read model. Raw `EvidenceRecord` payload/context is not a Player Window display layer.

A selected capability entry always includes every dimension of its exact competence frame. The UI vocabulary preserves support standing and conflict instead of translating them into mastery/weakness/zero.

```text
SELECTED STATE -> COMPLETE FRAME DIMENSION VISIBILITY
SUPPORTED != MASTERED
INSUFFICIENT != LOW
UNKNOWN != ZERO
SUPPORTED + UNRESOLVED != CONFLICT-FREE SUPPORT
```

Frontier relation strings stored in display entries are human-readable projection summaries. They are not a canonical machine-readable replacement for the typed PR8 source frontier.

```text
DISPLAY SUMMARY != SOURCE FRONTIER
DISPLAY SUMMARY != CANONICAL PROVENANCE
DO NOT PARSE PRESENTATION TEXT AS AUTHORITY
```

## PlayerWindow
A private subject-scoped immutable PR9 **product read model** over explicitly selected governed PR3 state, PR7 history/Legend, and optional PR8 frontier records.

It is not a `PersonalDevelopmentModel`, current person truth, recommendation engine, permission system, public profile, Human Level, or general UI framework. It preserves the exact selection and deterministic projection output under the fixed `core:deterministic_player_window@1` policy and rule generator.

```text
PLAYER WINDOW != PERSONAL DEVELOPMENT MODEL
PLAYER WINDOW != PERSON
PLAYER WINDOW != CURRENT TRUTH
PLAYER WINDOW != AUTHORITY
DISPLAYED != CANONICAL
OMITTED != ABSENT
DISPLAY ORDER != PRIORITY
```

Visible source closure is part of PR9 integrity. A selected Legend cannot hide a cited selected history source. A selected frontier cannot hide selected seed/prerequisite personal-state basis. For verified windows, a selected milestone sourced from an achievement must preserve that selected typed history→history closure.

`PlayerWindow` has no Human Level, XP, score, rank, growth metric, difficulty, readiness, recommendation probability, or inferred domain score. PR9 does not derive recent growth merely from differences between immutable state records.

```text
STATE DIFFERENCE != GROWTH
MORE SUPPORTED DIMENSIONS != HUMAN PROGRESS SCORE
ACHIEVEMENT != CURRENT READINESS
GAP != BLOCKED
NO GAP != READY / SAFE / PERMITTED
```

## PlayerWindowSet
A deterministic private one-subject collection of alternative immutable `PlayerWindow` projections.

Window ids are snapshot-local opaque identities. Multiple alternative windows may coexist; generated time, insertion order, or deterministic sorting does not establish latest-wins authority, current truth, or a canonical view.

```text
MULTIPLE WINDOWS != CONFLICT
LATER WINDOW != CANONICAL WINDOW
WINDOW ORDER != IMPORTANCE
```

## Player Window serialization and verification
PR9 defines strict deterministic serialization for `PlayerWindowRequest`, `PlayerWindow`, and `PlayerWindowSet`.

Structural deserialization validates schema and read-model invariants only. It does not prove that display content came from the supplied source records.

`validate_player_window_v1(...)` is the explicit source-backed verifier. It validates exactly selected PR3 states against supplied epistemic/capability/frame snapshots; validates exactly selected PR7 history/Legend against achievement-family, epistemic, and history contracts; validates any selected PR8 frontier through PR8 exact source-backed verification; then reconstructs the PR9 request, re-runs `derive_player_window_v1(...)`, and requires exact equality.

Unselected state/history/Legend records remain inert for verification.

```text
SELECTED SOURCE MUST SATISFY ITS GOVERNING CONTRACT
STRUCTURALLY VALID WINDOW != VERIFIED WINDOW
DESERIALIZED WINDOW != VERIFIED WINDOW
VERIFIED WINDOW != AUTHENTICATED SOURCE SNAPSHOT
```

Verification proves deterministic consistency with supplied source snapshots. It does not authenticate source publisher identity, same-ref semantic/family content across independent stores, archive timestamps, signatures, viewer authority, export permission, or policy content. A historical `window.as_of` does not prove that supplied semantic snapshots existed in the same form at that historical date.

## Player Window HTML renderer
`render_player_window_html_v1(window)` is PR9's dependency-free leaf presentation layer. It accepts only an already constructed `PlayerWindow`; it does not receive source catalogs/sets and therefore cannot auto-select latest/best/current records or re-derive upstream meaning.

The renderer emits one self-contained read-only HTML document with embedded CSS, HTML escaping, no JavaScript, no remote fonts/assets/analytics, `noindex,nofollow`, and a restrictive Content Security Policy. The bundled Civilization Bootstrap demo verifies its Player Window before rendering.

```bash
python -m capability_lab.player_window.demo --output player_window.html
```

The rendered file is a private data artifact, not a source record, verified-window signature, publication, authorization, or share-consent token.

```text
RENDERER != DERIVER
SOURCE TEXT != TRUSTED HTML
RENDERED HTML != VERIFIED WINDOW
VERIFIED PLAYER WINDOW != SIGNED HTML ARTIFACT
LOCAL != PUBLIC
NO NETWORK REQUEST != SAFE TO SHARE
HTML FILE COPY == DATA EXPORT
LOCAL HTML != PUBLICATION PERMISSION
```

## PilotProtocolRef
The exact PR10.0 revision identity of a pilot protocol. Pilot 01 uses:

```text
civilization_bootstrap:pilot_01_basic_electricity@1
```

The ref prevents silent latest-revision substitution inside the PR10.0 workspace contract. It is not a content hash, authenticated publisher identity, trusted timestamp, or authority grant. Canonical protocol bytes are regression-frozen under `@1`; the regression fingerprint detects semantic drift but does not create authenticity.

## PilotProtocol / PilotProbeDefinition
`PilotProtocol` is PR10.0's versioned participant-facing capture protocol. `PilotProbeDefinition` describes one probe, its requirement status, permitted raw capture kinds, and participant-facing instructions without answer keys, evaluation thresholds, capability conclusions, or claim-to-dimension bindings.

Pilot 01 contains required conceptual/calculation/diagnosis text probes plus an optional execution probe. Required probes allow at most one capture in the final mutation geometry. The optional execution probe may preserve multiple participant-provided text notes and file artifacts.

```text
PROTOCOL PROMPT != EVALUATION RUBRIC
REQUIRED PROBE != REQUIRED CAPABILITY
MISSING OPTIONAL EXECUTION != FAILURE
```

## PilotCaptureRecord
A strict private PR10.0 raw-capture record bound to one exact protocol revision, session id, `CapabilitySubjectRef`, probe id, capture kind, declared origin, declared capture time, and either UTF-8 text content or one copied artifact descriptor.

Pilot 01 capture kinds are `TEXT_RESPONSE` and `FILE_ARTIFACT`. Its declared origin kind is `SUBJECT_PROVIDED`, which records what the ingesting workflow declares about origin; it does not authenticate human authorship or physical presence.

A file-backed capture carries canonical relative path, original filename, byte size, and SHA-256 for local integrity/linkage. Those fields do not prove authorship, truth, correctness, evidentiary relevance, or originality.

```text
PILOT CAPTURE != EVIDENCE RECORD
PILOT RESPONSE != CAPABILITY CLAIM
PILOT ARTIFACT != CLAIM EVALUATION
DECLARED HUMAN ORIGIN != AUTHENTICATED HUMAN ORIGIN
ARTIFACT SHA-256 != AUTHORSHIP / AUTHENTICITY
```

## PilotCaptureSet
A deterministic one-session, one-subject PR10.0 collection of raw capture records under one exact protocol ref.

Capture ids are unique and canonical file keys. In the supported public transaction geometry, each required probe may have at most one capture; the optional execution probe may have multiple captures. A capture set is not an `EpistemicRecordSet`, capability-state snapshot, attempt score, or participant outcome.

```text
CAPTURE SET != EPISTEMIC RECORD SET
CAPTURE COUNT != CAPABILITY STRENGTH
CAPTURE COMPLETENESS != CAPABILITY
```

## PrivatePilotWorkspaceManifest
The canonical PR10.0 metadata record for one private local Pilot 01 workspace. It binds exact `PilotProtocolRef`, session id, `CapabilitySubjectRef`, and declared workspace creation time.

`created_at` is a canonical declared timestamp for local consistency. It is not an authenticated session-start time. The manifest does not grant access, publication permission, evaluator authority, or evidence status.

A repository-local workspace is permitted only below `<repo>/.local/`; `.local/` is git-ignored. A workspace outside the repository may also be used. Copying either kind of workspace is still a private-data export.

## PilotWorkspaceValidationReport
The public PR10.0 result of stable private-workspace validation. It reports session id, capture/artifact counts, captured probe ids, missing required probe ids, derived `capture_complete`, and `snapshot_sha256`.

`capture_complete` means only that all required Pilot 01 probes are represented. It is not pass/fail, readiness, capability support, mastery, or evidence sufficiency. An incomplete but structurally valid workspace is a successful validation result with `capture_complete=false`.

```text
CAPTURE INCOMPLETENESS != COMMAND FAILURE
CAPTURE COMPLETE != CAPABILITY SUPPORTED
```

## Pilot 01 private workspace
The closed-world filesystem representation used by PR10.0 to preserve one private raw session.

Its top-level layout is exactly the frozen manifest, protocol snapshot, private notice, `captures/`, and `artifacts/`. Capture JSON must be canonical; internal symlinks, unexpected adjacent files, cross-capture artifact substitution, orphan artifact entries, missing artifact directories, size/digest mismatch, and protocol/session/subject inconsistencies fail closed.

The public mutation surface stages before publication, performs full pre-append validation, refuses overwrite, and revalidates the post-write state. New valid captures do not silently repair previous corruption.

Artifact capture has two final filesystem objects, so PR10.0 explicitly does not claim portable multi-path atomicity. An abrupt crash can leave an orphan artifact directory between publication steps. That crash state is invalid and blocks further append; PR10.0 does not silently synthesize missing capture metadata or choose an ambiguous recovery history.

```text
VALID WORKSPACE != AUTHENTICATED SESSION
CORRUPT WORKSPACE != APPENDABLE WORKSPACE
ORPHAN ARTIFACT != RECOVERED CAPTURE
RECOVERY != SILENT REPAIR OF PARTICIPANT HISTORY
```

## Pilot workspace snapshot_sha256
A domain-separated SHA-256 returned by PR10.0 public validation over the validated workspace's relative directory/file shape plus exact file bytes.

Validation performs two complete reads; if the structural reports or fingerprints differ, the workspace is rejected as having changed during validation. Equal byte-equivalent copies or deterministic reconstructions reproduce the same fingerprint under this scheme.

The fingerprint is snapshot identity, not authenticated history. It does not prove who created the bytes, when the real-world session happened, which copy is original, whether the participant was present, or whether any capture should become evidence.

```text
VALIDATION REPORT != LOCK
SAME SNAPSHOT SHA-256 != SAME HISTORICAL EVENT
SNAPSHOT SHA-256 != TRUSTED TIMESTAMP
SNAPSHOT SHA-256 != HUMAN AUTHORSHIP
SNAPSHOT SHA-256 != EVIDENCE AUTHORITY
DETERMINISTIC REPLAY != PROOF OF ORIGINALITY
```

## Pilot 01 runner
The dependency-free PR10.0 CLI for private capture operations:

```text
init
show-protocol
record-text
record-artifact
validate
```

The runner is a capture/validation mechanism, not an evaluator, evidence materializer, state deriver, frontier deriver, or Player Window generator. PR10.0 statically guards against hidden coupling to those authority pipelines.

```text
RUNNER != EVALUATOR
RUNNER != EVIDENCE MATERIALIZER
TRANSACTIONAL CAPTURE != EVIDENCE AUTHORITY
STABLE SNAPSHOT != EVALUATED SNAPSHOT
```
