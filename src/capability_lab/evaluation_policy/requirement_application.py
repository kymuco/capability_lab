"""PR12.11 governed admitted-policy requirement mapping and application v1."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import json
import re
import unicodedata

from capability_lab.epistemics import (
    CapabilityClaim,
    CapabilityClaimId,
    CapabilitySubjectRef,
    ClaimEvidenceDispositionCoverageReceipt,
    ClaimEvidenceLineageDependenceReceipt,
    ClaimScope,
    EpistemicError,
    EpistemicRecordSet,
    EvaluationPolicyRef,
    EvidenceBearing,
    EvidenceId,
)
from capability_lab.epistemics.claim_evidence_disposition_coverage import (
    ClaimEvidenceDispositionCoverageError,
    validate_complete_claim_evidence_disposition_coverage_v1,
)
from capability_lab.epistemics.claim_evidence_lineage_dependence import (
    ClaimEvidenceLineageDependenceError,
    validate_claim_evidence_lineage_dependence_v1,
)
from capability_lab.epistemics.core import canonical_time, format_time, parse_time
from capability_lab.semantics import CapabilityConceptRef, CapabilityId

from . import requirement_application_authority as _process_authority
from .registry_authority import resolve_admitted_domain_evaluation_policy_v1
from .specification import (
    DomainEvaluationPolicySpecification,
    domain_evaluation_policy_specification_applies_to_v1,
    domain_evaluation_policy_specification_sha256_v1,
)


class DomainPolicyRequirementApplicationError(EpistemicError):
    """Base error for PR12.11 governed requirement mapping/application."""


class InvalidDomainPolicyRequirementApplication(DomainPolicyRequirementApplicationError):
    """The supplied PR12.11 artifact or transition is invalid."""


class DomainPolicyRequirementApplicationDisposition(str, Enum):
    COVERED = "COVERED"
    NOT_COVERED = "NOT_COVERED"
    UNRESOLVED = "UNRESOLVED"


class ClaimPolicyRequirementMappingReviewerKind(str, Enum):
    HUMAN = "HUMAN"


class ClaimPolicyRequirementMappingReviewVerdict(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"


_SCHEMA_VERSION = 1
_REQUIREMENT_KEY_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_OPAQUE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_SHA256_HEX_DIGITS = frozenset("0123456789abcdef")
_PROPOSAL_HASH_DOMAIN = b"capability_lab/claim_domain_policy_requirement_mapping_proposal@1\x00"
_REVIEW_HASH_DOMAIN = b"capability_lab/claim_policy_requirement_mapping_review@1\x00"
_REVIEW_LEDGER_HASH_DOMAIN = b"capability_lab/claim_policy_requirement_mapping_review_ledger@1\x00"


def _fail(message: str) -> None:
    raise InvalidDomainPolicyRequirementApplication(message)


def _validate_sha256(value: object, field_name: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in _SHA256_HEX_DIGITS for character in value)
    ):
        _fail(f"{field_name} must be 64 lowercase hexadecimal SHA-256 characters")
    return value


def _opaque_id(value: object, field_name: str) -> str:
    if type(value) is not str or _OPAQUE_ID_RE.fullmatch(value) is None:
        _fail(f"{field_name} must be a canonical opaque ASCII identifier")
    return value


def _text(value: object, field_name: str) -> str:
    if type(value) is not str:
        _fail(f"{field_name} must use exact str")
    cleaned = unicodedata.normalize("NFC", value).strip()
    if not cleaned:
        _fail(f"{field_name} must be non-empty")
    return cleaned


def _canonical_boundary(value: object, field_name: str) -> datetime:
    if type(value) is not datetime:
        _fail(f"{field_name} must use exact datetime")
    try:
        return canonical_time(value, field_name)
    except EpistemicError as exc:
        raise InvalidDomainPolicyRequirementApplication(str(exc)) from exc


def _strict_stored_utc_time(value: object, field_name: str) -> datetime:
    if type(value) is not datetime or value.tzinfo is not timezone.utc:
        _fail(f"{field_name} must use exact canonical UTC datetime")
    return value


def _strict_claim_id(value: object, field_name: str = "claim_id") -> CapabilityClaimId:
    if type(value) is not CapabilityClaimId or type(value.value) is not str:
        _fail(f"{field_name} must use exact CapabilityClaimId")
    try:
        restored = CapabilityClaimId(value.value)
    except (TypeError, ValueError) as exc:
        raise InvalidDomainPolicyRequirementApplication(
            f"{field_name} failed strict reconstruction: {exc}"
        ) from exc
    if restored != value:
        _fail(f"{field_name} must equal strict semantic reconstruction")
    return value


def _strict_subject_ref(value: object) -> CapabilitySubjectRef:
    if type(value) is not CapabilitySubjectRef or type(value.value) is not str:
        _fail("subject_ref must use exact CapabilitySubjectRef")
    restored = CapabilitySubjectRef(value.value)
    if restored != value:
        _fail("subject_ref must equal strict semantic reconstruction")
    return value


def _strict_evidence_id(value: object, field_name: str = "evidence_id") -> EvidenceId:
    if type(value) is not EvidenceId or type(value.value) is not str:
        _fail(f"{field_name} must use exact EvidenceId")
    restored = EvidenceId(value.value)
    if restored != value:
        _fail(f"{field_name} must equal strict semantic reconstruction")
    return value


def _strict_evidence_ids(value: object, field_name: str) -> tuple[EvidenceId, ...]:
    if type(value) is not tuple:
        _fail(f"{field_name} must use exact tuple")
    for index, item in enumerate(value):
        _strict_evidence_id(item, f"{field_name}[{index}]")
    if len(set(value)) != len(value):
        _fail(f"{field_name} must not contain duplicate evidence ids")
    canonical = tuple(sorted(value))
    if canonical != value:
        _fail(f"{field_name} must use canonical evidence-id ordering")
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
    if type(value.namespace) is not str or type(value.key) is not str or type(value.revision) is not int:
        _fail("policy_ref contains non-exact scalar fields")
    restored = EvaluationPolicyRef(value.namespace, value.key, value.revision)
    if restored != value:
        _fail("policy_ref must equal strict semantic reconstruction")
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
        raise InvalidDomainPolicyRequirementApplication(
            f"payload is not canonically JSON serializable: {exc}"
        ) from exc


def _hash(domain: bytes, payload: object) -> str:
    digest = sha256()
    digest.update(domain)
    digest.update(_canonical_json_bytes(payload))
    return digest.hexdigest()


def _require_exact_object(payload: object, *, expected_keys: set[str], field_name: str) -> dict:
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
                InvalidDomainPolicyRequirementApplication(
                    f"{field_name} JSON forbids non-standard constant: {value}"
                )
            ),
        )
    except InvalidDomainPolicyRequirementApplication:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise InvalidDomainPolicyRequirementApplication(
            f"{field_name} JSON is invalid: {exc}"
        ) from exc


def _canonical_json_text(payload: object) -> str:
    return _canonical_json_bytes(payload).decode("utf-8")


def _coverage_sha256(coverage: ClaimEvidenceDispositionCoverageReceipt) -> str:
    if type(coverage) is not ClaimEvidenceDispositionCoverageReceipt:
        _fail("coverage must use exact ClaimEvidenceDispositionCoverageReceipt")
    return sha256(coverage.to_json().encode("utf-8")).hexdigest()


def _lineage_sha256(lineage: ClaimEvidenceLineageDependenceReceipt) -> str:
    if type(lineage) is not ClaimEvidenceLineageDependenceReceipt:
        _fail("lineage must use exact ClaimEvidenceLineageDependenceReceipt")
    return sha256(lineage.to_json().encode("utf-8")).hexdigest()


@dataclass(frozen=True, order=True, slots=True)
class DomainPolicyRequirementApplicationEntry:
    requirement_key: str
    disposition: DomainPolicyRequirementApplicationDisposition
    evidence_ids: tuple[EvidenceId, ...]
    rationale: str

    def __post_init__(self) -> None:
        if type(self.requirement_key) is not str or _REQUIREMENT_KEY_RE.fullmatch(self.requirement_key) is None:
            _fail("requirement_key must use lowercase machine-key syntax")
        if type(self.disposition) is not DomainPolicyRequirementApplicationDisposition:
            _fail("disposition must use exact DomainPolicyRequirementApplicationDisposition")
        if type(self.evidence_ids) is not tuple:
            _fail("evidence_ids must use exact tuple")
        for index, item in enumerate(self.evidence_ids):
            _strict_evidence_id(item, f"evidence_ids[{index}]")
        ids = tuple(sorted(self.evidence_ids))
        if len(set(ids)) != len(ids):
            _fail("evidence_ids must not contain duplicate evidence ids")
        object.__setattr__(self, "evidence_ids", ids)
        object.__setattr__(self, "rationale", _text(self.rationale, "application rationale"))
        if self.disposition is DomainPolicyRequirementApplicationDisposition.COVERED:
            if not ids:
                _fail("COVERED requirement application requires at least one evidence id")
        elif ids:
            _fail("NOT_COVERED and UNRESOLVED requirement applications require empty evidence_ids")

    def to_dict(self) -> dict:
        return domain_policy_requirement_application_entry_to_dict(self)

    @classmethod
    def from_dict(cls, payload: object) -> "DomainPolicyRequirementApplicationEntry":
        return domain_policy_requirement_application_entry_from_dict(payload)


def _strict_entry(value: object, field_name: str = "requirement application entry") -> DomainPolicyRequirementApplicationEntry:
    if type(value) is not DomainPolicyRequirementApplicationEntry:
        _fail(f"{field_name} must use exact DomainPolicyRequirementApplicationEntry")
    if type(value.requirement_key) is not str or type(value.rationale) is not str:
        _fail(f"{field_name} text fields must use exact str")
    if type(value.disposition) is not DomainPolicyRequirementApplicationDisposition:
        _fail(f"{field_name}.disposition must use exact enum")
    _strict_evidence_ids(value.evidence_ids, f"{field_name}.evidence_ids")
    restored = DomainPolicyRequirementApplicationEntry(
        requirement_key=value.requirement_key,
        disposition=value.disposition,
        evidence_ids=tuple(EvidenceId(item.value) for item in value.evidence_ids),
        rationale=value.rationale,
    )
    if restored != value:
        _fail(f"{field_name} must equal strict semantic reconstruction")
    return value


def _canonical_entries(value: object, *, require_canonical: bool) -> tuple[DomainPolicyRequirementApplicationEntry, ...]:
    if type(value) is not tuple:
        _fail("requirement_applications must use exact tuple")
    for index, item in enumerate(value):
        _strict_entry(item, f"requirement_applications[{index}]")
    keys = tuple(item.requirement_key for item in value)
    if len(set(keys)) != len(keys):
        _fail("requirement_applications must contain exactly one entry per requirement_key")
    canonical = tuple(sorted(value, key=lambda item: item.requirement_key))
    if require_canonical and canonical != value:
        _fail("requirement_applications must use canonical requirement-key ordering")
    return canonical


@dataclass(frozen=True, slots=True)
class ClaimDomainPolicyRequirementMappingProposal:
    snapshot_sha256: str
    claim_id: CapabilityClaimId
    subject_ref: CapabilitySubjectRef
    concept_ref: CapabilityConceptRef
    claim_scope: ClaimScope
    as_of: datetime
    policy_ref: EvaluationPolicyRef
    specification_sha256: str
    policy_review_id: str
    policy_review_sha256: str
    policy_admitted_at: datetime
    disposition_coverage_sha256: str
    lineage_dependence_sha256: str
    requirement_applications: tuple[DomainPolicyRequirementApplicationEntry, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "snapshot_sha256", _validate_sha256(self.snapshot_sha256, "snapshot_sha256"))
        _strict_claim_id(self.claim_id)
        _strict_subject_ref(self.subject_ref)
        _strict_concept_ref(self.concept_ref)
        _strict_claim_scope(self.claim_scope)
        object.__setattr__(self, "as_of", _canonical_boundary(self.as_of, "proposal as_of"))
        _strict_policy_ref(self.policy_ref)
        object.__setattr__(self, "specification_sha256", _validate_sha256(self.specification_sha256, "specification_sha256"))
        object.__setattr__(self, "policy_review_id", _opaque_id(self.policy_review_id, "policy_review_id"))
        object.__setattr__(self, "policy_review_sha256", _validate_sha256(self.policy_review_sha256, "policy_review_sha256"))
        object.__setattr__(self, "policy_admitted_at", _canonical_boundary(self.policy_admitted_at, "policy_admitted_at"))
        object.__setattr__(self, "disposition_coverage_sha256", _validate_sha256(self.disposition_coverage_sha256, "disposition_coverage_sha256"))
        object.__setattr__(self, "lineage_dependence_sha256", _validate_sha256(self.lineage_dependence_sha256, "lineage_dependence_sha256"))
        object.__setattr__(self, "requirement_applications", _canonical_entries(self.requirement_applications, require_canonical=False))

    def to_dict(self) -> dict:
        return claim_domain_policy_requirement_mapping_proposal_to_dict(self)

    @classmethod
    def from_dict(cls, payload: object) -> "ClaimDomainPolicyRequirementMappingProposal":
        return claim_domain_policy_requirement_mapping_proposal_from_dict(payload)

    def to_json(self) -> str:
        return claim_domain_policy_requirement_mapping_proposal_to_json(self)

    @classmethod
    def from_json(cls, payload: object) -> "ClaimDomainPolicyRequirementMappingProposal":
        return claim_domain_policy_requirement_mapping_proposal_from_json(payload)


def _strict_proposal(value: object) -> ClaimDomainPolicyRequirementMappingProposal:
    if type(value) is not ClaimDomainPolicyRequirementMappingProposal:
        _fail("mapping proposal must use exact ClaimDomainPolicyRequirementMappingProposal")
    _validate_sha256(value.snapshot_sha256, "snapshot_sha256")
    _strict_claim_id(value.claim_id)
    _strict_subject_ref(value.subject_ref)
    _strict_concept_ref(value.concept_ref)
    _strict_claim_scope(value.claim_scope)
    _strict_stored_utc_time(value.as_of, "proposal as_of")
    _strict_policy_ref(value.policy_ref)
    _validate_sha256(value.specification_sha256, "specification_sha256")
    if type(value.policy_review_id) is not str:
        _fail("policy_review_id must use exact str storage")
    _opaque_id(value.policy_review_id, "policy_review_id")
    _validate_sha256(value.policy_review_sha256, "policy_review_sha256")
    _strict_stored_utc_time(value.policy_admitted_at, "policy_admitted_at")
    _validate_sha256(value.disposition_coverage_sha256, "disposition_coverage_sha256")
    _validate_sha256(value.lineage_dependence_sha256, "lineage_dependence_sha256")
    _canonical_entries(value.requirement_applications, require_canonical=True)
    restored = ClaimDomainPolicyRequirementMappingProposal(
        snapshot_sha256=value.snapshot_sha256,
        claim_id=CapabilityClaimId(value.claim_id.value),
        subject_ref=CapabilitySubjectRef(value.subject_ref.value),
        concept_ref=CapabilityConceptRef(
            CapabilityId(value.concept_ref.capability_id.namespace, value.concept_ref.capability_id.key),
            value.concept_ref.revision,
        ),
        claim_scope=ClaimScope(value.claim_scope.description, value.claim_scope.tags),
        as_of=value.as_of,
        policy_ref=EvaluationPolicyRef(value.policy_ref.namespace, value.policy_ref.key, value.policy_ref.revision),
        specification_sha256=value.specification_sha256,
        policy_review_id=value.policy_review_id,
        policy_review_sha256=value.policy_review_sha256,
        policy_admitted_at=value.policy_admitted_at,
        disposition_coverage_sha256=value.disposition_coverage_sha256,
        lineage_dependence_sha256=value.lineage_dependence_sha256,
        requirement_applications=tuple(
            DomainPolicyRequirementApplicationEntry(
                item.requirement_key,
                item.disposition,
                tuple(EvidenceId(evidence_id.value) for evidence_id in item.evidence_ids),
                item.rationale,
            )
            for item in value.requirement_applications
        ),
    )
    if restored != value:
        _fail("mapping proposal must equal strict semantic reconstruction")
    return value


def _proposal_payload(value: ClaimDomainPolicyRequirementMappingProposal) -> dict:
    return claim_domain_policy_requirement_mapping_proposal_to_dict(_strict_proposal(value))


def claim_domain_policy_requirement_mapping_proposal_sha256_v1(
    proposal: ClaimDomainPolicyRequirementMappingProposal,
) -> str:
    return _hash(_PROPOSAL_HASH_DOMAIN, _proposal_payload(proposal))


@dataclass(frozen=True, order=True, slots=True)
class ClaimPolicyRequirementMappingReviewId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _opaque_id(self.value, "mapping review id"))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, order=True, slots=True)
class ClaimPolicyRequirementMappingReviewerRef:
    kind: ClaimPolicyRequirementMappingReviewerKind
    ref: str

    def __post_init__(self) -> None:
        if type(self.kind) is not ClaimPolicyRequirementMappingReviewerKind:
            _fail("mapping reviewer kind must use exact ClaimPolicyRequirementMappingReviewerKind")
        if self.kind is not ClaimPolicyRequirementMappingReviewerKind.HUMAN:
            _fail("PR12.11 v1 requires an explicitly declared HUMAN mapping reviewer")
        object.__setattr__(self, "ref", _opaque_id(self.ref, "mapping reviewer ref"))


@dataclass(frozen=True, slots=True)
class ClaimPolicyRequirementMappingReview:
    review_id: ClaimPolicyRequirementMappingReviewId
    claim_id: CapabilityClaimId
    policy_ref: EvaluationPolicyRef
    mapping_proposal_sha256: str
    reviewer_ref: ClaimPolicyRequirementMappingReviewerRef
    verdict: ClaimPolicyRequirementMappingReviewVerdict
    reviewed_at: datetime
    rationale: str

    def __post_init__(self) -> None:
        if type(self.review_id) is not ClaimPolicyRequirementMappingReviewId:
            _fail("review_id must use exact ClaimPolicyRequirementMappingReviewId")
        _strict_claim_id(self.claim_id)
        _strict_policy_ref(self.policy_ref)
        object.__setattr__(self, "mapping_proposal_sha256", _validate_sha256(self.mapping_proposal_sha256, "mapping_proposal_sha256"))
        if type(self.reviewer_ref) is not ClaimPolicyRequirementMappingReviewerRef:
            _fail("reviewer_ref must use exact ClaimPolicyRequirementMappingReviewerRef")
        if type(self.verdict) is not ClaimPolicyRequirementMappingReviewVerdict:
            _fail("verdict must use exact ClaimPolicyRequirementMappingReviewVerdict")
        object.__setattr__(self, "reviewed_at", _canonical_boundary(self.reviewed_at, "mapping reviewed_at"))
        object.__setattr__(self, "rationale", _text(self.rationale, "mapping review rationale"))

    def to_dict(self) -> dict:
        return claim_policy_requirement_mapping_review_to_dict(self)

    @classmethod
    def from_dict(cls, payload: object) -> "ClaimPolicyRequirementMappingReview":
        return claim_policy_requirement_mapping_review_from_dict(payload)

    def to_json(self) -> str:
        return claim_policy_requirement_mapping_review_to_json(self)

    @classmethod
    def from_json(cls, payload: object) -> "ClaimPolicyRequirementMappingReview":
        return claim_policy_requirement_mapping_review_from_json(payload)


def _strict_review_id(value: object) -> ClaimPolicyRequirementMappingReviewId:
    if type(value) is not ClaimPolicyRequirementMappingReviewId or type(value.value) is not str:
        _fail("mapping review_id must use exact ClaimPolicyRequirementMappingReviewId")
    restored = ClaimPolicyRequirementMappingReviewId(value.value)
    if restored != value:
        _fail("mapping review_id must equal strict semantic reconstruction")
    return value


def _strict_reviewer_ref(value: object) -> ClaimPolicyRequirementMappingReviewerRef:
    if type(value) is not ClaimPolicyRequirementMappingReviewerRef:
        _fail("mapping reviewer_ref must use exact ClaimPolicyRequirementMappingReviewerRef")
    if type(value.kind) is not ClaimPolicyRequirementMappingReviewerKind or type(value.ref) is not str:
        _fail("mapping reviewer_ref contains non-exact fields")
    restored = ClaimPolicyRequirementMappingReviewerRef(value.kind, value.ref)
    if restored != value:
        _fail("mapping reviewer_ref must equal strict semantic reconstruction")
    return value


def _strict_review(value: object) -> ClaimPolicyRequirementMappingReview:
    if type(value) is not ClaimPolicyRequirementMappingReview:
        _fail("mapping review must use exact ClaimPolicyRequirementMappingReview")
    _strict_review_id(value.review_id)
    _strict_claim_id(value.claim_id)
    _strict_policy_ref(value.policy_ref)
    _validate_sha256(value.mapping_proposal_sha256, "mapping_proposal_sha256")
    _strict_reviewer_ref(value.reviewer_ref)
    if type(value.verdict) is not ClaimPolicyRequirementMappingReviewVerdict:
        _fail("mapping review verdict must use exact enum")
    _strict_stored_utc_time(value.reviewed_at, "mapping reviewed_at")
    if type(value.rationale) is not str:
        _fail("mapping review rationale must use exact str storage")
    restored = ClaimPolicyRequirementMappingReview(
        review_id=ClaimPolicyRequirementMappingReviewId(value.review_id.value),
        claim_id=CapabilityClaimId(value.claim_id.value),
        policy_ref=EvaluationPolicyRef(value.policy_ref.namespace, value.policy_ref.key, value.policy_ref.revision),
        mapping_proposal_sha256=value.mapping_proposal_sha256,
        reviewer_ref=ClaimPolicyRequirementMappingReviewerRef(value.reviewer_ref.kind, value.reviewer_ref.ref),
        verdict=value.verdict,
        reviewed_at=value.reviewed_at,
        rationale=value.rationale,
    )
    if restored != value:
        _fail("mapping review must equal strict semantic reconstruction")
    return value


def _review_payload(value: ClaimPolicyRequirementMappingReview) -> dict:
    return claim_policy_requirement_mapping_review_to_dict(_strict_review(value))


def claim_policy_requirement_mapping_review_sha256_v1(
    review: ClaimPolicyRequirementMappingReview,
) -> str:
    return _hash(_REVIEW_HASH_DOMAIN, _review_payload(review))


@dataclass(frozen=True, slots=True)
class ClaimPolicyRequirementMappingReviewLedger:
    reviews: tuple[ClaimPolicyRequirementMappingReview, ...] = ()

    def __post_init__(self) -> None:
        if type(self.reviews) is not tuple:
            _fail("mapping review ledger reviews must use exact tuple")
        restored = tuple(_strict_review(review) for review in self.reviews)
        seen_ids: set[ClaimPolicyRequirementMappingReviewId] = set()
        seen_proposals: set[tuple[CapabilityClaimId, EvaluationPolicyRef, str]] = set()
        for review in restored:
            if review.review_id in seen_ids:
                _fail(f"duplicate mapping review_id in ledger: {review.review_id}")
            identity = (review.claim_id, review.policy_ref, review.mapping_proposal_sha256)
            if identity in seen_proposals:
                _fail("exact mapping proposal already has a terminal review in ledger")
            seen_ids.add(review.review_id)
            seen_proposals.add(identity)
        object.__setattr__(self, "reviews", restored)

    def to_dict(self) -> dict:
        return claim_policy_requirement_mapping_review_ledger_to_dict(self)

    @classmethod
    def from_dict(cls, payload: object) -> "ClaimPolicyRequirementMappingReviewLedger":
        return claim_policy_requirement_mapping_review_ledger_from_dict(payload)

    def to_json(self) -> str:
        return claim_policy_requirement_mapping_review_ledger_to_json(self)

    @classmethod
    def from_json(cls, payload: object) -> "ClaimPolicyRequirementMappingReviewLedger":
        return claim_policy_requirement_mapping_review_ledger_from_json(payload)


def _strict_review_ledger(value: object) -> ClaimPolicyRequirementMappingReviewLedger:
    if type(value) is not ClaimPolicyRequirementMappingReviewLedger:
        _fail("mapping review_ledger must use exact ClaimPolicyRequirementMappingReviewLedger")
    if type(value.reviews) is not tuple:
        _fail("mapping review_ledger reviews must use exact tuple")
    return ClaimPolicyRequirementMappingReviewLedger(
        reviews=tuple(_strict_review(review) for review in value.reviews)
    )


def _review_ledger_payload(value: ClaimPolicyRequirementMappingReviewLedger) -> dict:
    checked = _strict_review_ledger(value)
    return {"schema_version": _SCHEMA_VERSION, "reviews": [review.to_dict() for review in checked.reviews]}


def claim_policy_requirement_mapping_review_ledger_sha256_v1(
    review_ledger: ClaimPolicyRequirementMappingReviewLedger,
) -> str:
    return _hash(_REVIEW_LEDGER_HASH_DOMAIN, _review_ledger_payload(review_ledger))


def validate_claim_policy_requirement_mapping_review_ledger_successor_v1(
    previous: ClaimPolicyRequirementMappingReviewLedger,
    current: ClaimPolicyRequirementMappingReviewLedger,
) -> None:
    previous = _strict_review_ledger(previous)
    current = _strict_review_ledger(current)
    if len(current.reviews) < len(previous.reviews):
        _fail("mapping review ledger successor may not remove prior terminal reviews")
    if current.reviews[: len(previous.reviews)] != previous.reviews:
        _fail("mapping review ledger successor must preserve exact prior review prefix")


class ClaimPolicyRequirementMappingReviewAdmission:
    """Runtime-only authority for one exact HUMAN mapping-review transition."""

    __slots__ = (
        "claim_id",
        "policy_ref",
        "mapping_proposal_sha256",
        "review_id",
        "review_sha256",
        "predecessor_review_ledger_sha256",
        "successor_review_ledger_sha256",
        "review_ledger_sha256",
    )

    def __init__(self, *args: object, **kwargs: object) -> None:
        _fail("mapping review admission authority can only be issued by admit_claim_policy_requirement_mapping_review_v1")

    def __setattr__(self, name: str, value: object) -> None:
        _fail("mapping review admission authority is immutable")

    def __reduce__(self):
        _fail("mapping review admission authority is runtime-only and not serializable")


def _review_admission_payload(value: ClaimPolicyRequirementMappingReviewAdmission) -> tuple[object, ...]:
    if type(value) is not ClaimPolicyRequirementMappingReviewAdmission:
        _fail("mapping review admission must use exact ClaimPolicyRequirementMappingReviewAdmission")
    return (
        str(_strict_claim_id(value.claim_id)),
        str(_strict_policy_ref(value.policy_ref)),
        _validate_sha256(value.mapping_proposal_sha256, "mapping review admission proposal digest"),
        str(_strict_review_id(value.review_id)),
        _validate_sha256(value.review_sha256, "mapping review admission review digest"),
        _validate_sha256(value.predecessor_review_ledger_sha256, "mapping review admission predecessor digest"),
        _validate_sha256(value.successor_review_ledger_sha256, "mapping review admission successor digest"),
        _validate_sha256(value.review_ledger_sha256, "mapping review admission ledger digest"),
    )


def _strict_review_admission(value: object) -> ClaimPolicyRequirementMappingReviewAdmission:
    if type(value) is not ClaimPolicyRequirementMappingReviewAdmission:
        _fail("mapping review admission must use exact ClaimPolicyRequirementMappingReviewAdmission")
    payload = _review_admission_payload(value)
    try:
        _process_authority.require_mapping_review_process_authority_v1(value, payload)
    except ValueError as exc:
        raise InvalidDomainPolicyRequirementApplication(str(exc)) from exc
    return value


def _issue_review_admission(
    *,
    review: ClaimPolicyRequirementMappingReview,
    predecessor: ClaimPolicyRequirementMappingReviewLedger,
    transition_successor: ClaimPolicyRequirementMappingReviewLedger,
    current: ClaimPolicyRequirementMappingReviewLedger,
) -> ClaimPolicyRequirementMappingReviewAdmission:
    review = _strict_review(review)
    predecessor = _strict_review_ledger(predecessor)
    transition_successor = _strict_review_ledger(transition_successor)
    current = _strict_review_ledger(current)
    validate_claim_policy_requirement_mapping_review_ledger_successor_v1(predecessor, transition_successor)
    if len(transition_successor.reviews) != len(predecessor.reviews) + 1:
        _fail("mapping review authority must bind an exact one-review append transition")
    if transition_successor.reviews[-1] != review:
        _fail("mapping review authority transition must append the exact review")
    if current.reviews[: len(transition_successor.reviews)] != transition_successor.reviews:
        _fail("current mapping review ledger must preserve admitted transition prefix")
    admission = object.__new__(ClaimPolicyRequirementMappingReviewAdmission)
    object.__setattr__(admission, "claim_id", review.claim_id)
    object.__setattr__(admission, "policy_ref", review.policy_ref)
    object.__setattr__(admission, "mapping_proposal_sha256", review.mapping_proposal_sha256)
    object.__setattr__(admission, "review_id", review.review_id)
    object.__setattr__(admission, "review_sha256", claim_policy_requirement_mapping_review_sha256_v1(review))
    object.__setattr__(admission, "predecessor_review_ledger_sha256", claim_policy_requirement_mapping_review_ledger_sha256_v1(predecessor))
    object.__setattr__(admission, "successor_review_ledger_sha256", claim_policy_requirement_mapping_review_ledger_sha256_v1(transition_successor))
    object.__setattr__(admission, "review_ledger_sha256", claim_policy_requirement_mapping_review_ledger_sha256_v1(current))
    payload = _review_admission_payload(admission)
    _process_authority.issue_mapping_review_process_authority_v1(admission, payload)
    return admission


def _resolve_exact_claim(*, records: EpistemicRecordSet, claim_id: CapabilityClaimId) -> CapabilityClaim:
    if type(records) is not EpistemicRecordSet:
        _fail("records must use exact EpistemicRecordSet")
    target = _strict_claim_id(claim_id)
    matches = tuple(claim for claim in records.claims if claim.claim_id == target)
    if len(matches) != 1 or type(matches[0]) is not CapabilityClaim:
        _fail("claim_id is absent or ambiguous in supplied EpistemicRecordSet")
    return matches[0]


def _validate_upstream(
    *,
    records: EpistemicRecordSet,
    claim_id: CapabilityClaimId,
    as_of: datetime,
    coverage: ClaimEvidenceDispositionCoverageReceipt,
    lineage: ClaimEvidenceLineageDependenceReceipt,
) -> tuple[ClaimEvidenceDispositionCoverageReceipt, ClaimEvidenceLineageDependenceReceipt]:
    try:
        checked_coverage = validate_complete_claim_evidence_disposition_coverage_v1(
            records=records,
            claim_id=claim_id,
            as_of=as_of,
            coverage=coverage,
        )
    except ClaimEvidenceDispositionCoverageError as exc:
        raise InvalidDomainPolicyRequirementApplication(
            f"PR12.9 disposition coverage validation failed: {exc}"
        ) from exc
    try:
        checked_lineage = validate_claim_evidence_lineage_dependence_v1(
            records=records,
            claim_id=claim_id,
            as_of=as_of,
            coverage=checked_coverage,
            lineage=lineage,
        )
    except ClaimEvidenceLineageDependenceError as exc:
        raise InvalidDomainPolicyRequirementApplication(
            f"PR12.10 lineage dependence validation failed: {exc}"
        ) from exc
    return checked_coverage, checked_lineage


def _resolve_exact_admitted_policy_basis(
    *,
    registry: object,
    policy_ref: EvaluationPolicyRef,
    specification_sha256: str,
) -> tuple[DomainEvaluationPolicySpecification, object]:
    checked_ref = _strict_policy_ref(policy_ref)
    checked_digest = _validate_sha256(specification_sha256, "specification_sha256")
    try:
        specification = resolve_admitted_domain_evaluation_policy_v1(
            registry=registry,
            policy_ref=checked_ref,
            specification_sha256=checked_digest,
        )
    except (TypeError, ValueError) as exc:
        raise InvalidDomainPolicyRequirementApplication(
            f"PR12.7 admitted policy resolution failed: {exc}"
        ) from exc
    entries = getattr(registry, "entries", None)
    if type(entries) is not tuple:
        _fail("authorized policy registry must expose canonical tuple entries")
    matches = tuple(
        entry
        for entry in entries
        if getattr(entry, "policy_ref", None) == checked_ref
        and getattr(entry, "specification_sha256", None) == checked_digest
    )
    if len(matches) != 1:
        _fail("authorized policy registry lacks one exact selected policy entry")
    entry = matches[0]
    if str(getattr(entry, "review_id", "")) == "":
        _fail("selected policy entry lacks review audit binding")
    _validate_sha256(getattr(entry, "review_sha256", None), "policy review_sha256")
    admitted_at = getattr(entry, "admitted_at", None)
    _strict_stored_utc_time(admitted_at, "policy admitted_at")
    return specification, entry


def _validate_policy_applicability(*, specification: DomainEvaluationPolicySpecification, claim: CapabilityClaim) -> None:
    try:
        applies = domain_evaluation_policy_specification_applies_to_v1(
            specification,
            concept_ref=claim.concept_ref,
            claim_scope=claim.scope,
        )
    except (TypeError, ValueError) as exc:
        raise InvalidDomainPolicyRequirementApplication(
            f"PR12.6 policy applicability validation failed: {exc}"
        ) from exc
    if not applies:
        _fail("exact admitted policy specification does not apply to claim concept_ref and scope")


def _validate_mapping_entries(
    *,
    specification: DomainEvaluationPolicySpecification,
    coverage: ClaimEvidenceDispositionCoverageReceipt,
    entries: tuple[DomainPolicyRequirementApplicationEntry, ...],
) -> tuple[DomainPolicyRequirementApplicationEntry, ...]:
    checked = _canonical_entries(entries, require_canonical=False)
    expected_keys = tuple(requirement.requirement_key for requirement in specification.requirements)
    actual_keys = tuple(entry.requirement_key for entry in checked)
    missing = tuple(sorted(set(expected_keys) - set(actual_keys)))
    if missing:
        _fail(f"mapping proposal omits admitted policy requirement: {missing[0]}")
    extra = tuple(sorted(set(actual_keys) - set(expected_keys)))
    if extra:
        _fail(f"mapping proposal includes unknown policy requirement: {extra[0]}")
    dispositions = {item.evidence_id: item for item in coverage.dispositions}
    for entry in checked:
        if entry.disposition is not DomainPolicyRequirementApplicationDisposition.COVERED:
            continue
        for evidence_id in entry.evidence_ids:
            assessment = dispositions.get(evidence_id)
            if assessment is None:
                _fail(f"mapping proposal cites evidence outside exact PR12.9 universe: {evidence_id}")
            if assessment.bearing is EvidenceBearing.NOT_RELEVANT:
                _fail(f"NOT_RELEVANT evidence cannot satisfy a policy requirement: {evidence_id}")
    return checked


def build_claim_domain_policy_requirement_mapping_proposal_v1(
    *,
    records: EpistemicRecordSet,
    claim_id: CapabilityClaimId,
    as_of: datetime,
    coverage: ClaimEvidenceDispositionCoverageReceipt,
    lineage: ClaimEvidenceLineageDependenceReceipt,
    registry: object,
    policy_ref: EvaluationPolicyRef,
    specification_sha256: str,
    requirement_applications: tuple[DomainPolicyRequirementApplicationEntry, ...],
) -> ClaimDomainPolicyRequirementMappingProposal:
    """Build ordinary proposal data; this function grants no mapping authority."""

    boundary = _canonical_boundary(as_of, "proposal as_of")
    checked_coverage, checked_lineage = _validate_upstream(
        records=records,
        claim_id=claim_id,
        as_of=boundary,
        coverage=coverage,
        lineage=lineage,
    )
    claim = _resolve_exact_claim(records=records, claim_id=claim_id)
    specification, policy_entry = _resolve_exact_admitted_policy_basis(
        registry=registry,
        policy_ref=policy_ref,
        specification_sha256=specification_sha256,
    )
    _validate_policy_applicability(specification=specification, claim=claim)
    entries = _validate_mapping_entries(
        specification=specification,
        coverage=checked_coverage,
        entries=requirement_applications,
    )
    return ClaimDomainPolicyRequirementMappingProposal(
        snapshot_sha256=checked_coverage.snapshot_sha256,
        claim_id=claim.claim_id,
        subject_ref=claim.subject_ref,
        concept_ref=claim.concept_ref,
        claim_scope=claim.scope,
        as_of=checked_coverage.as_of,
        policy_ref=specification.policy_ref,
        specification_sha256=domain_evaluation_policy_specification_sha256_v1(specification),
        policy_review_id=str(policy_entry.review_id),
        policy_review_sha256=policy_entry.review_sha256,
        policy_admitted_at=policy_entry.admitted_at,
        disposition_coverage_sha256=_coverage_sha256(checked_coverage),
        lineage_dependence_sha256=_lineage_sha256(checked_lineage),
        requirement_applications=entries,
    )


def validate_claim_domain_policy_requirement_mapping_proposal_v1(
    *,
    records: EpistemicRecordSet,
    claim_id: CapabilityClaimId,
    as_of: datetime,
    coverage: ClaimEvidenceDispositionCoverageReceipt,
    lineage: ClaimEvidenceLineageDependenceReceipt,
    registry: object,
    proposal: ClaimDomainPolicyRequirementMappingProposal,
) -> ClaimDomainPolicyRequirementMappingProposal:
    supplied = _strict_proposal(proposal)
    expected = build_claim_domain_policy_requirement_mapping_proposal_v1(
        records=records,
        claim_id=claim_id,
        as_of=as_of,
        coverage=coverage,
        lineage=lineage,
        registry=registry,
        policy_ref=supplied.policy_ref,
        specification_sha256=supplied.specification_sha256,
        requirement_applications=supplied.requirement_applications,
    )
    if supplied != expected:
        _fail("mapping proposal does not match exact policy, claim, upstream basis, and supplied entries")
    return supplied


def validate_claim_policy_requirement_mapping_review_v1(
    *,
    proposal: ClaimDomainPolicyRequirementMappingProposal,
    review: ClaimPolicyRequirementMappingReview,
) -> None:
    proposal = _strict_proposal(proposal)
    review = _strict_review(review)
    if review.claim_id != proposal.claim_id:
        _fail("mapping review claim_id does not match exact proposal")
    if review.policy_ref != proposal.policy_ref:
        _fail("mapping review policy_ref does not match exact proposal")
    if review.mapping_proposal_sha256 != claim_domain_policy_requirement_mapping_proposal_sha256_v1(proposal):
        _fail("mapping review proposal digest does not match exact proposal")
    if review.reviewed_at < proposal.as_of:
        _fail("mapping review reviewed_at must not precede proposal as_of")
    if review.reviewed_at < proposal.policy_admitted_at:
        _fail("mapping review reviewed_at must not precede policy admitted_at")


def review_claim_domain_policy_requirement_mapping_proposal_v1(
    *,
    proposal: ClaimDomainPolicyRequirementMappingProposal,
    review_id: ClaimPolicyRequirementMappingReviewId,
    reviewer_ref: ClaimPolicyRequirementMappingReviewerRef,
    verdict: ClaimPolicyRequirementMappingReviewVerdict,
    reviewed_at: datetime,
    rationale: str,
) -> ClaimPolicyRequirementMappingReview:
    proposal = _strict_proposal(proposal)
    review = ClaimPolicyRequirementMappingReview(
        review_id=review_id,
        claim_id=proposal.claim_id,
        policy_ref=proposal.policy_ref,
        mapping_proposal_sha256=claim_domain_policy_requirement_mapping_proposal_sha256_v1(proposal),
        reviewer_ref=reviewer_ref,
        verdict=verdict,
        reviewed_at=reviewed_at,
        rationale=rationale,
    )
    validate_claim_policy_requirement_mapping_review_v1(proposal=proposal, review=review)
    return review


def admit_claim_policy_requirement_mapping_review_v1(
    *,
    review_ledger: ClaimPolicyRequirementMappingReviewLedger,
    proposal: ClaimDomainPolicyRequirementMappingProposal,
    review: ClaimPolicyRequirementMappingReview,
) -> tuple[ClaimPolicyRequirementMappingReviewLedger, ClaimPolicyRequirementMappingReviewAdmission]:
    """Admit one exact terminal HUMAN review and issue fresh process-local authority."""

    ledger = _strict_review_ledger(review_ledger)
    proposal = _strict_proposal(proposal)
    review = _strict_review(review)
    validate_claim_policy_requirement_mapping_review_v1(proposal=proposal, review=review)
    identity = (review.claim_id, review.policy_ref, review.mapping_proposal_sha256)
    for index, existing in enumerate(ledger.reviews):
        existing_identity = (existing.claim_id, existing.policy_ref, existing.mapping_proposal_sha256)
        if existing_identity == identity:
            if _review_payload(existing) != _review_payload(review):
                _fail("exact mapping proposal already has a different terminal review")
            predecessor = ClaimPolicyRequirementMappingReviewLedger(reviews=ledger.reviews[:index])
            transition_successor = ClaimPolicyRequirementMappingReviewLedger(reviews=ledger.reviews[: index + 1])
            return ledger, _issue_review_admission(
                review=review,
                predecessor=predecessor,
                transition_successor=transition_successor,
                current=ledger,
            )
        if existing.review_id == review.review_id:
            _fail("mapping review_id is already bound to a different proposal")
    successor = ClaimPolicyRequirementMappingReviewLedger(reviews=ledger.reviews + (review,))
    validate_claim_policy_requirement_mapping_review_ledger_successor_v1(ledger, successor)
    return successor, _issue_review_admission(
        review=review,
        predecessor=ledger,
        transition_successor=successor,
        current=successor,
    )


def validate_claim_policy_requirement_mapping_review_admission_v1(
    *,
    review_ledger: ClaimPolicyRequirementMappingReviewLedger,
    proposal: ClaimDomainPolicyRequirementMappingProposal,
    review_admission: ClaimPolicyRequirementMappingReviewAdmission,
) -> ClaimPolicyRequirementMappingReview:
    ledger = _strict_review_ledger(review_ledger)
    proposal = _strict_proposal(proposal)
    admission = _strict_review_admission(review_admission)
    proposal_digest = claim_domain_policy_requirement_mapping_proposal_sha256_v1(proposal)
    if admission.claim_id != proposal.claim_id or admission.policy_ref != proposal.policy_ref:
        _fail("mapping review admission claim/policy binding does not match exact proposal")
    if admission.mapping_proposal_sha256 != proposal_digest:
        _fail("mapping review admission proposal digest does not match exact proposal")
    if admission.review_ledger_sha256 != claim_policy_requirement_mapping_review_ledger_sha256_v1(ledger):
        _fail("mapping review admission authority is stale for supplied review ledger")
    matches = tuple(
        (index, review)
        for index, review in enumerate(ledger.reviews)
        if review.claim_id == proposal.claim_id
        and review.policy_ref == proposal.policy_ref
        and review.mapping_proposal_sha256 == proposal_digest
    )
    if len(matches) != 1:
        _fail("mapping review admission exact proposal has no unique terminal review")
    index, review = matches[0]
    validate_claim_policy_requirement_mapping_review_v1(proposal=proposal, review=review)
    if admission.review_id != review.review_id:
        _fail("mapping review admission review_id does not match terminal review")
    review_digest = claim_policy_requirement_mapping_review_sha256_v1(review)
    if admission.review_sha256 != review_digest:
        _fail("mapping review admission review digest does not match terminal review")
    predecessor = ClaimPolicyRequirementMappingReviewLedger(reviews=ledger.reviews[:index])
    transition_successor = ClaimPolicyRequirementMappingReviewLedger(reviews=ledger.reviews[: index + 1])
    if admission.predecessor_review_ledger_sha256 != claim_policy_requirement_mapping_review_ledger_sha256_v1(predecessor):
        _fail("mapping review admission predecessor digest mismatch")
    if admission.successor_review_ledger_sha256 != claim_policy_requirement_mapping_review_ledger_sha256_v1(transition_successor):
        _fail("mapping review admission transition successor digest mismatch")
    return review


def require_approved_claim_policy_requirement_mapping_review_v1(
    *,
    review_ledger: ClaimPolicyRequirementMappingReviewLedger,
    proposal: ClaimDomainPolicyRequirementMappingProposal,
    review_admission: ClaimPolicyRequirementMappingReviewAdmission,
) -> ClaimPolicyRequirementMappingReview:
    review = validate_claim_policy_requirement_mapping_review_admission_v1(
        review_ledger=review_ledger,
        proposal=proposal,
        review_admission=review_admission,
    )
    if review.verdict is not ClaimPolicyRequirementMappingReviewVerdict.APPROVE:
        _fail("mapping proposal terminal review is REJECT, not APPROVE")
    return review


@dataclass(frozen=True, slots=True)
class ClaimDomainPolicyRequirementApplicationReceipt:
    snapshot_sha256: str
    claim_id: CapabilityClaimId
    subject_ref: CapabilitySubjectRef
    concept_ref: CapabilityConceptRef
    claim_scope: ClaimScope
    as_of: datetime
    policy_ref: EvaluationPolicyRef
    specification_sha256: str
    policy_review_id: str
    policy_review_sha256: str
    policy_admitted_at: datetime
    disposition_coverage_sha256: str
    lineage_dependence_sha256: str
    mapping_proposal_sha256: str
    mapping_review_id: ClaimPolicyRequirementMappingReviewId
    mapping_review_sha256: str
    requirement_applications: tuple[DomainPolicyRequirementApplicationEntry, ...]
    required_requirement_coverage_complete: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "snapshot_sha256", _validate_sha256(self.snapshot_sha256, "snapshot_sha256"))
        _strict_claim_id(self.claim_id)
        _strict_subject_ref(self.subject_ref)
        _strict_concept_ref(self.concept_ref)
        _strict_claim_scope(self.claim_scope)
        object.__setattr__(self, "as_of", _canonical_boundary(self.as_of, "application as_of"))
        _strict_policy_ref(self.policy_ref)
        object.__setattr__(self, "specification_sha256", _validate_sha256(self.specification_sha256, "specification_sha256"))
        object.__setattr__(self, "policy_review_id", _opaque_id(self.policy_review_id, "policy_review_id"))
        object.__setattr__(self, "policy_review_sha256", _validate_sha256(self.policy_review_sha256, "policy_review_sha256"))
        object.__setattr__(self, "policy_admitted_at", _canonical_boundary(self.policy_admitted_at, "policy_admitted_at"))
        object.__setattr__(self, "disposition_coverage_sha256", _validate_sha256(self.disposition_coverage_sha256, "disposition_coverage_sha256"))
        object.__setattr__(self, "lineage_dependence_sha256", _validate_sha256(self.lineage_dependence_sha256, "lineage_dependence_sha256"))
        object.__setattr__(self, "mapping_proposal_sha256", _validate_sha256(self.mapping_proposal_sha256, "mapping_proposal_sha256"))
        _strict_review_id(self.mapping_review_id)
        object.__setattr__(self, "mapping_review_sha256", _validate_sha256(self.mapping_review_sha256, "mapping_review_sha256"))
        object.__setattr__(self, "requirement_applications", _canonical_entries(self.requirement_applications, require_canonical=False))
        if type(self.required_requirement_coverage_complete) is not bool:
            _fail("required_requirement_coverage_complete must use exact bool")

    def to_dict(self) -> dict:
        return claim_domain_policy_requirement_application_receipt_to_dict(self)

    @classmethod
    def from_dict(cls, payload: object) -> "ClaimDomainPolicyRequirementApplicationReceipt":
        return claim_domain_policy_requirement_application_receipt_from_dict(payload)

    def to_json(self) -> str:
        return claim_domain_policy_requirement_application_receipt_to_json(self)

    @classmethod
    def from_json(cls, payload: object) -> "ClaimDomainPolicyRequirementApplicationReceipt":
        return claim_domain_policy_requirement_application_receipt_from_json(payload)


def _strict_application_receipt(value: object) -> ClaimDomainPolicyRequirementApplicationReceipt:
    if type(value) is not ClaimDomainPolicyRequirementApplicationReceipt:
        _fail("application receipt must use exact ClaimDomainPolicyRequirementApplicationReceipt")
    data = value.to_dict()
    restored = claim_domain_policy_requirement_application_receipt_from_dict(data)
    if restored != value:
        _fail("application receipt must equal strict semantic reconstruction")
    return value


def _required_coverage_complete(
    specification: DomainEvaluationPolicySpecification,
    entries: tuple[DomainPolicyRequirementApplicationEntry, ...],
) -> bool:
    by_key = {entry.requirement_key: entry for entry in entries}
    return all(
        by_key[requirement.requirement_key].disposition
        is DomainPolicyRequirementApplicationDisposition.COVERED
        for requirement in specification.requirements
        if requirement.required_for_sufficiency
    )


def apply_admitted_domain_policy_requirements_v1(
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
) -> ClaimDomainPolicyRequirementApplicationReceipt:
    """Apply exact HUMAN-approved mapping and compute only required coverage completeness."""

    proposal = validate_claim_domain_policy_requirement_mapping_proposal_v1(
        records=records,
        claim_id=claim_id,
        as_of=as_of,
        coverage=coverage,
        lineage=lineage,
        registry=registry,
        proposal=proposal,
    )
    review = require_approved_claim_policy_requirement_mapping_review_v1(
        review_ledger=review_ledger,
        proposal=proposal,
        review_admission=review_admission,
    )
    specification, _ = _resolve_exact_admitted_policy_basis(
        registry=registry,
        policy_ref=proposal.policy_ref,
        specification_sha256=proposal.specification_sha256,
    )
    return ClaimDomainPolicyRequirementApplicationReceipt(
        snapshot_sha256=proposal.snapshot_sha256,
        claim_id=proposal.claim_id,
        subject_ref=proposal.subject_ref,
        concept_ref=proposal.concept_ref,
        claim_scope=proposal.claim_scope,
        as_of=proposal.as_of,
        policy_ref=proposal.policy_ref,
        specification_sha256=proposal.specification_sha256,
        policy_review_id=proposal.policy_review_id,
        policy_review_sha256=proposal.policy_review_sha256,
        policy_admitted_at=proposal.policy_admitted_at,
        disposition_coverage_sha256=proposal.disposition_coverage_sha256,
        lineage_dependence_sha256=proposal.lineage_dependence_sha256,
        mapping_proposal_sha256=claim_domain_policy_requirement_mapping_proposal_sha256_v1(proposal),
        mapping_review_id=review.review_id,
        mapping_review_sha256=claim_policy_requirement_mapping_review_sha256_v1(review),
        requirement_applications=proposal.requirement_applications,
        required_requirement_coverage_complete=_required_coverage_complete(
            specification,
            proposal.requirement_applications,
        ),
    )


def validate_claim_domain_policy_requirement_application_v1(
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
) -> ClaimDomainPolicyRequirementApplicationReceipt:
    supplied = _strict_application_receipt(application)
    expected = apply_admitted_domain_policy_requirements_v1(
        records=records,
        claim_id=claim_id,
        as_of=as_of,
        coverage=coverage,
        lineage=lineage,
        registry=registry,
        proposal=proposal,
        review_ledger=review_ledger,
        review_admission=review_admission,
    )
    if supplied != expected:
        _fail("application receipt does not match complete governed PR12.11 replay")
    return supplied


# ---- strict serializers -------------------------------------------------

def domain_policy_requirement_application_entry_to_dict(entry: DomainPolicyRequirementApplicationEntry) -> dict:
    checked = _strict_entry(entry)
    return {
        "requirement_key": checked.requirement_key,
        "disposition": checked.disposition.value,
        "evidence_ids": [item.value for item in checked.evidence_ids],
        "rationale": checked.rationale,
    }


def domain_policy_requirement_application_entry_from_dict(payload: object) -> DomainPolicyRequirementApplicationEntry:
    data = _require_exact_object(
        payload,
        expected_keys={"requirement_key", "disposition", "evidence_ids", "rationale"},
        field_name="requirement application entry",
    )
    if type(data["requirement_key"]) is not str or type(data["disposition"]) is not str or type(data["rationale"]) is not str:
        _fail("requirement application entry textual fields must use exact strings")
    if type(data["evidence_ids"]) is not list or any(type(item) is not str for item in data["evidence_ids"]):
        _fail("requirement application entry evidence_ids must use exact array/list of strings")
    try:
        entry = DomainPolicyRequirementApplicationEntry(
            requirement_key=data["requirement_key"],
            disposition=DomainPolicyRequirementApplicationDisposition(data["disposition"]),
            evidence_ids=tuple(EvidenceId(item) for item in data["evidence_ids"]),
            rationale=data["rationale"],
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InvalidDomainPolicyRequirementApplication):
            raise
        raise InvalidDomainPolicyRequirementApplication(f"requirement application entry is invalid: {exc}") from exc
    if entry.to_dict() != data:
        _fail("requirement application entry payload must use canonical ordering/content")
    return entry


def _scope_to_dict(scope: ClaimScope) -> dict:
    scope = _strict_claim_scope(scope)
    return {"description": scope.description, "tags": list(scope.tags)}


def _scope_from_dict(payload: object) -> ClaimScope:
    data = _require_exact_object(payload, expected_keys={"description", "tags"}, field_name="claim_scope")
    if type(data["description"]) is not str or type(data["tags"]) is not list or any(type(item) is not str for item in data["tags"]):
        _fail("claim_scope must use exact description string and tags array/list")
    scope = ClaimScope(data["description"], tuple(data["tags"]))
    if _scope_to_dict(scope) != data:
        _fail("claim_scope payload must use canonical ordering/content")
    return scope


def claim_domain_policy_requirement_mapping_proposal_to_dict(proposal: ClaimDomainPolicyRequirementMappingProposal) -> dict:
    checked = _strict_proposal(proposal)
    return {
        "schema_version": _SCHEMA_VERSION,
        "snapshot_sha256": checked.snapshot_sha256,
        "claim_id": checked.claim_id.value,
        "subject_ref": checked.subject_ref.value,
        "concept_ref": str(checked.concept_ref),
        "claim_scope": _scope_to_dict(checked.claim_scope),
        "as_of": format_time(checked.as_of),
        "policy_ref": str(checked.policy_ref),
        "specification_sha256": checked.specification_sha256,
        "policy_review_id": checked.policy_review_id,
        "policy_review_sha256": checked.policy_review_sha256,
        "policy_admitted_at": format_time(checked.policy_admitted_at),
        "disposition_coverage_sha256": checked.disposition_coverage_sha256,
        "lineage_dependence_sha256": checked.lineage_dependence_sha256,
        "requirement_applications": [item.to_dict() for item in checked.requirement_applications],
    }


def claim_domain_policy_requirement_mapping_proposal_from_dict(payload: object) -> ClaimDomainPolicyRequirementMappingProposal:
    keys = {
        "schema_version", "snapshot_sha256", "claim_id", "subject_ref", "concept_ref", "claim_scope",
        "as_of", "policy_ref", "specification_sha256", "policy_review_id", "policy_review_sha256",
        "policy_admitted_at", "disposition_coverage_sha256", "lineage_dependence_sha256", "requirement_applications",
    }
    data = _require_exact_object(payload, expected_keys=keys, field_name="mapping proposal")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        _fail("mapping proposal schema_version must be exact integer 1")
    for key in keys - {"schema_version", "claim_scope", "requirement_applications"}:
        if type(data[key]) is not str:
            _fail(f"mapping proposal {key} must use exact string")
    if type(data["requirement_applications"]) is not list:
        _fail("mapping proposal requirement_applications must use exact array/list")
    try:
        proposal = ClaimDomainPolicyRequirementMappingProposal(
            snapshot_sha256=data["snapshot_sha256"],
            claim_id=CapabilityClaimId(data["claim_id"]),
            subject_ref=CapabilitySubjectRef(data["subject_ref"]),
            concept_ref=CapabilityConceptRef.parse(data["concept_ref"]),
            claim_scope=_scope_from_dict(data["claim_scope"]),
            as_of=parse_time(data["as_of"], "proposal as_of"),
            policy_ref=EvaluationPolicyRef.parse(data["policy_ref"]),
            specification_sha256=data["specification_sha256"],
            policy_review_id=data["policy_review_id"],
            policy_review_sha256=data["policy_review_sha256"],
            policy_admitted_at=parse_time(data["policy_admitted_at"], "policy admitted_at"),
            disposition_coverage_sha256=data["disposition_coverage_sha256"],
            lineage_dependence_sha256=data["lineage_dependence_sha256"],
            requirement_applications=tuple(domain_policy_requirement_application_entry_from_dict(item) for item in data["requirement_applications"]),
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InvalidDomainPolicyRequirementApplication):
            raise
        raise InvalidDomainPolicyRequirementApplication(f"mapping proposal is invalid: {exc}") from exc
    if proposal.to_dict() != data:
        _fail("mapping proposal payload must use canonical ordering/content")
    return proposal


def claim_domain_policy_requirement_mapping_proposal_to_json(proposal: ClaimDomainPolicyRequirementMappingProposal) -> str:
    return _canonical_json_text(proposal.to_dict())


def claim_domain_policy_requirement_mapping_proposal_from_json(payload: object) -> ClaimDomainPolicyRequirementMappingProposal:
    data = _parse_canonical_json(payload, "mapping proposal")
    proposal = claim_domain_policy_requirement_mapping_proposal_from_dict(data)
    if proposal.to_json() != payload:
        _fail("mapping proposal JSON must use exact canonical encoding")
    return proposal


def claim_policy_requirement_mapping_review_to_dict(review: ClaimPolicyRequirementMappingReview) -> dict:
    checked = _strict_review(review)
    return {
        "schema_version": _SCHEMA_VERSION,
        "review_id": checked.review_id.value,
        "claim_id": checked.claim_id.value,
        "policy_ref": str(checked.policy_ref),
        "mapping_proposal_sha256": checked.mapping_proposal_sha256,
        "reviewer_ref": {"kind": checked.reviewer_ref.kind.value, "ref": checked.reviewer_ref.ref},
        "verdict": checked.verdict.value,
        "reviewed_at": format_time(checked.reviewed_at),
        "rationale": checked.rationale,
    }


def claim_policy_requirement_mapping_review_from_dict(payload: object) -> ClaimPolicyRequirementMappingReview:
    data = _require_exact_object(
        payload,
        expected_keys={"schema_version", "review_id", "claim_id", "policy_ref", "mapping_proposal_sha256", "reviewer_ref", "verdict", "reviewed_at", "rationale"},
        field_name="mapping review",
    )
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        _fail("mapping review schema_version must be exact integer 1")
    for key in ("review_id", "claim_id", "policy_ref", "mapping_proposal_sha256", "verdict", "reviewed_at", "rationale"):
        if type(data[key]) is not str:
            _fail(f"mapping review {key} must use exact string")
    reviewer = _require_exact_object(data["reviewer_ref"], expected_keys={"kind", "ref"}, field_name="mapping reviewer_ref")
    if type(reviewer["kind"]) is not str or type(reviewer["ref"]) is not str:
        _fail("mapping reviewer_ref fields must use exact strings")
    try:
        review = ClaimPolicyRequirementMappingReview(
            review_id=ClaimPolicyRequirementMappingReviewId(data["review_id"]),
            claim_id=CapabilityClaimId(data["claim_id"]),
            policy_ref=EvaluationPolicyRef.parse(data["policy_ref"]),
            mapping_proposal_sha256=data["mapping_proposal_sha256"],
            reviewer_ref=ClaimPolicyRequirementMappingReviewerRef(
                ClaimPolicyRequirementMappingReviewerKind(reviewer["kind"]), reviewer["ref"]
            ),
            verdict=ClaimPolicyRequirementMappingReviewVerdict(data["verdict"]),
            reviewed_at=parse_time(data["reviewed_at"], "mapping reviewed_at"),
            rationale=data["rationale"],
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InvalidDomainPolicyRequirementApplication):
            raise
        raise InvalidDomainPolicyRequirementApplication(f"mapping review is invalid: {exc}") from exc
    if review.to_dict() != data:
        _fail("mapping review payload must use canonical ordering/content")
    return review


def claim_policy_requirement_mapping_review_to_json(review: ClaimPolicyRequirementMappingReview) -> str:
    return _canonical_json_text(review.to_dict())


def claim_policy_requirement_mapping_review_from_json(payload: object) -> ClaimPolicyRequirementMappingReview:
    data = _parse_canonical_json(payload, "mapping review")
    review = claim_policy_requirement_mapping_review_from_dict(data)
    if review.to_json() != payload:
        _fail("mapping review JSON must use exact canonical encoding")
    return review


def claim_policy_requirement_mapping_review_ledger_to_dict(ledger: ClaimPolicyRequirementMappingReviewLedger) -> dict:
    checked = _strict_review_ledger(ledger)
    return {"schema_version": 1, "reviews": [review.to_dict() for review in checked.reviews]}


def claim_policy_requirement_mapping_review_ledger_from_dict(payload: object) -> ClaimPolicyRequirementMappingReviewLedger:
    data = _require_exact_object(payload, expected_keys={"schema_version", "reviews"}, field_name="mapping review ledger")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        _fail("mapping review ledger schema_version must be exact integer 1")
    if type(data["reviews"]) is not list:
        _fail("mapping review ledger reviews must use exact array/list")
    ledger = ClaimPolicyRequirementMappingReviewLedger(
        reviews=tuple(claim_policy_requirement_mapping_review_from_dict(item) for item in data["reviews"])
    )
    if ledger.to_dict() != data:
        _fail("mapping review ledger payload must use canonical ordering/content")
    return ledger


def claim_policy_requirement_mapping_review_ledger_to_json(ledger: ClaimPolicyRequirementMappingReviewLedger) -> str:
    return _canonical_json_text(ledger.to_dict())


def claim_policy_requirement_mapping_review_ledger_from_json(payload: object) -> ClaimPolicyRequirementMappingReviewLedger:
    data = _parse_canonical_json(payload, "mapping review ledger")
    ledger = claim_policy_requirement_mapping_review_ledger_from_dict(data)
    if ledger.to_json() != payload:
        _fail("mapping review ledger JSON must use exact canonical encoding")
    return ledger


def claim_domain_policy_requirement_application_receipt_to_dict(application: ClaimDomainPolicyRequirementApplicationReceipt) -> dict:
    _validate_sha256(application.snapshot_sha256, "snapshot_sha256")
    _strict_claim_id(application.claim_id)
    _strict_subject_ref(application.subject_ref)
    _strict_concept_ref(application.concept_ref)
    _strict_claim_scope(application.claim_scope)
    _strict_stored_utc_time(application.as_of, "application as_of")
    _strict_policy_ref(application.policy_ref)
    _validate_sha256(application.specification_sha256, "specification_sha256")
    _opaque_id(application.policy_review_id, "policy_review_id")
    _validate_sha256(application.policy_review_sha256, "policy_review_sha256")
    _strict_stored_utc_time(application.policy_admitted_at, "policy_admitted_at")
    _validate_sha256(application.disposition_coverage_sha256, "disposition_coverage_sha256")
    _validate_sha256(application.lineage_dependence_sha256, "lineage_dependence_sha256")
    _validate_sha256(application.mapping_proposal_sha256, "mapping_proposal_sha256")
    _strict_review_id(application.mapping_review_id)
    _validate_sha256(application.mapping_review_sha256, "mapping_review_sha256")
    _canonical_entries(application.requirement_applications, require_canonical=True)
    if type(application.required_requirement_coverage_complete) is not bool:
        _fail("required_requirement_coverage_complete must use exact bool")
    return {
        "schema_version": 1,
        "snapshot_sha256": application.snapshot_sha256,
        "claim_id": application.claim_id.value,
        "subject_ref": application.subject_ref.value,
        "concept_ref": str(application.concept_ref),
        "claim_scope": _scope_to_dict(application.claim_scope),
        "as_of": format_time(application.as_of),
        "policy_ref": str(application.policy_ref),
        "specification_sha256": application.specification_sha256,
        "policy_review_id": application.policy_review_id,
        "policy_review_sha256": application.policy_review_sha256,
        "policy_admitted_at": format_time(application.policy_admitted_at),
        "disposition_coverage_sha256": application.disposition_coverage_sha256,
        "lineage_dependence_sha256": application.lineage_dependence_sha256,
        "mapping_proposal_sha256": application.mapping_proposal_sha256,
        "mapping_review_id": application.mapping_review_id.value,
        "mapping_review_sha256": application.mapping_review_sha256,
        "requirement_applications": [entry.to_dict() for entry in application.requirement_applications],
        "required_requirement_coverage_complete": application.required_requirement_coverage_complete,
    }


def claim_domain_policy_requirement_application_receipt_from_dict(payload: object) -> ClaimDomainPolicyRequirementApplicationReceipt:
    keys = {
        "schema_version", "snapshot_sha256", "claim_id", "subject_ref", "concept_ref", "claim_scope", "as_of",
        "policy_ref", "specification_sha256", "policy_review_id", "policy_review_sha256", "policy_admitted_at",
        "disposition_coverage_sha256", "lineage_dependence_sha256", "mapping_proposal_sha256", "mapping_review_id",
        "mapping_review_sha256", "requirement_applications", "required_requirement_coverage_complete",
    }
    data = _require_exact_object(payload, expected_keys=keys, field_name="application receipt")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        _fail("application receipt schema_version must be exact integer 1")
    if type(data["required_requirement_coverage_complete"]) is not bool:
        _fail("application receipt required_requirement_coverage_complete must use exact bool")
    for key in keys - {"schema_version", "claim_scope", "requirement_applications", "required_requirement_coverage_complete"}:
        if type(data[key]) is not str:
            _fail(f"application receipt {key} must use exact string")
    if type(data["requirement_applications"]) is not list:
        _fail("application receipt requirement_applications must use exact array/list")
    try:
        application = ClaimDomainPolicyRequirementApplicationReceipt(
            snapshot_sha256=data["snapshot_sha256"],
            claim_id=CapabilityClaimId(data["claim_id"]),
            subject_ref=CapabilitySubjectRef(data["subject_ref"]),
            concept_ref=CapabilityConceptRef.parse(data["concept_ref"]),
            claim_scope=_scope_from_dict(data["claim_scope"]),
            as_of=parse_time(data["as_of"], "application as_of"),
            policy_ref=EvaluationPolicyRef.parse(data["policy_ref"]),
            specification_sha256=data["specification_sha256"],
            policy_review_id=data["policy_review_id"],
            policy_review_sha256=data["policy_review_sha256"],
            policy_admitted_at=parse_time(data["policy_admitted_at"], "policy admitted_at"),
            disposition_coverage_sha256=data["disposition_coverage_sha256"],
            lineage_dependence_sha256=data["lineage_dependence_sha256"],
            mapping_proposal_sha256=data["mapping_proposal_sha256"],
            mapping_review_id=ClaimPolicyRequirementMappingReviewId(data["mapping_review_id"]),
            mapping_review_sha256=data["mapping_review_sha256"],
            requirement_applications=tuple(domain_policy_requirement_application_entry_from_dict(item) for item in data["requirement_applications"]),
            required_requirement_coverage_complete=data["required_requirement_coverage_complete"],
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InvalidDomainPolicyRequirementApplication):
            raise
        raise InvalidDomainPolicyRequirementApplication(f"application receipt is invalid: {exc}") from exc
    if application.to_dict() != data:
        _fail("application receipt payload must use canonical ordering/content")
    return application


def claim_domain_policy_requirement_application_receipt_to_json(application: ClaimDomainPolicyRequirementApplicationReceipt) -> str:
    return _canonical_json_text(application.to_dict())


def claim_domain_policy_requirement_application_receipt_from_json(payload: object) -> ClaimDomainPolicyRequirementApplicationReceipt:
    data = _parse_canonical_json(payload, "application receipt")
    application = claim_domain_policy_requirement_application_receipt_from_dict(data)
    if application.to_json() != payload:
        _fail("application receipt JSON must use exact canonical encoding")
    return application
