import pytest

from capability_lab.semantics import CapabilityCatalog, CapabilityConcept, CapabilityId, CapabilityNamespace, CapabilityRelation, InvalidCatalogError, RelationKind


def concept(key: str) -> CapabilityConcept:
    return CapabilityConcept(CapabilityId("core", key), key.upper(), f"Definition for core:{key}")


def test_specialization_cycle_rejected() -> None:
    a, b, c = concept("a"), concept("b"), concept("c")
    with pytest.raises(InvalidCatalogError, match="acyclic"):
        CapabilityCatalog(
            namespaces=(CapabilityNamespace("core", "Core"),),
            concepts=(a, b, c),
            relations=(
                CapabilityRelation(a.capability_id, b.capability_id, RelationKind.SPECIALIZES),
                CapabilityRelation(b.capability_id, c.capability_id, RelationKind.SPECIALIZES),
                CapabilityRelation(c.capability_id, a.capability_id, RelationKind.SPECIALIZES),
            ),
        )


def test_dependency_cycle_is_allowed() -> None:
    a, b = concept("a"), concept("b")
    catalog = CapabilityCatalog(
        namespaces=(CapabilityNamespace("core", "Core"),),
        concepts=(a, b),
        relations=(
            CapabilityRelation(a.capability_id, b.capability_id, RelationKind.SUPPORTED_BY),
            CapabilityRelation(b.capability_id, a.capability_id, RelationKind.SUPPORTED_BY),
        ),
    )
    assert len(catalog.relations) == 2


def test_long_specialization_chain_does_not_depend_on_python_recursion_limit() -> None:
    concepts = tuple(concept(f"n{index}") for index in range(1500))
    relations = tuple(
        CapabilityRelation(
            concepts[index].capability_id,
            concepts[index + 1].capability_id,
            RelationKind.SPECIALIZES,
        )
        for index in range(len(concepts) - 1)
    )
    catalog = CapabilityCatalog(
        namespaces=(CapabilityNamespace("core", "Core"),),
        concepts=concepts,
        relations=relations,
    )
    assert len(catalog.concepts) == 1500


def test_catalog_sorts_concepts_deterministically() -> None:
    a, b = concept("a"), concept("b")
    catalog = CapabilityCatalog(namespaces=(CapabilityNamespace("core", "Core"),), concepts=(b, a))
    assert [item.capability_id for item in catalog.concepts] == [a.capability_id, b.capability_id]
