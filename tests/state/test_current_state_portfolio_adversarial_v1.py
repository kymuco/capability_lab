import ast
from dataclasses import fields, replace
from datetime import timedelta
import inspect
from pathlib import Path

import pytest

from capability_lab.semantics import CapabilityConceptRef
from capability_lab.state import (
    CurrentStateSelectionAction,
    InvalidPersonalCapabilityCurrentStatePortfolio,
    PersonalCapabilityCurrentStatePortfolio,
    PersonalCapabilityCurrentStatePortfolioEntry,
    PersonalCapabilityStateSet,
    derive_personal_capability_current_state_portfolio_v1,
    personal_capability_state_content_sha256_v1,
    select_current_personal_capability_state_v1,
    validate_personal_capability_current_state_portfolio_v1,
)

from test_current_state_selection_v1 import (
    CONCEPT,
    FRAME,
    OTHER_CONCEPT,
    OTHER_FRAME,
    SUBJECT,
    T0,
    _request,
    _select_a_fixture,
)
from test_current_state_selection_authority_v1 import (
    _basis,
    _cross_scope_authority_fixture,
    _root_basis,
)
from test_current_state_portfolio_v1 import _clear_fixture


def _cross_scope_with_clear():
    history, bases, _ = _cross_scope_authority_fixture(stale_target=False)
    last_basis = max(bases, key=lambda item: item.selection.selected_at)
    cleared = select_current_personal_capability_state_v1(
        state_snapshot=last_basis.state_snapshot,
        acceptance_predecessor=last_basis.acceptance_successor,
        acceptance_successor=last_basis.acceptance_successor,
        selection_history=history,
        request=_request(
            CurrentStateSelectionAction.CLEAR,
            selected_minutes=10,
            concept=OTHER_CONCEPT,
            frame=OTHER_FRAME,
        ),
    )
    clear = max(cleared.selections, key=lambda item: item.selected_at)
    clear_basis = _basis(
        clear,
        last_basis.state_snapshot,
        last_basis.acceptance_successor,
        last_basis.acceptance_successor,
    )
    return cleared, bases + (clear_basis,)


def test_fresh_validation_rejects_omission_of_explicit_clear_scope() -> None:
    history, bases = _cross_scope_with_clear()
    portfolio = derive_personal_capability_current_state_portfolio_v1(
        history=history,
        authority_bases=bases,
        generated_at=T0 + timedelta(minutes=11),
    )
    select_entry = next(
        item for item in portfolio.entries if item.action is CurrentStateSelectionAction.SELECT
    )
    omitted = PersonalCapabilityCurrentStatePortfolio(
        subject_ref=portfolio.subject_ref,
        generated_at=portfolio.generated_at,
        current_selection_history_sha256=portfolio.current_selection_history_sha256,
        entries=(select_entry,),
        current_state_set=portfolio.current_state_set,
    )
    with pytest.raises(
        InvalidPersonalCapabilityCurrentStatePortfolio,
        match="does not equal fresh complete governed derivation",
    ):
        validate_personal_capability_current_state_portfolio_v1(
            history=history,
            authority_bases=bases,
            portfolio=omitted,
        )


def test_fresh_validation_rejects_added_scope_absent_from_governed_history() -> None:
    fixture, history = _select_a_fixture()
    portfolio = derive_personal_capability_current_state_portfolio_v1(
        history=history,
        authority_bases=(_root_basis(fixture, history),),
        generated_at=T0 + timedelta(minutes=10),
    )
    fake = PersonalCapabilityCurrentStatePortfolioEntry(
        concept_ref=OTHER_CONCEPT,
        frame_ref=OTHER_FRAME,
        action=CurrentStateSelectionAction.CLEAR,
        current_selection_sha256="0" * 64,
        selected_state_id=None,
        selected_state_sha256=None,
    )
    expanded = PersonalCapabilityCurrentStatePortfolio(
        subject_ref=portfolio.subject_ref,
        generated_at=portfolio.generated_at,
        current_selection_history_sha256=portfolio.current_selection_history_sha256,
        entries=portfolio.entries + (fake,),
        current_state_set=portfolio.current_state_set,
    )
    with pytest.raises(
        InvalidPersonalCapabilityCurrentStatePortfolio,
        match="does not equal fresh complete governed derivation",
    ):
        validate_personal_capability_current_state_portfolio_v1(
            history=history,
            authority_bases=(_root_basis(fixture, history),),
            portfolio=expanded,
        )


def test_newer_accepted_state_cannot_replace_explicit_current_state() -> None:
    fixture, history = _select_a_fixture()
    basis = _root_basis(fixture, history)
    portfolio = derive_personal_capability_current_state_portfolio_v1(
        history=history,
        authority_bases=(basis,),
        generated_at=T0 + timedelta(minutes=10),
    )
    state_b_sha256 = personal_capability_state_content_sha256_v1(
        snapshot=fixture[2],
        state_id=fixture[1].state_id,
    )
    forged_entry = replace(
        portfolio.entries[0],
        selected_state_id=fixture[1].state_id,
        selected_state_sha256=state_b_sha256,
    )
    forged = PersonalCapabilityCurrentStatePortfolio(
        subject_ref=portfolio.subject_ref,
        generated_at=portfolio.generated_at,
        current_selection_history_sha256=portfolio.current_selection_history_sha256,
        entries=(forged_entry,),
        current_state_set=PersonalCapabilityStateSet(SUBJECT, (fixture[1],)),
    )
    with pytest.raises(
        InvalidPersonalCapabilityCurrentStatePortfolio,
        match="does not equal fresh complete governed derivation",
    ):
        validate_personal_capability_current_state_portfolio_v1(
            history=history,
            authority_bases=(basis,),
            portfolio=forged,
        )


def test_same_state_id_with_changed_content_cannot_impersonate_current_state() -> None:
    fixture, history = _select_a_fixture()
    basis = _root_basis(fixture, history)
    portfolio = derive_personal_capability_current_state_portfolio_v1(
        history=history,
        authority_bases=(basis,),
        generated_at=T0 + timedelta(minutes=10),
    )
    mutated_state = replace(fixture[0], rationale="Mutated post-authority state content.")
    mutated_set = PersonalCapabilityStateSet(SUBJECT, (mutated_state,))
    mutated_sha256 = personal_capability_state_content_sha256_v1(
        snapshot=mutated_set,
        state_id=mutated_state.state_id,
    )
    forged_entry = replace(
        portfolio.entries[0],
        selected_state_sha256=mutated_sha256,
    )
    forged = PersonalCapabilityCurrentStatePortfolio(
        subject_ref=portfolio.subject_ref,
        generated_at=portfolio.generated_at,
        current_selection_history_sha256=portfolio.current_selection_history_sha256,
        entries=(forged_entry,),
        current_state_set=mutated_set,
    )
    with pytest.raises(
        InvalidPersonalCapabilityCurrentStatePortfolio,
        match="does not equal fresh complete governed derivation",
    ):
        validate_personal_capability_current_state_portfolio_v1(
            history=history,
            authority_bases=(basis,),
            portfolio=forged,
        )


def test_missing_or_duplicate_authority_basis_fails_closed() -> None:
    fixture, history = _select_a_fixture()
    basis = _root_basis(fixture, history)
    with pytest.raises(
        InvalidPersonalCapabilityCurrentStatePortfolio,
        match="subject-wide PR11.8 current-state authority replay rejected",
    ):
        derive_personal_capability_current_state_portfolio_v1(
            history=history,
            authority_bases=(),
            generated_at=T0 + timedelta(minutes=10),
        )
    with pytest.raises(
        InvalidPersonalCapabilityCurrentStatePortfolio,
        match="subject-wide PR11.8 current-state authority replay rejected",
    ):
        derive_personal_capability_current_state_portfolio_v1(
            history=history,
            authority_bases=(basis, basis),
            generated_at=T0 + timedelta(minutes=10),
        )


def test_future_governance_cannot_enter_earlier_portfolio() -> None:
    fixture, history = _select_a_fixture()
    with pytest.raises(
        InvalidPersonalCapabilityCurrentStatePortfolio,
        match="governance act after portfolio generated_at",
    ):
        derive_personal_capability_current_state_portfolio_v1(
            history=history,
            authority_bases=(_root_basis(fixture, history),),
            generated_at=T0 + timedelta(minutes=4),
        )


def test_old_portfolio_is_stale_after_later_clear() -> None:
    fixture, history_a = _select_a_fixture()
    old = derive_personal_capability_current_state_portfolio_v1(
        history=history_a,
        authority_bases=(_root_basis(fixture, history_a),),
        generated_at=T0 + timedelta(minutes=5),
    )
    _, history_clear, bases = _clear_fixture()
    with pytest.raises(
        InvalidPersonalCapabilityCurrentStatePortfolio,
        match="governance act after portfolio generated_at",
    ):
        validate_personal_capability_current_state_portfolio_v1(
            history=history_clear,
            authority_bases=bases,
            portfolio=old,
        )


def test_state_layer_authority_errors_are_wrapped_at_pr11_10_boundary() -> None:
    fixture, history = _select_a_fixture()
    basis = _root_basis(fixture, history)
    malformed = replace(
        basis,
        state_snapshot=PersonalCapabilityStateSet(SUBJECT),
    )
    with pytest.raises(
        InvalidPersonalCapabilityCurrentStatePortfolio,
        match="subject-wide PR11.8 current-state authority replay rejected",
    ):
        derive_personal_capability_current_state_portfolio_v1(
            history=history,
            authority_bases=(malformed,),
            generated_at=T0 + timedelta(minutes=10),
        )


def test_post_construction_corrupted_entry_ref_fails_strict_reconstruction() -> None:
    fixture, history = _select_a_fixture()
    portfolio = derive_personal_capability_current_state_portfolio_v1(
        history=history,
        authority_bases=(_root_basis(fixture, history),),
        generated_at=T0 + timedelta(minutes=10),
    )
    corrupted = CapabilityConceptRef.parse(str(portfolio.entries[0].concept_ref))
    object.__setattr__(corrupted, "revision", 0)
    object.__setattr__(portfolio.entries[0], "concept_ref", corrupted)
    with pytest.raises(
        InvalidPersonalCapabilityCurrentStatePortfolio,
        match="strict semantic round-trip",
    ):
        validate_personal_capability_current_state_portfolio_v1(
            history=history,
            authority_bases=(_root_basis(fixture, history),),
            portfolio=portfolio,
        )


def test_post_construction_non_exact_entries_container_is_rejected() -> None:
    fixture, history = _select_a_fixture()
    portfolio = derive_personal_capability_current_state_portfolio_v1(
        history=history,
        authority_bases=(_root_basis(fixture, history),),
        generated_at=T0 + timedelta(minutes=10),
    )

    class TupleSubclass(tuple):
        pass

    object.__setattr__(portfolio, "entries", TupleSubclass(portfolio.entries))
    with pytest.raises(
        InvalidPersonalCapabilityCurrentStatePortfolio,
        match="entries must be exact tuple",
    ):
        validate_personal_capability_current_state_portfolio_v1(
            history=history,
            authority_bases=(_root_basis(fixture, history),),
            portfolio=portfolio,
        )


def test_public_surface_contains_no_caller_scope_or_state_selection_controls() -> None:
    parameter_names = set(
        inspect.signature(
            derive_personal_capability_current_state_portfolio_v1
        ).parameters
    )
    assert parameter_names == {"history", "authority_bases", "generated_at"}
    artifact_fields = {item.name for item in fields(PersonalCapabilityCurrentStatePortfolio)}
    forbidden = {
        "selected_state_ids",
        "requested_scopes",
        "concept_filter",
        "frame_filter",
        "latest",
        "rank",
        "readiness",
        "permission",
        "mastery",
    }
    assert artifact_fields.isdisjoint(forbidden)


def test_current_state_portfolio_import_surface_is_frozen_upstream_only() -> None:
    root = Path(__file__).parents[2]
    tree = ast.parse(
        (root / "src/capability_lab/state/current_state_portfolio.py").read_text()
    )
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.add(node.module)
    assert modules == {
        "__future__",
        "dataclasses",
        "datetime",
        "hashlib",
        "json",
        "capability_lab.epistemics",
        "capability_lab.semantics",
        "acceptance",
        "core",
        "current_selection",
        "current_selection_authority",
        "snapshot_transition",
    }
