"""Reviewed Pilot 01 multi-evidence to real PR2 ClaimEvaluation boundary."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from capability_lab.epistemics import (
    CapabilityClaim,
    CapabilityClaimId,
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
    EvidenceReliability,
)

from .claim_evaluation import (
    InvalidPilotClaimEvaluation,
    _canonical_time,
    _claim_key,
    _clean_text,
    validate_civilization_bootstrap_pilot_01_capability_claim_v1,
)
from .evaluation_policy import PilotHumanEvaluationPolicy
from .evaluation_policy_exact import (
    validate_exact_civilization_bootstrap_pilot_01_evaluation_policy_v1,
)
from .materialization_terminal import (
    validate_pilot_materialized_evidence_reviewed_dependence_preconditions_v1,
)


@dataclass(frozen=True, slots=True)
class PilotHumanMultiEvidenceAssessmentDecision:
    """One explicit human assessment decision for one reviewed EvidenceRecord."""

    evidence_id: EvidenceId
    bearing: EvidenceBearing
    reliability: EvidenceReliability
    coverage_note: str
    rationale: str

    def __post_init__(self) -> None:
        if not isinstance(self.evidence_id, EvidenceId):
            raise InvalidPilotClaimEvaluation("evidence_id must be EvidenceId")
        if not isinstance(self.bearing, EvidenceBearing):
            raise InvalidPilotClaimEvaluation("bearing must be EvidenceBearing")
        if not isinstance(self.reliability, EvidenceReliability):
            raise InvalidPilotClaimEvaluation(
                "reliability must be EvidenceReliability"
            )
        if self.reliability is EvidenceReliability.UNASSESSED:
            raise InvalidPilotClaimEvaluation(
                "PR11.2 requires an explicit human reliability assessment for "
                "every EvidenceRecord; EvidenceReliability.UNASSESSED is not permitted"
            )
        object.__setattr__(
            self,
            "coverage_note",
            _clean_text(self.coverage_note, "coverage_note"),
        )
        object.__setattr__(
            self,
            "rationale",
            _clean_text(self.rationale, "evidence rationale"),
        )


@dataclass(frozen=True, slots=True)
class PilotHumanMultiEvidenceEvaluationDecision:
    """Explicit human claim-level decision over an exact multi-evidence basis."""

    evaluation_id: ClaimEvaluationId
    claim_key: str
    claim_id: CapabilityClaimId
    policy_ref: EvaluationPolicyRef
    evaluator_ref: EvaluatorRef
    evaluated_at: datetime
    assessment_decisions: tuple[PilotHumanMultiEvidenceAssessmentDecision, ...]
    coverage: CoverageAssessment
    conflict_status: ConflictStatus
    conclusion: EvaluationConclusion
    evaluation_rationale: str

    def __post_init__(self) -> None:
        if not isinstance(self.evaluation_id, ClaimEvaluationId):
            raise InvalidPilotClaimEvaluation(
                "evaluation_id must be ClaimEvaluationId"
            )
        object.__setattr__(self, "claim_key", _claim_key(self.claim_key))
        if not isinstance(self.claim_id, CapabilityClaimId):
            raise InvalidPilotClaimEvaluation("claim_id must be CapabilityClaimId")
        if not isinstance(self.policy_ref, EvaluationPolicyRef):
            raise InvalidPilotClaimEvaluation(
                "policy_ref must be EvaluationPolicyRef"
            )
        if not isinstance(self.evaluator_ref, EvaluatorRef):
            raise InvalidPilotClaimEvaluation("evaluator_ref must be EvaluatorRef")
        if self.evaluator_ref.kind is not EvaluatorKind.HUMAN:
            raise InvalidPilotClaimEvaluation(
                "PR11.2 requires an explicit HUMAN EvaluatorRef"
            )
        object.__setattr__(
            self,
            "evaluated_at",
            _canonical_time(self.evaluated_at, "evaluated_at"),
        )

        if isinstance(self.assessment_decisions, (str, bytes)):
            raise InvalidPilotClaimEvaluation(
                "assessment_decisions must be an iterable"
            )
        try:
            assessments = tuple(self.assessment_decisions)
        except TypeError as exc:
            raise InvalidPilotClaimEvaluation(
                "assessment_decisions must be iterable"
            ) from exc
        if len(assessments) < 2:
            raise InvalidPilotClaimEvaluation(
                "PR11.2 multi-evidence evaluation requires at least two explicit "
                "EvidenceRecord assessment decisions"
            )
        if any(
            not isinstance(item, PilotHumanMultiEvidenceAssessmentDecision)
            for item in assessments
        ):
            raise InvalidPilotClaimEvaluation(
                "assessment_decisions must contain "
                "PilotHumanMultiEvidenceAssessmentDecision values"
            )
        ids = tuple(item.evidence_id for item in assessments)
        if len(set(ids)) != len(ids):
            raise InvalidPilotClaimEvaluation(
                "PR11.2 assessment_decisions must bind each EvidenceId exactly once"
            )
        object.__setattr__(
            self,
            "assessment_decisions",
            tuple(sorted(assessments, key=lambda item: item.evidence_id)),
        )

        if not isinstance(self.coverage, CoverageAssessment):
            raise InvalidPilotClaimEvaluation("coverage must be CoverageAssessment")
        if not isinstance(self.conflict_status, ConflictStatus):
            raise InvalidPilotClaimEvaluation(
                "conflict_status must be ConflictStatus"
            )
        if self.conflict_status is ConflictStatus.RESOLVED_BY_POLICY:
            raise InvalidPilotClaimEvaluation(
                "PR11.2 cannot use RESOLVED_BY_POLICY because the exact PR11.0 "
                "Pilot 01 policy defines no directional conflict-resolution rule"
            )
        if not isinstance(self.conclusion, EvaluationConclusion):
            raise InvalidPilotClaimEvaluation(
                "conclusion must be EvaluationConclusion"
            )
        object.__setattr__(
            self,
            "evaluation_rationale",
            _clean_text(self.evaluation_rationale, "evaluation_rationale"),
        )


def _tuple_input(value, field_name: str) -> tuple:
    if isinstance(value, (str, bytes)):
        raise InvalidPilotClaimEvaluation(f"{field_name} must be an iterable")
    try:
        return tuple(value)
    except TypeError as exc:
        raise InvalidPilotClaimEvaluation(f"{field_name} must be iterable") from exc


def _basis_entry(selection_entry):
    return (
        selection_entry.allocation_entry.temporal_entry.coordination_entry
        .mechanism_entry.upstream_lineage_entry.basis_entry
    )


def _validate_multi_evidence_coverage_v1(
    *,
    claim_key: str,
    policy: PilotHumanEvaluationPolicy,
    probe_by_evidence_id: dict[EvidenceId, str],
    decision: PilotHumanMultiEvidenceEvaluationDecision,
) -> None:
    template = policy.claim(claim_key)
    decisions_by_id = {
        item.evidence_id: item for item in decision.assessment_decisions
    }
    covered_probe_ids = {
        probe_by_evidence_id[evidence_id]
        for evidence_id, assessment in decisions_by_id.items()
        if assessment.bearing is not EvidenceBearing.NOT_RELEVANT
    }
    required_probe_ids = set(template.sufficiency_probe_ids)

    if decision.coverage.status is CoverageStatus.SUFFICIENT_FOR_CLAIM:
        missing = tuple(sorted(required_probe_ids - covered_probe_ids))
        if missing:
            raise InvalidPilotClaimEvaluation(
                "PR11.2 SUFFICIENT_FOR_CLAIM coverage requires relevant assessed "
                "evidence for every exact PR11.0 sufficiency probe; missing="
                f"{missing!r}"
            )
    elif decision.conclusion not in {
        EvaluationConclusion.INSUFFICIENT,
        EvaluationConclusion.ABSTAINED,
    }:
        raise InvalidPilotClaimEvaluation(
            "PR11.2 partial/unassessed multi-evidence coverage cannot emit a "
            "claim-wide directional or MIXED conclusion; conclusion must remain "
            "INSUFFICIENT or ABSTAINED"
        )


def evaluate_reviewed_civilization_bootstrap_pilot_01_multi_evidence_v1(
    *,
    claim_key: str,
    claim: CapabilityClaim,
    policy: PilotHumanEvaluationPolicy,
    decision: PilotHumanMultiEvidenceEvaluationDecision,
    selection_entries,
    materialization_resolution_bindings,
    source_lineage_graph,
    source_completeness_review,
    mechanism_lineage_graph,
    mechanism_completeness_review,
    coordination_lineage_graph,
    coordination_completeness_review,
    temporal_lineage_graph,
    temporal_completeness_review,
    allocation_lineage_graph,
    allocation_completeness_review,
    selection_lineage_graph,
    selection_completeness_review,
) -> ClaimEvaluation:
    """Create one governed PR2 ClaimEvaluation from one exact multi-evidence basis.

    A PR10.1 terminal dependence PASS is required for the exact basis before any
    aggregation occurs. That PASS is only permission to combine the reviewed
    records under this boundary; it is not claim support, a reliability value,
    statistical independence, or state authority.
    """

    validate_exact_civilization_bootstrap_pilot_01_evaluation_policy_v1(policy)
    key = _claim_key(claim_key)
    validate_civilization_bootstrap_pilot_01_capability_claim_v1(
        claim,
        claim_key=key,
        policy=policy,
    )
    if not isinstance(decision, PilotHumanMultiEvidenceEvaluationDecision):
        raise InvalidPilotClaimEvaluation(
            "decision must be PilotHumanMultiEvidenceEvaluationDecision"
        )

    entries = _tuple_input(selection_entries, "selection_entries")
    bindings = _tuple_input(
        materialization_resolution_bindings,
        "materialization_resolution_bindings",
    )

    validated_entries = tuple(
        validate_pilot_materialized_evidence_reviewed_dependence_preconditions_v1(
            entries,
            materialization_resolution_bindings=bindings,
            source_lineage_graph=source_lineage_graph,
            source_completeness_review=source_completeness_review,
            mechanism_lineage_graph=mechanism_lineage_graph,
            mechanism_completeness_review=mechanism_completeness_review,
            coordination_lineage_graph=coordination_lineage_graph,
            coordination_completeness_review=coordination_completeness_review,
            temporal_lineage_graph=temporal_lineage_graph,
            temporal_completeness_review=temporal_completeness_review,
            allocation_lineage_graph=allocation_lineage_graph,
            allocation_completeness_review=allocation_completeness_review,
            selection_lineage_graph=selection_lineage_graph,
            selection_completeness_review=selection_completeness_review,
        )
    )
    if len(validated_entries) < 2:
        raise InvalidPilotClaimEvaluation(
            "PR11.2 terminal dependence basis must contain at least two observations"
        )

    basis_entries = tuple(_basis_entry(entry) for entry in validated_entries)
    evidence_ids = tuple(item.evidence.evidence_id for item in basis_entries)
    decision_ids = tuple(item.evidence_id for item in decision.assessment_decisions)
    if set(evidence_ids) != set(decision_ids) or len(evidence_ids) != len(decision_ids):
        raise InvalidPilotClaimEvaluation(
            "PR11.2 decision assessment_decisions must provide exact one-to-one "
            "coverage of the terminal EvidenceRecord basis"
        )

    if decision.claim_key != key:
        raise InvalidPilotClaimEvaluation(
            "decision claim_key does not match selected claim_key"
        )
    if decision.claim_id != claim.claim_id:
        raise InvalidPilotClaimEvaluation(
            "decision claim_id does not match exact CapabilityClaim"
        )
    if decision.policy_ref != policy.policy_ref:
        raise InvalidPilotClaimEvaluation(
            "decision policy_ref does not match exact PR11.0 evaluation policy"
        )

    probe_by_evidence_id: dict[EvidenceId, str] = {}
    for basis in basis_entries:
        candidate = basis.candidate
        evidence = basis.evidence
        rubric = policy.rubric(candidate.probe_id)
        if rubric.claim_key != key:
            raise InvalidPilotClaimEvaluation(
                "terminal reviewed evidence probe is not bound to the selected "
                "claim under the exact PR11.0 policy"
            )
        if candidate.subject_ref != claim.subject_ref:
            raise InvalidPilotClaimEvaluation(
                "candidate subject_ref does not match CapabilityClaim subject_ref"
            )
        if evidence.subject_ref != claim.subject_ref:
            raise InvalidPilotClaimEvaluation(
                "EvidenceRecord subject_ref does not match CapabilityClaim subject_ref"
            )
        probe_by_evidence_id[evidence.evidence_id] = candidate.probe_id

    if decision.evaluated_at < claim.created_at:
        raise InvalidPilotClaimEvaluation(
            "evaluated_at must not precede CapabilityClaim created_at"
        )
    latest_recorded_at = max(item.evidence.recorded_at for item in basis_entries)
    if decision.evaluated_at < latest_recorded_at:
        raise InvalidPilotClaimEvaluation(
            "evaluated_at must not precede the latest reviewed EvidenceRecord recorded_at"
        )

    bindings_by_id = {binding.receipt.evidence_id: binding for binding in bindings}
    latest_resolved_at = max(
        bindings_by_id[evidence_id].receipt.resolved_at
        for evidence_id in evidence_ids
    )
    if decision.evaluated_at < latest_resolved_at:
        raise InvalidPilotClaimEvaluation(
            "evaluated_at must not precede the latest reviewed materialization receipt resolved_at"
        )

    dependence_reviews = (
        source_completeness_review,
        mechanism_completeness_review,
        coordination_completeness_review,
        temporal_completeness_review,
        allocation_completeness_review,
        selection_completeness_review,
    )
    latest_dependence_reviewed_at = max(
        review.reviewed_at for review in dependence_reviews
    )
    if decision.evaluated_at < latest_dependence_reviewed_at:
        raise InvalidPilotClaimEvaluation(
            "evaluated_at must not precede the latest PR10.1 terminal dependence "
            "completeness review used by this evaluation"
        )

    _validate_multi_evidence_coverage_v1(
        claim_key=key,
        policy=policy,
        probe_by_evidence_id=probe_by_evidence_id,
        decision=decision,
    )

    assessments = tuple(
        EvidenceAssessment(
            evidence_id=item.evidence_id,
            bearing=item.bearing,
            reliability=item.reliability,
            coverage_note=item.coverage_note,
            rationale=item.rationale,
        )
        for item in decision.assessment_decisions
    )
    return ClaimEvaluation(
        evaluation_id=decision.evaluation_id,
        claim_id=claim.claim_id,
        policy_ref=policy.policy_ref,
        evaluator_ref=decision.evaluator_ref,
        evaluated_at=decision.evaluated_at,
        evidence_assessments=assessments,
        coverage=decision.coverage,
        conflict_status=decision.conflict_status,
        conclusion=decision.conclusion,
        rationale=decision.evaluation_rationale,
    )
