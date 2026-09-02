import importlib
import os
import signal
import sys
import threading

import pytest


@pytest.mark.skipif(not hasattr(os, "fork"), reason="isolated governance publication regression")
def test_package_serializer_waits_for_complete_namespace_generation_publication():
    """New live N+1 values cannot be serialized against stale package generation N."""

    isolated_pid = os.fork()
    if isolated_pid == 0:
        try:
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
            allow_generation_switch = threading.Event()
            serializer_entered_selection = threading.Event()
            reload_errors: list[BaseException] = []
            serialization_errors: list[BaseException] = []
            serialized: list[str] = []

            original_publish = hardening._publish_live_namespace_values
            original_stable_selection = hardening._stable_current_published_generation

            def pausing_publish(module, published_values):
                original_publish(module, published_values)
                namespace_exposed.set()
                if not allow_generation_switch.wait(timeout=10):
                    raise RuntimeError("timed out waiting to finish generation publication")

            def observed_stable_selection():
                serializer_entered_selection.set()
                return original_stable_selection()

            hardening._publish_live_namespace_values = pausing_publish
            hardening._stable_current_published_generation = observed_stable_selection

            def reload_governance() -> None:
                try:
                    importlib.reload(governance)
                except BaseException as exc:
                    reload_errors.append(exc)

            reload_worker = threading.Thread(target=reload_governance)
            reload_worker.start()
            if not namespace_exposed.wait(timeout=10):
                os._exit(11)

            # N+1 live classes are now visible, but the publishing thread still
            # owns the publication lock and has not switched the stable pointer.
            ledger = governance.DomainEvaluationPolicyReviewLedger()
            if type(ledger) is old_generation.DomainEvaluationPolicyReviewLedger:
                os._exit(12)

            def serialize_new_live_value() -> None:
                try:
                    serialized.append(
                        serialization.domain_evaluation_policy_review_ledger_to_json(
                            ledger
                        )
                    )
                except BaseException as exc:
                    serialization_errors.append(exc)

            serializer_worker = threading.Thread(target=serialize_new_live_value)
            serializer_worker.start()
            if not serializer_entered_selection.wait(timeout=10):
                os._exit(13)
            if not serializer_worker.is_alive():
                # Without the shared publication barrier the stale generation N
                # is selected immediately and exact-type validation fails.
                os._exit(14)

            allow_generation_switch.set()
            reload_worker.join(timeout=10)
            serializer_worker.join(timeout=10)
            if reload_worker.is_alive() or serializer_worker.is_alive():
                os._exit(15)
            if reload_errors or serialization_errors:
                os._exit(16)
            if serialized != ['{"reviews":[],"schema_version":1}']:
                os._exit(17)

            new_generation = serialization._governance()
            if new_generation is old_generation:
                os._exit(18)
            if type(ledger) is not new_generation.DomainEvaluationPolicyReviewLedger:
                os._exit(19)
        except BaseException:
            os._exit(20)
        os._exit(0)

    _, status = os.waitpid(isolated_pid, 0)
    assert os.waitstatus_to_exitcode(status) == 0


@pytest.mark.skipif(not hasattr(os, "fork"), reason="isolated replacement-import regression")
def test_package_serializer_uses_last_complete_generation_during_replacement_import():
    """An initializing replacement in sys.modules never becomes serializer authority."""

    isolated_pid = os.fork()
    if isolated_pid == 0:
        try:
            module_name = "capability_lab.evaluation_policy.governance"
            serialization_name = (
                "capability_lab.evaluation_policy.governance_serialization"
            )
            hardening_name = (
                "capability_lab.evaluation_policy.governance_import_hardening"
            )

            retained = importlib.import_module(module_name)
            serialization = importlib.import_module(serialization_name)
            hardening = importlib.import_module(hardening_name)
            old_generation = serialization._governance()
            old_ledger = retained.DomainEvaluationPolicyReviewLedger()

            replacement_entered = threading.Event()
            allow_replacement = threading.Event()
            import_errors: list[BaseException] = []
            imported: list[object] = []
            real_path_finder = hardening.PathFinder

            class PausingLoader:
                def __init__(self, delegate):
                    self._delegate = delegate

                def create_module(self, spec):
                    create_module = getattr(self._delegate, "create_module", None)
                    if create_module is None:
                        return None
                    return create_module(spec)

                def exec_module(self, module):
                    replacement_entered.set()
                    if not allow_replacement.wait(timeout=10):
                        raise RuntimeError("timed out waiting to execute replacement module")
                    self._delegate.exec_module(module)

                def __getattr__(self, name):
                    return getattr(self._delegate, name)

            class PausingPathFinder:
                @classmethod
                def find_spec(cls, fullname, path=None, target=None):
                    spec = real_path_finder.find_spec(fullname, path, target)
                    if fullname == module_name and spec is not None and spec.loader is not None:
                        spec.loader = PausingLoader(spec.loader)
                    return spec

            hardening.PathFinder = PausingPathFinder
            del sys.modules[module_name]

            def import_replacement() -> None:
                try:
                    imported.append(importlib.import_module(module_name))
                except BaseException as exc:
                    import_errors.append(exc)

            import_worker = threading.Thread(target=import_replacement)
            import_worker.start()
            if not replacement_entered.wait(timeout=10):
                os._exit(31)

            transient = sys.modules.get(module_name)
            if transient is None or transient is retained:
                os._exit(32)

            # The replacement live module is present but still initializing.
            # Package-level serialization must ignore it and continue on the
            # last fully published immutable generation rather than raising
            # "untrusted published governance generation".
            encoded = serialization.domain_evaluation_policy_review_ledger_to_json(
                old_ledger
            )
            if encoded != '{"reviews":[],"schema_version":1}':
                os._exit(33)
            if serialization._governance() is not old_generation:
                os._exit(34)

            allow_replacement.set()
            import_worker.join(timeout=10)
            if import_worker.is_alive() or import_errors or len(imported) != 1:
                os._exit(35)
            fresh = imported[0]
            if fresh is retained:
                os._exit(36)

            new_generation = serialization._governance()
            if new_generation is old_generation:
                os._exit(37)
            if (
                getattr(fresh, "_pr12_7_published_governance_generation", None)
                is not new_generation
            ):
                os._exit(38)
        except BaseException:
            os._exit(39)
        os._exit(0)

    _, status = os.waitpid(isolated_pid, 0)
    assert os.waitstatus_to_exitcode(status) == 0


@pytest.mark.skipif(
    not hasattr(os, "fork") or not hasattr(os, "register_at_fork"),
    reason="POSIX publication-lock fork regression",
)
def test_fork_child_reinitializes_publication_lock_held_by_parent_thread():
    """Forking while another thread owns the publication lock cannot deadlock child."""

    isolated_pid = os.fork()
    if isolated_pid == 0:
        try:
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
            ledger = governance.DomainEvaluationPolicyReviewLedger()

            lock_held = threading.Event()
            release_parent_lock = threading.Event()

            def hold_publication_lock() -> None:
                with hardening._GOVERNANCE_PUBLICATION_LOCK:
                    lock_held.set()
                    release_parent_lock.wait(timeout=10)

            holder = threading.Thread(target=hold_publication_lock)
            holder.start()
            if not lock_held.wait(timeout=10):
                os._exit(51)

            nested_pid = os.fork()
            if nested_pid == 0:
                def timed_out(_signum, _frame):
                    os._exit(61)

                try:
                    signal.signal(signal.SIGALRM, timed_out)
                    signal.alarm(5)
                    encoded = (
                        serialization.domain_evaluation_policy_review_ledger_to_json(
                            ledger
                        )
                    )
                    signal.alarm(0)
                    if encoded != '{"reviews":[],"schema_version":1}':
                        os._exit(62)
                except BaseException:
                    os._exit(63)
                os._exit(0)

            # Releasing the parent's copy does not unlock the child's inherited
            # copy; child success therefore proves the at-fork reinitialization.
            release_parent_lock.set()
            holder.join(timeout=10)
            if holder.is_alive():
                os._exit(52)

            _, nested_status = os.waitpid(nested_pid, 0)
            if os.waitstatus_to_exitcode(nested_status) != 0:
                os._exit(53)
        except BaseException:
            os._exit(54)
        os._exit(0)

    _, status = os.waitpid(isolated_pid, 0)
    assert os.waitstatus_to_exitcode(status) == 0
