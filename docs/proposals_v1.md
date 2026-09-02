# Capability Proposal and Model Non-Authority Boundary v1

Status: **PR6 normative proposal-layer contract**

PR6 introduces an immutable candidate/review layer between interpretation and accepted Capability Lab records. It allows humans, rules, models, hybrid systems, and external systems to make inspectable suggestions without granting those mechanisms authority to mutate shared semantics, create accepted person-scoped claims, or alter personal capability state.

The central boundary is:

```text
PROPOSAL != ACCEPTED OBJECT
MODEL OUTPUT != AUTHORITY
```

## 1. Position in the architecture

```text
CapabilityCatalog / EpistemicRecordSet
               |
               | inspected by an authorized workflow
               v
       proposal generator
               |
               v
      CapabilityProposal
               |
               v
        ProposalReview
               |
               X  no implicit application/materialization
               |
               v
CapabilityConcept / CapabilityRelation /
CapabilityClaim / ClaimEvaluation /
PersonalCapabilityState
```

PR6 records candidate artifacts and review facts. It does not implement a catalog mutation API, a claim-acceptance workflow, a state transition engine, or a Commons publication path.

```text
REVIEW != MATERIALIZATION
RECOMMEND_ACCEPT != ACCEPTED OBJECT
```

## 2. Candidate specs are not accepted core records

Proposal payloads use dedicated candidate types rather than embedding accepted semantic or epistemic records.

```text
ConceptCandidateSpec != CapabilityConcept
RelationCreateCandidate != CapabilityRelation
ClaimCreateCandidate != CapabilityClaim
```

A candidate may be structurally valid and still remain only a suggestion.

For a new concept, `suggested_capability_id` is a proposed namespace identifier. It does not reserve that id, create a namespace entry, or allocate semantic revision `@1`.

```text
SUGGESTED ID != RESERVED ID
VALID CANDIDATE != ACCEPTED RECORD
```

## 3. Proposal kinds v1

PR6 supports exactly six proposal kinds:

```text
CREATE_CONCEPT
REVISE_CONCEPT
SPLIT_CONCEPT
MERGE_CONCEPTS
CREATE_RELATION
CREATE_CLAIM
```

PR6 does not yet define achievement proposals, progression/frontier proposals, recommendation proposals, state proposals, permission proposals, or generic workflow commands.

### 3.1 Create concept

`ConceptCreateCandidate` contains one `ConceptCandidateSpec` with a suggested `CapabilityId`, name, definition, and aliases. It has no semantic revision and no accepted lifecycle record.

### 3.2 Revise concept

`ConceptRevisionCandidate` names the exact existing `CapabilityConceptRef` whose semantics were inspected and supplies candidate replacement semantic fields.

```text
TARGET concept@1 + proposal != RESERVED concept@2
```

The next accepted revision, if any, belongs to a future governed materialization path.

### 3.3 Split and merge

Split and merge proposals preserve the PR1 identity boundary. Split outputs and a merge output use new suggested ids rather than silently reusing an input lineage.

```text
SPLIT != REVISION
MERGE != REVISION
```

### 3.4 Create relation

`RelationCreateCandidate` records exact source and target `CapabilityConceptRef` values to preserve which semantic revisions the proposer inspected. Its relation kind/scope/strength/provenance fields obey PR1 relation validation.

An eventual accepted PR1 `CapabilityRelation` is lineage-level (`CapabilityId` endpoints), but proposal audit history remains exact-revision aware.

### 3.5 Create claim

`ClaimCreateCandidate` contains an exact concept ref, candidate statement, and claim scope. The proposal envelope supplies the subject.

```text
CLAIM PROPOSAL != CAPABILITY CLAIM
CAPABILITY CLAIM != SUPPORTED CLAIM
```

Even a positively reviewed claim candidate does not create a PR2 `CapabilityClaim`, `ClaimEvaluation`, or PR3 state.

## 4. Generator identity and generation policy

`ProposalGeneratorRef` records the mechanism class and opaque mechanism ref:

```text
HUMAN
RULE
MODEL
HYBRID
EXTERNAL_SYSTEM
```

`ProposalGenerationPolicyRef` identifies the exact declared proposal-generation policy revision.

```text
GENERATOR != AUTHORITY
MODEL != AUTHORITY
HUMAN != AUTHORITY
RULE != AUTHORITY
GENERATION POLICY != AUTHORITY
```

A human-generated proposal is not accepted merely because the generator is human. A model-generated proposal is not rejected merely because the generator is a model. Acceptance/materialization authority is intentionally outside PR6.

## 5. Model output is not always a proposal

PR6 does not redefine PR2 model evaluation.

A model operating as an evaluator under an exact PR2 `EvaluationPolicyRef` may produce a real `ClaimEvaluation` because that workflow already names an existing governed claim and an evaluation policy.

A model suggesting a candidate object that does not yet exist in the accepted layer produces a PR6 proposal.

```text
MODEL OUTPUT != ALWAYS PROPOSAL
MODEL ClaimEvaluation != PersonalCapabilityState
MODEL Proposal != ClaimEvaluation
```

PR4 still requires explicit selected evaluations before state derivation.

## 6. Proposal basis and rationale

`ProposalBasisRef` records why a proposal was generated or which records/semantic objects were inspected. Supported internal basis kinds are:

```text
CAPABILITY_CONCEPT
EVIDENCE_RECORD
CAPABILITY_CLAIM
CLAIM_EVALUATION
EXTERNAL_ARTIFACT
OTHER
```

Basis is audit context, not epistemic assessment.

```text
PROPOSAL BASIS != EVIDENCE ASSESSMENT
BASIS EVIDENCE != SUPPORTING EVIDENCE
PROPOSAL RATIONALE != PROOF
```

A proposal citing an `EvidenceRecord` does not declare that record SUPPORTS a candidate claim. PR2 evaluation remains the layer that interprets evidence relative to a claim.

## 7. Privacy and one-scope proposal sets

`CapabilityProposal.subject_ref` is `None` for shared-scope proposals and an exact `CapabilitySubjectRef` for private person-scoped proposals.

`CapabilityProposalSet` is structurally one-scope:

```text
shared proposal set
  -> subject_ref = None

private proposal set
  -> exactly one subject_ref
```

Shared and person-scoped proposals cannot coexist in one set. Multiple private subjects cannot coexist in one set.

Person-scoped epistemic records may be used as internal basis only by a proposal carrying the same subject ref.

```text
SHARED TARGET != SHAREABLE PROPOSAL
PRIVATE BASIS -> PRIVATE PROPOSAL SCOPE
CROSS-SUBJECT PRIVATE BASIS -> INVALID
```

For example, a private project may reveal a possible gap in the shared Civilization Bootstrap ontology. The candidate target may be shared semantics while the proposal record remains private because its internal basis is person-scoped.

PR6 does not implement sanitization, consent, publication, or Commons promotion.

## 8. Exact semantic references and stale proposals

Proposals that inspect existing capability semantics use exact `CapabilityConceptRef` values.

Explicit validation against a supplied `CapabilityCatalog` rejects missing or stale revisions rather than substituting latest semantics.

```text
EXACT TARGET REF != LATEST REF
STALE PROPOSAL != SILENTLY UPGRADED PROPOSAL
```

Create-concept/split/merge suggested ids must also remain absent from the supplied catalog when validated; suggestion does not reserve namespace identity.

A create-relation proposal that already exists in the supplied catalog fails validation rather than silently becoming a no-op acceptance.

## 9. Immutable reviews

`ProposalReview` is a separate immutable record with:

```text
ProposalReviewId
proposal_id
ProposalReviewerRef
ProposalReviewPolicyRef
reviewed_at
verdict
rationale
```

PR6 review verdicts are deliberately recommendations:

```text
RECOMMEND_ACCEPT
RECOMMEND_REJECT
REQUEST_REVISION
ABSTAIN
```

There is no `ACCEPTED` verdict in v1.

```text
REVIEWER != AUTHORITY
HUMAN REVIEW != AUTOMATIC AUTHORITY
MODEL REVIEW != AUTOMATIC AUTHORITY
REVIEW POLICY != PERMISSION
```

## 10. Multiple reviews are facts, not votes

A proposal may have contradictory reviews. PR6 preserves all of them.

```text
RECOMMEND_ACCEPT
RECOMMEND_REJECT
ABSTAIN
```

may legitimately coexist.

PR6 performs no aggregation:

```text
MULTIPLE REVIEWS != VOTE
LATEST REVIEW != AUTHORITY
REVIEW COUNT != ACCEPTANCE
HUMAN REVIEW != MODEL OVERRIDE
```

A later governance layer may define an explicit aggregation/authorization policy, but PR6 does not infer one.

## 11. Proposal revision is new history

A proposal may name `supersedes_proposal_id` to preserve replacement lineage after review or reconsideration.

```text
PROPOSAL REVISION != MUTATION
```

The superseded proposal remains unchanged. `CapabilityProposalSet` requires the parent to exist in the same scope, requires causal ordering, and rejects supersession cycles.

PR6 intentionally has no mutable `proposal.status` or `proposal.is_approved` field. Workflow status belongs to later projections/governance rather than being silently inferred from review facts.

## 12. Validation against epistemics

`CapabilityProposalSet.validate_against_epistemics()` validates internal PR2 basis references without reinterpreting them:

- referenced evidence/claims/evaluations must exist;
- private basis requires a person-scoped proposal;
- basis subject must match proposal subject;
- evaluation basis resolves through its PR2 claim to determine subject.

Validation does not create a claim, evaluation, or state.

## 13. Deterministic strict serialization

A proposal snapshot is immutable and canonicalized:

```text
same exact proposals
+ same exact reviews
= same CapabilityProposalSet
= same canonical JSON
```

Proposal ids, review ids, basis refs, split outputs, merge source refs, proposals, and reviews are canonicalized deterministically where order has no semantic meaning.

Strict JSON decoding rejects:

- duplicate object keys;
- unknown/missing schema fields;
- unknown proposal kinds;
- unknown enum values;
- malformed exact refs;
- non-finite JSON constants.

```text
SERIALIZABLE PROPOSAL != GOVERNED ACCEPTANCE
```

## 14. Model runtime boundary

PR6 represents model generation/review identity but invokes no model runtime.

```text
MODEL REPRESENTABILITY != MODEL INTEGRATION
```

There are no OpenAI/Anthropic/Gemini/local-model calls, prompts, model credentials, network operations, or inference dependencies in PR6.

## 15. Explicitly absent public APIs

PR6 intentionally provides no public function named or equivalent to:

```text
apply_proposal
accept_proposal
approve_proposal
materialize_proposal
promote_proposal
proposal_to_claim
proposal_to_concept
auto_accept
```

It also introduces no:

```text
proposal confidence
acceptance score
approval count
authority score
majority vote
latest-review-wins rule
```

These absences are part of the non-authority boundary, not missing convenience features.

## 16. Real Civilization Bootstrap integration

PR6 is exercised against the real PR5 domain.

### Ontology proposal smoke

A model may propose a new scoped relation between exact PR5 concept revisions and receive `RECOMMEND_ACCEPT`. The PR5 `CapabilityCatalog` remains byte-for-byte unchanged and the proposed relation remains absent.

```text
MODEL ONTOLOGY PROPOSAL != ONTOLOGY MUTATION
```

### Person claim proposal smoke

A private PR2 `EvidenceRecord` may motivate a model-generated `basic_circuits@1` claim candidate. Even after `RECOMMEND_ACCEPT`:

```text
EpistemicRecordSet.claims == ()
EpistemicRecordSet.evaluations == ()
```

and no `PersonalCapabilityState` is created.

```text
MODEL CLAIM PROPOSAL != CLAIM
CLAIM PROPOSAL REVIEW != EVALUATION
RECOMMEND_ACCEPT != PERSONAL STATE
```

## 17. Non-goals

PR6 intentionally does not implement:

- proposal application/materialization;
- catalog mutation;
- automatic acceptance;
- automatic rejection by generator kind;
- reviewer authority inference;
- majority vote or review aggregation;
- proposal confidence/priority/authority scores;
- LLM/model runtime integration;
- prompt management;
- achievement or milestone proposals;
- progression/frontier proposals;
- recommendations or challenge generation;
- state proposals;
- permission/action proposals;
- database persistence;
- synchronization;
- Commons publication/promotion;
- HDE adapters;
- UI workflow status.

The PR6 contract is complete when Capability Lab can represent useful candidate changes and candidate person propositions without any proposal/review fact becoming an implicit authority to rewrite accepted semantics or person-scoped state.
