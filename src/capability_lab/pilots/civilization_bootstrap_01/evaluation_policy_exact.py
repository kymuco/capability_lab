"""Exact frozen-revision gate for Pilot 01 evaluation policy v1.

The base PR11.0 policy module provides structural policy records and deterministic
serialization. This module adds the release-level exact-revision boundary needed
before a later evaluator may rely on ``@1`` as the declared Pilot 01 policy.

EvaluationPolicyRef remains nominal governance identity, not a content hash.
Exact-v1 acceptance therefore requires the ref, the frozen canonical Pilot 01
protocol fingerprint, the canonical policy object, and the frozen policy digest
to agree.
"""

from __future__ import annotations

import hashlib

from capability_lab.epistemics import EvaluationPolicyRef

from .evaluation_policy import (
    CIVILIZATION_BOOTSTRAP_PILOT_01_EVALUATION_POLICY_REF_V1,
    InvalidPilotEvaluationPolicy,
    PilotHumanEvaluationPolicy,
    build_civilization_bootstrap_pilot_01_evaluation_policy_v1,
    pilot_evaluation_policy_sha256_v1,
    pilot_evaluation_policy_to_dict_v1,
    pilot_evaluation_policy_to_json_v1,
    validate_civilization_bootstrap_pilot_01_evaluation_policy_v1,
)
from .protocol import PilotProtocol, build_civilization_bootstrap_pilot_01_protocol_v1
from .serialization import pilot_protocol_to_json


_PROTOCOL_HASH_DOMAIN = (
    b"capability_lab/civilization_bootstrap_pilot_01_protocol@1\x00"
)

CIVILIZATION_BOOTSTRAP_PILOT_01_PROTOCOL_SHA256_V1 = (
    "238e0d12810e4f27536665a56a90f8d835e7a8a95cc9ded46777c8477803f5d5"
)
CIVILIZATION_BOOTSTRAP_PILOT_01_EVALUATION_POLICY_SHA256_V1 = (
    "f1b2be9d059e3375419e3a96803f099a671f0d98531b6d9a061dd36505c4c18a"
)


def pilot_01_protocol_sha256_v1(protocol: PilotProtocol) -> str:
    """Return the domain-separated hash of the complete canonical protocol JSON."""

    if not isinstance(protocol, PilotProtocol):
        raise InvalidPilotEvaluationPolicy("protocol must be PilotProtocol")
    digest = hashlib.sha256()
    digest.update(_PROTOCOL_HASH_DOMAIN)
    digest.update(pilot_protocol_to_json(protocol).encode("utf-8"))
    return digest.hexdigest()


def validate_exact_civilization_bootstrap_pilot_01_evaluation_policy_v1(
    policy: PilotHumanEvaluationPolicy,
    *,
    protocol: PilotProtocol | None = None,
) -> None:
    """Require the exact frozen Pilot 01 protocol and evaluation-policy revision.

    This is a governance/content-integrity gate, not authentication, PKI,
    trusted persistence, or proof that a human evaluation occurred.
    """

    if not isinstance(policy, PilotHumanEvaluationPolicy):
        raise InvalidPilotEvaluationPolicy(
            "policy must be PilotHumanEvaluationPolicy"
        )

    canonical_protocol = build_civilization_bootstrap_pilot_01_protocol_v1()
    canonical_protocol_digest = pilot_01_protocol_sha256_v1(canonical_protocol)
    if (
        canonical_protocol_digest
        != CIVILIZATION_BOOTSTRAP_PILOT_01_PROTOCOL_SHA256_V1
    ):
        raise InvalidPilotEvaluationPolicy(
            "canonical Pilot 01 v1 protocol digest drifted from the frozen release fingerprint"
        )

    if protocol is not None:
        if not isinstance(protocol, PilotProtocol):
            raise InvalidPilotEvaluationPolicy("protocol must be PilotProtocol")
        supplied_protocol_digest = pilot_01_protocol_sha256_v1(protocol)
        if (
            supplied_protocol_digest
            != CIVILIZATION_BOOTSTRAP_PILOT_01_PROTOCOL_SHA256_V1
        ):
            raise InvalidPilotEvaluationPolicy(
                "protocol does not match the exact frozen Pilot 01 v1 protocol semantics"
            )
        if protocol != canonical_protocol:
            raise InvalidPilotEvaluationPolicy(
                "protocol does not match the exact frozen Pilot 01 v1 protocol semantics"
            )

    if policy.policy_ref != CIVILIZATION_BOOTSTRAP_PILOT_01_EVALUATION_POLICY_REF_V1:
        raise InvalidPilotEvaluationPolicy(
            "policy_ref does not match frozen Pilot 01 evaluation policy v1"
        )

    # Retain the lower structural invariants as defense-in-depth.
    validate_civilization_bootstrap_pilot_01_evaluation_policy_v1(
        policy,
        protocol=canonical_protocol,
    )

    canonical_policy = build_civilization_bootstrap_pilot_01_evaluation_policy_v1()
    canonical_digest = pilot_evaluation_policy_sha256_v1(canonical_policy)
    if canonical_digest != CIVILIZATION_BOOTSTRAP_PILOT_01_EVALUATION_POLICY_SHA256_V1:
        raise InvalidPilotEvaluationPolicy(
            "canonical Pilot 01 evaluation policy v1 digest drifted from the frozen release fingerprint"
        )

    if policy != canonical_policy:
        raise InvalidPilotEvaluationPolicy(
            "policy content does not match the exact frozen Pilot 01 evaluation policy v1 snapshot"
        )

    actual_digest = pilot_evaluation_policy_sha256_v1(policy)
    if actual_digest != CIVILIZATION_BOOTSTRAP_PILOT_01_EVALUATION_POLICY_SHA256_V1:
        raise InvalidPilotEvaluationPolicy(
            "policy digest does not match the exact frozen Pilot 01 evaluation policy v1 fingerprint"
        )


def exact_pilot_01_evaluation_policy_to_dict_v1(
    policy: PilotHumanEvaluationPolicy,
) -> dict[str, object]:
    validate_exact_civilization_bootstrap_pilot_01_evaluation_policy_v1(policy)
    return pilot_evaluation_policy_to_dict_v1(policy)


def exact_pilot_01_evaluation_policy_to_json_v1(
    policy: PilotHumanEvaluationPolicy,
) -> str:
    validate_exact_civilization_bootstrap_pilot_01_evaluation_policy_v1(policy)
    return pilot_evaluation_policy_to_json_v1(policy)


def exact_pilot_01_evaluation_policy_sha256_v1(
    policy: PilotHumanEvaluationPolicy,
) -> str:
    validate_exact_civilization_bootstrap_pilot_01_evaluation_policy_v1(policy)
    digest = pilot_evaluation_policy_sha256_v1(policy)
    if digest != CIVILIZATION_BOOTSTRAP_PILOT_01_EVALUATION_POLICY_SHA256_V1:
        raise InvalidPilotEvaluationPolicy(
            "exact Pilot 01 evaluation policy digest mismatch"
        )
    return digest


def is_exact_pilot_01_evaluation_policy_ref_v1(value: object) -> bool:
    """Small nominal-ref helper; it grants no authority by itself."""

    return (
        isinstance(value, EvaluationPolicyRef)
        and value == CIVILIZATION_BOOTSTRAP_PILOT_01_EVALUATION_POLICY_REF_V1
    )
