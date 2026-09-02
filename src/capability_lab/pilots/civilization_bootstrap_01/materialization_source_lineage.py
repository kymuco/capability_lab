"""Declared source-to-source lineage governance for PR10.1 Pilot 01 evidence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from . import materialization as _materialization
from . import materialization_dependence as _dependence


def _source_sort_key(source: _dependence.PilotUpstreamSourceRef) -> tuple[str, str]:
    return (source.kind.value, source.ref)


class PilotUpstreamSourceRelationKind(str, Enum):
    """Explicit source-to-source lineage relations.

    For COPY_OF, TRANSFORM_OF, and DERIVED_FROM, ``source`` is the downstream
    value and ``upstream`` is its declared parent. ALIAS_OF is symmetric.
    """

    ALIAS_OF = "ALIAS_OF"
    COPY_OF = "COPY_OF"
    TRANSFORM_OF = "TRANSFORM_OF"
    DERIVED_FROM = "DERIVED_FROM"


@dataclass(frozen=True, slots=True)
class PilotUpstreamSourceRelation:
    """One explicit relation between two governed upstream-source identities."""

    relation_kind: PilotUpstreamSourceRelationKind
    source: _dependence.PilotUpstreamSourceRef
    upstream: _dependence.PilotUpstreamSourceRef

    def __post_init__(self) -> None:
        if not isinstance(self.relation_kind, PilotUpstreamSourceRelationKind):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "upstream source relation kind must be PilotUpstreamSourceRelationKind"
            )
        if not isinstance(self.source, _dependence.PilotUpstreamSourceRef):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "upstream source relation source must be PilotUpstreamSourceRef"
            )
        if not isinstance(self.upstream, _dependence.PilotUpstreamSourceRef):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "upstream source relation upstream must be PilotUpstreamSourceRef"
            )
        if self.source == self.upstream:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "upstream source relation must connect two distinct exact source refs"
            )


def _canonical_relation(
    relation: PilotUpstreamSourceRelation,
) -> PilotUpstreamSourceRelation:
    if relation.relation_kind is not PilotUpstreamSourceRelationKind.ALIAS_OF:
        return relation
    if _source_sort_key(relation.source) <= _source_sort_key(relation.upstream):
        return relation
    return PilotUpstreamSourceRelation(
        PilotUpstreamSourceRelationKind.ALIAS_OF,
        relation.upstream,
        relation.source,
    )


def _relation_sort_key(
    relation: PilotUpstreamSourceRelation,
) -> tuple[str, str, str, str, str]:
    return (
        relation.relation_kind.value,
        relation.source.kind.value,
        relation.source.ref,
        relation.upstream.kind.value,
        relation.upstream.ref,
    )


def _validate_lineage_graph(
    relations: tuple[PilotUpstreamSourceRelation, ...],
) -> None:
    nodes = {
        source
        for relation in relations
        for source in (relation.source, relation.upstream)
    }
    parent = {node: node for node in nodes}

    def find(node: _dependence.PilotUpstreamSourceRef):
        root = node
        while parent[root] != root:
            root = parent[root]
        while parent[node] != node:
            next_node = parent[node]
            parent[node] = root
            node = next_node
        return root

    def union(
        left: _dependence.PilotUpstreamSourceRef,
        right: _dependence.PilotUpstreamSourceRef,
    ) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root == right_root:
            return
        if _source_sort_key(left_root) <= _source_sort_key(right_root):
            parent[right_root] = left_root
        else:
            parent[left_root] = right_root

    for relation in relations:
        if relation.relation_kind is PilotUpstreamSourceRelationKind.ALIAS_OF:
            union(relation.source, relation.upstream)

    collapsed_edges: dict[
        tuple[
            _dependence.PilotUpstreamSourceRef,
            _dependence.PilotUpstreamSourceRef,
        ],
        PilotUpstreamSourceRelationKind,
    ] = {}
    adjacency: dict[
        _dependence.PilotUpstreamSourceRef,
        set[_dependence.PilotUpstreamSourceRef],
    ] = {}

    for relation in relations:
        if relation.relation_kind is PilotUpstreamSourceRelationKind.ALIAS_OF:
            continue
        source_root = find(relation.source)
        upstream_root = find(relation.upstream)
        if source_root == upstream_root:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "directed upstream source relation must not collapse within one alias class"
            )
        pair = (source_root, upstream_root)
        previous_kind = collapsed_edges.get(pair)
        if previous_kind is not None and previous_kind is not relation.relation_kind:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "upstream source lineage graph has conflicting directed relation kinds after alias contraction"
            )
        collapsed_edges[pair] = relation.relation_kind
        adjacency.setdefault(source_root, set()).add(upstream_root)

    visiting: set[_dependence.PilotUpstreamSourceRef] = set()
    visited: set[_dependence.PilotUpstreamSourceRef] = set()

    def visit(node: _dependence.PilotUpstreamSourceRef) -> None:
        if node in visited:
            return
        if node in visiting:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "upstream source lineage graph must be acyclic after alias contraction"
            )
        visiting.add(node)
        for upstream in sorted(adjacency.get(node, ()), key=_source_sort_key):
            visit(upstream)
        visiting.remove(node)
        visited.add(node)

    for node in sorted({find(item) for item in nodes}, key=_source_sort_key):
        visit(node)


@dataclass(frozen=True, slots=True)
class PilotUpstreamSourceLineageGraph:
    """Private declaration of known alias and directed source ancestry relations.

    An empty or incomplete graph means only that no additional relations were
    supplied. It never proves that the represented sources are independent.
    """

    relations: tuple[PilotUpstreamSourceRelation, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.relations, tuple):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "upstream source lineage graph relations must be a tuple"
            )
        if any(
            not isinstance(item, PilotUpstreamSourceRelation)
            for item in self.relations
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "upstream source lineage graph must contain PilotUpstreamSourceRelation values"
            )

        canonical = tuple(_canonical_relation(item) for item in self.relations)
        if len(set(canonical)) != len(canonical):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "upstream source lineage graph must not repeat an exact or reverse-alias relation"
            )

        directed_pairs: dict[
            tuple[
                _dependence.PilotUpstreamSourceRef,
                _dependence.PilotUpstreamSourceRef,
            ],
            PilotUpstreamSourceRelationKind,
        ] = {}
        for relation in canonical:
            if relation.relation_kind is PilotUpstreamSourceRelationKind.ALIAS_OF:
                continue
            pair = (relation.source, relation.upstream)
            previous_kind = directed_pairs.get(pair)
            if previous_kind is not None and previous_kind is not relation.relation_kind:
                raise _materialization.InvalidPilotEvidenceMaterialization(
                    "upstream source lineage graph must not assign conflicting relation kinds to one directed pair"
                )
            directed_pairs[pair] = relation.relation_kind

        canonical = tuple(sorted(canonical, key=_relation_sort_key))
        _validate_lineage_graph(canonical)
        object.__setattr__(self, "relations", canonical)


def pilot_upstream_source_lineage_closure_keys_v1(
    source: _dependence.PilotUpstreamSourceRef,
    graph: PilotUpstreamSourceLineageGraph,
) -> tuple[str, ...]:
    """Return exact-source keys reachable through alias or declared upstream ancestry.

    The closure always includes ``source`` itself. ALIAS_OF is traversed in both
    directions. COPY_OF, TRANSFORM_OF, and DERIVED_FROM are traversed only from
    downstream source to upstream parent. The result describes declared lineage,
    not exhaustive causal ancestry.
    """

    if not isinstance(source, _dependence.PilotUpstreamSourceRef):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "source must be PilotUpstreamSourceRef"
        )
    if not isinstance(graph, PilotUpstreamSourceLineageGraph):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "graph must be PilotUpstreamSourceLineageGraph"
        )

    adjacency: dict[
        _dependence.PilotUpstreamSourceRef,
        set[_dependence.PilotUpstreamSourceRef],
    ] = {}
    for relation in graph.relations:
        if relation.relation_kind is PilotUpstreamSourceRelationKind.ALIAS_OF:
            adjacency.setdefault(relation.source, set()).add(relation.upstream)
            adjacency.setdefault(relation.upstream, set()).add(relation.source)
        else:
            adjacency.setdefault(relation.source, set()).add(relation.upstream)

    pending = [source]
    reachable: set[_dependence.PilotUpstreamSourceRef] = set()
    while pending:
        current = pending.pop()
        if current in reachable:
            continue
        reachable.add(current)
        pending.extend(
            sorted(adjacency.get(current, ()), key=_source_sort_key, reverse=True)
        )

    return tuple(
        sorted(
            _dependence.pilot_upstream_source_dependence_key_v1(item)
            for item in reachable
        )
    )


def validate_pilot_materialized_evidence_source_ancestry_preconditions_v1(
    lineage_entries,
    *,
    source_lineage_graph: PilotUpstreamSourceLineageGraph,
):
    """Reject known shared alias/ancestor lineage after all earlier PR10.1 gates.

    Passing means only that the supplied graph did not expose a common exact
    source, alias, or declared ancestor across observations. Missing graph edges,
    hidden common sources, and undeclared ancestry remain unknown.
    """

    if not isinstance(source_lineage_graph, PilotUpstreamSourceLineageGraph):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "source_lineage_graph must be PilotUpstreamSourceLineageGraph"
        )

    entries = (
        _dependence.validate_pilot_materialized_evidence_upstream_lineage_preconditions_v1(
            lineage_entries
        )
    )

    seen_lineage: dict[str, object] = {}
    for entry in entries:
        entry_lineage_keys: set[str] = set()
        for source in entry.upstream_declaration.sources:
            entry_lineage_keys.update(
                pilot_upstream_source_lineage_closure_keys_v1(
                    source,
                    source_lineage_graph,
                )
            )

        for key in sorted(entry_lineage_keys):
            previous = seen_lineage.get(key)
            if previous is not None:
                raise _materialization.InvalidPilotEvidenceMaterialization(
                    "distinct materialized Pilot observations converge through one "
                    "declared upstream source alias/ancestry lineage; related copies, "
                    "transforms, aliases, or descendants cannot satisfy PR10.1 "
                    "source-ancestry independence preconditions: "
                    f"source_lineage={key}, first={previous}, "
                    f"second={entry.basis_entry.evidence.evidence_id}"
                )
            seen_lineage[key] = entry.basis_entry.evidence.evidence_id

    return entries
