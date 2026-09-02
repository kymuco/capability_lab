"""Declared cross-observation coordination/control lineage governance for PR10.1 Pilot 01."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from . import materialization as _materialization
from . import materialization_coordination_dependence as _coordination
from . import materialization_lineage_completeness as _source_completeness
from . import materialization_mechanism_completeness as _mechanism_completeness
from . import materialization_mechanism_lineage as _mechanism_lineage
from . import materialization_source_lineage as _source_lineage


def _coordination_sort_key(
    coordination: _coordination.PilotObservationCoordinationRef,
) -> tuple[str, str]:
    return (coordination.kind.value, coordination.ref)


class PilotObservationCoordinationRelationKind(str, Enum):
    """Explicit dependence-relevant coordination/control lineage relations.

    DELEGATED_FROM, DERIVED_FROM and STATE_CONTINUATION_OF are directed
    downstream -> upstream. ALIAS_OF is symmetric.

    These relations intentionally exclude generic family/type membership.
    """

    ALIAS_OF = "ALIAS_OF"
    DELEGATED_FROM = "DELEGATED_FROM"
    DERIVED_FROM = "DERIVED_FROM"
    STATE_CONTINUATION_OF = "STATE_CONTINUATION_OF"


@dataclass(frozen=True, slots=True)
class PilotObservationCoordinationRelation:
    """One explicit dependence-relevant relation between coordination identities."""

    relation_kind: PilotObservationCoordinationRelationKind
    coordination: _coordination.PilotObservationCoordinationRef
    upstream: _coordination.PilotObservationCoordinationRef

    def __post_init__(self) -> None:
        if not isinstance(
            self.relation_kind,
            PilotObservationCoordinationRelationKind,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation coordination relation kind must be "
                "PilotObservationCoordinationRelationKind"
            )
        if not isinstance(
            self.coordination,
            _coordination.PilotObservationCoordinationRef,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation coordination relation coordination must be "
                "PilotObservationCoordinationRef"
            )
        if not isinstance(
            self.upstream,
            _coordination.PilotObservationCoordinationRef,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation coordination relation upstream must be "
                "PilotObservationCoordinationRef"
            )
        if self.coordination == self.upstream:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation coordination relation must connect two distinct "
                "exact coordination refs"
            )


def _canonical_relation(
    relation: PilotObservationCoordinationRelation,
) -> PilotObservationCoordinationRelation:
    if relation.relation_kind is not PilotObservationCoordinationRelationKind.ALIAS_OF:
        return relation
    if _coordination_sort_key(relation.coordination) <= _coordination_sort_key(
        relation.upstream
    ):
        return relation
    return PilotObservationCoordinationRelation(
        PilotObservationCoordinationRelationKind.ALIAS_OF,
        relation.upstream,
        relation.coordination,
    )


def _relation_sort_key(
    relation: PilotObservationCoordinationRelation,
) -> tuple[str, str, str, str, str]:
    return (
        relation.relation_kind.value,
        relation.coordination.kind.value,
        relation.coordination.ref,
        relation.upstream.kind.value,
        relation.upstream.ref,
    )


def _validate_coordination_lineage_graph(
    relations: tuple[PilotObservationCoordinationRelation, ...],
) -> None:
    nodes = {
        coordination
        for relation in relations
        for coordination in (relation.coordination, relation.upstream)
    }
    parent = {node: node for node in nodes}

    def find(node: _coordination.PilotObservationCoordinationRef):
        root = node
        while parent[root] != root:
            root = parent[root]
        while parent[node] != node:
            next_node = parent[node]
            parent[node] = root
            node = next_node
        return root

    def union(
        left: _coordination.PilotObservationCoordinationRef,
        right: _coordination.PilotObservationCoordinationRef,
    ) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root == right_root:
            return
        if _coordination_sort_key(left_root) <= _coordination_sort_key(right_root):
            parent[right_root] = left_root
        else:
            parent[left_root] = right_root

    for relation in relations:
        if relation.relation_kind is PilotObservationCoordinationRelationKind.ALIAS_OF:
            union(relation.coordination, relation.upstream)

    collapsed_edges: dict[
        tuple[
            _coordination.PilotObservationCoordinationRef,
            _coordination.PilotObservationCoordinationRef,
        ],
        PilotObservationCoordinationRelationKind,
    ] = {}
    adjacency: dict[
        _coordination.PilotObservationCoordinationRef,
        set[_coordination.PilotObservationCoordinationRef],
    ] = {}

    for relation in relations:
        if relation.relation_kind is PilotObservationCoordinationRelationKind.ALIAS_OF:
            continue
        coordination_root = find(relation.coordination)
        upstream_root = find(relation.upstream)
        if coordination_root == upstream_root:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "directed observation coordination relation must not collapse "
                "within one alias class"
            )
        pair = (coordination_root, upstream_root)
        previous_kind = collapsed_edges.get(pair)
        if previous_kind is not None and previous_kind is not relation.relation_kind:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation coordination lineage graph has conflicting directed "
                "relation kinds after alias contraction"
            )
        collapsed_edges[pair] = relation.relation_kind
        adjacency.setdefault(coordination_root, set()).add(upstream_root)

    visiting: set[_coordination.PilotObservationCoordinationRef] = set()
    visited: set[_coordination.PilotObservationCoordinationRef] = set()

    def visit(node: _coordination.PilotObservationCoordinationRef) -> None:
        if node in visited:
            return
        if node in visiting:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation coordination lineage graph must be acyclic after "
                "alias contraction"
            )
        visiting.add(node)
        for upstream in sorted(
            adjacency.get(node, ()),
            key=_coordination_sort_key,
        ):
            visit(upstream)
        visiting.remove(node)
        visited.add(node)

    for node in sorted({find(item) for item in nodes}, key=_coordination_sort_key):
        visit(node)


@dataclass(frozen=True, slots=True)
class PilotObservationCoordinationLineageGraph:
    """Private declaration of known dependence-relevant coordination lineage.

    Empty/incomplete means only that no additional relations were supplied.
    It never proves coordination/control independence.
    """

    relations: tuple[PilotObservationCoordinationRelation, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.relations, tuple):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation coordination lineage graph relations must be a tuple"
            )
        if any(
            not isinstance(item, PilotObservationCoordinationRelation)
            for item in self.relations
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation coordination lineage graph must contain "
                "PilotObservationCoordinationRelation values"
            )

        canonical = tuple(_canonical_relation(item) for item in self.relations)
        if len(set(canonical)) != len(canonical):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation coordination lineage graph must not repeat an exact "
                "or reverse-alias relation"
            )

        directed_pairs: dict[
            tuple[
                _coordination.PilotObservationCoordinationRef,
                _coordination.PilotObservationCoordinationRef,
            ],
            PilotObservationCoordinationRelationKind,
        ] = {}
        for relation in canonical:
            if relation.relation_kind is PilotObservationCoordinationRelationKind.ALIAS_OF:
                continue
            pair = (relation.coordination, relation.upstream)
            previous_kind = directed_pairs.get(pair)
            if previous_kind is not None and previous_kind is not relation.relation_kind:
                raise _materialization.InvalidPilotEvidenceMaterialization(
                    "observation coordination lineage graph must not assign "
                    "conflicting relation kinds to one directed pair"
                )
            directed_pairs[pair] = relation.relation_kind

        canonical = tuple(sorted(canonical, key=_relation_sort_key))
        _validate_coordination_lineage_graph(canonical)
        object.__setattr__(self, "relations", canonical)


def pilot_observation_coordination_lineage_closure_keys_v1(
    coordination: _coordination.PilotObservationCoordinationRef,
    graph: PilotObservationCoordinationLineageGraph,
) -> tuple[str, ...]:
    """Return exact keys reachable through alias/upstream control lineage.

    ALIAS_OF is traversed both directions. Directed relations are traversed
    downstream -> upstream only. The result is declared lineage, not exhaustive
    causal ancestry or an independence certificate.
    """

    if not isinstance(
        coordination,
        _coordination.PilotObservationCoordinationRef,
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "coordination must be PilotObservationCoordinationRef"
        )
    if not isinstance(graph, PilotObservationCoordinationLineageGraph):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "graph must be PilotObservationCoordinationLineageGraph"
        )

    adjacency: dict[
        _coordination.PilotObservationCoordinationRef,
        set[_coordination.PilotObservationCoordinationRef],
    ] = {}
    for relation in graph.relations:
        if relation.relation_kind is PilotObservationCoordinationRelationKind.ALIAS_OF:
            adjacency.setdefault(relation.coordination, set()).add(relation.upstream)
            adjacency.setdefault(relation.upstream, set()).add(relation.coordination)
        else:
            adjacency.setdefault(relation.coordination, set()).add(relation.upstream)

    pending = [coordination]
    reachable: set[_coordination.PilotObservationCoordinationRef] = set()
    while pending:
        current = pending.pop()
        if current in reachable:
            continue
        reachable.add(current)
        pending.extend(
            sorted(
                adjacency.get(current, ()),
                key=_coordination_sort_key,
                reverse=True,
            )
        )

    return tuple(
        sorted(
            _coordination.pilot_observation_coordination_dependence_key_v1(item)
            for item in reachable
        )
    )


def validate_pilot_materialized_evidence_coordination_ancestry_preconditions_v1(
    coordination_entries,
    *,
    source_lineage_graph: _source_lineage.PilotUpstreamSourceLineageGraph,
    source_completeness_review: _source_completeness.PilotUpstreamLineageCompletenessReview,
    mechanism_lineage_graph: _mechanism_lineage.PilotObservationMechanismLineageGraph,
    mechanism_completeness_review: _mechanism_completeness.PilotMechanismLineageCompletenessReview,
    coordination_lineage_graph: PilotObservationCoordinationLineageGraph,
):
    """Reject known shared coordination alias/ancestor lineage after prior gates.

    Passing means only that the entire reviewed source/mechanism ladder passed,
    no exact coordination ref was shared, and the supplied coordination graph
    exposed no common alias or upstream control lineage. Missing declarations or
    graph edges remain unknown.
    """

    if not isinstance(
        coordination_lineage_graph,
        PilotObservationCoordinationLineageGraph,
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "coordination_lineage_graph must be "
            "PilotObservationCoordinationLineageGraph"
        )

    entries = (
        _coordination.validate_pilot_materialized_evidence_shared_coordination_preconditions_v1(
            coordination_entries,
            source_lineage_graph=source_lineage_graph,
            source_completeness_review=source_completeness_review,
            mechanism_lineage_graph=mechanism_lineage_graph,
            mechanism_completeness_review=mechanism_completeness_review,
        )
    )

    seen_lineage: dict[str, object] = {}
    for entry in entries:
        evidence_id = (
            entry.mechanism_entry.upstream_lineage_entry.basis_entry.evidence.evidence_id
        )
        entry_lineage_keys: set[str] = set()
        for coordination in entry.coordination_declaration.coordinations:
            entry_lineage_keys.update(
                pilot_observation_coordination_lineage_closure_keys_v1(
                    coordination,
                    coordination_lineage_graph,
                )
            )

        for key in sorted(entry_lineage_keys):
            previous = seen_lineage.get(key)
            if previous is not None:
                raise _materialization.InvalidPilotEvidenceMaterialization(
                    "distinct materialized Pilot observations converge through one "
                    "declared cross-observation coordination/control alias/ancestry "
                    "lineage; related aliases, delegations, derivations, or state "
                    "continuations cannot satisfy PR10.1 coordination-ancestry "
                    f"independence preconditions: coordination_lineage={key}, "
                    f"first={previous}, second={evidence_id}"
                )
            seen_lineage[key] = evidence_id

    return entries
