from dataclasses import replace
from datetime import datetime, timedelta, timezone
from enum import Enum
import ast
from pathlib import Path

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
    validate_personal_capability_state_acceptance_v1,
)


T0 = datetime(2026, 8, 21, 12, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("alice_pr11_7_adversarial")
CONCEPT = CapabilityConceptRef.parse("core:acceptance_adversarial@1")
FRAME = CompetenceFrameRef.parse("core:acceptance_adversarial_frame@1")
DERIVATION_POLICY = StateDerivationPolicyRef.parse("core:acceptance_adversarial_derive@1")
DERIVER = StateDeriverRef(StateDeriverKind.RULE, "acceptance_adversarial_deriver")
POLICY = StateAcceptancePolicyRef.parse("core:acceptance_adversarial@1")
ACCEPTER = StateAccepterRef(StateAcceptanceMechanismKind.HUMAN, "acceptance_reviewer")
CLAIM = CapabilityClaimId("claim_acceptance_adversarial")
EVALUATION = ClaimEvaluationId("evaluation_acceptance_adversarial")


def _state(state_id="state_acceptance_adversarial"):
    return PersonalCapabilityState(
        state_id=PersonalCapabilityStateId(state_id),
        subject_ref=SUBJECT,
        concept_ref=CONCEPT,
        frame_ref=FRAME,
        derivation_policy_ref=DERIVATION_POLICY,
        deriver_ref=DERIVER,
        as_of=T0,
        derived_at=T0 + timedelta(minutes=1),
        dimensions=(
            CompetenceDimensionState(
                dimension_key="execution",
                standing=DimensionStanding.SUPPORTED,
                supported_claim_ids=(CLAIM,),
                basis_evaluation_ids=(EVALUATION,),
                rationale="Exact adversarial state fixture.",
                conflict_status=DimensionConflictStatus.NONE,
            ),
        ),
        rationale="Exact adversarial PR11.7 state.",
    )


def _request(state):
    return PersonalCapabilityStateAcceptanceRequest(
        state_id=state.state_id,
        acceptance_policy_ref=POLICY,
        accepter_ref=ACCEPTER,
        accepted_at=T0 + timedelta(minutes=2),
        rationale="Explicit adversarial acceptance fixture.",
    )


def _accept(state, request=None):
    return accept_persisted_personal_capability_state_v1(
        predecessor=PersonalCapabilityStateSet(SUBJECT),
        successor=PersonalCapabilityStateSet(SUBJECT, (state,)),
        request=request or _request(state),
    )


class _StateIdSubclass(PersonalCapabilityStateId):
    pass


class _PolicySubclass(StateAcceptancePolicyRef):
    pass


class _AccepterSubclass(StateAccepterRef):
    pass


class _RequestSubclass(PersonalCapabilityStateAcceptanceRequest):
    pass


class _AcceptanceSubclass(PersonalCapabilityStateAcceptance):
    pass


class _SubjectSubclass(CapabilitySubjectRef):
    pass


class _DateTimeSubclass(datetime):
    pass


class _StrSubclass(str):
    pass


class _IntSubclass(int):
    pass


class _FakePolicy:
    namespace = "core"
    key = "acceptance_adversarial"
    revision = 1


class _FakeAccepter:
    kind = StateAcceptanceMechanismKind.HUMAN
    ref = "acceptance_reviewer"


class _FakeStateId:
    value = "state_acceptance_adversarial"


def test_request_subclass_is_rejected_before_governance_use() -> None:
    state = _state()
    request = _RequestSubclass(
        state_id=state.state_id,
        acceptance_policy_ref=POLICY,
        accepter_ref=ACCEPTER,
        accepted_at=T0 + timedelta(minutes=2),
        rationale="Subclass request.",
    )
    with pytest.raises(InvalidPersonalCapabilityStateAcceptance, match="acceptance request"):
        _accept(state, request=request)


def test_state_id_subclass_in_request_is_rejected() -> None:
    state = _state()
    request = _request(state)
    object.__setattr__(request, "state_id", _StateIdSubclass(state.state_id.value))
    with pytest.raises(InvalidPersonalCapabilityStateAcceptance, match="state_id"):
        _accept(state, request=request)


def test_unrelated_fake_state_id_is_rejected_before_lookup() -> None:
    state = _state()
    request = _request(state)
    object.__setattr__(request, "state_id", _FakeStateId())
    with pytest.raises(InvalidPersonalCapabilityStateAcceptance, match="state_id"):
        _accept(state, request=request)


def test_policy_subclass_in_request_is_rejected() -> None:
    state = _state()
    request = _request(state)
    object.__setattr__(request, "acceptance_policy_ref", _PolicySubclass("core", "x", 1))
    with pytest.raises(InvalidPersonalCapabilityStateAcceptance, match="acceptance_policy_ref"):
        _accept(state, request=request)


def test_unrelated_fake_policy_is_rejected() -> None:
    state = _state()
    request = _request(state)
    object.__setattr__(request, "acceptance_policy_ref", _FakePolicy())
    with pytest.raises(InvalidPersonalCapabilityStateAcceptance, match="acceptance_policy_ref"):
        _accept(state, request=request)


def test_postconstruction_invalid_policy_namespace_is_rejected() -> None:
    state = _state()
    request = _request(state)
    policy = StateAcceptancePolicyRef("core", "valid_key", 1)
    object.__setattr__(policy, "namespace", "Core.Bad")
    object.__setattr__(request, "acceptance_policy_ref", policy)
    with pytest.raises(InvalidPersonalCapabilityStateAcceptance, match="namespace"):
        _accept(state, request=request)


def test_postconstruction_str_subclass_policy_key_is_rejected() -> None:
    state = _state()
    request = _request(state)
    policy = StateAcceptancePolicyRef("core", "valid_key", 1)
    object.__setattr__(policy, "key", _StrSubclass("valid_key"))
    object.__setattr__(request, "acceptance_policy_ref", policy)
    with pytest.raises(InvalidPersonalCapabilityStateAcceptance, match="key"):
        _accept(state, request=request)


def test_postconstruction_int_subclass_policy_revision_is_rejected() -> None:
    state = _state()
    request = _request(state)
    policy = StateAcceptancePolicyRef("core", "valid_key", 1)
    object.__setattr__(policy, "revision", _IntSubclass(1))
    object.__setattr__(request, "acceptance_policy_ref", policy)
    with pytest.raises(InvalidPersonalCapabilityStateAcceptance, match="revision"):
        _accept(state, request=request)


def test_accepter_subclass_in_request_is_rejected() -> None:
    state = _state()
    request = _request(state)
    object.__setattr__(
        request,
        "accepter_ref",
        _AccepterSubclass(StateAcceptanceMechanismKind.HUMAN, "reviewer"),
    )
    with pytest.raises(InvalidPersonalCapabilityStateAcceptance, match="accepter_ref"):
        _accept(state, request=request)


def test_unrelated_fake_accepter_is_rejected() -> None:
    state = _state()
    request = _request(state)
    object.__setattr__(request, "accepter_ref", _FakeAccepter())
    with pytest.raises(InvalidPersonalCapabilityStateAcceptance, match="accepter_ref"):
        _accept(state, request=request)


def test_postconstruction_wrong_accepter_kind_type_is_rejected() -> None:
    state = _state()
    request = _request(state)
    accepter = StateAccepterRef(StateAcceptanceMechanismKind.HUMAN, "reviewer")
    object.__setattr__(accepter, "kind", StateDeriverKind.HUMAN)
    object.__setattr__(request, "accepter_ref", accepter)
    with pytest.raises(InvalidPersonalCapabilityStateAcceptance, match="kind"):
        _accept(state, request=request)


def test_postconstruction_str_subclass_accepter_ref_is_rejected() -> None:
    state = _state()
    request = _request(state)
    accepter = StateAccepterRef(StateAcceptanceMechanismKind.HUMAN, "reviewer")
    object.__setattr__(accepter, "ref", _StrSubclass("reviewer"))
    object.__setattr__(request, "accepter_ref", accepter)
    with pytest.raises(InvalidPersonalCapabilityStateAcceptance, match="ref"):
        _accept(state, request=request)


def test_datetime_subclass_is_rejected_after_request_tampering() -> None:
    state = _state()
    request = _request(state)
    subclass_time = _DateTimeSubclass(
        2026, 8, 21, 12, 2, tzinfo=timezone.utc
    )
    object.__setattr__(request, "accepted_at", subclass_time)
    with pytest.raises(InvalidPersonalCapabilityStateAcceptance, match="accepted_at"):
        _accept(state, request=request)


def test_noncanonical_timezone_after_request_tampering_is_rejected() -> None:
    state = _state()
    request = _request(state)
    object.__setattr__(
        request,
        "accepted_at",
        datetime(2026, 8, 21, 18, 2, tzinfo=timezone(timedelta(hours=6))),
    )
    with pytest.raises(InvalidPersonalCapabilityStateAcceptance, match="normalized to UTC"):
        _accept(state, request=request)


def test_noncanonical_rationale_after_request_tampering_is_rejected() -> None:
    state = _state()
    request = _request(state)
    object.__setattr__(request, "rationale", "  changed  ")
    with pytest.raises(InvalidPersonalCapabilityStateAcceptance, match="canonical NFC-trimmed"):
        _accept(state, request=request)


def test_acceptance_subclass_is_rejected_on_revalidation() -> None:
    state = _state()
    acceptance = _accept(state)
    forged = _AcceptanceSubclass(**{
        field: getattr(acceptance, field)
        for field in (
            "subject_ref",
            "state_id",
            "accepted_state_sha256",
            "persistence_predecessor_sha256",
            "persistence_successor_sha256",
            "acceptance_policy_ref",
            "accepter_ref",
            "accepted_at",
            "rationale",
        )
    })
    with pytest.raises(InvalidPersonalCapabilityStateAcceptance, match="acceptance"):
        validate_personal_capability_state_acceptance_v1(
            predecessor=PersonalCapabilityStateSet(SUBJECT),
            successor=PersonalCapabilityStateSet(SUBJECT, (state,)),
            acceptance=forged,
        )


def test_postconstruction_subject_subclass_in_acceptance_is_rejected() -> None:
    state = _state()
    acceptance = _accept(state)
    object.__setattr__(acceptance, "subject_ref", _SubjectSubclass(SUBJECT.value))
    with pytest.raises(InvalidPersonalCapabilityStateAcceptance, match="subject_ref"):
        validate_personal_capability_state_acceptance_v1(
            predecessor=PersonalCapabilityStateSet(SUBJECT),
            successor=PersonalCapabilityStateSet(SUBJECT, (state,)),
            acceptance=acceptance,
        )


def test_postconstruction_digest_str_subclass_is_rejected() -> None:
    state = _state()
    acceptance = _accept(state)
    object.__setattr__(
        acceptance,
        "accepted_state_sha256",
        _StrSubclass(acceptance.accepted_state_sha256),
    )
    with pytest.raises(InvalidPersonalCapabilityStateAcceptance, match="accepted_state_sha256"):
        validate_personal_capability_state_acceptance_v1(
            predecessor=PersonalCapabilityStateSet(SUBJECT),
            successor=PersonalCapabilityStateSet(SUBJECT, (state,)),
            acceptance=acceptance,
        )


def test_exact_builtin_but_invalid_dimension_key_tampering_fails_strict_roundtrip() -> None:
    state = _state("state_bad_dimension_key")
    object.__setattr__(state.dimensions[0], "dimension_key", "Not Canonical")
    successor = PersonalCapabilityStateSet(SUBJECT, (state,))
    with pytest.raises(
        InvalidPersonalCapabilityStateAcceptance,
        match="strict PR3 semantic round-trip",
    ):
        accept_persisted_personal_capability_state_v1(
            predecessor=PersonalCapabilityStateSet(SUBJECT),
            successor=successor,
            request=_request(state),
        )


def test_exact_builtin_but_invalid_concept_revision_tampering_fails_strict_roundtrip() -> None:
    state = _state("state_bad_revision")
    tampered_ref = CapabilityConceptRef.parse(str(CONCEPT))
    object.__setattr__(tampered_ref, "revision", 0)
    object.__setattr__(state, "concept_ref", tampered_ref)
    successor = PersonalCapabilityStateSet(SUBJECT, (state,))
    with pytest.raises(
        InvalidPersonalCapabilityStateAcceptance,
        match="strict PR3 semantic round-trip",
    ):
        accept_persisted_personal_capability_state_v1(
            predecessor=PersonalCapabilityStateSet(SUBJECT),
            successor=successor,
            request=_request(state),
        )


def test_exact_datetime_but_naive_state_time_tampering_fails_strict_roundtrip() -> None:
    state = _state("state_naive_derived_at")
    object.__setattr__(state, "derived_at", datetime(2026, 8, 21, 12, 1))
    successor = PersonalCapabilityStateSet(SUBJECT, (state,))
    with pytest.raises(
        InvalidPersonalCapabilityStateAcceptance,
        match="strict PR3 semantic round-trip",
    ):
        accept_persisted_personal_capability_state_v1(
            predecessor=PersonalCapabilityStateSet(SUBJECT),
            successor=successor,
            request=_request(state),
        )


def test_exact_str_but_empty_state_rationale_tampering_fails_content_hash() -> None:
    state = _state("state_empty_rationale")
    object.__setattr__(state, "rationale", "")
    snapshot = PersonalCapabilityStateSet(SUBJECT, (state,))
    with pytest.raises(
        InvalidPersonalCapabilityStateAcceptance,
        match="strict PR3 semantic round-trip",
    ):
        personal_capability_state_content_sha256_v1(
            snapshot=snapshot,
            state_id=state.state_id,
        )


def test_invalid_pr11_6_successor_is_rejected_even_when_requested_state_is_unchanged() -> None:
    state_a = _state("state_a")
    state_b = _state("state_b")
    predecessor = PersonalCapabilityStateSet(SUBJECT, (state_a,))
    successor = PersonalCapabilityStateSet(SUBJECT, (state_b,))
    with pytest.raises(
        InvalidPersonalCapabilityStateAcceptance,
        match="may not remove persisted state",
    ):
        accept_persisted_personal_capability_state_v1(
            predecessor=predecessor,
            successor=successor,
            request=_request(state_b),
        )


def test_state_content_hash_frozen_known_answer_v1() -> None:
    state = _state("state_acceptance_adversarial")
    digest = personal_capability_state_content_sha256_v1(
        snapshot=PersonalCapabilityStateSet(SUBJECT, (state,)),
        state_id=state.state_id,
    )
    assert digest == "ea1d572c4aa67f19da5bd233da2c3fa55abbbeabbd2052d9e4ae3115fa406c2b"


def test_production_import_surface_is_exactly_frozen() -> None:
    path = Path(__file__).parents[2] / "src" / "capability_lab" / "state" / "acceptance.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))

    actual_imports = set()
    actual_from_imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                actual_imports.add((alias.name, alias.asname))
        elif isinstance(node, ast.ImportFrom):
            actual_from_imports.add(
                (
                    node.level,
                    node.module or "",
                    tuple((alias.name, alias.asname) for alias in node.names),
                )
            )

    assert actual_imports == {
        ("hashlib", None),
        ("re", None),
        ("unicodedata", None),
    }
    assert actual_from_imports == {
        (0, "__future__", (("annotations", None),)),
        (0, "dataclasses", (("dataclass", None),)),
        (0, "datetime", (("datetime", None), ("timezone", None))),
        (0, "enum", (("Enum", None),)),
        (0, "capability_lab.epistemics", (("CapabilitySubjectRef", None),)),
        (
            1,
            "core",
            (
                ("PersonalCapabilityState", None),
                ("PersonalCapabilityStateId", None),
                ("PersonalCapabilityStateSet", None),
                ("StateError", None),
            ),
        ),
        (
            1,
            "snapshot_transition",
            (
                ("PersonalCapabilityStateSetSuccessionReceipt", None),
                ("personal_capability_state_set_sha256_v1", None),
                ("validate_personal_capability_state_set_successor_v1", None),
            ),
        ),
    }


def test_acceptance_mechanism_kind_has_no_implicit_priority_order() -> None:
    assert tuple(item.value for item in StateAcceptanceMechanismKind) == (
        "human",
        "rule",
        "model",
        "hybrid",
        "external_system",
    )
    assert not issubclass(StateAcceptanceMechanismKind, int)


def test_acceptance_record_carries_no_authenticated_principal_or_permission_claim() -> None:
    state = _state()
    acceptance = _accept(state)
    assert not hasattr(acceptance, "authenticated_principal")
    assert not hasattr(acceptance, "permission")
    assert not hasattr(acceptance, "license")
    assert not hasattr(acceptance, "current")
