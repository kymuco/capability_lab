from dataclasses import replace
from datetime import timedelta

import pytest

from capability_lab.derivation import (
    ClaimDimensionBinding,
    CompletePortfolioStateDerivationRequest,
    derive_supported_state_from_complete_portfolio_v1,
)
from capability_lab.epistemics import (
    EpistemicRecordSet,
    validate_epistemic_snapshot_successor_v1,
)
from capability_lab.state import (
    InvalidPersonalCapabilityStateSetSuccessor,
    PersonalCapabilityStateId,
    PersonalCapabilityStateSet,
    validate_personal_capability_state_set_successor_v1,
)

from test_civilization_bootstrap_pilot_01_complete_portfolio_derivation_integration_v1 import (
    _correction,
    _frame,
    _portfolio,
    _reasoning,
)
from test_civilization_bootstrap_pilot_01_snapshot_succession_integration_v1 import (
    _real_pr11_2_case,
)


def _request(state_id: str, claim_id, *, derived_at):
    return CompletePortfolioStateDerivationRequest(
        state_id=PersonalCapabilityStateId(state_id),
        derived_at=derived_at,
        claim_dimension_bindings=(
            ClaimDimensionBinding(claim_id, ("reasoning",)),
        ),
    )


def _derive(records, claim, *, as_of, state_id: str, derived_at=None):
    portfolio = _portfolio(records, claim, as_of=as_of)
    state = derive_supported_state_from_complete_portfolio_v1(
        records=records,
        frame=_frame(),
        portfolio=portfolio,
        request=_request(
            state_id,
            claim.claim_id,
            derived_at=portfolio.as_of if derived_at is None else derived_at,
        ),
    )
    return portfolio, state


def test_real_pr11_5_state_can_enter_empty_state_history_under_fresh_identity(tmp_path) -> None:
    _, snapshot, evaluation, _, claim = _real_pr11_2_case(tmp_path)
    portfolio, state = _derive(
        snapshot,
        claim,
        as_of=evaluation.evaluated_at,
        state_id="state_pilot_01_pr11_6_initial",
    )

    predecessor = PersonalCapabilityStateSet(claim.subject_ref)
    successor = PersonalCapabilityStateSet(claim.subject_ref, (state,))
    receipt = validate_personal_capability_state_set_successor_v1(
        predecessor=predecessor,
        successor=successor,
    )

    assert receipt.added_state_ids == (state.state_id,)
    assert receipt.retained_state_ids == ()
    assert _reasoning(state).basis_evaluation_ids == portfolio.admissible_evaluation_ids


def test_real_correction_rebuilds_chain_and_appends_new_state_identity(tmp_path) -> None:
    _, snapshot, evaluation, _, claim = _real_pr11_2_case(tmp_path)
    _, state_a = _derive(
        snapshot,
        claim,
        as_of=evaluation.evaluated_at,
        state_id="state_pilot_01_pr11_6_a",
    )

    correction = _correction(
        evaluation,
        evaluation_id="evaluation_multi_bounded_reasoning_pr11_6_correction",
        minutes=1,
    )
    epistemic_successor = EpistemicRecordSet(
        evidence_records=snapshot.evidence_records,
        claims=snapshot.claims,
        evaluations=snapshot.evaluations + (correction,),
    )
    epistemic_receipt = validate_epistemic_snapshot_successor_v1(
        predecessor=snapshot,
        successor=epistemic_successor,
    )
    assert epistemic_receipt.added_evaluation_ids == (correction.evaluation_id,)

    portfolio_b, state_b = _derive(
        epistemic_successor,
        claim,
        as_of=correction.evaluated_at,
        state_id="state_pilot_01_pr11_6_b",
    )

    history_a = PersonalCapabilityStateSet(claim.subject_ref, (state_a,))
    history_b = PersonalCapabilityStateSet(claim.subject_ref, (state_a, state_b))
    state_receipt = validate_personal_capability_state_set_successor_v1(
        predecessor=history_a,
        successor=history_b,
    )

    assert state_receipt.retained_state_ids == (state_a.state_id,)
    assert state_receipt.added_state_ids == (state_b.state_id,)
    assert state_a in history_b.states
    assert _reasoning(state_b).basis_evaluation_ids == portfolio_b.admissible_evaluation_ids
    assert correction.evaluation_id in _reasoning(state_b).basis_evaluation_ids


def test_real_recomputed_state_content_cannot_overwrite_old_state_identity(tmp_path) -> None:
    _, snapshot, evaluation, _, claim = _real_pr11_2_case(tmp_path)
    _, state_a = _derive(
        snapshot,
        claim,
        as_of=evaluation.evaluated_at,
        state_id="state_pilot_01_pr11_6_overwrite",
    )

    correction = _correction(
        evaluation,
        evaluation_id="evaluation_multi_bounded_reasoning_pr11_6_overwrite",
        minutes=1,
    )
    epistemic_successor = EpistemicRecordSet(
        evidence_records=snapshot.evidence_records,
        claims=snapshot.claims,
        evaluations=snapshot.evaluations + (correction,),
    )
    validate_epistemic_snapshot_successor_v1(
        predecessor=snapshot,
        successor=epistemic_successor,
    )
    _, state_b = _derive(
        epistemic_successor,
        claim,
        as_of=correction.evaluated_at,
        state_id="state_pilot_01_pr11_6_fresh_temp",
    )
    illegal_overwrite = replace(state_b, state_id=state_a.state_id)

    with pytest.raises(
        InvalidPersonalCapabilityStateSetSuccessor,
        match=f"may not mutate retained state: {state_a.state_id}",
    ):
        validate_personal_capability_state_set_successor_v1(
            predecessor=PersonalCapabilityStateSet(claim.subject_ref, (state_a,)),
            successor=PersonalCapabilityStateSet(
                claim.subject_ref,
                (illegal_overwrite,),
            ),
        )


def test_real_new_state_identity_does_not_authorize_deleting_old_history(tmp_path) -> None:
    _, snapshot, evaluation, _, claim = _real_pr11_2_case(tmp_path)
    _, state_a = _derive(
        snapshot,
        claim,
        as_of=evaluation.evaluated_at,
        state_id="state_pilot_01_pr11_6_retained",
    )
    _, state_b = _derive(
        snapshot,
        claim,
        as_of=evaluation.evaluated_at,
        state_id="state_pilot_01_pr11_6_replacement",
        derived_at=evaluation.evaluated_at + timedelta(minutes=5),
    )

    with pytest.raises(
        InvalidPersonalCapabilityStateSetSuccessor,
        match=f"may not remove persisted state: {state_a.state_id}",
    ):
        validate_personal_capability_state_set_successor_v1(
            predecessor=PersonalCapabilityStateSet(claim.subject_ref, (state_a,)),
            successor=PersonalCapabilityStateSet(claim.subject_ref, (state_b,)),
        )


def test_real_historical_reconstruction_can_be_appended_after_later_state(tmp_path) -> None:
    _, snapshot, evaluation, _, claim = _real_pr11_2_case(tmp_path)
    later_as_of = evaluation.evaluated_at + timedelta(minutes=10)
    _, later_state = _derive(
        snapshot,
        claim,
        as_of=later_as_of,
        state_id="state_pilot_01_pr11_6_later",
        derived_at=later_as_of,
    )
    _, historical_state = _derive(
        snapshot,
        claim,
        as_of=evaluation.evaluated_at,
        state_id="state_pilot_01_pr11_6_historical",
        derived_at=later_as_of + timedelta(minutes=10),
    )

    receipt = validate_personal_capability_state_set_successor_v1(
        predecessor=PersonalCapabilityStateSet(claim.subject_ref, (later_state,)),
        successor=PersonalCapabilityStateSet(
            claim.subject_ref,
            (later_state, historical_state),
        ),
    )

    assert historical_state.as_of < later_state.as_of
    assert historical_state.derived_at > later_state.derived_at
    assert receipt.retained_state_ids == (later_state.state_id,)
    assert receipt.added_state_ids == (historical_state.state_id,)
