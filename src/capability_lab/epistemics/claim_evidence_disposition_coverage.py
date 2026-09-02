"""PR12.9 complete explicit candidate disposition coverage gate v1."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json

from capability_lab.semantics import CapabilityConceptRef, CapabilityId

from .claim_evidence_candidate_portfolio import (
    ClaimEvidenceCandidatePortfolioError,
    ClaimEvidenceCandidatePortfolioReceipt,
    build_complete_claim_evidence_candidate_portfolio_v1,
)
from .core import (
    CapabilityClaimId,
    CapabilitySubjectRef,
    EpistemicError,
    EvidenceAssessment,
    EvidenceBearing,
    EvidenceId,
    EvidenceReliability,
    canonical_time,
    format_time,
    parse_time,
)
from .record_set import EpistemicRecordSet


class ClaimEvidenceDispositionCoverageError(EpistemicError):
    """Base error for PR12.9 explicit disposition coverage governance."""


class InvalidClaimEvidenceDispositionCoverage(ClaimEvidenceDispositionCoverageError):
    """The supplied disposition coverage violates PR12.9 completeness."""


_SCHEMA_VERSION = 1
_SHA256_HEX_DIGITS = frozenset("0123456789abcdef")


def _fail(message: str) -> None:
    raise InvalidClaimEvidenceDispositionCoverage(message)


def _validate_sha256(value: object, field_name: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in _SHA256_HEX_DIGITS for character in value)
    ):
        _fail(f"{field_name} must be 64 lowercase hexadecimal SHA-256 characters")
    return value


def _canonical_boundary(value: object, field_name: str) -> datetime:
    if type(value) is not datetime:
        _fail(f"{field_name} must use exact datetime")
    try:
        return canonical_time(value, field_name)
    except EpistemicError as exc:
        raise InvalidClaimEvidenceDispositionCoverage(str(exc)) from exc


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
        raise InvalidClaimEvidenceDispositionCoverage(
            f"{field_name} failed strict reconstruction: {exc}"
        ) from exc
    if restored != value:
        _fail(f"{field_name} must equal strict semantic reconstruction")
    return value


def _strict_subject_ref(
    value: object,
    field_name: str = "subject_ref",
) -> CapabilitySubjectRef:
    if type(value) is not CapabilitySubjectRef or type(value.value) is not str:
        _fail(f"{field_name} must use exact CapabilitySubjectRef")
    try:
        restored = CapabilitySubjectRef(value.value)
    except (TypeError, ValueError) as exc:
        raise InvalidClaimEvidenceDispositionCoverage(
            f"{field_name} failed strict reconstruction: {exc}"
        ) from exc
    if restored != value:
        _fail(f"{field_name} must equal strict semantic reconstruction")
    return value


def _strict_evidence_id(value: object, field_name: str = "evidence_id") -> EvidenceId:
    if type(value) is not EvidenceId or type(value.value) is not str:
        _fail(f"{field_name} must use exact EvidenceId")
    try:
        restored = EvidenceId(value.value)
    except (TypeError, ValueError) as exc:
        raise InvalidClaimEvidenceDispositionCoverage(
            f"{field_name} failed strict reconstruction: {exc}"
        ) from exc
    if restored != value:
        _fail(f"{field_name} must equal strict semantic reconstruction")
    return value


def _strict_concept_ref(
    value: object,
    field_name: str = "concept_ref",
) -> CapabilityConceptRef:
    if type(value) is not CapabilityConceptRef:
        _fail(f"{field_name} must use exact CapabilityConceptRef")
    if type(value.capability_id) is not CapabilityId:
        _fail(f"{field_name}.capability_id must use exact CapabilityId")
    if (
        type(value.capability_id.namespace) is not str
        or type(value.capability_id.key) is not str
        or type(value.revision) is not int
    ):
        _fail(f"{field_name} contains non-exact scalar fields")
    try:
        restored = CapabilityConceptRef(
            CapabilityId(value.capability_id.namespace, value.capability_id.key),
            value.revision,
        )
    except (TypeError, ValueError) as exc:
        raise InvalidClaimEvidenceDispositionCoverage(
            f"{field_name} failed strict reconstruction: {exc}"
        ) from exc
    if restored != value:
        _fail(f"{field_name} must equal strict semantic reconstruction")
    return value


def _strict_assessment(
    value: object,
    field_name: str = "disposition",
) -> EvidenceAssessment:
    if type(value) is not EvidenceAssessment:
        _fail(f"{field_name} must use exact EvidenceAssessment")
    _strict_evidence_id(value.evidence_id, f"{field_name}.evidence_id")
    if type(value.bearing) is not EvidenceBearing:
        _fail(f"{field_name}.bearing must use exact EvidenceBearing")
    if type(value.reliability) is not EvidenceReliability:
        _fail(f"{field_name}.reliability must use exact EvidenceReliability")
    if type(value.coverage_note) is not str or type(value.rationale) is not str:
        _fail(f"{field_name} text fields must use exact strings")
    try:
        restored = EvidenceAssessment(
            evidence_id=EvidenceId(value.evidence_id.value),
            bearing=EvidenceBearing(value.bearing.value),
            reliability=EvidenceReliability(value.reliability.value),
            coverage_note=value.coverage_note,
            rationale=value.rationale,
        )
    except (TypeError, ValueError) as exc:
        raise InvalidClaimEvidenceDispositionCoverage(
            f"{field_name} failed strict reconstruction: {exc}"
        ) from exc
    if restored != value:
        _fail(f"{field_name} must equal strict semantic reconstruction")
    return value


def _canonical_assessments(
    value: object,
    field_name: str = "dispositions",
) -> tuple[EvidenceAssessment, ...]:
    if type(value) is not tuple:
        _fail(f"{field_name} must use exact tuple")
    items = value
    for index, item in enumerate(items):
        _strict_assessment(item, f"{field_name}[{index}]")
    ids = tuple(item.evidence_id for item in items)
    if len(set(ids)) != len(ids):
        _fail(f"{field_name} must contain exactly one disposition per evidence id")
    return tuple(sorted(items, key=lambda item: item.evidence_id))


def _portfolio_sha256(portfolio: ClaimEvidenceCandidatePortfolioReceipt) -> str:
    if type(portfolio) is not ClaimEvidenceCandidatePortfolioReceipt:
        _fail("candidate portfolio must use exact ClaimEvidenceCandidatePortfolioReceipt")
    return sha256(portfolio.to_json().encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ClaimEvidenceDispositionCoverageReceipt:
    """Deterministic complete explicit disposition coverage for one PR12.8 portfolio."""

    snapshot_sha256: str
    claim_id: CapabilityClaimId
    subject_ref: CapabilitySubjectRef
    concept_ref: CapabilityConceptRef
    as_of: datetime
    candidate_portfolio_sha256: str
    dispositions: tuple[EvidenceAssessment, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "snapshot_sha256",
            _validate_sha256(self.snapshot_sha256, "snapshot_sha256"),
        )
        _strict_claim_id(self.claim_id)
        _strict_subject_ref(self.subject_ref)
        _strict_concept_ref(self.concept_ref)
        object.__setattr__(
            self,
            "as_of",
            _canonical_boundary(self.as_of, "coverage as_of"),
        )
        object.__setattr__(
            self,
            "candidate_portfolio_sha256",
            _validate_sha256(
                self.candidate_portfolio_sha256,
                "candidate_portfolio_sha256",
            ),
        )
        object.__setattr__(
            self,
            "dispositions",
            _canonical_assessments(self.dispositions),
        )

    def to_dict(self) -> dict:
        return claim_evidence_disposition_coverage_receipt_to_dict(self)

    @classmethod
    def from_dict(cls, payload: object) -> "ClaimEvidenceDispositionCoverageReceipt":
        return claim_evidence_disposition_coverage_receipt_from_dict(payload)

    def to_json(self) -> str:
        return claim_evidence_disposition_coverage_receipt_to_json(self)

    @classmethod
    def from_json(cls, payload: object) -> "ClaimEvidenceDispositionCoverageReceipt":
        return claim_evidence_disposition_coverage_receipt_from_json(payload)


def _strict_receipt(
    coverage: object,
) -> ClaimEvidenceDispositionCoverageReceipt:
    if type(coverage) is not ClaimEvidenceDispositionCoverageReceipt:
        _fail("coverage must use exact ClaimEvidenceDispositionCoverageReceipt")
    _validate_sha256(coverage.snapshot_sha256, "snapshot_sha256")
    _strict_claim_id(coverage.claim_id)
    _strict_subject_ref(coverage.subject_ref)
    _strict_concept_ref(coverage.concept_ref)
    _strict_stored_utc_time(coverage.as_of, "coverage as_of")
    _validate_sha256(
        coverage.candidate_portfolio_sha256,
        "candidate_portfolio_sha256",
    )
    canonical = _canonical_assessments(coverage.dispositions)
    if canonical != coverage.dispositions:
        _fail("coverage dispositions must use canonical evidence-id ordering")
    try:
        restored = ClaimEvidenceDispositionCoverageReceipt(
            snapshot_sha256=coverage.snapshot_sha256,
            claim_id=CapabilityClaimId(coverage.claim_id.value),
            subject_ref=CapabilitySubjectRef(coverage.subject_ref.value),
            concept_ref=CapabilityConceptRef(
                CapabilityId(
                    coverage.concept_ref.capability_id.namespace,
                    coverage.concept_ref.capability_id.key,
                ),
                coverage.concept_ref.revision,
            ),
            as_of=coverage.as_of,
            candidate_portfolio_sha256=coverage.candidate_portfolio_sha256,
            dispositions=tuple(
                EvidenceAssessment(
                    evidence_id=EvidenceId(item.evidence_id.value),
                    bearing=EvidenceBearing(item.bearing.value),
                    reliability=EvidenceReliability(item.reliability.value),
                    coverage_note=item.coverage_note,
                    rationale=item.rationale,
                )
                for item in coverage.dispositions
            ),
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InvalidClaimEvidenceDispositionCoverage):
            raise
        raise InvalidClaimEvidenceDispositionCoverage(
            f"coverage failed strict reconstruction: {exc}"
        ) from exc
    if restored != coverage:
        _fail("coverage must equal strict semantic reconstruction")
    return coverage


def _build_expected_portfolio(
    *,
    records: EpistemicRecordSet,
    claim_id: CapabilityClaimId,
    as_of: datetime,
) -> ClaimEvidenceCandidatePortfolioReceipt:
    try:
        return build_complete_claim_evidence_candidate_portfolio_v1(
            records=records,
            claim_id=claim_id,
            as_of=as_of,
        )
    except ClaimEvidenceCandidatePortfolioError as exc:
        raise InvalidClaimEvidenceDispositionCoverage(
            f"PR12.8 candidate portfolio validation failed: {exc}"
        ) from exc


def _require_complete_disposition_set(
    *,
    candidate_ids: tuple[EvidenceId, ...],
    dispositions: tuple[EvidenceAssessment, ...],
) -> tuple[EvidenceAssessment, ...]:
    assessment_ids = tuple(item.evidence_id for item in dispositions)
    expected = set(candidate_ids)
    supplied = set(assessment_ids)
    missing = tuple(sorted(expected - supplied))
    if missing:
        _fail(f"disposition coverage omits candidate evidence: {missing[0]}")
    extra = tuple(sorted(supplied - expected))
    if extra:
        _fail(f"disposition coverage includes non-candidate evidence: {extra[0]}")
    return dispositions


def build_claim_evidence_disposition_coverage_v1(
    *,
    records: EpistemicRecordSet,
    claim_id: CapabilityClaimId,
    as_of: datetime,
    dispositions: tuple[EvidenceAssessment, ...],
) -> ClaimEvidenceDispositionCoverageReceipt:
    """Build exact one-to-one explicit disposition coverage for a PR12.8 portfolio."""

    portfolio = _build_expected_portfolio(
        records=records,
        claim_id=claim_id,
        as_of=as_of,
    )
    checked = _canonical_assessments(dispositions)
    _require_complete_disposition_set(
        candidate_ids=portfolio.evidence_ids,
        dispositions=checked,
    )
    return ClaimEvidenceDispositionCoverageReceipt(
        snapshot_sha256=portfolio.snapshot_sha256,
        claim_id=portfolio.claim_id,
        subject_ref=portfolio.subject_ref,
        concept_ref=portfolio.concept_ref,
        as_of=portfolio.as_of,
        candidate_portfolio_sha256=_portfolio_sha256(portfolio),
        dispositions=checked,
    )


def validate_complete_claim_evidence_disposition_coverage_v1(
    *,
    records: EpistemicRecordSet,
    claim_id: CapabilityClaimId,
    as_of: datetime,
    coverage: ClaimEvidenceDispositionCoverageReceipt,
) -> ClaimEvidenceDispositionCoverageReceipt:
    """Rebuild PR12.8 membership and require exact complete disposition coverage."""

    supplied = _strict_receipt(coverage)
    expected = build_claim_evidence_disposition_coverage_v1(
        records=records,
        claim_id=claim_id,
        as_of=as_of,
        dispositions=supplied.dispositions,
    )
    if supplied != expected:
        _fail(
            "coverage content does not match exact records-derived candidate portfolio "
            "and supplied disposition set"
        )
    return supplied


def claim_evidence_disposition_coverage_receipt_to_dict(
    coverage: ClaimEvidenceDispositionCoverageReceipt,
) -> dict:
    checked = _strict_receipt(coverage)
    return {
        "schema_version": _SCHEMA_VERSION,
        "snapshot_sha256": checked.snapshot_sha256,
        "claim_id": checked.claim_id.value,
        "subject_ref": checked.subject_ref.value,
        "concept_ref": str(checked.concept_ref),
        "as_of": format_time(checked.as_of),
        "candidate_portfolio_sha256": checked.candidate_portfolio_sha256,
        "dispositions": [
            {
                "evidence_id": item.evidence_id.value,
                "bearing": item.bearing.value,
                "reliability": item.reliability.value,
                "coverage_note": item.coverage_note,
                "rationale": item.rationale,
            }
            for item in checked.dispositions
        ],
    }


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
    actual_keys = set(payload)
    unknown = actual_keys - expected_keys
    if unknown:
        _fail(f"{field_name} contains unknown field: {sorted(unknown)[0]}")
    missing = expected_keys - actual_keys
    if missing:
        _fail(f"{field_name} is missing field: {sorted(missing)[0]}")
    return payload


def _assessment_from_dict(payload: object, index: int) -> EvidenceAssessment:
    field_name = f"dispositions[{index}]"
    data = _require_exact_object(
        payload,
        expected_keys={
            "evidence_id",
            "bearing",
            "reliability",
            "coverage_note",
            "rationale",
        },
        field_name=field_name,
    )
    if any(
        type(data[key]) is not str
        for key in (
            "evidence_id",
            "bearing",
            "reliability",
            "coverage_note",
            "rationale",
        )
    ):
        _fail(f"{field_name} fields must use exact strings")
    try:
        return EvidenceAssessment(
            evidence_id=EvidenceId(data["evidence_id"]),
            bearing=EvidenceBearing(data["bearing"]),
            reliability=EvidenceReliability(data["reliability"]),
            coverage_note=data["coverage_note"],
            rationale=data["rationale"],
        )
    except (TypeError, ValueError) as exc:
        raise InvalidClaimEvidenceDispositionCoverage(
            f"{field_name} failed strict reconstruction: {exc}"
        ) from exc


def claim_evidence_disposition_coverage_receipt_from_dict(
    payload: object,
) -> ClaimEvidenceDispositionCoverageReceipt:
    data = _require_exact_object(
        payload,
        expected_keys={
            "schema_version",
            "snapshot_sha256",
            "claim_id",
            "subject_ref",
            "concept_ref",
            "as_of",
            "candidate_portfolio_sha256",
            "dispositions",
        },
        field_name="coverage payload",
    )
    if type(data["schema_version"]) is not int or data["schema_version"] != _SCHEMA_VERSION:
        _fail("coverage payload schema_version must be exact integer 1")
    for key in (
        "snapshot_sha256",
        "claim_id",
        "subject_ref",
        "concept_ref",
        "as_of",
        "candidate_portfolio_sha256",
    ):
        if type(data[key]) is not str:
            _fail(f"coverage payload {key} must use exact string")
    if type(data["dispositions"]) is not list:
        _fail("coverage payload dispositions must use exact JSON array/list")
    dispositions = tuple(
        _assessment_from_dict(item, index)
        for index, item in enumerate(data["dispositions"])
    )
    canonical = tuple(sorted(dispositions, key=lambda item: item.evidence_id))
    if dispositions != canonical:
        _fail("coverage payload dispositions must use canonical evidence-id ordering")
    try:
        return ClaimEvidenceDispositionCoverageReceipt(
            snapshot_sha256=_validate_sha256(
                data["snapshot_sha256"],
                "snapshot_sha256",
            ),
            claim_id=CapabilityClaimId(data["claim_id"]),
            subject_ref=CapabilitySubjectRef(data["subject_ref"]),
            concept_ref=CapabilityConceptRef.parse(data["concept_ref"]),
            as_of=parse_time(data["as_of"], "coverage as_of"),
            candidate_portfolio_sha256=_validate_sha256(
                data["candidate_portfolio_sha256"],
                "candidate_portfolio_sha256",
            ),
            dispositions=dispositions,
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InvalidClaimEvidenceDispositionCoverage):
            raise
        raise InvalidClaimEvidenceDispositionCoverage(
            f"coverage payload failed strict reconstruction: {exc}"
        ) from exc


def _reject_json_constant(value: str):
    _fail(f"coverage JSON contains non-standard constant: {value}")


def _reject_duplicate_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            _fail(f"coverage JSON contains duplicate field: {key}")
        result[key] = value
    return result


def claim_evidence_disposition_coverage_receipt_to_json(
    coverage: ClaimEvidenceDispositionCoverageReceipt,
) -> str:
    return json.dumps(
        claim_evidence_disposition_coverage_receipt_to_dict(coverage),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def claim_evidence_disposition_coverage_receipt_from_json(
    payload: object,
) -> ClaimEvidenceDispositionCoverageReceipt:
    if type(payload) is not str:
        _fail("coverage JSON payload must use exact string")
    try:
        decoded = json.loads(
            payload,
            object_pairs_hook=_reject_duplicate_json_object,
            parse_constant=_reject_json_constant,
        )
    except InvalidClaimEvidenceDispositionCoverage:
        raise
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise InvalidClaimEvidenceDispositionCoverage(
            f"coverage JSON is invalid: {exc}"
        ) from exc
    return claim_evidence_disposition_coverage_receipt_from_dict(decoded)
