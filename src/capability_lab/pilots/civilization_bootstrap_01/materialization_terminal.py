"""Terminal reviewed-dependence governance for PR10.1 Pilot 01 evidence."""

from __future__ import annotations

from . import materialization as _materialization
from . import materialization_lineage_completeness as _source_completeness
from . import materialization_mechanism_completeness as _mechanism_completeness
from . import materialization_coordination_completeness as _coordination_completeness
from . import materialization_temporal_completeness as _temporal_completeness
from . import materialization_allocation_completeness as _allocation_completeness
from . import materialization_resolution as _resolution
from . import materialization_selection_completeness as _selection_completeness
from . import materialization_selection_dependence as _selection


_MIN_TERMINAL_OBSERVATIONS = 2


def _selection_entries_tuple(selection_entries):
    if isinstance(selection_entries, (str, bytes)):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "selection_entries must be an iterable of PilotMaterializedEvidenceSelectionEntry values"
        )
    try:
        entries = tuple(selection_entries)
    except TypeError as exc:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "selection_entries must be iterable"
        ) from exc
    if any(
        not isinstance(item, _selection.PilotMaterializedEvidenceSelectionEntry)
        for item in entries
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "selection_entries must contain PilotMaterializedEvidenceSelectionEntry values"
        )
    return entries


def _basis_entry(selection_entry):
    return (
        selection_entry.allocation_entry.temporal_entry.coordination_entry
        .mechanism_entry.upstream_lineage_entry.basis_entry
    )


def _validate_terminal_basis_cardinality_v1(entries) -> None:
    if len(entries) < _MIN_TERMINAL_OBSERVATIONS:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "terminal PR10.1 dependence preconditions require at least two "
            "materialized observation slots; an empty or singleton basis cannot "
            "establish a cross-observation dependence precondition"
        )


def _validate_unique_evidence_identity_v1(entries) -> None:
    seen: set[object] = set()
    for entry in entries:
        evidence_id = _basis_entry(entry).evidence.evidence_id
        if evidence_id in seen:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "duplicate EvidenceId appears in multiple PR10.1 observation slots; "
                "one EvidenceRecord identity cannot represent multiple causal basis entries: "
                f"evidence_id={evidence_id}"
            )
        seen.add(evidence_id)


def _resolution_bindings_tuple(materialization_resolution_bindings):
    if isinstance(materialization_resolution_bindings, (str, bytes)):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "materialization_resolution_bindings must be an iterable of "
            "PilotReviewedMaterializationResolutionBinding values"
        )
    try:
        bindings = tuple(materialization_resolution_bindings)
    except TypeError as exc:
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "materialization_resolution_bindings must be iterable"
        ) from exc
    if any(
        not isinstance(
            item,
            _resolution.PilotReviewedMaterializationResolutionBinding,
        )
        for item in bindings
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "materialization_resolution_bindings must contain "
            "PilotReviewedMaterializationResolutionBinding values"
        )
    return bindings


def _validate_reviewed_resolution_bindings_v1(entries, bindings) -> None:
    bindings = _resolution_bindings_tuple(bindings)
    by_evidence_id = {}
    for binding in bindings:
        evidence_id = binding.receipt.evidence_id
        if evidence_id in by_evidence_id:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "duplicate reviewed-resolution binding for terminal EvidenceId: "
                f"evidence_id={evidence_id}"
            )
        by_evidence_id[evidence_id] = binding

    terminal_ids = tuple(_basis_entry(entry).evidence.evidence_id for entry in entries)
    if set(by_evidence_id) != set(terminal_ids) or len(bindings) != len(entries):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "terminal PR10.1 basis must have exact one-to-one reviewed-resolution "
            "receipt coverage for every materialized EvidenceRecord"
        )

    for entry in entries:
        basis = _basis_entry(entry)
        _resolution.validate_pilot_reviewed_materialization_resolution_binding_v1(
            basis.candidate,
            basis.evidence,
            by_evidence_id[basis.evidence.evidence_id],
        )


def _validate_completeness_review_temporal_causality_v1(
    entries,
    *,
    source_completeness_review,
    mechanism_completeness_review,
    coordination_completeness_review,
    temporal_completeness_review,
    allocation_completeness_review,
    selection_completeness_review,
) -> None:
    latest_recorded_at = max(
        _basis_entry(entry).evidence.recorded_at
        for entry in entries
    )
    reviews = (
        (
            "source",
            source_completeness_review,
            _source_completeness.PilotUpstreamLineageCompletenessReview,
        ),
        (
            "mechanism",
            mechanism_completeness_review,
            _mechanism_completeness.PilotMechanismLineageCompletenessReview,
        ),
        (
            "coordination",
            coordination_completeness_review,
            _coordination_completeness.PilotCoordinationLineageCompletenessReview,
        ),
        (
            "temporal",
            temporal_completeness_review,
            _temporal_completeness.PilotTemporalLineageCompletenessReview,
        ),
        (
            "allocation",
            allocation_completeness_review,
            _allocation_completeness.PilotAllocationLineageCompletenessReview,
        ),
        (
            "selection",
            selection_completeness_review,
            _selection_completeness.PilotSelectionLineageCompletenessReview,
        ),
    )
    for family, review, review_type in reviews:
        if not isinstance(review, review_type):
            # Exact type diagnostics remain owned by the corresponding family
            # gate; chronology is meaningful only for a valid review record.
            continue
        if review.reviewed_at < latest_recorded_at:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                f"{family} completeness reviewed_at must not precede the latest "
                "materialized EvidenceRecord recorded_at in the exact terminal basis"
            )


def validate_pilot_materialized_evidence_reviewed_dependence_preconditions_v1(
    selection_entries,
    *,
    materialization_resolution_bindings,
    source_lineage_graph,
    source_completeness_review,
    mechanism_lineage_graph,
    mechanism_completeness_review,
    coordination_lineage_graph,
    coordination_completeness_review,
    temporal_lineage_graph,
    temporal_completeness_review,
    allocation_lineage_graph,
    allocation_completeness_review,
    selection_lineage_graph,
    selection_completeness_review,
):
    """Run the complete current PR10.1 reviewed-dependence precondition ladder.

    This is the terminal PR10.1 dependence-governance gate. Lower family gates are
    diagnostic primitives and their PASS does not mean that later PR10.1 families
    were checked. A terminal PASS requires a genuine multi-observation basis, an
    exact MATERIALIZE review plus resolver-issued full-EvidenceRecord receipt for
    every slot, and the complete current structural/reviewed-completeness ladder.
    It is not proof of statistical independence or authority to claim independent
    replication.
    """

    entries = _selection_entries_tuple(selection_entries)

    # A cross-observation dependence precondition is meaningless for an empty or
    # singleton basis. Fail closed before any review or scope digest is accepted.
    _validate_terminal_basis_cardinality_v1(entries)

    # Reject ambiguous multi-observation identity before any completeness scope
    # digest is allowed to rely on evidence_id ordering.
    _validate_unique_evidence_identity_v1(entries)

    # A self-described EvidenceRecord provenance note is not enough. Terminal
    # governance requires exact resolver-issued binding to the selected MATERIALIZE
    # review and the full canonical EvidenceRecord bytes for every observation.
    _validate_reviewed_resolution_bindings_v1(
        entries,
        materialization_resolution_bindings,
    )

    # Aggregate defense-in-depth. Every family also enforces the same chronology
    # at its own reviewed gate so lower reviewed-family APIs cannot return a
    # causally impossible PASS in isolation.
    _validate_completeness_review_temporal_causality_v1(
        entries,
        source_completeness_review=source_completeness_review,
        mechanism_completeness_review=mechanism_completeness_review,
        coordination_completeness_review=coordination_completeness_review,
        temporal_completeness_review=temporal_completeness_review,
        allocation_completeness_review=allocation_completeness_review,
        selection_completeness_review=selection_completeness_review,
    )

    return (
        _selection_completeness.validate_pilot_materialized_evidence_reviewed_selection_origin_preconditions_v1(
            entries,
            source_lineage_graph=source_lineage_graph,
            source_completeness_review=source_completeness_review,
            mechanism_lineage_graph=mechanism_lineage_graph,
            mechanism_completeness_review=mechanism_completeness_review,
            coordination_lineage_graph=coordination_lineage_graph,
            coordination_completeness_review=coordination_completeness_review,
            temporal_lineage_graph=temporal_lineage_graph,
            temporal_completeness_review=temporal_completeness_review,
            allocation_lineage_graph=allocation_lineage_graph,
            allocation_completeness_review=allocation_completeness_review,
            selection_lineage_graph=selection_lineage_graph,
            selection_completeness_review=selection_completeness_review,
        )
    )
