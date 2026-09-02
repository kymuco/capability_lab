from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from capability_lab.pilots.civilization_bootstrap_01 import (
    InvalidPilotEvidenceMaterialization,
    PilotEvidenceMaterializationReviewerKind,
    PilotEvidenceMaterializationReviewerRef,
    PilotObservationTemporalKind,
    PilotObservationTemporalLineageGraph,
    PilotObservationTemporalRef,
    PilotObservationTemporalRelation,
    PilotObservationTemporalRelationKind,
    PilotTemporalCompletenessStatus,
    PilotTemporalLineageCompletenessReview,
    build_pilot_temporal_lineage_completeness_review_v1,
    pilot_observation_temporal_lineage_graph_sha256_v1,
    pilot_observation_temporal_origin_scope_sha256_v1,
    validate_pilot_materialized_evidence_reviewed_temporal_origin_preconditions_v1,
)
from capability_lab.pilots.civilization_bootstrap_01 import (
    materialization_temporal_completeness as completeness_module,
)


T0 = datetime(2026, 1, 14, 12, 0, tzinfo=timezone.utc)


def _reviewer():
    return PilotEvidenceMaterializationReviewerRef(
        PilotEvidenceMaterializationReviewerKind.HUMAN,
        "reviewer_temporal_completeness_01",
    )


def _ref(kind, ref):
    return SimpleNamespace(kind=SimpleNamespace(value=kind), ref=ref)


def _entry(
    evidence_id,
    *,
    candidate="1" * 64,
    capture="pilot_capture:" + "a" * 64,
    source="artifact:source_a",
    mechanism="tool_execution:run_a",
    coordination="controller:control_a",
    temporal="intervention_episode:temporal_a",
):
    basis = SimpleNamespace(
        evidence=SimpleNamespace(evidence_id=evidence_id),
        exact_source_key=capture,
    )
    upstream = SimpleNamespace(
        basis_entry=basis,
        upstream_declaration=SimpleNamespace(sources=(_ref("ARTIFACT", source),)),
    )
    mech = SimpleNamespace(
        upstream_lineage_entry=upstream,
        mechanism_declaration=SimpleNamespace(
            mechanisms=(_ref("TOOL_EXECUTION", mechanism),)
        ),
    )
    coord = SimpleNamespace(
        mechanism_entry=mech,
        coordination_declaration=SimpleNamespace(
            coordinations=(_ref("CONTROLLER", coordination),)
        ),
    )
    return SimpleNamespace(
        coordination_entry=coord,
        temporal_declaration=SimpleNamespace(
            candidate_sha256=candidate,
            temporals=(_ref("INTERVENTION_EPISODE", temporal),),
        ),
    )


def _entries():
    return (
        _entry("evidence_a"),
        _entry(
            "evidence_b",
            candidate="2" * 64,
            capture="pilot_capture:" + "b" * 64,
            source="artifact:source_b",
            mechanism="tool_execution:run_b",
            coordination="controller:control_b",
            temporal="intervention_episode:temporal_b",
        ),
    )


def _patch_entries(monkeypatch):
    def canonical(values):
        return tuple(
            sorted(
                tuple(values),
                key=lambda item: str(
                    item.coordination_entry.mechanism_entry.upstream_lineage_entry
                    .basis_entry.evidence.evidence_id
                ),
            )
        )

    monkeypatch.setattr(completeness_module, "_temporal_entries_tuple", canonical)
    return canonical


def _patch_prior_gate(monkeypatch):
    monkeypatch.setattr(
        completeness_module._temporal_lineage,
        "validate_pilot_materialized_evidence_temporal_ancestry_preconditions_v1",
        lambda entries, **kwargs: tuple(entries),
    )


def _complete_review(entries, graph):
    return build_pilot_temporal_lineage_completeness_review_v1(
        entries,
        temporal_lineage_graph=graph,
        review_id="temporal_completeness_complete_01",
        temporal_declarations_status=PilotTemporalCompletenessStatus.COMPLETE_FOR_SCOPE,
        temporal_lineage_graph_status=PilotTemporalCompletenessStatus.COMPLETE_FOR_SCOPE,
        reviewer_ref=_reviewer(),
        reviewed_at=T0,
        rationale="Reviewed exact bounded temporal scope.",
    )


def _validate(entries, graph, review):
    marker = object()
    return validate_pilot_materialized_evidence_reviewed_temporal_origin_preconditions_v1(
        entries,
        source_lineage_graph=marker,
        source_completeness_review=marker,
        mechanism_lineage_graph=marker,
        mechanism_completeness_review=marker,
        coordination_lineage_graph=marker,
        coordination_completeness_review=marker,
        temporal_lineage_graph=graph,
        temporal_completeness_review=review,
    )


def test_both_complete_dimensions_allow_only_bounded_precondition(monkeypatch) -> None:
    canonical = _patch_entries(monkeypatch)
    _patch_prior_gate(monkeypatch)
    entries = _entries()
    graph = PilotObservationTemporalLineageGraph()
    review = _complete_review(entries, graph)
    assert _validate(tuple(reversed(entries)), graph, review) == canonical(entries)


@pytest.mark.parametrize(
    "declarations,graph_status,match",
    [
        (
            PilotTemporalCompletenessStatus.INCOMPLETE,
            PilotTemporalCompletenessStatus.COMPLETE_FOR_SCOPE,
            "temporal declarations are not reviewed COMPLETE_FOR_SCOPE",
        ),
        (
            PilotTemporalCompletenessStatus.UNKNOWN,
            PilotTemporalCompletenessStatus.COMPLETE_FOR_SCOPE,
            "temporal declarations are not reviewed COMPLETE_FOR_SCOPE",
        ),
        (
            PilotTemporalCompletenessStatus.COMPLETE_FOR_SCOPE,
            PilotTemporalCompletenessStatus.INCOMPLETE,
            "temporal lineage graph is not reviewed COMPLETE_FOR_SCOPE",
        ),
        (
            PilotTemporalCompletenessStatus.COMPLETE_FOR_SCOPE,
            PilotTemporalCompletenessStatus.UNKNOWN,
            "temporal lineage graph is not reviewed COMPLETE_FOR_SCOPE",
        ),
    ],
)
def test_unknown_or_incomplete_fails_closed(
    monkeypatch, declarations, graph_status, match
) -> None:
    _patch_entries(monkeypatch)
    _patch_prior_gate(monkeypatch)
    entries = _entries()
    graph = PilotObservationTemporalLineageGraph()
    review = build_pilot_temporal_lineage_completeness_review_v1(
        entries,
        temporal_lineage_graph=graph,
        review_id="temporal_completeness_negative_01",
        temporal_declarations_status=declarations,
        temporal_lineage_graph_status=graph_status,
        reviewer_ref=_reviewer(),
        reviewed_at=T0,
        rationale="Negative completeness review.",
    )
    with pytest.raises(InvalidPilotEvidenceMaterialization, match=match):
        _validate(entries, graph, review)


def test_review_cannot_replay_onto_changed_graph(monkeypatch) -> None:
    _patch_entries(monkeypatch)
    _patch_prior_gate(monkeypatch)
    entries = _entries()
    graph_a = PilotObservationTemporalLineageGraph()
    review = _complete_review(entries, graph_a)
    child = PilotObservationTemporalRef(
        PilotObservationTemporalKind.CARRYOVER_STATE, "carryover_state:child"
    )
    root = PilotObservationTemporalRef(
        PilotObservationTemporalKind.HISTORY_STATE, "history_state:root"
    )
    graph_b = PilotObservationTemporalLineageGraph(
        relations=(
            PilotObservationTemporalRelation(
                PilotObservationTemporalRelationKind.CARRYOVER_FROM, child, root
            ),
        )
    )
    assert pilot_observation_temporal_lineage_graph_sha256_v1(graph_a) != (
        pilot_observation_temporal_lineage_graph_sha256_v1(graph_b)
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="graph_sha256 does not match exact temporal-lineage graph",
    ):
        _validate(entries, graph_b, review)


@pytest.mark.parametrize(
    "replacement",
    [
        dict(candidate="3" * 64),
        dict(capture="pilot_capture:" + "c" * 64),
        dict(source="artifact:replacement"),
        dict(mechanism="tool_execution:replacement"),
        dict(coordination="controller:replacement"),
        dict(temporal="intervention_episode:replacement"),
    ],
)
def test_scope_digest_binds_lower_and_temporal_basis(monkeypatch, replacement) -> None:
    _patch_entries(monkeypatch)
    entries = _entries()
    changed = (
        _entry("evidence_a", **replacement),
        entries[1],
    )
    assert pilot_observation_temporal_origin_scope_sha256_v1(entries) != (
        pilot_observation_temporal_origin_scope_sha256_v1(changed)
    )


def test_scope_digest_is_order_independent(monkeypatch) -> None:
    _patch_entries(monkeypatch)
    entries = _entries()
    assert pilot_observation_temporal_origin_scope_sha256_v1(entries) == (
        pilot_observation_temporal_origin_scope_sha256_v1(tuple(reversed(entries)))
    )


def test_graph_hash_canonicalizes_reverse_alias_orientation() -> None:
    left = PilotObservationTemporalRef(
        PilotObservationTemporalKind.ADAPTIVE_STATE, "adaptive_state:left"
    )
    right = PilotObservationTemporalRef(
        PilotObservationTemporalKind.ADAPTIVE_STATE, "adaptive_state:right"
    )
    graph_a = PilotObservationTemporalLineageGraph(
        relations=(
            PilotObservationTemporalRelation(
                PilotObservationTemporalRelationKind.ALIAS_OF, left, right
            ),
        )
    )
    graph_b = PilotObservationTemporalLineageGraph(
        relations=(
            PilotObservationTemporalRelation(
                PilotObservationTemporalRelationKind.ALIAS_OF, right, left
            ),
        )
    )
    assert pilot_observation_temporal_lineage_graph_sha256_v1(graph_a) == (
        pilot_observation_temporal_lineage_graph_sha256_v1(graph_b)
    )


def test_known_temporal_ancestry_rejects_before_completeness(monkeypatch) -> None:
    _patch_entries(monkeypatch)
    entries = _entries()
    graph = PilotObservationTemporalLineageGraph()
    review = _complete_review(entries, graph)

    def reject(*args, **kwargs):
        raise InvalidPilotEvidenceMaterialization(
            "temporal-ancestry independence preconditions"
        )

    monkeypatch.setattr(
        completeness_module._temporal_lineage,
        "validate_pilot_materialized_evidence_temporal_ancestry_preconditions_v1",
        reject,
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="temporal-ancestry independence preconditions",
    ):
        _validate(entries, graph, review)


def test_raw_string_status_rejected(monkeypatch) -> None:
    _patch_entries(monkeypatch)
    entries = _entries()
    graph = PilotObservationTemporalLineageGraph()
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="temporal declarations status must be PilotTemporalCompletenessStatus",
    ):
        PilotTemporalLineageCompletenessReview(
            review_id="bad_status_01",
            scope_sha256=pilot_observation_temporal_origin_scope_sha256_v1(entries),
            graph_sha256=pilot_observation_temporal_lineage_graph_sha256_v1(graph),
            temporal_declarations_status="COMPLETE_FOR_SCOPE",
            temporal_lineage_graph_status=PilotTemporalCompletenessStatus.COMPLETE_FOR_SCOPE,
            reviewer_ref=_reviewer(),
            reviewed_at=T0,
            rationale="Invalid raw string status.",
        )


def test_review_time_and_rationale_are_canonicalized(monkeypatch) -> None:
    _patch_entries(monkeypatch)
    review = build_pilot_temporal_lineage_completeness_review_v1(
        _entries(),
        temporal_lineage_graph=PilotObservationTemporalLineageGraph(),
        review_id="normalization_01",
        temporal_declarations_status=PilotTemporalCompletenessStatus.COMPLETE_FOR_SCOPE,
        temporal_lineage_graph_status=PilotTemporalCompletenessStatus.COMPLETE_FOR_SCOPE,
        reviewer_ref=_reviewer(),
        reviewed_at=datetime(
            2026, 1, 14, 18, 30, tzinfo=timezone(timedelta(hours=6))
        ),
        rationale="  Reviewed bounded temporal scope.  ",
    )
    assert review.reviewed_at == datetime(2026, 1, 14, 12, 30, tzinfo=timezone.utc)
    assert review.rationale == "Reviewed bounded temporal scope."


def test_scope_helper_rejects_wrong_entry_type() -> None:
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="must contain PilotMaterializedEvidenceTemporalEntry",
    ):
        pilot_observation_temporal_origin_scope_sha256_v1((object(),))
