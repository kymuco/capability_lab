# Epistemic Records v1

Status: **PR2 implementation contract**

PR2 introduces Capability Lab's first person-scoped epistemic layer. It records observations independently from capability interpretation, represents reviewable propositions against exact capability semantic revisions, and records evaluator/policy-specific interpretations of evidence without producing personal capability state.

## Core boundary

```text
Source Event / Artifact -> EvidenceRecord
                              |
CapabilityConceptRef ------> CapabilityClaim
                              |
EvidenceRecord ---------------+
EvaluationPolicyRef ----------+--> ClaimEvaluation
EvaluatorRef -----------------+
                                      |
                                      X
                            PersonalCapabilityState
                                  (PR3)
```

The following distinctions are normative:

```text
EVIDENCE != CAPABILITY
CLAIM != CAPABILITY
EVALUATION != CAPABILITY
EVALUATION != PERSONAL STATE

EVIDENCE RECORD != CAPABILITY MAPPING
EVIDENCE DOES NOT KNOW WHAT IT PROVES
INTERNAL CLAIM != SOURCE EVIDENCE
MULTIPLE EVIDENCE RECORDS != INDEPENDENT EVIDENCE

EVIDENCE KIND != RELIABILITY
PROVENANCE != VALIDITY
PROVENANCE != RELIABILITY

OBSERVED CONTEXT != CLAIM SCOPE

CAPABILITY CLAIM = PROPOSITION
CLAIM != EVIDENCE SET
CLAIM != EVALUATION
UNEVALUATED CLAIM != SUPPORTED CLAIM
EVALUATED EVIDENCE BELONGS TO ClaimEvaluation

FAILURE OBSERVATION != LOW CAPABILITY
SUCCESS OBSERVATION != MASTERY

EVIDENCE RELIABILITY != CLAIM SUPPORT
CLAIM SUPPORT != COVERAGE
CONFLICT != SUFFICIENCY
RECENCY != RELIABILITY

EVALUATOR != AUTHORITY
POLICY != TRUTH
POLICY REF != POLICY CONTENT HASH
EVALUATOR REF != AUTHENTICATED GLOBAL IDENTITY
SUBJECT REF != AUTHENTICATED GLOBAL PERSON ID

SERIALIZABLE != SHAREABLE
```

## Subject and record identity

PR2 uses nominal `CapabilitySubjectRef`, `EvidenceId`, `CapabilityClaimId`, and `ClaimEvaluationId` types. These identifiers are opaque record references, not profiles, content hashes, authority grants, or semantic capability identifiers.

A `CapabilitySubjectRef` identifies the subject of person-scoped records without adding profile fields. Subject identity must remain separate from operator, contributor, evaluator, and viewer roles.

`CapabilitySubjectRef` is exact only inside the subject-registry/import governance that interprets it. It is not globally collision-proof and does not authenticate a real-world person. Two independent stores that both contain `alice` must not silently assume that the refs denote the same person. Combining independently governed record sets requires an explicit identity-mapping decision or continued namespace/isolation at the import boundary.

Record IDs identify immutable historical records. Once persisted, the same `EvidenceId`, `CapabilityClaimId`, or `ClaimEvaluationId` must not be reused for materially different record content. A changed observation, proposition/scope/semantic reference, or evaluation is a new record with a new ID. `EpistemicRecordSet` enforces uniqueness inside one snapshot; persistent storage and synchronization layers must preserve the same no-ID-reuse contract across snapshots.

Opaque record IDs are likewise not globally collision-proof across mutually untrusted stores. Importers must not equate independently issued IDs merely because their strings match unless the relevant registry/governance relationship establishes that interpretation.

An `EpistemicRecordSet` may contain records for more than one subject. That does not create cross-subject authority: internal derivation and claim evaluation remain subject-isolated.

## EvidenceRecord

`EvidenceRecord` stores an observation, artifact, assessment, attestation, outcome, or demonstration. It intentionally contains no `CapabilityId` or `CapabilityConceptRef`: a single observation may later bear differently on multiple capability propositions.

Core evidence kinds are:

- `SELF_REPORT`;
- `CONVERSATION_OBSERVATION`;
- `QUIZ`;
- `SUPERVISED_EXERCISE`;
- `ARTIFACT`;
- `PROJECT`;
- `EXTERNAL_ASSESSMENT`;
- `REPEATED_PERFORMANCE`;
- `REAL_WORLD_DEMONSTRATION`;
- `OTHER`.

Evidence kind is descriptive and does not imply reliability. Evidence outcome may be `SUCCESS`, `PARTIAL`, `FAILURE`, or `NOT_APPLICABLE`; outcome is not a capability level.

`observed_at` and `recorded_at` must be timezone-aware and are canonicalized to UTC. `recorded_at` cannot precede `observed_at`.

For point observations, `observation_started_at` is omitted and `observed_at` identifies the observation time. For a bounded observation window or series, `observation_started_at` identifies the earliest represented observation and `observed_at` identifies the terminal/latest represented observation. The start may not follow the terminal observation. `REPEATED_PERFORMANCE` requires an explicit `observation_started_at`, so repeated evidence cannot silently collapse a longitudinal observation into one ambiguous timestamp.

Recency remains derivable from the terminal `observed_at` under a later evaluation policy rather than being persisted as an unexplained score. The explicit start preserves duration/window information without turning duration into capability evidence by itself.

## EvidenceContext

Evidence context records the conditions actually observed. It can preserve machine-readable scope tags plus explicit factors such as tools, assistance, accessibility accommodations, collaboration, reference material, automation, and environmental conditions.

Context factor kinds include `TOOL`, `ASSISTANCE`, `ACCOMMODATION`, `COLLABORATION`, `REFERENCE_MATERIAL`, `AUTOMATION`, `ENVIRONMENT`, and `OTHER`. Exact duplicate context factors are rejected so deterministic records do not silently double-count the same described condition.

Context factors are not automatic penalties. Their meaning for a proposition belongs in evaluation.

## Provenance

`ProvenanceTrail` preserves one or more source references and optional ordered transformation steps. Generic source kinds can identify actors, artifacts, external records, systems, evidence records, or claims, but internal epistemic references are deliberately layer-restricted.

For an `EvidenceRecord`, an internal epistemic parent may only be another `EvidenceRecord`. An evidence record may not derive from an internal `CapabilityClaim`: a claim is an interpretation, not source evidence. This layer-invalid form is rejected by the `EvidenceRecord` constructor rather than being allowed to circulate until snapshot assembly. A record also rejects self-derivation and any provenance step that occurs after its own `recorded_at` before snapshot assembly. If an external assertion or attestation is itself observed, it must be captured as evidence through an actor/external-record source rather than feeding an internal capability claim back into the evidence layer.

For a `CapabilityClaim`, an internal epistemic parent may only be another `CapabilityClaim`. Evaluated `EvidenceRecord` references are intentionally absent from claim provenance and are rejected by the `CapabilityClaim` constructor; evidence selection and bearing belong to `ClaimEvaluation`. Claims likewise reject self-derivation and provenance steps after their own `created_at` locally. This prevents claim identity from becoming a hidden evidence bundle.

Internal provenance is subject-isolated. Derived evidence must have the same subject as its source evidence, and a claim derived from another claim must have the same subject as its source claim. Internal provenance parents must already exist in the record set, cannot point backward from an earlier record to a later parent, and each same-layer provenance graph must be acyclic.

Provenance steps are order-bearing history. Their order is preserved, their timestamps must be nondecreasing inside the trail, and a step cannot occur after the record creation boundary (`recorded_at` for evidence or `created_at` for claims). If internal parent records are listed and transformation steps are present, the transformation chain may not begin before the latest internal parent existed.

Cycle validation is iterative rather than recursive. Deep valid derivation graphs therefore do not depend on Python's recursion limit.

Derived evidence references source evidence rather than replacing it. An evaluation is allowed to inspect both a source record and a record derived from it because they may expose different representations or relevant properties, but their coexistence does **not** imply statistical or epistemic independence. Any later weighting/aggregation policy must consult provenance rather than treating assessment count as independent support count.

Provenance explains where a record came from; it does not assert that the record is valid, reliable, tamper-proof, content-addressed, independent, or true.

## CapabilityClaim

A `CapabilityClaim` is a stable, reviewable proposition about one `CapabilitySubjectRef`. It contains:

- a nominal claim identifier;
- the subject;
- an exact `CapabilityConceptRef`;
- a non-empty proposition statement;
- explicit `ClaimScope`;
- creation time;
- proposition provenance.

A claim does **not** contain an evaluated evidence bundle or a conclusion. New evidence or a new evaluation policy can therefore evaluate the same proposition without changing claim identity.

Claims must reference an exact semantic revision. A historical `concept@2` must never silently become `concept@4` merely because a newer catalog is supplied. As established in PR1, `CapabilityConceptRef` is exact relative to the namespace/catalog governance that issued that semantic record; it is not a cryptographic content address.

Observed evidence context and claim scope are deliberately separate. Evaluation determines whether evidence observed in one context justifies a proposition with a stated scope.

## EvaluationPolicyRef and EvaluatorRef

Every `ClaimEvaluation` carries an exact, versioned `EvaluationPolicyRef` in canonical `<namespace>:<key>@<revision>` form and an `EvaluatorRef` identifying a human, rule, model, or external system.

`EvaluationPolicyRef` identifies an exact declared policy revision only within a governance regime that agrees on that policy namespace. It is not a cryptographic content address, proof of policy contents, trust level, or authority grant. Future policy registries/snapshot digests may strengthen historical content verification without changing this boundary.

`EvaluatorRef` is an opaque evaluator identity within the record/import governance that interprets it. Its `kind` distinguishes human, rule, model, and external-system roles, but the ref is not globally collision-proof, does not authenticate a real-world actor, and is not itself a versioned evaluator implementation. Where collision resistance matters, producers should issue scoped refs such as `local:reviewer_01` or a provider-specific run identifier. Evaluation decision semantics remain anchored to the exact `EvaluationPolicyRef`.

Evaluator identity does not grant authority. Model output remains an evaluation record, not accepted personal state.

## EvidenceAssessment

Evidence meaning is claim-relative and evaluation-relative. Each `EvidenceAssessment` records:

- an `EvidenceId`;
- bearing: `SUPPORTS`, `CONTRADICTS`, `INDETERMINATE`, or `NOT_RELEVANT`;
- qualitative reliability: `UNASSESSED`, `LOW`, `MODERATE`, or `HIGH`;
- a coverage note;
- rationale.

Reliability is not probability and is not claim support. The same `EvidenceRecord` may support one claim, contradict another, and remain indeterminate for a third.

## ClaimEvaluation

`ClaimEvaluation` combines one claim reference, one exact policy, one evaluator, zero or more evidence assessments, coverage, conflict status, a conclusion, and rationale.

Conclusions are:

- `SUPPORTED`;
- `CONTRADICTED`;
- `MIXED`;
- `INSUFFICIENT`;
- `ABSTAINED`.

Coverage is represented separately as `UNASSESSED`, `PARTIAL`, or `SUFFICIENT_FOR_CLAIM`.

Conflict status is `NONE`, `RESOLVED_BY_POLICY`, or `UNRESOLVED`. Supporting and contradicting evidence cannot coexist while conflict is silently marked `NONE`. `RESOLVED_BY_POLICY` requires an actual directional conflict and may resolve only to `SUPPORTED` or `CONTRADICTED`.

`UNRESOLVED` requires both supporting and contradicting assessments but does **not** force sufficiency. Its conclusion may be `MIXED`, `INSUFFICIENT`, or `ABSTAINED`. This preserves the distinction between the existence of directional conflict and whether the available evidence is sufficient for any substantive conclusion. `MIXED` still requires actual supporting and contradicting evidence.

An evaluation with no evidence may only be `INSUFFICIENT` or `ABSTAINED`.

Cross-record time is causal: `evaluated_at` cannot precede the referenced claim's `created_at`, and an evaluation cannot assess an `EvidenceRecord` whose terminal `observed_at` lies in the evaluation's future. `recorded_at` may be later than a historical evaluation when the local record is legitimately backfilled after the underlying observation occurred.

## EpistemicRecordSet

`EpistemicRecordSet` is an immutable deterministic snapshot containing evidence records, claims, and evaluations. It is not a personal capability state or a publication surface.

Cross-record validation rejects:

- duplicate record identifiers;
- evaluations referencing missing claims or evidence;
- evidence about one subject used to evaluate another subject's claim;
- internal evidence-to-claim or claim-to-evidence provenance leakage;
- dangling, cross-subject, future-pointing, self-referential, or cyclic internal provenance;
- provenance steps occurring after their record creation boundary or before an explicitly referenced internal parent existed;
- evaluations occurring before their claim or assessed observations;
- duplicate evidence assessment inside one evaluation.

Record sets can exist independently of a current semantic catalog so historical records remain preservable. Explicit `validate_against_catalog()` requires an exact concept revision match and rejects silent substitution of the catalog's current revision.

`EpistemicRecordSet` is a snapshot, not the system-wide identity registry. It cannot prove that a record ID was never reused in another historical snapshot; persistent storage/synchronization must enforce the no-ID-reuse contract when those layers are introduced. It likewise cannot decide whether subject IDs from independently governed stores refer to the same real-world person; that is an explicit import/identity-mapping responsibility.

## Serialization and privacy

The deterministic schema marker is:

```text
capability_epistemics/v1
```

Strict ingestion rejects unknown fields, malformed nested records, duplicate JSON object keys, strings in place of arrays, non-standard JSON numeric constants, invalid enum values, dangling references, and invalid cross-record invariants.

Timestamp ingestion uses a deliberately narrow extended ISO-8601 profile: `YYYY-MM-DDTHH:MM:SS[.fraction]Z` or the same form with an explicit `±HH:MM` offset. Arbitrary separators accepted by Python's permissive `datetime.fromisoformat()`, basic no-separator date/time forms, and timezone-less timestamps are rejected. Accepted timestamps are normalized to UTC for deterministic serialization.

Equivalent valid record sets serialize deterministically regardless of input ordering. Ordered provenance transformation steps remain ordered rather than being canonicalized as a set. Observation windows round-trip exactly through the v1 schema.

Serialization is not consent, publication, synchronization, or sharing. Person-scoped epistemic records remain private by default under the Capability Lab constitution.

## Explicit non-goals

PR2 does not implement:

- `PersonalCapabilityState` or competence dimensions;
- mastery, novice/intermediate/expert labels, or capability scores;
- evidence weighting or automatic evidence-to-state algorithms;
- deterministic baseline evaluation policy (PR4);
- automatic claim creation or model authority;
- policy registry/content-addressed policy snapshots;
- globally authenticated evaluator or subject identities;
- cross-store identity reconciliation;
- record-database or synchronization-wide ID immutability enforcement;
- recommendations, progression, achievements, or Human Level;
- full consent/guardian/organizational authorization workflows;
- database storage, synchronization, publication, or Commons aggregation;
- full Civilization Bootstrap ontology.

The Civilization Bootstrap examples and tests are bounded smoke fixtures only.
