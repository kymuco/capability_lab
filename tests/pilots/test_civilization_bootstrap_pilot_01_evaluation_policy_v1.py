from dataclasses import replace

import pytest

from capability_lab.epistemics import (
    ClaimScope,
    EvaluationPolicyRef,
    EvidenceBearing,
)
from capability_lab.pilots.civilization_bootstrap_01 import (
    CIVILIZATION_BOOTSTRAP_PILOT_01_PROTOCOL_REF,
    build_civilization_bootstrap_pilot_01_protocol_v1,
)
from capability_lab.pilots.civilization_bootstrap_01.evaluation_policy import (
    CIVILIZATION_BOOTSTRAP_PILOT_01_EVALUATION_POLICY_REF_V1,
    InvalidPilotEvaluationPolicy,
    PILOT_01_EXECUTION_CLAIM_KEY,
    PILOT_01_REASONING_CLAIM_KEY,
    PILOT_EVALUATION_POLICY_SCHEMA_V1,
    PilotClaimTemplate,
    PilotEvidenceBearingGuidance,
    PilotHumanEvaluationPolicy,
    PilotMissingProbeSemantics,
    PilotProbeEvaluationRubric,
    PilotRubricCriterion,
    build_civilization_bootstrap_pilot_01_evaluation_policy_v1,
    pilot_evaluation_policy_sha256_v1,
    pilot_evaluation_policy_to_dict_v1,
    pilot_evaluation_policy_to_json_v1,
    validate_civilization_bootstrap_pilot_01_evaluation_policy_v1,
)
from capability_lab.semantics import CapabilityConceptRef


EXPECTED_POLICY_SHA256 = "f1b2be9d059e3375419e3a96803f099a671f0d98531b6d9a061dd36505c4c18a"


def _policy():
    return build_civilization_bootstrap_pilot_01_evaluation_policy_v1()


def test_policy_ref_and_protocol_ref_are_frozen():
    policy = _policy()
    assert policy.policy_ref == EvaluationPolicyRef(
        "civilization_bootstrap",
        "pilot_01_basic_electricity_human_review",
        1,
    )
    assert policy.policy_ref == CIVILIZATION_BOOTSTRAP_PILOT_01_EVALUATION_POLICY_REF_V1
    assert policy.protocol_ref == CIVILIZATION_BOOTSTRAP_PILOT_01_PROTOCOL_REF


def test_policy_defines_two_separate_claim_templates():
    policy = _policy()
    assert tuple(item.claim_key for item in policy.claims) == (
        PILOT_01_REASONING_CLAIM_KEY,
        PILOT_01_EXECUTION_CLAIM_KEY,
    )
    assert all(
        item.concept_ref
        == CapabilityConceptRef.parse("civilization_bootstrap:basic_electricity@1")
        for item in policy.claims
    )


def test_reasoning_claim_requires_exact_three_reasoning_probes():
    claim = _policy().claim(PILOT_01_REASONING_CLAIM_KEY)
    assert claim.sufficiency_probe_ids == (
        "conceptual_explanation",
        "calculation_work",
        "diagnosis_reasoning",
    )
    assert "execution_artifact" not in claim.sufficiency_probe_ids


def test_execution_claim_is_isolated_to_optional_execution_artifact():
    claim = _policy().claim(PILOT_01_EXECUTION_CLAIM_KEY)
    assert claim.sufficiency_probe_ids == ("execution_artifact",)
    assert "absence" in claim.scope.description.lower()
    assert "unobserved" in claim.scope.description.lower()


def test_every_protocol_probe_has_exactly_one_rubric():
    protocol = build_civilization_bootstrap_pilot_01_protocol_v1()
    policy = _policy()
    assert {item.probe_id for item in policy.probe_rubrics} == {
        item.probe_id for item in protocol.probes
    }
    assert len(policy.probe_rubrics) == len(protocol.probes)


def test_required_probe_absence_is_coverage_gap_not_contradiction():
    policy = _policy()
    for probe_id in (
        "conceptual_explanation",
        "calculation_work",
        "diagnosis_reasoning",
    ):
        assert (
            policy.rubric(probe_id).missing_probe_semantics
            is PilotMissingProbeSemantics.REQUIRED_COVERAGE_GAP
        )


def test_optional_execution_absence_is_unobserved_not_failure():
    rubric = _policy().rubric("execution_artifact")
    assert (
        rubric.missing_probe_semantics
        is PilotMissingProbeSemantics.OPTIONAL_UNOBSERVED
    )
    contradicts = rubric.guidance_for(EvidenceBearing.CONTRADICTS).condition.lower()
    assert "absence" in contradicts
    assert "never contradiction" in contradicts


def test_every_rubric_defines_all_four_evidence_bearings_exactly_once():
    for rubric in _policy().probe_rubrics:
        assert {item.bearing for item in rubric.bearing_guidance} == set(EvidenceBearing)
        assert len(rubric.bearing_guidance) == len(EvidenceBearing)


def test_supports_is_not_defined_as_default_for_materialized_evidence():
    policy = _policy()
    assert "must not automatically promote reliability" in policy.reliability_rule
    for rubric in policy.probe_rubrics:
        assert rubric.guidance_for(EvidenceBearing.SUPPORTS).condition


def test_multi_record_sufficiency_requires_pr10_1_dependence_governance():
    rule = _policy().dependence_rule
    assert "PR10.1 terminal reviewed-dependence precondition" in rule
    assert "not claim support" in rule


def test_policy_contains_no_authority_promotion_semantics():
    policy = _policy()
    boundaries = set(policy.authority_boundaries)
    assert "CLAIM TEMPLATE != CAPABILITY CLAIM" in boundaries
    assert "RUBRIC != CLAIM EVALUATION" in boundaries
    assert "EVALUATION POLICY != EVALUATION" in boundaries
    assert "PR11.0 != PERSONAL CAPABILITY STATE" in boundaries


def test_calculation_rubric_freezes_reference_checkpoints():
    rubric = _policy().rubric("calculation_work")
    requirements = "\n".join(item.requirement for item in rubric.criteria)
    assert "5.0 mA" in requirements
    assert "21.2 mA" in requirements
    assert "15.625 mA" in requirements
    assert "1.5625 V" in requirements
    assert "3.4375 V" in requirements
    assert "0.144 W" in requirements


def test_diagnosis_rubric_rejects_out_of_scope_physical_work():
    rubric = _policy().rubric("diagnosis_reasoning")
    errors = "\n".join(
        error
        for criterion in rubric.criteria
        for error in criterion.material_error_conditions
    )
    assert "mains" in errors
    assert "high-voltage" in errors or "high voltage" in errors


def test_execution_rubric_preserves_provenance_authentication_limit():
    rubric = _policy().rubric("execution_artifact")
    requirements = "\n".join(item.requirement for item in rubric.criteria)
    assert "do not authenticate human authorship" in requirements
    assert "historical execution" in requirements


def test_policy_rejects_missing_rubric_before_validation():
    policy = _policy()
    with pytest.raises(
        InvalidPilotEvaluationPolicy,
        match="every claim sufficiency probe must have a rubric bound to that claim",
    ):
        replace(policy, probe_rubrics=policy.probe_rubrics[:-1])


def test_policy_rejects_reasoning_execution_scope_collapse():
    policy = _policy()
    reasoning = policy.claim(PILOT_01_REASONING_CLAIM_KEY)
    collapsed = replace(
        reasoning,
        sufficiency_probe_ids=reasoning.sufficiency_probe_ids
        + ("execution_artifact",),
    )
    with pytest.raises(
        InvalidPilotEvaluationPolicy,
        match="every claim sufficiency probe must have a rubric bound to that claim",
    ):
        replace(
            policy,
            claims=(collapsed, policy.claim(PILOT_01_EXECUTION_CLAIM_KEY)),
        )


def test_validator_rejects_optional_execution_missing_as_required_gap():
    policy = _policy()
    rubrics = tuple(
        replace(
            item,
            missing_probe_semantics=PilotMissingProbeSemantics.REQUIRED_COVERAGE_GAP,
        )
        if item.probe_id == "execution_artifact"
        else item
        for item in policy.probe_rubrics
    )
    changed = replace(policy, probe_rubrics=rubrics)
    with pytest.raises(
        InvalidPilotEvaluationPolicy,
        match="probe missing semantics do not match protocol requirement",
    ):
        validate_civilization_bootstrap_pilot_01_evaluation_policy_v1(changed)


def test_probe_rubric_requires_each_bearing_exactly_once():
    criterion = PilotRubricCriterion(
        criterion_id="criterion",
        requirement="Bounded requirement.",
    )
    duplicated = (
        PilotEvidenceBearingGuidance(
            EvidenceBearing.SUPPORTS,
            "First support condition.",
        ),
        PilotEvidenceBearingGuidance(
            EvidenceBearing.SUPPORTS,
            "Duplicate support condition.",
        ),
        PilotEvidenceBearingGuidance(
            EvidenceBearing.INDETERMINATE,
            "Indeterminate condition.",
        ),
        PilotEvidenceBearingGuidance(
            EvidenceBearing.NOT_RELEVANT,
            "Not relevant condition.",
        ),
    )
    with pytest.raises(
        InvalidPilotEvaluationPolicy,
        match="cover each EvidenceBearing exactly once",
    ):
        PilotProbeEvaluationRubric(
            probe_id="conceptual_explanation",
            claim_key=PILOT_01_REASONING_CLAIM_KEY,
            criteria=(criterion,),
            bearing_guidance=duplicated,
            missing_probe_semantics=PilotMissingProbeSemantics.REQUIRED_COVERAGE_GAP,
        )


def test_claim_template_rejects_empty_sufficiency_basis():
    with pytest.raises(
        InvalidPilotEvaluationPolicy,
        match="claim sufficiency_probe_ids must be non-empty",
    ):
        PilotClaimTemplate(
            claim_key="bounded_test",
            concept_ref=CapabilityConceptRef.parse(
                "civilization_bootstrap:basic_electricity@1"
            ),
            statement="A bounded proposition.",
            scope=ClaimScope("A bounded scope."),
            sufficiency_probe_ids=(),
        )


def test_policy_serialization_is_deterministic_and_schema_marked():
    policy = _policy()
    encoded = pilot_evaluation_policy_to_dict_v1(policy)
    assert encoded["schema"] == PILOT_EVALUATION_POLICY_SCHEMA_V1
    assert pilot_evaluation_policy_to_json_v1(policy) == pilot_evaluation_policy_to_json_v1(
        _policy()
    )


def test_policy_snapshot_digest_is_frozen():
    assert pilot_evaluation_policy_sha256_v1(_policy()) == EXPECTED_POLICY_SHA256


def test_policy_hash_is_content_sensitive():
    policy = _policy()
    changed_reasoning = replace(
        policy.claim(PILOT_01_REASONING_CLAIM_KEY),
        statement="Changed proposition under the same policy ref.",
    )
    changed = replace(
        policy,
        claims=(changed_reasoning, policy.claim(PILOT_01_EXECUTION_CLAIM_KEY)),
    )
    assert pilot_evaluation_policy_sha256_v1(changed) != EXPECTED_POLICY_SHA256


def test_unknown_claim_and_probe_lookup_fail_closed():
    policy = _policy()
    with pytest.raises(InvalidPilotEvaluationPolicy, match="unknown claim_key"):
        policy.claim("unknown_claim")
    with pytest.raises(InvalidPilotEvaluationPolicy, match="unknown probe_id"):
        policy.rubric("unknown_probe")
