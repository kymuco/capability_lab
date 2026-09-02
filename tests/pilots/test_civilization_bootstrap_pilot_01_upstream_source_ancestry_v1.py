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
    PilotMaterializedEvidenceBasisEntry,
    PilotMaterializedEvidenceUpstreamLineageEntry,
    PilotUpstreamSourceKind,
    PilotUpstreamSourceLineageGraph,
    PilotUpstreamSourceRef,
    PilotUpstreamSourceRelation,
    PilotUpstreamSourceRelationKind,
    build_pilot_materialization_upstream_source_declaration_v1,
    initialize_private_workspace,
    pilot_evidence_materialization_candidate_sha256,
    pilot_upstream_source_dependence_key_v1,
    pilot_upstream_source_lineage_closure_keys_v1,
    propose_pilot_capture_evidence_materialization_v1,
    record_text_capture,
    resolve_reviewed_pilot_evidence_materialization_v1,
    validate_pilot_materialized_evidence_source_ancestry_preconditions_v1,
    validate_pilot_materialized_evidence_upstream_lineage_preconditions_v1,
)


T0 = datetime(2026, 1, 7, 12, 0, tzinfo=timezone.utc)


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
        subject_ref=CapabilitySubjectRef("subject_source_ancestry_01"),
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
        reviewer_ref=PilotEvidenceMaterializationReviewerRef(
            PilotEvidenceMaterializationReviewerKind.HUMAN,
            "reviewer_source_ancestry_01",
        ),
        verdict=PilotEvidenceMaterializationVerdict.MATERIALIZE,
        reviewed_at=T0 + timedelta(minutes=3),
        rationale="Materialize the observation without capability inference.",
    )
    evidence = resolve_reviewed_pilot_evidence_materialization_v1(
        root,
        candidate=candidate,
        review=review,
        resolved_at=T0 + timedelta(minutes=4),
    )
    assert evidence is not None
    return candidate, evidence


def _distinct_lineage_entries(tmp_path, source_a, source_b):
    root_a = _workspace(
        tmp_path,
        name="ancestry_conceptual",
        session_id="session_source_ancestry_a",
        capture_id="conceptual_01",
        probe_id="conceptual_explanation",
        text="Synthetic conceptual observation.",
    )
    root_b = _workspace(
        tmp_path,
        name="ancestry_calculation",
        session_id="session_source_ancestry_b",
        capture_id="calculation_01",
        probe_id="calculation_work",
        text="Synthetic calculation observation.",
    )
    candidate_a, evidence_a = _materialize(
        root_a,
        capture_id="conceptual_01",
        materialization_id="materialization_source_ancestry_a",
        evidence_id="evidence_source_ancestry_a",
        review_id="review_source_ancestry_a",
    )
    candidate_b, evidence_b = _materialize(
        root_b,
        capture_id="calculation_01",
        materialization_id="materialization_source_ancestry_b",
        evidence_id="evidence_source_ancestry_b",
        review_id="review_source_ancestry_b",
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


def test_distinct_declared_sources_with_common_ancestor_are_rejected(tmp_path) -> None:
    root_source = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.REFERENCE,
        "reference:common_root_v1",
    )
    source_a = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.MODEL_OUTPUT,
        "model_output:transformed_a",
    )
    source_b = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.TOOL_OUTPUT,
        "tool_output:copied_b",
    )
    entry_a, entry_b = _distinct_lineage_entries(tmp_path, source_a, source_b)

    assert validate_pilot_materialized_evidence_upstream_lineage_preconditions_v1(
        (entry_a, entry_b)
    ) == (entry_a, entry_b)

    graph = PilotUpstreamSourceLineageGraph(
        relations=(
            PilotUpstreamSourceRelation(
                PilotUpstreamSourceRelationKind.TRANSFORM_OF,
                source_a,
                root_source,
            ),
            PilotUpstreamSourceRelation(
                PilotUpstreamSourceRelationKind.COPY_OF,
                source_b,
                root_source,
            ),
        )
    )

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="converge through one declared upstream source alias/ancestry lineage",
    ):
        validate_pilot_materialized_evidence_source_ancestry_preconditions_v1(
            (entry_a, entry_b),
            source_lineage_graph=graph,
        )


def test_direct_ancestor_and_descendant_are_not_independent_sources(tmp_path) -> None:
    parent = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.DATASET,
        "dataset:parent_v1",
    )
    child = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.ARTIFACT,
        "artifact:derived_child_v1",
    )
    entry_a, entry_b = _distinct_lineage_entries(tmp_path, child, parent)
    graph = PilotUpstreamSourceLineageGraph(
        relations=(
            PilotUpstreamSourceRelation(
                PilotUpstreamSourceRelationKind.DERIVED_FROM,
                child,
                parent,
            ),
        )
    )

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="source-ancestry independence preconditions",
    ):
        validate_pilot_materialized_evidence_source_ancestry_preconditions_v1(
            (entry_a, entry_b),
            source_lineage_graph=graph,
        )


def test_alias_refs_are_detected_even_when_exact_refs_differ(tmp_path) -> None:
    source_a = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.REFERENCE,
        "reference:canonical_manual_v1",
    )
    source_b = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.EXTERNAL_RECORD,
        "external_record:manual_alias_v1",
    )
    entry_a, entry_b = _distinct_lineage_entries(tmp_path, source_a, source_b)

    assert pilot_upstream_source_dependence_key_v1(source_a) != (
        pilot_upstream_source_dependence_key_v1(source_b)
    )

    graph = PilotUpstreamSourceLineageGraph(
        relations=(
            PilotUpstreamSourceRelation(
                PilotUpstreamSourceRelationKind.ALIAS_OF,
                source_a,
                source_b,
            ),
        )
    )

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="alias/ancestry lineage",
    ):
        validate_pilot_materialized_evidence_source_ancestry_preconditions_v1(
            (entry_a, entry_b),
            source_lineage_graph=graph,
        )


def test_multihop_copy_transform_lineage_reaches_common_root(tmp_path) -> None:
    root = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.REFERENCE,
        "reference:root_multihop_v1",
    )
    middle = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.ARTIFACT,
        "artifact:middle_multihop_v1",
    )
    source_a = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.MODEL_OUTPUT,
        "model_output:leaf_multihop_a",
    )
    source_b = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.TOOL_OUTPUT,
        "tool_output:leaf_multihop_b",
    )
    entry_a, entry_b = _distinct_lineage_entries(tmp_path, source_a, source_b)
    graph = PilotUpstreamSourceLineageGraph(
        relations=(
            PilotUpstreamSourceRelation(
                PilotUpstreamSourceRelationKind.TRANSFORM_OF,
                source_a,
                middle,
            ),
            PilotUpstreamSourceRelation(
                PilotUpstreamSourceRelationKind.COPY_OF,
                middle,
                root,
            ),
            PilotUpstreamSourceRelation(
                PilotUpstreamSourceRelationKind.DERIVED_FROM,
                source_b,
                root,
            ),
        )
    )

    closure_a = pilot_upstream_source_lineage_closure_keys_v1(source_a, graph)
    assert pilot_upstream_source_dependence_key_v1(root) in closure_a

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="source-ancestry independence preconditions",
    ):
        validate_pilot_materialized_evidence_source_ancestry_preconditions_v1(
            (entry_a, entry_b),
            source_lineage_graph=graph,
        )


def test_unconnected_declared_lineages_clear_only_known_graph_gate(tmp_path) -> None:
    root_a = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.REFERENCE,
        "reference:root_a",
    )
    root_b = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.REFERENCE,
        "reference:root_b",
    )
    source_a = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.ARTIFACT,
        "artifact:source_a",
    )
    source_b = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.ARTIFACT,
        "artifact:source_b",
    )
    entry_a, entry_b = _distinct_lineage_entries(tmp_path, source_a, source_b)
    graph = PilotUpstreamSourceLineageGraph(
        relations=(
            PilotUpstreamSourceRelation(
                PilotUpstreamSourceRelationKind.COPY_OF,
                source_a,
                root_a,
            ),
            PilotUpstreamSourceRelation(
                PilotUpstreamSourceRelationKind.TRANSFORM_OF,
                source_b,
                root_b,
            ),
        )
    )

    assert validate_pilot_materialized_evidence_source_ancestry_preconditions_v1(
        (entry_b, entry_a),
        source_lineage_graph=graph,
    ) == (entry_a, entry_b)


def test_empty_graph_is_allowed_without_asserting_source_independence(tmp_path) -> None:
    source_a = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.REFERENCE,
        "reference:unknown_lineage_a",
    )
    source_b = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.REFERENCE,
        "reference:unknown_lineage_b",
    )
    entry_a, entry_b = _distinct_lineage_entries(tmp_path, source_a, source_b)

    assert validate_pilot_materialized_evidence_source_ancestry_preconditions_v1(
        (entry_a, entry_b),
        source_lineage_graph=PilotUpstreamSourceLineageGraph(),
    ) == (entry_a, entry_b)


def test_lineage_closure_is_directional_and_does_not_echo_raw_refs() -> None:
    parent = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.REFERENCE,
        "reference:private_parent_v1",
    )
    child = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.MODEL_OUTPUT,
        "model_output:private_child_v1",
    )
    graph = PilotUpstreamSourceLineageGraph(
        relations=(
            PilotUpstreamSourceRelation(
                PilotUpstreamSourceRelationKind.TRANSFORM_OF,
                child,
                parent,
            ),
        )
    )

    child_closure = pilot_upstream_source_lineage_closure_keys_v1(child, graph)
    parent_closure = pilot_upstream_source_lineage_closure_keys_v1(parent, graph)

    assert pilot_upstream_source_dependence_key_v1(child) in child_closure
    assert pilot_upstream_source_dependence_key_v1(parent) in child_closure
    assert pilot_upstream_source_dependence_key_v1(parent) in parent_closure
    assert pilot_upstream_source_dependence_key_v1(child) not in parent_closure
    assert all(child.ref not in item and parent.ref not in item for item in child_closure)


def test_reverse_alias_duplicate_is_rejected() -> None:
    source_a = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.REFERENCE,
        "reference:alias_a",
    )
    source_b = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.REFERENCE,
        "reference:alias_b",
    )

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="reverse-alias relation",
    ):
        PilotUpstreamSourceLineageGraph(
            relations=(
                PilotUpstreamSourceRelation(
                    PilotUpstreamSourceRelationKind.ALIAS_OF,
                    source_a,
                    source_b,
                ),
                PilotUpstreamSourceRelation(
                    PilotUpstreamSourceRelationKind.ALIAS_OF,
                    source_b,
                    source_a,
                ),
            )
        )


def test_directed_cycle_after_alias_contraction_is_rejected() -> None:
    source_a = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.REFERENCE,
        "reference:cycle_alias_a",
    )
    source_b = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.EXTERNAL_RECORD,
        "external_record:cycle_alias_b",
    )
    source_c = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.ARTIFACT,
        "artifact:cycle_c",
    )

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="acyclic after alias contraction",
    ):
        PilotUpstreamSourceLineageGraph(
            relations=(
                PilotUpstreamSourceRelation(
                    PilotUpstreamSourceRelationKind.ALIAS_OF,
                    source_a,
                    source_b,
                ),
                PilotUpstreamSourceRelation(
                    PilotUpstreamSourceRelationKind.DERIVED_FROM,
                    source_b,
                    source_c,
                ),
                PilotUpstreamSourceRelation(
                    PilotUpstreamSourceRelationKind.COPY_OF,
                    source_c,
                    source_a,
                ),
            )
        )


def test_relation_cannot_point_to_same_exact_source_ref() -> None:
    source = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.REFERENCE,
        "reference:self_relation",
    )

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="two distinct exact source refs",
    ):
        PilotUpstreamSourceRelation(
            PilotUpstreamSourceRelationKind.DERIVED_FROM,
            source,
            source,
        )
