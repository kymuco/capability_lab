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
    PilotMaterializationUpstreamSourceDeclaration,
    PilotMaterializedEvidenceBasisEntry,
    PilotMaterializedEvidenceUpstreamLineageEntry,
    PilotUpstreamSourceKind,
    PilotUpstreamSourceRef,
    build_pilot_materialization_upstream_source_declaration_v1,
    initialize_private_workspace,
    pilot_evidence_materialization_candidate_sha256,
    pilot_upstream_source_dependence_key_v1,
    propose_pilot_capture_evidence_materialization_v1,
    record_text_capture,
    resolve_reviewed_pilot_evidence_materialization_v1,
    validate_pilot_materialized_evidence_cross_session_replication_preconditions_v1,
    validate_pilot_materialized_evidence_upstream_lineage_preconditions_v1,
)


T0 = datetime(2026, 1, 6, 12, 0, tzinfo=timezone.utc)


def _workspace(
    tmp_path,
    *,
    name: str,
    session_id: str,
    subject_ref: str,
    capture_id: str,
    probe_id: str,
    text: str,
):
    root = tmp_path / name
    initialize_private_workspace(
        root,
        session_id=session_id,
        subject_ref=CapabilitySubjectRef(subject_ref),
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
            "reviewer_upstream_01",
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


def _distinct_cross_session_probe_entries(tmp_path):
    root_a = _workspace(
        tmp_path,
        name="conceptual_session",
        session_id="session_upstream_a",
        subject_ref="subject_upstream_01",
        capture_id="conceptual_01",
        probe_id="conceptual_explanation",
        text="Synthetic conceptual observation.",
    )
    root_b = _workspace(
        tmp_path,
        name="calculation_session",
        session_id="session_upstream_b",
        subject_ref="subject_upstream_01",
        capture_id="calculation_01",
        probe_id="calculation_work",
        text="Synthetic calculation observation.",
    )
    candidate_a, evidence_a = _materialize(
        root_a,
        capture_id="conceptual_01",
        materialization_id="materialization_upstream_a",
        evidence_id="evidence_upstream_a",
        review_id="review_upstream_a",
    )
    candidate_b, evidence_b = _materialize(
        root_b,
        capture_id="calculation_01",
        materialization_id="materialization_upstream_b",
        evidence_id="evidence_upstream_b",
        review_id="review_upstream_b",
    )
    basis_a = PilotMaterializedEvidenceBasisEntry(candidate_a, evidence_a)
    basis_b = PilotMaterializedEvidenceBasisEntry(candidate_b, evidence_b)
    return (candidate_a, basis_a), (candidate_b, basis_b)


def test_shared_declared_reference_rejects_otherwise_distinct_cross_session_basis(
    tmp_path,
) -> None:
    (candidate_a, basis_a), (candidate_b, basis_b) = (
        _distinct_cross_session_probe_entries(tmp_path)
    )

    assert validate_pilot_materialized_evidence_cross_session_replication_preconditions_v1(
        (basis_a, basis_b)
    ) == (basis_a, basis_b)

    shared = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.REFERENCE,
        "reference:shared_electricity_note_v1",
    )
    entry_a = PilotMaterializedEvidenceUpstreamLineageEntry(
        basis_a,
        build_pilot_materialization_upstream_source_declaration_v1(
            candidate_a,
            sources=(shared,),
        ),
    )
    entry_b = PilotMaterializedEvidenceUpstreamLineageEntry(
        basis_b,
        build_pilot_materialization_upstream_source_declaration_v1(
            candidate_b,
            sources=(shared,),
        ),
    )

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="share one exact declared upstream source lineage",
    ):
        validate_pilot_materialized_evidence_upstream_lineage_preconditions_v1(
            (entry_a, entry_b)
        )


def test_distinct_declared_upstream_sources_clear_only_known_upstream_gate(
    tmp_path,
) -> None:
    (candidate_a, basis_a), (candidate_b, basis_b) = (
        _distinct_cross_session_probe_entries(tmp_path)
    )
    entry_a = PilotMaterializedEvidenceUpstreamLineageEntry(
        basis_a,
        build_pilot_materialization_upstream_source_declaration_v1(
            candidate_a,
            sources=(
                PilotUpstreamSourceRef(
                    PilotUpstreamSourceKind.REFERENCE,
                    "reference:source_a",
                ),
            ),
        ),
    )
    entry_b = PilotMaterializedEvidenceUpstreamLineageEntry(
        basis_b,
        build_pilot_materialization_upstream_source_declaration_v1(
            candidate_b,
            sources=(
                PilotUpstreamSourceRef(
                    PilotUpstreamSourceKind.REFERENCE,
                    "reference:source_b",
                ),
            ),
        ),
    )

    assert validate_pilot_materialized_evidence_upstream_lineage_preconditions_v1(
        (entry_b, entry_a)
    ) == (entry_a, entry_b)


def test_empty_declaration_is_allowed_but_does_not_assert_source_absence(tmp_path) -> None:
    (candidate_a, basis_a), (candidate_b, basis_b) = (
        _distinct_cross_session_probe_entries(tmp_path)
    )
    entry_a = PilotMaterializedEvidenceUpstreamLineageEntry(
        basis_a,
        build_pilot_materialization_upstream_source_declaration_v1(candidate_a),
    )
    entry_b = PilotMaterializedEvidenceUpstreamLineageEntry(
        basis_b,
        build_pilot_materialization_upstream_source_declaration_v1(candidate_b),
    )

    assert entry_a.upstream_source_keys == ()
    assert entry_b.upstream_source_keys == ()
    assert validate_pilot_materialized_evidence_upstream_lineage_preconditions_v1(
        (entry_a, entry_b)
    ) == (entry_a, entry_b)


def test_upstream_declaration_is_bound_to_exact_candidate(tmp_path) -> None:
    (candidate_a, basis_a), (candidate_b, basis_b) = (
        _distinct_cross_session_probe_entries(tmp_path)
    )
    declaration_a = build_pilot_materialization_upstream_source_declaration_v1(
        candidate_a,
        sources=(
            PilotUpstreamSourceRef(
                PilotUpstreamSourceKind.ARTIFACT,
                "artifact:shared_fixture_v1",
            ),
        ),
    )

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="candidate_sha256 does not match exact basis candidate",
    ):
        PilotMaterializedEvidenceUpstreamLineageEntry(
            basis_b,
            declaration_a,
        )

    assert declaration_a.candidate_sha256 == (
        pilot_evidence_materialization_candidate_sha256(candidate_a)
    )
    assert declaration_a.candidate_sha256 != (
        pilot_evidence_materialization_candidate_sha256(candidate_b)
    )


def test_upstream_source_key_is_domain_separated_and_kind_sensitive() -> None:
    raw_ref = "model_output:private_run_123"
    model_source = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.MODEL_OUTPUT,
        raw_ref,
    )
    tool_source = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.TOOL_OUTPUT,
        raw_ref,
    )

    model_key = pilot_upstream_source_dependence_key_v1(model_source)
    tool_key = pilot_upstream_source_dependence_key_v1(tool_source)

    assert model_key.startswith("pilot_upstream_source:")
    assert len(model_key.removeprefix("pilot_upstream_source:")) == 64
    assert raw_ref not in model_key
    assert model_key != tool_key


def test_upstream_declaration_rejects_duplicate_exact_source_refs(tmp_path) -> None:
    (candidate_a, _basis_a), _ = _distinct_cross_session_probe_entries(tmp_path)
    source = PilotUpstreamSourceRef(
        PilotUpstreamSourceKind.EXTERNAL_RECORD,
        "external_record:shared_01",
    )

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="must not repeat an exact source ref",
    ):
        PilotMaterializationUpstreamSourceDeclaration(
            candidate_sha256=pilot_evidence_materialization_candidate_sha256(
                candidate_a
            ),
            sources=(source, source),
        )


def test_upstream_source_ref_requires_canonical_opaque_ascii_identifier() -> None:
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="canonical opaque ASCII identifier",
    ):
        PilotUpstreamSourceRef(
            PilotUpstreamSourceKind.REFERENCE,
            "https://example.com/reference with spaces",
        )
