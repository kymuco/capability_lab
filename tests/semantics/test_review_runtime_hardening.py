import pytest

from capability_lab.semantics import CapabilityCatalog, CapabilityConcept, CapabilityId, CapabilityNamespace, CapabilityRelation, InvalidCatalogError, InvalidConceptError, InvalidRelationError, RelationKind, RelationStrength
from capability_lab.semantics.reference import CapabilityConceptRef

A = CapabilityId("core", "a")
B = CapabilityId("core", "b")


def test_versioned_concept_ref_roundtrip() -> None:
    ref = CapabilityConceptRef(A, 3)
    assert str(ref) == "core:a@3"
    assert CapabilityConceptRef.parse(str(ref)) == ref


@pytest.mark.parametrize("value", ["core:a@01", "core:a@0", "core:a@١", "core:a@+1"])
def test_versioned_concept_ref_rejects_noncanonical_syntax(value: str) -> None:
    with pytest.raises(InvalidConceptError):
        CapabilityConceptRef.parse(value)


@pytest.mark.parametrize("revision", [0, -1, True, 1.5])
def test_versioned_concept_ref_rejects_invalid_revision(revision) -> None:
    with pytest.raises(InvalidConceptError):
        CapabilityConceptRef(A, revision)


def test_concept_exposes_exact_revision_ref() -> None:
    assert CapabilityConcept(A, "A", "Definition", revision=4).ref == CapabilityConceptRef(A, 4)


def test_concept_rejects_runtime_type_holes() -> None:
    with pytest.raises(InvalidConceptError):
        CapabilityConcept(A, "A", "Definition", lifecycle="deprecated")
    with pytest.raises(InvalidConceptError):
        CapabilityConcept(A, "A", "Definition", aliases="Alias")
    with pytest.raises(InvalidConceptError):
        CapabilityConcept("core:a", "A", "Definition")


def test_namespace_rejects_non_string_metadata() -> None:
    with pytest.raises(InvalidConceptError):
        CapabilityNamespace("core", 123)
    with pytest.raises(InvalidConceptError):
        CapabilityNamespace("core", "Core", description=123)


def test_relation_rejects_runtime_type_holes() -> None:
    with pytest.raises(InvalidRelationError):
        CapabilityRelation(A, B, "requires")
    with pytest.raises(InvalidRelationError):
        CapabilityRelation(A, B, RelationKind.REQUIRES, strength="strong")
    with pytest.raises(InvalidRelationError):
        CapabilityRelation("core:a", B, RelationKind.REQUIRES)
    with pytest.raises(InvalidRelationError):
        CapabilityRelation(A, B, RelationKind.REQUIRES, scope="dc")


def test_relation_rejects_provenance_string_container() -> None:
    with pytest.raises(InvalidRelationError):
        CapabilityRelation(A, B, RelationKind.COMMONLY_PRECEDES, provenance_refs="study:1")


def test_ordinal_strength_is_only_for_supported_by() -> None:
    with pytest.raises(InvalidRelationError):
        CapabilityRelation(A, B, RelationKind.REQUIRES, strength=RelationStrength.STRONG)
    with pytest.raises(InvalidRelationError):
        CapabilityRelation(A, B, RelationKind.ENABLED_BY, strength=RelationStrength.WEAK)
    relation = CapabilityRelation(A, B, RelationKind.SUPPORTED_BY, strength=RelationStrength.STRONG)
    assert relation.strength.rank == 3


def test_catalog_rejects_wrong_element_types_before_sorting() -> None:
    with pytest.raises(InvalidCatalogError):
        CapabilityCatalog(namespaces=("core",))
    with pytest.raises(InvalidCatalogError):
        CapabilityCatalog(concepts=("core:a",))
    with pytest.raises(InvalidCatalogError):
        CapabilityCatalog(relations=((A, B),))
