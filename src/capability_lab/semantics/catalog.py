"""Immutable deterministic catalog for shared capability semantics."""

from __future__ import annotations

from dataclasses import dataclass
import heapq
import json
from typing import Any, Mapping

from .catalog_io import catalog_to_dict, decode_catalog_parts
from .concept import CapabilityConcept
from .errors import InvalidCatalogError
from .ids import CapabilityId
from .namespace import CapabilityNamespace
from .relation import CapabilityRelation, RelationKind
from .serialization import loads_strict_json


@dataclass(frozen=True, slots=True)
class CapabilityCatalog:
    """A local semantic graph snapshot, not the Human Capability Commons."""

    namespaces: tuple[CapabilityNamespace, ...] = ()
    concepts: tuple[CapabilityConcept, ...] = ()
    relations: tuple[CapabilityRelation, ...] = ()

    def __post_init__(self) -> None:
        try:
            raw_namespaces = tuple(self.namespaces)
            raw_concepts = tuple(self.concepts)
            raw_relations = tuple(self.relations)
        except TypeError as exc:
            raise InvalidCatalogError("catalog collections must be iterable") from exc

        if any(not isinstance(item, CapabilityNamespace) for item in raw_namespaces):
            raise InvalidCatalogError("catalog namespaces must contain CapabilityNamespace values")
        if any(not isinstance(item, CapabilityConcept) for item in raw_concepts):
            raise InvalidCatalogError("catalog concepts must contain CapabilityConcept values")
        if any(not isinstance(item, CapabilityRelation) for item in raw_relations):
            raise InvalidCatalogError("catalog relations must contain CapabilityRelation values")

        namespaces = tuple(sorted(raw_namespaces, key=lambda item: item.namespace_id))
        concepts = tuple(sorted(raw_concepts, key=lambda item: item.capability_id))
        relations = tuple(sorted(raw_relations, key=lambda item: item.deterministic_key))

        namespace_ids = [item.namespace_id for item in namespaces]
        duplicate_namespace_ids = _duplicates(namespace_ids)
        if duplicate_namespace_ids:
            raise InvalidCatalogError(f"duplicate namespace ids: {', '.join(duplicate_namespace_ids)}")

        concept_ids = [item.capability_id for item in concepts]
        duplicate_concept_ids = _duplicates(concept_ids)
        if duplicate_concept_ids:
            raise InvalidCatalogError(
                "duplicate capability ids: "
                + ", ".join(str(item) for item in duplicate_concept_ids)
            )

        namespace_set = set(namespace_ids)
        concept_set = set(concept_ids)
        for concept in concepts:
            if concept.capability_id.namespace not in namespace_set:
                raise InvalidCatalogError(
                    f"concept references unknown namespace: {concept.capability_id}"
                )

        relation_keys: set[tuple[str, str, str, str]] = set()
        for relation in relations:
            if relation.source_id not in concept_set:
                raise InvalidCatalogError(
                    f"relation source is not present in catalog: {relation.source_id}"
                )
            if relation.target_id not in concept_set:
                raise InvalidCatalogError(
                    f"relation target is not present in catalog: {relation.target_id}"
                )
            if relation.semantic_key in relation_keys:
                raise InvalidCatalogError(
                    "duplicate semantic relation: " + repr(relation.semantic_key)
                )
            relation_keys.add(relation.semantic_key)

        _validate_specialization_acyclic(concepts, relations)

        object.__setattr__(self, "namespaces", namespaces)
        object.__setattr__(self, "concepts", concepts)
        object.__setattr__(self, "relations", relations)

    def to_dict(self) -> dict[str, Any]:
        return catalog_to_dict(self)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "CapabilityCatalog":
        namespaces, concepts, relations = decode_catalog_parts(payload)
        return cls(namespaces=namespaces, concepts=concepts, relations=relations)

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )

    @classmethod
    def from_json(cls, payload: str) -> "CapabilityCatalog":
        return cls.from_dict(loads_strict_json(payload))


def _duplicates(values):
    seen = set()
    duplicates = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def _validate_specialization_acyclic(
    concepts: tuple[CapabilityConcept, ...],
    relations: tuple[CapabilityRelation, ...],
) -> None:
    adjacency: dict[CapabilityId, set[CapabilityId]] = {
        concept.capability_id: set() for concept in concepts
    }
    indegree: dict[CapabilityId, int] = {node: 0 for node in adjacency}

    for relation in relations:
        if relation.kind is RelationKind.SPECIALIZES:
            if relation.target_id not in adjacency[relation.source_id]:
                adjacency[relation.source_id].add(relation.target_id)
                indegree[relation.target_id] += 1

    ready = [node for node, degree in indegree.items() if degree == 0]
    heapq.heapify(ready)
    visited = 0

    while ready:
        node = heapq.heappop(ready)
        visited += 1
        for target in sorted(adjacency[node]):
            indegree[target] -= 1
            if indegree[target] == 0:
                heapq.heappush(ready, target)

    if visited != len(adjacency):
        raise InvalidCatalogError("SPECIALIZES relations must be acyclic")
