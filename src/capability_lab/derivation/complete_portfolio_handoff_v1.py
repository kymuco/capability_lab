"""PR11.5 complete-portfolio-to-state governed handoff v1."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from capability_lab.epistemics import (
    ClaimEvaluationPortfolioReceipt,
    EpistemicRecordSet,
    InvalidClaimEvaluationPortfolio,
    validate_exact_claim_evaluation_selection_v1,
)
from capability_lab.epistemics.core import EpistemicError, canonical_time
from capability_lab.state import (
    CompetenceFrame,
    PersonalCapabilityState,
    PersonalCapabilityStateId,
)

from .deterministic_v1 import (
    ClaimDimensionBinding,
    DeterministicStateDerivationRequest,
    StateDerivationError,
    derive_supported_state_v1,
)


class CompletePortfolioStateDerivationError(StateDerivationError):
    """The PR11.5 governed handoff cannot authorize deterministic derivation."""


@dataclass(frozen=True, slots=True)
class CompletePortfolioStateDerivationRequest:
    """Caller inputs not already fixed by the exact PR11.4 portfolio scope."""

    state_id: PersonalCapabilityStateId
    derived_at: datetime
    claim_dimension_bindings: tuple[ClaimDimensionBinding, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.state_id, PersonalCapabilityStateId):
            raise CompletePortfolioStateDerivationError(
                "state_id must be PersonalCapabilityStateId"
            )
        try:
            derived_at = canonical_time(
                self.derived_at,
                "complete portfolio derivation derived_at",
            )
        except EpistemicError as exc:
            raise CompletePortfolioStateDerivationError(str(exc)) from exc

        if isinstance(self.claim_dimension_bindings, (str, bytes)):
            raise CompletePortfolioStateDerivationError(
                "claim_dimension_bindings must be an iterable"
            )
        try:
            bindings = tuple(self.claim_dimension_bindings)
        except TypeError as exc:
            raise CompletePortfolioStateDerivationError(
                "claim_dimension_bindings must be iterable"
            ) from exc
        if any(not isinstance(item, ClaimDimensionBinding) for item in bindings):
            raise CompletePortfolioStateDerivationError(
                "claim_dimension_bindings must contain ClaimDimensionBinding values"
            )
        binding_claim_ids = tuple(item.claim_id for item in bindings)
        if len(set(binding_claim_ids)) != len(binding_claim_ids):
            raise CompletePortfolioStateDerivationError(
                "each claim may have at most one claim-dimension binding per request"
            )

        object.__setattr__(self, "derived_at", derived_at)
        object.__setattr__(
            self,
            "claim_dimension_bindings",
            tuple(sorted(bindings, key=lambda item: item.claim_id)),
        )


def _validated_complete_evaluation_basis(
    *,
    records: EpistemicRecordSet,
    portfolio: ClaimEvaluationPortfolioReceipt,
) -> tuple:
    """Revalidate PR11.4 content authority and return its exact complete basis."""

    try:
        return validate_exact_claim_evaluation_selection_v1(
            records=records,
            portfolio=portfolio,
            selected_evaluation_ids=portfolio.admissible_evaluation_ids,
        )
    except (AttributeError, InvalidClaimEvaluationPortfolio) as exc:
        raise CompletePortfolioStateDerivationError(
            f"invalid complete evaluation portfolio: {exc}"
        ) from exc


def derive_supported_state_from_complete_portfolio_v1(
    *,
    records: EpistemicRecordSet,
    frame: CompetenceFrame,
    portfolio: ClaimEvaluationPortfolioReceipt,
    request: CompletePortfolioStateDerivationRequest,
) -> PersonalCapabilityState:
    """Derive PR4 state only from one complete, revalidated PR11.4 portfolio.

    PR11.5 grants no evaluator preference, binding-semantic authority, or new
    standing/conflict policy.  It closes admission only: every in-scope claim
    must be evaluable and bound, and every admissible evaluation must reach the
    existing deterministic PR4 primitive.
    """

    if not isinstance(records, EpistemicRecordSet):
        raise CompletePortfolioStateDerivationError(
            "records must be EpistemicRecordSet"
        )
    if not isinstance(frame, CompetenceFrame):
        raise CompletePortfolioStateDerivationError(
            "frame must be CompetenceFrame"
        )
    if not isinstance(portfolio, ClaimEvaluationPortfolioReceipt):
        raise CompletePortfolioStateDerivationError(
            "portfolio must be ClaimEvaluationPortfolioReceipt"
        )
    if not isinstance(request, CompletePortfolioStateDerivationRequest):
        raise CompletePortfolioStateDerivationError(
            "request must be CompletePortfolioStateDerivationRequest"
        )

    complete_evaluation_ids = _validated_complete_evaluation_basis(
        records=records,
        portfolio=portfolio,
    )

    if request.derived_at < portfolio.as_of:
        raise CompletePortfolioStateDerivationError(
            "derived_at must not precede complete portfolio as_of"
        )

    if portfolio.unevaluated_claim_ids:
        raise CompletePortfolioStateDerivationError(
            "complete portfolio contains unevaluated claim: "
            f"{portfolio.unevaluated_claim_ids[0]}"
        )

    portfolio_claim_ids = set(portfolio.claim_ids)
    binding_claim_ids = {
        binding.claim_id for binding in request.claim_dimension_bindings
    }

    missing_bindings = tuple(sorted(portfolio_claim_ids - binding_claim_ids))
    if missing_bindings:
        raise CompletePortfolioStateDerivationError(
            "complete portfolio claim is missing claim-dimension binding: "
            f"{missing_bindings[0]}"
        )

    extra_bindings = tuple(sorted(binding_claim_ids - portfolio_claim_ids))
    if extra_bindings:
        raise CompletePortfolioStateDerivationError(
            "claim-dimension binding references non-portfolio claim: "
            f"{extra_bindings[0]}"
        )

    frame_dimension_keys = {dimension.key for dimension in frame.dimensions}
    for binding in request.claim_dimension_bindings:
        unknown_keys = tuple(
            sorted(set(binding.dimension_keys) - frame_dimension_keys)
        )
        if unknown_keys:
            raise CompletePortfolioStateDerivationError(
                "claim-dimension binding references dimension absent from exact frame: "
                f"{unknown_keys[0]}"
            )

    raw_request = DeterministicStateDerivationRequest(
        state_id=request.state_id,
        subject_ref=portfolio.subject_ref,
        concept_ref=portfolio.concept_ref,
        frame_ref=frame.ref,
        as_of=portfolio.as_of,
        derived_at=request.derived_at,
        selected_evaluation_ids=complete_evaluation_ids,
        claim_dimension_bindings=request.claim_dimension_bindings,
    )

    try:
        state = derive_supported_state_v1(
            records=records,
            frame=frame,
            request=raw_request,
        )
    except StateDerivationError as exc:
        raise CompletePortfolioStateDerivationError(
            f"deterministic state derivation rejected governed handoff: {exc}"
        ) from exc

    if state.state_id != request.state_id:
        raise CompletePortfolioStateDerivationError(
            "derived state state_id does not match governed request"
        )
    if state.subject_ref != portfolio.subject_ref:
        raise CompletePortfolioStateDerivationError(
            "derived state subject_ref does not match complete portfolio"
        )
    if state.concept_ref != portfolio.concept_ref:
        raise CompletePortfolioStateDerivationError(
            "derived state concept_ref does not match complete portfolio"
        )
    if state.frame_ref != frame.ref:
        raise CompletePortfolioStateDerivationError(
            "derived state frame_ref does not match exact supplied frame"
        )
    if state.as_of != portfolio.as_of:
        raise CompletePortfolioStateDerivationError(
            "derived state as_of does not match complete portfolio"
        )
    if state.derived_at != request.derived_at:
        raise CompletePortfolioStateDerivationError(
            "derived state derived_at does not match governed request"
        )

    output_evaluation_ids = {
        evaluation_id
        for dimension in state.dimensions
        for evaluation_id in dimension.basis_evaluation_ids
    }
    if output_evaluation_ids != set(complete_evaluation_ids):
        raise CompletePortfolioStateDerivationError(
            "derived state basis does not exactly preserve complete portfolio evaluations"
        )

    evaluations_by_id = {
        evaluation.evaluation_id: evaluation for evaluation in records.evaluations
    }
    for evaluation_id in output_evaluation_ids:
        if evaluation_id not in evaluations_by_id:
            raise CompletePortfolioStateDerivationError(
                "derived state basis references evaluation absent from supplied records: "
                f"{evaluation_id}"
            )

    complete_evaluations_by_claim = {
        entry.claim_id: set(entry.evaluation_ids) for entry in portfolio.entries
    }
    dimensions_by_key = {
        dimension.dimension_key: dimension for dimension in state.dimensions
    }
    for binding in request.claim_dimension_bindings:
        expected_claim_basis = complete_evaluations_by_claim[binding.claim_id]
        for dimension_key in binding.dimension_keys:
            dimension = dimensions_by_key.get(dimension_key)
            if dimension is None:
                raise CompletePortfolioStateDerivationError(
                    "derived state omits bound exact-frame dimension: "
                    f"{dimension_key}"
                )
            actual_claim_basis = {
                evaluation_id
                for evaluation_id in dimension.basis_evaluation_ids
                if evaluations_by_id[evaluation_id].claim_id == binding.claim_id
            }
            if actual_claim_basis != expected_claim_basis:
                raise CompletePortfolioStateDerivationError(
                    "derived state dimension does not preserve complete claim evaluation basis: "
                    f"{binding.claim_id} -> {dimension_key}"
                )

    reconstructed_dimensions_by_claim: dict[object, set[str]] = {}
    for dimension in state.dimensions:
        for evaluation_id in dimension.basis_evaluation_ids:
            evaluation = evaluations_by_id[evaluation_id]
            reconstructed_dimensions_by_claim.setdefault(
                evaluation.claim_id,
                set(),
            ).add(dimension.dimension_key)

    expected_dimensions_by_claim = {
        binding.claim_id: set(binding.dimension_keys)
        for binding in request.claim_dimension_bindings
    }
    if reconstructed_dimensions_by_claim != expected_dimensions_by_claim:
        raise CompletePortfolioStateDerivationError(
            "derived state basis does not exactly preserve complete claim-dimension bindings"
        )

    return state
