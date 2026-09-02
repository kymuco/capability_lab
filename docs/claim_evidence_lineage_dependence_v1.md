# PR12.10 — Complete Evidence Lineage Profiles, Proven Shared-Origin Dependence and Replication Non-Inference Gate v1

## Purpose

PR12.8 proves the complete snapshot-bound candidate universe. PR12.9 proves exactly one explicit disposition for every candidate. PR12.10 freezes the next safety property: complete deterministic provenance-lineage profiles that can prove known shared-origin dependence without inventing positive independence.

```text
exact records
+ exact claim_id
+ exact as_of
+ exact validated PR12.9 disposition coverage
        ↓
one lineage profile for every candidate
        ↓
PROVEN_SHARED_LINEAGE | UNRESOLVED
```

PR12.10 is an anti-double-counting / non-inference boundary. It does not delete evidence, change dispositions, apply policy, or emit a claim-wide conclusion.

## Core invariants

```text
TWO EvidenceRecord VALUES != TWO INDEPENDENT OBSERVATIONS
TWO DISTINCT EvidenceIds != TWO INDEPENDENT OBSERVATIONS
MULTIPLE SOURCES != INDEPENDENCE
DIFFERENT SOURCE REFS != INDEPENDENCE
NON-OVERLAPPING TIME != INDEPENDENCE
REPEATED_PERFORMANCE != MULTIPLE INDEPENDENT REPLICATIONS
NO PROVEN SHARED LINEAGE != PROVEN INDEPENDENCE

PROVEN SHARED LINEAGE
-> MUST NOT BE INTERPRETED AS INDEPENDENT REPLICATION

DEPENDENCE != NOT_RELEVANT
DEPENDENCE != EVIDENCE DELETION
DEPENDENCE != EvidenceBearing
DEPENDENCE != EvidenceReliability
DEPENDENCE != POLICY COVERAGE
DEPENDENCE != CLAIM-WIDE CONCLUSION
```

## Exact upstream basis

PR12.10 accepts one exact `EpistemicRecordSet`, `CapabilityClaimId`, `as_of`, and `ClaimEvidenceDispositionCoverageReceipt`.

The supplied PR12.9 coverage is first revalidated through `validate_complete_claim_evidence_disposition_coverage_v1`. That replay already re-establishes PR12.8 complete candidate membership. PR12.10 does not contain a second candidate-membership algorithm and does not infer completeness from a caller-created lineage receipt.

## Why v1 does not expose INDEPENDENT

The current generic provenance model can reconstruct some shared-lineage facts:

- direct/transitive `EVIDENCE_RECORD` derivation;
- two records descending from one internal root evidence;
- a shared exact `ARTIFACT` origin;
- a shared exact `EXTERNAL_RECORD` origin;
- inherited concrete origins through derived evidence.

But absence of those facts does not prove statistical or observational independence.

Therefore the v1 pair relation is intentionally only:

```text
EvidenceLineageRelation.PROVEN_SHARED_LINEAGE
EvidenceLineageRelation.UNRESOLVED
```

There is no positive `INDEPENDENT` value, flag, count, or authority field.

## EvidenceLineageProfile

Each exact candidate receives:

```text
EvidenceLineageProfile
    evidence_id
    direct_parent_evidence_ids
    root_evidence_ids
    origin_sources
```

### Direct parents

`direct_parent_evidence_ids` contains every exact provenance source with `ProvenanceSourceKind.EVIDENCE_RECORD`.

`EpistemicRecordSet` already requires those parents to exist, share the subject, not occur after the child, and participate in an acyclic derivation graph.

### Internal roots

Frozen recursion:

```text
no EVIDENCE_RECORD parents
-> roots = (self,)

has parents
-> roots = canonical union(parent.roots)
```

A combined child must not cause reverse connected-component collapse.

```text
A ─┐
   ├→ C
B ─┘
```

Required:

```text
A ↔ C = PROVEN_SHARED_LINEAGE
B ↔ C = PROVEN_SHARED_LINEAGE
A ↔ B = UNRESOLVED
```

### Concrete origins

`origin_sources` is the canonical inherited union of only:

```text
ARTIFACT
EXTERNAL_RECORD
```

For each evidence:

```text
direct ARTIFACT / EXTERNAL_RECORD sources
UNION
all parent origin_sources
```

The following are deliberately not treated as concrete shared-origin tokens:

```text
ACTOR
SYSTEM
payload_refs
EvidenceKind
outcome
context tags
observation timing
recorded_at spacing
```

## Pair relation

For two distinct exact candidate profiles `left` and `right`:

```text
left.roots ∩ right.roots != ∅
OR
left.origins ∩ right.origins != ∅
        ↓
PROVEN_SHARED_LINEAGE
```

Otherwise the result is `UNRESOLVED`. `UNRESOLVED` must never be reinterpreted as `INDEPENDENT`.

The public pair resolver rebuilds the expected PR12.10 lineage from exact records and exact revalidated PR12.9 coverage. An optional supplied lineage receipt is accepted only if it equals that rebuild in full.

## Complete profile coverage

PR12.10 emits exactly one profile for every PR12.9 disposition / PR12.8 candidate, including explicit `NOT_RELEVANT` evidence.

```text
{profile.evidence_id}
==
{PR12.9 disposition.evidence_id}
==
{PR12.8 candidate evidence_ids}
```

Known dependence never removes, merges, suppresses, or rewrites a disposition.

## Repetition boundary

`EvidenceKind.REPEATED_PERFORMANCE` remains one evidence record.

PR12.10 does not infer hidden observation count, independent episode count, replication count, majority, or statistical weight. Multiple `REPEATED_PERFORMANCE` records likewise do not become independent replications merely because there are multiple ids or distinct time windows.

## Receipt

```text
ClaimEvidenceLineageDependenceReceipt
    snapshot_sha256
    claim_id
    subject_ref
    concept_ref
    as_of
    disposition_coverage_sha256
    lineage_profiles
```

`disposition_coverage_sha256` is SHA-256 of canonical PR12.9 coverage JSON. It binds the exact disposition basis but grants no authority.

## Content-authority model

Every v1 fact is reconstructible:

```text
LINEAGE RECEIPT != RUNTIME AUTHORITY
LINEAGE RECEIPT != INDEPENDENCE AUTHORITY

exact records
+ exact validated PR12.9 coverage
+ deterministic provenance traversal
= PR12.10 lineage truth
```

There is no PID binding, runtime issuance table, object-identity capability, fork authority, hidden token, or reviewer admission in PR12.10. Caller-created and JSON-restored exact receipts may pass only after complete deterministic replay.

## Strict serialization

Schema-v1 dict/JSON serialization is deterministic. Validation rejects unknown/missing fields, duplicate JSON keys, non-standard JSON constants, malformed evidence ids or provenance sources, non-exact containers/scalars, duplicate ids/origins, noncanonical profile/root/origin ordering, stale snapshot/claim/as_of/coverage bindings, caller-created profile omission/addition, and post-construction semantic corruption.

## Interaction with PR12.11

PR12.6 v1 intentionally has no cardinality or positive-independence requirements. PR12.10 must not extend the admitted policy language by itself.

PR12.11 may require exact PR12.10 replay as a safety prerequisite, while requirement application remains explicit semantic coverage mapping rather than record/source counts, inferred independent observations, majority vote, or weighted evidence score.

## Interaction with PR12.12

PR12.12 must not convert record count into directional strength. Known shared-lineage evidence remains visible with its exact PR12.9 disposition. PR12.10 only prevents later code from pretending that multiple records necessarily represent independent replication.

## Future positive independence

If a future policy revision genuinely requires `at least two independently observed episodes`, current provenance does not establish that by non-overlap alone.

```text
positive independence assertion
cannot be reconstructed from current data
-> requires a separate governed authority transition
```

That future reviewed/admitted episode or independence relation is explicitly outside PR12.10 v1.

## Public API

```text
EvidenceLineageProfile
EvidenceLineageRelation
ClaimEvidenceLineageDependenceReceipt
build_claim_evidence_lineage_dependence_v1(...)
validate_claim_evidence_lineage_dependence_v1(...)
resolve_claim_evidence_pair_lineage_relation_v1(...)
evidence_lineage_profile_to_dict(...)
evidence_lineage_profile_from_dict(...)
claim_evidence_lineage_dependence_receipt_to_dict(...)
claim_evidence_lineage_dependence_receipt_from_dict(...)
claim_evidence_lineage_dependence_receipt_to_json(...)
claim_evidence_lineage_dependence_receipt_from_json(...)
```

## Non-goals

```text
PR12.10 != STATISTICAL INDEPENDENCE PROOF
PR12.10 != POSITIVE INDEPENDENCE ADMISSION
PR12.10 != EPISODE LABEL GENERATION
PR12.10 != EVIDENCE DELETION / DEDUPLICATION
PR12.10 != EVIDENCE RELEVANCE
PR12.10 != EvidenceBearing
PR12.10 != EvidenceReliability
PR12.10 != POLICY APPLICATION
PR12.10 != REQUIREMENT MAPPING
PR12.10 != CARDINALITY / MAJORITY / WEIGHTING
PR12.10 != CLAIM-WIDE CONCLUSION
PR12.10 != CONFLICT RESOLUTION
PR12.10 != DOMAIN SUFFICIENCY
PR12.10 != PersonalCapabilityState
PR12.10 != PROGRESSION
PR12.10 != PRESENTATION
PR12.10 != RUNTIME ADMISSION AUTHORITY
PR12.10 != CRYPTOGRAPHIC AUTHENTICATION
```

## Intended continuation

```text
PR12.8  complete candidate portfolio                    ✅
PR12.9  complete explicit disposition coverage          ✅
PR12.10 complete deterministic lineage / non-inference  ← this PR
PR12.11 exact admitted-policy requirement application
PR12.12 conservative domain-sufficient evaluation
then     end-to-end capability inference audit
```
