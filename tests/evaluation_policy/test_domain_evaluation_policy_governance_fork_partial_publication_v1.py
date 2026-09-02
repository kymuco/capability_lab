import importlib
import os
import signal
import threading

import pytest


@pytest.mark.skipif(
    not hasattr(os, "fork") or not hasattr(os, "register_at_fork"),
    reason="POSIX partial-publication fork regression",
)
def test_fork_child_rolls_back_partial_governance_publication_to_last_complete_generation():
    """A child cannot inherit N+1 live values with stable generation still at N."""

    isolated_pid = os.fork()
    if isolated_pid == 0:
        try:
            # Import the package so its after_in_child recovery hook is registered.
            importlib.import_module("capability_lab.evaluation_policy")
            module_name = "capability_lab.evaluation_policy.governance"
            serialization_name = (
                "capability_lab.evaluation_policy.governance_serialization"
            )
            hardening_name = (
                "capability_lab.evaluation_policy.governance_import_hardening"
            )

            governance = importlib.import_module(module_name)
            serialization = importlib.import_module(serialization_name)
            hardening = importlib.import_module(hardening_name)
            old_generation = serialization._governance()

            namespace_exposed = threading.Event()
            allow_parent_publication_to_finish = threading.Event()
            reload_errors: list[BaseException] = []
            original_publish = hardening._publish_live_namespace_values

            def pausing_publish(module, published_values):
                # This is the exact dangerous point: N+1 live values exist, but
                # the publisher still owns the publication lock and the stable
                # current-generation pointer remains N.
                original_publish(module, published_values)
                namespace_exposed.set()
                if not allow_parent_publication_to_finish.wait(timeout=10):
                    raise RuntimeError("timed out waiting to finish parent publication")

            hardening._publish_live_namespace_values = pausing_publish

            def reload_governance() -> None:
                try:
                    importlib.reload(governance)
                except BaseException as exc:
                    reload_errors.append(exc)

            reload_worker = threading.Thread(target=reload_governance)
            reload_worker.start()
            if not namespace_exposed.wait(timeout=10):
                os._exit(11)

            # Prove the parent really is in the mixed publication state before
            # forking: the live class is N+1 while stable package selection is N.
            if governance.DomainEvaluationPolicyReviewLedger is old_generation.DomainEvaluationPolicyReviewLedger:
                os._exit(12)
            if hardening._CURRENT_PUBLISHED_GOVERNANCE_GENERATION is not old_generation:
                os._exit(13)

            nested_pid = os.fork()
            if nested_pid == 0:
                def timed_out(_signum, _frame):
                    os._exit(21)

                try:
                    signal.signal(signal.SIGALRM, timed_out)
                    signal.alarm(5)

                    # after_in_child must roll the live module back to the exact
                    # last complete generation N, not merely unlock the stale
                    # N/N+1 mixture inherited from the vanished publisher.
                    if serialization._governance() is not old_generation:
                        os._exit(22)
                    if (
                        governance._pr12_7_published_governance_generation
                        is not old_generation
                    ):
                        os._exit(23)
                    if (
                        governance.DomainEvaluationPolicyReviewLedger
                        is not old_generation.DomainEvaluationPolicyReviewLedger
                    ):
                        os._exit(24)

                    ledger = governance.DomainEvaluationPolicyReviewLedger()
                    encoded = (
                        serialization.domain_evaluation_policy_review_ledger_to_json(
                            ledger
                        )
                    )
                    signal.alarm(0)
                    if encoded != '{"reviews":[],"schema_version":1}':
                        os._exit(25)
                except BaseException:
                    os._exit(26)
                os._exit(0)

            # Parent keeps normal semantics: its publisher may finish N+1 once
            # the child snapshot has been taken.
            allow_parent_publication_to_finish.set()
            reload_worker.join(timeout=10)
            if reload_worker.is_alive() or reload_errors:
                os._exit(14)

            _, nested_status = os.waitpid(nested_pid, 0)
            if os.waitstatus_to_exitcode(nested_status) != 0:
                os._exit(15)
        except BaseException:
            os._exit(16)
        os._exit(0)

    _, status = os.waitpid(isolated_pid, 0)
    assert os.waitstatus_to_exitcode(status) == 0
