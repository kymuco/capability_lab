# Civilization Bootstrap Adversarial Domain-Semantics Review v0

Status: **PR5 review contract**

This document records the second adversarial review pass for the Civilization Bootstrap seed graph. It focuses on graded `SUPPORTED_BY` semantics, broad capability concepts, cross-domain support, and relation-local scope interpretation.

## Strength semantics

PR1 defines `RelationStrength` only for `SUPPORTED_BY`. In PR5, `WEAK`, `MODERATE`, and `STRONG` describe the material-help relation of one exact edge under that edge's exact scope.

```text
RELATION STRENGTH != NECESSITY
RELATION STRENGTH != PROBABILITY
RELATION STRENGTH != DIFFICULTY
RELATION STRENGTH != LEARNING PRIORITY
RELATION STRENGTH != HUMAN IMPORTANCE
RELATION STRENGTH != CAPABILITY SCORE
```

A `STRONG` `SUPPORTED_BY` edge remains non-categorical. It must not be silently promoted to `REQUIRES` by a consumer.

Strength is also not a property of either endpoint in isolation:

```text
EDGE STRENGTH != TARGET CAPABILITY STRENGTH
EDGE STRENGTH != SOURCE CAPABILITY STRENGTH
```

Seed v0 contains deliberate counterexamples. `microbiology_and_contamination_control` supports different source capabilities with different strength values, and `pump_systems` has different strength values for different supporting capabilities. This prevents interpreting the enum as a global importance label attached to a node.

`RelationStrength.rank` provides the PR1 ordinal ordering of graded support metadata. PR5 does not define a ranking algorithm, weighted prerequisite score, path cost, recommendation priority, difficulty estimate, or graph-derived human score from those ranks.

## Scope locality

`RelationScope` remains relation-local under PR1.

```text
SAME RelationScope.key != GLOBAL SCOPE IDENTITY
SAME RelationScope.key != SHARED POLICY OBJECT
SAME RelationScope.key != AUTOMATIC COMPARABILITY
```

PR5 reuses human-readable keys such as `conceptual_analysis`, `bounded_execution`, and `bench_validation` as authoring vocabulary. Reuse does not create a global registry. Relation identity remains tied to source, relation kind, target, and its relation-local qualifier.

Consumers must not group unrelated edges into one semantic object merely because their scope keys have equal strings. A future globally governed scope vocabulary would require a separate explicit identity/versioning design.

## Broad concepts and scoped claims

Some seed concepts intentionally cover a bounded system family rather than one atomic operation. Examples include `electric_motor_systems`, `pump_systems`, `refrigeration_systems`, and `public_health_reasoning`.

Their breadth does not collapse the PR2/PR3 separation:

```text
BROAD CAPABILITY CONCEPT != BROAD PERSONAL CLAIM
CONCEPT DEFINITION != SUPPORTED DIMENSION SET
```

A person-scoped assertion remains a `CapabilityClaim` with an explicit statement and scope. The PR4 `ClaimDimensionBinding` determines which competence-frame dimensions that exact governed claim contributes to. A broad concept therefore does not automatically imply execution, diagnosis, transfer, independence, or explanation.

Materially different meanings that cannot be bounded honestly by claim scope remain candidates for later concept split/new identity under PR1 semantic-governance rules. PR5 does not claim the v0 decomposition is final.

## Cross-domain support

Cross-domain edges are useful precisely because the seed is not a school-subject tree. They remain local claims about material support, not global curriculum rules.

For example:

```text
pump_systems SUPPORTED_BY fluid_pressure_and_flow
food_preservation SUPPORTED_BY microbiology_and_contamination_control
microcontroller_sensor_systems SUPPORTED_BY embedded_programming
```

These edges do not mean:

```text
TARGET MUST BE MASTERED FIRST
TARGET IS MORE IMPORTANT
SOURCE IS HARDER
SUPPORT TRANSITIVELY IMPLIES ALL ANCESTORS
SUBJECT STATE PROPAGATES ALONG THE EDGE
```

PR5 defines no automatic transitive closure for dependency meaning. A path of `SUPPORTED_BY` edges is not itself a `REQUIRES` path.

## Review outcome

The first ontology review repaired false `SPECIALIZES` family edges and overly strong categorical dependencies. This second pass found no additional production-data blocker requiring a graph rewrite.

Instead it freezes the interpretation boundary needed for the remaining graded support metadata:

```text
SUPPORTED_BY STRENGTH IS EDGE-LOCAL AND SCOPE-LOCAL
STRONG SUPPORTED_BY != REQUIRES
GRAPH RELATIONS DO NOT DERIVE PERSONAL STATE
RELATION SCOPE KEYS ARE NOT GLOBAL IDENTITIES
```

Executable regressions protect these boundaries in `tests/domains/test_civilization_bootstrap_adversarial_semantics_v0.py`.

## Non-goals

This review does not add a strength-calibration dataset, empirical prerequisite model, difficulty model, learning-order policy, recommendation engine, path optimizer, node-importance metric, global scope registry, or concept-splitting framework.
