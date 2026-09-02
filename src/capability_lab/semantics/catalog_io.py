"""Schema-v1 codec for shared capability catalog snapshots."""

from __future__ import annotations

from typing import Any, Mapping

from .concept import CapabilityConcept, ConceptLifecycle
from .errors import CapabilitySemanticsError, InvalidCatalogError
from .ids import CapabilityId
from .namespace import CapabilityNamespace
from .relation import CapabilityRelation, RelationKind, RelationScope, RelationStrength
from .serialization import reject_unknown_keys, require_mapping, require_sequence

CATALOG_SCHEMA = "capability_catalog/v1"

_ROOT_KEYS = {"schema", "namespaces", "concepts", "relations"}
_NAMESPACE_KEYS = {"namespace_id", "display_name", "description"}
_CONCEPT_KEYS = {
    "capability_id", "name", "definition", "aliases", "revision",
    "lifecycle", "deprecation_note",
}
_RELATION_KEYS = {
    "source_id", "target_id", "kind", "scope", "strength", "provenance_refs",
}
_SCOPE_KEYS = {"key", "description"}


def catalog_to_dict(catalog) -> dict[str, Any]:
    return {
        "schema": CATALOG_SCHEMA,
        "namespaces": [
            {
                "namespace_id": item.namespace_id,
                "display_name": item.display_name,
                "description": item.description,
            }
            for item in catalog.namespaces
        ],
        "concepts": [
            {
                "capability_id": str(item.capability_id),
                "name": item.name,
                "definition": item.definition,
                "aliases": list(item.aliases),
                "revision": item.revision,
                "lifecycle": item.lifecycle.value,
                "deprecation_note": item.deprecation_note,
            }
            for item in catalog.concepts
        ],
        "relations": [
            {
                "source_id": str(item.source_id),
                "target_id": str(item.target_id),
                "kind": item.kind.value,
                "scope": (
                    {"key": item.scope.key, "description": item.scope.description}
                    if item.scope is not None else None
                ),
                "strength": item.strength.value,
                "provenance_refs": list(item.provenance_refs),
            }
            for item in catalog.relations
        ],
    }


def decode_catalog_parts(payload: Mapping[str, Any]):
    root = require_mapping(payload, context="catalog payload")
    reject_unknown_keys(root, allowed=_ROOT_KEYS, context="catalog payload")
    if root.get("schema") != CATALOG_SCHEMA:
        raise InvalidCatalogError("unsupported or missing catalog schema")

    try:
        namespaces = []
        for index, raw in enumerate(require_sequence(root.get("namespaces", []), context="namespaces")):
            item = require_mapping(raw, context=f"namespaces[{index}]")
            reject_unknown_keys(item, allowed=_NAMESPACE_KEYS, context=f"namespaces[{index}]")
            namespaces.append(
                CapabilityNamespace(
                    namespace_id=item["namespace_id"],
                    display_name=item["display_name"],
                    description=item.get("description", ""),
                )
            )

        concepts = []
        for index, raw in enumerate(require_sequence(root.get("concepts", []), context="concepts")):
            item = require_mapping(raw, context=f"concepts[{index}]")
            reject_unknown_keys(item, allowed=_CONCEPT_KEYS, context=f"concepts[{index}]")
            aliases = require_sequence(item.get("aliases", []), context=f"concepts[{index}].aliases")
            concepts.append(
                CapabilityConcept(
                    capability_id=CapabilityId.parse(item["capability_id"]),
                    name=item["name"],
                    definition=item["definition"],
                    aliases=tuple(aliases),
                    revision=item.get("revision", 1),
                    lifecycle=ConceptLifecycle(item.get("lifecycle", "active")),
                    deprecation_note=item.get("deprecation_note"),
                )
            )

        relations = []
        for index, raw in enumerate(require_sequence(root.get("relations", []), context="relations")):
            item = require_mapping(raw, context=f"relations[{index}]")
            reject_unknown_keys(item, allowed=_RELATION_KEYS, context=f"relations[{index}]")
            raw_scope = item.get("scope")
            if raw_scope is None:
                scope = None
            else:
                scope_item = require_mapping(raw_scope, context=f"relations[{index}].scope")
                reject_unknown_keys(scope_item, allowed=_SCOPE_KEYS, context=f"relations[{index}].scope")
                scope = RelationScope(scope_item["key"], scope_item["description"])
            refs = require_sequence(
                item.get("provenance_refs", []),
                context=f"relations[{index}].provenance_refs",
            )
            relations.append(
                CapabilityRelation(
                    source_id=CapabilityId.parse(item["source_id"]),
                    target_id=CapabilityId.parse(item["target_id"]),
                    kind=RelationKind(item["kind"]),
                    scope=scope,
                    strength=RelationStrength(item.get("strength", "unspecified")),
                    provenance_refs=tuple(refs),
                )
            )
    except InvalidCatalogError:
        raise
    except (CapabilitySemanticsError, KeyError, TypeError, ValueError) as exc:
        raise InvalidCatalogError(f"invalid catalog payload: {exc}") from exc

    return tuple(namespaces), tuple(concepts), tuple(relations)
