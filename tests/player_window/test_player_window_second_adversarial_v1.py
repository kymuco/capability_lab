from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from capability_lab.domains import (
    build_civilization_bootstrap_frame_catalog_v1,
    build_civilization_bootstrap_seed_catalog_v0,
)
from capability_lab.epistemics import CapabilitySubjectRef, EpistemicRecordSet
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
from capability_lab.player_window import (
    InvalidPlayerWindow,
    PlayerWindowId,
    PlayerWindowMechanismKind,
    PlayerWindowRequest,
    PlayerWindowRequesterRef,
    PlayerWindowViewerRef,
    derive_player_window_v1,
    render_player_window_html_v1,
    validate_player_window_v1,
)
from capability_lab.player_window.demo import (
    build_civilization_bootstrap_player_window_demo_v1,
)
from capability_lab.progression import ProgressionFrontierSet
from capability_lab.state import PersonalCapabilityStateSet


T0 = datetime(2020, 1, 1, 12, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("subject_pr9_second_adversarial")


def _family(*, definition: str = "Original bounded family semantics.") -> AchievementFamily:
    return AchievementFamily(
        AchievementFamilyId("test", "pr9_second_family"),
        "PR9 Second-Pass Achievement",
        definition,
    )


def _achievement(
    family: AchievementFamily,
    *,
    achievement_id: str = "achievement_pr9_second_selected",
    basis_kind: AchievementBasisKind = AchievementBasisKind.EXTERNAL_ARTIFACT,
    basis_ref: str = "artifact:pr9_second_selected",
    context: str = "Original selected historical context.",
) -> AchievementInstance:
    return AchievementInstance(
        AchievementInstanceId(achievement_id),
        SUBJECT,
        family.ref,
        T0,
        T0 + timedelta(minutes=1),
        AchievementQualificationPolicyRef.parse("test:pr9_second_qualification@1"),
        AchievementQualifierRef(HistoryMechanismKind.HUMAN, "test:pr9_second_qualifier"),
        (AchievementBasisRef(basis_kind, basis_ref),),
        context,
    )


def _request(
    achievement: AchievementInstance,
    *,
    legend_id: PersonalLegendId | None = None,
    as_of: datetime | None = None,
) -> PlayerWindowRequest:
    return PlayerWindowRequest(
        PlayerWindowId("window_pr9_second_adversarial"),
        SUBJECT,
        as_of or (T0 + timedelta(minutes=5)),
        T0 + timedelta(days=1),
        PlayerWindowRequesterRef(PlayerWindowMechanismKind.HUMAN, "test:requester"),
        PlayerWindowViewerRef(PlayerWindowMechanismKind.HUMAN, "test:viewer"),
        selected_achievement_ids=(achievement.achievement_id,),
        selected_legend_id=legend_id,
    )


def _derive_history_window(
    *,
    family_catalog: AchievementFamilyCatalog,
    history_set: PersonalHistoryRecordSet,
    request: PlayerWindowRequest,
    legend_set: PersonalLegendSet | None = None,
):
    return derive_player_window_v1(
        capability_catalog=build_civilization_bootstrap_seed_catalog_v0(),
        competence_frame_catalog=build_civilization_bootstrap_frame_catalog_v1(),
        epistemic_records=EpistemicRecordSet(),
        state_set=PersonalCapabilityStateSet(SUBJECT),
        achievement_family_catalog=family_catalog,
        history_set=history_set,
        legend_set=legend_set or PersonalLegendSet(SUBJECT),
        frontier_set=ProgressionFrontierSet(SUBJECT),
        request=request,
    )


def _verify_history_window(
    *,
    family_catalog: AchievementFamilyCatalog,
    history_set: PersonalHistoryRecordSet,
    window,
    legend_set: PersonalLegendSet | None = None,
) -> None:
    validate_player_window_v1(
        capability_catalog=build_civilization_bootstrap_seed_catalog_v0(),
        competence_frame_catalog=build_civilization_bootstrap_frame_catalog_v1(),
        epistemic_records=EpistemicRecordSet(),
        state_set=PersonalCapabilityStateSet(SUBJECT),
        achievement_family_catalog=family_catalog,
        history_set=history_set,
        legend_set=legend_set or PersonalLegendSet(SUBJECT),
        frontier_set=ProgressionFrontierSet(SUBJECT),
        window=window,
    )


def test_selected_history_must_satisfy_pr7_epistemic_governance_before_verified_window() -> None:
    family = _family()
    family_catalog = AchievementFamilyCatalog((family,))
    achievement = _achievement(
        family,
        basis_kind=AchievementBasisKind.EVIDENCE_RECORD,
        basis_ref="missing_evidence_pr9_second",
    )
    history_set = PersonalHistoryRecordSet(SUBJECT, (achievement,), ())
    window = _derive_history_window(
        family_catalog=family_catalog,
        history_set=history_set,
        request=_request(achievement),
    )

    with pytest.raises(InvalidPlayerWindow):
        _verify_history_window(
            family_catalog=family_catalog,
            history_set=history_set,
            window=window,
        )


def test_unselected_invalid_history_record_remains_inert_for_selected_window_verification() -> None:
    family = _family()
    family_catalog = AchievementFamilyCatalog((family,))
    selected = _achievement(family)
    unselected_invalid = _achievement(
        family,
        achievement_id="achievement_pr9_second_unselected_invalid",
        basis_kind=AchievementBasisKind.EVIDENCE_RECORD,
        basis_ref="missing_unselected_evidence_pr9_second",
        context="Unselected invalid history record.",
    )
    history_set = PersonalHistoryRecordSet(
        SUBJECT,
        (selected, unselected_invalid),
        (),
    )
    window = _derive_history_window(
        family_catalog=family_catalog,
        history_set=history_set,
        request=_request(selected),
    )

    _verify_history_window(
        family_catalog=family_catalog,
        history_set=history_set,
        window=window,
    )


def test_selected_legend_must_satisfy_pr7_cross_entry_source_governance() -> None:
    family = _family()
    family_catalog = AchievementFamilyCatalog((family,))
    achievement = _achievement(family)
    history_set = PersonalHistoryRecordSet(SUBJECT, (achievement,), ())
    source = LegendSourceRef(
        LegendSourceKind.ACHIEVEMENT_INSTANCE,
        str(achievement.achievement_id),
    )
    legend = PersonalLegend(
        PersonalLegendId("legend_pr9_second_replayed_source"),
        SUBJECT,
        T0 + timedelta(minutes=2),
        T0 + timedelta(minutes=3),
        LegendProjectionPolicyRef.parse("test:pr9_second_legend@1"),
        LegendGeneratorRef(HistoryMechanismKind.MODEL, "test:legend_generator"),
        "Structurally valid but source-replaying Legend",
        "The same source is intentionally replayed across two entries for the adversarial test.",
        (
            PersonalLegendEntry((source,), "Entry one", "First narrative use."),
            PersonalLegendEntry((source,), "Entry two", "Second narrative use."),
        ),
    )
    legend_set = PersonalLegendSet(SUBJECT, (legend,))
    window = _derive_history_window(
        family_catalog=family_catalog,
        history_set=history_set,
        legend_set=legend_set,
        request=_request(achievement, legend_id=legend.legend_id),
    )

    with pytest.raises(InvalidPlayerWindow):
        _verify_history_window(
            family_catalog=family_catalog,
            history_set=history_set,
            legend_set=legend_set,
            window=window,
        )


def test_same_ref_family_semantic_substitution_is_not_authenticated_by_pr9_verifier() -> None:
    family_a = _family(definition="Original family definition retained by source store A.")
    family_b = _family(definition="Materially different definition under the same exact ref in source store B.")
    assert family_a.ref == family_b.ref
    assert family_a.definition != family_b.definition
    assert family_a.name == family_b.name

    achievement = _achievement(family_a)
    history_set = PersonalHistoryRecordSet(SUBJECT, (achievement,), ())
    window = _derive_history_window(
        family_catalog=AchievementFamilyCatalog((family_a,)),
        history_set=history_set,
        request=_request(achievement),
    )

    # PR9 verifies consistency with the supplied snapshot. It does not authenticate
    # which same-ref semantic store is historically or institutionally authoritative.
    _verify_history_window(
        family_catalog=AchievementFamilyCatalog((family_b,)),
        history_set=history_set,
        window=window,
    )


def test_same_id_history_content_substitution_is_detected_when_projected_content_changes() -> None:
    family = _family()
    family_catalog = AchievementFamilyCatalog((family,))
    original = _achievement(family, context="Original selected historical context.")
    original_history = PersonalHistoryRecordSet(SUBJECT, (original,), ())
    window = _derive_history_window(
        family_catalog=family_catalog,
        history_set=original_history,
        request=_request(original),
    )

    substituted = replace(
        original,
        context="Substituted history content under the same opaque achievement id.",
    )
    substituted_history = PersonalHistoryRecordSet(SUBJECT, (substituted,), ())
    with pytest.raises(InvalidPlayerWindow):
        _verify_history_window(
            family_catalog=family_catalog,
            history_set=substituted_history,
            window=window,
        )


def test_historical_window_as_of_does_not_authenticate_semantic_snapshot_time() -> None:
    family_a = _family(definition="Semantic snapshot A.")
    family_b = _family(definition="Later or alternate same-ref semantic snapshot B.")
    achievement = _achievement(family_a)
    history_set = PersonalHistoryRecordSet(SUBJECT, (achievement,), ())
    historical_as_of = T0 + timedelta(minutes=5)
    window = _derive_history_window(
        family_catalog=AchievementFamilyCatalog((family_a,)),
        history_set=history_set,
        request=_request(achievement, as_of=historical_as_of),
    )

    assert window.as_of == historical_as_of
    _verify_history_window(
        family_catalog=AchievementFamilyCatalog((family_b,)),
        history_set=history_set,
        window=window,
    )


def test_local_html_omits_raw_evidence_payload_and_context_from_demo_projection() -> None:
    window = build_civilization_bootstrap_player_window_demo_v1()
    html = render_player_window_html_v1(window)

    assert "Private local read model" in html
    assert "Local HTML is not publication or authorization." in html
    assert "Analyzed and checked a bounded low-voltage DC setup with explicit assumptions." not in html
    assert "Local bench-style conceptual exercise with ordinary reference tools." not in html


def test_rendered_html_is_representation_not_a_verified_artifact_container() -> None:
    window = build_civilization_bootstrap_player_window_demo_v1()
    html = render_player_window_html_v1(window)
    modified_html = html.replace("Player Window", "Modified Artifact", 1)

    assert modified_html != html
    assert not hasattr(window, "rendered_html_digest")
    assert not hasattr(window, "artifact_signature")
