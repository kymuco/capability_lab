from dataclasses import replace

import pytest

from capability_lab.epistemics import EvidenceBearing
from capability_lab.pilots.civilization_bootstrap_01 import evaluation_policy_exact as exact_policy_module
from capability_lab.pilots.civilization_bootstrap_01.evaluation_policy import (
    InvalidPilotEvaluationPolicy,
    PILOT_01_REASONING_CLAIM_KEY,
    build_civilization_bootstrap_pilot_01_evaluation_policy_v1,
)
from capability_lab.pilots.civilization_bootstrap_01.evaluation_policy_exact import (
    CIVILIZATION_BOOTSTRAP_PILOT_01_EVALUATION_POLICY_SHA256_V1,
    CIVILIZATION_BOOTSTRAP_PILOT_01_PROTOCOL_SHA256_V1,
    exact_pilot_01_evaluation_policy_sha256_v1,
    exact_pilot_01_evaluation_policy_to_dict_v1,
    exact_pilot_01_evaluation_policy_to_json_v1,
    pilot_01_protocol_sha256_v1,
    validate_exact_civilization_bootstrap_pilot_01_evaluation_policy_v1,
)
from capability_lab.pilots.civilization_bootstrap_01.protocol import (
    build_civilization_bootstrap_pilot_01_protocol_v1,
)


def _policy():
    return build_civilization_bootstrap_pilot_01_evaluation_policy_v1()


def test_exact_gate_accepts_only_canonical_policy_and_frozen_digests():
    policy = _policy()
    protocol = build_civilization_bootstrap_pilot_01_protocol_v1()
    validate_exact_civilization_bootstrap_pilot_01_evaluation_policy_v1(
        policy,
        protocol=protocol,
    )
    assert (
        pilot_01_protocol_sha256_v1(protocol)
        == CIVILIZATION_BOOTSTRAP_PILOT_01_PROTOCOL_SHA256_V1
    )
    assert (
        exact_pilot_01_evaluation_policy_sha256_v1(policy)
        == CIVILIZATION_BOOTSTRAP_PILOT_01_EVALUATION_POLICY_SHA256_V1
    )
    assert exact_pilot_01_evaluation_policy_to_dict_v1(policy)["policy_ref"] == (
        "civilization_bootstrap:pilot_01_basic_electricity_human_review@1"
    )
    assert exact_pilot_01_evaluation_policy_to_json_v1(policy)


def test_exact_gate_rejects_canonical_protocol_builder_drift_under_same_protocol_ref(
    monkeypatch,
):
    protocol = build_civilization_bootstrap_pilot_01_protocol_v1()
    changed = replace(
        protocol,
        description="Changed canonical protocol semantics under the same exact protocol ref.",
    )
    monkeypatch.setattr(
        exact_policy_module,
        "build_civilization_bootstrap_pilot_01_protocol_v1",
        lambda: changed,
    )

    with pytest.raises(
        InvalidPilotEvaluationPolicy,
        match="canonical Pilot 01 v1 protocol digest drifted from the frozen release fingerprint",
    ):
        validate_exact_civilization_bootstrap_pilot_01_evaluation_policy_v1(_policy())


def test_exact_gate_rejects_protocol_semantic_drift_under_same_protocol_ref():
    protocol = build_civilization_bootstrap_pilot_01_protocol_v1()
    changed = replace(
        protocol,
        description="Changed protocol semantics under the same exact protocol ref.",
    )
    with pytest.raises(
        InvalidPilotEvaluationPolicy,
        match="exact frozen Pilot 01 v1 protocol semantics",
    ):
        validate_exact_civilization_bootstrap_pilot_01_evaluation_policy_v1(
            _policy(),
            protocol=changed,
        )


def test_exact_gate_rejects_participant_prompt_drift_under_same_protocol_ref():
    protocol = build_civilization_bootstrap_pilot_01_protocol_v1()
    probes = tuple(
        replace(
            probe,
            participant_prompt="Changed participant prompt under the same protocol ref.",
        )
        if probe.probe_id == "calculation_work"
        else probe
        for probe in protocol.probes
    )
    changed = replace(protocol, probes=probes)
    with pytest.raises(
        InvalidPilotEvaluationPolicy,
        match="exact frozen Pilot 01 v1 protocol semantics",
    ):
        validate_exact_civilization_bootstrap_pilot_01_evaluation_policy_v1(
            _policy(),
            protocol=changed,
        )


def test_exact_gate_rejects_claim_statement_rebinding_under_same_policy_ref():
    policy = _policy()
    changed_reasoning = replace(
        policy.claim(PILOT_01_REASONING_CLAIM_KEY),
        statement="Changed proposition under the same nominal policy revision.",
    )
    changed = replace(
        policy,
        claims=(changed_reasoning, policy.claim("bounded_execution")),
    )
    with pytest.raises(
        InvalidPilotEvaluationPolicy,
        match="policy content does not match the exact frozen",
    ):
        validate_exact_civilization_bootstrap_pilot_01_evaluation_policy_v1(changed)


def test_exact_gate_rejects_rubric_rebinding_under_same_policy_ref():
    policy = _policy()
    conceptual = policy.rubric("conceptual_explanation")
    changed_guidance = tuple(
        replace(item, condition="Changed SUPPORTS condition under the same policy ref.")
        if item.bearing is EvidenceBearing.SUPPORTS
        else item
        for item in conceptual.bearing_guidance
    )
    changed_conceptual = replace(conceptual, bearing_guidance=changed_guidance)
    changed_rubrics = tuple(
        changed_conceptual if item.probe_id == "conceptual_explanation" else item
        for item in policy.probe_rubrics
    )
    changed = replace(policy, probe_rubrics=changed_rubrics)
    with pytest.raises(
        InvalidPilotEvaluationPolicy,
        match="policy content does not match the exact frozen",
    ):
        validate_exact_civilization_bootstrap_pilot_01_evaluation_policy_v1(changed)


def test_exact_gate_rejects_criterion_drift_even_when_structure_still_valid():
    policy = _policy()
    calculation = policy.rubric("calculation_work")
    criteria = tuple(
        replace(
            item,
            requirement="Changed numeric checkpoint under the same policy revision.",
        )
        if item.criterion_id == "resistor_power"
        else item
        for item in calculation.criteria
    )
    changed_calculation = replace(calculation, criteria=criteria)
    changed = replace(
        policy,
        probe_rubrics=tuple(
            changed_calculation if item.probe_id == "calculation_work" else item
            for item in policy.probe_rubrics
        ),
    )
    with pytest.raises(
        InvalidPilotEvaluationPolicy,
        match="policy content does not match the exact frozen",
    ):
        validate_exact_civilization_bootstrap_pilot_01_evaluation_policy_v1(changed)
