from dataclasses import replace
from datetime import timedelta

import pytest

from capability_lab.derivation import (
    ClaimDimensionBinding,
    CompletePortfolioStateDerivationError,
    CompletePortfolioStateDerivationRequest,
    derive_supported_state_from_complete_portfolio_v1,
)
from capability_lab.epistemics import (
    CapabilityClaimId,
    ClaimEvaluationId,
    EpistemicRecordSet,
    EvaluationConclusion,
    build_complete_claim_evaluation_portfolio_v1,
    validate_epistemic_snapshot_successor_v1,
)
from capability_lab.state import (
    CompetenceDimensionDefinition,
    CompetenceFrame,
    CompetenceFrameId,
    DimensionStanding,
    PersonalCapabilityStateId,
)

from test_civilization_bootstrap_pilot_01_snapshot_succession_integration_v1 import (
    _real_pr11_2_case,
)


def _frame() -> CompetenceFrame:
    return CompetenceFrame(
        CompetenceFrameId.parse("pilot:bounded_reasoning_handoff"),
        1,
        "Pilot 01 bounded reasoning handoff frame",
        "Minimal exact frame used only to exercise the PR11.5 governed handoff.",
        (
            CompetenceDimensionDefinition(
                "reasoning",
                "Reasoning",
                "Bounded reasoning dimension for the real Pilot 01 integration path.",
            ),
        ),
    )


def _portfolio(records, claim, *, as_of):
    return build_complete_claim_evaluation_portfolio_v1(
        records=records,
        subject_ref=claim.subject_ref,
        concept_ref=claim.concept_ref,
        as_of=as_of,
    )


def _request(*claim_ids: CapabilityClaimId, derived_at):
    return CompletePortfolioStateDerivationRequest(
        state_id=PersonalCapabilityStateId("state_pilot_01_pr11_5_handoff"),
        derived_at=derived_at,
        claim_dimension_bindings=tuple(
            ClaimDimensionBinding(claim_id, ("reasoning",))
            for claim_id in claim_ids
        ),
    )


def _reasoning(state):
    return next(item for item in state.dimensions if item.dimension_key == "reasoning")


def _correction(evaluation, *, evaluation_id: str, minutes: int):
    return replace(
        evaluation,
        evaluation_id=ClaimEvaluationId(evaluation_id),
        evaluated_at=evaluation.evaluated_at + timedelta(minutes=minutes),
        conclusion=EvaluationConclusion.ABSTAINED,
        rationale=(
            "PR11.5 integration correction is appended under a new immutable "
            "ClaimEvaluation identity and must remain in the governed state basis."
        ),
    )


def test_real_pr11_2_evaluation_reaches_state_only_through_complete_portfolio(tmp_path) -> None:
    _, snapshot, evaluation, _, claim = _real_pr11_2_case(tmp_path)
    portfolio = _portfolio(snapshot, claim, as_of=evaluation.evaluated_at)

    state = derive_supported_state_from_complete_portfolio_v1(
        records=snapshot,
        frame=_frame(),
        portfolio=portfolio,
        request=_request(claim.claim_id, derived_at=portfolio.as_of),
    )

    reasoning = _reasoning(state)
    assert portfolio.admissible_evaluation_ids == (evaluation.evaluation_id,)
    assert reasoning.basis_evaluation_ids == (evaluation.evaluation_id,)
    assert reasoning.standing is DimensionStanding.INSUFFICIENT
    assert state.subject_ref == claim.subject_ref
    assert state.concept_ref == claim.concept_ref
    assert state.as_of == portfolio.as_of


def test_real_pr11_3_append_only_correction_expands_pr11_5_state_basis(tmp_path) -> None:
    _, snapshot, evaluation, _, claim = _real_pr11_2_case(tmp_path)
    correction = _correction(
        evaluation,
        evaluation_id="evaluation_multi_bounded_reasoning_pr11_5_correction",
        minutes=1,
    )
    successor = EpistemicRecordSet(
        evidence_records=snapshot.evidence_records,
        claims=snapshot.claims,
        evaluations=snapshot.evaluations + (correction,),
    )
    succession = validate_epistemic_snapshot_successor_v1(
        predecessor=snapshot,
        successor=successor,
    )
    assert succession.added_evaluation_ids == (correction.evaluation_id,)

    portfolio = _portfolio(successor, claim, as_of=correction.evaluated_at)
    state = derive_supported_state_from_complete_portfolio_v1(
        records=successor,
        frame=_frame(),
        portfolio=portfolio,
        request=_request(claim.claim_id, derived_at=portfolio.as_of),
    )

    assert portfolio.admissible_evaluation_ids == tuple(
        sorted((evaluation.evaluation_id, correction.evaluation_id))
    )
    assert _reasoning(state).basis_evaluation_ids == portfolio.admissible_evaluation_ids
    assert _reasoning(state).standing is DimensionStanding.INSUFFICIENT


def test_real_pre_append_portfolio_cannot_authorize_state_on_successor(tmp_path) -> None:
    _, snapshot, evaluation, _, claim = _real_pr11_2_case(tmp_path)
    old = _portfolio(
        snapshot,
        claim,
        as_of=evaluation.evaluated_at + timedelta(minutes=10),
    )
    correction = _correction(
        evaluation,
        evaluation_id="evaluation_multi_bounded_reasoning_pr11_5_stale",
        minutes=1,
    )
    successor = EpistemicRecordSet(
        evidence_records=snapshot.evidence_records,
        claims=snapshot.claims,
        evaluations=snapshot.evaluations + (correction,),
    )
    validate_epistemic_snapshot_successor_v1(
        predecessor=snapshot,
        successor=successor,
    )

    with pytest.raises(
        CompletePortfolioStateDerivationError,
        match="portfolio snapshot does not match supplied EpistemicRecordSet",
    ):
        derive_supported_state_from_complete_portfolio_v1(
            records=successor,
            frame=_frame(),
            portfolio=old,
            request=_request(claim.claim_id, derived_at=old.as_of),
        )


def test_real_historical_backfill_requires_rebuild_and_becomes_state_basis(tmp_path) -> None:
    _, snapshot, evaluation, _, claim = _real_pr11_2_case(tmp_path)
    historical_as_of = evaluation.evaluated_at + timedelta(minutes=10)
    old = _portfolio(snapshot, claim, as_of=historical_as_of)
    backfill = _correction(
        evaluation,
        evaluation_id="evaluation_multi_bounded_reasoning_pr11_5_backfill",
        minutes=5,
    )
    successor = EpistemicRecordSet(
        evidence_records=snapshot.evidence_records,
        claims=snapshot.claims,
        evaluations=snapshot.evaluations + (backfill,),
    )
    validate_epistemic_snapshot_successor_v1(
        predecessor=snapshot,
        successor=successor,
    )

    with pytest.raises(CompletePortfolioStateDerivationError):
        derive_supported_state_from_complete_portfolio_v1(
            records=successor,
            frame=_frame(),
            portfolio=old,
            request=_request(claim.claim_id, derived_at=old.as_of),
        )

    rebuilt = _portfolio(successor, claim, as_of=historical_as_of)
    state = derive_supported_state_from_complete_portfolio_v1(
        records=successor,
        frame=_frame(),
        portfolio=rebuilt,
        request=_request(claim.claim_id, derived_at=rebuilt.as_of),
    )
    assert _reasoning(state).basis_evaluation_ids == tuple(
        sorted((evaluation.evaluation_id, backfill.evaluation_id))
    )


def test_real_unevaluated_appended_claim_blocks_whole_governed_derivation(tmp_path) -> None:
    _, snapshot, evaluation, _, claim = _real_pr11_2_case(tmp_path)
    unevaluated = replace(
        claim,
        claim_id=CapabilityClaimId("claim_bounded_reasoning_pr11_5_unevaluated"),
        statement=claim.statement + " Unevaluated append for PR11.5 fail-closed coverage.",
    )
    successor = EpistemicRecordSet(
        evidence_records=snapshot.evidence_records,
        claims=snapshot.claims + (unevaluated,),
        evaluations=snapshot.evaluations,
    )
    validate_epistemic_snapshot_successor_v1(
        predecessor=snapshot,
        successor=successor,
    )
    portfolio = _portfolio(successor, claim, as_of=evaluation.evaluated_at)
    assert portfolio.unevaluated_claim_ids == (unevaluated.claim_id,)

    with pytest.raises(
        CompletePortfolioStateDerivationError,
        match=f"complete portfolio contains unevaluated claim: {unevaluated.claim_id}",
    ):
        derive_supported_state_from_complete_portfolio_v1(
            records=successor,
            frame=_frame(),
            portfolio=portfolio,
            request=_request(
                claim.claim_id,
                unevaluated.claim_id,
                derived_at=portfolio.as_of,
            ),
        )
