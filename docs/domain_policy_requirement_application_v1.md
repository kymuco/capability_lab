# PR12.11 — Governed Admitted-Policy Requirement Mapping and Coverage Application v1

## Purpose

PR12.11 applies one exact already-admitted PR12.7 domain policy to one exact claim and its complete PR12.9/PR12.10 evidence basis without turning semantic requirement coverage into claim truth or a directional `ClaimEvaluation`.

The critical architectural fact is that the mapping

```text
EvidenceId X semantically covers requirement Y
```

is not reconstructible from the existing record set, disposition receipt, lineage receipt, or policy specification. It is a human semantic judgment.

Therefore PR12.11 has an explicit governed boundary:

```text
exact admitted policy authority
+ exact PR12.9 disposition coverage
+ exact PR12.10 lineage basis
        ↓
non-authoritative complete mapping proposal
        ↓
explicit HUMAN terminal review
        ↓
runtime-only review admission authority
        ↓
deterministic application receipt
```

```text
RAW MAPPING PROPOSAL != AUTHORITY
MAPPING JSON != AUTHORITY
RAW HUMAN APPROVE != AUTHORITY
SERIALIZED REVIEW LEDGER != AUTHORITY
```

## Exact upstream basis

A proposal is built only from exact:

- `EpistemicRecordSet`;
- `CapabilityClaimId`;
- `as_of`;
- fully replay-validated PR12.9 `ClaimEvidenceDispositionCoverageReceipt`;
- fully replay-validated PR12.10 `ClaimEvidenceLineageDependenceReceipt`;
- PR12.7 registry with current runtime admission authority;
- `EvaluationPolicyRef`;
- exact PR12.6 specification SHA-256;
- one explicit requirement application entry for every admitted policy requirement.

The selected policy is resolved only through the hardened PR12.7 registry authority path.

```text
RAW POLICY SPEC != ADMITTED POLICY
SERIALIZED REGISTRY != CURRENT RUNTIME REGISTRY AUTHORITY
```

## Exact policy applicability

The admitted policy must match the target claim by exact:

```text
policy.concept_ref == claim.concept_ref
policy.claim_scope == claim.scope
```

There is no latest-revision matching, capability-id-only matching, tag subset matching, statement heuristic, fuzzy similarity, or scope widening.

## Mapping vocabulary

Each admitted policy requirement receives exactly one:

```text
DomainPolicyRequirementApplicationEntry
    requirement_key
    disposition
    evidence_ids
    rationale
```

The only v1 dispositions are:

```text
COVERED
NOT_COVERED
UNRESOLVED
```

### COVERED

A human proposal says one or more exact PR12.9 candidate evidence values address the exact semantic requirement.

`COVERED` requires at least one mapped `EvidenceId`.

### NOT_COVERED

A human proposal explicitly says no evidence mapping is admitted for that requirement on this exact basis.

`NOT_COVERED` requires `evidence_ids == ()`.

### UNRESOLVED

The human proposal does not assert either covered or not-covered for the exact requirement.

`UNRESOLVED` also requires `evidence_ids == ()`.

No missing-entry shorthand exists. Optional requirements also require explicit entries.

```text
MISSING ENTRY != NOT_COVERED
MISSING ENTRY != UNRESOLVED
MISSING ENTRY != OPTIONAL
```

## Coverage is not bearing

PR12.11 preserves the distinction between semantic coverage and directional evidence bearing.

Mapped evidence may have PR12.9 bearing:

```text
SUPPORTS
CONTRADICTS
INDETERMINATE
```

and still cover a semantic requirement.

```text
COVERED != SUPPORTS
CONTRADICTS CAN COVER A REQUIREMENT
INDETERMINATE CAN COVER A REQUIREMENT
```

`NOT_RELEVANT` evidence cannot satisfy a requirement.

PR12.11 never rewrites PR12.9 bearing or reliability.

## Reliability and lineage remain orthogonal

PR12.6 contains no reliability threshold, cardinality rule, majority rule, source weighting, or positive independence requirement. PR12.11 therefore invents none.

```text
LOW != AUTOMATIC NON-COVERAGE
HIGH != EXTRA VOTE
UNASSESSED != AUTOMATIC FAILURE

MULTIPLE MAPPED EVIDENCE != STRONGER COVERAGE
MULTIPLE MAPPED EVIDENCE != INDEPENDENT REPLICATION
PROVEN_SHARED_LINEAGE != AUTOMATIC REQUIREMENT FAILURE
UNRESOLVED LINEAGE != PROVEN INDEPENDENCE
```

PR12.10 remains mandatory so later code cannot silently reintroduce record-count fiction.

## Mapping proposal

`ClaimDomainPolicyRequirementMappingProposal` is immutable serializable audit data binding:

```text
snapshot_sha256
claim_id
subject_ref
concept_ref
claim_scope
as_of
policy_ref
specification_sha256
policy_review_id
policy_review_sha256
policy_admitted_at
disposition_coverage_sha256
lineage_dependence_sha256
requirement_applications
```

`claim_domain_policy_requirement_mapping_proposal_sha256_v1(...)` computes a domain-separated digest over the complete canonical proposal.

The digest is integrity/audit data only.

## HUMAN review

`ClaimPolicyRequirementMappingReview` binds one exact proposal digest to:

```text
review_id
claim_id
policy_ref
mapping_proposal_sha256
HUMAN reviewer ref
APPROVE | REJECT
reviewed_at
rationale
```

Rules:

- reviewer kind is exactly `HUMAN`;
- review binds the exact proposal digest;
- `reviewed_at >= proposal.as_of`;
- `reviewed_at >= policy_admitted_at`;
- one valid ledger lineage may contain at most one terminal review for one exact proposal identity;
- changed proposal content requires a different digest and review;
- conflicting terminal review fails closed;
- `REJECT` never permits application.

## Runtime review admission authority

`ClaimPolicyRequirementMappingReviewAdmission` is runtime-only and cannot be publicly constructed or serialized.

`admit_claim_policy_requirement_mapping_review_v1(...)` is the explicit transition that issues authority bound to:

- exact claim;
- exact policy ref;
- exact proposal digest;
- exact review id/digest;
- predecessor review-ledger digest;
- exact one-review transition successor digest;
- exact current review-ledger digest;
- current process/PID.

Exact replay is ledger-idempotent but issues fresh runtime authority.

A stale admission fails after review-ledger growth.

POSIX fork inheritance fails closed. The child may explicitly replay admission to obtain child-local authority without duplicating the review. Because PR12.7 policy-registry authority is also process-local, a child performing final application must explicitly replay both the policy-admission authority and the PR12.11 mapping-review authority.

No cryptographic human authentication is claimed.

## Deterministic application

After exact proposal replay and exact approved review-admission validation, application is deterministic.

`ClaimDomainPolicyRequirementApplicationReceipt` binds the complete exact basis plus:

```text
mapping_proposal_sha256
mapping_review_id
mapping_review_sha256
requirement_applications
required_requirement_coverage_complete
```

The only aggregate boolean in PR12.11 is:

```text
required_requirement_coverage_complete = true
iff
EVERY admitted requirement with required_for_sufficiency == true
has disposition == COVERED
```

Optional requirement status does not affect this boolean.

```text
REQUIRED COVERAGE COMPLETE != CLAIM SUPPORTED
REQUIRED COVERAGE COMPLETE != CLAIM TRUE
REQUIRED COVERAGE COMPLETE != EvaluationConclusion
```

PR12.12 remains responsible for conservative claim-wide directional evaluation.

## Strict replay and serialization

Proposal, review, review ledger, and application receipt have strict schema-v1 dict/JSON serialization. Validation fails closed on unknown/missing fields, duplicate JSON keys, noncanonical encoding, malformed refs/ids/timestamps/enums, duplicate requirement/evidence ids, noncanonical ordering, stale upstream hashes, changed claims/policies, and post-construction semantic corruption.

A JSON-restored final application receipt may validate only after the complete current upstream, policy-authority, proposal, and HUMAN review-admission replay succeeds.

## Public API

```text
DomainPolicyRequirementApplicationDisposition
DomainPolicyRequirementApplicationEntry
ClaimDomainPolicyRequirementMappingProposal
ClaimPolicyRequirementMappingReviewId
ClaimPolicyRequirementMappingReviewerKind
ClaimPolicyRequirementMappingReviewerRef
ClaimPolicyRequirementMappingReviewVerdict
ClaimPolicyRequirementMappingReview
ClaimPolicyRequirementMappingReviewLedger
ClaimPolicyRequirementMappingReviewAdmission
ClaimDomainPolicyRequirementApplicationReceipt

build_claim_domain_policy_requirement_mapping_proposal_v1(...)
validate_claim_domain_policy_requirement_mapping_proposal_v1(...)
review_claim_domain_policy_requirement_mapping_proposal_v1(...)
admit_claim_policy_requirement_mapping_review_v1(...)
validate_claim_policy_requirement_mapping_review_admission_v1(...)
require_approved_claim_policy_requirement_mapping_review_v1(...)
apply_admitted_domain_policy_requirements_v1(...)
validate_claim_domain_policy_requirement_application_v1(...)
```

Plus domain-separated digest and strict serialization helpers for ordinary serializable artifacts.

## Non-goals

```text
PR12.11 != AUTOMATIC REQUIREMENT CLASSIFIER
PR12.11 != EvidenceBearing GENERATION
PR12.11 != EvidenceReliability GENERATION
PR12.11 != EVIDENCE DELETION / DEDUPLICATION
PR12.11 != POSITIVE INDEPENDENCE ADMISSION
PR12.11 != REPLICATION COUNT
PR12.11 != MAJORITY VOTE
PR12.11 != EVIDENCE WEIGHTING
PR12.11 != CONFLICT RESOLUTION
PR12.11 != CLAIM-WIDE EvaluationConclusion
PR12.11 != CLAIM TRUTH
PR12.11 != PersonalCapabilityState
PR12.11 != PROGRESSION
PR12.11 != PRESENTATION
PR12.11 != CRYPTOGRAPHIC HUMAN AUTHENTICATION
```

## Intended continuation

```text
PR12.8  complete candidate portfolio                    ✅
PR12.9  complete explicit disposition coverage          ✅
PR12.10 complete deterministic lineage / non-inference  ✅
PR12.11 governed admitted-policy requirement mapping    ← this PR
PR12.12 conservative domain-sufficient evaluation
then     end-to-end capability inference audit/demo
```
