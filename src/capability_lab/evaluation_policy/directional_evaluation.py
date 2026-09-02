"""PR12.12 conservative domain-sufficient directional ClaimEvaluation v1."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json

from capability_lab.epistemics import (
    CapabilityClaimId,
    CapabilitySubjectRef,
    ClaimEvaluation,
    ClaimEvaluationId,
    ClaimEvidenceDispositionCoverageReceipt,
    ClaimEvidenceLineageDependenceReceipt,
    ClaimScope,
    ConflictStatus,
    CoverageAssessment,
    CoverageStatus,
    EpistemicError,
    EpistemicRecordSet,
    EvaluationConclusion,
    EvaluationPolicyRef,
    EvaluatorKind,
    EvaluatorRef,
    EvidenceAssessment,
    EvidenceBearing,
    EvidenceId,
    EvidenceReliability,
)
from capability_lab.epistemics.core import format_time, parse_time
from capability_lab.semantics import CapabilityConceptRef, CapabilityId

from .requirement_application import (
    ClaimDomainPolicyRequirementApplicationReceipt,
    ClaimDomainPolicyRequirementMappingProposal,
    ClaimPolicyRequirementMappingReviewAdmission,
    ClaimPolicyRequirementMappingReviewId,
    ClaimPolicyRequirementMappingReviewLedger,
    InvalidDomainPolicyRequirementApplication,
    claim_policy_requirement_mapping_review_sha256_v1,
    require_approved_claim_policy_requirement_mapping_review_v1,
    validate_claim_domain_policy_requirement_application_v1,
)
from .specification import DOMAIN_EVALUATION_SUFFICIENCY_SEMANTICS_V1


class DomainPolicyDirectionalEvaluationError(EpistemicError):
    """Base error for PR12.12 governed directional evaluation."""


class InvalidDomainPolicyDirectionalEvaluation(DomainPolicyDirectionalEvaluationError):
    """The supplied PR12.12 evaluation or audit receipt is invalid."""


_SCHEMA_VERSION = 1
_FROZEN_SUFFICIENCY_SEMANTICS = "all_required_requirements_explicitly_covered"
_EVALUATOR_REF = EvaluatorRef(
    EvaluatorKind.RULE,
    "capability_lab:pr12_12_domain_directional_rule_v1",
)
_EVALUATION_ID_DOMAIN = b"capability_lab/domain_policy_directional_evaluation_id@1\x00"
_EVALUATION_HASH_DOMAIN = b"capability_lab/domain_policy_directional_evaluation@1\x00"
_APPLICATION_HASH_DOMAIN = b"capability_lab/domain_policy_requirement_application_binding@1\x00"
_RECEIPT_HASH_DOMAIN = b"capability_lab/domain_policy_directional_evaluation_receipt@1\x00"
_SHA256_HEX_DIGITS = frozenset("0123456789abcdef")


def _fail(message: str) -> None:
    raise InvalidDomainPolicyDirectionalEvaluation(message)


def _validate_sha256(value: object, field_name: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in _SHA256_HEX_DIGITS for character in value)
    ):
        _fail(f"{field_name} must be 64 lowercase hexadecimal SHA-256 characters")
    return value


def _canonical_json_bytes(payload: object) -> bytes:
    try:
        return json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise InvalidDomainPolicyDirectionalEvaluation(
            f"payload is not canonically JSON serializable: {exc}"
        ) from exc


def _canonical_json_text(payload: object) -> str:
    return _canonical_json_bytes(payload).decode("utf-8")


def _hash(domain: bytes, payload: object) -> str:
    digest = sha256()
    digest.update(domain)
    digest.update(_canonical_json_bytes(payload))
    return digest.hexdigest()


def _require_exact_object(
    payload: object,
    *,
    expected_keys: set[str],
    field_name: str,
) -> dict:
    if type(payload) is not dict:
        _fail(f"{field_name} must use exact object/dict")
    if any(type(key) is not str for key in payload):
        _fail(f"{field_name} keys must use exact strings")
    unknown = set(payload) - expected_keys
    if unknown:
        _fail(f"{field_name} contains unknown field: {sorted(unknown)[0]}")
    missing = expected_keys - set(payload)
    if missing:
        _fail(f"{field_name} is missing field: {sorted(missing)[0]}")
    return payload


def _no_duplicate_object_pairs(pairs: list[tuple[str, object]]) -> dict:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            _fail(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _parse_canonical_json(payload: object, field_name: str) -> object:
    if type(payload) is not str:
        _fail(f"{field_name} JSON payload must use exact str")
    try:
        return json.loads(
            payload,
            object_pairs_hook=_no_duplicate_object_pairs,
            parse_constant=lambda value: (_ for _ in ()).throw(
                InvalidDomainPolicyDirectionalEvaluation(
                    f"{field_name} JSON forbids non-standard constant: {value}"
                )
            ),
        )
    except InvalidDomainPolicyDirectionalEvaluation:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise InvalidDomainPolicyDirectionalEvaluation(
            f"{field_name} JSON is invalid: {exc}"
        ) from exc


def _strict_utc_time(value: object, field_name: str) -> datetime:
    if type(value) is not datetime or value.tzinfo is not timezone.utc:
        _fail(f"{field_name} must use exact canonical UTC datetime")
    return value


def _strict_claim_id(value: object) -> CapabilityClaimId:
    if type(value) is not CapabilityClaimId or type(value.value) is not str:
        _fail("claim_id must use exact CapabilityClaimId")
    restored = CapabilityClaimId(value.value)
    if restored != value:
        _fail("claim_id must equal strict semantic reconstruction")
    return value


def _strict_subject_ref(value: object) -> CapabilitySubjectRef:
    if type(value) is not CapabilitySubjectRef or type(value.value) is not str:
        _fail("subject_ref must use exact CapabilitySubjectRef")
    restored = CapabilitySubjectRef(value.value)
    if restored != value:
        _fail("subject_ref must equal strict semantic reconstruction")
    return value


def _strict_concept_ref(value: object) -> CapabilityConceptRef:
    if type(value) is not CapabilityConceptRef or type(value.capability_id) is not CapabilityId:
        _fail("concept_ref must use exact CapabilityConceptRef")
    if (
        type(value.capability_id.namespace) is not str
        or type(value.capability_id.key) is not str
        or type(value.revision) is not int
    ):
        _fail("concept_ref contains non-exact scalar fields")
    restored = CapabilityConceptRef(
        CapabilityId(value.capability_id.namespace, value.capability_id.key),
        value.revision,
    )
    if restored != value:
        _fail("concept_ref must equal strict semantic reconstruction")
    return value


def _strict_claim_scope(value: object) -> ClaimScope:
    if type(value) is not ClaimScope:
        _fail("claim_scope must use exact ClaimScope")
    if type(value.description) is not str or type(value.tags) is not tuple:
        _fail("claim_scope must use exact canonical storage")
    if any(type(tag) is not str for tag in value.tags):
        _fail("claim_scope tags must use exact strings")
    restored = ClaimScope(value.description, value.tags)
    if restored != value:
        _fail("claim_scope must equal strict semantic reconstruction")
    return value


def _strict_policy_ref(value: object) -> EvaluationPolicyRef:
    if type(value) is not EvaluationPolicyRef:
        _fail("policy_ref must use exact EvaluationPolicyRef")
    if (
        type(value.namespace) is not str
        or type(value.key) is not str
        or type(value.revision) is not int
    ):
        _fail("policy_ref contains non-exact scalar fields")
    restored = EvaluationPolicyRef(value.namespace, value.key, value.revision)
    if restored != value:
        _fail("policy_ref must equal strict semantic reconstruction")
    return value


def _strict_evaluation_id(value: object) -> ClaimEvaluationId:
    if type(value) is not ClaimEvaluationId or type(value.value) is not str:
        _fail("evaluation_id must use exact ClaimEvaluationId")
    restored = ClaimEvaluationId(value.value)
    if restored != value:
        _fail("evaluation_id must equal strict semantic reconstruction")
    return value


def _strict_reviewer_id(value: object) -> ClaimPolicyRequirementMappingReviewId:
    if (
        type(value) is not ClaimPolicyRequirementMappingReviewId
        or type(value.value) is not str
    ):
        _fail("mapping_review_id must use exact ClaimPolicyRequirementMappingReviewId")
    restored = ClaimPolicyRequirementMappingReviewId(value.value)
    if restored != value:
        _fail("mapping_review_id must equal strict semantic reconstruction")
    return value


def _strict_assessment(value: object, field_name: str) -> EvidenceAssessment:
    if type(value) is not EvidenceAssessment:
        _fail(f"{field_name} must use exact EvidenceAssessment")
    if type(value.evidence_id) is not EvidenceId or type(value.evidence_id.value) is not str:
        _fail(f"{field_name}.evidence_id must use exact EvidenceId")
    if type(value.bearing) is not EvidenceBearing:
        _fail(f"{field_name}.bearing must use exact EvidenceBearing")
    if type(value.reliability) is not EvidenceReliability:
        _fail(f"{field_name}.reliability must use exact EvidenceReliability")
    if type(value.coverage_note) is not str or type(value.rationale) is not str:
        _fail(f"{field_name} text fields must use exact str")
    restored = EvidenceAssessment(
        EvidenceId(value.evidence_id.value),
        value.bearing,
        value.reliability,
        value.coverage_note,
        value.rationale,
    )
    if restored != value:
        _fail(f"{field_name} must equal strict semantic reconstruction")
    return value


def _strict_coverage_assessment(value: object) -> CoverageAssessment:
    if type(value) is not CoverageAssessment:
        _fail("evaluation coverage must use exact CoverageAssessment")
    if type(value.status) is not CoverageStatus or type(value.notes) is not str:
        _fail("evaluation coverage contains non-exact fields")
    restored = CoverageAssessment(value.status, value.notes)
    if restored != value:
        _fail("evaluation coverage must equal strict semantic reconstruction")
    return value


def _strict_evaluator_ref(value: object) -> EvaluatorRef:
    if type(value) is not EvaluatorRef:
        _fail("evaluator_ref must use exact EvaluatorRef")
    if type(value.kind) is not EvaluatorKind or type(value.ref) is not str:
        _fail("evaluator_ref contains non-exact fields")
    restored = EvaluatorRef(value.kind, value.ref)
    if restored != value:
        _fail("evaluator_ref must equal strict semantic reconstruction")
    return value


def _strict_evaluation(value: object) -> ClaimEvaluation:
    if type(value) is not ClaimEvaluation:
        _fail("evaluation must use exact ClaimEvaluation")
    _strict_evaluation_id(value.evaluation_id)
    _strict_claim_id(value.claim_id)
    _strict_policy_ref(value.policy_ref)
    _strict_evaluator_ref(value.evaluator_ref)
    _strict_utc_time(value.evaluated_at, "evaluation evaluated_at")
    if type(value.evidence_assessments) is not tuple:
        _fail("evaluation evidence_assessments must use exact tuple")
    for index, assessment in enumerate(value.evidence_assessments):
        _strict_assessment(assessment, f"evaluation evidence_assessments[{index}]")
    canonical_assessments = tuple(
        sorted(value.evidence_assessments, key=lambda item: item.evidence_id)
    )
    if canonical_assessments != value.evidence_assessments:
        _fail("evaluation evidence_assessments must use canonical evidence-id ordering")
    _strict_coverage_assessment(value.coverage)
    if type(value.conflict_status) is not ConflictStatus:
        _fail("evaluation conflict_status must use exact ConflictStatus")
    if type(value.conclusion) is not EvaluationConclusion:
        _fail("evaluation conclusion must use exact EvaluationConclusion")
    if type(value.rationale) is not str:
        _fail("evaluation rationale must use exact str")
    restored = ClaimEvaluation(
        evaluation_id=ClaimEvaluationId(value.evaluation_id.value),
        claim_id=CapabilityClaimId(value.claim_id.value),
        policy_ref=EvaluationPolicyRef(
            value.policy_ref.namespace,
            value.policy_ref.key,
            value.policy_ref.revision,
        ),
        evaluator_ref=EvaluatorRef(value.evaluator_ref.kind, value.evaluator_ref.ref),
        evaluated_at=value.evaluated_at,
        evidence_assessments=tuple(
            EvidenceAssessment(
                EvidenceId(item.evidence_id.value),
                item.bearing,
                item.reliability,
                item.coverage_note,
                item.rationale,
            )
            for item in value.evidence_assessments
        ),
        coverage=CoverageAssessment(value.coverage.status, value.coverage.notes),
        conflict_status=value.conflict_status,
        conclusion=value.conclusion,
        rationale=value.rationale,
    )
    if restored != value:
        _fail("evaluation must equal strict semantic reconstruction")
    return value


def _assessment_to_dict(value: EvidenceAssessment) -> dict:
    checked = _strict_assessment(value, "evidence assessment")
    return {
        "evidence_id": checked.evidence_id.value,
        "bearing": checked.bearing.value,
        "reliability": checked.reliability.value,
        "coverage_note": checked.coverage_note,
        "rationale": checked.rationale,
    }


def _evaluation_payload(
    *,
    evaluation_id: ClaimEvaluationId | None,
    claim_id: CapabilityClaimId,
    policy_ref: EvaluationPolicyRef,
    evaluator_ref: EvaluatorRef,
    evaluated_at: datetime,
    evidence_assessments: tuple[EvidenceAssessment, ...],
    coverage: CoverageAssessment,
    conflict_status: ConflictStatus,
    conclusion: EvaluationConclusion,
    rationale: str,
) -> dict:
    _strict_claim_id(claim_id)
    _strict_policy_ref(policy_ref)
    _strict_evaluator_ref(evaluator_ref)
    _strict_utc_time(evaluated_at, "evaluation evaluated_at")
    if type(evidence_assessments) is not tuple:
        _fail("evaluation evidence_assessments must use exact tuple")
    assessments = tuple(
        sorted(
            (
                _strict_assessment(item, "evaluation evidence assessment")
                for item in evidence_assessments
            ),
            key=lambda item: item.evidence_id,
        )
    )
    _strict_coverage_assessment(coverage)
    if type(conflict_status) is not ConflictStatus:
        _fail("evaluation conflict_status must use exact ConflictStatus")
    if type(conclusion) is not EvaluationConclusion:
        _fail("evaluation conclusion must use exact EvaluationConclusion")
    if type(rationale) is not str or not rationale.strip():
        _fail("evaluation rationale must use exact non-empty str")
    payload = {
        "claim_id": claim_id.value,
        "policy_ref": str(policy_ref),
        "evaluator_ref": {"kind": evaluator_ref.kind.value, "ref": evaluator_ref.ref},
        "evaluated_at": format_time(evaluated_at),
        "evidence_assessments": [_assessment_to_dict(item) for item in assessments],
        "coverage": {"status": coverage.status.value, "notes": coverage.notes},
        "conflict_status": conflict_status.value,
        "conclusion": conclusion.value,
        "rationale": rationale,
    }
    if evaluation_id is not None:
        _strict_evaluation_id(evaluation_id)
        payload = {"evaluation_id": evaluation_id.value, **payload}
    return payload


def _strict_evaluation_payload(value: ClaimEvaluation, *, include_id: bool) -> dict:
    checked = _strict_evaluation(value)
    return _evaluation_payload(
        evaluation_id=checked.evaluation_id if include_id else None,
        claim_id=checked.claim_id,
        policy_ref=checked.policy_ref,
        evaluator_ref=checked.evaluator_ref,
        evaluated_at=checked.evaluated_at,
        evidence_assessments=checked.evidence_assessments,
        coverage=checked.coverage,
        conflict_status=checked.conflict_status,
        conclusion=checked.conclusion,
        rationale=checked.rationale,
    )


def claim_domain_policy_directional_claim_evaluation_sha256_v1(
    evaluation: ClaimEvaluation,
) -> str:
    return _hash(_EVALUATION_HASH_DOMAIN, _strict_evaluation_payload(evaluation, include_id=True))


def _requirement_application_sha256(
    application: ClaimDomainPolicyRequirementApplicationReceipt,
) -> str:
    if type(application) is not ClaimDomainPolicyRequirementApplicationReceipt:
        _fail("application must use exact ClaimDomainPolicyRequirementApplicationReceipt")
    return _hash(_APPLICATION_HASH_DOMAIN, application.to_dict())


def _scope_to_dict(scope: ClaimScope) -> dict:
    scope = _strict_claim_scope(scope)
    return {"description": scope.description, "tags": list(scope.tags)}


def _scope_from_dict(payload: object) -> ClaimScope:
    data = _require_exact_object(
        payload,
        expected_keys={"description", "tags"},
        field_name="claim_scope",
    )
    if (
        type(data["description"]) is not str
        or type(data["tags"]) is not list
        or any(type(item) is not str for item in data["tags"])
    ):
        _fail("claim_scope must use exact description string and tags array/list")
    scope = ClaimScope(data["description"], tuple(data["tags"]))
    if _scope_to_dict(scope) != data:
        _fail("claim_scope payload must use canonical ordering/content")
    return scope


@dataclass(frozen=True, slots=True)
class ClaimDomainPolicyDirectionalEvaluationReceipt:
    snapshot_sha256: str
    claim_id: CapabilityClaimId
    subject_ref: CapabilitySubjectRef
    concept_ref: CapabilityConceptRef
    claim_scope: ClaimScope
    as_of: datetime
    policy_ref: EvaluationPolicyRef
    specification_sha256: str
    disposition_coverage_sha256: str
    lineage_dependence_sha256: str
    requirement_application_sha256: str
    mapping_review_id: ClaimPolicyRequirementMappingReviewId
    mapping_review_sha256: str
    mapping_reviewed_at: datetime
    evaluation_id: ClaimEvaluationId
    evaluation_sha256: str
    coverage_status: CoverageStatus
    conflict_status: ConflictStatus
    conclusion: EvaluationConclusion

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "snapshot_sha256",
            _validate_sha256(self.snapshot_sha256, "snapshot_sha256"),
        )
        _strict_claim_id(self.claim_id)
        _strict_subject_ref(self.subject_ref)
        _strict_concept_ref(self.concept_ref)
        _strict_claim_scope(self.claim_scope)
        _strict_utc_time(self.as_of, "receipt as_of")
        _strict_policy_ref(self.policy_ref)
        for name in (
            "specification_sha256",
            "disposition_coverage_sha256",
            "lineage_dependence_sha256",
            "requirement_application_sha256",
            "mapping_review_sha256",
            "evaluation_sha256",
        ):
            object.__setattr__(self, name, _validate_sha256(getattr(self, name), name))
        _strict_reviewer_id(self.mapping_review_id)
        _strict_utc_time(self.mapping_reviewed_at, "mapping_reviewed_at")
        _strict_evaluation_id(self.evaluation_id)
        if type(self.coverage_status) is not CoverageStatus:
            _fail("coverage_status must use exact CoverageStatus")
        if type(self.conflict_status) is not ConflictStatus:
            _fail("conflict_status must use exact ConflictStatus")
        if type(self.conclusion) is not EvaluationConclusion:
            _fail("conclusion must use exact EvaluationConclusion")
        if self.conflict_status is ConflictStatus.RESOLVED_BY_POLICY:
            _fail("PR12.12 v1 never emits RESOLVED_BY_POLICY")

    def to_dict(self) -> dict:
        return claim_domain_policy_directional_evaluation_receipt_to_dict(self)

    @classmethod
    def from_dict(cls, payload: object) -> "ClaimDomainPolicyDirectionalEvaluationReceipt":
        return claim_domain_policy_directional_evaluation_receipt_from_dict(payload)

    def to_json(self) -> str:
        return claim_domain_policy_directional_evaluation_receipt_to_json(self)

    @classmethod
    def from_json(cls, payload: object) -> "ClaimDomainPolicyDirectionalEvaluationReceipt":
        return claim_domain_policy_directional_evaluation_receipt_from_json(payload)


def _strict_receipt(value: object) -> ClaimDomainPolicyDirectionalEvaluationReceipt:
    if type(value) is not ClaimDomainPolicyDirectionalEvaluationReceipt:
        _fail("directional evaluation receipt must use exact ClaimDomainPolicyDirectionalEvaluationReceipt")
    restored = claim_domain_policy_directional_evaluation_receipt_from_dict(value.to_dict())
    if restored != value:
        _fail("directional evaluation receipt must equal strict semantic reconstruction")
    return value


def claim_domain_policy_directional_evaluation_receipt_to_dict(
    receipt: ClaimDomainPolicyDirectionalEvaluationReceipt,
) -> dict:
    if type(receipt) is not ClaimDomainPolicyDirectionalEvaluationReceipt:
        _fail("directional evaluation receipt must use exact ClaimDomainPolicyDirectionalEvaluationReceipt")
    _validate_sha256(receipt.snapshot_sha256, "snapshot_sha256")
    _strict_claim_id(receipt.claim_id)
    _strict_subject_ref(receipt.subject_ref)
    _strict_concept_ref(receipt.concept_ref)
    _strict_claim_scope(receipt.claim_scope)
    _strict_utc_time(receipt.as_of, "receipt as_of")
    _strict_policy_ref(receipt.policy_ref)
    for name in (
        "specification_sha256",
        "disposition_coverage_sha256",
        "lineage_dependence_sha256",
        "requirement_application_sha256",
        "mapping_review_sha256",
        "evaluation_sha256",
    ):
        _validate_sha256(getattr(receipt, name), name)
    _strict_reviewer_id(receipt.mapping_review_id)
    _strict_utc_time(receipt.mapping_reviewed_at, "mapping_reviewed_at")
    _strict_evaluation_id(receipt.evaluation_id)
    if type(receipt.coverage_status) is not CoverageStatus:
        _fail("coverage_status must use exact CoverageStatus")
    if type(receipt.conflict_status) is not ConflictStatus:
        _fail("conflict_status must use exact ConflictStatus")
    if type(receipt.conclusion) is not EvaluationConclusion:
        _fail("conclusion must use exact EvaluationConclusion")
    if receipt.conflict_status is ConflictStatus.RESOLVED_BY_POLICY:
        _fail("PR12.12 v1 never emits RESOLVED_BY_POLICY")
    return {
        "schema_version": _SCHEMA_VERSION,
        "snapshot_sha256": receipt.snapshot_sha256,
        "claim_id": receipt.claim_id.value,
        "subject_ref": receipt.subject_ref.value,
        "concept_ref": str(receipt.concept_ref),
        "claim_scope": _scope_to_dict(receipt.claim_scope),
        "as_of": format_time(receipt.as_of),
        "policy_ref": str(receipt.policy_ref),
        "specification_sha256": receipt.specification_sha256,
        "disposition_coverage_sha256": receipt.disposition_coverage_sha256,
        "lineage_dependence_sha256": receipt.lineage_dependence_sha256,
        "requirement_application_sha256": receipt.requirement_application_sha256,
        "mapping_review_id": receipt.mapping_review_id.value,
        "mapping_review_sha256": receipt.mapping_review_sha256,
        "mapping_reviewed_at": format_time(receipt.mapping_reviewed_at),
        "evaluation_id": receipt.evaluation_id.value,
        "evaluation_sha256": receipt.evaluation_sha256,
        "coverage_status": receipt.coverage_status.value,
        "conflict_status": receipt.conflict_status.value,
        "conclusion": receipt.conclusion.value,
    }


def claim_domain_policy_directional_evaluation_receipt_from_dict(
    payload: object,
) -> ClaimDomainPolicyDirectionalEvaluationReceipt:
    keys = {
        "schema_version",
        "snapshot_sha256",
        "claim_id",
        "subject_ref",
        "concept_ref",
        "claim_scope",
        "as_of",
        "policy_ref",
        "specification_sha256",
        "disposition_coverage_sha256",
        "lineage_dependence_sha256",
        "requirement_application_sha256",
        "mapping_review_id",
        "mapping_review_sha256",
        "mapping_reviewed_at",
        "evaluation_id",
        "evaluation_sha256",
        "coverage_status",
        "conflict_status",
        "conclusion",
    }
    data = _require_exact_object(
        payload,
        expected_keys=keys,
        field_name="directional evaluation receipt",
    )
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        _fail("directional evaluation receipt schema_version must be exact integer 1")
    for key in keys - {"schema_version", "claim_scope"}:
        if type(data[key]) is not str:
            _fail(f"directional evaluation receipt {key} must use exact string")
    try:
        receipt = ClaimDomainPolicyDirectionalEvaluationReceipt(
            snapshot_sha256=data["snapshot_sha256"],
            claim_id=CapabilityClaimId(data["claim_id"]),
            subject_ref=CapabilitySubjectRef(data["subject_ref"]),
            concept_ref=CapabilityConceptRef.parse(data["concept_ref"]),
            claim_scope=_scope_from_dict(data["claim_scope"]),
            as_of=parse_time(data["as_of"], "receipt as_of"),
            policy_ref=EvaluationPolicyRef.parse(data["policy_ref"]),
            specification_sha256=data["specification_sha256"],
            disposition_coverage_sha256=data["disposition_coverage_sha256"],
            lineage_dependence_sha256=data["lineage_dependence_sha256"],
            requirement_application_sha256=data["requirement_application_sha256"],
            mapping_review_id=ClaimPolicyRequirementMappingReviewId(
                data["mapping_review_id"]
            ),
            mapping_review_sha256=data["mapping_review_sha256"],
            mapping_reviewed_at=parse_time(
                data["mapping_reviewed_at"],
                "mapping_reviewed_at",
            ),
            evaluation_id=ClaimEvaluationId(data["evaluation_id"]),
            evaluation_sha256=data["evaluation_sha256"],
            coverage_status=CoverageStatus(data["coverage_status"]),
            conflict_status=ConflictStatus(data["conflict_status"]),
            conclusion=EvaluationConclusion(data["conclusion"]),
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InvalidDomainPolicyDirectionalEvaluation):
            raise
        raise InvalidDomainPolicyDirectionalEvaluation(
            f"directional evaluation receipt is invalid: {exc}"
        ) from exc
    if receipt.to_dict() != data:
        _fail("directional evaluation receipt payload must use canonical ordering/content")
    return receipt


def claim_domain_policy_directional_evaluation_receipt_to_json(
    receipt: ClaimDomainPolicyDirectionalEvaluationReceipt,
) -> str:
    return _canonical_json_text(receipt.to_dict())


def claim_domain_policy_directional_evaluation_receipt_from_json(
    payload: object,
) -> ClaimDomainPolicyDirectionalEvaluationReceipt:
    data = _parse_canonical_json(payload, "directional evaluation receipt")
    receipt = claim_domain_policy_directional_evaluation_receipt_from_dict(data)
    if receipt.to_json() != payload:
        _fail("directional evaluation receipt JSON must use exact canonical encoding")
    return receipt


def claim_domain_policy_directional_evaluation_receipt_sha256_v1(
    receipt: ClaimDomainPolicyDirectionalEvaluationReceipt,
) -> str:
    return _hash(_RECEIPT_HASH_DOMAIN, _strict_receipt(receipt).to_dict())


def _derive_direction(
    *,
    coverage_complete: bool,
    assessments: tuple[EvidenceAssessment, ...],
) -> tuple[CoverageAssessment, ConflictStatus, EvaluationConclusion]:
    if type(coverage_complete) is not bool:
        _fail("coverage_complete must use exact bool")
    has_support = any(item.bearing is EvidenceBearing.SUPPORTS for item in assessments)
    has_contradiction = any(
        item.bearing is EvidenceBearing.CONTRADICTS for item in assessments
    )
    has_conflict = has_support and has_contradiction

    if not coverage_complete:
        return (
            CoverageAssessment(
                CoverageStatus.PARTIAL,
                "At least one required admitted policy requirement is not explicitly covered under the frozen PR12.6/PR12.11 sufficiency rule.",
            ),
            ConflictStatus.UNRESOLVED if has_conflict else ConflictStatus.NONE,
            EvaluationConclusion.INSUFFICIENT,
        )

    coverage = CoverageAssessment(
        CoverageStatus.SUFFICIENT_FOR_CLAIM,
        "All required admitted policy requirements are explicitly covered under the frozen PR12.6/PR12.11 sufficiency rule.",
    )
    if has_conflict:
        return coverage, ConflictStatus.UNRESOLVED, EvaluationConclusion.MIXED
    if has_support:
        return coverage, ConflictStatus.NONE, EvaluationConclusion.SUPPORTED
    if has_contradiction:
        return coverage, ConflictStatus.NONE, EvaluationConclusion.CONTRADICTED
    return coverage, ConflictStatus.NONE, EvaluationConclusion.ABSTAINED


def _evaluation_rationale(
    conclusion: EvaluationConclusion,
    conflict_status: ConflictStatus,
) -> str:
    return (
        "PR12.12 deterministically evaluates the complete exact PR12.9 disposition "
        "universe after full PR12.11 governed replay. Requirement mapping is not "
        "used as a directional evidence selector; reliability, evidence counts, "
        "recency, and lineage do not weight direction. "
        f"Result: conclusion={conclusion.value}, conflict={conflict_status.value}."
    )


def build_claim_domain_policy_directional_evaluation_v1(
    *,
    records: EpistemicRecordSet,
    claim_id: CapabilityClaimId,
    as_of: datetime,
    coverage: ClaimEvidenceDispositionCoverageReceipt,
    lineage: ClaimEvidenceLineageDependenceReceipt,
    registry: object,
    proposal: ClaimDomainPolicyRequirementMappingProposal,
    review_ledger: ClaimPolicyRequirementMappingReviewLedger,
    review_admission: ClaimPolicyRequirementMappingReviewAdmission,
    application: ClaimDomainPolicyRequirementApplicationReceipt,
) -> tuple[ClaimEvaluation, ClaimDomainPolicyDirectionalEvaluationReceipt]:
    """Build the deterministic PR12.12 ClaimEvaluation after exact PR12.11 replay."""

    if (
        DOMAIN_EVALUATION_SUFFICIENCY_SEMANTICS_V1
        != _FROZEN_SUFFICIENCY_SEMANTICS
    ):
        _fail("PR12.6 sufficiency semantics drifted from the PR12.12 frozen contract")

    try:
        checked_application = validate_claim_domain_policy_requirement_application_v1(
            records=records,
            claim_id=claim_id,
            as_of=as_of,
            coverage=coverage,
            lineage=lineage,
            registry=registry,
            proposal=proposal,
            review_ledger=review_ledger,
            review_admission=review_admission,
            application=application,
        )
        review = require_approved_claim_policy_requirement_mapping_review_v1(
            review_ledger=review_ledger,
            proposal=proposal,
            review_admission=review_admission,
        )
    except InvalidDomainPolicyRequirementApplication as exc:
        raise InvalidDomainPolicyDirectionalEvaluation(
            f"PR12.11 governed application replay failed: {exc}"
        ) from exc

    if type(coverage) is not ClaimEvidenceDispositionCoverageReceipt:
        _fail("coverage must use exact ClaimEvidenceDispositionCoverageReceipt")
    if type(lineage) is not ClaimEvidenceLineageDependenceReceipt:
        _fail("lineage must use exact ClaimEvidenceLineageDependenceReceipt")

    assessments = tuple(
        sorted(
            (
                _strict_assessment(item, "PR12.9 disposition")
                for item in coverage.dispositions
            ),
            key=lambda item: item.evidence_id,
        )
    )
    coverage_assessment, conflict_status, conclusion = _derive_direction(
        coverage_complete=checked_application.required_requirement_coverage_complete,
        assessments=assessments,
    )
    rationale = _evaluation_rationale(conclusion, conflict_status)

    id_payload = _evaluation_payload(
        evaluation_id=None,
        claim_id=checked_application.claim_id,
        policy_ref=checked_application.policy_ref,
        evaluator_ref=_EVALUATOR_REF,
        evaluated_at=review.reviewed_at,
        evidence_assessments=assessments,
        coverage=coverage_assessment,
        conflict_status=conflict_status,
        conclusion=conclusion,
        rationale=rationale,
    )
    evaluation_id = ClaimEvaluationId(
        f"pr12_12:{_hash(_EVALUATION_ID_DOMAIN, id_payload)}"
    )
    evaluation = ClaimEvaluation(
        evaluation_id=evaluation_id,
        claim_id=checked_application.claim_id,
        policy_ref=checked_application.policy_ref,
        evaluator_ref=_EVALUATOR_REF,
        evaluated_at=review.reviewed_at,
        evidence_assessments=assessments,
        coverage=coverage_assessment,
        conflict_status=conflict_status,
        conclusion=conclusion,
        rationale=rationale,
    )
    _strict_evaluation(evaluation)

    receipt = ClaimDomainPolicyDirectionalEvaluationReceipt(
        snapshot_sha256=checked_application.snapshot_sha256,
        claim_id=checked_application.claim_id,
        subject_ref=checked_application.subject_ref,
        concept_ref=checked_application.concept_ref,
        claim_scope=checked_application.claim_scope,
        as_of=checked_application.as_of,
        policy_ref=checked_application.policy_ref,
        specification_sha256=checked_application.specification_sha256,
        disposition_coverage_sha256=checked_application.disposition_coverage_sha256,
        lineage_dependence_sha256=checked_application.lineage_dependence_sha256,
        requirement_application_sha256=_requirement_application_sha256(
            checked_application
        ),
        mapping_review_id=review.review_id,
        mapping_review_sha256=claim_policy_requirement_mapping_review_sha256_v1(
            review
        ),
        mapping_reviewed_at=review.reviewed_at,
        evaluation_id=evaluation.evaluation_id,
        evaluation_sha256=claim_domain_policy_directional_claim_evaluation_sha256_v1(
            evaluation
        ),
        coverage_status=evaluation.coverage.status,
        conflict_status=evaluation.conflict_status,
        conclusion=evaluation.conclusion,
    )
    return evaluation, receipt


def validate_claim_domain_policy_directional_evaluation_v1(
    *,
    records: EpistemicRecordSet,
    claim_id: CapabilityClaimId,
    as_of: datetime,
    coverage: ClaimEvidenceDispositionCoverageReceipt,
    lineage: ClaimEvidenceLineageDependenceReceipt,
    registry: object,
    proposal: ClaimDomainPolicyRequirementMappingProposal,
    review_ledger: ClaimPolicyRequirementMappingReviewLedger,
    review_admission: ClaimPolicyRequirementMappingReviewAdmission,
    application: ClaimDomainPolicyRequirementApplicationReceipt,
    evaluation: ClaimEvaluation,
    receipt: ClaimDomainPolicyDirectionalEvaluationReceipt,
) -> tuple[ClaimEvaluation, ClaimDomainPolicyDirectionalEvaluationReceipt]:
    """Fully replay PR12.7-PR12.12 and require exact deterministic equality."""

    supplied_evaluation = _strict_evaluation(evaluation)
    supplied_receipt = _strict_receipt(receipt)
    expected_evaluation, expected_receipt = (
        build_claim_domain_policy_directional_evaluation_v1(
            records=records,
            claim_id=claim_id,
            as_of=as_of,
            coverage=coverage,
            lineage=lineage,
            registry=registry,
            proposal=proposal,
            review_ledger=review_ledger,
            review_admission=review_admission,
            application=application,
        )
    )
    if supplied_evaluation != expected_evaluation:
        _fail("ClaimEvaluation does not match complete governed PR12.12 replay")
    if supplied_receipt != expected_receipt:
        _fail("directional evaluation receipt does not match complete governed PR12.12 replay")
    return supplied_evaluation, supplied_receipt
