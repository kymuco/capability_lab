import pytest

from capability_lab.epistemics import (
    EpistemicRecordSet,
    InvalidEpistemicSnapshotSuccessor,
    validate_epistemic_snapshot_successor_v1,
)
from capability_lab.observations import (
    resolve_reviewed_external_observation_evidence_materialization_v1,
)

from test_external_observation_materialization_v1 import _candidate, _ledger, _review


def test_materialized_observation_hands_off_to_pr11_3_as_one_exact_evidence_append():
    ledger = _ledger()
    candidate = _candidate(ledger)
    review = _review(candidate)
    evidence, _ = resolve_reviewed_external_observation_evidence_materialization_v1(
        ledger=ledger,
        candidate=candidate,
        review=review,
    )
    predecessor = EpistemicRecordSet()
    successor = EpistemicRecordSet(evidence_records=(evidence,))
    receipt = validate_epistemic_snapshot_successor_v1(
        predecessor=predecessor,
        successor=successor,
    )
    assert receipt.validator_issued
    assert receipt.added_evidence_ids == (evidence.evidence_id,)
    assert receipt.retained_evidence_ids == ()


def test_same_observation_second_resolution_has_same_id_and_cannot_replace_appended_record():
    ledger = _ledger()
    first_candidate = _candidate(ledger, materialization_id="mat-first")
    first_review = _review(first_candidate, review_id="review-first")
    first_evidence, _ = resolve_reviewed_external_observation_evidence_materialization_v1(
        ledger=ledger,
        candidate=first_candidate,
        review=first_review,
    )
    second_candidate = _candidate(ledger, materialization_id="mat-second")
    second_review = _review(second_candidate, review_id="review-second", seconds=2)
    second_evidence, _ = resolve_reviewed_external_observation_evidence_materialization_v1(
        ledger=ledger,
        candidate=second_candidate,
        review=second_review,
    )
    assert first_evidence.evidence_id == second_evidence.evidence_id
    assert first_evidence != second_evidence
    predecessor = EpistemicRecordSet(evidence_records=(first_evidence,))
    replacement = EpistemicRecordSet(evidence_records=(second_evidence,))
    with pytest.raises(
        InvalidEpistemicSnapshotSuccessor,
        match="may not mutate retained evidence record",
    ):
        validate_epistemic_snapshot_successor_v1(
            predecessor=predecessor,
            successor=replacement,
        )


def test_same_observation_cannot_be_allocated_distinct_evidence_ids():
    ledger = _ledger()
    first = _candidate(ledger, materialization_id="mat-one")
    second = _candidate(ledger, materialization_id="mat-two")
    assert first.materialized_evidence_id == second.materialized_evidence_id
