import ast
from datetime import timedelta
from pathlib import Path

import pytest

from capability_lab.player_window import (
    CurrentStateGovernedPlayerWindow,
    CurrentStatePlayerWindowRequest,
    InvalidCurrentStateGovernedPlayerWindow,
    validate_current_state_governed_player_window_v1,
)
from capability_lab.progression import CurrentStateProgressionAuthorityStatus
from capability_lab.state import CurrentStateSelectionAction

from test_current_state_governed_player_window_v1 import (
    T0,
    VIEWER,
    WINDOW_REQUESTER,
    _case,
    _clear_a,
    _derive,
    _request,
    _seed_progression_request,
)


def _validate(case, snapshot, *, history=None, bases=None):
    return validate_current_state_governed_player_window_v1(
        capability_catalog=case["catalog"],
        competence_frame_catalog=case["frames"],
        epistemic_records=case["records"],
        selection_history=history or case["history"],
        authority_bases=case["bases"] if bases is None else bases,
        achievement_family_catalog=case["family_catalog"],
        history_set=case["history_set"],
        legend_set=case["legend_set"],
        snapshot=snapshot,
    )


def test_historical_current_selection_append_stales_cached_snapshot() -> None:
    case = _case()
    snapshot = _derive(case, _request(case))
    history, bases = _clear_a(case, minutes=24)
    assert all(
        item.selected_at <= snapshot.request.generated_at
        for item in history.selections
    )
    with pytest.raises(
        InvalidCurrentStateGovernedPlayerWindow,
        match="fresh governed source derivation rejected|does not equal",
    ):
        _validate(case, snapshot, history=history, bases=bases)


def test_future_governance_cannot_authorize_earlier_snapshot() -> None:
    case = _case()
    snapshot = _derive(case, _request(case))
    history, bases = _clear_a(case, minutes=41)
    with pytest.raises(
        InvalidCurrentStateGovernedPlayerWindow,
        match="fresh governed source derivation rejected",
    ):
        _validate(case, snapshot, history=history, bases=bases)


def test_complete_current_profile_is_never_silently_filtered_by_as_of() -> None:
    case = _case()
    progression = _seed_progression_request(
        case,
        as_of=T0 + timedelta(minutes=10),
        generated_at=T0 + timedelta(minutes=40),
    )
    with pytest.raises(
        InvalidCurrentStateGovernedPlayerWindow,
        match="historical filtering is forbidden",
    ):
        _derive(case, _request(case, progression=progression))


def test_tampered_frontier_authority_binding_is_rejected_inside_pr11_11_boundary() -> None:
    case = _case()
    snapshot = _derive(case, _request(case))
    binding = snapshot.frontier_authority_bindings[0]
    object.__setattr__(
        binding,
        "status",
        CurrentStateProgressionAuthorityStatus.ABSENT,
    )
    with pytest.raises(InvalidCurrentStateGovernedPlayerWindow):
        _validate(case, snapshot)


def test_omitting_one_current_scope_from_snapshot_is_rejected() -> None:
    case = _case()
    snapshot = _derive(case, _request(case))
    object.__setattr__(
        snapshot,
        "current_state_entries",
        (snapshot.current_state_entries[0],),
    )
    with pytest.raises(
        InvalidCurrentStateGovernedPlayerWindow,
        match="every and only PR11.10 current SELECT state",
    ):
        _validate(case, snapshot)


def test_tampered_raw_window_cannot_hide_current_state() -> None:
    case = _case()
    snapshot = _derive(case, _request(case))
    object.__setattr__(
        snapshot.window,
        "selected_state_ids",
        (case["state_a"].state_id,),
    )
    with pytest.raises(
        InvalidCurrentStateGovernedPlayerWindow,
        match="window failed strict PR9 semantic reconstruction",
    ):
        _validate(case, snapshot)


def test_request_rejects_noncanonical_visibility_container_and_time_split() -> None:
    case = _case()
    progression = _seed_progression_request(case)
    with pytest.raises(
        InvalidCurrentStateGovernedPlayerWindow,
        match="visible_achievement_ids must be exact tuple",
    ):
        CurrentStatePlayerWindowRequest(
            window_id=_request(case).window_id,
            generated_at=progression.generated_at,
            requester_ref=WINDOW_REQUESTER,
            viewer_ref=VIEWER,
            progression_request=progression,
            visible_achievement_ids=[],
        )

    with pytest.raises(
        InvalidCurrentStateGovernedPlayerWindow,
        match="must exactly equal progression_request.generated_at",
    ):
        CurrentStatePlayerWindowRequest(
            window_id=_request(case).window_id,
            generated_at=progression.generated_at + timedelta(seconds=1),
            requester_ref=WINDOW_REQUESTER,
            viewer_ref=VIEWER,
            progression_request=progression,
        )


def test_serialization_rejects_duplicate_json_keys() -> None:
    case = _case()
    snapshot = _derive(case, _request(case))
    payload = snapshot.to_json()
    forged = payload.replace(
        '"schema_version":1',
        '"schema_version":1,"schema_version":1',
        1,
    )
    with pytest.raises(
        InvalidCurrentStateGovernedPlayerWindow,
        match="duplicate JSON object keys",
    ):
        CurrentStateGovernedPlayerWindow.from_json(forged)


def test_clear_and_absent_are_not_interchangeable_in_stored_authority_projection() -> None:
    case = _case()
    history, bases = _clear_a(case)
    from test_current_state_governed_player_window_v1 import (
        _prerequisite_progression_request,
    )

    snapshot = _derive(
        case,
        _request(
            case,
            progression=_prerequisite_progression_request(case),
        ),
        history=history,
        bases=bases,
    )
    assert snapshot.current_state_entries[0].action in {
        CurrentStateSelectionAction.SELECT,
        CurrentStateSelectionAction.CLEAR,
    }
    binding = snapshot.frontier_authority_bindings[0]
    assert binding.status is CurrentStateProgressionAuthorityStatus.CLEAR
    object.__setattr__(
        binding,
        "status",
        CurrentStateProgressionAuthorityStatus.ABSENT,
    )
    object.__setattr__(binding, "current_selection_sha256", None)
    with pytest.raises(
        InvalidCurrentStateGovernedPlayerWindow,
        match="ABSENT authority requires",
    ):
        _validate(case, snapshot)


def test_production_import_surface_freezes_exact_modules_and_symbols() -> None:
    root = Path(__file__).parents[2]
    tree = ast.parse(
        (
            root
            / "src/capability_lab/player_window/current_state_snapshot.py"
        ).read_text()
    )
    imports = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.extend(("import", alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(
                (
                    "from",
                    node.level,
                    node.module,
                    tuple(alias.name for alias in node.names),
                )
            )

    assert imports == [
        ("from", 0, "__future__", ("annotations",)),
        ("from", 0, "dataclasses", ("dataclass",)),
        ("from", 0, "datetime", ("datetime", "timezone")),
        ("import", "hashlib"),
        ("import", "json"),
        (
            "from",
            0,
            "capability_lab.epistemics",
            ("CapabilitySubjectRef", "EpistemicRecordSet"),
        ),
        (
            "from",
            0,
            "capability_lab.history",
            (
                "AchievementFamilyCatalog",
                "AchievementInstanceId",
                "PersonalHistoryRecordSet",
                "PersonalLegendId",
                "PersonalLegendSet",
                "PersonalMilestoneEventId",
            ),
        ),
        (
            "from",
            0,
            "capability_lab.progression",
            (
                "CurrentStateProgressionAuthorityBinding",
                "CurrentStateProgressionAuthorityStatus",
                "CurrentStateProgressionFrontierRequest",
                "ProgressionFrontierSet",
                "current_state_governed_progression_frontier_sha256_v1",
                "derive_progression_frontier_from_current_state_v1",
            ),
        ),
        (
            "from",
            0,
            "capability_lab.semantics",
            ("CapabilityCatalog",),
        ),
        (
            "from",
            0,
            "capability_lab.state",
            (
                "CompetenceFrameCatalog",
                "CurrentStateSelectionAction",
                "PersonalCapabilityCurrentStatePortfolioEntry",
                "PersonalCapabilityCurrentStateSelectionAuthorityBasis",
                "PersonalCapabilityCurrentStateSelectionHistory",
                "derive_personal_capability_current_state_portfolio_v1",
                "personal_capability_current_state_portfolio_sha256_v1",
            ),
        ),
        (
            "from",
            1,
            "core",
            (
                "PlayerWindow",
                "PlayerWindowError",
                "PlayerWindowId",
                "PlayerWindowRequest",
                "PlayerWindowRequesterRef",
                "PlayerWindowViewerRef",
            ),
        ),
        ("from", 1, "derivation", ("derive_player_window_v1",)),
        ("from", 1, "verification", ("validate_player_window_v1",)),
    ]
