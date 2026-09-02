import importlib
import os
import sys

import pytest


@pytest.mark.skipif(
    not hasattr(os, "fork"),
    reason="isolated package generation-coherence regression",
)
def test_package_governance_exports_follow_complete_current_generation_after_reexecution():
    """The public evaluation_policy module cannot mix stale model aliases with current serializers."""

    isolated_pid = os.fork()
    if isolated_pid == 0:
        try:
            package = importlib.import_module("capability_lab.evaluation_policy")
            module_name = "capability_lab.evaluation_policy.governance"
            live = importlib.import_module(module_name)
            generation_n = live._pr12_7_published_governance_generation

            if package.DomainEvaluationPolicyReviewLedger is not generation_n.DomainEvaluationPolicyReviewLedger:
                os._exit(11)
            retained_n_ledger_type = package.DomainEvaluationPolicyReviewLedger

            reloaded = importlib.reload(live)
            generation_n1 = reloaded._pr12_7_published_governance_generation
            if generation_n1 is generation_n:
                os._exit(12)

            # The package module itself must resolve governance models/functions
            # from the same complete current generation used by its stable
            # package-level serializer facade.
            if package.DomainEvaluationPolicyReviewLedger is not generation_n1.DomainEvaluationPolicyReviewLedger:
                os._exit(13)
            if package.DomainEvaluationPolicyRegistry is not generation_n1.DomainEvaluationPolicyRegistry:
                os._exit(14)
            if package.InvalidDomainEvaluationPolicyGovernance is not generation_n1.InvalidDomainEvaluationPolicyGovernance:
                os._exit(15)
            if package.admit_domain_evaluation_policy_review_v1 is not generation_n1.admit_domain_evaluation_policy_review_v1:
                os._exit(16)
            if package.admit_domain_evaluation_policy_v1 is not generation_n1.admit_domain_evaluation_policy_v1:
                os._exit(17)
            if package.resolve_admitted_domain_evaluation_policy_v1 is not generation_n1.resolve_admitted_domain_evaluation_policy_v1:
                os._exit(18)

            ledger = package.DomainEvaluationPolicyReviewLedger()
            encoded = package.domain_evaluation_policy_review_ledger_to_json(ledger)
            restored = package.domain_evaluation_policy_review_ledger_from_json(encoded)
            if type(ledger) is not generation_n1.DomainEvaluationPolicyReviewLedger:
                os._exit(19)
            if type(restored) is not generation_n1.DomainEvaluationPolicyReviewLedger:
                os._exit(20)

            # Retained direct aliases keep ordinary Python retained-reference
            # semantics; only the package module's public attributes are current.
            if retained_n_ledger_type is not generation_n.DomainEvaluationPolicyReviewLedger:
                os._exit(21)
            if retained_n_ledger_type is generation_n1.DomainEvaluationPolicyReviewLedger:
                os._exit(22)

            del sys.modules[module_name]
            fresh = importlib.import_module(module_name)
            generation_n2 = fresh._pr12_7_published_governance_generation
            if generation_n2 is generation_n1:
                os._exit(23)
            if package.DomainEvaluationPolicyReviewLedger is not generation_n2.DomainEvaluationPolicyReviewLedger:
                os._exit(24)
            if package.admit_domain_evaluation_policy_v1 is not generation_n2.admit_domain_evaluation_policy_v1:
                os._exit(25)

            registry = package.DomainEvaluationPolicyRegistry()
            registry_json = package.domain_evaluation_policy_registry_to_json(registry)
            restored_registry = package.domain_evaluation_policy_registry_from_json(registry_json)
            if type(registry) is not generation_n2.DomainEvaluationPolicyRegistry:
                os._exit(26)
            if type(restored_registry) is not generation_n2.DomainEvaluationPolicyRegistry:
                os._exit(27)

            if "DomainEvaluationPolicyReviewLedger" not in dir(package):
                os._exit(28)
        except BaseException:
            os._exit(29)
        os._exit(0)

    _, status = os.waitpid(isolated_pid, 0)
    assert os.waitstatus_to_exitcode(status) == 0
