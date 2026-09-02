# Civilization Bootstrap Pilot 01 — Reviewed-Resolution and Release Hardening

Status: **PR10.1 final adversarial closure**

This hardening closes the final whole-PR seams found after the six-family dependence ladder and terminal composition were reviewed as one system.

## Exact reviewed-resolution receipt

The original materializer correctly required one exact `PilotEvidenceMaterializationReview` to create an `EvidenceRecord`, but the later dependence basis stored only `(candidate, evidence)`. A structurally shaped `EvidenceRecord` could therefore describe a review id in its provenance note without the terminal gate receiving the actual selected review object.

PR10.1 now adds:

```text
PilotReviewedMaterializationResolutionReceipt
PilotReviewedMaterializationResolutionBinding
resolve_reviewed_pilot_evidence_materialization_with_receipt_v1(...)
```

For `MATERIALIZE`, the wrapper returns:

```text
exact EvidenceRecord
+
resolver-issued receipt
```

For `DO_NOT_MATERIALIZE`, it returns:

```text
(None, None)
```

The receipt binds domain-separated hashes of the exact canonical candidate review and the exact complete PR2 `EvidenceRecord`, together with materialization/review/evidence identity and `resolved_at`.

The terminal gate requires exact one-to-one binding coverage for every observation slot.

```text
SELF-DESCRIBED PROVENANCE NOTE != REVIEWED RESOLUTION
MISSING MATERIALIZE REVIEW        -> REJECT
MISSING RECEIPT                   -> REJECT
WRONG REVIEW                      -> REJECT
CHANGED REVIEW AFTER RESOLUTION   -> REJECT
CHANGED EvidenceRecord            -> REJECT
```

The receipt is not a signature, PKI object, authenticated reviewer identity, trusted timestamp, or proof of historical execution. It closes structural binding inside the declared local governance model only.

## Non-transferable resolver-issuance witness

A resolver-issued receipt also carries a private payload-bound issuance witness. The witness commits the exact tuple:

```text
materialization_id
candidate_sha256
review_id
review_sha256
evidence_id
evidence_sha256
resolved_at
```

The issuer capability used to construct that witness is an init-only value and is not retained on the witness. Therefore a legitimate receipt cannot transfer resolver issuance authority to another payload through ordinary dataclass copying.

```text
replace(valid_receipt, changed_payload)
    -> old witness / new payload mismatch -> REJECT

replace(valid_receipt._issuance_witness, changed_payload_sha)
    -> fresh private issuer capability required -> REJECT
```

Binding validation recomputes the witness commitment, so even a low-level post-construction mutation of receipt fields cannot retain terminal eligibility under the old witness.

```text
ONE GENUINE RECEIPT != GENERAL RECEIPT ISSUER CAPABILITY
COPIED WITNESS != AUTHORITY TO REBIND A DIFFERENT PAYLOAD
ISSUANCE WITNESS != SIGNATURE / PKI / TRUSTED PERSISTENCE
```

The witness is process-local structural governance only. It does not authenticate the reviewer, historical execution, source publisher, timestamp, or persistence history.

## Materialized-evidence semantic integrity

The resolver's neutral mapping remains frozen:

```text
TEXT_RESPONSE -> EvidenceKind.OTHER
FILE_ARTIFACT -> EvidenceKind.ARTIFACT
outcome       -> None
observation_started_at -> None
```

and exact neutral summary/context/provenance are checked again by the receipt binding validator.

The receipt hash then binds every canonical PR2 `EvidenceRecord` field, so a post-resolution mutation such as changing kind, summary, context, provenance actor, timestamps, or payload metadata cannot retain terminal eligibility under the old receipt.

```text
SAME EvidenceId != SAME EvidenceRecord
SAME SOURCE REF != SAME EvidenceRecord
SAME CANDIDATE NOTE != SAME EvidenceRecord
```

## Lower-basis EvidenceId uniqueness

Duplicate `EvidenceId` is now rejected in the lowest multi-basis structural gate before same-source/session analysis. Terminal keeps its duplicate-ID check as defense-in-depth.

This preserves the canonical ordering premise used by all reviewed scope hashes:

```text
ONE EvidenceId != TWO OBSERVATION SLOTS
INPUT ORDER != IDENTITY
```

## Family-local completeness-review causality

All six public reviewed completeness gates now enforce, for real PR2 evidence bases:

```text
family_review.reviewed_at
    >=
latest EvidenceRecord.recorded_at in that reviewed family basis
```

Families:

```text
source
mechanism
coordination/control
temporal/intervention/carryover
allocation/randomization
sampling/selection/cohort construction
```

The terminal six-family chronology check remains as aggregate defense-in-depth.

Timestamp consistency still does not authenticate the timestamp or reviewer.

## Terminal semantics

The canonical terminal path now requires:

```text
at least two observation slots
unique EvidenceId values
exact reviewed-resolution binding for every slot
payload-bound non-transferable resolver-issuance witness for every receipt
full current EvidenceRecord equality to its receipt
source identity -> ancestry -> reviewed completeness
mechanism identity -> ancestry -> reviewed completeness
coordination identity -> ancestry -> reviewed completeness
temporal identity -> ancestry -> reviewed completeness
allocation identity -> ancestry -> reviewed completeness
selection identity -> ancestry -> reviewed completeness
```

A PASS remains only a bounded governance precondition.

```text
TERMINAL PASS != STATISTICAL INDEPENDENCE
TERMINAL PASS != INDEPENDENT REPLICATION
TERMINAL PASS != SUCCESSFUL PERFORMANCE
TERMINAL PASS != CAPABILITY SUPPORT
TERMINAL PASS != CLAIM / EVALUATION / STATE AUTHORITY
RECEIPT != SIGNATURE / AUTHENTICATED HISTORY
ISSUANCE WITNESS != SIGNATURE / AUTHENTICATED HISTORY
```

## Release surface

The PR10.1 release documentation is updated to show that Pilot 01 no longer stops at raw capture: it has an explicit human-reviewed, exact-receipt-bound path into neutral PR2 evidence, while claims, evaluations and state remain downstream governed layers with no automatic transition.
