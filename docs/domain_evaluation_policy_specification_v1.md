# PR12.6 — Generic Domain Evaluation Policy Specification v1

## Purpose

PR12.6 defines the first generic declarative policy shape that can describe what semantic aspects a later governed evaluator must cover before a claim may be considered domain-sufficient.

It does **not** activate a policy, approve a policy, evaluate evidence, create `ClaimEvaluation`, derive `PersonalCapabilityState`, or grant progression/readiness/permission authority.

```text
POLICY SPECIFICATION != ACTIVE POLICY
POLICY SPECIFICATION != CLAIM EVALUATION
POLICY SPECIFICATION != CLAIM TRUTH
POLICY SPECIFICATION != CAPABILITY STATE
```

## Exact applicability

A `DomainEvaluationPolicySpecification` is bound to one exact:

```text
EvaluationPolicyRef
CapabilityConceptRef revision
ClaimScope value
```

Applicability is exact structural equality only. There is no fuzzy scope matching, latest-revision matching, statement regex matching, or caller-controlled widening.

```text
SAME CAPABILITY ID + DIFFERENT REVISION != SAME APPLICABILITY
SIMILAR CLAIM SCOPE != EXACT CLAIM SCOPE
```

## Declarative requirements

Each `DomainEvaluationPolicyRequirement` contains only:

```text
requirement_key
description
required_for_sufficiency
```

Requirement keys are canonical lowercase machine keys, unique within a specification, and stored in deterministic order. At least one requirement must be marked `required_for_sufficiency=True`.

The frozen v1 sufficiency semantics are identified as:

```text
all_required_requirements_explicitly_covered
```

This means only that a **later governed evaluation layer** may establish sufficient semantic coverage when every required requirement key has been explicitly covered by governed evidence assessment. PR12.6 itself performs no evidence mapping and computes no coverage result.

```text
REQUIREMENT != EVIDENCE
REQUIREMENT != SUPPORT
COVERAGE REQUIREMENT != RELIABILITY
```

## No repetition or independence fiction

The v1 specification contains no observation-count, repetition, source-count, statistical-independence, evaluator-majority, confidence-weighting, or recency-weighting field.

```text
TWO EvidenceRecord VALUES != TWO INDEPENDENT OBSERVATIONS
MULTIPLE SOURCES != INDEPENDENCE
REPETITION COUNT != REPLICATION AUTHORITY
```

Generic dependence/repetition governance remains future work.

## Identity and serialization

`domain_evaluation_policy_specification_sha256_v1(...)` computes a domain-separated SHA-256 over the complete canonical declarative content:

- exact `EvaluationPolicyRef`;
- exact `CapabilityConceptRef` revision;
- exact `ClaimScope`;
- every canonical requirement;
- frozen v1 sufficiency semantics.

```text
POLICY REF != POLICY CONTENT HASH
SAME POLICY REF + DIFFERENT CONTENT != SAME SPECIFICATION
HASH != SIGNATURE
HASH != AUTHENTICATION
HASH != ACTIVATION
```

Schema-v1 dict/JSON serialization rejects unknown fields, missing fields, duplicate JSON keys, malformed nested objects, non-canonical requirement ordering, and changed sufficiency semantics.

Public hash/serialization paths strict-reconstruct nested typed content so post-construction runtime corruption fails closed.

## Authority boundary

Production is isolated to:

```text
capability_lab.evaluation_policy.specification
capability_lab.evaluation_policy.serialization
```

The generic implementation imports only shared epistemic/semantic value types and standard-library utilities. It imports no derivation, history, progression, Player Window, pilot, domain implementation, or HDE runtime authority.

The package-root `capability_lab` surface is unchanged.

## Non-goals

```text
PR12.6 != POLICY REGISTRY
PR12.6 != POLICY ACTIVATION
PR12.6 != POLICY APPROVAL
PR12.6 != HUMAN POLICY REVIEW
PR12.6 != ClaimEvaluation
PR12.6 != MULTI-EVIDENCE EVALUATOR
PR12.6 != CONFLICT RESOLUTION
PR12.6 != EVIDENCE INDEPENDENCE GOVERNANCE
PR12.6 != PersonalCapabilityState
PR12.6 != CLOSED-LOOP CAPABILITY UPDATE
```

The intended later chain remains separate:

```text
PR12.6 specification
→ governed policy admission/registry
→ exact admitted policy application
→ directional ClaimEvaluation
→ existing complete-portfolio/state path
```
