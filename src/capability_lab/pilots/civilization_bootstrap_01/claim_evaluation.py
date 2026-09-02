"""Reviewed Pilot 01 evidence to real PR2 claim/evaluation boundary."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
import unicodedata

from capability_lab.epistemics import (
    CapabilityClaim,
    CapabilityClaimId,
    CapabilitySubjectRef,
    ClaimEvaluation,
    ClaimEvaluationId,
    ConflictStatus,
    CoverageAssessment,
    CoverageStatus,
    EvaluationConclusion,
    EvaluationPolicyRef,
    EvaluatorKind,
    EvaluatorRef,
    EvidenceAssessment,
    EvidenceBearing,
    EvidenceId,
    EvidenceRecord,
    EvidenceReliability,
    ProvenanceTrail,
)

from .evaluation_policy import PilotHumanEvaluationPolicy
from .evaluation_policy_exact import (
    validate_exact_civilization_bootstrap_pilot_01_evaluation_policy_v1,
)
from .materialization import PilotEvidenceMaterializationCandidate
from .materialization_resolution import (
    PilotReviewedMaterializationResolutionBinding,
    validate_pilot_reviewed_materialization_resolution_binding_v1,
)


class PilotClaimEvaluationError(ValueError):
    """Base validation error for the PR11.1 Pilot 01 evaluation boundary."""


class InvalidPilotClaimEvaluation(PilotClaimEvaluationError):
    pass


_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def _clean_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise InvalidPilotClaimEvaluation(f"{field_name} must be a string")
    cleaned = unicodedata.normalize("NFC", value).strip()
    if not cleaned:
        raise InvalidPilotClaimEvaluation(f"{field_name} must be non-empty")
    return cleaned


def _claim_key(value: object) -> str:
    if not isinstance(value, str) or _KEY_RE.fullmatch(value) is None:
        raise InvalidPilotClaimEvaluation(
            "claim_key must use canonical lowercase key syntax"
        )
    return value


def _canonical_time(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise InvalidPilotClaimEvaluation(f"{field_name} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise InvalidPilotClaimEvaluation(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class PilotHumanSingleEvidenceEvaluationDecision:
    evaluation_id: ClaimEvaluationId
    claim_key: str
    claim_id: CapabilityClaimId
    evidence_id: EvidenceId
    policy_ref: EvaluationPolicyRef
    evaluator_ref: EvaluatorRef
    evaluated_at: datetime
    bearing: EvidenceBearing
    reliability: EvidenceReliability
    coverage: CoverageAssessment
    conflict_status: ConflictStatus
    conclusion: EvaluationConclusion
    coverage_note: str
    evidence_rationale: str
    evaluation_rationale: str

    def __post_init__(self) -> None:
        if not isinstance(self.evaluation_id, ClaimEvaluationId):
            raise InvalidPilotClaimEvaluation(
                "evaluation_id must be ClaimEvaluationId"
            )
        object.__setattr__(self, "claim_key", _claim_key(self.claim_key))
        if not isinstance(self.claim_id, CapabilityClaimId):
            raise InvalidPilotClaimEvaluation("claim_id must be CapabilityClaimId")
        if not isinstance(self.evidence_id, EvidenceId):
            raise InvalidPilotClaimEvaluation("evidence_id must be EvidenceId")
        if not isinstance(self.policy_ref, EvaluationPolicyRef):
            raise InvalidPilotClaimEvaluation(
                "policy_ref must be EvaluationPolicyRef"
            )
        if not isinstance(self.evaluator_ref, EvaluatorRef):
            raise InvalidPilotClaimEvaluation("evaluator_ref must be EvaluatorRef")
        if self.evaluator_ref.kind is not EvaluatorKind.HUMAN:
            raise InvalidPilotClaimEvaluation(
                "PR11.1 requires an explicit HUMAN EvaluatorRef"
            )
        object.__setattr__(
            self,
            "evaluated_at",
            _canonical_time(self.evaluated_at, "evaluated_at"),
        )
        if not isinstance(self.bearing, EvidenceBearing):
            raise InvalidPilotClaimEvaluation("bearing must be EvidenceBearing")
        if not isinstance(self.reliability, EvidenceReliability):
            raise InvalidPilotClaimEvaluation(
                "reliability must be EvidenceReliability"
            )
        if self.reliability is EvidenceReliability.UNASSESSED:
            raise InvalidPilotClaimEvaluation(
                "PR11.1 requires an explicit human reliability assessment; "
                "EvidenceReliability.UNASSESSED is not permitted"
            )
        if not isinstance(self.coverage, CoverageAssessment):
            raise InvalidPilotClaimEvaluation("coverage must be CoverageAssessment")
        if not isinstance(self.conflict_status, ConflictStatus):
            raise InvalidPilotClaimEvaluation(
                "conflict_status must be ConflictStatus"
            )
        if not isinstance(self.conclusion, EvaluationConclusion):
            raise InvalidPilotClaimEvaluation(
                "conclusion must be EvaluationConclusion"
            )
        if self.conflict_status is not ConflictStatus.NONE:
            raise InvalidPilotClaimEvaluation(
                "PR11.1 single-evidence evaluation cannot declare evidence conflict; "
                "multi-evidence conflict governance belongs to PR11.2"
            )
        object.__setattr__(
            self,
            "coverage_note",
            _clean_text(self.coverage_note, "coverage_note"),
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


def validate_civilization_bootstrap_pilot_01_capability_claim_v1(
    claim: CapabilityClaim,
    *,
    claim_key: str,
    policy: PilotHumanEvaluationPolicy,
) -> None:
    validate_exact_civilization_bootstrap_pilot_01_evaluation_policy_v1(policy)
    if not isinstance(claim, CapabilityClaim):
        raise InvalidPilotClaimEvaluation("claim must be CapabilityClaim")

    key = _claim_key(claim_key)
    template = policy.claim(key)
    if claim.concept_ref != template.concept_ref:
        raise InvalidPilotClaimEvaluation(
            "claim concept_ref does not match exact PR11.0 claim template"
        )
    if claim.statement != template.statement:
        raise InvalidPilotClaimEvaluation(
            "claim statement does not match exact PR11.0 claim template"
        )
    if claim.scope != template.scope:
        raise InvalidPilotClaimEvaluation(
            "claim scope does not match exact PR11.0 claim template"
        )


def instantiate_civilization_bootstrap_pilot_01_capability_claim_v1(
    *,
    claim_key: str,
    subject_ref: CapabilitySubjectRef,
    claim_id: CapabilityClaimId,
    created_at: datetime,
    provenance: ProvenanceTrail,
    policy: PilotHumanEvaluationPolicy,
) -> CapabilityClaim:
    validate_exact_civilization_bootstrap_pilot_01_evaluation_policy_v1(policy)
    key = _claim_key(claim_key)
    template = policy.claim(key)

    if not isinstance(subject_ref, CapabilitySubjectRef):
        raise InvalidPilotClaimEvaluation(
            "subject_ref must be CapabilitySubjectRef"
        )
    if not isinstance(claim_id, CapabilityClaimId):
        raise InvalidPilotClaimEvaluation("claim_id must be CapabilityClaimId")
    if not isinstance(provenance, ProvenanceTrail):
        raise InvalidPilotClaimEvaluation("provenance must be ProvenanceTrail")
    created = _canonical_time(created_at, "created_at")

    claim = CapabilityClaim(
        claim_id=claim_id,
        subject_ref=subject_ref,
        concept_ref=template.concept_ref,
        statement=template.statement,
        scope=template.scope,
        created_at=created,
        provenance=provenance,
    )
    validate_civilization_bootstrap_pilot_01_capability_claim_v1(
        claim,
        claim_key=key,
        policy=policy,
    )
    return claim


def _validate_single_evidence_coverage_v1(
    *,
    claim_key: str,
    probe_id: str,
    policy: PilotHumanEvaluationPolicy,
    decision: PilotHumanSingleEvidenceEvaluationDecision,
) -> None:
    template = policy.claim(claim_key)

    if decision.coverage.status is CoverageStatus.SUFFICIENT_FOR_CLAIM:
        if (
            len(template.sufficiency_probe_ids) != 1
            or template.sufficiency_probe_ids[0] != probe_id
        ):
            raise InvalidPilotClaimEvaluation(
                "PR11.1 single-evidence evaluation cannot establish "
                "SUFFICIENT_FOR_CLAIM coverage for a multi-probe claim; "
                "multi-evidence sufficiency belongs to PR11.2"
            )
    elif decision.conclusion not in {
        EvaluationConclusion.INSUFFICIENT,
        EvaluationConclusion.ABSTAINED,
    }:
        raise InvalidPilotClaimEvaluation(
            "PR11.1 partial/unassessed single-evidence coverage may preserve "
            "directional EvidenceBearing, but the claim-wide conclusion must "
            "remain INSUFFICIENT or ABSTAINED"
        )


def evaluate_reviewed_civilization_bootstrap_pilot_01_single_evidence_v1(
    *,
    claim_key: str,
    claim: CapabilityClaim,
    policy: PilotHumanEvaluationPolicy,
    candidate: PilotEvidenceMaterializationCandidate,
    evidence: EvidenceRecord,
    resolution_binding: PilotReviewedMaterializationResolutionBinding,
    decision: PilotHumanSingleEvidenceEvaluationDecision,
) -> ClaimEvaluation:
    validate_exact_civilization_bootstrap_pilot_01_evaluation_policy_v1(policy)
    key = _claim_key(claim_key)
    validate_civilization_bootstrap_pilot_01_capability_claim_v1(
        claim,
        claim_key=key,
        policy=policy,
    )

    if not isinstance(candidate, PilotEvidenceMaterializationCandidate):
        raise InvalidPilotClaimEvaluation(
            "candidate must be PilotEvidenceMaterializationCandidate"
        )
    if not isinstance(evidence, EvidenceRecord):
        raise InvalidPilotClaimEvaluation("evidence must be EvidenceRecord")
    if not isinstance(
        resolution_binding,
        PilotReviewedMaterializationResolutionBinding,
    ):
        raise InvalidPilotClaimEvaluation(
            "resolution_binding must be PilotReviewedMaterializationResolutionBinding"
        )
    if not isinstance(
        decision,
        PilotHumanSingleEvidenceEvaluationDecision,
    ):
        raise InvalidPilotClaimEvaluation(
            "decision must be PilotHumanSingleEvidenceEvaluationDecision"
        )

    validate_pilot_reviewed_materialization_resolution_binding_v1(
        candidate,
        evidence,
        resolution_binding,
    )

    rubric = policy.rubric(candidate.probe_id)
    if rubric.claim_key != key:
        raise InvalidPilotClaimEvaluation(
            "reviewed evidence probe is not bound to the selected claim under "
            "the exact PR11.0 policy"
        )

    if candidate.subject_ref != claim.subject_ref:
        raise InvalidPilotClaimEvaluation(
            "candidate subject_ref does not match CapabilityClaim subject_ref"
        )
    if evidence.subject_ref != claim.subject_ref:
        raise InvalidPilotClaimEvaluation(
            "EvidenceRecord subject_ref does not match CapabilityClaim subject_ref"
        )

    if decision.claim_key != key:
        raise InvalidPilotClaimEvaluation(
            "decision claim_key does not match selected claim_key"
        )
    if decision.claim_id != claim.claim_id:
        raise InvalidPilotClaimEvaluation(
            "decision claim_id does not match exact CapabilityClaim"
        )
    if decision.evidence_id != evidence.evidence_id:
        raise InvalidPilotClaimEvaluation(
            "decision evidence_id does not match exact reviewed EvidenceRecord"
        )
    if decision.policy_ref != policy.policy_ref:
        raise InvalidPilotClaimEvaluation(
            "decision policy_ref does not match exact PR11.0 evaluation policy"
        )

    if decision.evaluated_at < claim.created_at:
        raise InvalidPilotClaimEvaluation(
            "evaluated_at must not precede CapabilityClaim created_at"
        )
    if decision.evaluated_at < evidence.recorded_at:
        raise InvalidPilotClaimEvaluation(
            "evaluated_at must not precede reviewed EvidenceRecord recorded_at"
        )
    if decision.evaluated_at < resolution_binding.receipt.resolved_at:
        raise InvalidPilotClaimEvaluation(
            "evaluated_at must not precede reviewed materialization receipt resolved_at"
        )

    _validate_single_evidence_coverage_v1(
        claim_key=key,
        probe_id=candidate.probe_id,
        policy=policy,
        decision=decision,
    )

    assessment = EvidenceAssessment(
        evidence_id=evidence.evidence_id,
        bearing=decision.bearing,
        reliability=decision.reliability,
        coverage_note=decision.coverage_note,
        rationale=decision.evidence_rationale,
    )
    return ClaimEvaluation(
        evaluation_id=decision.evaluation_id,
        claim_id=claim.claim_id,
        policy_ref=policy.policy_ref,
        evaluator_ref=decision.evaluator_ref,
        evaluated_at=decision.evaluated_at,
        evidence_assessments=(assessment,),
        coverage=decision.coverage,
        conflict_status=decision.conflict_status,
        conclusion=decision.conclusion,
        rationale=decision.evaluation_rationale,
    )
