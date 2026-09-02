"""Shared, person-agnostic capability semantics."""

from .catalog import CapabilityCatalog
from .concept import CapabilityConcept, ConceptLifecycle
from .errors import (
    CapabilitySemanticsError,
    InvalidCatalogError,
    InvalidConceptError,
    InvalidIdentifierError,
    InvalidRelationError,
)
from .ids import CapabilityId
from .namespace import CapabilityNamespace
from .reference import CapabilityConceptRef
from .relation import (
    CapabilityRelation,
    RelationFamily,
    RelationKind,
    RelationScope,
    RelationStrength,
)

__all__ = [
    "CapabilityCatalog",
    "CapabilityConcept",
    "CapabilityConceptRef",
    "CapabilityId",
    "CapabilityNamespace",
    "CapabilityRelation",
    "CapabilitySemanticsError",
    "ConceptLifecycle",
    "InvalidCatalogError",
    "InvalidConceptError",
    "InvalidIdentifierError",
    "InvalidRelationError",
    "RelationFamily",
    "RelationKind",
    "RelationScope",
    "RelationStrength",
]
