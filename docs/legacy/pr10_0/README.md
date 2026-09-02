# Capability Lab

Capability Lab is an experimental system for modeling **evidence and governed claims about what a person can do**, **how supported capability state changes over time**, **what has actually happened in their development history**, and **what development paths may be available next**.

It is intended to become an evidence-backed progression layer that can later integrate with HDE (Human Development Environment), while remaining independently useful and independently testable.

> **The system models evidence, claims, evaluations, derived capability state, non-authoritative proposals, immutable personal history, and derived narrative/advisory/product projections. It does not directly observe or define the person.**

## Why this project exists

Most learning and professional systems track proxies: courses completed, credentials earned, jobs held, tests passed, or self-reported skills. Those signals can be useful, but they are not the same as demonstrated capability.

Capability Lab explores a different model:

- represent capability concepts as an evolving graph rather than a single tree;
- separate shared capability semantics from a person's private evidence and state;
- ground capability claims in inspectable evidence and provenance;
- preserve exact semantic and policy revisions rather than silently substituting "latest";
- represent `UNKNOWN`, insufficiency, supported scoped content, and conflict explicitly;
- use domain-defined competence frames instead of one universal mastery scalar;
- preserve achievements and milestones as immutable person-scoped history rather than reduce them to XP;
- keep narrative Legend projections separate from the historical source records they interpret;
- keep progression frontier, prerequisite evidence-gap, and exploration projections advisory rather than prescriptive;
- expose selected governed records through a source-visible Player Window without turning presentation into authority;
- capture the first real Civilization Bootstrap pilot in a private raw-workspace layer without automatically converting participant responses into evidence, claims, evaluations, or state;
- allow models to propose, evaluate, qualify, record, narrate, or request bounded projections under explicit policies without turning model output into authority;
- eventually learn aggregate development paths through a privacy-preserving Human Capability Commons.

## Current status

The implemented foundation runs through **PR9 — Player Window Read Model and Local Prototype v1**, and **PR10.0 — Civilization Bootstrap Pilot 01 Protocol & Private Workspace Boundary** now provides the first real-pilot capture surface on top of that foundation.

Implemented sequence:

- **PR0** — Project Constitution, Epistemic Boundaries and System Architecture;
- **PR1** — Capability Concept, Relation Families and Namespace Model v1;
- **PR2** — Evidence Record, Provenance, Capability Claim and Evaluation Boundary v1;
- **PR3** — Personal Capability State and Multi-Dimensional Competence Representation v1;
- **PR4** — Deterministic Evidence-to-Supported-State Baseline v1;
- **PR5** — Civilization Bootstrap Seed Capability Graph v0;
- **PR6** — Capability Proposal and Model Non-Authority Boundary v1;
- **PR7** — Achievement Family, Personal Milestone and Legend History v1;
- **PR8** — Progression Frontier, Prerequisite Evidence Gap and Exploration Projection v1;
- **PR9** — Player Window Read Model and Local Prototype v1;
- **PR10.0** — Civilization Bootstrap Pilot 01 Protocol & Private Workspace Boundary.

PR3 provides the immutable private subject-scoped state representation. PR4 adds the first executable deterministic derivation policy. PR5 supplies the first real curated technical domain: 63 bounded capability concepts, a deliberately sparse 57-edge semantic/dependency graph, and the exact `civilization_bootstrap:technical_competence@1` frame. PR6 adds a separate immutable candidate/review layer so human, rule, model, hybrid, or external-system suggestions remain auditable without gaining authority to mutate accepted semantics or person-scoped state. PR7 adds shared versioned achievement-family semantics, private one-subject achievement/milestone history, and source-backed Personal Legend projections while keeping historical accomplishment separate from current readiness and narrative interpretation. PR8 adds the first deterministic non-ranking advisory progression projection from explicitly selected supported state dimensions, direct accepted graph relations, request-local focus, explicit prerequisite checks, and preserved exploration inputs while keeping `COULD BE CONSIDERED != SHOULD DO`. PR9 adds the first deterministic private product read model and dependency-free local HTML prototype over explicitly selected PR3 state, PR7 history/Legend, and one explicitly selected PR8 frontier while preserving source visibility, non-authority, privacy, and verification boundaries. PR10.0 adds a frozen participant-facing Basic Electricity pilot protocol, strict private raw-capture records, a `.local/` workspace boundary, transactional/fail-closed capture mutation, deterministic workspace validation/fingerprinting, and an explicit stop before `PilotCaptureRecord -> EvidenceRecord` materialization.

## Current architecture

```text
Civilization Bootstrap Pilot 01 protocol (PR10.0)
                |
                v
      private raw workspace
                |
                v
        PilotCaptureRecord
                X no automatic EvidenceRecord / claim / evaluation / state

Civilization Bootstrap seed semantics (PR5)
                |
                v
CapabilityConcept / CapabilityRelation
                |
                +------------------------------+
                |                              |
                v                              v
          CapabilityClaim <----- EvidenceRecord   proposal generator
                |                      |                 |
                +---- ClaimEvaluation--+                 v
                           |                      CapabilityProposal
             explicit selected evaluations              |
             + explicit claim/dimension bindings         v
                           |                       ProposalReview
                           v                              |
          deterministic state derivation (PR4 v1)       X no implicit apply
                           |                              |
              +------------+------------+                 |
              |                         |                 |
      CompetenceFrameRef       StateDerivationPolicyRef  |
              |                         |                 |
              +------------+------------+                 |
                           |                              |
                           v                              |
               PersonalCapabilityState <-----------------+
                           |
             explicit selected state dimensions
             + direct accepted relations
             + request-local focus/exploration
                           |
                           v
                 ProgressionFrontier (PR8)
                 /          |           \
      FrontierCandidate  EvidenceGap  ExplorationOpportunity
                 X no state/history/permission mutation

AchievementFamily -> AchievementInstance ----+
                                            |
PersonalMilestoneEvent ----------------------+--> PersonalHistoryRecordSet
                                                     |
                                                     v
                                                PersonalLegend
                                                     X no history/state rewrite

selected PersonalCapabilityState -----------+
selected PersonalHistoryRecordSet ----------+
selected PersonalLegend --------------------+--> PlayerWindow (PR9)
selected verified ProgressionFrontier -------+          |
                                                        v
                                             self-contained local HTML
                                                        X no mutation/publication authority
```

The important boundaries are:

```text
PILOT CAPTURE != EVIDENCE
PILOT RESPONSE != CLAIM
PILOT ARTIFACT != EVALUATION
RUNNER != EVALUATOR
CAPTURE COMPLETENESS != CAPABILITY
DECLARED HUMAN ORIGIN != AUTHENTICATED HUMAN ORIGIN
VALID WORKSPACE != AUTHENTICATED SESSION HISTORY
SNAPSHOT SHA-256 != EVIDENCE AUTHORITY

EVIDENCE != CAPABILITY
CLAIM != CAPABILITY
EVALUATION != CAPABILITY
MODEL STATE != PERSON

PR4 COMPOSES EVALUATIONS
PR4 DOES NOT RE-EVALUATE EVIDENCE

STATE DOES NOT INTERPRET RAW EVIDENCE
STATE BASIS PASSES THROUGH ClaimEvaluation

SELECTED EVALUATION != TRUTH
SELECTION != AUTHORITY

CONCEPT EXISTS != SUBJECT HAS CAPABILITY
DOMAIN GRAPH != UNIVERSAL CURRICULUM
EDITORIAL FAMILY MEMBERSHIP != SPECIALIZES
GRAPH DEPTH != DIFFICULTY
GRAPH CENTRALITY != HUMAN IMPORTANCE

PROPOSAL != ACCEPTED OBJECT
MODEL OUTPUT != AUTHORITY
RECOMMEND_ACCEPT != MATERIALIZATION
CLAIM PROPOSAL != CAPABILITY CLAIM
RELATION PROPOSAL != CAPABILITY RELATION
SHARED TARGET != SHAREABLE PROPOSAL
POLICY REF != AUTHENTICATED POLICY
OPAQUE ID != CONTENT HASH
SERIALIZED != ACCEPTED
PERSISTED != AUTHORITATIVE

HISTORY != CURRENT STATE
ACHIEVEMENT INSTANCE != EVIDENCE RECORD
SUPPORTED STATE != ACHIEVEMENT EVENT
CURRENT READINESS LOSS != ACHIEVEMENT ERASURE
ACHIEVEMENT INSTANCE != PERSONAL MILESTONE
MILESTONE != TROPHY
LEGEND != HISTORY
LEGEND != EVIDENCE / CLAIM / STATE / PERSON IDENTITY
LEGEND SOURCE != LEGEND
PERSONAL LEGEND != CANONICAL SELF-NARRATIVE

PROGRESSION FRONTIER != RECOMMENDATION
FRONTIER CANDIDATE != NEXT REQUIRED STEP
PREREQUISITE EVIDENCE GAP != MISSING CAPABILITY
PREREQUISITE GAP != PROHIBITION / ACCESS CONTROL
NO GAP != READY / SAFE / PERMITTED
PROGRESSION FOCUS != GOAL / INTEREST / IDENTITY
EXPLORATION OPPORTUNITY != RECOMMENDATION
SERIALIZED FRONTIER != VERIFIED DERIVATION
VERIFIED DERIVATION != AUTHENTICATED SOURCE SNAPSHOT

PLAYER WINDOW != PERSONAL DEVELOPMENT MODEL
PLAYER WINDOW != PERSON / CURRENT TRUTH / AUTHORITY
DISPLAYED != CANONICAL
OMITTED != ABSENT
WINDOW SELECTION != IMPORTANCE / COMPLETENESS / SUBJECT ENDORSEMENT
LATEST STATE / LEGEND / FRONTIER != AUTOMATIC WINDOW INPUT
VISIBLE LEGEND MUST NOT HIDE ITS SOURCE HISTORY
VISIBLE FRONTIER MUST NOT HIDE ITS PERSONAL-STATE BASIS
STRUCTURALLY VALID WINDOW != VERIFIED WINDOW
VERIFIED WINDOW != AUTHENTICATED SOURCE SNAPSHOT
RENDERED HTML != VERIFIED WINDOW
LOCAL HTML != PUBLICATION / AUTHORIZATION
NO NETWORK REQUEST != SAFE TO SHARE

UNKNOWN != ZERO
INSUFFICIENT != LOW
SUPPORTED != MASTERY
CONFLICT != SUFFICIENCY
```

## Shared semantics

PR1 provides reusable shared semantics:

- `CapabilityNamespace`;
- stable `CapabilityId`;
- exact `CapabilityConceptRef` revisions;
- immutable `CapabilityConcept` records;
- structural, dependency, and empirical-development relation families;
- deterministic strict `CapabilityCatalog` snapshots.

Shared capability concepts contain no assertion that a particular person has the capability.

## Epistemic records

PR2 provides the person-scoped epistemic layer:

- `EvidenceRecord` with explicit context, outcomes, observation time, provenance, and source kind;
- `CapabilityClaim` as a stable scoped proposition against an exact `CapabilityConceptRef`;
- `ClaimEvaluation` with evaluator identity, exact evaluation policy, claim-relative evidence assessments, coverage, conflict, and conclusion;
- deterministic `EpistemicRecordSet` validation and strict serialization.

Evidence intentionally does not know what capability it proves. The same evidence may support one claim, contradict another, and be indeterminate for a third.

## Personal capability state

PR3 defines the representation of derived state.

A `CompetenceFrame` provides a versioned, domain-defined decomposition such as execution, diagnosis, transfer, or independence. These dimension keys are **frame-local**, not universal dimensions of every person or domain.

A `CompetenceDimensionState` separates:

```text
support standing:
  UNKNOWN
  INSUFFICIENT
  SUPPORTED

conflict status:
  NONE
  RESOLVED_BY_POLICY
  UNRESOLVED
```

This allows honest combinations such as `SUPPORTED + UNRESOLVED` without collapsing conflict into a mastery level.

`PersonalCapabilityState` contains no canonical mastery percentage, XP, rank, or universal novice/intermediate/expert label. Its supported content remains explicit scoped claims traceable to basis `ClaimEvaluation` records.

`PersonalCapabilityStateSet` is structurally one-subject and private by default.

## Deterministic supported-state derivation

PR4 provides the first deterministic bridge from PR2 evaluations into PR3 state.

`DeterministicStateDerivationRequest` supplies the exact subject, capability concept revision, competence-frame revision, historical `as_of` boundary, caller-supplied state identity, selected evaluation ids, and explicit `ClaimDimensionBinding` values. The derivation implementation fixes its own policy and rule-deriver identity rather than allowing callers to relabel the algorithm.

Baseline v1 derives only support standing and unresolved conflict from the explicitly selected evaluation set. Unselected evaluations are inert. Evaluator kind, evaluator identity, evaluation-policy identity, evidence reliability, coverage, evidence counts, and recency do not become hidden derivation weights.

The derivation layer is stateless. Historical cross-snapshot ID immutability and no-ID-reuse remain persistence/import governance responsibilities rather than hidden registry behavior inside PR4.

## Civilization Bootstrap seed domain

PR5 provides the first real multi-domain semantic graph in the `civilization_bootstrap` namespace.

The seed is curated in eight editorial families spanning technical inquiry, materials, energy, fabrication, machines, electrical/information systems, infrastructure, and life systems. It also contains eight broad capability concepts. Those families are curation structure, not automatic semantic edges, and there is deliberately no `technical_generalist` or global root capability.

Seed v0 contains:

```text
63 active concepts @1
2 SPECIALIZES
51 scoped SUPPORTED_BY
1 scoped REQUIRES
3 scoped ENABLED_BY
0 empirical-development edges
```

The only structural specialization edges in v0 are:

```text
electrical_measurement SPECIALIZES physical_measurement
dimensional_metrology SPECIALIZES physical_measurement
```

This is intentionally sparse. `SPECIALIZES` is not used merely to make an editorial family look like a tree.

Every dependency edge is explicitly scoped. `SUPPORTED_BY` is preferred for useful dependencies that do not justify categorical necessity. The only retained `REQUIRES` edge is:

```text
low_voltage_power_distribution
    REQUIRES basic_electricity
    scope = conceptual_analysis
```

Two initially stronger dependencies were deliberately downgraded during adversarial review because alternative routes exist: embedded programming strongly supports microcontroller sensing, and microbiology strongly supports potable-water treatment, but neither is encoded as a universal categorical barrier in seed v0.

`RelationScope` remains PR1 relation-local semantics. Reusing a key such as `conceptual_analysis` across edges does not create a global scope identity or license downstream code to merge unrelated relations solely by key.

The seed does not invent `COMMONLY_PRECEDES`, `COMMONLY_COOCCURS`, or `TRANSFER_OBSERVED_TO` edges because PR5 has no empirical development dataset whose provenance would justify them.

PR5 also defines:

```text
civilization_bootstrap:technical_competence@1
```

with the non-ordinal dimensions:

```text
conceptual_knowledge
calculation
execution
diagnosis
transfer
independence
explanation
```

A real integration smoke sends `civilization_bootstrap:basic_circuits@1` through PR2 evidence/claim/evaluation, PR4 derivation, and PR3 state. Supported conceptual/calculation claims do not silently create supported execution, diagnosis, transfer, independence, or explanation.

## Capability proposals and model non-authority

PR6 adds immutable proposal and review records without adding an application/materialization engine.

`CapabilityProposal` supports six v1 candidate families:

```text
CREATE_CONCEPT
REVISE_CONCEPT
SPLIT_CONCEPT
MERGE_CONCEPTS
CREATE_RELATION
CREATE_CLAIM
```

Candidate payloads are deliberately not accepted core records. A `ConceptCandidateSpec` does not reserve its suggested id or semantic revision and cannot implicitly create a namespace. A relation candidate stores exact concept revisions for audit, while an accepted PR1 relation remains a separate semantic record. A claim candidate is not a PR2 claim and cannot enter PR4 state derivation.

Generators and reviewers identify their mechanism kind (`HUMAN`, `RULE`, `MODEL`, `HYBRID`, `EXTERNAL_SYSTEM`) and exact proposal/review policy refs. Mechanism kind never grants authority. Policy refs are exact syntactic identifiers, not policy content hashes, signatures, authenticated registry entries, or authority grants.

Reviews remain separate immutable facts with recommendation verdicts only:

```text
RECOMMEND_ACCEPT
RECOMMEND_REJECT
REQUEST_REVISION
ABSTAIN
```

Conflicting reviews may coexist. PR6 does not majority-vote, prefer latest review, prefer human over model, infer reviewer authority, or expose `proposal.status` / `is_approved`.

`CapabilityProposalSet` is one-scope: shared proposals (`subject_ref=None`) cannot mix with person-scoped proposals, and private proposal sets cannot mix subjects. Internal PR2 evidence/claim/evaluation basis requires the same person scope. A proposal for shared semantics may therefore remain private when it was motivated by private evidence. Known internal PR2 record IDs cannot be laundered through relation provenance or by relabeling them as `EXTERNAL_ARTIFACT` / `OTHER`; an unknown external ref nevertheless remains opaque and is not proven public/shareable merely because it is absent from the supplied epistemic snapshot.

Explicit validation against a `CapabilityCatalog` requires exact existing revisions and rejects stale targets rather than silently substituting latest semantics. Strict deterministic JSON serialization accepts one explicit extended ISO-8601 timestamp profile, canonicalizes valid offsets to UTC, and preserves proposal/review history without granting acceptance.

Proposal/review IDs are opaque and unique within one `CapabilityProposalSet`, not globally content-addressed identities. Cross-snapshot no-reuse, persistence transactions, policy-registry authenticity, sync reconciliation, and publication authorization remain outside PR6.

PR6 intentionally exposes no `apply_proposal`, `accept_proposal`, `materialize_proposal`, `proposal_to_claim`, persistence authority, or equivalent shortcut.

## Achievement, milestone, and Legend history

PR7 adds history without turning history into current capability state or gamified progression.

`AchievementFamily` is shared, revisioned accomplishment semantics. `AchievementInstance` is a private person-scoped immutable record referencing one exact family revision and explicit qualification context. Every v1 achievement requires at least one event-bearing `EvidenceRecord` or `EXTERNAL_ARTIFACT` basis; PR3 current state is not an achievement basis.

```text
ACHIEVEMENT FAMILY != ACHIEVEMENT INSTANCE
ACHIEVEMENT INSTANCE != PERSONAL CAPABILITY STATE
ACHIEVEMENT INSTANCE != EVIDENCE RECORD
SUPPORTED STATE != ACHIEVEMENT EVENT
CURRENT READINESS LOSS != ACHIEVEMENT ERASURE
```

A repeatable family may have many genuine instances, but inside one `PersonalHistoryRecordSet` the same exact event-bearing basis cannot be replayed as multiple instances of one stable family merely by changing id, timestamp, or revision. This is snapshot-local anti-replay, not global event fingerprinting: timestamps/windows do not define event identity, and distinct refs do not prove distinct real events.

`PersonalMilestoneEvent` is independent person-scoped history and may represent success, failure, a decision, transition, abandoned path, or unique event without any achievement family. `significance_note` is attributed recorder content, not subject endorsement or scalar importance.

`PersonalHistoryRecordSet` is deterministic, private, and one-subject. It enforces subject isolation, history-id separation, exact family revision validation, causal source boundaries, typed internal PR2 references, and protection against relabeling exact history IDs into PR2 provenance/payload to manufacture a `history -> evidence -> history` cycle.

Historical backfill distinguishes event time from record time. Event-bearing evidence must describe the event no later than the milestone/achievement event, while later documentary claims/evaluations may support honest backfill only if they exist by the immutable history `recorded_at` boundary. A milestone cannot cite an achievement record that did not yet exist when the milestone itself was recorded.

`PersonalLegend` is a separate source-backed narrative projection over `AchievementInstance` and `PersonalMilestoneEvent` records. It cannot directly cite evidence, claims, evaluations, state, or another Legend. A cited source event must respect the Legend `as_of` boundary and its immutable record must exist by `generated_at`. One exact source cannot be repeated across several entries of the same Legend merely to amplify it, while different alternative Legends may reuse the same history source.

```text
ACHIEVEMENT INSTANCE != PERSONAL MILESTONE
MILESTONE != TROPHY
MILESTONE SIGNIFICANCE != GLOBAL IMPORTANCE

LEGEND != HISTORY
LEGEND != EVIDENCE
LEGEND != CLAIM
LEGEND != STATE
LEGEND != PERSON IDENTITY
LEGEND SOURCE != LEGEND
LEGEND OMISSION != HISTORY DELETION
PERSONAL LEGEND != CANONICAL SELF-NARRATIVE
```

History, milestone, and Legend IDs remain opaque and snapshot-local rather than global content hashes. Exact `AchievementFamilyRef` is revision identity, not authenticated historical content. Qualifier/recorder/Legend-generator mechanism kinds, including `MODEL`, are declared context rather than authority, subject endorsement, or automatic truth.

PR7 deliberately exposes no XP/points/tier/rank, `unlock_achievement`, auto-award, history→state derivation, legend→evidence/claim/state, in-place history correction, deletion, or retraction workflow. Immutable history does not mean irretractable falsehood: correction/retraction remains a future append-only governance boundary.

## Progression frontier, prerequisite evidence gaps, and exploration

PR8 adds the first executable advisory progression layer without turning graph adjacency into curriculum authority.

`ProgressionFrontierRequest` contains only explicit request-local inputs: subject, `as_of`/`generated_at`, requester mechanism, explicit focus, selected state/dimension seed bindings, explicit prerequisite checks, and preserved exploration inputs. PR8 does not auto-select the latest state, infer a goal or interest, read history/Legend as a progression signal, or interpret raw evidence directly.

The deterministic baseline considers only direct one-hop `SPECIALIZES`, `REQUIRES`, `SUPPORTED_BY`, and `ENABLED_BY` relations whose target is an explicitly selected supported seed capability. Stored PR1 dependency direction remains source capability → dependency/supporting capability. Multiple adjacency witnesses preserve provenance but do not create score or priority.

```text
PROGRESSION FRONTIER != RECOMMENDATION
FRONTIER CANDIDATE != NEXT REQUIRED STEP
FRONTIER CANDIDATE != READINESS / PERMISSION
DIRECT RELATION != OPTIMAL PATH
ONE-HOP FRONTIER != CURRICULUM
RELATION STRENGTH != FRONTIER PRIORITY
```

Only a real categorical `REQUIRES` relation may produce a `PrerequisiteEvidenceGap`, and only through an explicit request-local `PrerequisiteCheckBinding` from exact relation scope to exact competence-frame dimensions. `SUPPORTED_BY` and `ENABLED_BY` do not become prerequisites. Missing binding stays `unassessed_prerequisites`; an explicit binding with no state yields `NO_SELECTED_STATE`; selected state dimensions may yield `UNKNOWN` or `INSUFFICIENT` gaps.

```text
PREREQUISITE EVIDENCE GAP != MISSING CAPABILITY
UNASSESSED PREREQUISITE != SATISFIED PREREQUISITE
PREREQUISITE GAP != PROHIBITION / ACCESS CONTROL
NO GAP != READY / SAFE / PERMITTED
RELATION SCOPE != COMPETENCE DIMENSION
```

`ProgressionFocus` is a request-local direction marker, not a stored Goal, Interest, identity statement, or authority claim. It may overlap a genuinely adjacent derived candidate, but an exact selected seed cannot also be supplied as focus because seed basis and projected direction remain distinct. At most one seed state for one exact seed concept may be selected per request, preventing state-id-only witness amplification without introducing an automatic newest-state rule.

`ExplorationInput` is explicit preservation rather than automatic graph-distance novelty generation. An exploration-only concept becomes an `ExplorationOpportunity`, not a frontier candidate or recommendation. A previous frontier, history record, Achievement, or Legend is not an input to PR8 derivation, preventing a hidden self-confirming projection loop by construction.

Strict request/frontier/frontier-set serialization is deterministic and structural. Deserialization alone does not prove that a frontier was produced by the frozen baseline. `validate_progression_frontier_v1(...)` reconstructs the stored effective request, re-derives against supplied semantic/frame/epistemic/state snapshots, and requires exact output equality.

```text
SERIALIZED FRONTIER != VERIFIED DERIVATION
DESERIALIZED FRONTIER != VERIFIED DERIVATION
VERIFIED DERIVATION != AUTHENTICATED SOURCE SNAPSHOT
EXACT CONCEPT REF != CONTENT HASH / SIGNATURE
```

The verifier proves consistency with supplied snapshots, not publisher identity, archive authenticity, or that an exact same-ref semantic snapshot existed at historical `frontier.as_of`. PR8 intentionally adds no signature/content-address registry, persistence/sync, ranking, path optimization, safety/licensing inference, permission engine, or Player Window UI.

## Player Window and local product projection

PR9 adds the first executable private product read model without turning presentation into a new source of truth. `PlayerWindowRequest` explicitly selects the exact state, achievement, milestone, optional Legend, and optional frontier records to include. There is no automatic latest/current/best source selection.

```text
selected PR3 state
      +
selected PR7 history / optional Legend
      +
selected PR8 frontier
      |
      v
PlayerWindow
      |
      v
render_player_window_html_v1(...)
      |
      v
self-contained local HTML
```

Every selected capability state is projected with the complete dimension set of its exact competence frame. `UNKNOWN`, `INSUFFICIENT`, `SUPPORTED`, and conflict remain visible; PR9 does not expose a Human Level, XP, score, rank, growth metric, readiness scalar, domain percentage, or recommendation priority.

Visible narrative and advisory projection must preserve inspectability. A selected Legend cannot hide cited selected history. A selected frontier cannot hide any selected personal-state seed/prerequisite basis. A verified milestone sourced from an achievement must preserve that selected history source closure. Window source selection itself is not truth, importance, completeness, or subject endorsement.

`validate_player_window_v1(...)` is the explicit source-backed verification boundary. It validates exactly selected PR3 states against their governing PR1/PR2/frame snapshots, validates exactly selected PR7 history/Legend against family/epistemic/history contracts, validates a selected PR8 frontier by PR8 exact re-derivation, then re-derives the PR9 read model and requires exact equality. Unselected state/history/Legend records remain inert.

```text
STRUCTURALLY VALID WINDOW != VERIFIED WINDOW
DESERIALIZED WINDOW != VERIFIED WINDOW
VERIFIED WINDOW != AUTHENTICATED SOURCE SNAPSHOT
RENDERED HTML != VERIFIED WINDOW
DISPLAY SUMMARY != CANONICAL SOURCE PROVENANCE
```

The dependency-free HTML renderer accepts only a ready `PlayerWindow`; it cannot select source records or infer latest/best/current semantics. It escapes source text, embeds CSS, uses no JavaScript or remote assets/analytics, and emits a strict local CSP. The bundled demo first derives and verifies the real Civilization Bootstrap Player Window before rendering it.

```bash
python -m capability_lab.player_window.demo --output player_window.html
```

The output is private product data, not a publication or authorization artifact. Network silence does not make a copied HTML file safe to share, and PR9 defines no sharing, export-consent, redaction, signature, artifact-authentication, persistence, or public-profile workflow.

```text
LOCAL != PUBLIC
NO NETWORK REQUEST != SAFE TO SHARE
HTML FILE COPY == DATA EXPORT
VIEWER REF != EXPORT AUTHORIZATION
LOCAL HTML != PUBLICATION PERMISSION
```

## Civilization Bootstrap Pilot 01 private raw-capture boundary

PR10.0 adds the first real participant-session capture surface for `civilization_bootstrap:basic_electricity@1` without granting raw responses epistemic authority.

The frozen protocol is:

```text
civilization_bootstrap:pilot_01_basic_electricity@1
```

with three required text probes (`conceptual_explanation`, `calculation_work`, `diagnosis_reasoning`) and plural optional `execution_artifact` captures. Protocol/runtime code is versioned; participant data belongs in a private local workspace, conventionally below:

```text
.local/pilots/cb01/
```

The public runner surface is deliberately narrow:

```text
init
show-protocol
record-text
record-artifact
validate
```

It does not expose generation, grading, evaluation, evidence materialization, state derivation, progression derivation, or Player Window production. The supported mutation path stages before publication, refuses append over an invalid workspace, validates exact capture/artifact closure, preserves multiple optional execution captures, and revalidates after mutation. Public validation performs a stable double read and reports a deterministic `snapshot_sha256` over relative workspace shape and exact bytes.

```text
PILOT CAPTURE != EVIDENCE
PILOT RESPONSE != CLAIM
PILOT ARTIFACT != EVALUATION
RUNNER != EVALUATOR

CAPTURE COMPLETENESS != CAPABILITY
MISSING OPTIONAL EXECUTION != FAILURE

DECLARED HUMAN ORIGIN != AUTHENTICATED HUMAN ORIGIN
VALID WORKSPACE != AUTHENTICATED SESSION HISTORY
SNAPSHOT SHA-256 != TRUSTED TIMESTAMP / AUTHORSHIP / EVIDENCE AUTHORITY
```

The artifact-capture layout spans an artifact directory and a capture JSON, so PR10.0 does not claim impossible portable multi-path atomicity. A crash between the two final publications may leave an orphan artifact directory; that state is invalid, cannot accept further captures, and is not silently repaired into participant history.

The next real-pilot step is therefore **not** automatic `Capture -> Evidence`. The first live session should produce a validated private raw snapshot; a later explicitly reviewed boundary can decide how particular captures become PR2 `EvidenceRecord` material without retroactively changing PR10.0 capture semantics.

## Subject and actor roles

The person being modeled is the `CapabilitySubject`, represented in current records by `CapabilitySubjectRef`. That role is not automatically the same actor as the operator, evaluator, state deriver, evidence contributor, proposal generator/reviewer, achievement qualifier, milestone recorder, Legend generator, progression requester/deriver, Player Window requester, or Player Window viewer.

Opaque subject/evaluator/deriver/generator/reviewer/qualifier/recorder/requester/viewer refs are interpreted inside their identity/import governance. Equal strings from unrelated stores are not automatically proof of the same real-world identity.

Capability Lab must not treat incidental observations about another person as permission to construct or publish a persistent capability, history, progression, or Player Window profile about them.

## Core invariants

- Capability is not directly observed; evidence supports claims about capability.
- A Pilot 01 capture is raw private participant material, not an `EvidenceRecord`, claim, evaluation, or capability state by construction.
- A valid Pilot 01 workspace proves local structural/content consistency under the frozen protocol, not authenticated human authorship, true event time, or evidentiary authority.
- Evidence is not capability, and a claim/evaluation/state record does not define the person.
- Capability is not human worth, intelligence, identity, interest, or desired direction.
- Capability is not a credential, license, permission, or authority.
- `UNKNOWN` is first-class and is not silently converted to zero.
- A failed attempt is evidence/outcome, not a capability level by itself.
- Conflicting evidence/evaluations may remain unresolved; the system must not fabricate certainty.
- Support standing and conflict remain independent axes.
- A canonical global `Human Level` or mastery score is forbidden.
- Domain graph position, depth, degree, or centrality must not become a hidden human score.
- Editorial grouping must not silently become structural or developmental semantics.
- Subject-scoped pilot captures, evidence, proposals, state, history, Legends, progression frontiers, and Player Windows are private by default.
- Model output is not authority merely because it is structurally valid, positively reviewed, serialized, deserialized, persisted, attributed as a history mechanism, used as a projection requester, or displayed in Player Window.
- Proposal/review validity does not imply materialization, publication, permission, or accepted person truth.
- Historical record validity does not imply current readiness, publication, subject endorsement, or authenticated workflow acceptance.
- Current readiness loss does not erase honestly recorded historical accomplishment.
- Achievement/milestone counts do not become capability or human-progress scores.
- Legend selection/order/omission does not become global importance or official identity narrative.
- Frontier membership/order/witness count does not become recommendation priority or readiness.
- Prerequisite evidence gaps do not become missing-capability assertions, prohibitions, or access control.
- Player Window selection/order/omission does not become canonical person truth, importance, completeness, readiness, or permission.
- Rendering or copying local HTML does not create publication/share authorization or artifact authenticity.
- Exact proposal/review/history/progression/Player Window policy refs do not themselves authenticate policy content or grant authority.
- Consequential interpretations remain tied to identifiable exact policies and provenance.
- The capability subject must be able to contest person-scoped claims where they participate in the system.
- Common aggregate paths are descriptive by default, not causal, required, or optimal.
- Exploration outside the currently inferred profile must remain possible.

See [`docs/constitution.md`](docs/constitution.md) for the normative constitutional boundaries.

## Documents

- [`docs/constitution.md`](docs/constitution.md) — normative project boundaries and invariants;
- [`docs/vocabulary.md`](docs/vocabulary.md) — terminology refined through the implemented layers;
- [`docs/architecture.md`](docs/architecture.md) — current semantic / epistemic / state / derivation / domain / proposal / history / progression / Player Window / pilot-capture boundaries;
- [`docs/state_v1.md`](docs/state_v1.md) — normative PR3 state representation contract;
- [`docs/derivation_v1.md`](docs/derivation_v1.md) — normative PR4 deterministic derivation contract;
- [`docs/derivation_history_boundary_v1.md`](docs/derivation_history_boundary_v1.md) — PR4 historical/recomputation and persistence-governance boundary;
- [`docs/domains/civilization_bootstrap.md`](docs/domains/civilization_bootstrap.md) — normative PR5 Civilization Bootstrap seed contract;
- [`docs/domains/civilization_bootstrap_adversarial_semantics_v0.md`](docs/domains/civilization_bootstrap_adversarial_semantics_v0.md) — PR5 adversarial ontology/relation-semantics review contract;
- [`docs/proposals_v1.md`](docs/proposals_v1.md) — normative PR6 proposal and model non-authority contract;
- [`docs/proposal_authority_adversarial_v1.md`](docs/proposal_authority_adversarial_v1.md) — PR6 primary proposal-authority adversarial review;
- [`docs/proposal_second_adversarial_v1.md`](docs/proposal_second_adversarial_v1.md) — PR6 strict-ingestion, privacy-classification, policy-ref, ID, and persistence-boundary review;
- [`docs/history_v1.md`](docs/history_v1.md) — normative PR7 achievement / milestone / Legend history contract;
- [`docs/history_integrity_adversarial_v1.md`](docs/history_integrity_adversarial_v1.md) — PR7 primary history-integrity adversarial review;
- [`docs/history_second_adversarial_v1.md`](docs/history_second_adversarial_v1.md) — PR7 opaque-ID, backfill-causality, family-authenticity, source-amplification, and model non-authority review;
- [`docs/progression_v1.md`](docs/progression_v1.md) — normative PR8 progression frontier / prerequisite evidence-gap / exploration contract;
- [`docs/progression_authority_adversarial_v1.md`](docs/progression_authority_adversarial_v1.md) — PR8 primary progression-authority and source-backed verification review;
- [`docs/progression_second_adversarial_v1.md`](docs/progression_second_adversarial_v1.md) — PR8 focus/seed separation, partial prerequisite coverage, conflict-bearing seeds, historical reconstruction, and source-authenticity boundary review;
- [`docs/player_window_v1.md`](docs/player_window_v1.md) — normative PR9 Player Window read-model and local-product contract;
- [`docs/player_window_integrity_authority_adversarial_v1.md`](docs/player_window_integrity_authority_adversarial_v1.md) — PR9 presentation-integrity, selected-state governance, authority, and HTML-safety review;
- [`docs/player_window_second_adversarial_v1.md`](docs/player_window_second_adversarial_v1.md) — PR9 selected-history/Legend governance, source-snapshot, historical reconstruction, rendered-artifact, and privacy/export review;
- [`docs/pilots/civilization_bootstrap_pilot_01.md`](docs/pilots/civilization_bootstrap_pilot_01.md) — normative PR10.0 Pilot 01 protocol/private-workspace contract;
- [`docs/pilots/civilization_bootstrap_pilot_01_boundary_adversarial_v1.md`](docs/pilots/civilization_bootstrap_pilot_01_boundary_adversarial_v1.md) — PR10.0 raw-capture provenance, workspace-closure, protocol-substitution, and authority-boundary review;
- [`docs/pilots/civilization_bootstrap_pilot_01_transaction_recovery_adversarial_v1.md`](docs/pilots/civilization_bootstrap_pilot_01_transaction_recovery_adversarial_v1.md) — PR10.0 transaction, interruption, recovery, TOCTOU, and deterministic-replay review;
- [`docs/roadmap.md`](docs/roadmap.md) — initial PR sequence.

## Relationship to HDE

Capability Lab is not `hde-core` and does not own HDE identity, canonical memory, consent, action authorization, companion evolution, or Continuum records. It remains independently testable and may later integrate through explicit interfaces.

A future integration may look roughly like:

```text
Continuum ------> history/evidence candidates
PracticeLens ---> evaluations
Projects -------> artifacts
HDE Core -------> approved context + trust boundaries
                       |
                       v
                 Capability Lab
                       |
          +------------+------------+
          |            |            |
       Graph      Player Window   Frontier
```

These adapters must not bypass Capability Lab's provenance, policy, privacy, proposal non-authority, history-integrity, state-governance, progression non-authority, Player Window source-visibility, or Pilot 01 raw-capture/evidence boundary.

## Near-term roadmap

PR0–PR9 provide the governed modeling/product foundation. PR10.0 now provides the bounded private capture surface required to begin the **first real Civilization Bootstrap pilot** without pre-declaring participant responses as evidence.

The immediate next workflow is deliberately two-stage:

```text
Stage A — real private capture
frozen Pilot 01 protocol
        -> participant responses / optional artifacts
        -> validated private raw workspace
        -> snapshot_sha256

Stage B — later reviewed epistemic materialization
selected raw captures
        -> explicit reviewed Capture -> Evidence boundary
        -> claims / evaluations
        -> selected capability state
        -> preserved history / optional Legend
        -> advisory frontier
        -> verified Player Window
        -> private local HTML
```

Stage B is **not implemented by PR10.0**. The first live session should therefore teach us where the capture/evidence boundary needs to be designed from real material rather than from synthetic fixtures.

## Development

```bash
python -m pip install -e .
python -m pytest -q
```

Inspect the frozen Pilot 01 protocol with:

```bash
python -m capability_lab.pilots.civilization_bootstrap_01.run show-protocol
```

Create a private Pilot 01 workspace inside the repository's ignored `.local/` boundary with explicit subject/session/timestamp values, then record participant-provided captures using the runner's `record-text` / `record-artifact` commands and finish with:

```bash
python -m capability_lab.pilots.civilization_bootstrap_01.run validate --workspace .local/pilots/cb01
```

A structurally valid incomplete workspace still returns `capture_complete=false`; incompleteness is not participant failure. `snapshot_sha256` identifies validated local bytes/shape under the Pilot 01 fingerprint scheme, not authenticated history or evidence authority.

Generate the existing PR9 local Civilization Bootstrap product projection with:

```bash
python -m capability_lab.player_window.demo --output player_window.html
```

The demo output is a private local artifact containing selected person-scoped projection data. It is intentionally network-silent, but copying or sharing the file is still a data export and is outside PR9 authorization/consent governance.

For the private repository, exact local Python 3.11 test passes on the reviewed remote HEAD are currently used as the merge gate when hosted Actions are unavailable.

## Project stage

Research prototype. Interfaces and terminology are expected to evolve under explicit review rather than silent semantic drift.
