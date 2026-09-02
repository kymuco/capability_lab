"""Stable process binding for PR12.7 runtime review-admission authority.

This module owns only the non-serializable process binding.  It does not import
`governance`; instead the governance import hardener supplies each freshly
executed governance module instance so reload/reimport cannot lose the guard.
"""

from __future__ import annotations

import os
from types import ModuleType


# Strong-reference the exact capability so Python id reuse cannot rebind a live
# authority. PID is checked independently of any governance module instance.
_ISSUED_REVIEW_PROCESS_AUTHORITIES: dict[int, tuple[object, int]] = {}


def harden_governance_review_authority(governance: ModuleType) -> None:
    """Wrap one freshly executed governance module with stable PID authority."""

    structural_issue = governance._issue_review_admission
    structural_strict = governance._strict_review_admission

    def issue_with_process_binding(
        *,
        review,
        predecessor_review_ledger,
        transition_successor_review_ledger,
        current_review_ledger,
    ):
        admission = structural_issue(
            review=review,
            predecessor_review_ledger=predecessor_review_ledger,
            transition_successor_review_ledger=transition_successor_review_ledger,
            current_review_ledger=current_review_ledger,
        )
        _ISSUED_REVIEW_PROCESS_AUTHORITIES[id(admission)] = (
            admission,
            os.getpid(),
        )
        return admission

    def strict_with_process_binding(value):
        value = structural_strict(value)
        issued = _ISSUED_REVIEW_PROCESS_AUTHORITIES.get(id(value))
        if issued is None or issued[0] is not value:
            governance._fail(
                "review admission process authority was not issued by the governed "
                "terminal-review admission path"
            )
        if issued[1] != os.getpid():
            governance._fail(
                "review admission process authority belongs to a different process"
            )
        return value

    governance._issue_review_admission = issue_with_process_binding
    governance._strict_review_admission = strict_with_process_binding


def clear_review_process_authorities_after_fork_v1() -> None:
    """Drop the child copy of all issued review-process authority."""

    _ISSUED_REVIEW_PROCESS_AUTHORITIES.clear()
