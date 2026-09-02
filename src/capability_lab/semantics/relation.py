"""Typed relations between shared capability concepts."""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from .errors import InvalidRelationError
from .ids import CapabilityId, validate_key


class RelationFamily(str, Enum):
    STRUCTURAL = "structural"
    DEPENDENCY = "dependency"
    EMPIRICAL_DEVELOPMENT = "empirical_development"


class RelationKind(str, Enum):
    SPECIALIZES = "specializes"
    OVERLAPS = "overlaps"
    REQUIRES = "requires"
    SUPPORTED_BY = "supported_by"
    ENABLED_BY = "enabled_by"
    COMMONLY_PRECEDES = "commonly_precedes"
    COMMONLY_COOCCURS = "commonly_cooccurs"
    TRANSFER_OBSERVED_TO = "transfer_observed_to"

    @property
    def family(self) -> RelationFamily:
        return _RELATION_FAMILY[self]

    @property
    def is_symmetric(self) -> bool:
        return self in _SYMMETRIC_KINDS


_RELATION_FAMILY = {
    RelationKind.SPECIALIZES: RelationFamily.STRUCTURAL,
    RelationKind.OVERLAPS: RelationFamily.STRUCTURAL,
    RelationKind.REQUIRES: RelationFamily.DEPENDENCY,
    RelationKind.SUPPORTED_BY: RelationFamily.DEPENDENCY,
    RelationKind.ENABLED_BY: RelationFamily.DEPENDENCY,
    RelationKind.COMMONLY_PRECEDES: RelationFamily.EMPIRICAL_DEVELOPMENT,
    RelationKind.COMMONLY_COOCCURS: RelationFamily.EMPIRICAL_DEVELOPMENT,
    RelationKind.TRANSFER_OBSERVED_TO: RelationFamily.EMPIRICAL_DEVELOPMENT,
}
_SYMMETRIC_KINDS = {RelationKind.OVERLAPS, RelationKind.COMMONLY_COOCCURS}
if set(_RELATION_FAMILY) != set(RelationKind):
    raise RuntimeError("every RelationKind must map to exactly one RelationFamily")


class RelationStrength(str, Enum):
    UNSPECIFIED = "unspecified"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"

    @property
    def rank(self) -> int | None:
        return {self.UNSPECIFIED: None, self.WEAK: 1, self.MODERATE: 2, self.STRONG: 3}[self]


@dataclass(frozen=True, order=True, slots=True)
class RelationScope:
    key: str
    description: str

    def __post_init__(self) -> None:
        validate_key(self.key, field_name="relation scope key")
        if not isinstance(self.description, str):
            raise InvalidRelationError("relation scope description must be a string")
        description = self.description.strip()
        if not description:
            raise InvalidRelationError("relation scope description must be non-empty")
        object.__setattr__(self, "description", description)


@dataclass(frozen=True, slots=True)
class CapabilityRelation:
    source_id: CapabilityId
    target_id: CapabilityId
    kind: RelationKind
    scope: RelationScope | None = None
    strength: RelationStrength = RelationStrength.UNSPECIFIED
    provenance_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, CapabilityId) or not isinstance(self.target_id, CapabilityId):
            raise InvalidRelationError("relation endpoints must be CapabilityId values")
        if not isinstance(self.kind, RelationKind):
            raise InvalidRelationError("relation kind must be a RelationKind")
        if self.scope is not None and not isinstance(self.scope, RelationScope):
            raise InvalidRelationError("relation scope must be a RelationScope or None")
        if not isinstance(self.strength, RelationStrength):
            raise InvalidRelationError("relation strength must be a RelationStrength")
        if self.source_id == self.target_id:
            raise InvalidRelationError("self-relations are not valid in semantics v1")

        source_id, target_id = self.source_id, self.target_id
        if self.kind.is_symmetric and target_id < source_id:
            source_id, target_id = target_id, source_id

        if isinstance(self.provenance_refs, (str, bytes)):
            raise InvalidRelationError("provenance_refs must be an iterable of strings, not a string")
        try:
            raw_refs = tuple(self.provenance_refs)
        except TypeError as exc:
            raise InvalidRelationError("provenance_refs must be an iterable of strings") from exc
        refs = []
        seen = set()
        for ref in raw_refs:
            if not isinstance(ref, str):
                raise InvalidRelationError("provenance references must be strings")
            cleaned = ref.strip()
            if not cleaned:
                raise InvalidRelationError("provenance references must be non-empty")
            if cleaned in seen:
                raise InvalidRelationError(f"duplicate provenance reference: {cleaned!r}")
            seen.add(cleaned)
            refs.append(cleaned)
        provenance_refs = tuple(sorted(refs))

        if self.kind.family is RelationFamily.STRUCTURAL:
            if self.scope is not None or self.strength is not RelationStrength.UNSPECIFIED:
                raise InvalidRelationError("structural relations do not accept scope or strength in v1")
        if self.kind.family is RelationFamily.EMPIRICAL_DEVELOPMENT:
            if not provenance_refs:
                raise InvalidRelationError("empirical development relations require provenance_refs")
            if self.strength is not RelationStrength.UNSPECIFIED:
                raise InvalidRelationError("empirical development relations do not use ordinal strength in v1")
        if self.kind in {RelationKind.REQUIRES, RelationKind.ENABLED_BY} and self.strength is not RelationStrength.UNSPECIFIED:
            raise InvalidRelationError(f"{self.kind.value} is categorical and does not accept ordinal strength in v1")

        object.__setattr__(self, "source_id", source_id)
        object.__setattr__(self, "target_id", target_id)
        object.__setattr__(self, "provenance_refs", provenance_refs)

    @property
    def semantic_key(self) -> tuple[str, str, str, str]:
        return (str(self.source_id), self.kind.value, str(self.target_id), self.scope.key if self.scope else "")

    @property
    def deterministic_key(self) -> tuple[str, ...]:
        return (*self.semantic_key, self.scope.description if self.scope else "", self.strength.value, *self.provenance_refs)
