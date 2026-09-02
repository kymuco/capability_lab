"""Strict helpers for deterministic semantic catalog ingestion."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from .errors import InvalidCatalogError


def require_mapping(value: object, *, context: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise InvalidCatalogError(f"{context} must be an object")
    for key in value:
        if not isinstance(key, str):
            raise InvalidCatalogError(f"{context} keys must be strings")
    return value


def require_sequence(value: object, *, context: str) -> Sequence[Any]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise InvalidCatalogError(f"{context} must be an array")
    return value


def reject_unknown_keys(
    value: Mapping[str, Any], *, allowed: set[str], context: str
) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise InvalidCatalogError(
            f"{context} contains unknown fields: {', '.join(unknown)}"
        )


def loads_strict_json(payload: object) -> Mapping[str, Any]:
    if not isinstance(payload, str):
        raise InvalidCatalogError("catalog JSON payload must be a string")

    def pairs_hook(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise InvalidCatalogError(f"duplicate JSON object key: {key!r}")
            result[key] = value
        return result

    def reject_constant(value: str):
        raise InvalidCatalogError(f"non-standard JSON numeric constant is not allowed: {value}")

    try:
        decoded = json.loads(
            payload,
            object_pairs_hook=pairs_hook,
            parse_constant=reject_constant,
        )
    except json.JSONDecodeError as exc:
        raise InvalidCatalogError(f"invalid catalog JSON: {exc}") from exc

    return require_mapping(decoded, context="catalog JSON root")
