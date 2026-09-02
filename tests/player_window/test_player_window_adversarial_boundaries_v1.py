from dataclasses import fields
from datetime import datetime, timezone
import inspect

import pytest

import capability_lab.player_window as player_window
from capability_lab.epistemics import CapabilitySubjectRef
from capability_lab.player_window import (
    InvalidPlayerWindowRequest,
    PlayerWindow,
    PlayerWindowCapabilityEntry,
    PlayerWindowFrontierCandidateEntry,
    PlayerWindowId,
    PlayerWindowMechanismKind,
    PlayerWindowRequest,
    PlayerWindowRequesterRef,
    PlayerWindowViewerRef,
    derive_player_window_v1,
    render_player_window_html_v1,
)


T0 = datetime(2026, 8, 16, 10, 0, tzinfo=timezone.utc)


def test_request_requires_explicit_source_selection() -> None:
    with pytest.raises(InvalidPlayerWindowRequest):
        PlayerWindowRequest(
            PlayerWindowId("window_empty"),
            CapabilitySubjectRef("subject_window_empty"),
            T0,
            T0,
            PlayerWindowRequesterRef(PlayerWindowMechanismKind.HUMAN, "test:requester"),
            PlayerWindowViewerRef(PlayerWindowMechanismKind.HUMAN, "test:viewer"),
        )


def test_public_surface_exposes_no_score_rank_growth_or_auto_latest_shortcuts() -> None:
    forbidden_api = {
        "auto_select_latest_state",
        "auto_select_latest_legend",
        "auto_select_latest_frontier",
        "rank_player_window",
        "score_player_window",
        "compute_human_level",
        "compute_growth",
        "recommend_next",
        "best_next_step",
        "window_to_state",
        "window_to_claim",
        "publish_player_window",
    }
    assert forbidden_api.isdisjoint(set(dir(player_window)))

    forbidden_fields = {
        "score",
        "rank",
        "level",
        "xp",
        "priority",
        "difficulty",
        "readiness",
        "probability",
        "growth",
        "growth_score",
        "human_level",
    }
    for cls in (PlayerWindow, PlayerWindowCapabilityEntry, PlayerWindowFrontierCandidateEntry):
        assert forbidden_fields.isdisjoint({item.name for item in fields(cls)})

    derive_params = set(inspect.signature(derive_player_window_v1).parameters)
    assert "latest_state" not in derive_params
    assert "previous_window" not in derive_params
    assert "growth_policy" not in derive_params
    assert "ranking_policy" not in derive_params

    render_params = list(inspect.signature(render_player_window_html_v1).parameters)
    assert render_params == ["window"]
