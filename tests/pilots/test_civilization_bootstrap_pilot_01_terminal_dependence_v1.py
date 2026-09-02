from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from capability_lab.epistemics import CapabilitySubjectRef, EvidenceId
from capability_lab.pilots.civilization_bootstrap_01 import (
    REVIEWED_PILOT_CAPTURE_TO_EVIDENCE_POLICY_V1,
    InvalidPilotEvidenceMaterialization,
    PilotAllocationCompletenessStatus,
    PilotCoordinationCompletenessStatus,
    PilotEvidenceMaterializationId,
    PilotEvidenceMaterializationReview,
    PilotEvidenceMaterializationReviewId,
    PilotEvidenceMaterializationReviewerKind,
    PilotEvidenceMaterializationReviewerRef,
    PilotEvidenceMaterializationVerdict,
    PilotLineageCompletenessStatus,
    PilotMaterializedEvidenceAllocationEntry,
    PilotMaterializedEvidenceBasisEntry,
    PilotMaterializedEvidenceCoordinationEntry,
    PilotMaterializedEvidenceMechanismEntry,
    PilotMaterializedEvidenceSelectionEntry,
    PilotMaterializedEvidenceTemporalEntry,
    PilotMaterializedEvidenceUpstreamLineageEntry,
    PilotMechanismCompletenessStatus,
    PilotObservationAllocationKind,
    PilotObservationAllocationLineageGraph,
    PilotObservationAllocationRef,
    PilotObservationCoordinationKind,
    PilotObservationCoordinationLineageGraph,
    PilotObservationCoordinationRef,
    PilotObservationMechanismKind,
    PilotObservationMechanismLineageGraph,
    PilotObservationMechanismRef,
    PilotObservationSelectionKind,
    PilotObservationSelectionLineageGraph,
    PilotObservationSelectionRef,
    PilotObservationTemporalKind,
    PilotObservationTemporalLineageGraph,
    PilotObservationTemporalRef,
    PilotReviewedMaterializationResolutionBinding,
    PilotSelectionCompletenessStatus,
    PilotTemporalCompletenessStatus,
    PilotUpstreamSourceKind,
    PilotUpstreamSourceLineageGraph,
    PilotUpstreamSourceRef,
    build_pilot_allocation_lineage_completeness_review_v1,
    build_pilot_coordination_lineage_completeness_review_v1,
    build_pilot_materialization_allocation_declaration_v1,
    build_pilot_materialization_coordination_declaration_v1,
    build_pilot_materialization_mechanism_declaration_v1,
    build_pilot_materialization_selection_declaration_v1,
    build_pilot_materialization_temporal_declaration_v1,
    build_pilot_materialization_upstream_source_declaration_v1,
    build_pilot_mechanism_lineage_completeness_review_v1,
    build_pilot_selection_lineage_completeness_review_v1,
    build_pilot_temporal_lineage_completeness_review_v1,
    build_pilot_upstream_lineage_completeness_review_v1,
    initialize_private_workspace,
    pilot_evidence_materialization_candidate_sha256,
    propose_pilot_capture_evidence_materialization_v1,
    record_text_capture,
    resolve_reviewed_pilot_evidence_materialization_with_receipt_v1,
    validate_pilot_materialized_evidence_reviewed_dependence_preconditions_v1,
)
from capability_lab.pilots.civilization_bootstrap_01 import (
    materialization_terminal as terminal_module,
)

T0 = datetime(2026, 1, 20, 12, 0, tzinfo=timezone.utc)


def _reviewer():
    return PilotEvidenceMaterializationReviewerRef(
        PilotEvidenceMaterializationReviewerKind.HUMAN,
        "reviewer_terminal_01",
    )


def _materialize_one(
    root,
    *,
    capture_id,
    materialization_id,
    evidence_id,
    review_id,
    proposed_at,
    reviewed_at,
    resolved_at,
):
    candidate = propose_pilot_capture_evidence_materialization_v1(
        root,
        capture_id=capture_id,
        materialization_id=PilotEvidenceMaterializationId(materialization_id),
        proposed_evidence_id=EvidenceId(evidence_id),
        proposed_at=proposed_at,
    )
    review = PilotEvidenceMaterializationReview(
        review_id=PilotEvidenceMaterializationReviewId(review_id),
        materialization_id=candidate.materialization_id,
        candidate_sha256=pilot_evidence_materialization_candidate_sha256(candidate),
        policy_ref=REVIEWED_PILOT_CAPTURE_TO_EVIDENCE_POLICY_V1,
        reviewer_ref=_reviewer(),
        verdict=PilotEvidenceMaterializationVerdict.MATERIALIZE,
        reviewed_at=reviewed_at,
        rationale="Materialize exact capture for terminal dependence regression.",
    )
    evidence, receipt = resolve_reviewed_pilot_evidence_materialization_with_receipt_v1(
        root,
        candidate=candidate,
        review=review,
        resolved_at=resolved_at,
    )
    assert evidence is not None
    assert receipt is not None
    return (
        candidate,
        evidence,
        PilotReviewedMaterializationResolutionBinding(review, receipt),
    )


def _real_materialized_pair(tmp_path, *, duplicate_evidence_id=False):
    subject = CapabilitySubjectRef("subject_terminal_01")
    root_a = tmp_path / "terminal_a"
    root_b = tmp_path / "terminal_b"
    initialize_private_workspace(
        root_a,
        session_id="session_terminal_a",
        subject_ref=subject,
        created_at=T0,
    )
    initialize_private_workspace(
        root_b,
        session_id="session_terminal_b",
        subject_ref=subject,
        created_at=T0,
    )
    record_text_capture(
        root_a,
        capture_id="capture_terminal_a",
        probe_id="conceptual_explanation",
        text_content="Terminal regression conceptual observation.",
        captured_at=T0 + timedelta(minutes=1),
    )
    record_text_capture(
        root_b,
        capture_id="capture_terminal_b",
        probe_id="calculation_work",
        text_content="Terminal regression calculation observation.",
        captured_at=T0 + timedelta(minutes=2),
    )
    evidence_a_id = (
        "evidence_terminal_shared" if duplicate_evidence_id else "evidence_terminal_a"
    )
    evidence_b_id = (
        "evidence_terminal_shared" if duplicate_evidence_id else "evidence_terminal_b"
    )
    return (
        _materialize_one(
            root_a,
            capture_id="capture_terminal_a",
            materialization_id="materialization_terminal_a",
            evidence_id=evidence_a_id,
            review_id="review_terminal_a",
            proposed_at=T0 + timedelta(minutes=3),
            reviewed_at=T0 + timedelta(minutes=4),
            resolved_at=T0 + timedelta(minutes=5),
        ),
        _materialize_one(
            root_b,
            capture_id="capture_terminal_b",
            materialization_id="materialization_terminal_b",
            evidence_id=evidence_b_id,
            review_id="review_terminal_b",
            proposed_at=T0 + timedelta(minutes=6),
            reviewed_at=T0 + timedelta(minutes=7),
            resolved_at=T0 + timedelta(minutes=8),
        ),
    )


def _ref_value(family, suffix, shared_family):
    tail = "shared" if family == shared_family else suffix
    return {
        "source": "artifact:source_",
        "mechanism": "tool_execution:run_",
        "coordination": "controller:control_",
        "temporal": "intervention_episode:temporal_",
        "allocation": "randomization_state:allocation_",
        "selection": "sampling_frame:selection_",
    }[family] + tail


def _wrap_observation(candidate, evidence, suffix, shared_family=None):
    basis = PilotMaterializedEvidenceBasisEntry(candidate, evidence)
    upstream = PilotMaterializedEvidenceUpstreamLineageEntry(
        basis,
        build_pilot_materialization_upstream_source_declaration_v1(
            candidate,
            sources=(
                PilotUpstreamSourceRef(
                    PilotUpstreamSourceKind.ARTIFACT,
                    _ref_value("source", suffix, shared_family),
                ),
            ),
        ),
    )
    mechanism = PilotMaterializedEvidenceMechanismEntry(
        upstream,
        build_pilot_materialization_mechanism_declaration_v1(
            candidate,
            mechanisms=(
                PilotObservationMechanismRef(
                    PilotObservationMechanismKind.TOOL_EXECUTION,
                    _ref_value("mechanism", suffix, shared_family),
                ),
            ),
        ),
    )
    coordination = PilotMaterializedEvidenceCoordinationEntry(
        mechanism,
        build_pilot_materialization_coordination_declaration_v1(
            candidate,
            coordinations=(
                PilotObservationCoordinationRef(
                    PilotObservationCoordinationKind.CONTROLLER,
                    _ref_value("coordination", suffix, shared_family),
                ),
            ),
        ),
    )
    temporal = PilotMaterializedEvidenceTemporalEntry(
        coordination,
        build_pilot_materialization_temporal_declaration_v1(
            candidate,
            temporals=(
                PilotObservationTemporalRef(
                    PilotObservationTemporalKind.INTERVENTION_EPISODE,
                    _ref_value("temporal", suffix, shared_family),
                ),
            ),
        ),
    )
    allocation = PilotMaterializedEvidenceAllocationEntry(
        temporal,
        build_pilot_materialization_allocation_declaration_v1(
            candidate,
            allocations=(
                PilotObservationAllocationRef(
                    PilotObservationAllocationKind.RANDOMIZATION_STATE,
                    _ref_value("allocation", suffix, shared_family),
                ),
            ),
        ),
    )
    return PilotMaterializedEvidenceSelectionEntry(
        allocation,
        build_pilot_materialization_selection_declaration_v1(
            candidate,
            selections=(
                PilotObservationSelectionRef(
                    PilotObservationSelectionKind.SAMPLING_FRAME_INSTANCE,
                    _ref_value("selection", suffix, shared_family),
                ),
            ),
        ),
    )


def _lower_entries(selection_entries):
    allocations = tuple(entry.allocation_entry for entry in selection_entries)
    temporals = tuple(entry.temporal_entry for entry in allocations)
    coordinations = tuple(entry.coordination_entry for entry in temporals)
    mechanisms = tuple(entry.mechanism_entry for entry in coordinations)
    upstream = tuple(entry.upstream_lineage_entry for entry in mechanisms)
    return upstream, mechanisms, coordinations, temporals, allocations


def _case(tmp_path, *, shared_family=None, duplicate_evidence_id=False):
    pair = _real_materialized_pair(
        tmp_path,
        duplicate_evidence_id=duplicate_evidence_id,
    )
    entries = (
        _wrap_observation(pair[0][0], pair[0][1], "a", shared_family),
        _wrap_observation(pair[1][0], pair[1][1], "b", shared_family),
    )
    upstream, mechanisms, coordinations, temporals, allocations = _lower_entries(entries)

    source_graph = PilotUpstreamSourceLineageGraph()
    mechanism_graph = PilotObservationMechanismLineageGraph()
    coordination_graph = PilotObservationCoordinationLineageGraph()
    temporal_graph = PilotObservationTemporalLineageGraph()
    allocation_graph = PilotObservationAllocationLineageGraph()
    selection_graph = PilotObservationSelectionLineageGraph()

    source_review = build_pilot_upstream_lineage_completeness_review_v1(
        upstream,
        source_lineage_graph=source_graph,
        review_id="terminal_source_complete",
        upstream_source_declarations_status=PilotLineageCompletenessStatus.COMPLETE_FOR_SCOPE,
        source_lineage_graph_status=PilotLineageCompletenessStatus.COMPLETE_FOR_SCOPE,
        reviewer_ref=_reviewer(),
        reviewed_at=T0 + timedelta(minutes=10),
        rationale="Terminal source scope reviewed complete.",
    )
    mechanism_review = build_pilot_mechanism_lineage_completeness_review_v1(
        mechanisms,
        mechanism_lineage_graph=mechanism_graph,
        review_id="terminal_mechanism_complete",
        mechanism_declarations_status=PilotMechanismCompletenessStatus.COMPLETE_FOR_SCOPE,
        mechanism_lineage_graph_status=PilotMechanismCompletenessStatus.COMPLETE_FOR_SCOPE,
        reviewer_ref=_reviewer(),
        reviewed_at=T0 + timedelta(minutes=11),
        rationale="Terminal mechanism scope reviewed complete.",
    )
    coordination_review = build_pilot_coordination_lineage_completeness_review_v1(
        coordinations,
        coordination_lineage_graph=coordination_graph,
        review_id="terminal_coordination_complete",
        coordination_declarations_status=PilotCoordinationCompletenessStatus.COMPLETE_FOR_SCOPE,
        coordination_lineage_graph_status=PilotCoordinationCompletenessStatus.COMPLETE_FOR_SCOPE,
        reviewer_ref=_reviewer(),
        reviewed_at=T0 + timedelta(minutes=12),
        rationale="Terminal coordination scope reviewed complete.",
    )
    temporal_review = build_pilot_temporal_lineage_completeness_review_v1(
        temporals,
        temporal_lineage_graph=temporal_graph,
        review_id="terminal_temporal_complete",
        temporal_declarations_status=PilotTemporalCompletenessStatus.COMPLETE_FOR_SCOPE,
        temporal_lineage_graph_status=PilotTemporalCompletenessStatus.COMPLETE_FOR_SCOPE,
        reviewer_ref=_reviewer(),
        reviewed_at=T0 + timedelta(minutes=13),
        rationale="Terminal temporal scope reviewed complete.",
    )
    allocation_review = build_pilot_allocation_lineage_completeness_review_v1(
        allocations,
        allocation_lineage_graph=allocation_graph,
        review_id="terminal_allocation_complete",
        allocation_declarations_status=PilotAllocationCompletenessStatus.COMPLETE_FOR_SCOPE,
        allocation_lineage_graph_status=PilotAllocationCompletenessStatus.COMPLETE_FOR_SCOPE,
        reviewer_ref=_reviewer(),
        reviewed_at=T0 + timedelta(minutes=14),
        rationale="Terminal allocation scope reviewed complete.",
    )
    selection_review = build_pilot_selection_lineage_completeness_review_v1(
        entries,
        selection_lineage_graph=selection_graph,
        review_id="terminal_selection_complete",
        selection_declarations_status=PilotSelectionCompletenessStatus.COMPLETE_FOR_SCOPE,
        selection_lineage_graph_status=PilotSelectionCompletenessStatus.COMPLETE_FOR_SCOPE,
        reviewer_ref=_reviewer(),
        reviewed_at=T0 + timedelta(minutes=15),
        rationale="Terminal selection scope reviewed complete.",
    )

    return {
        "selection_entries": entries,
        "materialization_resolution_bindings": (pair[0][2], pair[1][2]),
        "source_lineage_graph": source_graph,
        "source_completeness_review": source_review,
        "mechanism_lineage_graph": mechanism_graph,
        "mechanism_completeness_review": mechanism_review,
        "coordination_lineage_graph": coordination_graph,
        "coordination_completeness_review": coordination_review,
        "temporal_lineage_graph": temporal_graph,
        "temporal_completeness_review": temporal_review,
        "allocation_lineage_graph": allocation_graph,
        "allocation_completeness_review": allocation_review,
        "selection_lineage_graph": selection_graph,
        "selection_completeness_review": selection_review,
    }


def _validate(case):
    return validate_pilot_materialized_evidence_reviewed_dependence_preconditions_v1(
        **case
    )


def test_real_whole_ladder_terminal_pass(tmp_path):
    result = _validate(_case(tmp_path))
    assert tuple(
        str(
            entry.allocation_entry.temporal_entry.coordination_entry.mechanism_entry
            .upstream_lineage_entry.basis_entry.evidence.evidence_id
        )
        for entry in result
    ) == ("evidence_terminal_a", "evidence_terminal_b")


@pytest.mark.parametrize(
    "family",
    ["source", "mechanism", "coordination", "temporal", "allocation", "selection"],
)
def test_terminal_rejects_shared_exact_identity_in_every_family(tmp_path, family):
    with pytest.raises(InvalidPilotEvidenceMaterialization):
        _validate(_case(tmp_path, shared_family=family))


def test_terminal_rejects_duplicate_evidence_identity_before_scope_acceptance(tmp_path):
    with pytest.raises(InvalidPilotEvidenceMaterialization, match="duplicate EvidenceId"):
        _validate(_case(tmp_path, duplicate_evidence_id=True))


def test_terminal_rejects_missing_reviewed_resolution_binding(tmp_path):
    case = _case(tmp_path)
    case["materialization_resolution_bindings"] = case[
        "materialization_resolution_bindings"
    ][:1]
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="one-to-one reviewed-resolution receipt coverage",
    ):
        _validate(case)


@pytest.mark.parametrize(
    "review_key,field_name,unknown_status",
    [
        (
            "source_completeness_review",
            "upstream_source_declarations_status",
            PilotLineageCompletenessStatus.UNKNOWN,
        ),
        (
            "mechanism_completeness_review",
            "mechanism_declarations_status",
            PilotMechanismCompletenessStatus.UNKNOWN,
        ),
        (
            "coordination_completeness_review",
            "coordination_declarations_status",
            PilotCoordinationCompletenessStatus.UNKNOWN,
        ),
        (
            "temporal_completeness_review",
            "temporal_declarations_status",
            PilotTemporalCompletenessStatus.UNKNOWN,
        ),
        (
            "allocation_completeness_review",
            "allocation_declarations_status",
            PilotAllocationCompletenessStatus.UNKNOWN,
        ),
        (
            "selection_completeness_review",
            "selection_declarations_status",
            PilotSelectionCompletenessStatus.UNKNOWN,
        ),
    ],
)
def test_terminal_propagates_incomplete_governance_from_every_family(
    tmp_path,
    review_key,
    field_name,
    unknown_status,
):
    case = _case(tmp_path)
    case[review_key] = replace(
        case[review_key],
        **{field_name: unknown_status},
    )
    with pytest.raises(InvalidPilotEvidenceMaterialization):
        _validate(case)


@pytest.mark.parametrize(
    "family,review_key",
    [
        ("source", "source_completeness_review"),
        ("mechanism", "mechanism_completeness_review"),
        ("coordination", "coordination_completeness_review"),
        ("temporal", "temporal_completeness_review"),
        ("allocation", "allocation_completeness_review"),
        ("selection", "selection_completeness_review"),
    ],
)
def test_each_family_gate_rejects_review_that_predates_materialized_basis_even_without_terminal_guard(
    tmp_path,
    monkeypatch,
    family,
    review_key,
):
    case = _case(tmp_path)
    case[review_key] = replace(
        case[review_key],
        reviewed_at=T0 + timedelta(minutes=1),
    )
    monkeypatch.setattr(
        terminal_module,
        "_validate_completeness_review_temporal_causality_v1",
        lambda _entries, **_kwargs: None,
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match=rf"{family} completeness reviewed_at must not precede",
    ):
        _validate(case)
