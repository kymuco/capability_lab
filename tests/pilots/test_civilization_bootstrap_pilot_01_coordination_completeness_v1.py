from datetime import datetime, timedelta, timezone

import pytest

from capability_lab.epistemics import CapabilitySubjectRef, EvidenceId
from capability_lab.pilots.civilization_bootstrap_01 import (
    REVIEWED_PILOT_CAPTURE_TO_EVIDENCE_POLICY_V1,
    InvalidPilotEvidenceMaterialization,
    PilotCoordinationCompletenessStatus,
    PilotCoordinationLineageCompletenessReview,
    PilotEvidenceMaterializationId,
    PilotEvidenceMaterializationReview,
    PilotEvidenceMaterializationReviewId,
    PilotEvidenceMaterializationReviewerKind,
    PilotEvidenceMaterializationReviewerRef,
    PilotEvidenceMaterializationVerdict,
    PilotLineageCompletenessStatus,
    PilotMaterializedEvidenceBasisEntry,
    PilotMaterializedEvidenceCoordinationEntry,
    PilotMaterializedEvidenceMechanismEntry,
    PilotMaterializedEvidenceUpstreamLineageEntry,
    PilotMechanismCompletenessStatus,
    PilotObservationCoordinationKind,
    PilotObservationCoordinationLineageGraph,
    PilotObservationCoordinationRef,
    PilotObservationCoordinationRelation,
    PilotObservationCoordinationRelationKind,
    PilotObservationMechanismKind,
    PilotObservationMechanismLineageGraph,
    PilotObservationMechanismRef,
    PilotUpstreamSourceKind,
    PilotUpstreamSourceLineageGraph,
    PilotUpstreamSourceRef,
    build_pilot_coordination_lineage_completeness_review_v1,
    build_pilot_materialization_coordination_declaration_v1,
    build_pilot_materialization_mechanism_declaration_v1,
    build_pilot_materialization_upstream_source_declaration_v1,
    build_pilot_mechanism_lineage_completeness_review_v1,
    build_pilot_upstream_lineage_completeness_review_v1,
    initialize_private_workspace,
    pilot_evidence_materialization_candidate_sha256,
    pilot_observation_coordination_lineage_graph_sha256_v1,
    pilot_observation_coordination_origin_scope_sha256_v1,
    propose_pilot_capture_evidence_materialization_v1,
    record_text_capture,
    resolve_reviewed_pilot_evidence_materialization_v1,
    validate_pilot_materialized_evidence_reviewed_coordination_origin_preconditions_v1,
)


T0 = datetime(2026, 1, 12, 12, 0, tzinfo=timezone.utc)


def _reviewer():
    return PilotEvidenceMaterializationReviewerRef(
        PilotEvidenceMaterializationReviewerKind.HUMAN,
        "reviewer_coordination_completeness_01",
    )


def _workspace(tmp_path, *, name, session_id, capture_id, probe_id, text):
    root = tmp_path / name
    initialize_private_workspace(
        root,
        session_id=session_id,
        subject_ref=CapabilitySubjectRef("subject_coordination_completeness_01"),
        created_at=T0,
    )
    record_text_capture(
        root,
        capture_id=capture_id,
        probe_id=probe_id,
        text_content=text,
        captured_at=T0 + timedelta(minutes=1),
    )
    return root


def _materialize(root, *, capture_id, materialization_id, evidence_id, review_id):
    candidate = propose_pilot_capture_evidence_materialization_v1(
        root,
        capture_id=capture_id,
        materialization_id=PilotEvidenceMaterializationId(materialization_id),
        proposed_evidence_id=EvidenceId(evidence_id),
        proposed_at=T0 + timedelta(minutes=2),
    )
    review = PilotEvidenceMaterializationReview(
        review_id=PilotEvidenceMaterializationReviewId(review_id),
        materialization_id=candidate.materialization_id,
        candidate_sha256=pilot_evidence_materialization_candidate_sha256(candidate),
        policy_ref=REVIEWED_PILOT_CAPTURE_TO_EVIDENCE_POLICY_V1,
        reviewer_ref=_reviewer(),
        verdict=PilotEvidenceMaterializationVerdict.MATERIALIZE,
        reviewed_at=T0 + timedelta(minutes=3),
        rationale="Materialize exact synthetic observation.",
    )
    evidence = resolve_reviewed_pilot_evidence_materialization_v1(
        root,
        candidate=candidate,
        review=review,
        resolved_at=T0 + timedelta(minutes=4),
    )
    assert evidence is not None
    return candidate, evidence


def _basis(tmp_path):
    root_a = _workspace(
        tmp_path,
        name="coord_complete_conceptual",
        session_id="session_coord_complete_a",
        capture_id="conceptual_01",
        probe_id="conceptual_explanation",
        text="Synthetic conceptual observation.",
    )
    root_b = _workspace(
        tmp_path,
        name="coord_complete_calculation",
        session_id="session_coord_complete_b",
        capture_id="calculation_01",
        probe_id="calculation_work",
        text="Synthetic calculation observation.",
    )
    candidate_a, evidence_a = _materialize(
        root_a,
        capture_id="conceptual_01",
        materialization_id="materialization_coord_complete_a",
        evidence_id="evidence_coord_complete_a",
        review_id="review_coord_complete_a",
    )
    candidate_b, evidence_b = _materialize(
        root_b,
        capture_id="calculation_01",
        materialization_id="materialization_coord_complete_b",
        evidence_id="evidence_coord_complete_b",
        review_id="review_coord_complete_b",
    )

    upstream_a = PilotMaterializedEvidenceUpstreamLineageEntry(
        PilotMaterializedEvidenceBasisEntry(candidate_a, evidence_a),
        build_pilot_materialization_upstream_source_declaration_v1(
            candidate_a,
            sources=(
                PilotUpstreamSourceRef(
                    PilotUpstreamSourceKind.ARTIFACT,
                    "artifact:coord_complete_source_a",
                ),
            ),
        ),
    )
    upstream_b = PilotMaterializedEvidenceUpstreamLineageEntry(
        PilotMaterializedEvidenceBasisEntry(candidate_b, evidence_b),
        build_pilot_materialization_upstream_source_declaration_v1(
            candidate_b,
            sources=(
                PilotUpstreamSourceRef(
                    PilotUpstreamSourceKind.DATASET,
                    "dataset:coord_complete_source_b",
                ),
            ),
        ),
    )
    source_graph = PilotUpstreamSourceLineageGraph()
    source_review = build_pilot_upstream_lineage_completeness_review_v1(
        (upstream_a, upstream_b),
        source_lineage_graph=source_graph,
        review_id="source_complete_for_coord_complete_01",
        upstream_source_declarations_status=(
            PilotLineageCompletenessStatus.COMPLETE_FOR_SCOPE
        ),
        source_lineage_graph_status=(
            PilotLineageCompletenessStatus.COMPLETE_FOR_SCOPE
        ),
        reviewer_ref=_reviewer(),
        reviewed_at=T0 + timedelta(minutes=10),
        rationale="Reviewed exact source basis.",
    )

    mechanism_a = PilotObservationMechanismRef(
        PilotObservationMechanismKind.TOOL_EXECUTION,
        "tool_execution:coord_complete_run_a",
    )
    mechanism_b = PilotObservationMechanismRef(
        PilotObservationMechanismKind.TOOL_EXECUTION,
        "tool_execution:coord_complete_run_b",
    )
    mechanism_entry_a = PilotMaterializedEvidenceMechanismEntry(
        upstream_a,
        build_pilot_materialization_mechanism_declaration_v1(
            candidate_a,
            mechanisms=(mechanism_a,),
        ),
    )
    mechanism_entry_b = PilotMaterializedEvidenceMechanismEntry(
        upstream_b,
        build_pilot_materialization_mechanism_declaration_v1(
            candidate_b,
            mechanisms=(mechanism_b,),
        ),
    )
    mechanism_graph = PilotObservationMechanismLineageGraph()
    mechanism_review = build_pilot_mechanism_lineage_completeness_review_v1(
        (mechanism_entry_a, mechanism_entry_b),
        mechanism_lineage_graph=mechanism_graph,
        review_id="mechanism_complete_for_coord_complete_01",
        mechanism_declarations_status=(
            PilotMechanismCompletenessStatus.COMPLETE_FOR_SCOPE
        ),
        mechanism_lineage_graph_status=(
            PilotMechanismCompletenessStatus.COMPLETE_FOR_SCOPE
        ),
        reviewer_ref=_reviewer(),
        reviewed_at=T0 + timedelta(minutes=20),
        rationale="Reviewed exact mechanism basis.",
    )

    coordination_a = PilotObservationCoordinationRef(
        PilotObservationCoordinationKind.CONTROLLER,
        "controller:coord_complete_a",
    )
    coordination_b = PilotObservationCoordinationRef(
        PilotObservationCoordinationKind.ADAPTIVE_SELECTOR,
        "adaptive_selector:coord_complete_b",
    )
    entry_a = PilotMaterializedEvidenceCoordinationEntry(
        mechanism_entry_a,
        build_pilot_materialization_coordination_declaration_v1(
            candidate_a,
            coordinations=(coordination_a,),
        ),
    )
    entry_b = PilotMaterializedEvidenceCoordinationEntry(
        mechanism_entry_b,
        build_pilot_materialization_coordination_declaration_v1(
            candidate_b,
            coordinations=(coordination_b,),
        ),
    )
    return (
        candidate_a,
        candidate_b,
        entry_a,
        entry_b,
        source_graph,
        source_review,
        mechanism_graph,
        mechanism_review,
        coordination_a,
        coordination_b,
    )


def _complete_review(entries, graph):
    return build_pilot_coordination_lineage_completeness_review_v1(
        entries,
        coordination_lineage_graph=graph,
        review_id="coordination_completeness_complete_01",
        coordination_declarations_status=(
            PilotCoordinationCompletenessStatus.COMPLETE_FOR_SCOPE
        ),
        coordination_lineage_graph_status=(
            PilotCoordinationCompletenessStatus.COMPLETE_FOR_SCOPE
        ),
        reviewer_ref=_reviewer(),
        reviewed_at=T0 + timedelta(minutes=30),
        rationale="Reviewed exact coordination declarations and lineage graph.",
    )


def _validate(entries, sg, sr, mg, mr, cg, cr):
    return validate_pilot_materialized_evidence_reviewed_coordination_origin_preconditions_v1(
        entries,
        source_lineage_graph=sg,
        source_completeness_review=sr,
        mechanism_lineage_graph=mg,
        mechanism_completeness_review=mr,
        coordination_lineage_graph=cg,
        coordination_completeness_review=cr,
    )


def test_complete_for_scope_on_both_dimensions_allows_only_reviewed_coordination_origin_precondition(
    tmp_path,
) -> None:
    _, _, a, b, sg, sr, mg, mr, _, _ = _basis(tmp_path)
    entries = (a, b)
    graph = PilotObservationCoordinationLineageGraph()
    review = _complete_review(entries, graph)

    assert _validate(tuple(reversed(entries)), sg, sr, mg, mr, graph, review) == entries


@pytest.mark.parametrize(
    "declaration_status,graph_status,match",
    [
        (
            PilotCoordinationCompletenessStatus.INCOMPLETE,
            PilotCoordinationCompletenessStatus.COMPLETE_FOR_SCOPE,
            "observation coordination declarations are not reviewed COMPLETE_FOR_SCOPE",
        ),
        (
            PilotCoordinationCompletenessStatus.UNKNOWN,
            PilotCoordinationCompletenessStatus.COMPLETE_FOR_SCOPE,
            "observation coordination declarations are not reviewed COMPLETE_FOR_SCOPE",
        ),
        (
            PilotCoordinationCompletenessStatus.COMPLETE_FOR_SCOPE,
            PilotCoordinationCompletenessStatus.INCOMPLETE,
            "coordination lineage graph is not reviewed COMPLETE_FOR_SCOPE",
        ),
        (
            PilotCoordinationCompletenessStatus.COMPLETE_FOR_SCOPE,
            PilotCoordinationCompletenessStatus.UNKNOWN,
            "coordination lineage graph is not reviewed COMPLETE_FOR_SCOPE",
        ),
    ],
)
def test_incomplete_or_unknown_dimension_fails_closed(
    tmp_path,
    declaration_status,
    graph_status,
    match,
) -> None:
    _, _, a, b, sg, sr, mg, mr, _, _ = _basis(tmp_path)
    entries = (a, b)
    graph = PilotObservationCoordinationLineageGraph()
    review = build_pilot_coordination_lineage_completeness_review_v1(
        entries,
        coordination_lineage_graph=graph,
        review_id="coordination_completeness_negative_01",
        coordination_declarations_status=declaration_status,
        coordination_lineage_graph_status=graph_status,
        reviewer_ref=_reviewer(),
        reviewed_at=T0 + timedelta(minutes=30),
        rationale="Synthetic negative coordination completeness review.",
    )
    with pytest.raises(InvalidPilotEvidenceMaterialization, match=match):
        _validate(entries, sg, sr, mg, mr, graph, review)


def test_review_cannot_be_replayed_onto_changed_coordination_graph(tmp_path) -> None:
    _, _, a, b, sg, sr, mg, mr, _, _ = _basis(tmp_path)
    entries = (a, b)
    graph_a = PilotObservationCoordinationLineageGraph()
    review = _complete_review(entries, graph_a)

    child = PilotObservationCoordinationRef(
        PilotObservationCoordinationKind.OTHER,
        "other:isolated_coordination_child",
    )
    parent = PilotObservationCoordinationRef(
        PilotObservationCoordinationKind.OTHER,
        "other:isolated_coordination_parent",
    )
    graph_b = PilotObservationCoordinationLineageGraph(
        relations=(
            PilotObservationCoordinationRelation(
                PilotObservationCoordinationRelationKind.DERIVED_FROM,
                child,
                parent,
            ),
        )
    )

    assert pilot_observation_coordination_lineage_graph_sha256_v1(graph_a) != (
        pilot_observation_coordination_lineage_graph_sha256_v1(graph_b)
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="graph_sha256 does not match exact coordination-lineage graph",
    ):
        _validate(entries, sg, sr, mg, mr, graph_b, review)


def test_review_cannot_be_replayed_onto_changed_coordination_declaration(
    tmp_path,
) -> None:
    candidate_a, _, a, b, sg, sr, mg, mr, _, _ = _basis(tmp_path)
    entries = (a, b)
    graph = PilotObservationCoordinationLineageGraph()
    review = _complete_review(entries, graph)

    replacement = PilotObservationCoordinationRef(
        PilotObservationCoordinationKind.SCHEDULER,
        "scheduler:replacement_coordination_a",
    )
    changed_a = PilotMaterializedEvidenceCoordinationEntry(
        a.mechanism_entry,
        build_pilot_materialization_coordination_declaration_v1(
            candidate_a,
            coordinations=(replacement,),
        ),
    )
    changed_entries = (changed_a, b)

    assert pilot_observation_coordination_origin_scope_sha256_v1(entries) != (
        pilot_observation_coordination_origin_scope_sha256_v1(changed_entries)
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="scope_sha256 does not match exact evaluated observation/source/mechanism/coordination scope",
    ):
        _validate(changed_entries, sg, sr, mg, mr, graph, review)


def test_coordination_scope_digest_binds_underlying_mechanism_declaration(
    tmp_path,
) -> None:
    candidate_a, _, a, b, *_ = _basis(tmp_path)
    entries = (a, b)
    replacement_mechanism = PilotObservationMechanismRef(
        PilotObservationMechanismKind.MODEL_RUN,
        "model_run:replacement_underlying_mechanism_a",
    )
    changed_mechanism_entry = PilotMaterializedEvidenceMechanismEntry(
        a.mechanism_entry.upstream_lineage_entry,
        build_pilot_materialization_mechanism_declaration_v1(
            candidate_a,
            mechanisms=(replacement_mechanism,),
        ),
    )
    changed_a = PilotMaterializedEvidenceCoordinationEntry(
        changed_mechanism_entry,
        a.coordination_declaration,
    )
    assert pilot_observation_coordination_origin_scope_sha256_v1(entries) != (
        pilot_observation_coordination_origin_scope_sha256_v1((changed_a, b))
    )


def test_scope_digest_is_order_independent(tmp_path) -> None:
    _, _, a, b, *_ = _basis(tmp_path)
    digest_ab = pilot_observation_coordination_origin_scope_sha256_v1((a, b))
    digest_ba = pilot_observation_coordination_origin_scope_sha256_v1((b, a))
    assert digest_ab == digest_ba
    assert len(digest_ab) == 64


def test_known_common_coordination_ancestor_rejects_even_with_complete_review(
    tmp_path,
) -> None:
    _, _, a, b, sg, sr, mg, mr, coordination_a, coordination_b = _basis(tmp_path)
    root = PilotObservationCoordinationRef(
        PilotObservationCoordinationKind.CONTROLLER,
        "controller:coord_complete_common_root",
    )
    graph = PilotObservationCoordinationLineageGraph(
        relations=(
            PilotObservationCoordinationRelation(
                PilotObservationCoordinationRelationKind.DELEGATED_FROM,
                coordination_a,
                root,
            ),
            PilotObservationCoordinationRelation(
                PilotObservationCoordinationRelationKind.DERIVED_FROM,
                coordination_b,
                root,
            ),
        )
    )
    review = _complete_review((a, b), graph)

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="coordination-ancestry independence preconditions",
    ):
        _validate((a, b), sg, sr, mg, mr, graph, review)


def test_review_rejects_non_enum_completeness_status(tmp_path) -> None:
    _, _, a, b, *_ = _basis(tmp_path)
    graph = PilotObservationCoordinationLineageGraph()
    scope_sha = pilot_observation_coordination_origin_scope_sha256_v1((a, b))
    graph_sha = pilot_observation_coordination_lineage_graph_sha256_v1(graph)
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="coordination declarations status must be PilotCoordinationCompletenessStatus",
    ):
        PilotCoordinationLineageCompletenessReview(
            review_id="coordination_completeness_bad_status_01",
            scope_sha256=scope_sha,
            graph_sha256=graph_sha,
            coordination_declarations_status="COMPLETE_FOR_SCOPE",
            coordination_lineage_graph_status=(
                PilotCoordinationCompletenessStatus.COMPLETE_FOR_SCOPE
            ),
            reviewer_ref=_reviewer(),
            reviewed_at=T0,
            rationale="Invalid raw-string status.",
        )


def test_review_time_is_canonicalized_to_utc_and_rationale_is_normalized(
    tmp_path,
) -> None:
    _, _, a, b, *_ = _basis(tmp_path)
    graph = PilotObservationCoordinationLineageGraph()
    local_time = datetime(
        2026,
        1,
        12,
        18,
        30,
        tzinfo=timezone(timedelta(hours=6)),
    )
    review = build_pilot_coordination_lineage_completeness_review_v1(
        (a, b),
        coordination_lineage_graph=graph,
        review_id="coordination_completeness_normalization_01",
        coordination_declarations_status=(
            PilotCoordinationCompletenessStatus.COMPLETE_FOR_SCOPE
        ),
        coordination_lineage_graph_status=(
            PilotCoordinationCompletenessStatus.COMPLETE_FOR_SCOPE
        ),
        reviewer_ref=_reviewer(),
        reviewed_at=local_time,
        rationale="  Reviewed bounded coordination scope.  ",
    )
    assert review.reviewed_at == datetime(2026, 1, 12, 12, 30, tzinfo=timezone.utc)
    assert review.rationale == "Reviewed bounded coordination scope."
