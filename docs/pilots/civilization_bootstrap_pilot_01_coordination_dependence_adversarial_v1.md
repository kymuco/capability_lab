# Civilization Bootstrap Pilot 01 — Explicit Cross-Observation Coordination/Control Authority Dependence

Status: **PR10.1 adversarial closure**

This closure addresses the first dependence layer above reviewed source and mechanism provenance.

The current PR10.1 ladder can already reject:

```text
same exact capture
same session lineage
same elicitation lineage
same exact upstream source
source alias/ancestry/common origin
incomplete source declarations or source graph
same exact acquisition/governance mechanism
mechanism alias/clone/derivation/state-continuation ancestry
incomplete mechanism declarations or mechanism graph
```

That still leaves a different false-replication geometry:

```text
observation A -> source A -> mechanism A
observation B -> source B -> mechanism B

source origins are reviewed separated
mechanism origins are reviewed separated

BUT

one controller chooses both observations
```

or:

```text
one policy execution chooses both collection conditions
one adaptive selector chooses both test cases
one condition assigner chooses both treatments
one scheduler coordinates both collection windows
one adjudication authority decides which observations are admitted
```

Therefore:

```text
SOURCE SEPARATION
+
MECHANISM SEPARATION
!=
CROSS-OBSERVATION CONTROL SEPARATION
```

## Why this is not another mechanism kind

`PilotObservationMechanismRef` describes acquisition/governance mechanisms directly relevant to one observation: operator activity, model runs, tool executions, environments, acquisition pipelines, or review processes.

The new layer describes a higher-order authority/process that can shape **multiple otherwise separate observations**.

For example:

```text
observation A -> tool execution A
observation B -> tool execution B

controller X -> chooses A
controller X -> chooses B
```

The two tool executions can be distinct while the selection process remains shared.

PR10.1 therefore does not overload:

```text
OPERATOR
REVIEW_PROCESS
MODEL_RUN
ACQUISITION_PIPELINE
```

to mean cross-observation control.

## Explicit coordination/control identities

PR10.1 adds:

```text
PilotObservationCoordinationKind
```

with:

```text
CONTROLLER
POLICY_EXECUTION
ADAPTIVE_SELECTOR
CONDITION_ASSIGNER
SCHEDULER
ADJUDICATION_AUTHORITY
COORDINATION_PROCESS
OTHER
```

and:

```text
PilotObservationCoordinationRef(kind, ref)
```

A ref identifies one exact bounded controller/authority/process instance.

This distinction is deliberate:

```text
SAME POLICY DEFINITION
!=
SAME POLICY_EXECUTION
```

```text
SAME SELECTOR ALGORITHM
!=
SAME ADAPTIVE_SELECTOR INSTANCE
```

```text
SAME SCHEDULER IMPLEMENTATION
!=
SAME SCHEDULER RUN
```

```text
SAME REVIEWER REF
!=
SAME ADJUDICATION_AUTHORITY
```

Existing metadata is never silently promoted into this layer.

## Candidate-bound declaration

`PilotMaterializationCoordinationDeclaration` contains:

```text
candidate_sha256
coordinations[]
```

and is created through:

```text
build_pilot_materialization_coordination_declaration_v1(...)
```

The declaration is bound to the exact materialization candidate digest.

Therefore:

```text
COORDINATION DECLARATION FOR CANDIDATE A
!=
AUTHORITY FOR CANDIDATE B
```

An empty declaration is valid, but means only:

```text
NO COORDINATION REFS WERE SUPPLIED
```

It does not mean:

```text
NO CROSS-OBSERVATION CONTROLLER EXISTS
```

## Exact dependence key

`pilot_observation_coordination_dependence_key_v1(...)` hashes the exact typed `{kind, ref}` pair under:

```text
capability_lab/pilot_observation_coordination_control_dependence@1
```

and returns:

```text
pilot_observation_coordination:<sha256>
```

The validator therefore does not need to echo raw coordination refs in dependence errors.

Equality means only:

```text
THE SAME EXACT TYPED COORDINATION IDENTITY WAS DECLARED
```

Different keys do not prove distinct causal control origins.

## Coordination entry

`PilotMaterializedEvidenceCoordinationEntry` pairs:

```text
one exact PilotMaterializedEvidenceMechanismEntry
+
one exact candidate-bound coordination declaration
```

This preserves the full previously reviewed source/mechanism basis.

The declaration cannot be replayed onto another materialization candidate.

## Strongest gate

The new gate is:

```text
validate_pilot_materialized_evidence_shared_coordination_preconditions_v1(...)
```

It first invokes:

```text
validate_pilot_materialized_evidence_reviewed_mechanism_origin_preconditions_v1(...)
```

Therefore every earlier structural and completeness gate remains mandatory.

Only after source and mechanism provenance have passed does the gate inspect cross-observation coordination identities.

If:

```text
observation A -> CONTROLLER:controller_x
observation B -> CONTROLLER:controller_x
```

then:

```text
REJECT
```

Likewise:

```text
A -> POLICY_EXECUTION:policy_run_x
B -> POLICY_EXECUTION:policy_run_x
```

```text
A -> ADAPTIVE_SELECTOR:selector_x
B -> ADAPTIVE_SELECTOR:selector_x
```

```text
A -> CONDITION_ASSIGNER:assigner_x
B -> CONDITION_ASSIGNER:assigner_x
```

```text
A -> ADJUDICATION_AUTHORITY:authority_x
B -> ADJUDICATION_AUTHORITY:authority_x
```

all fail the strict shared-coordination independence precondition.

The historical EvidenceRecords remain valid. The gate only blocks a stronger replication interpretation.

## Prior dependence still dominates

Distinct coordination refs cannot repair an earlier dependence.

If two observations already share:

```text
MODEL_RUN:run_x
```

then the existing mechanism gate rejects before coordination identities can help.

Therefore:

```text
DISTINCT CONTROLLERS
!=
PERMISSION TO IGNORE SHARED MECHANISM DEPENDENCE
```

## Empty and distinct declaration semantics

These may pass the new exact-equality layer:

```text
A -> CONTROLLER:a
B -> CONTROLLER:b
```

or:

```text
A -> no declared coordination
B -> no declared coordination
```

But the semantics remain conservative:

```text
DIFFERENT COORDINATION REFS
!=
INDEPENDENT CONTROLLERS
```

```text
EMPTY COORDINATION DECLARATION
!=
NO COORDINATION
```

```text
SHARED-COORDINATION PRECONDITION PASS
!=
INDEPENDENT REPLICATION
```

Distinct refs can still be aliases, descendants of one controller state, executions of one adaptive process, or share a hidden decision authority.

That is intentionally left for later layers.

## No implicit promotion from existing metadata

PR10.1 does not infer coordination from:

```text
same reviewer_ref
same operator ref
same tool name
same model family
same environment label
same session owner
same protocol
same static policy definition
same selector implementation
```

If a reviewer actually served as one shared adjudication authority, that fact must be explicitly declared as:

```text
ADJUDICATION_AUTHORITY
```

If a policy actually executed once and chose conditions for both observations, that bounded execution must be explicitly declared as:

```text
POLICY_EXECUTION
```

This prevents broad metadata equality from manufacturing false dependence.

## New invariants

```text
SOURCE-ORIGIN SEPARATION
!=
CROSS-OBSERVATION CONTROL SEPARATION
```

```text
MECHANISM-ORIGIN SEPARATION
!=
CROSS-OBSERVATION CONTROL SEPARATION
```

```text
SAME EXACT DECLARED COORDINATION AUTHORITY
=>
KNOWN HIGHER-ORDER CORRELATION
```

```text
SAME STATIC POLICY
!=
SAME POLICY EXECUTION
```

```text
SAME REVIEWER METADATA
!=
SAME ADJUDICATION AUTHORITY
```

```text
EMPTY DECLARATION
!=
NO CONTROL AUTHORITY
```

```text
DIFFERENT COORDINATION KEYS
!=
INDEPENDENT CONTROL ORIGINS
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
coordination/control lineage
controller alias discovery
policy-execution ancestry
adaptive-selector state lineage
coordination completeness review
automatic controller inference
policy similarity inference
reviewer-to-authority inference
cryptographic authority identity
evidence weighting
independent-replication claims
CapabilityClaim creation
Evaluation
PR3 state
achievements
progression
Player Window behavior
```

## Next unresolved boundary

Exact coordination equality still cannot detect:

```text
controller A != controller B

BUT

controller A and controller B are aliases
```

or:

```text
policy execution A DESCENDS_FROM controller state X
policy execution B DESCENDS_FROM controller state X
```

or:

```text
selector A CONTINUES_STATE_FROM selector B
```

Likewise, an empty or disjoint declared control set does not establish complete control disclosure.

The next controlled layer should therefore add explicit **coordination/control lineage** before any reviewed coordination-completeness claim.
