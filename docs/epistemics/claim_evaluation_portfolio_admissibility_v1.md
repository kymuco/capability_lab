# PR11.4 — Complete ClaimEvaluation Portfolio Admissibility, Snapshot-Bound Exact Selection Basis and Anti-Cherry-Picking Governance v1

## Outcome

PR11.4 introduces a generic epistemic boundary that derives the complete in-scope
`CapabilityClaim` / `ClaimEvaluation` portfolio from one exact immutable
`EpistemicRecordSet` snapshot.

It closes the caller-controlled selection gap that remains after PR11.3.
Existing deterministic state derivation accepts explicit
`selected_evaluation_ids`; PR11.4 does not modify state derivation yet, but it
establishes the complete snapshot-bound evaluation set that a later governed
handoff must preserve.

## Core invariant

```text
COMPLETE IN-SCOPE PORTFOLIO
=
NO CALLER-CHOSEN SUBSET
```

For one exact:

```text
EpistemicRecordSet snapshot
CapabilitySubjectRef
CapabilityConceptRef revision
as_of
```

the complete portfolio contains every claim satisfying:

```text
claim.subject_ref == subject_ref
claim.concept_ref == concept_ref
claim.created_at <= as_of
```

and, for every such claim, every evaluation satisfying:

```text
evaluation.claim_id == claim.claim_id
evaluation.evaluated_at <= as_of
```

Claims with no admissible evaluation remain explicitly represented with an empty
evaluation tuple.

## Membership is not preference

Portfolio membership does not inspect an evaluation's:

```text
conclusion
policy_ref
evaluator_ref
evaluator kind
evidence reliability
coverage
conflict status
```

Therefore:

```text
ADMISSIBLE
!= TRUE
!= TRUSTED
!= PREFERRED
!= ACTIVE
!= STATE AUTHORITY
```

`SUPPORTED`, `CONTRADICTED`, `MIXED`, `INSUFFICIENT`, and `ABSTAINED`
evaluations are all retained when they are in scope.

PR11.4 defines no human-over-model rule, model-over-human rule, policy
preference, majority vote, recency weighting, supersession, or latest-wins
authority.

## Public surface

PR11.4 adds these symbols under `capability_lab.epistemics`:

```text
ClaimEvaluationPortfolioEntry
ClaimEvaluationPortfolioError
ClaimEvaluationPortfolioReceipt
InvalidClaimEvaluationPortfolio
build_complete_claim_evaluation_portfolio_v1
validate_exact_claim_evaluation_selection_v1
```

The two public operations are:

```python
build_complete_claim_evaluation_portfolio_v1(
    *,
    records: EpistemicRecordSet,
    subject_ref: CapabilitySubjectRef,
    concept_ref: CapabilityConceptRef,
    as_of: datetime,
) -> ClaimEvaluationPortfolioReceipt
```

and:

```python
validate_exact_claim_evaluation_selection_v1(
    *,
    records: EpistemicRecordSet,
    portfolio: ClaimEvaluationPortfolioReceipt,
    selected_evaluation_ids: tuple[ClaimEvaluationId, ...],
) -> tuple[ClaimEvaluationId, ...]
```

These symbols are deliberately not added to the package-root
`capability_lab` public surface.

## Portfolio receipt

A portfolio receipt binds:

```text
snapshot_sha256
subject_ref
exact concept_ref revision
canonical as_of
complete claim/evaluation entries
future claim exclusions
future evaluation exclusions
```

Convenience properties expose:

```text
claim_ids
admissible_evaluation_ids
unevaluated_claim_ids
```

The receipt contains no winning evaluation, preferred policy, confidence,
mastery, score, claim-dimension binding, or `PersonalCapabilityState`.

## Validator-issued provenance

As in PR11.3, structural receipt shape is not evidence that the governing
builder ran.

```text
direct ClaimEvaluationPortfolioReceipt(...)
-> validator_issued == False

build_complete_claim_evaluation_portfolio_v1(...)
-> validator_issued == True
```

The exact-selection gate accepts only a validator-issued receipt.

This marker is provenance-of-validation only. It is not authentication,
a signature, trusted persistence, or protection against hostile Python runtime
introspection.

## Records-derived content authority

The validator-issued marker identifies builder provenance only. It is not the
authority for portfolio completeness, and receipt-contained membership is never
trusted by itself.

Before validating a caller selection, PR11.4 reconstructs the expected portfolio
from the supplied `EpistemicRecordSet` using the receipt's exact:

```text
subject_ref
concept_ref
as_of
```

and requires the supplied receipt to equal that records-derived portfolio in
full, including:

```text
claim/evaluation entries
future claim exclusions
future evaluation exclusions
```

Only after that equality check does the gate compare caller-selected evaluation
identities with the records-derived admissible set.

```text
RECEIPT MARKER
!= CONTENT AUTHORITY

RECORDS-DERIVED COMPLETE PORTFOLIO
= CONTENT AUTHORITY
```

This rule is intentionally stronger than Python object immutability. For
example, `dataclasses.replace(...)` can preserve the private runtime receipt type
while changing dataclass fields. Such a modified receipt remains structurally
well formed but fails records-derived content equality and therefore cannot hide
an admissible evaluation or temporal exclusion.

Likewise, a public subclass cannot acquire builder authority merely by
redefining `validator_issued`; the selection gate requires the exact private
builder receipt runtime type.

These checks are application-level integrity governance, not cryptographic
authentication or protection against a hostile interpreter/runtime.

## Exact selection

After records-derived receipt verification, the anti-cherry-picking gate requires
canonical exact equality:

```text
selected_evaluation_ids
==
records-derived expected.admissible_evaluation_ids
```

It is symmetric with respect to direction:

```text
omit SUPPORTED    -> REJECT
omit CONTRADICTED -> REJECT
omit ABSTAINED    -> REJECT
add inadmissible  -> REJECT
exact complete set -> PASS
```

When multiple problems exist, deterministic sorted identity order controls the
first reported omission or extra identity.

## Exact snapshot binding

The receipt is bound to the complete canonical PR11.3 snapshot fingerprint:

```text
portfolio.snapshot_sha256
==
epistemic_snapshot_sha256_v1(records)
```

Any snapshot change invalidates the receipt, including an unrelated append.

PR11.4 intentionally does not introduce scope hashes, incremental proofs, or
dependency-aware receipt reuse in v1. Rebuilding the portfolio is the simple,
auditable operation.

## Historical backfill

PR11.3 allows a newly appended immutable evaluation to have an historical
`evaluated_at`.

Therefore:

```text
AS_OF TIME
!= KNOWLEDGE SNAPSHOT
```

If:

```text
S1 -> portfolio(S1, as_of=T10)
```

and PR11.3 later permits:

```text
S2 = S1 + evaluation(evaluated_at=T7)
```

then the old receipt cannot be used with `S2`, even though `as_of` remains
`T10`.

The rebuilt portfolio over `S2` includes the historical evaluation.

```text
HISTORICAL BACKFILL
CANNOT BE HIDDEN
BY REUSING AN OLD PORTFOLIO RECEIPT
```

## Temporal audit surface

Claims for the exact subject/concept scope created after `as_of` appear in:

```text
excluded_future_claim_ids
```

Evaluations attached to exact-scope claims but evaluated after `as_of` appear in:

```text
excluded_future_evaluation_ids
```

These fields explain temporal exclusion. They do not establish preference or
state authority.

Records from another subject or another exact concept revision are simply
outside the requested scope and are not temporal exclusions.

## Real PR11.2 -> PR11.3 -> PR11.4 bridge

The integration suite reuses the real Pilot 01 PR11.2 multi-evidence
`ClaimEvaluation`, places it in a real `EpistemicRecordSet`, and then exercises
PR11.3 append-only correction semantics.

```text
real PR10.1 terminal reviewed-dependence PASS
        ->
real PR11.2 multi-evidence ClaimEvaluation
        ->
PR11.3 immutable snapshot
        ->
append correction under NEW ClaimEvaluationId
        ->
PR11.4 complete portfolio
```

After correction append, both original and correction identities are mandatory.
Selecting only either side is rejected.

The integration suite also appends an historical correction under a new identity
and proves that an old portfolio receipt becomes stale while a rebuilt portfolio
includes the backfilled evaluation.

The review-hardening regression suite additionally proves that:

```text
dataclasses.replace(builder_receipt, entries=cherry_picked_subset)
-> REJECT

public receipt subclass with validator_issued=True
-> REJECT

dataclasses.replace(builder_receipt, excluded_future_evaluation_ids=())
-> REJECT
```

## Authority localization

Production authority is isolated to:

```text
src/capability_lab/epistemics/evaluation_portfolio.py
```

Its exact import surface is frozen:

```text
stdlib:
    dataclasses.dataclass
    datetime.datetime

capability_lab.semantics:
    CapabilityConceptRef

.core:
    CapabilityClaimId
    CapabilitySubjectRef
    ClaimEvaluationId
    EpistemicError
    canonical_time

.record_set:
    EpistemicRecordSet

.snapshot_transition:
    epistemic_snapshot_sha256_v1
```

It imports no derivation, state, history, progression, proposals, PlayerWindow,
domain, or Pilot authority.

Pilot 01 production modules are forbidden from importing the PR11.4 portfolio
module or its public symbols.

## Explicit non-goals

```text
PR11.4 != EVALUATION TRUTH
PR11.4 != EVALUATOR TRUST
PR11.4 != HUMAN > MODEL
PR11.4 != MODEL > HUMAN
PR11.4 != POLICY PREFERENCE
PR11.4 != SUPERSESSION
PR11.4 != LATEST-WINS
PR11.4 != MAJORITY VOTE
PR11.4 != RECENCY WEIGHTING
PR11.4 != EVIDENCE WEIGHTING
PR11.4 != CLAIM-DIMENSION BINDING
PR11.4 != STATE DERIVATION
PR11.4 != PersonalCapabilityState
PR11.4 != PROGRESSION
PR11.4 != PlayerWindow
```

In particular:

```text
PORTFOLIO COMPLETE
!=
PORTFOLIO CONSISTENT
```

A complete portfolio may contain mutually opposing evaluations. PR11.4 must
preserve that epistemic fact instead of resolving it.

## Intended diff

PR11.4 is intentionally limited to exactly six files:

```text
docs/epistemics/claim_evaluation_portfolio_admissibility_v1.md
src/capability_lab/epistemics/__init__.py
src/capability_lab/epistemics/evaluation_portfolio.py
tests/epistemics/test_evaluation_portfolio_v1.py
tests/pilots/test_civilization_bootstrap_pilot_01_authority_boundary_v1.py
tests/pilots/test_civilization_bootstrap_pilot_01_evaluation_portfolio_integration_v1.py
```

No state, derivation, history, progression, PlayerWindow, or Pilot production
module is part of the intended diff.

## Release boundary

After PR11.4, Capability Lab may deterministically establish that, for one exact
snapshot/scope/as-of tuple:

- every in-scope claim is represented;
- unevaluated claims remain visible;
- every in-scope evaluation through the temporal boundary is represented;
- evaluator identity, policy, or conclusion cannot silently remove an
  evaluation;
- caller selection cannot silently omit an admissible evaluation;
- a structurally valid or marker-preserving modified receipt cannot replace the
  records-derived complete portfolio;
- stale snapshot-bound receipts cannot hide later append-only historical
  knowledge.

The next authority boundary is PR11.5: governed handoff from this complete
portfolio into deterministic state derivation.
