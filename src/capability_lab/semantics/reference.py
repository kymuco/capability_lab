"""Exact references to versioned shared capability semantics."""

from __future__ import annotations

from dataclasses import dataclass
import re

from .errors import InvalidConceptError
from .ids import CapabilityId

_REVISION_RE = re.compile(r"^[1-9][0-9]*$")


def validate_revision(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise InvalidConceptError("concept revision must be an integer >= 1")
    return value


@dataclass(frozen=True, order=True, slots=True)
class CapabilityConceptRef:
    """Exact reference to one semantic revision of a capability concept."""

    capability_id: CapabilityId
    revision: int

    def __post_init__(self) -> None:
        if not isinstance(self.capability_id, CapabilityId):
            raise InvalidConceptError("concept reference capability_id must be a CapabilityId")
        validate_revision(self.revision)

    @classmethod
    def parse(cls, value: str) -> "CapabilityConceptRef":
        if not isinstance(value, str) or value.count("@") != 1:
            raise InvalidConceptError("concept reference must use '<namespace>:<key>@<revision>'")
        raw_id, raw_revision = value.rsplit("@", 1)
        if not _REVISION_RE.fullmatch(raw_revision):
            raise InvalidConceptError("concept reference revision must use canonical positive ASCII decimal syntax")
        return cls(CapabilityId.parse(raw_id), int(raw_revision))

    def __str__(self) -> str:
        return f"{self.capability_id}@{self.revision}"
