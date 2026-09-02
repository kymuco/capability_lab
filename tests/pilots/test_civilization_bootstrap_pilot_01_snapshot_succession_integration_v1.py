from dataclasses import fields, replace
from datetime import timedelta

import pytest

from capability_lab.epistemics import (
    CapabilitySubjectRef,
    ClaimEvaluationId,
    CoverageStatus,
    EpistemicRecordSet,
    EvaluationConclusion,
    EvidenceBearing,
    EvidenceReliability,
    InvalidEpistemicSnapshotSuccessor,
    validate_epistemic_snapshot_successor_v1,
)

from test_civilization_bootstrap_pilot_01_claim_evaluation_multi_v1 import (
    _basis,
    _claim,
    _decision,
    _evaluate,
)
from test_civilization_bootstrap_pilot_01_terminal_dependence_v1 import (
    _case as _terminal_case,
)


def _real_pr11_2_case(tmp_path):
    case = _terminal_case(tmp_path)
    entries = tuple(case["selection_entries"])
    claim = _claim(subject_ref=CapabilitySubjectRef("subject_terminal_01"))
    decision = _decision(
        claim=claim,
        entries=entries,
        coverage_status=CoverageStatus.PARTIAL,
        conclusion=EvaluationConclusion.INSUFFICIENT,
    )
    evaluation = _evaluate(claim=claim, decision=decision, case=case)
    evidence_records = tuple(
        sorted(
            (_basis(entry).evidence for entry in entries),
            key=lambda item: item.evidence_id,
        )
    )
    predecessor = EpistemicRecordSet(
        evidence_records=evidence_records,
        claims=(claim,),
    )
    successor = EpistemicRecordSet(
        evidence_records=evidence_records,
        claims=(claim,),
        evaluations=(evaluation,),
    )
    return predecessor, successor, evaluation, evidence_records, claim


def test_real_pr11_2_multi_evidence_evaluation_can_be_appended_as_new_epistemic_identity(
    tmp_path,
) -> None:
    predecessor, successor, evaluation, _, _ = _real_pr11_2_case(tmp_path)

    receipt = validate_epistemic_snapshot_successor_v1(
        predecessor=predecessor,
        successor=successor,
    )

    assert receipt.retained_evidence_ids == tuple(
        item.evidence_id for item in predecessor.evidence_records
    )
    assert receipt.retained_claim_ids == tuple(item.claim_id for item in predecessor.claims)
    assert receipt.added_evaluation_ids == (evaluation.evaluation_id,)


def test_real_pr11_2_snapshot_can_be_revalidated_idempotently(tmp_path) -> None:
    _, snapshot, evaluation, _, _ = _real_pr11_2_case(tmp_path)

    receipt = validate_epistemic_snapshot_successor_v1(
        predecessor=snapshot,
        successor=snapshot,
    )

    assert receipt.predecessor_sha256 == receipt.successor_sha256
    assert receipt.retained_evaluation_ids == (evaluation.evaluation_id,)
    assert receipt.added_evaluation_ids == ()


def test_same_pr11_2_evaluation_id_cannot_change_assessment_reliability(tmp_path) -> None:
    _, snapshot, evaluation, _, _ = _real_pr11_2_case(tmp_path)
    first, *rest = evaluation.evidence_assessments
    replacement = replace(
        evaluation,
        evidence_assessments=(
            replace(
                first,
                reliability=(
                    EvidenceReliability.HIGH
                    if first.reliability is not EvidenceReliability.HIGH
                    else EvidenceReliability.LOW
                ),
            ),
            *rest,
        ),
    )
    successor = EpistemicRecordSet(
        evidence_records=snapshot.evidence_records,
        claims=snapshot.claims,
        evaluations=(replacement,),
    )

    with pytest.raises(
        InvalidEpistemicSnapshotSuccessor,
        match="may not mutate retained claim evaluation",
    ):
        validate_epistemic_snapshot_successor_v1(
            predecessor=snapshot,
            successor=successor,
        )


def test_same_pr11_2_evaluation_id_cannot_change_assessment_bearing(tmp_path) -> None:
    _, snapshot, evaluation, _, _ = _real_pr11_2_case(tmp_path)
    first, *rest = evaluation.evidence_assessments
    replacement = replace(
        evaluation,
        evidence_assessments=(
            replace(first, bearing=EvidenceBearing.INDETERMINATE),
            *rest,
        ),
    )
    successor = EpistemicRecordSet(
        evidence_records=snapshot.evidence_records,
        claims=snapshot.claims,
        evaluations=(replacement,),
    )

    with pytest.raises(
        InvalidEpistemicSnapshotSuccessor,
        match="may not mutate retained claim evaluation",
    ):
        validate_epistemic_snapshot_successor_v1(
            predecessor=snapshot,
            successor=successor,
        )


def test_same_pr11_2_evaluation_id_cannot_change_conclusion(tmp_path) -> None:
    _, snapshot, evaluation, _, _ = _real_pr11_2_case(tmp_path)
    replacement = replace(
        evaluation,
        conclusion=EvaluationConclusion.ABSTAINED,
    )
    successor = EpistemicRecordSet(
        evidence_records=snapshot.evidence_records,
        claims=snapshot.claims,
        evaluations=(replacement,),
    )

    with pytest.raises(
        InvalidEpistemicSnapshotSuccessor,
        match="may not mutate retained claim evaluation",
    ):
        validate_epistemic_snapshot_successor_v1(
            predecessor=snapshot,
            successor=successor,
        )


def test_terminal_basis_evidence_identity_cannot_disappear_from_successor(tmp_path) -> None:
    _, snapshot, _, evidence_records, claim = _real_pr11_2_case(tmp_path)
    removed = evidence_records[0]
    successor = EpistemicRecordSet(
        evidence_records=tuple(
            item for item in evidence_records if item.evidence_id != removed.evidence_id
        ),
        claims=(claim,),
    )

    with pytest.raises(
        InvalidEpistemicSnapshotSuccessor,
        match="may not remove evidence record",
    ):
        validate_epistemic_snapshot_successor_v1(
            predecessor=snapshot,
            successor=successor,
        )


def test_terminal_basis_evidence_identity_cannot_acquire_changed_content(tmp_path) -> None:
    _, snapshot, evaluation, evidence_records, claim = _real_pr11_2_case(tmp_path)
    original = evidence_records[0]
    mutated = replace(
        original,
        summary=original.summary + " Mutated after persistence.",
    )
    successor = EpistemicRecordSet(
        evidence_records=(mutated,) + evidence_records[1:],
        claims=(claim,),
        evaluations=(evaluation,),
    )

    with pytest.raises(
        InvalidEpistemicSnapshotSuccessor,
        match="may not mutate retained evidence record",
    ):
        validate_epistemic_snapshot_successor_v1(
            predecessor=snapshot,
            successor=successor,
        )


def test_correction_is_append_only_new_evaluation_identity_not_supersession(tmp_path) -> None:
    _, snapshot, evaluation, _, _ = _real_pr11_2_case(tmp_path)
    correction = replace(
        evaluation,
        evaluation_id=ClaimEvaluationId("evaluation_multi_bounded_reasoning_correction"),
        evaluated_at=evaluation.evaluated_at + timedelta(minutes=1),
        conclusion=EvaluationConclusion.ABSTAINED,
        rationale="Explicit correction appended under a new immutable evaluation identity.",
    )
    successor = EpistemicRecordSet(
        evidence_records=snapshot.evidence_records,
        claims=snapshot.claims,
        evaluations=snapshot.evaluations + (correction,),
    )

    receipt = validate_epistemic_snapshot_successor_v1(
        predecessor=snapshot,
        successor=successor,
    )

    assert receipt.retained_evaluation_ids == (evaluation.evaluation_id,)
    assert receipt.added_evaluation_ids == (correction.evaluation_id,)
    assert evaluation in successor.evaluations
    receipt_fields = {item.name for item in fields(type(receipt))}
    assert {
        "superseded_ids",
        "selected_evaluation_ids",
        "preferred_evaluation_id",
        "active_evaluation_id",
    }.isdisjoint(receipt_fields)


def test_pr11_3_receipt_does_not_reinterpret_pr11_2_terminal_pass_as_state_authority(
    tmp_path,
) -> None:
    predecessor, successor, _, _, _ = _real_pr11_2_case(tmp_path)

    receipt = validate_epistemic_snapshot_successor_v1(
        predecessor=predecessor,
        successor=successor,
    )

    assert not hasattr(receipt, "personal_capability_state")
    assert not hasattr(receipt, "mastery")
    assert not hasattr(receipt, "score")
    assert not hasattr(receipt, "confidence")
