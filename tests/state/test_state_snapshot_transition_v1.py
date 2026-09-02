from dataclasses import fields, replace
from datetime import datetime, timedelta, timezone
import json

import pytest

from capability_lab.epistemics import (
    CapabilityClaimId,
    CapabilitySubjectRef,
    ClaimEvaluationId,
)
from capability_lab.semantics import CapabilityConceptRef
from capability_lab.state import (
    CompetenceDimensionState,
    CompetenceFrameRef,
    DimensionConflictStatus,
    DimensionStanding,
    InvalidPersonalCapabilityStateSetSuccessor,
    PersonalCapabilityState,
    PersonalCapabilityStateId,
    PersonalCapabilityStateSet,
    PersonalCapabilityStateSetSuccessionReceipt,
    StateDerivationPolicyRef,
    StateDeriverKind,
    StateDeriverRef,
    personal_capability_state_set_sha256_v1,
    validate_personal_capability_state_set_successor_v1,
)


T0 = datetime(2026, 8, 21, 6, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("alice_pr11_6")
OTHER_SUBJECT = CapabilitySubjectRef("bob_pr11_6")
CONCEPT = CapabilityConceptRef.parse("core:state_snapshot_capability@1")
FRAME = CompetenceFrameRef.parse("core:state_snapshot_frame@1")
POLICY = StateDerivationPolicyRef.parse("core:state_snapshot_policy@1")
DERIVER = StateDeriverRef(StateDeriverKind.RULE, "state_snapshot_rule")
CLAIM_A = CapabilityClaimId("claim_state_snapshot_a")
CLAIM_B = CapabilityClaimId("claim_state_snapshot_b")
EVAL_A = ClaimEvaluationId("evaluation_state_snapshot_a")
EVAL_B = ClaimEvaluationId("evaluation_state_snapshot_b")
EMPTY_SHA256_V1 = "6085b36ef5e5c91e9821561dc0fe553a1f024245a31b9a936dbb3e1b3c2df09d"


def _dimension(
    *,
    key: str = "execution",
    standing: DimensionStanding = DimensionStanding.SUPPORTED,
    conflict: DimensionConflictStatus = DimensionConflictStatus.NONE,
    claims: tuple[CapabilityClaimId, ...] = (CLAIM_A,),
    evaluations: tuple[ClaimEvaluationId, ...] = (EVAL_A,),
    rationale: str = "Bounded supported state content.",
) -> CompetenceDimensionState:
    return CompetenceDimensionState(
        dimension_key=key,
        standing=standing,
        supported_claim_ids=claims,
        basis_evaluation_ids=evaluations,
        rationale=rationale,
        conflict_status=conflict,
    )


def _state(
    state_id: str,
    *,
    subject_ref: CapabilitySubjectRef = SUBJECT,
    concept_ref: CapabilityConceptRef = CONCEPT,
    frame_ref: CompetenceFrameRef = FRAME,
    policy_ref: StateDerivationPolicyRef = POLICY,
    deriver_ref: StateDeriverRef = DERIVER,
    as_of: datetime = T0,
    derived_at: datetime = T0 + timedelta(minutes=1),
    dimensions: tuple[CompetenceDimensionState, ...] | None = None,
    rationale: str = "PR11.6 immutable state fixture.",
) -> PersonalCapabilityState:
    return PersonalCapabilityState(
        state_id=PersonalCapabilityStateId(state_id),
        subject_ref=subject_ref,
        concept_ref=concept_ref,
        frame_ref=frame_ref,
        derivation_policy_ref=policy_ref,
        deriver_ref=deriver_ref,
        as_of=as_of,
        derived_at=derived_at,
        dimensions=dimensions or (_dimension(),),
        rationale=rationale,
    )


def _set(*states: PersonalCapabilityState) -> PersonalCapabilityStateSet:
    return PersonalCapabilityStateSet(SUBJECT, states)


def test_state_snapshot_hash_rejects_non_state_set() -> None:
    with pytest.raises(
        InvalidPersonalCapabilityStateSetSuccessor,
        match="snapshot must be PersonalCapabilityStateSet",
    ):
        personal_capability_state_set_sha256_v1(object())  # type: ignore[arg-type]


def test_subject_scoped_empty_snapshot_fingerprint_is_frozen() -> None:
    assert (
        personal_capability_state_set_sha256_v1(PersonalCapabilityStateSet(SUBJECT))
        == EMPTY_SHA256_V1
    )


def test_state_snapshot_fingerprint_roundtrip_is_stable() -> None:
    snapshot = _set(_state("state_a"), _state("state_b", as_of=T0 - timedelta(days=1)))
    restored = PersonalCapabilityStateSet.from_json(snapshot.to_json())
    assert (
        personal_capability_state_set_sha256_v1(restored)
        == personal_capability_state_set_sha256_v1(snapshot)
    )


def test_state_snapshot_hash_uses_canonical_typed_order_not_construction_order() -> None:
    first = _set(_state("state_b"), _state("state_a"))
    second = _set(*reversed(first.states))
    assert first == second
    assert (
        personal_capability_state_set_sha256_v1(first)
        == personal_capability_state_set_sha256_v1(second)
    )


def test_json_whitespace_and_key_order_do_not_change_hash_after_strict_parse() -> None:
    snapshot = _set(_state("state_a"))
    payload = snapshot.to_dict()
    reordered = {
        "states": payload["states"],
        "subject_ref": payload["subject_ref"],
        "schema": payload["schema"],
    }
    restored = PersonalCapabilityStateSet.from_json(
        json.dumps(reordered, ensure_ascii=False, indent=2)
    )
    assert (
        personal_capability_state_set_sha256_v1(restored)
        == personal_capability_state_set_sha256_v1(snapshot)
    )


def test_hash_changes_when_canonical_state_content_changes() -> None:
    first = _set(_state("state_a"))
    changed = replace(first.states[0], rationale="Changed persisted state content.")
    second = _set(changed)
    assert (
        personal_capability_state_set_sha256_v1(first)
        != personal_capability_state_set_sha256_v1(second)
    )


def test_noop_successor_is_allowed_and_retains_every_state_identity() -> None:
    snapshot = _set(_state("state_b"), _state("state_a"))
    receipt = validate_personal_capability_state_set_successor_v1(
        predecessor=snapshot,
        successor=snapshot,
    )
    assert receipt.predecessor_sha256 == receipt.successor_sha256
    assert receipt.subject_ref == SUBJECT
    assert receipt.retained_state_ids == (
        PersonalCapabilityStateId("state_a"),
        PersonalCapabilityStateId("state_b"),
    )
    assert receipt.added_state_ids == ()


def test_empty_subject_snapshot_can_append_first_state() -> None:
    predecessor = PersonalCapabilityStateSet(SUBJECT)
    successor = _set(_state("state_a"))
    receipt = validate_personal_capability_state_set_successor_v1(
        predecessor=predecessor,
        successor=successor,
    )
    assert receipt.retained_state_ids == ()
    assert receipt.added_state_ids == (PersonalCapabilityStateId("state_a"),)


def test_existing_snapshot_can_append_multiple_new_states() -> None:
    state_a = _state("state_a")
    predecessor = _set(state_a)
    successor = _set(
        state_a,
        _state("state_c", as_of=T0 - timedelta(days=10)),
        _state("state_b", derived_at=T0 + timedelta(minutes=2)),
    )
    receipt = validate_personal_capability_state_set_successor_v1(
        predecessor=predecessor,
        successor=successor,
    )
    assert receipt.retained_state_ids == (PersonalCapabilityStateId("state_a"),)
    assert receipt.added_state_ids == (
        PersonalCapabilityStateId("state_b"),
        PersonalCapabilityStateId("state_c"),
    )


def test_historical_state_backfill_under_new_identity_is_allowed() -> None:
    current = _state("state_current", as_of=T0, derived_at=T0 + timedelta(minutes=1))
    historical = _state(
        "state_historical",
        as_of=datetime(2020, 1, 1, tzinfo=timezone.utc),
        derived_at=T0 + timedelta(days=1),
    )
    receipt = validate_personal_capability_state_set_successor_v1(
        predecessor=_set(current),
        successor=_set(current, historical),
    )
    assert receipt.added_state_ids == (PersonalCapabilityStateId("state_historical"),)


def test_timezone_equivalent_state_times_are_same_canonical_content() -> None:
    utc_state = _state(
        "state_timezone",
        as_of=datetime(2026, 8, 21, 6, 0, tzinfo=timezone.utc),
        derived_at=datetime(2026, 8, 21, 6, 1, tzinfo=timezone.utc),
    )
    plus_six = _state(
        "state_timezone",
        as_of=datetime(2026, 8, 21, 12, 0, tzinfo=timezone(timedelta(hours=6))),
        derived_at=datetime(2026, 8, 21, 12, 1, tzinfo=timezone(timedelta(hours=6))),
    )
    assert utc_state == plus_six
    validate_personal_capability_state_set_successor_v1(
        predecessor=_set(utc_state),
        successor=_set(plus_six),
    )


def test_receipt_is_structural_and_contains_no_acceptance_or_current_state_fields() -> None:
    names = {field.name for field in fields(PersonalCapabilityStateSetSuccessionReceipt)}
    assert {
        "accepted_state_id",
        "current_state_id",
        "preferred_state_id",
        "selected_state_ids",
        "superseded_state_ids",
        "progression_state_ids",
        "acceptance_policy_ref",
        "accepter_ref",
        "score",
        "weight",
        "confidence",
    }.isdisjoint(names)


def test_receipt_normalizes_ids_but_grants_no_instance_provenance() -> None:
    receipt = PersonalCapabilityStateSetSuccessionReceipt(
        predecessor_sha256=EMPTY_SHA256_V1,
        successor_sha256=EMPTY_SHA256_V1,
        subject_ref=SUBJECT,
        retained_state_ids=(PersonalCapabilityStateId("z"), PersonalCapabilityStateId("a")),
        added_state_ids=(PersonalCapabilityStateId("y"), PersonalCapabilityStateId("b")),
    )
    assert receipt.retained_state_ids == (
        PersonalCapabilityStateId("a"),
        PersonalCapabilityStateId("z"),
    )
    assert receipt.added_state_ids == (
        PersonalCapabilityStateId("b"),
        PersonalCapabilityStateId("y"),
    )
    assert not hasattr(receipt, "validator_issued")


def test_receipt_rejects_retained_and_added_identity_overlap() -> None:
    with pytest.raises(
        InvalidPersonalCapabilityStateSetSuccessor,
        match="retained_state_ids and added_state_ids must be disjoint",
    ):
        PersonalCapabilityStateSetSuccessionReceipt(
            predecessor_sha256=EMPTY_SHA256_V1,
            successor_sha256=EMPTY_SHA256_V1,
            subject_ref=SUBJECT,
            retained_state_ids=(PersonalCapabilityStateId("state_overlap"),),
            added_state_ids=(PersonalCapabilityStateId("state_overlap"),),
        )


def test_successor_rejects_wrong_argument_types() -> None:
    empty = PersonalCapabilityStateSet(SUBJECT)
    with pytest.raises(
        InvalidPersonalCapabilityStateSetSuccessor,
        match="predecessor must be PersonalCapabilityStateSet",
    ):
        validate_personal_capability_state_set_successor_v1(
            predecessor=object(),  # type: ignore[arg-type]
            successor=empty,
        )
    with pytest.raises(
        InvalidPersonalCapabilityStateSetSuccessor,
        match="successor must be PersonalCapabilityStateSet",
    ):
        validate_personal_capability_state_set_successor_v1(
            predecessor=empty,
            successor=object(),  # type: ignore[arg-type]
        )


def test_different_subject_snapshot_is_not_a_successor() -> None:
    predecessor = PersonalCapabilityStateSet(SUBJECT)
    successor = PersonalCapabilityStateSet(OTHER_SUBJECT)
    with pytest.raises(
        InvalidPersonalCapabilityStateSetSuccessor,
        match="preserve exact state-set subject_ref",
    ):
        validate_personal_capability_state_set_successor_v1(
            predecessor=predecessor,
            successor=successor,
        )
