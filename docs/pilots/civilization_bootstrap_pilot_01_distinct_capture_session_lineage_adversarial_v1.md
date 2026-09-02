# Civilization Bootstrap Pilot 01 — Distinct-Capture Session-Lineage Dependence and False-Independence Adversarial Closure

Status: **PR10.1 adversarial closure**

This closure addresses the next dependence failure mode after exact same-source amplification.

Two different `PilotCaptureRecord` values can have different `source_capture_sha256` values and still share one acquisition lineage. In Pilot 01, the strongest already-reviewed structural relation available without inventing a statistical model is the exact protocol / subject / session tuple carried by `PilotEvidenceMaterializationCandidate`.

## Adversarial finding

The previous closure correctly established:

```text
SAME SOURCE CAPTURE => DEPENDENT
DIFFERENT SOURCE HASHES != PROVEN INDEPENDENCE
```

The unresolved adversarial case was:

```text
capture A != capture B
source_hash(A) != source_hash(B)

BUT

protocol(A) == protocol(B)
subject(A)  == subject(B)
session(A)  == session(B)
```

Those are two real observations, so PR10.1 must not collapse them into one evidence record. But they also share one Pilot acquisition session and therefore must not silently satisfy an independence claim.

```text
DISTINCT OBSERVATION != INDEPENDENT OBSERVATION
DISTINCT CAPTURE HASH != DISTINCT ACQUISITION LINEAGE
SAME SESSION != DUPLICATE SOURCE
SAME SESSION => KNOWN STRUCTURAL CORRELATION
```

## Exact candidate ↔ evidence binding

PR10.1 materialized evidence already preserves the reviewed candidate digest in the canonical provenance note:

```text
materialization_id=<...>;
candidate_sha256=<...>;
review_id=<...>
```

This closure uses that existing binding instead of adding new authority fields to `EvidenceRecord`.

`PilotMaterializedEvidenceBasisEntry` pairs:

```text
PilotEvidenceMaterializationCandidate
+
EvidenceRecord
```

and fails closed unless all of the following agree:

- exact Pilot capture source ref;
- proposed `EvidenceId`;
- subject ref;
- materialization ID embedded in provenance;
- exact canonical `candidate_sha256` embedded in provenance.

This prevents a caller from taking a valid materialized record and attaching a fabricated candidate with a different `session_id` merely to manufacture apparent independence.

```text
SAME SOURCE + FORGED DIFFERENT SESSION != VALID BASIS ENTRY
CANDIDATE RELABELING != INDEPENDENCE
```

This remains structural verification, not authentication. A forged unsigned `EvidenceRecord` and forged candidate can still be jointly fabricated outside the trusted local workflow.

## Session-lineage key

PR10.1 now exposes:

```text
pilot_materialization_candidate_session_lineage_key_v1(candidate)
```

The key is a domain-separated SHA-256 over the canonical tuple:

```text
protocol_ref
subject_ref
session_id
```

and is represented as:

```text
pilot_session_lineage:<sha256>
```

Equality has one bounded meaning:

```text
SAME SESSION-LINEAGE KEY
=>
SAME REVIEWED PILOT PROTOCOL / SUBJECT / SESSION LINEAGE
```

Inequality does **not** prove independence.

```text
DIFFERENT SESSION-LINEAGE KEYS != STATISTICAL INDEPENDENCE
DIFFERENT SESSION-LINEAGE KEYS != EPISTEMIC INDEPENDENCE
```

The key does not embed raw response text. It also does not provide anonymization: a stable digest of known metadata can remain linkable and may be guessable when the input namespace is small.

## Independence precondition gate

PR10.1 now exposes:

```text
validate_pilot_materialized_evidence_independence_preconditions_v1(entries)
```

This validator is deliberately named a **precondition** gate.

It rejects:

1. exact same-source reuse already covered by the previous amplification closure;
2. distinct source captures that share one exact Pilot session lineage.

Therefore:

```text
FAIL => A KNOWN PR10.1 STRUCTURAL DEPENDENCE EXISTS
PASS != INDEPENDENCE
```

A pass means only:

```text
no repeated exact PilotCaptureRecord source
AND
no shared exact Pilot protocol/subject/session lineage
```

It does not inspect or prove independence across:

- repeated prompts in separate sessions;
- copied or transformed source material;
- shared external references;
- same tool-generated content;
- same operator intervention;
- common upstream datasets;
- temporal carry-over;
- model or evaluator reuse;
- coordinated or causally linked sessions;
- hidden shared mechanisms.

Those require later explicit evaluation-policy or provenance-lineage governance.

## Why same-session observations are not rejected from evidence basis

This closure does **not** prohibit multiple captures from one session from being evaluated together.

For example:

```text
conceptual_explanation
calculation_work
diagnosis_reasoning
```

are distinct observations and may all be relevant to a later claim.

The forbidden move is narrower:

```text
THREE SAME-SESSION OBSERVATIONS
!=
THREE INDEPENDENT OBSERVATIONS
```

A future evaluation policy may still use all three, but it must preserve their dependence rather than converting record count into independent support count.

## PR2 compatibility

Generic PR2 remains unchanged.

`EpistemicRecordSet` may preserve multiple evidence records with shared acquisition context. PR2 already states:

```text
MULTIPLE EVIDENCE RECORDS != INDEPENDENT EVIDENCE
```

PR10.1 adds Pilot-specific structure needed to make one known correlation family machine-detectable before future claim/evaluation construction.

No generic PR2 deduplication or correlation rule is introduced.

## Non-goals

This closure does not add:

- claim creation;
- claim evaluation;
- evidence weighting;
- majority vote;
- an independence score or probability;
- statistical dependence estimation;
- cross-session causal inference;
- global correlation clustering;
- a signed candidate/review archive;
- authenticated subject/session identity;
- state, achievements, progression, or Player Window;
- public or shared storage.

## New invariants

```text
SAME RAW CAPTURE
=> EXACT-SOURCE DEPENDENCE

DISTINCT RAW CAPTURES + SAME PILOT SESSION
=> KNOWN SESSION-LINEAGE CORRELATION

DISTINCT PILOT SESSIONS
!= PROVEN INDEPENDENCE

PASSING STRUCTURAL PRECONDITIONS
!= AUTHORITY TO CLAIM INDEPENDENCE
```

This closes the first distinct-capture correlated-source hole without inventing unsupported independence semantics.
