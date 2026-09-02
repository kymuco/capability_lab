import importlib
import os
from datetime import datetime, timezone

import pytest

from capability_lab.epistemics import ClaimScope, EvaluationPolicyRef
from capability_lab.evaluation_policy import (
    DomainEvaluationPolicyRegistry,
    DomainEvaluationPolicyRequirement,
    DomainEvaluationPolicyReviewId,
    DomainEvaluationPolicyReviewerKind,
    DomainEvaluationPolicyReviewerRef,
    DomainEvaluationPolicyReviewLedger,
    DomainEvaluationPolicyReviewVerdict,
    DomainEvaluationPolicySpecification,
    InvalidDomainEvaluationPolicyGovernance,
    admit_domain_evaluation_policy_review_v1,
    admit_domain_evaluation_policy_v1,
    domain_evaluation_policy_specification_sha256_v1,
    resolve_admitted_domain_evaluation_policy_v1,
    review_domain_evaluation_policy_specification_v1,
)
from capability_lab.semantics import CapabilityConceptRef, CapabilityId


_REVIEWED_AT = datetime(2026, 8, 31, 12, 0, tzinfo=timezone.utc)
_ADMITTED_AT = datetime(2026, 8, 31, 13, 0, tzinfo=timezone.utc)


def _specification() -> DomainEvaluationPolicySpecification:
    return DomainEvaluationPolicySpecification(
        policy_ref=EvaluationPolicyRef(
            "research",
            "registry_process_boundary_review",
            1,
        ),
        concept_ref=CapabilityConceptRef(
            CapabilityId.parse("research:signal_reasoning"),
            1,
        ),
        claim_scope=ClaimScope(
            "Bounded signal interpretation.",
            ("bounded_reasoning",),
        ),
        requirements=(
            DomainEvaluationPolicyRequirement(
                "diagnostic_reasoning",
                "Diagnoses a bounded signal case.",
                True,
            ),
        ),
    )


def _review(specification: DomainEvaluationPolicySpecification):
    return review_domain_evaluation_policy_specification_v1(
        specification=specification,
        review_id=DomainEvaluationPolicyReviewId("registry-process-review-01"),
        reviewer_ref=DomainEvaluationPolicyReviewerRef(
            DomainEvaluationPolicyReviewerKind.HUMAN,
            "human:reviewer_01",
        ),
        verdict=DomainEvaluationPolicyReviewVerdict.APPROVE,
        reviewed_at=_REVIEWED_AT,
        rationale="Reviewed exact policy before process-boundary test.",
    )


def _admit(specification, review, *, ledger=None, registry=None):
    if ledger is None:
        ledger = DomainEvaluationPolicyReviewLedger()
    if registry is None:
        registry = DomainEvaluationPolicyRegistry()
    ledger, review_admission = admit_domain_evaluation_policy_review_v1(
        review_ledger=ledger,
        specification=specification,
        review=review,
    )
    registry, receipt = admit_domain_evaluation_policy_v1(
        registry=registry,
        review_ledger=ledger,
        review_admission=review_admission,
        specification=specification,
        admitted_at=_ADMITTED_AT,
    )
    return ledger, registry, receipt


def _resolve(registry, specification):
    return resolve_admitted_domain_evaluation_policy_v1(
        registry=registry,
        policy_ref=specification.policy_ref,
        specification_sha256=domain_evaluation_policy_specification_sha256_v1(
            specification
        ),
    )


@pytest.mark.skipif(
    not hasattr(os, "fork") or not hasattr(os, "register_at_fork"),
    reason="POSIX fork process-boundary regression",
)
def test_parent_registry_authority_is_not_usable_in_fork_child_and_replay_is_local():
    specification = _specification()
    review = _review(specification)
    ledger, registry, _ = _admit(specification, review)
    assert _resolve(registry, specification) == specification

    child_pid = os.fork()
    if child_pid == 0:
        try:
            try:
                _resolve(registry, specification)
            except InvalidDomainEvaluationPolicyGovernance as exc:
                if not (
                    "no runtime admission authority" in str(exc)
                    or "different process" in str(exc)
                ):
                    os._exit(11)
            else:
                os._exit(12)

            replayed_ledger, replayed_registry, _ = _admit(
                specification,
                review,
                ledger=ledger,
                registry=registry,
            )
            if replayed_ledger != ledger or replayed_registry != registry:
                os._exit(13)
            if _resolve(replayed_registry, specification) != specification:
                os._exit(14)
        except BaseException:
            os._exit(15)
        os._exit(0)

    _, status = os.waitpid(child_pid, 0)
    assert os.waitstatus_to_exitcode(status) == 0

    # Fork invalidation mutates only the child's copied runtime state.
    assert _resolve(registry, specification) == specification


@pytest.mark.skipif(
    not hasattr(os, "fork"),
    reason="isolated module-reload regression uses fork containment",
)
def test_registry_authority_module_reload_does_not_capture_wrapper_as_structural_core():
    child_pid = os.fork()
    if child_pid == 0:
        try:
            import capability_lab.evaluation_policy.registry_authority as authority

            importlib.reload(authority)
            specification = _specification()
            review = _review(specification)

            # Package-level function objects imported before reload retain the
            # same module globals. They must continue to call the stable stored
            # structural core rather than recurse into themselves.
            _, registry, _ = _admit(specification, review)
            if _resolve(registry, specification) != specification:
                os._exit(21)

            # The freshly reloaded module surface must also use that same core.
            if (
                authority.resolve_admitted_domain_evaluation_policy_v1(
                    registry=registry,
                    policy_ref=specification.policy_ref,
                    specification_sha256=(
                        domain_evaluation_policy_specification_sha256_v1(
                            specification
                        )
                    ),
                )
                != specification
            ):
                os._exit(22)
        except RecursionError:
            os._exit(23)
        except BaseException:
            os._exit(24)
        os._exit(0)

    _, status = os.waitpid(child_pid, 0)
    assert os.waitstatus_to_exitcode(status) == 0
