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
    build_pilot_materialization_coordination_declaration_v1,
    build_pilot_materialization_mechanism_declaration_v1,
    build_pilot_materialization_upstream_source_declaration_v1,
    build_pilot_mechanism_lineage_completeness_review_v1,
    build_pilot_upstream_lineage_completeness_review_v1,
    initialize_private_workspace,
    pilot_evidence_materialization_candidate_sha256,
    pilot_observation_coordination_lineage_closure_keys_v1,
    propose_pilot_capture_evidence_materialization_v1,
    record_text_capture,
    resolve_reviewed_pilot_evidence_materialization_v1,
    validate_pilot_materialized_evidence_coordination_ancestry_preconditions_v1,
)


T0 = datetime(2026, 1, 12, 12, 0, tzinfo=timezone.utc)


def _reviewer():
    return PilotEvidenceMaterializationReviewerRef(
        PilotEvidenceMaterializationReviewerKind.HUMAN,
        "reviewer_coordination_lineage_01",
    )


def _workspace(tmp_path, *, name, session_id, capture_id, probe_id, text):
    root = tmp_path / name
    initialize_private_workspace(
        root,
        session_id=session_id,
        subject_ref=CapabilitySubjectRef("subject_coordination_lineage_01"),
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


def _reviewed_coordination_basis(tmp_path, *, shared_coordination=False):
    root_a = _workspace(
        tmp_path,
        name="coordination_lineage_conceptual",
        session_id="session_coordination_lineage_a",
        capture_id="conceptual_01",
        probe_id="conceptual_explanation",
        text="Synthetic conceptual observation.",
    )
    root_b = _workspace(
        tmp_path,
        name="coordination_lineage_calculation",
        session_id="session_coordination_lineage_b",
        capture_id="calculation_01",
        probe_id="calculation_work",
        text="Synthetic calculation observation.",
    )
    candidate_a, evidence_a = _materialize(
        root_a,
        capture_id="conceptual_01",
        materialization_id="materialization_coordination_lineage_a",
        evidence_id="evidence_coordination_lineage_a",
        review_id="review_coordination_lineage_a",
    )
    candidate_b, evidence_b = _materialize(
        root_b,
        capture_id="calculation_01",
        materialization_id="materialization_coordination_lineage_b",
        evidence_id="evidence_coordination_lineage_b",
        review_id="review_coordination_lineage_b",
    )

    upstream_a = PilotMaterializedEvidenceUpstreamLineageEntry(
        PilotMaterializedEvidenceBasisEntry(candidate_a, evidence_a),
        build_pilot_materialization_upstream_source_declaration_v1(
            candidate_a,
            sources=(
                PilotUpstreamSourceRef(
                    PilotUpstreamSourceKind.ARTIFACT,
                    "artifact:coordination_lineage_source_a",
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
                    "dataset:coordination_lineage_source_b",
                ),
            ),
        ),
    )
    source_graph = PilotUpstreamSourceLineageGraph()
    source_review = build_pilot_upstream_lineage_completeness_review_v1(
        (upstream_a, upstream_b),
        source_lineage_graph=source_graph,
        review_id="source_complete_for_coordination_lineage_01",
        upstream_source_declarations_status=(
            PilotLineageCompletenessStatus.COMPLETE_FOR_SCOPE
        ),
        source_lineage_graph_status=(
            PilotLineageCompletenessStatus.COMPLETE_FOR_SCOPE
        ),
        reviewer_ref=_reviewer(),
        reviewed_at=T0 + timedelta(minutes=10),
        rationale="Reviewed exact source basis for coordination lineage tests.",
    )

    mechanism_a = PilotObservationMechanismRef(
        PilotObservationMechanismKind.TOOL_EXECUTION,
        "tool_execution:coordination_lineage_run_a",
    )
    mechanism_b = PilotObservationMechanismRef(
        PilotObservationMechanismKind.TOOL_EXECUTION,
        "tool_execution:coordination_lineage_run_b",
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
        review_id="mechanism_complete_for_coordination_lineage_01",
        mechanism_declarations_status=(
            PilotMechanismCompletenessStatus.COMPLETE_FOR_SCOPE
        ),
        mechanism_lineage_graph_status=(
            PilotMechanismCompletenessStatus.COMPLETE_FOR_SCOPE
        ),
        reviewer_ref=_reviewer(),
        reviewed_at=T0 + timedelta(minutes=20),
        rationale="Reviewed exact mechanism basis for coordination lineage tests.",
    )

    coordination_a = PilotObservationCoordinationRef(
        PilotObservationCoordinationKind.CONTROLLER,
        (
            "controller:coordination_lineage_shared"
            if shared_coordination
            else "controller:coordination_lineage_a"
        ),
    )
    coordination_b = PilotObservationCoordinationRef(
        PilotObservationCoordinationKind.CONTROLLER,
        (
            "controller:coordination_lineage_shared"
            if shared_coordination
            else "controller:coordination_lineage_b"
        ),
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
        entry_a,
        entry_b,
        source_graph,
        source_review,
        mechanism_graph,
        mechanism_review,
        coordination_a,
        coordination_b,
    )


def _validate(entries, source_graph, source_review, mechanism_graph, mechanism_review, graph):
    return validate_pilot_materialized_evidence_coordination_ancestry_preconditions_v1(
        entries,
        source_lineage_graph=source_graph,
        source_completeness_review=source_review,
        mechanism_lineage_graph=mechanism_graph,
        mechanism_completeness_review=mechanism_review,
        coordination_lineage_graph=graph,
    )


def test_aliases_with_distinct_refs_reject(tmp_path) -> None:
    a, b, sg, sr, mg, mr, coordination_a, coordination_b = (
        _reviewed_coordination_basis(tmp_path)
    )
    graph = PilotObservationCoordinationLineageGraph(
        relations=(
            PilotObservationCoordinationRelation(
                PilotObservationCoordinationRelationKind.ALIAS_OF,
                coordination_a,
                coordination_b,
            ),
        )
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="coordination/control alias/ancestry lineage",
    ):
        _validate((a, b), sg, sr, mg, mr, graph)


def test_direct_delegated_authority_ancestor_rejects(tmp_path) -> None:
    a, b, sg, sr, mg, mr, coordination_a, coordination_b = (
        _reviewed_coordination_basis(tmp_path)
    )
    graph = PilotObservationCoordinationLineageGraph(
        relations=(
            PilotObservationCoordinationRelation(
                PilotObservationCoordinationRelationKind.DELEGATED_FROM,
                coordination_a,
                coordination_b,
            ),
        )
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="coordination-ancestry independence preconditions",
    ):
        _validate((a, b), sg, sr, mg, mr, graph)


def test_distinct_policy_and_selector_with_common_control_origin_reject(tmp_path) -> None:
    a, b, sg, sr, mg, mr, _coordination_a, _coordination_b = (
        _reviewed_coordination_basis(tmp_path)
    )
    policy = PilotObservationCoordinationRef(
        PilotObservationCoordinationKind.POLICY_EXECUTION,
        "policy_execution:lineage_policy_a",
    )
    selector = PilotObservationCoordinationRef(
        PilotObservationCoordinationKind.ADAPTIVE_SELECTOR,
        "adaptive_selector:lineage_selector_b",
    )
    root = PilotObservationCoordinationRef(
        PilotObservationCoordinationKind.CONTROLLER,
        "controller:common_control_root",
    )

    candidate_a = a.mechanism_entry.upstream_lineage_entry.basis_entry.candidate
    candidate_b = b.mechanism_entry.upstream_lineage_entry.basis_entry.candidate
    a = PilotMaterializedEvidenceCoordinationEntry(
        a.mechanism_entry,
        build_pilot_materialization_coordination_declaration_v1(
            candidate_a,
            coordinations=(policy,),
        ),
    )
    b = PilotMaterializedEvidenceCoordinationEntry(
        b.mechanism_entry,
        build_pilot_materialization_coordination_declaration_v1(
            candidate_b,
            coordinations=(selector,),
        ),
    )
    graph = PilotObservationCoordinationLineageGraph(
        relations=(
            PilotObservationCoordinationRelation(
                PilotObservationCoordinationRelationKind.DERIVED_FROM,
                policy,
                root,
            ),
            PilotObservationCoordinationRelation(
                PilotObservationCoordinationRelationKind.STATE_CONTINUATION_OF,
                selector,
                root,
            ),
        )
    )

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="coordination/control alias/ancestry lineage",
    ):
        _validate((a, b), sg, sr, mg, mr, graph)


def test_transitive_coordination_lineage_rejects(tmp_path) -> None:
    a, b, sg, sr, mg, mr, coordination_a, coordination_b = (
        _reviewed_coordination_basis(tmp_path)
    )
    middle = PilotObservationCoordinationRef(
        PilotObservationCoordinationKind.COORDINATION_PROCESS,
        "coordination_process:lineage_middle",
    )
    root = PilotObservationCoordinationRef(
        PilotObservationCoordinationKind.CONTROLLER,
        "controller:lineage_root",
    )
    graph = PilotObservationCoordinationLineageGraph(
        relations=(
            PilotObservationCoordinationRelation(
                PilotObservationCoordinationRelationKind.DELEGATED_FROM,
                coordination_a,
                middle,
            ),
            PilotObservationCoordinationRelation(
                PilotObservationCoordinationRelationKind.DERIVED_FROM,
                middle,
                root,
            ),
            PilotObservationCoordinationRelation(
                PilotObservationCoordinationRelationKind.STATE_CONTINUATION_OF,
                coordination_b,
                root,
            ),
        )
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="coordination-ancestry independence preconditions",
    ):
        _validate((a, b), sg, sr, mg, mr, graph)


def test_disjoint_declared_control_roots_clear_only_lineage_gate(tmp_path) -> None:
    a, b, sg, sr, mg, mr, coordination_a, coordination_b = (
        _reviewed_coordination_basis(tmp_path)
    )
    root_a = PilotObservationCoordinationRef(
        PilotObservationCoordinationKind.CONTROLLER,
        "controller:disjoint_root_a",
    )
    root_b = PilotObservationCoordinationRef(
        PilotObservationCoordinationKind.CONTROLLER,
        "controller:disjoint_root_b",
    )
    graph = PilotObservationCoordinationLineageGraph(
        relations=(
            PilotObservationCoordinationRelation(
                PilotObservationCoordinationRelationKind.DERIVED_FROM,
                coordination_a,
                root_a,
            ),
            PilotObservationCoordinationRelation(
                PilotObservationCoordinationRelationKind.DERIVED_FROM,
                coordination_b,
                root_b,
            ),
        )
    )
    assert _validate((b, a), sg, sr, mg, mr, graph) == (a, b)


def test_empty_coordination_graph_does_not_assert_independence(tmp_path) -> None:
    a, b, sg, sr, mg, mr, *_ = _reviewed_coordination_basis(tmp_path)
    graph = PilotObservationCoordinationLineageGraph()
    assert graph.relations == ()
    assert _validate((a, b), sg, sr, mg, mr, graph) == (a, b)


def test_coordination_lineage_traversal_is_upstream_only() -> None:
    child = PilotObservationCoordinationRef(
        PilotObservationCoordinationKind.POLICY_EXECUTION,
        "policy_execution:directional_child",
    )
    parent = PilotObservationCoordinationRef(
        PilotObservationCoordinationKind.CONTROLLER,
        "controller:directional_parent",
    )
    graph = PilotObservationCoordinationLineageGraph(
        relations=(
            PilotObservationCoordinationRelation(
                PilotObservationCoordinationRelationKind.DELEGATED_FROM,
                child,
                parent,
            ),
        )
    )
    child_closure = set(
        pilot_observation_coordination_lineage_closure_keys_v1(child, graph)
    )
    parent_closure = set(
        pilot_observation_coordination_lineage_closure_keys_v1(parent, graph)
    )
    assert parent_closure < child_closure


def test_coordination_lineage_closure_does_not_echo_raw_refs() -> None:
    raw_ref = "controller:opaque_control_origin_123"
    coordination = PilotObservationCoordinationRef(
        PilotObservationCoordinationKind.CONTROLLER,
        raw_ref,
    )
    keys = pilot_observation_coordination_lineage_closure_keys_v1(
        coordination,
        PilotObservationCoordinationLineageGraph(),
    )
    assert len(keys) == 1
    assert raw_ref not in keys[0]
    assert keys[0].startswith("pilot_observation_coordination:")


def test_reverse_alias_duplicate_rejects() -> None:
    a = PilotObservationCoordinationRef(
        PilotObservationCoordinationKind.CONTROLLER,
        "controller:alias_a",
    )
    b = PilotObservationCoordinationRef(
        PilotObservationCoordinationKind.CONTROLLER,
        "controller:alias_b",
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="reverse-alias relation",
    ):
        PilotObservationCoordinationLineageGraph(
            relations=(
                PilotObservationCoordinationRelation(
                    PilotObservationCoordinationRelationKind.ALIAS_OF,
                    a,
                    b,
                ),
                PilotObservationCoordinationRelation(
                    PilotObservationCoordinationRelationKind.ALIAS_OF,
                    b,
                    a,
                ),
            )
        )


def test_conflicting_directed_relation_kinds_reject() -> None:
    child = PilotObservationCoordinationRef(
        PilotObservationCoordinationKind.ADAPTIVE_SELECTOR,
        "adaptive_selector:conflict_child",
    )
    parent = PilotObservationCoordinationRef(
        PilotObservationCoordinationKind.CONTROLLER,
        "controller:conflict_parent",
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="conflicting relation kinds",
    ):
        PilotObservationCoordinationLineageGraph(
            relations=(
                PilotObservationCoordinationRelation(
                    PilotObservationCoordinationRelationKind.DELEGATED_FROM,
                    child,
                    parent,
                ),
                PilotObservationCoordinationRelation(
                    PilotObservationCoordinationRelationKind.DERIVED_FROM,
                    child,
                    parent,
                ),
            )
        )


def test_alias_contracted_cycle_rejects() -> None:
    a = PilotObservationCoordinationRef(
        PilotObservationCoordinationKind.CONTROLLER,
        "controller:cycle_a",
    )
    alias_a = PilotObservationCoordinationRef(
        PilotObservationCoordinationKind.CONTROLLER,
        "controller:cycle_alias_a",
    )
    b = PilotObservationCoordinationRef(
        PilotObservationCoordinationKind.COORDINATION_PROCESS,
        "coordination_process:cycle_b",
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="acyclic after alias contraction",
    ):
        PilotObservationCoordinationLineageGraph(
            relations=(
                PilotObservationCoordinationRelation(
                    PilotObservationCoordinationRelationKind.ALIAS_OF,
                    a,
                    alias_a,
                ),
                PilotObservationCoordinationRelation(
                    PilotObservationCoordinationRelationKind.DERIVED_FROM,
                    alias_a,
                    b,
                ),
                PilotObservationCoordinationRelation(
                    PilotObservationCoordinationRelationKind.DELEGATED_FROM,
                    b,
                    a,
                ),
            )
        )


def test_directed_relation_inside_alias_class_rejects() -> None:
    a = PilotObservationCoordinationRef(
        PilotObservationCoordinationKind.CONTROLLER,
        "controller:inside_alias_a",
    )
    b = PilotObservationCoordinationRef(
        PilotObservationCoordinationKind.CONTROLLER,
        "controller:inside_alias_b",
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="collapse within one alias class",
    ):
        PilotObservationCoordinationLineageGraph(
            relations=(
                PilotObservationCoordinationRelation(
                    PilotObservationCoordinationRelationKind.ALIAS_OF,
                    a,
                    b,
                ),
                PilotObservationCoordinationRelation(
                    PilotObservationCoordinationRelationKind.STATE_CONTINUATION_OF,
                    a,
                    b,
                ),
            )
        )


def test_exact_shared_coordination_still_rejects_before_lineage_graph_can_help(
    tmp_path,
) -> None:
    a, b, sg, sr, mg, mr, *_ = _reviewed_coordination_basis(
        tmp_path,
        shared_coordination=True,
    )
    graph = PilotObservationCoordinationLineageGraph()
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="share one exact declared cross-observation coordination/control authority",
    ):
        _validate((a, b), sg, sr, mg, mr, graph)
