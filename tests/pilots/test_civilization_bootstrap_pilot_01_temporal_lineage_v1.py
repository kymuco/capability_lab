from types import SimpleNamespace

import pytest

from capability_lab.pilots.civilization_bootstrap_01 import (
    InvalidPilotEvidenceMaterialization,
    PilotObservationTemporalKind,
    PilotObservationTemporalLineageGraph,
    PilotObservationTemporalRef,
    PilotObservationTemporalRelation,
    PilotObservationTemporalRelationKind,
    pilot_observation_temporal_dependence_key_v1,
    pilot_observation_temporal_lineage_closure_keys_v1,
    validate_pilot_materialized_evidence_temporal_ancestry_preconditions_v1,
)
from capability_lab.pilots.civilization_bootstrap_01 import (
    materialization_temporal_lineage as temporal_lineage_module,
)


def _temporal(kind, ref):
    return PilotObservationTemporalRef(kind, ref)


def _relation(kind, temporal, upstream):
    return PilotObservationTemporalRelation(kind, temporal, upstream)


def _fake_entry(evidence_id, *temporals):
    evidence = SimpleNamespace(evidence_id=evidence_id)
    basis_entry = SimpleNamespace(evidence=evidence)
    upstream_lineage_entry = SimpleNamespace(basis_entry=basis_entry)
    mechanism_entry = SimpleNamespace(upstream_lineage_entry=upstream_lineage_entry)
    coordination_entry = SimpleNamespace(mechanism_entry=mechanism_entry)
    temporal_declaration = SimpleNamespace(temporals=tuple(temporals))
    return SimpleNamespace(
        coordination_entry=coordination_entry,
        temporal_declaration=temporal_declaration,
    )


def _patch_prior_gate(monkeypatch, returned_entries):
    calls = []

    def fake_prior(entries, **kwargs):
        calls.append((tuple(entries), kwargs))
        return tuple(returned_entries)

    monkeypatch.setattr(
        temporal_lineage_module._temporal,
        "validate_pilot_materialized_evidence_shared_temporal_preconditions_v1",
        fake_prior,
    )
    return calls


def _validate(entries, graph):
    marker = object()
    return validate_pilot_materialized_evidence_temporal_ancestry_preconditions_v1(
        entries,
        source_lineage_graph=marker,
        source_completeness_review=marker,
        mechanism_lineage_graph=marker,
        mechanism_completeness_review=marker,
        coordination_lineage_graph=marker,
        coordination_completeness_review=marker,
        temporal_lineage_graph=graph,
    )


def test_alias_is_symmetric_in_temporal_lineage_closure() -> None:
    a = _temporal(
        PilotObservationTemporalKind.INTERVENTION_EPISODE,
        "intervention_episode:alias_a",
    )
    b = _temporal(
        PilotObservationTemporalKind.INTERVENTION_EPISODE,
        "intervention_episode:alias_b",
    )
    graph = PilotObservationTemporalLineageGraph(
        relations=(
            _relation(
                PilotObservationTemporalRelationKind.ALIAS_OF,
                b,
                a,
            ),
        )
    )

    expected = {
        pilot_observation_temporal_dependence_key_v1(a),
        pilot_observation_temporal_dependence_key_v1(b),
    }
    assert set(pilot_observation_temporal_lineage_closure_keys_v1(a, graph)) == expected
    assert set(pilot_observation_temporal_lineage_closure_keys_v1(b, graph)) == expected


def test_directed_lineage_traverses_only_upstream() -> None:
    child = _temporal(
        PilotObservationTemporalKind.ADAPTIVE_STATE,
        "adaptive_state:child",
    )
    parent = _temporal(
        PilotObservationTemporalKind.HISTORY_STATE,
        "history_state:parent",
    )
    graph = PilotObservationTemporalLineageGraph(
        relations=(
            _relation(
                PilotObservationTemporalRelationKind.DERIVED_FROM,
                child,
                parent,
            ),
        )
    )

    child_keys = set(
        pilot_observation_temporal_lineage_closure_keys_v1(child, graph)
    )
    parent_keys = set(
        pilot_observation_temporal_lineage_closure_keys_v1(parent, graph)
    )
    child_key = pilot_observation_temporal_dependence_key_v1(child)
    parent_key = pilot_observation_temporal_dependence_key_v1(parent)

    assert child_keys == {child_key, parent_key}
    assert parent_keys == {parent_key}


def test_transitive_temporal_lineage_reaches_common_root_across_kinds() -> None:
    adaptive = _temporal(
        PilotObservationTemporalKind.ADAPTIVE_STATE,
        "adaptive_state:derived",
    )
    carryover = _temporal(
        PilotObservationTemporalKind.CARRYOVER_STATE,
        "carryover_state:middle",
    )
    root = _temporal(
        PilotObservationTemporalKind.INTERVENTION_EPISODE,
        "intervention_episode:root",
    )
    graph = PilotObservationTemporalLineageGraph(
        relations=(
            _relation(
                PilotObservationTemporalRelationKind.CARRYOVER_FROM,
                adaptive,
                carryover,
            ),
            _relation(
                PilotObservationTemporalRelationKind.STATE_CONTINUATION_OF,
                carryover,
                root,
            ),
        )
    )

    keys = set(
        pilot_observation_temporal_lineage_closure_keys_v1(adaptive, graph)
    )
    assert pilot_observation_temporal_dependence_key_v1(root) in keys


def test_common_temporal_ancestor_rejects_distinct_exact_refs(monkeypatch) -> None:
    left = _temporal(
        PilotObservationTemporalKind.INTERVENTION_EPISODE,
        "intervention_episode:left",
    )
    right = _temporal(
        PilotObservationTemporalKind.ADAPTIVE_STATE,
        "adaptive_state:right",
    )
    root = _temporal(
        PilotObservationTemporalKind.HISTORY_STATE,
        "history_state:common_root",
    )
    entry_a = _fake_entry("evidence_temporal_lineage_a", left)
    entry_b = _fake_entry("evidence_temporal_lineage_b", right)
    calls = _patch_prior_gate(monkeypatch, (entry_a, entry_b))
    graph = PilotObservationTemporalLineageGraph(
        relations=(
            _relation(
                PilotObservationTemporalRelationKind.DERIVED_FROM,
                left,
                root,
            ),
            _relation(
                PilotObservationTemporalRelationKind.STATE_CONTINUATION_OF,
                right,
                root,
            ),
        )
    )

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="temporal-ancestry independence preconditions",
    ):
        _validate((entry_a, entry_b), graph)

    assert len(calls) == 1


def test_disjoint_declared_temporal_roots_clear_only_lineage_gate(monkeypatch) -> None:
    left = _temporal(
        PilotObservationTemporalKind.EXPOSURE_EPISODE,
        "exposure_episode:left",
    )
    right = _temporal(
        PilotObservationTemporalKind.EXPOSURE_EPISODE,
        "exposure_episode:right",
    )
    root_a = _temporal(
        PilotObservationTemporalKind.HISTORY_STATE,
        "history_state:root_a",
    )
    root_b = _temporal(
        PilotObservationTemporalKind.HISTORY_STATE,
        "history_state:root_b",
    )
    entry_a = _fake_entry("evidence_a", left)
    entry_b = _fake_entry("evidence_b", right)
    _patch_prior_gate(monkeypatch, (entry_a, entry_b))
    graph = PilotObservationTemporalLineageGraph(
        relations=(
            _relation(
                PilotObservationTemporalRelationKind.DERIVED_FROM,
                left,
                root_a,
            ),
            _relation(
                PilotObservationTemporalRelationKind.DERIVED_FROM,
                right,
                root_b,
            ),
        )
    )

    assert _validate((entry_a, entry_b), graph) == (entry_a, entry_b)


def test_multiple_temporals_inside_one_observation_do_not_self_collide(monkeypatch) -> None:
    alias_a = _temporal(
        PilotObservationTemporalKind.CARRYOVER_STATE,
        "carryover_state:alias_a",
    )
    alias_b = _temporal(
        PilotObservationTemporalKind.CARRYOVER_STATE,
        "carryover_state:alias_b",
    )
    other = _temporal(
        PilotObservationTemporalKind.HISTORY_STATE,
        "history_state:other",
    )
    entry_a = _fake_entry("evidence_a", alias_a, alias_b)
    entry_b = _fake_entry("evidence_b", other)
    _patch_prior_gate(monkeypatch, (entry_a, entry_b))
    graph = PilotObservationTemporalLineageGraph(
        relations=(
            _relation(
                PilotObservationTemporalRelationKind.ALIAS_OF,
                alias_a,
                alias_b,
            ),
        )
    )

    assert _validate((entry_a, entry_b), graph) == (entry_a, entry_b)


def test_empty_graph_closure_contains_only_exact_temporal_identity() -> None:
    temporal = _temporal(
        PilotObservationTemporalKind.HISTORY_STATE,
        "history_state:isolated",
    )
    graph = PilotObservationTemporalLineageGraph()
    assert pilot_observation_temporal_lineage_closure_keys_v1(
        temporal,
        graph,
    ) == (pilot_observation_temporal_dependence_key_v1(temporal),)


def test_graph_canonicalizes_reverse_alias_orientation() -> None:
    a = _temporal(
        PilotObservationTemporalKind.INTERVENTION_EPISODE,
        "intervention_episode:a",
    )
    b = _temporal(
        PilotObservationTemporalKind.INTERVENTION_EPISODE,
        "intervention_episode:b",
    )
    graph = PilotObservationTemporalLineageGraph(
        relations=(
            _relation(
                PilotObservationTemporalRelationKind.ALIAS_OF,
                b,
                a,
            ),
        )
    )
    assert graph.relations[0].temporal == a
    assert graph.relations[0].upstream == b


def test_reverse_alias_duplicate_is_rejected() -> None:
    a = _temporal(
        PilotObservationTemporalKind.INTERVENTION_EPISODE,
        "intervention_episode:a",
    )
    b = _temporal(
        PilotObservationTemporalKind.INTERVENTION_EPISODE,
        "intervention_episode:b",
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="reverse-alias relation",
    ):
        PilotObservationTemporalLineageGraph(
            relations=(
                _relation(
                    PilotObservationTemporalRelationKind.ALIAS_OF,
                    a,
                    b,
                ),
                _relation(
                    PilotObservationTemporalRelationKind.ALIAS_OF,
                    b,
                    a,
                ),
            )
        )


def test_conflicting_relation_kinds_for_same_directed_pair_reject() -> None:
    child = _temporal(
        PilotObservationTemporalKind.ADAPTIVE_STATE,
        "adaptive_state:child",
    )
    root = _temporal(
        PilotObservationTemporalKind.HISTORY_STATE,
        "history_state:root",
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="conflicting relation kinds",
    ):
        PilotObservationTemporalLineageGraph(
            relations=(
                _relation(
                    PilotObservationTemporalRelationKind.DERIVED_FROM,
                    child,
                    root,
                ),
                _relation(
                    PilotObservationTemporalRelationKind.CARRYOVER_FROM,
                    child,
                    root,
                ),
            )
        )


def test_directed_edge_inside_alias_class_rejects() -> None:
    a = _temporal(
        PilotObservationTemporalKind.ADAPTIVE_STATE,
        "adaptive_state:a",
    )
    b = _temporal(
        PilotObservationTemporalKind.ADAPTIVE_STATE,
        "adaptive_state:b",
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="within one alias class",
    ):
        PilotObservationTemporalLineageGraph(
            relations=(
                _relation(
                    PilotObservationTemporalRelationKind.ALIAS_OF,
                    a,
                    b,
                ),
                _relation(
                    PilotObservationTemporalRelationKind.STATE_CONTINUATION_OF,
                    a,
                    b,
                ),
            )
        )


def test_cycle_after_alias_contraction_rejects() -> None:
    a = _temporal(
        PilotObservationTemporalKind.ADAPTIVE_STATE,
        "adaptive_state:a",
    )
    a2 = _temporal(
        PilotObservationTemporalKind.ADAPTIVE_STATE,
        "adaptive_state:a2",
    )
    b = _temporal(
        PilotObservationTemporalKind.HISTORY_STATE,
        "history_state:b",
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="acyclic after alias contraction",
    ):
        PilotObservationTemporalLineageGraph(
            relations=(
                _relation(
                    PilotObservationTemporalRelationKind.ALIAS_OF,
                    a,
                    a2,
                ),
                _relation(
                    PilotObservationTemporalRelationKind.DERIVED_FROM,
                    a2,
                    b,
                ),
                _relation(
                    PilotObservationTemporalRelationKind.CARRYOVER_FROM,
                    b,
                    a,
                ),
            )
        )


def test_plain_directed_cycle_rejects() -> None:
    a = _temporal(
        PilotObservationTemporalKind.HISTORY_STATE,
        "history_state:a",
    )
    b = _temporal(
        PilotObservationTemporalKind.HISTORY_STATE,
        "history_state:b",
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="acyclic after alias contraction",
    ):
        PilotObservationTemporalLineageGraph(
            relations=(
                _relation(
                    PilotObservationTemporalRelationKind.DERIVED_FROM,
                    a,
                    b,
                ),
                _relation(
                    PilotObservationTemporalRelationKind.DERIVED_FROM,
                    b,
                    a,
                ),
            )
        )


def test_self_relation_rejects() -> None:
    temporal = _temporal(
        PilotObservationTemporalKind.HISTORY_STATE,
        "history_state:self",
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="two distinct exact temporal refs",
    ):
        _relation(
            PilotObservationTemporalRelationKind.DERIVED_FROM,
            temporal,
            temporal,
        )


def test_non_temporal_ordering_relations_are_not_in_v1_enum() -> None:
    values = {kind.value for kind in PilotObservationTemporalRelationKind}
    assert "PRECEDES" not in values
    assert "FOLLOWS" not in values
    assert "OVERLAPS" not in values
    assert "SAME_WINDOW" not in values
    assert "INSTANCE_OF" not in values


def test_prior_exact_temporal_gate_failure_dominates_lineage(monkeypatch) -> None:
    temporal = _temporal(
        PilotObservationTemporalKind.INTERVENTION_EPISODE,
        "intervention_episode:shared",
    )
    entry_a = _fake_entry("evidence_a", temporal)
    entry_b = _fake_entry("evidence_b", temporal)

    def fail_prior(*args, **kwargs):
        raise InvalidPilotEvidenceMaterialization(
            "shared-temporal independence preconditions"
        )

    monkeypatch.setattr(
        temporal_lineage_module._temporal,
        "validate_pilot_materialized_evidence_shared_temporal_preconditions_v1",
        fail_prior,
    )

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="shared-temporal independence preconditions",
    ):
        _validate(
            (entry_a, entry_b),
            PilotObservationTemporalLineageGraph(),
        )


def test_validator_rejects_wrong_graph_type_before_prior_gate(monkeypatch) -> None:
    calls = _patch_prior_gate(monkeypatch, ())
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="temporal_lineage_graph must be",
    ):
        _validate((), object())
    assert calls == []


def test_graph_relations_are_canonically_sorted() -> None:
    a = _temporal(
        PilotObservationTemporalKind.ADAPTIVE_STATE,
        "adaptive_state:a",
    )
    b = _temporal(
        PilotObservationTemporalKind.HISTORY_STATE,
        "history_state:b",
    )
    c = _temporal(
        PilotObservationTemporalKind.CARRYOVER_STATE,
        "carryover_state:c",
    )
    graph_a = PilotObservationTemporalLineageGraph(
        relations=(
            _relation(
                PilotObservationTemporalRelationKind.CARRYOVER_FROM,
                c,
                b,
            ),
            _relation(
                PilotObservationTemporalRelationKind.DERIVED_FROM,
                a,
                b,
            ),
        )
    )
    graph_b = PilotObservationTemporalLineageGraph(
        relations=tuple(reversed(graph_a.relations))
    )
    assert graph_a == graph_b
