# PR6 Second Adversarial Boundary Review v1

Status: **normative adversarial supplement for PR6**

This review attacks boundaries that are easy to overread after the primary proposal-authority pass: policy-ref authenticity, external-artifact privacy classification, timestamp ingestion, proposal/review identity across independent snapshots, and persistence-level authority.

It does not add proposal application, materialization, authority aggregation, policy registries, storage, sync, or publication.

## 1. Strict timestamp ingestion — blocker repaired

The initial PR6 JSON parser checked for a visible `T` and timezone marker, then delegated to Python `datetime.fromisoformat()`. That parser accepts ISO-8601 forms broader than the audit schema claimed to support, including basic forms and some non-canonical offset representations.

PR6 now accepts only the explicit extended profile:

```text
YYYY-MM-DDTHH:MM:SS[.ffffff](Z|+HH:MM|-HH:MM)
```

with one to six fractional-second digits when a fraction is present.

Valid offset-aware inputs normalize to UTC on serialization.

```text
STRICT SERIALIZATION != PERMISSIVE DATETIME PARSING
VALID TIME != EVERY FORM datetime.fromisoformat ACCEPTS
SERIALIZED TIME IDENTITY = CANONICAL UTC REPRESENTATION
```

This is an ingestion/audit boundary. It does not make timestamp recency authoritative and does not change the first adversarial conclusion that explicit proposal/review links, not timestamp ordering alone, carry causal meaning.

## 2. Policy refs are identifiers, not authenticated policy content

`ProposalGenerationPolicyRef` and `ProposalReviewPolicyRef` contain exactly:

```text
namespace
key
revision
```

They provide canonical, exact policy identity syntax inside the supplied governance context.

They do **not** contain:

```text
policy content
content hash
signature
registry proof
authenticated issuer
authority grant
```

Therefore:

```text
POLICY REF != POLICY CONTENT
POLICY REF != CONTENT HASH
POLICY REF != AUTHENTICATED POLICY
POLICY REF != AUTHORITY
SAME POLICY REF STRING ACROSS STORES != PROOF OF SAME POLICY CONTENT
```

A future policy registry/import layer may bind exact refs to governed policy artifacts, hashes, issuers, or signatures. PR6 intentionally does not invent that layer.

The same boundary already exists conceptually in earlier Capability Lab layers: opaque/exact refs preserve declared identity without proving global authenticity.

## 3. External artifact and OTHER basis classification

`ProposalBasisKind.EXTERNAL_ARTIFACT` and `ProposalBasisKind.OTHER` are intentionally opaque references. PR6 does not resolve arbitrary external stores and therefore cannot infer whether such an artifact is public, private, consented, confidential, or shareable.

```text
EXTERNAL_ARTIFACT != PUBLIC ARTIFACT
OTHER != UNRESTRICTED DATA
OPAQUE REF != PRIVACY CLASSIFICATION
SERIALIZABLE EXTERNAL REF != SHAREABILITY PROOF
```

### 3.1 Internal-record relabeling — blocker repaired

The second adversarial pass found a concrete laundering path: an internal private `EvidenceId`, `CapabilityClaimId`, or `ClaimEvaluationId` could be placed in a `ProposalBasisRef` while falsely declaring its kind as `EXTERNAL_ARTIFACT` or `OTHER`. That would bypass the typed private-basis subject checks even though the supplied `EpistemicRecordSet` knew the identifier was internal.

Repair: during `validate_against_epistemics()`, if an `EXTERNAL_ARTIFACT` or `OTHER` ref exactly matches an internal evidence/claim/evaluation id in the supplied snapshot, validation fails closed and requires the correct typed basis kind.

```text
BASIS KIND LABEL != PRIVACY ESCAPE HATCH
INTERNAL RECORD ID != EXTERNAL ARTIFACT BY RELABELING
KNOWN INTERNAL BASIS MUST USE ITS TYPED BASIS KIND
```

### 3.2 What PR6 still cannot know

If an opaque external ref does not correspond to any internal PR2 record in the supplied snapshot, PR6 has no evidence from which to infer privacy classification.

That is not treated as public.

```text
NOT KNOWN INTERNAL != KNOWN PUBLIC
NO MATCH IN EpistemicRecordSet != SHAREABLE
```

Future connector/import/publication governance must carry artifact ownership, consent, visibility, provenance, and shareability metadata when those properties matter.

## 4. Proposal and review IDs are snapshot-local opaque IDs

`CapabilityProposalId` and `ProposalReviewId` are opaque identifiers. `CapabilityProposalSet` rejects duplicate proposal ids and duplicate review ids **inside one snapshot**.

PR6 is stateless and has no persistence registry. Therefore two independently assembled snapshots can reuse the same opaque id for materially different records.

```text
OPAQUE ID != CONTENT HASH
SNAPSHOT-LOCAL UNIQUENESS != GLOBAL UNIQUENESS
SAME PROPOSAL ID ACROSS SNAPSHOTS != SAME MATERIAL PROPOSAL
SAME REVIEW ID ACROSS SNAPSHOTS != SAME MATERIAL REVIEW
```

If two conflicting records with the same id are assembled into one `CapabilityProposalSet`, the set rejects the duplicate. But PR6 cannot compare records it was never given.

This mirrors the historical/recomputation boundary already established for other stateless Capability Lab layers:

```text
RECORD VALIDATION != PERSISTENCE GOVERNANCE
STATELESS SNAPSHOT != GLOBAL ID REGISTRY
```

A persistence/import/sync layer must govern cross-snapshot no-reuse, collision handling, source identity, and reconciliation.

## 5. Serialization and persistence do not create authority

A proposal set can be serialized, deserialized, stored, copied, or loaded without gaining acceptance semantics.

Canonical JSON preserves facts such as:

```text
proposal
review
RECOMMEND_ACCEPT
supersession lineage
basis refs
```

It does not add:

```text
accepted_proposals
authoritative_proposals
materialized_proposals
effective_verdict
current_status
permission
```

Therefore:

```text
SERIALIZED != ACCEPTED
DESERIALIZED != APPROVED
PERSISTED != AUTHORITATIVE
DURABLE RECORD != GOVERNED TRANSITION
RECOMMEND_ACCEPT + STORAGE != MATERIALIZATION
```

A database row, file, remote object, sync replica, or signed transport envelope would still only preserve a PR6 proposal/review record unless a separate governed materialization layer explicitly creates an accepted semantic or epistemic record.

## 6. Persistence-level race and identity limits

Because PR6 does not implement storage or transactions, it cannot guarantee:

- global uniqueness across writers;
- exactly-once proposal insertion;
- compare-and-swap on proposal lineage;
- review write ordering across replicas;
- cross-store policy-ref authenticity;
- immutable historical retention after external deletion;
- publication authorization;
- globally collision-proof actor/generator/reviewer refs.

Adding hidden in-memory registries to PR6 would not solve these distributed/persistence properties and would damage determinism.

```text
DERIVATION/VALIDATION LAYER != STORAGE TRANSACTION LAYER
IN-MEMORY REGISTRY != DISTRIBUTED AUTHORITY
```

These remain explicit future persistence/import/sync governance concerns.

## 7. Executable regressions

`tests/proposals/test_proposal_second_adversarial_v1.py` protects:

- rejection of non-canonical/basic timestamp forms;
- identical strict timestamp rules for proposal and review ingestion;
- UTC canonicalization of valid offset-aware input;
- policy refs exposing identifier fields only, not content/authentication/authority fields;
- rejection of internal PR2 record ids relabeled as `EXTERNAL_ARTIFACT` or `OTHER`;
- opaque unmatched external artifacts remaining unclassified rather than becoming implicitly public;
- proposal-id uniqueness being snapshot-local rather than content-addressed/global;
- review-id uniqueness being snapshot-local rather than global identity proof;
- serialization roundtrip not creating acceptance/materialization/authority fields.

## 8. Final boundary after second pass

```text
POLICY REF != AUTHENTICATED POLICY
EXTERNAL ARTIFACT != PUBLIC ARTIFACT
OPAQUE REF != PRIVACY CLASSIFICATION
KNOWN INTERNAL RECORD != EXTERNAL BY RELABELING

OPAQUE ID != CONTENT HASH
SNAPSHOT UNIQUENESS != GLOBAL UNIQUENESS
PERSISTENCE GOVERNANCE != PR6 VALIDATION

STRICT JSON != PERMISSIVE ISO PARSER
SERIALIZED != ACCEPTED
PERSISTED != AUTHORITATIVE
```

The second pass preserves the original PR6 purpose: proposals and reviews can become durable, inspectable governance inputs without any syntactic validity, policy ref, external reference, timestamp, identifier, storage event, or review recommendation becoming hidden authority.