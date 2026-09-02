import pytest

from capability_lab.semantics import CapabilityId, CapabilityRelation, InvalidRelationError, RelationKind, RelationScope, RelationStrength

A = CapabilityId("core", "a")
B = CapabilityId("core", "b")


def test_structural_relation_rejects_scope() -> None:
    with pytest.raises(InvalidRelationError):
        CapabilityRelation(A, B, RelationKind.SPECIALIZES, scope=RelationScope("dc", "DC context"))


def test_structural_relation_rejects_strength() -> None:
    with pytest.raises(InvalidRelationError):
        CapabilityRelation(A, B, RelationKind.SPECIALIZES, strength=RelationStrength.STRONG)


def test_supported_by_accepts_scope_and_graded_strength() -> None:
    relation = CapabilityRelation(
        A,
        B,
        RelationKind.SUPPORTED_BY,
        scope=RelationScope("low_voltage_dc", "Low-voltage DC"),
        strength=RelationStrength.STRONG,
    )
    assert relation.scope.key == "low_voltage_dc"
    assert relation.strength is RelationStrength.STRONG
    assert relation.strength.rank == 3


@pytest.mark.parametrize("kind", [RelationKind.REQUIRES, RelationKind.ENABLED_BY])
def test_categorical_dependency_rejects_ordinal_strength(kind: RelationKind) -> None:
    with pytest.raises(InvalidRelationError):
        CapabilityRelation(A, B, kind, strength=RelationStrength.WEAK)
