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
    build_pilot_upstream_lineage_completeness_review_v1,
    initialize_private_workspace,
    pilot_evidence_materialization_candidate_sha256,
    pilot_observation_mechanism_dependence_key_v1,
    pilot_observation_mechanism_lineage_closure_keys_v1,
    propose_pilot_capture_evidence_materialization_v1,
    record_text_capture,
    resolve_reviewed_pilot_evidence_materialization_v1,
    validate_pilot_materialized_evidence_mechanism_ancestry_preconditions_v1,
    validate_pilot_materialized_evidence_shared_mechanism_preconditions_v1,
)


T0 = datetime(2026, 1, 10, 12, 0, tzinfo=timezone.utc)


def _reviewer():
    return PilotEvidenceMaterializationReviewerRef(
        PilotEvidenceMaterializationReviewerKind.HUMAN,
        "reviewer_mechanism_lineage_01",
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
        subject_ref=CapabilitySubjectRef("subject_mechanism_lineage_01"),
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


def _reviewed_source_origin(tmp_path):
    root_a = _workspace(
        tmp_path,
        name="mechanism_lineage_conceptual",
        session_id="session_mechanism_lineage_a",
        capture_id="conceptual_01",
        probe_id="conceptual_explanation",
        text="Synthetic conceptual observation.",
    )
    root_b = _workspace(
        tmp_path,
        name="mechanism_lineage_calculation",
        session_id="session_mechanism_lineage_b",
        capture_id="calculation_01",
        probe_id="calculation_work",
        text="Synthetic calculation observation.",
    )
    candidate_a, evidence_a = _materialize(
        root_a,
        capture_id="conceptual_01",
        materialization_id="materialization_mechanism_lineage_a",
        evidence_id="evidence_mechanism_lineage_a",
        review_id="review_mechanism_lineage_a",
    )
    candidate_b, evidence_b = _materialize(
        root_b,
        capture_id="calculation_01",
        materialization_id="materialization_mechanism_lineage_b",
        evidence_id="evidence_mechanism_lineage_b",
        review_id="review_mechanism_lineage_b",
    )

    source_a = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.ARTIFACT,
        "artifact:mechanism_lineage_source_a",
    )
    source_b = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.DATASET,
        "dataset:mechanism_lineage_source_b",
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
    upstream_entries = (upstream_a, upstream_b)
    source_graph = PilotUpstreamSourceLineageGraph()
    completeness_review = build_pilot_upstream_lineage_completeness_review_v1(
        upstream_entries,
        source_lineage_graph=source_graph,
        review_id="mechanism_lineage_source_complete_01",
        upstream_source_declarations_status=(
            PilotLineageCompletenessStatus.COMPLETE_FOR_SCOPE
        ),
        source_lineage_graph_status=(
            PilotLineageCompletenessStatus.COMPLETE_FOR_SCOPE
        ),
        reviewer_ref=_reviewer(),
        reviewed_at=T0 + timedelta(minutes=10),
        rationale="Reviewed source origin before mechanism-lineage governance.",
    )
    return (
        (candidate_a, upstream_a),
        (candidate_b, upstream_b),
        source_graph,
        completeness_review,
    )


def _mechanism_entry(candidate, upstream_entry, *mechanisms):
    return PilotMaterializedEvidenceMechanismEntry(
        upstream_entry,
        build_pilot_materialization_mechanism_declaration_v1(
            candidate,
            mechanisms=tuple(mechanisms),
        ),
    )


def test_distinct_mechanism_refs_with_common_declared_origin_are_rejected(
    tmp_path,
) -> None:
    (candidate_a, upstream_a), (candidate_b, upstream_b), source_graph, review = (
        _reviewed_source_origin(tmp_path)
    )
    root = PilotObservationMechanismRef(
        PilotObservationMechanismKind.ACQUISITION_PIPELINE,
        "acquisition_pipeline:common_origin_v1",
    )
    mechanism_a = PilotObservationMechanismRef(
        PilotObservationMechanismKind.ACQUISITION_PIPELINE,
        "acquisition_pipeline:derived_a",
    )
    mechanism_b = PilotObservationMechanismRef(
        PilotObservationMechanismKind.ACQUISITION_PIPELINE,
        "acquisition_pipeline:clone_b",
    )
    entry_a = _mechanism_entry(candidate_a, upstream_a, mechanism_a)
    entry_b = _mechanism_entry(candidate_b, upstream_b, mechanism_b)

    assert validate_pilot_materialized_evidence_shared_mechanism_preconditions_v1(
        (entry_a, entry_b),
        source_lineage_graph=source_graph,
        completeness_review=review,
    ) == (entry_a, entry_b)

    graph = PilotObservationMechanismLineageGraph(
        relations=(
            PilotObservationMechanismRelation(
                PilotObservationMechanismRelationKind.DERIVED_FROM,
                mechanism_a,
                root,
            ),
            PilotObservationMechanismRelation(
                PilotObservationMechanismRelationKind.CLONED_FROM,
                mechanism_b,
                root,
            ),
        )
    )

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="converge through one declared acquisition/governance mechanism alias/ancestry lineage",
    ):
        validate_pilot_materialized_evidence_mechanism_ancestry_preconditions_v1(
            (entry_a, entry_b),
            source_lineage_graph=source_graph,
            completeness_review=review,
            mechanism_lineage_graph=graph,
        )


def test_direct_mechanism_ancestor_and_descendant_are_rejected(tmp_path) -> None:
    (candidate_a, upstream_a), (candidate_b, upstream_b), source_graph, review = (
        _reviewed_source_origin(tmp_path)
    )
    parent = PilotObservationMechanismRef(
        PilotObservationMechanismKind.MODEL_RUN,
        "model_run:parent_state",
    )
    child = PilotObservationMechanismRef(
        PilotObservationMechanismKind.MODEL_RUN,
        "model_run:continued_child",
    )
    entry_a = _mechanism_entry(candidate_a, upstream_a, child)
    entry_b = _mechanism_entry(candidate_b, upstream_b, parent)
    graph = PilotObservationMechanismLineageGraph(
        relations=(
            PilotObservationMechanismRelation(
                PilotObservationMechanismRelationKind.STATE_CONTINUATION_OF,
                child,
                parent,
            ),
        )
    )

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="mechanism-ancestry independence preconditions",
    ):
        validate_pilot_materialized_evidence_mechanism_ancestry_preconditions_v1(
            (entry_a, entry_b),
            source_lineage_graph=source_graph,
            completeness_review=review,
            mechanism_lineage_graph=graph,
        )


def test_distinct_alias_refs_are_rejected(tmp_path) -> None:
    (candidate_a, upstream_a), (candidate_b, upstream_b), source_graph, review = (
        _reviewed_source_origin(tmp_path)
    )
    mechanism_a = PilotObservationMechanismRef(
        PilotObservationMechanismKind.REVIEW_PROCESS,
        "review_process:canonical_v1",
    )
    mechanism_b = PilotObservationMechanismRef(
        PilotObservationMechanismKind.OTHER,
        "other:review_process_alias_v1",
    )
    entry_a = _mechanism_entry(candidate_a, upstream_a, mechanism_a)
    entry_b = _mechanism_entry(candidate_b, upstream_b, mechanism_b)
    graph = PilotObservationMechanismLineageGraph(
        relations=(
            PilotObservationMechanismRelation(
                PilotObservationMechanismRelationKind.ALIAS_OF,
                mechanism_a,
                mechanism_b,
            ),
        )
    )

    assert pilot_observation_mechanism_dependence_key_v1(mechanism_a) != (
        pilot_observation_mechanism_dependence_key_v1(mechanism_b)
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="mechanism alias/ancestry lineage",
    ):
        validate_pilot_materialized_evidence_mechanism_ancestry_preconditions_v1(
            (entry_a, entry_b),
            source_lineage_graph=source_graph,
            completeness_review=review,
            mechanism_lineage_graph=graph,
        )


def test_multihop_mechanism_lineage_reaches_common_root(tmp_path) -> None:
    (candidate_a, upstream_a), (candidate_b, upstream_b), source_graph, review = (
        _reviewed_source_origin(tmp_path)
    )
    root = PilotObservationMechanismRef(
        PilotObservationMechanismKind.ENVIRONMENT,
        "environment:root_snapshot",
    )
    middle = PilotObservationMechanismRef(
        PilotObservationMechanismKind.ENVIRONMENT,
        "environment:middle_snapshot",
    )
    mechanism_a = PilotObservationMechanismRef(
        PilotObservationMechanismKind.ENVIRONMENT,
        "environment:leaf_a",
    )
    mechanism_b = PilotObservationMechanismRef(
        PilotObservationMechanismKind.ENVIRONMENT,
        "environment:leaf_b",
    )
    entry_a = _mechanism_entry(candidate_a, upstream_a, mechanism_a)
    entry_b = _mechanism_entry(candidate_b, upstream_b, mechanism_b)
    graph = PilotObservationMechanismLineageGraph(
        relations=(
            PilotObservationMechanismRelation(
                PilotObservationMechanismRelationKind.CLONED_FROM,
                mechanism_a,
                middle,
            ),
            PilotObservationMechanismRelation(
                PilotObservationMechanismRelationKind.DERIVED_FROM,
                middle,
                root,
            ),
            PilotObservationMechanismRelation(
                PilotObservationMechanismRelationKind.STATE_CONTINUATION_OF,
                mechanism_b,
                root,
            ),
        )
    )

    closure_a = pilot_observation_mechanism_lineage_closure_keys_v1(
        mechanism_a,
        graph,
    )
    assert pilot_observation_mechanism_dependence_key_v1(root) in closure_a

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="mechanism-ancestry independence preconditions",
    ):
        validate_pilot_materialized_evidence_mechanism_ancestry_preconditions_v1(
            (entry_a, entry_b),
            source_lineage_graph=source_graph,
            completeness_review=review,
            mechanism_lineage_graph=graph,
        )


def test_disconnected_declared_mechanism_lineages_clear_only_known_graph_gate(
    tmp_path,
) -> None:
    (candidate_a, upstream_a), (candidate_b, upstream_b), source_graph, review = (
        _reviewed_source_origin(tmp_path)
    )
    root_a = PilotObservationMechanismRef(
        PilotObservationMechanismKind.TOOL_EXECUTION,
        "tool_execution:root_a",
    )
    root_b = PilotObservationMechanismRef(
        PilotObservationMechanismKind.TOOL_EXECUTION,
        "tool_execution:root_b",
    )
    mechanism_a = PilotObservationMechanismRef(
        PilotObservationMechanismKind.TOOL_EXECUTION,
        "tool_execution:child_a",
    )
    mechanism_b = PilotObservationMechanismRef(
        PilotObservationMechanismKind.TOOL_EXECUTION,
        "tool_execution:child_b",
    )
    entry_a = _mechanism_entry(candidate_a, upstream_a, mechanism_a)
    entry_b = _mechanism_entry(candidate_b, upstream_b, mechanism_b)
    graph = PilotObservationMechanismLineageGraph(
        relations=(
            PilotObservationMechanismRelation(
                PilotObservationMechanismRelationKind.DERIVED_FROM,
                mechanism_a,
                root_a,
            ),
            PilotObservationMechanismRelation(
                PilotObservationMechanismRelationKind.DERIVED_FROM,
                mechanism_b,
                root_b,
            ),
        )
    )

    assert validate_pilot_materialized_evidence_mechanism_ancestry_preconditions_v1(
        (entry_b, entry_a),
        source_lineage_graph=source_graph,
        completeness_review=review,
        mechanism_lineage_graph=graph,
    ) == (entry_a, entry_b)


def test_empty_mechanism_lineage_graph_does_not_assert_independence(tmp_path) -> None:
    (candidate_a, upstream_a), (candidate_b, upstream_b), source_graph, review = (
        _reviewed_source_origin(tmp_path)
    )
    mechanism_a = PilotObservationMechanismRef(
        PilotObservationMechanismKind.OPERATOR,
        "operator:unknown_lineage_a",
    )
    mechanism_b = PilotObservationMechanismRef(
        PilotObservationMechanismKind.OPERATOR,
        "operator:unknown_lineage_b",
    )
    entry_a = _mechanism_entry(candidate_a, upstream_a, mechanism_a)
    entry_b = _mechanism_entry(candidate_b, upstream_b, mechanism_b)

    assert validate_pilot_materialized_evidence_mechanism_ancestry_preconditions_v1(
        (entry_a, entry_b),
        source_lineage_graph=source_graph,
        completeness_review=review,
        mechanism_lineage_graph=PilotObservationMechanismLineageGraph(),
    ) == (entry_a, entry_b)


def test_mechanism_lineage_closure_is_directional_and_does_not_echo_raw_refs() -> None:
    parent = PilotObservationMechanismRef(
        PilotObservationMechanismKind.MODEL_RUN,
        "model_run:private_parent",
    )
    child = PilotObservationMechanismRef(
        PilotObservationMechanismKind.MODEL_RUN,
        "model_run:private_child",
    )
    graph = PilotObservationMechanismLineageGraph(
        relations=(
            PilotObservationMechanismRelation(
                PilotObservationMechanismRelationKind.STATE_CONTINUATION_OF,
                child,
                parent,
            ),
        )
    )

    child_closure = pilot_observation_mechanism_lineage_closure_keys_v1(child, graph)
    parent_closure = pilot_observation_mechanism_lineage_closure_keys_v1(parent, graph)

    assert pilot_observation_mechanism_dependence_key_v1(child) in child_closure
    assert pilot_observation_mechanism_dependence_key_v1(parent) in child_closure
    assert pilot_observation_mechanism_dependence_key_v1(parent) in parent_closure
    assert pilot_observation_mechanism_dependence_key_v1(child) not in parent_closure
    assert all(
        child.ref not in item and parent.ref not in item
        for item in child_closure
    )


def test_reverse_alias_duplicate_is_rejected() -> None:
    mechanism_a = PilotObservationMechanismRef(
        PilotObservationMechanismKind.OTHER,
        "other:alias_a",
    )
    mechanism_b = PilotObservationMechanismRef(
        PilotObservationMechanismKind.OTHER,
        "other:alias_b",
    )

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="reverse-alias relation",
    ):
        PilotObservationMechanismLineageGraph(
            relations=(
                PilotObservationMechanismRelation(
                    PilotObservationMechanismRelationKind.ALIAS_OF,
                    mechanism_a,
                    mechanism_b,
                ),
                PilotObservationMechanismRelation(
                    PilotObservationMechanismRelationKind.ALIAS_OF,
                    mechanism_b,
                    mechanism_a,
                ),
            )
        )


def test_directed_cycle_after_alias_contraction_is_rejected() -> None:
    mechanism_a = PilotObservationMechanismRef(
        PilotObservationMechanismKind.ACQUISITION_PIPELINE,
        "acquisition_pipeline:cycle_alias_a",
    )
    mechanism_b = PilotObservationMechanismRef(
        PilotObservationMechanismKind.OTHER,
        "other:cycle_alias_b",
    )
    mechanism_c = PilotObservationMechanismRef(
        PilotObservationMechanismKind.ACQUISITION_PIPELINE,
        "acquisition_pipeline:cycle_c",
    )

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="acyclic after alias contraction",
    ):
        PilotObservationMechanismLineageGraph(
            relations=(
                PilotObservationMechanismRelation(
                    PilotObservationMechanismRelationKind.ALIAS_OF,
                    mechanism_a,
                    mechanism_b,
                ),
                PilotObservationMechanismRelation(
                    PilotObservationMechanismRelationKind.DERIVED_FROM,
                    mechanism_b,
                    mechanism_c,
                ),
                PilotObservationMechanismRelation(
                    PilotObservationMechanismRelationKind.CLONED_FROM,
                    mechanism_c,
                    mechanism_a,
                ),
            )
        )


def test_relation_cannot_point_to_same_exact_mechanism_ref() -> None:
    mechanism = PilotObservationMechanismRef(
        PilotObservationMechanismKind.ENVIRONMENT,
        "environment:self_relation",
    )

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="two distinct exact mechanism refs",
    ):
        PilotObservationMechanismRelation(
            PilotObservationMechanismRelationKind.DERIVED_FROM,
            mechanism,
            mechanism,
        )
