from dataclasses import replace
from datetime import datetime, timezone
import inspect

import pytest

from capability_lab.epistemics import (
    CapabilityClaim,
    CapabilityClaimId,
    CapabilitySubjectRef,
    ClaimEvidenceCandidatePortfolioReceipt,
    ClaimScope,
    EpistemicRecordSet,
    EvidenceContext,
    EvidenceId,
    EvidenceKind,
    EvidenceOutcome,
    EvidenceOutcomeStatus,
    EvidenceRecord,
    InvalidClaimEvidenceCandidatePortfolio,
    ProvenanceSource,
    ProvenanceSourceKind,
    ProvenanceTrail,
    build_complete_claim_evidence_candidate_portfolio_v1,
    claim_evidence_candidate_portfolio_receipt_from_dict,
    claim_evidence_candidate_portfolio_receipt_from_json,
    epistemic_snapshot_sha256_v1,
    validate_exact_claim_evidence_candidate_selection_v1,
)
from capability_lab.semantics import CapabilityConceptRef, CapabilityId


def _time(hour: int) -> datetime:
    return datetime(2026, 9, 1, hour, 0, tzinfo=timezone.utc)


def _subject(value: str = "subject_1") -> CapabilitySubjectRef:
    return CapabilitySubjectRef(value)


def _concept(revision: int = 1) -> CapabilityConceptRef:
    return CapabilityConceptRef(CapabilityId.parse("research:signal_reasoning"), revision)


def _provenance(ref: str = "source_1", *, kind=ProvenanceSourceKind.SYSTEM):
    return ProvenanceTrail(sources=(ProvenanceSource(kind, ref),))


def _claim(
    *,
    claim_id: str = "claim_1",
    subject: str = "subject_1",
    created_hour: int = 12,
    statement: str = "The subject can reason about bounded signal evidence.",
) -> CapabilityClaim:
    return CapabilityClaim(
        claim_id=CapabilityClaimId(claim_id),
        subject_ref=_subject(subject),
        concept_ref=_concept(),
        statement=statement,
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
    kind: EvidenceKind = EvidenceKind.ARTIFACT,
    outcome: EvidenceOutcome | None = None,
    context: EvidenceContext | None = None,
    source_kind: ProvenanceSourceKind = ProvenanceSourceKind.SYSTEM,
) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=EvidenceId(evidence_id),
        subject_ref=_subject(subject),
        kind=kind,
        summary=f"Evidence {evidence_id}.",
        context=context or EvidenceContext("Generic context.", ("generic",)),
        observed_at=_time(observed_hour),
        recorded_at=_time(recorded_hour),
        provenance=_provenance(f"source_{evidence_id}", kind=source_kind),
        outcome=outcome,
        payload_refs=(f"payload_{evidence_id}",),
    )


def _basis(*, evidence=(), claims=None) -> tuple[EpistemicRecordSet, CapabilityClaim]:
    claim = _claim()
    records = EpistemicRecordSet(
        evidence_records=tuple(evidence),
        claims=tuple(claims) if claims is not None else (claim,),
    )
    return records, claim


def _build(records: EpistemicRecordSet, claim: CapabilityClaim, *, hour: int = 14):
    return build_complete_claim_evidence_candidate_portfolio_v1(
        records=records,
        claim_id=claim.claim_id,
        as_of=_time(hour),
    )


def test_exact_claim_resolution_and_snapshot_binding():
    evidence = (_evidence("evidence_1"),)
    records, claim = _basis(evidence=evidence)
    portfolio = _build(records, claim)

    assert portfolio.snapshot_sha256 == epistemic_snapshot_sha256_v1(records)
    assert portfolio.claim_id == claim.claim_id
    assert portfolio.subject_ref == claim.subject_ref
    assert portfolio.concept_ref == claim.concept_ref
    assert portfolio.as_of == _time(14)
    assert portfolio.evidence_ids == (EvidenceId("evidence_1"),)


def test_claim_created_after_as_of_is_rejected():
    claim = _claim(created_hour=15)
    records = EpistemicRecordSet(claims=(claim,))
    with pytest.raises(
        InvalidClaimEvidenceCandidatePortfolio,
        match="created_at",
    ):
        _build(records, claim, hour=14)


def test_all_same_subject_evidence_available_by_as_of_is_included():
    records, claim = _basis(
        evidence=(
            _evidence("evidence_3", recorded_hour=13),
            _evidence("evidence_1", recorded_hour=11),
            _evidence("evidence_2", recorded_hour=14),
        )
    )
    portfolio = _build(records, claim)
    assert portfolio.evidence_ids == (
        EvidenceId("evidence_1"),
        EvidenceId("evidence_2"),
        EvidenceId("evidence_3"),
    )


def test_same_subject_future_evidence_is_explicitly_excluded_by_recorded_at():
    records, claim = _basis(
        evidence=(
            _evidence("evidence_now", observed_hour=10, recorded_hour=14),
            _evidence("evidence_future", observed_hour=10, recorded_hour=16),
        )
    )
    portfolio = _build(records, claim)
    assert portfolio.evidence_ids == (EvidenceId("evidence_now"),)
    assert portfolio.excluded_future_evidence_ids == (EvidenceId("evidence_future"),)


def test_different_subject_evidence_is_not_candidate_or_future_disposition():
    records, claim = _basis(
        evidence=(
            _evidence("same_subject", subject="subject_1", recorded_hour=13),
            _evidence("other_subject", subject="subject_2", recorded_hour=13),
            _evidence("other_future", subject="subject_2", recorded_hour=16),
        )
    )
    portfolio = _build(records, claim)
    assert portfolio.evidence_ids == (EvidenceId("same_subject"),)
    assert portfolio.excluded_future_evidence_ids == ()


def test_kind_outcome_context_and_provenance_do_not_filter_membership():
    records, claim = _basis(
        evidence=(
            _evidence(
                "failure_quiz",
                kind=EvidenceKind.QUIZ,
                outcome=EvidenceOutcome(EvidenceOutcomeStatus.FAILURE, "Failed attempt."),
                context=EvidenceContext("Quiz context.", ("quiz_context",)),
                source_kind=ProvenanceSourceKind.EXTERNAL_RECORD,
            ),
            _evidence(
                "success_project",
                kind=EvidenceKind.PROJECT,
                outcome=EvidenceOutcome(EvidenceOutcomeStatus.SUCCESS, "Successful project."),
                context=EvidenceContext("Project context.", ("project_context",)),
                source_kind=ProvenanceSourceKind.ARTIFACT,
            ),
        )
    )
    assert _build(records, claim).evidence_ids == (
        EvidenceId("failure_quiz"),
        EvidenceId("success_project"),
    )


def test_empty_candidate_portfolio_is_valid():
    records, claim = _basis()
    portfolio = _build(records, claim)
    assert portfolio.evidence_ids == ()
    assert portfolio.excluded_future_evidence_ids == ()
    assert validate_exact_claim_evidence_candidate_selection_v1(
        records=records,
        claim_id=claim.claim_id,
        as_of=_time(14),
        selected_evidence_ids=(),
        portfolio=portfolio,
    ) == ()


def test_portfolio_and_selection_use_canonical_ordering():
    records, claim = _basis(
        evidence=(
            _evidence("z_evidence"),
            _evidence("a_evidence"),
        )
    )
    portfolio = _build(records, claim)
    assert portfolio.evidence_ids == (EvidenceId("a_evidence"), EvidenceId("z_evidence"))
    selected = validate_exact_claim_evidence_candidate_selection_v1(
        records=records,
        claim_id=claim.claim_id,
        as_of=_time(14),
        selected_evidence_ids=(EvidenceId("z_evidence"), EvidenceId("a_evidence")),
        portfolio=portfolio,
    )
    assert selected == (EvidenceId("a_evidence"), EvidenceId("z_evidence"))


def test_unrelated_snapshot_append_invalidates_stale_receipt():
    records, claim = _basis(evidence=(_evidence("evidence_1"),))
    portfolio = _build(records, claim)
    changed = EpistemicRecordSet(
        evidence_records=records.evidence_records
        + (_evidence("other_subject", subject="subject_2"),),
        claims=records.claims,
    )
    with pytest.raises(InvalidClaimEvidenceCandidatePortfolio, match="portfolio content"):
        validate_exact_claim_evidence_candidate_selection_v1(
            records=changed,
            claim_id=claim.claim_id,
            as_of=_time(14),
            selected_evidence_ids=portfolio.evidence_ids,
            portfolio=portfolio,
        )


def test_changed_target_claim_content_invalidates_stale_receipt_via_snapshot_binding():
    records, claim = _basis(evidence=(_evidence("evidence_1"),))
    portfolio = _build(records, claim)
    changed_claim = replace(claim, statement="Changed exact claim content.")
    changed = EpistemicRecordSet(
        evidence_records=records.evidence_records,
        claims=(changed_claim,),
    )
    with pytest.raises(InvalidClaimEvidenceCandidatePortfolio, match="portfolio content"):
        validate_exact_claim_evidence_candidate_selection_v1(
            records=changed,
            claim_id=claim.claim_id,
            as_of=_time(14),
            selected_evidence_ids=portfolio.evidence_ids,
            portfolio=portfolio,
        )


def test_explicit_as_of_binding_rejects_stale_receipt():
    records, claim = _basis(evidence=(_evidence("evidence_1"),))
    portfolio = _build(records, claim, hour=14)
    with pytest.raises(InvalidClaimEvidenceCandidatePortfolio, match="portfolio content"):
        validate_exact_claim_evidence_candidate_selection_v1(
            records=records,
            claim_id=claim.claim_id,
            as_of=_time(13),
            selected_evidence_ids=(EvidenceId("evidence_1"),),
            portfolio=portfolio,
        )


def test_caller_created_subset_receipt_fails_records_derived_replay():
    records, claim = _basis(
        evidence=(_evidence("evidence_1"), _evidence("evidence_2"))
    )
    expected = _build(records, claim)
    subset = ClaimEvidenceCandidatePortfolioReceipt(
        snapshot_sha256=expected.snapshot_sha256,
        claim_id=expected.claim_id,
        subject_ref=expected.subject_ref,
        concept_ref=expected.concept_ref,
        as_of=expected.as_of,
        evidence_ids=(EvidenceId("evidence_1"),),
        excluded_future_evidence_ids=expected.excluded_future_evidence_ids,
    )
    with pytest.raises(InvalidClaimEvidenceCandidatePortfolio, match="portfolio content"):
        validate_exact_claim_evidence_candidate_selection_v1(
            records=records,
            claim_id=claim.claim_id,
            as_of=_time(14),
            selected_evidence_ids=(EvidenceId("evidence_1"),),
            portfolio=subset,
        )


def test_dataclasses_replace_subset_receipt_fails_records_derived_replay():
    records, claim = _basis(
        evidence=(_evidence("evidence_1"), _evidence("evidence_2"))
    )
    expected = _build(records, claim)
    subset = replace(expected, evidence_ids=(EvidenceId("evidence_1"),))
    with pytest.raises(InvalidClaimEvidenceCandidatePortfolio, match="portfolio content"):
        validate_exact_claim_evidence_candidate_selection_v1(
            records=records,
            claim_id=claim.claim_id,
            as_of=_time(14),
            selected_evidence_ids=subset.evidence_ids,
            portfolio=subset,
        )


def test_json_restored_exact_receipt_passes_only_after_records_revalidation():
    records, claim = _basis(evidence=(_evidence("evidence_1"),))
    expected = _build(records, claim)
    restored = claim_evidence_candidate_portfolio_receipt_from_json(expected.to_json())
    assert restored == expected
    assert restored is not expected
    assert validate_exact_claim_evidence_candidate_selection_v1(
        records=records,
        claim_id=claim.claim_id,
        as_of=_time(14),
        selected_evidence_ids=restored.evidence_ids,
        portfolio=restored,
    ) == restored.evidence_ids


def test_equal_distinct_receipt_does_not_widen_selection():
    records, claim = _basis(
        evidence=(_evidence("evidence_1"), _evidence("evidence_2"))
    )
    expected = _build(records, claim)
    equal_copy = ClaimEvidenceCandidatePortfolioReceipt.from_dict(expected.to_dict())
    assert equal_copy == expected and equal_copy is not expected
    with pytest.raises(InvalidClaimEvidenceCandidatePortfolio, match="omits"):
        validate_exact_claim_evidence_candidate_selection_v1(
            records=records,
            claim_id=claim.claim_id,
            as_of=_time(14),
            selected_evidence_ids=(EvidenceId("evidence_1"),),
            portfolio=equal_copy,
        )


def test_selection_can_be_validated_without_receipt_because_receipt_is_not_authority():
    records, claim = _basis(evidence=(_evidence("evidence_1"),))
    assert validate_exact_claim_evidence_candidate_selection_v1(
        records=records,
        claim_id=claim.claim_id,
        as_of=_time(14),
        selected_evidence_ids=(EvidenceId("evidence_1"),),
    ) == (EvidenceId("evidence_1"),)


def test_omitted_admissible_evidence_is_rejected():
    records, claim = _basis(
        evidence=(_evidence("evidence_1"), _evidence("evidence_2"))
    )
    with pytest.raises(InvalidClaimEvidenceCandidatePortfolio, match="omits"):
        validate_exact_claim_evidence_candidate_selection_v1(
            records=records,
            claim_id=claim.claim_id,
            as_of=_time(14),
            selected_evidence_ids=(EvidenceId("evidence_1"),),
        )


def test_extra_future_evidence_is_rejected():
    records, claim = _basis(
        evidence=(
            _evidence("evidence_now", recorded_hour=13),
            _evidence("evidence_future", recorded_hour=16),
        )
    )
    with pytest.raises(InvalidClaimEvidenceCandidatePortfolio, match="inadmissible"):
        validate_exact_claim_evidence_candidate_selection_v1(
            records=records,
            claim_id=claim.claim_id,
            as_of=_time(14),
            selected_evidence_ids=(
                EvidenceId("evidence_now"),
                EvidenceId("evidence_future"),
            ),
        )


def test_extra_other_subject_evidence_is_rejected():
    records, claim = _basis(
        evidence=(
            _evidence("evidence_now"),
            _evidence("other_subject", subject="subject_2"),
        )
    )
    with pytest.raises(InvalidClaimEvidenceCandidatePortfolio, match="inadmissible"):
        validate_exact_claim_evidence_candidate_selection_v1(
            records=records,
            claim_id=claim.claim_id,
            as_of=_time(14),
            selected_evidence_ids=(EvidenceId("evidence_now"), EvidenceId("other_subject")),
        )


def test_duplicate_selected_evidence_ids_are_rejected():
    records, claim = _basis(evidence=(_evidence("evidence_1"),))
    with pytest.raises(InvalidClaimEvidenceCandidatePortfolio, match="duplicate"):
        validate_exact_claim_evidence_candidate_selection_v1(
            records=records,
            claim_id=claim.claim_id,
            as_of=_time(14),
            selected_evidence_ids=(EvidenceId("evidence_1"), EvidenceId("evidence_1")),
        )


def test_wrong_claim_id_is_rejected_even_when_receipt_names_another_claim():
    first = _claim(claim_id="claim_1", subject="subject_1")
    second = _claim(claim_id="claim_2", subject="subject_2")
    records = EpistemicRecordSet(
        evidence_records=(_evidence("evidence_1", subject="subject_1"),),
        claims=(first, second),
    )
    portfolio = _build(records, first)
    with pytest.raises(InvalidClaimEvidenceCandidatePortfolio, match="portfolio content"):
        validate_exact_claim_evidence_candidate_selection_v1(
            records=records,
            claim_id=second.claim_id,
            as_of=_time(14),
            selected_evidence_ids=portfolio.evidence_ids,
            portfolio=portfolio,
        )


def test_historical_backfill_available_by_same_as_of_forces_rebuild_and_selection():
    records, claim = _basis(evidence=(_evidence("evidence_1", recorded_hour=13),))
    stale = _build(records, claim)
    backfilled = EpistemicRecordSet(
        evidence_records=records.evidence_records
        + (_evidence("historical_backfill", observed_hour=9, recorded_hour=12),),
        claims=records.claims,
    )
    with pytest.raises(InvalidClaimEvidenceCandidatePortfolio, match="portfolio content"):
        validate_exact_claim_evidence_candidate_selection_v1(
            records=backfilled,
            claim_id=claim.claim_id,
            as_of=_time(14),
            selected_evidence_ids=stale.evidence_ids,
            portfolio=stale,
        )
    rebuilt = _build(backfilled, claim)
    assert rebuilt.evidence_ids == (
        EvidenceId("evidence_1"),
        EvidenceId("historical_backfill"),
    )


def test_post_construction_receipt_corruption_fails_closed():
    records, claim = _basis(evidence=(_evidence("evidence_1"),))
    portfolio = _build(records, claim)
    object.__setattr__(portfolio, "evidence_ids", [EvidenceId("evidence_1")])
    with pytest.raises(InvalidClaimEvidenceCandidatePortfolio, match="exact tuple"):
        validate_exact_claim_evidence_candidate_selection_v1(
            records=records,
            claim_id=claim.claim_id,
            as_of=_time(14),
            selected_evidence_ids=(EvidenceId("evidence_1"),),
            portfolio=portfolio,
        )


def test_behavioral_subclassed_scalar_in_receipt_fails_closed():
    class PretendSha(str):
        pass

    records, claim = _basis(evidence=(_evidence("evidence_1"),))
    portfolio = _build(records, claim)
    object.__setattr__(portfolio, "snapshot_sha256", PretendSha(portfolio.snapshot_sha256))
    with pytest.raises(InvalidClaimEvidenceCandidatePortfolio, match="SHA-256"):
        validate_exact_claim_evidence_candidate_selection_v1(
            records=records,
            claim_id=claim.claim_id,
            as_of=_time(14),
            selected_evidence_ids=(EvidenceId("evidence_1"),),
            portfolio=portfolio,
        )


def test_subclassed_evidence_id_in_selection_fails_closed():
    class PretendEvidenceId(EvidenceId):
        pass

    records, claim = _basis(evidence=(_evidence("evidence_1"),))
    with pytest.raises(InvalidClaimEvidenceCandidatePortfolio, match="exact EvidenceId"):
        validate_exact_claim_evidence_candidate_selection_v1(
            records=records,
            claim_id=claim.claim_id,
            as_of=_time(14),
            selected_evidence_ids=(PretendEvidenceId("evidence_1"),),
        )


def test_receipt_serialization_is_canonical_and_rejects_schema_corruption():
    records, claim = _basis(
        evidence=(
            _evidence("evidence_1"),
            _evidence("evidence_future", recorded_hour=16),
        )
    )
    portfolio = _build(records, claim)
    payload = portfolio.to_json()
    restored = ClaimEvidenceCandidatePortfolioReceipt.from_json(payload)
    assert restored == portfolio
    assert restored.to_json() == payload

    unknown = portfolio.to_dict()
    unknown["policy"] = "forged"
    with pytest.raises(InvalidClaimEvidenceCandidatePortfolio, match="unknown"):
        claim_evidence_candidate_portfolio_receipt_from_dict(unknown)

    missing = portfolio.to_dict()
    missing.pop("claim_id")
    with pytest.raises(InvalidClaimEvidenceCandidatePortfolio, match="missing"):
        claim_evidence_candidate_portfolio_receipt_from_dict(missing)

    duplicate = payload.replace(
        '"schema_version":1',
        '"schema_version":1,"schema_version":1',
        1,
    )
    with pytest.raises(InvalidClaimEvidenceCandidatePortfolio, match="duplicate JSON"):
        claim_evidence_candidate_portfolio_receipt_from_json(duplicate)


def test_receipt_json_requires_canonical_sorted_id_arrays():
    records, claim = _basis(
        evidence=(_evidence("a_evidence"), _evidence("z_evidence"))
    )
    obj = _build(records, claim).to_dict()
    obj["evidence_ids"] = ["z_evidence", "a_evidence"]
    with pytest.raises(InvalidClaimEvidenceCandidatePortfolio, match="canonical sorted"):
        claim_evidence_candidate_portfolio_receipt_from_dict(obj)


def test_import_surface_has_no_evaluator_policy_interpretation_state_or_pilot_authority():
    import capability_lab.epistemics.claim_evidence_candidate_portfolio as module

    source = inspect.getsource(module)
    forbidden_import_fragments = (
        "capability_lab.interpretation",
        "capability_lab.evaluation_policy",
        "pilot",
        "progression",
        "PersonalCapabilityState",
    )
    assert not any(fragment in source for fragment in forbidden_import_fragments)

    build_parameters = set(
        inspect.signature(build_complete_claim_evidence_candidate_portfolio_v1).parameters
    )
    assert build_parameters == {"records", "claim_id", "as_of"}
    selection_parameters = set(
        inspect.signature(validate_exact_claim_evidence_candidate_selection_v1).parameters
    )
    assert selection_parameters == {
        "records",
        "claim_id",
        "as_of",
        "selected_evidence_ids",
        "portfolio",
    }
    assert not {
        "policy",
        "evaluation",
        "reliability",
        "bearing",
        "independence",
        "state",
    } & selection_parameters
