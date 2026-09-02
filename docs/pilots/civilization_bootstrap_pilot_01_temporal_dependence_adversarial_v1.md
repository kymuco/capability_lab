# Civilization Bootstrap Pilot 01 — Exact Temporal / Intervention / Carryover Dependence Closure

Status: **PR10.1 adversarial closure**

The current PR10.1 ladder now has reviewed bounded completeness for three causal layers:

```text
SOURCE
    exact identity
    -> ancestry
    -> reviewed completeness

MECHANISM
    exact identity
    -> ancestry
    -> reviewed completeness

COORDINATION / CONTROL
    exact identity
    -> ancestry
    -> reviewed completeness
```

That still does not establish temporal or intervention independence.

Two observations can be fully separated on all three layers and still share one bounded causal history:

```text
observation A -> source A -> mechanism A -> controller A
observation B -> source B -> mechanism B -> controller B

all three origins reviewed separated

BUT

A and B belong to intervention episode X
```

or:

```text
A and B were produced under one adaptive state X
```

or:

```text
A and B share one carryover state X
```

or:

```text
A and B descend from the same bounded exposure/history state X
```

Therefore:

```text
SOURCE SEPARATION
+
MECHANISM SEPARATION
+
COORDINATION SEPARATION
!=
TEMPORAL / INTERVENTION INDEPENDENCE
```

## Why this is a separate causal layer

This layer is not another source, mechanism, or controller type.

A source answers:

```text
what upstream information/material contributed?
```

A mechanism answers:

```text
what acquisition/production/governance mechanism produced the observation?
```

A coordination identity answers:

```text
what higher-order authority/process selected or coordinated multiple observations?
```

The temporal/intervention layer answers:

```text
what bounded causal episode or state can persist across otherwise separate observations?
```

For example, two independent tool executions under two independent controllers can still observe the same subject after one shared intervention. Likewise, two test forms can be collected under separate pipelines but after the same adaptive-learning episode.

PR10.1 therefore adds a separate declaration instead of overloading:

```text
UPSTREAM SOURCE
MECHANISM
COORDINATION AUTHORITY
SESSION
```

with temporal-history semantics.

## Explicit bounded temporal identities

The new enum is:

```text
PilotObservationTemporalKind
```

with:

```text
INTERVENTION_EPISODE
ADAPTIVE_STATE
CARRYOVER_STATE
EXPOSURE_EPISODE
HISTORY_STATE
OTHER
```

and exact typed identity:

```text
PilotObservationTemporalRef(kind, ref)
```

These identities are deliberately bounded.

Examples:

```text
INTERVENTION_EPISODE:training_block_07
ADAPTIVE_STATE:selector_state_after_round_12
CARRYOVER_STATE:post_prompt_memory_state_03
EXPOSURE_EPISODE:shared_stimulus_exposure_05
HISTORY_STATE:subject_history_checkpoint_09
```

The declaration says only that governance already knows the exact bounded identity is relevant to causal dependence.

## What is intentionally not inferred

PR10.1 does **not** infer temporal dependence from:

```text
same timestamp
same minute
same hour
same day
same subject
same session owner
same machine
same protocol
same reviewer
temporal proximity
chronological ordering
```

Therefore:

```text
SAME TIME WINDOW
!=
SAME TEMPORAL CAUSAL EPISODE
```

and:

```text
OBSERVATION B OCCURS AFTER A
!=
B CARRIES STATE FROM A
```

Those are different claims.

A causal episode must be explicitly represented.

## Candidate-bound temporal declaration

The new record is:

```text
PilotMaterializationTemporalDeclaration(
    candidate_sha256,
    temporals,
)
```

created by:

```text
build_pilot_materialization_temporal_declaration_v1(...)
```

The declaration is bound to the exact materialization candidate digest.

Therefore:

```text
TEMPORAL DECLARATION FOR CANDIDATE A
!=
AUTHORITY FOR CANDIDATE B
```

An empty declaration is valid.

Its only meaning is:

```text
NO TEMPORAL / INTERVENTION REFS WERE SUPPLIED
```

It must never be interpreted as:

```text
NO TEMPORAL DEPENDENCE EXISTS
```

## Exact temporal dependence key

The exact typed `{kind, ref}` identity is hashed under:

```text
capability_lab/pilot_observation_temporal_intervention_dependence@1
```

through:

```text
pilot_observation_temporal_dependence_key_v1(...)
```

and produces:

```text
pilot_observation_temporal:<sha256>
```

Same typed identity means known exact shared temporal context.

Different keys mean only different exact declared identities.

```text
DIFFERENT TEMPORAL KEYS
!=
INDEPENDENT TEMPORAL ORIGINS
```

The hashed key reduces accidental raw-ref disclosure in validator errors.

```text
HASHED KEY != ANONYMIZATION
HASHED KEY != AUTHENTICATION
```

## Temporal evidence entry

The new wrapper is:

```text
PilotMaterializedEvidenceTemporalEntry
```

containing:

```text
one exact PilotMaterializedEvidenceCoordinationEntry
+
one exact candidate-bound PilotMaterializationTemporalDeclaration
```

This preserves the entire prior reviewed source/mechanism/coordination basis.

## Strongest gate

The new gate is:

```text
validate_pilot_materialized_evidence_shared_temporal_preconditions_v1(...)
```

It first invokes:

```text
validate_pilot_materialized_evidence_reviewed_coordination_origin_preconditions_v1(...)
```

Therefore the full previous ladder remains mandatory:

```text
exact capture
same session
same elicitation/test form
same upstream source
source ancestry/common origin
reviewed source completeness
same mechanism
mechanism ancestry/common origin
reviewed mechanism completeness
same coordination/control authority
coordination ancestry/common origin
reviewed coordination completeness
```

Only after all of those pass does the new gate inspect exact temporal/intervention identities.

If:

```text
A -> INTERVENTION_EPISODE:X
B -> INTERVENTION_EPISODE:X
```

then:

```text
REJECT
```

Likewise:

```text
A -> ADAPTIVE_STATE:X
B -> ADAPTIVE_STATE:X
```

```text
A -> CARRYOVER_STATE:X
B -> CARRYOVER_STATE:X
```

```text
A -> EXPOSURE_EPISODE:X
B -> EXPOSURE_EPISODE:X
```

```text
A -> HISTORY_STATE:X
B -> HISTORY_STATE:X
```

all represent known exact shared temporal causal context and fail the stricter replication precondition.

The historical EvidenceRecords remain valid. The rejection applies only to a stronger independence interpretation.

## Prior dependence still dominates

Distinct temporal refs cannot repair an earlier dependence.

For example:

```text
A -> controller X
B -> controller X

A -> intervention A
B -> intervention B
```

still rejects through the existing coordination layer before temporal identities can help.

Therefore:

```text
DISTINCT TEMPORAL EPISODES
!=
PERMISSION TO IGNORE SHARED SOURCE / MECHANISM / CONTROL DEPENDENCE
```

## Conservative PASS

These may pass the exact temporal-equality layer:

```text
A -> INTERVENTION_EPISODE:A
B -> INTERVENTION_EPISODE:B
```

or:

```text
A -> no temporal declaration
B -> no temporal declaration
```

but:

```text
DIFFERENT TEMPORAL REFS
!=
DIFFERENT TEMPORAL ORIGINS
```

and:

```text
EMPTY TEMPORAL DECLARATION
!=
NO TEMPORAL DEPENDENCE
```

Two different refs can still be aliases, descendants of one intervention, adjacent states in one adaptive trajectory, or children of a hidden history root.

That is intentionally left for the next lineage layer.

## New invariants

```text
SOURCE / MECHANISM / COORDINATION SEPARATION
!=
TEMPORAL / INTERVENTION SEPARATION
```

```text
SAME EXACT DECLARED INTERVENTION EPISODE
=>
KNOWN TEMPORAL DEPENDENCE
```

```text
SAME EXACT DECLARED ADAPTIVE OR CARRYOVER STATE
=>
KNOWN STATE DEPENDENCE
```

```text
TEMPORAL PROXIMITY
!=
TEMPORAL CAUSAL IDENTITY
```

```text
EMPTY TEMPORAL DECLARATION
!=
NO TEMPORAL DEPENDENCE
```

```text
DIFFERENT TEMPORAL KEYS
!=
INDEPENDENT TEMPORAL ORIGINS
```

```text
PASS
!=
STATISTICAL INDEPENDENCE
```

```text
PASS
!=
AUTHORITY TO CLAIM INDEPENDENT REPLICATION
```

## Non-goals

This closure does not add:

```text
temporal/intervention lineage
intervention alias discovery
adaptive-state ancestry
carryover-state propagation inference
time-window heuristics
automatic temporal clustering
coordination-to-temporal inference
subject-state estimation
temporal completeness review
evidence weighting
independent-replication claim creation
CapabilityClaim creation
Evaluation
PR3 state
achievements
progression
Player Window behavior
```

## Next unresolved boundary

Exact temporal identity still cannot detect:

```text
intervention A != intervention B

BUT

A and B descend from common intervention root X
```

or:

```text
adaptive_state_2 STATE_CONTINUATION_OF adaptive_state_1
```

or:

```text
carryover A DERIVED_FROM history root X
carryover B DERIVED_FROM history root X
```

Therefore the next controlled layer should add explicit **temporal/intervention lineage**, with strict upstream direction and without inferring causality from timestamps alone.

Only after temporal lineage should PR10.1 add reviewed temporal declaration/graph completeness.
