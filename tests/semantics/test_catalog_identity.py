import pytest

from capability_lab.semantics import CapabilityCatalog, CapabilityConcept, CapabilityId, CapabilityNamespace, CapabilityRelation, InvalidCatalogError, RelationKind


def concept(namespace: str, key: str) -> CapabilityConcept:
    return CapabilityConcept(CapabilityId(namespace, key), key.title(), f"Definition for {namespace}:{key}")


def test_duplicate_namespace_rejected() -> None:
    with pytest.raises(InvalidCatalogError):
        CapabilityCatalog(namespaces=(CapabilityNamespace("core", "Core"), CapabilityNamespace("core", "Other")))


def test_duplicate_capability_id_rejected() -> None:
    a = concept("core", "a")
    with pytest.raises(InvalidCatalogError):
        CapabilityCatalog(namespaces=(CapabilityNamespace("core", "Core"),), concepts=(a, a))


def test_missing_namespace_rejected() -> None:
    with pytest.raises(InvalidCatalogError):
        CapabilityCatalog(concepts=(concept("missing", "a"),))


def test_dangling_target_rejected() -> None:
    a = concept("core", "a")
    with pytest.raises(InvalidCatalogError):
        CapabilityCatalog(
            namespaces=(CapabilityNamespace("core", "Core"),),
            concepts=(a,),
            relations=(CapabilityRelation(a.capability_id, CapabilityId("core", "missing"), RelationKind.REQUIRES),),
        )


def test_cross_namespace_relation_is_valid() -> None:
    algebra = concept("math", "algebra")
    circuits = concept("electronics", "circuits")
    catalog = CapabilityCatalog(
        namespaces=(CapabilityNamespace("math", "Math"), CapabilityNamespace("electronics", "Electronics")),
        concepts=(circuits, algebra),
        relations=(CapabilityRelation(circuits.capability_id, algebra.capability_id, RelationKind.REQUIRES),),
    )
    assert len(catalog.relations) == 1
