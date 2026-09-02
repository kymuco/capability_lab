# Civilization Bootstrap Pilot 01 — Claim Scope & Human Evaluation Policy Boundary v1

Status: **PR11.0 implementation contract**

Evaluation policy ref:

```text
civilization_bootstrap:pilot_01_basic_electricity_human_review@1
```

Protocol ref:

```text
civilization_bootstrap:pilot_01_basic_electricity@1
```

Capability ref:

```text
civilization_bootstrap:basic_electricity@1
```

Frozen policy snapshot SHA-256:

```text
f1b2be9d059e3375419e3a96803f099a671f0d98531b6d9a061dd36505c4c18a
```

The digest is a deterministic software/content integrity marker for this exact
policy snapshot. It is not a signature, policy authority, reviewer identity,
authenticated history, or proof that an evaluation occurred.

## Outcome

PR11.0 defines the first real Pilot 01 interpretation boundary **without yet
performing an evaluation**.

```text
reviewed PR10.1 EvidenceRecord
        |
        X  PR11.0 does not evaluate it yet

PR11.0 defines:
    exact claim templates
    exact claim scopes
    probe-relative rubrics
    evidence-bearing semantics
    coverage rules
    reliability rule
    PR10.1 dependence prerequisite for multi-record sufficiency
```

The authority boundary is deliberate:

```text
CLAIM TEMPLATE != CAPABILITY CLAIM
RUBRIC != CLAIM EVALUATION
EVALUATION POLICY != EVALUATION
EVIDENCE BEARING GUIDANCE != AUTOMATIC BEARING
PR11.0 != PERSONAL CAPABILITY STATE
```

`PilotClaimTemplate` is subject-free policy metadata. A real
`CapabilityClaim` still requires an explicit subject, claim id, creation time,
scope, and provenance under PR2. `PilotHumanEvaluationPolicy` never constructs
a `CapabilityClaim`, `ClaimEvaluation`, or `PersonalCapabilityState`.

## Why reasoning and execution are separate claims

Pilot 01 contains three required reasoning probes and one optional execution
probe. PR10.0 already defines absence of the optional probe as allowed and
unobserved rather than failed.

PR11.0 therefore refuses to collapse them into one proposition.

### bounded_reasoning

The reasoning claim covers only:

```text
conceptual_explanation
calculation_work
diagnosis_reasoning
```

Its proposition is bounded to low-voltage DC conceptual relationships,
protocol calculations, and safe diagnosis reasoning.

### bounded_execution

The execution claim covers only:

```text
execution_artifact
```

It is a distinct practical proposition. Missing `execution_artifact` means:

```text
OPTIONAL_UNOBSERVED
```

not:

```text
FAILURE
CONTRADICTION
LOW CAPABILITY
NEGATIVE EVIDENCE
```

This avoids an optional data-collection decision silently lowering a capability
judgment.

## Probe-relative rubric

Every frozen Pilot 01 probe has exactly one rubric.

Each rubric contains:

```text
criterion_id
requirement
acceptable_variations
material_error_conditions
bearing guidance for:
    SUPPORTS
    CONTRADICTS
    INDETERMINATE
    NOT_RELEVANT
missing-probe semantics
```

The rubric is not a hidden score. PR11.0 defines no numeric threshold, mastery
scalar, weighted point total, or automatic pass/fail algorithm.

### conceptual_explanation

The rubric checks the bounded relation among voltage, current, and resistance,
including Ohm's law, the direction of change under fixed resistance / fixed
voltage, one concrete example, and material assumptions or uncertainty.

A substantive misconception may later justify `CONTRADICTS`; omission or
ambiguity alone is not automatically contradiction.

### calculation_work

Reference checkpoints are frozen for human review:

```text
5.0 V / 1.0 kΩ
    -> 5.0 mA

(9.0 V - stated 2.0 V LED drop) / 330 Ω
    -> about 21.2 mA

5.0 V across 100 Ω + 220 Ω in series
    -> 320 Ω total
    -> 15.625 mA
    -> about 1.5625 V across 100 Ω
    -> about 3.4375 V across 220 Ω

12.0 V across 1.0 kΩ
    -> 0.144 W = 144 mW
```

Equivalent algebra, correct unit conversions, and reasonable rounding are
allowed. The human reviewer still inspects the reasoning rather than treating
the numbers as a sufficient automatic score.

### diagnosis_reasoning

The rubric requires a safe bounded low-voltage sequence, ordered inspection /
measurement, branching reasoning based on results, multiple plausible fault
hypotheses, and technically coherent multimeter interpretation.

Out-of-scope mains, high-voltage, opened-power-supply, or unknown energized
work is a material error relative to this policy boundary.

### execution_artifact

The optional execution rubric only applies if an actual reviewed/materialized
execution artifact exists.

It requires bounded low-voltage context and enough inspectable execution,
measurement, or observation content to bear on the practical claim.

The rubric also repeats the PR10.x provenance limit:

```text
DECLARED SUBJECT-PROVIDED ORIGIN != AUTHENTICATED HUMAN AUTHORSHIP
LOCAL HASH != PROOF OF HISTORICAL EXECUTION
RECEIPT != SIGNATURE
```

A photo, note, or measurement record can later bear on the bounded execution
claim while still not becoming authenticated historical proof.

## Evidence-bearing semantics

PR11.0 uses the existing PR2 `EvidenceBearing` vocabulary rather than creating
another conclusion language.

```text
SUPPORTS
CONTRADICTS
INDETERMINATE
NOT_RELEVANT
```

The policy defines guidance, not automatic classification.

Key constraints:

```text
OMISSION != CONTRADICTION
MISSING REQUIRED PROBE -> COVERAGE GAP
MISSING OPTIONAL EXECUTION -> UNOBSERVED
MATERIALIZED EVIDENCE != SUPPORT
EVIDENCE KIND != RELIABILITY
```

A future evaluator must make an explicit reviewed decision for each actual
evidence item.

## Reliability boundary

PR11.0 does not infer `EvidenceReliability` from:

```text
EvidenceKind
successful PR10.1 materialization
valid reviewed-resolution receipt
probe identity
file-vs-text capture kind
```

Reliability must be explicitly assessed by the evaluator in the later
`ClaimEvaluation`.

This keeps:

```text
PROVENANCE != RELIABILITY
MATERIALIZATION VALIDITY != RELIABILITY
```

## Coverage boundary

For `bounded_reasoning`, sufficient-for-claim coverage may only be considered
after the three required reasoning probes have actually been assessed.

Missing required material is a coverage gap. It does not become negative
evidence by absence.

For `bounded_execution`, sufficient coverage requires an actually observed
`execution_artifact`. The optional probe's absence remains unobserved.

PR11.0 does not itself construct a PR2 `CoverageAssessment`.

## Dependence boundary

The work in PR10.1 now becomes an actual prerequisite for stronger
interpretation.

Multiple `EvidenceRecord` values may be assessed individually, but a later
evaluation policy implementation must not treat them as independent/repeated
support or use them to justify multi-record sufficiency unless the PR10.1
terminal reviewed-dependence precondition passes for the exact basis.

```text
MULTIPLE EvidenceRecord != INDEPENDENT SUPPORT

PR10.1 TERMINAL DEPENDENCE PASS
    -> permits bounded use as a multi-record precondition
    X does not itself create claim support
```

This preserves all six PR10.1 causal families:

```text
source
mechanism
coordination/control
temporal/intervention/carryover
allocation/randomization
sampling/selection/cohort construction
```

## Deterministic policy snapshot

`pilot_evaluation_policy_to_json_v1(...)` serializes the complete policy using
canonical JSON ordering and `pilot_evaluation_policy_sha256_v1(...)` adds a
domain-separated SHA-256 digest.

The snapshot binds the exact:

```text
policy ref
protocol ref
claim templates and scopes
probe criteria
bearing guidance
missing-probe semantics
reliability rule
coverage rule
dependence rule
authority boundaries
```

Changing policy content under the same conceptual policy revision changes the
digest and must be reviewed. A semantic revision intended for durable use
should receive a new `EvaluationPolicyRef` revision rather than silently
replacing `@1`.

```text
POLICY REF != CONTENT HASH
POLICY HASH != SIGNATURE
POLICY HASH != AUTHORITY
SERIALIZED POLICY != EXECUTED EVALUATION
```

## PR11.0 non-goals

PR11.0 intentionally does **not** implement:

- a participant score;
- automatic answer grading;
- a `CapabilityClaim` instance;
- a `ClaimEvaluation`;
- an `EvaluatorRef` decision record;
- evidence reliability judgments for real evidence;
- coverage/conclusion computation;
- conflict resolution;
- state derivation;
- achievement/milestone creation;
- progression/frontier changes;
- Player Window changes;
- HDE integration;
- reviewer authentication;
- trusted timestamps;
- proof of human authorship.

The next causal step is a separate reviewed boundary:

```text
PR11.1
exact PR11.0 policy
    +
exact PR10.1 reviewed EvidenceRecord basis
    +
explicit human evaluator
    ->
CapabilityClaim + ClaimEvaluation
```

Only after a real `ClaimEvaluation` exists should the project consider feeding
that evaluation into the already-existing PR3/PR4 personal-state derivation
layer.
