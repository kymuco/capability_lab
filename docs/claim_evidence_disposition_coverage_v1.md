# PR12.9 — Complete Explicit Candidate Disposition Coverage Gate v1

## Purpose

PR12.8 proves the complete snapshot-bound evidence candidate universe for one exact
`CapabilityClaim`. PR12.9 proves the next property: every candidate has one explicit
`EvidenceAssessment` disposition before downstream dependence governance or admitted-policy
application.

```text
complete PR12.8 candidate portfolio
        ↓
exact one-to-one EvidenceAssessment coverage
        ↓
complete explicit disposition coverage
```

This PR is an anti-omission gate. It does not decide whether any disposition is correct.

## Core invariants

```text
COMPLETE CANDIDATE PORTFOLIO
!= COMPLETE DISPOSITION COVERAGE

ABSENCE OF ASSESSMENT
!= NOT_RELEVANT

OMITTED CANDIDATE
!= IMPLICITLY IRRELEVANT

EXPLICIT NOT_RELEVANT
!= SILENT OMISSION

DISPOSITION COVERAGE
!= CLAIM-WIDE CONCLUSION

DISPOSITION COVERAGE
!= POLICY APPLICATION

DISPOSITION COVERAGE
!= INDEPENDENCE
```

## Candidate source of truth

PR12.9 does not contain a second membership algorithm. It calls the merged PR12.8 public API `build_complete_claim_evidence_candidate_portfolio_v1(records, claim_id, as_of)`.

Candidate membership therefore remains `same subject + recorded_at <= as_of`, with PR12.8's explicit same-subject future exclusions and exact snapshot/claim/time binding.

The canonical PR12.8 receipt JSON is SHA-256 hashed into `candidate_portfolio_sha256`. This binds the PR12.9 artifact to the complete PR12.8 content, including future-exclusion content, without making that digest a separate authority source.

## Disposition vocabulary

PR12.9 reuses the existing generic `EvidenceAssessment` model and the existing `EvidenceBearing` values:

```text
SUPPORTS
CONTRADICTS
INDETERMINATE
NOT_RELEVANT
```

All four bearings count as explicit coverage. PR12.9 does not generate them.

`EvidenceReliability` is preserved as supplied assessment content but never filters candidate membership or coverage.

## Frozen v1 completeness rule

For exact `(records, claim_id, as_of)`:

1. rebuild the exact PR12.8 portfolio;
2. strict-validate an exact tuple of exact `EvidenceAssessment` values;
3. reject duplicate `evidence_id` dispositions;
4. require every disposition id to be a PR12.8 candidate;
5. require every PR12.8 candidate to have a disposition;
6. canonicalize dispositions by `EvidenceId`;
7. allow empty dispositions only for an empty candidate portfolio.

Success is exact set equality:

```text
{assessment.evidence_id}
==
{PR12.8 portfolio.evidence_ids}
```

with one and only one assessment per id.

## Coverage artifact

```text
ClaimEvidenceDispositionCoverageReceipt
    snapshot_sha256
    claim_id
    subject_ref
    concept_ref
    as_of
    candidate_portfolio_sha256
    dispositions
```

The receipt binds the exact epistemic snapshot, claim, subject/concept revision, `as_of`, deterministic PR12.8 portfolio content, and complete explicit disposition tuple.

## Content authority model

Coverage is deterministic:

```text
COVERAGE RECEIPT
!= RUNTIME AUTHORITY

records-derived candidate set
+ exact supplied dispositions
+ one-to-one set equality
= coverage truth
```

No PID binding, object-identity issuance registry, fork capability, reviewer authority, or non-serializable permission token exists here.

A caller-created or JSON-restored exact receipt may pass only after PR12.9 rebuilds PR12.8 from the supplied records and proves exact coverage equality.

## No latest-wins behavior

PR12.9 never scans `EpistemicRecordSet.evaluations` and never chooses a historical assessment by timestamp.

```text
multiple historical assessments
!= latest assessment is authoritative
```

The gate receives one exact supplied disposition tuple. If a caller obtains that tuple from a `ClaimEvaluation`, that evaluation's policy, evaluator, claim-wide coverage, conflict status, conclusion, and timestamp grant no PR12.9 authority.

## Existing ClaimEvaluation interaction

A partial `ClaimEvaluation.evidence_assessments` tuple fails if it omits any PR12.8 candidate. A complete tuple may pass, but only because the exact tuple covers the independently rebuilt candidate universe.

```text
EXISTING ClaimEvaluation
!= COMPLETE COVERAGE PROOF

ClaimEvaluation.conclusion
!= CANDIDATE MEMBERSHIP

ClaimEvaluation.coverage
!= PR12.9 COVERAGE TRUTH
```

## Reliability boundary

Reliability is explicit assessment data only. PR12.9 does not infer, aggregate, threshold, or use reliability to remove candidates from coverage.

## Dependence boundary

```text
TWO EXPLICITLY DISPOSITIONED RECORDS
!= TWO INDEPENDENT OBSERVATIONS

COMPLETE DISPOSITION COVERAGE
!= INDEPENDENCE GOVERNANCE
```

Shared provenance, derived evidence, repeated measurements, source correlation, common episode lineage, and replication semantics remain PR12.10 concerns.

## Strict replay and serialization

Public coverage-critical inputs use exact core value/container types. The validator rejects non-exact ids/assessments, non-tuple disposition containers, duplicate ids, post-construction mutation, noncanonical stored UTC timestamps, stale snapshot/claim/as_of/candidate bindings, unknown or missing JSON fields, duplicate JSON keys, noncanonical disposition ordering, and non-standard JSON constants such as `NaN` and `Infinity`.

Schema-v1 JSON is deterministic and contains no runtime authority.

## Temporal consequences inherited from PR12.8

Evidence recorded before claim creation can still be a candidate if PR12.8 includes it, so it must receive an explicit PR12.9 disposition.

Evidence excluded as future at one boundary is not disposition-required at that boundary. If a later `as_of` makes it a candidate, it becomes mandatory.

Historical backfill recorded by the same `as_of` changes the PR12.8 portfolio and forces coverage rebuild.

## Public API

```text
ClaimEvidenceDispositionCoverageReceipt
build_claim_evidence_disposition_coverage_v1(...)
validate_complete_claim_evidence_disposition_coverage_v1(...)
claim_evidence_disposition_coverage_receipt_to_dict(...)
claim_evidence_disposition_coverage_receipt_from_dict(...)
claim_evidence_disposition_coverage_receipt_to_json(...)
claim_evidence_disposition_coverage_receipt_from_json(...)
```

## Non-goals

```text
PR12.9 != RELEVANCE JUDGMENT GENERATION
PR12.9 != AUTOMATIC EVIDENCE CLASSIFICATION
PR12.9 != EVIDENCE RELIABILITY INFERENCE
PR12.9 != DEPENDENCE / REPETITION GOVERNANCE
PR12.9 != POLICY APPLICATION
PR12.9 != REQUIREMENT MAPPING
PR12.9 != CLAIM-WIDE CONCLUSION
PR12.9 != CONFLICT RESOLUTION
PR12.9 != DOMAIN SUFFICIENCY
PR12.9 != PersonalCapabilityState
PR12.9 != PROGRESSION
PR12.9 != PRESENTATION
PR12.9 != LATEST-WINS ASSESSMENT SELECTION
PR12.9 != RUNTIME ADMISSION AUTHORITY
PR12.9 != CRYPTOGRAPHIC AUTHENTICATION
```

## Intended continuation

```text
PR12.8 complete candidate portfolio                    ✅
PR12.9 complete explicit disposition coverage          ← this PR
PR12.10 evidence dependence / repetition governance
PR12.11 exact admitted-policy requirement application
PR12.12 domain-sufficient multi-evidence evaluation
```
