from datetime import datetime, timedelta, timezone

import pytest

from capability_lab.epistemics import CapabilitySubjectRef
from capability_lab.history import (
    AchievementBasisKind,
    AchievementBasisRef,
    AchievementFamily,
    AchievementFamilyCatalog,
    AchievementFamilyId,
    AchievementInstance,
    AchievementInstanceId,
    AchievementQualificationPolicyRef,
    AchievementQualifierRef,
    HistoryError,
    HistoryMechanismKind,
    LegendGeneratorRef,
    LegendProjectionPolicyRef,
    LegendSourceKind,
    LegendSourceRef,
    PersonalHistoryRecordSet,
    PersonalLegend,
    PersonalLegendEntry,
    PersonalLegendId,
    PersonalLegendSet,
)


T0 = datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("subject_pr7_serialization")
FAMILY = AchievementFamily(
    AchievementFamilyId("civilization_bootstrap", "serialization_build"),
    "Serialization Build",
    "A bounded accomplishment family used to exercise strict PR7 serialization.",
)
ACHIEVEMENT = AchievementInstance(
    AchievementInstanceId("achievement_pr7_serialization"),
    SUBJECT,
    FAMILY.ref,
    T0,
    T0 + timedelta(hours=1),
    AchievementQualificationPolicyRef.parse("core:achievement_qualification@1"),
    AchievementQualifierRef(HistoryMechanismKind.RULE, "test:qualifier_rule"),
    (AchievementBasisRef(AchievementBasisKind.EXTERNAL_ARTIFACT, "artifact:serialization"),),
    "Bounded serialization test context.",
)
LEGEND = PersonalLegend(
    PersonalLegendId("legend_pr7_serialization"),
    SUBJECT,
    T0 + timedelta(days=1),
    T0 + timedelta(days=2),
    LegendProjectionPolicyRef.parse("core:personal_legend_projection@1"),
    LegendGeneratorRef(HistoryMechanismKind.MODEL, "test:legend_model"),
    "Serialization legend",
    "A derived projection used only to test deterministic representation.",
    (
        PersonalLegendEntry(
            (LegendSourceRef(LegendSourceKind.ACHIEVEMENT_INSTANCE, str(ACHIEVEMENT.achievement_id)),),
            "Recorded accomplishment",
            "The projection cites the exact history record without replacing it.",
        ),
    ),
)


def test_family_history_and_legend_roundtrip_are_canonical() -> None:
    family_catalog = AchievementFamilyCatalog((FAMILY,))
    history = PersonalHistoryRecordSet(SUBJECT, (ACHIEVEMENT,), ())
    legends = PersonalLegendSet(SUBJECT, (LEGEND,))

    assert AchievementFamilyCatalog.from_json(family_catalog.to_json()) == family_catalog
    assert PersonalHistoryRecordSet.from_json(history.to_json()) == history
    assert PersonalLegend.from_json(LEGEND.to_json()) == LEGEND
    assert PersonalLegendSet.from_json(legends.to_json()) == legends

    assert AchievementFamilyCatalog.from_json(family_catalog.to_json()).to_json() == family_catalog.to_json()
    assert PersonalHistoryRecordSet.from_json(history.to_json()).to_json() == history.to_json()
    assert PersonalLegendSet.from_json(legends.to_json()).to_json() == legends.to_json()


def test_history_json_rejects_duplicate_object_keys_and_non_finite_numbers() -> None:
    payload = PersonalHistoryRecordSet(SUBJECT, (ACHIEVEMENT,), ()).to_json()
    duplicate = payload.replace('"schema_version":1', '"schema_version":1,"schema_version":1', 1)
    with pytest.raises(HistoryError):
        PersonalHistoryRecordSet.from_json(duplicate)

    with pytest.raises(HistoryError):
        PersonalHistoryRecordSet.from_json('{"schema_version":NaN}')


def test_history_json_rejects_noncanonical_timestamp_profiles() -> None:
    payload = PersonalHistoryRecordSet(SUBJECT, (ACHIEVEMENT,), ()).to_json()
    assert "2026-08-15T12:00:00Z" in payload

    for invalid in (
        "20260815T120000Z",
        "2026-08-15T12:00:00+0000",
        "2026-08-15T12:00:00.1234567Z",
        "2026-08-15T12:00:00",
    ):
        modified = payload.replace("2026-08-15T12:00:00Z", invalid, 1)
        with pytest.raises(HistoryError):
            PersonalHistoryRecordSet.from_json(modified)


def test_valid_offset_timestamps_canonicalize_to_utc() -> None:
    payload = PersonalHistoryRecordSet(SUBJECT, (ACHIEVEMENT,), ()).to_json()
    modified = payload.replace("2026-08-15T12:00:00Z", "2026-08-15T18:00:00+06:00", 1)
    restored = PersonalHistoryRecordSet.from_json(modified)

    assert restored.achievement_instances[0].achieved_at == T0
    assert "2026-08-15T12:00:00Z" in restored.to_json()
