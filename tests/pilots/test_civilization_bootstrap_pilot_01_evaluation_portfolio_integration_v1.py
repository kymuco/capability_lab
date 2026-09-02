from dataclasses import fields, replace
from datetime import timedelta

import pytest

from capability_lab.epistemics import (
    ClaimEvaluationId,
    ClaimEvaluationPortfolioEntry,
    ClaimEvaluationPortfolioReceipt,
    EpistemicRecordSet,
    EvaluationConclusion,
    InvalidClaimEvaluationPortfolio,
    build_complete_claim_evaluation_portfolio_v1,
    validate_epistemic_snapshot_successor_v1,
    validate_exact_claim_evaluation_selection_v1,
)

from test_civilization_bootstrap_pilot_01_snapshot_succession_integration_v1 import (
    _real_pr11_2_case,
)


def _portfolio(records, claim, *, as_of):
    return build_complete_claim_evaluation_portfolio_v1(
        records=records,
        subject_ref=claim.subject_ref,
        concept_ref=claim.concept_ref,
        as_of=as_of,
    )


def _correction(evaluation, *, evaluation_id: str, minutes: int):
    return replace(
        evaluation,
        evaluation_id=ClaimEvaluationId(evaluation_id),
        evaluated_at=evaluation.evaluated_at + timedelta(minutes=minutes),
        conclusion=EvaluationConclusion.ABSTAINED,
        rationale=(
            "PR11.4 append-only correction retained alongside the original "
            "immutable ClaimEvaluation."
        ),
    )


def test_real_pr11_2_evaluation_enters_complete_pr11_4_portfolio(tmp_path) -> None:
    _, snapshot, evaluation, _, claim = _real_pr11_2_case(tmp_path)

    portfolio = _portfolio(
        snapshot,
        claim,
        as_of=evaluation.evaluated_at,
    )

    assert portfolio.validator_issued is True
    assert portfolio.claim_ids == (claim.claim_id,)
    assert portfolio.admissible_evaluation_ids == (evaluation.evaluation_id,)


def test_pr11_3_append_only_correction_makes_both_evaluations_mandatory(tmp_path) -> None:
    _, snapshot, evaluation, _, claim = _real_pr11_2_case(tmp_path)
    correction = _correction(
        evaluation,
        evaluation_id="evaluation_multi_bounded_reasoning_pr11_4_correction",
        minutes=1,
    )
    successor = EpistemicRecordSet(
        evidence_records=snapshot.evidence_records,
        claims=snapshot.claims,
        evaluations=snapshot.evaluations + (correction,),
    )

    succession = validate_epistemic_snapshot_successor_v1(
        predecessor=snapshot,
        successor=successor,
    )
    assert succession.retained_evaluation_ids == (evaluation.evaluation_id,)
    assert succession.added_evaluation_ids == (correction.evaluation_id,)

    portfolio = _portfolio(
        successor,
        claim,
        as_of=correction.evaluated_at,
    )
    assert portfolio.admissible_evaluation_ids == tuple(
        sorted((evaluation.evaluation_id, correction.evaluation_id))
    )


def test_original_only_selection_is_rejected_after_correction_append(tmp_path) -> None:
    _, snapshot, evaluation, _, claim = _real_pr11_2_case(tmp_path)
    correction = _correction(
        evaluation,
        evaluation_id="evaluation_multi_bounded_reasoning_pr11_4_correction",
        minutes=1,
    )
    successor = EpistemicRecordSet(
        evidence_records=snapshot.evidence_records,
        claims=snapshot.claims,
        evaluations=snapshot.evaluations + (correction,),
    )
    validate_epistemic_snapshot_successor_v1(
        predecessor=snapshot,
        successor=successor,
    )
    portfolio = _portfolio(successor, claim, as_of=correction.evaluated_at)

    with pytest.raises(
        InvalidClaimEvaluationPortfolio,
        match=(
            "selection omits admissible claim evaluation: "
            "evaluation_multi_bounded_reasoning_pr11_4_correction"
        ),
    ):
        validate_exact_claim_evaluation_selection_v1(
            records=successor,
            portfolio=portfolio,
            selected_evaluation_ids=(evaluation.evaluation_id,),
        )


def test_correction_only_selection_is_rejected_after_correction_append(tmp_path) -> None:
    _, snapshot, evaluation, _, claim = _real_pr11_2_case(tmp_path)
    correction = _correction(
        evaluation,
        evaluation_id="evaluation_multi_bounded_reasoning_pr11_4_correction",
        minutes=1,
    )
    successor = EpistemicRecordSet(
        evidence_records=snapshot.evidence_records,
        claims=snapshot.claims,
        evaluations=snapshot.evaluations + (correction,),
    )
    validate_epistemic_snapshot_successor_v1(
        predecessor=snapshot,
        successor=successor,
    )
    portfolio = _portfolio(successor, claim, as_of=correction.evaluated_at)

    with pytest.raises(
        InvalidClaimEvaluationPortfolio,
        match=f"selection omits admissible claim evaluation: {evaluation.evaluation_id}",
    ):
        validate_exact_claim_evaluation_selection_v1(
            records=successor,
            portfolio=portfolio,
            selected_evaluation_ids=(correction.evaluation_id,),
        )


def test_exact_original_plus_correction_selection_passes(tmp_path) -> None:
    _, snapshot, evaluation, _, claim = _real_pr11_2_case(tmp_path)
    correction = _correction(
        evaluation,
        evaluation_id="evaluation_multi_bounded_reasoning_pr11_4_correction",
        minutes=1,
    )
    successor = EpistemicRecordSet(
        evidence_records=snapshot.evidence_records,
        claims=snapshot.claims,
        evaluations=snapshot.evaluations + (correction,),
    )
    validate_epistemic_snapshot_successor_v1(
        predecessor=snapshot,
        successor=successor,
    )
    portfolio = _portfolio(successor, claim, as_of=correction.evaluated_at)

    selected = validate_exact_claim_evaluation_selection_v1(
        records=successor,
        portfolio=portfolio,
        selected_evaluation_ids=(
            correction.evaluation_id,
            evaluation.evaluation_id,
        ),
    )
    assert selected == portfolio.admissible_evaluation_ids


def test_pre_append_portfolio_cannot_be_reused_on_pr11_3_successor(tmp_path) -> None:
    _, snapshot, evaluation, _, claim = _real_pr11_2_case(tmp_path)
    old = _portfolio(
        snapshot,
        claim,
        as_of=evaluation.evaluated_at + timedelta(minutes=10),
    )
    correction = _correction(
        evaluation,
        evaluation_id="evaluation_multi_bounded_reasoning_pr11_4_correction",
        minutes=1,
    )
    successor = EpistemicRecordSet(
        evidence_records=snapshot.evidence_records,
        claims=snapshot.claims,
        evaluations=snapshot.evaluations + (correction,),
    )
    validate_epistemic_snapshot_successor_v1(
        predecessor=snapshot,
        successor=successor,
    )

    with pytest.raises(
        InvalidClaimEvaluationPortfolio,
        match="portfolio snapshot does not match supplied EpistemicRecordSet",
    ):
        validate_exact_claim_evaluation_selection_v1(
            records=successor,
            portfolio=old,
            selected_evaluation_ids=old.admissible_evaluation_ids,
        )


def test_historical_backfill_before_same_as_of_requires_rebuild(tmp_path) -> None:
    _, snapshot, evaluation, _, claim = _real_pr11_2_case(tmp_path)
    historical_as_of = evaluation.evaluated_at + timedelta(minutes=10)
    old = _portfolio(snapshot, claim, as_of=historical_as_of)

    backfilled = _correction(
        evaluation,
        evaluation_id="evaluation_multi_bounded_reasoning_pr11_4_backfill",
        minutes=5,
    )
    successor = EpistemicRecordSet(
        evidence_records=snapshot.evidence_records,
        claims=snapshot.claims,
        evaluations=snapshot.evaluations + (backfilled,),
    )
    succession = validate_epistemic_snapshot_successor_v1(
        predecessor=snapshot,
        successor=successor,
    )
    assert succession.added_evaluation_ids == (backfilled.evaluation_id,)

    with pytest.raises(
        InvalidClaimEvaluationPortfolio,
        match="portfolio snapshot does not match supplied EpistemicRecordSet",
    ):
        validate_exact_claim_evaluation_selection_v1(
            records=successor,
            portfolio=old,
            selected_evaluation_ids=old.admissible_evaluation_ids,
        )

    rebuilt = _portfolio(successor, claim, as_of=historical_as_of)
    assert rebuilt.admissible_evaluation_ids == tuple(
        sorted((evaluation.evaluation_id, backfilled.evaluation_id))
    )


def test_pr11_4_receipt_does_not_reinterpret_portfolio_as_state_authority(
    tmp_path,
) -> None:
    _, snapshot, evaluation, _, claim = _real_pr11_2_case(tmp_path)
    portfolio = _portfolio(snapshot, claim, as_of=evaluation.evaluated_at)

    receipt_fields = {item.name for item in fields(type(portfolio))}
    assert {
        "preferred_evaluation_id",
        "active_evaluation_id",
        "winning_conclusion",
        "claim_dimension_bindings",
        "personal_capability_state",
        "mastery",
        "score",
        "confidence",
    }.isdisjoint(receipt_fields)


def test_replaced_builder_receipt_cannot_hide_real_appended_correction(tmp_path) -> None:
    _, snapshot, evaluation, _, claim = _real_pr11_2_case(tmp_path)
    correction = _correction(
        evaluation,
        evaluation_id="evaluation_multi_bounded_reasoning_pr11_4_receipt_tamper",
        minutes=1,
    )
    successor = EpistemicRecordSet(
        evidence_records=snapshot.evidence_records,
        claims=snapshot.claims,
        evaluations=snapshot.evaluations + (correction,),
    )
    validate_epistemic_snapshot_successor_v1(
        predecessor=snapshot,
        successor=successor,
    )
    issued = _portfolio(successor, claim, as_of=correction.evaluated_at)
    tampered = replace(
        issued,
        entries=(
            ClaimEvaluationPortfolioEntry(
                claim_id=claim.claim_id,
                evaluation_ids=(evaluation.evaluation_id,),
            ),
        ),
    )

    # dataclasses.replace preserves the private marker runtime type.  The
    # selection gate therefore must derive completeness from records rather
    # than trusting marker provenance or receipt-contained membership.
    assert tampered.validator_issued is True
    with pytest.raises(
        InvalidClaimEvaluationPortfolio,
        match="portfolio content does not match complete records-derived portfolio",
    ):
        validate_exact_claim_evaluation_selection_v1(
            records=successor,
            portfolio=tampered,
            selected_evaluation_ids=(evaluation.evaluation_id,),
        )


def test_public_receipt_subclass_cannot_forge_builder_authority(tmp_path) -> None:
    _, snapshot, evaluation, _, claim = _real_pr11_2_case(tmp_path)
    issued = _portfolio(snapshot, claim, as_of=evaluation.evaluated_at)

    class ForgedReceipt(ClaimEvaluationPortfolioReceipt):
        __slots__ = ()

        @property
        def validator_issued(self) -> bool:
            return True

    forged = ForgedReceipt(
        snapshot_sha256=issued.snapshot_sha256,
        subject_ref=issued.subject_ref,
        concept_ref=issued.concept_ref,
        as_of=issued.as_of,
        entries=issued.entries,
        excluded_future_claim_ids=issued.excluded_future_claim_ids,
        excluded_future_evaluation_ids=issued.excluded_future_evaluation_ids,
    )
    assert forged.validator_issued is True

    with pytest.raises(
        InvalidClaimEvaluationPortfolio,
        match="portfolio must be validator-issued",
    ):
        validate_exact_claim_evaluation_selection_v1(
            records=snapshot,
            portfolio=forged,
            selected_evaluation_ids=issued.admissible_evaluation_ids,
        )


def test_replaced_builder_receipt_cannot_hide_future_exclusion_metadata(tmp_path) -> None:
    _, snapshot, evaluation, _, claim = _real_pr11_2_case(tmp_path)
    future = _correction(
        evaluation,
        evaluation_id="evaluation_multi_bounded_reasoning_pr11_4_future_metadata",
        minutes=1,
    )
    successor = EpistemicRecordSet(
        evidence_records=snapshot.evidence_records,
        claims=snapshot.claims,
        evaluations=snapshot.evaluations + (future,),
    )
    validate_epistemic_snapshot_successor_v1(
        predecessor=snapshot,
        successor=successor,
    )
    issued = _portfolio(successor, claim, as_of=evaluation.evaluated_at)
    assert issued.excluded_future_evaluation_ids == (future.evaluation_id,)

    tampered = replace(issued, excluded_future_evaluation_ids=())
    assert tampered.validator_issued is True
    with pytest.raises(
        InvalidClaimEvaluationPortfolio,
        match="portfolio content does not match complete records-derived portfolio",
    ):
        validate_exact_claim_evaluation_selection_v1(
            records=successor,
            portfolio=tampered,
            selected_evaluation_ids=issued.admissible_evaluation_ids,
        )
