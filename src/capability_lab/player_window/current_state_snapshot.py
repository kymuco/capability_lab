"""PR11.11 governed current-state product/read snapshot v1."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json

from capability_lab.epistemics import CapabilitySubjectRef, EpistemicRecordSet
from capability_lab.history import (
    AchievementFamilyCatalog,
    AchievementInstanceId,
    PersonalHistoryRecordSet,
    PersonalLegendId,
    PersonalLegendSet,
    PersonalMilestoneEventId,
)
from capability_lab.progression import (
    CurrentStateProgressionAuthorityBinding,
    CurrentStateProgressionAuthorityStatus,
    CurrentStateProgressionFrontierRequest,
    ProgressionFrontierSet,
    current_state_governed_progression_frontier_sha256_v1,
    derive_progression_frontier_from_current_state_v1,
)
from capability_lab.semantics import CapabilityCatalog
from capability_lab.state import (
    CompetenceFrameCatalog,
    CurrentStateSelectionAction,
    PersonalCapabilityCurrentStatePortfolioEntry,
    PersonalCapabilityCurrentStateSelectionAuthorityBasis,
    PersonalCapabilityCurrentStateSelectionHistory,
    derive_personal_capability_current_state_portfolio_v1,
    personal_capability_current_state_portfolio_sha256_v1,
)
from .core import (
    PlayerWindow,
    PlayerWindowError,
    PlayerWindowId,
    PlayerWindowRequest,
    PlayerWindowRequesterRef,
    PlayerWindowViewerRef,
)
from .derivation import derive_player_window_v1
from .verification import validate_player_window_v1


class CurrentStateGovernedPlayerWindowError(PlayerWindowError):
    """PR11.11 cannot construct or validate the governed product/read snapshot."""


class InvalidCurrentStateGovernedPlayerWindow(CurrentStateGovernedPlayerWindowError):
    """The supplied PR11.11 request, source set, or artifact is invalid."""


_HASH_DOMAIN = b"capability_lab/current_state_governed_player_window@1\x00"
_HEX = frozenset("0123456789abcdef")


def _fail(message: str) -> None:
    raise InvalidCurrentStateGovernedPlayerWindow(message)


def _exact(value: object, expected: type, label: str):
    if type(value) is not expected:
        _fail(f"{label} must use exact type {expected.__name__}")
    return value


def _sha(value: object, label: str) -> str:
    value = _exact(value, str, label)
    if len(value) != 64 or any(character not in _HEX for character in value):
        _fail(f"{label} must be 64 lowercase hexadecimal SHA-256 characters")
    return value


def _time(value: object, label: str) -> datetime:
    value = _exact(value, datetime, label)
    if value.tzinfo is not timezone.utc:
        _fail(f"{label} must be timezone-aware and already normalized to UTC")
    return value


def _subject(value: object, label: str) -> CapabilitySubjectRef:
    value = _exact(value, CapabilitySubjectRef, label)
    try:
        restored = CapabilitySubjectRef(value.value)
    except (TypeError, ValueError) as exc:
        raise InvalidCurrentStateGovernedPlayerWindow(
            f"{label} must survive strict semantic reconstruction: {exc}"
        ) from exc
    if restored != value:
        _fail(f"{label} must equal strict semantic reconstruction")
    return value


def _opaque_id(value: object, expected: type, label: str):
    value = _exact(value, expected, label)
    try:
        restored = expected(str(value))
    except (TypeError, ValueError) as exc:
        raise InvalidCurrentStateGovernedPlayerWindow(
            f"{label} must survive strict semantic reconstruction: {exc}"
        ) from exc
    if restored != value:
        _fail(f"{label} must equal strict semantic reconstruction")
    return value


def _requester(value: object, expected: type, label: str):
    value = _exact(value, expected, label)
    try:
        restored = expected(value.kind, value.ref)
    except (TypeError, ValueError) as exc:
        raise InvalidCurrentStateGovernedPlayerWindow(
            f"{label} must survive strict semantic reconstruction: {exc}"
        ) from exc
    if restored != value:
        _fail(f"{label} must equal strict semantic reconstruction")
    return value


def _strict_progression_request(value: object) -> CurrentStateProgressionFrontierRequest:
    value = _exact(value, CurrentStateProgressionFrontierRequest, "progression_request")
    try:
        restored = CurrentStateProgressionFrontierRequest(
            frontier_id=value.frontier_id,
            as_of=value.as_of,
            generated_at=value.generated_at,
            requester_ref=value.requester_ref,
            focuses=value.focuses,
            seeds=value.seeds,
            prerequisite_checks=value.prerequisite_checks,
            exploration_inputs=value.exploration_inputs,
        )
    except (TypeError, ValueError) as exc:
        raise InvalidCurrentStateGovernedPlayerWindow(
            f"progression_request failed strict semantic reconstruction: {exc}"
        ) from exc
    if restored != value:
        _fail("progression_request must equal strict semantic reconstruction")
    return value


def _typed_ids(value: object, expected: type, label: str) -> tuple:
    if type(value) is not tuple:
        _fail(f"{label} must be exact tuple")
    restored = tuple(_opaque_id(item, expected, label) for item in value)
    if len(set(restored)) != len(restored):
        _fail(f"{label} must not contain duplicates")
    return tuple(sorted(restored, key=str))


@dataclass(frozen=True, slots=True)
class CurrentStatePlayerWindowRequest:
    window_id: PlayerWindowId
    generated_at: datetime
    requester_ref: PlayerWindowRequesterRef
    viewer_ref: PlayerWindowViewerRef
    progression_request: CurrentStateProgressionFrontierRequest
    visible_achievement_ids: tuple[AchievementInstanceId, ...] = ()
    visible_milestone_ids: tuple[PersonalMilestoneEventId, ...] = ()
    visible_legend_id: PersonalLegendId | None = None

    def __post_init__(self) -> None:
        _opaque_id(self.window_id, PlayerWindowId, "window_id")
        generated_at = _time(self.generated_at, "generated_at")
        _requester(self.requester_ref, PlayerWindowRequesterRef, "requester_ref")
        _requester(self.viewer_ref, PlayerWindowViewerRef, "viewer_ref")
        progression_request = _strict_progression_request(self.progression_request)
        if generated_at != progression_request.generated_at:
            _fail("snapshot generated_at must exactly equal progression_request.generated_at")
        achievements = _typed_ids(
            self.visible_achievement_ids,
            AchievementInstanceId,
            "visible_achievement_ids",
        )
        milestones = _typed_ids(
            self.visible_milestone_ids,
            PersonalMilestoneEventId,
            "visible_milestone_ids",
        )
        if self.visible_legend_id is not None:
            _opaque_id(self.visible_legend_id, PersonalLegendId, "visible_legend_id")
        object.__setattr__(self, "generated_at", generated_at)
        object.__setattr__(self, "visible_achievement_ids", achievements)
        object.__setattr__(self, "visible_milestone_ids", milestones)

    @property
    def as_of(self) -> datetime:
        return self.progression_request.as_of

    def to_dict(self) -> dict:
        from .current_state_snapshot_serialization import request_to_dict
        return request_to_dict(self)

    @classmethod
    def from_dict(cls, payload: object) -> "CurrentStatePlayerWindowRequest":
        from .current_state_snapshot_serialization import request_from_dict
        return request_from_dict(payload)

    def to_json(self) -> str:
        from .current_state_snapshot_serialization import request_to_json
        return request_to_json(self)

    @classmethod
    def from_json(cls, payload: str) -> "CurrentStatePlayerWindowRequest":
        from .current_state_snapshot_serialization import request_from_json
        return request_from_json(payload)


def _strict_request(value: object) -> CurrentStatePlayerWindowRequest:
    value = _exact(value, CurrentStatePlayerWindowRequest, "request")
    restored = CurrentStatePlayerWindowRequest(
        window_id=value.window_id,
        generated_at=value.generated_at,
        requester_ref=value.requester_ref,
        viewer_ref=value.viewer_ref,
        progression_request=value.progression_request,
        visible_achievement_ids=value.visible_achievement_ids,
        visible_milestone_ids=value.visible_milestone_ids,
        visible_legend_id=value.visible_legend_id,
    )
    if restored != value:
        _fail("request must equal strict semantic reconstruction")
    return value


def _strict_entry(value: object) -> PersonalCapabilityCurrentStatePortfolioEntry:
    value = _exact(value, PersonalCapabilityCurrentStatePortfolioEntry, "current_state_entry")
    try:
        restored = PersonalCapabilityCurrentStatePortfolioEntry(
            concept_ref=value.concept_ref,
            frame_ref=value.frame_ref,
            action=value.action,
            current_selection_sha256=value.current_selection_sha256,
            selected_state_id=value.selected_state_id,
            selected_state_sha256=value.selected_state_sha256,
        )
    except (TypeError, ValueError) as exc:
        raise InvalidCurrentStateGovernedPlayerWindow(
            f"current_state_entry failed strict semantic reconstruction: {exc}"
        ) from exc
    if restored != value:
        _fail("current_state_entry must equal strict semantic reconstruction")
    return value


def _strict_binding(value: object) -> CurrentStateProgressionAuthorityBinding:
    value = _exact(value, CurrentStateProgressionAuthorityBinding, "frontier_authority_binding")
    try:
        restored = CurrentStateProgressionAuthorityBinding(
            concept_ref=value.concept_ref,
            frame_ref=value.frame_ref,
            status=value.status,
            current_selection_sha256=value.current_selection_sha256,
            selected_state_id=value.selected_state_id,
            selected_state_sha256=value.selected_state_sha256,
        )
    except (TypeError, ValueError) as exc:
        raise InvalidCurrentStateGovernedPlayerWindow(
            f"frontier_authority_binding failed strict semantic reconstruction: {exc}"
        ) from exc
    if restored != value:
        _fail("frontier_authority_binding must equal strict semantic reconstruction")
    return value


def _scope_key(value) -> tuple[str, str]:
    return str(value.concept_ref), str(value.frame_ref)


def _reconcile_authority(*, entries, bindings) -> None:
    by_scope = {(item.concept_ref, item.frame_ref): item for item in entries}
    for binding in bindings:
        entry = by_scope.get((binding.concept_ref, binding.frame_ref))
        if binding.status is CurrentStateProgressionAuthorityStatus.SELECT:
            if entry is None or entry.action is not CurrentStateSelectionAction.SELECT:
                _fail("PR11.9 SELECT authority must match PR11.10 SELECT for the exact scope")
            if (
                binding.current_selection_sha256 != entry.current_selection_sha256
                or binding.selected_state_id != entry.selected_state_id
                or binding.selected_state_sha256 != entry.selected_state_sha256
            ):
                _fail("PR11.9 SELECT authority identity must exactly match PR11.10 current entry")
        elif binding.status is CurrentStateProgressionAuthorityStatus.CLEAR:
            if entry is None or entry.action is not CurrentStateSelectionAction.CLEAR:
                _fail("PR11.9 CLEAR authority must match PR11.10 CLEAR for the exact scope")
            if binding.current_selection_sha256 != entry.current_selection_sha256:
                _fail("PR11.9 CLEAR selection identity must exactly match PR11.10 current entry")
        elif binding.status is CurrentStateProgressionAuthorityStatus.ABSENT:
            if entry is not None:
                _fail("PR11.9 ABSENT authority requires the exact scope to be absent from PR11.10")
        else:
            _fail("unsupported progression authority status")


def _strict_window(value: object) -> PlayerWindow:
    value = _exact(value, PlayerWindow, "window")
    try:
        restored = PlayerWindow.from_dict(value.to_dict())
    except (TypeError, ValueError) as exc:
        raise InvalidCurrentStateGovernedPlayerWindow(
            f"window failed strict PR9 semantic reconstruction: {exc}"
        ) from exc
    if restored != value:
        _fail("window must equal strict PR9 semantic reconstruction")
    return value


@dataclass(frozen=True, slots=True)
class CurrentStateGovernedPlayerWindow:
    request: CurrentStatePlayerWindowRequest
    subject_ref: CapabilitySubjectRef
    current_selection_history_sha256: str
    current_state_portfolio_sha256: str
    governed_frontier_sha256: str
    current_state_entries: tuple[PersonalCapabilityCurrentStatePortfolioEntry, ...]
    frontier_authority_bindings: tuple[CurrentStateProgressionAuthorityBinding, ...]
    window: PlayerWindow

    def __post_init__(self) -> None:
        request = _strict_request(self.request)
        subject = _subject(self.subject_ref, "subject_ref")
        _sha(self.current_selection_history_sha256, "current_selection_history_sha256")
        _sha(self.current_state_portfolio_sha256, "current_state_portfolio_sha256")
        _sha(self.governed_frontier_sha256, "governed_frontier_sha256")

        if type(self.current_state_entries) is not tuple:
            _fail("current_state_entries must be exact tuple")
        entries = tuple(_strict_entry(item) for item in self.current_state_entries)
        entries = tuple(sorted(entries, key=_scope_key))
        if len({_scope_key(item) for item in entries}) != len(entries):
            _fail("current_state_entries may contain each exact scope at most once")

        if type(self.frontier_authority_bindings) is not tuple:
            _fail("frontier_authority_bindings must be exact tuple")
        bindings = tuple(_strict_binding(item) for item in self.frontier_authority_bindings)
        bindings = tuple(sorted(bindings, key=_scope_key))
        if len({_scope_key(item) for item in bindings}) != len(bindings):
            _fail("frontier_authority_bindings may contain each exact scope at most once")

        _reconcile_authority(entries=entries, bindings=bindings)
        window = _strict_window(self.window)
        if window.subject_ref != subject:
            _fail("window belongs to a different subject")
        if window.window_id != request.window_id:
            _fail("window_id must exactly match request")
        if window.as_of != request.as_of:
            _fail("window as_of must exactly match progression request as_of")
        if window.generated_at != request.generated_at:
            _fail("window generated_at must exactly match request")
        if window.requester_ref != request.requester_ref:
            _fail("window requester_ref must exactly match request")
        if window.viewer_ref != request.viewer_ref:
            _fail("window viewer_ref must exactly match request")
        if window.selected_achievement_ids != request.visible_achievement_ids:
            _fail("window history visibility must exactly match request")
        if window.selected_milestone_ids != request.visible_milestone_ids:
            _fail("window milestone visibility must exactly match request")
        if window.selected_legend_id != request.visible_legend_id:
            _fail("window Legend visibility must exactly match request")
        if window.selected_frontier_id != request.progression_request.frontier_id:
            _fail("window frontier must be the exact freshly governed frontier")
        if window.frontier is None:
            _fail("governed product/read snapshot requires a visible frontier panel")

        selected_entry_ids = tuple(
            sorted(
                (
                    item.selected_state_id
                    for item in entries
                    if item.action is CurrentStateSelectionAction.SELECT
                ),
                key=str,
            )
        )
        if window.selected_state_ids != selected_entry_ids:
            _fail("window must expose every and only PR11.10 current SELECT state")

        object.__setattr__(self, "request", request)
        object.__setattr__(self, "subject_ref", subject)
        object.__setattr__(self, "current_state_entries", entries)
        object.__setattr__(self, "frontier_authority_bindings", bindings)
        object.__setattr__(self, "window", window)

    def to_dict(self) -> dict:
        from .current_state_snapshot_serialization import snapshot_to_dict
        return snapshot_to_dict(self)

    @classmethod
    def from_dict(cls, payload: object) -> "CurrentStateGovernedPlayerWindow":
        from .current_state_snapshot_serialization import snapshot_from_dict
        return snapshot_from_dict(payload)

    def to_json(self) -> str:
        from .current_state_snapshot_serialization import snapshot_to_json
        return snapshot_to_json(self)

    @classmethod
    def from_json(cls, payload: str) -> "CurrentStateGovernedPlayerWindow":
        from .current_state_snapshot_serialization import snapshot_from_json
        return snapshot_from_json(payload)


def _strict_snapshot(value: object) -> CurrentStateGovernedPlayerWindow:
    value = _exact(value, CurrentStateGovernedPlayerWindow, "governed player window")
    restored = CurrentStateGovernedPlayerWindow(
        request=value.request,
        subject_ref=value.subject_ref,
        current_selection_history_sha256=value.current_selection_history_sha256,
        current_state_portfolio_sha256=value.current_state_portfolio_sha256,
        governed_frontier_sha256=value.governed_frontier_sha256,
        current_state_entries=value.current_state_entries,
        frontier_authority_bindings=value.frontier_authority_bindings,
        window=value.window,
    )
    if restored != value:
        _fail("governed player window must equal strict semantic reconstruction")
    return value


def _exact_inputs(
    *,
    capability_catalog,
    competence_frame_catalog,
    epistemic_records,
    selection_history,
    authority_bases,
    achievement_family_catalog,
    history_set,
    legend_set,
):
    _exact(capability_catalog, CapabilityCatalog, "capability_catalog")
    _exact(competence_frame_catalog, CompetenceFrameCatalog, "competence_frame_catalog")
    _exact(epistemic_records, EpistemicRecordSet, "epistemic_records")
    _exact(selection_history, PersonalCapabilityCurrentStateSelectionHistory, "selection_history")
    if type(authority_bases) is not tuple or any(
        type(item) is not PersonalCapabilityCurrentStateSelectionAuthorityBasis
        for item in authority_bases
    ):
        _fail("authority_bases must be exact tuple of exact PR11.8 authority bases")
    _exact(achievement_family_catalog, AchievementFamilyCatalog, "achievement_family_catalog")
    _exact(history_set, PersonalHistoryRecordSet, "history_set")
    _exact(legend_set, PersonalLegendSet, "legend_set")


def _derive_governed_sources(
    *,
    capability_catalog,
    competence_frame_catalog,
    epistemic_records,
    selection_history,
    authority_bases,
    request,
):
    try:
        portfolio = derive_personal_capability_current_state_portfolio_v1(
            history=selection_history,
            authority_bases=authority_bases,
            generated_at=request.generated_at,
        )
        governed_frontier = derive_progression_frontier_from_current_state_v1(
            capability_catalog=capability_catalog,
            frame_catalog=competence_frame_catalog,
            records=epistemic_records,
            selection_history=selection_history,
            authority_bases=authority_bases,
            request=request.progression_request,
        )
    except (TypeError, ValueError) as exc:
        raise InvalidCurrentStateGovernedPlayerWindow(
            f"fresh governed source derivation rejected snapshot inputs: {exc}"
        ) from exc

    if portfolio.current_selection_history_sha256 != governed_frontier.current_selection_history_sha256:
        _fail("PR11.10 portfolio and PR11.9 frontier must bind the same selection history")

    _reconcile_authority(
        entries=portfolio.entries,
        bindings=governed_frontier.authority_bindings,
    )

    if any(state.as_of > request.as_of for state in portfolio.current_state_set.states):
        _fail(
            "complete current profile contains state after snapshot as_of; historical filtering is forbidden"
        )
    return portfolio, governed_frontier


def derive_current_state_governed_player_window_v1(
    *,
    capability_catalog: CapabilityCatalog,
    competence_frame_catalog: CompetenceFrameCatalog,
    epistemic_records: EpistemicRecordSet,
    selection_history: PersonalCapabilityCurrentStateSelectionHistory,
    authority_bases: tuple[PersonalCapabilityCurrentStateSelectionAuthorityBasis, ...],
    achievement_family_catalog: AchievementFamilyCatalog,
    history_set: PersonalHistoryRecordSet,
    legend_set: PersonalLegendSet,
    request: CurrentStatePlayerWindowRequest,
) -> CurrentStateGovernedPlayerWindow:
    """Fresh-compose PR11.10 + PR11.9 into unchanged PR9 without caller state/frontier selection."""

    _exact_inputs(
        capability_catalog=capability_catalog,
        competence_frame_catalog=competence_frame_catalog,
        epistemic_records=epistemic_records,
        selection_history=selection_history,
        authority_bases=authority_bases,
        achievement_family_catalog=achievement_family_catalog,
        history_set=history_set,
        legend_set=legend_set,
    )
    request = _strict_request(request)
    subject = _subject(selection_history.subject_ref, "selection_history.subject_ref")

    if history_set.subject_ref != subject:
        _fail("history_set belongs to a different subject")
    if legend_set.subject_ref != subject:
        _fail("legend_set belongs to a different subject")

    portfolio, governed_frontier = _derive_governed_sources(
        capability_catalog=capability_catalog,
        competence_frame_catalog=competence_frame_catalog,
        epistemic_records=epistemic_records,
        selection_history=selection_history,
        authority_bases=authority_bases,
        request=request,
    )

    raw_request = PlayerWindowRequest(
        window_id=request.window_id,
        subject_ref=subject,
        as_of=request.as_of,
        generated_at=request.generated_at,
        requester_ref=request.requester_ref,
        viewer_ref=request.viewer_ref,
        selected_state_ids=tuple(state.state_id for state in portfolio.current_state_set.states),
        selected_achievement_ids=request.visible_achievement_ids,
        selected_milestone_ids=request.visible_milestone_ids,
        selected_legend_id=request.visible_legend_id,
        selected_frontier_id=governed_frontier.frontier.frontier_id,
    )
    frontier_set = ProgressionFrontierSet(subject, (governed_frontier.frontier,))
    try:
        window = derive_player_window_v1(
            capability_catalog=capability_catalog,
            competence_frame_catalog=competence_frame_catalog,
            epistemic_records=epistemic_records,
            state_set=portfolio.current_state_set,
            achievement_family_catalog=achievement_family_catalog,
            history_set=history_set,
            legend_set=legend_set,
            frontier_set=frontier_set,
            request=raw_request,
        )
        validate_player_window_v1(
            capability_catalog=capability_catalog,
            competence_frame_catalog=competence_frame_catalog,
            epistemic_records=epistemic_records,
            state_set=portfolio.current_state_set,
            achievement_family_catalog=achievement_family_catalog,
            history_set=history_set,
            legend_set=legend_set,
            frontier_set=frontier_set,
            window=window,
        )
    except (TypeError, ValueError) as exc:
        raise InvalidCurrentStateGovernedPlayerWindow(
            f"unchanged PR9 rejected governed product/read inputs: {exc}"
        ) from exc

    return CurrentStateGovernedPlayerWindow(
        request=request,
        subject_ref=subject,
        current_selection_history_sha256=portfolio.current_selection_history_sha256,
        current_state_portfolio_sha256=personal_capability_current_state_portfolio_sha256_v1(portfolio),
        governed_frontier_sha256=current_state_governed_progression_frontier_sha256_v1(governed_frontier),
        current_state_entries=portfolio.entries,
        frontier_authority_bindings=governed_frontier.authority_bindings,
        window=window,
    )


def validate_current_state_governed_player_window_v1(
    *,
    capability_catalog: CapabilityCatalog,
    competence_frame_catalog: CompetenceFrameCatalog,
    epistemic_records: EpistemicRecordSet,
    selection_history: PersonalCapabilityCurrentStateSelectionHistory,
    authority_bases: tuple[PersonalCapabilityCurrentStateSelectionAuthorityBasis, ...],
    achievement_family_catalog: AchievementFamilyCatalog,
    history_set: PersonalHistoryRecordSet,
    legend_set: PersonalLegendSet,
    snapshot: CurrentStateGovernedPlayerWindow,
) -> None:
    """Fresh-replay every governed source and require exact PR11.11 artifact equality."""

    snapshot = _strict_snapshot(snapshot)
    expected = derive_current_state_governed_player_window_v1(
        capability_catalog=capability_catalog,
        competence_frame_catalog=competence_frame_catalog,
        epistemic_records=epistemic_records,
        selection_history=selection_history,
        authority_bases=authority_bases,
        achievement_family_catalog=achievement_family_catalog,
        history_set=history_set,
        legend_set=legend_set,
        request=snapshot.request,
    )
    if expected != snapshot:
        _fail("governed player window does not equal fresh PR11.10 + PR11.9 + PR9 derivation")


def _progression_request_payload(request: CurrentStateProgressionFrontierRequest) -> dict:
    return {
        "frontier_id": str(request.frontier_id),
        "as_of": request.as_of.isoformat().replace("+00:00", "Z"),
        "generated_at": request.generated_at.isoformat().replace("+00:00", "Z"),
        "requester_ref": {"kind": request.requester_ref.kind.value, "ref": request.requester_ref.ref},
        "focuses": [
            {"concept_ref": str(item.concept_ref), "rationale": item.rationale}
            for item in request.focuses
        ],
        "seeds": [
            {
                "concept_ref": str(item.concept_ref),
                "frame_ref": str(item.frame_ref),
                "dimension_keys": list(item.dimension_keys),
            }
            for item in request.seeds
        ],
        "prerequisite_checks": [
            {
                "target_ref": str(item.target_ref),
                "prerequisite_ref": str(item.prerequisite_ref),
                "relation_scope": None if item.relation_scope is None else {
                    "key": item.relation_scope.key,
                    "description": item.relation_scope.description,
                },
                "frame_ref": str(item.frame_ref),
                "required_dimension_keys": list(item.required_dimension_keys),
            }
            for item in request.prerequisite_checks
        ],
        "exploration_inputs": [
            {"concept_ref": str(item.concept_ref), "rationale": item.rationale}
            for item in request.exploration_inputs
        ],
    }


def _request_payload(request: CurrentStatePlayerWindowRequest) -> dict:
    return {
        "window_id": str(request.window_id),
        "generated_at": request.generated_at.isoformat().replace("+00:00", "Z"),
        "requester_ref": {"kind": request.requester_ref.kind.value, "ref": request.requester_ref.ref},
        "viewer_ref": {"kind": request.viewer_ref.kind.value, "ref": request.viewer_ref.ref},
        "progression_request": _progression_request_payload(request.progression_request),
        "visible_achievement_ids": [str(item) for item in request.visible_achievement_ids],
        "visible_milestone_ids": [str(item) for item in request.visible_milestone_ids],
        "visible_legend_id": str(request.visible_legend_id) if request.visible_legend_id is not None else None,
    }


def current_state_governed_player_window_sha256_v1(
    snapshot: CurrentStateGovernedPlayerWindow,
) -> str:
    """Return deterministic domain-separated integrity identity for PR11.11."""

    snapshot = _strict_snapshot(snapshot)
    payload = {
        "request": _request_payload(snapshot.request),
        "subject_ref": str(snapshot.subject_ref),
        "current_selection_history_sha256": snapshot.current_selection_history_sha256,
        "current_state_portfolio_sha256": snapshot.current_state_portfolio_sha256,
        "governed_frontier_sha256": snapshot.governed_frontier_sha256,
        "current_state_entries": [
            {
                "concept_ref": str(item.concept_ref),
                "frame_ref": str(item.frame_ref),
                "action": item.action.value,
                "current_selection_sha256": item.current_selection_sha256,
                "selected_state_id": str(item.selected_state_id) if item.selected_state_id is not None else None,
                "selected_state_sha256": item.selected_state_sha256,
            }
            for item in snapshot.current_state_entries
        ],
        "frontier_authority_bindings": [
            {
                "concept_ref": str(item.concept_ref),
                "frame_ref": str(item.frame_ref),
                "status": item.status.value,
                "current_selection_sha256": item.current_selection_sha256,
                "selected_state_id": str(item.selected_state_id) if item.selected_state_id is not None else None,
                "selected_state_sha256": item.selected_state_sha256,
            }
            for item in snapshot.frontier_authority_bindings
        ],
        "window": snapshot.window.to_dict(),
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    digest = hashlib.sha256()
    digest.update(_HASH_DOMAIN)
    digest.update(encoded)
    return digest.hexdigest()
