# Civilization Bootstrap / Technical Generalist

Status: **PR5 seed domain contract under adversarial review**

Civilization Bootstrap is Capability Lab's first real domain wedge. It asks what bounded technical capabilities help a person understand, diagnose, reconstruct, and combine important physical and informational systems from first principles.

The graph is not a claim that one person should reconstruct modern civilization, and it is not a ranking of people.

```text
CIVILIZATION BOOTSTRAP GRAPH != UNIVERSAL CURRICULUM
CIVILIZATION BOOTSTRAP GRAPH != HUMAN LEVEL
GRAPH DEPTH != DIFFICULTY
GRAPH CENTRALITY != HUMAN IMPORTANCE
CAPABILITY != LICENSE / AUTHORITY / PERMISSION
```

## Seed v0 snapshot

PR5 introduces the curated `civilization_bootstrap` namespace as a deterministic `CapabilityCatalog` with:

- **63 active capability concepts**, initially at semantic revision `@1`;
- **57 typed relations** after adversarial ontology repair;
- **2 structural `SPECIALIZES` relations** whose narrower/broader semantics are directly defensible;
- **51 scoped `SUPPORTED_BY` relations** with explicit qualitative strength;
- **1 scoped categorical `REQUIRES` relation**;
- **3 scoped categorical `ENABLED_BY` relations**;
- **0 empirical-development relations**.

Pack version and concept revision are different identities:

```text
SEED PACK v0 != CAPABILITY CONCEPT @1
```

`v0` identifies this curated domain snapshot. `@1` identifies one exact semantic revision of one capability concept. Graph-geometry changes do not automatically revise every concept.

## Editorial families are not graph structure

The seed is curated in eight editorial families:

- foundations / inquiry;
- matter / materials;
- energy / physical systems;
- fabrication / metrology;
- mechanical systems;
- electrical / information systems;
- infrastructure;
- life systems.

The pack also contains eight broad capabilities such as `technical_inquiry`, `energy_system_reasoning`, and `life_support_system_reasoning`. They are real capability concepts that may receive their own scoped claims; they are not UI folders and there is deliberately no `technical_generalist` root.

Adversarial review found that the initial seed incorrectly used `SPECIALIZES` to encode family membership. For example:

```text
quantitative_estimation SPECIALIZES technical_inquiry
```

was structurally convenient but semantically false: quantitative estimation can support technical inquiry without being a narrower form of the whole inquiry capability.

PR5 therefore freezes the stronger rule:

```text
EDITORIAL FAMILY MEMBERSHIP != SPECIALIZES
GRAPH GROUPING != SEMANTIC IS-A
```

Seed v0 now stores only these structural specialization edges:

```text
electrical_measurement SPECIALIZES physical_measurement
dimensional_metrology SPECIALIZES physical_measurement
```

No relation is required merely to keep an editorial family visually connected.

## Capability concepts, not school subjects

Seed concepts are intended to support bounded inspectable claims. Broad school-subject labels such as `physics`, `chemistry`, or `engineering` are not used as terminal personal capability assertions.

Examples include:

```text
physical_measurement
basic_circuits
electric_motor_systems
pump_systems
microcontroller_sensor_systems
potable_water_treatment
microbiology_and_contamination_control
```

A concept's existence says nothing about a person:

```text
CONCEPT EXISTS != SUBJECT HAS CAPABILITY
DOMAIN PACK IMPORT != PERSONAL STATE CREATION
```

Person-scoped evidence, claims, evaluations, and state remain PR2–PR4 responsibilities.

## Dependency relation policy

PR1 relation orientation remains authoritative:

```text
A REQUIRES B
```

means B is the dependency/supporting capability for A under the exact relation scope.

Every dependency relation in this pack carries an explicit `RelationScope`. Every `SUPPORTED_BY` relation carries a non-`UNSPECIFIED` strength.

`SUPPORTED_BY` is the default when a capability materially helps another without establishing categorical necessity. `REQUIRES` is reserved for cases where the bounded definition and exact scope make the dependency necessary.

Adversarial review downgraded two initial categorical claims:

```text
microcontroller_sensor_systems
    SUPPORTED_BY embedded_programming

potable_water_treatment
    SUPPORTED_BY microbiology_and_contamination_control
```

Both have important alternative-route concerns: a bounded microcontroller sensing system may use pre-existing firmware/configuration, and bounded water-treatment reasoning does not require the full microbiology capability in every route. They remain strong support relations rather than universal barriers.

Seed v0 retains one categorical dependency:

```text
low_voltage_power_distribution
    REQUIRES basic_electricity
    scope = conceptual_analysis
```

This remains intentionally narrow: the concept explicitly includes analysis of source, load, conductor, protection, measurement, and isolation relationships, and the categorical assertion applies only to the stated conceptual-analysis scope.

`ENABLED_BY` is used where a capability opens a practical route without claiming uniqueness; for example soldering can enable prototype assembly while other interconnection routes may exist.

## No empirical learning path in v0

Seed v0 intentionally contains no:

```text
COMMONLY_PRECEDES
COMMONLY_COOCCURS
TRANSFER_OBSERVED_TO
```

PR1 requires provenance for empirical-development relations. Curriculum intuition is not empirical evidence.

```text
CURRICULUM INTUITION != EMPIRICAL DEVELOPMENT OBSERVATION
```

Future pilots may justify provenance-backed empirical relations in later snapshots.

## Cross-domain chains

The useful graph is not a tree. Examples of retained cross-domain support include:

```text
electric_motor_systems
    SUPPORTED_BY electromagnetism
    SUPPORTED_BY mechanisms_and_power_transmission

pump_systems
    SUPPORTED_BY fluid_pressure_and_flow
    SUPPORTED_BY mechanisms_and_power_transmission

microcontroller_sensor_systems
    SUPPORTED_BY sensing_and_signal_conditioning
    SUPPORTED_BY embedded_programming
    ENABLED_BY soldering

food_preservation
    SUPPORTED_BY microbiology_and_contamination_control
```

Relation kinds and scopes, not diagram position, carry the semantics.

## Technical competence frame v1

PR5 provides the domain-defined frame:

```text
civilization_bootstrap:technical_competence@1
```

with seven non-ordinal dimensions:

- `conceptual_knowledge`;
- `calculation`;
- `execution`;
- `diagnosis`;
- `transfer`;
- `independence`;
- `explanation`.

The frame is not a universal human ontology and contains no mastery percentage, XP, rank, or novice/intermediate/expert ladder.

`independence` is only independence inside an explicit assistance/reference/tool/collaboration/automation boundary. It is not human worth, identity, general autonomy, professional authority, or permission.

Safety is not introduced as a universal eighth dimension. Safety constraints may live in capability semantics, claim scope, evidence context, and governed policy without prematurely declaring one universal safety axis.

## Real vertical integration

PR5 is required to work through the already merged layers using a real domain concept:

```text
civilization_bootstrap:basic_circuits@1
        |
        v
EvidenceRecord
        |
        v
CapabilityClaim
        |
        v
ClaimEvaluation
        |
        v
PR4 deterministic derivation
        |
        v
PersonalCapabilityState
```

The integration smoke deliberately derives:

```text
conceptual_knowledge = SUPPORTED
calculation          = SUPPORTED
execution            = UNKNOWN
diagnosis            = UNKNOWN
transfer             = UNKNOWN
independence         = UNKNOWN
explanation          = UNKNOWN
```

Supported theory/calculation does not silently imply execution, diagnosis, transfer, independence, explanation, or mastery.

## Design principles

1. Prefer first-principles capability over trivia.
2. Model defensible dependency chains rather than isolated devices or decorative hierarchy.
3. Keep theoretical understanding separate from practical execution.
4. Treat rough functional reconstruction and diagnosis as meaningful bounded outcomes.
5. Preserve `UNKNOWN` where governed basis is absent.
6. A failed attempt is evidence-bearing, not an automatic low-capability classification.
7. Do not confuse technical understanding with authority, credentialing, licensing, or permission.
8. Treat prerequisites as contextual rather than universal barriers unless exact scope justifies `REQUIRES`.
9. Keep empirical development observations separate from structural/dependency semantics.
10. Treat editorial families as curation, not automatic graph edges.
11. Treat this pack as one technical wedge, not a universal human ontology.

## PR5 non-goals

PR5 does not implement:

- a generic domain/plugin framework;
- a complete civilization ontology;
- a universal curriculum;
- a technical-generalist score or global root capability;
- difficulty inferred from graph depth;
- importance inferred from centrality or degree;
- empirical learning-path edges without provenance;
- model-generated taxonomy;
- automatic claims, evaluations, or personal state;
- progression frontier or next-step recommendations;
- achievements, XP, ranks, or Player Window;
- credential, license, authority, consent, or action-permission semantics.
