"""PR11.3 append-only epistemic snapshot succession governance v1."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

from .core import (
    CapabilityClaimId,
    ClaimEvaluationId,
    EpistemicError,
    EvidenceId,
)
from .record_set import EpistemicRecordSet
from .serialization import record_set_to_json


class EpistemicSnapshotTransitionError(EpistemicError):
    """Base error for governed epistemic snapshot succession."""


class InvalidEpistemicSnapshotSuccessor(EpistemicSnapshotTransitionError):
    """The supplied successor is not an append-only immutable successor."""


_EPISTEMIC_SNAPSHOT_HASH_DOMAIN_V1 = b"capability_lab/epistemic_snapshot@1\x00"
_SHA256_HEX_DIGITS = frozenset("0123456789abcdef")


def _validate_sha256(value: object, field_name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in _SHA256_HEX_DIGITS for character in value)
    ):
        raise InvalidEpistemicSnapshotSuccessor(
            f"{field_name} must be 64 lowercase hexadecimal SHA-256 characters"
        )
    return value


def _validated_id_tuple(
    value: object,
    item_type: type,
    field_name: str,
) -> tuple:
    if isinstance(value, (str, bytes)):
        raise InvalidEpistemicSnapshotSuccessor(
            f"{field_name} must be an iterable of typed ids"
        )
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise InvalidEpistemicSnapshotSuccessor(
            f"{field_name} must be iterable"
        ) from exc
    if any(not isinstance(item, item_type) for item in items):
        raise InvalidEpistemicSnapshotSuccessor(
            f"{field_name} contains an invalid typed id"
        )
    if len(set(items)) != len(items):
        raise InvalidEpistemicSnapshotSuccessor(
            f"{field_name} must not contain duplicate ids"
        )
    return tuple(sorted(items))


@dataclass(frozen=True, slots=True)
class EpistemicSnapshotSuccessionReceipt:
    """Structural succession receipt; validator origin is explicit via a property."""

    predecessor_sha256: str
    successor_sha256: str

    retained_evidence_ids: tuple[EvidenceId, ...] = ()
    added_evidence_ids: tuple[EvidenceId, ...] = ()

    retained_claim_ids: tuple[CapabilityClaimId, ...] = ()
    added_claim_ids: tuple[CapabilityClaimId, ...] = ()

    retained_evaluation_ids: tuple[ClaimEvaluationId, ...] = ()
    added_evaluation_ids: tuple[ClaimEvaluationId, ...] = ()

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
        object.__setattr__(
            self,
            "retained_evidence_ids",
            _validated_id_tuple(
                self.retained_evidence_ids,
                EvidenceId,
                "retained_evidence_ids",
            ),
        )
        object.__setattr__(
            self,
            "added_evidence_ids",
            _validated_id_tuple(
                self.added_evidence_ids,
                EvidenceId,
                "added_evidence_ids",
            ),
        )
        object.__setattr__(
            self,
            "retained_claim_ids",
            _validated_id_tuple(
                self.retained_claim_ids,
                CapabilityClaimId,
                "retained_claim_ids",
            ),
        )
        object.__setattr__(
            self,
            "added_claim_ids",
            _validated_id_tuple(
                self.added_claim_ids,
                CapabilityClaimId,
                "added_claim_ids",
            ),
        )
        object.__setattr__(
            self,
            "retained_evaluation_ids",
            _validated_id_tuple(
                self.retained_evaluation_ids,
                ClaimEvaluationId,
                "retained_evaluation_ids",
            ),
        )
        object.__setattr__(
            self,
            "added_evaluation_ids",
            _validated_id_tuple(
                self.added_evaluation_ids,
                ClaimEvaluationId,
                "added_evaluation_ids",
            ),
        )

    @property
    def validator_issued(self) -> bool:
        """Whether this instance came directly from the PR11.3 validator."""

        return isinstance(self, _ValidatorIssuedEpistemicSnapshotSuccessionReceipt)


class _ValidatorIssuedEpistemicSnapshotSuccessionReceipt(
    EpistemicSnapshotSuccessionReceipt
):
    """Private marker subclass used only by the validated transition path."""

    __slots__ = ()


def epistemic_snapshot_sha256_v1(snapshot: EpistemicRecordSet) -> str:
    """Return a domain-separated hash of the canonical PR2 snapshot JSON."""

    if not isinstance(snapshot, EpistemicRecordSet):
        raise InvalidEpistemicSnapshotSuccessor(
            "snapshot must be EpistemicRecordSet"
        )
    digest = hashlib.sha256()
    digest.update(_EPISTEMIC_SNAPSHOT_HASH_DOMAIN_V1)
    digest.update(record_set_to_json(snapshot).encode("utf-8"))
    return digest.hexdigest()


def _validate_record_family_successor(
    *,
    predecessor_items: tuple,
    successor_items: tuple,
    id_attribute: str,
    removal_label: str,
    mutation_label: str,
) -> tuple[tuple, tuple]:
    predecessor_by_id = {
        getattr(item, id_attribute): item for item in predecessor_items
    }
    successor_by_id = {
        getattr(item, id_attribute): item for item in successor_items
    }

    predecessor_ids = set(predecessor_by_id)
    successor_ids = set(successor_by_id)

    removed_ids = tuple(sorted(predecessor_ids - successor_ids))
    if removed_ids:
        raise InvalidEpistemicSnapshotSuccessor(
            f"successor may not remove {removal_label}: {removed_ids[0]}"
        )

    retained_ids = tuple(sorted(predecessor_ids))
    for record_id in retained_ids:
        if predecessor_by_id[record_id] != successor_by_id[record_id]:
            raise InvalidEpistemicSnapshotSuccessor(
                f"successor may not mutate retained {mutation_label}: {record_id}"
            )

    added_ids = tuple(sorted(successor_ids - predecessor_ids))
    return retained_ids, added_ids


def validate_epistemic_snapshot_successor_v1(
    *,
    predecessor: EpistemicRecordSet,
    successor: EpistemicRecordSet,
) -> EpistemicSnapshotSuccessionReceipt:
    """Validate append-only canonical-content succession between PR2 snapshots.

    This transition does not establish truth, supersession, evaluator preference,
    state selection, state derivation, progression, or presentation authority.
    """

    if not isinstance(predecessor, EpistemicRecordSet):
        raise InvalidEpistemicSnapshotSuccessor(
            "predecessor must be EpistemicRecordSet"
        )
    if not isinstance(successor, EpistemicRecordSet):
        raise InvalidEpistemicSnapshotSuccessor(
            "successor must be EpistemicRecordSet"
        )

    retained_evidence_ids, added_evidence_ids = _validate_record_family_successor(
        predecessor_items=predecessor.evidence_records,
        successor_items=successor.evidence_records,
        id_attribute="evidence_id",
        removal_label="evidence record",
        mutation_label="evidence record",
    )
    retained_claim_ids, added_claim_ids = _validate_record_family_successor(
        predecessor_items=predecessor.claims,
        successor_items=successor.claims,
        id_attribute="claim_id",
        removal_label="capability claim",
        mutation_label="capability claim",
    )
    retained_evaluation_ids, added_evaluation_ids = _validate_record_family_successor(
        predecessor_items=predecessor.evaluations,
        successor_items=successor.evaluations,
        id_attribute="evaluation_id",
        removal_label="claim evaluation",
        mutation_label="claim evaluation",
    )

    return _ValidatorIssuedEpistemicSnapshotSuccessionReceipt(
        predecessor_sha256=epistemic_snapshot_sha256_v1(predecessor),
        successor_sha256=epistemic_snapshot_sha256_v1(successor),
        retained_evidence_ids=retained_evidence_ids,
        added_evidence_ids=added_evidence_ids,
        retained_claim_ids=retained_claim_ids,
        added_claim_ids=added_claim_ids,
        retained_evaluation_ids=retained_evaluation_ids,
        added_evaluation_ids=added_evaluation_ids,
    )
