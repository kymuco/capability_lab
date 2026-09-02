# Civilization Bootstrap Pilot 01 — Exact Sampling / Selection / Cohort-Construction Dependence Closure

Status: **PR10.1 adversarial closure**

This closure introduces a new causal family after reviewed allocation-origin
governance.

The existing PR10.1 ladder can now require bounded reviewed separation across:

```text
SOURCE
  exact identity
  -> explicit ancestry
  -> reviewed bounded completeness

MECHANISM
  exact identity
  -> explicit ancestry
  -> reviewed bounded completeness

COORDINATION / CONTROL
  exact identity
  -> explicit ancestry
  -> reviewed bounded completeness

TEMPORAL / INTERVENTION / CARRYOVER
  exact identity
  -> explicit ancestry
  -> reviewed bounded completeness

ALLOCATION / ASSIGNMENT / RANDOMIZATION
  exact identity
  -> explicit ancestry
  -> reviewed bounded completeness
```

That still does not answer a separate question:

> How did the observational unit enter the observed set in the first place?

Allocation answers how already-considered units were assigned to conditions.
Selection/sampling answers how units were admitted, sampled, recruited,
constructed, resampled, or otherwise entered the analyzed cohort.

Those causal questions must remain distinct.

## Remaining false-replication geometry

Two observations may pass every previous gate:

```text
observation A
  source separated
  mechanism separated
  control separated
  temporal separated
  allocation separated

observation B
  source separated
  mechanism separated
  control separated
  temporal separated
  allocation separated
```

but both can still originate from one bounded selection process:

```text
A -> selection episode X
B -> selection episode X
```

or:

```text
A -> recruitment batch X
B -> recruitment batch X
```

or:

```text
A -> bootstrap/resampling draw X
B -> bootstrap/resampling draw X
```

Treating such observations as selection-independent would be unsafe.

Therefore:

```text
REVIEWED ALLOCATION-ORIGIN SEPARATION
!=
SAMPLING / SELECTION INDEPENDENCE
```

## Exact selection identities

PR10.1 adds:

```text
PilotObservationSelectionKind
PilotObservationSelectionRef
```

The exact bounded identity kinds are:

```text
SAMPLING_FRAME_INSTANCE
SELECTION_EPISODE
COHORT_CONSTRUCTION_STATE
RECRUITMENT_BATCH
RESAMPLING_DRAW
INCLUSION_POLICY_EXECUTION
OTHER
```

These identify bounded process instances, not generic semantic labels.

### SAMPLING_FRAME_INSTANCE

An exact bounded sampling-frame instance used by the observations.

Examples of intended semantics:

```text
eligible_pool_snapshot:2026-08-18T00
survey_sampling_frame:batch_07
candidate_pool_snapshot:run_42
```

This does not mean a generic population label such as:

```text
adult_users
students
english_speakers
```

is a sampling-frame identity.

### SELECTION_EPISODE

One bounded process that selected or admitted units into the observed set.

Examples:

```text
selection_episode:run_018
screening_episode:2026_08_18_A
admission_episode:cohort_build_9
```

### COHORT_CONSTRUCTION_STATE

A bounded stateful cohort-building process whose internal state can couple
observations.

Examples:

```text
cohort_builder_state:epoch_12
eligibility_state:step_98
```

### RECRUITMENT_BATCH

A bounded recruitment/acquisition batch.

Examples:

```text
recruitment_batch:campus_A_2026_08
participant_batch:email_wave_14
```

### RESAMPLING_DRAW

One exact bootstrap/resampling/subsampling draw or equivalent bounded draw state.

Examples:

```text
bootstrap_draw:000184
subsample_draw:run_9
```

Two observations from one exact resampling draw are not two independent
selection origins merely because they later become separate EvidenceRecords.

### INCLUSION_POLICY_EXECUTION

One bounded execution of an inclusion/exclusion policy.

This is deliberately different from the policy definition.

```text
SAME INCLUSION RULE DEFINITION
!=
SAME INCLUSION POLICY EXECUTION
```

The exact execution may carry shared state, ordering, thresholds, adaptive
context, or one coupled admission decision process.

## What is intentionally not an exact selection identity

The following must not be inferred as shared selection-process identity merely
because their values are equal:

```text
same population label
same cohort label
same sampling algorithm
same inclusion-rule definition
same dataset name
same study family
same nominal sampling probability
same demographic category
same protocol
same reviewer
same machine
same timestamp
```

Therefore the enum intentionally does not contain pseudo-identities such as:

```text
POPULATION_LABEL
COHORT_LABEL
SAMPLING_ALGORITHM
INCLUSION_RULE
DATASET_NAME
STUDY_FAMILY
```

This avoids conflating design similarity with one bounded causal process.

## Exact dependence key

PR10.1 adds:

```text
pilot_observation_selection_dependence_key_v1(selection)
```

under the domain:

```text
capability_lab/pilot_observation_sampling_selection_dependence@1
```

The canonical payload contains:

```text
kind
ref
```

and the public comparison key is:

```text
pilot_observation_selection:<sha256>
```

The raw ref is not echoed into the dependence key.

Still:

```text
HASHED KEY
!=
ANONYMIZATION

HASHED KEY
!=
AUTHENTICATION
```

The hash is only a privacy-reducing structural comparison key.

Kind is part of the hash domain payload.

Therefore the same raw ref under different bounded kinds is not silently
collapsed:

```text
SAMPLING_FRAME_INSTANCE:X
!=
RECRUITMENT_BATCH:X
```

unless a future lineage layer explicitly relates them.

## Candidate-bound selection declaration

PR10.1 adds:

```text
PilotMaterializationSelectionDeclaration(
    candidate_sha256,
    selections,
)
```

and:

```text
build_pilot_materialization_selection_declaration_v1(...)
```

The declaration is bound to exact materialization candidate bytes using the
existing candidate SHA-256 binding.

Therefore:

```text
SELECTION DECLARATION FOR CANDIDATE A
!=
SELECTION DECLARATION FOR CANDIDATE B
```

A declaration cannot be silently moved onto another candidate merely because
the selection refs look similar.

The declaration is canonicalized by:

```text
(kind.value, ref)
```

and rejects repeated exact refs.

## Empty declaration semantics

An empty declaration means only:

```text
NO SELECTION REFS WERE SUPPLIED
```

It does not mean:

```text
NO SAMPLING PROCESS EXISTED
NO SELECTION PROCESS EXISTED
NO COHORT CONSTRUCTION EXISTED
NO RECRUITMENT BATCH EXISTED
NO RESAMPLING DRAW EXISTED
NO INCLUSION POLICY EXECUTION EXISTED
```

It certainly does not mean:

```text
INDEPENDENT SAMPLING
INDEPENDENT COHORT CONSTRUCTION
INDEPENDENT REPLICATION
```

Completeness governance for this family is intentionally deferred to a later
closure.

## Combined selection entry

PR10.1 adds:

```text
PilotMaterializedEvidenceSelectionEntry(
    allocation_entry,
    selection_declaration,
)
```

The underlying allocation entry already carries the full lower reviewed basis.

The new wrapper verifies:

```text
selection_declaration.candidate_sha256
==
exact basis candidate sha256
```

so:

```text
allocation basis A
+
selection declaration for candidate B
-> REJECT
```

This prevents selection metadata from floating free from the materialized
observation it describes.

## Strongest prior gate remains mandatory

The new selection gate first invokes:

```text
validate_pilot_materialized_evidence_reviewed_allocation_origin_preconditions_v1(...)
```

That gate already composes the entire preceding ladder.

Thus:

```text
SELECTION SEPARATION
!=
OVERRIDE OF PRIOR DEPENDENCE
```

If observations share a source, mechanism, controller, temporal root,
allocation root, or have unresolved reviewed completeness in any previous
family, the selection layer never gets authority to bless them.

## Exact shared-selection gate

The new strongest gate is:

```text
validate_pilot_materialized_evidence_shared_selection_preconditions_v1(...)
```

Its behavior is:

1. validate and canonicalize `PilotMaterializedEvidenceSelectionEntry` values;
2. require the full reviewed allocation-origin gate;
3. verify returned allocation basis ordering exactly matches selection entries;
4. hash every declared exact selection ref;
5. reject any exact selection key reused by two distinct observations;
6. return canonical entries otherwise.

## Structural reject examples

Shared sampling-frame instance:

```text
A -> SAMPLING_FRAME_INSTANCE:frame_X
B -> SAMPLING_FRAME_INSTANCE:frame_X

=> REJECT
```

Shared selection episode:

```text
A -> SELECTION_EPISODE:episode_X
B -> SELECTION_EPISODE:episode_X

=> REJECT
```

Shared cohort-construction state:

```text
A -> COHORT_CONSTRUCTION_STATE:state_X
B -> COHORT_CONSTRUCTION_STATE:state_X

=> REJECT
```

Shared recruitment batch:

```text
A -> RECRUITMENT_BATCH:batch_X
B -> RECRUITMENT_BATCH:batch_X

=> REJECT
```

Shared resampling draw:

```text
A -> RESAMPLING_DRAW:draw_X
B -> RESAMPLING_DRAW:draw_X

=> REJECT
```

Shared inclusion-policy execution:

```text
A -> INCLUSION_POLICY_EXECUTION:execution_X
B -> INCLUSION_POLICY_EXECUTION:execution_X

=> REJECT
```

## Multiple refs inside one observation

One observation may legitimately declare multiple exact selection identities:

```text
observation A
  -> SAMPLING_FRAME_INSTANCE:frame_A
  -> RECRUITMENT_BATCH:batch_A
  -> INCLUSION_POLICY_EXECUTION:policy_run_A
```

These refs do not collide with each other merely because they occur inside one
observation.

The gate compares selection identities **across observations**.

## Distinct exact refs are not an independence certificate

Suppose:

```text
A -> SELECTION_EPISODE:A
B -> SELECTION_EPISODE:B
```

and:

```text
A != B
```

The exact layer only establishes:

```text
NO EXACT DECLARED SELECTION IDENTITY WAS REUSED
```

It does not establish:

```text
NO COMMON SELECTION ANCESTOR
NO CLONED COHORT-BUILDER STATE
NO SHARED UPSTREAM SAMPLING FRAME
NO SHARED RECRUITMENT ORIGIN
NO HIDDEN COMMON RESAMPLING ROOT
COMPLETE SELECTION DECLARATIONS
COMPLETE SELECTION LINEAGE GRAPH
INDEPENDENT SAMPLING
STATISTICAL INDEPENDENCE
INDEPENDENT REPLICATION
```

Those are separate claims.

## Why this is not source provenance

A sampling frame or recruitment batch can be represented by files or records,
but the causal question is not identical to source provenance.

Source provenance asks:

> Did the evidence derive from one information source or upstream artifact?

Selection asks:

> Did the observed units enter the observed set through one bounded selection
> process?

Two observations can use separate source artifacts while still sharing one
selection episode.

Therefore selection dependence must not be folded into source provenance.

## Why this is not allocation

Allocation asks:

> Given a considered unit, how was it assigned to a condition?

Selection asks:

> Why was that unit considered/observed at all?

For example:

```text
same recruitment batch
+ independent random assignment afterward
```

can satisfy allocation separation while still sharing a selection origin.

Conversely:

```text
independent recruitment batches
+ one shared adaptive randomization state
```

can satisfy selection separation while failing allocation separation.

The families are therefore orthogonal enough to deserve separate governance.

## Conservative PASS semantics

Passing the new exact-selection gate means only:

```text
full reviewed lower ladder passed
+
no exact declared selection identity was shared across observations
```

It does not mean:

```text
selection-lineage separation
selection completeness
independent sampling
representative sampling
exchangeability
absence of selection bias
absence of collider bias
independent subjects
independent experimental replication
valid causal identification
valid evidence weighting
```

And it does not authorize:

```text
CapabilityClaim creation
Evaluation
PR3 state update
achievement unlock
progression update
Player Window change
```

## New invariants

```text
REVIEWED ALLOCATION-ORIGIN SEPARATION
!=
SELECTION INDEPENDENCE

SAME EXACT SELECTION IDENTITY
=>
KNOWN DECLARED SELECTION DEPENDENCE

DIFFERENT SELECTION REFS
!=
DIFFERENT SELECTION ORIGINS

SAME POPULATION LABEL
!=
SAME SELECTION IDENTITY

SAME COHORT LABEL
!=
SAME COHORT-CONSTRUCTION STATE

SAME SAMPLING ALGORITHM
!=
SAME SAMPLING PROCESS INSTANCE

SAME INCLUSION RULE
!=
SAME INCLUSION POLICY EXECUTION

EMPTY SELECTION DECLARATION
!=
NO SELECTION DEPENDENCE

PASS
!=
STATISTICAL INDEPENDENCE

PASS
!=
AUTHORITY TO CLAIM INDEPENDENT REPLICATION
```

## Resulting ladder

After this closure the dependency ladder becomes:

```text
SOURCE
  identity -> ancestry -> reviewed completeness

MECHANISM
  identity -> ancestry -> reviewed completeness

COORDINATION / CONTROL
  identity -> ancestry -> reviewed completeness

TEMPORAL / INTERVENTION / CARRYOVER
  identity -> ancestry -> reviewed completeness

ALLOCATION / ASSIGNMENT / RANDOMIZATION
  identity -> ancestry -> reviewed completeness

SAMPLING / SELECTION / COHORT CONSTRUCTION
  exact identity
```

Selection is intentionally only at the first stage after this commit.

## Non-goals

This closure does not add:

```text
selection-lineage graph
selection completeness review
automatic discovery of sampling processes
population-representativeness claims
sampling weights
propensity scores
selection-bias correction
collider analysis
causal effect estimation
subject-independence inference
reviewer authentication
signatures
CapabilityClaim support
Evaluation
PR3 state derivation
achievements
progression
Player Window behavior
```

## Next causal boundary

The immediate next selection-family boundary is explicit lineage/common origin.

False-replication example:

```text
observation A -> SELECTION_EPISODE:A
observation B -> RECRUITMENT_BATCH:B

A != B

BUT

A DERIVED_FROM selection_root_X
B STATE_CONTINUATION_OF selection_root_X
```

or two cohort-construction states cloned from one upstream selection state.

That should become a dedicated:

```text
Sampling / Selection / Cohort-Construction Lineage and Common-Origin Closure
```

Only after that should reviewed selection declaration + selection-lineage graph
completeness be added.
