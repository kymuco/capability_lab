from dataclasses import replace
from datetime import datetime, timedelta, timezone
import inspect
import json

import pytest

import capability_lab.epistemics.claim_evidence_disposition_coverage as coverage_module
from capability_lab.epistemics import (
    ActorRef,
    CapabilityClaim,
    CapabilityClaimId,
    CapabilitySubjectRef,
    ClaimEvaluation,
    ClaimEvaluationId,
    ClaimEvidenceDispositionCoverageReceipt,
    ClaimScope,
    ConflictStatus,
    CoverageAssessment,
    CoverageStatus,
    EpistemicRecordSet,
    EvaluationConclusion,
    EvaluationPolicyRef,
    EvaluatorKind,
    EvaluatorRef,
    EvidenceAssessment,
    EvidenceBearing,
    EvidenceContext,
    EvidenceId,
    EvidenceKind,
    EvidenceRecord,
    EvidenceReliability,
    InvalidClaimEvidenceDispositionCoverage,
    ProvenanceSource,
    ProvenanceSourceKind,
    ProvenanceTrail,
    build_claim_evidence_disposition_coverage_v1,
    claim_evidence_disposition_coverage_receipt_from_dict,
    claim_evidence_disposition_coverage_receipt_from_json,
    validate_complete_claim_evidence_disposition_coverage_v1,
)
from capability_lab.semantics import CapabilityConceptRef, CapabilityId


def _time(hour: int) -> datetime:
    return datetime(2026, 9, 1, hour, 0, tzinfo=timezone.utc)


def _subject(value: str = "subject_1") -> CapabilitySubjectRef:
    return CapabilitySubjectRef(value)


def _concept(revision: int = 1) -> CapabilityConceptRef:
    return CapabilityConceptRef(CapabilityId.parse("research:signal_reasoning"), revision)


def _provenance(ref: str = "source_1") -> ProvenanceTrail:
    return ProvenanceTrail(
        sources=(ProvenanceSource(ProvenanceSourceKind.SYSTEM, ref),)
    )


def _claim(
    *,
    claim_id: str = "claim_1",
    subject: str = "subject_1",
    created_hour: int = 12,
) -> CapabilityClaim:
    return CapabilityClaim(
        claim_id=CapabilityClaimId(claim_id),
        subject_ref=_subject(subject),
        concept_ref=_concept(),
        statement="The subject can reason about bounded signal evidence.",
        scope=ClaimScope("Bounded signal reasoning.", ("bounded_reasoning",)),
        created_at=_time(created_hour),
        provenance=_provenance("claim_source"),
    )


def _evidence(
    evidence_id: str,
    *,
    subject: str = "subject_1",
    observed_hour: int = 10,
    recorded_hour: int = 11,
) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=EvidenceId(evidence_id),
        subject_ref=_subject(subject),
        kind=EvidenceKind.ARTIFACT,
        summary=f"Evidence {evidence_id}.",
        context=EvidenceContext("Generic context.", ("generic",)),
        observed_at=_time(observed_hour),
        recorded_at=_time(recorded_hour),
        provenance=_provenance(f"source_{evidence_id}"),
        payload_refs=(f"payload_{evidence_id}",),
    )


def _assessment(
    evidence_id: str,
    *,
    bearing: EvidenceBearing = EvidenceBearing.SUPPORTS,
    reliability: EvidenceReliability = EvidenceReliability.UNASSESSED,
) -> EvidenceAssessment:
    return EvidenceAssessment(
        evidence_id=EvidenceId(evidence_id),
        bearing=bearing,
        reliability=reliability,
        coverage_note=f"coverage {evidence_id}",
        rationale=f"rationale {evidence_id}",
    )


def _basis(
    *,
    evidence=(),
    evaluations=(),
    claim: CapabilityClaim | None = None,
) -> tuple[EpistemicRecordSet, CapabilityClaim]:
    target = claim or _claim()
    return (
        EpistemicRecordSet(
            evidence_records=tuple(evidence),
            claims=(target,),
            evaluations=tuple(evaluations),
        ),
        target,
    )


def _build(
    records: EpistemicRecordSet,
    claim: CapabilityClaim,
    dispositions: tuple[EvidenceAssessment, ...],
    *,
    hour: int = 14,
):
    return build_claim_evidence_disposition_coverage_v1(
        records=records,
        claim_id=claim.claim_id,
        as_of=_time(hour),
        dispositions=dispositions,
    )


def _evaluation(
    claim: CapabilityClaim,
    assessments: tuple[EvidenceAssessment, ...],
    *,
    evaluation_id: str = "evaluation_1",
    conclusion: EvaluationConclusion = EvaluationConclusion.SUPPORTED,
    conflict_status: ConflictStatus = ConflictStatus.NONE,
) -> ClaimEvaluation:
    return ClaimEvaluation(
        evaluation_id=ClaimEvaluationId(evaluation_id),
        claim_id=claim.claim_id,
        policy_ref=EvaluationPolicyRef("generic", "human_evidence", 1),
        evaluator_ref=EvaluatorRef(EvaluatorKind.HUMAN, "reviewer_1"),
        evaluated_at=_time(14),
        evidence_assessments=assessments,
        coverage=CoverageAssessment(CoverageStatus.PARTIAL, "Partial human assessment."),
        conflict_status=conflict_status,
        conclusion=conclusion,
        rationale="Conservative human evidence-level evaluation.",
    )


def test_empty_candidate_portfolio_requires_and_accepts_empty_dispositions():
    records, claim = _basis()
    coverage = _build(records, claim, ())
    assert coverage.dispositions == ()
    assert validate_complete_claim_evidence_disposition_coverage_v1(
        records=records,
        claim_id=claim.claim_id,
        as_of=_time(14),
        coverage=coverage,
    ) == coverage


def test_one_candidate_one_explicit_disposition_succeeds():
    records, claim = _basis(evidence=(_evidence("evidence_1"),))
    coverage = _build(records, claim, (_assessment("evidence_1"),))
    assert tuple(item.evidence_id for item in coverage.dispositions) == (
        EvidenceId("evidence_1"),
    )


def test_all_four_bearings_count_as_explicit_coverage():
    ids_and_bearings = (
        ("a_support", EvidenceBearing.SUPPORTS),
        ("b_contradict", EvidenceBearing.CONTRADICTS),
        ("c_indeterminate", EvidenceBearing.INDETERMINATE),
        ("d_not_relevant", EvidenceBearing.NOT_RELEVANT),
    )
    records, claim = _basis(
        evidence=tuple(_evidence(evidence_id) for evidence_id, _ in ids_and_bearings)
    )
    coverage = _build(
        records,
        claim,
        tuple(
            _assessment(evidence_id, bearing=bearing)
            for evidence_id, bearing in reversed(ids_and_bearings)
        ),
    )
    assert tuple(item.bearing for item in coverage.dispositions) == tuple(
        bearing for _, bearing in ids_and_bearings
    )


def test_explicit_not_relevant_succeeds_where_silent_omission_fails():
    records, claim = _basis(
        evidence=(_evidence("evidence_1"), _evidence("evidence_2"))
    )
    with pytest.raises(
        InvalidClaimEvidenceDispositionCoverage,
        match="omits candidate evidence",
    ):
        _build(records, claim, (_assessment("evidence_1"),))
    coverage = _build(
        records,
        claim,
        (
            _assessment("evidence_1"),
            _assessment("evidence_2", bearing=EvidenceBearing.NOT_RELEVANT),
        ),
    )
    assert len(coverage.dispositions) == 2


def test_only_favorable_supporting_subset_is_rejected():
    records, claim = _basis(
        evidence=(_evidence("favorable"), _evidence("inconvenient"))
    )
    with pytest.raises(InvalidClaimEvidenceDispositionCoverage, match="omits"):
        _build(records, claim, (_assessment("favorable"),))


def test_only_contradictory_subset_is_rejected():
    records, claim = _basis(
        evidence=(_evidence("contradictory"), _evidence("other"))
    )
    with pytest.raises(InvalidClaimEvidenceDispositionCoverage, match="omits"):
        _build(
            records,
            claim,
            (
                _assessment(
                    "contradictory",
                    bearing=EvidenceBearing.CONTRADICTS,
                ),
            ),
        )


def test_extra_other_subject_evidence_disposition_is_rejected():
    records, claim = _basis(
        evidence=(
            _evidence("candidate"),
            _evidence("other_subject", subject="subject_2"),
        )
    )
    with pytest.raises(InvalidClaimEvidenceDispositionCoverage, match="non-candidate"):
        _build(
            records,
            claim,
            (_assessment("candidate"), _assessment("other_subject")),
        )


def test_future_evidence_disposition_is_rejected_until_it_becomes_candidate():
    records, claim = _basis(
        evidence=(
            _evidence("now", recorded_hour=13),
            _evidence("future", observed_hour=10, recorded_hour=16),
        )
    )
    with pytest.raises(InvalidClaimEvidenceDispositionCoverage, match="non-candidate"):
        _build(
            records,
            claim,
            (_assessment("now"), _assessment("future")),
            hour=14,
        )
    later = _build(
        records,
        claim,
        (_assessment("now"), _assessment("future")),
        hour=16,
    )
    assert tuple(item.evidence_id for item in later.dispositions) == (
        EvidenceId("future"),
        EvidenceId("now"),
    )


def test_evidence_absent_from_snapshot_is_rejected():
    records, claim = _basis(evidence=(_evidence("candidate"),))
    with pytest.raises(InvalidClaimEvidenceDispositionCoverage, match="non-candidate"):
        _build(
            records,
            claim,
            (_assessment("candidate"), _assessment("missing")),
        )


def test_duplicate_disposition_for_same_evidence_is_rejected():
    records, claim = _basis(evidence=(_evidence("candidate"),))
    with pytest.raises(InvalidClaimEvidenceDispositionCoverage, match="exactly one"):
        _build(
            records,
            claim,
            (_assessment("candidate"), _assessment("candidate")),
        )


def test_conflicting_duplicate_dispositions_are_rejected_not_latest_wins():
    records, claim = _basis(evidence=(_evidence("candidate"),))
    with pytest.raises(InvalidClaimEvidenceDispositionCoverage, match="exactly one"):
        _build(
            records,
            claim,
            (
                _assessment("candidate", bearing=EvidenceBearing.SUPPORTS),
                _assessment("candidate", bearing=EvidenceBearing.CONTRADICTS),
            ),
        )


def test_dispositions_are_canonically_ordered_by_evidence_id():
    records, claim = _basis(
        evidence=(_evidence("z_evidence"), _evidence("a_evidence"))
    )
    coverage = _build(
        records,
        claim,
        (_assessment("z_evidence"), _assessment("a_evidence")),
    )
    assert tuple(item.evidence_id for item in coverage.dispositions) == (
        EvidenceId("a_evidence"),
        EvidenceId("z_evidence"),
    )


def test_candidate_portfolio_digest_binds_full_pr12_8_content():
    records, claim = _basis(
        evidence=(
            _evidence("candidate", recorded_hour=13),
            _evidence("future", observed_hour=10, recorded_hour=16),
        )
    )
    coverage = _build(records, claim, (_assessment("candidate"),), hour=14)
    assert len(coverage.candidate_portfolio_sha256) == 64
    changed = _build(
        records,
        claim,
        (_assessment("candidate"), _assessment("future")),
        hour=16,
    )
    assert changed.candidate_portfolio_sha256 != coverage.candidate_portfolio_sha256


def test_stale_coverage_fails_after_unrelated_snapshot_append():
    records, claim = _basis(evidence=(_evidence("candidate"),))
    coverage = _build(records, claim, (_assessment("candidate"),))
    changed = EpistemicRecordSet(
        evidence_records=records.evidence_records
        + (_evidence("other_subject", subject="subject_2"),),
        claims=records.claims,
    )
    with pytest.raises(InvalidClaimEvidenceDispositionCoverage, match="coverage content"):
        validate_complete_claim_evidence_disposition_coverage_v1(
            records=changed,
            claim_id=claim.claim_id,
            as_of=_time(14),
            coverage=coverage,
        )


def test_historical_backfill_becomes_new_mandatory_disposition():
    records, claim = _basis(evidence=(_evidence("old_candidate"),))
    coverage = _build(records, claim, (_assessment("old_candidate"),))
    changed = EpistemicRecordSet(
        evidence_records=records.evidence_records
        + (_evidence("backfilled", observed_hour=9, recorded_hour=10),),
        claims=records.claims,
    )
    with pytest.raises(InvalidClaimEvidenceDispositionCoverage, match="omits"):
        validate_complete_claim_evidence_disposition_coverage_v1(
            records=changed,
            claim_id=claim.claim_id,
            as_of=_time(14),
            coverage=coverage,
        )


def test_changed_as_of_invalidates_stale_coverage():
    records, claim = _basis(
        evidence=(
            _evidence("now", recorded_hour=13),
            _evidence("later", observed_hour=10, recorded_hour=15),
        )
    )
    coverage = _build(records, claim, (_assessment("now"),), hour=14)
    with pytest.raises(InvalidClaimEvidenceDispositionCoverage):
        validate_complete_claim_evidence_disposition_coverage_v1(
            records=records,
            claim_id=claim.claim_id,
            as_of=_time(15),
            coverage=coverage,
        )


def test_changed_target_claim_is_rejected():
    records, claim = _basis(evidence=(_evidence("candidate"),))
    coverage = _build(records, claim, (_assessment("candidate"),))
    other_claim = _claim(claim_id="claim_2")
    changed = EpistemicRecordSet(
        evidence_records=records.evidence_records,
        claims=(other_claim,),
    )
    with pytest.raises(InvalidClaimEvidenceDispositionCoverage):
        validate_complete_claim_evidence_disposition_coverage_v1(
            records=changed,
            claim_id=other_claim.claim_id,
            as_of=_time(14),
            coverage=coverage,
        )


def test_pre_claim_evidence_included_by_pr12_8_is_still_mandatory():
    claim = _claim(created_hour=12)
    records, claim = _basis(
        claim=claim,
        evidence=(_evidence("pre_claim", observed_hour=9, recorded_hour=10),),
    )
    with pytest.raises(InvalidClaimEvidenceDispositionCoverage, match="omits"):
        _build(records, claim, ())
    assert _build(records, claim, (_assessment("pre_claim"),)).dispositions


def test_partial_existing_claim_evaluation_is_not_completeness_authority():
    claim = _claim()
    evidence = (_evidence("evidence_1"), _evidence("evidence_2"))
    partial = _evaluation(claim, (_assessment("evidence_1"),))
    records, claim = _basis(
        claim=claim,
        evidence=evidence,
        evaluations=(partial,),
    )
    with pytest.raises(InvalidClaimEvidenceDispositionCoverage, match="omits"):
        _build(records, claim, partial.evidence_assessments)


def test_complete_existing_assessment_tuple_passes_only_via_pr12_8_replay():
    claim = _claim()
    evidence = (_evidence("evidence_1"), _evidence("evidence_2"))
    full_assessments = (
        _assessment("evidence_1", bearing=EvidenceBearing.SUPPORTS),
        _assessment("evidence_2", bearing=EvidenceBearing.NOT_RELEVANT),
    )
    evaluation = _evaluation(claim, full_assessments)
    records, claim = _basis(
        claim=claim,
        evidence=evidence,
        evaluations=(evaluation,),
    )
    coverage = _build(records, claim, evaluation.evidence_assessments)
    assert len(coverage.dispositions) == 2


def test_claim_evaluation_conclusion_is_not_part_of_coverage_artifact():
    source = inspect.getsource(coverage_module)
    assert "ClaimEvaluation" not in source
    assert ".evaluations" not in source
    assert "EvaluationConclusion" not in source


def test_reliability_never_filters_candidate_coverage():
    records, claim = _basis(
        evidence=(
            _evidence("unassessed"),
            _evidence("low"),
            _evidence("high"),
        )
    )
    coverage = _build(
        records,
        claim,
        (
            _assessment("unassessed", reliability=EvidenceReliability.UNASSESSED),
            _assessment("low", reliability=EvidenceReliability.LOW),
            _assessment("high", reliability=EvidenceReliability.HIGH),
        ),
    )
    assert len(coverage.dispositions) == 3


def test_json_round_trip_is_data_only_and_requires_revalidation():
    records, claim = _basis(evidence=(_evidence("candidate"),))
    coverage = _build(records, claim, (_assessment("candidate"),))
    restored = claim_evidence_disposition_coverage_receipt_from_json(
        coverage.to_json()
    )
    assert restored == coverage
    assert restored is not coverage
    assert validate_complete_claim_evidence_disposition_coverage_v1(
        records=records,
        claim_id=claim.claim_id,
        as_of=_time(14),
        coverage=restored,
    ) == restored


def test_equal_distinct_caller_created_coverage_is_safe():
    records, claim = _basis(evidence=(_evidence("candidate"),))
    coverage = _build(records, claim, (_assessment("candidate"),))
    copy = ClaimEvidenceDispositionCoverageReceipt.from_dict(coverage.to_dict())
    assert copy == coverage and copy is not coverage
    assert validate_complete_claim_evidence_disposition_coverage_v1(
        records=records,
        claim_id=claim.claim_id,
        as_of=_time(14),
        coverage=copy,
    ) == copy


def test_dataclasses_replace_omission_fails():
    records, claim = _basis(
        evidence=(_evidence("evidence_1"), _evidence("evidence_2"))
    )
    coverage = _build(
        records,
        claim,
        (_assessment("evidence_1"), _assessment("evidence_2")),
    )
    subset = replace(
        coverage,
        dispositions=(_assessment("evidence_1"),),
    )
    with pytest.raises(InvalidClaimEvidenceDispositionCoverage, match="omits"):
        validate_complete_claim_evidence_disposition_coverage_v1(
            records=records,
            claim_id=claim.claim_id,
            as_of=_time(14),
            coverage=subset,
        )


def test_dataclasses_replace_extra_disposition_fails():
    records, claim = _basis(evidence=(_evidence("evidence_1"),))
    coverage = _build(records, claim, (_assessment("evidence_1"),))
    widened = replace(
        coverage,
        dispositions=(
            _assessment("evidence_1"),
            _assessment("not_candidate"),
        ),
    )
    with pytest.raises(InvalidClaimEvidenceDispositionCoverage, match="non-candidate"):
        validate_complete_claim_evidence_disposition_coverage_v1(
            records=records,
            claim_id=claim.claim_id,
            as_of=_time(14),
            coverage=widened,
        )


def test_post_construction_coverage_corruption_fails_closed():
    records, claim = _basis(evidence=(_evidence("candidate"),))
    coverage = _build(records, claim, (_assessment("candidate"),))
    object.__setattr__(coverage, "candidate_portfolio_sha256", "0" * 64)
    with pytest.raises(InvalidClaimEvidenceDispositionCoverage, match="coverage content"):
        validate_complete_claim_evidence_disposition_coverage_v1(
            records=records,
            claim_id=claim.claim_id,
            as_of=_time(14),
            coverage=coverage,
        )


def test_post_construction_assessment_corruption_fails_closed():
    records, claim = _basis(evidence=(_evidence("candidate"),))
    assessment = _assessment("candidate")
    coverage = _build(records, claim, (assessment,))
    object.__setattr__(assessment, "bearing", "supports")
    with pytest.raises(InvalidClaimEvidenceDispositionCoverage, match="EvidenceBearing"):
        validate_complete_claim_evidence_disposition_coverage_v1(
            records=records,
            claim_id=claim.claim_id,
            as_of=_time(14),
            coverage=coverage,
        )


def test_behavioral_evidence_id_subclass_fails_exact_type_boundary():
    class EvilEvidenceId(EvidenceId):
        pass

    records, claim = _basis(evidence=(_evidence("candidate"),))
    evil = EvidenceAssessment(
        evidence_id=EvilEvidenceId("candidate"),
        bearing=EvidenceBearing.SUPPORTS,
        reliability=EvidenceReliability.UNASSESSED,
        coverage_note="coverage",
        rationale="rationale",
    )
    with pytest.raises(InvalidClaimEvidenceDispositionCoverage, match="exact EvidenceId"):
        _build(records, claim, (evil,))


def test_non_tuple_disposition_container_fails_exact_boundary():
    records, claim = _basis(evidence=(_evidence("candidate"),))
    with pytest.raises(InvalidClaimEvidenceDispositionCoverage, match="exact tuple"):
        build_claim_evidence_disposition_coverage_v1(
            records=records,
            claim_id=claim.claim_id,
            as_of=_time(14),
            dispositions=[_assessment("candidate")],  # type: ignore[arg-type]
        )


def test_noncanonical_stored_as_of_corruption_fails():
    records, claim = _basis(evidence=(_evidence("candidate"),))
    coverage = _build(records, claim, (_assessment("candidate"),))
    object.__setattr__(
        coverage,
        "as_of",
        datetime(2026, 9, 1, 15, 0, tzinfo=timezone(timedelta(hours=1))),
    )
    with pytest.raises(InvalidClaimEvidenceDispositionCoverage, match="canonical UTC"):
        validate_complete_claim_evidence_disposition_coverage_v1(
            records=records,
            claim_id=claim.claim_id,
            as_of=_time(14),
            coverage=coverage,
        )


def test_json_unknown_missing_duplicate_and_noncanonical_fields_fail():
    records, claim = _basis(
        evidence=(_evidence("a_candidate"), _evidence("z_candidate"))
    )
    coverage = _build(
        records,
        claim,
        (_assessment("a_candidate"), _assessment("z_candidate")),
    )
    payload = coverage.to_dict()

    unknown = dict(payload)
    unknown["unknown"] = "x"
    with pytest.raises(InvalidClaimEvidenceDispositionCoverage, match="unknown"):
        claim_evidence_disposition_coverage_receipt_from_dict(unknown)

    missing = dict(payload)
    missing.pop("claim_id")
    with pytest.raises(InvalidClaimEvidenceDispositionCoverage, match="missing"):
        claim_evidence_disposition_coverage_receipt_from_dict(missing)

    noncanonical = dict(payload)
    noncanonical["dispositions"] = list(reversed(payload["dispositions"]))
    with pytest.raises(InvalidClaimEvidenceDispositionCoverage, match="canonical"):
        claim_evidence_disposition_coverage_receipt_from_dict(noncanonical)

    duplicate_json = coverage.to_json().replace(
        '"claim_id":"claim_1"',
        '"claim_id":"claim_1","claim_id":"claim_1"',
        1,
    )
    with pytest.raises(InvalidClaimEvidenceDispositionCoverage, match="duplicate"):
        claim_evidence_disposition_coverage_receipt_from_json(duplicate_json)


def test_json_nan_and_non_string_python_dict_keys_fail():
    records, claim = _basis(evidence=(_evidence("candidate"),))
    coverage = _build(records, claim, (_assessment("candidate"),))
    bad_json = coverage.to_json().replace(
        '"coverage_note":"coverage candidate"',
        '"coverage_note":NaN',
        1,
    )
    with pytest.raises(InvalidClaimEvidenceDispositionCoverage, match="non-standard"):
        claim_evidence_disposition_coverage_receipt_from_json(bad_json)

    payload = coverage.to_dict()
    payload[1] = "bad"  # type: ignore[index]
    with pytest.raises(InvalidClaimEvidenceDispositionCoverage, match="exact strings"):
        claim_evidence_disposition_coverage_receipt_from_dict(payload)


def test_import_surface_contains_no_policy_pilot_state_or_progression_authority():
    source = inspect.getsource(coverage_module)
    forbidden = (
        "evaluation_policy",
        "capability_lab.interpretation",
        "pilot",
        "PersonalCapabilityState",
        "progression",
        "presentation",
        "admit_",
        "runtime authority",
    )
    for term in forbidden:
        assert term not in source


def test_production_path_contains_no_latest_wins_or_history_scan():
    source = inspect.getsource(coverage_module)
    assert "latest" not in source.lower()
    assert ".evaluations" not in source
    assert "evaluated_at" not in source


def test_receipt_dict_is_deterministic_and_schema_v1():
    records, claim = _basis(evidence=(_evidence("candidate"),))
    coverage = _build(records, claim, (_assessment("candidate"),))
    assert coverage.to_dict()["schema_version"] == 1
    assert coverage.to_json() == coverage.to_json()
    assert json.loads(coverage.to_json())["candidate_portfolio_sha256"] == (
        coverage.candidate_portfolio_sha256
    )
