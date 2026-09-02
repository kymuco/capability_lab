"""Stable process-local authority for PR12.7 policy-registry resolution.

The canonical registry/receipt values remain serializable audit data.  Each
freshly executed governance module is wrapped after execution so ordinary
import, reload, and module replacement all require exact process-local registry
admission authority before admitted-policy resolution.
"""

from __future__ import annotations

import importlib
import os
from types import ModuleType

from capability_lab.epistemics import EvaluationPolicyRef

from .specification import (
    DomainEvaluationPolicySpecification,
    _strict_policy_ref,
    _strict_specification,
    domain_evaluation_policy_specification_sha256_v1,
)


_GOVERNANCE_MODULE = "capability_lab.evaluation_policy.governance"

# Exact process-local registry authority. Strong registry references prevent
# object-id reuse while an issuance exists. PID independently blocks fork
# inheritance even when a module-specific cleanup hook is stale or absent.
_ISSUED_POLICY_REGISTRY_AUTHORITIES: dict[
    tuple[int, str],
    tuple[object, int, str, int, str, str, str, str, str],
] = {}


def _authority_key(registry: object, policy_ref: EvaluationPolicyRef) -> tuple[int, str]:
    return (id(registry), str(policy_ref))


def harden_governance_registry_authority(governance: ModuleType) -> None:
    """Wrap one freshly executed governance module's public registry surface."""

    structural_admit = governance.admit_domain_evaluation_policy_v1
    structural_resolve = governance.resolve_admitted_domain_evaluation_policy_v1

    def entry_index(*, registry, policy_ref, specification_sha256: str) -> int:
        matches = tuple(
            (index, entry)
            for index, entry in enumerate(registry.entries)
            if entry.policy_ref == policy_ref
        )
        if len(matches) != 1:
            governance._fail("policy_ref is not admitted in supplied registry")
        index, entry = matches[0]
        if entry.specification_sha256 != specification_sha256:
            governance._fail(
                "admitted policy digest does not match requested exact content"
            )
        return index

    def registry_transition_basis(*, registry, entry_index_value: int):
        return governance._receipt_for_existing_entry(
            registry=registry,
            entry_index=entry_index_value,
        )

    def issue_policy_registry_authority(
        *,
        registry,
        review_ledger,
        review_admission,
        specification: DomainEvaluationPolicySpecification,
    ) -> None:
        governance._strict_registry(registry)
        review_ledger = governance._strict_review_ledger(review_ledger)
        specification = _strict_specification(specification)
        specification_sha256 = domain_evaluation_policy_specification_sha256_v1(
            specification
        )
        index = entry_index(
            registry=registry,
            policy_ref=specification.policy_ref,
            specification_sha256=specification_sha256,
        )
        predecessor, transition_successor, receipt = registry_transition_basis(
            registry=registry,
            entry_index_value=index,
        )
        governance.validate_domain_evaluation_policy_admission_receipt_v1(
            predecessor_registry=predecessor,
            successor_registry=transition_successor,
            review_ledger=review_ledger,
            review_admission=review_admission,
            specification=specification,
            receipt=receipt,
        )
        entry = registry.entries[index]
        _ISSUED_POLICY_REGISTRY_AUTHORITIES[
            _authority_key(registry, specification.policy_ref)
        ] = (
            registry,
            os.getpid(),
            governance.domain_evaluation_policy_registry_sha256_v1(registry),
            index,
            specification_sha256,
            str(entry.review_id),
            entry.review_sha256,
            governance.domain_evaluation_policy_registry_sha256_v1(predecessor),
            governance.domain_evaluation_policy_registry_sha256_v1(
                transition_successor
            ),
        )

    def require_policy_registry_authority(
        *,
        registry,
        policy_ref: EvaluationPolicyRef,
        specification_sha256: str,
    ) -> None:
        governance._strict_registry(registry)
        policy_ref = _strict_policy_ref(policy_ref)
        specification_sha256 = governance._sha256(
            specification_sha256,
            "specification_sha256",
        )
        index = entry_index(
            registry=registry,
            policy_ref=policy_ref,
            specification_sha256=specification_sha256,
        )
        issued = _ISSUED_POLICY_REGISTRY_AUTHORITIES.get(
            _authority_key(registry, policy_ref)
        )
        if issued is None or issued[0] is not registry:
            governance._fail(
                "policy registry has no runtime admission authority for this exact "
                "policy; replay admit_domain_evaluation_policy_v1 first"
            )
        if issued[1] != os.getpid():
            governance._fail(
                "policy registry admission authority belongs to a different process"
            )
        current_registry_sha256 = governance.domain_evaluation_policy_registry_sha256_v1(
            registry
        )
        if issued[2] != current_registry_sha256:
            governance._fail(
                "policy registry admission authority is stale for the supplied registry"
            )
        if issued[3] != index or issued[4] != specification_sha256:
            governance._fail(
                "policy registry admission authority exact policy binding mismatch"
            )
        entry = registry.entries[index]
        predecessor, transition_successor, _ = registry_transition_basis(
            registry=registry,
            entry_index_value=index,
        )
        if issued[5] != str(entry.review_id) or issued[6] != entry.review_sha256:
            governance._fail(
                "policy registry admission authority review binding mismatch"
            )
        if issued[7] != governance.domain_evaluation_policy_registry_sha256_v1(
            predecessor
        ):
            governance._fail("policy registry admission predecessor digest mismatch")
        if issued[8] != governance.domain_evaluation_policy_registry_sha256_v1(
            transition_successor
        ):
            governance._fail(
                "policy registry admission transition-successor digest mismatch"
            )

    def admitted_policy_with_authority(
        *,
        registry,
        review_ledger,
        review_admission,
        specification: DomainEvaluationPolicySpecification,
        admitted_at,
    ):
        successor, receipt = structural_admit(
            registry=registry,
            review_ledger=review_ledger,
            review_admission=review_admission,
            specification=specification,
            admitted_at=admitted_at,
        )
        issue_policy_registry_authority(
            registry=successor,
            review_ledger=review_ledger,
            review_admission=review_admission,
            specification=specification,
        )
        return successor, receipt

    def resolve_with_authority(
        *,
        registry,
        policy_ref: EvaluationPolicyRef,
        specification_sha256: str,
    ) -> DomainEvaluationPolicySpecification:
        require_policy_registry_authority(
            registry=registry,
            policy_ref=policy_ref,
            specification_sha256=specification_sha256,
        )
        return structural_resolve(
            registry=registry,
            policy_ref=policy_ref,
            specification_sha256=specification_sha256,
        )

    governance.admit_domain_evaluation_policy_v1 = admitted_policy_with_authority
    governance.resolve_admitted_domain_evaluation_policy_v1 = resolve_with_authority


def admit_domain_evaluation_policy_v1(**kwargs):
    """Compatibility facade delegating to the current hardened governance module."""

    governance = importlib.import_module(_GOVERNANCE_MODULE)
    return governance.admit_domain_evaluation_policy_v1(**kwargs)


def resolve_admitted_domain_evaluation_policy_v1(**kwargs):
    """Compatibility facade delegating to the current hardened governance module."""

    governance = importlib.import_module(_GOVERNANCE_MODULE)
    return governance.resolve_admitted_domain_evaluation_policy_v1(**kwargs)


def clear_policy_registry_authorities_after_fork_v1() -> None:
    """Drop the child copy of all process-local registry authority."""

    _ISSUED_POLICY_REGISTRY_AUTHORITIES.clear()
