# Capability Lab Vocabulary

Status: **terminology synchronized through PR12.1 reviewed external-observation to neutral-evidence materialization governance**

This file is the current release-level terminology index. The pre-PR10.1
long-form vocabulary snapshot is preserved at
`docs/legacy/pr10_0/vocabulary.md`.

## Recurring boundaries

```text
PILOT CAPTURE != EVIDENCE
CANDIDATE != EVIDENCE
REVIEW != EVALUATION
MATERIALIZE != CLAIM SUPPORT
MATERIALIZED EVIDENCE != CAPABILITY CONCLUSION
DO_NOT_MATERIALIZE != NEGATIVE EVIDENCE
REVIEWED-RESOLUTION RECEIPT != SIGNATURE / AUTHENTICATED HISTORY
ISSUANCE WITNESS != SIGNATURE / AUTHENTICATED HISTORY
TERMINAL DEPENDENCE PASS != STATISTICAL INDEPENDENCE
TERMINAL DEPENDENCE PASS != INDEPENDENT REPLICATION
CLAIM TEMPLATE != CAPABILITY CLAIM
RUBRIC != CLAIM EVALUATION
EVALUATION POLICY != EVALUATION
EVIDENCE BEARING GUIDANCE != AUTOMATIC BEARING
MISSING REQUIRED PROBE != CONTRADICTION
MISSING OPTIONAL EXECUTION != FAILURE
DEPENDENCE PASS != CLAIM SUPPORT
EVIDENCE != CAPABILITY
CLAIM != CAPABILITY
EVALUATION != CAPABILITY
MODEL STATE != PERSON
CURRENT != LATEST
CURRENT != BEST
CURRENT != PREFERRED
CURRENT != MASTERY
CURRENT != READINESS
CURRENT != PERMISSION
CLEAR != ABSENT
VISIBLE != CURRENT
VISIBLE != AUTHORITATIVE
HIDDEN != DELETED
PRESENTATION != AUTHORITY
EXTERNAL OBSERVATION != EVIDENCE
DUPLICATE DELIVERY != NEW OBSERVATION
REUSED SOURCE EVENT ID != PERMISSION TO REWRITE HISTORY
DECLARED ORIGIN != AUTHENTICATED ORIGIN
PAYLOAD HASH != AUTHORSHIP / CORRECTNESS / CAPABILITY
LEDGER SIZE != EVIDENCE STRENGTH
REVIEWED OBSERVATION != CAPABILITY
MATERIALIZE != SUCCESS
DO_NOT_MATERIALIZE != FAILURE / CONTRADICTION / NEGATIVE EVIDENCE
DECLARED HUMAN REVIEWER != AUTHENTICATED HUMAN IDENTITY
DETERMINISTIC EVIDENCE ID != CAPABILITY INTERPRETATION
TERMINAL RECEIPT != EVIDENCE / SIGNATURE / TRUSTED TIME
```

## PilotCaptureRecord

A private raw participant capture under one exact Pilot 01
protocol/session/workspace context. It is not a PR2 `EvidenceRecord`, claim,
evaluation, outcome judgment, or capability state. PR10.0 owns raw capture.

## PilotEvidenceMaterializationCandidate

A PR10.1 exact selected-capture proposal. It pins materialization id, frozen
policy/protocol, session/subject/capture/probe/kind, workspace snapshot hash,
canonical capture hash, proposed evidence id, and proposal time. The candidate
is not evidence and grants no authority by itself.

## PilotEvidenceMaterializationReview

An explicit selected review of one exact candidate, bound by candidate SHA and
materialization id. PR10.1 v1 permits only declared HUMAN reviewer kind and the
verdicts `MATERIALIZE` and `DO_NOT_MATERIALIZE`. Declared HUMAN does not
authenticate a real-world identity. `DO_NOT_MATERIALIZE` creates no negative
evidence.

## PilotReviewedMaterializationResolutionReceipt

Resolver-issued local governance metadata for a successful `MATERIALIZE`
resolution. It binds the exact candidate SHA, exact canonical review SHA,
review id, evidence id, exact full canonical PR2 `EvidenceRecord` SHA, and
resolution time.

Each receipt carries a private resolver-issuance witness bound to that exact
receipt payload. The issuer capability is not retained on the witness, so
copying a legitimate receipt or witness does not authorize
`dataclasses.replace(...)` to rebind it to a different payload.

It is not a digital signature, PKI object, authenticated reviewer identity,
trusted timestamp, persistence transaction, or proof that historical execution
occurred.

## PilotReviewedMaterializationResolutionBinding

The exact selected `PilotEvidenceMaterializationReview` paired with its
resolver-issued receipt. Terminal PR10.1 dependence governance requires
one-to-one binding coverage for every materialized observation slot.

## PR10.1 materialized dependence governance

A bounded precondition ladder over multiple materialized observations. The six
families are source, mechanism, coordination/control,
temporal/intervention/carryover, allocation/randomization, and
sampling/selection/cohort construction. Each family has exact-identity,
explicit-ancestry, and reviewed-completeness stages.

A terminal PASS is not a certificate of statistical independence,
exchangeability, representative sampling, independent randomization,
independent cohorts, independent replication, successful performance,
capability support, or claim/evaluation authority.

## PilotClaimTemplate

PR11.0 subject-free policy metadata describing one exact proposition shape
against an exact `CapabilityConceptRef`, plus a `ClaimScope` and the probe basis
required before sufficient coverage may later be considered.

It is **not** a PR2 `CapabilityClaim`. It has no subject, claim id, creation
time, or claim provenance and cannot enter state derivation.

Pilot 01 v1 defines two claim templates:

```text
bounded_reasoning
bounded_execution
```

The separation prevents the optional execution observation from silently
changing the meaning or coverage of the required reasoning proposition.

## PilotRubricCriterion

One human-review criterion inside a PR11.0 probe rubric. It states a bounded
requirement plus optional acceptable variations and material-error conditions.

A criterion is not a score, weight, probability, conclusion, or authority
grant.

## PilotProbeEvaluationRubric

The PR11.0 interpretation specification for one exact Pilot 01 probe. Every
probe has exactly one rubric bound to exactly one claim template.

Each rubric defines criteria, all four PR2 evidence-bearing guidance states, and
missing-probe semantics.

```text
SUPPORTS
CONTRADICTS
INDETERMINATE
NOT_RELEVANT
```

The rubric guides a future explicit evaluator. It does not automatically assign
an `EvidenceBearing`.

## PilotMissingProbeSemantics

PR11.0 distinguishes absence from observed negative evidence.

```text
REQUIRED_COVERAGE_GAP
OPTIONAL_UNOBSERVED
```

The three required reasoning probes use `REQUIRED_COVERAGE_GAP`. The optional
`execution_artifact` uses `OPTIONAL_UNOBSERVED`.

```text
MISSING REQUIRED PROBE != CONTRADICTION
MISSING OPTIONAL EXECUTION != FAILURE
```

## PilotHumanEvaluationPolicy

The versioned PR11.0 Pilot 01 evaluation specification.

Exact ref:

```text
civilization_bootstrap:pilot_01_basic_electricity_human_review@1
```

It contains the exact claim templates, probe rubrics, evidence-bearing
guidance, reliability rule, coverage rule, dependence rule, and explicit
authority boundaries.

It is not a `ClaimEvaluation`, evaluator decision, scoring result, or
`PersonalCapabilityState`.

## Pilot evaluation policy snapshot hash

`pilot_evaluation_policy_sha256_v1(...)` domain-separates and hashes the
deterministic canonical JSON representation of the exact PR11.0 policy content.

```text
POLICY REF != CONTENT HASH
POLICY HASH != SIGNATURE
POLICY HASH != AUTHORITY
SERIALIZED POLICY != EXECUTED EVALUATION
```

The hash is useful for detecting policy-content drift. It does not authenticate
who authored or approved the policy.

## EvidenceRecord

A person-scoped PR2 record of an observation, artifact, assessment,
attestation, outcome, or demonstration. Evidence intentionally contains no
capability mapping. PR10.1 maps reviewed Pilot 01 captures only to neutral
evidence; PR12.1 maps reviewed generic external observations only through a
frozen neutral mapping. Later interpretation belongs to explicit
claims/evaluations.

## CapabilityClaim / ClaimEvaluation / PersonalCapabilityState

A `CapabilityClaim` is a stable scoped proposition against an exact capability
concept. A `ClaimEvaluation` records governed interpretation of evidence
relative to that claim. `PersonalCapabilityState` is a separate derived layer.

PR11.0 defines claim templates and an evaluation policy only. Later PR11.x
layers construct and govern real evaluations, state, acceptance and currentness
without collapsing those meanings together.

## PersonalCapabilityCurrentStateSelection

PR11.8 explicit governed current-state act for one exact concept/frame scope.
`SELECT` names one exact accepted state; `CLEAR` explicitly removes current
state authority for that scope. Newer derivation or acceptance does not move
current automatically.

```text
DERIVED != ACCEPTED
ACCEPTED != CURRENT
CURRENT != LATEST
```

## PersonalCapabilityCurrentStatePortfolio

PR11.10 complete projection of every governed current-selection scope head in
one subject history after full PR11.8 authority replay.

Each entry preserves exact scope, `SELECT`/`CLEAR`, current-selection digest and,
for `SELECT`, exact selected-state identity/content digest. Its
`current_state_set` contains exactly SELECT-head states.

```text
COMPLETE PORTFOLIO != ALL HUMAN CAPABILITIES
CLEAR != ABSENT
ABSENT SCOPE != UNKNOWN
ABSENT SCOPE != INSUFFICIENT
ABSENT SCOPE != NEGATIVE EVIDENCE
```

## CurrentStateProgressionFrontierRequest

PR11.9 state-less progression request. It may describe exact concept/frame seed
and prerequisite scopes but contains no caller-selected personal state ID and
no caller-selected subject. Personal-state inputs are resolved through PR11.8
authority.

## CurrentStateProgressionAuthorityBinding

PR11.9 per-requested-scope authority projection:

```text
SELECT -> exact governed current state
CLEAR  -> explicit cleared current authority, no state
ABSENT -> no governed current-selection scope
```

It is progression input authority only, not readiness, permission,
recommendation, safety or mastery.

## CurrentStateGovernedProgressionFrontier

PR11.9 wrapper that binds the state-less request, complete current-selection
history identity, exact SELECT/CLEAR/ABSENT authority projection, and unchanged
raw PR8 deterministic frontier.

## PlayerWindow

PR9 deterministic source-visible product projection. Raw PR9 intentionally
supports explicit source selection. That is useful as a low-level renderer but
raw `selected_state_ids` / `selected_frontier_id` are not an HDE-facing current
authority contract.

## CurrentStatePlayerWindowRequest

PR11.11 HDE/product-facing request. It contains:

```text
window_id
generated_at
requester_ref
viewer_ref
state-less PR11.9 progression_request
visible_achievement_ids
visible_milestone_ids
visible_legend_id
```

It contains no subject selector, state set, frontier set, selected state IDs,
selected existing frontier ID, supplied PR11.10 portfolio, or supplied PR11.9
governed frontier.

The `visible_*` fields control presentation only.

```text
VISIBLE != CURRENT
HIDDEN != DELETED
NOT DISPLAYED != DID NOT HAPPEN
```

## CurrentStateGovernedPlayerWindow

PR11.11 governed product/read artifact. It fresh-derives PR11.10 complete
current-state authority and PR11.9 governed progression from the same
current-selection history, reconciles their authority bindings, and invokes
unchanged PR9 derivation and source-backed verification.

It contains:

```text
request
subject_ref
current_selection_history_sha256
current_state_portfolio_sha256
governed_frontier_sha256
current_state_entries
frontier_authority_bindings
window
```

All PR11.10 SELECT states are visible in the raw PR9 window even if progression
uses only a subset. PR11.10 CLEAR remains visible in `current_state_entries`;
PR11.9 SELECT/CLEAR/ABSENT remains visible in `frontier_authority_bindings`.

A complete current state later than the requested `as_of` causes rejection
instead of silent filtering.

## PR11.11 digest

`current_state_governed_player_window_sha256_v1(...)` uses:

```text
capability_lab/current_state_governed_player_window@1\0
```

It is deterministic content integrity identity, not a signature,
authentication proof, trusted timestamp, HDE permission, publication authority,
or capability truth.

## HDE read/advisory integration boundary

After PR11.11, HDE may consume a stable governed read snapshot without deciding
which personal state is current or which existing progression frontier should
be treated as authoritative.

PR12.0 + PR12.1 additionally provide a governed write-side admission path from
an external/HDE observation through explicit review to neutral PR2 evidence.
This still does not authorize automatic claim evaluation or capability-state
mutation.

```text
READ / ADVISORY HDE INTEGRATION          = READY
REVIEWED OBSERVATION -> NEUTRAL EVIDENCE = READY
AUTOMATIC CLOSED-LOOP CAPABILITY UPDATE  = NOT READY

HDE ACTIVITY != EVIDENCE
HDE OBSERVATION != EVIDENCE
HDE OUTPUT != CAPABILITY UPDATE
HDE VIEW != CAPABILITY AUTHORITY
```

## ExternalObservationId

PR12.0 opaque identity for one immutable generic external observation record. It
is not an `EvidenceId` and carries no evidence or capability authority.

## ExternalObservationSourceRef

PR12.0 declared external source identity. Source kinds are `application`,
`agent_runtime`, `tool`, `external_system`, `actor`, and `other`.

The ref is provenance metadata only:

```text
DECLARED SOURCE != AUTHENTICATED SOURCE
SOURCE REF != TRUST GRANT
```

## ExternalObservationEnvelope

PR12.0 subject-scoped immutable record of one declared external source event.
It preserves:

```text
observation_id
subject_ref
source_ref
source_event_id
form
origin_kind
observation_started_at?
observed_at
captured_at
context_factors
payload_refs
```

It intentionally contains no EvidenceKind/Outcome, capability concept, claim,
evaluation, state, score, grade, success/failure, mastery, readiness, or
permission field.

```text
EXTERNAL OBSERVATION != EVIDENCE
```

## ExternalObservationForm

Structural source-record form only:

```text
event
text
artifact
conversation
bundle
other
```

It is not PR2 `EvidenceKind`.

```text
ARTIFACT FORM != PROJECT EVIDENCE
TEXT FORM != SELF_REPORT
CONVERSATION FORM != CAPABILITY SUPPORT
EVENT FORM != REAL_WORLD_DEMONSTRATION
```

## ExternalObservationOriginKind

Declared content/execution origin:

```text
subject
other_human
model
system
mixed
unknown
```

Origin is not authenticated identity or contribution measurement.

```text
DECLARED SUBJECT != AUTHENTICATED SUBJECT
DECLARED MODEL != AUTHENTICATED MODEL
MIXED != KNOWN CONTRIBUTION FRACTIONS
```

## ExternalObservationPayloadRef

Stable external payload identity and exact SHA-256 fingerprint, with optional
byte size and MIME type. Capability Lab may keep only this reference/fingerprint
while raw payload bytes remain in local external storage.

```text
PAYLOAD HASH != AUTHORSHIP
PAYLOAD HASH != CORRECTNESS
PAYLOAD HASH != CAPABILITY
```

## ExternalObservationLedger

PR12.0 immutable subject-scoped collection of canonical observations. It requires
unique `observation_id`, unique `(source_ref, source_event_id)`, and one exact
subject across every record.

`admit_external_observation_v1(...)` treats exact replay of an already admitted
canonical source event as an idempotent no-op. Reuse of that source-event
identity or observation id with different content fails closed.

```text
DUPLICATE DELIVERY != NEW OBSERVATION
IDEMPOTENT REPLAY != NEW EVIDENCE
REUSED SOURCE EVENT ID != PERMISSION TO REWRITE HISTORY
```

## ExternalObservationLedgerSuccessionReceipt

Structural PR12.0 result of append-only ledger validation. It binds predecessor
and successor ledger hashes plus retained/added observation ids. A directly
constructed public receipt is not validator-issued.

```text
SUCCESSION RECEIPT != EVIDENCE
SUCCESSION RECEIPT != SIGNATURE
SUCCESSION RECEIPT != AUTHENTICATED HISTORY
```

PR12.0 binds immutability to each exact observation rather than a global
continuously-growing source snapshot, so an unrelated new observation does not
stale an old retained observation.

## PR12.0 digests

Observation digest domain:

```text
capability_lab/external_observation@1\0
```

Ledger digest domain:

```text
capability_lab/external_observation_ledger@1\0
```

They are deterministic content identities, not signatures, authentication,
trusted time, authorship, evidence, or capability truth.

## ExternalObservationEvidenceMaterializationCandidate

PR12.1 exact source-derived proposal for whether one already admitted PR12.0
observation should become neutral PR2 evidence. It binds:

```text
materialization_id
frozen policy_ref
observation_id
observation_sha256
subject_ref
source_ref
source_event_id
form
origin_kind
deterministic materialized_evidence_id
proposed_at
```

The public proposal API does not accept a caller-selected evidence id, evidence
kind/outcome, summary, context, capability concept, claim, score, mastery,
readiness, or permission.

The candidate binds one exact observation, not the continuously growing ledger
hash. Therefore an unrelated later observation does not stale the candidate.

```text
CANDIDATE != EVIDENCE
CANDIDATE != REVIEW
CANDIDATE != CAPABILITY INTERPRETATION
```

## PR12.1 deterministic external-observation EvidenceId

`external_observation_evidence_id_v1(...)` derives the sole evidence identity
for one exact canonical PR12.0 observation:

```text
external_observation:<external_observation_sha256_v1>
```

Repeated materialization attempts for the same exact observation therefore have
the same `EvidenceId`. This prevents caller-selected one-observation -> many-ID
amplification. It does not mean the observation is valid evidence or supports
any claim.

```text
DETERMINISTIC EVIDENCE ID != EVIDENCE QUALITY
DETERMINISTIC EVIDENCE ID != CLAIM SUPPORT
DETERMINISTIC EVIDENCE ID != CAPABILITY
```

## ExternalObservationEvidenceMaterializationReview

PR12.1 explicit review of one exact materialization candidate. The review binds
the exact candidate digest and materialization id and uses the frozen PR12.1
policy. V1 permits only declared `HUMAN` reviewer kind and the verdicts:

```text
MATERIALIZE
DO_NOT_MATERIALIZE
```

The reviewer ref is declared governance metadata, not authenticated real-world
identity.

```text
DECLARED HUMAN REVIEWER != AUTHENTICATED HUMAN IDENTITY
MATERIALIZE != SUCCESS
DO_NOT_MATERIALIZE != FAILURE
DO_NOT_MATERIALIZE != CONTRADICTION
DO_NOT_MATERIALIZE != NEGATIVE EVIDENCE
```

## PR12.1 neutral evidence mapping

Only `MATERIALIZE` creates a PR2 `EvidenceRecord`. The mapping is frozen:

```text
ExternalObservationForm.ARTIFACT
-> EvidenceKind.ARTIFACT

ExternalObservationForm.CONVERSATION
-> EvidenceKind.CONVERSATION_OBSERVATION

EVENT / TEXT / BUNDLE / OTHER
-> EvidenceKind.OTHER

EvidenceRecord.outcome = None
```

Observation times, context factors, payload refs and exact observation
provenance remain source-visible. PR12.1 does not infer a capability topic,
success/failure, evidence bearing, reliability, mastery, readiness, permission,
or recommendation.

## ExternalObservationEvidenceResolutionReceipt

PR12.1 resolver-issued terminal governance metadata for **both** review verdicts.
It binds the exact materialization id, candidate digest, review id/digest,
verdict, observation digest, resolution time, and — only for `MATERIALIZE` —
the exact deterministic evidence id and full canonical PR2 EvidenceRecord
digest.

A `DO_NOT_MATERIALIZE` receipt must contain no evidence id or evidence digest.

Every legitimate receipt carries a private payload-bound issuance witness.
Changing candidate/review/verdict/observation/evidence/resolution fields via
`dataclasses.replace(...)` invalidates the witness.

```text
TERMINAL RECEIPT != EVIDENCE
TERMINAL RECEIPT != SIGNATURE / PKI
TERMINAL RECEIPT != AUTHENTICATED REVIEWER
TERMINAL RECEIPT != TRUSTED TIME
DO_NOT_MATERIALIZE RECEIPT != NEGATIVE EVIDENCE
```

## ExternalObservationEvidenceResolutionBinding

The exact selected PR12.1 review paired with its exact resolver-issued terminal
receipt. Fresh validation replays the admitted observation binding, exact
candidate/review identities, receipt witness, and — for `MATERIALIZE` — the
complete frozen neutral `EvidenceRecord` mapping.

The binding itself is not a claim evaluation, persistence transaction, or
capability update.

## PR12.1 / PR11.3 handoff

PR12.1 stops at:

```text
EvidenceRecord | None
+
terminal resolution receipt
```

It does not mutate `EpistemicRecordSet`. A materialized record enters the
existing epistemic layer only through an explicit successor snapshot governed
by unchanged PR11.3 `validate_epistemic_snapshot_successor_v1(...)`.

Because one exact observation always has one deterministic evidence id, a
second differently reviewed/resolved record for that observation cannot replace
an already appended record without PR11.3 rejecting retained-evidence mutation.

```text
REVIEWED OBSERVATION != CLAIM
MATERIALIZED EXTERNAL EVIDENCE != CLAIM EVALUATION
MATERIALIZED EXTERNAL EVIDENCE != PERSONAL STATE
PR12.1 != CURRENT-STATE AUTHORITY
PR12.1 != PROGRESSION AUTHORITY
```

## Other existing terminology

The project continues to use the PR0–PR9 terminology for capability semantics,
evidence/provenance, competence frames, deterministic state derivation,
proposals, history/achievements/Legends, progression frontiers/evidence
gaps/exploration, and Player Window projections.

For normative current details see:

- `docs/pilots/civilization_bootstrap_pilot_01_materialization_v1.md`
- `docs/pilots/civilization_bootstrap_pilot_01_terminal_dependence_governance_v1.md`
- `docs/pilots/civilization_bootstrap_pilot_01_reviewed_resolution_hardening_v1.md`
- `docs/pilots/civilization_bootstrap_pilot_01_evaluation_policy_v1.md`
- `docs/progression_current_state_handoff_v1.md`
- `docs/current_state_portfolio_v1.md`
- `docs/current_state_governed_player_window_v1.md`
- `docs/external_observation_boundary_v1.md`
- `docs/external_observation_evidence_materialization_v1.md`
