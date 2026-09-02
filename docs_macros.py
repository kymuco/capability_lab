from __future__ import annotations

from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parent
_ALLOWED_CONTRACTS = frozenset(
    {
        "COMMERCIAL-LICENSING.md",
        "LICENSE-HISTORY.md",
        "PUBLICATION.md",
        "SECURITY.md",
    }
)


def _include_contract(name: str) -> str:
    if name not in _ALLOWED_CONTRACTS:
        raise ValueError(f"unsupported documentation contract: {name!r}")
    return (_REPO_ROOT / name).read_text(encoding="utf-8")


def define_env(env) -> None:
    env.macro(_include_contract, "include_contract")
