from datetime import datetime, timezone
import json

import pytest

from capability_lab.epistemics import CapabilitySubjectRef, EvidenceId
from capability_lab.pilots.civilization_bootstrap_01 import (
    MATERIALIZATION_CANDIDATE_SCHEMA,
    MATERIALIZATION_REVIEW_SCHEMA,
    REVIEWED_PILOT_CAPTURE_TO_EVIDENCE_POLICY_V1,
    PilotCaptureKind,
    PilotEvidenceMaterializationCandidate,
    PilotEvidenceMaterializationId,
    PilotEvidenceMaterializationReview,
    PilotEvidenceMaterializationReviewId,
    PilotEvidenceMaterializationReviewerKind,
    PilotEvidenceMaterializationReviewerRef,
    PilotEvidenceMaterializationSerializationError,
    PilotEvidenceMaterializationVerdict,
    PilotProtocolRef,
    materialization_candidate_from_json,
    materialization_candidate_to_json,
    materialization_review_from_json,
    materialization_review_to_json,
    pilot_evidence_materialization_candidate_sha256,
)


T0 = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


def _candidate() -> PilotEvidenceMaterializationCandidate:
    return PilotEvidenceMaterializationCandidate(
        materialization_id=PilotEvidenceMaterializationId("materialization_01"),
        policy_ref=REVIEWED_PILOT_CAPTURE_TO_EVIDENCE_POLICY_V1,
        protocol_ref=PilotProtocolRef.parse(
            "civilization_bootstrap:pilot_01_basic_electricity@1"
        ),
        session_id="session_01",
        subject_ref=CapabilitySubjectRef("subject_01"),
        capture_id="conceptual_01",
        probe_id="conceptual_explanation",
        capture_kind=PilotCaptureKind.TEXT_RESPONSE,
        source_snapshot_sha256="a" * 64,
        source_capture_sha256="b" * 64,
        proposed_evidence_id=EvidenceId("evidence_01"),
        proposed_at=T0,
    )


def _review() -> PilotEvidenceMaterializationReview:
    candidate = _candidate()
    return PilotEvidenceMaterializationReview(
        review_id=PilotEvidenceMaterializationReviewId("review_01"),
        materialization_id=candidate.materialization_id,
        candidate_sha256=pilot_evidence_materialization_candidate_sha256(candidate),
        policy_ref=REVIEWED_PILOT_CAPTURE_TO_EVIDENCE_POLICY_V1,
        reviewer_ref=PilotEvidenceMaterializationReviewerRef(
            PilotEvidenceMaterializationReviewerKind.HUMAN,
            "reviewer_01",
        ),
        verdict=PilotEvidenceMaterializationVerdict.MATERIALIZE,
        reviewed_at=T0,
        rationale="Bounded source materialization only.",
    )


def test_candidate_and_review_roundtrip_deterministically() -> None:
    candidate_json = materialization_candidate_to_json(_candidate())
    review_json = materialization_review_to_json(_review())

    assert materialization_candidate_from_json(candidate_json) == _candidate()
    assert materialization_review_from_json(review_json) == _review()
    assert (
        materialization_candidate_to_json(
            materialization_candidate_from_json(candidate_json)
        )
        == candidate_json
    )
    assert (
        materialization_review_to_json(materialization_review_from_json(review_json))
        == review_json
    )
    assert candidate_json.endswith("\n")
    assert review_json.endswith("\n")
    assert json.loads(candidate_json)["schema"] == MATERIALIZATION_CANDIDATE_SCHEMA
    assert json.loads(review_json)["schema"] == MATERIALIZATION_REVIEW_SCHEMA
    assert json.loads(candidate_json)["subject_ref"] == "subject_01"
    assert json.loads(review_json)["candidate_sha256"] == (
        pilot_evidence_materialization_candidate_sha256(_candidate())
    )


def test_unknown_fields_and_duplicate_json_keys_are_rejected() -> None:
    candidate = json.loads(materialization_candidate_to_json(_candidate()))
    candidate["surprise"] = "hidden authority"
    with pytest.raises(
        PilotEvidenceMaterializationSerializationError,
        match="unknown fields",
    ):
        materialization_candidate_from_json(json.dumps(candidate))

    raw = materialization_review_to_json(_review()).rstrip("\n")
    duplicate = raw[:-1] + ',"rationale":"duplicate"}'
    with pytest.raises(
        PilotEvidenceMaterializationSerializationError,
        match="duplicate JSON key",
    ):
        materialization_review_from_json(duplicate)


def test_boolean_schema_version_and_noncanonical_timestamps_are_rejected() -> None:
    candidate = json.loads(materialization_candidate_to_json(_candidate()))
    candidate["schema_version"] = True
    with pytest.raises(
        PilotEvidenceMaterializationSerializationError,
        match="integer 1",
    ):
        materialization_candidate_from_json(json.dumps(candidate))

    review = json.loads(materialization_review_to_json(_review()))
    review["reviewed_at"] = "20260101T120000Z"
    with pytest.raises(
        PilotEvidenceMaterializationSerializationError,
        match="extended ISO-8601",
    ):
        materialization_review_from_json(json.dumps(review))


def test_review_candidate_binding_digest_is_required_and_strict() -> None:
    review = json.loads(materialization_review_to_json(_review()))
    review.pop("candidate_sha256")
    with pytest.raises(
        PilotEvidenceMaterializationSerializationError,
        match="missing fields",
    ):
        materialization_review_from_json(json.dumps(review))

    review = json.loads(materialization_review_to_json(_review()))
    review["candidate_sha256"] = "not-a-digest"
    with pytest.raises(
        PilotEvidenceMaterializationSerializationError,
        match="candidate_sha256 must be a lowercase 64-character sha256 digest",
    ):
        materialization_review_from_json(json.dumps(review))


def test_model_reviewer_cannot_be_smuggled_through_serialization() -> None:
    review = json.loads(materialization_review_to_json(_review()))
    review["reviewer_kind"] = "MODEL"
    with pytest.raises(
        PilotEvidenceMaterializationSerializationError,
        match="invalid materialization reviewer_kind",
    ):
        materialization_review_from_json(json.dumps(review))


def test_serialized_candidate_cannot_relabel_frozen_materialization_policy() -> None:
    candidate = json.loads(materialization_candidate_to_json(_candidate()))
    candidate["policy_ref"] = "capability_lab:other_policy@1"
    with pytest.raises(
        PilotEvidenceMaterializationSerializationError,
        match="frozen reviewed materialization policy",
    ):
        materialization_candidate_from_json(json.dumps(candidate))
