import ast
from dataclasses import fields, replace
from pathlib import Path

import pytest

from capability_lab.progression import (
    CurrentStateGovernedProgressionFrontier,
    CurrentStatePrerequisiteCheck,
    CurrentStateProgressionAuthorityBinding,
    CurrentStateProgressionAuthorityStatus,
    CurrentStateProgressionFrontierRequest,
    CurrentStateProgressionSeed,
    PrerequisiteDimensionGapKind,
    ProgressionAuthorityHandoffError,
    ProgressionFocus,
    ProgressionFrontierId,
    current_state_governed_progression_frontier_sha256_v1,
    validate_current_state_governed_progression_frontier_v1,
)
from capability_lab.semantics import CapabilityConceptRef
from capability_lab.state import (
    CompetenceFrame,
    CompetenceFrameCatalog,
    CompetenceFrameId,
    CompetenceFrameRef,
    PersonalCapabilityCurrentStateSelectionHistory,
    PersonalCapabilityStateSet,
)

from test_current_state_progression_handoff_v1 import (
    REQUESTER,
    _clear,
    _current_basic_case,
    _derive,
    _requires_relation,
    _seed_request,
)


def _absent_prerequisite_case(case):
    target, relation = _requires_relation(case)
    source_frame = case["frames"].frames[0]
    absent_frame = CompetenceFrame(
        CompetenceFrameId("test", "pr11_9_absent_scope"),
        1,
        "PR11.9 Absent Scope",
        "Valid competence frame with no current-state selection for the prerequisite.",
        source_frame.dimensions,
    )
    frames = CompetenceFrameCatalog(case["frames"].frames + (absent_frame,))
    request = CurrentStateProgressionFrontierRequest(
        frontier_id=ProgressionFrontierId("frontier_pr11_9_absent_prerequisite"),
        as_of=case["state"].as_of,
        generated_at=case["selected_at"],
        requester_ref=REQUESTER,
        focuses=(
            ProgressionFocus(
                target.ref,
                "Explicit focus exposes the real REQUIRES relation for absent-scope replay.",
            ),
        ),
        prerequisite_checks=(
            CurrentStatePrerequisiteCheck(
                target_ref=target.ref,
                prerequisite_ref=case["state"].concept_ref,
                relation_scope=relation.scope,
                frame_ref=absent_frame.ref,
                required_dimension_keys=("conceptual_knowledge",),
            ),
        ),
    )
    scoped_case = dict(case)
    scoped_case["frames"] = frames
    return scoped_case, request


def test_raw_pr8_frontier_cannot_impersonate_pr11_9_governed_artifact() -> None:
    case = _current_basic_case()
    governed = _derive(case, _seed_request(case))
    with pytest.raises(
        ProgressionAuthorityHandoffError,
        match="governed_frontier must use exact type",
    ):
        validate_current_state_governed_progression_frontier_v1(
            capability_catalog=case["catalog"],
            frame_catalog=case["frames"],
            records=case["records"],
            selection_history=case["history"],
            authority_bases=case["bases"],
            governed_frontier=governed.frontier,
        )


def test_old_governed_frontier_is_stale_after_later_clear() -> None:
    case = _current_basic_case()
    governed = _derive(case, _seed_request(case))
    cleared, bases, _ = _clear(case)
    with pytest.raises(
        ProgressionAuthorityHandoffError,
        match="governance act after progression generated_at",
    ):
        validate_current_state_governed_progression_frontier_v1(
            capability_catalog=case["catalog"],
            frame_catalog=case["frames"],
            records=case["records"],
            selection_history=cleared,
            authority_bases=bases,
            governed_frontier=governed,
        )


def test_tampered_history_digest_cannot_pass_fresh_revalidation() -> None:
    case = _current_basic_case()
    governed = _derive(case, _seed_request(case))
    tampered = replace(governed, current_selection_history_sha256="0" * 64)
    assert tampered.frontier == governed.frontier
    assert (
        current_state_governed_progression_frontier_sha256_v1(tampered)
        != current_state_governed_progression_frontier_sha256_v1(governed)
    )
    with pytest.raises(
        ProgressionAuthorityHandoffError,
        match="does not exactly match fresh PR11.8 authority replay",
    ):
        validate_current_state_governed_progression_frontier_v1(
            capability_catalog=case["catalog"],
            frame_catalog=case["frames"],
            records=case["records"],
            selection_history=case["history"],
            authority_bases=case["bases"],
            governed_frontier=tampered,
        )


def test_tampered_authority_binding_cannot_match_raw_frontier_state_input() -> None:
    case = _current_basic_case()
    governed = _derive(case, _seed_request(case))
    original = governed.authority_bindings[0]
    forged = CurrentStateProgressionAuthorityBinding(
        concept_ref=original.concept_ref,
        frame_ref=original.frame_ref,
        status=original.status,
        current_selection_sha256=original.current_selection_sha256,
        selected_state_id=type(case["state"].state_id)("forged_pr11_9_state"),
        selected_state_sha256=original.selected_state_sha256,
    )
    with pytest.raises(
        ProgressionAuthorityHandoffError,
        match="raw frontier seed bindings do not match authority-derived current states",
    ):
        CurrentStateGovernedProgressionFrontier(
            request=governed.request,
            current_selection_history_sha256=governed.current_selection_history_sha256,
            authority_bindings=(forged,),
            frontier=governed.frontier,
        )


def test_missing_current_selection_authority_basis_is_rejected() -> None:
    case = _current_basic_case()
    with pytest.raises(
        ProgressionAuthorityHandoffError,
        match="authority_bases must cover exactly the subject selection history",
    ):
        _derive(case, _seed_request(case), bases=())


def test_malformed_authority_bases_container_fails_closed() -> None:
    case = _current_basic_case()

    class TupleSubclass(tuple):
        pass

    for malformed in (None, [], TupleSubclass(case["bases"])):
        with pytest.raises(ProgressionAuthorityHandoffError):
            _derive(case, _seed_request(case), bases=malformed)


def test_state_layer_authority_replay_errors_are_wrapped_at_pr11_9_boundary() -> None:
    case = _current_basic_case()
    malformed_basis = replace(
        case["bases"][0],
        state_snapshot=PersonalCapabilityStateSet(case["state"].subject_ref),
    )

    with pytest.raises(
        ProgressionAuthorityHandoffError,
        match="subject-wide current-state authority preflight rejected progression history",
    ):
        _derive(case, _seed_request(case), bases=(malformed_basis,))


def test_all_requested_seed_scopes_absent_replays_subject_authority_then_rejects_seed() -> None:
    case = _current_basic_case()
    target, _ = _requires_relation(case)
    request = CurrentStateProgressionFrontierRequest(
        frontier_id=ProgressionFrontierId("frontier_pr11_9_absent_scope"),
        as_of=case["state"].as_of,
        generated_at=case["selected_at"],
        requester_ref=REQUESTER,
        seeds=(
            CurrentStateProgressionSeed(
                concept_ref=target.ref,
                frame_ref=case["state"].frame_ref,
                dimension_keys=("conceptual_knowledge",),
            ),
        ),
    )
    with pytest.raises(
        ProgressionAuthorityHandoffError,
        match="scope resolved as absent",
    ):
        _derive(case, request)


def test_all_absent_prerequisite_uses_full_subject_authority_and_emits_no_selected_state() -> None:
    case = _current_basic_case()
    scoped_case, request = _absent_prerequisite_case(case)
    governed = _derive(scoped_case, request)

    assert len(governed.authority_bindings) == 1
    assert governed.authority_bindings[0].status is CurrentStateProgressionAuthorityStatus.ABSENT
    assert governed.frontier.prerequisite_bindings[0].state_id is None
    assert (
        governed.frontier.prerequisite_gaps[0].dimension_gaps[0].kind
        is PrerequisiteDimensionGapKind.NO_SELECTED_STATE
    )
    validate_current_state_governed_progression_frontier_v1(
        capability_catalog=scoped_case["catalog"],
        frame_catalog=scoped_case["frames"],
        records=scoped_case["records"],
        selection_history=scoped_case["history"],
        authority_bases=scoped_case["bases"],
        governed_frontier=governed,
    )


def test_all_absent_prerequisite_rejects_unrelated_forged_history_without_full_bases() -> None:
    case = _current_basic_case()
    scoped_case, request = _absent_prerequisite_case(case)
    forged_selection = replace(
        case["history"].selections[0],
        rationale="Structurally valid unrelated selection with no supplied authority basis.",
    )
    forged_history = PersonalCapabilityCurrentStateSelectionHistory(
        case["state"].subject_ref,
        (forged_selection,),
    )

    with pytest.raises(
        ProgressionAuthorityHandoffError,
        match="authority_bases must cover exactly the subject selection history",
    ):
        _derive(
            scoped_case,
            request,
            history=forged_history,
            bases=(),
        )


def test_governed_request_cannot_be_state_free_focus_only_wrapper() -> None:
    case = _current_basic_case()
    target, _ = _requires_relation(case)
    with pytest.raises(
        ProgressionAuthorityHandoffError,
        match="requires at least one personal-state scope",
    ):
        CurrentStateProgressionFrontierRequest(
            frontier_id=ProgressionFrontierId("frontier_pr11_9_focus_only"),
            as_of=case["state"].as_of,
            generated_at=case["selected_at"],
            requester_ref=REQUESTER,
            focuses=(ProgressionFocus(target.ref, "Raw PR8 focus remains raw."),),
        )


def test_post_construction_corrupted_concept_ref_is_rejected_before_authority_lookup() -> None:
    case = _current_basic_case()
    valid = CapabilityConceptRef.parse(str(case["state"].concept_ref))
    seed = CurrentStateProgressionSeed(
        concept_ref=valid,
        frame_ref=case["state"].frame_ref,
        dimension_keys=("conceptual_knowledge",),
    )
    object.__setattr__(valid, "revision", 0)
    with pytest.raises(
        ProgressionAuthorityHandoffError,
        match="strict semantic round-trip",
    ):
        CurrentStateProgressionFrontierRequest(
            frontier_id=ProgressionFrontierId("frontier_pr11_9_corrupt_concept"),
            as_of=case["state"].as_of,
            generated_at=case["selected_at"],
            requester_ref=REQUESTER,
            seeds=(seed,),
        )


def test_post_construction_corrupted_frame_ref_is_rejected_before_authority_lookup() -> None:
    case = _current_basic_case()
    valid = CompetenceFrameRef.parse(str(case["state"].frame_ref))
    seed = CurrentStateProgressionSeed(
        concept_ref=case["state"].concept_ref,
        frame_ref=valid,
        dimension_keys=("conceptual_knowledge",),
    )
    object.__setattr__(valid, "revision", 0)
    with pytest.raises(
        ProgressionAuthorityHandoffError,
        match="strict semantic round-trip",
    ):
        CurrentStateProgressionFrontierRequest(
            frontier_id=ProgressionFrontierId("frontier_pr11_9_corrupt_frame"),
            as_of=case["state"].as_of,
            generated_at=case["selected_at"],
            requester_ref=REQUESTER,
            seeds=(seed,),
        )


def test_post_construction_noncanonical_seed_dimensions_are_rejected() -> None:
    case = _current_basic_case()
    seed = CurrentStateProgressionSeed(
        concept_ref=case["state"].concept_ref,
        frame_ref=case["state"].frame_ref,
        dimension_keys=("calculation", "conceptual_knowledge"),
    )
    object.__setattr__(
        seed,
        "dimension_keys",
        ("conceptual_knowledge", "calculation"),
    )

    with pytest.raises(
        ProgressionAuthorityHandoffError,
        match="seed must equal strict semantic reconstruction",
    ):
        CurrentStateProgressionFrontierRequest(
            frontier_id=ProgressionFrontierId("frontier_pr11_9_corrupt_seed_dimensions"),
            as_of=case["state"].as_of,
            generated_at=case["selected_at"],
            requester_ref=REQUESTER,
            seeds=(seed,),
        )


def test_post_construction_noncanonical_prerequisite_dimensions_are_rejected() -> None:
    case = _current_basic_case()
    target, relation = _requires_relation(case)
    check = CurrentStatePrerequisiteCheck(
        target_ref=target.ref,
        prerequisite_ref=case["state"].concept_ref,
        relation_scope=relation.scope,
        frame_ref=case["state"].frame_ref,
        required_dimension_keys=("calculation", "conceptual_knowledge"),
    )
    object.__setattr__(
        check,
        "required_dimension_keys",
        ("conceptual_knowledge", "calculation"),
    )

    with pytest.raises(
        ProgressionAuthorityHandoffError,
        match="prerequisite check must equal strict semantic reconstruction",
    ):
        CurrentStateProgressionFrontierRequest(
            frontier_id=ProgressionFrontierId(
                "frontier_pr11_9_corrupt_prerequisite_dimensions"
            ),
            as_of=case["state"].as_of,
            generated_at=case["selected_at"],
            requester_ref=REQUESTER,
            focuses=(
                ProgressionFocus(
                    target.ref,
                    "Explicit focus for strict prerequisite reconstruction regression.",
                ),
            ),
            prerequisite_checks=(check,),
        )


def test_governed_artifact_exposes_no_recommendation_readiness_or_permission_fields() -> None:
    forbidden = {
        "ready",
        "readiness",
        "permitted",
        "permission",
        "recommendation",
        "recommended",
        "rank",
        "score",
        "priority",
        "mastery",
    }
    assert forbidden.isdisjoint(
        {item.name for item in fields(CurrentStateGovernedProgressionFrontier)}
    )
    assert forbidden.isdisjoint(
        {item.name for item in fields(CurrentStateProgressionFrontierRequest)}
    )


def test_pr11_9_production_import_surface_is_exactly_frozen() -> None:
    import capability_lab.progression.current_state_handoff as handoff_module

    allowed_imports = {"hashlib", "json", "re"}
    allowed_from_imports = {
        (0, "__future__"): {"annotations"},
        (0, "dataclasses"): {"dataclass"},
        (0, "datetime"): {"datetime", "timezone"},
        (0, "enum"): {"Enum"},
        (0, "capability_lab.epistemics"): {"EpistemicRecordSet"},
        (0, "capability_lab.semantics"): {
            "CapabilityCatalog",
            "CapabilityConceptRef",
            "RelationScope",
        },
        (0, "capability_lab.state"): {
            "CompetenceFrameCatalog",
            "CompetenceFrameRef",
            "CurrentStateSelectionAction",
            "PersonalCapabilityCurrentStateSelection",
            "PersonalCapabilityCurrentStateSelectionAuthorityBasis",
            "PersonalCapabilityCurrentStateSelectionHistory",
            "PersonalCapabilityState",
            "PersonalCapabilityStateId",
            "PersonalCapabilityStateSet",
            "StateError",
            "personal_capability_current_state_selection_history_sha256_v1",
            "personal_capability_current_state_selection_sha256_v1",
            "personal_capability_state_content_sha256_v1",
            "validate_personal_capability_current_state_selection_v1",
        },
        (1, "core"): {
            "ExplorationInput",
            "FrontierSeedBinding",
            "PrerequisiteCheckBinding",
            "ProgressionError",
            "ProgressionFocus",
            "ProgressionFrontier",
            "ProgressionFrontierId",
            "ProgressionFrontierRequest",
            "ProgressionRequesterRef",
        },
        (1, "derivation"): {"derive_progression_frontier_v1"},
        (1, "verification"): {"validate_progression_frontier_v1"},
    }

    path = Path(handoff_module.__file__)
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    seen_imports = set()
    seen_from = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                seen_imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            key = (node.level, node.module or "")
            seen_from.setdefault(key, set()).update(alias.name for alias in node.names)

    assert seen_imports == allowed_imports
    assert seen_from == allowed_from_imports
