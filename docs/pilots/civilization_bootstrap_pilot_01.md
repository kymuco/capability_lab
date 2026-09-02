# Civilization Bootstrap Pilot 01 — Protocol & Private Workspace Boundary

Status: **PR10.0 baseline + first boundary hardening**

Protocol ref:

```text
civilization_bootstrap:pilot_01_basic_electricity@1
```

Capability / frame:

```text
civilization_bootstrap:basic_electricity@1
civilization_bootstrap:technical_competence@1
```

## Outcome

PR10.0 introduces the first versioned protocol and private local capture workspace for a real one-subject Civilization Bootstrap pilot.

It does **not** evaluate the participant, derive capability state, create achievements, or produce a Player Window. Its job is narrower: preserve exactly declared participant-provided responses/artifacts under a deterministic protocol so a later reviewed step can decide what, if anything, becomes governed PR2 evidence.

```text
REAL PARTICIPANT WORK
        ↓
PilotCaptureRecord
        X
NO AUTOMATIC EvidenceRecord / Claim / Evaluation / State
```

Core boundary:

```text
PILOT CAPTURE != EVIDENCE
PILOT RESPONSE != CLAIM
PILOT ARTIFACT != EVALUATION
RUNNER != EVALUATOR

CAPTURE COMPLETENESS != CAPABILITY
CAPTURE INCOMPLETENESS != COMMAND FAILURE
MISSING OPTIONAL EXECUTION != FAILURE
```

## Why capture is separate from evidence

A raw response or artifact may later support one or more bounded `EvidenceRecord` values, or may turn out not to be useful evidence at all. PR10.0 therefore does not let filesystem ingestion silently gain epistemic authority.

The later materialization boundary must remain explicit and reviewable:

```text
PilotCaptureRecord
        ↓ explicit reviewed materialization (future)
EvidenceRecord
        ↓
Claim / Evaluation / State
```

PR10.0 deliberately does not implement the arrow above.

## Participant-facing protocol

The frozen protocol contains four probes:

1. `conceptual_explanation` — required text response;
2. `calculation_work` — required text response;
3. `diagnosis_reasoning` — required text response;
4. `execution_artifact` — optional text and/or file artifact.

The participant-facing protocol contains prompts and boundaries, but no answer key, scoring threshold, mastery criterion, dimension binding, evaluation policy, or recommendation.

```text
PROTOCOL PROMPT != EVALUATION RUBRIC
QUESTION != EXPECTED ANSWER
```

The optional execution probe may be skipped. Its absence means the pilot did not observe execution in that session; it is not a failed attempt and does not imply low capability.

## Frozen protocol revision

The canonical serialized bytes of protocol revision `@1` are regression-frozen by tests. Changing prompts, boundaries, probe requirements, capability/frame refs, or other serialized protocol semantics requires review and normally a new revision rather than silent mutation under the same exact ref.

The regression fingerprint is only a software-change detector:

```text
PROTOCOL SHA-256 != AUTHENTICITY
PROTOCOL SHA-256 != ISSUER IDENTITY
PROTOCOL SHA-256 != HISTORICAL ARCHIVE PROOF
```

## Physical boundary

Pilot 01 is intentionally bounded to ordinary low-voltage DC contexts appropriate to the participant's existing equipment and experience.

The protocol explicitly excludes:

- mains wiring;
- high-voltage systems;
- opened power supplies;
- unknown energized systems.

The protocol is not a safety certification, license, or permission to perform electrical work.

## Private workspace boundary

Repository-local pilot data belongs under `.local/`, which is gitignored by PR10.0.

If the runner detects that a requested workspace is inside a git repository, it rejects any location that is not below:

```text
<repo>/.local/
```

A workspace outside the repository is also allowed.

```text
VERSIONED PROTOCOL != PRIVATE PARTICIPANT DATA
LOCAL != PUBLIC
NO NETWORK != SAFE TO SHARE
WORKSPACE COPY == DATA EXPORT
```

Workspace path components must not resolve through symlinks. The workspace root, metadata files, `captures/`, `artifacts/`, per-capture artifact directories, and captured artifact files must all satisfy their expected regular-file/real-directory roles.

## Closed-world workspace integrity

PR10.0 does not treat a directory as valid merely because some expected files can be parsed.

```text
VALID WORKSPACE != DIRECTORY WITH SOME VALID FILES

VALID WORKSPACE =
    EXACT TOP-LEVEL LAYOUT
    + EXACT CANONICAL METADATA
    + EXACT CANONICAL CAPTURE FILE SET
    + EXACT CAPTURE↔ARTIFACT CLOSURE
```

The top level must contain exactly:

```text
workspace.json
protocol.json
PRIVATE_WORKSPACE.txt
captures/
artifacts/
```

Unexpected adjacent files such as `synthetic.json`, `evidence.json`, or hidden alternative inputs invalidate the workspace.

`captures/` may contain only regular, non-symlink canonical JSON capture files whose filename matches `capture_id` exactly.

For a file artifact capture, the only valid linkage is:

```text
artifacts/<capture_id>/<original_filename>
```

The per-capture artifact directory must contain exactly that one file. Orphan artifact directories, missing artifact directories, extra adjacent artifact files, path substitution between captures, symlinked paths, and digest/size mismatches invalidate the workspace.

## Workspace layout

After initialization:

```text
.local/pilots/cb01/
├── workspace.json
├── protocol.json
├── PRIVATE_WORKSPACE.txt
├── captures/
└── artifacts/
```

Initialization creates **no sample answers, demo captures, synthetic evidence, evaluations, or Player Window data**.

Each capture is one immutable JSON file:

```text
captures/<capture_id>.json
```

`capture_id` uses a deliberately narrower cross-platform file-key grammar than general Capability Lab opaque IDs because it is used as a Windows-compatible filename. Windows reserved device stems are rejected.

Artifact filenames are also constrained to simple cross-platform-safe filenames before they are copied into the workspace.

Artifact captures record:

- canonical workspace-relative artifact path;
- original filename;
- byte size;
- SHA-256 digest.

The digest is an integrity/linkage check only:

```text
HASH != HUMAN AUTHORSHIP
HASH != AUTHENTICITY
HASH != EVIDENCE AUTHORITY
```

## Exact capture schema

A `PilotCaptureRecord` preserves:

```text
capture_id
protocol_ref
session_id
subject_ref
probe_id
capture_kind
origin_kind
captured_at
declared_tools
participant_note
text_content | artifact
```

Capture kinds:

```text
TEXT_RESPONSE
FILE_ARTIFACT
```

Pilot 01 origin kind:

```text
SUBJECT_PROVIDED
```

That value is a declaration represented by the capture format. A manually constructed structurally valid capture can carry the same declaration.

```text
DECLARED HUMAN ORIGIN != AUTHENTICATED HUMAN ORIGIN
STRUCTURALLY VALID CAPTURE != PROOF OF HUMAN AUTHORSHIP
```

The runner has no `generate`, `demo`, `sample`, `grade`, or `evaluate` command. It can ingest data the caller supplies, but it cannot prove how those bytes were authored before ingestion.

## Session and timestamp semantics

The workspace manifest and every selected capture must agree on `protocol_ref`, `session_id`, and `subject_ref`. A capture timestamp must be timezone-aware and must not precede the workspace `created_at` value.

These are consistency constraints, not external authentication:

```text
WORKSPACE CONSISTENCY != SESSION AUTHENTICITY
SUBJECT_REF CONSISTENCY != SUBJECT AUTHENTICATION
CAPTURED_AT != AUTHENTICATED EVENT TIME
CREATED_AT != AUTHENTICATED SESSION-START TIME
```

A coordinated rewrite of otherwise valid local metadata is outside PR10.0's authenticity guarantees. PR10.0 intentionally does not add signatures, remote attestations, biometric proof, or a trusted timestamp service.

## Strict serialization

Protocol, workspace manifest, and capture JSON use strict deterministic serialization:

- exact fields;
- duplicate JSON keys rejected;
- unknown or missing fields rejected;
- `schema_version` is exact integer `1` (`true` is rejected);
- timestamps must be timezone-aware;
- enums are exact;
- canonical JSON output is sorted and newline-terminated.

Workspace validation additionally requires stored metadata and capture files to equal their canonical deterministic serialization exactly.

```text
STRICT SERIALIZATION != SOURCE AUTHENTICATION
CANONICAL JSON != HUMAN AUTHORSHIP
```

## Runner

Show the frozen public protocol:

```powershell
python -m capability_lab.pilots.civilization_bootstrap_01.run show-protocol
```

Initialize a private session from the repository root:

```powershell
python -m capability_lab.pilots.civilization_bootstrap_01.run init `
  --workspace .local/pilots/cb01 `
  --session-id cb01_session `
  --subject-ref local_subject
```

For reproducible serialized metadata, an explicit timezone-aware `--created-at` may be supplied. It remains a declared timestamp, not authenticated session-start time.

Record a text response already written by the participant:

```powershell
python -m capability_lab.pilots.civilization_bootstrap_01.run record-text `
  --workspace .local/pilots/cb01 `
  --capture-id conceptual_01 `
  --probe conceptual_explanation `
  --input .local/input/conceptual.md `
  --tool "plain text editor"
```

Record an optional local artifact:

```powershell
python -m capability_lab.pilots.civilization_bootstrap_01.run record-artifact `
  --workspace .local/pilots/cb01 `
  --capture-id execution_photo_01 `
  --probe execution_artifact `
  --input C:\path\to\subject_photo.jpg
```

Validate structural integrity and see missing required probes:

```powershell
python -m capability_lab.pilots.civilization_bootstrap_01.run validate `
  --workspace .local/pilots/cb01
```

A structurally valid but incomplete workspace returns success and reports, for example:

```text
capture_complete=false
missing_required_probe_ids=calculation_work,diagnosis_reasoning
```

There is intentionally no `--require-complete` failure mode in PR10.0.

```text
MISSING REQUIRED CAPTURE != FAILED PARTICIPANT
CAPTURE INCOMPLETENESS != PROCESS FAILURE
```

## No-synthetic-data boundary

PR10.0 freezes:

```text
RUNNER GENERATED ANSWER -> FORBIDDEN SURFACE
RUNNER GENERATED EVIDENCE -> FORBIDDEN SURFACE
MODEL EVALUATION -> NOT IMPLEMENTED
AUTO CLAIM MATERIALIZATION -> NOT IMPLEMENTED
AUTO STATE DERIVATION -> NOT IMPLEMENTED
```

The Pilot 01 implementation also has an import-boundary regression preventing hidden coupling to PR4 derivation, PR7 history, PR8 progression, PR9 Player Window, or proposal authority layers. From PR2 epistemics it imports only the subject reference needed to scope private captures.

The versioned test suite may use synthetic records to test software invariants. Those test fixtures are not Pilot 01 participant data and are never emitted by the real runner.

```text
SYNTHETIC TEST FIXTURE != PILOT PARTICIPANT DATA
NO GENERATOR SURFACE != AUTHORSHIP AUTHENTICATION
```

## Non-goals

PR10.0 does not add:

- Capture -> EvidenceRecord materialization;
- evaluation rubric or answer key;
- LLM/model evaluator;
- PR4 state selection;
- PR7 achievement/milestone creation;
- PR8 frontier derivation;
- PR9 Player Window generation from real pilot data;
- participant scoring, XP, rank, level, mastery, or Human Level;
- authorship authentication;
- trusted timestamping or session attestation;
- publication/sharing workflow;
- cloud storage or telemetry;
- electrical safety certification.

## Next controlled step

After PR10.0 passes its exact-head gate, the intended next action is **not another generic architecture layer**. It is to initialize one real private Pilot 01 workspace and collect the three required participant responses.

Only after inspecting those real captures should Capability Lab design the reviewed `PilotCaptureRecord -> EvidenceRecord` materialization boundary.
