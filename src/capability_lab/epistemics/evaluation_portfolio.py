"""PR11.4 complete ClaimEvaluation portfolio admissibility governance v1."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from capability_lab.semantics import CapabilityConceptRef

from .core import (
    CapabilityClaimId,
    CapabilitySubjectRef,
    ClaimEvaluationId,
    EpistemicError,
    canonical_time,
)
from .record_set import EpistemicRecordSet
from .snapshot_transition import epistemic_snapshot_sha256_v1


class ClaimEvaluationPortfolioError(EpistemicError):
    """Base error for complete ClaimEvaluation portfolio governance."""


class InvalidClaimEvaluationPortfolio(ClaimEvaluationPortfolioError):
    """The supplied portfolio or selection violates complete admissibility."""


_SHA256_HEX_DIGITS = frozenset("0123456789abcdef")


def _validate_sha256(value: object, field_name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in _SHA256_HEX_DIGITS for character in value)
    ):
        raise InvalidClaimEvaluationPortfolio(
            f"{field_name} must be 64 lowercase hexadecimal SHA-256 characters"
        )
    return value


def _canonical_portfolio_time(value: object, field_name: str) -> datetime:
    try:
        return canonical_time(value, field_name)
    except EpistemicError as exc:
        raise InvalidClaimEvaluationPortfolio(str(exc)) from exc


def _validated_id_tuple(
    value: object,
    item_type: type,
    field_name: str,
) -> tuple:
    if isinstance(value, (str, bytes)):
        raise InvalidClaimEvaluationPortfolio(
            f"{field_name} must be an iterable of typed ids"
        )
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise InvalidClaimEvaluationPortfolio(
            f"{field_name} must be iterable"
        ) from exc
    if any(not isinstance(item, item_type) for item in items):
        raise InvalidClaimEvaluationPortfolio(
            f"{field_name} contains an invalid typed id"
        )
    if len(set(items)) != len(items):
        raise InvalidClaimEvaluationPortfolio(
            f"{field_name} must not contain duplicate ids"
        )
    return tuple(sorted(items))


@dataclass(frozen=True, slots=True)
class ClaimEvaluationPortfolioEntry:
    """One in-scope claim and every admissible evaluation identity for that claim."""

    claim_id: CapabilityClaimId
    evaluation_ids: tuple[ClaimEvaluationId, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.claim_id, CapabilityClaimId):
            raise InvalidClaimEvaluationPortfolio(
                "portfolio entry claim_id must be CapabilityClaimId"
            )
        object.__setattr__(
            self,
            "evaluation_ids",
            _validated_id_tuple(
                self.evaluation_ids,
                ClaimEvaluationId,
                "portfolio entry evaluation_ids",
            ),
        )


@dataclass(frozen=True, slots=True)
class ClaimEvaluationPortfolioReceipt:
    """Structural complete-portfolio receipt; validator origin is explicit."""

    snapshot_sha256: str
    subject_ref: CapabilitySubjectRef
    concept_ref: CapabilityConceptRef
    as_of: datetime
    entries: tuple[ClaimEvaluationPortfolioEntry, ...] = ()
    excluded_future_claim_ids: tuple[CapabilityClaimId, ...] = ()
    excluded_future_evaluation_ids: tuple[ClaimEvaluationId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "snapshot_sha256",
            _validate_sha256(self.snapshot_sha256, "snapshot_sha256"),
        )
        if not isinstance(self.subject_ref, CapabilitySubjectRef):
            raise InvalidClaimEvaluationPortfolio(
                "subject_ref must be CapabilitySubjectRef"
            )
        if not isinstance(self.concept_ref, CapabilityConceptRef):
            raise InvalidClaimEvaluationPortfolio(
                "concept_ref must be exact CapabilityConceptRef"
            )
        object.__setattr__(
            self,
            "as_of",
            _canonical_portfolio_time(self.as_of, "portfolio as_of"),
        )

        if isinstance(self.entries, (str, bytes)):
            raise InvalidClaimEvaluationPortfolio(
                "entries must be an iterable of ClaimEvaluationPortfolioEntry values"
            )
        try:
            entries = tuple(self.entries)
        except TypeError as exc:
            raise InvalidClaimEvaluationPortfolio(
                "entries must be iterable"
            ) from exc
        if any(not isinstance(item, ClaimEvaluationPortfolioEntry) for item in entries):
            raise InvalidClaimEvaluationPortfolio(
                "entries must contain ClaimEvaluationPortfolioEntry values"
            )
        claim_ids = tuple(item.claim_id for item in entries)
        if len(set(claim_ids)) != len(claim_ids):
            raise InvalidClaimEvaluationPortfolio(
                "portfolio entries must not contain duplicate claim ids"
            )
        evaluation_ids = tuple(
            evaluation_id
            for entry in entries
            for evaluation_id in entry.evaluation_ids
        )
        if len(set(evaluation_ids)) != len(evaluation_ids):
            raise InvalidClaimEvaluationPortfolio(
                "portfolio evaluation ids must belong to exactly one claim entry"
            )
        entries = tuple(sorted(entries, key=lambda item: item.claim_id))
        object.__setattr__(self, "entries", entries)

        future_claim_ids = _validated_id_tuple(
            self.excluded_future_claim_ids,
            CapabilityClaimId,
            "excluded_future_claim_ids",
        )
        future_evaluation_ids = _validated_id_tuple(
            self.excluded_future_evaluation_ids,
            ClaimEvaluationId,
            "excluded_future_evaluation_ids",
        )
        if set(claim_ids) & set(future_claim_ids):
            raise InvalidClaimEvaluationPortfolio(
                "admissible and excluded future claim ids must be disjoint"
            )
        if set(evaluation_ids) & set(future_evaluation_ids):
            raise InvalidClaimEvaluationPortfolio(
                "admissible and excluded future evaluation ids must be disjoint"
            )
        object.__setattr__(
            self,
            "excluded_future_claim_ids",
            future_claim_ids,
        )
        object.__setattr__(
            self,
            "excluded_future_evaluation_ids",
            future_evaluation_ids,
        )

    @property
    def claim_ids(self) -> tuple[CapabilityClaimId, ...]:
        return tuple(entry.claim_id for entry in self.entries)

    @property
    def admissible_evaluation_ids(self) -> tuple[ClaimEvaluationId, ...]:
        return tuple(
            sorted(
                evaluation_id
                for entry in self.entries
                for evaluation_id in entry.evaluation_ids
            )
        )

    @property
    def unevaluated_claim_ids(self) -> tuple[CapabilityClaimId, ...]:
        return tuple(
            entry.claim_id
            for entry in self.entries
            if not entry.evaluation_ids
        )

    @property
    def validator_issued(self) -> bool:
        """Whether this instance has the exact private PR11.4 builder receipt type."""

        return type(self) is _ValidatorIssuedClaimEvaluationPortfolioReceipt


class _ValidatorIssuedClaimEvaluationPortfolioReceipt(
    ClaimEvaluationPortfolioReceipt
):
    """Private marker subclass used only by the complete-portfolio builder."""

    __slots__ = ()


def build_complete_claim_evaluation_portfolio_v1(
    *,
    records: EpistemicRecordSet,
    subject_ref: CapabilitySubjectRef,
    concept_ref: CapabilityConceptRef,
    as_of: datetime,
) -> ClaimEvaluationPortfolioReceipt:
    """Build the complete in-scope ClaimEvaluation portfolio for one snapshot.

    Membership is determined only by exact subject, exact concept revision, and
    inclusive temporal scope. Conclusion, evaluator identity/kind, policy,
    reliability, coverage, and conflict state do not filter membership.
    """

    if not isinstance(records, EpistemicRecordSet):
        raise InvalidClaimEvaluationPortfolio(
            "records must be EpistemicRecordSet"
        )
    if not isinstance(subject_ref, CapabilitySubjectRef):
        raise InvalidClaimEvaluationPortfolio(
            "subject_ref must be CapabilitySubjectRef"
        )
    if not isinstance(concept_ref, CapabilityConceptRef):
        raise InvalidClaimEvaluationPortfolio(
            "concept_ref must be exact CapabilityConceptRef"
        )
    boundary = _canonical_portfolio_time(as_of, "portfolio as_of")

    matching_claims = tuple(
        claim
        for claim in records.claims
        if claim.subject_ref == subject_ref and claim.concept_ref == concept_ref
    )
    matching_claim_ids = {claim.claim_id for claim in matching_claims}
    admissible_claims = tuple(
        claim for claim in matching_claims if claim.created_at <= boundary
    )
    excluded_future_claim_ids = tuple(
        sorted(
            claim.claim_id
            for claim in matching_claims
            if claim.created_at > boundary
        )
    )

    admissible_evaluations_by_claim: dict[
        CapabilityClaimId,
        list[ClaimEvaluationId],
    ] = {claim.claim_id: [] for claim in admissible_claims}
    excluded_future_evaluation_ids: list[ClaimEvaluationId] = []
    for evaluation in records.evaluations:
        if evaluation.claim_id not in matching_claim_ids:
            continue
        if evaluation.evaluated_at > boundary:
            excluded_future_evaluation_ids.append(evaluation.evaluation_id)
            continue
        if evaluation.claim_id in admissible_evaluations_by_claim:
            admissible_evaluations_by_claim[evaluation.claim_id].append(
                evaluation.evaluation_id
            )

    entries = tuple(
        ClaimEvaluationPortfolioEntry(
            claim_id=claim.claim_id,
            evaluation_ids=tuple(
                sorted(admissible_evaluations_by_claim[claim.claim_id])
            ),
        )
        for claim in admissible_claims
    )

    return _ValidatorIssuedClaimEvaluationPortfolioReceipt(
        snapshot_sha256=epistemic_snapshot_sha256_v1(records),
        subject_ref=subject_ref,
        concept_ref=concept_ref,
        as_of=boundary,
        entries=entries,
        excluded_future_claim_ids=excluded_future_claim_ids,
        excluded_future_evaluation_ids=tuple(
            sorted(excluded_future_evaluation_ids)
        ),
    )


def validate_exact_claim_evaluation_selection_v1(
    *,
    records: EpistemicRecordSet,
    portfolio: ClaimEvaluationPortfolioReceipt,
    selected_evaluation_ids: tuple[ClaimEvaluationId, ...],
) -> tuple[ClaimEvaluationId, ...]:
    """Require caller selection to equal the complete snapshot-bound portfolio."""

    if not isinstance(records, EpistemicRecordSet):
        raise InvalidClaimEvaluationPortfolio(
            "records must be EpistemicRecordSet"
        )
    if not isinstance(portfolio, ClaimEvaluationPortfolioReceipt):
        raise InvalidClaimEvaluationPortfolio(
            "portfolio must be ClaimEvaluationPortfolioReceipt"
        )
    if type(portfolio) is not _ValidatorIssuedClaimEvaluationPortfolioReceipt:
        raise InvalidClaimEvaluationPortfolio(
            "portfolio must be validator-issued"
        )
    if epistemic_snapshot_sha256_v1(records) != portfolio.snapshot_sha256:
        raise InvalidClaimEvaluationPortfolio(
            "portfolio snapshot does not match supplied EpistemicRecordSet"
        )

    expected = build_complete_claim_evaluation_portfolio_v1(
        records=records,
        subject_ref=portfolio.subject_ref,
        concept_ref=portfolio.concept_ref,
        as_of=portfolio.as_of,
    )
    if portfolio != expected:
        raise InvalidClaimEvaluationPortfolio(
            "portfolio content does not match complete records-derived portfolio"
        )

    selected = _validated_id_tuple(
        selected_evaluation_ids,
        ClaimEvaluationId,
        "selected_evaluation_ids",
    )
    admissible = expected.admissible_evaluation_ids

    missing = tuple(sorted(set(admissible) - set(selected)))
    if missing:
        raise InvalidClaimEvaluationPortfolio(
            f"selection omits admissible claim evaluation: {missing[0]}"
        )
    extra = tuple(sorted(set(selected) - set(admissible)))
    if extra:
        raise InvalidClaimEvaluationPortfolio(
            f"selection includes inadmissible claim evaluation: {extra[0]}"
        )
    return selected
