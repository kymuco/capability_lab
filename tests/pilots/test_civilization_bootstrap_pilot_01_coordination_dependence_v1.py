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
    PilotObservationCoordinationRef,
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
    pilot_observation_coordination_dependence_key_v1,
    propose_pilot_capture_evidence_materialization_v1,
    record_text_capture,
    resolve_reviewed_pilot_evidence_materialization_v1,
    validate_pilot_materialized_evidence_shared_coordination_preconditions_v1,
)


T0 = datetime(2026, 1, 11, 12, 0, tzinfo=timezone.utc)


def _reviewer():
    return PilotEvidenceMaterializationReviewerRef(
        PilotEvidenceMaterializationReviewerKind.HUMAN,
        "reviewer_coordination_dependence_01",
    )


def _workspace(tmp_path, *, name, session_id, capture_id, probe_id, text):
    root = tmp_path / name
    initialize_private_workspace(
        root,
        session_id=session_id,
        subject_ref=CapabilitySubjectRef("subject_coordination_dependence_01"),
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


def _reviewed_mechanism_basis(tmp_path, *, shared_mechanism=False):
    root_a = _workspace(
        tmp_path,
        name="coordination_conceptual",
        session_id="session_coordination_a",
        capture_id="conceptual_01",
        probe_id="conceptual_explanation",
        text="Synthetic conceptual observation.",
    )
    root_b = _workspace(
        tmp_path,
        name="coordination_calculation",
        session_id="session_coordination_b",
        capture_id="calculation_01",
        probe_id="calculation_work",
        text="Synthetic calculation observation.",
    )
    candidate_a, evidence_a = _materialize(
        root_a,
        capture_id="conceptual_01",
        materialization_id="materialization_coordination_a",
        evidence_id="evidence_coordination_a",
        review_id="review_coordination_a",
    )
    candidate_b, evidence_b = _materialize(
        root_b,
        capture_id="calculation_01",
        materialization_id="materialization_coordination_b",
        evidence_id="evidence_coordination_b",
        review_id="review_coordination_b",
    )

    upstream_a = PilotMaterializedEvidenceUpstreamLineageEntry(
        PilotMaterializedEvidenceBasisEntry(candidate_a, evidence_a),
        build_pilot_materialization_upstream_source_declaration_v1(
            candidate_a,
            sources=(
                PilotUpstreamSourceRef(
                    PilotUpstreamSourceKind.ARTIFACT,
                    "artifact:coordination_source_a",
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
                    "dataset:coordination_source_b",
                ),
            ),
        ),
    )
    source_graph = PilotUpstreamSourceLineageGraph()
    source_review = build_pilot_upstream_lineage_completeness_review_v1(
        (upstream_a, upstream_b),
        source_lineage_graph=source_graph,
        review_id="source_complete_for_coordination_01",
        upstream_source_declarations_status=PilotLineageCompletenessStatus.COMPLETE_FOR_SCOPE,
        source_lineage_graph_status=PilotLineageCompletenessStatus.COMPLETE_FOR_SCOPE,
        reviewer_ref=_reviewer(),
        reviewed_at=T0 + timedelta(minutes=10),
        rationale="Reviewed exact source basis for coordination tests.",
    )

    mechanism_a = PilotObservationMechanismRef(
        PilotObservationMechanismKind.TOOL_EXECUTION,
        "tool_execution:coordination_run_shared" if shared_mechanism else "tool_execution:coordination_run_a",
    )
    mechanism_b = PilotObservationMechanismRef(
        PilotObservationMechanismKind.TOOL_EXECUTION,
        "tool_execution:coordination_run_shared" if shared_mechanism else "tool_execution:coordination_run_b",
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
    mechanism_graph = PilotObservationMechanismLineageGraph()
    mechanism_review = build_pilot_mechanism_lineage_completeness_review_v1(
        (entry_a, entry_b),
        mechanism_lineage_graph=mechanism_graph,
        review_id="mechanism_complete_for_coordination_01",
        mechanism_declarations_status=PilotMechanismCompletenessStatus.COMPLETE_FOR_SCOPE,
        mechanism_lineage_graph_status=PilotMechanismCompletenessStatus.COMPLETE_FOR_SCOPE,
        reviewer_ref=_reviewer(),
        reviewed_at=T0 + timedelta(minutes=20),
        rationale="Reviewed exact mechanism basis for coordination tests.",
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
    )


def _coordination_entry(candidate, mechanism_entry, *coordinations):
    return PilotMaterializedEvidenceCoordinationEntry(
        mechanism_entry,
        build_pilot_materialization_coordination_declaration_v1(
            candidate,
            coordinations=tuple(coordinations),
        ),
    )


def _validate(entries, source_graph, source_review, mechanism_graph, mechanism_review):
    return validate_pilot_materialized_evidence_shared_coordination_preconditions_v1(
        entries,
        source_lineage_graph=source_graph,
        source_completeness_review=source_review,
        mechanism_lineage_graph=mechanism_graph,
        mechanism_completeness_review=mechanism_review,
    )


def test_shared_exact_controller_rejects_fully_reviewed_provenance_basis(tmp_path) -> None:
    candidate_a, candidate_b, entry_a, entry_b, sg, sr, mg, mr = _reviewed_mechanism_basis(tmp_path)
    shared = PilotObservationCoordinationRef(
        PilotObservationCoordinationKind.CONTROLLER,
        "controller:shared_collection_controller_01",
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="share one exact declared cross-observation coordination/control authority",
    ):
        _validate(
            (
                _coordination_entry(candidate_a, entry_a, shared),
                _coordination_entry(candidate_b, entry_b, shared),
            ),
            sg,
            sr,
            mg,
            mr,
        )


@pytest.mark.parametrize(
    "kind,ref",
    [
        (PilotObservationCoordinationKind.POLICY_EXECUTION, "policy_execution:shared_01"),
        (PilotObservationCoordinationKind.ADAPTIVE_SELECTOR, "adaptive_selector:shared_01"),
        (PilotObservationCoordinationKind.CONDITION_ASSIGNER, "condition_assigner:shared_01"),
        (PilotObservationCoordinationKind.ADJUDICATION_AUTHORITY, "adjudication_authority:shared_01"),
    ],
)
def test_other_shared_coordination_authorities_reject(tmp_path, kind, ref) -> None:
    candidate_a, candidate_b, entry_a, entry_b, sg, sr, mg, mr = _reviewed_mechanism_basis(tmp_path)
    shared = PilotObservationCoordinationRef(kind, ref)
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="shared-coordination independence preconditions",
    ):
        _validate(
            (
                _coordination_entry(candidate_a, entry_a, shared),
                _coordination_entry(candidate_b, entry_b, shared),
            ),
            sg,
            sr,
            mg,
            mr,
        )


def test_distinct_declared_coordination_refs_clear_only_exact_coordination_gate(tmp_path) -> None:
    candidate_a, candidate_b, entry_a, entry_b, sg, sr, mg, mr = _reviewed_mechanism_basis(tmp_path)
    a = _coordination_entry(
        candidate_a,
        entry_a,
        PilotObservationCoordinationRef(
            PilotObservationCoordinationKind.CONTROLLER,
            "controller:bounded_a",
        ),
    )
    b = _coordination_entry(
        candidate_b,
        entry_b,
        PilotObservationCoordinationRef(
            PilotObservationCoordinationKind.CONTROLLER,
            "controller:bounded_b",
        ),
    )
    assert _validate((b, a), sg, sr, mg, mr) == (a, b)


def test_empty_coordination_declarations_do_not_assert_control_absence(tmp_path) -> None:
    candidate_a, candidate_b, entry_a, entry_b, sg, sr, mg, mr = _reviewed_mechanism_basis(tmp_path)
    a = _coordination_entry(candidate_a, entry_a)
    b = _coordination_entry(candidate_b, entry_b)
    assert a.coordination_keys == ()
    assert b.coordination_keys == ()
    assert _validate((a, b), sg, sr, mg, mr) == (a, b)


def test_existing_reviewer_metadata_is_not_implicitly_coordination_authority(tmp_path) -> None:
    candidate_a, candidate_b, entry_a, entry_b, sg, sr, mg, mr = _reviewed_mechanism_basis(tmp_path)
    assert sr.reviewer_ref == mr.reviewer_ref == _reviewer()
    assert _validate(
        (
            _coordination_entry(candidate_a, entry_a),
            _coordination_entry(candidate_b, entry_b),
        ),
        sg,
        sr,
        mg,
        mr,
    )


def test_prior_shared_mechanism_rejects_before_distinct_coordination_can_help(tmp_path) -> None:
    candidate_a, candidate_b, entry_a, entry_b, sg, sr, mg, mr = _reviewed_mechanism_basis(
        tmp_path,
        shared_mechanism=True,
    )
    a = _coordination_entry(
        candidate_a,
        entry_a,
        PilotObservationCoordinationRef(
            PilotObservationCoordinationKind.CONTROLLER,
            "controller:distinct_a",
        ),
    )
    b = _coordination_entry(
        candidate_b,
        entry_b,
        PilotObservationCoordinationRef(
            PilotObservationCoordinationKind.CONTROLLER,
            "controller:distinct_b",
        ),
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="share one exact declared acquisition/governance mechanism",
    ):
        _validate((a, b), sg, sr, mg, mr)


def test_coordination_declaration_is_bound_to_exact_candidate(tmp_path) -> None:
    candidate_a, _candidate_b, _entry_a, entry_b, *_ = _reviewed_mechanism_basis(tmp_path)
    declaration_a = build_pilot_materialization_coordination_declaration_v1(
        candidate_a,
        coordinations=(
            PilotObservationCoordinationRef(
                PilotObservationCoordinationKind.SCHEDULER,
                "scheduler:bound_to_candidate_a",
            ),
        ),
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="candidate_sha256 does not match exact basis candidate",
    ):
        PilotMaterializedEvidenceCoordinationEntry(entry_b, declaration_a)


def test_coordination_key_is_domain_separated_kind_sensitive_and_does_not_echo_ref() -> None:
    raw_ref = "shared:opaque_coordination_123"
    controller = PilotObservationCoordinationRef(
        PilotObservationCoordinationKind.CONTROLLER,
        raw_ref,
    )
    selector = PilotObservationCoordinationRef(
        PilotObservationCoordinationKind.ADAPTIVE_SELECTOR,
        raw_ref,
    )
    controller_key = pilot_observation_coordination_dependence_key_v1(controller)
    selector_key = pilot_observation_coordination_dependence_key_v1(selector)
    assert controller_key.startswith("pilot_observation_coordination:")
    assert len(controller_key.removeprefix("pilot_observation_coordination:")) == 64
    assert raw_ref not in controller_key
    assert controller_key != selector_key


def test_coordination_declaration_rejects_duplicate_exact_refs(tmp_path) -> None:
    candidate_a, *_ = _reviewed_mechanism_basis(tmp_path)
    coordination = PilotObservationCoordinationRef(
        PilotObservationCoordinationKind.COORDINATION_PROCESS,
        "coordination_process:duplicate_01",
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="must not repeat an exact coordination ref",
    ):
        build_pilot_materialization_coordination_declaration_v1(
            candidate_a,
            coordinations=(coordination, coordination),
        )


def test_coordination_ref_requires_canonical_opaque_ascii_identifier() -> None:
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="canonical opaque ASCII identifier",
    ):
        PilotObservationCoordinationRef(
            PilotObservationCoordinationKind.OTHER,
            "coordination with spaces",
        )
