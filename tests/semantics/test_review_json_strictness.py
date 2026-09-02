import pytest

from capability_lab.semantics import CapabilityCatalog, InvalidCatalogError


def test_duplicate_json_object_keys_rejected() -> None:
    raw = '{"schema":"capability_catalog/v1","namespaces":[],"concepts":[],"concepts":[],"relations":[]}'
    with pytest.raises(InvalidCatalogError):
        CapabilityCatalog.from_json(raw)


def test_nonstandard_json_numeric_constant_rejected() -> None:
    raw = '{"schema":"capability_catalog/v1","namespaces":[],"concepts":[],"relations":[],"x":NaN}'
    with pytest.raises(InvalidCatalogError):
        CapabilityCatalog.from_json(raw)
