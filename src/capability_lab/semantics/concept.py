"""Shared capability concept model."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import unicodedata

from .errors import InvalidConceptError
from .ids import CapabilityId
from .reference import CapabilityConceptRef, validate_revision


class ConceptLifecycle(str, Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"


def _text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise InvalidConceptError(f"{field_name} must be a string")
    value = unicodedata.normalize("NFC", value).strip()
    if not value:
        raise InvalidConceptError(f"{field_name} must be non-empty")
    return value


@dataclass(frozen=True, slots=True)
class CapabilityConcept:
    """Reusable semantics with no assertion about any particular person."""

    capability_id: CapabilityId
    name: str
    definition: str
    aliases: tuple[str, ...] = ()
    revision: int = 1
    lifecycle: ConceptLifecycle = ConceptLifecycle.ACTIVE
    deprecation_note: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.capability_id, CapabilityId):
            raise InvalidConceptError("concept capability_id must be a CapabilityId")
        if not isinstance(self.lifecycle, ConceptLifecycle):
            raise InvalidConceptError("concept lifecycle must be a ConceptLifecycle")

        name = _text(self.name, "concept name")
        definition = _text(self.definition, "concept definition")
        revision = validate_revision(self.revision)

        if isinstance(self.aliases, (str, bytes)):
            raise InvalidConceptError("aliases must be an iterable of strings, not a string")
        try:
            raw_aliases = tuple(self.aliases)
        except TypeError as exc:
            raise InvalidConceptError("aliases must be an iterable of strings") from exc

        normalized_aliases: list[str] = []
        seen: set[str] = set()
        for alias in raw_aliases:
            cleaned = _text(alias, "alias")
            if cleaned == name:
                raise InvalidConceptError("alias must not duplicate the primary concept name")
            if cleaned in seen:
                raise InvalidConceptError(f"duplicate alias: {cleaned!r}")
            seen.add(cleaned)
            normalized_aliases.append(cleaned)

        aliases = tuple(sorted(normalized_aliases))
        note = None if self.deprecation_note is None else _text(self.deprecation_note, "deprecation_note")
        if self.lifecycle is ConceptLifecycle.DEPRECATED and note is None:
            raise InvalidConceptError("deprecated concepts require a non-empty deprecation_note")
        if self.lifecycle is ConceptLifecycle.ACTIVE and note is not None:
            raise InvalidConceptError("active concepts must not carry a deprecation_note")

        object.__setattr__(self, "name", name)
        object.__setattr__(self, "definition", definition)
        object.__setattr__(self, "aliases", aliases)
        object.__setattr__(self, "revision", revision)
        object.__setattr__(self, "deprecation_note", note)

    @property
    def ref(self) -> CapabilityConceptRef:
        return CapabilityConceptRef(self.capability_id, self.revision)
