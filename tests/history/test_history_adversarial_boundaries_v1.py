from datetime import datetime, timedelta, timezone

import pytest

from capability_lab.epistemics import CapabilitySubjectRef
from capability_lab.history import (
    HistoryMechanismKind,
    InvalidPersonalLegend,
    LegendGeneratorRef,
    LegendProjectionPolicyRef,
    PersonalLegend,
    PersonalLegendId,
)


T0 = datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("subject_pr7_adversarial")


def test_personal_legend_cannot_be_source_free_narrative() -> None:
    with pytest.raises(InvalidPersonalLegend):
        PersonalLegend(
            PersonalLegendId("legend_pr7_source_free"),
            SUBJECT,
            T0,
            T0 + timedelta(minutes=1),
            LegendProjectionPolicyRef.parse("core:personal_legend_projection@1"),
            LegendGeneratorRef(HistoryMechanismKind.MODEL, "test:model_legend"),
            "Source-free narrative",
            "A narrative without cited history must not become a PR7 PersonalLegend.",
            (),
        )


def test_history_mechanism_kind_is_identity_metadata_not_authority_enum() -> None:
    assert {item.value for item in HistoryMechanismKind} == {
        "human",
        "rule",
        "model",
        "hybrid",
        "external_system",
    }
    assert not hasattr(HistoryMechanismKind, "AUTHORIZED")
    assert not hasattr(HistoryMechanismKind, "TRUSTED")
