import json

from capability_lab.semantics import CapabilityCatalog, CapabilityConcept, CapabilityId, CapabilityNamespace, CapabilityRelation, RelationKind


def sample(reverse: bool = False) -> CapabilityCatalog:
    ns = CapabilityNamespace("core", "Core")
    a = CapabilityConcept(CapabilityId("core", "a"), "A", "Definition A")
    b = CapabilityConcept(CapabilityId("core", "b"), "B", "Definition B")
    concepts = (b, a) if reverse else (a, b)
    relation = CapabilityRelation(b.capability_id, a.capability_id, RelationKind.REQUIRES)
    return CapabilityCatalog(namespaces=(ns,), concepts=concepts, relations=(relation,))


def test_dict_and_json_roundtrip() -> None:
    catalog = sample()
    assert CapabilityCatalog.from_dict(catalog.to_dict()) == catalog
    assert CapabilityCatalog.from_json(catalog.to_json()) == catalog


def test_insertion_order_is_stable() -> None:
    assert sample(False).to_json() == sample(True).to_json()


def test_json_is_compact_canonical_form() -> None:
    encoded = sample().to_json()
    assert encoded == json.dumps(json.loads(encoded), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
