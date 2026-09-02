import pytest

from capability_lab.semantics import CapabilityId, CapabilityRelation, InvalidRelationError, RelationKind, RelationStrength

A = CapabilityId("core", "a")
B = CapabilityId("core", "b")


@pytest.mark.parametrize("kind", [RelationKind.COMMONLY_PRECEDES, RelationKind.COMMONLY_COOCCURS, RelationKind.TRANSFER_OBSERVED_TO])
def test_empirical_relation_requires_provenance(kind: RelationKind) -> None:
    with pytest.raises(InvalidRelationError):
        CapabilityRelation(A, B, kind)


def test_empirical_relation_rejects_strength() -> None:
    with pytest.raises(InvalidRelationError):
        CapabilityRelation(A, B, RelationKind.COMMONLY_PRECEDES, strength=RelationStrength.STRONG, provenance_refs=("dataset:1",))


def test_empirical_symmetric_relation_canonicalizes_order() -> None:
    relation = CapabilityRelation(B, A, RelationKind.COMMONLY_COOCCURS, provenance_refs=("study:1",))
    assert relation.source_id == A
    assert relation.target_id == B


def test_provenance_is_sorted() -> None:
    relation = CapabilityRelation(A, B, RelationKind.COMMONLY_PRECEDES, provenance_refs=("study:z", " dataset:a "))
    assert relation.provenance_refs == ("dataset:a", "study:z")


def test_duplicate_provenance_is_rejected() -> None:
    with pytest.raises(InvalidRelationError):
        CapabilityRelation(A, B, RelationKind.COMMONLY_PRECEDES, provenance_refs=("study:1", " study:1 "))
