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
    PilotMaterializationMechanismDeclaration,
    PilotObservationMechanismKind,
    PilotObservationMechanismRef,
    PilotUpstreamSourceKind,
    PilotUpstreamSourceLineageGraph,
    PilotUpstreamSourceRef,
    build_pilot_materialization_mechanism_declaration_v1,
    build_pilot_materialization_upstream_source_declaration_v1,
    build_pilot_upstream_lineage_completeness_review_v1,
    initialize_private_workspace,
    pilot_evidence_materialization_candidate_sha256,
    pilot_observation_mechanism_dependence_key_v1,
    propose_pilot_capture_evidence_materialization_v1,
    record_text_capture,
    resolve_reviewed_pilot_evidence_materialization_v1,
    validate_pilot_materialized_evidence_reviewed_source_origin_preconditions_v1,
    validate_pilot_materialized_evidence_shared_mechanism_preconditions_v1,
)


T0 = datetime(2026, 1, 9, 12, 0, tzinfo=timezone.utc)


def _reviewer():
    return PilotEvidenceMaterializationReviewerRef(
        PilotEvidenceMaterializationReviewerKind.HUMAN,
        "reviewer_mechanism_dependence_01",
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
        subject_ref=CapabilitySubjectRef("subject_mechanism_dependence_01"),
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


def _reviewed_origin_basis(tmp_path):
    root_a = _workspace(
        tmp_path,
        name="mechanism_conceptual",
        session_id="session_mechanism_a",
        capture_id="conceptual_01",
        probe_id="conceptual_explanation",
        text="Synthetic conceptual observation.",
    )
    root_b = _workspace(
        tmp_path,
        name="mechanism_calculation",
        session_id="session_mechanism_b",
        capture_id="calculation_01",
        probe_id="calculation_work",
        text="Synthetic calculation observation.",
    )
    candidate_a, evidence_a = _materialize(
        root_a,
        capture_id="conceptual_01",
        materialization_id="materialization_mechanism_a",
        evidence_id="evidence_mechanism_a",
        review_id="review_mechanism_a",
    )
    candidate_b, evidence_b = _materialize(
        root_b,
        capture_id="calculation_01",
        materialization_id="materialization_mechanism_b",
        evidence_id="evidence_mechanism_b",
        review_id="review_mechanism_b",
    )

    source_a = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.ARTIFACT,
        "artifact:mechanism_root_a",
    )
    source_b = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.DATASET,
        "dataset:mechanism_root_b",
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
    graph = PilotUpstreamSourceLineageGraph()
    completeness_review = build_pilot_upstream_lineage_completeness_review_v1(
        upstream_entries,
        source_lineage_graph=graph,
        review_id="mechanism_source_origin_complete_01",
        upstream_source_declarations_status=(
            PilotLineageCompletenessStatus.COMPLETE_FOR_SCOPE
        ),
        source_lineage_graph_status=(
            PilotLineageCompletenessStatus.COMPLETE_FOR_SCOPE
        ),
        reviewer_ref=_reviewer(),
        reviewed_at=T0 + timedelta(minutes=10),
        rationale="Reviewed exact source-origin scope before mechanism governance.",
    )
    assert validate_pilot_materialized_evidence_reviewed_source_origin_preconditions_v1(
        upstream_entries,
        source_lineage_graph=graph,
        completeness_review=completeness_review,
    ) == upstream_entries
    return (candidate_a, upstream_a), (candidate_b, upstream_b), graph, completeness_review


def _mechanism_entry(candidate, upstream_entry, *mechanisms):
    return PilotMaterializedEvidenceMechanismEntry(
        upstream_entry,
        build_pilot_materialization_mechanism_declaration_v1(
            candidate,
            mechanisms=tuple(mechanisms),
        ),
    )


def test_shared_exact_model_run_rejects_source_separated_reviewed_basis(tmp_path) -> None:
    (candidate_a, upstream_a), (candidate_b, upstream_b), graph, review = (
        _reviewed_origin_basis(tmp_path)
    )
    shared = PilotObservationMechanismRef(
        PilotObservationMechanismKind.MODEL_RUN,
        "model_run:shared_run_01",
    )
    entry_a = _mechanism_entry(candidate_a, upstream_a, shared)
    entry_b = _mechanism_entry(candidate_b, upstream_b, shared)

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="share one exact declared acquisition/governance mechanism",
    ):
        validate_pilot_materialized_evidence_shared_mechanism_preconditions_v1(
            (entry_a, entry_b),
            source_lineage_graph=graph,
            completeness_review=review,
        )


def test_shared_exact_acquisition_pipeline_rejects(tmp_path) -> None:
    (candidate_a, upstream_a), (candidate_b, upstream_b), graph, review = (
        _reviewed_origin_basis(tmp_path)
    )
    shared = PilotObservationMechanismRef(
        PilotObservationMechanismKind.ACQUISITION_PIPELINE,
        "acquisition_pipeline:shared_pipeline_v1",
    )

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="shared-mechanism independence preconditions",
    ):
        validate_pilot_materialized_evidence_shared_mechanism_preconditions_v1(
            (
                _mechanism_entry(candidate_a, upstream_a, shared),
                _mechanism_entry(candidate_b, upstream_b, shared),
            ),
            source_lineage_graph=graph,
            completeness_review=review,
        )


def test_distinct_declared_mechanisms_clear_only_exact_shared_mechanism_gate(
    tmp_path,
) -> None:
    (candidate_a, upstream_a), (candidate_b, upstream_b), graph, review = (
        _reviewed_origin_basis(tmp_path)
    )
    entry_a = _mechanism_entry(
        candidate_a,
        upstream_a,
        PilotObservationMechanismRef(
            PilotObservationMechanismKind.TOOL_EXECUTION,
            "tool_execution:run_a",
        ),
    )
    entry_b = _mechanism_entry(
        candidate_b,
        upstream_b,
        PilotObservationMechanismRef(
            PilotObservationMechanismKind.TOOL_EXECUTION,
            "tool_execution:run_b",
        ),
    )

    assert validate_pilot_materialized_evidence_shared_mechanism_preconditions_v1(
        (entry_b, entry_a),
        source_lineage_graph=graph,
        completeness_review=review,
    ) == (entry_a, entry_b)


def test_empty_mechanism_declarations_do_not_assert_mechanism_absence(tmp_path) -> None:
    (candidate_a, upstream_a), (candidate_b, upstream_b), graph, review = (
        _reviewed_origin_basis(tmp_path)
    )
    entry_a = _mechanism_entry(candidate_a, upstream_a)
    entry_b = _mechanism_entry(candidate_b, upstream_b)

    assert entry_a.mechanism_keys == ()
    assert entry_b.mechanism_keys == ()
    assert validate_pilot_materialized_evidence_shared_mechanism_preconditions_v1(
        (entry_a, entry_b),
        source_lineage_graph=graph,
        completeness_review=review,
    ) == (entry_a, entry_b)


def test_same_existing_reviewer_metadata_is_not_implicitly_a_mechanism_key(
    tmp_path,
) -> None:
    (candidate_a, upstream_a), (candidate_b, upstream_b), graph, review = (
        _reviewed_origin_basis(tmp_path)
    )
    assert review.reviewer_ref == _reviewer()

    entry_a = _mechanism_entry(candidate_a, upstream_a)
    entry_b = _mechanism_entry(candidate_b, upstream_b)

    assert validate_pilot_materialized_evidence_shared_mechanism_preconditions_v1(
        (entry_a, entry_b),
        source_lineage_graph=graph,
        completeness_review=review,
    ) == (entry_a, entry_b)


def test_mechanism_declaration_is_bound_to_exact_candidate(tmp_path) -> None:
    (candidate_a, _upstream_a), (_candidate_b, upstream_b), _graph, _review = (
        _reviewed_origin_basis(tmp_path)
    )
    declaration_a = build_pilot_materialization_mechanism_declaration_v1(
        candidate_a,
        mechanisms=(
            PilotObservationMechanismRef(
                PilotObservationMechanismKind.OPERATOR,
                "operator:explicit_acquisition_operator_a",
            ),
        ),
    )

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="candidate_sha256 does not match exact basis candidate",
    ):
        PilotMaterializedEvidenceMechanismEntry(
            upstream_b,
            declaration_a,
        )


def test_mechanism_key_is_domain_separated_kind_sensitive_and_does_not_echo_ref() -> None:
    raw_ref = "shared:opaque_mechanism_123"
    model = PilotObservationMechanismRef(
        PilotObservationMechanismKind.MODEL_RUN,
        raw_ref,
    )
    tool = PilotObservationMechanismRef(
        PilotObservationMechanismKind.TOOL_EXECUTION,
        raw_ref,
    )

    model_key = pilot_observation_mechanism_dependence_key_v1(model)
    tool_key = pilot_observation_mechanism_dependence_key_v1(tool)

    assert model_key.startswith("pilot_observation_mechanism:")
    assert len(model_key.removeprefix("pilot_observation_mechanism:")) == 64
    assert raw_ref not in model_key
    assert model_key != tool_key


def test_mechanism_declaration_rejects_duplicate_exact_refs(tmp_path) -> None:
    (candidate_a, _upstream_a), _, _, _ = _reviewed_origin_basis(tmp_path)
    mechanism = PilotObservationMechanismRef(
        PilotObservationMechanismKind.ENVIRONMENT,
        "environment:shared_lab_context_v1",
    )

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="must not repeat an exact mechanism ref",
    ):
        PilotMaterializationMechanismDeclaration(
            candidate_sha256=pilot_evidence_materialization_candidate_sha256(
                candidate_a
            ),
            mechanisms=(mechanism, mechanism),
        )


def test_mechanism_ref_requires_canonical_opaque_ascii_identifier() -> None:
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="canonical opaque ASCII identifier",
    ):
        PilotObservationMechanismRef(
            PilotObservationMechanismKind.REVIEW_PROCESS,
            "review process with spaces",
        )
