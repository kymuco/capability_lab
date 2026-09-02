from datetime import datetime, timedelta, timezone

import pytest

from capability_lab.epistemics import (
    EvaluationPolicyRef,
    InvalidEvaluationError,
    InvalidProvenanceError,
    ProvenanceSource,
    ProvenanceSourceKind,
    ProvenanceStep,
    ProvenanceTrail,
)


T0 = datetime(2026, 8, 14, 9, 0, tzinfo=timezone.utc)


def test_policy_direct_constructor_rejects_string_revision() -> None:
    with pytest.raises(InvalidEvaluationError, match="integer"):
        EvaluationPolicyRef("core", "manual_evidence_review", "1")  # type: ignore[arg-type]


def test_policy_namespace_uses_same_segmented_machine_syntax() -> None:
    assert str(EvaluationPolicyRef("org.team", "review", 1)) == "org.team:review@1"
    with pytest.raises(InvalidEvaluationError):
        EvaluationPolicyRef("org..team", "review", 1)


def test_provenance_step_order_is_semantic_and_preserved() -> None:
    first = ProvenanceStep("capture", T0)
    second = ProvenanceStep("normalize", T0 + timedelta(seconds=1))
    trail = ProvenanceTrail(
        sources=(ProvenanceSource(ProvenanceSourceKind.SYSTEM, "system_01"),),
        steps=(first, second),
    )
    assert trail.steps == (first, second)


def test_reverse_time_provenance_chain_is_rejected() -> None:
    first = ProvenanceStep("normalize", T0 + timedelta(seconds=1))
    second = ProvenanceStep("capture", T0)
    with pytest.raises(InvalidProvenanceError, match="ordered"):
        ProvenanceTrail(
            sources=(ProvenanceSource(ProvenanceSourceKind.SYSTEM, "system_01"),),
            steps=(first, second),
        )
