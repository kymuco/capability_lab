import pytest

from capability_lab.pilots.civilization_bootstrap_01 import (
    InvalidPilotEvidenceMaterialization,
    validate_pilot_materialized_evidence_reviewed_dependence_preconditions_v1,
)
from capability_lab.pilots.civilization_bootstrap_01 import (
    materialization_terminal as terminal_module,
)


def _markers():
    marker = object()
    return {
        "materialization_resolution_bindings": (),
        "source_lineage_graph": marker,
        "source_completeness_review": marker,
        "mechanism_lineage_graph": marker,
        "mechanism_completeness_review": marker,
        "coordination_lineage_graph": marker,
        "coordination_completeness_review": marker,
        "temporal_lineage_graph": marker,
        "temporal_completeness_review": marker,
        "allocation_lineage_graph": marker,
        "allocation_completeness_review": marker,
        "selection_lineage_graph": marker,
        "selection_completeness_review": marker,
    }


def test_terminal_rejects_empty_basis_before_any_family_review() -> None:
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="require at least two materialized observation slots",
    ):
        validate_pilot_materialized_evidence_reviewed_dependence_preconditions_v1(
            (),
            **_markers(),
        )


def test_terminal_rejects_singleton_basis_before_any_family_review(
    monkeypatch,
) -> None:
    singleton = object()
    monkeypatch.setattr(
        terminal_module,
        "_selection_entries_tuple",
        lambda _values: (singleton,),
    )

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="require at least two materialized observation slots",
    ):
        validate_pilot_materialized_evidence_reviewed_dependence_preconditions_v1(
            (singleton,),
            **_markers(),
        )


def test_terminal_cardinality_guard_dominates_lower_family_gate(
    monkeypatch,
) -> None:
    def should_not_run(*_args, **_kwargs):
        raise AssertionError("lower family gate must not run for vacuous terminal basis")

    monkeypatch.setattr(
        terminal_module._selection_completeness,
        "validate_pilot_materialized_evidence_reviewed_selection_origin_preconditions_v1",
        should_not_run,
    )

    with pytest.raises(InvalidPilotEvidenceMaterialization):
        validate_pilot_materialized_evidence_reviewed_dependence_preconditions_v1(
            (),
            **_markers(),
        )


def test_two_slots_are_not_rejected_by_cardinality_guard(monkeypatch) -> None:
    first = object()
    second = object()
    entries = (first, second)
    sentinel = ("terminal-lower-gate-result",)

    monkeypatch.setattr(
        terminal_module,
        "_selection_entries_tuple",
        lambda _values: entries,
    )
    monkeypatch.setattr(
        terminal_module,
        "_validate_unique_evidence_identity_v1",
        lambda _entries: None,
    )
    monkeypatch.setattr(
        terminal_module,
        "_validate_reviewed_resolution_bindings_v1",
        lambda _entries, _bindings: None,
    )
    monkeypatch.setattr(
        terminal_module,
        "_validate_completeness_review_temporal_causality_v1",
        lambda _entries, **_kwargs: None,
    )
    monkeypatch.setattr(
        terminal_module._selection_completeness,
        "validate_pilot_materialized_evidence_reviewed_selection_origin_preconditions_v1",
        lambda _entries, **_kwargs: sentinel,
    )

    assert (
        validate_pilot_materialized_evidence_reviewed_dependence_preconditions_v1(
            entries,
            **_markers(),
        )
        == sentinel
    )
