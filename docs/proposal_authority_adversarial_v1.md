# PR6 Adversarial Proposal-Authority Review v1

Status: **adversarial governance review for PR6**

This review attacks ways in which a non-authoritative proposal or review could accidentally acquire semantic, epistemic, privacy, namespace, or temporal authority.

The review assumes the PR6 core contract:

```text
PROPOSAL != ACCEPTED OBJECT
MODEL OUTPUT != AUTHORITY
RECOMMEND_ACCEPT != MATERIALIZATION
```

## 1. Namespace / identity reservation attack

### Attack

A `CREATE_CONCEPT`, split output, or merge output can carry a suggested `CapabilityId`. If validation only checks that the full id is not already present, a proposal could use an entirely absent namespace and thereby behave like an implicit namespace-creation request even though PR6 has no `CREATE_NAMESPACE` proposal kind.

That would collapse two governance operations:

```text
suggest concept id in unknown namespace
    -> implicit namespace creation
```

### Repair

Catalog validation now requires every new suggested concept id to belong to a namespace already present in the supplied `CapabilityCatalog`.

This applies to:

- `CREATE_CONCEPT` candidate ids;
- `SPLIT_CONCEPT` output ids;
- `MERGE_CONCEPTS` output ids.

```text
CONCEPT PROPOSAL != NAMESPACE PROPOSAL
UNKNOWN NAMESPACE != IMPLICITLY CREATED NAMESPACE
SUGGESTED ID != RESERVED ID
```

Multiple independent proposals may still suggest the same currently unoccupied id. PR6 does not reserve ids, count proposals as votes, or choose a winner.

```text
SAME SUGGESTED ID IN N PROPOSALS != RESERVED ID
PROPOSAL COUNT != NAMESPACE AUTHORITY
```

## 2. Private-basis laundering through relation provenance

### Attack

`RelationCreateCandidate` intentionally preserves PR1 `provenance_refs`. Those refs are generic strings because accepted relation provenance can point to external/shared provenance artifacts.

Without an additional PR6 boundary, a person-scoped internal `EvidenceId`, `CapabilityClaimId`, or `ClaimEvaluationId` could be copied into `RelationCreateCandidate.provenance_refs` rather than represented through typed `ProposalBasisRef`. That would bypass the one-subject/private-basis checks applied to proposal basis records.

### Repair

When `CapabilityProposalSet.validate_against_epistemics(records)` is supplied, relation candidate `provenance_refs` are checked against every internal evidence, claim, and evaluation id in that snapshot. A collision fails closed.

Internal person-scoped epistemic records belong in typed proposal basis:

```text
INTERNAL PR2 RECORD REF
    -> ProposalBasisRef
    -> subject/privacy validation
```

not:

```text
INTERNAL PR2 RECORD REF
    -> RelationCreateCandidate.provenance_refs
```

Therefore:

```text
RELATION PROVENANCE REF != PRIVATE-BASIS ESCAPE HATCH
PRIVATE INTERNAL BASIS != SHARED RELATION PROVENANCE
```

This check is intentionally snapshot-relative. It cannot prove the absence of an internal record outside the supplied `EpistemicRecordSet`.

```text
VALIDATED AGAINST SNAPSHOT != GLOBAL PROVENANCE AUTHENTICATION
```

## 3. Same-timestamp supersession / review attack

### Attack

A replacement proposal or review may have exactly the same canonical timestamp as the proposal it references. A naive consumer could interpret equal times as ambiguous ordering, or use timestamp recency as authority.

### Review conclusion

Equal timestamps are not a blocker in PR6. Explicit record references establish the causal relation:

```text
child.supersedes_proposal_id -> parent
review.proposal_id           -> reviewed proposal
```

The timestamp boundary only forbids contradiction: a parent may not be timestamped after its replacement and a review may not be timestamped before the proposal it references.

This preserves compatibility with coarse/distributed clocks while avoiding a hidden `latest timestamp wins` rule.

```text
TIMESTAMP EQUALITY != EVENT IDENTITY
TIMESTAMP RECENCY != AUTHORITY
SUPERSESSION LINK != LATEST-TIMESTAMP HEURISTIC
```

## 4. Stale review / supersession race attack

### Attack

A proposal can receive `RECOMMEND_ACCEPT`, then be superseded. A dangerous implementation could transfer the old review to the successor or expose a derived `accepted/current/effective` status.

### Result

PR6 preserves review identity exactly. A review names one exact `CapabilityProposalId`; supersession creates a different proposal id.

```text
REVIEW OF P1 != REVIEW OF P2
P2 SUPERSEDES P1 != P1 REVIEW TRANSFERS TO P2
```

No `latest_review`, `effective_verdict`, `current_status`, or `accepted_proposal` API is provided.

## 5. Review-count / reviewer-kind authority attack

Multiple reviews remain independent facts. PR6 does not:

- count recommendations into a decision;
- prefer the latest review;
- prefer human over model;
- prefer model over rule;
- infer authority from review policy identity.

```text
MULTIPLE REVIEWS != VOTE
LATEST REVIEW != AUTHORITY
HUMAN REVIEW != AUTOMATIC AUTHORITY
MODEL REVIEW != AUTOMATIC AUTHORITY
REVIEW COUNT != ACCEPTANCE
```

## 6. Candidate-to-core-record type escape attack

Candidate payloads remain dedicated proposal-layer types. Constructors may reuse PR1 value validation internally, but they do not store or return accepted `CapabilityConcept`, `CapabilityRelation`, or `CapabilityClaim` records.

Validation may instantiate a temporary core value to check frozen semantic rules; this is validation, not materialization.

```text
VALIDATED LIKE CORE RECORD != CORE RECORD
CORE CONSTRUCTOR USED INTERNALLY != ACCEPTED OBJECT CREATED
```

PR6 exposes no `apply_proposal`, `materialize_proposal`, `proposal_to_claim`, or equivalent conversion shortcut.

## 7. Copy-without-lineage limitation

PR6 can reject explicit cross-scope supersession and typed private-basis misuse. It cannot determine from isolated immutable records that an operator copied candidate text from a private proposal into a newly constructed shared proposal while intentionally omitting provenance and lineage.

That is not silently treated as safe publication. It is an explicit limit of record-local validation:

```text
NO RECORDED LINEAGE != PROOF OF INDEPENDENT ORIGIN
SERIALIZABLE SHARED PROPOSAL != PROVEN SHAREABILITY
```

Future persistence/publication governance must preserve derivation provenance and authorization when moving information across privacy boundaries. PR6 does not implement sanitization or Commons promotion.

## 8. Exact-ref stale race

All proposal operations against existing semantics preserve exact `CapabilityConceptRef` values. Validation against a later catalog fails if the exact revision is no longer the one represented by that snapshot.

For new ids, validation fails if the id became occupied before validation/materialization governance.

PR6 never silently converts:

```text
concept@1 proposal -> concept@latest proposal
unoccupied suggested id -> reserved id
```

## 9. Result of adversarial pass

Blocking findings repaired:

1. unknown namespace could be smuggled through create/split/merge concept candidates;
2. private internal PR2 record ids could be laundered through relation candidate `provenance_refs` instead of typed proposal basis.

Reviewed and intentionally retained:

- equal timestamps when explicit causal links are present;
- multiple independent proposals suggesting the same unoccupied id;
- conflicting reviews;
- reviews of superseded historical proposals;
- model and human actors using the same non-authoritative proposal/review record shapes.

The remaining boundary is:

```text
PR6 RECORD VALIDITY != GOVERNANCE ACCEPTANCE
PR6 SNAPSHOT VALIDATION != GLOBAL AUTHENTICATION
PR6 REVIEW HISTORY != MATERIALIZATION POLICY
```
