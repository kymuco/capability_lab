from capability_lab.semantics import (
    CapabilityCatalog,
    CapabilityConcept,
    CapabilityId,
    CapabilityNamespace,
    CapabilityRelation,
    RelationKind,
)


def test_civilization_bootstrap_seed_graph_is_representable() -> None:
    ns = CapabilityNamespace("civilization_bootstrap", "Civilization Bootstrap")
    measurement = CapabilityConcept(
        CapabilityId("civilization_bootstrap", "electrical_measurement"),
        "Electrical Measurement",
        "Measure electrical quantities in a stated context.",
    )
    circuits = CapabilityConcept(
        CapabilityId("civilization_bootstrap", "basic_circuits"),
        "Basic Circuits",
        "Reason about basic electrical circuits.",
    )
    catalog = CapabilityCatalog(
        namespaces=(ns,),
        concepts=(measurement, circuits),
        relations=(CapabilityRelation(circuits.capability_id, measurement.capability_id, RelationKind.REQUIRES),),
    )
    assert len(catalog.concepts) == 2
    assert len(catalog.relations) == 1
