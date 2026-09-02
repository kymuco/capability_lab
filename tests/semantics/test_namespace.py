import pytest

from capability_lab.semantics import (
    CapabilityNamespace,
    InvalidConceptError,
    InvalidIdentifierError,
)


def test_namespace_normalizes_human_text() -> None:
    namespace = CapabilityNamespace("core", " Core ", " Shared concepts ")
    assert namespace.display_name == "Core"
    assert namespace.description == "Shared concepts"


def test_namespace_supports_unicode_display_name() -> None:
    namespace = CapabilityNamespace("kg.skills", "Кыргыз көндүмдөрү")
    assert namespace.display_name == "Кыргыз көндүмдөрү"


def test_namespace_rejects_empty_display_name() -> None:
    with pytest.raises(InvalidConceptError):
        CapabilityNamespace("core", "   ")


def test_namespace_id_does_not_encode_authority() -> None:
    namespace = CapabilityNamespace("local.a7c392", "Local")
    assert namespace.namespace_id == "local.a7c392"


def test_invalid_namespace_id_rejected() -> None:
    with pytest.raises(InvalidIdentifierError):
        CapabilityNamespace("Canonical", "Canonical")
