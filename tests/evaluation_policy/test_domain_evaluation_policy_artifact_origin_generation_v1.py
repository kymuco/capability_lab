import importlib
import os

import pytest


@pytest.mark.skipif(not hasattr(os, "fork"), reason="isolated governance generation regression")
def test_artifact_methods_and_classmethods_keep_origin_generation_after_reload():
    isolated_pid = os.fork()
    if isolated_pid == 0:
        try:
            package = importlib.import_module("capability_lab.evaluation_policy")
            module_name = "capability_lab.evaluation_policy.governance"
            serialization_name = (
                "capability_lab.evaluation_policy.governance_serialization"
            )
            live = importlib.import_module(module_name)
            generation_n = live._pr12_7_published_governance_generation

            old_ledger = generation_n.DomainEvaluationPolicyReviewLedger()
            old_registry = generation_n.DomainEvaluationPolicyRegistry()
            old_ledger_json = old_ledger.to_json()
            old_registry_json = old_registry.to_json()

            live = importlib.reload(live)
            generation_n1 = live._pr12_7_published_governance_generation
            if generation_n1 is generation_n:
                os._exit(21)

            # Instance methods belong to generation N. Even though N+1 is now
            # current before delegation begins, they must serialize against N.
            if old_ledger.to_json() != old_ledger_json:
                os._exit(22)
            if old_registry.to_json() != old_registry_json:
                os._exit(23)

            # Old classmethods must likewise reconstruct exact N objects rather
            # than silently switching to the current generation N+1.
            old_ledger_restored = generation_n.DomainEvaluationPolicyReviewLedger.from_json(
                old_ledger_json
            )
            old_registry_restored = generation_n.DomainEvaluationPolicyRegistry.from_json(
                old_registry_json
            )
            if type(old_ledger_restored) is not generation_n.DomainEvaluationPolicyReviewLedger:
                os._exit(24)
            if type(old_registry_restored) is not generation_n.DomainEvaluationPolicyRegistry:
                os._exit(25)

            # New classmethods bind N+1.
            new_ledger_restored = generation_n1.DomainEvaluationPolicyReviewLedger.from_json(
                old_ledger_json
            )
            new_registry_restored = generation_n1.DomainEvaluationPolicyRegistry.from_json(
                old_registry_json
            )
            if type(new_ledger_restored) is not generation_n1.DomainEvaluationPolicyReviewLedger:
                os._exit(26)
            if type(new_registry_restored) is not generation_n1.DomainEvaluationPolicyRegistry:
                os._exit(27)

            # Package-level serializer aliases are not artifact methods: they
            # intentionally resolve the current published generation N+1.
            package_ledger = package.domain_evaluation_policy_review_ledger_from_json(
                old_ledger_json
            )
            package_registry = package.domain_evaluation_policy_registry_from_json(
                old_registry_json
            )
            if type(package_ledger) is not generation_n1.DomainEvaluationPolicyReviewLedger:
                os._exit(28)
            if type(package_registry) is not generation_n1.DomainEvaluationPolicyRegistry:
                os._exit(29)

            # A same-named global in an unrelated caller module must not be
            # treated as artifact-origin authority. The candidate must actually
            # own the caller function globals. The obsolete lookup accepted this
            # injected N pointer and made an ordinary package call reconstruct N.
            globals()["_pr12_7_published_governance_generation"] = generation_n
            spoofed_package_ledger = (
                package.domain_evaluation_policy_review_ledger_from_json(
                    old_ledger_json
                )
            )
            if type(spoofed_package_ledger) is not generation_n1.DomainEvaluationPolicyReviewLedger:
                os._exit(32)

            # Reexecuting the serializer itself must reapply the origin-aware
            # lookup before publication; this hardening is not one-shot.
            serialization = importlib.import_module(serialization_name)
            importlib.reload(serialization)
            if old_ledger.to_json() != old_ledger_json:
                os._exit(30)
            old_after_serializer_reload = (
                generation_n.DomainEvaluationPolicyReviewLedger.from_json(
                    old_ledger_json
                )
            )
            if type(old_after_serializer_reload) is not generation_n.DomainEvaluationPolicyReviewLedger:
                os._exit(31)
        except BaseException:
            os._exit(40)
        os._exit(0)

    _, status = os.waitpid(isolated_pid, 0)
    assert os.waitstatus_to_exitcode(status) == 0
