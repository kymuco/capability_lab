import ast
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from capability_lab.derivation import (
    CompletePortfolioStateDerivationError,
    CompletePortfolioStateDerivationRequest,
    DeterministicStateDerivationRequest,
    derive_supported_state_from_complete_portfolio_v1,
    derive_supported_state_v1,
)
from capability_lab.epistemics import (
    ClaimEvaluationPortfolioEntry,
    ClaimEvaluationPortfolioReceipt,
    EpistemicRecordSet,
    EvaluationConclusion,
    build_complete_claim_evaluation_portfolio_v1,
)
from capability_lab.state import (
    DimensionConflictStatus,
    PersonalCapabilityStateId,
)

from test_derivation_adversarial_v1 import (
    CLAIM_A,
    CLAIM_B,
    CONCEPT_A,
    CONCEPT_B,
    EVAL_MAIN,
    EVAL_SECOND,
    SUBJECT_A,
    SUBJECT_B,
    T0,
    binding,
    claim,
    evaluation,
    evidence,
    frame,
    records,
)


def _portfolio(snapshot: EpistemicRecordSet, *, as_of=T0):
    return build_complete_claim_evaluation_portfolio_v1(
        records=snapshot,
        subject_ref=SUBJECT_A,
        concept_ref=CONCEPT_A,
        as_of=as_of,
    )


def _request(*bindings):
    return CompletePortfolioStateDerivationRequest(
        state_id=PersonalCapabilityStateId("state_pr11_5_adversarial"),
        derived_at=T0,
        claim_dimension_bindings=tuple(bindings),
    )


def _two_directional_snapshot() -> EpistemicRecordSet:
    return records(
        evidence_records=(
            evidence("ev_pr11_5_adv_main", SUBJECT_A),
            evidence("ev_pr11_5_adv_second", SUBJECT_A),
        ),
        claims=(claim(CLAIM_A, SUBJECT_A, CONCEPT_A),),
        evaluations=(
            evaluation(
                evaluation_id=EVAL_MAIN,
                claim_id=CLAIM_A,
                evidence_id="ev_pr11_5_adv_main",
                conclusion=EvaluationConclusion.SUPPORTED,
            ),
            evaluation(
                evaluation_id=EVAL_SECOND,
                claim_id=CLAIM_A,
                evidence_id="ev_pr11_5_adv_second",
                conclusion=EvaluationConclusion.CONTRADICTED,
            ),
        ),
    )


def _dimension(state, key: str):
    return next(item for item in state.dimensions if item.dimension_key == key)


def test_raw_pr4_subset_can_hide_conflict_but_governed_pr11_5_path_cannot() -> None:
    snapshot = _two_directional_snapshot()
    exact_frame = frame()

    raw = derive_supported_state_v1(
        records=snapshot,
        frame=exact_frame,
        request=DeterministicStateDerivationRequest(
            state_id=PersonalCapabilityStateId("state_pr11_5_raw_subset"),
            subject_ref=SUBJECT_A,
            concept_ref=CONCEPT_A,
            frame_ref=exact_frame.ref,
            as_of=T0,
            derived_at=T0,
            selected_evaluation_ids=(EVAL_MAIN,),
            claim_dimension_bindings=(binding(CLAIM_A, "execution"),),
        ),
    )
    assert _dimension(raw, "execution").basis_evaluation_ids == (EVAL_MAIN,)
    assert _dimension(raw, "execution").conflict_status is DimensionConflictStatus.NONE

    portfolio = _portfolio(snapshot)
    governed = derive_supported_state_from_complete_portfolio_v1(
        records=snapshot,
        frame=exact_frame,
        portfolio=portfolio,
        request=_request(binding(CLAIM_A, "execution")),
    )
    execution = _dimension(governed, "execution")
    assert execution.basis_evaluation_ids == tuple(sorted((EVAL_MAIN, EVAL_SECOND)))
    assert execution.conflict_status is DimensionConflictStatus.UNRESOLVED


def test_stale_portfolio_is_rejected_after_unrelated_snapshot_append() -> None:
    base = records(
        evidence_records=(evidence("ev_pr11_5_adv_main", SUBJECT_A),),
        claims=(claim(CLAIM_A, SUBJECT_A, CONCEPT_A),),
        evaluations=(
            evaluation(
                evaluation_id=EVAL_MAIN,
                claim_id=CLAIM_A,
                evidence_id="ev_pr11_5_adv_main",
                conclusion=EvaluationConclusion.SUPPORTED,
            ),
        ),
    )
    old = _portfolio(base)
    expanded = EpistemicRecordSet(
        evidence_records=base.evidence_records,
        claims=base.claims + (claim(CLAIM_B, SUBJECT_B, CONCEPT_A),),
        evaluations=base.evaluations,
    )

    with pytest.raises(
        CompletePortfolioStateDerivationError,
        match="portfolio snapshot does not match supplied EpistemicRecordSet",
    ):
        derive_supported_state_from_complete_portfolio_v1(
            records=expanded,
            frame=frame(),
            portfolio=old,
            request=_request(binding(CLAIM_A, "execution")),
        )


def test_dataclasses_replace_cannot_hide_admissible_evaluation_from_handoff() -> None:
    snapshot = _two_directional_snapshot()
    issued = _portfolio(snapshot)
    tampered = replace(
        issued,
        entries=(
            ClaimEvaluationPortfolioEntry(
                claim_id=CLAIM_A,
                evaluation_ids=(EVAL_MAIN,),
            ),
        ),
    )
    assert tampered.validator_issued is True

    with pytest.raises(
        CompletePortfolioStateDerivationError,
        match="portfolio content does not match complete records-derived portfolio",
    ):
        derive_supported_state_from_complete_portfolio_v1(
            records=snapshot,
            frame=frame(),
            portfolio=tampered,
            request=_request(binding(CLAIM_A, "execution")),
        )


def test_public_receipt_subclass_cannot_forge_handoff_authority() -> None:
    snapshot = _two_directional_snapshot()
    issued = _portfolio(snapshot)

    class ForgedReceipt(ClaimEvaluationPortfolioReceipt):
        __slots__ = ()

        @property
        def validator_issued(self) -> bool:
            return True

    forged = ForgedReceipt(
        snapshot_sha256=issued.snapshot_sha256,
        subject_ref=issued.subject_ref,
        concept_ref=issued.concept_ref,
        as_of=issued.as_of,
        entries=issued.entries,
        excluded_future_claim_ids=issued.excluded_future_claim_ids,
        excluded_future_evaluation_ids=issued.excluded_future_evaluation_ids,
    )

    with pytest.raises(
        CompletePortfolioStateDerivationError,
        match="portfolio must be validator-issued",
    ):
        derive_supported_state_from_complete_portfolio_v1(
            records=snapshot,
            frame=frame(),
            portfolio=forged,
            request=_request(binding(CLAIM_A, "execution")),
        )


def test_structural_public_receipt_cannot_authorize_handoff() -> None:
    snapshot = _two_directional_snapshot()
    issued = _portfolio(snapshot)
    structural = ClaimEvaluationPortfolioReceipt(
        snapshot_sha256=issued.snapshot_sha256,
        subject_ref=issued.subject_ref,
        concept_ref=issued.concept_ref,
        as_of=issued.as_of,
        entries=issued.entries,
        excluded_future_claim_ids=issued.excluded_future_claim_ids,
        excluded_future_evaluation_ids=issued.excluded_future_evaluation_ids,
    )
    assert structural.validator_issued is False

    with pytest.raises(
        CompletePortfolioStateDerivationError,
        match="portfolio must be validator-issued",
    ):
        derive_supported_state_from_complete_portfolio_v1(
            records=snapshot,
            frame=frame(),
            portfolio=structural,
            request=_request(binding(CLAIM_A, "execution")),
        )


def test_historical_backfill_forces_portfolio_rebuild_and_basis_expansion() -> None:
    first = evaluation(
        evaluation_id=EVAL_MAIN,
        claim_id=CLAIM_A,
        evidence_id="ev_pr11_5_adv_main",
        conclusion=EvaluationConclusion.SUPPORTED,
    )
    base = records(
        evidence_records=(
            evidence("ev_pr11_5_adv_main", SUBJECT_A),
            evidence("ev_pr11_5_adv_second", SUBJECT_A),
        ),
        claims=(claim(CLAIM_A, SUBJECT_A, CONCEPT_A),),
        evaluations=(first,),
    )
    old = _portfolio(base)
    backfilled = evaluation(
        evaluation_id=EVAL_SECOND,
        claim_id=CLAIM_A,
        evidence_id="ev_pr11_5_adv_second",
        conclusion=EvaluationConclusion.CONTRADICTED,
    )
    successor = EpistemicRecordSet(
        evidence_records=base.evidence_records,
        claims=base.claims,
        evaluations=base.evaluations + (backfilled,),
    )

    with pytest.raises(
        CompletePortfolioStateDerivationError,
        match="portfolio snapshot does not match supplied EpistemicRecordSet",
    ):
        derive_supported_state_from_complete_portfolio_v1(
            records=successor,
            frame=frame(),
            portfolio=old,
            request=_request(binding(CLAIM_A, "execution")),
        )

    rebuilt = _portfolio(successor)
    state = derive_supported_state_from_complete_portfolio_v1(
        records=successor,
        frame=frame(),
        portfolio=rebuilt,
        request=_request(binding(CLAIM_A, "execution")),
    )
    assert _dimension(state, "execution").basis_evaluation_ids == tuple(
        sorted((EVAL_MAIN, EVAL_SECOND))
    )


def test_future_evaluation_remains_excluded_by_exact_portfolio_as_of() -> None:
    current = evaluation(
        evaluation_id=EVAL_MAIN,
        claim_id=CLAIM_A,
        evidence_id="ev_pr11_5_adv_main",
        conclusion=EvaluationConclusion.SUPPORTED,
    )
    future = replace(
        evaluation(
            evaluation_id=EVAL_SECOND,
            claim_id=CLAIM_A,
            evidence_id="ev_pr11_5_adv_second",
            conclusion=EvaluationConclusion.CONTRADICTED,
        ),
        evaluated_at=T0 + timedelta(seconds=1),
    )
    snapshot = records(
        evidence_records=(
            evidence("ev_pr11_5_adv_main", SUBJECT_A),
            evidence("ev_pr11_5_adv_second", SUBJECT_A),
        ),
        claims=(claim(CLAIM_A, SUBJECT_A, CONCEPT_A),),
        evaluations=(current, future),
    )
    portfolio = _portfolio(snapshot)
    assert portfolio.admissible_evaluation_ids == (EVAL_MAIN,)
    assert portfolio.excluded_future_evaluation_ids == (EVAL_SECOND,)

    state = derive_supported_state_from_complete_portfolio_v1(
        records=snapshot,
        frame=frame(),
        portfolio=portfolio,
        request=_request(binding(CLAIM_A, "execution")),
    )
    assert _dimension(state, "execution").basis_evaluation_ids == (EVAL_MAIN,)


def test_unknown_binding_dimension_is_rejected_before_raw_derivation() -> None:
    snapshot = records(
        evidence_records=(evidence("ev_pr11_5_adv_main", SUBJECT_A),),
        claims=(claim(CLAIM_A, SUBJECT_A, CONCEPT_A),),
        evaluations=(
            evaluation(
                evaluation_id=EVAL_MAIN,
                claim_id=CLAIM_A,
                evidence_id="ev_pr11_5_adv_main",
                conclusion=EvaluationConclusion.SUPPORTED,
            ),
        ),
    )
    portfolio = _portfolio(snapshot)

    with pytest.raises(
        CompletePortfolioStateDerivationError,
        match="dimension absent from exact frame: nonexistent_dimension",
    ):
        derive_supported_state_from_complete_portfolio_v1(
            records=snapshot,
            frame=frame(),
            portfolio=portfolio,
            request=_request(binding(CLAIM_A, "nonexistent_dimension")),
        )


def test_pr11_5_production_imports_match_exact_authority_allowlist() -> None:
    import capability_lab.derivation.complete_portfolio_handoff_v1 as handoff_module

    allowed_from_imports = {
        (0, "__future__"): {"annotations"},
        (0, "dataclasses"): {"dataclass"},
        (0, "datetime"): {"datetime"},
        (0, "capability_lab.epistemics"): {
            "ClaimEvaluationPortfolioReceipt",
            "EpistemicRecordSet",
            "InvalidClaimEvaluationPortfolio",
            "validate_exact_claim_evaluation_selection_v1",
        },
        (0, "capability_lab.epistemics.core"): {"EpistemicError", "canonical_time"},
        (0, "capability_lab.state"): {
            "CompetenceFrame",
            "PersonalCapabilityState",
            "PersonalCapabilityStateId",
        },
        (1, "deterministic_v1"): {
            "ClaimDimensionBinding",
            "DeterministicStateDerivationRequest",
            "StateDerivationError",
            "derive_supported_state_v1",
        },
    }

    path = Path(handoff_module.__file__)
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            raise AssertionError(f"ordinary import not allowed in PR11.5 authority module: {node}")
        if isinstance(node, ast.ImportFrom):
            key = (node.level, node.module or "")
            assert key in allowed_from_imports, key
            assert {alias.name for alias in node.names} <= allowed_from_imports[key]


def test_postcondition_rejects_cross_dimension_partition_of_same_claim_basis(
    monkeypatch,
) -> None:
    import capability_lab.derivation.complete_portfolio_handoff_v1 as handoff_module

    snapshot = _two_directional_snapshot()
    portfolio = _portfolio(snapshot)
    exact_frame = frame()
    original_derive = handoff_module.derive_supported_state_v1

    def partitioned_raw_derivation(*, records, frame, request):
        state = original_derive(records=records, frame=frame, request=request)
        partitioned_dimensions = []
        for dimension in state.dimensions:
            if dimension.dimension_key == "execution":
                partitioned_dimensions.append(
                    replace(dimension, basis_evaluation_ids=(EVAL_MAIN,))
                )
            elif dimension.dimension_key == "diagnosis":
                partitioned_dimensions.append(
                    replace(dimension, basis_evaluation_ids=(EVAL_SECOND,))
                )
            else:
                partitioned_dimensions.append(dimension)
        return replace(state, dimensions=tuple(partitioned_dimensions))

    monkeypatch.setattr(
        handoff_module,
        "derive_supported_state_v1",
        partitioned_raw_derivation,
    )

    with pytest.raises(
        CompletePortfolioStateDerivationError,
        match=(
            "derived state dimension does not preserve complete claim evaluation basis: "
            f"{CLAIM_A} -> diagnosis"
        ),
    ):
        derive_supported_state_from_complete_portfolio_v1(
            records=snapshot,
            frame=exact_frame,
            portfolio=portfolio,
            request=_request(binding(CLAIM_A, "execution", "diagnosis")),
        )


@pytest.mark.parametrize(
    ("field_name", "mutated_value", "message"),
    (
        (
            "state_id",
            PersonalCapabilityStateId("state_pr11_5_wrong_output_id"),
            "derived state state_id does not match governed request",
        ),
        (
            "subject_ref",
            SUBJECT_B,
            "derived state subject_ref does not match complete portfolio",
        ),
        (
            "concept_ref",
            CONCEPT_B,
            "derived state concept_ref does not match complete portfolio",
        ),
        (
            "as_of",
            T0 - timedelta(seconds=1),
            "derived state as_of does not match complete portfolio",
        ),
        (
            "derived_at",
            T0 + timedelta(seconds=1),
            "derived state derived_at does not match governed request",
        ),
    ),
)
def test_postcondition_rejects_governed_output_scope_or_identity_drift(
    monkeypatch,
    field_name,
    mutated_value,
    message,
) -> None:
    import capability_lab.derivation.complete_portfolio_handoff_v1 as handoff_module

    snapshot = _two_directional_snapshot()
    portfolio = _portfolio(snapshot)
    exact_frame = frame()
    original_derive = handoff_module.derive_supported_state_v1

    def mutated_raw_derivation(*, records, frame, request):
        state = original_derive(records=records, frame=frame, request=request)
        return replace(state, **{field_name: mutated_value})

    monkeypatch.setattr(
        handoff_module,
        "derive_supported_state_v1",
        mutated_raw_derivation,
    )

    with pytest.raises(CompletePortfolioStateDerivationError, match=message):
        derive_supported_state_from_complete_portfolio_v1(
            records=snapshot,
            frame=exact_frame,
            portfolio=portfolio,
            request=_request(binding(CLAIM_A, "execution")),
        )


def test_postcondition_rejects_governed_output_frame_drift(monkeypatch) -> None:
    import capability_lab.derivation.complete_portfolio_handoff_v1 as handoff_module

    snapshot = _two_directional_snapshot()
    portfolio = _portfolio(snapshot)
    exact_frame = frame()
    wrong_frame_ref = replace(exact_frame, revision=exact_frame.revision + 1).ref
    original_derive = handoff_module.derive_supported_state_v1

    def mutated_raw_derivation(*, records, frame, request):
        state = original_derive(records=records, frame=frame, request=request)
        return replace(state, frame_ref=wrong_frame_ref)

    monkeypatch.setattr(
        handoff_module,
        "derive_supported_state_v1",
        mutated_raw_derivation,
    )

    with pytest.raises(
        CompletePortfolioStateDerivationError,
        match="derived state frame_ref does not match exact supplied frame",
    ):
        derive_supported_state_from_complete_portfolio_v1(
            records=snapshot,
            frame=exact_frame,
            portfolio=portfolio,
            request=_request(binding(CLAIM_A, "execution")),
        )
