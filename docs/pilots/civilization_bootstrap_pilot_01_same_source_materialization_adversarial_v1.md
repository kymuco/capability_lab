# Civilization Bootstrap Pilot 01 — Same-Source Materialization Dependence and Evidence-Amplification Adversarial Closure

Status: **PR10.1 adversarial closure**

This closure addresses one narrow failure mode in the reviewed Pilot 01 capture-to-evidence bridge: one exact private `PilotCaptureRecord` may be reviewed and materialized more than once under different opaque materialization IDs, review IDs, resolution times, or proposed `EvidenceId` values. Those governance events may produce distinct PR2 `EvidenceRecord` values, but they do not create distinct observations.

## Adversarial finding

PR2 intentionally permits multiple evidence records to coexist and explicitly states that record count does not imply epistemic or statistical independence. `EpistemicRecordSet` therefore rejects duplicate record IDs, but it does not globally reject two different evidence IDs whose provenance ultimately identifies the same external source. That generic behavior is correct: PR2 must preserve derived and alternate representations without pretending to know every domain-specific dependence relation.

For Pilot 01 materialization, however, the exact source relation is known:

```text
EvidenceRecord A ----\
                      +--> pilot_capture:<source_capture_sha256>
EvidenceRecord B ----/
```

If A and B came from the same exact `PilotCaptureRecord`, counting them as two independent evidence slots would be evidence amplification.

```text
TWO MATERIALIZATION RECORDS != TWO OBSERVATIONS
DIFFERENT EVIDENCE IDS != DIFFERENT SOURCE OBSERVATIONS
DIFFERENT REVIEW IDS != INDEPENDENT EVIDENCE
DIFFERENT MATERIALIZATION IDS != INDEPENDENT EVIDENCE
```

## Machine-readable dependence key

PR10.1 now exposes:

```text
pilot_materialized_evidence_dependence_key_v1(evidence)
```

For a structurally valid PR10.1 materialized `EvidenceRecord`, the function returns its exact source key:

```text
pilot_capture:<source_capture_sha256>
```

The extractor fails closed unless the record preserves the frozen PR10.1 materialization shape:

- exactly one `EXTERNAL_RECORD` provenance source;
- source ref `pilot_capture:<64 lowercase hex chars>`;
- `payload_refs` exactly repeat that source ref;
- exactly one `pilot_materialize` provenance step;
- the step uses `capability_lab:reviewed_pilot_capture_to_evidence@1`;
- the provenance note preserves canonical `materialization_id`, `candidate_sha256`, and `review_id` binding fields;
- `EvidenceRecord.outcome` remains `None`.

This is structural recognition, not authentication.

```text
DEPENDENCE KEY != SIGNATURE
DEPENDENCE KEY != HUMAN AUTHORSHIP PROOF
DEPENDENCE KEY != SOURCE VALIDITY
DEPENDENCE KEY != CAPABILITY SUPPORT
```

## Same-source amplification gate

PR10.1 also exposes:

```text
validate_pilot_materialized_evidence_no_same_source_amplification_v1(records)
```

The validator accepts a multi-record Pilot 01 evidence basis only when no exact `pilot_capture:<source_capture_sha256>` key occurs more than once. Repeated same-source materializations fail closed before they can be treated as multiple evidence slots.

```text
SAME SOURCE CAPTURE => SAME DEPENDENCE GROUP
SAME DEPENDENCE GROUP + MULTIPLE EVIDENCE SLOTS => REJECT
```

The validator deliberately does **not** claim that distinct source keys are independent:

```text
DIFFERENT SOURCE HASHES != PROVEN INDEPENDENCE
NO EXACT-SOURCE DUPLICATE != STATISTICAL INDEPENDENCE
NO EXACT-SOURCE DUPLICATE != EPISTEMIC INDEPENDENCE
```

Two different captures can still be correlated through the same prompt, session, participant, tool chain, derivation lineage, or external mechanism. A subsequent PR10.1 adversarial closure now detects one structurally provable subset — shared exact Pilot protocol / subject / session lineage — while broader cross-session and hidden-mechanism correlation remains future evaluation-policy governance.

## PR2 compatibility

Generic PR2 archival coexistence remains unchanged. Two materialized records with distinct `EvidenceId` values can still exist in an `EpistemicRecordSet` even when they point to the same exact Pilot capture source. Their coexistence is not the failure mode; treating their count as independent support is.

Future Pilot 01 claim/evaluation construction that treats a selected collection as multiple evidence units must pass that collection through the PR10.1 same-source amplification gate first.

PR10.1 therefore adds a domain-specific dependence guard without changing the generic PR2 invariant:

```text
MULTIPLE EVIDENCE RECORDS != INDEPENDENT EVIDENCE
```

## Non-goals

This closure does not add:

- a global evidence deduplication registry;
- deletion or mutation of repeated archival records;
- generic PR2 provenance-source uniqueness rules;
- statistical independence estimation;
- general correlated-source clustering across distinct capture hashes;
- claim creation or claim evaluation;
- evidence weighting or support counting;
- state, achievement, progression, or Player Window derivation;
- reviewer authentication or signed provenance;
- persistence or synchronization-wide no-reuse governance.

## New invariant

```text
ONE RAW PILOT CAPTURE MAY HAVE MANY GOVERNANCE EVENTS
ONE RAW PILOT CAPTURE MAY HAVE MANY MATERIALIZATION RECORDS
ONE RAW PILOT CAPTURE MAY NOT OCCUPY MANY INDEPENDENT-EVIDENCE SLOTS
```

This is the bounded adversarial closure required before Pilot 01 begins designing actual capability claims and evaluation policy.
