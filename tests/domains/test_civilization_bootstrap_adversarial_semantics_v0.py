from capability_lab.domains import build_civilization_bootstrap_seed_catalog_v0
from capability_lab.semantics import RelationKind, RelationStrength


def _relations(kind: RelationKind):
    catalog = build_civilization_bootstrap_seed_catalog_v0()
    return [relation for relation in catalog.relations if relation.kind is kind]


def test_supported_by_strength_never_upgrades_relation_to_necessity() -> None:
    catalog = build_civilization_bootstrap_seed_catalog_v0()
    supported = [
        relation
        for relation in catalog.relations
        if relation.kind is RelationKind.SUPPORTED_BY
    ]
    requires_keys = {
        (
            relation.source_id,
            relation.target_id,
            relation.scope.key if relation.scope else None,
        )
        for relation in catalog.relations
        if relation.kind is RelationKind.REQUIRES
    }

    assert any(relation.strength is RelationStrength.STRONG for relation in supported)
    assert all(
        (
            relation.source_id,
            relation.target_id,
            relation.scope.key if relation.scope else None,
        )
        not in requires_keys
        for relation in supported
    )


def test_support_strength_is_edge_local_not_target_global() -> None:
    target_relations = [
        relation
        for relation in _relations(RelationKind.SUPPORTED_BY)
        if relation.target_id.key == "microbiology_and_contamination_control"
    ]
    strengths = {relation.strength for relation in target_relations}

    assert RelationStrength.STRONG in strengths
    assert RelationStrength.MODERATE in strengths


def test_support_strength_is_edge_local_not_source_global() -> None:
    source_relations = [
        relation
        for relation in _relations(RelationKind.SUPPORTED_BY)
        if relation.source_id.key == "pump_systems"
    ]
    by_target = {
        relation.target_id.key: relation.strength for relation in source_relations
    }

    assert by_target["fluid_pressure_and_flow"] is RelationStrength.STRONG
    assert by_target["mechanisms_and_power_transmission"] is RelationStrength.MODERATE


def test_same_scope_key_does_not_create_global_relation_identity() -> None:
    conceptual = [
        relation
        for relation in build_civilization_bootstrap_seed_catalog_v0().relations
        if relation.scope is not None and relation.scope.key == "conceptual_analysis"
    ]

    assert len(conceptual) > 5
    assert len({relation.semantic_key for relation in conceptual}) == len(conceptual)
    assert len({relation.source_id for relation in conceptual}) > 5
    assert len({relation.target_id for relation in conceptual}) > 5


def test_scope_key_does_not_define_support_strength() -> None:
    conceptual = [
        relation
        for relation in _relations(RelationKind.SUPPORTED_BY)
        if relation.scope is not None and relation.scope.key == "conceptual_analysis"
    ]
    strengths = {relation.strength for relation in conceptual}

    assert RelationStrength.STRONG in strengths
    assert RelationStrength.MODERATE in strengths


def test_domain_pack_exports_no_priority_difficulty_or_score_surface() -> None:
    import capability_lab.domains.civilization_bootstrap as domain

    exported = set(domain.__all__)
    forbidden_fragments = {"priority", "difficulty", "score", "rank", "importance"}

    assert all(
        not any(fragment in name.lower() for fragment in forbidden_fragments)
        for name in exported
    )
