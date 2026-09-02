from capability_lab.pilots.civilization_bootstrap_01 import (
    CIVILIZATION_BOOTSTRAP_PILOT_01_PROTOCOL_REF,
    PilotCaptureKind,
    PilotProbeRequirement,
    build_civilization_bootstrap_pilot_01_protocol_v1,
)


def test_pilot_01_protocol_freezes_exact_subject_facing_scope_without_rubric() -> None:
    protocol = build_civilization_bootstrap_pilot_01_protocol_v1()

    assert protocol.protocol_ref == CIVILIZATION_BOOTSTRAP_PILOT_01_PROTOCOL_REF
    assert str(protocol.protocol_ref) == "civilization_bootstrap:pilot_01_basic_electricity@1"
    assert str(protocol.capability_ref) == "civilization_bootstrap:basic_electricity@1"
    assert str(protocol.frame_ref) == "civilization_bootstrap:technical_competence@1"
    assert tuple(probe.probe_id for probe in protocol.probes) == (
        "conceptual_explanation",
        "calculation_work",
        "diagnosis_reasoning",
        "execution_artifact",
    )
    assert protocol.required_probe_ids == (
        "conceptual_explanation",
        "calculation_work",
        "diagnosis_reasoning",
    )
    assert protocol.probe("execution_artifact").requirement is PilotProbeRequirement.OPTIONAL
    assert protocol.probe("conceptual_explanation").allowed_capture_kinds == (
        PilotCaptureKind.TEXT_RESPONSE,
    )
    assert set(protocol.probe("execution_artifact").allowed_capture_kinds) == {
        PilotCaptureKind.TEXT_RESPONSE,
        PilotCaptureKind.FILE_ARTIFACT,
    }

    fields = set(protocol.probes[0].__dataclass_fields__)
    assert "score" not in fields
    assert "threshold" not in fields
    assert "expected_answer" not in fields
    assert "dimension_binding" not in fields
    assert "evaluation_policy" not in fields


def test_pilot_01_protocol_preserves_privacy_optional_execution_and_physical_boundaries() -> None:
    protocol = build_civilization_bootstrap_pilot_01_protocol_v1()
    privacy = " ".join(protocol.privacy_boundaries).lower()
    physical = " ".join(protocol.physical_boundaries).lower()
    execution = protocol.probe("execution_artifact").participant_prompt.lower()

    assert "private by default" in privacy
    assert "not automatically an evidencerecord" in privacy
    assert "not authentication" in privacy
    assert "mains" in physical
    assert "opened power supplies" in physical
    assert "not a safety certification" in physical
    assert "skip this probe" in execution


def test_protocol_contains_questions_but_no_embedded_answer_key_or_state_conclusion() -> None:
    protocol = build_civilization_bootstrap_pilot_01_protocol_v1()
    participant_surface = "\n".join(
        (*protocol.participant_instructions, *(probe.participant_prompt for probe in protocol.probes))
    ).lower()

    assert "supported" not in participant_surface
    assert "insufficient" not in participant_surface
    assert "mastered" not in participant_surface
    assert "recommended next" not in participant_surface
    assert "correct answer is" not in participant_surface
    assert "expected answer" not in participant_surface
