# Civilization Bootstrap Pilot 01 — Exact Evaluation-Policy Revision Hardening v1

Status: **PR11.0 adversarial closure**

PR11.0 defines a subject-free Pilot 01 claim/rubric/evaluation-policy specification. The base policy records are deterministic structural values, but `PilotProtocolRef` and `EvaluationPolicyRef` remain nominal governance identifiers rather than content addresses.

The release-level exact-v1 gate therefore requires all of the following to agree:

```text
exact EvaluationPolicyRef
+ frozen domain-separated Pilot 01 protocol SHA-256
+ exact canonical Pilot 01 protocol object
+ exact canonical PilotHumanEvaluationPolicy object
+ frozen domain-separated policy SHA-256
```

Frozen protocol digest:

```text
238e0d12810e4f27536665a56a90f8d835e7a8a95cc9ded46777c8477803f5d5
```

Frozen policy digest:

```text
f1b2be9d059e3375419e3a96803f099a671f0d98531b6d9a061dd36505c4c18a
```

The protocol digest covers the complete canonical `pilot_protocol_to_json(...)` output, including protocol metadata, participant instructions, privacy and physical boundaries, probe metadata, capture-kind allowances, and participant-facing prompts.

The public hardening gate is:

```text
validate_exact_civilization_bootstrap_pilot_01_evaluation_policy_v1(...)
```

and deterministic content helpers include:

```text
pilot_01_protocol_sha256_v1(...)
exact_pilot_01_evaluation_policy_to_dict_v1(...)
exact_pilot_01_evaluation_policy_to_json_v1(...)
exact_pilot_01_evaluation_policy_sha256_v1(...)
```

## Closed drift cases

The exact gate rejects semantic mutation under an unchanged nominal revision, including:

```text
changed canonical protocol builder under same protocol_ref
changed protocol description under same protocol_ref
changed participant prompt under same protocol_ref
changed privacy / physical boundary under same protocol_ref
changed claim proposition under same policy_ref
changed EvidenceBearing guidance under same policy_ref
changed rubric criterion/checkpoint under same policy_ref
```

The canonical builder itself is checked against the frozen protocol digest before it can serve as the comparison baseline. Therefore a future source edit to `build_civilization_bootstrap_pilot_01_protocol_v1()` cannot redefine what `@1` means merely by becoming the new in-process canonical object.

This closes the gap between:

```text
STRUCTURALLY VALID POLICY / PROTOCOL OBJECT
```

and:

```text
EXACT FROZEN PR11.0 + PILOT 01 V1 RELEASE REVISION
```

## Authority boundary

The exact gate is still local structural/content governance only.

```text
PROTOCOL REF != CONTENT HASH
PROTOCOL HASH != SIGNATURE
PROTOCOL HASH != PROTOCOL AUTHORITY
POLICY REF != CONTENT HASH
POLICY HASH != SIGNATURE
POLICY HASH != POLICY AUTHORITY
EXACT POLICY != HUMAN EVALUATION
EXACT POLICY != AUTHENTICATED REVIEWER
EXACT POLICY != CLAIM SUPPORT
EXACT POLICY != PERSONAL CAPABILITY STATE
```

It does not prove that an evaluation happened, authenticate a reviewer, establish trusted historical persistence, or grant downstream state authority. Its purpose is narrower: a later PR11.1 evaluator must not silently execute altered rubric/proposition/protocol semantics while still claiming the frozen `@1` policy revision.
