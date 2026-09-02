from capability_lab.domains import (
    CIVILIZATION_BOOTSTRAP_NAMESPACE,
    CIVILIZATION_BOOTSTRAP_SEED_VERSION,
    CIVILIZATION_BOOTSTRAP_TECHNICAL_COMPETENCE_FRAME_V1,
    build_civilization_bootstrap_frame_catalog_v1,
    build_civilization_bootstrap_seed_catalog_v0,
)
from capability_lab.semantics import (
    CapabilityCatalog,
    ConceptLifecycle,
    RelationFamily,
    RelationKind,
    RelationStrength,
)
from capability_lab.state import CompetenceFrameCatalog


EXPECTED_DIMENSIONS = {
    "conceptual_knowledge",
    "calculation",
    "execution",
    "diagnosis",
    "transfer",
    "independence",
    "explanation",
}


def test_seed_v0_has_frozen_curated_shape() -> None:
    catalog = build_civilization_bootstrap_seed_catalog_v0()

    assert CIVILIZATION_BOOTSTRAP_SEED_VERSION == "v0"
    assert catalog.namespaces == (CIVILIZATION_BOOTSTRAP_NAMESPACE,)
    assert CIVILIZATION_BOOTSTRAP_NAMESPACE.namespace_id == "civilization_bootstrap"
    assert len(catalog.concepts) == 63
    assert len(catalog.relations) == 57


def test_seed_v0_concepts_are_active_revision_one_and_not_a_human_level_root() -> None:
    catalog = build_civilization_bootstrap_seed_catalog_v0()
    keys = {concept.capability_id.key for concept in catalog.concepts}

    assert "technical_generalist" not in keys
    assert "human_level" not in keys
    assert all(concept.revision == 1 for concept in catalog.concepts)
    assert all(concept.lifecycle is ConceptLifecycle.ACTIVE for concept in catalog.concepts)

    assert {
        "technical_inquiry",
        "material_behavior_and_processing",
        "energy_system_reasoning",
        "fabrication_process_execution",
        "mechanical_system_reasoning",
        "electrical_information_system_reasoning",
        "infrastructure_system_reasoning",
        "life_support_system_reasoning",
    }.issubset(keys)


def test_seed_v0_contains_no_empirical_development_edges() -> None:
    catalog = build_civilization_bootstrap_seed_catalog_v0()

    assert all(
        relation.kind.family is not RelationFamily.EMPIRICAL_DEVELOPMENT
        for relation in catalog.relations
    )


def test_editorial_families_are_not_encoded_as_specialization_tree() -> None:
    catalog = build_civilization_bootstrap_seed_catalog_v0()
    specializes = {
        (relation.source_id.key, relation.target_id.key)
        for relation in catalog.relations
        if relation.kind is RelationKind.SPECIALIZES
    }

    assert specializes == {
        ("electrical_measurement", "physical_measurement"),
        ("dimensional_metrology", "physical_measurement"),
    }
    assert ("quantitative_estimation", "technical_inquiry") not in specializes
    assert ("basic_circuits", "electrical_information_system_reasoning") not in specializes
    assert ("first_aid_principles", "life_support_system_reasoning") not in specializes


def test_every_dependency_edge_is_explicitly_scoped() -> None:
    catalog = build_civilization_bootstrap_seed_catalog_v0()
    dependencies = [
        relation
        for relation in catalog.relations
        if relation.kind.family is RelationFamily.DEPENDENCY
    ]

    assert dependencies
    assert all(relation.scope is not None for relation in dependencies)


def test_supported_by_edges_have_explicit_strength_and_categorical_dependencies_do_not() -> None:
    catalog = build_civilization_bootstrap_seed_catalog_v0()

    supported = [
        relation
        for relation in catalog.relations
        if relation.kind is RelationKind.SUPPORTED_BY
    ]
    categorical = [
        relation
        for relation in catalog.relations
        if relation.kind in {RelationKind.REQUIRES, RelationKind.ENABLED_BY}
    ]

    assert len(supported) == 51
    assert len([r for r in categorical if r.kind is RelationKind.REQUIRES]) == 1
    assert len([r for r in categorical if r.kind is RelationKind.ENABLED_BY]) == 3
    assert all(r.strength is not RelationStrength.UNSPECIFIED for r in supported)
    assert all(r.strength is RelationStrength.UNSPECIFIED for r in categorical)


def test_requires_is_extremely_sparse_and_only_the_defensible_scoped_edge_remains() -> None:
    catalog = build_civilization_bootstrap_seed_catalog_v0()
    requires = [r for r in catalog.relations if r.kind is RelationKind.REQUIRES]

    assert len(requires) == 1
    relation = requires[0]
    assert relation.source_id.key == "low_voltage_power_distribution"
    assert relation.target_id.key == "basic_electricity"
    assert relation.scope is not None
    assert relation.scope.key == "conceptual_analysis"


def test_review_downgrades_alternative_route_dependencies_to_supported_by() -> None:
    catalog = build_civilization_bootstrap_seed_catalog_v0()
    relation_keys = {
        (relation.source_id.key, relation.kind, relation.target_id.key)
        for relation in catalog.relations
    }

    assert (
        "microcontroller_sensor_systems",
        RelationKind.SUPPORTED_BY,
        "embedded_programming",
    ) in relation_keys
    assert (
        "potable_water_treatment",
        RelationKind.SUPPORTED_BY,
        "microbiology_and_contamination_control",
    ) in relation_keys
    assert (
        "microcontroller_sensor_systems",
        RelationKind.REQUIRES,
        "embedded_programming",
    ) not in relation_keys
    assert (
        "potable_water_treatment",
        RelationKind.REQUIRES,
        "microbiology_and_contamination_control",
    ) not in relation_keys


def test_cross_domain_reconstruction_chains_are_present_without_curriculum_edges() -> None:
    catalog = build_civilization_bootstrap_seed_catalog_v0()
    edge_keys = {
        (
            relation.source_id.key,
            relation.kind,
            relation.target_id.key,
        )
        for relation in catalog.relations
    }

    assert (
        "electric_motor_systems",
        RelationKind.SUPPORTED_BY,
        "electromagnetism",
    ) in edge_keys
    assert (
        "pump_systems",
        RelationKind.SUPPORTED_BY,
        "fluid_pressure_and_flow",
    ) in edge_keys
    assert (
        "microcontroller_sensor_systems",
        RelationKind.SUPPORTED_BY,
        "embedded_programming",
    ) in edge_keys
    assert (
        "food_preservation",
        RelationKind.SUPPORTED_BY,
        "microbiology_and_contamination_control",
    ) in edge_keys


def test_seed_catalog_construction_is_canonical_and_deterministic() -> None:
    first = build_civilization_bootstrap_seed_catalog_v0()
    second = build_civilization_bootstrap_seed_catalog_v0()

    assert first == second
    assert first.to_json() == second.to_json()


def test_real_seed_catalog_roundtrips_through_strict_semantics_schema() -> None:
    catalog = build_civilization_bootstrap_seed_catalog_v0()

    restored = CapabilityCatalog.from_json(catalog.to_json())

    assert restored == catalog
    assert restored.to_json() == catalog.to_json()


def test_technical_competence_frame_v1_is_exact_and_non_ordinal() -> None:
    frame = CIVILIZATION_BOOTSTRAP_TECHNICAL_COMPETENCE_FRAME_V1
    frame_catalog = build_civilization_bootstrap_frame_catalog_v1()

    assert str(frame.ref) == "civilization_bootstrap:technical_competence@1"
    assert {dimension.key for dimension in frame.dimensions} == EXPECTED_DIMENSIONS
    assert frame_catalog.frames == (frame,)
    assert "mastery" not in {dimension.key for dimension in frame.dimensions}
    assert "safety" not in {dimension.key for dimension in frame.dimensions}


def test_real_frame_catalog_roundtrips_through_strict_state_schema() -> None:
    frame_catalog = build_civilization_bootstrap_frame_catalog_v1()

    restored = CompetenceFrameCatalog.from_json(frame_catalog.to_json())

    assert restored == frame_catalog
    assert restored.to_json() == frame_catalog.to_json()
