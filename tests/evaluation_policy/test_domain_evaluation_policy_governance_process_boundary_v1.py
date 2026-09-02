import importlib
import os
from datetime import datetime, timezone

import pytest

from capability_lab.epistemics import ClaimScope, EvaluationPolicyRef
from capability_lab.evaluation_policy import (
    DomainEvaluationPolicyRequirement,
    DomainEvaluationPolicyReviewId,
    DomainEvaluationPolicyReviewerKind,
    DomainEvaluationPolicyReviewerRef,
    DomainEvaluationPolicyReviewLedger,
    DomainEvaluationPolicyReviewVerdict,
    DomainEvaluationPolicySpecification,
    InvalidDomainEvaluationPolicyGovernance,
    admit_domain_evaluation_policy_review_v1,
    review_domain_evaluation_policy_specification_v1,
    validate_domain_evaluation_policy_review_admission_v1,
)
from capability_lab.semantics import CapabilityConceptRef, CapabilityId


_REVIEWED_AT = datetime(2026, 8, 31, 12, 0, tzinfo=timezone.utc)


def _specification() -> DomainEvaluationPolicySpecification:
    return DomainEvaluationPolicySpecification(
        policy_ref=EvaluationPolicyRef(
            "research",
            "fork_process_boundary_review",
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
        review_id=DomainEvaluationPolicyReviewId("fork-policy-review-01"),
        reviewer_ref=DomainEvaluationPolicyReviewerRef(
            DomainEvaluationPolicyReviewerKind.HUMAN,
            "human:reviewer_01",
        ),
        verdict=DomainEvaluationPolicyReviewVerdict.APPROVE,
        reviewed_at=_REVIEWED_AT,
        rationale="Reviewed exact policy before process-boundary replay test.",
    )


@pytest.mark.skipif(
    not hasattr(os, "fork") or not hasattr(os, "register_at_fork"),
    reason="POSIX fork process-boundary regression",
)
def test_parent_issued_review_admission_loses_authority_in_fork_child():
    specification = _specification()
    review = _review(specification)
    ledger, parent_admission = admit_domain_evaluation_policy_review_v1(
        review_ledger=DomainEvaluationPolicyReviewLedger(),
        specification=specification,
        review=review,
    )

    assert (
        validate_domain_evaluation_policy_review_admission_v1(
            review_ledger=ledger,
            specification=specification,
            review_admission=parent_admission,
        )
        == review
    )

    child_pid = os.fork()
    if child_pid == 0:
        try:
            try:
                validate_domain_evaluation_policy_review_admission_v1(
                    review_ledger=ledger,
                    specification=specification,
                    review_admission=parent_admission,
                )
            except InvalidDomainEvaluationPolicyGovernance as exc:
                if "was not issued" not in str(exc):
                    os._exit(11)
            else:
                os._exit(12)

            replayed_ledger, child_admission = (
                admit_domain_evaluation_policy_review_v1(
                    review_ledger=ledger,
                    specification=specification,
                    review=review,
                )
            )
            if replayed_ledger != ledger or len(replayed_ledger.reviews) != 1:
                os._exit(13)
            if (
                validate_domain_evaluation_policy_review_admission_v1(
                    review_ledger=replayed_ledger,
                    specification=specification,
                    review_admission=child_admission,
                )
                != review
            ):
                os._exit(14)
        except BaseException:
            os._exit(15)
        os._exit(0)

    _, status = os.waitpid(child_pid, 0)
    assert os.waitstatus_to_exitcode(status) == 0

    # The child clears its copied issuance table only; parent authority remains
    # valid in the issuing process.
    assert (
        validate_domain_evaluation_policy_review_admission_v1(
            review_ledger=ledger,
            specification=specification,
            review_admission=parent_admission,
        )
        == review
    )


@pytest.mark.skipif(
    not hasattr(os, "fork") or not hasattr(os, "register_at_fork"),
    reason="POSIX fork + module-reload process-boundary regression",
)
def test_reload_then_fork_clears_the_current_governance_issuance_table():
    """Regression for a stale bound ``dict.clear`` at-fork callback.

    The reload is isolated in a fork child so the pytest worker's already-imported
    package symbols are not polluted by re-executing the governance module.
    """

    reload_host_pid = os.fork()
    if reload_host_pid == 0:
        try:
            import capability_lab.evaluation_policy.governance as governance

            governance = importlib.reload(governance)
            specification = _specification()
            review = governance.review_domain_evaluation_policy_specification_v1(
                specification=specification,
                review_id=governance.DomainEvaluationPolicyReviewId(
                    "reload-fork-policy-review-01"
                ),
                reviewer_ref=governance.DomainEvaluationPolicyReviewerRef(
                    governance.DomainEvaluationPolicyReviewerKind.HUMAN,
                    "human:reload_reviewer_01",
                ),
                verdict=governance.DomainEvaluationPolicyReviewVerdict.APPROVE,
                reviewed_at=_REVIEWED_AT,
                rationale="Issued after governance reload before nested fork.",
            )
            ledger, parent_admission = governance.admit_domain_evaluation_policy_review_v1(
                review_ledger=governance.DomainEvaluationPolicyReviewLedger(),
                specification=specification,
                review=review,
            )
            if (
                governance.validate_domain_evaluation_policy_review_admission_v1(
                    review_ledger=ledger,
                    specification=specification,
                    review_admission=parent_admission,
                )
                != review
            ):
                os._exit(31)

            fork_child_pid = os.fork()
            if fork_child_pid == 0:
                try:
                    try:
                        governance.validate_domain_evaluation_policy_review_admission_v1(
                            review_ledger=ledger,
                            specification=specification,
                            review_admission=parent_admission,
                        )
                    except governance.InvalidDomainEvaluationPolicyGovernance as exc:
                        if "was not issued" not in str(exc):
                            os._exit(32)
                    else:
                        os._exit(33)

                    replayed_ledger, child_admission = (
                        governance.admit_domain_evaluation_policy_review_v1(
                            review_ledger=ledger,
                            specification=specification,
                            review=review,
                        )
                    )
                    if replayed_ledger != ledger or len(replayed_ledger.reviews) != 1:
                        os._exit(34)
                    if (
                        governance.validate_domain_evaluation_policy_review_admission_v1(
                            review_ledger=replayed_ledger,
                            specification=specification,
                            review_admission=child_admission,
                        )
                        != review
                    ):
                        os._exit(35)
                except BaseException:
                    os._exit(36)
                os._exit(0)

            _, child_status = os.waitpid(fork_child_pid, 0)
            if os.waitstatus_to_exitcode(child_status) != 0:
                os._exit(37)

            # Nested child invalidation must not revoke the reload host's own
            # process-local capability.
            if (
                governance.validate_domain_evaluation_policy_review_admission_v1(
                    review_ledger=ledger,
                    specification=specification,
                    review_admission=parent_admission,
                )
                != review
            ):
                os._exit(38)
        except BaseException:
            os._exit(39)
        os._exit(0)

    _, status = os.waitpid(reload_host_pid, 0)
    assert os.waitstatus_to_exitcode(status) == 0
