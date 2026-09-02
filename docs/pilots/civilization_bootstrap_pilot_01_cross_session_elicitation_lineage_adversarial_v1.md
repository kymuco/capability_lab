# Civilization Bootstrap Pilot 01 — Cross-Session Elicitation-Lineage Correlation and False-Replication Adversarial Closure

Status: **PR10.1 adversarial closure**

This closure addresses the next dependence boundary after exact same-source amplification and same-session lineage detection.

Two Pilot 01 observations can now satisfy all earlier structural gates while still sharing one exact elicitation mechanism:

```text
capture A != capture B
source_hash(A) != source_hash(B)
session(A) != session(B)

BUT

protocol_ref(A) == protocol_ref(B)
subject_ref(A)  == subject_ref(B)
probe_id(A)     == probe_id(B)
```

For the frozen Pilot 01 protocol, `protocol_ref + probe_id` identifies one exact participant-facing probe/test form. Repeating that probe for the same subject in another session creates a real new observation, but session separation alone does not make it an independent replication.

```text
NEW SESSION != NEW TEST FORM
NEW CAPTURE HASH != NEW ELICITATION MECHANISM
REPEATED SAME PROBE != INDEPENDENT REPLICATION
```

## Why this boundary is structural

`PilotEvidenceMaterializationCandidate` already preserves:

- exact `protocol_ref`;
- exact `subject_ref`;
- exact `probe_id`;
- exact `session_id`;
- exact source-capture fingerprint;
- exact candidate digest binding later preserved in materialized evidence provenance.

No prompt text, response text, model inference, or probabilistic correlation estimate is needed to detect repeated use of the same frozen probe.

The frozen protocol revision is part of the key. A future changed prompt must use a different protocol revision rather than silently reusing the same `protocol_ref`.

## Elicitation-lineage key

PR10.1 now exposes:

```text
pilot_materialization_candidate_elicitation_lineage_key_v1(candidate)
```

It returns a domain-separated SHA-256 over the canonical tuple:

```text
protocol_ref
subject_ref
probe_id
```

represented as:

```text
pilot_elicitation_lineage:<sha256>
```

Equality has one bounded meaning:

```text
SAME ELICITATION-LINEAGE KEY
=>
SAME SUBJECT + SAME FROZEN PILOT PROTOCOL REVISION + SAME PROBE
```

The key intentionally omits `session_id`, because the failure mode being detected is persistence of the elicitation mechanism **across** sessions.

It also intentionally omits raw response contents.

```text
ELICITATION KEY != RESPONSE HASH
ELICITATION KEY != PERFORMANCE RESULT
ELICITATION KEY != CAPABILITY CLAIM
ELICITATION KEY != STATISTICAL DEPENDENCE ESTIMATE
```

## Layered gates

The existing:

```text
validate_pilot_materialized_evidence_independence_preconditions_v1(...)
```

remains the first-tier structural gate from the previous closure. It rejects:

1. exact same-source amplification;
2. shared exact session lineage.

Its contract always stated:

```text
PASS != INDEPENDENCE
```

That remains true.

This closure adds the stronger cross-session replication gate:

```text
validate_pilot_materialized_evidence_cross_session_replication_preconditions_v1(...)
```

It first runs the existing first-tier gate, then rejects repeated elicitation lineage across otherwise distinct sessions.

```text
EXACT SOURCE REUSE
    -> REJECT

SAME SESSION LINEAGE
    -> REJECT

DISTINCT SESSIONS + SAME ELICITATION LINEAGE
    -> REJECT FOR CROSS-SESSION REPLICATION

PASS
    != INDEPENDENCE
```

A future claim that several Pilot 01 records constitute cross-session replication must use the stronger gate. The lower-level gate is not an alternate path to an independence assertion.

## Why repeated same-probe observations remain valid evidence

This closure does **not** delete, merge, or invalidate repeated observations.

A subject may answer `conceptual_explanation` in January and again in March. Both captures are legitimate historical observations.

The forbidden inference is:

```text
TWO VALID OBSERVATIONS
+
TWO DIFFERENT SESSION IDS
=
TWO INDEPENDENT REPLICATIONS
```

That equation is not licensed.

A later evaluation policy may use repeated same-probe observations for longitudinal change, stability, learning, drift, or retest analysis. It must preserve the common test-form lineage rather than treating the observations as independent support votes.

## Why declared tools are not used as a hard correlation key

Pilot captures also preserve `declared_tools`. This closure deliberately does **not** reject two records merely because both mention a tool such as:

```text
calculator
multimeter
browser
```

Tool equality is too weak to prove a shared causal source. The same generic tool can be used independently.

Likewise, PR10.1 does not infer shared references from free-form text or response content.

Future provenance may add stronger structured source/reference identities. If so, those can support additional correlation families without retroactively pretending that tool-name equality was enough.

## Candidate binding prevents probe relabeling

The existing `PilotMaterializedEvidenceBasisEntry` exact candidate↔evidence binding remains critical.

A caller cannot take one materialized record and relabel its candidate from:

```text
probe_id = conceptual_explanation
```

to:

```text
probe_id = calculation_work
```

to manufacture a different elicitation key.

Changing `probe_id` changes canonical candidate bytes and therefore changes `candidate_sha256`. The materialized evidence provenance still contains the originally reviewed candidate digest, so the basis entry fails closed.

```text
PROBE RELABELING != NEW LINEAGE
FORGED DIFFERENT PROBE != VALID BASIS ENTRY
```

## What a PASS means

Passing the stronger cross-session gate means only:

```text
no repeated exact source capture
AND
no shared exact session lineage
AND
no repeated exact protocol/subject/probe elicitation lineage
```

It does **not** establish independence from:

- shared external references;
- copied source material;
- common upstream datasets;
- common operator intervention;
- shared model/tool outputs;
- temporal carry-over or learning;
- coordinated sessions;
- hidden causal mechanisms;
- common environment;
- common evaluator;
- common prompt ancestry across different protocol revisions.

Those require explicit provenance or later evaluation-policy governance.

## New invariants

```text
DISTINCT SESSION IDS != INDEPENDENT REPLICATION

SAME SUBJECT
+
SAME FROZEN PROTOCOL REVISION
+
SAME PROBE
=>
KNOWN CROSS-SESSION ELICITATION LINEAGE

KNOWN CROSS-SESSION ELICITATION LINEAGE
=>
MAY REMAIN MULTIPLE OBSERVATIONS

KNOWN CROSS-SESSION ELICITATION LINEAGE
!=
MULTIPLE INDEPENDENT SUPPORT VOTES

PASSING CROSS-SESSION STRUCTURAL PRECONDITIONS
!=
PROOF OF INDEPENDENCE
```

This closes the first provable cross-session correlation family without adding a statistical model, hidden weighting, or new authority to PR2 evidence records.
