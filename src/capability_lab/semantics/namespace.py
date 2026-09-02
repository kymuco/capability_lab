"""Namespace records for shared capability identifiers."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import InvalidConceptError
from .ids import validate_namespace_id


@dataclass(frozen=True, order=True, slots=True)
class CapabilityNamespace:
    """Collision boundary for capability identities, not an authority level."""

    namespace_id: str
    display_name: str
    description: str = ""

    def __post_init__(self) -> None:
        validate_namespace_id(self.namespace_id)
        if not isinstance(self.display_name, str):
            raise InvalidConceptError("namespace display_name must be a string")
        if not isinstance(self.description, str):
            raise InvalidConceptError("namespace description must be a string")
        display_name = self.display_name.strip()
        description = self.description.strip()
        if not display_name:
            raise InvalidConceptError("namespace display_name must be non-empty")
        object.__setattr__(self, "display_name", display_name)
        object.__setattr__(self, "description", description)
