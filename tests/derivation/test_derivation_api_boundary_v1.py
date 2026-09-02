from dataclasses import fields
import inspect

from capability_lab.derivation import (
    DETERMINISTIC_SUPPORTED_STATE_POLICY_V1,
    DeterministicStateDerivationRequest,
    derive_supported_state_v1,
)


def test_derivation_request_has_no_raw_evidence_or_hidden_policy_controls() -> None:
    names = {field.name for field in fields(DeterministicStateDerivationRequest)}
    assert names == {
        "state_id",
        "subject_ref",
        "concept_ref",
        "frame_ref",
        "as_of",
        "derived_at",
        "selected_evaluation_ids",
        "claim_dimension_bindings",
    }
    forbidden = {
        "evidence_ids",
        "evidence_weights",
        "evaluator_weights",
        "confidence",
        "score",
        "mastery",
        "derivation_policy_ref",
        "preferred_evaluator_kind",
        "preferred_evaluation_policy",
    }
    assert names.isdisjoint(forbidden)


def test_baseline_policy_identity_is_fixed_by_implementation() -> None:
    assert str(DETERMINISTIC_SUPPORTED_STATE_POLICY_V1) == (
        "core:deterministic_supported_state@1"
    )
    parameters = set(inspect.signature(derive_supported_state_v1).parameters)
    assert parameters == {"records", "frame", "request"}
