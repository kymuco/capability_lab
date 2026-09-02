"""PR11.7 governed persisted personal capability state acceptance v1."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import re
import unicodedata

from capability_lab.epistemics import CapabilitySubjectRef

from .core import (
    PersonalCapabilityState,
    PersonalCapabilityStateId,
    PersonalCapabilityStateSet,
    StateError,
)
from .snapshot_transition import (
    PersonalCapabilityStateSetSuccessionReceipt,
    personal_capability_state_set_sha256_v1,
    validate_personal_capability_state_set_successor_v1,
)


class StateAcceptanceError(StateError):
    """Base error for governed persisted-state acceptance."""


class InvalidPersonalCapabilityStateAcceptance(StateAcceptanceError):
    """The supplied request, acceptance record, or persistence basis is invalid."""


_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_NAMESPACE_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*$")
_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_POLICY_RE = re.compile(
    r"^([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*):"
    r"([a-z][a-z0-9_]*)@([1-9][0-9]*)$"
)
_SHA256_HEX_DIGITS = frozenset("0123456789abcdef")
_STATE_CONTENT_HASH_DOMAIN_V1 = b"capability_lab/personal_capability_state@1\x00"


def _fail(message: str) -> None:
    raise InvalidPersonalCapabilityStateAcceptance(message)


def _exact_type(value: object, expected_type: type, field_name: str) -> None:
    if type(value) is not expected_type:
        _fail(f"{field_name} must use exact type {expected_type.__name__}")


def _exact_str(value: object, field_name: str) -> str:
    if type(value) is not str:
        _fail(f"{field_name} must be exact str")
    return value


def _opaque_id(value: object, field_name: str) -> str:
    value = _exact_str(value, field_name)
    if _ID_RE.fullmatch(value) is None:
        _fail(f"{field_name} must be a canonical opaque ASCII identifier")
    return value


def _canonical_text(value: object, field_name: str) -> str:
    value = _exact_str(value, field_name)
    cleaned = unicodedata.normalize("NFC", value).strip()
    if not cleaned:
        _fail(f"{field_name} must be non-empty")
    return cleaned


def _require_canonical_text(value: object, field_name: str) -> str:
    cleaned = _canonical_text(value, field_name)
    if value != cleaned:
        _fail(f"{field_name} must already be canonical NFC-trimmed text")
    return cleaned


def _canonical_time(value: object, field_name: str) -> datetime:
    _exact_type(value, datetime, field_name)
    if value.tzinfo is None or value.utcoffset() is None:
        _fail(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _require_canonical_time(value: object, field_name: str) -> datetime:
    canonical = _canonical_time(value, field_name)
    if value.tzinfo is not timezone.utc:
        _fail(f"{field_name} must already be normalized to UTC")
    return canonical


def _validate_sha256(value: object, field_name: str) -> str:
    value = _exact_str(value, field_name)
    if len(value) != 64 or any(character not in _SHA256_HEX_DIGITS for character in value):
        _fail(f"{field_name} must be 64 lowercase hexadecimal SHA-256 characters")
    return value


def _validate_state_id(value: object, field_name: str) -> PersonalCapabilityStateId:
    _exact_type(value, PersonalCapabilityStateId, field_name)
    _opaque_id(value.value, f"{field_name}.value")
    return value


class StateAcceptanceMechanismKind(str, Enum):
    HUMAN = "human"
    RULE = "rule"
    MODEL = "model"
    HYBRID = "hybrid"
    EXTERNAL_SYSTEM = "external_system"


@dataclass(frozen=True, order=True, slots=True)
class StateAcceptancePolicyRef:
    namespace: str
    key: str
    revision: int

    def __post_init__(self) -> None:
        namespace = _exact_str(self.namespace, "acceptance policy namespace")
        key = _exact_str(self.key, "acceptance policy key")
        if _NAMESPACE_RE.fullmatch(namespace) is None:
            _fail("acceptance policy namespace must use canonical namespace syntax")
        if _KEY_RE.fullmatch(key) is None:
            _fail("acceptance policy key must use canonical lowercase key syntax")
        if type(self.revision) is not int or self.revision < 1:
            _fail("acceptance policy revision must be an exact integer >= 1")

    @classmethod
    def parse(cls, value: object) -> "StateAcceptancePolicyRef":
        value = _exact_str(value, "acceptance policy ref")
        match = _POLICY_RE.fullmatch(value)
        if match is None:
            _fail("acceptance policy ref must use '<namespace>:<key>@<revision>'")
        return cls(match.group(1), match.group(2), int(match.group(3)))

    def __str__(self) -> str:
        return f"{self.namespace}:{self.key}@{self.revision}"


@dataclass(frozen=True, order=True, slots=True)
class StateAccepterRef:
    kind: StateAcceptanceMechanismKind
    ref: str

    def __post_init__(self) -> None:
        _exact_type(self.kind, StateAcceptanceMechanismKind, "accepter kind")
        _exact_str(self.kind.value, "accepter kind value")
        object.__setattr__(self, "ref", _opaque_id(self.ref, "accepter ref"))


@dataclass(frozen=True, slots=True)
class PersonalCapabilityStateAcceptanceRequest:
    state_id: PersonalCapabilityStateId
    acceptance_policy_ref: StateAcceptancePolicyRef
    accepter_ref: StateAccepterRef
    accepted_at: datetime
    rationale: str

    def __post_init__(self) -> None:
        _validate_state_id(self.state_id, "acceptance request state_id")
        _validate_policy_ref(
            self.acceptance_policy_ref,
            "acceptance request acceptance_policy_ref",
        )
        _validate_accepter_ref(self.accepter_ref, "acceptance request accepter_ref")
        object.__setattr__(
            self,
            "accepted_at",
            _canonical_time(self.accepted_at, "acceptance request accepted_at"),
        )
        object.__setattr__(
            self,
            "rationale",
            _canonical_text(self.rationale, "acceptance request rationale"),
        )


@dataclass(frozen=True, slots=True)
class PersonalCapabilityStateAcceptance:
    """Immutable acceptance fact bound to one exact persisted state content."""

    subject_ref: CapabilitySubjectRef
    state_id: PersonalCapabilityStateId
    accepted_state_sha256: str
    persistence_predecessor_sha256: str
    persistence_successor_sha256: str
    acceptance_policy_ref: StateAcceptancePolicyRef
    accepter_ref: StateAccepterRef
    accepted_at: datetime
    rationale: str

    def __post_init__(self) -> None:
        _validate_subject_ref(self.subject_ref, "acceptance subject_ref")
        _validate_state_id(self.state_id, "acceptance state_id")
        object.__setattr__(
            self,
            "accepted_state_sha256",
            _validate_sha256(self.accepted_state_sha256, "accepted_state_sha256"),
        )
        object.__setattr__(
            self,
            "persistence_predecessor_sha256",
            _validate_sha256(
                self.persistence_predecessor_sha256,
                "persistence_predecessor_sha256",
            ),
        )
        object.__setattr__(
            self,
            "persistence_successor_sha256",
            _validate_sha256(
                self.persistence_successor_sha256,
                "persistence_successor_sha256",
            ),
        )
        _validate_policy_ref(self.acceptance_policy_ref, "acceptance acceptance_policy_ref")
        _validate_accepter_ref(self.accepter_ref, "acceptance accepter_ref")
        object.__setattr__(
            self,
            "accepted_at",
            _canonical_time(self.accepted_at, "acceptance accepted_at"),
        )
        object.__setattr__(
            self,
            "rationale",
            _canonical_text(self.rationale, "acceptance rationale"),
        )


def _validate_subject_ref(value: object, field_name: str) -> CapabilitySubjectRef:
    _exact_type(value, CapabilitySubjectRef, field_name)
    _opaque_id(value.value, f"{field_name}.value")
    return value


def _validate_policy_ref(value: object, field_name: str) -> StateAcceptancePolicyRef:
    _exact_type(value, StateAcceptancePolicyRef, field_name)
    namespace = _exact_str(value.namespace, f"{field_name}.namespace")
    key = _exact_str(value.key, f"{field_name}.key")
    if _NAMESPACE_RE.fullmatch(namespace) is None:
        _fail(f"{field_name}.namespace must use canonical namespace syntax")
    if _KEY_RE.fullmatch(key) is None:
        _fail(f"{field_name}.key must use canonical lowercase key syntax")
    if type(value.revision) is not int or value.revision < 1:
        _fail(f"{field_name}.revision must be an exact integer >= 1")
    return value


def _validate_accepter_ref(value: object, field_name: str) -> StateAccepterRef:
    _exact_type(value, StateAccepterRef, field_name)
    _exact_type(value.kind, StateAcceptanceMechanismKind, f"{field_name}.kind")
    _exact_str(value.kind.value, f"{field_name}.kind.value")
    _opaque_id(value.ref, f"{field_name}.ref")
    return value


def _validated_request(
    value: object,
) -> PersonalCapabilityStateAcceptanceRequest:
    _exact_type(value, PersonalCapabilityStateAcceptanceRequest, "acceptance request")
    _validate_state_id(value.state_id, "acceptance request state_id")
    _validate_policy_ref(
        value.acceptance_policy_ref,
        "acceptance request acceptance_policy_ref",
    )
    _validate_accepter_ref(value.accepter_ref, "acceptance request accepter_ref")
    _require_canonical_time(value.accepted_at, "acceptance request accepted_at")
    _require_canonical_text(value.rationale, "acceptance request rationale")
    return value


def _validated_acceptance(
    value: object,
) -> PersonalCapabilityStateAcceptance:
    _exact_type(value, PersonalCapabilityStateAcceptance, "acceptance")
    _validate_subject_ref(value.subject_ref, "acceptance subject_ref")
    _validate_state_id(value.state_id, "acceptance state_id")
    _validate_sha256(value.accepted_state_sha256, "accepted_state_sha256")
    _validate_sha256(
        value.persistence_predecessor_sha256,
        "persistence_predecessor_sha256",
    )
    _validate_sha256(
        value.persistence_successor_sha256,
        "persistence_successor_sha256",
    )
    _validate_policy_ref(value.acceptance_policy_ref, "acceptance acceptance_policy_ref")
    _validate_accepter_ref(value.accepter_ref, "acceptance accepter_ref")
    _require_canonical_time(value.accepted_at, "acceptance accepted_at")
    _require_canonical_text(value.rationale, "acceptance rationale")
    return value


def _state_by_id(
    snapshot: PersonalCapabilityStateSet,
    state_id: PersonalCapabilityStateId,
) -> PersonalCapabilityState:
    for state in snapshot.states:
        if state.state_id == state_id:
            return state
    _fail(f"accepted state is absent from successor snapshot: {state_id}")


def _strict_one_state_snapshot(
    snapshot: PersonalCapabilityStateSet,
    state_id: PersonalCapabilityStateId,
) -> PersonalCapabilityStateSet:
    # PR11.6 hash validation rejects behavioral subclasses before lookup/serialization.
    try:
        personal_capability_state_set_sha256_v1(snapshot)
    except (StateError, TypeError, ValueError) as exc:
        raise InvalidPersonalCapabilityStateAcceptance(str(exc)) from exc
    state_id = _validate_state_id(state_id, "state_id")
    state = _state_by_id(snapshot, state_id)
    one_state = PersonalCapabilityStateSet(snapshot.subject_ref, (state,))

    # Strict PR3 parse re-runs semantic constructors, catching post-construction
    # tampering that still uses exact built-in/core classes but invalid field values.
    try:
        restored = PersonalCapabilityStateSet.from_json(one_state.to_json())
    except (StateError, TypeError, ValueError) as exc:
        raise InvalidPersonalCapabilityStateAcceptance(
            f"accepted state fails strict PR3 semantic round-trip: {exc}"
        ) from exc
    if restored != one_state:
        _fail(
            "accepted state fails strict PR3 semantic round-trip: "
            "canonical round-trip mismatch"
        )
    return restored


def personal_capability_state_content_sha256_v1(
    *,
    snapshot: PersonalCapabilityStateSet,
    state_id: PersonalCapabilityStateId,
) -> str:
    """Hash one exact state independently of unrelated later snapshot appends."""

    one_state = _strict_one_state_snapshot(snapshot, state_id)
    digest = hashlib.sha256()
    digest.update(_STATE_CONTENT_HASH_DOMAIN_V1)
    digest.update(one_state.to_json().encode("utf-8"))
    return digest.hexdigest()


def _validated_persistence_basis(
    *,
    predecessor: PersonalCapabilityStateSet,
    successor: PersonalCapabilityStateSet,
    state_id: PersonalCapabilityStateId,
) -> tuple[PersonalCapabilityStateSetSuccessionReceipt, PersonalCapabilityState]:
    try:
        receipt = validate_personal_capability_state_set_successor_v1(
            predecessor=predecessor,
            successor=successor,
        )
    except StateError as exc:
        raise InvalidPersonalCapabilityStateAcceptance(str(exc)) from exc
    state_id = _validate_state_id(state_id, "state_id")
    state = _state_by_id(successor, state_id)
    # Revalidate the accepted state through strict PR3 semantics, not only exact types.
    _strict_one_state_snapshot(successor, state_id)
    return receipt, state


def accept_persisted_personal_capability_state_v1(
    *,
    predecessor: PersonalCapabilityStateSet,
    successor: PersonalCapabilityStateSet,
    request: PersonalCapabilityStateAcceptanceRequest,
) -> PersonalCapabilityStateAcceptance:
    """Create one explicit acceptance fact over an exact persisted state.

    This operation re-runs PR11.6 succession validation. It does not accept a
    succession receipt as proof, select a current/preferred state, supersede any
    state, or grant progression/permission authority.
    """

    request = _validated_request(request)
    receipt, state = _validated_persistence_basis(
        predecessor=predecessor,
        successor=successor,
        state_id=request.state_id,
    )
    if request.accepted_at < state.derived_at:
        _fail("accepted_at must not precede the accepted state's derived_at")

    return PersonalCapabilityStateAcceptance(
        subject_ref=successor.subject_ref,
        state_id=state.state_id,
        accepted_state_sha256=personal_capability_state_content_sha256_v1(
            snapshot=successor,
            state_id=state.state_id,
        ),
        persistence_predecessor_sha256=receipt.predecessor_sha256,
        persistence_successor_sha256=receipt.successor_sha256,
        acceptance_policy_ref=request.acceptance_policy_ref,
        accepter_ref=request.accepter_ref,
        accepted_at=request.accepted_at,
        rationale=request.rationale,
    )


def validate_personal_capability_state_acceptance_binding_v1(
    *,
    snapshot: PersonalCapabilityStateSet,
    acceptance: PersonalCapabilityStateAcceptance,
) -> PersonalCapabilityStateAcceptance:
    """Validate that an acceptance still binds one exact state in a later snapshot.

    This durable binding check is independent of unrelated later appends. It does
    not replay or replace validation of the original PR11.6 issuance basis.
    """

    acceptance = _validated_acceptance(acceptance)
    state_sha256 = personal_capability_state_content_sha256_v1(
        snapshot=snapshot,
        state_id=acceptance.state_id,
    )
    state = _state_by_id(snapshot, acceptance.state_id)
    if acceptance.subject_ref != snapshot.subject_ref:
        _fail("acceptance subject_ref must match persisted state subject_ref")
    if acceptance.accepted_at < state.derived_at:
        _fail("accepted_at must not precede the accepted state's derived_at")
    if acceptance.accepted_state_sha256 != state_sha256:
        _fail(
            "acceptance accepted_state_sha256 does not match exact persisted state content"
        )
    return acceptance


def validate_personal_capability_state_acceptance_v1(
    *,
    predecessor: PersonalCapabilityStateSet,
    successor: PersonalCapabilityStateSet,
    acceptance: PersonalCapabilityStateAcceptance,
) -> PersonalCapabilityStateAcceptance:
    """Revalidate an acceptance record against its exact persistence basis."""

    acceptance = _validated_acceptance(acceptance)
    receipt, state = _validated_persistence_basis(
        predecessor=predecessor,
        successor=successor,
        state_id=acceptance.state_id,
    )
    if acceptance.subject_ref != successor.subject_ref:
        _fail("acceptance subject_ref must match persisted state subject_ref")
    if acceptance.accepted_at < state.derived_at:
        _fail("accepted_at must not precede the accepted state's derived_at")

    state_sha256 = personal_capability_state_content_sha256_v1(
        snapshot=successor,
        state_id=acceptance.state_id,
    )
    if acceptance.accepted_state_sha256 != state_sha256:
        _fail("acceptance accepted_state_sha256 does not match exact persisted state content")
    if acceptance.persistence_predecessor_sha256 != receipt.predecessor_sha256:
        _fail("acceptance predecessor hash does not match freshly validated PR11.6 basis")
    if acceptance.persistence_successor_sha256 != receipt.successor_sha256:
        _fail("acceptance successor hash does not match freshly validated PR11.6 basis")
    return acceptance
