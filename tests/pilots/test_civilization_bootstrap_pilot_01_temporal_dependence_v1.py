from datetime import datetime, timedelta, timezone

import pytest

from capability_lab.epistemics import CapabilitySubjectRef, EvidenceId
from capability_lab.pilots.civilization_bootstrap_01 import (
    REVIEWED_PILOT_CAPTURE_TO_EVIDENCE_POLICY_V1,
    InvalidPilotEvidenceMaterialization,
    PilotCoordinationCompletenessStatus,
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
    PilotMaterializedEvidenceTemporalEntry,
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
    PilotObservationTemporalKind,
    PilotObservationTemporalRef,
    PilotUpstreamSourceKind,
    PilotUpstreamSourceLineageGraph,
    PilotUpstreamSourceRef,
    build_pilot_coordination_lineage_completeness_review_v1,
    build_pilot_materialization_coordination_declaration_v1,
    build_pilot_materialization_mechanism_declaration_v1,
    build_pilot_materialization_temporal_declaration_v1,
    build_pilot_materialization_upstream_source_declaration_v1,
    build_pilot_mechanism_lineage_completeness_review_v1,
    build_pilot_upstream_lineage_completeness_review_v1,
    initialize_private_workspace,
    pilot_evidence_materialization_candidate_sha256,
    pilot_observation_temporal_dependence_key_v1,
    propose_pilot_capture_evidence_materialization_v1,
    record_text_capture,
    resolve_reviewed_pilot_evidence_materialization_v1,
    validate_pilot_materialized_evidence_shared_temporal_preconditions_v1,
)


T0 = datetime(2026, 1, 13, 12, 0, tzinfo=timezone.utc)


def _reviewer():
    return PilotEvidenceMaterializationReviewerRef(
        PilotEvidenceMaterializationReviewerKind.HUMAN,
        "reviewer_temporal_dependence_01",
    )


def _workspace(tmp_path, *, name, session_id, capture_id, probe_id, text):
    root = tmp_path / name
    initialize_private_workspace(
        root,
        session_id=session_id,
        subject_ref=CapabilitySubjectRef("subject_temporal_dependence_01"),
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
        name="temporal_conceptual",
        session_id="session_temporal_a",
        capture_id="conceptual_01",
        probe_id="conceptual_explanation",
        text="Synthetic conceptual observation.",
    )
    root_b = _workspace(
        tmp_path,
        name="temporal_calculation",
        session_id="session_temporal_b",
        capture_id="calculation_01",
        probe_id="calculation_work",
        text="Synthetic calculation observation.",
    )
    candidate_a, evidence_a = _materialize(
        root_a,
        capture_id="conceptual_01",
        materialization_id="materialization_temporal_a",
        evidence_id="evidence_temporal_a",
        review_id="review_temporal_a",
    )
    candidate_b, evidence_b = _materialize(
        root_b,
        capture_id="calculation_01",
        materialization_id="materialization_temporal_b",
        evidence_id="evidence_temporal_b",
        review_id="review_temporal_b",
    )

    upstream_a = PilotMaterializedEvidenceUpstreamLineageEntry(
        PilotMaterializedEvidenceBasisEntry(candidate_a, evidence_a),
        build_pilot_materialization_upstream_source_declaration_v1(
            candidate_a,
            sources=(
                PilotUpstreamSourceRef(
                    PilotUpstreamSourceKind.ARTIFACT,
                    "artifact:temporal_source_a",
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
                    "dataset:temporal_source_b",
                ),
            ),
        ),
    )
    source_graph = PilotUpstreamSourceLineageGraph()
    source_review = build_pilot_upstream_lineage_completeness_review_v1(
        (upstream_a, upstream_b),
        source_lineage_graph=source_graph,
        review_id="source_complete_for_temporal_01",
        upstream_source_declarations_status=(
            PilotLineageCompletenessStatus.COMPLETE_FOR_SCOPE
        ),
        source_lineage_graph_status=(
            PilotLineageCompletenessStatus.COMPLETE_FOR_SCOPE
        ),
        reviewer_ref=_reviewer(),
        reviewed_at=T0 + timedelta(minutes=10),
        rationale="Reviewed exact source basis for temporal tests.",
    )

    mechanism_a = PilotObservationMechanismRef(
        PilotObservationMechanismKind.TOOL_EXECUTION,
        "tool_execution:temporal_run_a",
    )
    mechanism_b = PilotObservationMechanismRef(
        PilotObservationMechanismKind.TOOL_EXECUTION,
        "tool_execution:temporal_run_b",
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
        review_id="mechanism_complete_for_temporal_01",
        mechanism_declarations_status=(
            PilotMechanismCompletenessStatus.COMPLETE_FOR_SCOPE
        ),
        mechanism_lineage_graph_status=(
            PilotMechanismCompletenessStatus.COMPLETE_FOR_SCOPE
        ),
        reviewer_ref=_reviewer(),
        reviewed_at=T0 + timedelta(minutes=20),
        rationale="Reviewed exact mechanism basis for temporal tests.",
    )

    coordination_a = PilotObservationCoordinationRef(
        PilotObservationCoordinationKind.CONTROLLER,
        (
            "controller:temporal_shared"
            if shared_coordination
            else "controller:temporal_a"
        ),
    )
    coordination_b = PilotObservationCoordinationRef(
        PilotObservationCoordinationKind.CONTROLLER,
        (
            "controller:temporal_shared"
            if shared_coordination
            else "controller:temporal_b"
        ),
    )
    coordination_entry_a = PilotMaterializedEvidenceCoordinationEntry(
        mechanism_entry_a,
        build_pilot_materialization_coordination_declaration_v1(
            candidate_a,
            coordinations=(coordination_a,),
        ),
    )
    coordination_entry_b = PilotMaterializedEvidenceCoordinationEntry(
        mechanism_entry_b,
        build_pilot_materialization_coordination_declaration_v1(
            candidate_b,
            coordinations=(coordination_b,),
        ),
    )
    coordination_graph = PilotObservationCoordinationLineageGraph()
    coordination_review = build_pilot_coordination_lineage_completeness_review_v1(
        (coordination_entry_a, coordination_entry_b),
        coordination_lineage_graph=coordination_graph,
        review_id="coordination_complete_for_temporal_01",
        coordination_declarations_status=(
            PilotCoordinationCompletenessStatus.COMPLETE_FOR_SCOPE
        ),
        coordination_lineage_graph_status=(
            PilotCoordinationCompletenessStatus.COMPLETE_FOR_SCOPE
        ),
        reviewer_ref=_reviewer(),
        reviewed_at=T0 + timedelta(minutes=30),
        rationale="Reviewed exact coordination basis for temporal tests.",
    )

    return (
        candidate_a,
        candidate_b,
        coordination_entry_a,
        coordination_entry_b,
        source_graph,
        source_review,
        mechanism_graph,
        mechanism_review,
        coordination_graph,
        coordination_review,
    )


def _temporal_entry(candidate, coordination_entry, *temporals):
    return PilotMaterializedEvidenceTemporalEntry(
        coordination_entry,
        build_pilot_materialization_temporal_declaration_v1(
            candidate,
            temporals=tuple(temporals),
        ),
    )


def _validate(entries, sg, sr, mg, mr, cg, cr):
    return validate_pilot_materialized_evidence_shared_temporal_preconditions_v1(
        entries,
        source_lineage_graph=sg,
        source_completeness_review=sr,
        mechanism_lineage_graph=mg,
        mechanism_completeness_review=mr,
        coordination_lineage_graph=cg,
        coordination_completeness_review=cr,
    )


def test_shared_exact_intervention_episode_rejects_fully_reviewed_basis(tmp_path) -> None:
    candidate_a, candidate_b, a, b, sg, sr, mg, mr, cg, cr = (
        _reviewed_coordination_basis(tmp_path)
    )
    shared = PilotObservationTemporalRef(
        PilotObservationTemporalKind.INTERVENTION_EPISODE,
        "intervention_episode:shared_01",
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="share one exact declared temporal/intervention/carryover causal identity",
    ):
        _validate(
            (
                _temporal_entry(candidate_a, a, shared),
                _temporal_entry(candidate_b, b, shared),
            ),
            sg,
            sr,
            mg,
            mr,
            cg,
            cr,
        )


@pytest.mark.parametrize(
    "kind,ref",
    [
        (
            PilotObservationTemporalKind.ADAPTIVE_STATE,
            "adaptive_state:shared_01",
        ),
        (
            PilotObservationTemporalKind.CARRYOVER_STATE,
            "carryover_state:shared_01",
        ),
        (
            PilotObservationTemporalKind.EXPOSURE_EPISODE,
            "exposure_episode:shared_01",
        ),
        (
            PilotObservationTemporalKind.HISTORY_STATE,
            "history_state:shared_01",
        ),
    ],
)
def test_other_shared_temporal_identities_reject(tmp_path, kind, ref) -> None:
    candidate_a, candidate_b, a, b, sg, sr, mg, mr, cg, cr = (
        _reviewed_coordination_basis(tmp_path)
    )
    shared = PilotObservationTemporalRef(kind, ref)
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="shared-temporal independence preconditions",
    ):
        _validate(
            (
                _temporal_entry(candidate_a, a, shared),
                _temporal_entry(candidate_b, b, shared),
            ),
            sg,
            sr,
            mg,
            mr,
            cg,
            cr,
        )


def test_distinct_temporal_refs_clear_only_exact_temporal_gate(tmp_path) -> None:
    candidate_a, candidate_b, a, b, sg, sr, mg, mr, cg, cr = (
        _reviewed_coordination_basis(tmp_path)
    )
    temporal_a = PilotObservationTemporalRef(
        PilotObservationTemporalKind.INTERVENTION_EPISODE,
        "intervention_episode:bounded_a",
    )
    temporal_b = PilotObservationTemporalRef(
        PilotObservationTemporalKind.INTERVENTION_EPISODE,
        "intervention_episode:bounded_b",
    )
    entry_a = _temporal_entry(candidate_a, a, temporal_a)
    entry_b = _temporal_entry(candidate_b, b, temporal_b)
    assert _validate((entry_b, entry_a), sg, sr, mg, mr, cg, cr) == (
        entry_a,
        entry_b,
    )


def test_empty_temporal_declarations_do_not_assert_absence(tmp_path) -> None:
    candidate_a, candidate_b, a, b, sg, sr, mg, mr, cg, cr = (
        _reviewed_coordination_basis(tmp_path)
    )
    entry_a = _temporal_entry(candidate_a, a)
    entry_b = _temporal_entry(candidate_b, b)
    assert entry_a.temporal_keys == ()
    assert entry_b.temporal_keys == ()
    assert _validate((entry_a, entry_b), sg, sr, mg, mr, cg, cr) == (
        entry_a,
        entry_b,
    )


def test_equal_capture_timestamps_are_not_implicitly_temporal_identity(tmp_path) -> None:
    candidate_a, candidate_b, a, b, sg, sr, mg, mr, cg, cr = (
        _reviewed_coordination_basis(tmp_path)
    )
    capture_a = a.mechanism_entry.upstream_lineage_entry.basis_entry.candidate
    capture_b = b.mechanism_entry.upstream_lineage_entry.basis_entry.candidate
    assert capture_a.proposed_at == capture_b.proposed_at
    assert _validate(
        (
            _temporal_entry(candidate_a, a),
            _temporal_entry(candidate_b, b),
        ),
        sg,
        sr,
        mg,
        mr,
        cg,
        cr,
    )


def test_prior_shared_coordination_rejects_before_distinct_temporal_can_help(
    tmp_path,
) -> None:
    candidate_a, candidate_b, a, b, sg, sr, mg, mr, cg, cr = (
        _reviewed_coordination_basis(tmp_path, shared_coordination=True)
    )
    temporal_a = PilotObservationTemporalRef(
        PilotObservationTemporalKind.INTERVENTION_EPISODE,
        "intervention_episode:distinct_a",
    )
    temporal_b = PilotObservationTemporalRef(
        PilotObservationTemporalKind.INTERVENTION_EPISODE,
        "intervention_episode:distinct_b",
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="share one exact declared cross-observation coordination/control authority",
    ):
        _validate(
            (
                _temporal_entry(candidate_a, a, temporal_a),
                _temporal_entry(candidate_b, b, temporal_b),
            ),
            sg,
            sr,
            mg,
            mr,
            cg,
            cr,
        )


def test_temporal_declaration_is_bound_to_exact_candidate(tmp_path) -> None:
    candidate_a, _candidate_b, _a, b, *_ = _reviewed_coordination_basis(tmp_path)
    declaration_a = build_pilot_materialization_temporal_declaration_v1(
        candidate_a,
        temporals=(
            PilotObservationTemporalRef(
                PilotObservationTemporalKind.CARRYOVER_STATE,
                "carryover_state:bound_to_candidate_a",
            ),
        ),
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="candidate_sha256 does not match exact basis candidate",
    ):
        PilotMaterializedEvidenceTemporalEntry(b, declaration_a)


def test_temporal_key_is_domain_separated_kind_sensitive_and_does_not_echo_ref() -> None:
    raw_ref = "shared:opaque_temporal_123"
    intervention = PilotObservationTemporalRef(
        PilotObservationTemporalKind.INTERVENTION_EPISODE,
        raw_ref,
    )
    adaptive = PilotObservationTemporalRef(
        PilotObservationTemporalKind.ADAPTIVE_STATE,
        raw_ref,
    )
    intervention_key = pilot_observation_temporal_dependence_key_v1(intervention)
    adaptive_key = pilot_observation_temporal_dependence_key_v1(adaptive)
    assert intervention_key.startswith("pilot_observation_temporal:")
    assert len(intervention_key.removeprefix("pilot_observation_temporal:")) == 64
    assert raw_ref not in intervention_key
    assert intervention_key != adaptive_key


def test_temporal_declaration_rejects_duplicate_exact_refs(tmp_path) -> None:
    candidate_a, *_ = _reviewed_coordination_basis(tmp_path)
    temporal = PilotObservationTemporalRef(
        PilotObservationTemporalKind.HISTORY_STATE,
        "history_state:duplicate_01",
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="must not repeat an exact temporal ref",
    ):
        build_pilot_materialization_temporal_declaration_v1(
            candidate_a,
            temporals=(temporal, temporal),
        )


def test_temporal_ref_requires_canonical_opaque_ascii_identifier() -> None:
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="canonical opaque ASCII identifier",
    ):
        PilotObservationTemporalRef(
            PilotObservationTemporalKind.OTHER,
            "temporal with spaces",
        )
