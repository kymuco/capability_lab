"""Declared experimental allocation/randomization-state lineage governance for PR10.1 Pilot 01."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from . import materialization as _materialization
from . import materialization_allocation_dependence as _allocation
from . import materialization_coordination_completeness as _coordination_completeness
from . import materialization_coordination_lineage as _coordination_lineage
from . import materialization_lineage_completeness as _source_completeness
from . import materialization_mechanism_completeness as _mechanism_completeness
from . import materialization_mechanism_lineage as _mechanism_lineage
from . import materialization_source_lineage as _source_lineage
from . import materialization_temporal_completeness as _temporal_completeness
from . import materialization_temporal_lineage as _temporal_lineage


def _allocation_sort_key(
    allocation: _allocation.PilotObservationAllocationRef,
) -> tuple[str, str]:
    return (allocation.kind.value, allocation.ref)


class PilotObservationAllocationRelationKind(str, Enum):
    """Explicit dependence-relevant allocation/randomization lineage relations.

    DERIVED_FROM, CLONED_FROM and STATE_CONTINUATION_OF are directed
    downstream -> upstream. ALIAS_OF is symmetric.

    Same arm, treatment label, nominal probability, allocation algorithm,
    policy family, or experiment family are intentionally not lineage
    relations.
    """

    ALIAS_OF = "ALIAS_OF"
    DERIVED_FROM = "DERIVED_FROM"
    CLONED_FROM = "CLONED_FROM"
    STATE_CONTINUATION_OF = "STATE_CONTINUATION_OF"


@dataclass(frozen=True, slots=True)
class PilotObservationAllocationRelation:
    """One explicit dependence-relevant relation between allocation identities."""

    relation_kind: PilotObservationAllocationRelationKind
    allocation: _allocation.PilotObservationAllocationRef
    upstream: _allocation.PilotObservationAllocationRef

    def __post_init__(self) -> None:
        if not isinstance(
            self.relation_kind,
            PilotObservationAllocationRelationKind,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation allocation relation kind must be "
                "PilotObservationAllocationRelationKind"
            )
        if not isinstance(
            self.allocation,
            _allocation.PilotObservationAllocationRef,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation allocation relation allocation must be "
                "PilotObservationAllocationRef"
            )
        if not isinstance(
            self.upstream,
            _allocation.PilotObservationAllocationRef,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation allocation relation upstream must be "
                "PilotObservationAllocationRef"
            )
        if self.allocation == self.upstream:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation allocation relation must connect two distinct "
                "exact allocation refs"
            )


def _canonical_relation(
    relation: PilotObservationAllocationRelation,
) -> PilotObservationAllocationRelation:
    if relation.relation_kind is not PilotObservationAllocationRelationKind.ALIAS_OF:
        return relation
    if _allocation_sort_key(relation.allocation) <= _allocation_sort_key(
        relation.upstream
    ):
        return relation
    return PilotObservationAllocationRelation(
        PilotObservationAllocationRelationKind.ALIAS_OF,
        relation.upstream,
        relation.allocation,
    )


def _relation_sort_key(
    relation: PilotObservationAllocationRelation,
) -> tuple[str, str, str, str, str]:
    return (
        relation.relation_kind.value,
        relation.allocation.kind.value,
        relation.allocation.ref,
        relation.upstream.kind.value,
        relation.upstream.ref,
    )


def _validate_allocation_lineage_graph(
    relations: tuple[PilotObservationAllocationRelation, ...],
) -> None:
    nodes = {
        allocation
        for relation in relations
        for allocation in (relation.allocation, relation.upstream)
    }
    parent = {node: node for node in nodes}

    def find(node: _allocation.PilotObservationAllocationRef):
        root = node
        while parent[root] != root:
            root = parent[root]
        while parent[node] != node:
            next_node = parent[node]
            parent[node] = root
            node = next_node
        return root

    def union(
        left: _allocation.PilotObservationAllocationRef,
        right: _allocation.PilotObservationAllocationRef,
    ) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root == right_root:
            return
        if _allocation_sort_key(left_root) <= _allocation_sort_key(right_root):
            parent[right_root] = left_root
        else:
            parent[left_root] = right_root

    for relation in relations:
        if relation.relation_kind is PilotObservationAllocationRelationKind.ALIAS_OF:
            union(relation.allocation, relation.upstream)

    collapsed_edges: dict[
        tuple[
            _allocation.PilotObservationAllocationRef,
            _allocation.PilotObservationAllocationRef,
        ],
        PilotObservationAllocationRelationKind,
    ] = {}
    adjacency: dict[
        _allocation.PilotObservationAllocationRef,
        set[_allocation.PilotObservationAllocationRef],
    ] = {}

    for relation in relations:
        if relation.relation_kind is PilotObservationAllocationRelationKind.ALIAS_OF:
            continue
        allocation_root = find(relation.allocation)
        upstream_root = find(relation.upstream)
        if allocation_root == upstream_root:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "directed observation allocation relation must not collapse "
                "within one alias class"
            )
        pair = (allocation_root, upstream_root)
        previous_kind = collapsed_edges.get(pair)
        if previous_kind is not None and previous_kind is not relation.relation_kind:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation allocation lineage graph has conflicting directed "
                "relation kinds after alias contraction"
            )
        collapsed_edges[pair] = relation.relation_kind
        adjacency.setdefault(allocation_root, set()).add(upstream_root)

    visiting: set[_allocation.PilotObservationAllocationRef] = set()
    visited: set[_allocation.PilotObservationAllocationRef] = set()

    def visit(node: _allocation.PilotObservationAllocationRef) -> None:
        if node in visited:
            return
        if node in visiting:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation allocation lineage graph must be acyclic after "
                "alias contraction"
            )
        visiting.add(node)
        for upstream in sorted(
            adjacency.get(node, ()),
            key=_allocation_sort_key,
        ):
            visit(upstream)
        visiting.remove(node)
        visited.add(node)

    for node in sorted({find(item) for item in nodes}, key=_allocation_sort_key):
        visit(node)


@dataclass(frozen=True, slots=True)
class PilotObservationAllocationLineageGraph:
    """Private declaration of known allocation/randomization-state lineage.

    Empty/incomplete means only that no additional relations were supplied.
    It never proves independent randomization, independent assignment,
    statistical independence, or independent replication.
    """

    relations: tuple[PilotObservationAllocationRelation, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.relations, tuple):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation allocation lineage graph relations must be a tuple"
            )
        if any(
            not isinstance(item, PilotObservationAllocationRelation)
            for item in self.relations
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation allocation lineage graph must contain "
                "PilotObservationAllocationRelation values"
            )

        canonical = tuple(_canonical_relation(item) for item in self.relations)
        if len(set(canonical)) != len(canonical):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation allocation lineage graph must not repeat an exact "
                "or reverse-alias relation"
            )

        directed_pairs: dict[
            tuple[
                _allocation.PilotObservationAllocationRef,
                _allocation.PilotObservationAllocationRef,
            ],
            PilotObservationAllocationRelationKind,
        ] = {}
        for relation in canonical:
            if relation.relation_kind is PilotObservationAllocationRelationKind.ALIAS_OF:
                continue
            pair = (relation.allocation, relation.upstream)
            previous_kind = directed_pairs.get(pair)
            if previous_kind is not None and previous_kind is not relation.relation_kind:
                raise _materialization.InvalidPilotEvidenceMaterialization(
                    "observation allocation lineage graph must not assign "
                    "conflicting relation kinds to one directed pair"
                )
            directed_pairs[pair] = relation.relation_kind

        canonical = tuple(sorted(canonical, key=_relation_sort_key))
        _validate_allocation_lineage_graph(canonical)
        object.__setattr__(self, "relations", canonical)


def pilot_observation_allocation_lineage_closure_keys_v1(
    allocation: _allocation.PilotObservationAllocationRef,
    graph: PilotObservationAllocationLineageGraph,
) -> tuple[str, ...]:
    """Return exact keys reachable through alias/upstream allocation lineage.

    ALIAS_OF is traversed both directions. Directed relations are traversed
    downstream -> upstream only. No edge is inferred from arm labels,
    treatment names, nominal probabilities, algorithms, policy families,
    experiment families, timestamps, or ordering.
    """

    if not isinstance(allocation, _allocation.PilotObservationAllocationRef):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "allocation must be PilotObservationAllocationRef"
        )
    if not isinstance(graph, PilotObservationAllocationLineageGraph):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "graph must be PilotObservationAllocationLineageGraph"
        )

    adjacency: dict[
        _allocation.PilotObservationAllocationRef,
        set[_allocation.PilotObservationAllocationRef],
    ] = {}
    for relation in graph.relations:
        if relation.relation_kind is PilotObservationAllocationRelationKind.ALIAS_OF:
            adjacency.setdefault(relation.allocation, set()).add(relation.upstream)
            adjacency.setdefault(relation.upstream, set()).add(relation.allocation)
        else:
            adjacency.setdefault(relation.allocation, set()).add(relation.upstream)

    pending = [allocation]
    reachable: set[_allocation.PilotObservationAllocationRef] = set()
    while pending:
        current = pending.pop()
        if current in reachable:
            continue
        reachable.add(current)
        pending.extend(
            sorted(
                adjacency.get(current, ()),
                key=_allocation_sort_key,
                reverse=True,
            )
        )

    return tuple(
        sorted(
            _allocation.pilot_observation_allocation_dependence_key_v1(item)
            for item in reachable
        )
    )


def validate_pilot_materialized_evidence_allocation_ancestry_preconditions_v1(
    allocation_entries,
    *,
    source_lineage_graph: _source_lineage.PilotUpstreamSourceLineageGraph,
    source_completeness_review: _source_completeness.PilotUpstreamLineageCompletenessReview,
    mechanism_lineage_graph: _mechanism_lineage.PilotObservationMechanismLineageGraph,
    mechanism_completeness_review: _mechanism_completeness.PilotMechanismLineageCompletenessReview,
    coordination_lineage_graph: _coordination_lineage.PilotObservationCoordinationLineageGraph,
    coordination_completeness_review: _coordination_completeness.PilotCoordinationLineageCompletenessReview,
    temporal_lineage_graph: _temporal_lineage.PilotObservationTemporalLineageGraph,
    temporal_completeness_review: _temporal_completeness.PilotTemporalLineageCompletenessReview,
    allocation_lineage_graph: PilotObservationAllocationLineageGraph,
):
    """Reject known shared allocation alias/ancestor lineage after prior gates.

    PASS means only that the full reviewed source/mechanism/coordination/temporal
    ladder passed, no exact allocation ref was shared, and the supplied
    allocation graph exposed no common alias or upstream allocation/randomization
    lineage. Missing declarations or graph edges remain unknown.
    """

    if not isinstance(
        allocation_lineage_graph,
        PilotObservationAllocationLineageGraph,
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "allocation_lineage_graph must be "
            "PilotObservationAllocationLineageGraph"
        )

    entries = (
        _allocation.validate_pilot_materialized_evidence_shared_allocation_preconditions_v1(
            allocation_entries,
            source_lineage_graph=source_lineage_graph,
            source_completeness_review=source_completeness_review,
            mechanism_lineage_graph=mechanism_lineage_graph,
            mechanism_completeness_review=mechanism_completeness_review,
            coordination_lineage_graph=coordination_lineage_graph,
            coordination_completeness_review=coordination_completeness_review,
            temporal_lineage_graph=temporal_lineage_graph,
            temporal_completeness_review=temporal_completeness_review,
        )
    )

    seen_lineage: dict[str, object] = {}
    for entry in entries:
        evidence_id = (
            entry.temporal_entry.coordination_entry.mechanism_entry
            .upstream_lineage_entry.basis_entry.evidence.evidence_id
        )
        entry_lineage_keys: set[str] = set()
        for allocation in entry.allocation_declaration.allocations:
            entry_lineage_keys.update(
                pilot_observation_allocation_lineage_closure_keys_v1(
                    allocation,
                    allocation_lineage_graph,
                )
            )

        for key in sorted(entry_lineage_keys):
            previous = seen_lineage.get(key)
            if previous is not None:
                raise _materialization.InvalidPilotEvidenceMaterialization(
                    "distinct materialized Pilot observations converge through one "
                    "declared experimental allocation/randomization alias/ancestry "
                    "lineage; related aliases, derivations, clones, or state "
                    "continuations cannot satisfy PR10.1 allocation-ancestry "
                    "independence preconditions: "
                    f"allocation_lineage={key}, first={previous}, second={evidence_id}"
                )
            seen_lineage[key] = evidence_id

    return entries
