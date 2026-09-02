from dataclasses import fields, replace
from datetime import datetime, timedelta, timezone
import inspect

import pytest

from capability_lab.epistemics import CapabilityClaimId, CapabilitySubjectRef, ClaimEvaluationId
from capability_lab.semantics import CapabilityConceptRef
from capability_lab.state import (
    CompetenceDimensionState,
    CompetenceFrameRef,
    DimensionConflictStatus,
    DimensionStanding,
    InvalidPersonalCapabilityStateAcceptance,
    PersonalCapabilityState,
    PersonalCapabilityStateAcceptance,
    PersonalCapabilityStateAcceptanceRequest,
    PersonalCapabilityStateId,
    PersonalCapabilityStateSet,
    StateAcceptanceMechanismKind,
    StateAcceptancePolicyRef,
    StateAccepterRef,
    StateDerivationPolicyRef,
    StateDeriverKind,
    StateDeriverRef,
    accept_persisted_personal_capability_state_v1,
    personal_capability_state_content_sha256_v1,
    validate_personal_capability_state_acceptance_binding_v1,
    validate_personal_capability_state_acceptance_v1,
    validate_personal_capability_state_set_successor_v1,
)


T0 = datetime(2026, 8, 21, 10, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("alice_pr11_7")
CONCEPT = CapabilityConceptRef.parse("core:state_acceptance_capability@1")
FRAME = CompetenceFrameRef.parse("core:state_acceptance_frame@1")
DERIVATION_POLICY = StateDerivationPolicyRef.parse("core:state_acceptance_derivation@1")
DERIVER = StateDeriverRef(StateDeriverKind.RULE, "state_acceptance_deriver")
ACCEPTANCE_POLICY = StateAcceptancePolicyRef.parse("core:state_acceptance@1")
ACCEPTER = StateAccepterRef(StateAcceptanceMechanismKind.HUMAN, "alice_reviewer")
CLAIM_A = CapabilityClaimId("claim_acceptance_a")
CLAIM_B = CapabilityClaimId("claim_acceptance_b")
EVAL_A = ClaimEvaluationId("evaluation_acceptance_a")
EVAL_B = ClaimEvaluationId("evaluation_acceptance_b")


def _dimension(
    *,
    standing=DimensionStanding.SUPPORTED,
    conflict=DimensionConflictStatus.NONE,
    claims=(CLAIM_A,),
    evaluations=(EVAL_A,),
    rationale="Governed acceptance dimension fixture.",
):
    return CompetenceDimensionState(
        dimension_key="execution",
        standing=standing,
        supported_claim_ids=claims,
        basis_evaluation_ids=evaluations,
        rationale=rationale,
        conflict_status=conflict,
    )


def _state(
    state_id="state_a",
    *,
    dimensions=None,
    as_of=T0,
    derived_at=T0 + timedelta(minutes=1),
    rationale="PR11.7 acceptance fixture.",
):
    return PersonalCapabilityState(
        state_id=PersonalCapabilityStateId(state_id),
        subject_ref=SUBJECT,
        concept_ref=CONCEPT,
        frame_ref=FRAME,
        derivation_policy_ref=DERIVATION_POLICY,
        deriver_ref=DERIVER,
        as_of=as_of,
        derived_at=derived_at,
        dimensions=dimensions or (_dimension(),),
        rationale=rationale,
    )


def _set(*states):
    return PersonalCapabilityStateSet(SUBJECT, states)


def _request(state, *, accepted_at=None, policy=ACCEPTANCE_POLICY, accepter=ACCEPTER):
    return PersonalCapabilityStateAcceptanceRequest(
        state_id=state.state_id,
        acceptance_policy_ref=policy,
        accepter_ref=accepter,
        accepted_at=accepted_at or state.derived_at + timedelta(minutes=1),
        rationale="Explicit governed acceptance for this exact persisted state.",
    )


def _accept(state, *, predecessor=None, successor=None, request=None):
    predecessor = predecessor or PersonalCapabilityStateSet(SUBJECT)
    successor = successor or _set(state)
    return accept_persisted_personal_capability_state_v1(
        predecessor=predecessor,
        successor=successor,
        request=request or _request(state),
    )


def test_acceptance_policy_ref_parse_roundtrip() -> None:
    policy = StateAcceptancePolicyRef.parse("core.review:manual_acceptance@2")
    assert str(policy) == "core.review:manual_acceptance@2"


def test_acceptance_request_normalizes_time_and_rationale() -> None:
    state = _state()
    request = PersonalCapabilityStateAcceptanceRequest(
        state_id=state.state_id,
        acceptance_policy_ref=ACCEPTANCE_POLICY,
        accepter_ref=ACCEPTER,
        accepted_at=datetime(
            2026, 8, 21, 16, 2, tzinfo=timezone(timedelta(hours=6))
        ),
        rationale="  Explicit acceptance.  ",
    )
    assert request.accepted_at == datetime(2026, 8, 21, 10, 2, tzinfo=timezone.utc)
    assert request.accepted_at.tzinfo is timezone.utc
    assert request.rationale == "Explicit acceptance."


def test_state_content_hash_is_stable_across_unrelated_later_append() -> None:
    state_a = _state("state_a")
    state_b = _state("state_b", derived_at=T0 + timedelta(minutes=5))
    first = personal_capability_state_content_sha256_v1(
        snapshot=_set(state_a), state_id=state_a.state_id
    )
    second = personal_capability_state_content_sha256_v1(
        snapshot=_set(state_a, state_b), state_id=state_a.state_id
    )
    assert first == second


def test_state_content_hash_binds_state_identity_as_material_content() -> None:
    state_a = _state("state_a")
    state_b = replace(state_a, state_id=PersonalCapabilityStateId("state_b"))
    assert personal_capability_state_content_sha256_v1(
        snapshot=_set(state_a), state_id=state_a.state_id
    ) != personal_capability_state_content_sha256_v1(
        snapshot=_set(state_b), state_id=state_b.state_id
    )


def test_state_content_hash_rejects_absent_state() -> None:
    with pytest.raises(
        InvalidPersonalCapabilityStateAcceptance,
        match="absent from successor snapshot",
    ):
        personal_capability_state_content_sha256_v1(
            snapshot=PersonalCapabilityStateSet(SUBJECT),
            state_id=PersonalCapabilityStateId("missing"),
        )


def test_explicit_acceptance_of_newly_appended_state_binds_fresh_pr11_6_basis() -> None:
    state = _state()
    predecessor = PersonalCapabilityStateSet(SUBJECT)
    successor = _set(state)
    succession = validate_personal_capability_state_set_successor_v1(
        predecessor=predecessor,
        successor=successor,
    )
    acceptance = _accept(state, predecessor=predecessor, successor=successor)
    assert acceptance.subject_ref == SUBJECT
    assert acceptance.state_id == state.state_id
    assert acceptance.persistence_predecessor_sha256 == succession.predecessor_sha256
    assert acceptance.persistence_successor_sha256 == succession.successor_sha256
    assert acceptance.accepted_state_sha256 == personal_capability_state_content_sha256_v1(
        snapshot=successor, state_id=state.state_id
    )


def test_retained_state_can_be_accepted_after_newer_state_is_appended() -> None:
    state_a = _state("state_a")
    state_b = _state("state_b", derived_at=T0 + timedelta(minutes=5))
    predecessor = _set(state_a)
    successor = _set(state_a, state_b)
    acceptance = _accept(
        state_a,
        predecessor=predecessor,
        successor=successor,
        request=_request(state_a, accepted_at=T0 + timedelta(minutes=6)),
    )
    assert acceptance.state_id == state_a.state_id


def test_acceptance_binding_survives_unrelated_later_state_append() -> None:
    state_a = _state("state_a")
    state_b = _state("state_b", derived_at=T0 + timedelta(minutes=5))
    acceptance_a = _accept(state_a)
    later_snapshot = _set(state_a, state_b)
    assert validate_personal_capability_state_acceptance_binding_v1(
        snapshot=later_snapshot,
        acceptance=acceptance_a,
    ) is acceptance_a


def test_noop_persistence_basis_can_support_delayed_acceptance() -> None:
    state = _state()
    snapshot = _set(state)
    acceptance = _accept(
        state,
        predecessor=snapshot,
        successor=snapshot,
        request=_request(state, accepted_at=T0 + timedelta(days=1)),
    )
    assert acceptance.persistence_predecessor_sha256 == acceptance.persistence_successor_sha256


def test_state_must_exist_in_validated_successor() -> None:
    missing = _state("missing")
    empty = PersonalCapabilityStateSet(SUBJECT)
    with pytest.raises(
        InvalidPersonalCapabilityStateAcceptance,
        match="absent from successor snapshot",
    ):
        accept_persisted_personal_capability_state_v1(
            predecessor=empty,
            successor=empty,
            request=_request(missing),
        )


def test_acceptance_time_must_not_precede_state_derivation() -> None:
    state = _state()
    with pytest.raises(
        InvalidPersonalCapabilityStateAcceptance,
        match="must not precede the accepted state's derived_at",
    ):
        _accept(state, request=_request(state, accepted_at=state.derived_at - timedelta(seconds=1)))


def test_acceptance_at_exact_derivation_time_is_allowed() -> None:
    state = _state()
    acceptance = _accept(state, request=_request(state, accepted_at=state.derived_at))
    assert acceptance.accepted_at == state.derived_at


def test_existing_acceptance_revalidates_against_exact_same_basis() -> None:
    state = _state()
    predecessor = PersonalCapabilityStateSet(SUBJECT)
    successor = _set(state)
    acceptance = _accept(state, predecessor=predecessor, successor=successor)
    assert validate_personal_capability_state_acceptance_v1(
        predecessor=predecessor,
        successor=successor,
        acceptance=acceptance,
    ) is acceptance


def test_acceptance_record_with_wrong_state_digest_is_rejected_on_revalidation() -> None:
    state = _state()
    predecessor = PersonalCapabilityStateSet(SUBJECT)
    successor = _set(state)
    acceptance = _accept(state, predecessor=predecessor, successor=successor)
    forged = replace(acceptance, accepted_state_sha256="0" * 64)
    with pytest.raises(
        InvalidPersonalCapabilityStateAcceptance,
        match="does not match exact persisted state content",
    ):
        validate_personal_capability_state_acceptance_v1(
            predecessor=predecessor,
            successor=successor,
            acceptance=forged,
        )


def test_acceptance_record_with_wrong_persistence_hash_is_rejected() -> None:
    state = _state()
    predecessor = PersonalCapabilityStateSet(SUBJECT)
    successor = _set(state)
    acceptance = _accept(state, predecessor=predecessor, successor=successor)
    forged = replace(acceptance, persistence_successor_sha256="0" * 64)
    with pytest.raises(
        InvalidPersonalCapabilityStateAcceptance,
        match="successor hash does not match freshly validated PR11.6 basis",
    ):
        validate_personal_capability_state_acceptance_v1(
            predecessor=predecessor,
            successor=successor,
            acceptance=forged,
        )


def test_unknown_state_can_be_governance_accepted_without_becoming_positive_claim() -> None:
    state = _state(
        "state_unknown",
        dimensions=(
            _dimension(
                standing=DimensionStanding.UNKNOWN,
                claims=(),
                evaluations=(),
                rationale="No sufficient evidence at this boundary.",
            ),
        ),
    )
    acceptance = _accept(state)
    assert acceptance.state_id == state.state_id


def test_insufficient_state_can_be_governance_accepted() -> None:
    state = _state(
        "state_insufficient",
        dimensions=(
            _dimension(
                standing=DimensionStanding.INSUFFICIENT,
                claims=(),
                evaluations=(EVAL_A,),
            ),
        ),
    )
    assert _accept(state).state_id == state.state_id


def test_unresolved_conflict_state_can_be_governance_accepted() -> None:
    state = _state(
        "state_conflict",
        dimensions=(
            _dimension(
                standing=DimensionStanding.SUPPORTED,
                conflict=DimensionConflictStatus.UNRESOLVED,
            ),
        ),
    )
    assert _accept(state).state_id == state.state_id


def test_same_state_can_have_distinct_acceptances_without_aggregation_semantics() -> None:
    state = _state()
    first = _accept(state)
    second = _accept(
        state,
        request=_request(
            state,
            accepted_at=T0 + timedelta(minutes=4),
            policy=StateAcceptancePolicyRef.parse("core:secondary_acceptance@1"),
            accepter=StateAccepterRef(StateAcceptanceMechanismKind.RULE, "acceptance_rule"),
        ),
    )
    assert first.accepted_state_sha256 == second.accepted_state_sha256
    assert first.acceptance_policy_ref != second.acceptance_policy_ref
    assert first.accepter_ref != second.accepter_ref


def test_acceptance_of_a_does_not_propagate_to_fresh_state_b() -> None:
    state_a = _state("state_a")
    state_b = _state(
        "state_b",
        dimensions=(
            _dimension(
                claims=(CLAIM_A, CLAIM_B),
                evaluations=(EVAL_A, EVAL_B),
            ),
        ),
        derived_at=T0 + timedelta(minutes=5),
    )
    acceptance_a = _accept(state_a)
    assert acceptance_a.state_id != state_b.state_id
    assert acceptance_a.accepted_state_sha256 != personal_capability_state_content_sha256_v1(
        snapshot=_set(state_a, state_b), state_id=state_b.state_id
    )


def test_multiple_accepted_states_create_no_current_or_preferred_selection() -> None:
    state_a = _state("state_a")
    state_b = _state("state_b", derived_at=T0 + timedelta(minutes=5))
    acceptance_a = _accept(state_a)
    acceptance_b = _accept(state_b)
    assert acceptance_a.state_id != acceptance_b.state_id
    forbidden = {
        "current_state_id",
        "preferred_state_id",
        "supersedes_state_id",
        "progression_state_id",
        "score",
        "weight",
        "confidence",
    }
    assert forbidden.isdisjoint(field.name for field in fields(PersonalCapabilityStateAcceptance))


def test_acceptance_api_never_accepts_pr11_6_receipt_as_authority_input() -> None:
    parameters = inspect.signature(accept_persisted_personal_capability_state_v1).parameters
    assert set(parameters) == {"predecessor", "successor", "request"}
    assert "receipt" not in parameters


def test_acceptance_is_not_a_rejection_or_revocation_record() -> None:
    names = {field.name for field in fields(PersonalCapabilityStateAcceptance)}
    assert {
        "verdict",
        "rejected_state_id",
        "revoked_acceptance_id",
        "revoked_at",
    }.isdisjoint(names)


def test_historical_backfill_can_be_accepted_after_later_state() -> None:
    later = _state("later", as_of=T0, derived_at=T0 + timedelta(minutes=1))
    historical = _state(
        "historical",
        as_of=datetime(2020, 1, 1, tzinfo=timezone.utc),
        derived_at=T0 + timedelta(minutes=10),
    )
    acceptance = _accept(
        historical,
        predecessor=_set(later),
        successor=_set(later, historical),
        request=_request(historical, accepted_at=T0 + timedelta(minutes=11)),
    )
    assert historical.as_of < later.as_of
    assert acceptance.state_id == historical.state_id


def test_acceptance_constructor_rejects_malformed_hash() -> None:
    state = _state()
    with pytest.raises(
        InvalidPersonalCapabilityStateAcceptance,
        match="accepted_state_sha256 must be 64 lowercase",
    ):
        PersonalCapabilityStateAcceptance(
            subject_ref=SUBJECT,
            state_id=state.state_id,
            accepted_state_sha256="not-a-hash",
            persistence_predecessor_sha256="0" * 64,
            persistence_successor_sha256="1" * 64,
            acceptance_policy_ref=ACCEPTANCE_POLICY,
            accepter_ref=ACCEPTER,
            accepted_at=state.derived_at,
            rationale="Invalid fixture.",
        )


def test_acceptance_policy_is_not_derivation_policy() -> None:
    assert StateAcceptancePolicyRef is not StateDerivationPolicyRef
    assert StateAcceptanceMechanismKind is not StateDeriverKind
