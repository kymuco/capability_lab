from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from capability_lab.pilots.civilization_bootstrap_01 import materialization_selection_completeness as c
from capability_lab.pilots.civilization_bootstrap_01.materialization import (
    InvalidPilotEvidenceMaterialization,
    PilotEvidenceMaterializationReviewerKind,
    PilotEvidenceMaterializationReviewerRef,
)
from capability_lab.pilots.civilization_bootstrap_01.materialization_selection_dependence import (
    PilotObservationSelectionKind,
    PilotObservationSelectionRef,
)
from capability_lab.pilots.civilization_bootstrap_01.materialization_selection_lineage import (
    PilotObservationSelectionLineageGraph,
    PilotObservationSelectionRelation,
    PilotObservationSelectionRelationKind,
)

T0 = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)


def _ref(kind, ref):
    return SimpleNamespace(kind=SimpleNamespace(value=kind), ref=ref)


def _entry(evidence, candidate, suffix):
    basis = SimpleNamespace(
        evidence=SimpleNamespace(evidence_id=evidence),
        exact_source_key=f"pilot_capture:{suffix * 64}",
    )
    upstream = SimpleNamespace(
        basis_entry=basis,
        upstream_declaration=SimpleNamespace(sources=(_ref("ARTIFACT", f"source:{suffix}"),)),
    )
    mechanism = SimpleNamespace(
        upstream_lineage_entry=upstream,
        mechanism_declaration=SimpleNamespace(mechanisms=(_ref("TOOL_EXECUTION", f"mechanism:{suffix}"),)),
    )
    coordination = SimpleNamespace(
        mechanism_entry=mechanism,
        coordination_declaration=SimpleNamespace(coordinations=(_ref("CONTROLLER", f"coordination:{suffix}"),)),
    )
    temporal = SimpleNamespace(
        coordination_entry=coordination,
        temporal_declaration=SimpleNamespace(temporals=(_ref("INTERVENTION_EPISODE", f"temporal:{suffix}"),)),
    )
    allocation = SimpleNamespace(
        temporal_entry=temporal,
        allocation_declaration=SimpleNamespace(allocations=(_ref("RANDOMIZATION_STATE", f"allocation:{suffix}"),)),
    )
    return SimpleNamespace(
        allocation_entry=allocation,
        selection_declaration=SimpleNamespace(
            candidate_sha256=candidate,
            selections=(_ref("SAMPLING_FRAME_INSTANCE", f"selection:{suffix}"),),
        ),
    )


def _entries():
    return (_entry("evidence_a", "1" * 64, "a"), _entry("evidence_b", "2" * 64, "b"))


def _patch_entries(monkeypatch):
    monkeypatch.setattr(c, "_entries_tuple", lambda values: tuple(sorted(
        tuple(values),
        key=lambda x: str(
            x.allocation_entry.temporal_entry.coordination_entry.mechanism_entry
            .upstream_lineage_entry.basis_entry.evidence.evidence_id
        ),
    )))


def _patch_prior(monkeypatch):
    monkeypatch.setattr(
        c._lineage,
        "validate_pilot_materialized_evidence_selection_ancestry_preconditions_v1",
        lambda entries, **kwargs: tuple(entries),
    )


def _review(entries, graph, d=c.PilotSelectionCompletenessStatus.COMPLETE_FOR_SCOPE,
            g=c.PilotSelectionCompletenessStatus.COMPLETE_FOR_SCOPE):
    return c.build_pilot_selection_lineage_completeness_review_v1(
        entries,
        selection_lineage_graph=graph,
        review_id="selection_complete_01",
        selection_declarations_status=d,
        selection_lineage_graph_status=g,
        reviewer_ref=PilotEvidenceMaterializationReviewerRef(
            PilotEvidenceMaterializationReviewerKind.HUMAN, "reviewer_selection_01"
        ),
        reviewed_at=T0,
        rationale="Reviewed bounded selection scope.",
    )


def _validate(entries, graph, review):
    marker = object()
    return c.validate_pilot_materialized_evidence_reviewed_selection_origin_preconditions_v1(
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
        selection_completeness_review=review,
    )


def test_complete_review_passes_only_bounded_precondition(monkeypatch):
    _patch_entries(monkeypatch)
    _patch_prior(monkeypatch)
    entries = _entries()
    graph = PilotObservationSelectionLineageGraph()
    review = _review(entries, graph)
    assert _validate(tuple(reversed(entries)), graph, review) == entries


@pytest.mark.parametrize("d,g", [
    (c.PilotSelectionCompletenessStatus.UNKNOWN, c.PilotSelectionCompletenessStatus.COMPLETE_FOR_SCOPE),
    (c.PilotSelectionCompletenessStatus.INCOMPLETE, c.PilotSelectionCompletenessStatus.COMPLETE_FOR_SCOPE),
    (c.PilotSelectionCompletenessStatus.COMPLETE_FOR_SCOPE, c.PilotSelectionCompletenessStatus.UNKNOWN),
    (c.PilotSelectionCompletenessStatus.COMPLETE_FOR_SCOPE, c.PilotSelectionCompletenessStatus.INCOMPLETE),
])
def test_unknown_or_incomplete_fails_closed(monkeypatch, d, g):
    _patch_entries(monkeypatch)
    _patch_prior(monkeypatch)
    entries = _entries()
    graph = PilotObservationSelectionLineageGraph()
    with pytest.raises(InvalidPilotEvidenceMaterialization):
        _validate(entries, graph, _review(entries, graph, d, g))


def test_scope_binds_all_lower_basis_and_selection(monkeypatch):
    _patch_entries(monkeypatch)
    entries = _entries()
    original = c.pilot_observation_selection_origin_scope_sha256_v1(entries)
    changed = list(entries)
    changed[0] = _entry("evidence_a", "3" * 64, "a")
    assert original != c.pilot_observation_selection_origin_scope_sha256_v1(changed)


def test_scope_is_order_independent(monkeypatch):
    _patch_entries(monkeypatch)
    entries = _entries()
    assert c.pilot_observation_selection_origin_scope_sha256_v1(entries) == (
        c.pilot_observation_selection_origin_scope_sha256_v1(tuple(reversed(entries)))
    )


def test_graph_hash_canonicalizes_reverse_alias():
    left = PilotObservationSelectionRef(PilotObservationSelectionKind.SAMPLING_FRAME_INSTANCE, "frame:left")
    right = PilotObservationSelectionRef(PilotObservationSelectionKind.SAMPLING_FRAME_INSTANCE, "frame:right")
    a = PilotObservationSelectionLineageGraph(relations=(
        PilotObservationSelectionRelation(PilotObservationSelectionRelationKind.ALIAS_OF, left, right),
    ))
    b = PilotObservationSelectionLineageGraph(relations=(
        PilotObservationSelectionRelation(PilotObservationSelectionRelationKind.ALIAS_OF, right, left),
    ))
    assert c.pilot_observation_selection_lineage_graph_sha256_v1(a) == c.pilot_observation_selection_lineage_graph_sha256_v1(b)


def test_stale_graph_review_rejected(monkeypatch):
    _patch_entries(monkeypatch)
    _patch_prior(monkeypatch)
    entries = _entries()
    empty = PilotObservationSelectionLineageGraph()
    review = _review(entries, empty)
    child = PilotObservationSelectionRef(PilotObservationSelectionKind.RESAMPLING_DRAW, "draw:child")
    root = PilotObservationSelectionRef(PilotObservationSelectionKind.COHORT_CONSTRUCTION_STATE, "cohort:root")
    changed = PilotObservationSelectionLineageGraph(relations=(
        PilotObservationSelectionRelation(PilotObservationSelectionRelationKind.RESAMPLED_FROM, child, root),
    ))
    with pytest.raises(InvalidPilotEvidenceMaterialization, match="graph_sha256"):
        _validate(entries, changed, review)


def test_known_ancestry_rejects_before_completeness(monkeypatch):
    _patch_entries(monkeypatch)
    entries = _entries()
    graph = PilotObservationSelectionLineageGraph()
    review = _review(entries, graph)
    def reject(*args, **kwargs):
        raise InvalidPilotEvidenceMaterialization("selection-ancestry independence preconditions")
    monkeypatch.setattr(c._lineage, "validate_pilot_materialized_evidence_selection_ancestry_preconditions_v1", reject)
    with pytest.raises(InvalidPilotEvidenceMaterialization, match="selection-ancestry"):
        _validate(entries, graph, review)


def test_raw_string_status_rejected(monkeypatch):
    _patch_entries(monkeypatch)
    entries = _entries()
    graph = PilotObservationSelectionLineageGraph()
    with pytest.raises(InvalidPilotEvidenceMaterialization, match="status must be PilotSelectionCompletenessStatus"):
        c.PilotSelectionLineageCompletenessReview(
            review_id="bad_01",
            scope_sha256=c.pilot_observation_selection_origin_scope_sha256_v1(entries),
            graph_sha256=c.pilot_observation_selection_lineage_graph_sha256_v1(graph),
            selection_declarations_status="COMPLETE_FOR_SCOPE",
            selection_lineage_graph_status=c.PilotSelectionCompletenessStatus.COMPLETE_FOR_SCOPE,
            reviewer_ref=PilotEvidenceMaterializationReviewerRef(
                PilotEvidenceMaterializationReviewerKind.HUMAN, "reviewer"
            ),
            reviewed_at=T0,
            rationale="bad raw status",
        )
