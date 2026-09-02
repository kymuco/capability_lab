"""PR12.5 conservative generic external-evidence to ClaimEvaluation boundary."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import unicodedata

from capability_lab.epistemics import (
    CapabilityClaimId,
    ClaimEvaluation,
    ClaimEvaluationId,
    ConflictStatus,
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
    EvidenceId,
    EvidenceReliability,
    epistemic_snapshot_sha256_v1,
    validate_epistemic_snapshot_successor_v1,
)
from capability_lab.semantics import CapabilityCatalog

from .claim_materialization import (
    ExternalEvidenceInterpretationClaimMaterialization,
    _strict_materialization,
    _strict_snapshot,
    external_evidence_interpretation_claim_materialization_receipt_sha256_v1,
    materialized_capability_claim_sha256_v1,
    validate_external_evidence_interpretation_claim_materialization_v1,
)
from .core import (
    ExternalEvidenceClaimInterpretationCandidate,
    ExternalEvidenceInterpretationProposalId,
    InvalidExternalEvidenceInterpretation,
    _sha256,
    _strict_candidate,
    _time,
    external_evidence_claim_interpretation_candidate_sha256_v1,
)
from .review import ExternalEvidenceInterpretationReviewId
from .review_ledger import ExternalEvidenceInterpretationReviewLedger


_GENERIC_EVALUATION_ID_HASH_DOMAIN = (
    b"capability_lab/generic_external_evidence_claim_evaluation_record_identity@1\x00"
)
_GENERIC_EVALUATION_HASH_DOMAIN = (
    b"capability_lab/generic_external_evidence_claim_evaluation@1\x00"
)
_GENERIC_EVALUATION_RECEIPT_HASH_DOMAIN = (
    b"capability_lab/generic_external_evidence_claim_evaluation_admission_receipt@1\x00"
)

GENERIC_EXTERNAL_EVIDENCE_HUMAN_EVALUATION_POLICY_V1 = EvaluationPolicyRef(
    "capability_lab",
    "generic_external_evidence_human_evaluation",
    1,
)


@dataclass(frozen=True, slots=True)
class ExternalEvidenceHumanClaimEvaluationDecision:
    """One explicit human assessment under the conservative generic policy.

    The decision deliberately contains no evidence selector, claim selector,
    policy selector, evaluation id, conflict selector, state authority, score,
    mastery, readiness, or permission field. The exact evidence and claim are
    resolved from the already-governed PR12.2 -> PR12.4 chain.
    """

    evaluator_ref: EvaluatorRef
    evaluated_at: datetime
    bearing: EvidenceBearing
    reliability: EvidenceReliability
    coverage_status: CoverageStatus
    conclusion: EvaluationConclusion
    evidence_coverage_note: str
    claim_coverage_notes: str
    evidence_rationale: str
    evaluation_rationale: str

    def __post_init__(self) -> None:
        if type(self.evaluator_ref) is not EvaluatorRef:
            raise InvalidExternalEvidenceInterpretation(
                "evaluator_ref must use exact EvaluatorRef"
            )
        if self.evaluator_ref.kind is not EvaluatorKind.HUMAN:
            raise InvalidExternalEvidenceInterpretation(
                "PR12.5 generic evaluation requires an explicit HUMAN EvaluatorRef"
            )
        object.__setattr__(
            self,
            "evaluated_at",
            _time(self.evaluated_at, "evaluated_at"),
        )
        if type(self.bearing) is not EvidenceBearing:
            raise InvalidExternalEvidenceInterpretation(
                "bearing must use exact EvidenceBearing"
            )
        if type(self.reliability) is not EvidenceReliability:
            raise InvalidExternalEvidenceInterpretation(
                "reliability must use exact EvidenceReliability"
            )
        if self.reliability is EvidenceReliability.UNASSESSED:
            raise InvalidExternalEvidenceInterpretation(
                "PR12.5 requires explicit assessed reliability; UNASSESSED is forbidden"
            )
        if type(self.coverage_status) is not CoverageStatus:
            raise InvalidExternalEvidenceInterpretation(
                "coverage_status must use exact CoverageStatus"
            )
        if self.coverage_status not in {
            CoverageStatus.UNASSESSED,
            CoverageStatus.PARTIAL,
        }:
            raise InvalidExternalEvidenceInterpretation(
                "generic PR12.5 policy has no domain sufficiency rule; "
                "SUFFICIENT_FOR_CLAIM coverage is forbidden"
            )
        if type(self.conclusion) is not EvaluationConclusion:
            raise InvalidExternalEvidenceInterpretation(
                "conclusion must use exact EvaluationConclusion"
            )
        if self.conclusion not in {
            EvaluationConclusion.INSUFFICIENT,
            EvaluationConclusion.ABSTAINED,
        }:
            raise InvalidExternalEvidenceInterpretation(
                "generic PR12.5 policy cannot emit SUPPORTED, CONTRADICTED, or MIXED; "
                "claim-wide conclusion must remain INSUFFICIENT or ABSTAINED"
            )
        object.__setattr__(
            self,
            "evidence_coverage_note",
            _clean_text(self.evidence_coverage_note, "evidence_coverage_note"),
        )
        object.__setattr__(
            self,
            "claim_coverage_notes",
            _clean_text(self.claim_coverage_notes, "claim_coverage_notes"),
        )
        object.__setattr__(
            self,
            "evidence_rationale",
            _clean_text(self.evidence_rationale, "evidence_rationale"),
        )
        object.__setattr__(
            self,
            "evaluation_rationale",
            _clean_text(self.evaluation_rationale, "evaluation_rationale"),
        )


@dataclass(frozen=True, slots=True)
class ExternalEvidenceClaimEvaluationAdmissionReceipt:
    policy_ref: EvaluationPolicyRef
    proposal_id: ExternalEvidenceInterpretationProposalId
    candidate_sha256: str
    review_id: ExternalEvidenceInterpretationReviewId
    review_sha256: str
    claim_materialization_receipt_sha256: str
    evidence_id: EvidenceId
    evidence_sha256: str
    claim_id: CapabilityClaimId
    claim_sha256: str
    evaluation_id: ClaimEvaluationId
    evaluation_sha256: str
    predecessor_snapshot_sha256: str
    successor_snapshot_sha256: str
    evaluated_at: datetime

    def __post_init__(self) -> None:
        if type(self.policy_ref) is not EvaluationPolicyRef:
            raise InvalidExternalEvidenceInterpretation(
                "receipt policy_ref must use exact EvaluationPolicyRef"
            )
        if self.policy_ref != GENERIC_EXTERNAL_EVIDENCE_HUMAN_EVALUATION_POLICY_V1:
            raise InvalidExternalEvidenceInterpretation(
                "evaluation admission receipt must use frozen PR12.5 policy"
            )
        if type(self.proposal_id) is not ExternalEvidenceInterpretationProposalId:
            raise InvalidExternalEvidenceInterpretation(
                "receipt proposal_id must use exact ExternalEvidenceInterpretationProposalId"
            )
        object.__setattr__(
            self,
            "candidate_sha256",
            _sha256(self.candidate_sha256, "candidate_sha256"),
        )
        if type(self.review_id) is not ExternalEvidenceInterpretationReviewId:
            raise InvalidExternalEvidenceInterpretation(
                "receipt review_id must use exact ExternalEvidenceInterpretationReviewId"
            )
        object.__setattr__(
            self,
            "review_sha256",
            _sha256(self.review_sha256, "review_sha256"),
        )
        object.__setattr__(
            self,
            "claim_materialization_receipt_sha256",
            _sha256(
                self.claim_materialization_receipt_sha256,
                "claim_materialization_receipt_sha256",
            ),
        )
        if type(self.evidence_id) is not EvidenceId:
            raise InvalidExternalEvidenceInterpretation(
                "receipt evidence_id must use exact EvidenceId"
            )
        object.__setattr__(
            self,
            "evidence_sha256",
            _sha256(self.evidence_sha256, "evidence_sha256"),
        )
        if type(self.claim_id) is not CapabilityClaimId:
            raise InvalidExternalEvidenceInterpretation(
                "receipt claim_id must use exact CapabilityClaimId"
            )
        object.__setattr__(
            self,
            "claim_sha256",
            _sha256(self.claim_sha256, "claim_sha256"),
        )
        if type(self.evaluation_id) is not ClaimEvaluationId:
            raise InvalidExternalEvidenceInterpretation(
                "receipt evaluation_id must use exact ClaimEvaluationId"
            )
        object.__setattr__(
            self,
            "evaluation_sha256",
            _sha256(self.evaluation_sha256, "evaluation_sha256"),
        )
        object.__setattr__(
            self,
            "predecessor_snapshot_sha256",
            _sha256(
                self.predecessor_snapshot_sha256,
                "predecessor_snapshot_sha256",
            ),
        )
        object.__setattr__(
            self,
            "successor_snapshot_sha256",
            _sha256(
                self.successor_snapshot_sha256,
                "successor_snapshot_sha256",
            ),
        )
        object.__setattr__(
            self,
            "evaluated_at",
            _time(self.evaluated_at, "evaluated_at"),
        )

    def to_dict(self) -> dict:
        from .generic_claim_evaluation_serialization import (
            external_evidence_claim_evaluation_admission_receipt_to_dict,
        )

        return external_evidence_claim_evaluation_admission_receipt_to_dict(self)

    @classmethod
    def from_dict(
        cls,
        payload: object,
    ) -> "ExternalEvidenceClaimEvaluationAdmissionReceipt":
        from .generic_claim_evaluation_serialization import (
            external_evidence_claim_evaluation_admission_receipt_from_dict,
        )

        return external_evidence_claim_evaluation_admission_receipt_from_dict(payload)

    def to_json(self) -> str:
        from .generic_claim_evaluation_serialization import (
            external_evidence_claim_evaluation_admission_receipt_to_json,
        )

        return external_evidence_claim_evaluation_admission_receipt_to_json(self)

    @classmethod
    def from_json(
        cls,
        payload: object,
    ) -> "ExternalEvidenceClaimEvaluationAdmissionReceipt":
        from .generic_claim_evaluation_serialization import (
            external_evidence_claim_evaluation_admission_receipt_from_json,
        )

        return external_evidence_claim_evaluation_admission_receipt_from_json(payload)


@dataclass(frozen=True, slots=True)
class ExternalEvidenceClaimEvaluationAdmission:
    evaluation: ClaimEvaluation
    successor_snapshot: EpistemicRecordSet
    succession_receipt: EpistemicSnapshotSuccessionReceipt
    admission_receipt: ExternalEvidenceClaimEvaluationAdmissionReceipt

    def __post_init__(self) -> None:
        _strict_evaluation(self.evaluation)
        _strict_snapshot(self.successor_snapshot, "successor_snapshot")
        if not isinstance(
            self.succession_receipt,
            EpistemicSnapshotSuccessionReceipt,
        ) or not self.succession_receipt.validator_issued:
            raise InvalidExternalEvidenceInterpretation(
                "succession_receipt must be validator-issued by PR11.3"
            )
        _strict_admission_receipt(self.admission_receipt)


def _clean_text(value: object, field_name: str) -> str:
    if type(value) is not str:
        raise InvalidExternalEvidenceInterpretation(
            f"{field_name} must be a string"
        )
    cleaned = unicodedata.normalize("NFC", value).strip()
    if not cleaned:
        raise InvalidExternalEvidenceInterpretation(
            f"{field_name} must be non-empty"
        )
    return cleaned


def _canonical_json(payload: object) -> str:
    try:
        return json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise InvalidExternalEvidenceInterpretation(
            f"evaluation identity payload is not canonically JSON serializable: {exc}"
        ) from exc


def _format_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _strict_decision(
    decision: ExternalEvidenceHumanClaimEvaluationDecision,
) -> ExternalEvidenceHumanClaimEvaluationDecision:
    if type(decision) is not ExternalEvidenceHumanClaimEvaluationDecision:
        raise InvalidExternalEvidenceInterpretation(
            "decision must use exact ExternalEvidenceHumanClaimEvaluationDecision"
        )
    restored = ExternalEvidenceHumanClaimEvaluationDecision(
        evaluator_ref=EvaluatorRef(decision.evaluator_ref.kind, decision.evaluator_ref.ref),
        evaluated_at=decision.evaluated_at,
        bearing=EvidenceBearing(decision.bearing.value),
        reliability=EvidenceReliability(decision.reliability.value),
        coverage_status=CoverageStatus(decision.coverage_status.value),
        conclusion=EvaluationConclusion(decision.conclusion.value),
        evidence_coverage_note=decision.evidence_coverage_note,
        claim_coverage_notes=decision.claim_coverage_notes,
        evidence_rationale=decision.evidence_rationale,
        evaluation_rationale=decision.evaluation_rationale,
    )
    if restored != decision:
        raise InvalidExternalEvidenceInterpretation(
            "decision must equal strict semantic reconstruction"
        )
    return decision


def _strict_evaluation(evaluation: ClaimEvaluation) -> ClaimEvaluation:
    if type(evaluation) is not ClaimEvaluation:
        raise InvalidExternalEvidenceInterpretation(
            "evaluation must use exact ClaimEvaluation"
        )
    if type(evaluation.evaluation_id) is not ClaimEvaluationId:
        raise InvalidExternalEvidenceInterpretation(
            "evaluation_id must use exact ClaimEvaluationId"
        )
    if type(evaluation.claim_id) is not CapabilityClaimId:
        raise InvalidExternalEvidenceInterpretation(
            "evaluation claim_id must use exact CapabilityClaimId"
        )
    if type(evaluation.policy_ref) is not EvaluationPolicyRef:
        raise InvalidExternalEvidenceInterpretation(
            "evaluation policy_ref must use exact EvaluationPolicyRef"
        )
    if type(evaluation.evaluator_ref) is not EvaluatorRef:
        raise InvalidExternalEvidenceInterpretation(
            "evaluation evaluator_ref must use exact EvaluatorRef"
        )
    if type(evaluation.coverage) is not CoverageAssessment:
        raise InvalidExternalEvidenceInterpretation(
            "evaluation coverage must use exact CoverageAssessment"
        )
    if type(evaluation.conflict_status) is not ConflictStatus:
        raise InvalidExternalEvidenceInterpretation(
            "evaluation conflict_status must use exact ConflictStatus"
        )
    if type(evaluation.conclusion) is not EvaluationConclusion:
        raise InvalidExternalEvidenceInterpretation(
            "evaluation conclusion must use exact EvaluationConclusion"
        )
    for item in evaluation.evidence_assessments:
        if type(item) is not EvidenceAssessment:
            raise InvalidExternalEvidenceInterpretation(
                "evaluation assessments must use exact EvidenceAssessment"
            )
        if type(item.evidence_id) is not EvidenceId:
            raise InvalidExternalEvidenceInterpretation(
                "assessment evidence_id must use exact EvidenceId"
            )
        if type(item.bearing) is not EvidenceBearing:
            raise InvalidExternalEvidenceInterpretation(
                "assessment bearing must use exact EvidenceBearing"
            )
        if type(item.reliability) is not EvidenceReliability:
            raise InvalidExternalEvidenceInterpretation(
                "assessment reliability must use exact EvidenceReliability"
            )
    assessments = tuple(
        EvidenceAssessment(
            evidence_id=EvidenceId(item.evidence_id.value),
            bearing=EvidenceBearing(item.bearing.value),
            reliability=EvidenceReliability(item.reliability.value),
            coverage_note=item.coverage_note,
            rationale=item.rationale,
        )
        for item in evaluation.evidence_assessments
    )
    restored = ClaimEvaluation(
        evaluation_id=ClaimEvaluationId(evaluation.evaluation_id.value),
        claim_id=CapabilityClaimId(evaluation.claim_id.value),
        policy_ref=EvaluationPolicyRef(
            evaluation.policy_ref.namespace,
            evaluation.policy_ref.key,
            evaluation.policy_ref.revision,
        ),
        evaluator_ref=EvaluatorRef(
            evaluation.evaluator_ref.kind,
            evaluation.evaluator_ref.ref,
        ),
        evaluated_at=evaluation.evaluated_at,
        evidence_assessments=assessments,
        coverage=CoverageAssessment(
            CoverageStatus(evaluation.coverage.status.value),
            evaluation.coverage.notes,
        ),
        conflict_status=ConflictStatus(evaluation.conflict_status.value),
        conclusion=EvaluationConclusion(evaluation.conclusion.value),
        rationale=evaluation.rationale,
    )
    if restored != evaluation:
        raise InvalidExternalEvidenceInterpretation(
            "evaluation must equal strict semantic reconstruction"
        )
    return evaluation


def _strict_admission_receipt(
    receipt: ExternalEvidenceClaimEvaluationAdmissionReceipt,
) -> ExternalEvidenceClaimEvaluationAdmissionReceipt:
    if type(receipt) is not ExternalEvidenceClaimEvaluationAdmissionReceipt:
        raise InvalidExternalEvidenceInterpretation(
            "admission_receipt must use exact ExternalEvidenceClaimEvaluationAdmissionReceipt"
        )
    from .generic_claim_evaluation_serialization import (
        external_evidence_claim_evaluation_admission_receipt_from_json,
        external_evidence_claim_evaluation_admission_receipt_to_json,
    )

    restored = external_evidence_claim_evaluation_admission_receipt_from_json(
        external_evidence_claim_evaluation_admission_receipt_to_json(receipt)
    )
    if restored != receipt:
        raise InvalidExternalEvidenceInterpretation(
            "admission_receipt must equal strict semantic reconstruction"
        )
    return receipt


def _strict_admission(
    value: ExternalEvidenceClaimEvaluationAdmission,
) -> ExternalEvidenceClaimEvaluationAdmission:
    if type(value) is not ExternalEvidenceClaimEvaluationAdmission:
        raise InvalidExternalEvidenceInterpretation(
            "admission must use exact ExternalEvidenceClaimEvaluationAdmission"
        )
    _strict_evaluation(value.evaluation)
    _strict_snapshot(value.successor_snapshot, "successor_snapshot")
    if not isinstance(
        value.succession_receipt,
        EpistemicSnapshotSuccessionReceipt,
    ) or not value.succession_receipt.validator_issued:
        raise InvalidExternalEvidenceInterpretation(
            "succession_receipt must be validator-issued by PR11.3"
        )
    _strict_admission_receipt(value.admission_receipt)
    return value


def _evaluation_record_payload_without_id(
    *,
    claim_id: CapabilityClaimId,
    evidence_id: EvidenceId,
    decision: ExternalEvidenceHumanClaimEvaluationDecision,
) -> dict:
    decision = _strict_decision(decision)
    if type(claim_id) is not CapabilityClaimId:
        raise InvalidExternalEvidenceInterpretation(
            "claim_id must use exact CapabilityClaimId"
        )
    if type(evidence_id) is not EvidenceId:
        raise InvalidExternalEvidenceInterpretation(
            "evidence_id must use exact EvidenceId"
        )
    return {
        "claim_id": str(claim_id),
        "policy_ref": str(GENERIC_EXTERNAL_EVIDENCE_HUMAN_EVALUATION_POLICY_V1),
        "evaluator_ref": {
            "kind": decision.evaluator_ref.kind.value,
            "ref": decision.evaluator_ref.ref,
        },
        "evaluated_at": _format_time(decision.evaluated_at),
        "evidence_assessments": [
            {
                "evidence_id": str(evidence_id),
                "bearing": decision.bearing.value,
                "reliability": decision.reliability.value,
                "coverage_note": decision.evidence_coverage_note,
                "rationale": decision.evidence_rationale,
            }
        ],
        "coverage": {
            "status": decision.coverage_status.value,
            "notes": decision.claim_coverage_notes,
        },
        "conflict_status": ConflictStatus.NONE.value,
        "conclusion": decision.conclusion.value,
        "rationale": decision.evaluation_rationale,
    }


def _deterministic_evaluation_id(
    *,
    claim_id: CapabilityClaimId,
    evidence_id: EvidenceId,
    decision: ExternalEvidenceHumanClaimEvaluationDecision,
) -> ClaimEvaluationId:
    payload = _evaluation_record_payload_without_id(
        claim_id=claim_id,
        evidence_id=evidence_id,
        decision=decision,
    )
    digest = hashlib.sha256()
    digest.update(_GENERIC_EVALUATION_ID_HASH_DOMAIN)
    digest.update(_canonical_json(payload).encode("utf-8"))
    return ClaimEvaluationId("external_evaluation:" + digest.hexdigest())


def _build_evaluation(
    *,
    claim,
    evidence,
    decision: ExternalEvidenceHumanClaimEvaluationDecision,
) -> ClaimEvaluation:
    decision = _strict_decision(decision)
    if decision.evaluated_at < claim.created_at:
        raise InvalidExternalEvidenceInterpretation(
            "evaluated_at must not precede materialized CapabilityClaim created_at"
        )
    if decision.evaluated_at < evidence.recorded_at:
        raise InvalidExternalEvidenceInterpretation(
            "evaluated_at must not precede exact external EvidenceRecord recorded_at"
        )
    assessment = EvidenceAssessment(
        evidence_id=evidence.evidence_id,
        bearing=decision.bearing,
        reliability=decision.reliability,
        coverage_note=decision.evidence_coverage_note,
        rationale=decision.evidence_rationale,
    )
    evaluation = ClaimEvaluation(
        evaluation_id=_deterministic_evaluation_id(
            claim_id=claim.claim_id,
            evidence_id=evidence.evidence_id,
            decision=decision,
        ),
        claim_id=claim.claim_id,
        policy_ref=GENERIC_EXTERNAL_EVIDENCE_HUMAN_EVALUATION_POLICY_V1,
        evaluator_ref=decision.evaluator_ref,
        evaluated_at=decision.evaluated_at,
        evidence_assessments=(assessment,),
        coverage=CoverageAssessment(
            status=decision.coverage_status,
            notes=decision.claim_coverage_notes,
        ),
        conflict_status=ConflictStatus.NONE,
        conclusion=decision.conclusion,
        rationale=decision.evaluation_rationale,
    )
    return _strict_evaluation(evaluation)


def _evaluation_payload(evaluation: ClaimEvaluation) -> dict:
    evaluation = _strict_evaluation(evaluation)
    return {
        "evaluation_id": str(evaluation.evaluation_id),
        "claim_id": str(evaluation.claim_id),
        "policy_ref": str(evaluation.policy_ref),
        "evaluator_ref": {
            "kind": evaluation.evaluator_ref.kind.value,
            "ref": evaluation.evaluator_ref.ref,
        },
        "evaluated_at": _format_time(evaluation.evaluated_at),
        "evidence_assessments": [
            {
                "evidence_id": str(item.evidence_id),
                "bearing": item.bearing.value,
                "reliability": item.reliability.value,
                "coverage_note": item.coverage_note,
                "rationale": item.rationale,
            }
            for item in evaluation.evidence_assessments
        ],
        "coverage": {
            "status": evaluation.coverage.status.value,
            "notes": evaluation.coverage.notes,
        },
        "conflict_status": evaluation.conflict_status.value,
        "conclusion": evaluation.conclusion.value,
        "rationale": evaluation.rationale,
    }


def generic_external_evidence_claim_evaluation_sha256_v1(
    evaluation: ClaimEvaluation,
) -> str:
    digest = hashlib.sha256()
    digest.update(_GENERIC_EVALUATION_HASH_DOMAIN)
    digest.update(_canonical_json(_evaluation_payload(evaluation)).encode("utf-8"))
    return digest.hexdigest()


def _same_evaluation_content_except_id(
    left: ClaimEvaluation,
    right: ClaimEvaluation,
) -> bool:
    left_payload = _evaluation_payload(left)
    right_payload = _evaluation_payload(right)
    left_payload.pop("evaluation_id")
    right_payload.pop("evaluation_id")
    return left_payload == right_payload


def _find_exact_evidence(
    snapshot: EpistemicRecordSet,
    evidence_id: EvidenceId,
):
    matches = tuple(
        item for item in snapshot.evidence_records if item.evidence_id == evidence_id
    )
    if len(matches) != 1:
        raise InvalidExternalEvidenceInterpretation(
            "current epistemic snapshot must contain selected EvidenceId exactly once"
        )
    return matches[0]


def _find_exact_claim(
    snapshot: EpistemicRecordSet,
    claim_id: CapabilityClaimId,
):
    matches = tuple(item for item in snapshot.claims if item.claim_id == claim_id)
    if len(matches) != 1:
        raise InvalidExternalEvidenceInterpretation(
            "current epistemic snapshot must contain materialized CapabilityClaim exactly once"
        )
    return matches[0]


def _validate_materialization_and_current_lineage(
    *,
    materialization_predecessor_snapshot: EpistemicRecordSet,
    current_epistemic_snapshot: EpistemicRecordSet,
    catalog: CapabilityCatalog,
    candidate: ExternalEvidenceClaimInterpretationCandidate,
    review_ledger: ExternalEvidenceInterpretationReviewLedger,
    materialization: ExternalEvidenceInterpretationClaimMaterialization,
):
    basis = _strict_snapshot(
        materialization_predecessor_snapshot,
        "materialization_predecessor_snapshot",
    )
    current = _strict_snapshot(current_epistemic_snapshot, "current_epistemic_snapshot")
    candidate = _strict_candidate(candidate)
    materialization = _strict_materialization(materialization)

    validate_external_evidence_interpretation_claim_materialization_v1(
        epistemic_snapshot=basis,
        catalog=catalog,
        candidate=candidate,
        review_ledger=review_ledger,
        materialization=materialization,
    )
    try:
        validate_epistemic_snapshot_successor_v1(
            predecessor=materialization.successor_snapshot,
            successor=current,
        )
    except (TypeError, ValueError) as exc:
        raise InvalidExternalEvidenceInterpretation(
            "current epistemic snapshot is not an append-only successor of exact "
            f"PR12.4 materialization: {exc}"
        ) from exc

    evidence = _find_exact_evidence(current, candidate.evidence_id)
    claim = _find_exact_claim(current, materialization.claim.claim_id)
    if claim != materialization.claim:
        raise InvalidExternalEvidenceInterpretation(
            "current snapshot materialized claim bytes differ from exact PR12.4 claim"
        )
    if evidence.subject_ref != claim.subject_ref:
        raise InvalidExternalEvidenceInterpretation(
            "exact selected evidence subject does not match materialized claim subject"
        )
    return basis, current, candidate, materialization, evidence, claim


def _build_successor(
    *,
    current: EpistemicRecordSet,
    evaluation: ClaimEvaluation,
) -> tuple[EpistemicRecordSet, EpistemicSnapshotSuccessionReceipt]:
    for existing in current.evaluations:
        if existing.evaluation_id == evaluation.evaluation_id:
            raise InvalidExternalEvidenceInterpretation(
                "deterministic generic evaluation_id already exists in current snapshot"
            )
        if _same_evaluation_content_except_id(existing, evaluation):
            raise InvalidExternalEvidenceInterpretation(
                "semantically identical immutable ClaimEvaluation already exists under "
                "a different evaluation_id; PR12.5 does not duplicate or reconcile it"
            )
    try:
        successor = EpistemicRecordSet(
            evidence_records=current.evidence_records,
            claims=current.claims,
            evaluations=current.evaluations + (evaluation,),
        )
        receipt = validate_epistemic_snapshot_successor_v1(
            predecessor=current,
            successor=successor,
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InvalidExternalEvidenceInterpretation):
            raise
        raise InvalidExternalEvidenceInterpretation(
            f"cannot admit generic ClaimEvaluation through PR11.3 succession: {exc}"
        ) from exc
    if receipt.added_evaluation_ids != (evaluation.evaluation_id,):
        raise InvalidExternalEvidenceInterpretation(
            "PR12.5 succession must append exactly one deterministic ClaimEvaluation"
        )
    if receipt.added_evidence_ids or receipt.added_claim_ids:
        raise InvalidExternalEvidenceInterpretation(
            "PR12.5 succession may not add evidence or CapabilityClaim records"
        )
    return successor, receipt


def _build_admission_receipt(
    *,
    candidate: ExternalEvidenceClaimInterpretationCandidate,
    materialization: ExternalEvidenceInterpretationClaimMaterialization,
    evidence,
    evaluation: ClaimEvaluation,
    current: EpistemicRecordSet,
    successor: EpistemicRecordSet,
) -> ExternalEvidenceClaimEvaluationAdmissionReceipt:
    materialization_receipt = materialization.materialization_receipt
    return ExternalEvidenceClaimEvaluationAdmissionReceipt(
        policy_ref=GENERIC_EXTERNAL_EVIDENCE_HUMAN_EVALUATION_POLICY_V1,
        proposal_id=candidate.proposal_id,
        candidate_sha256=external_evidence_claim_interpretation_candidate_sha256_v1(
            candidate
        ),
        review_id=materialization_receipt.review_id,
        review_sha256=materialization_receipt.review_sha256,
        claim_materialization_receipt_sha256=(
            external_evidence_interpretation_claim_materialization_receipt_sha256_v1(
                materialization_receipt
            )
        ),
        evidence_id=evidence.evidence_id,
        evidence_sha256=candidate.evidence_sha256,
        claim_id=materialization.claim.claim_id,
        claim_sha256=materialized_capability_claim_sha256_v1(materialization.claim),
        evaluation_id=evaluation.evaluation_id,
        evaluation_sha256=generic_external_evidence_claim_evaluation_sha256_v1(
            evaluation
        ),
        predecessor_snapshot_sha256=epistemic_snapshot_sha256_v1(current),
        successor_snapshot_sha256=epistemic_snapshot_sha256_v1(successor),
        evaluated_at=evaluation.evaluated_at,
    )


def evaluate_materialized_external_evidence_claim_v1(
    *,
    materialization_predecessor_snapshot: EpistemicRecordSet,
    current_epistemic_snapshot: EpistemicRecordSet,
    catalog: CapabilityCatalog,
    candidate: ExternalEvidenceClaimInterpretationCandidate,
    review_ledger: ExternalEvidenceInterpretationReviewLedger,
    materialization: ExternalEvidenceInterpretationClaimMaterialization,
    decision: ExternalEvidenceHumanClaimEvaluationDecision,
) -> ExternalEvidenceClaimEvaluationAdmission:
    """Create one conservative generic ClaimEvaluation from exact governed basis."""

    (
        _,
        current,
        candidate,
        materialization,
        evidence,
        claim,
    ) = _validate_materialization_and_current_lineage(
        materialization_predecessor_snapshot=materialization_predecessor_snapshot,
        current_epistemic_snapshot=current_epistemic_snapshot,
        catalog=catalog,
        candidate=candidate,
        review_ledger=review_ledger,
        materialization=materialization,
    )
    decision = _strict_decision(decision)
    evaluation = _build_evaluation(
        claim=claim,
        evidence=evidence,
        decision=decision,
    )
    successor, succession_receipt = _build_successor(
        current=current,
        evaluation=evaluation,
    )
    admission_receipt = _build_admission_receipt(
        candidate=candidate,
        materialization=materialization,
        evidence=evidence,
        evaluation=evaluation,
        current=current,
        successor=successor,
    )
    result = ExternalEvidenceClaimEvaluationAdmission(
        evaluation=evaluation,
        successor_snapshot=successor,
        succession_receipt=succession_receipt,
        admission_receipt=admission_receipt,
    )
    validate_external_evidence_claim_evaluation_admission_v1(
        materialization_predecessor_snapshot=materialization_predecessor_snapshot,
        current_epistemic_snapshot=current,
        catalog=catalog,
        candidate=candidate,
        review_ledger=review_ledger,
        materialization=materialization,
        decision=decision,
        admission=result,
    )
    return result


def validate_external_evidence_claim_evaluation_admission_v1(
    *,
    materialization_predecessor_snapshot: EpistemicRecordSet,
    current_epistemic_snapshot: EpistemicRecordSet,
    catalog: CapabilityCatalog,
    candidate: ExternalEvidenceClaimInterpretationCandidate,
    review_ledger: ExternalEvidenceInterpretationReviewLedger,
    materialization: ExternalEvidenceInterpretationClaimMaterialization,
    decision: ExternalEvidenceHumanClaimEvaluationDecision,
    admission: ExternalEvidenceClaimEvaluationAdmission,
) -> None:
    """Replay PR12.2-12.5 governance and exact PR11.3 evaluation admission."""

    (
        _,
        current,
        candidate,
        materialization,
        evidence,
        claim,
    ) = _validate_materialization_and_current_lineage(
        materialization_predecessor_snapshot=materialization_predecessor_snapshot,
        current_epistemic_snapshot=current_epistemic_snapshot,
        catalog=catalog,
        candidate=candidate,
        review_ledger=review_ledger,
        materialization=materialization,
    )
    decision = _strict_decision(decision)
    admission = _strict_admission(admission)
    expected_evaluation = _build_evaluation(
        claim=claim,
        evidence=evidence,
        decision=decision,
    )
    if admission.evaluation != expected_evaluation:
        raise InvalidExternalEvidenceInterpretation(
            "admitted ClaimEvaluation does not equal exact deterministic PR12.5 evaluation"
        )
    expected_successor, expected_succession_receipt = _build_successor(
        current=current,
        evaluation=expected_evaluation,
    )
    if admission.successor_snapshot != expected_successor:
        raise InvalidExternalEvidenceInterpretation(
            "successor_snapshot does not equal exact PR12.5 append-only successor"
        )
    if admission.succession_receipt != expected_succession_receipt:
        raise InvalidExternalEvidenceInterpretation(
            "succession_receipt does not equal validator-issued PR11.3 receipt"
        )
    expected_receipt = _build_admission_receipt(
        candidate=candidate,
        materialization=materialization,
        evidence=evidence,
        evaluation=expected_evaluation,
        current=current,
        successor=expected_successor,
    )
    if admission.admission_receipt != expected_receipt:
        raise InvalidExternalEvidenceInterpretation(
            "admission_receipt does not match exact PR12.5 governance basis"
        )


def external_evidence_claim_evaluation_admission_receipt_sha256_v1(
    receipt: ExternalEvidenceClaimEvaluationAdmissionReceipt,
) -> str:
    receipt = _strict_admission_receipt(receipt)
    from .generic_claim_evaluation_serialization import (
        external_evidence_claim_evaluation_admission_receipt_to_json,
    )

    digest = hashlib.sha256()
    digest.update(_GENERIC_EVALUATION_RECEIPT_HASH_DOMAIN)
    digest.update(
        external_evidence_claim_evaluation_admission_receipt_to_json(receipt).encode(
            "utf-8"
        )
    )
    return digest.hexdigest()
