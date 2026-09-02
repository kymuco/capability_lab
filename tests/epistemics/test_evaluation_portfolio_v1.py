from dataclasses import fields
from datetime import datetime, timedelta, timezone

import pytest

from capability_lab.epistemics import (
    CapabilityClaim,
    CapabilityClaimId,
    CapabilitySubjectRef,
    ClaimEvaluation,
    ClaimEvaluationId,
    ClaimEvaluationPortfolioEntry,
    ClaimEvaluationPortfolioReceipt,
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
    InvalidClaimEvaluationPortfolio,
    ProvenanceSource,
    ProvenanceSourceKind,
    ProvenanceTrail,
    build_complete_claim_evaluation_portfolio_v1,
    epistemic_snapshot_sha256_v1,
    validate_exact_claim_evaluation_selection_v1,
)
from capability_lab.semantics import CapabilityConceptRef


T0 = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)
ALICE = CapabilitySubjectRef("alice_pr11_4")
BOB = CapabilitySubjectRef("bob_pr11_4")
CONCEPT = CapabilityConceptRef.parse("core:portfolio_probe@1")
CONCEPT_V2 = CapabilityConceptRef.parse("core:portfolio_probe@2")


def _trail(ref: str) -> ProvenanceTrail:
    return ProvenanceTrail(
        (ProvenanceSource(ProvenanceSourceKind.ACTOR, ref),)
    )


def _evidence(evidence_id: str, *, subject_ref: CapabilitySubjectRef = ALICE) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=EvidenceId(evidence_id),
        subject_ref=subject_ref,
        kind=EvidenceKind.PROJECT,
        summary=f"Evidence {evidence_id}.",
        context=EvidenceContext("PR11.4 bounded portfolio context."),
        observed_at=T0 - timedelta(hours=3),
        recorded_at=T0 - timedelta(hours=2, minutes=59),
        provenance=_trail(f"actor_{evidence_id}"),
    )


def _claim(
    claim_id: str,
    *,
    subject_ref: CapabilitySubjectRef = ALICE,
    concept_ref: CapabilityConceptRef = CONCEPT,
    created_at: datetime | None = None,
) -> CapabilityClaim:
    return CapabilityClaim(
        claim_id=CapabilityClaimId(claim_id),
        subject_ref=subject_ref,
        concept_ref=concept_ref,
        statement=f"Claim {claim_id}.",
        scope=ClaimScope("PR11.4 bounded claim scope."),
        created_at=created_at or (T0 - timedelta(hours=2)),
        provenance=_trail(f"author_{claim_id}"),
    )


def _assessment(
    evidence_id: str,
    *,
    bearing: EvidenceBearing,
    reliability: EvidenceReliability = EvidenceReliability.HIGH,
) -> EvidenceAssessment:
    return EvidenceAssessment(
        EvidenceId(evidence_id), bearing, reliability,
        "PR11.4 coverage note.", "PR11.4 evidence rationale.",
    )


def _evaluation(
    evaluation_id: str,
    claim_id: str,
    *,
    conclusion: EvaluationConclusion = EvaluationConclusion.SUPPORTED,
    evaluated_at: datetime | None = None,
    policy_ref: str = "core:portfolio_policy@1",
    evaluator_kind: EvaluatorKind = EvaluatorKind.HUMAN,
    reliability: EvidenceReliability = EvidenceReliability.HIGH,
    evidence_a: str = "evidence_a",
    evidence_b: str = "evidence_b",
) -> ClaimEvaluation:
    if conclusion is EvaluationConclusion.SUPPORTED:
        assessments = (_assessment(evidence_a, bearing=EvidenceBearing.SUPPORTS, reliability=reliability),)
        coverage, conflict = CoverageStatus.SUFFICIENT_FOR_CLAIM, ConflictStatus.NONE
    elif conclusion is EvaluationConclusion.CONTRADICTED:
        assessments = (_assessment(evidence_a, bearing=EvidenceBearing.CONTRADICTS, reliability=reliability),)
        coverage, conflict = CoverageStatus.SUFFICIENT_FOR_CLAIM, ConflictStatus.NONE
    elif conclusion is EvaluationConclusion.MIXED:
        assessments = (
            _assessment(evidence_a, bearing=EvidenceBearing.SUPPORTS, reliability=reliability),
            _assessment(evidence_b, bearing=EvidenceBearing.CONTRADICTS, reliability=reliability),
        )
        coverage, conflict = CoverageStatus.SUFFICIENT_FOR_CLAIM, ConflictStatus.UNRESOLVED
    else:
        assessments = (_assessment(evidence_a, bearing=EvidenceBearing.INDETERMINATE, reliability=reliability),)
        coverage, conflict = CoverageStatus.PARTIAL, ConflictStatus.NONE
    return ClaimEvaluation(
        evaluation_id=ClaimEvaluationId(evaluation_id),
        claim_id=CapabilityClaimId(claim_id),
        policy_ref=EvaluationPolicyRef.parse(policy_ref),
        evaluator_ref=EvaluatorRef(evaluator_kind, f"reviewer_{evaluation_id}"),
        evaluated_at=evaluated_at or (T0 - timedelta(minutes=30)),
        evidence_assessments=assessments,
        coverage=CoverageAssessment(coverage, "PR11.4 claim coverage."),
        conflict_status=conflict,
        conclusion=conclusion,
        rationale=f"Evaluation {evaluation_id}.",
    )


def _records(*, evidence_records=(), claims=(), evaluations=()) -> EpistemicRecordSet:
    return EpistemicRecordSet(tuple(evidence_records), tuple(claims), tuple(evaluations))


def _base_snapshot() -> EpistemicRecordSet:
    return _records(
        evidence_records=(_evidence("evidence_a"), _evidence("evidence_b")),
        claims=(_claim("claim_a"), _claim("claim_b")),
        evaluations=(
            _evaluation("eval_supported", "claim_a"),
            _evaluation("eval_contradicted", "claim_a", conclusion=EvaluationConclusion.CONTRADICTED),
        ),
    )


def _portfolio(records, *, subject_ref=ALICE, concept_ref=CONCEPT, as_of=T0):
    return build_complete_claim_evaluation_portfolio_v1(
        records=records, subject_ref=subject_ref, concept_ref=concept_ref, as_of=as_of
    )


def test_empty_snapshot_yields_empty_validator_issued_portfolio() -> None:
    records = EpistemicRecordSet()
    portfolio = _portfolio(records)
    assert portfolio.validator_issued is True
    assert portfolio.snapshot_sha256 == epistemic_snapshot_sha256_v1(records)
    assert portfolio.entries == ()
    assert portfolio.admissible_evaluation_ids == ()


def test_unevaluated_claim_remains_visible() -> None:
    portfolio = _portfolio(_records(claims=(_claim("claim_a"),)))
    assert portfolio.entries == (ClaimEvaluationPortfolioEntry(CapabilityClaimId("claim_a"), ()),)
    assert portfolio.unevaluated_claim_ids == (CapabilityClaimId("claim_a"),)


def test_matching_claims_and_evaluations_are_sorted_deterministically() -> None:
    portfolio = _portfolio(_base_snapshot())
    assert portfolio.claim_ids == (CapabilityClaimId("claim_a"), CapabilityClaimId("claim_b"))
    assert portfolio.admissible_evaluation_ids == (
        ClaimEvaluationId("eval_contradicted"), ClaimEvaluationId("eval_supported")
    )


def test_foreign_subject_is_out_of_scope_not_an_exclusion() -> None:
    records = _records(
        evidence_records=(_evidence("evidence_a"), _evidence("evidence_foreign", subject_ref=BOB)),
        claims=(_claim("claim_a"), _claim("claim_foreign", subject_ref=BOB)),
        evaluations=(
            _evaluation("eval_supported", "claim_a"),
            _evaluation("eval_foreign", "claim_foreign", evidence_a="evidence_foreign"),
        ),
    )
    portfolio = _portfolio(records)
    assert portfolio.claim_ids == (CapabilityClaimId("claim_a"),)
    assert portfolio.admissible_evaluation_ids == (ClaimEvaluationId("eval_supported"),)
    assert portfolio.excluded_future_claim_ids == ()
    assert portfolio.excluded_future_evaluation_ids == ()


def test_other_concept_revision_is_out_of_scope() -> None:
    records = _records(claims=(_claim("claim_v1"), _claim("claim_v2", concept_ref=CONCEPT_V2)))
    assert _portfolio(records).claim_ids == (CapabilityClaimId("claim_v1"),)


def test_claim_created_exactly_at_as_of_is_admissible() -> None:
    portfolio = _portfolio(_records(claims=(_claim("claim_boundary", created_at=T0),)))
    assert portfolio.claim_ids == (CapabilityClaimId("claim_boundary"),)


def test_future_claim_is_explicitly_excluded() -> None:
    portfolio = _portfolio(_records(claims=(_claim("claim_future", created_at=T0 + timedelta(seconds=1)),)))
    assert portfolio.entries == ()
    assert portfolio.excluded_future_claim_ids == (CapabilityClaimId("claim_future"),)


def test_evaluation_exactly_at_as_of_is_admissible() -> None:
    records = _records(
        evidence_records=(_evidence("evidence_a"),), claims=(_claim("claim_a"),),
        evaluations=(_evaluation("eval_boundary", "claim_a", evaluated_at=T0),),
    )
    assert _portfolio(records).admissible_evaluation_ids == (ClaimEvaluationId("eval_boundary"),)


def test_future_evaluation_is_explicitly_excluded() -> None:
    records = _records(
        evidence_records=(_evidence("evidence_a"),), claims=(_claim("claim_a"),),
        evaluations=(_evaluation("eval_future", "claim_a", evaluated_at=T0 + timedelta(seconds=1)),),
    )
    portfolio = _portfolio(records)
    assert portfolio.admissible_evaluation_ids == ()
    assert portfolio.excluded_future_evaluation_ids == (ClaimEvaluationId("eval_future"),)


def test_evaluation_on_future_claim_is_reported_as_future_evaluation_too() -> None:
    future = T0 + timedelta(minutes=10)
    records = _records(
        evidence_records=(_evidence("evidence_a"),),
        claims=(_claim("claim_future", created_at=future),),
        evaluations=(_evaluation("eval_future", "claim_future", evaluated_at=future),),
    )
    portfolio = _portfolio(records)
    assert portfolio.excluded_future_claim_ids == (CapabilityClaimId("claim_future"),)
    assert portfolio.excluded_future_evaluation_ids == (ClaimEvaluationId("eval_future"),)


@pytest.mark.parametrize("conclusion", tuple(EvaluationConclusion))
def test_membership_does_not_filter_by_conclusion(conclusion) -> None:
    records = _records(
        evidence_records=(_evidence("evidence_a"), _evidence("evidence_b")),
        claims=(_claim("claim_a"),),
        evaluations=(_evaluation(f"eval_{conclusion.value}", "claim_a", conclusion=conclusion),),
    )
    assert _portfolio(records).admissible_evaluation_ids == (ClaimEvaluationId(f"eval_{conclusion.value}"),)


@pytest.mark.parametrize("evaluator_kind", tuple(EvaluatorKind))
def test_membership_does_not_filter_by_evaluator_kind(evaluator_kind) -> None:
    records = _records(
        evidence_records=(_evidence("evidence_a"),), claims=(_claim("claim_a"),),
        evaluations=(_evaluation("eval_any_evaluator", "claim_a", evaluator_kind=evaluator_kind),),
    )
    assert _portfolio(records).admissible_evaluation_ids == (ClaimEvaluationId("eval_any_evaluator"),)


def test_membership_does_not_filter_by_policy_or_reliability() -> None:
    records = _records(
        evidence_records=(_evidence("evidence_a"),), claims=(_claim("claim_a"),),
        evaluations=(
            _evaluation("eval_policy_a", "claim_a", reliability=EvidenceReliability.HIGH),
            _evaluation("eval_policy_b", "claim_a", policy_ref="research:alternative_policy@7", evaluator_kind=EvaluatorKind.MODEL, reliability=EvidenceReliability.LOW),
        ),
    )
    assert _portfolio(records).admissible_evaluation_ids == (
        ClaimEvaluationId("eval_policy_a"), ClaimEvaluationId("eval_policy_b")
    )


def test_exact_complete_selection_passes_and_is_sorted() -> None:
    records = _base_snapshot(); portfolio = _portfolio(records)
    selected = validate_exact_claim_evaluation_selection_v1(
        records=records, portfolio=portfolio,
        selected_evaluation_ids=(ClaimEvaluationId("eval_supported"), ClaimEvaluationId("eval_contradicted")),
    )
    assert selected == portfolio.admissible_evaluation_ids


def test_omitting_supported_evaluation_is_rejected() -> None:
    records = _base_snapshot(); portfolio = _portfolio(records)
    with pytest.raises(InvalidClaimEvaluationPortfolio, match="selection omits admissible claim evaluation: eval_supported"):
        validate_exact_claim_evaluation_selection_v1(
            records=records, portfolio=portfolio,
            selected_evaluation_ids=(ClaimEvaluationId("eval_contradicted"),),
        )


def test_omitting_contradicted_evaluation_is_rejected() -> None:
    records = _base_snapshot(); portfolio = _portfolio(records)
    with pytest.raises(InvalidClaimEvaluationPortfolio, match="selection omits admissible claim evaluation: eval_contradicted"):
        validate_exact_claim_evaluation_selection_v1(
            records=records, portfolio=portfolio,
            selected_evaluation_ids=(ClaimEvaluationId("eval_supported"),),
        )


def test_omitting_abstained_evaluation_is_rejected() -> None:
    records = _records(
        evidence_records=(_evidence("evidence_a"),), claims=(_claim("claim_a"),),
        evaluations=(
            _evaluation("eval_supported", "claim_a"),
            _evaluation("eval_abstained", "claim_a", conclusion=EvaluationConclusion.ABSTAINED),
        ),
    )
    portfolio = _portfolio(records)
    with pytest.raises(InvalidClaimEvaluationPortfolio, match="selection omits admissible claim evaluation: eval_abstained"):
        validate_exact_claim_evaluation_selection_v1(
            records=records, portfolio=portfolio,
            selected_evaluation_ids=(ClaimEvaluationId("eval_supported"),),
        )


def test_extra_inadmissible_evaluation_is_rejected() -> None:
    records = _base_snapshot(); portfolio = _portfolio(records)
    with pytest.raises(InvalidClaimEvaluationPortfolio, match="selection includes inadmissible claim evaluation: eval_extra"):
        validate_exact_claim_evaluation_selection_v1(
            records=records, portfolio=portfolio,
            selected_evaluation_ids=portfolio.admissible_evaluation_ids + (ClaimEvaluationId("eval_extra"),),
        )


def test_duplicate_selection_is_rejected_before_set_comparison() -> None:
    records = _base_snapshot(); portfolio = _portfolio(records)
    with pytest.raises(InvalidClaimEvaluationPortfolio, match="selected_evaluation_ids must not contain duplicate ids"):
        validate_exact_claim_evaluation_selection_v1(
            records=records, portfolio=portfolio,
            selected_evaluation_ids=(ClaimEvaluationId("eval_supported"), ClaimEvaluationId("eval_supported")),
        )


def test_structural_receipt_is_not_validator_issued_and_cannot_authorize_selection() -> None:
    records = _base_snapshot(); issued = _portfolio(records)
    structural = ClaimEvaluationPortfolioReceipt(
        snapshot_sha256=issued.snapshot_sha256, subject_ref=issued.subject_ref,
        concept_ref=issued.concept_ref, as_of=issued.as_of, entries=issued.entries,
    )
    assert structural.validator_issued is False
    with pytest.raises(InvalidClaimEvaluationPortfolio, match="portfolio must be validator-issued"):
        validate_exact_claim_evaluation_selection_v1(
            records=records, portfolio=structural,
            selected_evaluation_ids=issued.admissible_evaluation_ids,
        )


def test_unrelated_snapshot_append_invalidates_old_receipt() -> None:
    records = _base_snapshot(); portfolio = _portfolio(records)
    expanded = _records(
        evidence_records=records.evidence_records,
        claims=records.claims + (_claim("claim_foreign", subject_ref=BOB),),
        evaluations=records.evaluations,
    )
    with pytest.raises(InvalidClaimEvaluationPortfolio, match="portfolio snapshot does not match supplied EpistemicRecordSet"):
        validate_exact_claim_evaluation_selection_v1(
            records=expanded, portfolio=portfolio,
            selected_evaluation_ids=portfolio.admissible_evaluation_ids,
        )


def test_historical_backfill_requires_rebuild_and_becomes_mandatory() -> None:
    records = _records(
        evidence_records=(_evidence("evidence_a"),), claims=(_claim("claim_a"),),
        evaluations=(_evaluation("eval_original", "claim_a", evaluated_at=T0 - timedelta(hours=1)),),
    )
    old = _portfolio(records, as_of=T0)
    backfilled = _evaluation(
        "eval_backfilled", "claim_a", conclusion=EvaluationConclusion.CONTRADICTED,
        evaluated_at=T0 - timedelta(minutes=45),
    )
    expanded = _records(
        evidence_records=records.evidence_records, claims=records.claims,
        evaluations=records.evaluations + (backfilled,),
    )
    with pytest.raises(InvalidClaimEvaluationPortfolio, match="portfolio snapshot does not match supplied EpistemicRecordSet"):
        validate_exact_claim_evaluation_selection_v1(
            records=expanded, portfolio=old,
            selected_evaluation_ids=old.admissible_evaluation_ids,
        )
    rebuilt = _portfolio(expanded, as_of=T0)
    assert rebuilt.admissible_evaluation_ids == (
        ClaimEvaluationId("eval_backfilled"), ClaimEvaluationId("eval_original")
    )


def test_timezone_equivalent_as_of_values_produce_equal_scope() -> None:
    records = _base_snapshot()
    assert _portfolio(records, as_of=T0) == _portfolio(
        records, as_of=T0.astimezone(timezone(timedelta(hours=6)))
    )


def test_structural_entry_rejects_duplicate_evaluation_ids() -> None:
    with pytest.raises(InvalidClaimEvaluationPortfolio, match="portfolio entry evaluation_ids must not contain duplicate ids"):
        ClaimEvaluationPortfolioEntry(
            CapabilityClaimId("claim_a"),
            (ClaimEvaluationId("eval_a"), ClaimEvaluationId("eval_a")),
        )


def test_structural_receipt_rejects_evaluation_id_reused_across_claim_entries() -> None:
    with pytest.raises(InvalidClaimEvaluationPortfolio, match="portfolio evaluation ids must belong to exactly one claim entry"):
        ClaimEvaluationPortfolioReceipt(
            snapshot_sha256="0" * 64, subject_ref=ALICE, concept_ref=CONCEPT, as_of=T0,
            entries=(
                ClaimEvaluationPortfolioEntry(CapabilityClaimId("claim_a"), (ClaimEvaluationId("eval_shared"),)),
                ClaimEvaluationPortfolioEntry(CapabilityClaimId("claim_b"), (ClaimEvaluationId("eval_shared"),)),
            ),
        )


def test_portfolio_receipt_has_no_preference_or_state_authority_fields() -> None:
    field_names = {item.name for item in fields(ClaimEvaluationPortfolioReceipt)}
    assert {
        "preferred_evaluation_id", "active_evaluation_id", "winning_conclusion",
        "confidence", "score", "mastery", "personal_capability_state",
        "claim_dimension_bindings",
    }.isdisjoint(field_names)


def test_builder_rejects_wrong_scope_types_and_naive_as_of() -> None:
    with pytest.raises(InvalidClaimEvaluationPortfolio, match="records must be EpistemicRecordSet"):
        build_complete_claim_evaluation_portfolio_v1(
            records=object(), subject_ref=ALICE, concept_ref=CONCEPT, as_of=T0
        )
    with pytest.raises(InvalidClaimEvaluationPortfolio, match="subject_ref must be CapabilitySubjectRef"):
        build_complete_claim_evaluation_portfolio_v1(
            records=EpistemicRecordSet(), subject_ref="alice", concept_ref=CONCEPT, as_of=T0
        )
    with pytest.raises(InvalidClaimEvaluationPortfolio, match="concept_ref must be exact CapabilityConceptRef"):
        build_complete_claim_evaluation_portfolio_v1(
            records=EpistemicRecordSet(), subject_ref=ALICE, concept_ref="core:portfolio_probe@1", as_of=T0
        )
    with pytest.raises(InvalidClaimEvaluationPortfolio, match="portfolio as_of must be timezone-aware"):
        _portfolio(EpistemicRecordSet(), as_of=datetime(2026, 8, 20, 12, 0))
