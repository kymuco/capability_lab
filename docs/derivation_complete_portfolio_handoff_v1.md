# PR11.5 — Complete Portfolio-to-State Governed Handoff, Exact Derivation Basis Closure, Full Claim-Binding Coverage and Unevaluated-Claim Fail-Closed Governance v1

## Outcome

PR11.5 closes the authority gap between the complete snapshot-bound
`ClaimEvaluation` portfolio established by PR11.4 and the existing PR4 pure
deterministic state-derivation primitive.

PR4 remains unchanged: it deterministically composes an exact explicitly supplied
evaluation basis and exact explicit claim-to-dimension bindings.  PR11.5 adds the
governed admission path that determines which basis is permitted to reach PR4.

```text
PR11.4 ESTABLISHES WHAT MUST BE CONSIDERED.

PR11.5 MAKES IT IMPOSSIBLE FOR GOVERNED DETERMINISTIC
STATE DERIVATION TO CONSIDER LESS.
```

## Core invariants

```text
PORTFOLIO SCOPE
=
DERIVATION SCOPE
```

```text
DERIVATION EVALUATION BASIS
=
COMPLETE REVALIDATED PORTFOLIO EVALUATION BASIS
```

```text
BOUND CLAIM SET
=
COMPLETE PORTFOLIO CLAIM SET
```

```text
UNEVALUATED CLAIM
=>
NO GOVERNED STATE DERIVATION v1
```

```text
OUTPUT EVALUATION BASIS
=
GOVERNED HANDOFF EVALUATION BASIS
```

```text
OUTPUT RECONSTRUCTED CLAIM BINDINGS
=
GOVERNED HANDOFF CLAIM BINDINGS
```

## Layering

PR11.5 deliberately does not replace PR4 or relabel the PR4 algorithm as a new
state-derivation policy.

```text
PR11.4 = which epistemic records are in scope
PR11.5 = which exact complete basis may reach state derivation
PR4     = how that exact basis deterministically becomes PR3 state
PR3     = state representation
```

The existing PR4 identifiers remain the identifiers of the state algorithm:

```text
policy  = core:deterministic_supported_state@1
deriver = capability_lab:deterministic_supported_state_v1
```

PR11.5 is an admission/governance boundary, not a new scoring, weighting,
conflict-resolution, mastery, or state-standing algorithm.

## Public API

PR11.5 adds under `capability_lab.derivation`:

```text
CompletePortfolioStateDerivationError
CompletePortfolioStateDerivationRequest
derive_supported_state_from_complete_portfolio_v1
```

The request is intentionally narrow:

```python
CompletePortfolioStateDerivationRequest(
    state_id: PersonalCapabilityStateId,
    derived_at: datetime,
    claim_dimension_bindings: tuple[ClaimDimensionBinding, ...] = (),
)
```

It contains no:

```text
subject_ref
concept_ref
frame_ref
as_of
selected_evaluation_ids
preferred_evaluation_id
evaluator preference
evaluation-policy preference
```

The governed operation is:

```python
derive_supported_state_from_complete_portfolio_v1(
    *,
    records: EpistemicRecordSet,
    frame: CompetenceFrame,
    portfolio: ClaimEvaluationPortfolioReceipt,
    request: CompletePortfolioStateDerivationRequest,
) -> PersonalCapabilityState
```

The historical raw PR4 operation remains public as a pure deterministic
primitive:

```text
derive_supported_state_v1
=
RAW DETERMINISTIC PR4 PRIMITIVE
```

The PR11.5 operation is the governed complete-portfolio entrypoint:

```text
derive_supported_state_from_complete_portfolio_v1
=
GOVERNED COMPLETE-BASIS ENTRYPOINT
```

Keeping the raw primitive does not grant it governance authority.  PR4's own
contract has always stated that selection authority is external to PR4.

## One source of scope authority

PR11.5 does not accept a second caller-supplied copy of portfolio scope.

The effective deterministic request receives:

```text
subject_ref <- portfolio.subject_ref
concept_ref <- portfolio.concept_ref
as_of       <- portfolio.as_of
frame_ref   <- exact supplied frame.ref
```

Therefore there is no caller-controlled `request.subject_ref`,
`request.concept_ref`, or `request.as_of` that could be rebound independently
of the exact PR11.4 receipt.

The exact frame remains an explicit input because PR11.4 contains no frame or
claim-to-dimension ontology authority.

## PR11.4 revalidation is mandatory

Before constructing any PR4 request, PR11.5 calls the hardened PR11.4 exact
selection gate using the portfolio's own complete evaluation-id tuple:

```python
validate_exact_claim_evaluation_selection_v1(
    records=records,
    portfolio=portfolio,
    selected_evaluation_ids=portfolio.admissible_evaluation_ids,
)
```

That gate does not trust receipt-contained membership by itself.  It requires:

```text
exact private builder receipt runtime type
+ exact current snapshot SHA
+ records-derived portfolio reconstruction
+ complete receipt equality
+ exact admissible evaluation set equality
```

Therefore PR11.5 inherits PR11.4 rejection of:

```text
stale portfolio receipts
public structural receipts
a forged public receipt subclass
dataclasses.replace(...) membership removal
future-exclusion metadata tampering
hidden historical correction/backfill
```

```text
RECEIPT MARKER != CONTENT AUTHORITY
RECORDS-DERIVED COMPLETE PORTFOLIO = CONTENT AUTHORITY
```

## Complete evaluation basis

The caller never supplies evaluation identities to PR11.5.

After PR11.4 revalidation, the returned exact complete evaluation tuple becomes
the only `selected_evaluation_ids` tuple supplied internally to PR4.

```text
CALLER EVALUATION SELECTION SURFACE = ABSENT
```

Consequently, in-scope evaluations cannot be omitted because they are:

```text
SUPPORTED
CONTRADICTED
MIXED
INSUFFICIENT
ABSTAINED
from another evaluator
from another evaluation policy
older
newer
inconvenient
```

PR11.5 does not reinterpret any of those categories.  It only prevents silent
membership loss between PR11.4 and PR4.

## Unevaluated claims fail closed

PR11.4 intentionally keeps claims with no admissible evaluation visible in the
portfolio.  Existing PR3 state v1 cannot honestly encode that condition:

```text
UNKNOWN dimension
-> may carry no claim or evaluation references

INSUFFICIENT dimension
-> requires at least one basis evaluation
```

PR11.5 therefore does not manufacture a state interpretation for an unevaluated
claim.

```text
UNEVALUATED CLAIM
!= UNKNOWN CAPABILITY

UNEVALUATED CLAIM
!= INSUFFICIENT CAPABILITY
```

If any complete in-scope portfolio entry has no admissible evaluation, the
whole governed derivation fails closed with the first canonical claim id.

This is intentionally stronger than deriving from the evaluated subset while
silently ignoring the unevaluated claim.

An entirely empty portfolio is different.  It contains no in-scope claim that
would be lost, so it may deterministically produce the existing all-`UNKNOWN`
PR4 state with an empty binding set.

## Complete claim-binding coverage

Evaluation completeness alone is insufficient because cherry-picking could
otherwise move from evaluation ids to claim bindings.

PR11.5 therefore requires:

```text
set(request.claim_dimension_bindings.claim_id)
==
set(portfolio.claim_ids)
```

For a non-empty admissible portfolio:

```text
missing portfolio claim binding -> REJECT
extra non-portfolio claim binding -> REJECT
duplicate claim binding -> REJECT
unknown exact-frame dimension -> REJECT
```

Each claim still uses PR4's existing invariant that its complete evaluation
basis is repeated consistently in every dimension to which the claim is bound.

```text
CLAIM BASIS IS CONSISTENT ACROSS ITS DIMENSION USES
```

## Binding coverage is not binding-semantic authority

PR11.5 guarantees complete explicit binding coverage.  It does not determine
whether a claim was mapped to the philosophically or semantically correct
competence dimension.

```text
COMPLETE CLAIM BINDING
!= SEMANTICALLY CORRECT CLAIM BINDING

BINDING COVERAGE
!= BINDING AUTHORITY
```

The exact frame and mapping remain explicit inputs at this boundary.  A later
policy layer may govern claim-to-dimension mapping semantics without weakening
PR11.5 completeness.

## Time

`as_of` is taken only from the exact portfolio.

`derived_at` remains an explicit deterministic caller input and must satisfy:

```text
derived_at >= portfolio.as_of
```

PR11.5 adds no current clock, random id generation, network dependency, model,
or global mutable configuration.

`state_id` remains caller-supplied exactly as in PR4.  Cross-snapshot
`PersonalCapabilityStateId` reuse is still a persistence/history concern, not a
stateless derivation concern.

## Internal handoff to PR4

After all PR11.5 admission checks, the adapter constructs:

```python
DeterministicStateDerivationRequest(
    state_id=request.state_id,
    subject_ref=portfolio.subject_ref,
    concept_ref=portfolio.concept_ref,
    frame_ref=frame.ref,
    as_of=portfolio.as_of,
    derived_at=request.derived_at,
    selected_evaluation_ids=complete_evaluation_ids,
    claim_dimension_bindings=request.claim_dimension_bindings,
)
```

and calls unchanged:

```python
derive_supported_state_v1(...)
```

Thus PR4 standing/conflict semantics remain the semantics of the resulting
`PersonalCapabilityState`.

For example, a complete same-claim basis containing both `SUPPORTED` and
`CONTRADICTED` still produces PR4's existing:

```text
standing = SUPPORTED
conflict_status = UNRESOLVED
```

PR11.5 does not resolve or suppress that conflict; it ensures both records reach
PR4.

## Postcondition audit

PR11.5 performs defense-in-depth checks after PR4 returns.

First it collects the union of every output `basis_evaluation_ids` and requires:

```text
output evaluation-id set
==
complete revalidated portfolio evaluation-id set
```

It also checks every bound claim in every bound dimension independently:

```text
output basis for (claim, dimension)
==
complete portfolio evaluation basis for claim
```

This prevents a future regression from partitioning one claim's evaluations across
dimensions while preserving only the global union.  For example, `SUPPORTED` may
not be routed only to `execution` while `CONTRADICTED` is routed only to
`diagnosis`.

Then it resolves each output basis evaluation back to its claim and reconstructs:

```text
claim_id -> dimension_keys
```

That reconstructed mapping must exactly equal the complete input binding map.

These postconditions turn the existing PR4 audit-completeness property into an
explicit PR11.5 handoff invariant.  A future PR4 regression that silently drops,
partitions, or moves a claim basis cannot pass the governed wrapper.

## Historical backfill composition

PR11.3 allows a later valid snapshot to append historical epistemic material
under a new typed identity.

Suppose:

```text
S1 contains eval_A evaluated at T5
portfolio(S1, as_of=T10) = {eval_A}
```

Later:

```text
S2 = S1 + eval_B evaluated at T7
```

The old S1 portfolio is stale on S2 because its snapshot hash no longer matches.
A rebuilt PR11.4 portfolio is:

```text
portfolio(S2, as_of=T10) = {eval_A, eval_B}
```

PR11.5 can derive only from that complete rebuilt basis.

```text
HISTORICAL BACKFILL
=> PORTFOLIO REBUILD
=> DERIVATION BASIS EXPANSION
```

No special latest-wins or supersession rule is introduced.

## Real Pilot 01 integration

The integration suite carries the existing real chain through the new boundary:

```text
real PR10.1 terminal reviewed-dependence PASS
        ->
real PR11.2 multi-evidence ClaimEvaluation
        ->
PR11.3 immutable snapshot succession
        ->
PR11.4 complete portfolio
        ->
PR11.5 governed deterministic state
```

The real PR11.2 evaluation is `INSUFFICIENT`, so the PR4 state remains
`INSUFFICIENT`; PR11.5 does not upgrade or reinterpret it.

When a correction is appended under a new `ClaimEvaluationId`, the rebuilt
portfolio contains both identities and the resulting state basis must contain
both identities.  A pre-append portfolio cannot authorize state derivation on
the successor snapshot.

The real integration also appends an in-scope claim with no evaluation and
proves that the entire governed state derivation fails closed instead of
silently deriving from the older evaluated subset.

## Authority localization

New production authority is localized to:

```text
src/capability_lab/derivation/complete_portfolio_handoff_v1.py
```

Its imports are frozen by an exact AST allowlist.  It may depend only on:

```text
stdlib:
    dataclasses.dataclass
    datetime.datetime

capability_lab.epistemics:
    ClaimEvaluationPortfolioReceipt
    EpistemicRecordSet
    InvalidClaimEvaluationPortfolio
    validate_exact_claim_evaluation_selection_v1

capability_lab.epistemics.core:
    EpistemicError
    canonical_time

capability_lab.state:
    CompetenceFrame
    PersonalCapabilityState
    PersonalCapabilityStateId

.derivation deterministic_v1:
    ClaimDimensionBinding
    DeterministicStateDerivationRequest
    StateDerivationError
    derive_supported_state_v1
```

It imports no:

```text
history
progression
proposals
player_window
domains
pilots
model or LLM runtime
```

No Pilot 01 production module gains derivation authority.

## Explicit non-goals

```text
PR11.5 != EVALUATION TRUTH
PR11.5 != EVALUATOR TRUST
PR11.5 != EVALUATOR WEIGHTING
PR11.5 != POLICY PREFERENCE
PR11.5 != LATEST-WINS
PR11.5 != SUPERSESSION
PR11.5 != MAJORITY VOTE
PR11.5 != RECENCY WEIGHTING
PR11.5 != CONFLICT RESOLUTION

PR11.5 != CLAIM-DIMENSION CLASSIFICATION
PR11.5 != BINDING SEMANTIC AUTHORITY
PR11.5 != FRAME AUTHORITY

PR11.5 != STATE SCHEMA V2
PR11.5 != STATE HISTORY ACCEPTANCE
PR11.5 != STATE-ID REGISTRY
PR11.5 != PROGRESSION
PR11.5 != PlayerWindow
```

## Release boundary

A successful PR11.5 governed derivation means only that:

```text
1. the exact PR11.4 portfolio revalidated against the exact supplied snapshot;
2. no in-scope claim lacked an admissible evaluation;
3. every in-scope claim had one explicit exact-frame binding;
4. every admissible evaluation reached the unchanged PR4 deterministic basis;
5. the output basis and reconstructed binding map preserved the governed handoff.
```

It does not mean the claims are true, the bindings are semantically correct, the
state is mastery, or downstream progression/publication authority has been
granted.

```text
GOVERNED HANDOFF PASS
!= TRUTH
!= MASTERY
!= BINDING CORRECTNESS
!= PROGRESSION AUTHORITY
```
