import pytest

from capability_lab.semantics import (
    CapabilityId,
    CapabilityRelation,
    InvalidRelationError,
    RelationFamily,
    RelationKind,
)

A = CapabilityId("core", "a")
B = CapabilityId("core", "b")


@pytest.mark.parametrize(
    ("kind", "family"),
    [
        (RelationKind.SPECIALIZES, RelationFamily.STRUCTURAL),
        (RelationKind.OVERLAPS, RelationFamily.STRUCTURAL),
        (RelationKind.REQUIRES, RelationFamily.DEPENDENCY),
        (RelationKind.SUPPORTED_BY, RelationFamily.DEPENDENCY),
        (RelationKind.ENABLED_BY, RelationFamily.DEPENDENCY),
        (RelationKind.COMMONLY_PRECEDES, RelationFamily.EMPIRICAL_DEVELOPMENT),
        (RelationKind.COMMONLY_COOCCURS, RelationFamily.EMPIRICAL_DEVELOPMENT),
        (RelationKind.TRANSFER_OBSERVED_TO, RelationFamily.EMPIRICAL_DEVELOPMENT),
    ],
)
def test_relation_kind_has_frozen_family(kind, family) -> None:
    assert kind.family is family


def test_every_relation_kind_has_a_family() -> None:
    assert all(isinstance(kind.family, RelationFamily) for kind in RelationKind)


def test_symmetric_relation_canonicalizes_endpoint_order() -> None:
    relation = CapabilityRelation(B, A, RelationKind.OVERLAPS)
    assert relation.source_id == A
    assert relation.target_id == B


def test_directional_relation_preserves_order() -> None:
    relation = CapabilityRelation(B, A, RelationKind.REQUIRES)
    assert relation.source_id == B
    assert relation.target_id == A


@pytest.mark.parametrize("kind", list(RelationKind))
def test_self_relation_rejected(kind: RelationKind) -> None:
    kwargs = {"provenance_refs": ("basis:1",)} if kind.family is RelationFamily.EMPIRICAL_DEVELOPMENT else {}
    with pytest.raises(InvalidRelationError):
        CapabilityRelation(A, A, kind, **kwargs)
