"""PR12.0 append-only succession governance for external observation ledgers."""

from __future__ import annotations

from dataclasses import dataclass
import re

from .core import (
    ExternalObservationId,
    ExternalObservationLedger,
    InvalidExternalObservationLedger,
    external_observation_ledger_sha256_v1,
    validate_external_observation_ledger_v1,
)


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _fail(message: str) -> None:
    raise InvalidExternalObservationLedger(message)


def _sha256(value: object, label: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        _fail(f"{label} must be 64 lowercase hexadecimal SHA-256 characters")
    return value


def _id_tuple(value: object, label: str) -> tuple[ExternalObservationId, ...]:
    if type(value) is not tuple:
        _fail(f"{label} must be exact tuple")
    if any(type(item) is not ExternalObservationId for item in value):
        _fail(f"{label} must contain exact ExternalObservationId values")
    if len(set(value)) != len(value):
        _fail(f"{label} must not contain duplicate observation ids")
    return tuple(sorted(value))


@dataclass(frozen=True, slots=True)
class ExternalObservationLedgerSuccessionReceipt:
    predecessor_sha256: str
    successor_sha256: str
    retained_observation_ids: tuple[ExternalObservationId, ...] = ()
    added_observation_ids: tuple[ExternalObservationId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "predecessor_sha256",
            _sha256(self.predecessor_sha256, "predecessor_sha256"),
        )
        object.__setattr__(
            self,
            "successor_sha256",
            _sha256(self.successor_sha256, "successor_sha256"),
        )
        retained = _id_tuple(
            self.retained_observation_ids,
            "retained_observation_ids",
        )
        added = _id_tuple(
            self.added_observation_ids,
            "added_observation_ids",
        )
        if set(retained) & set(added):
            _fail(
                "retained_observation_ids and added_observation_ids "
                "must be disjoint"
            )
        object.__setattr__(
            self,
            "retained_observation_ids",
            retained,
        )
        object.__setattr__(
            self,
            "added_observation_ids",
            added,
        )

    @property
    def validator_issued(self) -> bool:
        return isinstance(
            self,
            _ValidatorIssuedExternalObservationLedgerSuccessionReceipt,
        )


class _ValidatorIssuedExternalObservationLedgerSuccessionReceipt(
    ExternalObservationLedgerSuccessionReceipt
):
    __slots__ = ()


def validate_external_observation_ledger_successor_v1(
    *,
    predecessor: ExternalObservationLedger,
    successor: ExternalObservationLedger,
) -> ExternalObservationLedgerSuccessionReceipt:
    """Validate immutable append-only succession without granting evidence authority."""

    validate_external_observation_ledger_v1(predecessor)
    validate_external_observation_ledger_v1(successor)

    if predecessor.subject_ref != successor.subject_ref:
        _fail("successor ledger subject_ref must equal predecessor subject_ref")

    predecessor_by_id = {
        item.observation_id: item for item in predecessor.observations
    }
    successor_by_id = {
        item.observation_id: item for item in successor.observations
    }

    predecessor_ids = set(predecessor_by_id)
    successor_ids = set(successor_by_id)

    removed = tuple(sorted(predecessor_ids - successor_ids))
    if removed:
        _fail(
            "successor may not remove retained external observation: "
            f"{removed[0]}"
        )

    retained = tuple(sorted(predecessor_ids))
    for observation_id in retained:
        if predecessor_by_id[observation_id] != successor_by_id[observation_id]:
            _fail(
                "successor may not mutate retained external observation: "
                f"{observation_id}"
            )

    added = tuple(sorted(successor_ids - predecessor_ids))

    return _ValidatorIssuedExternalObservationLedgerSuccessionReceipt(
        predecessor_sha256=external_observation_ledger_sha256_v1(predecessor),
        successor_sha256=external_observation_ledger_sha256_v1(successor),
        retained_observation_ids=retained,
        added_observation_ids=added,
    )
