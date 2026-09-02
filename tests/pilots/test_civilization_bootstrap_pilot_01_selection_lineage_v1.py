from types import SimpleNamespace

import pytest

from capability_lab.pilots.civilization_bootstrap_01 import (
    InvalidPilotEvidenceMaterialization,
    PilotObservationSelectionKind,
    PilotObservationSelectionLineageGraph,
    PilotObservationSelectionRef,
    PilotObservationSelectionRelation,
    PilotObservationSelectionRelationKind,
    pilot_observation_selection_dependence_key_v1,
    pilot_observation_selection_lineage_closure_keys_v1,
    validate_pilot_materialized_evidence_selection_ancestry_preconditions_v1,
)
from capability_lab.pilots.civilization_bootstrap_01 import (
    materialization_selection_lineage as selection_lineage_module,
)


def _selection(kind, ref):
    return PilotObservationSelectionRef(kind, ref)


def _entry(evidence_id, *selections):
    basis = SimpleNamespace(evidence=SimpleNamespace(evidence_id=evidence_id))
    upstream = SimpleNamespace(basis_entry=basis)
    mechanism = SimpleNamespace(upstream_lineage_entry=upstream)
    coordination = SimpleNamespace(mechanism_entry=mechanism)
    temporal = SimpleNamespace(coordination_entry=coordination)
    allocation = SimpleNamespace(temporal_entry=temporal)
    return SimpleNamespace(
        allocation_entry=allocation,
        selection_declaration=SimpleNamespace(selections=tuple(selections)),
    )


def _patch_prior_gate(monkeypatch):
    monkeypatch.setattr(
        selection_lineage_module._selection,
        "validate_pilot_materialized_evidence_shared_selection_preconditions_v1",
        lambda entries, **kwargs: tuple(entries),
    )


def _validate(entries, graph):
    marker = object()
    return validate_pilot_materialized_evidence_selection_ancestry_preconditions_v1(
        entries,
        source_lineage_graph=marker,
        source_completeness_review=marker,
        mechanism_lineage_graph=marker,
        mechanism_completeness_review=marker,
        coordination_lineage_graph=marker,
        coordination_completeness_review=marker,
        temporal_lineage_graph=marker,
        temporal_completeness_review=marker,
        allocation_lineage_graph=marker,
        allocation_completeness_review=marker,
        selection_lineage_graph=graph,
    )


def test_empty_graph_closure_contains_exact_selection_only() -> None:
    selection = _selection(
        PilotObservationSelectionKind.SAMPLING_FRAME_INSTANCE,
        "sampling_frame:frame_a",
    )
    graph = PilotObservationSelectionLineageGraph()
    assert pilot_observation_selection_lineage_closure_keys_v1(
        selection, graph
    ) == (pilot_observation_selection_dependence_key_v1(selection),)


def test_alias_is_symmetric() -> None:
    left = _selection(
        PilotObservationSelectionKind.COHORT_CONSTRUCTION_STATE,
        "cohort_state:left",
    )
    right = _selection(
        PilotObservationSelectionKind.COHORT_CONSTRUCTION_STATE,
        "cohort_state:right",
    )
    graph = PilotObservationSelectionLineageGraph(
        relations=(
            PilotObservationSelectionRelation(
                PilotObservationSelectionRelationKind.ALIAS_OF,
                left,
                right,
            ),
        )
    )
    left_keys = set(
        pilot_observation_selection_lineage_closure_keys_v1(left, graph)
    )
    right_keys = set(
        pilot_observation_selection_lineage_closure_keys_v1(right, graph)
    )
    assert left_keys == right_keys
    assert len(left_keys) == 2


@pytest.mark.parametrize(
    "relation_kind",
    [
        PilotObservationSelectionRelationKind.DERIVED_FROM,
        PilotObservationSelectionRelationKind.RESAMPLED_FROM,
        PilotObservationSelectionRelationKind.CLONED_FROM,
        PilotObservationSelectionRelationKind.STATE_CONTINUATION_OF,
    ],
)
def test_directed_relations_traverse_downstream_to_upstream_only(
    relation_kind,
) -> None:
    child = _selection(
        PilotObservationSelectionKind.RESAMPLING_DRAW,
        "resampling_draw:child",
    )
    root = _selection(
        PilotObservationSelectionKind.SAMPLING_FRAME_INSTANCE,
        "sampling_frame:root",
    )
    graph = PilotObservationSelectionLineageGraph(
        relations=(
            PilotObservationSelectionRelation(
                relation_kind,
                child,
                root,
            ),
        )
    )

    child_keys = set(
        pilot_observation_selection_lineage_closure_keys_v1(child, graph)
    )
    root_keys = set(
        pilot_observation_selection_lineage_closure_keys_v1(root, graph)
    )
    assert pilot_observation_selection_dependence_key_v1(root) in child_keys
    assert pilot_observation_selection_dependence_key_v1(child) not in root_keys


def test_transitive_selection_ancestry_is_closed() -> None:
    draw = _selection(
        PilotObservationSelectionKind.RESAMPLING_DRAW,
        "resampling_draw:draw_a",
    )
    cohort = _selection(
        PilotObservationSelectionKind.COHORT_CONSTRUCTION_STATE,
        "cohort_state:cohort_a",
    )
    frame = _selection(
        PilotObservationSelectionKind.SAMPLING_FRAME_INSTANCE,
        "sampling_frame:root",
    )
    graph = PilotObservationSelectionLineageGraph(
        relations=(
            PilotObservationSelectionRelation(
                PilotObservationSelectionRelationKind.RESAMPLED_FROM,
                draw,
                cohort,
            ),
            PilotObservationSelectionRelation(
                PilotObservationSelectionRelationKind.DERIVED_FROM,
                cohort,
                frame,
            ),
        )
    )
    keys = set(pilot_observation_selection_lineage_closure_keys_v1(draw, graph))
    assert pilot_observation_selection_dependence_key_v1(cohort) in keys
    assert pilot_observation_selection_dependence_key_v1(frame) in keys


def test_distinct_refs_with_common_selection_root_reject(
    monkeypatch,
) -> None:
    _patch_prior_gate(monkeypatch)
    left = _selection(
        PilotObservationSelectionKind.COHORT_CONSTRUCTION_STATE,
        "cohort_state:left",
    )
    right = _selection(
        PilotObservationSelectionKind.RESAMPLING_DRAW,
        "resampling_draw:right",
    )
    root = _selection(
        PilotObservationSelectionKind.SAMPLING_FRAME_INSTANCE,
        "sampling_frame:root",
    )
    graph = PilotObservationSelectionLineageGraph(
        relations=(
            PilotObservationSelectionRelation(
                PilotObservationSelectionRelationKind.DERIVED_FROM,
                left,
                root,
            ),
            PilotObservationSelectionRelation(
                PilotObservationSelectionRelationKind.RESAMPLED_FROM,
                right,
                root,
            ),
        )
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="selection-ancestry independence preconditions",
    ):
        _validate(
            (_entry("evidence_a", left), _entry("evidence_b", right)),
            graph,
        )


def test_aliases_across_observations_reject(monkeypatch) -> None:
    _patch_prior_gate(monkeypatch)
    left = _selection(
        PilotObservationSelectionKind.RECRUITMENT_BATCH,
        "recruitment_batch:left",
    )
    right = _selection(
        PilotObservationSelectionKind.RECRUITMENT_BATCH,
        "recruitment_batch:right",
    )
    graph = PilotObservationSelectionLineageGraph(
        relations=(
            PilotObservationSelectionRelation(
                PilotObservationSelectionRelationKind.ALIAS_OF,
                left,
                right,
            ),
        )
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="selection-ancestry independence preconditions",
    ):
        _validate(
            (_entry("evidence_a", left), _entry("evidence_b", right)),
            graph,
        )


def test_disjoint_selection_roots_pass_only_structural_precondition(
    monkeypatch,
) -> None:
    _patch_prior_gate(monkeypatch)
    left = _selection(
        PilotObservationSelectionKind.SELECTION_EPISODE,
        "selection_episode:left",
    )
    right = _selection(
        PilotObservationSelectionKind.SELECTION_EPISODE,
        "selection_episode:right",
    )
    graph = PilotObservationSelectionLineageGraph()
    entries = (_entry("evidence_a", left), _entry("evidence_b", right))
    assert _validate(entries, graph) == entries


def test_multiple_aliases_within_one_observation_do_not_self_collide(
    monkeypatch,
) -> None:
    _patch_prior_gate(monkeypatch)
    left = _selection(
        PilotObservationSelectionKind.INCLUSION_POLICY_EXECUTION,
        "inclusion_exec:left",
    )
    alias = _selection(
        PilotObservationSelectionKind.INCLUSION_POLICY_EXECUTION,
        "inclusion_exec:alias",
    )
    other = _selection(
        PilotObservationSelectionKind.INCLUSION_POLICY_EXECUTION,
        "inclusion_exec:other",
    )
    graph = PilotObservationSelectionLineageGraph(
        relations=(
            PilotObservationSelectionRelation(
                PilotObservationSelectionRelationKind.ALIAS_OF,
                left,
                alias,
            ),
        )
    )
    entries = (
        _entry("evidence_a", left, alias),
        _entry("evidence_b", other),
    )
    assert _validate(entries, graph) == entries


def test_prior_exact_selection_gate_rejection_dominates(monkeypatch) -> None:
    selection = _selection(
        PilotObservationSelectionKind.SELECTION_EPISODE,
        "selection_episode:shared",
    )

    def reject(*args, **kwargs):
        raise InvalidPilotEvidenceMaterialization(
            "shared-selection independence preconditions"
        )

    monkeypatch.setattr(
        selection_lineage_module._selection,
        "validate_pilot_materialized_evidence_shared_selection_preconditions_v1",
        reject,
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="shared-selection independence preconditions",
    ):
        _validate(
            (_entry("evidence_a", selection), _entry("evidence_b", selection)),
            PilotObservationSelectionLineageGraph(),
        )


def test_reverse_alias_duplicate_rejected() -> None:
    left = _selection(
        PilotObservationSelectionKind.RECRUITMENT_BATCH,
        "recruitment_batch:left",
    )
    right = _selection(
        PilotObservationSelectionKind.RECRUITMENT_BATCH,
        "recruitment_batch:right",
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="reverse-alias relation",
    ):
        PilotObservationSelectionLineageGraph(
            relations=(
                PilotObservationSelectionRelation(
                    PilotObservationSelectionRelationKind.ALIAS_OF,
                    left,
                    right,
                ),
                PilotObservationSelectionRelation(
                    PilotObservationSelectionRelationKind.ALIAS_OF,
                    right,
                    left,
                ),
            )
        )


def test_conflicting_directed_relation_kinds_rejected() -> None:
    child = _selection(
        PilotObservationSelectionKind.COHORT_CONSTRUCTION_STATE,
        "cohort_state:child",
    )
    root = _selection(
        PilotObservationSelectionKind.SAMPLING_FRAME_INSTANCE,
        "sampling_frame:root",
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="conflicting relation kinds",
    ):
        PilotObservationSelectionLineageGraph(
            relations=(
                PilotObservationSelectionRelation(
                    PilotObservationSelectionRelationKind.DERIVED_FROM,
                    child,
                    root,
                ),
                PilotObservationSelectionRelation(
                    PilotObservationSelectionRelationKind.CLONED_FROM,
                    child,
                    root,
                ),
            )
        )


def test_directed_cycle_rejected() -> None:
    left = _selection(
        PilotObservationSelectionKind.COHORT_CONSTRUCTION_STATE,
        "cohort_state:left",
    )
    right = _selection(
        PilotObservationSelectionKind.COHORT_CONSTRUCTION_STATE,
        "cohort_state:right",
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="acyclic after alias contraction",
    ):
        PilotObservationSelectionLineageGraph(
            relations=(
                PilotObservationSelectionRelation(
                    PilotObservationSelectionRelationKind.DERIVED_FROM,
                    left,
                    right,
                ),
                PilotObservationSelectionRelation(
                    PilotObservationSelectionRelationKind.DERIVED_FROM,
                    right,
                    left,
                ),
            )
        )


def test_alias_contracted_cycle_rejected() -> None:
    left = _selection(
        PilotObservationSelectionKind.COHORT_CONSTRUCTION_STATE,
        "cohort_state:left",
    )
    alias = _selection(
        PilotObservationSelectionKind.COHORT_CONSTRUCTION_STATE,
        "cohort_state:left_alias",
    )
    right = _selection(
        PilotObservationSelectionKind.COHORT_CONSTRUCTION_STATE,
        "cohort_state:right",
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="acyclic after alias contraction",
    ):
        PilotObservationSelectionLineageGraph(
            relations=(
                PilotObservationSelectionRelation(
                    PilotObservationSelectionRelationKind.ALIAS_OF,
                    left,
                    alias,
                ),
                PilotObservationSelectionRelation(
                    PilotObservationSelectionRelationKind.DERIVED_FROM,
                    alias,
                    right,
                ),
                PilotObservationSelectionRelation(
                    PilotObservationSelectionRelationKind.STATE_CONTINUATION_OF,
                    right,
                    left,
                ),
            )
        )


def test_directed_relation_inside_alias_class_rejected() -> None:
    left = _selection(
        PilotObservationSelectionKind.COHORT_CONSTRUCTION_STATE,
        "cohort_state:left",
    )
    alias = _selection(
        PilotObservationSelectionKind.COHORT_CONSTRUCTION_STATE,
        "cohort_state:alias",
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="must not collapse within one alias class",
    ):
        PilotObservationSelectionLineageGraph(
            relations=(
                PilotObservationSelectionRelation(
                    PilotObservationSelectionRelationKind.ALIAS_OF,
                    left,
                    alias,
                ),
                PilotObservationSelectionRelation(
                    PilotObservationSelectionRelationKind.DERIVED_FROM,
                    left,
                    alias,
                ),
            )
        )


def test_self_relation_rejected() -> None:
    selection = _selection(
        PilotObservationSelectionKind.SELECTION_EPISODE,
        "selection_episode:self",
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="two distinct exact selection refs",
    ):
        PilotObservationSelectionRelation(
            PilotObservationSelectionRelationKind.DERIVED_FROM,
            selection,
            selection,
        )


def test_relation_enum_contains_no_design_similarity_pseudorelations() -> None:
    values = {item.value for item in PilotObservationSelectionRelationKind}
    assert "SAME_POPULATION" not in values
    assert "SAME_COHORT" not in values
    assert "USES_SAMPLER" not in values
    assert "SAME_INCLUSION_RULE" not in values
    assert "INSTANCE_OF" not in values
    assert "SAME_STUDY_FAMILY" not in values


def test_closure_rejects_wrong_selection_type() -> None:
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="selection must be PilotObservationSelectionRef",
    ):
        pilot_observation_selection_lineage_closure_keys_v1(
            object(),
            PilotObservationSelectionLineageGraph(),
        )


def test_validator_rejects_wrong_graph_type() -> None:
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="selection_lineage_graph must be PilotObservationSelectionLineageGraph",
    ):
        marker = object()
        validate_pilot_materialized_evidence_selection_ancestry_preconditions_v1(
            (),
            source_lineage_graph=marker,
            source_completeness_review=marker,
            mechanism_lineage_graph=marker,
            mechanism_completeness_review=marker,
            coordination_lineage_graph=marker,
            coordination_completeness_review=marker,
            temporal_lineage_graph=marker,
            temporal_completeness_review=marker,
            allocation_lineage_graph=marker,
            allocation_completeness_review=marker,
            selection_lineage_graph=object(),
        )
