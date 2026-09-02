import importlib
import os
import threading

import pytest


@pytest.mark.skipif(not hasattr(os, "fork"), reason="isolated governance generation regression")
def test_serialization_operation_stays_on_captured_generation_during_reload():
    isolated_pid = os.fork()
    if isolated_pid == 0:
        try:
            module_name = "capability_lab.evaluation_policy.governance"
            serialization_name = (
                "capability_lab.evaluation_policy.governance_serialization"
            )
            governance = importlib.import_module(module_name)
            serialization = importlib.import_module(serialization_name)

            old_generation = serialization._governance()
            if old_generation is governance:
                os._exit(11)
            if (
                getattr(
                    governance,
                    "_pr12_7_published_governance_generation",
                    None,
                )
                is not old_generation
            ):
                os._exit(12)

            ledger = governance.DomainEvaluationPolicyReviewLedger()
            if type(ledger) is not old_generation.DomainEvaluationPolicyReviewLedger:
                os._exit(13)

            entered = threading.Event()
            release = threading.Event()
            errors: list[BaseException] = []
            results: list[str] = []
            captured_generations: list[object] = []

            # The serializer is itself published from an isolated shadow
            # namespace. Patch the globals actually owned by the published
            # function rather than the retained live module mapping.
            serializer_globals = (
                serialization.domain_evaluation_policy_review_ledger_to_json.__globals__
            )
            original = serializer_globals["_review_ledger_to_dict"]

            def pausing_review_ledger_to_dict(generation, value):
                captured_generations.append(generation)
                entered.set()
                if not release.wait(timeout=10):
                    raise RuntimeError("timed out waiting for concurrent governance reload")
                return original(generation, value)

            serializer_globals["_review_ledger_to_dict"] = pausing_review_ledger_to_dict

            def serialize_old_generation() -> None:
                try:
                    results.append(
                        serialization.domain_evaluation_policy_review_ledger_to_json(
                            ledger
                        )
                    )
                except BaseException as exc:
                    errors.append(exc)

            worker = threading.Thread(target=serialize_old_generation)
            worker.start()
            if not entered.wait(timeout=10):
                os._exit(14)
            if captured_generations != [old_generation]:
                os._exit(15)

            reloaded = importlib.reload(governance)
            new_generation = serialization._governance()
            if new_generation is old_generation or new_generation is reloaded:
                os._exit(16)
            if (
                getattr(
                    reloaded,
                    "_pr12_7_published_governance_generation",
                    None,
                )
                is not new_generation
            ):
                os._exit(17)

            release.set()
            worker.join(timeout=10)
            if worker.is_alive() or errors:
                os._exit(18)
            if results != ['{"reviews":[],"schema_version":1}']:
                os._exit(19)

            # A new package-level operation captures the new published
            # generation, while artifact-origin semantics are covered by the
            # separate old-class/old-instance regression.
            current_ledger = reloaded.DomainEvaluationPolicyReviewLedger()
            current_json = current_ledger.to_json()
            restored = serialization.domain_evaluation_policy_review_ledger_from_json(
                current_json
            )
            if type(restored) is not new_generation.DomainEvaluationPolicyReviewLedger:
                os._exit(20)
            if type(restored) is not reloaded.DomainEvaluationPolicyReviewLedger:
                os._exit(21)
        except BaseException:
            os._exit(22)
        os._exit(0)

    _, status = os.waitpid(isolated_pid, 0)
    assert os.waitstatus_to_exitcode(status) == 0
