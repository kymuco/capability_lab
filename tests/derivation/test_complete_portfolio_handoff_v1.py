from dataclasses import fields
from datetime import timedelta

import pytest

from capability_lab.derivation import (
    ClaimDimensionBinding,
    CompletePortfolioStateDerivationError,
    CompletePortfolioStateDerivationRequest,
    DETERMINISTIC_SUPPORTED_STATE_POLICY_V1,
    derive_supported_state_from_complete_portfolio_v1,
)
from capability_lab.epistemics import (
    EpistemicRecordSet,
    EvaluationConclusion,
    build_complete_claim_evaluation_portfolio_v1,
)
from capability_lab.state import (
    DimensionConflictStatus,
    DimensionStanding,
    PersonalCapabilityStateId,
)

from test_derivation_adversarial_v1 import (
    CLAIM_A,
    CLAIM_C,
    CONCEPT_A,
    EVAL_MAIN,
    EVAL_SECOND,
    SUBJECT_A,
    T0,
    binding,
    claim,
    evaluation,
    evidence,
    frame,
    records,
)


def _portfolio(snapshot: EpistemicRecordSet, *, as_of=T0):
    return build_complete_claim_evaluation_portfolio_v1(
        records=snapshot,
        subject_ref=SUBJECT_A,
        concept_ref=CONCEPT_A,
        as_of=as_of,
    )


def _request(*bindings: ClaimDimensionBinding, derived_at=T0):
    return CompletePortfolioStateDerivationRequest(
        state_id=PersonalCapabilityStateId("state_pr11_5_complete_portfolio"),
        derived_at=derived_at,
        claim_dimension_bindings=tuple(bindings),
    )


def _dimension(state, key: str):
    return next(item for item in state.dimensions if item.dimension_key == key)


def _single_supported_snapshot() -> EpistemicRecordSet:
    return records(
        evidence_records=(evidence("ev_pr11_5_main", SUBJECT_A),),
        claims=(claim(CLAIM_A, SUBJECT_A, CONCEPT_A),),
        evaluations=(
            evaluation(
                evaluation_id=EVAL_MAIN,
                claim_id=CLAIM_A,
                evidence_id="ev_pr11_5_main",
                conclusion=EvaluationConclusion.SUPPORTED,
            ),
        ),
    )


def test_governed_request_surface_has_no_scope_or_evaluation_selection_controls() -> None:
    names = {item.name for item in fields(CompletePortfolioStateDerivationRequest)}
    assert names == {
        "state_id",
        "derived_at",
        "claim_dimension_bindings",
    }
    assert {
        "subject_ref",
        "concept_ref",
        "frame_ref",
        "as_of",
        "selected_evaluation_ids",
        "evaluation_ids",
        "preferred_evaluation_id",
        "evaluation_policy_ref",
        "evaluator_ref",
    }.isdisjoint(names)


def test_complete_single_claim_portfolio_derives_through_existing_pr4_policy() -> None:
    snapshot = _single_supported_snapshot()
    portfolio = _portfolio(snapshot)

    state = derive_supported_state_from_complete_portfolio_v1(
        records=snapshot,
        frame=frame(),
        portfolio=portfolio,
        request=_request(binding(CLAIM_A, "execution")),
    )

    execution = _dimension(state, "execution")
    assert state.subject_ref == portfolio.subject_ref
    assert state.concept_ref == portfolio.concept_ref
    assert state.as_of == portfolio.as_of
    assert state.derivation_policy_ref == DETERMINISTIC_SUPPORTED_STATE_POLICY_V1
    assert execution.standing is DimensionStanding.SUPPORTED
    assert execution.supported_claim_ids == (CLAIM_A,)
    assert execution.basis_evaluation_ids == (EVAL_MAIN,)


def test_empty_complete_portfolio_derives_all_unknown_without_bindings() -> None:
    snapshot = EpistemicRecordSet()
    portfolio = _portfolio(snapshot)

    state = derive_supported_state_from_complete_portfolio_v1(
        records=snapshot,
        frame=frame(),
        portfolio=portfolio,
        request=_request(),
    )

    assert portfolio.claim_ids == ()
    assert portfolio.admissible_evaluation_ids == ()
    assert all(item.standing is DimensionStanding.UNKNOWN for item in state.dimensions)
    assert all(item.basis_evaluation_ids == () for item in state.dimensions)


def test_unevaluated_in_scope_claim_fails_closed() -> None:
    snapshot = records(
        evidence_records=(),
        claims=(claim(CLAIM_A, SUBJECT_A, CONCEPT_A),),
        evaluations=(),
    )
    portfolio = _portfolio(snapshot)
    assert portfolio.unevaluated_claim_ids == (CLAIM_A,)

    with pytest.raises(
        CompletePortfolioStateDerivationError,
        match=f"complete portfolio contains unevaluated claim: {CLAIM_A}",
    ):
        derive_supported_state_from_complete_portfolio_v1(
            records=snapshot,
            frame=frame(),
            portfolio=portfolio,
            request=_request(binding(CLAIM_A, "execution")),
        )


def test_one_unevaluated_claim_blocks_whole_mixed_portfolio_derivation() -> None:
    supported = evaluation(
        evaluation_id=EVAL_MAIN,
        claim_id=CLAIM_A,
        evidence_id="ev_pr11_5_main",
        conclusion=EvaluationConclusion.SUPPORTED,
    )
    snapshot = records(
        evidence_records=(evidence("ev_pr11_5_main", SUBJECT_A),),
        claims=(
            claim(CLAIM_A, SUBJECT_A, CONCEPT_A),
            claim(CLAIM_C, SUBJECT_A, CONCEPT_A),
        ),
        evaluations=(supported,),
    )
    portfolio = _portfolio(snapshot)
    assert portfolio.unevaluated_claim_ids == (CLAIM_C,)

    with pytest.raises(
        CompletePortfolioStateDerivationError,
        match=f"complete portfolio contains unevaluated claim: {CLAIM_C}",
    ):
        derive_supported_state_from_complete_portfolio_v1(
            records=snapshot,
            frame=frame(),
            portfolio=portfolio,
            request=_request(
                binding(CLAIM_A, "execution"),
                binding(CLAIM_C, "diagnosis"),
            ),
        )


def test_every_complete_portfolio_claim_requires_exactly_one_binding() -> None:
    snapshot = _single_supported_snapshot()
    portfolio = _portfolio(snapshot)

    with pytest.raises(
        CompletePortfolioStateDerivationError,
        match=f"complete portfolio claim is missing claim-dimension binding: {CLAIM_A}",
    ):
        derive_supported_state_from_complete_portfolio_v1(
            records=snapshot,
            frame=frame(),
            portfolio=portfolio,
            request=_request(),
        )


def test_binding_for_non_portfolio_claim_is_rejected() -> None:
    snapshot = _single_supported_snapshot()
    portfolio = _portfolio(snapshot)

    with pytest.raises(
        CompletePortfolioStateDerivationError,
        match=f"claim-dimension binding references non-portfolio claim: {CLAIM_C}",
    ):
        derive_supported_state_from_complete_portfolio_v1(
            records=snapshot,
            frame=frame(),
            portfolio=portfolio,
            request=_request(
                binding(CLAIM_A, "execution"),
                binding(CLAIM_C, "diagnosis"),
            ),
        )


def test_derived_at_may_not_precede_portfolio_as_of() -> None:
    snapshot = _single_supported_snapshot()
    portfolio = _portfolio(snapshot)

    with pytest.raises(
        CompletePortfolioStateDerivationError,
        match="derived_at must not precede complete portfolio as_of",
    ):
        derive_supported_state_from_complete_portfolio_v1(
            records=snapshot,
            frame=frame(),
            portfolio=portfolio,
            request=_request(
                binding(CLAIM_A, "execution"),
                derived_at=T0 - timedelta(seconds=1),
            ),
        )


def test_complete_same_claim_conflict_reaches_state_without_partition_or_drop() -> None:
    supported = evaluation(
        evaluation_id=EVAL_MAIN,
        claim_id=CLAIM_A,
        evidence_id="ev_pr11_5_main",
        conclusion=EvaluationConclusion.SUPPORTED,
    )
    contradicted = evaluation(
        evaluation_id=EVAL_SECOND,
        claim_id=CLAIM_A,
        evidence_id="ev_pr11_5_second",
        conclusion=EvaluationConclusion.CONTRADICTED,
    )
    snapshot = records(
        evidence_records=(
            evidence("ev_pr11_5_main", SUBJECT_A),
            evidence("ev_pr11_5_second", SUBJECT_A),
        ),
        claims=(claim(CLAIM_A, SUBJECT_A, CONCEPT_A),),
        evaluations=(supported, contradicted),
    )
    portfolio = _portfolio(snapshot)

    state = derive_supported_state_from_complete_portfolio_v1(
        records=snapshot,
        frame=frame(),
        portfolio=portfolio,
        request=_request(binding(CLAIM_A, "execution")),
    )

    execution = _dimension(state, "execution")
    assert execution.basis_evaluation_ids == tuple(sorted((EVAL_MAIN, EVAL_SECOND)))
    assert execution.standing is DimensionStanding.SUPPORTED
    assert execution.conflict_status is DimensionConflictStatus.UNRESOLVED


def test_multi_dimension_binding_repeats_same_complete_claim_basis_in_each_dimension() -> None:
    snapshot = _single_supported_snapshot()
    portfolio = _portfolio(snapshot)

    state = derive_supported_state_from_complete_portfolio_v1(
        records=snapshot,
        frame=frame(),
        portfolio=portfolio,
        request=_request(binding(CLAIM_A, "execution", "diagnosis")),
    )

    assert _dimension(state, "execution").basis_evaluation_ids == (EVAL_MAIN,)
    assert _dimension(state, "diagnosis").basis_evaluation_ids == (EVAL_MAIN,)
