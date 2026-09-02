# Capability Lab Constitution

Status: **Normative draft for PR0**

This document defines the constraints that later Capability Lab implementations must preserve. A feature that violates these invariants is not merely a different UI or policy choice; it changes the project into a different system.

## 1. Purpose

Capability Lab models evidence and governed claims about human capability over time and supports development-oriented projections from those records.

The project may help answer questions such as:

- What evidence exists that a person can perform or understand something?
- In which contexts was that evidence observed?
- What claims are currently supported by that evidence?
- How strong, broad, recent, and reliable is the support?
- What is unknown or weakly evidenced?
- Which prerequisite evidence appears missing for a chosen target?
- Which development paths are plausible next?
- Which events in the person's history are meaningful enough to preserve as achievements or milestones?

The project does **not** attempt to compute the value of a human being.

### 1.1 Capability is not directly observed

Capability Lab observes or receives records such as performances, artifacts, assessments, attestations, outcomes, and other evidence. It may derive governed claims from those records, but it does not directly observe an abstract capability itself.

Therefore:

```text
EVIDENCE != CAPABILITY
CLAIM != CAPABILITY
MODEL STATE != PERSON
```

A capability claim is an epistemic statement supported to some degree by evidence. It is not the capability itself and does not define the person.

### 1.2 Capability concepts must remain bounded and evidence-addressable

A `CapabilityConcept` must not silently encode a judgment about a person's total value, identity, intelligence, morality, desirability, or social status.

Shared capability concepts should be scoped so that evidence could meaningfully support or contradict claims about them in identifiable contexts. Broad or contested concepts may exist, but their scope, interpretation, and uncertainty must remain visible rather than being treated as essential traits of the person.

## 2. Foundational distinctions

The following distinctions are constitutional:

```text
CAPABILITY != HUMAN WORTH
CAPABILITY != INTELLIGENCE
CAPABILITY != IDENTITY
CAPABILITY != INTEREST
CAPABILITY != GOAL
CAPABILITY != CREDENTIAL
CAPABILITY != LICENSE
CAPABILITY != AUTHORITY
CAPABILITY != PERMISSION
```

No later convenience API may silently collapse these distinctions.

### 2.1 Capability is contextual

A person may demonstrate a capability in one context while remaining unobserved or weakly evidenced in another. `Circuit design` supported by low-voltage analog evidence does not automatically support RF, high-voltage, or industrial competence.

### 2.2 Capability does not imply destiny

A person being good at something does not imply that they should pursue it. Recommendations must keep ability, interest, goals, values, and exploration separate.

### 2.3 Capability does not grant authority

Demonstrated medical knowledge does not create a medical license. Demonstrated legal knowledge does not create authority to practice law. Demonstrated operational ability does not create permission to act.

### 2.4 Subject, operator, evaluator, and viewer are different roles

The person whose capability is being modeled is the `CapabilitySubject`. That role must not be silently conflated with the person or process operating the software, evaluating evidence, or viewing a projection.

```text
CAPABILITY SUBJECT != OPERATOR
CAPABILITY SUBJECT != EVALUATOR
CAPABILITY SUBJECT != VIEWER
```

One actor may hold multiple roles in a specific workflow, but the data model and authorization model must not assume that they are always the same actor.

### 2.5 Assistance and accommodation are context, not automatic disqualification

Use of tools, assistance, accessibility accommodations, collaboration, reference material, or automation may affect what a piece of evidence supports, but their presence must not automatically be treated as failure or lower human capability.

The relevant conditions should be represented as context so claims can distinguish, for example, independent execution from assisted execution without converting assistance into a moral or global deficit.

## 3. Epistemic rules

### 3.1 `UNKNOWN` is first-class

Absence of evidence is not evidence of absence.

If Capability Lab lacks sufficient information about a capability, the appropriate person-scoped state is `UNKNOWN`, not `0` or `novice` unless evidence specifically supports such a conclusion.

A failed attempt is an observation or outcome that may become evidence. `FAILED` is not, by itself, a capability level.

```text
FAILURE OBSERVATION != LOW CAPABILITY
```

Task difficulty, context, assistance, novelty, conditions, and repeated performance may all affect what a failure supports.

### 3.2 Claims require provenance

A consequential personal capability claim must be traceable to the evidence and transformation steps that support it.

At minimum, later claim models should be capable of expressing:

- supporting and contradicting evidence references;
- provenance/source;
- observed context and scope;
- evaluator or evaluation mechanism;
- evaluation policy/version;
- time and recency;
- unresolved conflicts where applicable.

### 3.3 Conflicting evidence must remain representable

Capability Lab must not require contradictory observations or evaluations to be silently averaged into a single clean answer.

Where meaningful conflict remains unresolved, the system must be able to preserve that conflict and expose an unresolved, mixed, or policy-dependent state rather than fabricate certainty.

Different evaluators or policies may legitimately produce different scoped claims from the same underlying evidence. Their provenance must remain distinguishable.

### 3.4 Evidence types are not equivalent

Self-report, conversation observation, quiz performance, artifact review, repeated project performance, external assessment, and real-world demonstration may all be useful, but they must not be treated as interchangeable proof.

### 3.5 Epistemic dimensions must not be collapsed prematurely

A single field named `confidence` must not silently stand in for multiple distinct properties. Later models should be able to distinguish at least conceptually between:

- **evidence reliability** — how trustworthy the evidence record or source appears;
- **claim support** — how strongly the available evidence supports a particular claim;
- **coverage** — which contexts, dimensions, difficulty ranges, or conditions were actually observed;
- **recency** — how current the supporting evidence is.

Other calibrated uncertainty measures may be added later, but their semantics must remain explicit.

### 3.6 Precision must be earned

The system must not emit artificially precise scores where the evidence cannot justify that precision. A visually convenient percentage is not automatically an epistemically meaningful measurement.

### 3.7 Multiple capability dimensions are allowed and expected

A single scalar `mastery` is not assumed to be sufficient. Later domain models may separately represent dimensions such as:

- conceptual knowledge;
- calculation;
- construction/execution;
- diagnosis;
- transfer to unfamiliar contexts;
- independence;
- teaching/explanation;
- retention or current readiness.

The exact dimensions are domain-dependent and must not be treated as universal merely because one pack uses them.

### 3.8 Accepted state is governed state, not canonical truth about a person

The term `canonical` is reserved for governed shared artifacts such as concept identifiers, namespace entries, schema versions, or published definitions. Capability Lab must not describe a person-scoped capability assessment as `canonical truth`.

Person-scoped assessments should use terms such as `supported claim`, `accepted claim`, or `current supported state`, with provenance and policy version available for inspection.

## 4. Human agency rules

### 4.1 No canonical Human Level

Capability Lab must not define an official scalar function of the form:

```text
human -> one global score
```

No canonical system state may claim to measure total human level, value, intelligence, or rank.

A game-inspired UI may expose a local decorative progression indicator only if that indicator:

- is explicitly non-canonical;
- is not presented as a capability estimate, intelligence estimate, or measure of human value;
- is not used for eligibility, authority, licensing, or permission;
- is not used by Capability Lab for interpersonal ranking;
- is not assumed to be comparable between people unless a future explicitly bounded competitive context defines its own separate rules.

### 4.2 The capability subject must be able to contest person-scoped claims

Where the subject participates in Capability Lab, they must be able to inspect, challenge, annotate, correct, or request removal of claims about themselves, subject to provenance-preservation, external-attestation, and applicable policy constraints.

The system's statement is always equivalent to "the current evidence supports...", not "this is what you are."

An operator, evaluator, employer, parent, teacher, or other viewer must not automatically inherit unrestricted authority over the subject's private development model merely because they contributed evidence or operate an interface.

### 4.3 Exploration must remain possible

Progression recommendations must not trap a subject inside the current model of them. The architecture must support exploration of low-evidence and unrelated domains.

A low predicted fit, weak evidence, or missing prerequisite claim is not a prohibition.

### 4.4 No coercive engagement mechanics

Capability Lab must not use shame, guilt, punitive loss framing, artificial anxiety, or coercive engagement mechanics to manipulate continued participation.

Optional reminders, challenges, streak-like views, or milestones may exist only when they preserve user agency and do not make punishment, guilt, or loss the mechanism of retention.

## 5. Privacy, control, and sharing rules

### 5.1 Person-scoped development data is private by default

Raw evidence, failed attempts, private weaknesses, abandoned paths, interests, inferred goals, and personal history are not public commons data merely because they can be represented by the system.

### 5.2 Shared concepts are not shared personal state

A shared `CapabilityConcept` such as `electric_motor_construction` may exist in the commons. A person's evidence and state for that concept remain person-scoped unless explicitly shared, published, synchronized, or aggregated under a separate policy.

### 5.3 Node existence may itself be sensitive

The fact that a person has a capability, interest, evidence record, or learning path may reveal sensitive information. Privacy design must therefore protect not only evidence payloads but also membership and graph structure where appropriate.

### 5.4 Development telemetry is not employment telemetry by default

A personal development system must not silently become a worker-monitoring system. Any future organizational sharing must expose narrow, explicitly authorized claims rather than default access to private learning history.

### 5.5 Server presence is not equivalent to public sharing

Capability Lab is local-first, but this constitution does not forbid encrypted backup, multi-device synchronization, explicit publication, or privacy-preserving aggregation.

Private capability state must not become centrally available to the Human Capability Commons or to third parties by default. Any synchronization, backup, publication, or aggregation requires an explicit scoped policy and must preserve the distinction between private person-scoped records and shared concepts.

### 5.6 Incidental observation is not authority to build a third-party profile

Capability Lab must not treat incidental data about another person as automatic authorization to construct, retain, publish, or aggregate a persistent capability model about that person.

Future workflows that model a person other than the operator must define an explicit subject/authority/consent policy appropriate to that workflow. PR0 does not attempt to encode every legal or guardian relationship, but it forbids silent third-party profiling as the default behavior.

## 6. Model and automation authority rules

LLMs or other learned models may later:

- propose candidate capability concepts;
- map evidence to existing concepts;
- suggest relations and prerequisites;
- summarize evidence;
- propose achievement names and narratives;
- suggest development paths and challenges;
- detect possible duplicates or ontology gaps.

They may not silently:

- create accepted person-scoped capability claims;
- treat model output as truth about a person;
- fabricate evidence or provenance;
- overwrite contradictory evidence;
- publish private graph state;
- convert a suggestion into permission or authority;
- promote a personal concept into the shared commons without governance.

The default pattern is:

```text
observation or source record
   -> interpretation/proposal
   -> governed validation/evaluation and/or review
   -> accepted state transition
```

A specific implementation may be deterministic, probabilistic, human-reviewed, or hybrid. The constitutional requirements are that consequential transitions are governed, auditable, provenance-preserving, and reproducible to the degree promised by the evaluation policy. PR4 may intentionally use a deterministic baseline without making determinism a permanent constitutional requirement.

## 7. Shared commons rules

A future Human Capability Commons may contain shared capability concepts, relations, achievement families, aliases, cultural interpretations, and privacy-preserving aggregate statistics.

It must not assume that there is one objectively correct decomposition of all human ability.

The commons must be able to accommodate:

- aliases and multilingual names;
- overlapping concepts;
- culturally specific interpretations;
- competing taxonomies;
- provisional concepts;
- contested definitions;
- versioned evolution.

Person-scoped models may contain concepts that never become shared concepts.

### 7.1 Relation semantics must distinguish kinds of knowledge

Capability relations must not treat all graph edges as epistemically equivalent. At minimum, later relation models should distinguish conceptually between:

- **structural relations** such as `specializes`, `generalizes`, or `overlaps`;
- **dependency relations** such as `requires`, `supports`, or `enables`;
- **empirical development relations** such as `commonly_precedes`, `commonly_cooccurs`, or evidence-supported transfer relations.

An empirical observation that A commonly precedes B must never silently become a claim that A is required for B.

### 7.2 Prerequisites are contextual

A prerequisite relation should not be assumed absolute unless its scope warrants that claim. Later models should be able to express context/scope, relation strength, and provenance.

Useful distinctions may include `hard requirement`, `strong preparation`, and `common preparation`, but PR0 does not freeze their final encoding.

### 7.3 Aggregate paths are descriptive by default, not causal or optimal

If aggregate data shows that one capability or experience commonly precedes another, that observation is descriptive unless a stronger causal claim is separately justified.

```text
COMMON PATH != REQUIRED PATH
COMMON PATH != CAUSAL PATH
COMMON PATH != OPTIMAL PATH
```

Progression systems must not silently convert popularity into prescription. Minority, culturally specific, accessibility-adapted, and genuinely novel paths must remain representable.

## 8. Achievement and milestone rules

Achievements and milestones record history. They are not equivalent to capability state.

A person's current readiness may decay while an honestly earned historical accomplishment remains part of their record.

The architecture should distinguish at least conceptually between:

- shared `AchievementFamily` semantics;
- person-scoped `AchievementInstance` records;
- person-scoped `PersonalMilestoneEvent` records that may have no shared achievement family;
- a derived `PersonalLegend` narrative or projection that selects and interprets milestone history without rewriting the underlying records.

`AchievementFamily` should describe a shared, versioned accomplishment pattern and, where applicable, its qualification/evidence criteria. Whether an accomplishment is personally meaningful remains person-specific.

Global rarity may be informative, but a universal competitive leaderboard is not a core project goal.

## 9. Safety against optimization pathologies

The system must be designed with the expectation that visible metrics can be gamed.

Later evaluation systems should therefore prefer diverse, contextual, repeated evidence over single-point tests when stronger claims are required.

The project must explicitly test for Goodhart-like failure modes in which users optimize the measurement while the underlying capability does not improve.

Development activities should aim to develop or test real capability. Producing evidence is a consequence of meaningful activity, not the terminal objective of progression.

## 10. Change governance

Changes to this constitution require explicit review and must identify:

1. which invariant is changing;
2. why the previous invariant is insufficient;
3. what new failure modes become possible;
4. what migration or compatibility impact exists;
5. whether the change alters Capability Lab's relationship to HDE or user authority.

Convenience is not sufficient justification for silently weakening a constitutional boundary.
