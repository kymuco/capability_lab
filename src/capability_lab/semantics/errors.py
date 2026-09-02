"""Errors raised by the shared capability semantics layer."""


class CapabilitySemanticsError(ValueError):
    """Base error for invalid shared capability semantics."""


class InvalidIdentifierError(CapabilitySemanticsError):
    """Raised when a namespace, capability key, or scoped key is invalid."""


class InvalidConceptError(CapabilitySemanticsError):
    """Raised when a capability concept violates v1 invariants."""


class InvalidRelationError(CapabilitySemanticsError):
    """Raised when a capability relation violates v1 invariants."""


class InvalidCatalogError(CapabilitySemanticsError):
    """Raised when a capability catalog is internally inconsistent."""
