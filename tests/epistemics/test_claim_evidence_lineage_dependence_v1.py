from dataclasses import replace
from datetime import datetime, timezone
import ast
import inspect
import json

import pytest

import capability_lab.epistemics.claim_evidence_lineage_dependence as lineage_module
from capability_lab.epistemics import (
    CapabilityClaim,
    CapabilityClaimId,
    CapabilitySubjectRef,
    ClaimEvidenceLineageDependenceReceipt,
    ClaimScope,
    EpistemicRecordSet,
    EvidenceAssessment,
    EvidenceBearing,
    EvidenceContext,
    EvidenceId,
    EvidenceKind,
    EvidenceLineageProfile,
    EvidenceLineageRelation,
    EvidenceOutcome,
    EvidenceOutcomeStatus,
    EvidenceRecord,
    EvidenceReliability,
    InvalidClaimEvidenceLineageDependence,
    ProvenanceSource,
    ProvenanceSourceKind,
    ProvenanceTrail,
    build_claim_evidence_disposition_coverage_v1,
    build_claim_evidence_lineage_dependence_v1,
    claim_evidence_lineage_dependence_receipt_from_dict,
    claim_evidence_lineage_dependence_receipt_from_json,
    claim_evidence_lineage_dependence_receipt_to_dict,
    claim_evidence_lineage_dependence_receipt_to_json,
    resolve_claim_evidence_pair_lineage_relation_v1,
    validate_claim_evidence_lineage_dependence_v1,
)
from capability_lab.semantics import CapabilityConceptRef, CapabilityId


def _time(hour: int) -> datetime:
    return datetime(2026, 9, 1, hour, 0, tzinfo=timezone.utc)


def _subject(value: str = "subject_1") -> CapabilitySubjectRef:
    return CapabilitySubjectRef(value)


def _concept() -> CapabilityConceptRef:
    return CapabilityConceptRef(CapabilityId.parse("research:lineage_reasoning"), 1)


def _source(kind: ProvenanceSourceKind, ref: str) -> ProvenanceSource:
    return ProvenanceSource(kind, ref)


def _claim(
    *, claim_id: str = "claim_1", subject: str = "subject_1", created_hour: int = 9
) -> CapabilityClaim:
    return CapabilityClaim(
        claim_id=CapabilityClaimId(claim_id),
        subject_ref=_subject(subject),
        concept_ref=_concept(),
        statement="The subject can reason from a bounded body of evidence.",
        scope=ClaimScope("Bounded lineage reasoning.", ("lineage_reasoning",)),
        created_at=_time(created_hour),
        provenance=ProvenanceTrail(
            sources=(_source(ProvenanceSourceKind.SYSTEM, "claim_system"),)
        ),
    )


def _evidence(
    evidence_id: str,
    *,
    subject: str = "subject_1",
    kind: EvidenceKind = EvidenceKind.ARTIFACT,
    sources: tuple[ProvenanceSource, ...] | None = None,
    observed_hour: int = 10,
    recorded_hour: int = 11,
    observation_started_hour: int | None = None,
    payload_refs: tuple[str, ...] = (),
    outcome: EvidenceOutcome | None = None,
) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=EvidenceId(evidence_id),
        subject_ref=_subject(subject),
        kind=kind,
        summary=f"Evidence {evidence_id}.",
        context=EvidenceContext("Generic context.", ("generic",)),
        observed_at=_time(observed_hour),
        recorded_at=_time(recorded_hour),
        observation_started_at=(
            _time(observation_started_hour)
            if observation_started_hour is not None
            else None
        ),
        provenance=ProvenanceTrail(
            sources=sources
            or (_source(ProvenanceSourceKind.SYSTEM, f"system_{evidence_id}"),)
        ),
        outcome=outcome,
        payload_refs=payload_refs,
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
    evidence: tuple[EvidenceRecord, ...] = (),
    *,
    claim: CapabilityClaim | None = None,
) -> tuple[EpistemicRecordSet, CapabilityClaim]:
    target = claim or _claim()
    return EpistemicRecordSet(evidence_records=evidence, claims=(target,)), target


def _coverage(
    records: EpistemicRecordSet,
    claim: CapabilityClaim,
    *,
    hour: int = 14,
    bearings: dict[str, EvidenceBearing] | None = None,
    reliability: EvidenceReliability = EvidenceReliability.UNASSESSED,
):
    boundary = _time(hour)
    ids = tuple(
        item.evidence_id.value
        for item in records.evidence_records
        if item.subject_ref == claim.subject_ref and item.recorded_at <= boundary
    )
    mapping = bearings or {}
    return build_claim_evidence_disposition_coverage_v1(
        records=records,
        claim_id=claim.claim_id,
        as_of=boundary,
        dispositions=tuple(
            _assessment(
                evidence_id,
                bearing=mapping.get(evidence_id, EvidenceBearing.SUPPORTS),
                reliability=reliability,
            )
            for evidence_id in ids
        ),
    )


def _build(records, claim, *, hour: int = 14, coverage=None):
    actual = coverage or _coverage(records, claim, hour=hour)
    lineage = build_claim_evidence_lineage_dependence_v1(
        records=records,
        claim_id=claim.claim_id,
        as_of=_time(hour),
        coverage=actual,
    )
    return actual, lineage


def _relation(records, claim, coverage, left: str, right: str, *, hour=14, lineage=None):
    return resolve_claim_evidence_pair_lineage_relation_v1(
        records=records,
        claim_id=claim.claim_id,
        as_of=_time(hour),
        coverage=coverage,
        left_evidence_id=EvidenceId(left),
        right_evidence_id=EvidenceId(right),
        lineage=lineage,
    )


def _profile(lineage, evidence_id: str):
    return {item.evidence_id.value: item for item in lineage.lineage_profiles}[evidence_id]


def test_empty_candidate_universe_produces_empty_profiles():
    records, claim = _basis()
    coverage, lineage = _build(records, claim)
    assert coverage.dispositions == ()
    assert lineage.lineage_profiles == ()
    assert validate_claim_evidence_lineage_dependence_v1(
        records=records, claim_id=claim.claim_id, as_of=_time(14), coverage=coverage, lineage=lineage
    ) == lineage


def test_every_candidate_receives_exactly_one_profile():
    records, claim = _basis((_evidence("a"), _evidence("b")))
    coverage, lineage = _build(records, claim)
    assert tuple(item.evidence_id for item in lineage.lineage_profiles) == tuple(
        item.evidence_id for item in coverage.dispositions
    )


def test_root_profile_uses_self_as_internal_root():
    records, claim = _basis((_evidence("root"),))
    _, lineage = _build(records, claim)
    profile = _profile(lineage, "root")
    assert profile.direct_parent_evidence_ids == ()
    assert profile.root_evidence_ids == (EvidenceId("root"),)


def test_direct_parent_child_is_proven_shared_lineage():
    parent = _evidence("a", recorded_hour=10)
    child = _evidence(
        "b", recorded_hour=11,
        sources=(_source(ProvenanceSourceKind.EVIDENCE_RECORD, "a"),),
    )
    records, claim = _basis((parent, child))
    coverage, lineage = _build(records, claim)
    assert _profile(lineage, "b").direct_parent_evidence_ids == (EvidenceId("a"),)
    assert _profile(lineage, "b").root_evidence_ids == (EvidenceId("a"),)
    assert _relation(records, claim, coverage, "a", "b", lineage=lineage) is EvidenceLineageRelation.PROVEN_SHARED_LINEAGE


def test_transitive_root_descendant_is_proven_shared_lineage():
    a = _evidence("a", recorded_hour=10)
    b = _evidence("b", recorded_hour=11, sources=(_source(ProvenanceSourceKind.EVIDENCE_RECORD, "a"),))
    c = _evidence("c", recorded_hour=12, sources=(_source(ProvenanceSourceKind.EVIDENCE_RECORD, "b"),))
    records, claim = _basis((a, b, c))
    coverage, lineage = _build(records, claim)
    assert _profile(lineage, "c").root_evidence_ids == (EvidenceId("a"),)
    assert _relation(records, claim, coverage, "a", "c") is EvidenceLineageRelation.PROVEN_SHARED_LINEAGE


def test_sibling_descendants_share_internal_root():
    root = _evidence("root", recorded_hour=10)
    left = _evidence("left", recorded_hour=11, sources=(_source(ProvenanceSourceKind.EVIDENCE_RECORD, "root"),))
    right = _evidence("right", recorded_hour=12, sources=(_source(ProvenanceSourceKind.EVIDENCE_RECORD, "root"),))
    records, claim = _basis((root, left, right))
    coverage, _ = _build(records, claim)
    assert _relation(records, claim, coverage, "left", "right") is EvidenceLineageRelation.PROVEN_SHARED_LINEAGE


def test_same_exact_artifact_origin_is_proven_shared_lineage():
    origin = _source(ProvenanceSourceKind.ARTIFACT, "artifact_1")
    records, claim = _basis((_evidence("a", sources=(origin,)), _evidence("b", sources=(origin,))))
    coverage, lineage = _build(records, claim)
    assert _profile(lineage, "a").origin_sources == (origin,)
    assert _relation(records, claim, coverage, "a", "b") is EvidenceLineageRelation.PROVEN_SHARED_LINEAGE


def test_same_exact_external_record_origin_is_proven_shared_lineage():
    origin = _source(ProvenanceSourceKind.EXTERNAL_RECORD, "external_1")
    records, claim = _basis((_evidence("a", sources=(origin,)), _evidence("b", sources=(origin,))))
    coverage, _ = _build(records, claim)
    assert _relation(records, claim, coverage, "a", "b") is EvidenceLineageRelation.PROVEN_SHARED_LINEAGE


def test_concrete_origin_is_inherited_through_derived_evidence():
    origin = _source(ProvenanceSourceKind.ARTIFACT, "artifact_root")
    root = _evidence("root", recorded_hour=10, sources=(origin,))
    child = _evidence("child", recorded_hour=11, sources=(_source(ProvenanceSourceKind.EVIDENCE_RECORD, "root"),))
    records, claim = _basis((root, child))
    coverage, lineage = _build(records, claim)
    assert _profile(lineage, "child").origin_sources == (origin,)
    assert _relation(records, claim, coverage, "root", "child") is EvidenceLineageRelation.PROVEN_SHARED_LINEAGE


def test_profiles_and_nested_values_are_canonically_ordered():
    a = _evidence("a", recorded_hour=10)
    b = _evidence("b", recorded_hour=10)
    child = _evidence(
        "z", recorded_hour=11,
        sources=(
            _source(ProvenanceSourceKind.EXTERNAL_RECORD, "external_z"),
            _source(ProvenanceSourceKind.EVIDENCE_RECORD, "b"),
            _source(ProvenanceSourceKind.ARTIFACT, "artifact_a"),
            _source(ProvenanceSourceKind.EVIDENCE_RECORD, "a"),
        ),
    )
    records, claim = _basis((child, b, a))
    _, lineage = _build(records, claim)
    assert tuple(item.evidence_id.value for item in lineage.lineage_profiles) == ("a", "b", "z")
    profile = _profile(lineage, "z")
    assert tuple(item.value for item in profile.direct_parent_evidence_ids) == ("a", "b")
    assert tuple(item.value for item in profile.root_evidence_ids) == ("a", "b")
    assert profile.origin_sources == tuple(sorted(profile.origin_sources))


def test_a_plus_b_to_c_does_not_overcollapse_a_and_b():
    a = _evidence("a", recorded_hour=10)
    b = _evidence("b", recorded_hour=10)
    c = _evidence(
        "c", recorded_hour=11,
        sources=(
            _source(ProvenanceSourceKind.EVIDENCE_RECORD, "a"),
            _source(ProvenanceSourceKind.EVIDENCE_RECORD, "b"),
        ),
    )
    records, claim = _basis((a, b, c))
    coverage, _ = _build(records, claim)
    assert _relation(records, claim, coverage, "a", "c") is EvidenceLineageRelation.PROVEN_SHARED_LINEAGE
    assert _relation(records, claim, coverage, "b", "c") is EvidenceLineageRelation.PROVEN_SHARED_LINEAGE
    assert _relation(records, claim, coverage, "a", "b") is EvidenceLineageRelation.UNRESOLVED


@pytest.mark.parametrize("kind", [ProvenanceSourceKind.ACTOR, ProvenanceSourceKind.SYSTEM])
def test_same_actor_or_system_does_not_prove_shared_lineage(kind):
    shared = _source(kind, "shared_1")
    records, claim = _basis((_evidence("a", sources=(shared,)), _evidence("b", sources=(shared,))))
    coverage, lineage = _build(records, claim)
    assert _profile(lineage, "a").origin_sources == ()
    assert _relation(records, claim, coverage, "a", "b") is EvidenceLineageRelation.UNRESOLVED


def test_different_artifact_refs_do_not_prove_independence():
    records, claim = _basis((
        _evidence("a", sources=(_source(ProvenanceSourceKind.ARTIFACT, "artifact_a"),)),
        _evidence("b", sources=(_source(ProvenanceSourceKind.ARTIFACT, "artifact_b"),)),
    ))
    coverage, _ = _build(records, claim)
    assert _relation(records, claim, coverage, "a", "b") is EvidenceLineageRelation.UNRESOLVED


def test_same_ref_with_different_origin_kind_is_not_overlap():
    records, claim = _basis((
        _evidence("a", sources=(_source(ProvenanceSourceKind.ARTIFACT, "origin_1"),)),
        _evidence("b", sources=(_source(ProvenanceSourceKind.EXTERNAL_RECORD, "origin_1"),)),
    ))
    coverage, _ = _build(records, claim)
    assert _relation(records, claim, coverage, "a", "b") is EvidenceLineageRelation.UNRESOLVED


def test_disjoint_observation_times_do_not_prove_independence():
    records, claim = _basis((
        _evidence("a", observed_hour=10, recorded_hour=11),
        _evidence("b", observed_hour=12, recorded_hour=13),
    ))
    coverage, _ = _build(records, claim)
    assert _relation(records, claim, coverage, "a", "b") is EvidenceLineageRelation.UNRESOLVED


def test_overlapping_observation_windows_do_not_automatically_prove_dependence():
    records, claim = _basis((
        _evidence("a", observed_hour=12, recorded_hour=13, observation_started_hour=10),
        _evidence("b", observed_hour=12, recorded_hour=13, observation_started_hour=11),
    ))
    coverage, _ = _build(records, claim)
    assert _relation(records, claim, coverage, "a", "b") is EvidenceLineageRelation.UNRESOLVED


def test_repeated_performance_record_has_no_internal_replication_count_surface():
    repeated = _evidence(
        "repeated", kind=EvidenceKind.REPEATED_PERFORMANCE,
        observation_started_hour=8, observed_hour=12, recorded_hour=13,
    )
    records, claim = _basis((repeated,))
    _, lineage = _build(records, claim)
    assert set(_profile(lineage, "repeated").__dataclass_fields__) == {
        "evidence_id", "direct_parent_evidence_ids", "root_evidence_ids", "origin_sources"
    }


def test_multiple_repeated_performance_records_remain_unresolved():
    records, claim = _basis((
        _evidence("a", kind=EvidenceKind.REPEATED_PERFORMANCE, observation_started_hour=8, observed_hour=10, recorded_hour=11),
        _evidence("b", kind=EvidenceKind.REPEATED_PERFORMANCE, observation_started_hour=11, observed_hour=12, recorded_hour=13),
    ))
    coverage, _ = _build(records, claim)
    assert _relation(records, claim, coverage, "a", "b") is EvidenceLineageRelation.UNRESOLVED


def test_shared_payload_ref_alone_does_not_prove_dependence():
    records, claim = _basis((_evidence("a", payload_refs=("payload_same",)), _evidence("b", payload_refs=("payload_same",))))
    coverage, _ = _build(records, claim)
    assert _relation(records, claim, coverage, "a", "b") is EvidenceLineageRelation.UNRESOLVED


def test_kind_outcome_bearing_and_reliability_do_not_change_profiles():
    outcome = EvidenceOutcome(EvidenceOutcomeStatus.SUCCESS, "Success.")
    records, claim = _basis((_evidence("a", kind=EvidenceKind.QUIZ, outcome=outcome), _evidence("b", kind=EvidenceKind.PROJECT)))
    coverage_a = _coverage(records, claim, bearings={"a": EvidenceBearing.SUPPORTS, "b": EvidenceBearing.CONTRADICTS}, reliability=EvidenceReliability.HIGH)
    coverage_b = _coverage(records, claim, bearings={"a": EvidenceBearing.NOT_RELEVANT, "b": EvidenceBearing.INDETERMINATE}, reliability=EvidenceReliability.LOW)
    lineage_a = build_claim_evidence_lineage_dependence_v1(records=records, claim_id=claim.claim_id, as_of=_time(14), coverage=coverage_a)
    lineage_b = build_claim_evidence_lineage_dependence_v1(records=records, claim_id=claim.claim_id, as_of=_time(14), coverage=coverage_b)
    assert lineage_a.lineage_profiles == lineage_b.lineage_profiles
    assert lineage_a.disposition_coverage_sha256 != lineage_b.disposition_coverage_sha256


def test_not_relevant_candidate_still_receives_profile():
    records, claim = _basis((_evidence("a"), _evidence("b")))
    coverage = _coverage(records, claim, bearings={"b": EvidenceBearing.NOT_RELEVANT})
    lineage = build_claim_evidence_lineage_dependence_v1(records=records, claim_id=claim.claim_id, as_of=_time(14), coverage=coverage)
    assert tuple(item.evidence_id.value for item in lineage.lineage_profiles) == ("a", "b")


def test_shared_lineage_never_removes_or_mutates_dispositions():
    origin = _source(ProvenanceSourceKind.ARTIFACT, "artifact_1")
    records, claim = _basis((_evidence("a", sources=(origin,)), _evidence("b", sources=(origin,))))
    coverage = _coverage(records, claim, bearings={"a": EvidenceBearing.SUPPORTS, "b": EvidenceBearing.CONTRADICTS})
    before = coverage.to_json()
    lineage = build_claim_evidence_lineage_dependence_v1(records=records, claim_id=claim.claim_id, as_of=_time(14), coverage=coverage)
    assert coverage.to_json() == before
    assert len(lineage.lineage_profiles) == 2


def test_receipt_binds_exact_pr12_9_coverage_content():
    records, claim = _basis((_evidence("a"),))
    coverage_a = _coverage(records, claim, bearings={"a": EvidenceBearing.SUPPORTS})
    coverage_b = _coverage(records, claim, bearings={"a": EvidenceBearing.CONTRADICTS})
    lineage_a = build_claim_evidence_lineage_dependence_v1(records=records, claim_id=claim.claim_id, as_of=_time(14), coverage=coverage_a)
    lineage_b = build_claim_evidence_lineage_dependence_v1(records=records, claim_id=claim.claim_id, as_of=_time(14), coverage=coverage_b)
    assert lineage_a.lineage_profiles == lineage_b.lineage_profiles
    assert lineage_a.disposition_coverage_sha256 != lineage_b.disposition_coverage_sha256
    with pytest.raises(InvalidClaimEvidenceLineageDependence, match="lineage content"):
        validate_claim_evidence_lineage_dependence_v1(records=records, claim_id=claim.claim_id, as_of=_time(14), coverage=coverage_b, lineage=lineage_a)


def test_json_round_trip_passes_only_after_full_replay():
    records, claim = _basis((_evidence("a"), _evidence("b")))
    coverage, lineage = _build(records, claim)
    restored = claim_evidence_lineage_dependence_receipt_from_json(lineage.to_json())
    assert restored == lineage
    assert validate_claim_evidence_lineage_dependence_v1(records=records, claim_id=claim.claim_id, as_of=_time(14), coverage=coverage, lineage=restored) == lineage


def test_equal_but_distinct_caller_created_receipt_is_safe_after_replay():
    records, claim = _basis((_evidence("a"),))
    coverage, lineage = _build(records, claim)
    clone = ClaimEvidenceLineageDependenceReceipt.from_dict(lineage.to_dict())
    assert clone == lineage and clone is not lineage
    assert validate_claim_evidence_lineage_dependence_v1(records=records, claim_id=claim.claim_id, as_of=_time(14), coverage=coverage, lineage=clone) == clone


def test_stale_snapshot_rejected_even_for_unrelated_append():
    records, claim = _basis((_evidence("a"),))
    coverage, lineage = _build(records, claim)
    changed = EpistemicRecordSet(evidence_records=records.evidence_records + (_evidence("other", subject="subject_2"),), claims=records.claims)
    with pytest.raises(InvalidClaimEvidenceLineageDependence, match="PR12.9"):
        validate_claim_evidence_lineage_dependence_v1(records=changed, claim_id=claim.claim_id, as_of=_time(14), coverage=coverage, lineage=lineage)


def test_changed_as_of_rejects_stale_lineage():
    records, claim = _basis((_evidence("now", recorded_hour=11), _evidence("later", observed_hour=14, recorded_hour=15)))
    coverage, lineage = _build(records, claim, hour=14)
    with pytest.raises(InvalidClaimEvidenceLineageDependence):
        validate_claim_evidence_lineage_dependence_v1(records=records, claim_id=claim.claim_id, as_of=_time(15), coverage=coverage, lineage=lineage)


def test_changed_target_claim_rejects_stale_lineage():
    records, claim = _basis((_evidence("a"),))
    coverage, lineage = _build(records, claim)
    other = _claim(claim_id="claim_2")
    changed = EpistemicRecordSet(evidence_records=records.evidence_records, claims=(other,))
    with pytest.raises(InvalidClaimEvidenceLineageDependence):
        validate_claim_evidence_lineage_dependence_v1(records=changed, claim_id=other.claim_id, as_of=_time(14), coverage=coverage, lineage=lineage)


def test_changed_provenance_under_same_id_invalidates_stale_lineage():
    records, claim = _basis((_evidence("a", sources=(_source(ProvenanceSourceKind.ARTIFACT, "artifact_old"),)),))
    coverage, lineage = _build(records, claim)
    changed = EpistemicRecordSet(evidence_records=(_evidence("a", sources=(_source(ProvenanceSourceKind.ARTIFACT, "artifact_new"),)),), claims=(claim,))
    with pytest.raises(InvalidClaimEvidenceLineageDependence, match="PR12.9"):
        validate_claim_evidence_lineage_dependence_v1(records=changed, claim_id=claim.claim_id, as_of=_time(14), coverage=coverage, lineage=lineage)


def test_historical_backfill_forces_coverage_and_lineage_rebuild():
    records, claim = _basis((_evidence("a"),))
    coverage, lineage = _build(records, claim)
    changed = EpistemicRecordSet(evidence_records=records.evidence_records + (_evidence("backfill", observed_hour=8, recorded_hour=9),), claims=records.claims)
    with pytest.raises(InvalidClaimEvidenceLineageDependence, match="PR12.9"):
        validate_claim_evidence_lineage_dependence_v1(records=changed, claim_id=claim.claim_id, as_of=_time(14), coverage=coverage, lineage=lineage)


def test_future_evidence_becoming_candidate_gets_new_profile():
    records, claim = _basis((_evidence("now", recorded_hour=11), _evidence("future", observed_hour=14, recorded_hour=15)))
    _, early = _build(records, claim, hour=14)
    _, later = _build(records, claim, hour=15)
    assert tuple(item.evidence_id.value for item in early.lineage_profiles) == ("now",)
    assert tuple(item.evidence_id.value for item in later.lineage_profiles) == ("future", "now")


def test_dataclasses_replace_profile_omission_fails_full_replay():
    records, claim = _basis((_evidence("a"), _evidence("b")))
    coverage, lineage = _build(records, claim)
    forged = replace(lineage, lineage_profiles=lineage.lineage_profiles[:-1])
    with pytest.raises(InvalidClaimEvidenceLineageDependence, match="lineage content"):
        validate_claim_evidence_lineage_dependence_v1(records=records, claim_id=claim.claim_id, as_of=_time(14), coverage=coverage, lineage=forged)


def test_dataclasses_replace_extra_profile_fails_full_replay():
    records, claim = _basis((_evidence("a"),))
    coverage, lineage = _build(records, claim)
    extra_id = EvidenceId("extra")
    extra = EvidenceLineageProfile(evidence_id=extra_id, root_evidence_ids=(extra_id,))
    forged = replace(lineage, lineage_profiles=lineage.lineage_profiles + (extra,))
    with pytest.raises(InvalidClaimEvidenceLineageDependence, match="lineage content"):
        validate_claim_evidence_lineage_dependence_v1(records=records, claim_id=claim.claim_id, as_of=_time(14), coverage=coverage, lineage=forged)


def test_post_construction_corruption_fails_closed():
    records, claim = _basis((_evidence("a"),))
    coverage, lineage = _build(records, claim)
    object.__setattr__(lineage.lineage_profiles[0], "root_evidence_ids", ())
    with pytest.raises(InvalidClaimEvidenceLineageDependence):
        validate_claim_evidence_lineage_dependence_v1(records=records, claim_id=claim.claim_id, as_of=_time(14), coverage=coverage, lineage=lineage)


def test_behavioral_evidence_id_subclass_is_rejected_by_pair_api():
    class BehavioralEvidenceId(EvidenceId):
        pass
    records, claim = _basis((_evidence("a"), _evidence("b")))
    coverage, _ = _build(records, claim)
    with pytest.raises(InvalidClaimEvidenceLineageDependence, match="exact EvidenceId"):
        resolve_claim_evidence_pair_lineage_relation_v1(
            records=records, claim_id=claim.claim_id, as_of=_time(14), coverage=coverage,
            left_evidence_id=BehavioralEvidenceId("a"), right_evidence_id=EvidenceId("b"),
        )


def test_pair_api_rejects_same_or_non_candidate_ids():
    records, claim = _basis((_evidence("a"),))
    coverage, _ = _build(records, claim)
    with pytest.raises(InvalidClaimEvidenceLineageDependence, match="distinct"):
        _relation(records, claim, coverage, "a", "a")
    with pytest.raises(InvalidClaimEvidenceLineageDependence, match="candidate"):
        _relation(records, claim, coverage, "a", "missing")


def test_pair_api_does_not_trust_forged_lineage_receipt():
    records, claim = _basis((_evidence("a"), _evidence("b")))
    coverage, lineage = _build(records, claim)
    a = _profile(lineage, "a")
    b = _profile(lineage, "b")
    forged = replace(lineage, lineage_profiles=(a, replace(b, root_evidence_ids=a.root_evidence_ids)))
    with pytest.raises(InvalidClaimEvidenceLineageDependence, match="rebuilt lineage"):
        _relation(records, claim, coverage, "a", "b", lineage=forged)


def test_from_dict_rejects_unknown_missing_and_noncanonical_profile_order():
    records, claim = _basis((_evidence("a"), _evidence("b")))
    _, lineage = _build(records, claim)
    payload = lineage.to_dict()
    unknown = dict(payload); unknown["unknown"] = True
    with pytest.raises(InvalidClaimEvidenceLineageDependence, match="unknown"):
        claim_evidence_lineage_dependence_receipt_from_dict(unknown)
    missing = dict(payload); del missing["claim_id"]
    with pytest.raises(InvalidClaimEvidenceLineageDependence, match="missing"):
        claim_evidence_lineage_dependence_receipt_from_dict(missing)
    noncanonical = dict(payload); noncanonical["lineage_profiles"] = list(reversed(payload["lineage_profiles"]))
    with pytest.raises(InvalidClaimEvidenceLineageDependence, match="canonical"):
        claim_evidence_lineage_dependence_receipt_from_dict(noncanonical)


def test_from_dict_rejects_noncanonical_nested_root_and_origin_order():
    a = _evidence("a", recorded_hour=10)
    b = _evidence("b", recorded_hour=10)
    c = _evidence("c", recorded_hour=11, sources=(
        _source(ProvenanceSourceKind.EVIDENCE_RECORD, "a"),
        _source(ProvenanceSourceKind.EVIDENCE_RECORD, "b"),
        _source(ProvenanceSourceKind.ARTIFACT, "artifact_a"),
        _source(ProvenanceSourceKind.EXTERNAL_RECORD, "external_b"),
    ))
    records, claim = _basis((a, b, c))
    _, lineage = _build(records, claim)
    payload = lineage.to_dict()
    roots_bad = json.loads(json.dumps(payload))
    roots_c = next(item for item in roots_bad["lineage_profiles"] if item["evidence_id"] == "c")
    roots_c["root_evidence_ids"] = list(reversed(roots_c["root_evidence_ids"]))
    with pytest.raises(InvalidClaimEvidenceLineageDependence, match="canonical"):
        claim_evidence_lineage_dependence_receipt_from_dict(roots_bad)
    origins_bad = json.loads(json.dumps(payload))
    origins_c = next(item for item in origins_bad["lineage_profiles"] if item["evidence_id"] == "c")
    origins_c["origin_sources"] = list(reversed(origins_c["origin_sources"]))
    with pytest.raises(InvalidClaimEvidenceLineageDependence, match="canonical"):
        claim_evidence_lineage_dependence_receipt_from_dict(origins_bad)


def test_json_rejects_duplicate_keys_noncanonical_spacing_and_nan():
    records, claim = _basis((_evidence("a"),))
    _, lineage = _build(records, claim)
    canonical = lineage.to_json()
    duplicate = canonical.replace('"schema_version":1', '"schema_version":1,"schema_version":1', 1)
    with pytest.raises(InvalidClaimEvidenceLineageDependence, match="duplicate"):
        claim_evidence_lineage_dependence_receipt_from_json(duplicate)
    spaced = json.dumps(lineage.to_dict(), sort_keys=True)
    with pytest.raises(InvalidClaimEvidenceLineageDependence, match="canonical"):
        claim_evidence_lineage_dependence_receipt_from_json(spaced)
    nan_payload = canonical.replace('"schema_version":1', '"schema_version":NaN', 1)
    with pytest.raises(InvalidClaimEvidenceLineageDependence, match="non-standard"):
        claim_evidence_lineage_dependence_receipt_from_json(nan_payload)


def test_schema_exposes_no_positive_independent_relation():
    assert tuple(EvidenceLineageRelation) == (
        EvidenceLineageRelation.PROVEN_SHARED_LINEAGE,
        EvidenceLineageRelation.UNRESOLVED,
    )
    assert not hasattr(EvidenceLineageRelation, "INDEPENDENT")
    assert not hasattr(EvidenceLineageRelation, "PROVEN_INDEPENDENT")


def test_production_import_surface_has_no_policy_state_progression_or_pilot_authority():
    source = inspect.getsource(lineage_module)
    tree = ast.parse(source)
    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
    forbidden = (
        "capability_lab.evaluation_policy", "capability_lab.derivation", "capability_lab.history",
        "capability_lab.progression", "capability_lab.pilot", "capability_lab.player_window", "capability_lab.hde",
    )
    assert not any(name.startswith(prefix) for name in imported_modules for prefix in forbidden)
    assert "ClaimEvaluation" not in source
    assert ".evaluations" not in source


def test_receipt_schema_contains_no_count_weight_policy_state_or_authority_fields():
    fields = set(ClaimEvidenceLineageDependenceReceipt.__dataclass_fields__)
    assert fields == {
        "snapshot_sha256", "claim_id", "subject_ref", "concept_ref", "as_of",
        "disposition_coverage_sha256", "lineage_profiles",
    }
    forbidden = ("count", "weight", "independent", "replication", "policy", "conclusion", "state", "score", "authority")
    assert not any(fragment in field for field in fields for fragment in forbidden)


def test_exact_dict_and_json_helpers_are_deterministic():
    origin = _source(ProvenanceSourceKind.ARTIFACT, "artifact_1")
    records, claim = _basis((_evidence("a", sources=(origin,)),))
    _, lineage = _build(records, claim)
    first_dict = claim_evidence_lineage_dependence_receipt_to_dict(lineage)
    first_json = claim_evidence_lineage_dependence_receipt_to_json(lineage)
    assert first_dict == claim_evidence_lineage_dependence_receipt_to_dict(lineage)
    assert first_json == claim_evidence_lineage_dependence_receipt_to_json(lineage)
    assert claim_evidence_lineage_dependence_receipt_from_dict(first_dict) == lineage
