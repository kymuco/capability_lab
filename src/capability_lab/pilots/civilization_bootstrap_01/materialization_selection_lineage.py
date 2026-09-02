"""Declared sampling/selection/cohort-construction lineage governance for PR10.1 Pilot 01."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from . import materialization as _materialization
from . import materialization_allocation_completeness as _allocation_completeness
from . import materialization_allocation_lineage as _allocation_lineage
from . import materialization_coordination_completeness as _coordination_completeness
from . import materialization_coordination_lineage as _coordination_lineage
from . import materialization_lineage_completeness as _source_completeness
from . import materialization_mechanism_completeness as _mechanism_completeness
from . import materialization_mechanism_lineage as _mechanism_lineage
from . import materialization_selection_dependence as _selection
from . import materialization_source_lineage as _source_lineage
from . import materialization_temporal_completeness as _temporal_completeness
from . import materialization_temporal_lineage as _temporal_lineage


def _selection_sort_key(
    selection: _selection.PilotObservationSelectionRef,
) -> tuple[str, str]:
    return (selection.kind.value, selection.ref)


class PilotObservationSelectionRelationKind(str, Enum):
    """Explicit dependence-relevant sampling/selection lineage relations.

    DERIVED_FROM, RESAMPLED_FROM, CLONED_FROM, and STATE_CONTINUATION_OF are
    directed downstream -> upstream. ALIAS_OF is symmetric.

    Same population labels, cohort names, sampling algorithms, inclusion-rule
    definitions, recruitment methods, dataset names, or study families are
    intentionally not lineage relations.
    """

    ALIAS_OF = "ALIAS_OF"
    DERIVED_FROM = "DERIVED_FROM"
    RESAMPLED_FROM = "RESAMPLED_FROM"
    CLONED_FROM = "CLONED_FROM"
    STATE_CONTINUATION_OF = "STATE_CONTINUATION_OF"


@dataclass(frozen=True, slots=True)
class PilotObservationSelectionRelation:
    """One explicit dependence-relevant relation between selection identities."""

    relation_kind: PilotObservationSelectionRelationKind
    selection: _selection.PilotObservationSelectionRef
    upstream: _selection.PilotObservationSelectionRef

    def __post_init__(self) -> None:
        if not isinstance(
            self.relation_kind,
            PilotObservationSelectionRelationKind,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation selection relation kind must be "
                "PilotObservationSelectionRelationKind"
            )
        if not isinstance(
            self.selection,
            _selection.PilotObservationSelectionRef,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation selection relation selection must be "
                "PilotObservationSelectionRef"
            )
        if not isinstance(
            self.upstream,
            _selection.PilotObservationSelectionRef,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation selection relation upstream must be "
                "PilotObservationSelectionRef"
            )
        if self.selection == self.upstream:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation selection relation must connect two distinct "
                "exact selection refs"
            )


def _canonical_relation(
    relation: PilotObservationSelectionRelation,
) -> PilotObservationSelectionRelation:
    if relation.relation_kind is not PilotObservationSelectionRelationKind.ALIAS_OF:
        return relation
    if _selection_sort_key(relation.selection) <= _selection_sort_key(
        relation.upstream
    ):
        return relation
    return PilotObservationSelectionRelation(
        PilotObservationSelectionRelationKind.ALIAS_OF,
        relation.upstream,
        relation.selection,
    )


def _relation_sort_key(
    relation: PilotObservationSelectionRelation,
) -> tuple[str, str, str, str, str]:
    return (
        relation.relation_kind.value,
        relation.selection.kind.value,
        relation.selection.ref,
        relation.upstream.kind.value,
        relation.upstream.ref,
    )


def _validate_selection_lineage_graph(
    relations: tuple[PilotObservationSelectionRelation, ...],
) -> None:
    nodes = {
        selection
        for relation in relations
        for selection in (relation.selection, relation.upstream)
    }
    parent = {node: node for node in nodes}

    def find(node: _selection.PilotObservationSelectionRef):
        root = node
        while parent[root] != root:
            root = parent[root]
        while parent[node] != node:
            next_node = parent[node]
            parent[node] = root
            node = next_node
        return root

    def union(
        left: _selection.PilotObservationSelectionRef,
        right: _selection.PilotObservationSelectionRef,
    ) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root == right_root:
            return
        if _selection_sort_key(left_root) <= _selection_sort_key(right_root):
            parent[right_root] = left_root
        else:
            parent[left_root] = right_root

    for relation in relations:
        if relation.relation_kind is PilotObservationSelectionRelationKind.ALIAS_OF:
            union(relation.selection, relation.upstream)

    collapsed_edges: dict[
        tuple[
            _selection.PilotObservationSelectionRef,
            _selection.PilotObservationSelectionRef,
        ],
        PilotObservationSelectionRelationKind,
    ] = {}
    adjacency: dict[
        _selection.PilotObservationSelectionRef,
        set[_selection.PilotObservationSelectionRef],
    ] = {}

    for relation in relations:
        if relation.relation_kind is PilotObservationSelectionRelationKind.ALIAS_OF:
            continue
        selection_root = find(relation.selection)
        upstream_root = find(relation.upstream)
        if selection_root == upstream_root:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "directed observation selection relation must not collapse "
                "within one alias class"
            )
        pair = (selection_root, upstream_root)
        previous_kind = collapsed_edges.get(pair)
        if previous_kind is not None and previous_kind is not relation.relation_kind:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation selection lineage graph has conflicting directed "
                "relation kinds after alias contraction"
            )
        collapsed_edges[pair] = relation.relation_kind
        adjacency.setdefault(selection_root, set()).add(upstream_root)

    visiting: set[_selection.PilotObservationSelectionRef] = set()
    visited: set[_selection.PilotObservationSelectionRef] = set()

    def visit(node: _selection.PilotObservationSelectionRef) -> None:
        if node in visited:
            return
        if node in visiting:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation selection lineage graph must be acyclic after "
                "alias contraction"
            )
        visiting.add(node)
        for upstream in sorted(
            adjacency.get(node, ()),
            key=_selection_sort_key,
        ):
            visit(upstream)
        visiting.remove(node)
        visited.add(node)

    for node in sorted({find(item) for item in nodes}, key=_selection_sort_key):
        visit(node)


@dataclass(frozen=True, slots=True)
class PilotObservationSelectionLineageGraph:
    """Private declaration of known sampling/selection/cohort lineage.

    Empty/incomplete means only that no additional relations were supplied.
    It never proves independent sampling, independent recruitment, absence of
    cohort overlap, statistical independence, or independent replication.
    """

    relations: tuple[PilotObservationSelectionRelation, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.relations, tuple):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation selection lineage graph relations must be a tuple"
            )
        if any(
            not isinstance(item, PilotObservationSelectionRelation)
            for item in self.relations
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation selection lineage graph must contain "
                "PilotObservationSelectionRelation values"
            )

        canonical = tuple(_canonical_relation(item) for item in self.relations)
        if len(set(canonical)) != len(canonical):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation selection lineage graph must not repeat an exact "
                "or reverse-alias relation"
            )

        directed_pairs: dict[
            tuple[
                _selection.PilotObservationSelectionRef,
                _selection.PilotObservationSelectionRef,
            ],
            PilotObservationSelectionRelationKind,
        ] = {}
        for relation in canonical:
            if relation.relation_kind is PilotObservationSelectionRelationKind.ALIAS_OF:
                continue
            pair = (relation.selection, relation.upstream)
            previous_kind = directed_pairs.get(pair)
            if previous_kind is not None and previous_kind is not relation.relation_kind:
                raise _materialization.InvalidPilotEvidenceMaterialization(
                    "observation selection lineage graph must not assign "
                    "conflicting relation kinds to one directed pair"
                )
            directed_pairs[pair] = relation.relation_kind

        canonical = tuple(sorted(canonical, key=_relation_sort_key))
        _validate_selection_lineage_graph(canonical)
        object.__setattr__(self, "relations", canonical)


def pilot_observation_selection_lineage_closure_keys_v1(
    selection: _selection.PilotObservationSelectionRef,
    graph: PilotObservationSelectionLineageGraph,
) -> tuple[str, ...]:
    """Return exact keys reachable through alias/upstream selection lineage.

    ALIAS_OF is traversed both directions. Directed relations are traversed
    downstream -> upstream only. No edge is inferred from population/cohort
    labels, sampling algorithms, inclusion-rule definitions, recruitment
    methods, generic dataset names, study families, timestamps, or ordering.
    """

    if not isinstance(selection, _selection.PilotObservationSelectionRef):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "selection must be PilotObservationSelectionRef"
        )
    if not isinstance(graph, PilotObservationSelectionLineageGraph):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "graph must be PilotObservationSelectionLineageGraph"
        )

    adjacency: dict[
        _selection.PilotObservationSelectionRef,
        set[_selection.PilotObservationSelectionRef],
    ] = {}
    for relation in graph.relations:
        if relation.relation_kind is PilotObservationSelectionRelationKind.ALIAS_OF:
            adjacency.setdefault(relation.selection, set()).add(relation.upstream)
            adjacency.setdefault(relation.upstream, set()).add(relation.selection)
        else:
            adjacency.setdefault(relation.selection, set()).add(relation.upstream)

    pending = [selection]
    reachable: set[_selection.PilotObservationSelectionRef] = set()
    while pending:
        current = pending.pop()
        if current in reachable:
            continue
        reachable.add(current)
        pending.extend(
            sorted(
                adjacency.get(current, ()),
                key=_selection_sort_key,
                reverse=True,
            )
        )

    return tuple(
        sorted(
            _selection.pilot_observation_selection_dependence_key_v1(item)
            for item in reachable
        )
    )


def validate_pilot_materialized_evidence_selection_ancestry_preconditions_v1(
    selection_entries,
    *,
    source_lineage_graph: _source_lineage.PilotUpstreamSourceLineageGraph,
    source_completeness_review: _source_completeness.PilotUpstreamLineageCompletenessReview,
    mechanism_lineage_graph: _mechanism_lineage.PilotObservationMechanismLineageGraph,
    mechanism_completeness_review: _mechanism_completeness.PilotMechanismLineageCompletenessReview,
    coordination_lineage_graph: _coordination_lineage.PilotObservationCoordinationLineageGraph,
    coordination_completeness_review: _coordination_completeness.PilotCoordinationLineageCompletenessReview,
    temporal_lineage_graph: _temporal_lineage.PilotObservationTemporalLineageGraph,
    temporal_completeness_review: _temporal_completeness.PilotTemporalLineageCompletenessReview,
    allocation_lineage_graph: _allocation_lineage.PilotObservationAllocationLineageGraph,
    allocation_completeness_review: _allocation_completeness.PilotAllocationLineageCompletenessReview,
    selection_lineage_graph: PilotObservationSelectionLineageGraph,
):
    """Reject known shared selection alias/ancestor lineage after prior gates.

    PASS means only that the full reviewed source/mechanism/coordination/
    temporal/allocation ladder passed, no exact selection ref was shared, and
    the supplied selection graph exposed no common alias or upstream
    sampling/selection/cohort origin. Missing declarations or graph edges
    remain unknown.
    """

    if not isinstance(
        selection_lineage_graph,
        PilotObservationSelectionLineageGraph,
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "selection_lineage_graph must be PilotObservationSelectionLineageGraph"
        )

    entries = (
        _selection.validate_pilot_materialized_evidence_shared_selection_preconditions_v1(
            selection_entries,
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
        )
    )

    seen_lineage: dict[str, object] = {}
    for entry in entries:
        evidence_id = (
            entry.allocation_entry.temporal_entry.coordination_entry.mechanism_entry
            .upstream_lineage_entry.basis_entry.evidence.evidence_id
        )
        entry_lineage_keys: set[str] = set()
        for selection in entry.selection_declaration.selections:
            entry_lineage_keys.update(
                pilot_observation_selection_lineage_closure_keys_v1(
                    selection,
                    selection_lineage_graph,
                )
            )

        for key in sorted(entry_lineage_keys):
            previous = seen_lineage.get(key)
            if previous is not None:
                raise _materialization.InvalidPilotEvidenceMaterialization(
                    "distinct materialized Pilot observations converge through one "
                    "declared sampling/selection/cohort-construction alias/ancestry "
                    "lineage; related aliases, derivations, resamples, clones, or "
                    "state continuations cannot satisfy PR10.1 selection-ancestry "
                    "independence preconditions: "
                    f"selection_lineage={key}, first={previous}, second={evidence_id}"
                )
            seen_lineage[key] = evidence_id

    return entries
