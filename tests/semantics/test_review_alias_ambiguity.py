from capability_lab.semantics import CapabilityCatalog, CapabilityConcept, CapabilityId, CapabilityNamespace


def test_aliases_are_not_required_to_be_globally_unique() -> None:
    namespace = CapabilityNamespace("core", "Core")
    first = CapabilityConcept(CapabilityId("core", "first"), "First", "First definition", aliases=("Shared label",))
    second = CapabilityConcept(CapabilityId("core", "second"), "Second", "Second definition", aliases=("Shared label",))
    catalog = CapabilityCatalog(namespaces=(namespace,), concepts=(first, second))
    assert len(catalog.concepts) == 2
