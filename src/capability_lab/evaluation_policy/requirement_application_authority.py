"""Stable process-local authority store for PR12.11 mapping-review admissions."""

from __future__ import annotations

import os


_ISSUED_MAPPING_REVIEW_AUTHORITIES: dict[int, tuple[object, int, tuple[object, ...]]] = {}


def issue_mapping_review_process_authority_v1(
    admission: object,
    payload: tuple[object, ...],
) -> None:
    _ISSUED_MAPPING_REVIEW_AUTHORITIES[id(admission)] = (
        admission,
        os.getpid(),
        payload,
    )


def require_mapping_review_process_authority_v1(
    admission: object,
    payload: tuple[object, ...],
) -> None:
    issued = _ISSUED_MAPPING_REVIEW_AUTHORITIES.get(id(admission))
    if issued is None or issued[0] is not admission:
        raise ValueError(
            "mapping review admission process authority was not issued by the governed terminal-review admission path"
        )
    if issued[1] != os.getpid():
        raise ValueError("mapping review admission process authority belongs to a different process")
    if issued[2] != payload:
        raise ValueError("mapping review admission no longer matches its issued transition")


def clear_mapping_review_process_authorities_after_fork_v1() -> None:
    _ISSUED_MAPPING_REVIEW_AUTHORITIES.clear()
