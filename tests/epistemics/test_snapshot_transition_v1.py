from dataclasses import fields, replace
from datetime import datetime, timedelta, timezone
import json
import unicodedata

import pytest

from capability_lab.epistemics import (
    ActorRef,
    CapabilityClaim,
    CapabilityClaimId,
    CapabilitySubjectRef,
    ClaimEvaluation,
    ClaimEvaluationId,
    ClaimScope,
    ConflictStatus,
    ContextFactor,
    ContextFactorKind,
    CoverageAssessment,
    CoverageStatus,
    EpistemicRecordSet,
    EpistemicSnapshotSuccessionReceipt,
    EvaluationConclusion,
    EvaluationPolicyRef,
    EvaluatorKind,
    EvaluatorRef,
    EvidenceAssessment,
    EvidenceBearing,
    EvidenceContext,
    EvidenceId,
    EvidenceKind,
    EvidenceOutcome,
    EvidenceOutcomeStatus,
    EvidenceRecord,
    EvidenceReliability,
    InvalidEpistemicSnapshotSuccessor,
    ProvenanceSource,
    ProvenanceSourceKind,
    ProvenanceStep,
    ProvenanceTrail,
    epistemic_snapshot_sha256_v1,
    validate_epistemic_snapshot_successor_v1,
)
from capability_lab.semantics import CapabilityConceptRef


T0 = datetime(2026, 8, 20, 9, 0, tzinfo=timezone.utc)
ALICE = CapabilitySubjectRef("alice_pr11_3")
BOB = CapabilitySubjectRef("bob_pr11_3")
EMPTY_SHA256_V1 = "b775413096e9acc7f7d5514e904e44cafff4c29aa9af542bdeba3df3244c3a40"


def _trail(ref: str = "reviewer_pr11_3") -> ProvenanceTrail:
    return ProvenanceTrail(
        sources=(ProvenanceSource(ProvenanceSourceKind.ACTOR, ref),),
    )


def _trail_with_step(ref: str = "reviewer_pr11_3") -> ProvenanceTrail:
    return ProvenanceTrail(
        sources=(ProvenanceSource(ProvenanceSourceKind.ACTOR, ref),),
        steps=(
            ProvenanceStep(
                operation_key="review",
                occurred_at=T0,
                actor_ref=ActorRef(ref),
                mechanism_ref="manual_review",
                note="Reviewed under bounded conditions.",
            ),
        ),
    )


def _evidence(
    evidence_id: str,
    *,
    subject_ref: CapabilitySubjectRef = ALICE,
    summary: str | None = None,
    observed_at: datetime | None = None,
    recorded_at: datetime | None = None,
    provenance: ProvenanceTrail | None = None,
) -> EvidenceRecord:
    observed = T0 + timedelta(minutes=1) if observed_at is None else observed_at
    recorded = T0 + timedelta(minutes=2) if recorded_at is None else recorded_at
    return EvidenceRecord(
        evidence_id=EvidenceId(evidence_id),
        subject_ref=subject_ref,
        kind=EvidenceKind.PROJECT,
        summary=summary or f"Observation {evidence_id}.",
        context=EvidenceContext(
            "Bounded bench context.",
            ("low_voltage_dc", "pilot"),
            (ContextFactor(ContextFactorKind.REFERENCE_MATERIAL, "Reference sheet."),),
        ),
        observed_at=observed,
        recorded_at=recorded,
        provenance=provenance or _trail(),
        outcome=EvidenceOutcome(EvidenceOutcomeStatus.SUCCESS, "Observed successfully."),
        payload_refs=(f"payload:{evidence_id}",),
    )


def _claim(
    claim_id: str,
    *,
    subject_ref: CapabilitySubjectRef = ALICE,
    statement: str | None = None,
    created_at: datetime | None = None,
) -> CapabilityClaim:
    return CapabilityClaim(
        claim_id=CapabilityClaimId(claim_id),
        subject_ref=subject_ref,
        concept_ref=CapabilityConceptRef.parse(
            "civilization_bootstrap:basic_electricity@1"
        ),
        statement=statement or f"Claim {claim_id}.",
        scope=ClaimScope(
            "Bounded low-voltage DC scope.",
            ("basic_electricity", "low_voltage_dc"),
        ),
        created_at=T0 + timedelta(minutes=5) if created_at is None else created_at,
        provenance=_trail("claim_author_pr11_3"),
    )


def _evaluation(
    *,
    evaluation_id: str = "evaluation_main",
    claim_id: str = "claim_main",
    evidence_ids: tuple[str, ...] = ("evidence_a", "evidence_b"),
) -> ClaimEvaluation:
    assessments = tuple(
        EvidenceAssessment(
            EvidenceId(evidence_id),
            EvidenceBearing.SUPPORTS,
            EvidenceReliability.MODERATE if index == 0 else EvidenceReliability.HIGH,
            f"Coverage note {evidence_id}.",
            f"Rationale {evidence_id}.",
        )
        for index, evidence_id in enumerate(evidence_ids)
    )
    return ClaimEvaluation(
        evaluation_id=ClaimEvaluationId(evaluation_id),
        claim_id=CapabilityClaimId(claim_id),
        policy_ref=EvaluationPolicyRef.parse("core:manual_evidence_review@1"),
        evaluator_ref=EvaluatorRef(EvaluatorKind.HUMAN, "reviewer_pr11_3"),
        evaluated_at=T0 + timedelta(minutes=10),
        evidence_assessments=assessments,
        coverage=CoverageAssessment(
            CoverageStatus.SUFFICIENT_FOR_CLAIM,
            "Exact bounded basis reviewed.",
        ),
        conflict_status=ConflictStatus.NONE,
        conclusion=EvaluationConclusion.SUPPORTED,
        rationale="Supported within the bounded scope.",
    )


def _base_snapshot() -> EpistemicRecordSet:
    return EpistemicRecordSet(
        evidence_records=(
            _evidence("evidence_c"),
            _evidence("evidence_b"),
            _evidence("evidence_a"),
        ),
        claims=(
            _claim("claim_extra"),
            _claim("claim_main"),
        ),
        evaluations=(_evaluation(),),
    )


def _replace_evidence(
    snapshot: EpistemicRecordSet,
    evidence_id: str,
    replacement: EvidenceRecord,
) -> EpistemicRecordSet:
    records = tuple(
        replacement if str(item.evidence_id) == evidence_id else item
        for item in snapshot.evidence_records
    )
    return EpistemicRecordSet(
        evidence_records=records,
        claims=snapshot.claims,
        evaluations=snapshot.evaluations,
    )


def _replace_claim(
    snapshot: EpistemicRecordSet,
    claim_id: str,
    replacement: CapabilityClaim,
) -> EpistemicRecordSet:
    claims = tuple(
        replacement if str(item.claim_id) == claim_id else item
        for item in snapshot.claims
    )
    return EpistemicRecordSet(
        evidence_records=snapshot.evidence_records,
        claims=claims,
        evaluations=snapshot.evaluations,
    )


def _replace_evaluation(
    snapshot: EpistemicRecordSet,
    replacement: ClaimEvaluation,
    *,
    extra_evidence: tuple[EvidenceRecord, ...] = (),
    extra_claims: tuple[CapabilityClaim, ...] = (),
) -> EpistemicRecordSet:
    evaluations = tuple(
        replacement if item.evaluation_id == replacement.evaluation_id else item
        for item in snapshot.evaluations
    )
    return EpistemicRecordSet(
        evidence_records=snapshot.evidence_records + extra_evidence,
        claims=snapshot.claims + extra_claims,
        evaluations=evaluations,
    )


def _assert_mutation_rejected(
    predecessor: EpistemicRecordSet,
    successor: EpistemicRecordSet,
    label: str,
) -> None:
    with pytest.raises(
        InvalidEpistemicSnapshotSuccessor,
        match=rf"may not mutate retained {label}",
    ):
        validate_epistemic_snapshot_successor_v1(
            predecessor=predecessor,
            successor=successor,
        )


def test_snapshot_hash_rejects_non_record_set() -> None:
    with pytest.raises(
        InvalidEpistemicSnapshotSuccessor,
        match="snapshot must be EpistemicRecordSet",
    ):
        epistemic_snapshot_sha256_v1(object())  # type: ignore[arg-type]


def test_empty_snapshot_fingerprint_is_frozen() -> None:
    assert epistemic_snapshot_sha256_v1(EpistemicRecordSet()) == EMPTY_SHA256_V1


def test_snapshot_fingerprint_roundtrip_is_stable() -> None:
    snapshot = _base_snapshot()
    assert (
        epistemic_snapshot_sha256_v1(EpistemicRecordSet.from_json(snapshot.to_json()))
        == epistemic_snapshot_sha256_v1(snapshot)
    )


def test_snapshot_fingerprint_ignores_construction_order_after_typed_normalization() -> None:
    first = _base_snapshot()
    second = EpistemicRecordSet(
        evidence_records=tuple(reversed(first.evidence_records)),
        claims=tuple(reversed(first.claims)),
        evaluations=tuple(reversed(first.evaluations)),
    )
    assert first == second
    assert epistemic_snapshot_sha256_v1(first) == epistemic_snapshot_sha256_v1(second)


def test_snapshot_fingerprint_ignores_json_whitespace_and_object_key_order_after_parse() -> None:
    snapshot = _base_snapshot()
    payload = snapshot.to_dict()
    reordered = {
        "evaluations": payload["evaluations"],
        "schema": payload["schema"],
        "claims": payload["claims"],
        "evidence_records": payload["evidence_records"],
    }
    alternative_json = json.dumps(reordered, ensure_ascii=False, indent=2)
    reconstructed = EpistemicRecordSet.from_json(alternative_json)
    assert epistemic_snapshot_sha256_v1(reconstructed) == epistemic_snapshot_sha256_v1(snapshot)


def test_snapshot_fingerprint_changes_when_canonical_content_changes() -> None:
    first = _base_snapshot()
    evidence_c = next(
        item for item in first.evidence_records if item.evidence_id == EvidenceId("evidence_c")
    )
    second = _replace_evidence(
        first,
        "evidence_c",
        replace(evidence_c, summary="Changed canonical content."),
    )
    assert epistemic_snapshot_sha256_v1(first) != epistemic_snapshot_sha256_v1(second)


def test_noop_successor_is_allowed_and_receipt_retains_every_identity() -> None:
    snapshot = _base_snapshot()
    receipt = validate_epistemic_snapshot_successor_v1(
        predecessor=snapshot,
        successor=snapshot,
    )
    assert receipt.predecessor_sha256 == receipt.successor_sha256
    assert receipt.retained_evidence_ids == tuple(
        item.evidence_id for item in snapshot.evidence_records
    )
    assert receipt.retained_claim_ids == tuple(item.claim_id for item in snapshot.claims)
    assert receipt.retained_evaluation_ids == tuple(
        item.evaluation_id for item in snapshot.evaluations
    )
    assert receipt.added_evidence_ids == ()
    assert receipt.added_claim_ids == ()
    assert receipt.added_evaluation_ids == ()


def test_empty_to_one_evidence_is_allowed() -> None:
    successor = EpistemicRecordSet(evidence_records=(_evidence("new_evidence"),))
    receipt = validate_epistemic_snapshot_successor_v1(
        predecessor=EpistemicRecordSet(),
        successor=successor,
    )
    assert receipt.added_evidence_ids == (EvidenceId("new_evidence"),)


def test_append_claim_is_allowed() -> None:
    predecessor = EpistemicRecordSet(evidence_records=(_evidence("evidence_a"),))
    successor = EpistemicRecordSet(
        evidence_records=predecessor.evidence_records,
        claims=(_claim("claim_new"),),
    )
    receipt = validate_epistemic_snapshot_successor_v1(
        predecessor=predecessor,
        successor=successor,
    )
    assert receipt.added_claim_ids == (CapabilityClaimId("claim_new"),)


def test_append_evaluation_is_allowed() -> None:
    evidence_records = (_evidence("evidence_a"), _evidence("evidence_b"))
    claims = (_claim("claim_main"),)
    predecessor = EpistemicRecordSet(
        evidence_records=evidence_records,
        claims=claims,
    )
    successor = EpistemicRecordSet(
        evidence_records=evidence_records,
        claims=claims,
        evaluations=(_evaluation(),),
    )
    receipt = validate_epistemic_snapshot_successor_v1(
        predecessor=predecessor,
        successor=successor,
    )
    assert receipt.added_evaluation_ids == (ClaimEvaluationId("evaluation_main"),)


def test_append_evidence_claim_and_evaluation_together_is_allowed() -> None:
    predecessor = EpistemicRecordSet()
    successor = EpistemicRecordSet(
        evidence_records=(_evidence("evidence_a"), _evidence("evidence_b")),
        claims=(_claim("claim_main"),),
        evaluations=(_evaluation(),),
    )
    receipt = validate_epistemic_snapshot_successor_v1(
        predecessor=predecessor,
        successor=successor,
    )
    assert len(receipt.added_evidence_ids) == 2
    assert receipt.added_claim_ids == (CapabilityClaimId("claim_main"),)
    assert receipt.added_evaluation_ids == (ClaimEvaluationId("evaluation_main"),)


@pytest.mark.parametrize(
    ("family", "expected"),
    (
        ("evidence", "evidence record"),
        ("claim", "capability claim"),
        ("evaluation", "claim evaluation"),
    ),
)
def test_removal_of_any_persisted_record_family_is_rejected(family, expected) -> None:
    predecessor = _base_snapshot()
    if family == "evidence":
        successor = EpistemicRecordSet(
            evidence_records=tuple(
                item
                for item in predecessor.evidence_records
                if item.evidence_id != EvidenceId("evidence_c")
            ),
            claims=predecessor.claims,
            evaluations=predecessor.evaluations,
        )
    elif family == "claim":
        successor = EpistemicRecordSet(
            evidence_records=predecessor.evidence_records,
            claims=tuple(
                item
                for item in predecessor.claims
                if item.claim_id != CapabilityClaimId("claim_extra")
            ),
            evaluations=predecessor.evaluations,
        )
    else:
        successor = EpistemicRecordSet(
            evidence_records=predecessor.evidence_records,
            claims=predecessor.claims,
        )

    with pytest.raises(
        InvalidEpistemicSnapshotSuccessor,
        match=rf"may not remove {expected}",
    ):
        validate_epistemic_snapshot_successor_v1(
            predecessor=predecessor,
            successor=successor,
        )


def test_removal_remains_rejected_even_when_unrelated_new_record_is_added() -> None:
    predecessor = _base_snapshot()
    successor = EpistemicRecordSet(
        evidence_records=tuple(
            item
            for item in predecessor.evidence_records
            if item.evidence_id != EvidenceId("evidence_c")
        )
        + (_evidence("evidence_d"),),
        claims=predecessor.claims,
        evaluations=predecessor.evaluations,
    )
    with pytest.raises(InvalidEpistemicSnapshotSuccessor, match="may not remove evidence"):
        validate_epistemic_snapshot_successor_v1(
            predecessor=predecessor,
            successor=successor,
        )


@pytest.mark.parametrize(
    "mutator",
    (
        lambda value: replace(value, subject_ref=BOB),
        lambda value: replace(value, kind=EvidenceKind.ARTIFACT),
        lambda value: replace(value, summary="Mutated summary."),
        lambda value: replace(
            value,
            context=replace(value.context, description="Mutated context."),
        ),
        lambda value: replace(
            value,
            context=replace(value.context, scope_tags=("different_scope",)),
        ),
        lambda value: replace(
            value,
            context=replace(
                value.context,
                factors=(
                    ContextFactor(ContextFactorKind.TOOL, "Bench meter."),
                ),
            ),
        ),
        lambda value: replace(
            value,
            observation_started_at=value.observed_at - timedelta(minutes=1),
        ),
        lambda value: replace(value, observed_at=value.observed_at - timedelta(seconds=1)),
        lambda value: replace(value, recorded_at=value.recorded_at + timedelta(seconds=1)),
        lambda value: replace(value, provenance=_trail("different_actor")),
        lambda value: replace(value, provenance=_trail_with_step("reviewer_pr11_3")),
        lambda value: replace(
            value,
            outcome=EvidenceOutcome(EvidenceOutcomeStatus.FAILURE, "Different outcome."),
        ),
        lambda value: replace(value, payload_refs=("payload:changed",)),
    ),
)
def test_every_evidence_content_mutation_is_rejected(mutator) -> None:
    predecessor = _base_snapshot()
    original = next(
        item for item in predecessor.evidence_records if item.evidence_id == EvidenceId("evidence_c")
    )
    successor = _replace_evidence(
        predecessor,
        "evidence_c",
        mutator(original),
    )
    _assert_mutation_rejected(predecessor, successor, "evidence record")


@pytest.mark.parametrize(
    "mutator",
    (
        lambda value: replace(value, subject_ref=BOB),
        lambda value: replace(
            value,
            concept_ref=CapabilityConceptRef.parse(
                "civilization_bootstrap:basic_electricity@2"
            ),
        ),
        lambda value: replace(value, statement="Mutated claim statement."),
        lambda value: replace(
            value,
            scope=replace(value.scope, description="Mutated scope."),
        ),
        lambda value: replace(
            value,
            scope=replace(value.scope, tags=("changed_scope",)),
        ),
        lambda value: replace(value, created_at=value.created_at + timedelta(seconds=1)),
        lambda value: replace(
            value,
            provenance=ProvenanceTrail(
                sources=(
                    ProvenanceSource(ProvenanceSourceKind.SYSTEM, "changed_claim_source"),
                )
            ),
        ),
    ),
)
def test_every_claim_content_mutation_is_rejected(mutator) -> None:
    predecessor = _base_snapshot()
    original = next(
        item for item in predecessor.claims if item.claim_id == CapabilityClaimId("claim_extra")
    )
    successor = _replace_claim(
        predecessor,
        "claim_extra",
        mutator(original),
    )
    _assert_mutation_rejected(predecessor, successor, "capability claim")


def _mutated_evaluation_cases(
    predecessor: EpistemicRecordSet,
) -> tuple[EpistemicRecordSet, ...]:
    original = predecessor.evaluations[0]
    first_assessment, second_assessment = original.evidence_assessments
    new_claim = _claim("claim_alternative")
    evidence_d = _evidence("evidence_d")

    return (
        _replace_evaluation(
            predecessor,
            replace(original, claim_id=new_claim.claim_id),
            extra_claims=(new_claim,),
        ),
        _replace_evaluation(
            predecessor,
            replace(
                original,
                policy_ref=EvaluationPolicyRef.parse("core:manual_evidence_review@2"),
            ),
        ),
        _replace_evaluation(
            predecessor,
            replace(
                original,
                evaluator_ref=EvaluatorRef(EvaluatorKind.MODEL, "model_reviewer"),
            ),
        ),
        _replace_evaluation(
            predecessor,
            replace(
                original,
                evaluator_ref=EvaluatorRef(EvaluatorKind.HUMAN, "other_reviewer"),
            ),
        ),
        _replace_evaluation(
            predecessor,
            replace(original, evaluated_at=original.evaluated_at + timedelta(seconds=1)),
        ),
        _replace_evaluation(
            predecessor,
            replace(
                original,
                evidence_assessments=original.evidence_assessments
                + (
                    EvidenceAssessment(
                        EvidenceId("evidence_d"),
                        EvidenceBearing.INDETERMINATE,
                        EvidenceReliability.LOW,
                        "Additional coverage.",
                        "Additional rationale.",
                    ),
                ),
            ),
            extra_evidence=(evidence_d,),
        ),
        _replace_evaluation(
            predecessor,
            replace(original, evidence_assessments=(first_assessment,)),
        ),
        _replace_evaluation(
            predecessor,
            replace(
                original,
                evidence_assessments=(
                    replace(first_assessment, evidence_id=EvidenceId("evidence_d")),
                    second_assessment,
                ),
            ),
            extra_evidence=(evidence_d,),
        ),
        _replace_evaluation(
            predecessor,
            replace(
                original,
                evidence_assessments=(
                    replace(first_assessment, bearing=EvidenceBearing.INDETERMINATE),
                    second_assessment,
                ),
            ),
        ),
        _replace_evaluation(
            predecessor,
            replace(
                original,
                evidence_assessments=(
                    replace(first_assessment, reliability=EvidenceReliability.LOW),
                    second_assessment,
                ),
            ),
        ),
        _replace_evaluation(
            predecessor,
            replace(
                original,
                evidence_assessments=(
                    replace(first_assessment, coverage_note="Mutated coverage note."),
                    second_assessment,
                ),
            ),
        ),
        _replace_evaluation(
            predecessor,
            replace(
                original,
                evidence_assessments=(
                    replace(first_assessment, rationale="Mutated assessment rationale."),
                    second_assessment,
                ),
            ),
        ),
        _replace_evaluation(
            predecessor,
            replace(
                original,
                coverage=replace(original.coverage, status=CoverageStatus.PARTIAL),
            ),
        ),
        _replace_evaluation(
            predecessor,
            replace(
                original,
                coverage=replace(original.coverage, notes="Mutated coverage notes."),
            ),
        ),
        _replace_evaluation(
            predecessor,
            replace(original, conclusion=EvaluationConclusion.INSUFFICIENT),
        ),
        _replace_evaluation(
            predecessor,
            replace(original, rationale="Mutated evaluation rationale."),
        ),
    )


@pytest.mark.parametrize("case_index", range(16))
def test_claim_evaluation_canonical_content_is_identity_bound(case_index) -> None:
    predecessor = _base_snapshot()
    successor = _mutated_evaluation_cases(predecessor)[case_index]
    _assert_mutation_rejected(predecessor, successor, "claim evaluation")


def test_conflict_status_mutation_is_identity_bound() -> None:
    predecessor = _base_snapshot()
    original = predecessor.evaluations[0]
    first, second = original.evidence_assessments
    conflict = replace(
        original,
        evidence_assessments=(
            first,
            replace(second, bearing=EvidenceBearing.CONTRADICTS),
        ),
        conflict_status=ConflictStatus.UNRESOLVED,
        conclusion=EvaluationConclusion.MIXED,
    )
    conflict_snapshot = _replace_evaluation(predecessor, conflict)
    validate_epistemic_snapshot_successor_v1(
        predecessor=EpistemicRecordSet(
            evidence_records=predecessor.evidence_records,
            claims=predecessor.claims,
        ),
        successor=conflict_snapshot,
    )

    resolved = replace(
        conflict,
        conflict_status=ConflictStatus.RESOLVED_BY_POLICY,
        conclusion=EvaluationConclusion.SUPPORTED,
    )
    successor = _replace_evaluation(conflict_snapshot, resolved)
    _assert_mutation_rejected(conflict_snapshot, successor, "claim evaluation")


def test_correction_requires_new_evaluation_identity_and_preserves_old_record() -> None:
    predecessor = _base_snapshot()
    old = predecessor.evaluations[0]
    correction = replace(
        old,
        evaluation_id=ClaimEvaluationId("evaluation_correction"),
        conclusion=EvaluationConclusion.INSUFFICIENT,
        rationale="Correction appended under a new immutable identity.",
        evaluated_at=old.evaluated_at + timedelta(minutes=1),
    )
    successor = EpistemicRecordSet(
        evidence_records=predecessor.evidence_records,
        claims=predecessor.claims,
        evaluations=predecessor.evaluations + (correction,),
    )
    receipt = validate_epistemic_snapshot_successor_v1(
        predecessor=predecessor,
        successor=successor,
    )
    assert receipt.retained_evaluation_ids == (ClaimEvaluationId("evaluation_main"),)
    assert receipt.added_evaluation_ids == (ClaimEvaluationId("evaluation_correction"),)
    assert predecessor.evaluations[0] in successor.evaluations


def test_receipt_contains_no_selection_supersession_or_state_authority_fields() -> None:
    names = {field.name for field in fields(EpistemicSnapshotSuccessionReceipt)}
    assert {
        "selected_evaluation_ids",
        "preferred_evaluation_id",
        "active_evaluation_id",
        "superseded_ids",
        "winning_conclusion",
        "capability_state",
        "confidence",
        "score",
        "weight",
    }.isdisjoint(names)


def test_receipt_sorts_typed_ids_deterministically() -> None:
    receipt = EpistemicSnapshotSuccessionReceipt(
        predecessor_sha256=EMPTY_SHA256_V1,
        successor_sha256=EMPTY_SHA256_V1,
        added_evidence_ids=(EvidenceId("z"), EvidenceId("a")),
        added_claim_ids=(CapabilityClaimId("z"), CapabilityClaimId("a")),
        added_evaluation_ids=(ClaimEvaluationId("z"), ClaimEvaluationId("a")),
    )
    assert receipt.added_evidence_ids == (EvidenceId("a"), EvidenceId("z"))
    assert receipt.added_claim_ids == (CapabilityClaimId("a"), CapabilityClaimId("z"))
    assert receipt.added_evaluation_ids == (
        ClaimEvaluationId("a"),
        ClaimEvaluationId("z"),
    )


def test_typed_id_namespaces_do_not_collapse_to_global_string_identity() -> None:
    predecessor = EpistemicRecordSet(
        evidence_records=(_evidence("shared_identity"),),
    )
    successor = EpistemicRecordSet(
        evidence_records=predecessor.evidence_records,
        claims=(_claim("shared_identity"),),
    )
    receipt = validate_epistemic_snapshot_successor_v1(
        predecessor=predecessor,
        successor=successor,
    )
    assert receipt.retained_evidence_ids == (EvidenceId("shared_identity"),)
    assert receipt.added_claim_ids == (CapabilityClaimId("shared_identity"),)


def test_historical_backfill_is_allowed_for_new_identity() -> None:
    old_time = datetime(2020, 1, 1, 9, 0, tzinfo=timezone.utc)
    successor = EpistemicRecordSet(
        evidence_records=(
            _evidence(
                "historical_evidence",
                observed_at=old_time,
                recorded_at=old_time + timedelta(minutes=1),
            ),
        ),
    )
    receipt = validate_epistemic_snapshot_successor_v1(
        predecessor=EpistemicRecordSet(),
        successor=successor,
    )
    assert receipt.added_evidence_ids == (EvidenceId("historical_evidence"),)


def test_timezone_equivalent_datetimes_are_same_canonical_content() -> None:
    utc = _evidence(
        "timezone_evidence",
        observed_at=datetime(2026, 8, 20, 9, 0, tzinfo=timezone.utc),
        recorded_at=datetime(2026, 8, 20, 9, 1, tzinfo=timezone.utc),
    )
    plus_six = _evidence(
        "timezone_evidence",
        observed_at=datetime(
            2026, 8, 20, 15, 0, tzinfo=timezone(timedelta(hours=6))
        ),
        recorded_at=datetime(
            2026, 8, 20, 15, 1, tzinfo=timezone(timedelta(hours=6))
        ),
    )
    assert utc == plus_six
    validate_epistemic_snapshot_successor_v1(
        predecessor=EpistemicRecordSet(evidence_records=(utc,)),
        successor=EpistemicRecordSet(evidence_records=(plus_six,)),
    )


def test_nfc_equivalent_text_is_same_canonical_content() -> None:
    composed = "Café observation."
    decomposed = unicodedata.normalize("NFD", composed)
    first = _evidence("unicode_evidence", summary=composed)
    second = _evidence("unicode_evidence", summary=decomposed)
    assert first == second
    validate_epistemic_snapshot_successor_v1(
        predecessor=EpistemicRecordSet(evidence_records=(first,)),
        successor=EpistemicRecordSet(evidence_records=(second,)),
    )


def test_snapshot_successor_rejects_wrong_argument_types() -> None:
    with pytest.raises(
        InvalidEpistemicSnapshotSuccessor,
        match="predecessor must be EpistemicRecordSet",
    ):
        validate_epistemic_snapshot_successor_v1(
            predecessor=object(),  # type: ignore[arg-type]
            successor=EpistemicRecordSet(),
        )
    with pytest.raises(
        InvalidEpistemicSnapshotSuccessor,
        match="successor must be EpistemicRecordSet",
    ):
        validate_epistemic_snapshot_successor_v1(
            predecessor=EpistemicRecordSet(),
            successor=object(),  # type: ignore[arg-type]
        )


def test_snapshot_transition_imports_no_downstream_authority_modules() -> None:
    import ast
    from pathlib import Path
    import capability_lab.epistemics.snapshot_transition as transition_module

    forbidden = {
        "capability_lab.derivation",
        "capability_lab.state",
        "capability_lab.history",
        "capability_lab.progression",
        "capability_lab.proposals",
        "capability_lab.player_window",
        "capability_lab.domains",
        "capability_lab.pilots",
    }
    path = Path(transition_module.__file__)
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported = {alias.name for alias in node.names}
            assert forbidden.isdisjoint(imported)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            assert module not in forbidden
            assert not any(module.startswith(prefix + ".") for prefix in forbidden)
