"""Stable identifiers for shared capability semantics."""

from __future__ import annotations

from dataclasses import dataclass
import re

from .errors import InvalidIdentifierError

_NAMESPACE_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*$")
_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def validate_namespace_id(value: str) -> str:
    if not isinstance(value, str) or not _NAMESPACE_RE.fullmatch(value):
        raise InvalidIdentifierError(
            "namespace id must match [a-z][a-z0-9_]*(.[a-z][a-z0-9_]*)*"
        )
    return value


def validate_key(value: str, *, field_name: str = "key") -> str:
    if not isinstance(value, str) or not _KEY_RE.fullmatch(value):
        raise InvalidIdentifierError(f"{field_name} must match [a-z][a-z0-9_]*")
    return value


@dataclass(frozen=True, order=True, slots=True)
class CapabilityId:
    """Stable identity independent of display name and graph placement."""

    namespace: str
    key: str

    def __post_init__(self) -> None:
        validate_namespace_id(self.namespace)
        validate_key(self.key, field_name="capability key")

    @classmethod
    def parse(cls, value: str) -> "CapabilityId":
        if not isinstance(value, str) or value.count(":") != 1:
            raise InvalidIdentifierError("capability id must use '<namespace>:<key>'")
        namespace, key = value.split(":", 1)
        return cls(namespace=namespace, key=key)

    def __str__(self) -> str:
        return f"{self.namespace}:{self.key}"
