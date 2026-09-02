from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from capability_lab.epistemics import CapabilityClaimId, CapabilitySubjectRef, ClaimEvaluationId
from capability_lab.semantics import CapabilityConceptRef
from capability_lab.state import (
    CompetenceDimensionState,
    CompetenceFrameRef,
    DimensionConflictStatus,
    DimensionStanding,
    InvalidPersonalCapabilityStateAcceptanceSet,
    PersonalCapabilityState,
    PersonalCapabilityStateAcceptanceAdmission,
    PersonalCapabilityStateAcceptanceRequest,
    PersonalCapabilityStateAcceptanceSet,
    PersonalCapabilityStateId,
    PersonalCapabilityStateSet,
    StateAcceptanceMechanismKind,
    StateAcceptancePolicyRef,
    StateAccepterRef,
    StateDerivationPolicyRef,
    StateDeriverKind,
    StateDeriverRef,
    accept_persisted_personal_capability_state_v1,
    personal_capability_state_acceptance_set_sha256_v1,
    validate_personal_capability_state_acceptance_set_successor_v1,
)


T0 = datetime(2026, 8, 22, 10, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("alice_pr11_8_acceptance_set")
CONCEPT = CapabilityConceptRef.parse("core:current_selection_capability@1")
FRAME = CompetenceFrameRef.parse("core:current_selection_frame@1")
DERIVATION_POLICY = StateDerivationPolicyRef.parse("core:current_selection_derivation@1")
DERIVER = StateDeriverRef(StateDeriverKind.RULE, "current_selection_deriver")
ACCEPTANCE_POLICY = StateAcceptancePolicyRef.parse("core:current_selection_acceptance@1")
ACCEPTER = StateAccepterRef(StateAcceptanceMechanismKind.HUMAN, "alice_reviewer")
CLAIM = CapabilityClaimId("claim_pr11_8_acceptance_set")
EVALUATION = ClaimEvaluationId("evaluation_pr11_8_acceptance_set")


def _state(state_id: str, *, minutes: int = 1) -> PersonalCapabilityState:
    return PersonalCapabilityState(
        state_id=PersonalCapabilityStateId(state_id),
        subject_ref=SUBJECT,
        concept_ref=CONCEPT,
        frame_ref=FRAME,
        derivation_policy_ref=DERIVATION_POLICY,
        deriver_ref=DERIVER,
        as_of=T0,
        derived_at=T0 + timedelta(minutes=minutes),
        dimensions=(
            CompetenceDimensionState(
                dimension_key="execution",
                standing=DimensionStanding.SUPPORTED,
                supported_claim_ids=(CLAIM,),
                basis_evaluation_ids=(EVALUATION,),
                rationale="Exact PR11.8 acceptance-set fixture.",
                conflict_status=DimensionConflictStatus.NONE,
            ),
        ),
        rationale="Exact PR11.8 state fixture.",
    )


def _request(state: PersonalCapabilityState, *, accepted_minutes: int):
    return PersonalCapabilityStateAcceptanceRequest(
        state_id=state.state_id,
        acceptance_policy_ref=ACCEPTANCE_POLICY,
        accepter_ref=ACCEPTER,
        accepted_at=T0 + timedelta(minutes=accepted_minutes),
        rationale="Explicit PR11.8 acceptance-set admission.",
    )


def _issued(
    state: PersonalCapabilityState,
    *,
    predecessor: PersonalCapabilityStateSet,
    successor: PersonalCapabilityStateSet,
    accepted_minutes: int,
):
    acceptance = accept_persisted_personal_capability_state_v1(
        predecessor=predecessor,
        successor=successor,
        request=_request(state, accepted_minutes=accepted_minutes),
    )
    admission = PersonalCapabilityStateAcceptanceAdmission(
        acceptance=acceptance,
        persistence_predecessor=predecessor,
        persistence_successor=successor,
    )
    return acceptance, admission


def _fixture_two():
    state_a = _state("state_a", minutes=1)
    state_b = _state("state_b", minutes=3)
    empty_states = PersonalCapabilityStateSet(SUBJECT)
    states_a = PersonalCapabilityStateSet(SUBJECT, (state_a,))
    states_ab = PersonalCapabilityStateSet(SUBJECT, (state_a, state_b))
    acceptance_a, admission_a = _issued(
        state_a,
        predecessor=empty_states,
        successor=states_a,
        accepted_minutes=2,
    )
    acceptance_b, admission_b = _issued(
        state_b,
        predecessor=states_a,
        successor=states_ab,
        accepted_minutes=4,
    )
    return states_ab, acceptance_a, admission_a, acceptance_b, admission_b


def test_acceptance_set_canonicalizes_order_without_latest_wins() -> None:
    _, acceptance_a, _, acceptance_b, _ = _fixture_two()
    value = PersonalCapabilityStateAcceptanceSet(
        SUBJECT,
        (acceptance_b, acceptance_a),
    )
    assert set(value.acceptances) == {acceptance_a, acceptance_b}
    assert value.acceptances != (acceptance_b, acceptance_a)


def test_acceptance_set_rejects_duplicate_exact_acceptance_fact() -> None:
    _, acceptance_a, _, _, _ = _fixture_two()
    with pytest.raises(
        InvalidPersonalCapabilityStateAcceptanceSet,
        match="duplicate acceptance facts",
    ):
        PersonalCapabilityStateAcceptanceSet(
            SUBJECT,
            (acceptance_a, acceptance_a),
        )


def test_acceptance_set_hash_is_independent_of_unrelated_state_append() -> None:
    states_ab, acceptance_a, _, _, _ = _fixture_two()
    set_a = PersonalCapabilityStateAcceptanceSet(SUBJECT, (acceptance_a,))
    hash_ab = personal_capability_state_acceptance_set_sha256_v1(
        state_snapshot=states_ab,
        acceptance_set=set_a,
    )
    state_c = _state("state_c", minutes=7)
    states_abc = PersonalCapabilityStateSet(
        SUBJECT,
        states_ab.states + (state_c,),
    )
    hash_abc = personal_capability_state_acceptance_set_sha256_v1(
        state_snapshot=states_abc,
        acceptance_set=set_a,
    )
    assert hash_ab == hash_abc


def test_empty_to_two_acceptances_requires_exact_fresh_admissions() -> None:
    states_ab, acceptance_a, admission_a, acceptance_b, admission_b = _fixture_two()
    predecessor = PersonalCapabilityStateAcceptanceSet(SUBJECT)
    successor = PersonalCapabilityStateAcceptanceSet(
        SUBJECT,
        (acceptance_a, acceptance_b),
    )
    receipt = validate_personal_capability_state_acceptance_set_successor_v1(
        state_snapshot=states_ab,
        predecessor=predecessor,
        successor=successor,
        admissions=(admission_b, admission_a),
    )
    assert receipt.validator_issued is True
    assert set(receipt.added_acceptances) == {acceptance_a, acceptance_b}
    assert receipt.retained_acceptances == ()


def test_new_acceptance_without_pr11_7_admission_replay_is_rejected() -> None:
    states_ab, acceptance_a, admission_a, acceptance_b, _ = _fixture_two()
    predecessor = PersonalCapabilityStateAcceptanceSet(SUBJECT)
    successor = PersonalCapabilityStateAcceptanceSet(
        SUBJECT,
        (acceptance_a, acceptance_b),
    )
    with pytest.raises(
        InvalidPersonalCapabilityStateAcceptanceSet,
        match="requires fresh PR11.7 issuance-basis admission",
    ):
        validate_personal_capability_state_acceptance_set_successor_v1(
            state_snapshot=states_ab,
            predecessor=predecessor,
            successor=successor,
            admissions=(admission_a,),
        )


def test_unrelated_extra_admission_is_rejected() -> None:
    states_ab, acceptance_a, admission_a, _, admission_b = _fixture_two()
    predecessor = PersonalCapabilityStateAcceptanceSet(SUBJECT)
    successor = PersonalCapabilityStateAcceptanceSet(SUBJECT, (acceptance_a,))
    with pytest.raises(
        InvalidPersonalCapabilityStateAcceptanceSet,
        match="newly added",
    ):
        validate_personal_capability_state_acceptance_set_successor_v1(
            state_snapshot=states_ab,
            predecessor=predecessor,
            successor=successor,
            admissions=(admission_a, admission_b),
        )


def test_acceptance_set_successor_may_append_but_not_remove_a() -> None:
    states_ab, acceptance_a, admission_a, acceptance_b, admission_b = _fixture_two()
    empty = PersonalCapabilityStateAcceptanceSet(SUBJECT)
    only_a = PersonalCapabilityStateAcceptanceSet(SUBJECT, (acceptance_a,))
    both = PersonalCapabilityStateAcceptanceSet(SUBJECT, (acceptance_a, acceptance_b))
    validate_personal_capability_state_acceptance_set_successor_v1(
        state_snapshot=states_ab,
        predecessor=empty,
        successor=only_a,
        admissions=(admission_a,),
    )
    validate_personal_capability_state_acceptance_set_successor_v1(
        state_snapshot=states_ab,
        predecessor=only_a,
        successor=both,
        admissions=(admission_b,),
    )
    with pytest.raises(
        InvalidPersonalCapabilityStateAcceptanceSet,
        match="may not remove",
    ):
        validate_personal_capability_state_acceptance_set_successor_v1(
            state_snapshot=states_ab,
            predecessor=both,
            successor=only_a,
        )


def test_retained_acceptance_uses_durable_binding_after_later_state_append() -> None:
    states_ab, acceptance_a, admission_a, _, _ = _fixture_two()
    empty = PersonalCapabilityStateAcceptanceSet(SUBJECT)
    only_a = PersonalCapabilityStateAcceptanceSet(SUBJECT, (acceptance_a,))
    validate_personal_capability_state_acceptance_set_successor_v1(
        state_snapshot=states_ab,
        predecessor=empty,
        successor=only_a,
        admissions=(admission_a,),
    )
    state_c = _state("state_c", minutes=8)
    states_abc = PersonalCapabilityStateSet(SUBJECT, states_ab.states + (state_c,))
    receipt = validate_personal_capability_state_acceptance_set_successor_v1(
        state_snapshot=states_abc,
        predecessor=only_a,
        successor=only_a,
    )
    assert receipt.retained_acceptances == (acceptance_a,)
    assert receipt.added_acceptances == ()


def test_tampered_accepted_state_digest_is_rejected_by_set_hash() -> None:
    states_ab, acceptance_a, _, _, _ = _fixture_two()
    forged = replace(acceptance_a, accepted_state_sha256="0" * 64)
    forged_set = PersonalCapabilityStateAcceptanceSet(SUBJECT, (forged,))
    with pytest.raises(
        InvalidPersonalCapabilityStateAcceptanceSet,
        match="does not match exact persisted state content",
    ):
        personal_capability_state_acceptance_set_sha256_v1(
            state_snapshot=states_ab,
            acceptance_set=forged_set,
        )


def test_wrong_pr11_7_issuance_basis_is_rejected_on_admission() -> None:
    states_ab, acceptance_a, _, _, _ = _fixture_two()
    wrong = PersonalCapabilityStateAcceptanceAdmission(
        acceptance=acceptance_a,
        persistence_predecessor=states_ab,
        persistence_successor=states_ab,
    )
    with pytest.raises(InvalidPersonalCapabilityStateAcceptanceSet):
        validate_personal_capability_state_acceptance_set_successor_v1(
            state_snapshot=states_ab,
            predecessor=PersonalCapabilityStateAcceptanceSet(SUBJECT),
            successor=PersonalCapabilityStateAcceptanceSet(SUBJECT, (acceptance_a,)),
            admissions=(wrong,),
        )


def test_acceptance_set_is_subject_scoped() -> None:
    _, acceptance_a, _, _, _ = _fixture_two()
    with pytest.raises(
        InvalidPersonalCapabilityStateAcceptanceSet,
        match="acceptance set subject",
    ):
        PersonalCapabilityStateAcceptanceSet(
            CapabilitySubjectRef("bob_pr11_8"),
            (acceptance_a,),
        )
