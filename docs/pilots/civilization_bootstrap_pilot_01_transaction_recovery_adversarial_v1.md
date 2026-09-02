# Civilization Bootstrap Pilot 01 — Transaction & Recovery Adversarial Review v1

Status: **PR10.0 second and final adversarial pass**

This review attacks failure, interruption, replay, and mutation boundaries in the
private Pilot 01 capture path. It does not add evaluation, evidence
materialization, capability inference, or any new authority layer.

```text
versioned protocol
      ↓
private raw capture mutation
      ↓
valid closed workspace snapshot
      X
no automatic EvidenceRecord / Evaluation / State authority
```

## Frozen transaction boundaries

```text
PARTIAL OPERATION != VALID CAPTURE
HANDLED INTERRUPTION != PARTIAL FINAL PUBLICATION

CORRUPT WORKSPACE != APPENDABLE WORKSPACE
ORPHAN ARTIFACT != RECOVERED CAPTURE

REQUIRED PROBE DUPLICATE != ONE OBSERVATION
OPTIONAL EXECUTION PLURALITY != DUPLICATE REQUIRED ATTEMPT
CAPTURE ID -> ALWAYS UNIQUE

VALIDATION REPORT != LOCK
VALIDATION REPORT != FUTURE FILESYSTEM GUARANTEE

SNAPSHOT SHA-256 != AUTHENTICATED HISTORY
SNAPSHOT SHA-256 != TRUSTED TIMESTAMP
SNAPSHOT SHA-256 != HUMAN AUTHORSHIP
SNAPSHOT SHA-256 != EVIDENCE AUTHORITY

DETERMINISTIC REPLAY != PROOF OF ORIGINALITY
BYTE-EQUIVALENT COPY != SAME HISTORICAL EVENT
```

## Blocker 1 — append-after-corruption

The initial mutation path loaded workspace metadata before appending a new
capture, but metadata validity is weaker than complete workspace integrity.

A workspace could therefore already contain a corrupted capture JSON, an
artifact whose bytes no longer matched its recorded digest, or an orphan
artifact directory while a new append began.

That is now forbidden.

The supported public mutation path requires a complete stable validation pass
before any new text or artifact capture starts:

```text
APPEND PRECONDITION
=
FULL CURRENT WORKSPACE VALIDATION
```

If the current snapshot is invalid, the new capture is not published.

```text
APPEND AFTER CORRUPTION -> REJECT
NEW VALID CAPTURE != REPAIR OF OLD CORRUPTION
```

PR10.0 does not silently delete, rewrite, or reinterpret damaged participant
material to make append possible.

## Blocker 2 — partial workspace initialization

The original initializer created the final workspace directory and then wrote
its subdirectories and metadata sequentially. A handled interruption could
therefore leave a partial final target.

Initialization now stages the entire empty workspace in a private sibling
directory on the same filesystem and publishes the final directory only after
staging is complete.

Handled failures clean staging and leave the final target unpublished.

```text
PARTIAL INIT STAGING
!=
PARTIAL FINAL WORKSPACE
```

A host/process crash may still leave an abandoned private staging sibling. That
is not treated as a valid Pilot 01 workspace and is not silently replayed.

## Text capture publication

Text capture JSON is serialized and flushed to a private staging file before
publication.

Publication creates the canonical final capture path without replacing an
existing file:

```text
staged canonical JSON
      ↓ atomic single-file create
captures/<capture_id>.json
```

A handled publication failure removes staging and leaves no partial final
capture JSON.

```text
INTERRUPTED TEXT WRITE != PARTIAL VALID CAPTURE
EXISTING CAPTURE PATH != OVERWRITE TARGET
```

The public path then validates the complete post-write workspace again.

## Artifact capture is deliberately not called fully atomic

A file-artifact capture has two independent final objects:

```text
artifacts/<capture_id>/<filename>
captures/<capture_id>.json
```

The current PR10.0 layout has no portable single filesystem primitive that
publishes those two paths atomically as one transaction.

The hardened path therefore does the strongest bounded thing that is honest:

1. validate the current workspace completely;
2. copy/hash/build artifact and capture metadata in private staging;
3. publish the artifact directory;
4. publish canonical capture JSON without overwrite;
5. validate the complete resulting workspace;
6. on handled failure before capture publication, roll back the runner-owned
   artifact destination.

An abrupt process/host failure between steps 3 and 4 may leave:

```text
artifact directory present
capture JSON absent
```

That state is not silently recovered and is not valid.

The closed-world validator sees the orphan artifact directory and fails closed.
Because every append requires a valid current workspace, later capture also
refuses to proceed.

```text
ARTIFACT MULTI-PATH CRASH WINDOW EXISTS
ORPHAN CRASH STATE -> INVALID
INVALID CRASH STATE -> NO FURTHER APPEND
```

PR10.0 intentionally does not add an automatic journal replay that could itself
become a hidden capture-ingestion or provenance-laundering surface.

## Required-probe duplicate geometry

Capture IDs were already unique, but unique file IDs alone do not resolve
required-probe attempt ambiguity.

For example:

```text
conceptual_01 -> conceptual_explanation / TEXT_RESPONSE
conceptual_02 -> conceptual_explanation / TEXT_RESPONSE
```

would represent two separate required-probe responses. Treating both as one
unambiguous Pilot 01 observation would hide attempt geometry.

PR10.0 therefore freezes:

```text
REQUIRED PROBE -> AT MOST ONE CAPTURE
```

This applies to:

```text
conceptual_explanation
calculation_work
diagnosis_reasoning
```

A future protocol that intentionally repeats a required probe must model repeat
attempts explicitly rather than add extra capture IDs under revision `@1`.

## Optional execution intentionally remains plural

The frozen `execution_artifact` prompt explicitly permits preserving participant
photos or measurement notes as captures. Optional execution is therefore a raw
collection boundary, not a single-attempt scalar slot.

It may contain multiple declared captures, including multiple text notes and
multiple file artifacts, as long as every capture ID remains unique and every
artifact satisfies the exact linkage/integrity rules.

```text
OPTIONAL EXECUTION PLURALITY != REQUIRED-PROBE DUPLICATION
MULTIPLE OPTIONAL ARTIFACTS != CAPABILITY SCORE
MULTIPLE OPTIONAL ARTIFACTS != STRONGER EVIDENCE BY COUNT
```

PR10.0 does not count, rank, weight, or automatically aggregate these optional
captures.

## Stable-read validation and filesystem TOCTOU

PR10.0 cannot make the local filesystem globally immutable while validation is
running. Another process with write access can race the reader.

The supported public validator therefore performs two complete
structural/integrity reads and computes a deterministic workspace fingerprint on
both passes.

If the reports or fingerprints differ:

```text
PRIVATE WORKSPACE CHANGED DURING VALIDATION
```

validation fails.

This narrows ordinary validation-time races. It does not create a lock held
after the function returns.

```text
VALIDATION REPORT != LOCK
RETURNED REPORT != PROMISE THAT FILES CANNOT CHANGE NEXT
```

PR10.0 does not claim linearizable multi-process writer semantics.

A race after pre-validation but before/during final publication can make
post-write validation fail. The operation reports failure instead of laundering
the resulting filesystem state as valid.

## Workspace snapshot fingerprint

Successful public validation returns:

```text
snapshot_sha256
```

The fingerprint is domain-separated and deterministically covers the validated
workspace's relative directory/file shape plus exact file bytes.

The absolute machine path is excluded, so a byte-equivalent copy of the same
valid workspace can reproduce the same fingerprint.

It answers only the bounded integrity question:

> Does this independently validated copy/replay contain the same exact Pilot 01
> workspace bytes and relative shape as the snapshot I expected?

It does not answer:

- who authored those bytes;
- when they were really produced;
- whether this is the historical original;
- whether the subject identity is authenticated;
- whether any capture is true, correct, useful evidence, or capability proof.

```text
SAME SNAPSHOT SHA-256
-> SAME HASHED LOCAL CONTENT/SHAPE UNDER THIS SCHEME

SAME SNAPSHOT SHA-256
!= SAME HISTORICAL EVENT
!= AUTHENTICATED ORIGINAL
!= EVIDENCE AUTHORITY
```

## Copy-after-validation mutation

A caller may validate workspace `A`, receive fingerprint `H1`, and then have the
filesystem mutate before copying it.

The earlier report does not bless later bytes.

Therefore a copy must be independently validated and the resulting fingerprint
compared with the expected snapshot identity.

```text
VALIDATE SOURCE
THEN MUTATE SOURCE
THEN COPY
!=
VALIDATED COPY OF ORIGINAL SNAPSHOT
```

Changed but still canonical files may produce another structurally valid
workspace with a different `snapshot_sha256`. That distinction is deliberate.

## Deterministic workspace replay

The adversarial suite freezes two replay cases.

### Byte-equivalent copy

Copy every validated workspace byte and relative path to another local root,
validate independently, and the fingerprint is reproduced.

### Independent deterministic construction

Two separately initialized Pilot 01 workspaces with the same declared protocol,
session/subject refs, explicit timestamps, capture IDs, canonical text, artifact
filenames/bytes, and capture metadata reproduce the same snapshot fingerprint.

```text
DETERMINISTIC SERIALIZATION + SAME INPUT BYTES
-> SAME SNAPSHOT IDENTITY

SAME SNAPSHOT IDENTITY
-X-> PROOF OF SAME REAL-WORLD EVENT
```

Replay proves representation determinism, not historical authenticity.

## Recovery policy

PR10.0 recovery remains intentionally conservative.

Handled runner failures clean staging and, where ownership is unambiguous, roll
back unpublished runner-owned artifact output.

For an already-invalid final workspace, PR10.0 does not automatically:

- delete orphan participant bytes;
- choose between duplicate required-probe captures;
- rewrite timestamps or session refs;
- regenerate missing capture metadata;
- convert a partial artifact into evidence;
- resume an untrusted external transaction journal.

Those actions would require additional provenance and review semantics.

```text
RECOVERY != SILENT REPAIR OF PARTICIPANT HISTORY
```

The safe PR10.0 behavior is fail closed, preserve ambiguity, and require an
explicit future/manual decision if a real pilot ever reaches such a state.

## Public mutation route

The package-level and CLI mutation surface is now explicitly routed through
`transactional.py`:

```text
initialize_private_workspace
record_text_capture
record_artifact_capture
validate_private_workspace
```

The earlier `workspace.py` remains the structural parsing/closure engine. It is
not the supported package-level mutation route after this adversarial repair.

This routing is regression-tested so transaction hardening cannot be bypassed by
an accidental package export change.

## Authority boundary remains unchanged

None of this adds:

```text
PilotCaptureRecord -> EvidenceRecord
EvidenceRecord -> ClaimEvaluation
ClaimEvaluation -> PersonalCapabilityState
State -> ProgressionFrontier
State/History/Frontier -> PlayerWindow
```

`transactional.py` handles filesystem publication and snapshot integrity only.

```text
TRANSACTIONAL CAPTURE != EVIDENCE AUTHORITY
STABLE SNAPSHOT != EVALUATED SNAPSHOT
SNAPSHOT FINGERPRINT != CAPABILITY CONCLUSION
```

## Result

After the second adversarial pass, the strongest PR10.0 claim is:

> **The supported public Pilot 01 mutation path stages before publication,
> refuses append over an invalid workspace, keeps required-probe attempt
> geometry unambiguous without suppressing plural optional execution captures,
> fails closed on unresolved artifact crash states, revalidates post-write
> state, and can identify deterministic byte-equivalent workspace snapshots. It
> does not authenticate history, provide durable multi-process transactions, or
> grant raw captures any evidence/capability authority.**

This is the final adversarial pass for PR10.0. After an exact-head green local
gate, the remaining work should be release/readiness review rather than another
scope-expanding hardening layer.
