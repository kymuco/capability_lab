"""Immutable PR12.3 terminal-review ledger and append-only admission."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os

from capability_lab.epistemics import EpistemicRecordSet
from capability_lab.semantics import CapabilityCatalog

from .core import (
    ExternalEvidenceClaimInterpretationCandidate,
    InvalidExternalEvidenceInterpretation,
    _strict_candidate,
    external_evidence_claim_interpretation_candidate_sha256_v1,
)
from .review import (
    ExternalEvidenceClaimInterpretationReview,
    ExternalEvidenceInterpretationReviewVerdict,
    _strict_review,
    external_evidence_claim_interpretation_review_sha256_v1,
    validate_external_evidence_claim_interpretation_review_v1,
)

_LEDGER_HASH_DOMAIN = (
    b"capability_lab/external_evidence_claim_interpretation_review_ledger@1\x00"
)

# Runtime-only terminal-review admission registry. Review/ledger values remain
# canonical serializable audit artifacts; structural equality with an admitted
# ledger does not grant authority. Each issuance entry keeps a strong reference
# to the exact ledger object and binds the issuing process, exact current ledger,
# exact predecessor -> one-review transition, candidate, and review identities.
#
# Crossing a process boundary never restores this authority implicitly. A POSIX
# fork inherits Python memory, but the recorded issuer pid no longer equals
# os.getpid() in the child. Canonical audit data can regain child-local authority
# only by explicit replay through admit_external_evidence_claim_interpretation_review_v1.
_ISSUED_TERMINAL_REVIEW_AUTHORITIES: dict[
    tuple[int, str],
    tuple[
        "ExternalEvidenceInterpretationReviewLedger",
        int,
        str,
        str,
        str,
        str,
        str,
        object,
    ],
] = {}


@dataclass(frozen=True, slots=True)
class ExternalEvidenceInterpretationReviewLedger:
    """One immutable structural review lineage; not admission authority by itself."""

    reviews: tuple[ExternalEvidenceClaimInterpretationReview, ...] = ()

    def __post_init__(self) -> None:
        if type(self.reviews) is not tuple:
            raise InvalidExternalEvidenceInterpretation(
                "review ledger reviews must use exact tuple"
            )
        seen_review_ids = set()
        seen_proposal_ids = set()
        for review in self.reviews:
            _strict_review(review)
            if review.review_id in seen_review_ids:
                raise InvalidExternalEvidenceInterpretation(
                    f"duplicate review_id in review ledger: {review.review_id}"
                )
            if review.proposal_id in seen_proposal_ids:
                raise InvalidExternalEvidenceInterpretation(
                    f"proposal already has a terminal review in ledger: {review.proposal_id}"
                )
            seen_review_ids.add(review.review_id)
            seen_proposal_ids.add(review.proposal_id)

    def to_dict(self) -> dict:
        from .review_serialization import (
            external_evidence_claim_interpretation_review_ledger_to_dict,
        )

        return external_evidence_claim_interpretation_review_ledger_to_dict(self)

    @classmethod
    def from_dict(cls, payload: object) -> "ExternalEvidenceInterpretationReviewLedger":
        from .review_serialization import (
            external_evidence_claim_interpretation_review_ledger_from_dict,
        )

        return external_evidence_claim_interpretation_review_ledger_from_dict(payload)

    def to_json(self) -> str:
        from .review_serialization import (
            external_evidence_claim_interpretation_review_ledger_to_json,
        )

        return external_evidence_claim_interpretation_review_ledger_to_json(self)

    @classmethod
    def from_json(cls, payload: object) -> "ExternalEvidenceInterpretationReviewLedger":
        from .review_serialization import (
            external_evidence_claim_interpretation_review_ledger_from_json,
        )

        return external_evidence_claim_interpretation_review_ledger_from_json(payload)


def _strict_review_ledger(
    ledger: ExternalEvidenceInterpretationReviewLedger,
) -> ExternalEvidenceInterpretationReviewLedger:
    if type(ledger) is not ExternalEvidenceInterpretationReviewLedger:
        raise InvalidExternalEvidenceInterpretation(
            "review_ledger must use exact ExternalEvidenceInterpretationReviewLedger"
        )
    restored = ExternalEvidenceInterpretationReviewLedger(reviews=tuple(ledger.reviews))
    if restored != ledger:
        raise InvalidExternalEvidenceInterpretation(
            "review_ledger must equal strict semantic reconstruction"
        )
    return ledger


def external_evidence_claim_interpretation_review_ledger_sha256_v1(
    ledger: ExternalEvidenceInterpretationReviewLedger,
) -> str:
    _strict_review_ledger(ledger)
    from .review_serialization import (
        external_evidence_claim_interpretation_review_ledger_to_json,
    )

    digest = hashlib.sha256()
    digest.update(_LEDGER_HASH_DOMAIN)
    digest.update(
        external_evidence_claim_interpretation_review_ledger_to_json(ledger).encode("utf-8")
    )
    return digest.hexdigest()


def validate_external_evidence_interpretation_review_ledger_successor_v1(
    previous: ExternalEvidenceInterpretationReviewLedger,
    current: ExternalEvidenceInterpretationReviewLedger,
) -> None:
    """Require exact append-only succession for one review-ledger lineage."""

    previous = _strict_review_ledger(previous)
    current = _strict_review_ledger(current)
    if len(current.reviews) < len(previous.reviews):
        raise InvalidExternalEvidenceInterpretation(
            "review ledger successor may not remove prior terminal reviews"
        )
    if current.reviews[: len(previous.reviews)] != previous.reviews:
        raise InvalidExternalEvidenceInterpretation(
            "review ledger successor must preserve the exact prior review prefix"
        )


def _authority_key(
    ledger: ExternalEvidenceInterpretationReviewLedger,
    review: ExternalEvidenceClaimInterpretationReview,
) -> tuple[int, str]:
    return (id(ledger), str(review.proposal_id))


def _terminal_review_transition_basis(
    *,
    review_ledger: ExternalEvidenceInterpretationReviewLedger,
    review: ExternalEvidenceClaimInterpretationReview,
) -> tuple[
    ExternalEvidenceInterpretationReviewLedger,
    ExternalEvidenceInterpretationReviewLedger,
]:
    """Reconstruct the exact predecessor -> one-review terminal transition."""

    review_ledger = _strict_review_ledger(review_ledger)
    review = _strict_review(review)
    matches = tuple(
        (index, existing)
        for index, existing in enumerate(review_ledger.reviews)
        if existing.proposal_id == review.proposal_id
    )
    if len(matches) != 1:
        raise InvalidExternalEvidenceInterpretation(
            "terminal review authority requires one exact proposal review in ledger"
        )
    index, existing = matches[0]
    if existing != review:
        raise InvalidExternalEvidenceInterpretation(
            "terminal review authority review does not equal exact ledger review"
        )
    predecessor = ExternalEvidenceInterpretationReviewLedger(
        reviews=review_ledger.reviews[:index]
    )
    transition_successor = ExternalEvidenceInterpretationReviewLedger(
        reviews=review_ledger.reviews[: index + 1]
    )
    validate_external_evidence_interpretation_review_ledger_successor_v1(
        predecessor,
        transition_successor,
    )
    if len(transition_successor.reviews) != len(predecessor.reviews) + 1:
        raise InvalidExternalEvidenceInterpretation(
            "terminal review authority must bind an exact one-review append transition"
        )
    if transition_successor.reviews[-1] != review:
        raise InvalidExternalEvidenceInterpretation(
            "terminal review authority transition must append the exact review"
        )
    if review_ledger.reviews[: len(transition_successor.reviews)] != (
        transition_successor.reviews
    ):
        raise InvalidExternalEvidenceInterpretation(
            "current review ledger must preserve the admitted terminal transition prefix"
        )
    return predecessor, transition_successor


def _issue_terminal_review_authority(
    *,
    review_ledger: ExternalEvidenceInterpretationReviewLedger,
    candidate: ExternalEvidenceClaimInterpretationCandidate,
    review: ExternalEvidenceClaimInterpretationReview,
) -> None:
    review_ledger = _strict_review_ledger(review_ledger)
    candidate = _strict_candidate(candidate)
    review = _strict_review(review)
    predecessor, transition_successor = _terminal_review_transition_basis(
        review_ledger=review_ledger,
        review=review,
    )
    _ISSUED_TERMINAL_REVIEW_AUTHORITIES[_authority_key(review_ledger, review)] = (
        review_ledger,
        os.getpid(),
        external_evidence_claim_interpretation_review_ledger_sha256_v1(review_ledger),
        external_evidence_claim_interpretation_review_ledger_sha256_v1(predecessor),
        external_evidence_claim_interpretation_review_ledger_sha256_v1(
            transition_successor
        ),
        external_evidence_claim_interpretation_candidate_sha256_v1(candidate),
        external_evidence_claim_interpretation_review_sha256_v1(review),
        review.review_id,
    )


def _require_terminal_review_authority(
    *,
    review_ledger: ExternalEvidenceInterpretationReviewLedger,
    candidate: ExternalEvidenceClaimInterpretationCandidate,
    review: ExternalEvidenceClaimInterpretationReview,
) -> None:
    review_ledger = _strict_review_ledger(review_ledger)
    candidate = _strict_candidate(candidate)
    review = _strict_review(review)
    issued = _ISSUED_TERMINAL_REVIEW_AUTHORITIES.get(
        _authority_key(review_ledger, review)
    )
    if issued is None or issued[0] is not review_ledger:
        raise InvalidExternalEvidenceInterpretation(
            "terminal review ledger has no runtime admission authority for this exact proposal; "
            "replay admit_external_evidence_claim_interpretation_review_v1 first"
        )
    if issued[1] != os.getpid():
        raise InvalidExternalEvidenceInterpretation(
            "terminal review admission authority belongs to a different process"
        )
    if issued[2] != external_evidence_claim_interpretation_review_ledger_sha256_v1(
        review_ledger
    ):
        raise InvalidExternalEvidenceInterpretation(
            "terminal review admission authority is stale for the supplied review ledger"
        )
    predecessor, transition_successor = _terminal_review_transition_basis(
        review_ledger=review_ledger,
        review=review,
    )
    if issued[3] != external_evidence_claim_interpretation_review_ledger_sha256_v1(
        predecessor
    ):
        raise InvalidExternalEvidenceInterpretation(
            "terminal review admission predecessor digest mismatch"
        )
    if issued[4] != external_evidence_claim_interpretation_review_ledger_sha256_v1(
        transition_successor
    ):
        raise InvalidExternalEvidenceInterpretation(
            "terminal review admission transition-successor digest mismatch"
        )
    if issued[5] != external_evidence_claim_interpretation_candidate_sha256_v1(candidate):
        raise InvalidExternalEvidenceInterpretation(
            "terminal review admission authority candidate digest mismatch"
        )
    if issued[6] != external_evidence_claim_interpretation_review_sha256_v1(review):
        raise InvalidExternalEvidenceInterpretation(
            "terminal review admission authority review digest mismatch"
        )
    if issued[7] != review.review_id:
        raise InvalidExternalEvidenceInterpretation(
            "terminal review admission authority review id mismatch"
        )


def admit_external_evidence_claim_interpretation_review_v1(
    *,
    review_ledger: ExternalEvidenceInterpretationReviewLedger,
    epistemic_snapshot: EpistemicRecordSet,
    catalog: CapabilityCatalog,
    candidate: ExternalEvidenceClaimInterpretationCandidate,
    review: ExternalEvidenceClaimInterpretationReview,
) -> ExternalEvidenceInterpretationReviewLedger:
    """Append/replay one review and issue process-local terminal-review authority."""

    review_ledger = _strict_review_ledger(review_ledger)
    candidate = _strict_candidate(candidate)
    review = _strict_review(review)
    validate_external_evidence_claim_interpretation_review_v1(
        epistemic_snapshot=epistemic_snapshot,
        catalog=catalog,
        candidate=candidate,
        review=review,
    )

    for existing in review_ledger.reviews:
        if existing.proposal_id == review.proposal_id:
            if existing == review:
                _issue_terminal_review_authority(
                    review_ledger=review_ledger,
                    candidate=candidate,
                    review=review,
                )
                return review_ledger
            raise InvalidExternalEvidenceInterpretation(
                "proposal already has a different terminal review in this ledger lineage"
            )
        if existing.review_id == review.review_id:
            raise InvalidExternalEvidenceInterpretation(
                "review_id is already bound to a different proposal"
            )

    successor = ExternalEvidenceInterpretationReviewLedger(
        reviews=review_ledger.reviews + (review,)
    )
    validate_external_evidence_interpretation_review_ledger_successor_v1(
        review_ledger,
        successor,
    )
    _issue_terminal_review_authority(
        review_ledger=successor,
        candidate=candidate,
        review=review,
    )
    return successor


def resolve_external_evidence_claim_interpretation_terminal_review_v1(
    *,
    review_ledger: ExternalEvidenceInterpretationReviewLedger,
    epistemic_snapshot: EpistemicRecordSet,
    catalog: CapabilityCatalog,
    candidate: ExternalEvidenceClaimInterpretationCandidate,
) -> ExternalEvidenceClaimInterpretationReview:
    """Structurally resolve one review from audit data; this grants no authority."""

    review_ledger = _strict_review_ledger(review_ledger)
    candidate = _strict_candidate(candidate)
    matches = tuple(
        review
        for review in review_ledger.reviews
        if review.proposal_id == candidate.proposal_id
    )
    if len(matches) != 1:
        raise InvalidExternalEvidenceInterpretation(
            "candidate proposal has no exact terminal review in supplied ledger"
        )
    review = matches[0]
    validate_external_evidence_claim_interpretation_review_v1(
        epistemic_snapshot=epistemic_snapshot,
        catalog=catalog,
        candidate=candidate,
        review=review,
    )
    return review


def require_accepted_external_evidence_claim_interpretation_review_v1(
    *,
    review_ledger: ExternalEvidenceInterpretationReviewLedger,
    epistemic_snapshot: EpistemicRecordSet,
    catalog: CapabilityCatalog,
    candidate: ExternalEvidenceClaimInterpretationCandidate,
) -> ExternalEvidenceClaimInterpretationReview:
    """Require process-local terminal admission plus the exact ACCEPT verdict."""

    review = resolve_external_evidence_claim_interpretation_terminal_review_v1(
        review_ledger=review_ledger,
        epistemic_snapshot=epistemic_snapshot,
        catalog=catalog,
        candidate=candidate,
    )
    _require_terminal_review_authority(
        review_ledger=review_ledger,
        candidate=candidate,
        review=review,
    )
    if review.verdict is not ExternalEvidenceInterpretationReviewVerdict.ACCEPT:
        raise InvalidExternalEvidenceInterpretation(
            "candidate proposal terminal review is REJECT, not ACCEPT"
        )
    return review
