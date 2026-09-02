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
    PilotMaterializedEvidenceUpstreamLineageEntry,
    PilotUpstreamLineageCompletenessReview,
    PilotUpstreamSourceKind,
    PilotUpstreamSourceLineageGraph,
    PilotUpstreamSourceRef,
    PilotUpstreamSourceRelation,
    PilotUpstreamSourceRelationKind,
    build_pilot_materialization_upstream_source_declaration_v1,
    build_pilot_upstream_lineage_completeness_review_v1,
    initialize_private_workspace,
    pilot_evidence_materialization_candidate_sha256,
    pilot_upstream_source_lineage_graph_sha256_v1,
    pilot_upstream_source_origin_scope_sha256_v1,
    propose_pilot_capture_evidence_materialization_v1,
    record_text_capture,
    resolve_reviewed_pilot_evidence_materialization_v1,
    validate_pilot_materialized_evidence_reviewed_source_origin_preconditions_v1,
)


T0 = datetime(2026, 1, 8, 12, 0, tzinfo=timezone.utc)


def _reviewer():
    return PilotEvidenceMaterializationReviewerRef(
        PilotEvidenceMaterializationReviewerKind.HUMAN,
        "reviewer_lineage_completeness_01",
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
        subject_ref=CapabilitySubjectRef("subject_lineage_completeness_01"),
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


def _lineage_entries(tmp_path, source_a, source_b):
    root_a = _workspace(
        tmp_path,
        name="lineage_complete_conceptual",
        session_id="session_lineage_complete_a",
        capture_id="conceptual_01",
        probe_id="conceptual_explanation",
        text="Synthetic conceptual observation.",
    )
    root_b = _workspace(
        tmp_path,
        name="lineage_complete_calculation",
        session_id="session_lineage_complete_b",
        capture_id="calculation_01",
        probe_id="calculation_work",
        text="Synthetic calculation observation.",
    )
    candidate_a, evidence_a = _materialize(
        root_a,
        capture_id="conceptual_01",
        materialization_id="materialization_lineage_complete_a",
        evidence_id="evidence_lineage_complete_a",
        review_id="review_lineage_complete_a",
    )
    candidate_b, evidence_b = _materialize(
        root_b,
        capture_id="calculation_01",
        materialization_id="materialization_lineage_complete_b",
        evidence_id="evidence_lineage_complete_b",
        review_id="review_lineage_complete_b",
    )

    basis_a = PilotMaterializedEvidenceBasisEntry(candidate_a, evidence_a)
    basis_b = PilotMaterializedEvidenceBasisEntry(candidate_b, evidence_b)
    entry_a = PilotMaterializedEvidenceUpstreamLineageEntry(
        basis_a,
        build_pilot_materialization_upstream_source_declaration_v1(
            candidate_a,
            sources=(source_a,),
        ),
    )
    entry_b = PilotMaterializedEvidenceUpstreamLineageEntry(
        basis_b,
        build_pilot_materialization_upstream_source_declaration_v1(
            candidate_b,
            sources=(source_b,),
        ),
    )
    return entry_a, entry_b


def _disjoint_sources():
    source_a = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.ARTIFACT,
        "artifact:reviewed_root_a",
    )
    source_b = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.DATASET,
        "dataset:reviewed_root_b",
    )
    return source_a, source_b


def test_complete_for_scope_on_both_dimensions_allows_only_reviewed_origin_precondition(
    tmp_path,
) -> None:
    source_a, source_b = _disjoint_sources()
    entries = _lineage_entries(tmp_path, source_a, source_b)
    graph = PilotUpstreamSourceLineageGraph()
    review = build_pilot_upstream_lineage_completeness_review_v1(
        entries,
        source_lineage_graph=graph,
        review_id="lineage_completeness_complete_01",
        upstream_source_declarations_status=(
            PilotLineageCompletenessStatus.COMPLETE_FOR_SCOPE
        ),
        source_lineage_graph_status=(
            PilotLineageCompletenessStatus.COMPLETE_FOR_SCOPE
        ),
        reviewer_ref=_reviewer(),
        reviewed_at=T0 + timedelta(minutes=10),
        rationale=(
            "Reviewed exact bounded source declarations and graph for this synthetic scope."
        ),
    )

    assert validate_pilot_materialized_evidence_reviewed_source_origin_preconditions_v1(
        tuple(reversed(entries)),
        source_lineage_graph=graph,
        completeness_review=review,
    ) == entries


@pytest.mark.parametrize(
    "declaration_status,graph_status,match",
    [
        (
            PilotLineageCompletenessStatus.INCOMPLETE,
            PilotLineageCompletenessStatus.COMPLETE_FOR_SCOPE,
            "upstream source declarations are not reviewed COMPLETE_FOR_SCOPE",
        ),
        (
            PilotLineageCompletenessStatus.UNKNOWN,
            PilotLineageCompletenessStatus.COMPLETE_FOR_SCOPE,
            "upstream source declarations are not reviewed COMPLETE_FOR_SCOPE",
        ),
        (
            PilotLineageCompletenessStatus.COMPLETE_FOR_SCOPE,
            PilotLineageCompletenessStatus.INCOMPLETE,
            "source lineage graph is not reviewed COMPLETE_FOR_SCOPE",
        ),
        (
            PilotLineageCompletenessStatus.COMPLETE_FOR_SCOPE,
            PilotLineageCompletenessStatus.UNKNOWN,
            "source lineage graph is not reviewed COMPLETE_FOR_SCOPE",
        ),
    ],
)
def test_incomplete_or_unknown_dimension_blocks_stronger_origin_precondition(
    tmp_path,
    declaration_status,
    graph_status,
    match,
) -> None:
    source_a, source_b = _disjoint_sources()
    entries = _lineage_entries(tmp_path, source_a, source_b)
    graph = PilotUpstreamSourceLineageGraph()
    review = build_pilot_upstream_lineage_completeness_review_v1(
        entries,
        source_lineage_graph=graph,
        review_id="lineage_completeness_negative_01",
        upstream_source_declarations_status=declaration_status,
        source_lineage_graph_status=graph_status,
        reviewer_ref=_reviewer(),
        reviewed_at=T0 + timedelta(minutes=10),
        rationale="Synthetic negative completeness review.",
    )

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match=match,
    ):
        validate_pilot_materialized_evidence_reviewed_source_origin_preconditions_v1(
            entries,
            source_lineage_graph=graph,
            completeness_review=review,
        )


def test_review_cannot_be_replayed_onto_changed_graph_snapshot(tmp_path) -> None:
    source_a, source_b = _disjoint_sources()
    entries = _lineage_entries(tmp_path, source_a, source_b)
    graph_a = PilotUpstreamSourceLineageGraph()
    review = build_pilot_upstream_lineage_completeness_review_v1(
        entries,
        source_lineage_graph=graph_a,
        review_id="lineage_completeness_graph_binding_01",
        upstream_source_declarations_status=(
            PilotLineageCompletenessStatus.COMPLETE_FOR_SCOPE
        ),
        source_lineage_graph_status=(
            PilotLineageCompletenessStatus.COMPLETE_FOR_SCOPE
        ),
        reviewer_ref=_reviewer(),
        reviewed_at=T0 + timedelta(minutes=10),
        rationale="Review graph A only.",
    )

    isolated_child = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.REFERENCE,
        "reference:isolated_child",
    )
    isolated_parent = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.REFERENCE,
        "reference:isolated_parent",
    )
    graph_b = PilotUpstreamSourceLineageGraph(
        relations=(
            PilotUpstreamSourceRelation(
                PilotUpstreamSourceRelationKind.DERIVED_FROM,
                isolated_child,
                isolated_parent,
            ),
        )
    )

    assert pilot_upstream_source_lineage_graph_sha256_v1(graph_a) != (
        pilot_upstream_source_lineage_graph_sha256_v1(graph_b)
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="graph_sha256 does not match exact source-lineage graph",
    ):
        validate_pilot_materialized_evidence_reviewed_source_origin_preconditions_v1(
            entries,
            source_lineage_graph=graph_b,
            completeness_review=review,
        )


def test_review_cannot_be_replayed_onto_changed_source_declaration_scope(
    tmp_path,
) -> None:
    source_a, source_b = _disjoint_sources()
    entry_a, entry_b = _lineage_entries(tmp_path, source_a, source_b)
    entries = (entry_a, entry_b)
    graph = PilotUpstreamSourceLineageGraph()
    review = build_pilot_upstream_lineage_completeness_review_v1(
        entries,
        source_lineage_graph=graph,
        review_id="lineage_completeness_scope_binding_01",
        upstream_source_declarations_status=(
            PilotLineageCompletenessStatus.COMPLETE_FOR_SCOPE
        ),
        source_lineage_graph_status=(
            PilotLineageCompletenessStatus.COMPLETE_FOR_SCOPE
        ),
        reviewer_ref=_reviewer(),
        reviewed_at=T0 + timedelta(minutes=10),
        rationale="Review exact original source declaration scope.",
    )

    replacement_source = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.REFERENCE,
        "reference:replacement_root_b",
    )
    changed_entry_b = PilotMaterializedEvidenceUpstreamLineageEntry(
        entry_b.basis_entry,
        build_pilot_materialization_upstream_source_declaration_v1(
            entry_b.basis_entry.candidate,
            sources=(replacement_source,),
        ),
    )
    changed_entries = (entry_a, changed_entry_b)

    assert pilot_upstream_source_origin_scope_sha256_v1(entries) != (
        pilot_upstream_source_origin_scope_sha256_v1(changed_entries)
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="scope_sha256 does not match exact evaluated observation/source-declaration scope",
    ):
        validate_pilot_materialized_evidence_reviewed_source_origin_preconditions_v1(
            changed_entries,
            source_lineage_graph=graph,
            completeness_review=review,
        )


def test_scope_digest_is_order_independent_but_exact_content_sensitive(tmp_path) -> None:
    source_a, source_b = _disjoint_sources()
    entry_a, entry_b = _lineage_entries(tmp_path, source_a, source_b)

    digest_ab = pilot_upstream_source_origin_scope_sha256_v1((entry_a, entry_b))
    digest_ba = pilot_upstream_source_origin_scope_sha256_v1((entry_b, entry_a))

    assert digest_ab == digest_ba
    assert len(digest_ab) == 64


def test_structural_common_ancestor_still_rejects_even_with_complete_review(
    tmp_path,
) -> None:
    root = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.REFERENCE,
        "reference:hidden_no_longer_hidden_root",
    )
    source_a = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.ARTIFACT,
        "artifact:child_a",
    )
    source_b = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.MODEL_OUTPUT,
        "model_output:child_b",
    )
    entries = _lineage_entries(tmp_path, source_a, source_b)
    graph = PilotUpstreamSourceLineageGraph(
        relations=(
            PilotUpstreamSourceRelation(
                PilotUpstreamSourceRelationKind.COPY_OF,
                source_a,
                root,
            ),
            PilotUpstreamSourceRelation(
                PilotUpstreamSourceRelationKind.TRANSFORM_OF,
                source_b,
                root,
            ),
        )
    )
    review = build_pilot_upstream_lineage_completeness_review_v1(
        entries,
        source_lineage_graph=graph,
        review_id="lineage_completeness_common_ancestor_01",
        upstream_source_declarations_status=(
            PilotLineageCompletenessStatus.COMPLETE_FOR_SCOPE
        ),
        source_lineage_graph_status=(
            PilotLineageCompletenessStatus.COMPLETE_FOR_SCOPE
        ),
        reviewer_ref=_reviewer(),
        reviewed_at=T0 + timedelta(minutes=10),
        rationale="Even a complete review cannot override an explicit common ancestor.",
    )

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="source-ancestry independence preconditions",
    ):
        validate_pilot_materialized_evidence_reviewed_source_origin_preconditions_v1(
            entries,
            source_lineage_graph=graph,
            completeness_review=review,
        )


def test_review_normalizes_time_and_rationale_but_remains_declared_metadata(
    tmp_path,
) -> None:
    source_a, source_b = _disjoint_sources()
    entries = _lineage_entries(tmp_path, source_a, source_b)
    graph = PilotUpstreamSourceLineageGraph()
    reviewed_at = datetime(
        2026,
        1,
        8,
        18,
        30,
        tzinfo=timezone(timedelta(hours=6)),
    )
    review = build_pilot_upstream_lineage_completeness_review_v1(
        entries,
        source_lineage_graph=graph,
        review_id="lineage_completeness_metadata_01",
        upstream_source_declarations_status=(
            PilotLineageCompletenessStatus.COMPLETE_FOR_SCOPE
        ),
        source_lineage_graph_status=(
            PilotLineageCompletenessStatus.COMPLETE_FOR_SCOPE
        ),
        reviewer_ref=_reviewer(),
        reviewed_at=reviewed_at,
        rationale="  Reviewed bounded synthetic scope.  ",
    )

    assert review.reviewed_at == datetime(
        2026,
        1,
        8,
        12,
        30,
        tzinfo=timezone.utc,
    )
    assert review.rationale == "Reviewed bounded synthetic scope."
    assert review.scope_sha256 == pilot_upstream_source_origin_scope_sha256_v1(
        entries
    )
    assert review.graph_sha256 == pilot_upstream_source_lineage_graph_sha256_v1(
        graph
    )


def test_review_requires_canonical_hash_bindings() -> None:
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="scope_sha256 must be a lowercase 64-character sha256 digest",
    ):
        PilotUpstreamLineageCompletenessReview(
            review_id="lineage_completeness_bad_hash",
            scope_sha256="not-a-digest",
            graph_sha256="0" * 64,
            upstream_source_declarations_status=(
                PilotLineageCompletenessStatus.UNKNOWN
            ),
            source_lineage_graph_status=PilotLineageCompletenessStatus.UNKNOWN,
            reviewer_ref=_reviewer(),
            reviewed_at=T0,
            rationale="Negative construction test.",
        )
