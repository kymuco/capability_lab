from datetime import datetime, timedelta, timezone

import pytest

from capability_lab.epistemics import CapabilitySubjectRef, EvidenceId
from capability_lab.pilots.civilization_bootstrap_01 import (
    REVIEWED_PILOT_CAPTURE_TO_EVIDENCE_POLICY_V1,
    InvalidPilotEvidenceMaterialization,
    PilotEvidenceMaterializationId,
    PilotEvidenceMaterializationReview,
    PilotEvidenceMaterializationReviewId,
    PilotEvidenceMaterializationReviewerKind,
    PilotEvidenceMaterializationReviewerRef,
    PilotEvidenceMaterializationVerdict,
    PilotLineageCompletenessStatus,
    PilotMaterializedEvidenceBasisEntry,
    PilotMaterializedEvidenceMechanismEntry,
    PilotMaterializedEvidenceUpstreamLineageEntry,
    PilotMechanismCompletenessStatus,
    PilotObservationMechanismKind,
    PilotObservationMechanismLineageGraph,
    PilotObservationMechanismRef,
    PilotObservationMechanismRelation,
    PilotObservationMechanismRelationKind,
    PilotUpstreamSourceKind,
    PilotUpstreamSourceLineageGraph,
    PilotUpstreamSourceRef,
    build_pilot_materialization_mechanism_declaration_v1,
    build_pilot_materialization_upstream_source_declaration_v1,
    build_pilot_mechanism_lineage_completeness_review_v1,
    build_pilot_upstream_lineage_completeness_review_v1,
    initialize_private_workspace,
    pilot_evidence_materialization_candidate_sha256,
    pilot_observation_mechanism_lineage_graph_sha256_v1,
    pilot_observation_mechanism_origin_scope_sha256_v1,
    propose_pilot_capture_evidence_materialization_v1,
    record_text_capture,
    resolve_reviewed_pilot_evidence_materialization_v1,
    validate_pilot_materialized_evidence_reviewed_mechanism_origin_preconditions_v1,
)


T0 = datetime(2026, 1, 10, 12, 0, tzinfo=timezone.utc)


def _reviewer():
    return PilotEvidenceMaterializationReviewerRef(
        PilotEvidenceMaterializationReviewerKind.HUMAN,
        "reviewer_mechanism_completeness_01",
    )


def _workspace(
    tmp_path,
    *,
    name: str,
    session_id: str,
    capture_id: str,
    probe_id: str,
    text: str,
):
    root = tmp_path / name
    initialize_private_workspace(
        root,
        session_id=session_id,
        subject_ref=CapabilitySubjectRef("subject_mechanism_completeness_01"),
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


def _materialize(
    root,
    *,
    capture_id: str,
    materialization_id: str,
    evidence_id: str,
    review_id: str,
):
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
        name="mechanism_complete_conceptual",
        session_id="session_mechanism_complete_a",
        capture_id="conceptual_01",
        probe_id="conceptual_explanation",
        text="Synthetic conceptual observation.",
    )
    root_b = _workspace(
        tmp_path,
        name="mechanism_complete_calculation",
        session_id="session_mechanism_complete_b",
        capture_id="calculation_01",
        probe_id="calculation_work",
        text="Synthetic calculation observation.",
    )
    candidate_a, evidence_a = _materialize(
        root_a,
        capture_id="conceptual_01",
        materialization_id="materialization_mechanism_complete_a",
        evidence_id="evidence_mechanism_complete_a",
        review_id="review_mechanism_complete_a",
    )
    candidate_b, evidence_b = _materialize(
        root_b,
        capture_id="calculation_01",
        materialization_id="materialization_mechanism_complete_b",
        evidence_id="evidence_mechanism_complete_b",
        review_id="review_mechanism_complete_b",
    )

    source_a = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.ARTIFACT,
        "artifact:mechanism_complete_root_a",
    )
    source_b = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.DATASET,
        "dataset:mechanism_complete_root_b",
    )
    upstream_a = PilotMaterializedEvidenceUpstreamLineageEntry(
        PilotMaterializedEvidenceBasisEntry(candidate_a, evidence_a),
        build_pilot_materialization_upstream_source_declaration_v1(
            candidate_a,
            sources=(source_a,),
        ),
    )
    upstream_b = PilotMaterializedEvidenceUpstreamLineageEntry(
        PilotMaterializedEvidenceBasisEntry(candidate_b, evidence_b),
        build_pilot_materialization_upstream_source_declaration_v1(
            candidate_b,
            sources=(source_b,),
        ),
    )

    source_graph = PilotUpstreamSourceLineageGraph()
    source_review = build_pilot_upstream_lineage_completeness_review_v1(
        (upstream_a, upstream_b),
        source_lineage_graph=source_graph,
        review_id="source_complete_for_mechanism_complete_01",
        upstream_source_declarations_status=(
            PilotLineageCompletenessStatus.COMPLETE_FOR_SCOPE
        ),
        source_lineage_graph_status=(
            PilotLineageCompletenessStatus.COMPLETE_FOR_SCOPE
        ),
        reviewer_ref=_reviewer(),
        reviewed_at=T0 + timedelta(minutes=10),
        rationale="Source-origin basis reviewed complete for bounded synthetic scope.",
    )

    mechanism_a = PilotObservationMechanismRef(
        PilotObservationMechanismKind.TOOL_EXECUTION,
        "tool_execution:mechanism_complete_run_a",
    )
    mechanism_b = PilotObservationMechanismRef(
        PilotObservationMechanismKind.TOOL_EXECUTION,
        "tool_execution:mechanism_complete_run_b",
    )
    entry_a = PilotMaterializedEvidenceMechanismEntry(
        upstream_a,
        build_pilot_materialization_mechanism_declaration_v1(
            candidate_a,
            mechanisms=(mechanism_a,),
        ),
    )
    entry_b = PilotMaterializedEvidenceMechanismEntry(
        upstream_b,
        build_pilot_materialization_mechanism_declaration_v1(
            candidate_b,
            mechanisms=(mechanism_b,),
        ),
    )
    return (
        candidate_a,
        candidate_b,
        entry_a,
        entry_b,
        source_graph,
        source_review,
        mechanism_a,
        mechanism_b,
    )


def _complete_review(entries, graph):
    return build_pilot_mechanism_lineage_completeness_review_v1(
        entries,
        mechanism_lineage_graph=graph,
        review_id="mechanism_completeness_complete_01",
        mechanism_declarations_status=(
            PilotMechanismCompletenessStatus.COMPLETE_FOR_SCOPE
        ),
        mechanism_lineage_graph_status=(
            PilotMechanismCompletenessStatus.COMPLETE_FOR_SCOPE
        ),
        reviewer_ref=_reviewer(),
        reviewed_at=T0 + timedelta(minutes=20),
        rationale="Reviewed exact mechanism declarations and lineage graph for bounded scope.",
    )


def test_complete_for_scope_on_both_dimensions_allows_only_reviewed_mechanism_origin_precondition(
    tmp_path,
) -> None:
    _, _, entry_a, entry_b, source_graph, source_review, _, _ = _basis(tmp_path)
    entries = (entry_a, entry_b)
    mechanism_graph = PilotObservationMechanismLineageGraph()
    review = _complete_review(entries, mechanism_graph)

    assert validate_pilot_materialized_evidence_reviewed_mechanism_origin_preconditions_v1(
        tuple(reversed(entries)),
        source_lineage_graph=source_graph,
        source_completeness_review=source_review,
        mechanism_lineage_graph=mechanism_graph,
        mechanism_completeness_review=review,
    ) == entries


@pytest.mark.parametrize(
    "declaration_status,graph_status,match",
    [
        (
            PilotMechanismCompletenessStatus.INCOMPLETE,
            PilotMechanismCompletenessStatus.COMPLETE_FOR_SCOPE,
            "observation mechanism declarations are not reviewed COMPLETE_FOR_SCOPE",
        ),
        (
            PilotMechanismCompletenessStatus.UNKNOWN,
            PilotMechanismCompletenessStatus.COMPLETE_FOR_SCOPE,
            "observation mechanism declarations are not reviewed COMPLETE_FOR_SCOPE",
        ),
        (
            PilotMechanismCompletenessStatus.COMPLETE_FOR_SCOPE,
            PilotMechanismCompletenessStatus.INCOMPLETE,
            "mechanism lineage graph is not reviewed COMPLETE_FOR_SCOPE",
        ),
        (
            PilotMechanismCompletenessStatus.COMPLETE_FOR_SCOPE,
            PilotMechanismCompletenessStatus.UNKNOWN,
            "mechanism lineage graph is not reviewed COMPLETE_FOR_SCOPE",
        ),
    ],
)
def test_incomplete_or_unknown_dimension_fails_closed(
    tmp_path,
    declaration_status,
    graph_status,
    match,
) -> None:
    _, _, entry_a, entry_b, source_graph, source_review, _, _ = _basis(tmp_path)
    entries = (entry_a, entry_b)
    mechanism_graph = PilotObservationMechanismLineageGraph()
    review = build_pilot_mechanism_lineage_completeness_review_v1(
        entries,
        mechanism_lineage_graph=mechanism_graph,
        review_id="mechanism_completeness_negative_01",
        mechanism_declarations_status=declaration_status,
        mechanism_lineage_graph_status=graph_status,
        reviewer_ref=_reviewer(),
        reviewed_at=T0 + timedelta(minutes=20),
        rationale="Synthetic negative mechanism completeness review.",
    )

    with pytest.raises(InvalidPilotEvidenceMaterialization, match=match):
        validate_pilot_materialized_evidence_reviewed_mechanism_origin_preconditions_v1(
            entries,
            source_lineage_graph=source_graph,
            source_completeness_review=source_review,
            mechanism_lineage_graph=mechanism_graph,
            mechanism_completeness_review=review,
        )


def test_review_cannot_be_replayed_onto_changed_mechanism_graph(tmp_path) -> None:
    _, _, entry_a, entry_b, source_graph, source_review, _, _ = _basis(tmp_path)
    entries = (entry_a, entry_b)
    graph_a = PilotObservationMechanismLineageGraph()
    review = _complete_review(entries, graph_a)

    isolated_child = PilotObservationMechanismRef(
        PilotObservationMechanismKind.OTHER,
        "other:isolated_mechanism_child",
    )
    isolated_parent = PilotObservationMechanismRef(
        PilotObservationMechanismKind.OTHER,
        "other:isolated_mechanism_parent",
    )
    graph_b = PilotObservationMechanismLineageGraph(
        relations=(
            PilotObservationMechanismRelation(
                PilotObservationMechanismRelationKind.DERIVED_FROM,
                isolated_child,
                isolated_parent,
            ),
        )
    )

    assert pilot_observation_mechanism_lineage_graph_sha256_v1(graph_a) != (
        pilot_observation_mechanism_lineage_graph_sha256_v1(graph_b)
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="graph_sha256 does not match exact mechanism-lineage graph",
    ):
        validate_pilot_materialized_evidence_reviewed_mechanism_origin_preconditions_v1(
            entries,
            source_lineage_graph=source_graph,
            source_completeness_review=source_review,
            mechanism_lineage_graph=graph_b,
            mechanism_completeness_review=review,
        )


def test_review_cannot_be_replayed_onto_changed_mechanism_declaration(tmp_path) -> None:
    candidate_a, _, entry_a, entry_b, source_graph, source_review, _, _ = _basis(
        tmp_path
    )
    entries = (entry_a, entry_b)
    mechanism_graph = PilotObservationMechanismLineageGraph()
    review = _complete_review(entries, mechanism_graph)

    replacement = PilotObservationMechanismRef(
        PilotObservationMechanismKind.MODEL_RUN,
        "model_run:replacement_mechanism_a",
    )
    changed_a = PilotMaterializedEvidenceMechanismEntry(
        entry_a.upstream_lineage_entry,
        build_pilot_materialization_mechanism_declaration_v1(
            candidate_a,
            mechanisms=(replacement,),
        ),
    )
    changed_entries = (changed_a, entry_b)

    assert pilot_observation_mechanism_origin_scope_sha256_v1(entries) != (
        pilot_observation_mechanism_origin_scope_sha256_v1(changed_entries)
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="scope_sha256 does not match exact evaluated observation/source/mechanism scope",
    ):
        validate_pilot_materialized_evidence_reviewed_mechanism_origin_preconditions_v1(
            changed_entries,
            source_lineage_graph=source_graph,
            source_completeness_review=source_review,
            mechanism_lineage_graph=mechanism_graph,
            mechanism_completeness_review=review,
        )


def test_mechanism_scope_digest_binds_underlying_source_declaration(tmp_path) -> None:
    _, candidate_b, entry_a, entry_b, _source_graph, _source_review, _, _ = _basis(
        tmp_path
    )
    entries = (entry_a, entry_b)
    replacement_source = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.REFERENCE,
        "reference:replacement_underlying_source_b",
    )
    changed_upstream_b = PilotMaterializedEvidenceUpstreamLineageEntry(
        entry_b.upstream_lineage_entry.basis_entry,
        build_pilot_materialization_upstream_source_declaration_v1(
            candidate_b,
            sources=(replacement_source,),
        ),
    )
    changed_b = PilotMaterializedEvidenceMechanismEntry(
        changed_upstream_b,
        entry_b.mechanism_declaration,
    )
    changed_entries = (entry_a, changed_b)

    assert pilot_observation_mechanism_origin_scope_sha256_v1(entries) != (
        pilot_observation_mechanism_origin_scope_sha256_v1(changed_entries)
    )


def test_scope_digest_is_order_independent(tmp_path) -> None:
    _, _, entry_a, entry_b, _, _, _, _ = _basis(tmp_path)
    digest_ab = pilot_observation_mechanism_origin_scope_sha256_v1(
        (entry_a, entry_b)
    )
    digest_ba = pilot_observation_mechanism_origin_scope_sha256_v1(
        (entry_b, entry_a)
    )
    assert digest_ab == digest_ba
    assert len(digest_ab) == 64


def test_known_common_mechanism_ancestor_still_rejects_even_with_complete_review(
    tmp_path,
) -> None:
    _, _, entry_a, entry_b, source_graph, source_review, mechanism_a, mechanism_b = (
        _basis(tmp_path)
    )
    root = PilotObservationMechanismRef(
        PilotObservationMechanismKind.ACQUISITION_PIPELINE,
        "acquisition_pipeline:known_common_mechanism_root",
    )
    mechanism_graph = PilotObservationMechanismLineageGraph(
        relations=(
            PilotObservationMechanismRelation(
                PilotObservationMechanismRelationKind.DERIVED_FROM,
                mechanism_a,
                root,
            ),
            PilotObservationMechanismRelation(
                PilotObservationMechanismRelationKind.STATE_CONTINUATION_OF,
                mechanism_b,
                root,
            ),
        )
    )
    entries = (entry_a, entry_b)
    review = _complete_review(entries, mechanism_graph)

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="mechanism-ancestry independence preconditions",
    ):
        validate_pilot_materialized_evidence_reviewed_mechanism_origin_preconditions_v1(
            entries,
            source_lineage_graph=source_graph,
            source_completeness_review=source_review,
            mechanism_lineage_graph=mechanism_graph,
            mechanism_completeness_review=review,
        )


def test_review_normalizes_time_and_rationale(tmp_path) -> None:
    _, _, entry_a, entry_b, _, _, _, _ = _basis(tmp_path)
    entries = (entry_a, entry_b)
    graph = PilotObservationMechanismLineageGraph()
    reviewed_at = datetime(
        2026,
        1,
        10,
        18,
        30,
        tzinfo=timezone(timedelta(hours=6)),
    )
    review = build_pilot_mechanism_lineage_completeness_review_v1(
        entries,
        mechanism_lineage_graph=graph,
        review_id="mechanism_completeness_metadata_01",
        mechanism_declarations_status=(
            PilotMechanismCompletenessStatus.COMPLETE_FOR_SCOPE
        ),
        mechanism_lineage_graph_status=(
            PilotMechanismCompletenessStatus.COMPLETE_FOR_SCOPE
        ),
        reviewer_ref=_reviewer(),
        reviewed_at=reviewed_at,
        rationale="  Reviewed bounded mechanism scope.  ",
    )
    assert review.reviewed_at == datetime(
        2026, 1, 10, 12, 30, tzinfo=timezone.utc
    )
    assert review.rationale == "Reviewed bounded mechanism scope."
    assert review.scope_sha256 == (
        pilot_observation_mechanism_origin_scope_sha256_v1(entries)
    )
    assert review.graph_sha256 == (
        pilot_observation_mechanism_lineage_graph_sha256_v1(graph)
    )


def test_review_requires_canonical_id_and_nonempty_rationale(tmp_path) -> None:
    _, _, entry_a, entry_b, _, _, _, _ = _basis(tmp_path)
    entries = (entry_a, entry_b)
    graph = PilotObservationMechanismLineageGraph()

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="canonical opaque ASCII identifier",
    ):
        build_pilot_mechanism_lineage_completeness_review_v1(
            entries,
            mechanism_lineage_graph=graph,
            review_id="bad review id",
            mechanism_declarations_status=(
                PilotMechanismCompletenessStatus.COMPLETE_FOR_SCOPE
            ),
            mechanism_lineage_graph_status=(
                PilotMechanismCompletenessStatus.COMPLETE_FOR_SCOPE
            ),
            reviewer_ref=_reviewer(),
            reviewed_at=T0,
            rationale="Valid rationale.",
        )

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="rationale must be non-empty",
    ):
        build_pilot_mechanism_lineage_completeness_review_v1(
            entries,
            mechanism_lineage_graph=graph,
            review_id="mechanism_completeness_bad_rationale_01",
            mechanism_declarations_status=(
                PilotMechanismCompletenessStatus.COMPLETE_FOR_SCOPE
            ),
            mechanism_lineage_graph_status=(
                PilotMechanismCompletenessStatus.COMPLETE_FOR_SCOPE
            ),
            reviewer_ref=_reviewer(),
            reviewed_at=T0,
            rationale="   ",
        )
