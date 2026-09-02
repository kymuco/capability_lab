import pytest

from capability_lab.semantics import CapabilityCatalog, InvalidCatalogError


def payload():
    return {"schema": "capability_catalog/v1", "namespaces": [], "concepts": [], "relations": []}


def test_unknown_root_field_rejected() -> None:
    value = payload()
    value["conceptz"] = []
    with pytest.raises(InvalidCatalogError):
        CapabilityCatalog.from_dict(value)


def test_unknown_nested_field_rejected() -> None:
    value = payload()
    value["namespaces"] = [
        {"namespace_id": "core", "display_name": "Core", "authority": "canonical"}
    ]
    with pytest.raises(InvalidCatalogError):
        CapabilityCatalog.from_dict(value)


def test_catalog_arrays_must_be_arrays() -> None:
    value = payload()
    value["namespaces"] = "core"
    with pytest.raises(InvalidCatalogError):
        CapabilityCatalog.from_dict(value)


def test_aliases_must_be_array_not_string() -> None:
    value = payload()
    value["namespaces"] = [{"namespace_id": "core", "display_name": "Core"}]
    value["concepts"] = [
        {"capability_id": "core:a", "name": "A", "definition": "A", "aliases": "Alias"}
    ]
    with pytest.raises(InvalidCatalogError):
        CapabilityCatalog.from_dict(value)


def test_typoed_relation_field_is_not_ignored() -> None:
    value = payload()
    value["namespaces"] = [{"namespace_id": "core", "display_name": "Core"}]
    value["concepts"] = [
        {"capability_id": "core:a", "name": "A", "definition": "A"},
        {"capability_id": "core:b", "name": "B", "definition": "B"},
    ]
    value["relations"] = [
        {"source_id": "core:a", "target_id": "core:b", "kind": "requires", "strenght": "strict"}
    ]
    with pytest.raises(InvalidCatalogError):
        CapabilityCatalog.from_dict(value)
