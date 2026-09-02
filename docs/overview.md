# Understand the model

Capability Lab starts from a simple constraint: **a useful model of a person must not silently become authority over that person**.

That changes the architecture. Instead of asking for one universal score, the system keeps evidence,
interpretation, evaluation, state, advice, and authority as separate layers with explicit transitions.

## The five ideas to keep in mind

### 1. Evidence is not a score

An observation is only an external event or source artifact. It does not become evidence merely
because a model noticed it. The generic PR12 path requires an explicit reviewed materialization
boundary before a neutral `EvidenceRecord` exists.

Evidence itself still does not establish a capability claim or claim-wide conclusion.

```text
activity != observation authority
observation != evidence
evidence != claim
claim != supported claim
```

### 2. Unknown and conflict are real states

Capability Lab does not convert missing evidence into zero and does not force disagreement into a
single answer. `UNKNOWN`, insufficient evidence, and unresolved conflict remain representable.

A complete evidence basis can therefore produce a conservative result instead of manufacturing certainty.

### 3. History is part of the claim

Evaluations are retained rather than replaced by "the latest answer." Downstream state derivation
uses complete governed portfolios, so a caller cannot silently select only the convenient newer result.

This is why PR12.13 deliberately proves a history containing both an older `PARTIAL / INSUFFICIENT`
evaluation and a newer domain-sufficient `SUPPORTED` evaluation.

### 4. State requires governance after derivation

Even a valid derived capability state is not automatically the person's accepted or current state.

```text
DERIVED != PERSISTED
PERSISTED != ACCEPTED
ACCEPTED != CURRENT
CURRENT != LATEST
CURRENT != BEST
```

PR11.6 persists state, PR11.7 accepts it, and PR11.8 selects current state through separate governed steps.

### 5. Advice and presentation do not grant authority

PR11.9 progression is advisory. PR11.11 is a product/read projection. Neither can grant readiness,
mastery, licensing, permission, or professional authority.

```text
progression != prescription
product view != write-back
current capability != permission
```

## Shared definitions vs person-scoped records

Capability concepts and competence frames are shared semantic definitions. Evidence, evaluations,
state, acceptance, and current selection are person-scoped governed records.

Keeping those two categories separate avoids turning a shared ontology into a public profile database.

## Where to go next

If the mental model is clear, follow the [governed pipeline](governed-pipeline.md) end to end.
If you are integrating a consumer, go directly to the [consumer boundary](consumer-boundary.md).

For normative human-agency and privacy rules, read the [constitution](constitution.md).
For exact terminology, use the [vocabulary](vocabulary.md).
