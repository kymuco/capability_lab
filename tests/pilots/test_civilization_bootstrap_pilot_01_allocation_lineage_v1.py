from types import SimpleNamespace

import pytest

from capability_lab.pilots.civilization_bootstrap_01 import (
    InvalidPilotEvidenceMaterialization,
    PilotObservationAllocationKind,
    PilotObservationAllocationLineageGraph,
    PilotObservationAllocationRef,
    PilotObservationAllocationRelation,
    PilotObservationAllocationRelationKind,
    pilot_observation_allocation_dependence_key_v1,
    pilot_observation_allocation_lineage_closure_keys_v1,
    validate_pilot_materialized_evidence_allocation_ancestry_preconditions_v1,
)
from capability_lab.pilots.civilization_bootstrap_01 import (
    materialization_allocation_lineage as allocation_lineage_module,
)


def _ref(kind, ref):
    return PilotObservationAllocationRef(kind, ref)


def _entry(evidence_id, *allocations):
    basis = SimpleNamespace(evidence=SimpleNamespace(evidence_id=evidence_id))
    upstream = SimpleNamespace(basis_entry=basis)
    mechanism = SimpleNamespace(upstream_lineage_entry=upstream)
    coordination = SimpleNamespace(mechanism_entry=mechanism)
    temporal = SimpleNamespace(coordination_entry=coordination)
    return SimpleNamespace(
        temporal_entry=temporal,
        allocation_declaration=SimpleNamespace(allocations=tuple(allocations)),
    )


def _patch_prior_gate(monkeypatch):
    def canonical(entries, **kwargs):
        return tuple(
            sorted(
                tuple(entries),
                key=lambda item: str(
                    item.temporal_entry.coordination_entry.mechanism_entry
                    .upstream_lineage_entry.basis_entry.evidence.evidence_id
                ),
            )
        )

    monkeypatch.setattr(
        allocation_lineage_module._allocation,
        "validate_pilot_materialized_evidence_shared_allocation_preconditions_v1",
        canonical,
    )
    return canonical


def _validate(entries, graph):
    marker = object()
    return validate_pilot_materialized_evidence_allocation_ancestry_preconditions_v1(
        entries,
        source_lineage_graph=marker,
        source_completeness_review=marker,
        mechanism_lineage_graph=marker,
        mechanism_completeness_review=marker,
        coordination_lineage_graph=marker,
        coordination_completeness_review=marker,
        temporal_lineage_graph=marker,
        temporal_completeness_review=marker,
        allocation_lineage_graph=graph,
    )


def test_alias_closure_is_symmetric_and_privacy_reducing() -> None:
    left = _ref(
        PilotObservationAllocationKind.RANDOMIZATION_STATE,
        "randomization_state:left",
    )
    right = _ref(
        PilotObservationAllocationKind.RANDOMIZATION_STATE,
        "randomization_state:right",
    )
    graph = PilotObservationAllocationLineageGraph(
        relations=(
            PilotObservationAllocationRelation(
                PilotObservationAllocationRelationKind.ALIAS_OF,
                left,
                right,
            ),
        )
    )
    left_closure = set(
        pilot_observation_allocation_lineage_closure_keys_v1(left, graph)
    )
    right_closure = set(
        pilot_observation_allocation_lineage_closure_keys_v1(right, graph)
    )
    assert left_closure == right_closure
    assert left_closure == {
        pilot_observation_allocation_dependence_key_v1(left),
        pilot_observation_allocation_dependence_key_v1(right),
    }
    assert "randomization_state:left" not in " ".join(left_closure)


@pytest.mark.parametrize(
    "relation_kind",
    [
        PilotObservationAllocationRelationKind.DERIVED_FROM,
        PilotObservationAllocationRelationKind.CLONED_FROM,
        PilotObservationAllocationRelationKind.STATE_CONTINUATION_OF,
    ],
)
def test_directed_relations_traverse_upstream_only(relation_kind) -> None:
    child = _ref(
        PilotObservationAllocationKind.ADAPTIVE_ALLOCATION_STATE,
        "adaptive_allocation_state:child",
    )
    parent = _ref(
        PilotObservationAllocationKind.RANDOMIZATION_STATE,
        "randomization_state:parent",
    )
    graph = PilotObservationAllocationLineageGraph(
        relations=(
            PilotObservationAllocationRelation(
                relation_kind,
                child,
                parent,
            ),
        )
    )
    child_keys = set(
        pilot_observation_allocation_lineage_closure_keys_v1(child, graph)
    )
    parent_keys = set(
        pilot_observation_allocation_lineage_closure_keys_v1(parent, graph)
    )
    assert pilot_observation_allocation_dependence_key_v1(parent) in child_keys
    assert pilot_observation_allocation_dependence_key_v1(child) not in parent_keys


def test_transitive_allocation_lineage_reaches_common_root() -> None:
    leaf = _ref(
        PilotObservationAllocationKind.ASSIGNMENT_EPISODE,
        "assignment_episode:leaf",
    )
    middle = _ref(
        PilotObservationAllocationKind.ADAPTIVE_ALLOCATION_STATE,
        "adaptive_allocation_state:middle",
    )
    root = _ref(
        PilotObservationAllocationKind.RANDOMIZATION_STATE,
        "randomization_state:root",
    )
    graph = PilotObservationAllocationLineageGraph(
        relations=(
            PilotObservationAllocationRelation(
                PilotObservationAllocationRelationKind.STATE_CONTINUATION_OF,
                leaf,
                middle,
            ),
            PilotObservationAllocationRelation(
                PilotObservationAllocationRelationKind.DERIVED_FROM,
                middle,
                root,
            ),
        )
    )
    keys = set(pilot_observation_allocation_lineage_closure_keys_v1(leaf, graph))
    assert pilot_observation_allocation_dependence_key_v1(root) in keys


def test_cross_kind_common_allocation_root_rejects(monkeypatch) -> None:
    _patch_prior_gate(monkeypatch)
    allocation_a = _ref(
        PilotObservationAllocationKind.ADAPTIVE_ALLOCATION_STATE,
        "adaptive_allocation_state:a",
    )
    allocation_b = _ref(
        PilotObservationAllocationKind.ASSIGNMENT_EPISODE,
        "assignment_episode:b",
    )
    root = _ref(
        PilotObservationAllocationKind.RANDOMIZATION_STATE,
        "randomization_state:common_root",
    )
    graph = PilotObservationAllocationLineageGraph(
        relations=(
            PilotObservationAllocationRelation(
                PilotObservationAllocationRelationKind.DERIVED_FROM,
                allocation_a,
                root,
            ),
            PilotObservationAllocationRelation(
                PilotObservationAllocationRelationKind.STATE_CONTINUATION_OF,
                allocation_b,
                root,
            ),
        )
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="allocation-ancestry independence preconditions",
    ):
        _validate(
            (
                _entry("evidence_a", allocation_a),
                _entry("evidence_b", allocation_b),
            ),
            graph,
        )


def test_cloned_randomization_states_share_origin(monkeypatch) -> None:
    _patch_prior_gate(monkeypatch)
    clone_a = _ref(
        PilotObservationAllocationKind.RANDOMIZATION_STATE,
        "randomization_state:clone_a",
    )
    clone_b = _ref(
        PilotObservationAllocationKind.RANDOMIZATION_STATE,
        "randomization_state:clone_b",
    )
    root = _ref(
        PilotObservationAllocationKind.RANDOMIZATION_STATE,
        "randomization_state:root",
    )
    graph = PilotObservationAllocationLineageGraph(
        relations=(
            PilotObservationAllocationRelation(
                PilotObservationAllocationRelationKind.CLONED_FROM,
                clone_a,
                root,
            ),
            PilotObservationAllocationRelation(
                PilotObservationAllocationRelationKind.CLONED_FROM,
                clone_b,
                root,
            ),
        )
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="allocation-ancestry independence preconditions",
    ):
        _validate(
            (_entry("evidence_a", clone_a), _entry("evidence_b", clone_b)),
            graph,
        )


def test_disjoint_allocation_roots_clear_only_declared_ancestry_gate(monkeypatch) -> None:
    canonical = _patch_prior_gate(monkeypatch)
    a = _ref(
        PilotObservationAllocationKind.ALLOCATION_BLOCK,
        "allocation_block:a",
    )
    b = _ref(
        PilotObservationAllocationKind.ALLOCATION_BLOCK,
        "allocation_block:b",
    )
    root_a = _ref(
        PilotObservationAllocationKind.RANDOMIZATION_STATE,
        "randomization_state:root_a",
    )
    root_b = _ref(
        PilotObservationAllocationKind.RANDOMIZATION_STATE,
        "randomization_state:root_b",
    )
    graph = PilotObservationAllocationLineageGraph(
        relations=(
            PilotObservationAllocationRelation(
                PilotObservationAllocationRelationKind.DERIVED_FROM,
                a,
                root_a,
            ),
            PilotObservationAllocationRelation(
                PilotObservationAllocationRelationKind.DERIVED_FROM,
                b,
                root_b,
            ),
        )
    )
    entries = (_entry("evidence_b", b), _entry("evidence_a", a))
    assert _validate(entries, graph) == canonical(entries)


def test_multiple_same_observation_allocations_do_not_self_collide(monkeypatch) -> None:
    _patch_prior_gate(monkeypatch)
    alias_a = _ref(
        PilotObservationAllocationKind.RANDOMIZATION_STATE,
        "randomization_state:alias_a",
    )
    alias_b = _ref(
        PilotObservationAllocationKind.RANDOMIZATION_STATE,
        "randomization_state:alias_b",
    )
    independent = _ref(
        PilotObservationAllocationKind.RANDOMIZATION_STATE,
        "randomization_state:independent",
    )
    graph = PilotObservationAllocationLineageGraph(
        relations=(
            PilotObservationAllocationRelation(
                PilotObservationAllocationRelationKind.ALIAS_OF,
                alias_a,
                alias_b,
            ),
        )
    )
    assert _validate(
        (
            _entry("evidence_a", alias_a, alias_b),
            _entry("evidence_b", independent),
        ),
        graph,
    )


def test_empty_graph_does_not_assert_absence_of_hidden_allocation_origin(
    monkeypatch,
) -> None:
    _patch_prior_gate(monkeypatch)
    a = _ref(
        PilotObservationAllocationKind.RANDOMIZATION_STATE,
        "randomization_state:a",
    )
    b = _ref(
        PilotObservationAllocationKind.RANDOMIZATION_STATE,
        "randomization_state:b",
    )
    graph = PilotObservationAllocationLineageGraph()
    assert _validate((_entry("evidence_a", a), _entry("evidence_b", b)), graph)


def test_reverse_alias_duplicate_rejected() -> None:
    a = _ref(
        PilotObservationAllocationKind.RANDOMIZATION_STATE,
        "randomization_state:a",
    )
    b = _ref(
        PilotObservationAllocationKind.RANDOMIZATION_STATE,
        "randomization_state:b",
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="exact or reverse-alias relation",
    ):
        PilotObservationAllocationLineageGraph(
            relations=(
                PilotObservationAllocationRelation(
                    PilotObservationAllocationRelationKind.ALIAS_OF,
                    a,
                    b,
                ),
                PilotObservationAllocationRelation(
                    PilotObservationAllocationRelationKind.ALIAS_OF,
                    b,
                    a,
                ),
            )
        )


def test_conflicting_directed_relation_kinds_rejected() -> None:
    child = _ref(
        PilotObservationAllocationKind.ADAPTIVE_ALLOCATION_STATE,
        "adaptive_allocation_state:child",
    )
    root = _ref(
        PilotObservationAllocationKind.RANDOMIZATION_STATE,
        "randomization_state:root",
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="conflicting relation kinds",
    ):
        PilotObservationAllocationLineageGraph(
            relations=(
                PilotObservationAllocationRelation(
                    PilotObservationAllocationRelationKind.DERIVED_FROM,
                    child,
                    root,
                ),
                PilotObservationAllocationRelation(
                    PilotObservationAllocationRelationKind.CLONED_FROM,
                    child,
                    root,
                ),
            )
        )


def test_directed_relation_inside_alias_class_rejected() -> None:
    a = _ref(
        PilotObservationAllocationKind.RANDOMIZATION_STATE,
        "randomization_state:a",
    )
    b = _ref(
        PilotObservationAllocationKind.RANDOMIZATION_STATE,
        "randomization_state:b",
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="within one alias class",
    ):
        PilotObservationAllocationLineageGraph(
            relations=(
                PilotObservationAllocationRelation(
                    PilotObservationAllocationRelationKind.ALIAS_OF,
                    a,
                    b,
                ),
                PilotObservationAllocationRelation(
                    PilotObservationAllocationRelationKind.DERIVED_FROM,
                    a,
                    b,
                ),
            )
        )


def test_alias_contracted_cycle_rejected() -> None:
    a = _ref(
        PilotObservationAllocationKind.RANDOMIZATION_STATE,
        "randomization_state:a",
    )
    alias_a = _ref(
        PilotObservationAllocationKind.RANDOMIZATION_STATE,
        "randomization_state:a_alias",
    )
    b = _ref(
        PilotObservationAllocationKind.RANDOMIZATION_STATE,
        "randomization_state:b",
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="acyclic after alias contraction",
    ):
        PilotObservationAllocationLineageGraph(
            relations=(
                PilotObservationAllocationRelation(
                    PilotObservationAllocationRelationKind.ALIAS_OF,
                    a,
                    alias_a,
                ),
                PilotObservationAllocationRelation(
                    PilotObservationAllocationRelationKind.DERIVED_FROM,
                    alias_a,
                    b,
                ),
                PilotObservationAllocationRelation(
                    PilotObservationAllocationRelationKind.STATE_CONTINUATION_OF,
                    b,
                    a,
                ),
            )
        )


def test_self_relation_rejected() -> None:
    a = _ref(
        PilotObservationAllocationKind.ALLOCATION_BLOCK,
        "allocation_block:self",
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="two distinct exact allocation refs",
    ):
        PilotObservationAllocationRelation(
            PilotObservationAllocationRelationKind.ALIAS_OF,
            a,
            a,
        )


def test_graph_canonical_order_is_deterministic() -> None:
    a = _ref(
        PilotObservationAllocationKind.ALLOCATION_BLOCK,
        "allocation_block:a",
    )
    b = _ref(
        PilotObservationAllocationKind.ALLOCATION_BLOCK,
        "allocation_block:b",
    )
    root_a = _ref(
        PilotObservationAllocationKind.RANDOMIZATION_STATE,
        "randomization_state:a",
    )
    root_b = _ref(
        PilotObservationAllocationKind.RANDOMIZATION_STATE,
        "randomization_state:b",
    )
    relation_a = PilotObservationAllocationRelation(
        PilotObservationAllocationRelationKind.DERIVED_FROM,
        a,
        root_a,
    )
    relation_b = PilotObservationAllocationRelation(
        PilotObservationAllocationRelationKind.DERIVED_FROM,
        b,
        root_b,
    )
    graph_a = PilotObservationAllocationLineageGraph(
        relations=(relation_b, relation_a)
    )
    graph_b = PilotObservationAllocationLineageGraph(
        relations=(relation_a, relation_b)
    )
    assert graph_a == graph_b


def test_non_lineage_design_similarity_relations_do_not_exist() -> None:
    names = set(PilotObservationAllocationRelationKind.__members__)
    assert "SAME_ARM" not in names
    assert "SAME_TREATMENT" not in names
    assert "SAME_PROBABILITY" not in names
    assert "USES_ALGORITHM" not in names
    assert "INSTANCE_OF" not in names
    assert "SAME_EXPERIMENT_FAMILY" not in names


def test_prior_exact_allocation_gate_rejects_before_lineage_can_help(
    monkeypatch,
) -> None:
    def reject(*args, **kwargs):
        raise InvalidPilotEvidenceMaterialization(
            "shared-allocation independence preconditions"
        )

    monkeypatch.setattr(
        allocation_lineage_module._allocation,
        "validate_pilot_materialized_evidence_shared_allocation_preconditions_v1",
        reject,
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="shared-allocation independence preconditions",
    ):
        _validate(
            (
                _entry(
                    "evidence_a",
                    _ref(
                        PilotObservationAllocationKind.ALLOCATION_BLOCK,
                        "allocation_block:a",
                    ),
                ),
            ),
            PilotObservationAllocationLineageGraph(),
        )


def test_wrong_graph_type_rejects_before_prior_gate(monkeypatch) -> None:
    called = False

    def prior(*args, **kwargs):
        nonlocal called
        called = True
        return tuple(args[0])

    monkeypatch.setattr(
        allocation_lineage_module._allocation,
        "validate_pilot_materialized_evidence_shared_allocation_preconditions_v1",
        prior,
    )
    marker = object()
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="allocation_lineage_graph must be PilotObservationAllocationLineageGraph",
    ):
        validate_pilot_materialized_evidence_allocation_ancestry_preconditions_v1(
            (),
            source_lineage_graph=marker,
            source_completeness_review=marker,
            mechanism_lineage_graph=marker,
            mechanism_completeness_review=marker,
            coordination_lineage_graph=marker,
            coordination_completeness_review=marker,
            temporal_lineage_graph=marker,
            temporal_completeness_review=marker,
            allocation_lineage_graph=object(),
        )
    assert called is False
