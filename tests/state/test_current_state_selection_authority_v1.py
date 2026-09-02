from dataclasses import replace

import pytest

from capability_lab.state import (
    CurrentStateSelectionAction,
    InvalidCurrentStateSelection,
    PersonalCapabilityCurrentStateSelectionAuthorityBasis,
    PersonalCapabilityCurrentStateSelectionHistory,
    PersonalCapabilityStateAcceptanceSet,
    PersonalCapabilityStateSet,
    select_current_personal_capability_state_v1,
    validate_personal_capability_current_state_selection_v1,
)

from test_current_state_selection_v1 import (
    CONCEPT,
    FRAME,
    OTHER_CONCEPT,
    OTHER_FRAME,
    SUBJECT,
    _accept,
    _request,
    _select_a_fixture,
    _state,
    _two_candidates,
)


def _basis(selection, state_snapshot, predecessor, successor, admissions=()):
    return PersonalCapabilityCurrentStateSelectionAuthorityBasis(
        selection=selection,
        state_snapshot=state_snapshot,
        acceptance_predecessor=predecessor,
        acceptance_successor=successor,
        acceptance_admissions=admissions,
    )


def _root_basis(fixture, history):
    return _basis(
        history.selections[0],
        fixture[2],
        fixture[7],
        fixture[8],
        (fixture[5], fixture[6]),
    )


def test_current_selection_authority_replays_exact_root_basis() -> None:
    fixture, history = _select_a_fixture()
    validated = validate_personal_capability_current_state_selection_v1(
        authority_bases=(_root_basis(fixture, history),),
        history=history,
        concept_ref=CONCEPT,
        frame_ref=FRAME,
    )
    assert validated is not None
    assert validated.selected_state_id == fixture[0].state_id


def test_root_authority_rejects_preloaded_nonempty_acceptance_predecessor() -> None:
    fixture = _two_candidates()
    preloaded_history = select_current_personal_capability_state_v1(
        state_snapshot=fixture[2],
        acceptance_predecessor=fixture[8],
        acceptance_successor=fixture[8],
        selection_history=PersonalCapabilityCurrentStateSelectionHistory(SUBJECT),
        request=_request(
            CurrentStateSelectionAction.SELECT,
            state_id=fixture[0].state_id,
            selected_minutes=5,
        ),
    )
    with pytest.raises(
        InvalidCurrentStateSelection,
        match="from an empty predecessor with fresh admissions",
    ):
        validate_personal_capability_current_state_selection_v1(
            authority_bases=(
                _basis(
                    preloaded_history.selections[0],
                    fixture[2],
                    fixture[8],
                    fixture[8],
                ),
            ),
            history=preloaded_history,
            concept_ref=CONCEPT,
            frame_ref=FRAME,
        )


def test_later_authority_rejects_laundered_preloaded_genesis() -> None:
    fixture = _two_candidates()
    history_a = select_current_personal_capability_state_v1(
        state_snapshot=fixture[2],
        acceptance_predecessor=fixture[8],
        acceptance_successor=fixture[8],
        selection_history=PersonalCapabilityCurrentStateSelectionHistory(SUBJECT),
        request=_request(
            CurrentStateSelectionAction.SELECT,
            state_id=fixture[0].state_id,
            selected_minutes=5,
        ),
    )
    history_b = select_current_personal_capability_state_v1(
        state_snapshot=fixture[2],
        acceptance_predecessor=fixture[8],
        acceptance_successor=fixture[8],
        selection_history=history_a,
        request=_request(
            CurrentStateSelectionAction.SELECT,
            state_id=fixture[1].state_id,
            selected_minutes=6,
        ),
    )
    root = min(history_b.selections, key=lambda item: item.selected_at)
    head = max(history_b.selections, key=lambda item: item.selected_at)
    with pytest.raises(
        InvalidCurrentStateSelection,
        match="from an empty predecessor with fresh admissions",
    ):
        validate_personal_capability_current_state_selection_v1(
            authority_bases=(
                _basis(root, fixture[2], fixture[8], fixture[8]),
                _basis(head, fixture[2], fixture[8], fixture[8]),
            ),
            history=history_b,
            concept_ref=CONCEPT,
            frame_ref=FRAME,
        )


def test_authority_rejects_forged_candidate_portfolio_binding() -> None:
    fixture, history = _select_a_fixture()
    original = history.selections[0]
    forged = replace(original, candidate_portfolio_sha256="0" * 64)
    forged_history = PersonalCapabilityCurrentStateSelectionHistory(SUBJECT, (forged,))
    with pytest.raises(
        InvalidCurrentStateSelection,
        match="candidate_portfolio_sha256 does not match complete recomputed",
    ):
        validate_personal_capability_current_state_selection_v1(
            authority_bases=(
                _basis(
                    forged,
                    fixture[2],
                    fixture[7],
                    fixture[8],
                    (fixture[5], fixture[6]),
                ),
            ),
            history=forged_history,
            concept_ref=CONCEPT,
            frame_ref=FRAME,
        )


def test_later_authority_rejects_laundered_forged_predecessor_selection() -> None:
    fixture, history_a = _select_a_fixture()
    root = history_a.selections[0]
    forged_root = replace(root, candidate_portfolio_sha256="0" * 64)
    forged_history_a = PersonalCapabilityCurrentStateSelectionHistory(
        SUBJECT,
        (forged_root,),
    )
    forged_history_b = select_current_personal_capability_state_v1(
        state_snapshot=fixture[2],
        acceptance_predecessor=fixture[8],
        acceptance_successor=fixture[8],
        selection_history=forged_history_a,
        request=_request(
            CurrentStateSelectionAction.SELECT,
            state_id=fixture[1].state_id,
            selected_minutes=6,
        ),
    )
    head = max(forged_history_b.selections, key=lambda item: item.selected_at)
    with pytest.raises(
        InvalidCurrentStateSelection,
        match="candidate_portfolio_sha256 does not match complete recomputed",
    ):
        validate_personal_capability_current_state_selection_v1(
            authority_bases=(
                _basis(
                    forged_root,
                    fixture[2],
                    fixture[7],
                    fixture[8],
                    (fixture[5], fixture[6]),
                ),
                _basis(head, fixture[2], fixture[8], fixture[8]),
            ),
            history=forged_history_b,
            concept_ref=CONCEPT,
            frame_ref=FRAME,
        )


def test_later_authority_requires_full_acceptance_ancestry_basis() -> None:
    fixture, history_a = _select_a_fixture()
    history_b = select_current_personal_capability_state_v1(
        state_snapshot=fixture[2],
        acceptance_predecessor=fixture[8],
        acceptance_successor=fixture[8],
        selection_history=history_a,
        request=_request(
            CurrentStateSelectionAction.SELECT,
            state_id=fixture[1].state_id,
            selected_minutes=6,
        ),
    )
    head = max(history_b.selections, key=lambda item: item.selected_at)
    with pytest.raises(
        InvalidCurrentStateSelection,
        match="must cover exactly the subject selection history",
    ):
        validate_personal_capability_current_state_selection_v1(
            authority_bases=(
                _basis(head, fixture[2], fixture[8], fixture[8]),
            ),
            history=history_b,
            concept_ref=CONCEPT,
            frame_ref=FRAME,
        )


def test_later_authority_rejects_acceptance_universe_rollback_or_subset() -> None:
    fixture, history_a = _select_a_fixture()
    history_b = select_current_personal_capability_state_v1(
        state_snapshot=fixture[2],
        acceptance_predecessor=fixture[8],
        acceptance_successor=fixture[8],
        selection_history=history_a,
        request=_request(
            CurrentStateSelectionAction.SELECT,
            state_id=fixture[1].state_id,
            selected_minutes=6,
        ),
    )
    only_a = PersonalCapabilityStateAcceptanceSet(SUBJECT, (fixture[3],))
    root = min(history_b.selections, key=lambda item: item.selected_at)
    head = max(history_b.selections, key=lambda item: item.selected_at)
    with pytest.raises(
        InvalidCurrentStateSelection,
        match="acceptance lineage predecessor must exactly equal",
    ):
        validate_personal_capability_current_state_selection_v1(
            authority_bases=(
                _basis(
                    root,
                    fixture[2],
                    fixture[7],
                    fixture[8],
                    (fixture[5], fixture[6]),
                ),
                _basis(head, fixture[2], only_a, only_a),
            ),
            history=history_b,
            concept_ref=CONCEPT,
            frame_ref=FRAME,
        )


def _cross_scope_authority_fixture(*, stale_target: bool):
    fixture = _two_candidates()
    state_a, state_b = fixture[0], fixture[1]
    states_ab = fixture[2]
    acceptance_a, acceptance_b = fixture[3], fixture[4]
    admission_a, admission_b = fixture[5], fixture[6]
    empty_acceptances = fixture[7]

    state_c = _state(
        "state_c_other_scope",
        concept=OTHER_CONCEPT,
        frame=OTHER_FRAME,
        as_of_minutes=4,
        derived_minutes=5,
    )
    states_abc = PersonalCapabilityStateSet(SUBJECT, (state_a, state_b, state_c))
    acceptance_c, admission_c = _accept(
        state_c,
        predecessor=states_ab,
        successor=states_abc,
        accepted_minutes=6,
    )
    acceptances_a = PersonalCapabilityStateAcceptanceSet(SUBJECT, (acceptance_a,))
    acceptances_abc = PersonalCapabilityStateAcceptanceSet(
        SUBJECT,
        (acceptance_a, acceptance_b, acceptance_c),
    )

    history_target = select_current_personal_capability_state_v1(
        state_snapshot=states_abc,
        acceptance_predecessor=empty_acceptances,
        acceptance_successor=acceptances_a,
        acceptance_admissions=(admission_a,),
        selection_history=PersonalCapabilityCurrentStateSelectionHistory(SUBJECT),
        request=_request(
            CurrentStateSelectionAction.SELECT,
            state_id=state_a.state_id,
            selected_minutes=7,
        ),
    )
    history_other = select_current_personal_capability_state_v1(
        state_snapshot=states_abc,
        acceptance_predecessor=acceptances_a,
        acceptance_successor=acceptances_abc,
        acceptance_admissions=(admission_b, admission_c),
        selection_history=history_target,
        request=_request(
            CurrentStateSelectionAction.SELECT,
            state_id=state_c.state_id,
            selected_minutes=8,
            concept=OTHER_CONCEPT,
            frame=OTHER_FRAME,
        ),
    )
    target_predecessor = acceptances_a if stale_target else acceptances_abc
    target_successor = acceptances_a if stale_target else acceptances_abc
    history_final = select_current_personal_capability_state_v1(
        state_snapshot=states_abc,
        acceptance_predecessor=target_predecessor,
        acceptance_successor=target_successor,
        selection_history=history_other,
        request=_request(
            CurrentStateSelectionAction.SELECT,
            state_id=state_a.state_id,
            selected_minutes=9,
        ),
    )

    by_minute = {item.selected_at.minute: item for item in history_final.selections}
    bases = (
        _basis(
            by_minute[7],
            states_abc,
            empty_acceptances,
            acceptances_a,
            (admission_a,),
        ),
        _basis(
            by_minute[8],
            states_abc,
            acceptances_a,
            acceptances_abc,
            (admission_b, admission_c),
        ),
        _basis(
            by_minute[9],
            states_abc,
            target_predecessor,
            target_successor,
        ),
    )
    return history_final, bases, state_a


def test_authority_rejects_cross_scope_acceptance_universe_rollback() -> None:
    history, bases, _ = _cross_scope_authority_fixture(stale_target=True)
    with pytest.raises(
        InvalidCurrentStateSelection,
        match="subject-wide acceptance lineage predecessor must exactly equal",
    ):
        validate_personal_capability_current_state_selection_v1(
            authority_bases=bases,
            history=history,
            concept_ref=CONCEPT,
            frame_ref=FRAME,
        )


def test_authority_accepts_cross_scope_subject_wide_acceptance_continuity() -> None:
    history, bases, state_a = _cross_scope_authority_fixture(stale_target=False)
    validated = validate_personal_capability_current_state_selection_v1(
        authority_bases=bases,
        history=history,
        concept_ref=CONCEPT,
        frame_ref=FRAME,
    )
    assert validated is not None
    assert validated.selected_state_id == state_a.state_id


def test_authority_rejects_same_timestamp_conflicting_acceptance_transitions() -> None:
    fixture = _two_candidates()
    state_a, state_b = fixture[0], fixture[1]
    states_ab = fixture[2]
    acceptance_a, acceptance_b = fixture[3], fixture[4]
    admission_a, admission_b = fixture[5], fixture[6]
    empty_acceptances = fixture[7]
    acceptances_a = PersonalCapabilityStateAcceptanceSet(SUBJECT, (acceptance_a,))
    acceptances_ab = PersonalCapabilityStateAcceptanceSet(
        SUBJECT,
        (acceptance_a, acceptance_b),
    )

    history_target = select_current_personal_capability_state_v1(
        state_snapshot=states_ab,
        acceptance_predecessor=empty_acceptances,
        acceptance_successor=acceptances_a,
        acceptance_admissions=(admission_a,),
        selection_history=PersonalCapabilityCurrentStateSelectionHistory(SUBJECT),
        request=_request(
            CurrentStateSelectionAction.SELECT,
            state_id=state_a.state_id,
            selected_minutes=7,
        ),
    )
    history_other = select_current_personal_capability_state_v1(
        state_snapshot=states_ab,
        acceptance_predecessor=acceptances_a,
        acceptance_successor=acceptances_ab,
        acceptance_admissions=(admission_b,),
        selection_history=history_target,
        request=_request(
            CurrentStateSelectionAction.SELECT,
            state_id=state_b.state_id,
            selected_minutes=7,
            concept=CONCEPT,
            frame=FRAME,
        ),
    )
    root = min(
        history_other.selections,
        key=lambda item: item.predecessor_selection_sha256 is not None,
    )
    head = max(
        history_other.selections,
        key=lambda item: item.predecessor_selection_sha256 is not None,
    )
    with pytest.raises(
        InvalidCurrentStateSelection,
        match="selection acts sharing selected_at must bind one exact",
    ):
        validate_personal_capability_current_state_selection_v1(
            authority_bases=(
                _basis(
                    root,
                    states_ab,
                    empty_acceptances,
                    acceptances_a,
                    (admission_a,),
                ),
                _basis(
                    head,
                    states_ab,
                    acceptances_a,
                    acceptances_ab,
                    (admission_b,),
                ),
            ),
            history=history_other,
            concept_ref=CONCEPT,
            frame_ref=FRAME,
        )


def test_structural_resolver_result_is_not_progression_authority_by_itself() -> None:
    fixture, history = _select_a_fixture()
    selection = history.selections[0]
    assert selection.selected_state_id == fixture[0].state_id
    assert not hasattr(selection, "progression_authority")
    assert not hasattr(selection, "progression_state_id")


def test_authority_module_import_surface_has_no_downstream_layers() -> None:
    import ast
    from pathlib import Path

    root = Path(__file__).parents[2]
    tree = ast.parse(
        (root / "src/capability_lab/state/current_selection_authority.py").read_text()
    )
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
    forbidden = ("progression", "player_window", "proposals", "derivation")
    assert not any(fragment in name for name in imported for fragment in forbidden)


class _HistorySubclass(PersonalCapabilityCurrentStateSelectionHistory):
    pass


class _AuthorityBasesTupleSubclass(tuple):
    pass


@pytest.mark.parametrize(
    "authority_bases",
    (
        None,
        [],
        _AuthorityBasesTupleSubclass(),
    ),
)
def test_absent_scope_rejects_malformed_falsey_authority_bases(authority_bases) -> None:
    with pytest.raises(
        InvalidCurrentStateSelection,
        match="authority_bases must be exact tuple",
    ):
        validate_personal_capability_current_state_selection_v1(
            authority_bases=authority_bases,
            history=PersonalCapabilityCurrentStateSelectionHistory(SUBJECT),
            concept_ref=CONCEPT,
            frame_ref=FRAME,
        )


def test_absent_scope_rejects_corrupted_exact_concept_ref() -> None:
    corrupted = type(CONCEPT).parse(str(CONCEPT))
    object.__setattr__(corrupted, "revision", 0)
    with pytest.raises(
        InvalidCurrentStateSelection,
        match="concept_ref must survive strict semantic round-trip",
    ):
        validate_personal_capability_current_state_selection_v1(
            history=PersonalCapabilityCurrentStateSelectionHistory(SUBJECT),
            concept_ref=corrupted,
            frame_ref=FRAME,
        )


def test_absent_scope_rejects_corrupted_exact_frame_ref() -> None:
    corrupted = type(FRAME).parse(str(FRAME))
    object.__setattr__(corrupted, "revision", 0)
    with pytest.raises(
        InvalidCurrentStateSelection,
        match="frame_ref must survive strict semantic round-trip",
    ):
        validate_personal_capability_current_state_selection_v1(
            history=PersonalCapabilityCurrentStateSelectionHistory(SUBJECT),
            concept_ref=CONCEPT,
            frame_ref=corrupted,
        )


def test_clear_authority_replay_returns_none_after_full_validation() -> None:
    fixture, history_a = _select_a_fixture()
    cleared = select_current_personal_capability_state_v1(
        state_snapshot=fixture[2],
        acceptance_predecessor=fixture[8],
        acceptance_successor=fixture[8],
        selection_history=history_a,
        request=_request(
            CurrentStateSelectionAction.CLEAR,
            selected_minutes=6,
        ),
    )
    root = min(cleared.selections, key=lambda item: item.selected_at)
    head = max(cleared.selections, key=lambda item: item.selected_at)
    validated = validate_personal_capability_current_state_selection_v1(
        authority_bases=(
            _basis(
                root,
                fixture[2],
                fixture[7],
                fixture[8],
                (fixture[5], fixture[6]),
            ),
            _basis(head, fixture[2], fixture[8], fixture[8]),
        ),
        history=cleared,
        concept_ref=CONCEPT,
        frame_ref=FRAME,
    )
    assert validated is None


@pytest.mark.parametrize(
    ("field_name", "overrides"),
    (
        ("concept_ref", {"concept_ref": str(CONCEPT)}),
        ("frame_ref", {"frame_ref": str(FRAME)}),
    ),
)
def test_authority_rejects_non_exact_scope_types(field_name, overrides) -> None:
    fixture, history = _select_a_fixture()
    kwargs = {
        "authority_bases": (_root_basis(fixture, history),),
        "history": history,
        "concept_ref": CONCEPT,
        "frame_ref": FRAME,
    }
    kwargs.update(overrides)
    with pytest.raises(InvalidCurrentStateSelection, match=f"{field_name} must use exact type"):
        validate_personal_capability_current_state_selection_v1(**kwargs)


def test_authority_rejects_history_subclass_before_resolution() -> None:
    fixture, history = _select_a_fixture()
    subclass_history = _HistorySubclass(
        subject_ref=history.subject_ref,
        selections=history.selections,
    )
    with pytest.raises(InvalidCurrentStateSelection, match="history must use exact type"):
        validate_personal_capability_current_state_selection_v1(
            authority_bases=(_root_basis(fixture, history),),
            history=subclass_history,
            concept_ref=CONCEPT,
            frame_ref=FRAME,
        )


def test_authority_module_import_surface_is_exactly_frozen() -> None:
    import ast
    from pathlib import Path

    root = Path(__file__).parents[2]
    path = root / "src/capability_lab/state/current_selection_authority.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))

    normal = set()
    from_imports = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            normal.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            from_imports.add(
                (
                    node.module,
                    node.level,
                    tuple(alias.name for alias in node.names),
                )
            )

    assert normal == set()
    assert from_imports == {
        ("__future__", 0, ("annotations",)),
        ("dataclasses", 0, ("dataclass",)),
        (
            "acceptance",
            1,
            ("personal_capability_state_content_sha256_v1",),
        ),
        (
            "acceptance_set",
            1,
            (
                "PersonalCapabilityStateAcceptanceAdmission",
                "PersonalCapabilityStateAcceptanceSet",
                "validate_personal_capability_state_acceptance_set_successor_v1",
            ),
        ),
        (
            "core",
            1,
            ("CompetenceFrameRef", "PersonalCapabilityStateSet"),
        ),
        (
            "current_selection",
            1,
            (
                "CurrentStateSelectionAction",
                "InvalidCurrentStateSelection",
                "PersonalCapabilityCurrentStateSelection",
                "PersonalCapabilityCurrentStateSelectionHistory",
                "build_complete_current_state_candidate_portfolio_v1",
                "current_state_candidate_portfolio_sha256_v1",
                "personal_capability_current_state_selection_history_sha256_v1",
                "personal_capability_current_state_selection_sha256_v1",
            ),
        ),
        (
            "snapshot_transition",
            1,
            ("personal_capability_state_set_sha256_v1",),
        ),
        ("capability_lab.semantics", 0, ("CapabilityConceptRef",)),
    }
