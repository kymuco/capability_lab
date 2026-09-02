"""Declared mechanism-to-mechanism lineage governance for PR10.1 Pilot 01."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from . import materialization as _materialization
from . import materialization_lineage_completeness as _completeness
from . import materialization_mechanism_dependence as _mechanism
from . import materialization_source_lineage as _source_lineage


def _mechanism_sort_key(
    mechanism: _mechanism.PilotObservationMechanismRef,
) -> tuple[str, str]:
    return (mechanism.kind.value, mechanism.ref)


class PilotObservationMechanismRelationKind(str, Enum):
    """Explicit dependence-relevant mechanism lineage relations.

    For CLONED_FROM, DERIVED_FROM, and STATE_CONTINUATION_OF, ``mechanism`` is
    the downstream mechanism identity and ``upstream`` is its declared parent.
    ALIAS_OF is symmetric.

    These relations are not generic family/type relationships. An edge is meant
    to assert known lineage relevant to dependence governance for the reviewed
    observation basis.
    """

    ALIAS_OF = "ALIAS_OF"
    CLONED_FROM = "CLONED_FROM"
    DERIVED_FROM = "DERIVED_FROM"
    STATE_CONTINUATION_OF = "STATE_CONTINUATION_OF"


@dataclass(frozen=True, slots=True)
class PilotObservationMechanismRelation:
    """One explicit dependence-relevant relation between mechanism identities."""

    relation_kind: PilotObservationMechanismRelationKind
    mechanism: _mechanism.PilotObservationMechanismRef
    upstream: _mechanism.PilotObservationMechanismRef

    def __post_init__(self) -> None:
        if not isinstance(
            self.relation_kind,
            PilotObservationMechanismRelationKind,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation mechanism relation kind must be PilotObservationMechanismRelationKind"
            )
        if not isinstance(
            self.mechanism,
            _mechanism.PilotObservationMechanismRef,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation mechanism relation mechanism must be PilotObservationMechanismRef"
            )
        if not isinstance(
            self.upstream,
            _mechanism.PilotObservationMechanismRef,
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation mechanism relation upstream must be PilotObservationMechanismRef"
            )
        if self.mechanism == self.upstream:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation mechanism relation must connect two distinct exact mechanism refs"
            )


def _canonical_relation(
    relation: PilotObservationMechanismRelation,
) -> PilotObservationMechanismRelation:
    if (
        relation.relation_kind
        is not PilotObservationMechanismRelationKind.ALIAS_OF
    ):
        return relation
    if _mechanism_sort_key(relation.mechanism) <= _mechanism_sort_key(
        relation.upstream
    ):
        return relation
    return PilotObservationMechanismRelation(
        PilotObservationMechanismRelationKind.ALIAS_OF,
        relation.upstream,
        relation.mechanism,
    )


def _relation_sort_key(
    relation: PilotObservationMechanismRelation,
) -> tuple[str, str, str, str, str]:
    return (
        relation.relation_kind.value,
        relation.mechanism.kind.value,
        relation.mechanism.ref,
        relation.upstream.kind.value,
        relation.upstream.ref,
    )


def _validate_mechanism_lineage_graph(
    relations: tuple[PilotObservationMechanismRelation, ...],
) -> None:
    nodes = {
        mechanism
        for relation in relations
        for mechanism in (relation.mechanism, relation.upstream)
    }
    parent = {node: node for node in nodes}

    def find(node: _mechanism.PilotObservationMechanismRef):
        root = node
        while parent[root] != root:
            root = parent[root]
        while parent[node] != node:
            next_node = parent[node]
            parent[node] = root
            node = next_node
        return root

    def union(
        left: _mechanism.PilotObservationMechanismRef,
        right: _mechanism.PilotObservationMechanismRef,
    ) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root == right_root:
            return
        if _mechanism_sort_key(left_root) <= _mechanism_sort_key(right_root):
            parent[right_root] = left_root
        else:
            parent[left_root] = right_root

    for relation in relations:
        if (
            relation.relation_kind
            is PilotObservationMechanismRelationKind.ALIAS_OF
        ):
            union(relation.mechanism, relation.upstream)

    collapsed_edges: dict[
        tuple[
            _mechanism.PilotObservationMechanismRef,
            _mechanism.PilotObservationMechanismRef,
        ],
        PilotObservationMechanismRelationKind,
    ] = {}
    adjacency: dict[
        _mechanism.PilotObservationMechanismRef,
        set[_mechanism.PilotObservationMechanismRef],
    ] = {}

    for relation in relations:
        if (
            relation.relation_kind
            is PilotObservationMechanismRelationKind.ALIAS_OF
        ):
            continue
        mechanism_root = find(relation.mechanism)
        upstream_root = find(relation.upstream)
        if mechanism_root == upstream_root:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "directed observation mechanism relation must not collapse within one alias class"
            )
        pair = (mechanism_root, upstream_root)
        previous_kind = collapsed_edges.get(pair)
        if previous_kind is not None and previous_kind is not relation.relation_kind:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation mechanism lineage graph has conflicting directed relation kinds after alias contraction"
            )
        collapsed_edges[pair] = relation.relation_kind
        adjacency.setdefault(mechanism_root, set()).add(upstream_root)

    visiting: set[_mechanism.PilotObservationMechanismRef] = set()
    visited: set[_mechanism.PilotObservationMechanismRef] = set()

    def visit(node: _mechanism.PilotObservationMechanismRef) -> None:
        if node in visited:
            return
        if node in visiting:
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation mechanism lineage graph must be acyclic after alias contraction"
            )
        visiting.add(node)
        for upstream in sorted(
            adjacency.get(node, ()),
            key=_mechanism_sort_key,
        ):
            visit(upstream)
        visiting.remove(node)
        visited.add(node)

    for node in sorted({find(item) for item in nodes}, key=_mechanism_sort_key):
        visit(node)


@dataclass(frozen=True, slots=True)
class PilotObservationMechanismLineageGraph:
    """Private declaration of known dependence-relevant mechanism lineage.

    An empty or incomplete graph means only that no additional mechanism
    relations were supplied. It never proves that represented mechanisms are
    independent.
    """

    relations: tuple[PilotObservationMechanismRelation, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.relations, tuple):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation mechanism lineage graph relations must be a tuple"
            )
        if any(
            not isinstance(item, PilotObservationMechanismRelation)
            for item in self.relations
        ):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation mechanism lineage graph must contain PilotObservationMechanismRelation values"
            )

        canonical = tuple(_canonical_relation(item) for item in self.relations)
        if len(set(canonical)) != len(canonical):
            raise _materialization.InvalidPilotEvidenceMaterialization(
                "observation mechanism lineage graph must not repeat an exact or reverse-alias relation"
            )

        directed_pairs: dict[
            tuple[
                _mechanism.PilotObservationMechanismRef,
                _mechanism.PilotObservationMechanismRef,
            ],
            PilotObservationMechanismRelationKind,
        ] = {}
        for relation in canonical:
            if (
                relation.relation_kind
                is PilotObservationMechanismRelationKind.ALIAS_OF
            ):
                continue
            pair = (relation.mechanism, relation.upstream)
            previous_kind = directed_pairs.get(pair)
            if previous_kind is not None and previous_kind is not relation.relation_kind:
                raise _materialization.InvalidPilotEvidenceMaterialization(
                    "observation mechanism lineage graph must not assign conflicting relation kinds to one directed pair"
                )
            directed_pairs[pair] = relation.relation_kind

        canonical = tuple(sorted(canonical, key=_relation_sort_key))
        _validate_mechanism_lineage_graph(canonical)
        object.__setattr__(self, "relations", canonical)


def pilot_observation_mechanism_lineage_closure_keys_v1(
    mechanism: _mechanism.PilotObservationMechanismRef,
    graph: PilotObservationMechanismLineageGraph,
) -> tuple[str, ...]:
    """Return exact mechanism keys reachable through alias/upstream lineage.

    The closure always contains ``mechanism`` itself. ALIAS_OF is traversed in
    both directions. Directed relations are traversed only downstream -> upstream.
    The result describes declared dependence-relevant lineage, not exhaustive
    causal ancestry.
    """

    if not isinstance(
        mechanism,
        _mechanism.PilotObservationMechanismRef,
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "mechanism must be PilotObservationMechanismRef"
        )
    if not isinstance(graph, PilotObservationMechanismLineageGraph):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "graph must be PilotObservationMechanismLineageGraph"
        )

    adjacency: dict[
        _mechanism.PilotObservationMechanismRef,
        set[_mechanism.PilotObservationMechanismRef],
    ] = {}
    for relation in graph.relations:
        if (
            relation.relation_kind
            is PilotObservationMechanismRelationKind.ALIAS_OF
        ):
            adjacency.setdefault(relation.mechanism, set()).add(relation.upstream)
            adjacency.setdefault(relation.upstream, set()).add(relation.mechanism)
        else:
            adjacency.setdefault(relation.mechanism, set()).add(relation.upstream)

    pending = [mechanism]
    reachable: set[_mechanism.PilotObservationMechanismRef] = set()
    while pending:
        current = pending.pop()
        if current in reachable:
            continue
        reachable.add(current)
        pending.extend(
            sorted(
                adjacency.get(current, ()),
                key=_mechanism_sort_key,
                reverse=True,
            )
        )

    return tuple(
        sorted(
            _mechanism.pilot_observation_mechanism_dependence_key_v1(item)
            for item in reachable
        )
    )


def validate_pilot_materialized_evidence_mechanism_ancestry_preconditions_v1(
    mechanism_entries,
    *,
    source_lineage_graph: _source_lineage.PilotUpstreamSourceLineageGraph,
    completeness_review: _completeness.PilotUpstreamLineageCompletenessReview,
    mechanism_lineage_graph: PilotObservationMechanismLineageGraph,
):
    """Reject known shared mechanism alias/ancestor lineage after prior gates.

    Passing means only that reviewed source-origin preconditions passed, no exact
    mechanism ref was shared, and the supplied mechanism graph did not expose a
    common alias or declared upstream mechanism lineage. Missing mechanism
    declarations or graph edges remain unknown.
    """

    if not isinstance(
        mechanism_lineage_graph,
        PilotObservationMechanismLineageGraph,
    ):
        raise _materialization.InvalidPilotEvidenceMaterialization(
            "mechanism_lineage_graph must be PilotObservationMechanismLineageGraph"
        )

    entries = (
        _mechanism.validate_pilot_materialized_evidence_shared_mechanism_preconditions_v1(
            mechanism_entries,
            source_lineage_graph=source_lineage_graph,
            completeness_review=completeness_review,
        )
    )

    seen_lineage: dict[str, object] = {}
    for entry in entries:
        evidence_id = (
            entry.upstream_lineage_entry.basis_entry.evidence.evidence_id
        )
        entry_lineage_keys: set[str] = set()
        for mechanism in entry.mechanism_declaration.mechanisms:
            entry_lineage_keys.update(
                pilot_observation_mechanism_lineage_closure_keys_v1(
                    mechanism,
                    mechanism_lineage_graph,
                )
            )

        for key in sorted(entry_lineage_keys):
            previous = seen_lineage.get(key)
            if previous is not None:
                raise _materialization.InvalidPilotEvidenceMaterialization(
                    "distinct materialized Pilot observations converge through one "
                    "declared acquisition/governance mechanism alias/ancestry lineage; "
                    "related aliases, clones, derivations, or state continuations "
                    "cannot satisfy PR10.1 mechanism-ancestry independence preconditions: "
                    f"mechanism_lineage={key}, first={previous}, second={evidence_id}"
                )
            seen_lineage[key] = evidence_id

    return entries
