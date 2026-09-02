"""Exact reviewed-resolution receipts for terminal PR10.1 materialization governance."""

from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import re

from . import materialization as _materialization

_REVIEW_HASH_DOMAIN = (
    b"capability_lab/pilot_evidence_materialization_review_receipt_binding@1\x00"
)
_EVIDENCE_HASH_DOMAIN = (
    b"capability_lab/pilot_materialized_evidence_record_receipt_binding@1\x00"
)
_ISSUANCE_WITNESS_DOMAIN = (
    b"capability_lab/pilot_reviewed_materialization_resolution_issuance_witness@1\x00"
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_RECEIPT_ISSUER_TOKEN = object()


def _sha256(value: object, field_name: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            f"{field_name} must be a lowercase 64-character sha256 digest"
        )
    return value


def _canonical_time(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            f"{field_name} must be datetime"
        )
    if value.tzinfo is None or value.utcoffset() is None:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            f"{field_name} must be timezone-aware"
        )
    return value.astimezone(timezone.utc)


def _receipt_payload_sha256_v1(
    *,
    materialization_id,
    candidate_sha256: str,
    review_id,
    review_sha256: str,
    evidence_id,
    evidence_sha256: str,
    resolved_at: datetime,
) -> str:
    """Return the exact payload digest committed by a resolver issuance witness."""

    payload = {
        "materialization_id": str(materialization_id),
        "candidate_sha256": candidate_sha256,
        "review_id": str(review_id),
        "review_sha256": review_sha256,
        "evidence_id": str(evidence_id),
        "evidence_sha256": evidence_sha256,
        "resolved_at": resolved_at.isoformat(),
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    digest = hashlib.sha256()
    digest.update(_ISSUANCE_WITNESS_DOMAIN)
    digest.update(canonical)
    return digest.hexdigest()


def pilot_evidence_materialization_review_sha256_v1(review) -> str:
    """Return a domain-separated digest of exact canonical review bytes."""

    if not isinstance(review, _materialization.PilotEvidenceMaterializationReview):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "review must be PilotEvidenceMaterializationReview"
        )
    from .materialization_serialization import materialization_review_to_json

    digest = hashlib.sha256()
    digest.update(_REVIEW_HASH_DOMAIN)
    digest.update(materialization_review_to_json(review).encode("utf-8"))
    return digest.hexdigest()


def pilot_materialized_evidence_record_sha256_v1(evidence) -> str:
    """Bind a receipt to every canonical PR2 field of one EvidenceRecord."""

    if not isinstance(evidence, _materialization.EvidenceRecord):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "evidence must be EvidenceRecord"
        )
    from capability_lab.epistemics.record_set import EpistemicRecordSet
    from capability_lab.epistemics.serialization import record_set_to_json

    canonical = record_set_to_json(EpistemicRecordSet(evidence_records=(evidence,)))
    digest = hashlib.sha256()
    digest.update(_EVIDENCE_HASH_DOMAIN)
    digest.update(canonical.encode("utf-8"))
    return digest.hexdigest()


@dataclass(frozen=True, slots=True)
class _PilotReviewedMaterializationIssuanceWitness:
    """Private non-transferable resolver capability bound to one receipt payload."""

    payload_sha256: str
    _issuer_token: InitVar[object]

    def __post_init__(self, _issuer_token: object) -> None:
        if _issuer_token is not _RECEIPT_ISSUER_TOKEN:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "reviewed materialization issuance witness must be created by "
                "resolve_reviewed_pilot_evidence_materialization_with_receipt_v1"
            )
        object.__setattr__(
            self,
            "payload_sha256",
            _sha256(self.payload_sha256, "issuance witness payload_sha256"),
        )


@dataclass(frozen=True, slots=True)
class PilotReviewedMaterializationResolutionReceipt:
    """Resolver-issued exact binding of candidate, review and resolved evidence.

    The receipt is structural local governance metadata. It is not a signature,
    authenticated reviewer identity, trusted timestamp, or proof that the review
    was historically executed by the named person. Direct public construction is
    intentionally rejected; the supported issuer is the reviewed resolver wrapper.

    The private issuance witness commits the exact receipt payload. Copying a real
    receipt or witness therefore cannot authorize a different candidate/review/
    evidence binding through ``dataclasses.replace``.
    """

    materialization_id: _materialization.PilotEvidenceMaterializationId
    candidate_sha256: str
    review_id: _materialization.PilotEvidenceMaterializationReviewId
    review_sha256: str
    evidence_id: _materialization.EvidenceId
    evidence_sha256: str
    resolved_at: datetime
    _issuance_witness: _PilotReviewedMaterializationIssuanceWitness = field(
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.materialization_id,
            _materialization.PilotEvidenceMaterializationId,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "receipt materialization_id must be PilotEvidenceMaterializationId"
            )
        object.__setattr__(
            self,
            "candidate_sha256",
            _sha256(self.candidate_sha256, "receipt candidate_sha256"),
        )
        if not isinstance(
            self.review_id,
            _materialization.PilotEvidenceMaterializationReviewId,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "receipt review_id must be PilotEvidenceMaterializationReviewId"
            )
        object.__setattr__(
            self,
            "review_sha256",
            _sha256(self.review_sha256, "receipt review_sha256"),
        )
        if not isinstance(self.evidence_id, _materialization.EvidenceId):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "receipt evidence_id must be EvidenceId"
            )
        object.__setattr__(
            self,
            "evidence_sha256",
            _sha256(self.evidence_sha256, "receipt evidence_sha256"),
        )
        object.__setattr__(
            self,
            "resolved_at",
            _canonical_time(self.resolved_at, "receipt resolved_at"),
        )
        _validate_receipt_issuance_witness_v1(self)


def _validate_receipt_issuance_witness_v1(
    receipt: PilotReviewedMaterializationResolutionReceipt,
) -> None:
    if not isinstance(
        receipt._issuance_witness,
        _PilotReviewedMaterializationIssuanceWitness,
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "reviewed materialization resolution receipt requires a private "
            "resolver-issued payload witness"
        )
    expected_payload_sha256 = _receipt_payload_sha256_v1(
        materialization_id=receipt.materialization_id,
        candidate_sha256=receipt.candidate_sha256,
        review_id=receipt.review_id,
        review_sha256=receipt.review_sha256,
        evidence_id=receipt.evidence_id,
        evidence_sha256=receipt.evidence_sha256,
        resolved_at=receipt.resolved_at,
    )
    if receipt._issuance_witness.payload_sha256 != expected_payload_sha256:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "reviewed materialization resolution receipt issuance witness does not "
            "match the exact current receipt payload"
        )


@dataclass(frozen=True, slots=True)
class PilotReviewedMaterializationResolutionBinding:
    """Exact human review plus resolver-issued receipt for one terminal slot."""

    review: _materialization.PilotEvidenceMaterializationReview
    receipt: PilotReviewedMaterializationResolutionReceipt

    def __post_init__(self) -> None:
        if not isinstance(
            self.review,
            _materialization.PilotEvidenceMaterializationReview,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "resolution binding review must be PilotEvidenceMaterializationReview"
            )
        if not isinstance(
            self.receipt,
            PilotReviewedMaterializationResolutionReceipt,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "resolution binding receipt must be "
                "PilotReviewedMaterializationResolutionReceipt"
            )
        _validate_receipt_issuance_witness_v1(self.receipt)


def _expected_summary(candidate) -> str:
    return (
        f"Pilot 01 capture for probe '{candidate.probe_id}' "
        f"(kind={candidate.capture_kind.value}; origin declared SUBJECT_PROVIDED)."
    )


def _expected_context_description(candidate) -> str:
    return (
        f"Exact private Pilot 01 capture under {candidate.protocol_ref}; "
        f"session={candidate.session_id}; probe={candidate.probe_id}; "
        f"capture_kind={candidate.capture_kind.value}; origin is declared "
        "SUBJECT_PROVIDED. Source content remains in the private capture "
        "workspace and is not interpreted here."
    )


def _validate_candidate_review_v1(candidate, review, *, require_materialize: bool = True) -> str:
    if not isinstance(
        candidate,
        _materialization.PilotEvidenceMaterializationCandidate,
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "candidate must be PilotEvidenceMaterializationCandidate"
        )
    if not isinstance(review, _materialization.PilotEvidenceMaterializationReview):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "review must be PilotEvidenceMaterializationReview"
        )
    candidate_sha256 = _materialization.pilot_evidence_materialization_candidate_sha256(
        candidate
    )
    if review.materialization_id != candidate.materialization_id:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "resolution binding review materialization_id does not match candidate"
        )
    if review.policy_ref != candidate.policy_ref:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "resolution binding review policy_ref does not match candidate"
        )
    if review.candidate_sha256 != candidate_sha256:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "resolution binding review candidate_sha256 does not match exact candidate"
        )
    if (
        require_materialize
        and review.verdict is not _materialization.PilotEvidenceMaterializationVerdict.MATERIALIZE
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "terminal reviewed materialization binding requires MATERIALIZE verdict"
        )
    if review.reviewed_at < candidate.proposed_at:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "resolution binding review reviewed_at must not precede candidate proposed_at"
        )
    return candidate_sha256


def _validate_resolved_evidence_semantics_v1(candidate, review, evidence) -> None:
    if not isinstance(evidence, _materialization.EvidenceRecord):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "evidence must be EvidenceRecord"
        )

    # Local import avoids making the materialization module depend on its
    # downstream structural-dependence layer.
    from . import materialization_dependence as _dependence

    source_key = _dependence.pilot_materialized_evidence_dependence_key_v1(evidence)
    if source_key != candidate.source_capture_ref:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "resolved evidence source does not match candidate source capture"
        )
    if evidence.evidence_id != candidate.proposed_evidence_id:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "resolved evidence_id does not match candidate proposed_evidence_id"
        )
    if evidence.subject_ref != candidate.subject_ref:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "resolved evidence subject does not match candidate subject"
        )

    expected_kind = (
        _materialization.EvidenceKind.ARTIFACT
        if candidate.capture_kind is _materialization.PilotCaptureKind.FILE_ARTIFACT
        else _materialization.EvidenceKind.OTHER
    )
    if evidence.kind is not expected_kind:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "resolved evidence kind does not match the frozen neutral Pilot 01 mapping"
        )
    if evidence.summary != _expected_summary(candidate):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "resolved evidence summary does not match the frozen neutral Pilot 01 mapping"
        )
    if evidence.context.description != _expected_context_description(candidate):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "resolved evidence context description does not match the frozen neutral Pilot 01 mapping"
        )
    if evidence.context.scope_tags != tuple(
        sorted(("pilot_capture", candidate.probe_id))
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "resolved evidence scope_tags do not match the frozen Pilot 01 mapping"
        )
    if any(
        factor.kind is not _materialization.ContextFactorKind.TOOL
        for factor in evidence.context.factors
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "resolved evidence context factors must remain declared TOOL factors only"
        )
    if evidence.observation_started_at is not None:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "resolved Pilot 01 evidence must preserve observation_started_at=None"
        )
    if evidence.observed_at > candidate.proposed_at:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "resolved evidence observed_at must not follow candidate proposed_at"
        )
    if evidence.recorded_at < review.reviewed_at:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "resolved evidence recorded_at must not precede selected review"
        )

    materialization_id, candidate_sha256, review_id = (
        _dependence._materialization_note_fields_v1(evidence)
    )
    if materialization_id != str(candidate.materialization_id):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "resolved evidence provenance materialization_id does not match candidate"
        )
    if candidate_sha256 != review.candidate_sha256:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "resolved evidence provenance candidate_sha256 does not match selected review"
        )
    if review_id != str(review.review_id):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "resolved evidence provenance review_id does not match selected review"
        )

    step = evidence.provenance.steps[0]
    if step.actor_ref != _materialization.ActorRef(review.reviewer_ref.ref):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "resolved evidence provenance actor_ref does not match selected reviewer"
        )
    if step.occurred_at != evidence.recorded_at:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "resolved evidence provenance occurred_at must equal evidence recorded_at"
        )


def resolve_reviewed_pilot_evidence_materialization_with_receipt_v1(
    workspace,
    *,
    candidate,
    review,
    resolved_at,
):
    """Resolve a reviewed candidate and issue an exact receipt for MATERIALIZE.

    DO_NOT_MATERIALIZE preserves the existing resolver semantics and returns
    ``(None, None)``. A MATERIALIZE resolution returns the canonical EvidenceRecord
    plus a receipt binding exact candidate bytes, exact review bytes, and every
    canonical field of the exact PR2 EvidenceRecord.
    """

    candidate_sha256 = _validate_candidate_review_v1(
        candidate, review, require_materialize=False
    )
    evidence = _materialization.resolve_reviewed_pilot_evidence_materialization_v1(
        workspace,
        candidate=candidate,
        review=review,
        resolved_at=resolved_at,
    )
    if evidence is None:
        if review.verdict is not _materialization.PilotEvidenceMaterializationVerdict.DO_NOT_MATERIALIZE:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "non-DO_NOT_MATERIALIZE review unexpectedly produced no EvidenceRecord"
            )
        return None, None

    _validate_candidate_review_v1(candidate, review, require_materialize=True)
    _validate_resolved_evidence_semantics_v1(candidate, review, evidence)

    review_sha256 = pilot_evidence_materialization_review_sha256_v1(review)
    evidence_sha256 = pilot_materialized_evidence_record_sha256_v1(evidence)
    payload_sha256 = _receipt_payload_sha256_v1(
        materialization_id=candidate.materialization_id,
        candidate_sha256=candidate_sha256,
        review_id=review.review_id,
        review_sha256=review_sha256,
        evidence_id=evidence.evidence_id,
        evidence_sha256=evidence_sha256,
        resolved_at=evidence.recorded_at,
    )
    issuance_witness = _PilotReviewedMaterializationIssuanceWitness(
        payload_sha256=payload_sha256,
        _issuer_token=_RECEIPT_ISSUER_TOKEN,
    )
    receipt = PilotReviewedMaterializationResolutionReceipt(
        materialization_id=candidate.materialization_id,
        candidate_sha256=candidate_sha256,
        review_id=review.review_id,
        review_sha256=review_sha256,
        evidence_id=evidence.evidence_id,
        evidence_sha256=evidence_sha256,
        resolved_at=evidence.recorded_at,
        _issuance_witness=issuance_witness,
    )
    return evidence, receipt


def validate_pilot_reviewed_materialization_resolution_binding_v1(
    candidate,
    evidence,
    binding,
) -> None:
    """Require one exact MATERIALIZE review and resolver receipt for one slot."""

    if not isinstance(binding, PilotReviewedMaterializationResolutionBinding):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "binding must be PilotReviewedMaterializationResolutionBinding"
        )
    review = binding.review
    receipt = binding.receipt
    _validate_receipt_issuance_witness_v1(receipt)
    candidate_sha256 = _validate_candidate_review_v1(candidate, review)
    _validate_resolved_evidence_semantics_v1(candidate, review, evidence)

    if receipt.materialization_id != candidate.materialization_id:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "resolution receipt materialization_id does not match candidate"
        )
    if receipt.candidate_sha256 != candidate_sha256:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "resolution receipt candidate_sha256 does not match exact candidate"
        )
    if receipt.review_id != review.review_id:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "resolution receipt review_id does not match selected review"
        )
    if receipt.review_sha256 != pilot_evidence_materialization_review_sha256_v1(review):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "resolution receipt review_sha256 does not match exact selected review"
        )
    if receipt.evidence_id != evidence.evidence_id:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "resolution receipt evidence_id does not match exact EvidenceRecord"
        )
    if receipt.evidence_sha256 != pilot_materialized_evidence_record_sha256_v1(evidence):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "resolution receipt evidence_sha256 does not match exact current EvidenceRecord"
        )
    if receipt.resolved_at != evidence.recorded_at:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "resolution receipt resolved_at does not match EvidenceRecord recorded_at"
        )
