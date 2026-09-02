"""PR11.8 append-only governed PersonalCapabilityStateAcceptance universe v1."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json

from capability_lab.epistemics import CapabilitySubjectRef

from .acceptance import (
    PersonalCapabilityStateAcceptance,
    validate_personal_capability_state_acceptance_binding_v1,
    validate_personal_capability_state_acceptance_v1,
)
from .core import PersonalCapabilityStateSet, StateError
from .snapshot_transition import personal_capability_state_set_sha256_v1


class StateAcceptanceSetError(StateError):
    """Base error for the governed append-only acceptance universe."""


class InvalidPersonalCapabilityStateAcceptanceSet(StateAcceptanceSetError):
    """The supplied acceptance set, admission, or succession is invalid."""


_ACCEPTANCE_SET_HASH_DOMAIN_V1 = (
    b"capability_lab/personal_capability_state_acceptance_set@1\x00"
)
_SHA256_HEX_DIGITS = frozenset("0123456789abcdef")


def _fail(message: str) -> None:
    raise InvalidPersonalCapabilityStateAcceptanceSet(message)


def _exact_type(value: object, expected_type: type, field_name: str) -> None:
    if type(value) is not expected_type:
        _fail(f"{field_name} must use exact type {expected_type.__name__}")


def _validate_sha256(value: object, field_name: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in _SHA256_HEX_DIGITS for character in value)
    ):
        _fail(f"{field_name} must be 64 lowercase hexadecimal SHA-256 characters")
    return value


def _subject(value: object, field_name: str) -> CapabilitySubjectRef:
    _exact_type(value, CapabilitySubjectRef, field_name)
    if type(value.value) is not str:
        _fail(f"{field_name}.value must be exact str")
    return value


def _utc_text(value: datetime) -> str:
    if type(value) is not datetime:
        _fail("acceptance accepted_at must be exact datetime")
    if value.tzinfo is not timezone.utc:
        _fail("acceptance accepted_at must be canonical UTC")
    return value.isoformat().replace("+00:00", "Z")


def _acceptance_sort_key(
    acceptance: PersonalCapabilityStateAcceptance,
) -> tuple[str, ...]:
    return (
        acceptance.subject_ref.value,
        acceptance.state_id.value,
        acceptance.accepted_state_sha256,
        acceptance.persistence_predecessor_sha256,
        acceptance.persistence_successor_sha256,
        str(acceptance.acceptance_policy_ref),
        acceptance.accepter_ref.kind.value,
        acceptance.accepter_ref.ref,
        _utc_text(acceptance.accepted_at),
        acceptance.rationale,
    )


def _acceptance_canonical_payload_v1(
    acceptance: PersonalCapabilityStateAcceptance,
) -> dict[str, object]:
    _exact_type(
        acceptance,
        PersonalCapabilityStateAcceptance,
        "acceptance",
    )
    _validate_sha256(acceptance.accepted_state_sha256, "accepted_state_sha256")
    _validate_sha256(
        acceptance.persistence_predecessor_sha256,
        "persistence_predecessor_sha256",
    )
    _validate_sha256(
        acceptance.persistence_successor_sha256,
        "persistence_successor_sha256",
    )
    return {
        "subject_ref": acceptance.subject_ref.value,
        "state_id": acceptance.state_id.value,
        "accepted_state_sha256": acceptance.accepted_state_sha256,
        "persistence_predecessor_sha256": acceptance.persistence_predecessor_sha256,
        "persistence_successor_sha256": acceptance.persistence_successor_sha256,
        "acceptance_policy_ref": str(acceptance.acceptance_policy_ref),
        "accepter_kind": acceptance.accepter_ref.kind.value,
        "accepter_ref": acceptance.accepter_ref.ref,
        "accepted_at": _utc_text(acceptance.accepted_at),
        "rationale": acceptance.rationale,
    }


@dataclass(frozen=True, slots=True)
class PersonalCapabilityStateAcceptanceAdmission:
    """Fresh PR11.7 issuance basis used when an acceptance enters the set."""

    acceptance: PersonalCapabilityStateAcceptance
    persistence_predecessor: PersonalCapabilityStateSet
    persistence_successor: PersonalCapabilityStateSet

    def __post_init__(self) -> None:
        _exact_type(
            self.acceptance,
            PersonalCapabilityStateAcceptance,
            "acceptance admission acceptance",
        )
        _exact_type(
            self.persistence_predecessor,
            PersonalCapabilityStateSet,
            "acceptance admission persistence_predecessor",
        )
        _exact_type(
            self.persistence_successor,
            PersonalCapabilityStateSet,
            "acceptance admission persistence_successor",
        )


@dataclass(frozen=True, slots=True)
class PersonalCapabilityStateAcceptanceSet:
    """One-subject immutable snapshot of all governed acceptance facts present."""

    subject_ref: CapabilitySubjectRef
    acceptances: tuple[PersonalCapabilityStateAcceptance, ...] = ()

    def __post_init__(self) -> None:
        _subject(self.subject_ref, "acceptance set subject_ref")
        if type(self.acceptances) is not tuple:
            _fail("acceptance set acceptances must be exact tuple")
        for acceptance in self.acceptances:
            _exact_type(
                acceptance,
                PersonalCapabilityStateAcceptance,
                "acceptance set item",
            )
            if acceptance.subject_ref != self.subject_ref:
                _fail("every acceptance must belong to the acceptance set subject")
        if len(set(self.acceptances)) != len(self.acceptances):
            _fail("acceptance set must not contain duplicate acceptance facts")
        object.__setattr__(
            self,
            "acceptances",
            tuple(sorted(self.acceptances, key=_acceptance_sort_key)),
        )


@dataclass(frozen=True, slots=True)
class PersonalCapabilityStateAcceptanceSetSuccessionReceipt:
    """Structural append-only acceptance-universe receipt."""

    predecessor_sha256: str
    successor_sha256: str
    state_snapshot_sha256: str
    subject_ref: CapabilitySubjectRef
    retained_acceptances: tuple[PersonalCapabilityStateAcceptance, ...] = ()
    added_acceptances: tuple[PersonalCapabilityStateAcceptance, ...] = ()

    def __post_init__(self) -> None:
        _validate_sha256(self.predecessor_sha256, "predecessor_sha256")
        _validate_sha256(self.successor_sha256, "successor_sha256")
        _validate_sha256(self.state_snapshot_sha256, "state_snapshot_sha256")
        _subject(self.subject_ref, "acceptance set receipt subject_ref")
        for name, value in (
            ("retained_acceptances", self.retained_acceptances),
            ("added_acceptances", self.added_acceptances),
        ):
            if type(value) is not tuple:
                _fail(f"{name} must be exact tuple")
            if any(type(item) is not PersonalCapabilityStateAcceptance for item in value):
                _fail(f"{name} must contain exact acceptance values")
            if len(set(value)) != len(value):
                _fail(f"{name} must not contain duplicate acceptance facts")
        if set(self.retained_acceptances) & set(self.added_acceptances):
            _fail("retained and added acceptances must be disjoint")

    @property
    def validator_issued(self) -> bool:
        return type(self) is _ValidatorIssuedAcceptanceSetSuccessionReceipt


class _ValidatorIssuedAcceptanceSetSuccessionReceipt(
    PersonalCapabilityStateAcceptanceSetSuccessionReceipt
):
    __slots__ = ()


def _validated_set(
    value: object,
    field_name: str,
) -> PersonalCapabilityStateAcceptanceSet:
    _exact_type(value, PersonalCapabilityStateAcceptanceSet, field_name)
    _subject(value.subject_ref, f"{field_name}.subject_ref")
    if type(value.acceptances) is not tuple:
        _fail(f"{field_name}.acceptances must be exact tuple")
    if any(
        type(item) is not PersonalCapabilityStateAcceptance
        for item in value.acceptances
    ):
        _fail(f"{field_name}.acceptances must contain exact acceptance values")
    if len(set(value.acceptances)) != len(value.acceptances):
        _fail(f"{field_name}.acceptances must not contain duplicates")
    expected_order = tuple(sorted(value.acceptances, key=_acceptance_sort_key))
    if value.acceptances != expected_order:
        _fail(f"{field_name}.acceptances must be canonically ordered")
    if any(item.subject_ref != value.subject_ref for item in value.acceptances):
        _fail(f"{field_name} contains acceptance for another subject")
    return value


def _validated_admissions(
    value: object,
) -> tuple[PersonalCapabilityStateAcceptanceAdmission, ...]:
    if type(value) is not tuple:
        _fail("admissions must be exact tuple")
    if any(type(item) is not PersonalCapabilityStateAcceptanceAdmission for item in value):
        _fail("admissions must contain exact PersonalCapabilityStateAcceptanceAdmission values")
    acceptances = tuple(item.acceptance for item in value)
    if len(set(acceptances)) != len(acceptances):
        _fail("admissions must not duplicate an acceptance fact")
    return value


def _validate_bindings(
    *,
    state_snapshot: PersonalCapabilityStateSet,
    acceptance_set: PersonalCapabilityStateAcceptanceSet,
) -> None:
    for acceptance in acceptance_set.acceptances:
        try:
            validate_personal_capability_state_acceptance_binding_v1(
                snapshot=state_snapshot,
                acceptance=acceptance,
            )
        except StateError as exc:
            raise InvalidPersonalCapabilityStateAcceptanceSet(str(exc)) from exc


def personal_capability_state_acceptance_set_sha256_v1(
    *,
    state_snapshot: PersonalCapabilityStateSet,
    acceptance_set: PersonalCapabilityStateAcceptanceSet,
) -> str:
    """Hash a complete acceptance snapshot after exact durable-binding validation."""

    personal_capability_state_set_sha256_v1(state_snapshot)
    acceptance_set = _validated_set(acceptance_set, "acceptance_set")
    if state_snapshot.subject_ref != acceptance_set.subject_ref:
        _fail("state snapshot and acceptance set must belong to the same subject")
    _validate_bindings(
        state_snapshot=state_snapshot,
        acceptance_set=acceptance_set,
    )
    payload = {
        "subject_ref": acceptance_set.subject_ref.value,
        "acceptances": [
            _acceptance_canonical_payload_v1(item)
            for item in acceptance_set.acceptances
        ],
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    digest = hashlib.sha256()
    digest.update(_ACCEPTANCE_SET_HASH_DOMAIN_V1)
    digest.update(encoded)
    return digest.hexdigest()


def validate_personal_capability_state_acceptance_set_successor_v1(
    *,
    state_snapshot: PersonalCapabilityStateSet,
    predecessor: PersonalCapabilityStateAcceptanceSet,
    successor: PersonalCapabilityStateAcceptanceSet,
    admissions: tuple[PersonalCapabilityStateAcceptanceAdmission, ...] = (),
) -> PersonalCapabilityStateAcceptanceSetSuccessionReceipt:
    """Validate append-only acceptance succession and fresh-admit newly added facts.

    Every acceptance in the resulting universe must still bind the exact persisted
    state. Newly added facts additionally replay their original PR11.7 issuance
    basis. Retained facts deliberately use durable binding rather than pretending
    to replay historical whole-snapshot issuance transitions.
    """

    personal_capability_state_set_sha256_v1(state_snapshot)
    predecessor = _validated_set(predecessor, "predecessor")
    successor = _validated_set(successor, "successor")
    admissions = _validated_admissions(admissions)

    if predecessor.subject_ref != successor.subject_ref:
        _fail("successor must preserve exact acceptance-set subject_ref")
    if successor.subject_ref != state_snapshot.subject_ref:
        _fail("acceptance set and state snapshot must belong to the same subject")

    _validate_bindings(state_snapshot=state_snapshot, acceptance_set=predecessor)
    _validate_bindings(state_snapshot=state_snapshot, acceptance_set=successor)

    predecessor_values = set(predecessor.acceptances)
    successor_values = set(successor.acceptances)
    removed = tuple(sorted(predecessor_values - successor_values, key=_acceptance_sort_key))
    if removed:
        _fail(
            "successor may not remove persisted acceptance fact for state: "
            f"{removed[0].state_id}"
        )

    added = tuple(sorted(successor_values - predecessor_values, key=_acceptance_sort_key))
    admission_by_acceptance = {item.acceptance: item for item in admissions}
    missing_admissions = tuple(item for item in added if item not in admission_by_acceptance)
    if missing_admissions:
        _fail(
            "new acceptance requires fresh PR11.7 issuance-basis admission: "
            f"{missing_admissions[0].state_id}"
        )
    extra_admissions = tuple(
        item for item in admission_by_acceptance if item not in set(added)
    )
    if extra_admissions:
        _fail("admissions may refer only to acceptance facts newly added in this transition")

    for acceptance in added:
        admission = admission_by_acceptance[acceptance]
        try:
            validate_personal_capability_state_acceptance_v1(
                predecessor=admission.persistence_predecessor,
                successor=admission.persistence_successor,
                acceptance=acceptance,
            )
        except StateError as exc:
            raise InvalidPersonalCapabilityStateAcceptanceSet(str(exc)) from exc

    state_snapshot_sha256 = personal_capability_state_set_sha256_v1(state_snapshot)
    predecessor_sha256 = personal_capability_state_acceptance_set_sha256_v1(
        state_snapshot=state_snapshot,
        acceptance_set=predecessor,
    )
    successor_sha256 = personal_capability_state_acceptance_set_sha256_v1(
        state_snapshot=state_snapshot,
        acceptance_set=successor,
    )
    return _ValidatorIssuedAcceptanceSetSuccessionReceipt(
        predecessor_sha256=predecessor_sha256,
        successor_sha256=successor_sha256,
        state_snapshot_sha256=state_snapshot_sha256,
        subject_ref=successor.subject_ref,
        retained_acceptances=tuple(
            sorted(predecessor_values, key=_acceptance_sort_key)
        ),
        added_acceptances=added,
    )
