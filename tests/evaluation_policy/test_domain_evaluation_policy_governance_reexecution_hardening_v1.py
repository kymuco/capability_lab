import importlib
import os
import sys
import threading
from datetime import datetime, timezone

import pytest

from capability_lab.epistemics import ClaimScope, EvaluationPolicyRef
from capability_lab.evaluation_policy import (
    DomainEvaluationPolicyRequirement,
    DomainEvaluationPolicySpecification,
    domain_evaluation_policy_specification_sha256_v1,
)
from capability_lab.semantics import CapabilityConceptRef, CapabilityId


_REVIEWED_AT = datetime(2026, 8, 31, 12, 0, tzinfo=timezone.utc)
_ADMITTED_AT = datetime(2026, 8, 31, 13, 0, tzinfo=timezone.utc)


def _specification() -> DomainEvaluationPolicySpecification:
    return DomainEvaluationPolicySpecification(
        policy_ref=EvaluationPolicyRef(
            "research",
            "governance_reexecution_hardening",
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


def _manual_registry(governance, specification):
    empty = governance.DomainEvaluationPolicyRegistry()
    entry = governance.DomainEvaluationPolicyRegistryEntry(
        policy_ref=specification.policy_ref,
        specification_sha256=domain_evaluation_policy_specification_sha256_v1(
            specification
        ),
        specification=specification,
        review_id=governance.DomainEvaluationPolicyReviewId(
            "reload-manual-registry-review"
        ),
        review_sha256="0" * 64,
        admitted_at=_ADMITTED_AT,
        predecessor_registry_sha256=(
            governance.domain_evaluation_policy_registry_sha256_v1(empty)
        ),
    )
    return governance.DomainEvaluationPolicyRegistry(entries=(entry,))


def _assert_manual_registry_has_no_resolution_authority(governance, specification) -> None:
    manual = _manual_registry(governance, specification)
    try:
        governance.resolve_admitted_domain_evaluation_policy_v1(
            registry=manual,
            policy_ref=specification.policy_ref,
            specification_sha256=(
                domain_evaluation_policy_specification_sha256_v1(specification)
            ),
        )
    except governance.InvalidDomainEvaluationPolicyGovernance as exc:
        assert "no runtime admission authority" in str(exc)
    else:
        raise AssertionError("manual registry unexpectedly gained resolution authority")


def _assert_serialization_uses_current_generation(governance) -> None:
    serialization = importlib.import_module(
        "capability_lab.evaluation_policy.governance_serialization"
    )
    package = importlib.import_module("capability_lab.evaluation_policy")

    ledger = governance.DomainEvaluationPolicyReviewLedger()
    ledger_json = ledger.to_json()
    restored_ledger = governance.DomainEvaluationPolicyReviewLedger.from_json(ledger_json)
    assert type(restored_ledger) is governance.DomainEvaluationPolicyReviewLedger
    assert restored_ledger == ledger

    package_ledger_json = package.domain_evaluation_policy_review_ledger_to_json(ledger)
    package_restored_ledger = package.domain_evaluation_policy_review_ledger_from_json(
        package_ledger_json
    )
    assert package_ledger_json == ledger_json
    assert type(package_restored_ledger) is governance.DomainEvaluationPolicyReviewLedger

    serializer_restored_ledger = serialization.domain_evaluation_policy_review_ledger_from_json(
        ledger_json
    )
    assert type(serializer_restored_ledger) is governance.DomainEvaluationPolicyReviewLedger

    registry = governance.DomainEvaluationPolicyRegistry()
    registry_json = registry.to_json()
    restored_registry = governance.DomainEvaluationPolicyRegistry.from_json(registry_json)
    assert type(restored_registry) is governance.DomainEvaluationPolicyRegistry
    assert restored_registry == registry

    package_registry_json = package.domain_evaluation_policy_registry_to_json(registry)
    package_restored_registry = package.domain_evaluation_policy_registry_from_json(
        package_registry_json
    )
    assert package_registry_json == registry_json
    assert type(package_restored_registry) is governance.DomainEvaluationPolicyRegistry


@pytest.mark.skipif(not hasattr(os, "fork"), reason="isolated governance reload regression")
def test_reload_reapplies_registry_authority_before_public_resolution():
    isolated_pid = os.fork()
    if isolated_pid == 0:
        try:
            module_name = "capability_lab.evaluation_policy.governance"
            governance = importlib.import_module(module_name)
            governance = importlib.reload(governance)
            _assert_manual_registry_has_no_resolution_authority(
                governance,
                _specification(),
            )
        except BaseException:
            os._exit(13)
        os._exit(0)

    _, status = os.waitpid(isolated_pid, 0)
    assert os.waitstatus_to_exitcode(status) == 0


@pytest.mark.skipif(not hasattr(os, "fork"), reason="isolated governance serializer regression")
def test_reload_and_reimport_serialization_bind_current_governance_generation():
    isolated_pid = os.fork()
    if isolated_pid == 0:
        try:
            module_name = "capability_lab.evaluation_policy.governance"
            governance = importlib.import_module(module_name)
            reloaded = importlib.reload(governance)
            _assert_serialization_uses_current_generation(reloaded)

            del sys.modules[module_name]
            fresh = importlib.import_module(module_name)
            if fresh is reloaded:
                os._exit(51)
            _assert_serialization_uses_current_generation(fresh)
        except BaseException:
            os._exit(52)
        os._exit(0)

    _, status = os.waitpid(isolated_pid, 0)
    assert os.waitstatus_to_exitcode(status) == 0


@pytest.mark.skipif(not hasattr(os, "fork"), reason="isolated concurrent loader regression")
def test_delegate_execution_never_publishes_structural_registry_resolver():
    """Retained live module stays hardened while replacement source executes."""

    isolated_pid = os.fork()
    if isolated_pid == 0:
        try:
            module_name = "capability_lab.evaluation_policy.governance"
            governance = importlib.import_module(module_name)
            loader = governance.__spec__.loader
            if not hasattr(loader, "_delegate"):
                os._exit(41)
            real_delegate = loader._delegate
            structural_execution_complete = threading.Event()
            allow_hardening = threading.Event()
            worker_errors: list[BaseException] = []

            class PausingDelegate:
                def exec_module(self, module):
                    real_delegate.exec_module(module)
                    structural_execution_complete.set()
                    if not allow_hardening.wait(timeout=10):
                        raise RuntimeError("timed out waiting to continue governance hardening")

                def __getattr__(self, name):
                    return getattr(real_delegate, name)

            loader._delegate = PausingDelegate()

            def execute_replacement_generation() -> None:
                try:
                    loader.exec_module(governance)
                except BaseException as exc:
                    worker_errors.append(exc)

            worker = threading.Thread(target=execute_replacement_generation)
            worker.start()
            if not structural_execution_complete.wait(timeout=10):
                os._exit(42)

            # The delegate has completely executed the structural governance
            # source, but the loader has not yet run either hardener. A retained
            # live module must still expose only the previous hardened generation.
            _assert_manual_registry_has_no_resolution_authority(
                governance,
                _specification(),
            )

            allow_hardening.set()
            worker.join(timeout=10)
            if worker.is_alive():
                os._exit(43)
            if worker_errors:
                os._exit(44)

            # The newly published generation remains hardened after completion.
            _assert_manual_registry_has_no_resolution_authority(
                governance,
                _specification(),
            )
        except BaseException:
            os._exit(45)
        os._exit(0)

    _, status = os.waitpid(isolated_pid, 0)
    assert os.waitstatus_to_exitcode(status) == 0


@pytest.mark.skipif(
    not hasattr(os, "fork") or not hasattr(os, "register_at_fork"),
    reason="POSIX reload/replacement process-authority regression",
)
def test_reloaded_then_detached_governance_cannot_carry_review_authority_across_fork():
    isolated_pid = os.fork()
    if isolated_pid == 0:
        try:
            module_name = "capability_lab.evaluation_policy.governance"
            retained = importlib.import_module(module_name)
            retained = importlib.reload(retained)
            specification = _specification()
            review = retained.review_domain_evaluation_policy_specification_v1(
                specification=specification,
                review_id=retained.DomainEvaluationPolicyReviewId(
                    "reload-detached-review"
                ),
                reviewer_ref=retained.DomainEvaluationPolicyReviewerRef(
                    retained.DomainEvaluationPolicyReviewerKind.HUMAN,
                    "human:reviewer_01",
                ),
                verdict=retained.DomainEvaluationPolicyReviewVerdict.APPROVE,
                reviewed_at=_REVIEWED_AT,
                rationale="Review issued after governance reload.",
            )
            ledger, admission = retained.admit_domain_evaluation_policy_review_v1(
                review_ledger=retained.DomainEvaluationPolicyReviewLedger(),
                specification=specification,
                review=review,
            )
            retained.validate_domain_evaluation_policy_review_admission_v1(
                review_ledger=ledger,
                specification=specification,
                review_admission=admission,
            )

            del sys.modules[module_name]
            fresh = importlib.import_module(module_name)
            if fresh is retained:
                os._exit(21)

            nested_pid = os.fork()
            if nested_pid == 0:
                try:
                    try:
                        retained.validate_domain_evaluation_policy_review_admission_v1(
                            review_ledger=ledger,
                            specification=specification,
                            review_admission=admission,
                        )
                    except retained.InvalidDomainEvaluationPolicyGovernance as exc:
                        if not (
                            "process authority" in str(exc)
                            or "different process" in str(exc)
                            or "was not issued" in str(exc)
                        ):
                            os._exit(31)
                    else:
                        os._exit(32)

                    replayed_ledger, child_admission = (
                        retained.admit_domain_evaluation_policy_review_v1(
                            review_ledger=ledger,
                            specification=specification,
                            review=review,
                        )
                    )
                    if replayed_ledger != ledger or len(replayed_ledger.reviews) != 1:
                        os._exit(33)
                    retained.validate_domain_evaluation_policy_review_admission_v1(
                        review_ledger=replayed_ledger,
                        specification=specification,
                        review_admission=child_admission,
                    )
                except BaseException:
                    os._exit(34)
                os._exit(0)

            _, nested_status = os.waitpid(nested_pid, 0)
            if os.waitstatus_to_exitcode(nested_status) != 0:
                os._exit(22)
        except BaseException:
            os._exit(23)
        os._exit(0)

    _, status = os.waitpid(isolated_pid, 0)
    assert os.waitstatus_to_exitcode(status) == 0
