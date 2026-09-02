"""Declared temporal/intervention/carryover lineage governance for PR10.1 Pilot 01."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from . import materialization as _materialization
from . import materialization_coordination_completeness as _coordination_completeness
from . import materialization_coordination_lineage as _coordination_lineage
from . import materialization_lineage_completeness as _source_completeness
from . import materialization_mechanism_completeness as _mechanism_completeness
from . import materialization_mechanism_lineage as _mechanism_lineage
from . import materialization_source_lineage as _source_lineage
from . import materialization_temporal_dependence as _temporal


def _temporal_sort_key(
    temporal: _temporal.PilotObservationTemporalRef,
) -> tuple[str, str]:
    return (temporal.kind.value, temporal.ref)


class PilotObservationTemporalRelationKind(str, Enum):
    """Explicit dependence-relevant temporal/intervention lineage relations.

    DERIVED_FROM, STATE_CONTINUATION_OF and CARRYOVER_FROM are directed
    downstream -> upstream. ALIAS_OF is symmetric.

    Ordering, proximity, overlap, or generic family membership are
    intentionally not lineage relations.
    """

    ALIAS_OF = "ALIAS_OF"
    DERIVED_FROM = "DERIVED_FROM"
    STATE_CONTINUATION_OF = "STATE_CONTINUATION_OF"
    CARRYOVER_FROM = "CARRYOVER_FROM"


@dataclass(frozen=True, slots=True)
class PilotObservationTemporalRelation:
    """One explicit dependence-relevant relation between temporal identities."""

    relation_kind: PilotObservationTemporalRelationKind
    temporal: _temporal.PilotObservationTemporalRef
    upstream: _temporal.PilotObservationTemporalRef

    def __post_init__(self) -> None:
        if not isinstance(
            self.relation_kind,
            PilotObservationTemporalRelationKind,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation temporal relation kind must be "
                "PilotObservationTemporalRelationKind"
            )
        if not isinstance(
            self.temporal,
            _temporal.PilotObservationTemporalRef,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation temporal relation temporal must be "
                "PilotObservationTemporalRef"
            )
        if not isinstance(
            self.upstream,
            _temporal.PilotObservationTemporalRef,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation temporal relation upstream must be "
                "PilotObservationTemporalRef"
            )
        if self.temporal == self.upstream:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation temporal relation must connect two distinct "
                "exact temporal refs"
            )


def _canonical_relation(
    relation: PilotObservationTemporalRelation,
) -> PilotObservationTemporalRelation:
    if relation.relation_kind is not PilotObservationTemporalRelationKind.ALIAS_OF:
        return relation
    if _temporal_sort_key(relation.temporal) <= _temporal_sort_key(
        relation.upstream
    ):
        return relation
    return PilotObservationTemporalRelation(
        PilotObservationTemporalRelationKind.ALIAS_OF,
        relation.upstream,
        relation.temporal,
    )


def _relation_sort_key(
    relation: PilotObservationTemporalRelation,
) -> tuple[str, str, str, str, str]:
    return (
        relation.relation_kind.value,
        relation.temporal.kind.value,
        relation.temporal.ref,
        relation.upstream.kind.value,
        relation.upstream.ref,
    )


def _validate_temporal_lineage_graph(
    relations: tuple[PilotObservationTemporalRelation, ...],
) -> None:
    nodes = {
        temporal
        for relation in relations
        for temporal in (relation.temporal, relation.upstream)
    }
    parent = {node: node for node in nodes}

    def find(node: _temporal.PilotObservationTemporalRef):
        root = node
        while parent[root] != root:
            root = parent[root]
        while parent[node] != node:
            next_node = parent[node]
            parent[node] = root
            node = next_node
        return root

    def union(
        left: _temporal.PilotObservationTemporalRef,
        right: _temporal.PilotObservationTemporalRef,
    ) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root == right_root:
            return
        if _temporal_sort_key(left_root) <= _temporal_sort_key(right_root):
            parent[right_root] = left_root
        else:
            parent[left_root] = right_root

    for relation in relations:
        if relation.relation_kind is PilotObservationTemporalRelationKind.ALIAS_OF:
            union(relation.temporal, relation.upstream)

    collapsed_edges: dict[
        tuple[
            _temporal.PilotObservationTemporalRef,
            _temporal.PilotObservationTemporalRef,
        ],
        PilotObservationTemporalRelationKind,
    ] = {}
    adjacency: dict[
        _temporal.PilotObservationTemporalRef,
        set[_temporal.PilotObservationTemporalRef],
    ] = {}

    for relation in relations:
        if relation.relation_kind is PilotObservationTemporalRelationKind.ALIAS_OF:
            continue
        temporal_root = find(relation.temporal)
        upstream_root = find(relation.upstream)
        if temporal_root == upstream_root:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "directed observation temporal relation must not collapse "
                "within one alias class"
            )
        pair = (temporal_root, upstream_root)
        previous_kind = collapsed_edges.get(pair)
        if previous_kind is not None and previous_kind is not relation.relation_kind:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation temporal lineage graph has conflicting directed "
                "relation kinds after alias contraction"
            )
        collapsed_edges[pair] = relation.relation_kind
        adjacency.setdefault(temporal_root, set()).add(upstream_root)

    visiting: set[_temporal.PilotObservationTemporalRef] = set()
    visited: set[_temporal.PilotObservationTemporalRef] = set()

    def visit(node: _temporal.PilotObservationTemporalRef) -> None:
        if node in visited:
            return
        if node in visiting:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation temporal lineage graph must be acyclic after "
                "alias contraction"
            )
        visiting.add(node)
        for upstream in sorted(
            adjacency.get(node, ()),
            key=_temporal_sort_key,
        ):
            visit(upstream)
        visiting.remove(node)
        visited.add(node)

    for node in sorted({find(item) for item in nodes}, key=_temporal_sort_key):
        visit(node)


@dataclass(frozen=True, slots=True)
class PilotObservationTemporalLineageGraph:
    """Private declaration of known dependence-relevant temporal lineage.

    Empty/incomplete means only that no additional relations were supplied.
    It never proves temporal, intervention, carryover, or history independence.
    """

    relations: tuple[PilotObservationTemporalRelation, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.relations, tuple):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation temporal lineage graph relations must be a tuple"
            )
        if any(
            not isinstance(item, PilotObservationTemporalRelation)
            for item in self.relations
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation temporal lineage graph must contain "
                "PilotObservationTemporalRelation values"
            )

        canonical = tuple(_canonical_relation(item) for item in self.relations)
        if len(set(canonical)) != len(canonical):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation temporal lineage graph must not repeat an exact "
                "or reverse-alias relation"
            )

        directed_pairs: dict[
            tuple[
                _temporal.PilotObservationTemporalRef,
                _temporal.PilotObservationTemporalRef,
            ],
            PilotObservationTemporalRelationKind,
        ] = {}
        for relation in canonical:
            if relation.relation_kind is PilotObservationTemporalRelationKind.ALIAS_OF:
                continue
            pair = (relation.temporal, relation.upstream)
            previous_kind = directed_pairs.get(pair)
            if previous_kind is not None and previous_kind is not relation.relation_kind:
                raise _materialization.InvalidPilotEvidenceMaterialization(
                    "observation temporal lineage graph must not assign "
                    "conflicting relation kinds to one directed pair"
                )
            directed_pairs[pair] = relation.relation_kind

        canonical = tuple(sorted(canonical, key=_relation_sort_key))
        _validate_temporal_lineage_graph(canonical)
        object.__setattr__(self, "relations", canonical)


def pilot_observation_temporal_lineage_closure_keys_v1(
    temporal: _temporal.PilotObservationTemporalRef,
    graph: PilotObservationTemporalLineageGraph,
) -> tuple[str, ...]:
    """Return exact keys reachable through alias/upstream temporal lineage.

    ALIAS_OF is traversed both directions. Directed relations are traversed
    downstream -> upstream only. No edge is inferred from timestamps, order,
    overlap, proximity, or same-subject metadata.
    """

    if not isinstance(temporal, _temporal.PilotObservationTemporalRef):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "temporal must be PilotObservationTemporalRef"
        )
    if not isinstance(graph, PilotObservationTemporalLineageGraph):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "graph must be PilotObservationTemporalLineageGraph"
        )

    adjacency: dict[
        _temporal.PilotObservationTemporalRef,
        set[_temporal.PilotObservationTemporalRef],
    ] = {}
    for relation in graph.relations:
        if relation.relation_kind is PilotObservationTemporalRelationKind.ALIAS_OF:
            adjacency.setdefault(relation.temporal, set()).add(relation.upstream)
            adjacency.setdefault(relation.upstream, set()).add(relation.temporal)
        else:
            adjacency.setdefault(relation.temporal, set()).add(relation.upstream)

    pending = [temporal]
    reachable: set[_temporal.PilotObservationTemporalRef] = set()
    while pending:
        current = pending.pop()
        if current in reachable:
            continue
        reachable.add(current)
        pending.extend(
            sorted(
                adjacency.get(current, ()),
                key=_temporal_sort_key,
                reverse=True,
            )
        )

    return tuple(
        sorted(
            _temporal.pilot_observation_temporal_dependence_key_v1(item)
            for item in reachable
        )
    )


def validate_pilot_materialized_evidence_temporal_ancestry_preconditions_v1(
    temporal_entries,
    *,
    source_lineage_graph: _source_lineage.PilotUpstreamSourceLineageGraph,
    source_completeness_review: _source_completeness.PilotUpstreamLineageCompletenessReview,
    mechanism_lineage_graph: _mechanism_lineage.PilotObservationMechanismLineageGraph,
    mechanism_completeness_review: _mechanism_completeness.PilotMechanismLineageCompletenessReview,
    coordination_lineage_graph: _coordination_lineage.PilotObservationCoordinationLineageGraph,
    coordination_completeness_review: _coordination_completeness.PilotCoordinationLineageCompletenessReview,
    temporal_lineage_graph: PilotObservationTemporalLineageGraph,
):
    """Reject known shared temporal alias/ancestor lineage after prior gates.

    PASS means only that the reviewed source/mechanism/coordination ladder
    passed, no exact temporal ref was shared, and the supplied temporal graph
    exposed no common alias or upstream intervention/carryover/history lineage.
    Missing declarations or graph edges remain unknown.
    """

    if not isinstance(
        temporal_lineage_graph,
        PilotObservationTemporalLineageGraph,
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "temporal_lineage_graph must be "
            "PilotObservationTemporalLineageGraph"
        )

    entries = (
        _temporal.validate_pilot_materialized_evidence_shared_temporal_preconditions_v1(
            temporal_entries,
            source_lineage_graph=source_lineage_graph,
            source_completeness_review=source_completeness_review,
            mechanism_lineage_graph=mechanism_lineage_graph,
            mechanism_completeness_review=mechanism_completeness_review,
            coordination_lineage_graph=coordination_lineage_graph,
            coordination_completeness_review=coordination_completeness_review,
        )
    )

    seen_lineage: dict[str, object] = {}
    for entry in entries:
        evidence_id = (
            entry.coordination_entry.mechanism_entry.upstream_lineage_entry
            .basis_entry.evidence.evidence_id
        )
        entry_lineage_keys: set[str] = set()
        for temporal in entry.temporal_declaration.temporals:
            entry_lineage_keys.update(
                pilot_observation_temporal_lineage_closure_keys_v1(
                    temporal,
                    temporal_lineage_graph,
                )
            )

        for key in sorted(entry_lineage_keys):
            previous = seen_lineage.get(key)
            if previous is not None:
                raise _materialization.InvalidPilotEvidenceMaterialization(
                    "distinct materialized Pilot observations converge through one "
                    "declared temporal/intervention/carryover alias/ancestry "
                    "lineage; related aliases, derivations, state continuations, "
                    "or carryover relations cannot satisfy PR10.1 temporal-ancestry "
                    "independence preconditions: "
                    f"temporal_lineage={key}, first={previous}, second={evidence_id}"
                )
            seen_lineage[key] = evidence_id

    return entries
