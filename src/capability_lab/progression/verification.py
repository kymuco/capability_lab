"""Source-backed verification for deterministic PR8 progression frontiers."""

from __future__ import annotations

from capability_lab.epistemics import EpistemicRecordSet
from capability_lab.semantics import CapabilityCatalog
from capability_lab.state import CompetenceFrameCatalog, PersonalCapabilityStateSet

from .core import (
    InvalidProgressionFrontier,
    ProgressionFrontier,
    ProgressionFrontierRequest,
)
from .derivation import derive_progression_frontier_v1


def validate_progression_frontier_v1(
    *,
    capability_catalog: CapabilityCatalog,
    frame_catalog: CompetenceFrameCatalog,
    records: EpistemicRecordSet,
    state_set: PersonalCapabilityStateSet,
    frontier: ProgressionFrontier,
) -> None:
    """Verify that a frontier exactly re-derives from its stored effective inputs.

    Strict deserialization proves only structural/schema validity. This function is the
    source-backed deterministic verification boundary for the PR8 baseline.
    """

    if not isinstance(frontier, ProgressionFrontier):
        raise InvalidProgressionFrontier("frontier must be ProgressionFrontier")

    try:
        request = ProgressionFrontierRequest(
            frontier_id=frontier.frontier_id,
            subject_ref=frontier.subject_ref,
            as_of=frontier.as_of,
            generated_at=frontier.generated_at,
            requester_ref=frontier.requester_ref,
            focuses=frontier.focuses,
            seed_bindings=frontier.seed_bindings,
            prerequisite_bindings=frontier.prerequisite_bindings,
            exploration_inputs=frontier.exploration_inputs,
        )
        expected = derive_progression_frontier_v1(
            capability_catalog=capability_catalog,
            frame_catalog=frame_catalog,
            records=records,
            state_set=state_set,
            request=request,
        )
    except ValueError as exc:
        raise InvalidProgressionFrontier(
            "frontier effective inputs cannot be verified against supplied source snapshots"
        ) from exc

    if expected != frontier:
        raise InvalidProgressionFrontier(
            "frontier does not exactly match deterministic PR8 derivation from its stored "
            "effective inputs and supplied source snapshots"
        )
