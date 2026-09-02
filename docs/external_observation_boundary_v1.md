# PR12.0 — Generic External Observation Boundary v1

## Purpose

PR12.0 introduces a generic subject-scoped observation boundary for data produced
outside Capability Lab, including future HDE adapters, without allowing an
external caller to create evidence or capability authority.

```text
EXTERNAL SOURCE EVENT
        |
        v
ExternalObservationEnvelope
        |
 idempotent exact-event admission
        |
        v
ExternalObservationLedger
        |
 append-only succession validation
        |
        X
NO EvidenceRecord
NO CapabilityClaim
NO ClaimEvaluation
NO PersonalCapabilityState
```

The central invariant is:

```text
EXTERNAL OBSERVATION
=
IMMUTABLE SUBJECT-SCOPED RECORD
OF ONE DECLARED EXTERNAL SOURCE EVENT
WITH EXACT SOURCE IDENTITY
AND EXACT PAYLOAD FINGERPRINTS

WITHOUT
EVIDENCE / CLAIM / EVALUATION / STATE AUTHORITY
```

The core boundary is:

```text
OBSERVATION != EVIDENCE
```

PR12.0 is intentionally separate from the Pilot 01 capture boundary. Pilot
captures are protocol-, probe-, session-, and private-workspace-specific.
External observations are generic records suitable for independent applications,
tools, runtimes, actors, and external systems.

## No HDE-specific dependency

Capability Lab does not import HDE.

A future HDE adapter may identify itself as an external source, for example:

```text
source kind = application
source ref  = hde_core
```

but `hde_core` has no special authority inside Capability Lab.

```text
HDE SOURCE != TRUSTED SOURCE
HDE EVENT != EVIDENCE
HDE TASK COMPLETION != CAPABILITY UPDATE
```

## ExternalObservationEnvelope

One envelope contains:

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

It deliberately contains no EvidenceId, EvidenceKind, EvidenceOutcome,
CapabilityConceptRef, claim/evaluation/state ids, success/failure, score, grade,
mastery, readiness, or permission.

## Exact source-event identity

The stable delivery identity of one source event is:

```text
(source_ref, source_event_id)
```

`admit_external_observation_v1(...)` has explicit retry semantics:

```text
same source-event identity + exact same canonical observation
-> idempotent no-op

same source-event identity + different observation content
-> REJECT
```

Likewise an `observation_id` may not be rebound to different content.

```text
DUPLICATE DELIVERY != NEW OBSERVATION
IDEMPOTENT REPLAY != ADDITIONAL EVIDENCE
REUSED EVENT ID != PERMISSION TO REWRITE HISTORY
```

## Observation form and origin

Forms are structural only:

```text
event
text
artifact
conversation
bundle
other
```

```text
ARTIFACT FORM != PROJECT EVIDENCE
TEXT FORM != SELF_REPORT
CONVERSATION FORM != CAPABILITY SUPPORT
EVENT FORM != REAL_WORLD_DEMONSTRATION
```

Declared origins are:

```text
subject
other_human
model
system
mixed
unknown
```

```text
DECLARED SUBJECT != AUTHENTICATED SUBJECT
DECLARED MODEL != AUTHENTICATED MODEL
MIXED != KNOWN CONTRIBUTION FRACTIONS
```

Payload-bearing forms require at least one exact payload reference. Metadata-only
event/other observations may omit payloads.

## Context and payloads

Observation-side context factors preserve tool, assistance, accommodation,
collaboration, reference-material, automation, environment, and other metadata.
They are not PR2 EvidenceContext values.

`ExternalObservationPayloadRef` contains:

```text
ref
sha256
byte_size?
media_type?
```

Capability Lab need not own the raw bytes.

```text
PAYLOAD HASH != AUTHORSHIP
PAYLOAD HASH != CORRECTNESS
PAYLOAD HASH != CAPABILITY
```

## Time semantics

```text
observation_started_at <= observed_at <= captured_at
```

All times are timezone-aware and canonicalized to UTC.

```text
SOURCE TIME != TRUSTED TIME
CAPTURED_AT != AUTHENTICATED CLOCK
```

## ExternalObservationLedger

One ledger is subject-scoped. It requires unique `observation_id`, unique exact
`(source_ref, source_event_id)`, and exact subject equality for every observation.
Canonical order is by observation id.

```text
LEDGER SIZE != EVIDENCE STRENGTH
MORE OBSERVATIONS != MORE CAPABILITY
```

## Append-only succession

`validate_external_observation_ledger_successor_v1(...)` requires every old
observation to remain present and byte-semantically identical while allowing new
observations to append. It returns a structural receipt containing predecessor
and successor hashes plus retained/added observation ids.

```text
SUCCESSION RECEIPT != EVIDENCE
SUCCESSION RECEIPT != SIGNATURE
SUCCESSION RECEIPT != AUTHENTICATED HISTORY
SUCCESSION RECEIPT != CAPABILITY AUTHORITY
```

Direct public receipt construction is not validator issuance.

## Streaming-source boundary

PR12.0 does not pin one observation to a hash of the entire continuously growing
external source world.

```text
observation A admitted
unrelated observation B later admitted
observation A remains exactly valid
```

```text
NEW UNRELATED EVENT != STALE OLD OBSERVATION
```

Only mutation or rebinding of observation A is forbidden.

## Serialization and digests

Strict schema-v1 serialization supports dict/JSON round trips, exact fields,
duplicate-key rejection, non-finite-number rejection, explicit timezone-aware
times, and typed reconstruction.

Observation digest domain:

```text
capability_lab/external_observation@1\0
```

Ledger digest domain:

```text
capability_lab/external_observation_ledger@1\0
```

```text
DIGEST != SIGNATURE
DIGEST != AUTHENTICATION
DIGEST != TRUSTED TIME
DIGEST != AUTHORSHIP
DIGEST != EVIDENCE
```

## Production dependency boundary

PR12.0 core imports from PR2 only `CapabilitySubjectRef`. It does not import or
construct EvidenceRecord, CapabilityClaim, ClaimEvaluation, HDE, progression,
player-window, history, or state authority.

## Non-goals

PR12.0 does not create evidence, choose EvidenceKind/Outcome, infer correctness,
map observations to capability concepts, evaluate claims, derive/select state,
update progression, authenticate identities, provide trusted timestamps, or
publish external payload bytes.

## Next boundary

PR12.1 is separate:

```text
ExternalObservationEnvelope
        |
exact observation-bound candidate
        |
explicit HUMAN review
        |
MATERIALIZE / DO_NOT_MATERIALIZE
        |
neutral EvidenceRecord or no evidence
```

It must preserve:

```text
REVIEWED OBSERVATION != CAPABILITY
MATERIALIZE != CLAIM SUPPORT
DO_NOT_MATERIALIZE != NEGATIVE EVIDENCE
```

Existing PR11.3 remains the later append-only epistemic succession path.
