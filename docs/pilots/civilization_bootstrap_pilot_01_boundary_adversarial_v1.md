# Civilization Bootstrap Pilot 01 — First Boundary Adversarial Review v1

Status: **PR10.0 first adversarial pass**

This review attacks the boundary introduced by PR10.0:

```text
versioned Pilot 01 protocol
        ↓
private raw capture workspace
        X
no automatic PR2 evidence / evaluation / state authority
```

The review is intentionally about capture integrity and authority separation. It does not score or evaluate a participant.

## Frozen boundaries

```text
PILOT CAPTURE != EVIDENCE
PILOT RESPONSE != CLAIM
PILOT ARTIFACT != EVALUATION
RUNNER != EVALUATOR

CAPTURE COMPLETENESS != CAPABILITY
CAPTURE INCOMPLETENESS != COMMAND FAILURE
MISSING OPTIONAL EXECUTION != FAILURE

DECLARED HUMAN ORIGIN != AUTHENTICATED HUMAN ORIGIN
STRUCTURALLY VALID CAPTURE != PROOF OF HUMAN AUTHORSHIP

VALID WORKSPACE != DIRECTORY WITH SOME VALID FILES
VALID WORKSPACE = EXACT PR10.0 LAYOUT + EXACT CAPTURE/ARTIFACT CLOSURE

WORKSPACE CONSISTENCY != SESSION AUTHENTICITY
CAPTURED_AT != AUTHENTICATED EVENT TIME

HASH != AUTHENTICITY
HASH != AUTHORSHIP
HASH != EVIDENCE AUTHORITY
```

## Blocker 1 — symlink and workspace substitution

### Attack

The initial implementation verified that the workspace root itself was not a symlink, but `captures/` and `artifacts/` were accepted through ordinary directory checks. A symlinked internal directory could therefore redirect capture reads or artifact writes outside the intended workspace.

Metadata files and ancestor path components also required stronger treatment.

### Repair

PR10.0 now requires:

- no symlink component in the workspace path;
- a real non-symlink workspace directory;
- regular non-symlink `workspace.json`, `protocol.json`, and `PRIVATE_WORKSPACE.txt` files;
- real non-symlink `captures/` and `artifacts/` directories;
- no symlink components in captured artifact paths;
- no symlink components in runner text/artifact input paths.

The workspace top level is closed-world and must contain exactly the five frozen entries.

```text
SOME EXPECTED FILES PRESENT != VALID WORKSPACE
```

## Blocker 2 — artifact/capture substitution and orphan data

### Attack

The initial artifact validator checked path containment, byte size, and SHA-256. Those checks were insufficient to prove that an artifact belonged to the capture claiming it.

A capture could be manually edited to reference another in-workspace artifact with matching metadata, and unrelated artifact directories could coexist without being represented by any capture.

### Repair

Every artifact capture now has one canonical filesystem relationship:

```text
capture_id = C
original_filename = F

artifact.relative_path
    == artifacts/C/F
```

Additionally:

- `artifacts/C/` must be a real directory;
- it must contain exactly one file named `F`;
- `F` must be a regular non-symlink file;
- its size and SHA-256 must match the capture metadata;
- the set of artifact directories must equal the set of artifact-bearing capture IDs exactly.

Therefore:

```text
ARTIFACT BYTES WITH MATCHING HASH != CORRECT CAPTURE LINKAGE
ORPHAN ARTIFACT != HIDDEN PILOT INPUT
```

## Closed-world capture set

The initial loader selected `*.json` files and therefore could ignore other adjacent entries.

PR10.0 now rejects any `captures/` entry that is not a regular non-symlink `.json` capture file. Each file must:

- deserialize under the exact schema;
- reserialize byte-for-byte to the stored canonical deterministic JSON;
- have a filename exactly equal to `<capture_id>.json`;
- match workspace protocol/session/subject constraints;
- use a probe and capture kind allowed by the frozen protocol.

Unexpected `synthetic.json`, `evidence.json`, hidden text files, alternate encodings, or pretty-printed substitute capture files do not silently coexist with the canonical raw set.

## Protocol snapshot substitution

The workspace protocol snapshot must deserialize and equal the frozen Pilot 01 protocol object.

The test suite additionally freezes the SHA-256 of canonical serialized protocol revision `@1`:

```text
aa0c601450ed28516fa08af60ca92501180fde0483d453b83962df2689e5bd7c
```

This prevents an accidental code change from silently mutating serialized `@1` prompts or boundaries while tests remain unaware.

The fingerprint is deliberately **not** described as authentication:

```text
PROTOCOL SHA-256 != ISSUER AUTHORITY
PROTOCOL SHA-256 != SIGNATURE
PROTOCOL SHA-256 != HISTORICAL ARCHIVE PROOF
```

A material semantic change should be reviewed and normally receive a new protocol revision.

## Incomplete capture set must not become participant failure

### Attack

The initial runner exposed:

```text
validate --require-complete
```

which returned a non-zero process exit code while required probes were missing.

Although documented as capture completeness only, this created a product-level failure channel that downstream scripts could easily relabel as participant failure.

### Repair

The mode was removed.

A structurally valid incomplete workspace now returns validation success and reports:

```text
capture_complete=false
missing_required_probe_ids=...
```

Frozen:

```text
MISSING REQUIRED CAPTURE != FAILED PARTICIPANT
CAPTURE INCOMPLETENESS != PROCESS FAILURE
```

Structural corruption still fails validation. Missing observation does not.

## Capture provenance laundering

Pilot 01 accepts only the structural enum value:

```text
SUBJECT_PROVIDED
```

The adversarial suite intentionally demonstrates that a caller can manually construct canonical capture JSON carrying that declaration and pass structural workspace validation.

That is an explicit limit, not a hidden guarantee:

```text
SUBJECT_PROVIDED = DECLARED ORIGIN
SUBJECT_PROVIDED != AUTHENTICATED AUTHORSHIP
```

Adding a local hash, deterministic serializer, or another self-asserted field would not solve this problem.

PR10.0 therefore refuses to claim human-authorship authentication and, critically, refuses to give raw captures automatic evidence authority.

## Timestamp and session substitution

PR10.0 validates local consistency:

- capture `protocol_ref` must match workspace protocol;
- capture `session_id` must match workspace session;
- capture `subject_ref` must match workspace subject;
- capture `captured_at` must not precede workspace `created_at`;
- timestamps must be timezone-aware and canonically serialized.

However a coordinated rewrite of a local manifest and all dependent capture files can still be internally consistent.

Frozen:

```text
CONSISTENT SESSION ID != AUTHENTICATED SESSION
CONSISTENT SUBJECT REF != AUTHENTICATED PERSON
CAPTURED_AT != TRUSTED TIMESTAMP
CREATED_AT != TRUSTED SESSION START
```

Trusted timestamping, signer identity, hardware attestation, and remote append-only archival are outside PR10.0.

## Hidden synthetic-data path

The real runner surface remains limited to:

```text
init
show-protocol
record-text
record-artifact
validate
```

It has no generation, demo, sample, grading, or evaluation command.

A static regression now inspects Pilot 01 implementation imports. The package may not import PR4 derivation, PR7 history, PR8 progression, PR9 Player Window, or proposal authority modules. From PR2 epistemics it imports only `CapabilitySubjectRef`.

This closes the obvious hidden implementation route:

```text
NO PUBLIC evaluate() BUT PRIVATE AUTHORITY PIPELINE INSIDE RUNNER
```

That pattern is not permitted in PR10.0.

Test fixtures may contain synthetic values to exercise software invariants. They remain test fixtures and are not emitted into participant workspaces.

```text
SYNTHETIC TEST FIXTURE != PILOT DATA
```

## Accidental Capture -> Evidence authority creep

The Pilot 01 public API contains no:

```text
materialize_capture_as_evidence
evaluate_capture
evaluate_session
derive_state
derive_frontier
render_player_window
generate_answer
generate_sample_capture
```

The static import regression makes the same boundary stronger than a naming test: the underlying authority modules are absent from Pilot 01 implementation dependencies.

The future reviewed materializer therefore remains a real architectural step rather than a helper already hidden in the capture runner.

## What this pass proves

After the repair, PR10.0 can claim:

1. the participant-facing protocol revision is exact and regression-frozen;
2. a valid workspace has a closed, deterministic PR10.0 filesystem shape;
3. capture files are canonical and bound to one protocol/session/subject snapshot;
4. file artifacts have exact capture-linked paths and integrity metadata;
5. missing required captures remain absence-of-observation rather than failure;
6. the capture runner contains no automatic evidence/evaluation/state pipeline.

## What this pass does not prove

It does **not** prove:

- who authored a text or artifact before ingestion;
- that a declared subject identity corresponds to a physical person;
- that local timestamps are externally trustworthy;
- that a locally copied workspace has not been coherently rewritten by an actor with filesystem access;
- that SHA-256 identifies an authoritative source;
- that a structurally valid capture is useful evidence;
- that any participant answer is correct;
- that any capability is present, absent, high, low, safe, licensed, or ready.

Those are intentionally outside the capture boundary.

## Result

The first adversarial pass therefore strengthens PR10.0 from “strict files in a private directory” to a much narrower claim:

> **A validated Pilot 01 workspace is an exact, closed, locally self-consistent raw-capture snapshot under the frozen protocol. It is not authenticated human provenance and it carries no capability or evidence authority by itself.**
