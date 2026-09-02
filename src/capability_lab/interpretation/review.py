"""PR12.3 explicit human review of external evidence claim-interpretation proposals."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import hashlib

from capability_lab.epistemics import EpistemicRecordSet
from capability_lab.semantics import CapabilityCatalog

from .core import (
    ExternalEvidenceClaimInterpretationCandidate,
    ExternalEvidenceInterpretationPolicyRef,
    ExternalEvidenceInterpretationProposalId,
    InvalidExternalEvidenceInterpretation,
    _exact,
    _opaque_id,
    _sha256,
    _strict_candidate,
    _text,
    _time,
    external_evidence_claim_interpretation_candidate_sha256_v1,
    validate_external_evidence_claim_interpretation_candidate_v1,
)

_REVIEW_HASH_DOMAIN = b"capability_lab/external_evidence_claim_interpretation_review@1\x00"


@dataclass(frozen=True, order=True, slots=True)
class ExternalEvidenceInterpretationReviewId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _opaque_id(self.value, "review id"))

    def __str__(self) -> str:
        return self.value


EXTERNAL_EVIDENCE_CLAIM_INTERPRETATION_HUMAN_REVIEW_POLICY_V1 = (
    ExternalEvidenceInterpretationPolicyRef(
        "capability_lab", "external_evidence_claim_interpretation_human_review", 1
    )
)


class ExternalEvidenceInterpretationReviewerKind(str, Enum):
    HUMAN = "HUMAN"


@dataclass(frozen=True, order=True, slots=True)
class ExternalEvidenceInterpretationReviewerRef:
    kind: ExternalEvidenceInterpretationReviewerKind
    ref: str

    def __post_init__(self) -> None:
        _exact(self.kind, ExternalEvidenceInterpretationReviewerKind, "reviewer kind")
        if self.kind is not ExternalEvidenceInterpretationReviewerKind.HUMAN:
            raise InvalidExternalEvidenceInterpretation(
                "PR12.3 v1 requires an explicitly declared human reviewer"
            )
        object.__setattr__(self, "ref", _opaque_id(self.ref, "reviewer ref"))


class ExternalEvidenceInterpretationReviewVerdict(str, Enum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"


@dataclass(frozen=True, slots=True)
class ExternalEvidenceClaimInterpretationReview:
    review_id: ExternalEvidenceInterpretationReviewId
    policy_ref: ExternalEvidenceInterpretationPolicyRef
    proposal_id: ExternalEvidenceInterpretationProposalId
    candidate_sha256: str
    reviewer_ref: ExternalEvidenceInterpretationReviewerRef
    verdict: ExternalEvidenceInterpretationReviewVerdict
    reviewed_at: datetime
    rationale: str

    def __post_init__(self) -> None:
        _exact(self.review_id, ExternalEvidenceInterpretationReviewId, "review_id")
        if self.policy_ref != EXTERNAL_EVIDENCE_CLAIM_INTERPRETATION_HUMAN_REVIEW_POLICY_V1:
            raise InvalidExternalEvidenceInterpretation(
                "review must use the frozen PR12.3 human-review policy"
            )
        _exact(self.proposal_id, ExternalEvidenceInterpretationProposalId, "proposal_id")
        object.__setattr__(
            self,
            "candidate_sha256",
            _sha256(self.candidate_sha256, "candidate_sha256"),
        )
        _exact(
            self.reviewer_ref,
            ExternalEvidenceInterpretationReviewerRef,
            "reviewer_ref",
        )
        _exact(self.verdict, ExternalEvidenceInterpretationReviewVerdict, "verdict")
        object.__setattr__(self, "reviewed_at", _time(self.reviewed_at, "reviewed_at"))
        object.__setattr__(self, "rationale", _text(self.rationale, "review rationale"))


def _strict_review(
    review: ExternalEvidenceClaimInterpretationReview,
) -> ExternalEvidenceClaimInterpretationReview:
    if type(review) is not ExternalEvidenceClaimInterpretationReview:
        raise InvalidExternalEvidenceInterpretation(
            "review must use exact ExternalEvidenceClaimInterpretationReview"
        )
    try:
        restored = ExternalEvidenceClaimInterpretationReview(
            review_id=ExternalEvidenceInterpretationReviewId(review.review_id.value),
            policy_ref=ExternalEvidenceInterpretationPolicyRef(
                review.policy_ref.namespace,
                review.policy_ref.key,
                review.policy_ref.revision,
            ),
            proposal_id=ExternalEvidenceInterpretationProposalId(review.proposal_id.value),
            candidate_sha256=review.candidate_sha256,
            reviewer_ref=ExternalEvidenceInterpretationReviewerRef(
                ExternalEvidenceInterpretationReviewerKind(review.reviewer_ref.kind.value),
                review.reviewer_ref.ref,
            ),
            verdict=ExternalEvidenceInterpretationReviewVerdict(review.verdict.value),
            reviewed_at=review.reviewed_at,
            rationale=review.rationale,
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InvalidExternalEvidenceInterpretation):
            raise
        raise InvalidExternalEvidenceInterpretation(
            f"review failed strict semantic reconstruction: {exc}"
        ) from exc
    if restored != review:
        raise InvalidExternalEvidenceInterpretation(
            "review must equal strict semantic reconstruction"
        )
    return review


def external_evidence_claim_interpretation_review_sha256_v1(
    review: ExternalEvidenceClaimInterpretationReview,
) -> str:
    _strict_review(review)
    from .review_serialization import external_evidence_claim_interpretation_review_to_json

    digest = hashlib.sha256()
    digest.update(_REVIEW_HASH_DOMAIN)
    digest.update(external_evidence_claim_interpretation_review_to_json(review).encode("utf-8"))
    return digest.hexdigest()


def validate_external_evidence_claim_interpretation_review_v1(
    *,
    epistemic_snapshot: EpistemicRecordSet,
    catalog: CapabilityCatalog,
    candidate: ExternalEvidenceClaimInterpretationCandidate,
    review: ExternalEvidenceClaimInterpretationReview,
) -> None:
    _strict_candidate(candidate)
    _strict_review(review)
    validate_external_evidence_claim_interpretation_candidate_v1(
        epistemic_snapshot=epistemic_snapshot,
        catalog=catalog,
        candidate=candidate,
    )
    candidate_sha256 = external_evidence_claim_interpretation_candidate_sha256_v1(
        candidate
    )
    if review.proposal_id != candidate.proposal_id:
        raise InvalidExternalEvidenceInterpretation(
            "review proposal_id does not match candidate proposal_id"
        )
    if review.candidate_sha256 != candidate_sha256:
        raise InvalidExternalEvidenceInterpretation(
            "review candidate_sha256 does not match exact candidate"
        )
    if review.reviewed_at < candidate.proposed_at:
        raise InvalidExternalEvidenceInterpretation(
            "reviewed_at must not precede candidate proposed_at"
        )


def review_external_evidence_claim_interpretation_v1(
    *,
    epistemic_snapshot: EpistemicRecordSet,
    catalog: CapabilityCatalog,
    candidate: ExternalEvidenceClaimInterpretationCandidate,
    review_id: ExternalEvidenceInterpretationReviewId,
    reviewer_ref: ExternalEvidenceInterpretationReviewerRef,
    verdict: ExternalEvidenceInterpretationReviewVerdict,
    reviewed_at: datetime,
    rationale: str,
) -> ExternalEvidenceClaimInterpretationReview:
    """Human-review one exact PR12.2 candidate without creating claim authority."""

    validate_external_evidence_claim_interpretation_candidate_v1(
        epistemic_snapshot=epistemic_snapshot,
        catalog=catalog,
        candidate=candidate,
    )
    reviewed = _time(reviewed_at, "reviewed_at")
    if reviewed < candidate.proposed_at:
        raise InvalidExternalEvidenceInterpretation(
            "reviewed_at must not precede candidate proposed_at"
        )
    try:
        review = ExternalEvidenceClaimInterpretationReview(
            review_id=review_id,
            policy_ref=EXTERNAL_EVIDENCE_CLAIM_INTERPRETATION_HUMAN_REVIEW_POLICY_V1,
            proposal_id=candidate.proposal_id,
            candidate_sha256=external_evidence_claim_interpretation_candidate_sha256_v1(
                candidate
            ),
            reviewer_ref=reviewer_ref,
            verdict=verdict,
            reviewed_at=reviewed,
            rationale=rationale,
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InvalidExternalEvidenceInterpretation):
            raise
        raise InvalidExternalEvidenceInterpretation(
            f"cannot construct interpretation review: {exc}"
        ) from exc
    validate_external_evidence_claim_interpretation_review_v1(
        epistemic_snapshot=epistemic_snapshot,
        catalog=catalog,
        candidate=candidate,
        review=review,
    )
    return review
