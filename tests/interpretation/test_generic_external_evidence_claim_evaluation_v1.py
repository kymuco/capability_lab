from dataclasses import replace
from datetime import datetime, timezone
import inspect

import pytest

from capability_lab.epistemics import (
    ActorRef,
    ClaimEvaluationId,
    ClaimScope,
    ConflictStatus,
    CoverageStatus,
    EpistemicRecordSet,
    EvaluationConclusion,
    EvaluatorKind,
    EvaluatorRef,
    EvidenceBearing,
    EvidenceContext,
    EvidenceId,
    EvidenceKind,
    EvidenceRecord,
    EvidenceReliability,
    ProvenanceSource,
    ProvenanceSourceKind,
    ProvenanceStep,
    ProvenanceTrail,
)
from capability_lab.interpretation import (
    ExternalEvidenceHumanClaimEvaluationDecision,
    ExternalEvidenceInterpretationProposalId,
    ExternalEvidenceInterpretationProposerKind,
    ExternalEvidenceInterpretationProposerRef,
    ExternalEvidenceInterpretationReviewId,
    ExternalEvidenceInterpretationReviewLedger,
    ExternalEvidenceInterpretationReviewerKind,
    ExternalEvidenceInterpretationReviewerRef,
    ExternalEvidenceInterpretationReviewVerdict,
    InvalidExternalEvidenceInterpretation,
    admit_external_evidence_claim_interpretation_review_v1,
    evaluate_materialized_external_evidence_claim_v1,
    external_evidence_claim_evaluation_admission_receipt_from_dict,
    external_evidence_claim_evaluation_admission_receipt_from_json,
    external_evidence_claim_evaluation_admission_receipt_sha256_v1,
    generic_external_evidence_claim_evaluation_sha256_v1,
    materialize_accepted_external_evidence_interpretation_claim_v1,
    propose_external_evidence_claim_interpretation_v1,
    review_external_evidence_claim_interpretation_v1,
    validate_external_evidence_claim_evaluation_admission_v1,
)
from capability_lab.observations import REVIEWED_EXTERNAL_OBSERVATION_TO_EVIDENCE_POLICY_V1
from capability_lab.semantics import (
    CapabilityCatalog,
    CapabilityConcept,
    CapabilityId,
    CapabilityNamespace,
)
from capability_lab.epistemics import CapabilitySubjectRef


def _time(hour: int) -> datetime:
    return datetime(2026, 8, 31, hour, 0, tzinfo=timezone.utc)


def _catalog() -> CapabilityCatalog:
    return CapabilityCatalog(
        namespaces=(
            CapabilityNamespace(
                namespace_id="research",
                display_name="Research",
                description="Research capabilities.",
            ),
        ),
        concepts=(
            CapabilityConcept(
                capability_id=CapabilityId.parse("research:signal_reasoning"),
                name="Signal reasoning",
                definition="Reason about structured technical signals and evidence.",
            ),
        ),
    )


def _external_evidence(hex_char: str = "a", *, summary: str = "Reviewed external artifact.") -> EvidenceRecord:
    evidence_id = EvidenceId("external_observation:" + hex_char * 64)
    return EvidenceRecord(
        evidence_id=evidence_id,
        subject_ref=CapabilitySubjectRef("subject-pr12-5"),
        kind=EvidenceKind.ARTIFACT,
        summary=summary,
        context=EvidenceContext(
            description="Reviewed generic external observation.",
            scope_tags=("external_observation",),
        ),
        observed_at=_time(10),
        recorded_at=_time(11),
        provenance=ProvenanceTrail(
            sources=(
                ProvenanceSource(ProvenanceSourceKind.EXTERNAL_RECORD, str(evidence_id)),
            ),
            steps=(
                ProvenanceStep(
                    operation_key="external_observation_materialize",
                    occurred_at=_time(11),
                    actor_ref=ActorRef("observation-reviewer"),
                    mechanism_ref=str(REVIEWED_EXTERNAL_OBSERVATION_TO_EVIDENCE_POLICY_V1),
                    note="Reviewed PR12.1 materialization.",
                ),
            ),
        ),
        outcome=None,
        payload_refs=("artifact-pr12-5",),
    )


def _basis():
    evidence = _external_evidence()
    predecessor = EpistemicRecordSet(evidence_records=(evidence,))
    catalog = _catalog()
    candidate = propose_external_evidence_claim_interpretation_v1(
        epistemic_snapshot=predecessor,
        evidence_id=evidence.evidence_id,
        catalog=catalog,
        concept_ref=catalog.concepts[0].ref,
        claim_statement="The subject can reason about bounded signal evidence.",
        claim_scope=ClaimScope(
            "Bounded interpretation of supplied signal evidence.",
            ("bounded_reasoning",),
        ),
        proposer_ref=ExternalEvidenceInterpretationProposerRef(
            ExternalEvidenceInterpretationProposerKind.MODEL,
            "model-pr12-5",
        ),
        proposal_id=ExternalEvidenceInterpretationProposalId("pr12-5-proposal"),
        proposed_at=_time(12),
        rationale="Exact retained artifact may concern the bounded claim.",
    )
    review = review_external_evidence_claim_interpretation_v1(
        epistemic_snapshot=predecessor,
        catalog=catalog,
        candidate=candidate,
        review_id=ExternalEvidenceInterpretationReviewId("pr12-5-review"),
        reviewer_ref=ExternalEvidenceInterpretationReviewerRef(
            ExternalEvidenceInterpretationReviewerKind.HUMAN,
            "interpretation-reviewer",
        ),
        verdict=ExternalEvidenceInterpretationReviewVerdict.ACCEPT,
        reviewed_at=_time(13),
        rationale="Accept this exact evidence-to-claim interpretation only.",
    )
    ledger = admit_external_evidence_claim_interpretation_review_v1(
        review_ledger=ExternalEvidenceInterpretationReviewLedger(),
        epistemic_snapshot=predecessor,
        catalog=catalog,
        candidate=candidate,
        review=review,
    )
    materialization = materialize_accepted_external_evidence_interpretation_claim_v1(
        epistemic_snapshot=predecessor,
        catalog=catalog,
        candidate=candidate,
        review_ledger=ledger,
    )
    return predecessor, catalog, candidate, ledger, materialization


def _decision(
    *,
    bearing=EvidenceBearing.SUPPORTS,
    reliability=EvidenceReliability.HIGH,
    coverage_status=CoverageStatus.PARTIAL,
    conclusion=EvaluationConclusion.INSUFFICIENT,
    evaluator_kind=EvaluatorKind.HUMAN,
    evaluator_ref="human-evaluator-pr12-5",
    evaluated_at=None,
):
    return ExternalEvidenceHumanClaimEvaluationDecision(
        evaluator_ref=EvaluatorRef(evaluator_kind, evaluator_ref),
        evaluated_at=evaluated_at or _time(14),
        bearing=bearing,
        reliability=reliability,
        coverage_status=coverage_status,
        conclusion=conclusion,
        evidence_coverage_note="This artifact addresses only part of the bounded claim.",
        claim_coverage_notes="Generic policy has no domain sufficiency rule.",
        evidence_rationale="The exact artifact is directionally relevant to the proposition.",
        evaluation_rationale="Retain evidence-level judgment while abstaining from claim-wide sufficiency.",
    )


def _evaluate(*, current=None, decision=None):
    predecessor, catalog, candidate, ledger, materialization = _basis()
    current = current or materialization.successor_snapshot
    decision = decision or _decision()
    result = evaluate_materialized_external_evidence_claim_v1(
        materialization_predecessor_snapshot=predecessor,
        current_epistemic_snapshot=current,
        catalog=catalog,
        candidate=candidate,
        review_ledger=ledger,
        materialization=materialization,
        decision=decision,
    )
    return predecessor, catalog, candidate, ledger, materialization, decision, result


def test_supporting_external_evidence_remains_claim_wide_insufficient():
    _, _, _, _, materialization, _, result = _evaluate()
    evaluation = result.evaluation

    assert evaluation.claim_id == materialization.claim.claim_id
    assert len(evaluation.evidence_assessments) == 1
    assert evaluation.evidence_assessments[0].bearing is EvidenceBearing.SUPPORTS
    assert evaluation.evidence_assessments[0].reliability is EvidenceReliability.HIGH
    assert evaluation.coverage.status is CoverageStatus.PARTIAL
    assert evaluation.conflict_status is ConflictStatus.NONE
    assert evaluation.conclusion is EvaluationConclusion.INSUFFICIENT
    assert result.succession_receipt.added_evaluation_ids == (evaluation.evaluation_id,)
    assert result.succession_receipt.added_evidence_ids == ()
    assert result.succession_receipt.added_claim_ids == ()
    assert result.successor_snapshot.claims == materialization.successor_snapshot.claims
    assert result.successor_snapshot.evidence_records == materialization.successor_snapshot.evidence_records


def test_contradicting_external_evidence_does_not_become_claim_wide_contradicted():
    decision = _decision(
        bearing=EvidenceBearing.CONTRADICTS,
        conclusion=EvaluationConclusion.ABSTAINED,
    )
    _, _, _, _, _, _, result = _evaluate(decision=decision)
    assert result.evaluation.evidence_assessments[0].bearing is EvidenceBearing.CONTRADICTS
    assert result.evaluation.conclusion is EvaluationConclusion.ABSTAINED
    assert result.evaluation.conclusion is not EvaluationConclusion.CONTRADICTED


@pytest.mark.parametrize(
    "conclusion",
    [
        EvaluationConclusion.SUPPORTED,
        EvaluationConclusion.CONTRADICTED,
        EvaluationConclusion.MIXED,
    ],
)
def test_generic_policy_rejects_directional_or_mixed_claim_conclusions(conclusion):
    with pytest.raises(InvalidExternalEvidenceInterpretation, match="cannot emit"):
        _decision(conclusion=conclusion)


def test_generic_policy_rejects_sufficient_for_claim_coverage():
    with pytest.raises(InvalidExternalEvidenceInterpretation, match="SUFFICIENT_FOR_CLAIM"):
        _decision(coverage_status=CoverageStatus.SUFFICIENT_FOR_CLAIM)


def test_generic_policy_rejects_unassessed_reliability():
    with pytest.raises(InvalidExternalEvidenceInterpretation, match="UNASSESSED"):
        _decision(reliability=EvidenceReliability.UNASSESSED)


@pytest.mark.parametrize(
    "kind",
    [EvaluatorKind.MODEL, EvaluatorKind.RULE, EvaluatorKind.EXTERNAL_SYSTEM],
)
def test_generic_policy_requires_explicit_human_evaluator(kind):
    with pytest.raises(InvalidExternalEvidenceInterpretation, match="HUMAN"):
        _decision(evaluator_kind=kind)


def test_public_api_exposes_no_evaluation_id_policy_conflict_or_evidence_selector():
    parameters = set(inspect.signature(evaluate_materialized_external_evidence_claim_v1).parameters)
    assert "evaluation_id" not in parameters
    assert "policy_ref" not in parameters
    assert "conflict_status" not in parameters
    assert "evidence_id" not in parameters
    decision_fields = set(ExternalEvidenceHumanClaimEvaluationDecision.__dataclass_fields__)
    assert not ({"evaluation_id", "policy_ref", "conflict_status", "evidence_id", "claim_id"} & decision_fields)


def test_exact_retry_from_same_current_basis_is_byte_identical():
    *_, first = _evaluate()
    *_, second = _evaluate()
    assert first.evaluation == second.evaluation
    assert first.evaluation.evaluation_id == second.evaluation.evaluation_id
    assert first.successor_snapshot.to_json() == second.successor_snapshot.to_json()
    assert first.admission_receipt.to_json() == second.admission_receipt.to_json()


def test_unrelated_later_epistemic_append_does_not_change_evaluation_identity():
    predecessor, catalog, candidate, ledger, materialization = _basis()
    baseline = evaluate_materialized_external_evidence_claim_v1(
        materialization_predecessor_snapshot=predecessor,
        current_epistemic_snapshot=materialization.successor_snapshot,
        catalog=catalog,
        candidate=candidate,
        review_ledger=ledger,
        materialization=materialization,
        decision=_decision(),
    )
    unrelated = _external_evidence("b", summary="Unrelated later external artifact.")
    extended = EpistemicRecordSet(
        evidence_records=materialization.successor_snapshot.evidence_records + (unrelated,),
        claims=materialization.successor_snapshot.claims,
        evaluations=materialization.successor_snapshot.evaluations,
    )
    replay = evaluate_materialized_external_evidence_claim_v1(
        materialization_predecessor_snapshot=predecessor,
        current_epistemic_snapshot=extended,
        catalog=catalog,
        candidate=candidate,
        review_ledger=ledger,
        materialization=materialization,
        decision=_decision(),
    )
    assert replay.evaluation == baseline.evaluation
    assert replay.evaluation.evaluation_id == baseline.evaluation.evaluation_id
    assert replay.admission_receipt.predecessor_snapshot_sha256 != baseline.admission_receipt.predecessor_snapshot_sha256


def test_mutated_retained_evidence_bytes_fail_current_lineage_validation():
    predecessor, catalog, candidate, ledger, materialization = _basis()
    mutated = replace(
        materialization.successor_snapshot.evidence_records[0],
        summary="Mutated retained bytes.",
    )
    current = EpistemicRecordSet(
        evidence_records=(mutated,),
        claims=materialization.successor_snapshot.claims,
    )
    with pytest.raises(InvalidExternalEvidenceInterpretation, match="append-only successor"):
        evaluate_materialized_external_evidence_claim_v1(
            materialization_predecessor_snapshot=predecessor,
            current_epistemic_snapshot=current,
            catalog=catalog,
            candidate=candidate,
            review_ledger=ledger,
            materialization=materialization,
            decision=_decision(),
        )


def test_forged_pr12_4_materialization_basis_fails_replay():
    predecessor, catalog, candidate, ledger, materialization = _basis()
    forged_claim = replace(
        materialization.claim,
        statement="Forged wider proposition.",
    )
    forged = replace(materialization, claim=forged_claim)
    with pytest.raises(InvalidExternalEvidenceInterpretation):
        evaluate_materialized_external_evidence_claim_v1(
            materialization_predecessor_snapshot=predecessor,
            current_epistemic_snapshot=materialization.successor_snapshot,
            catalog=catalog,
            candidate=candidate,
            review_ledger=ledger,
            materialization=forged,
            decision=_decision(),
        )


def test_evaluation_time_cannot_precede_claim_or_evidence_recording():
    predecessor, catalog, candidate, ledger, materialization = _basis()
    with pytest.raises(InvalidExternalEvidenceInterpretation, match="must not precede"):
        evaluate_materialized_external_evidence_claim_v1(
            materialization_predecessor_snapshot=predecessor,
            current_epistemic_snapshot=materialization.successor_snapshot,
            catalog=catalog,
            candidate=candidate,
            review_ledger=ledger,
            materialization=materialization,
            decision=_decision(evaluated_at=_time(12)),
        )


def test_rematerializing_same_deterministic_evaluation_into_successor_fails_closed():
    predecessor, catalog, candidate, ledger, materialization, decision, first = _evaluate()
    with pytest.raises(InvalidExternalEvidenceInterpretation, match="already exists"):
        evaluate_materialized_external_evidence_claim_v1(
            materialization_predecessor_snapshot=predecessor,
            current_epistemic_snapshot=first.successor_snapshot,
            catalog=catalog,
            candidate=candidate,
            review_ledger=ledger,
            materialization=materialization,
            decision=decision,
        )


def test_preexisting_same_evaluation_content_under_legacy_id_fails_closed():
    predecessor, catalog, candidate, ledger, materialization = _basis()
    first = evaluate_materialized_external_evidence_claim_v1(
        materialization_predecessor_snapshot=predecessor,
        current_epistemic_snapshot=materialization.successor_snapshot,
        catalog=catalog,
        candidate=candidate,
        review_ledger=ledger,
        materialization=materialization,
        decision=_decision(),
    )
    legacy = replace(
        first.evaluation,
        evaluation_id=ClaimEvaluationId("legacy:generic-external-evaluation"),
    )
    current = EpistemicRecordSet(
        evidence_records=materialization.successor_snapshot.evidence_records,
        claims=materialization.successor_snapshot.claims,
        evaluations=(legacy,),
    )
    with pytest.raises(InvalidExternalEvidenceInterpretation, match="semantically identical"):
        evaluate_materialized_external_evidence_claim_v1(
            materialization_predecessor_snapshot=predecessor,
            current_epistemic_snapshot=current,
            catalog=catalog,
            candidate=candidate,
            review_ledger=ledger,
            materialization=materialization,
            decision=_decision(),
        )


def test_distinct_human_evaluation_is_allowed_for_same_claim_and_evidence():
    predecessor, catalog, candidate, ledger, materialization = _basis()
    first = evaluate_materialized_external_evidence_claim_v1(
        materialization_predecessor_snapshot=predecessor,
        current_epistemic_snapshot=materialization.successor_snapshot,
        catalog=catalog,
        candidate=candidate,
        review_ledger=ledger,
        materialization=materialization,
        decision=_decision(),
    )
    second = evaluate_materialized_external_evidence_claim_v1(
        materialization_predecessor_snapshot=predecessor,
        current_epistemic_snapshot=first.successor_snapshot,
        catalog=catalog,
        candidate=candidate,
        review_ledger=ledger,
        materialization=materialization,
        decision=_decision(
            bearing=EvidenceBearing.INDETERMINATE,
            reliability=EvidenceReliability.MODERATE,
            conclusion=EvaluationConclusion.ABSTAINED,
            evaluator_ref="second-human-evaluator",
            evaluated_at=_time(15),
        ),
    )
    assert second.evaluation.evaluation_id != first.evaluation.evaluation_id
    assert len(second.successor_snapshot.evaluations) == 2


def test_admission_receipt_round_trip_and_digest_are_deterministic():
    *_, result = _evaluate()
    payload = result.admission_receipt.to_json()
    restored = external_evidence_claim_evaluation_admission_receipt_from_json(payload)
    assert restored == result.admission_receipt
    assert restored.to_json() == payload
    assert (
        external_evidence_claim_evaluation_admission_receipt_sha256_v1(restored)
        == external_evidence_claim_evaluation_admission_receipt_sha256_v1(result.admission_receipt)
    )
    assert generic_external_evidence_claim_evaluation_sha256_v1(result.evaluation) == result.admission_receipt.evaluation_sha256


def test_receipt_serialization_rejects_unknown_missing_and_duplicate_fields():
    *_, result = _evaluate()
    obj = result.admission_receipt.to_dict()

    unknown = dict(obj)
    unknown["state_authority"] = True
    with pytest.raises(InvalidExternalEvidenceInterpretation, match="unknown"):
        external_evidence_claim_evaluation_admission_receipt_from_dict(unknown)

    missing = dict(obj)
    missing.pop("evaluation_sha256")
    with pytest.raises(InvalidExternalEvidenceInterpretation, match="missing"):
        external_evidence_claim_evaluation_admission_receipt_from_dict(missing)

    duplicate = result.admission_receipt.to_json().replace(
        '"schema_version":1',
        '"schema_version":1,"schema_version":1',
        1,
    )
    with pytest.raises(InvalidExternalEvidenceInterpretation, match="duplicate JSON"):
        external_evidence_claim_evaluation_admission_receipt_from_json(duplicate)


def test_forged_admission_receipt_fails_full_replay_validation():
    predecessor, catalog, candidate, ledger, materialization, decision, result = _evaluate()
    forged = replace(
        result,
        admission_receipt=replace(
            result.admission_receipt,
            evaluation_sha256="0" * 64,
        ),
    )
    with pytest.raises(InvalidExternalEvidenceInterpretation, match="admission_receipt"):
        validate_external_evidence_claim_evaluation_admission_v1(
            materialization_predecessor_snapshot=predecessor,
            current_epistemic_snapshot=materialization.successor_snapshot,
            catalog=catalog,
            candidate=candidate,
            review_ledger=ledger,
            materialization=materialization,
            decision=decision,
            admission=forged,
        )


def test_malformed_decision_fails_closed_before_evaluation():
    predecessor, catalog, candidate, ledger, materialization = _basis()
    with pytest.raises(InvalidExternalEvidenceInterpretation, match="exact ExternalEvidenceHumanClaimEvaluationDecision"):
        evaluate_materialized_external_evidence_claim_v1(
            materialization_predecessor_snapshot=predecessor,
            current_epistemic_snapshot=materialization.successor_snapshot,
            catalog=catalog,
            candidate=candidate,
            review_ledger=ledger,
            materialization=materialization,
            decision=object(),
        )
