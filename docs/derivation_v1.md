# Deterministic Supported-State Derivation v1

Status: **PR4 normative derivation contract**

PR4 introduces Capability Lab's first executable bridge from governed PR2 claim evaluations into the PR3 personal capability state representation. The baseline is deliberately conservative: it composes explicitly selected `ClaimEvaluation` records and explicit claim-to-dimension bindings. It does not re-evaluate raw evidence, infer evaluator authority, weight support, resolve state-level conflict, or produce a mastery scalar.

## Core boundary

```text
EvidenceRecord
      |
      v
CapabilityClaim
      |
      v
ClaimEvaluation
      |
      | explicit selected evaluation ids
      | explicit ClaimDimensionBinding values
      v
Deterministic Supported-State Baseline v1
      |
      v
PersonalCapabilityState
```

The central PR4 invariant is:

```text
PR4 COMPOSES EVALUATIONS
PR4 DOES NOT RE-EVALUATE EVIDENCE
```

The derivation function receives an `EpistemicRecordSet` only so it can resolve exact claim/evaluation identities and enforce PR2/PR3 cross-record contracts. The baseline decision logic does not inspect evidence reliability, evidence outcome, evidence kind, evidence count, evidence provenance depth, coverage status, evaluator kind, evaluator identity, or evaluation-policy identity.

## Fixed policy identity

PR4 v1 implements exactly one derivation policy:

```text
core:deterministic_supported_state@1
```

and one rule deriver identity:

```text
kind = rule
ref  = capability_lab:deterministic_supported_state_v1
```

The caller cannot relabel this implementation as another derivation policy. The policy ref identifies the semantics implemented by this code path; it remains an exact declared revision reference rather than a content hash or authority grant.

```text
POLICY REF IDENTIFIES THE ALGORITHM
DERIVER != AUTHORITY
```

## Explicit evaluation selection

The baseline never silently treats every structurally valid evaluation as authoritative state input.

`DeterministicStateDerivationRequest.selected_evaluation_ids` names the exact `ClaimEvaluationId` records that the surrounding governed workflow selected for this derivation run.

```text
SELECTED EVALUATION != TRUTH
SELECTION != AUTHORITY
UNSELECTED EVALUATION MUST NOT CHANGE OUTPUT STATE
```

PR4 does not define who may select an evaluation or why. Authorization/admission remains outside this pure baseline. In particular, the baseline does not prefer humans over models, one evaluator over another, one evaluation policy over another, or newer evaluations over older evaluations.

Every selected evaluation must:

- exist in the supplied `EpistemicRecordSet`;
- reference an existing claim;
- belong to the requested subject;
- target the exact requested capability concept revision;
- have `evaluated_at <= request.as_of`.

An evaluation that exists in the record set but is not explicitly selected is invisible to the derivation result.

## Explicit claim-to-dimension binding

`CapabilityClaim` intentionally does not embed `CompetenceFrame` semantics. PR4 preserves that boundary with explicit `ClaimDimensionBinding` input:

```text
ClaimDimensionBinding
├── claim_id
└── dimension_keys
```

A binding is scoped to the exact `CompetenceFrameRef` carried by the derivation request. It is not inferred from claim statement text, claim scope tags, embeddings, or a model.

```text
CLAIM != COMPETENCE DIMENSION
CLAIM SCOPE TAG != COMPETENCE DIMENSION
BINDING != EVALUATION
BINDING != SUPPORT
BINDING != AUTHORITY
```

A claim may bind to more than one dimension. The same complete selected evaluation basis for that claim is then used in every bound dimension. PR4 does not permit per-dimension slicing of one claim's selected evaluations because that could hide same-claim conflict by partitioning evaluations across dimensions.

```text
CLAIM BASIS IS CONSISTENT ACROSS ITS DIMENSION USES
```

Every selected evaluation's claim must have a binding, and every bound claim must have at least one selected evaluation. This ensures that no effective derivation input is silently unused.

## Pure deterministic request

`DeterministicStateDerivationRequest` contains all non-global run inputs:

- `PersonalCapabilityStateId`;
- `CapabilitySubjectRef`;
- exact `CapabilityConceptRef`;
- exact `CompetenceFrameRef`;
- `as_of`;
- `derived_at`;
- selected evaluation ids;
- claim-dimension bindings.

`state_id`, `as_of`, and `derived_at` are supplied by the caller. The baseline does not call a current clock or generate UUIDs.

For exact algorithm version v1:

```text
same exact EpistemicRecordSet
+ same exact CompetenceFrame
+ same canonical derivation request
=> exactly equal PersonalCapabilityState
```

Equivalent input ordering is canonicalized and cannot affect the output.

```text
NO CURRENT CLOCK
NO RANDOMNESS
NO UUID GENERATION
NO NETWORK
NO MODEL
NO GLOBAL CONFIG
NO ITERATION-ORDER DEPENDENCE
```

## Dimension derivation

For each dimension in the exact frame, PR4 collects every selected evaluation for every explicitly bound claim.

### No basis

If no selected evaluation basis is bound to the dimension:

```text
standing = UNKNOWN
supported_claim_ids = ()
basis_evaluation_ids = ()
conflict_status = NONE
```

An all-UNKNOWN state is therefore a valid deterministic output when the request contains no selected evaluations and no bindings.

### Basis without selected support

If basis exists but no bound claim has a selected evaluation with `conclusion = SUPPORTED`:

```text
standing = INSUFFICIENT
supported_claim_ids = ()
```

`CONTRADICTED`, `MIXED`, `INSUFFICIENT`, and `ABSTAINED` evaluations do not become a low competence level. They simply do not create supported state content in baseline v1.

```text
CONTRADICTED CLAIM != LOW STATE
```

### Supported content

A bound claim appears in `supported_claim_ids` if and only if at least one of its selected evaluations has `conclusion = SUPPORTED`.

If at least one supported claim exists in a dimension:

```text
standing = SUPPORTED
```

Multiple supported evaluations for the same claim do not increase a score and do not duplicate the claim id.

```text
MULTIPLE SUPPORTED EVALUATIONS != MORE CAPABILITY
```

## Conflict derivation

Baseline v1 emits only:

```text
NONE
UNRESOLVED
```

It never emits PR3 `DimensionConflictStatus.RESOLVED_BY_POLICY` because PR4 v1 implements no state-level conflict-resolution policy.

A dimension is `UNRESOLVED` if its selected basis contains either:

1. a `ClaimEvaluation` whose PR2 conflict status is `UNRESOLVED`; or
2. both selected `SUPPORTED` and selected `CONTRADICTED` evaluations for the same claim.

Otherwise the dimension conflict status is `NONE`.

A PR2 evaluation with `conflict_status = RESOLVED_BY_POLICY` has already resolved evidence-level conflict under that evaluation's exact `EvaluationPolicyRef`. PR4 does not reinterpret that as PR3 state-level `RESOLVED_BY_POLICY`; the evaluation record remains in the state basis for audit.

```text
EVALUATION-LEVEL RESOLUTION != STATE-LEVEL RESOLUTION
BASELINE V1 NEVER RESOLVES STATE-LEVEL CONFLICT
```

Support standing and conflict remain independent. A dimension may therefore be:

```text
SUPPORTED + UNRESOLVED
INSUFFICIENT + UNRESOLVED
```

## What baseline v1 deliberately ignores

PR4 v1 does not use the following to choose state standing or conflict:

- evidence kind;
- evidence outcome;
- evidence reliability;
- evidence-bearing counts;
- coverage status;
- number of evidence records;
- number of evaluations as a voting weight;
- evaluator kind or evaluator identity;
- evaluation policy identity as a preference;
- provenance depth;
- age/recency decay;
- current/latest evaluation ordering.

The only temporal gate in v1 is causal:

```text
evaluation.evaluated_at <= request.as_of
```

Future selected evaluations are rejected. Future or otherwise unselected evaluations do not affect a historical state.

```text
PR4 DOES NOT WEIGH EVALUATORS
PR4 DOES NOT WEIGH EVIDENCE
PR4 DOES NOT COUNT SUPPORT
PR4 DOES NOT PREFER LATEST
PR4 DOES NOT REINTERPRET COVERAGE
PR4 DOES NOT REINTERPRET RELIABILITY
```

## Defense-in-depth validation

Every derived output is assembled as a PR3 `PersonalCapabilityState` and then validated through a one-state `PersonalCapabilityStateSet` against:

- the supplied `EpistemicRecordSet`;
- a `CompetenceFrameCatalog` containing the exact supplied frame.

This does not make the result governance-accepted truth. It ensures only that the deterministic output also satisfies the PR3 representation boundary.

```text
DERIVED STATE != PERSON
VALID DERIVATION != GOVERNANCE ACCEPTANCE
```

## PR4 non-goals

PR4 deliberately does not implement:

- evidence weighting;
- evaluator weighting;
- majority vote or support counts;
- confidence or mastery scores;
- recency decay or forgetting;
- newest-evaluation-wins semantics;
- automatic evaluation admission;
- evaluator or policy authority inference;
- automatic claim creation;
- automatic claim-to-dimension classification;
- LLM/embedding-based dimension assignment;
- semantic contradiction detection across different claim propositions;
- state-level conflict resolution;
- `RESOLVED_BY_POLICY` emission by baseline v1;
- XP, progression, achievements, recommendations, or Player Window;
- persistence, synchronization, consent, acceptance, or publication workflows.

The boundary is:

```text
PR2 = GOVERNED EVALUATIONS
PR4 = PURE DETERMINISTIC COMPOSITION
PR3 = STATE REPRESENTATION
```
