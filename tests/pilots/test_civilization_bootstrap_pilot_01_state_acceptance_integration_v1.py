from datetime import timedelta

from capability_lab.epistemics import EpistemicRecordSet, validate_epistemic_snapshot_successor_v1
from capability_lab.state import (
    PersonalCapabilityStateAcceptanceRequest,
    PersonalCapabilityStateSet,
    StateAcceptanceMechanismKind,
    StateAcceptancePolicyRef,
    StateAccepterRef,
    accept_persisted_personal_capability_state_v1,
    personal_capability_state_content_sha256_v1,
    validate_personal_capability_state_acceptance_binding_v1,
    validate_personal_capability_state_acceptance_v1,
    validate_personal_capability_state_set_successor_v1,
)

from test_civilization_bootstrap_pilot_01_complete_portfolio_derivation_integration_v1 import (
    _correction,
    _reasoning,
)
from test_civilization_bootstrap_pilot_01_snapshot_succession_integration_v1 import (
    _real_pr11_2_case,
)
from test_civilization_bootstrap_pilot_01_state_snapshot_succession_integration_v1 import (
    _derive,
)


POLICY = StateAcceptancePolicyRef.parse("pilot:governed_state_acceptance@1")
ACCEPTER = StateAccepterRef(
    StateAcceptanceMechanismKind.HUMAN,
    "civilization_bootstrap_pilot_reviewer",
)


def _acceptance_request(state, *, accepted_at=None):
    return PersonalCapabilityStateAcceptanceRequest(
        state_id=state.state_id,
        acceptance_policy_ref=POLICY,
        accepter_ref=ACCEPTER,
        accepted_at=accepted_at or state.derived_at + timedelta(minutes=1),
        rationale="Pilot explicitly accepts this exact persisted state for governance use.",
    )


def _derive_initial(tmp_path, state_id):
    _, snapshot, evaluation, _, claim = _real_pr11_2_case(tmp_path)
    portfolio, state = _derive(
        snapshot,
        claim,
        as_of=evaluation.evaluated_at,
        state_id=state_id,
    )
    return snapshot, evaluation, claim, portfolio, state


def _derive_correction(snapshot, evaluation, claim, *, suffix, state_id):
    correction = _correction(
        evaluation,
        evaluation_id=f"evaluation_multi_bounded_reasoning_pr11_7_{suffix}",
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
    portfolio, state = _derive(
        epistemic_successor,
        claim,
        as_of=correction.evaluated_at,
        state_id=state_id,
    )
    return correction, epistemic_successor, portfolio, state


def test_real_pr11_5_state_is_explicitly_accepted_only_after_pr11_6_persistence(tmp_path) -> None:
    _, _, claim, portfolio, state = _derive_initial(
        tmp_path,
        "state_pilot_01_pr11_7_initial",
    )
    predecessor = PersonalCapabilityStateSet(claim.subject_ref)
    successor = PersonalCapabilityStateSet(claim.subject_ref, (state,))
    validate_personal_capability_state_set_successor_v1(
        predecessor=predecessor,
        successor=successor,
    )

    acceptance = accept_persisted_personal_capability_state_v1(
        predecessor=predecessor,
        successor=successor,
        request=_acceptance_request(state),
    )

    assert acceptance.state_id == state.state_id
    assert acceptance.subject_ref == claim.subject_ref
    assert _reasoning(state).basis_evaluation_ids == portfolio.admissible_evaluation_ids
    assert validate_personal_capability_state_acceptance_v1(
        predecessor=predecessor,
        successor=successor,
        acceptance=acceptance,
    ) is acceptance


def test_real_correction_appends_state_b_without_auto_accepting_or_invalidating_a(tmp_path) -> None:
    snapshot, evaluation, claim, _, state_a = _derive_initial(
        tmp_path,
        "state_pilot_01_pr11_7_a",
    )
    history_a = PersonalCapabilityStateSet(claim.subject_ref, (state_a,))
    empty = PersonalCapabilityStateSet(claim.subject_ref)
    acceptance_a = accept_persisted_personal_capability_state_v1(
        predecessor=empty,
        successor=history_a,
        request=_acceptance_request(state_a),
    )

    correction, _, portfolio_b, state_b = _derive_correction(
        snapshot,
        evaluation,
        claim,
        suffix="correction",
        state_id="state_pilot_01_pr11_7_b",
    )
    history_b = PersonalCapabilityStateSet(claim.subject_ref, (state_a, state_b))
    receipt = validate_personal_capability_state_set_successor_v1(
        predecessor=history_a,
        successor=history_b,
    )

    assert receipt.added_state_ids == (state_b.state_id,)
    assert acceptance_a.state_id == state_a.state_id
    assert acceptance_a.state_id != state_b.state_id
    assert acceptance_a.accepted_state_sha256 == personal_capability_state_content_sha256_v1(
        snapshot=history_b,
        state_id=state_a.state_id,
    )
    assert validate_personal_capability_state_acceptance_binding_v1(
        snapshot=history_b,
        acceptance=acceptance_a,
    ) is acceptance_a
    assert correction.evaluation_id in _reasoning(state_b).basis_evaluation_ids
    assert _reasoning(state_b).basis_evaluation_ids == portfolio_b.admissible_evaluation_ids


def test_real_state_b_requires_its_own_explicit_acceptance(tmp_path) -> None:
    snapshot, evaluation, claim, _, state_a = _derive_initial(
        tmp_path,
        "state_pilot_01_pr11_7_explicit_a",
    )
    _, _, _, state_b = _derive_correction(
        snapshot,
        evaluation,
        claim,
        suffix="explicit_b",
        state_id="state_pilot_01_pr11_7_explicit_b",
    )
    history_a = PersonalCapabilityStateSet(claim.subject_ref, (state_a,))
    history_b = PersonalCapabilityStateSet(claim.subject_ref, (state_a, state_b))

    acceptance_b = accept_persisted_personal_capability_state_v1(
        predecessor=history_a,
        successor=history_b,
        request=_acceptance_request(state_b),
    )

    assert acceptance_b.state_id == state_b.state_id
    assert acceptance_b.accepted_state_sha256 == personal_capability_state_content_sha256_v1(
        snapshot=history_b,
        state_id=state_b.state_id,
    )
    assert acceptance_b.state_id != state_a.state_id


def test_real_retained_state_can_receive_delayed_acceptance_after_new_state_append(
    tmp_path,
) -> None:
    snapshot, evaluation, claim, _, state_a = _derive_initial(
        tmp_path,
        "state_pilot_01_pr11_7_delayed_a",
    )
    _, _, _, state_b = _derive_correction(
        snapshot,
        evaluation,
        claim,
        suffix="delayed_b",
        state_id="state_pilot_01_pr11_7_delayed_b",
    )
    history_a = PersonalCapabilityStateSet(claim.subject_ref, (state_a,))
    history_b = PersonalCapabilityStateSet(claim.subject_ref, (state_a, state_b))

    acceptance_a = accept_persisted_personal_capability_state_v1(
        predecessor=history_a,
        successor=history_b,
        request=_acceptance_request(
            state_a,
            accepted_at=state_b.derived_at + timedelta(minutes=1),
        ),
    )

    assert acceptance_a.state_id == state_a.state_id
    assert validate_personal_capability_state_acceptance_binding_v1(
        snapshot=history_b,
        acceptance=acceptance_a,
    ) is acceptance_a


def test_real_multiple_accepted_states_still_create_no_current_or_progression_authority(
    tmp_path,
) -> None:
    snapshot, evaluation, claim, _, state_a = _derive_initial(
        tmp_path,
        "state_pilot_01_pr11_7_multi_a",
    )
    _, _, _, state_b = _derive_correction(
        snapshot,
        evaluation,
        claim,
        suffix="multi_b",
        state_id="state_pilot_01_pr11_7_multi_b",
    )
    history_a = PersonalCapabilityStateSet(claim.subject_ref, (state_a,))
    history_b = PersonalCapabilityStateSet(claim.subject_ref, (state_a, state_b))

    acceptance_a = accept_persisted_personal_capability_state_v1(
        predecessor=history_a,
        successor=history_b,
        request=_acceptance_request(
            state_a,
            accepted_at=state_b.derived_at + timedelta(minutes=1),
        ),
    )
    acceptance_b = accept_persisted_personal_capability_state_v1(
        predecessor=history_a,
        successor=history_b,
        request=_acceptance_request(
            state_b,
            accepted_at=state_b.derived_at + timedelta(minutes=2),
        ),
    )

    assert {acceptance_a.state_id, acceptance_b.state_id} == {
        state_a.state_id,
        state_b.state_id,
    }
    for acceptance in (acceptance_a, acceptance_b):
        assert not hasattr(acceptance, "current_state_id")
        assert not hasattr(acceptance, "preferred_state_id")
        assert not hasattr(acceptance, "supersedes_state_id")
        assert not hasattr(acceptance, "progression_state_id")
