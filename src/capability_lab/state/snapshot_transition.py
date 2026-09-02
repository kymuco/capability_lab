"""PR11.6 append-only personal capability state snapshot succession governance v1."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib

from capability_lab.epistemics import (
    CapabilityClaimId,
    CapabilitySubjectRef,
    ClaimEvaluationId,
)
from capability_lab.semantics import CapabilityConceptRef, CapabilityId

from .core import (
    CompetenceDimensionState,
    CompetenceFrameId,
    CompetenceFrameRef,
    DimensionConflictStatus,
    DimensionStanding,
    PersonalCapabilityState,
    PersonalCapabilityStateId,
    PersonalCapabilityStateSet,
    StateDerivationPolicyRef,
    StateDeriverKind,
    StateDeriverRef,
    StateError,
)


class StateSnapshotTransitionError(StateError):
    """Base error for governed personal capability state snapshot succession."""


class InvalidPersonalCapabilityStateSetSuccessor(StateSnapshotTransitionError):
    """The supplied state-set successor is not append-only and immutable."""


_STATE_SNAPSHOT_HASH_DOMAIN_V1 = (
    b"capability_lab/personal_capability_state_set@1\x00"
)
_SHA256_HEX_DIGITS = frozenset("0123456789abcdef")


def _validate_sha256(value: object, field_name: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in _SHA256_HEX_DIGITS for character in value)
    ):
        raise InvalidPersonalCapabilityStateSetSuccessor(
            f"{field_name} must be 64 lowercase hexadecimal SHA-256 characters"
        )
    return value


def _exact_type(value: object, expected_type: type, field_name: str) -> None:
    if type(value) is not expected_type:
        raise InvalidPersonalCapabilityStateSetSuccessor(
            f"{field_name} must use its exact core value type: {expected_type.__name__}"
        )


def _exact_primitive(value: object, expected_type: type, field_name: str) -> None:
    if type(value) is not expected_type:
        raise InvalidPersonalCapabilityStateSetSuccessor(
            f"{field_name} must be exact {expected_type.__name__}"
        )


def _exact_opaque_value(
    value: object,
    expected_type: type,
    field_name: str,
) -> None:
    _exact_type(value, expected_type, field_name)
    _exact_primitive(value.value, str, f"{field_name}.value")


def _validated_state_id_tuple(
    value: object,
    field_name: str,
) -> tuple[PersonalCapabilityStateId, ...]:
    if isinstance(value, (str, bytes)):
        raise InvalidPersonalCapabilityStateSetSuccessor(
            f"{field_name} must be an iterable of PersonalCapabilityStateId values"
        )
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise InvalidPersonalCapabilityStateSetSuccessor(
            f"{field_name} must be iterable"
        ) from exc
    for index, item in enumerate(items):
        if type(item) is not PersonalCapabilityStateId:
            raise InvalidPersonalCapabilityStateSetSuccessor(
                f"{field_name} contains an invalid state id"
            )
        _exact_primitive(item.value, str, f"{field_name}[{index}].value")
    if len(set(items)) != len(items):
        raise InvalidPersonalCapabilityStateSetSuccessor(
            f"{field_name} must not contain duplicate state ids"
        )
    return tuple(sorted(items))


def _validate_exact_state_value_graph(
    state: PersonalCapabilityState,
    field_name: str,
) -> None:
    _exact_type(state.state_id, PersonalCapabilityStateId, f"{field_name}.state_id")
    _exact_primitive(state.state_id.value, str, f"{field_name}.state_id.value")

    _exact_type(state.subject_ref, CapabilitySubjectRef, f"{field_name}.subject_ref")
    _exact_primitive(state.subject_ref.value, str, f"{field_name}.subject_ref.value")

    concept_ref = state.concept_ref
    _exact_type(concept_ref, CapabilityConceptRef, f"{field_name}.concept_ref")
    _exact_type(
        concept_ref.capability_id,
        CapabilityId,
        f"{field_name}.concept_ref.capability_id",
    )
    _exact_primitive(
        concept_ref.capability_id.namespace,
        str,
        f"{field_name}.concept_ref.capability_id.namespace",
    )
    _exact_primitive(
        concept_ref.capability_id.key,
        str,
        f"{field_name}.concept_ref.capability_id.key",
    )
    _exact_primitive(concept_ref.revision, int, f"{field_name}.concept_ref.revision")

    frame_ref = state.frame_ref
    _exact_type(frame_ref, CompetenceFrameRef, f"{field_name}.frame_ref")
    _exact_type(
        frame_ref.frame_id,
        CompetenceFrameId,
        f"{field_name}.frame_ref.frame_id",
    )
    _exact_primitive(
        frame_ref.frame_id.namespace,
        str,
        f"{field_name}.frame_ref.frame_id.namespace",
    )
    _exact_primitive(
        frame_ref.frame_id.key,
        str,
        f"{field_name}.frame_ref.frame_id.key",
    )
    _exact_primitive(frame_ref.revision, int, f"{field_name}.frame_ref.revision")

    policy_ref = state.derivation_policy_ref
    _exact_type(
        policy_ref,
        StateDerivationPolicyRef,
        f"{field_name}.derivation_policy_ref",
    )
    _exact_primitive(
        policy_ref.namespace,
        str,
        f"{field_name}.derivation_policy_ref.namespace",
    )
    _exact_primitive(policy_ref.key, str, f"{field_name}.derivation_policy_ref.key")
    _exact_primitive(
        policy_ref.revision,
        int,
        f"{field_name}.derivation_policy_ref.revision",
    )

    deriver_ref = state.deriver_ref
    _exact_type(deriver_ref, StateDeriverRef, f"{field_name}.deriver_ref")
    _exact_type(deriver_ref.kind, StateDeriverKind, f"{field_name}.deriver_ref.kind")
    _exact_primitive(
        deriver_ref.kind.value,
        str,
        f"{field_name}.deriver_ref.kind.value",
    )
    _exact_primitive(deriver_ref.ref, str, f"{field_name}.deriver_ref.ref")

    _exact_type(state.as_of, datetime, f"{field_name}.as_of")
    _exact_type(state.derived_at, datetime, f"{field_name}.derived_at")

    _exact_primitive(state.dimensions, tuple, f"{field_name}.dimensions")
    for index, dimension in enumerate(state.dimensions):
        path = f"{field_name}.dimensions[{index}]"
        _exact_type(dimension, CompetenceDimensionState, path)
        _exact_primitive(dimension.dimension_key, str, f"{path}.dimension_key")
        _exact_type(dimension.standing, DimensionStanding, f"{path}.standing")
        _exact_primitive(dimension.standing.value, str, f"{path}.standing.value")
        _exact_type(
            dimension.conflict_status,
            DimensionConflictStatus,
            f"{path}.conflict_status",
        )
        _exact_primitive(
            dimension.conflict_status.value,
            str,
            f"{path}.conflict_status.value",
        )
        _exact_primitive(
            dimension.supported_claim_ids,
            tuple,
            f"{path}.supported_claim_ids",
        )
        _exact_primitive(
            dimension.basis_evaluation_ids,
            tuple,
            f"{path}.basis_evaluation_ids",
        )
        for claim_index, claim_id in enumerate(dimension.supported_claim_ids):
            _exact_opaque_value(
                claim_id,
                CapabilityClaimId,
                f"{path}.supported_claim_ids[{claim_index}]",
            )
        for evaluation_index, evaluation_id in enumerate(
            dimension.basis_evaluation_ids
        ):
            _exact_opaque_value(
                evaluation_id,
                ClaimEvaluationId,
                f"{path}.basis_evaluation_ids[{evaluation_index}]",
            )
        _exact_primitive(dimension.rationale, str, f"{path}.rationale")

    _exact_primitive(state.rationale, str, f"{field_name}.rationale")


def _validated_exact_snapshot(
    value: object,
    field_name: str,
) -> PersonalCapabilityStateSet:
    if type(value) is not PersonalCapabilityStateSet:
        raise InvalidPersonalCapabilityStateSetSuccessor(
            f"{field_name} must be PersonalCapabilityStateSet"
        )
    if type(value.subject_ref) is not CapabilitySubjectRef:
        raise InvalidPersonalCapabilityStateSetSuccessor(
            f"{field_name} subject_ref must be exact CapabilitySubjectRef"
        )
    _exact_primitive(value.subject_ref.value, str, f"{field_name}.subject_ref.value")
    _exact_primitive(value.states, tuple, f"{field_name}.states")
    if any(type(state) is not PersonalCapabilityState for state in value.states):
        raise InvalidPersonalCapabilityStateSetSuccessor(
            f"{field_name} states must contain exact PersonalCapabilityState values"
        )
    for index, state in enumerate(value.states):
        _validate_exact_state_value_graph(state, f"{field_name}.states[{index}]")
        if state.subject_ref != value.subject_ref:
            raise InvalidPersonalCapabilityStateSetSuccessor(
                f"{field_name}.states[{index}] subject_ref must match state-set subject_ref"
            )
    return value


@dataclass(frozen=True, slots=True)
class PersonalCapabilityStateSetSuccessionReceipt:
    """Structural state-snapshot succession receipt, not state authority."""

    predecessor_sha256: str
    successor_sha256: str
    subject_ref: CapabilitySubjectRef
    retained_state_ids: tuple[PersonalCapabilityStateId, ...] = ()
    added_state_ids: tuple[PersonalCapabilityStateId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "predecessor_sha256",
            _validate_sha256(self.predecessor_sha256, "predecessor_sha256"),
        )
        object.__setattr__(
            self,
            "successor_sha256",
            _validate_sha256(self.successor_sha256, "successor_sha256"),
        )
        if type(self.subject_ref) is not CapabilitySubjectRef:
            raise InvalidPersonalCapabilityStateSetSuccessor(
                "subject_ref must be CapabilitySubjectRef"
            )
        _exact_primitive(self.subject_ref.value, str, "subject_ref.value")
        object.__setattr__(
            self,
            "retained_state_ids",
            _validated_state_id_tuple(
                self.retained_state_ids,
                "retained_state_ids",
            ),
        )
        object.__setattr__(
            self,
            "added_state_ids",
            _validated_state_id_tuple(
                self.added_state_ids,
                "added_state_ids",
            ),
        )
        overlap = set(self.retained_state_ids) & set(self.added_state_ids)
        if overlap:
            first = min(overlap)
            raise InvalidPersonalCapabilityStateSetSuccessor(
                f"retained_state_ids and added_state_ids must be disjoint: {first}"
            )


def personal_capability_state_set_sha256_v1(
    snapshot: PersonalCapabilityStateSet,
) -> str:
    """Return a domain-separated hash of canonical PR3 state-set JSON."""

    snapshot = _validated_exact_snapshot(snapshot, "snapshot")
    digest = hashlib.sha256()
    digest.update(_STATE_SNAPSHOT_HASH_DOMAIN_V1)
    digest.update(snapshot.to_json().encode("utf-8"))
    return digest.hexdigest()


def validate_personal_capability_state_set_successor_v1(
    *,
    predecessor: PersonalCapabilityStateSet,
    successor: PersonalCapabilityStateSet,
) -> PersonalCapabilityStateSetSuccessionReceipt:
    """Validate append-only canonical-content succession between state snapshots.

    The transition binds persisted state identity to exact immutable state content.
    It does not establish derivation provenance, acceptance, current-state selection,
    progression authority, history qualification, or presentation authority.
    """

    predecessor = _validated_exact_snapshot(predecessor, "predecessor")
    successor = _validated_exact_snapshot(successor, "successor")
    if predecessor.subject_ref != successor.subject_ref:
        raise InvalidPersonalCapabilityStateSetSuccessor(
            "successor must preserve exact state-set subject_ref"
        )

    predecessor_by_id = {item.state_id: item for item in predecessor.states}
    successor_by_id = {item.state_id: item for item in successor.states}
    predecessor_ids = set(predecessor_by_id)
    successor_ids = set(successor_by_id)

    removed_ids = tuple(sorted(predecessor_ids - successor_ids))
    if removed_ids:
        raise InvalidPersonalCapabilityStateSetSuccessor(
            f"successor may not remove persisted state: {removed_ids[0]}"
        )

    retained_ids = tuple(sorted(predecessor_ids))
    for state_id in retained_ids:
        if predecessor_by_id[state_id] != successor_by_id[state_id]:
            raise InvalidPersonalCapabilityStateSetSuccessor(
                f"successor may not mutate retained state: {state_id}"
            )

    added_ids = tuple(sorted(successor_ids - predecessor_ids))
    return PersonalCapabilityStateSetSuccessionReceipt(
        predecessor_sha256=personal_capability_state_set_sha256_v1(predecessor),
        successor_sha256=personal_capability_state_set_sha256_v1(successor),
        subject_ref=predecessor.subject_ref,
        retained_state_ids=retained_ids,
        added_state_ids=added_ids,
    )
