import json
from dataclasses import replace

import pytest

from capability_lab.player_window import (
    InvalidPlayerWindow,
    InvalidPlayerWindowRequest,
    PlayerWindow,
    PlayerWindowId,
    PlayerWindowRequest,
    PlayerWindowSet,
)
from capability_lab.player_window.demo import build_civilization_bootstrap_player_window_demo_v1


def test_player_window_roundtrips_canonically() -> None:
    window = build_civilization_bootstrap_player_window_demo_v1()
    payload = window.to_json()
    restored = PlayerWindow.from_json(payload)
    assert restored == window
    assert restored.to_json() == payload


def test_player_window_request_roundtrips_canonically() -> None:
    window = build_civilization_bootstrap_player_window_demo_v1()
    request = PlayerWindowRequest(
        window.window_id,
        window.subject_ref,
        window.as_of,
        window.generated_at,
        window.requester_ref,
        window.viewer_ref,
        window.selected_state_ids,
        window.selected_achievement_ids,
        window.selected_milestone_ids,
        window.selected_legend_id,
        window.selected_frontier_id,
    )
    assert PlayerWindowRequest.from_json(request.to_json()) == request


def test_player_window_set_roundtrips_and_keeps_alternative_windows_without_latest_wins() -> None:
    first = build_civilization_bootstrap_player_window_demo_v1()
    second = replace(first, window_id=PlayerWindowId("player_window_demo_alternative"))
    windows = PlayerWindowSet(first.subject_ref, (second, first))

    restored = PlayerWindowSet.from_json(windows.to_json())
    assert restored == windows
    assert restored.windows == tuple(sorted((first, second), key=lambda item: str(item.window_id)))
    assert not hasattr(restored, "latest")
    assert not hasattr(restored, "canonical")


def test_boolean_schema_version_is_rejected() -> None:
    window = build_civilization_bootstrap_player_window_demo_v1()
    payload = json.loads(window.to_json())
    payload["schema_version"] = True
    with pytest.raises(InvalidPlayerWindow):
        PlayerWindow.from_json(json.dumps(payload))

    request_payload = json.loads(PlayerWindowRequest(
        window.window_id,
        window.subject_ref,
        window.as_of,
        window.generated_at,
        window.requester_ref,
        window.viewer_ref,
        window.selected_state_ids,
        window.selected_achievement_ids,
        window.selected_milestone_ids,
        window.selected_legend_id,
        window.selected_frontier_id,
    ).to_json())
    request_payload["schema_version"] = True
    with pytest.raises(InvalidPlayerWindowRequest):
        PlayerWindowRequest.from_json(json.dumps(request_payload))


def test_duplicate_json_keys_are_rejected() -> None:
    with pytest.raises(InvalidPlayerWindow):
        PlayerWindow.from_json('{"schema_version":1,"schema_version":1}')
