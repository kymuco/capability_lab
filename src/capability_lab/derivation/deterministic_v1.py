"""PR4 deterministic evaluation-to-supported-state baseline v1."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re

from capability_lab.epistemics import (
    CapabilityClaimId,
    CapabilitySubjectRef,
    ClaimEvaluationId,
    ConflictStatus as EvaluationConflictStatus,
    EpistemicRecordSet,
    EvaluationConclusion,
)
from capability_lab.epistemics.core import EpistemicError, canonical_time
from capability_lab.semantics import CapabilityConceptRef
from capability_lab.state import (
    CompetenceDimensionState,
    CompetenceFrame,
    CompetenceFrameCatalog,
    CompetenceFrameRef,
    DimensionConflictStatus,
    DimensionStanding,
    PersonalCapabilityState,
    PersonalCapabilityStateId,
    PersonalCapabilityStateSet,
    StateDerivationPolicyRef,
    StateDeriverKind,
    StateDeriverRef,
)


class StateDerivationError(ValueError):
    """Invalid input to the deterministic PR4 derivation baseline."""


_DIMENSION_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")


DETERMINISTIC_SUPPORTED_STATE_POLICY_V1 = StateDerivationPolicyRef.parse(
    "core:deterministic_supported_state@1"
)
DETERMINISTIC_SUPPORTED_STATE_DERIVER_V1 = StateDeriverRef(
    StateDeriverKind.RULE,
    "capability_lab:deterministic_supported_state_v1",
)


@dataclass(frozen=True, order=True, slots=True)
class ClaimDimensionBinding:
    """Explicit frame-scoped placement of one claim into one or more dimensions."""

    claim_id: CapabilityClaimId
    dimension_keys: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.claim_id, CapabilityClaimId):
            raise StateDerivationError("binding claim_id must be CapabilityClaimId")
        if isinstance(self.dimension_keys, (str, bytes)):
            raise StateDerivationError("binding dimension_keys must be an iterable")
        try:
            keys = tuple(self.dimension_keys)
        except TypeError as exc:
            raise StateDerivationError(
                "binding dimension_keys must be iterable"
            ) from exc
        if not keys:
            raise StateDerivationError(
                "claim-dimension binding requires at least one dimension key"
            )
        if any(
            not isinstance(key, str) or _DIMENSION_KEY_RE.fullmatch(key) is None
            for key in keys
        ):
            raise StateDerivationError(
                "binding dimension keys must use canonical lowercase key syntax"
            )
        if len(set(keys)) != len(keys):
            raise StateDerivationError(
                "duplicate dimension keys are not allowed in one claim binding"
            )
        object.__setattr__(self, "dimension_keys", tuple(sorted(keys)))


@dataclass(frozen=True, slots=True)
class DeterministicStateDerivationRequest:
    """All non-global inputs required for one pure deterministic derivation run."""

    state_id: PersonalCapabilityStateId
    subject_ref: CapabilitySubjectRef
    concept_ref: CapabilityConceptRef
    frame_ref: CompetenceFrameRef
    as_of: datetime
    derived_at: datetime
    selected_evaluation_ids: tuple[ClaimEvaluationId, ...] = ()
    claim_dimension_bindings: tuple[ClaimDimensionBinding, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.state_id, PersonalCapabilityStateId):
            raise StateDerivationError("state_id must be PersonalCapabilityStateId")
        if not isinstance(self.subject_ref, CapabilitySubjectRef):
            raise StateDerivationError("subject_ref must be CapabilitySubjectRef")
        if not isinstance(self.concept_ref, CapabilityConceptRef):
            raise StateDerivationError("concept_ref must be exact CapabilityConceptRef")
        if not isinstance(self.frame_ref, CompetenceFrameRef):
            raise StateDerivationError("frame_ref must be exact CompetenceFrameRef")
        try:
            as_of = canonical_time(self.as_of, "derivation as_of")
            derived_at = canonical_time(self.derived_at, "derivation derived_at")
        except EpistemicError as exc:
            raise StateDerivationError(str(exc)) from exc
        if derived_at < as_of:
            raise StateDerivationError("derived_at must not precede as_of")

        if isinstance(self.selected_evaluation_ids, (str, bytes)):
            raise StateDerivationError(
                "selected_evaluation_ids must be an iterable"
            )
        if isinstance(self.claim_dimension_bindings, (str, bytes)):
            raise StateDerivationError(
                "claim_dimension_bindings must be an iterable"
            )
        try:
            evaluation_ids = tuple(self.selected_evaluation_ids)
            bindings = tuple(self.claim_dimension_bindings)
        except TypeError as exc:
            raise StateDerivationError(
                "derivation selections and bindings must be iterable"
            ) from exc
        if any(not isinstance(item, ClaimEvaluationId) for item in evaluation_ids):
            raise StateDerivationError(
                "selected_evaluation_ids must contain ClaimEvaluationId values"
            )
        if any(not isinstance(item, ClaimDimensionBinding) for item in bindings):
            raise StateDerivationError(
                "claim_dimension_bindings must contain ClaimDimensionBinding values"
            )
        if len(set(evaluation_ids)) != len(evaluation_ids):
            raise StateDerivationError(
                "duplicate selected evaluation ids are not allowed"
            )
        binding_claim_ids = [item.claim_id for item in bindings]
        if len(set(binding_claim_ids)) != len(binding_claim_ids):
            raise StateDerivationError(
                "each claim may have at most one claim-dimension binding per request"
            )

        object.__setattr__(self, "as_of", as_of)
        object.__setattr__(self, "derived_at", derived_at)
        object.__setattr__(
            self,
            "selected_evaluation_ids",
            tuple(sorted(evaluation_ids)),
        )
        object.__setattr__(
            self,
            "claim_dimension_bindings",
            tuple(sorted(bindings, key=lambda item: item.claim_id)),
        )


def derive_supported_state_v1(
    *,
    records: EpistemicRecordSet,
    frame: CompetenceFrame,
    request: DeterministicStateDerivationRequest,
) -> PersonalCapabilityState:
    """Derive PR3 state from explicit governed evaluations with no hidden weighting."""

    if not isinstance(records, EpistemicRecordSet):
        raise StateDerivationError("records must be EpistemicRecordSet")
    if not isinstance(frame, CompetenceFrame):
        raise StateDerivationError("frame must be CompetenceFrame")
    if not isinstance(request, DeterministicStateDerivationRequest):
        raise StateDerivationError(
            "request must be DeterministicStateDerivationRequest"
        )
    if frame.ref != request.frame_ref:
        raise StateDerivationError(
            f"request requires exact frame {request.frame_ref}; supplied frame is {frame.ref}"
        )

    claims = {claim.claim_id: claim for claim in records.claims}
    evaluations = {
        evaluation.evaluation_id: evaluation for evaluation in records.evaluations
    }

    selected = []
    for evaluation_id in request.selected_evaluation_ids:
        evaluation = evaluations.get(evaluation_id)
        if evaluation is None:
            raise StateDerivationError(
                f"selected evaluation does not exist: {evaluation_id}"
            )
        claim = claims.get(evaluation.claim_id)
        if claim is None:
            raise StateDerivationError(
                f"selected evaluation references missing claim: {evaluation.claim_id}"
            )
        if claim.subject_ref != request.subject_ref:
            raise StateDerivationError(
                "selected evaluation belongs to a different subject"
            )
        if claim.concept_ref != request.concept_ref:
            raise StateDerivationError(
                "selected evaluation belongs to a different capability concept revision"
            )
        if evaluation.evaluated_at > request.as_of:
            raise StateDerivationError(
                "selected evaluation may not occur after the request as_of boundary"
            )
        selected.append(evaluation)

    frame_dimension_keys = {dimension.key for dimension in frame.dimensions}
    bindings_by_claim: dict[CapabilityClaimId, ClaimDimensionBinding] = {}
    for binding in request.claim_dimension_bindings:
        claim = claims.get(binding.claim_id)
        if claim is None:
            raise StateDerivationError(
                f"claim-dimension binding references missing claim: {binding.claim_id}"
            )
        if claim.subject_ref != request.subject_ref:
            raise StateDerivationError(
                "claim-dimension binding belongs to a different subject"
            )
        if claim.concept_ref != request.concept_ref:
            raise StateDerivationError(
                "claim-dimension binding belongs to a different capability concept revision"
            )
        unknown_keys = set(binding.dimension_keys) - frame_dimension_keys
        if unknown_keys:
            raise StateDerivationError(
                "claim-dimension binding references dimensions absent from the exact frame: "
                f"{sorted(unknown_keys)!r}"
            )
        bindings_by_claim[binding.claim_id] = binding

    selected_claim_ids = {evaluation.claim_id for evaluation in selected}
    bound_claim_ids = set(bindings_by_claim)
    unbound_selected = selected_claim_ids - bound_claim_ids
    if unbound_selected:
        raise StateDerivationError(
            "every selected evaluation claim must have an explicit dimension binding: "
            f"{sorted(map(str, unbound_selected))!r}"
        )
    bound_without_selection = bound_claim_ids - selected_claim_ids
    if bound_without_selection:
        raise StateDerivationError(
            "every bound claim must have at least one selected evaluation: "
            f"{sorted(map(str, bound_without_selection))!r}"
        )

    selected_by_claim: dict[CapabilityClaimId, tuple] = {}
    for claim_id in selected_claim_ids:
        selected_by_claim[claim_id] = tuple(
            sorted(
                (
                    evaluation
                    for evaluation in selected
                    if evaluation.claim_id == claim_id
                ),
                key=lambda item: item.evaluation_id,
            )
        )

    dimensions = []
    for dimension in frame.dimensions:
        dimension_claim_ids = tuple(
            sorted(
                claim_id
                for claim_id, binding in bindings_by_claim.items()
                if dimension.key in binding.dimension_keys
            )
        )
        basis = tuple(
            sorted(
                (
                    evaluation
                    for claim_id in dimension_claim_ids
                    for evaluation in selected_by_claim[claim_id]
                ),
                key=lambda item: item.evaluation_id,
            )
        )

        if not basis:
            dimensions.append(
                CompetenceDimensionState(
                    dimension_key=dimension.key,
                    standing=DimensionStanding.UNKNOWN,
                    rationale=(
                        "No selected evaluation basis is bound to this dimension "
                        "under deterministic supported-state policy v1."
                    ),
                    conflict_status=DimensionConflictStatus.NONE,
                )
            )
            continue

        supported_claim_ids = tuple(
            sorted(
                {
                    evaluation.claim_id
                    for evaluation in basis
                    if evaluation.conclusion is EvaluationConclusion.SUPPORTED
                }
            )
        )
        standing = (
            DimensionStanding.SUPPORTED
            if supported_claim_ids
            else DimensionStanding.INSUFFICIENT
        )

        explicit_unresolved = any(
            evaluation.conflict_status is EvaluationConflictStatus.UNRESOLVED
            for evaluation in basis
        )
        directional_by_claim: dict[
            CapabilityClaimId, set[EvaluationConclusion]
        ] = {}
        for evaluation in basis:
            if evaluation.conclusion in {
                EvaluationConclusion.SUPPORTED,
                EvaluationConclusion.CONTRADICTED,
            }:
                directional_by_claim.setdefault(evaluation.claim_id, set()).add(
                    evaluation.conclusion
                )
        opposing_same_claim = any(
            {
                EvaluationConclusion.SUPPORTED,
                EvaluationConclusion.CONTRADICTED,
            }.issubset(conclusions)
            for conclusions in directional_by_claim.values()
        )
        conflict_status = (
            DimensionConflictStatus.UNRESOLVED
            if explicit_unresolved or opposing_same_claim
            else DimensionConflictStatus.NONE
        )

        if standing is DimensionStanding.SUPPORTED:
            rationale = (
                "Supported content contains each bound claim with at least one "
                "selected SUPPORTED ClaimEvaluation under deterministic "
                "supported-state policy v1."
            )
        else:
            rationale = (
                "Selected evaluation basis is present but contains no bound claim "
                "with a selected SUPPORTED ClaimEvaluation under deterministic "
                "supported-state policy v1."
            )
        if conflict_status is DimensionConflictStatus.UNRESOLVED:
            rationale += (
                " Selected basis also contains unresolved or opposing same-claim "
                "evaluation conclusions; baseline v1 does not resolve that conflict."
            )

        dimensions.append(
            CompetenceDimensionState(
                dimension_key=dimension.key,
                standing=standing,
                supported_claim_ids=supported_claim_ids,
                basis_evaluation_ids=tuple(
                    evaluation.evaluation_id for evaluation in basis
                ),
                rationale=rationale,
                conflict_status=conflict_status,
            )
        )

    state = PersonalCapabilityState(
        state_id=request.state_id,
        subject_ref=request.subject_ref,
        concept_ref=request.concept_ref,
        frame_ref=request.frame_ref,
        derivation_policy_ref=DETERMINISTIC_SUPPORTED_STATE_POLICY_V1,
        deriver_ref=DETERMINISTIC_SUPPORTED_STATE_DERIVER_V1,
        as_of=request.as_of,
        derived_at=request.derived_at,
        dimensions=tuple(dimensions),
        rationale=(
            "Deterministic supported-state baseline v1 composed only explicitly "
            "selected ClaimEvaluation records and explicit claim-dimension bindings; "
            "it performed no evidence weighting, evaluator weighting, recency decay, "
            "majority vote, mastery scoring, or state-level conflict resolution."
        ),
    )

    # Defense in depth: every derived output must already satisfy the PR3 contracts.
    state_set = PersonalCapabilityStateSet(request.subject_ref, (state,))
    state_set.validate_against_epistemics(records)
    state_set.validate_against_frame_catalog(CompetenceFrameCatalog((frame,)))
    return state
