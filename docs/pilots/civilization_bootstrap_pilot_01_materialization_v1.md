# Civilization Bootstrap Pilot 01 — Reviewed Capture-to-Evidence Materialization Boundary v1

Status: **PR10.1 initial implementation contract + exact-candidate review-binding hardening**

Policy ref:

```text
capability_lab:reviewed_pilot_capture_to_evidence@1
```

## Outcome

PR10.1 introduces the first explicit reviewed bridge from a validated private `PilotCaptureRecord` into a bounded PR2 `EvidenceRecord`.

The bridge is deliberately narrow. It does not grade a response, decide whether requested work is correct, create a capability claim, assess claim support, derive capability state, create history, derive a frontier, or produce a Player Window.

```text
VALIDATED PRIVATE PILOT CAPTURE
              |
              v
PilotEvidenceMaterializationCandidate
              |
      exact selected review
              |
      +-------+--------+
      |                |
MATERIALIZE      DO_NOT_MATERIALIZE
      |                |
      v                X
EvidenceRecord         no EvidenceRecord
```

Core boundary:

```text
CAPTURE != EVIDENCE
CANDIDATE != EVIDENCE
REVIEW != EVALUATION
MATERIALIZE != CLAIM SUPPORT
MATERIALIZED EVIDENCE != CAPABILITY CONCLUSION
DO_NOT_MATERIALIZE != NEGATIVE EVIDENCE
NO CAPTURE != NEGATIVE EVIDENCE

OPAQUE MATERIALIZATION ID != EXACT CANDIDATE BINDING
REVIEW OF CANDIDATE A != AUTHORITY TO MATERIALIZE CANDIDATE B
```

## Why PR10.1 exists

Real pilot use must support cases where a required probe has a valid raw capture without the requested worked performance, and cases where an optional probe remains entirely unobserved. Those geometries must remain representable without collapsing them into one success/failure bit or a capability conclusion.

```text
CAPTURE PRESENT != SUCCESSFUL PERFORMANCE
REQUESTED WORK NOT PRODUCED != INCORRECT WORK
REQUESTED WORK NOT PRODUCED != CAPABILITY ABSENCE
NO OPTIONAL CAPTURE != FAILED EXECUTION
```

PR10.1 therefore materializes only the fact that an exact capture exists under an exact Pilot 01 context. Any later interpretation belongs to PR2 claim/evaluation governance.

Private Pilot 01 responses, workspace identifiers, snapshot fingerprints, and participant-specific outcomes are not versioned fixtures and are not copied into this repository.

## Candidate boundary

`propose_pilot_capture_evidence_materialization_v1(...)` takes one explicit `capture_id` from one structurally valid stable private workspace.

It creates a `PilotEvidenceMaterializationCandidate`, not an `EvidenceRecord`.

A candidate preserves:

```text
materialization_id
policy_ref
protocol_ref
session_id
subject_ref
capture_id
probe_id
capture_kind
source_snapshot_sha256
source_capture_sha256
proposed_evidence_id
proposed_at
```

`subject_ref` remains the typed PR2 `CapabilitySubjectRef`; PR10.1 does not downgrade person scope to an untyped convenience string.

The candidate pins two different source integrity references:

- `source_snapshot_sha256` — the exact PR10.0 closed-world workspace snapshot at proposal time;
- `source_capture_sha256` — a domain-separated SHA-256 over canonical serialized `PilotCaptureRecord` bytes.

PR10.1 also exposes `pilot_evidence_materialization_candidate_sha256(...)`, a separate domain-separated SHA-256 over the exact canonical serialized `PilotEvidenceMaterializationCandidate` bytes. That digest is not stored on the candidate itself; it is recorded by the review so the review is bound to the exact candidate content it approved.

```text
WORKSPACE SNAPSHOT HASH != AUTHENTICATED SESSION HISTORY
CAPTURE HASH != HUMAN AUTHORSHIP
CAPTURE HASH != CAPABILITY EVIDENCE BY ITSELF
CANDIDATE HASH != REVIEWER IDENTITY
CANDIDATE HASH != REVIEW AUTHORITY BY ITSELF
HASH != REVIEW AUTHORITY
```

Because the candidate digest covers the canonical candidate schema, changing `proposed_evidence_id`, `proposed_at`, source fingerprints, selected capture/context fields, policy/protocol refs, subject/session scope, or `materialization_id` changes the digest.

If the workspace changes after proposal — even through an otherwise valid appended capture — the old candidate is stale and resolution fails closed. A new snapshot requires a new candidate and a new explicit review.

This strictness is intentional for v1:

```text
REVIEW OF SNAPSHOT A != REVIEW OF SNAPSHOT B
SAME CAPTURE ID != PERMISSION TO IGNORE WORKSPACE CHANGE
SAME MATERIALIZATION ID != SAME CANDIDATE
```

## Review boundary

`PilotEvidenceMaterializationReview` records one exact review of one exact materialization candidate.

A review preserves:

```text
review_id
materialization_id
candidate_sha256
policy_ref
reviewer_ref
verdict
reviewed_at
rationale
```

`materialization_id` is an opaque logical identifier. It is not treated as a content hash or uniqueness proof. `candidate_sha256` is the exact-content binding. Resolution requires both the logical ID and the candidate digest to match the selected candidate.

```text
MATERIALIZATION ID MATCH != CANDIDATE CONTENT MATCH
CANDIDATE DIGEST MATCH + ID MATCH -> REQUIRED FOR REVIEW RESOLUTION
```

V1 supports only:

```text
PilotEvidenceMaterializationReviewerKind.HUMAN
```

and exactly two verdicts:

```text
MATERIALIZE
DO_NOT_MATERIALIZE
```

The human mechanism kind is declared metadata, not identity authentication:

```text
DECLARED HUMAN REVIEWER != AUTHENTICATED HUMAN IDENTITY
REVIEWER REF != AUTHORITY GRANT
REVIEW POLICY REF != SIGNED POLICY CONTENT
```

PR10.1 does not majority-vote reviews, prefer the latest review, infer reviewer authority from mechanism kind, or automatically resolve conflicting independent review records. The resolver consumes one explicitly selected candidate and one explicitly selected matching review.

A review cannot be replayed onto another structurally valid candidate merely because that candidate reuses the same opaque `materialization_id`. Candidate content changes require a new candidate digest and therefore a new review record.

`DO_NOT_MATERIALIZE` returns no `EvidenceRecord`. It does not manufacture a negative record, failure outcome, contradiction, or capability state.

## Neutral PR2 EvidenceRecord mapping

A `MATERIALIZE` verdict produces one PR2 `EvidenceRecord` with deliberately conservative semantics.

### Evidence kind

V1 uses a fixed capture-form mapping:

```text
PilotCaptureKind.TEXT_RESPONSE -> EvidenceKind.OTHER
PilotCaptureKind.FILE_ARTIFACT -> EvidenceKind.ARTIFACT
```

PR10.1 does not infer `SELF_REPORT`, `QUIZ`, `SUPERVISED_EXERCISE`, `PROJECT`, `REAL_WORLD_DEMONSTRATION`, or another stronger PR2 evidence kind merely from the probe wording.

```text
PROMPT LOOKS LIKE QUIZ != EvidenceKind.QUIZ
TEXT RESPONSE != SELF_REPORT BY CONSTRUCTION
FILE ARTIFACT != SUCCESSFUL DEMONSTRATION
```

### Outcome

PR10.1 v1 always materializes:

```text
EvidenceRecord.outcome = None
```

It does not choose PR2 `SUCCESS`, `PARTIAL`, `FAILURE`, or `NOT_APPLICABLE` from raw capture content.

```text
"I DO NOT KNOW" != FAILURE OUTCOME BY MATERIALIZATION
NO WORKED ANSWER != FAILURE OUTCOME BY MATERIALIZATION
ARTIFACT EXISTS != SUCCESS OUTCOME BY MATERIALIZATION
```

A later `ClaimEvaluation` may interpret evidence relative to an explicit proposition and policy. Materialization itself does not.

### Summary and context

PR10.1 does not copy or paraphrase participant response text into the PR2 summary.

The summary/context state only bounded source facts such as exact probe id, capture kind, protocol/session context, and declared origin. Declared tools are copied as PR2 `ContextFactorKind.TOOL` factors because they are explicit capture metadata rather than inferred evaluation.

```text
RAW RESPONSE TEXT != MATERIALIZER-GENERATED INTERPRETATION
MATERIALIZER != NATURAL-LANGUAGE EVALUATOR
```

The source content remains in the private Pilot 01 workspace.

### Time

Resolution requires one explicit timezone-aware `resolved_at` value. This is the time at which the selected review is resolved by this boundary, whether the verdict creates an `EvidenceRecord` or returns no record.

```text
PilotCaptureRecord.captured_at
    <= candidate.proposed_at
    <= review.reviewed_at
    <= resolved_at

if verdict == MATERIALIZE:
    EvidenceRecord.observed_at = PilotCaptureRecord.captured_at
    EvidenceRecord.recorded_at = resolved_at
    ProvenanceStep.occurred_at = resolved_at

if verdict == DO_NOT_MATERIALIZE:
    result = None
```

This preserves three distinct facts: when the source observation was captured, when a human review decision was recorded, and when that selected review was resolved by the materialization boundary.

```text
REVIEW TIME != REVIEW RESOLUTION TIME
REVIEWED CANDIDATE != ALREADY-EXISTING EvidenceRecord
DO_NOT_MATERIALIZE != FICTIONAL MATERIALIZATION TIME
```

These remain declared local timestamps under the PR10.0 boundary; resolution does not upgrade them into trusted timestamps.

### Provenance

The materialized `EvidenceRecord` carries an `EXTERNAL_RECORD` provenance source:

```text
pilot_capture:<source_capture_sha256>
```

and, only for a `MATERIALIZE` verdict, a `pilot_materialize` provenance step at `resolved_at` identifying the declared reviewer actor ref, frozen materialization policy ref, opaque materialization/review IDs, and the exact `candidate_sha256` that the selected review bound.

The same capture fingerprint appearing in more than one record would expose common source dependence; record count must not be interpreted as independent evidence strength.

```text
SAME SOURCE CAPTURE != INDEPENDENT EVIDENCE
MULTIPLE MATERIALIZATIONS != MORE CAPABILITY
OPAQUE MATERIALIZATION ID != REVIEW CONTENT HASH
OPAQUE REVIEW ID != SIGNATURE
CANDIDATE SHA-256 != SIGNATURE
```

PR10.1 does not provide a signed governance archive for candidate/review content. A standalone PR2 EvidenceRecord therefore does not cryptographically prove the external candidate/review records named in its provenance note.

## Source verification and TOCTOU limit

Proposal and resolution each validate the PR10.0 private workspace through its stable double-read boundary. Resolution additionally requires exact equality with the candidate's pinned workspace and capture fingerprints.

Before any verdict can materialize evidence, resolution also recomputes the domain-separated canonical candidate digest and requires exact equality with `review.candidate_sha256`.

This detects ordinary source substitution between proposal and resolution and cross-candidate review replay, but it is not a filesystem lock, authenticated review signature, or linearizable multi-process transaction.

```text
STABLE DOUBLE READ != LOCK
MATCHING SNAPSHOT HASH != FUTURE FILESYSTEM GUARANTEE
SOURCE VERIFICATION != AUTHENTICATED HUMAN HISTORY
CANDIDATE DIGEST MATCH != AUTHENTICATED REVIEWER IDENTITY
```

PR10.1 does not mutate the private Pilot 01 workspace while proposing or resolving materialization.

## Strict serialization

PR10.1 defines deterministic strict schemas for candidate and review records:

```text
capability_lab/pilot_evidence_materialization_candidate@1
capability_lab/pilot_evidence_materialization_review@1
```

The serializers require exact fields, reject duplicate JSON keys and unknown fields, reject boolean schema versions, use explicit timezone-aware extended ISO-8601 timestamps, canonicalize valid times to UTC, and reject non-finite JSON constants.

`candidate_sha256` is a required strict field of the review schema and must be a lowercase 64-character SHA-256 digest. Removing it, malformed digest text, or substituting a digest for another candidate fails closed at serialization/resolution boundaries.

Serialization does not create a review decision or evidence authority.

```text
SERIALIZED CANDIDATE != EVIDENCE
SERIALIZED REVIEW != AUTHENTICATED APPROVAL
DESERIALIZED REVIEW != MATERIALIZATION BY ITSELF
CANONICAL CANDIDATE DIGEST != SIGNATURE
```

## Authority localization

PR10.0 intentionally allowed the raw Pilot 01 package to import only `CapabilitySubjectRef` from PR2. PR10.1 changes that boundary narrowly rather than giving the whole pilot package epistemic authority.

Raw capture modules remain limited to their previous PR2 subject-ref dependency. Only `materialization.py` may import the explicit PR2 subject/evidence/provenance construction types needed for this bridge. `materialization_serialization.py` may import only `CapabilitySubjectRef` and `EvidenceId` from PR2.

All Pilot 01 modules remain forbidden from importing:

```text
capability_lab.derivation
capability_lab.history
capability_lab.progression
capability_lab.player_window
capability_lab.proposals
```

The materialization bridge also does not import `CapabilityClaim` or `ClaimEvaluation`.

The PR10.0 CLI remains capture-only:

```text
init
show-protocol
record-text
record-artifact
validate
```

There is intentionally no `materialize`, `review`, `evaluate`, `derive-state`, or equivalent raw-runner command in PR10.1 v1.

## Non-goals

PR10.1 does not add:

- automatic capture-to-evidence conversion;
- bulk materialization of all captures;
- response correctness grading;
- inferred requested-work completion labels;
- PR2 `EvidenceOutcome` inference;
- automatic `CapabilityClaim` creation;
- `ClaimEvaluation` or evaluation policy logic;
- PR3 state derivation;
- PR7 achievement/milestone/Legend creation;
- PR8 progression derivation;
- PR9 Player Window generation;
- model/LLM reviewer;
- reviewer identity authentication;
- majority vote or latest-review authority;
- signed candidate/review archive;
- persistence/sync/global no-reuse registry;
- mutation of the raw private workspace;
- publication/export permission.

## Next controlled step

After exact-head validation and adversarial review of PR10.1, a private Pilot 01 snapshot may be used locally to create explicit materialization candidates and human review records without committing participant content to the repository.

Only after bounded PR2 `EvidenceRecord` values exist should Capability Lab design actual capability claims and claim evaluations for a pilot.
