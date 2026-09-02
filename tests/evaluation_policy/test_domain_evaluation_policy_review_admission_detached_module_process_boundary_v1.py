import importlib
import os
import sys
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
    review_domain_evaluation_policy_specification_v1,
)
from capability_lab.semantics import CapabilityConceptRef, CapabilityId


_REVIEWED_AT = datetime(2026, 8, 31, 12, 0, tzinfo=timezone.utc)


def _specification() -> DomainEvaluationPolicySpecification:
    return DomainEvaluationPolicySpecification(
        policy_ref=EvaluationPolicyRef(
            "research",
            "detached_module_process_review",
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
        review_id=DomainEvaluationPolicyReviewId("detached-module-review-01"),
        reviewer_ref=DomainEvaluationPolicyReviewerRef(
            DomainEvaluationPolicyReviewerKind.HUMAN,
            "human:reviewer_01",
        ),
        verdict=DomainEvaluationPolicyReviewVerdict.APPROVE,
        reviewed_at=_REVIEWED_AT,
        rationale="Reviewed before detached-module process-boundary regression.",
    )


@pytest.mark.skipif(
    not hasattr(os, "fork") or not hasattr(os, "register_at_fork"),
    reason="POSIX detached-module fork regression",
)
def test_retained_detached_governance_module_cannot_validate_parent_admission_in_child():
    # Contain sys.modules replacement inside an outer child so the pytest host
    # and all later tests retain the original import graph.
    isolated_pid = os.fork()
    if isolated_pid == 0:
        try:
            module_name = "capability_lab.evaluation_policy.governance"
            old_governance = importlib.import_module(module_name)
            specification = _specification()
            review = _review(specification)
            ledger, admission = old_governance.admit_domain_evaluation_policy_review_v1(
                review_ledger=DomainEvaluationPolicyReviewLedger(),
                specification=specification,
                review=review,
            )
            if (
                old_governance.validate_domain_evaluation_policy_review_admission_v1(
                    review_ledger=ledger,
                    specification=specification,
                    review_admission=admission,
                )
                != review
            ):
                os._exit(11)

            # Simulate a reload mechanism that discards the sys.modules entry
            # and imports a fresh governance module while a caller still retains
            # the old module object and its copied structural issuance table.
            del sys.modules[module_name]
            new_governance = importlib.import_module(module_name)
            if new_governance is old_governance:
                os._exit(12)

            nested_pid = os.fork()
            if nested_pid == 0:
                try:
                    try:
                        old_governance.validate_domain_evaluation_policy_review_admission_v1(
                            review_ledger=ledger,
                            specification=specification,
                            review_admission=admission,
                        )
                    except InvalidDomainEvaluationPolicyGovernance as exc:
                        if not (
                            "process authority" in str(exc)
                            or "different process" in str(exc)
                            or "was not issued" in str(exc)
                        ):
                            os._exit(21)
                    else:
                        os._exit(22)

                    # Exact replay through the retained module is allowed to
                    # issue fresh child-local process authority without adding a
                    # duplicate review.
                    replayed_ledger, child_admission = (
                        old_governance.admit_domain_evaluation_policy_review_v1(
                            review_ledger=ledger,
                            specification=specification,
                            review=review,
                        )
                    )
                    if replayed_ledger != ledger or len(replayed_ledger.reviews) != 1:
                        os._exit(23)
                    if (
                        old_governance.validate_domain_evaluation_policy_review_admission_v1(
                            review_ledger=replayed_ledger,
                            specification=specification,
                            review_admission=child_admission,
                        )
                        != review
                    ):
                        os._exit(24)
                except BaseException:
                    os._exit(25)
                os._exit(0)

            _, nested_status = os.waitpid(nested_pid, 0)
            if os.waitstatus_to_exitcode(nested_status) != 0:
                os._exit(13)

            # The nested child modified only its copied process table; retained
            # old-module authority remains valid in this issuing process.
            if (
                old_governance.validate_domain_evaluation_policy_review_admission_v1(
                    review_ledger=ledger,
                    specification=specification,
                    review_admission=admission,
                )
                != review
            ):
                os._exit(14)
        except BaseException:
            os._exit(15)
        os._exit(0)

    _, status = os.waitpid(isolated_pid, 0)
    assert os.waitstatus_to_exitcode(status) == 0
