"""Resolver-issued terminal receipts for PR12.1 external observation materialization."""

from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import re

from capability_lab.epistemics import EvidenceId
from capability_lab.epistemics.record_set import EpistemicRecordSet
from capability_lab.epistemics.serialization import record_set_from_json, record_set_to_json

from . import materialization as _m

_REVIEW_HASH_DOMAIN = b"capability_lab/external_observation_evidence_review@1\x00"
_EVIDENCE_HASH_DOMAIN = (
    b"capability_lab/external_observation_materialized_evidence_record@1\x00"
)
_ISSUANCE_WITNESS_DOMAIN = (
    b"capability_lab/external_observation_evidence_resolution_witness@1\x00"
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_RECEIPT_ISSUER_TOKEN = object()

def _fail(message: str) -> None:
    raise _m.InvalidExternalObservationEvidenceMaterialization(message)

def _sha256(value: object, label: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        _fail(f"{label} must be 64 lowercase hexadecimal SHA-256 characters")
    return value

def _time(value: object, label: str) -> datetime:
    if type(value) is not datetime:
        _fail(f"{label} must use exact datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        _fail(f"{label} must be timezone-aware")
    return value.astimezone(timezone.utc)

def external_observation_evidence_review_sha256_v1(review) -> str:
    _m._strict_review(review)
    from .materialization_serialization import external_observation_evidence_review_to_json
    digest = hashlib.sha256()
    digest.update(_REVIEW_HASH_DOMAIN)
    digest.update(external_observation_evidence_review_to_json(review).encode("utf-8"))
    return digest.hexdigest()

def _strict_evidence(evidence):
    if type(evidence) is not _m.EvidenceRecord:
        _fail("evidence must use exact EvidenceRecord")
    try:
        canonical = record_set_to_json(EpistemicRecordSet(evidence_records=(evidence,)))
        restored_set = record_set_from_json(canonical)
    except (TypeError, ValueError) as exc:
        raise _m.InvalidExternalObservationEvidenceMaterialization(
            f"evidence failed strict PR2 reconstruction: {exc}"
        ) from exc
    if restored_set.evidence_records != (evidence,):
        _fail("evidence must equal strict canonical PR2 reconstruction")
    return evidence

def external_observation_materialized_evidence_sha256_v1(evidence) -> str:
    _strict_evidence(evidence)
    try:
        canonical = record_set_to_json(EpistemicRecordSet(evidence_records=(evidence,)))
    except (TypeError, ValueError) as exc:
        raise _m.InvalidExternalObservationEvidenceMaterialization(
            f"cannot serialize exact EvidenceRecord: {exc}"
        ) from exc
    digest = hashlib.sha256()
    digest.update(_EVIDENCE_HASH_DOMAIN)
    digest.update(canonical.encode("utf-8"))
    return digest.hexdigest()

def _receipt_payload_sha256_v1(
    *, materialization_id, candidate_sha256: str, review_id, review_sha256: str,
    verdict, observation_sha256: str, evidence_id, evidence_sha256,
    resolved_at: datetime,
) -> str:
    payload = {
        "materialization_id": str(materialization_id),
        "candidate_sha256": candidate_sha256,
        "review_id": str(review_id),
        "review_sha256": review_sha256,
        "verdict": verdict.value,
        "observation_sha256": observation_sha256,
        "evidence_id": str(evidence_id) if evidence_id is not None else None,
        "evidence_sha256": evidence_sha256,
        "resolved_at": resolved_at.isoformat(),
    }
    try:
        canonical = json.dumps(
            payload, ensure_ascii=True, sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise _m.InvalidExternalObservationEvidenceMaterialization(
            f"receipt payload is not canonical JSON: {exc}"
        ) from exc
    digest = hashlib.sha256()
    digest.update(_ISSUANCE_WITNESS_DOMAIN)
    digest.update(canonical)
    return digest.hexdigest()

@dataclass(frozen=True, slots=True)
class _ExternalObservationEvidenceResolutionIssuanceWitness:
    payload_sha256: str
    _issuer_token: InitVar[object]
    def __post_init__(self, _issuer_token: object) -> None:
        if _issuer_token is not _RECEIPT_ISSUER_TOKEN:
            _fail("resolution issuance witness must be created by the PR12.1 resolver")
        object.__setattr__(
            self, "payload_sha256",
            _sha256(self.payload_sha256, "issuance witness payload_sha256")
        )

@dataclass(frozen=True, slots=True)
class ExternalObservationEvidenceResolutionReceipt:
    materialization_id: _m.ExternalObservationEvidenceMaterializationId
    candidate_sha256: str
    review_id: _m.ExternalObservationEvidenceReviewId
    review_sha256: str
    verdict: _m.ExternalObservationEvidenceMaterializationVerdict
    observation_sha256: str
    evidence_id: EvidenceId | None
    evidence_sha256: str | None
    resolved_at: datetime
    _issuance_witness: _ExternalObservationEvidenceResolutionIssuanceWitness = field(
        repr=False, compare=False
    )
    def __post_init__(self) -> None:
        if type(self.materialization_id) is not _m.ExternalObservationEvidenceMaterializationId:
            _fail("receipt materialization_id has invalid type")
        object.__setattr__(self, "candidate_sha256", _sha256(self.candidate_sha256, "receipt candidate_sha256"))
        if type(self.review_id) is not _m.ExternalObservationEvidenceReviewId:
            _fail("receipt review_id has invalid type")
        object.__setattr__(self, "review_sha256", _sha256(self.review_sha256, "receipt review_sha256"))
        if type(self.verdict) is not _m.ExternalObservationEvidenceMaterializationVerdict:
            _fail("receipt verdict has invalid type")
        object.__setattr__(self, "observation_sha256", _sha256(self.observation_sha256, "receipt observation_sha256"))
        if self.verdict is _m.ExternalObservationEvidenceMaterializationVerdict.MATERIALIZE:
            if type(self.evidence_id) is not EvidenceId:
                _fail("MATERIALIZE receipt requires exact EvidenceId")
            if self.evidence_sha256 is None:
                _fail("MATERIALIZE receipt requires evidence_sha256")
            object.__setattr__(self, "evidence_sha256", _sha256(self.evidence_sha256, "receipt evidence_sha256"))
        else:
            if self.evidence_id is not None or self.evidence_sha256 is not None:
                _fail("DO_NOT_MATERIALIZE receipt must not claim EvidenceRecord identity")
        object.__setattr__(self, "resolved_at", _time(self.resolved_at, "receipt resolved_at"))
        _validate_receipt_witness(self)

def _validate_receipt_witness(receipt: ExternalObservationEvidenceResolutionReceipt) -> None:
    if type(receipt._issuance_witness) is not _ExternalObservationEvidenceResolutionIssuanceWitness:
        _fail("resolution receipt requires a private resolver-issued witness")
    expected = _receipt_payload_sha256_v1(
        materialization_id=receipt.materialization_id,
        candidate_sha256=receipt.candidate_sha256,
        review_id=receipt.review_id,
        review_sha256=receipt.review_sha256,
        verdict=receipt.verdict,
        observation_sha256=receipt.observation_sha256,
        evidence_id=receipt.evidence_id,
        evidence_sha256=receipt.evidence_sha256,
        resolved_at=receipt.resolved_at,
    )
    if receipt._issuance_witness.payload_sha256 != expected:
        _fail("resolution receipt witness does not match exact current receipt payload")

@dataclass(frozen=True, slots=True)
class ExternalObservationEvidenceResolutionBinding:
    review: _m.ExternalObservationEvidenceMaterializationReview
    receipt: ExternalObservationEvidenceResolutionReceipt
    def __post_init__(self) -> None:
        _m._strict_review(self.review)
        if type(self.receipt) is not ExternalObservationEvidenceResolutionReceipt:
            _fail("binding receipt must use exact ExternalObservationEvidenceResolutionReceipt")
        _validate_receipt_witness(self.receipt)

def _validate_candidate_review(candidate, review) -> str:
    _m._strict_candidate(candidate)
    _m._strict_review(review)
    candidate_sha256 = _m.external_observation_evidence_materialization_candidate_sha256_v1(candidate)
    if review.materialization_id != candidate.materialization_id:
        _fail("review materialization_id does not match candidate")
    if review.policy_ref != candidate.policy_ref:
        _fail("review policy_ref does not match candidate")
    if review.candidate_sha256 != candidate_sha256:
        _fail("review candidate_sha256 does not match exact candidate")
    if review.reviewed_at < candidate.proposed_at:
        _fail("reviewed_at must not precede candidate proposed_at")
    return candidate_sha256

def _validate_evidence_semantics(candidate, review, observation, evidence) -> None:
    _strict_evidence(evidence)
    expected = _m._build_neutral_evidence(
        observation=observation,
        candidate=candidate,
        review=review,
        recorded_at=review.reviewed_at,
    )
    if evidence != expected:
        _fail("resolved EvidenceRecord does not match frozen PR12.1 neutral mapping")
    if evidence.evidence_id != candidate.materialized_evidence_id:
        _fail("resolved EvidenceRecord id does not match deterministic candidate id")
    if evidence.recorded_at != review.reviewed_at:
        _fail("PR12.1 EvidenceRecord recorded_at must equal exact review reviewed_at")
    if evidence.outcome is not None:
        _fail("PR12.1 materialized EvidenceRecord outcome must remain None")

def _issue_receipt(*, candidate, review, evidence):
    resolved_at = review.reviewed_at
    candidate_sha256 = _m.external_observation_evidence_materialization_candidate_sha256_v1(candidate)
    review_sha256 = external_observation_evidence_review_sha256_v1(review)
    evidence_id = evidence.evidence_id if evidence is not None else None
    evidence_sha256 = (
        external_observation_materialized_evidence_sha256_v1(evidence)
        if evidence is not None else None
    )
    payload_sha256 = _receipt_payload_sha256_v1(
        materialization_id=candidate.materialization_id,
        candidate_sha256=candidate_sha256,
        review_id=review.review_id,
        review_sha256=review_sha256,
        verdict=review.verdict,
        observation_sha256=candidate.observation_sha256,
        evidence_id=evidence_id,
        evidence_sha256=evidence_sha256,
        resolved_at=resolved_at,
    )
    witness = _ExternalObservationEvidenceResolutionIssuanceWitness(
        payload_sha256=payload_sha256, _issuer_token=_RECEIPT_ISSUER_TOKEN
    )
    return ExternalObservationEvidenceResolutionReceipt(
        materialization_id=candidate.materialization_id,
        candidate_sha256=candidate_sha256,
        review_id=review.review_id,
        review_sha256=review_sha256,
        verdict=review.verdict,
        observation_sha256=candidate.observation_sha256,
        evidence_id=evidence_id,
        evidence_sha256=evidence_sha256,
        resolved_at=resolved_at,
        _issuance_witness=witness,
    )

def resolve_reviewed_external_observation_evidence_materialization_v1(
    *, ledger, candidate, review
):
    """Deterministically resolve one exact admitted observation and exact review."""
    _validate_candidate_review(candidate, review)
    observation = _m._verify_candidate_source(ledger=ledger, candidate=candidate)
    if review.reviewed_at < observation.captured_at:
        _fail("reviewed_at must not precede admitted observation captured_at")
    evidence = None
    if review.verdict is _m.ExternalObservationEvidenceMaterializationVerdict.MATERIALIZE:
        evidence = _m._build_neutral_evidence(
            observation=observation, candidate=candidate, review=review,
            recorded_at=review.reviewed_at,
        )
        _validate_evidence_semantics(candidate, review, observation, evidence)
    receipt = _issue_receipt(candidate=candidate, review=review, evidence=evidence)
    return evidence, receipt

def validate_external_observation_evidence_resolution_binding_v1(
    *, ledger, candidate, evidence, binding
) -> None:
    if type(binding) is not ExternalObservationEvidenceResolutionBinding:
        _fail("binding must use exact ExternalObservationEvidenceResolutionBinding")
    review = binding.review
    receipt = binding.receipt
    candidate_sha256 = _validate_candidate_review(candidate, review)
    observation = _m._verify_candidate_source(ledger=ledger, candidate=candidate)
    _validate_receipt_witness(receipt)
    if receipt.materialization_id != candidate.materialization_id:
        _fail("receipt materialization_id does not match candidate")
    if receipt.candidate_sha256 != candidate_sha256:
        _fail("receipt candidate_sha256 does not match candidate")
    if receipt.review_id != review.review_id:
        _fail("receipt review_id does not match review")
    if receipt.review_sha256 != external_observation_evidence_review_sha256_v1(review):
        _fail("receipt review_sha256 does not match exact review")
    if receipt.verdict is not review.verdict:
        _fail("receipt verdict does not match review")
    if receipt.observation_sha256 != candidate.observation_sha256:
        _fail("receipt observation_sha256 does not match candidate")
    if receipt.resolved_at != review.reviewed_at:
        _fail("receipt resolved_at must equal exact review reviewed_at")
    if review.verdict is _m.ExternalObservationEvidenceMaterializationVerdict.DO_NOT_MATERIALIZE:
        if evidence is not None:
            _fail("DO_NOT_MATERIALIZE binding must not contain EvidenceRecord")
        if receipt.evidence_id is not None or receipt.evidence_sha256 is not None:
            _fail("DO_NOT_MATERIALIZE receipt must not claim evidence")
        return
    if evidence is None:
        _fail("MATERIALIZE binding requires EvidenceRecord")
    _validate_evidence_semantics(candidate, review, observation, evidence)
    if receipt.evidence_id != evidence.evidence_id:
        _fail("receipt evidence_id does not match EvidenceRecord")
    if receipt.evidence_sha256 != external_observation_materialized_evidence_sha256_v1(evidence):
        _fail("receipt evidence_sha256 does not match exact EvidenceRecord")
    if receipt.resolved_at != evidence.recorded_at:
        _fail("receipt resolved_at must equal EvidenceRecord recorded_at")
