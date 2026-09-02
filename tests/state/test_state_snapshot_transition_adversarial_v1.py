from dataclasses import replace
from datetime import datetime, timedelta, timezone
import ast
from pathlib import Path

import pytest

from capability_lab.epistemics import (
    CapabilityClaimId,
    CapabilitySubjectRef,
    ClaimEvaluationId,
)
from capability_lab.semantics import CapabilityConceptRef, CapabilityId
from capability_lab.state import (
    CompetenceDimensionState,
    CompetenceFrameId,
    CompetenceFrameRef,
    DimensionConflictStatus,
    DimensionStanding,
    InvalidPersonalCapabilityStateSetSuccessor,
    PersonalCapabilityState,
    PersonalCapabilityStateId,
    PersonalCapabilityStateSet,
    StateDerivationPolicyRef,
    StateDeriverKind,
    StateDeriverRef,
    personal_capability_state_set_sha256_v1,
    validate_personal_capability_state_set_successor_v1,
)


T0 = datetime(2026, 8, 21, 8, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("adversarial_pr11_6")
CONCEPT = CapabilityConceptRef.parse("core:state_snapshot_adversarial@1")
FRAME = CompetenceFrameRef.parse("core:state_snapshot_adversarial_frame@1")
POLICY = StateDerivationPolicyRef.parse("core:state_snapshot_adversarial_policy@1")
DERIVER = StateDeriverRef(StateDeriverKind.RULE, "pr11_6_adversarial_rule")
CLAIM_A = CapabilityClaimId("claim_pr11_6_a")
CLAIM_B = CapabilityClaimId("claim_pr11_6_b")
EVAL_A = ClaimEvaluationId("evaluation_pr11_6_a")
EVAL_B = ClaimEvaluationId("evaluation_pr11_6_b")


def _dimension() -> CompetenceDimensionState:
    return CompetenceDimensionState(
        "execution",
        DimensionStanding.SUPPORTED,
        supported_claim_ids=(CLAIM_A,),
        basis_evaluation_ids=(EVAL_A,),
        rationale="Immutable adversarial dimension.",
        conflict_status=DimensionConflictStatus.NONE,
    )


def _state(state_id: str = "state_persisted") -> PersonalCapabilityState:
    return PersonalCapabilityState(
        state_id=PersonalCapabilityStateId(state_id),
        subject_ref=SUBJECT,
        concept_ref=CONCEPT,
        frame_ref=FRAME,
        derivation_policy_ref=POLICY,
        deriver_ref=DERIVER,
        as_of=T0,
        derived_at=T0 + timedelta(minutes=1),
        dimensions=(_dimension(),),
        rationale="Immutable persisted state.",
    )


def _set(*states: PersonalCapabilityState) -> PersonalCapabilityStateSet:
    return PersonalCapabilityStateSet(SUBJECT, states)


def _mutated_states(original: PersonalCapabilityState) -> tuple[PersonalCapabilityState, ...]:
    dimension = original.dimensions[0]
    return (
        replace(
            original,
            concept_ref=CapabilityConceptRef.parse("core:state_snapshot_adversarial@2"),
        ),
        replace(
            original,
            frame_ref=CompetenceFrameRef.parse("core:state_snapshot_adversarial_frame@2"),
        ),
        replace(
            original,
            derivation_policy_ref=StateDerivationPolicyRef.parse(
                "core:state_snapshot_adversarial_policy@2"
            ),
        ),
        replace(
            original,
            deriver_ref=StateDeriverRef(StateDeriverKind.MODEL, "different_deriver"),
        ),
        replace(original, as_of=original.as_of - timedelta(seconds=1)),
        replace(original, derived_at=original.derived_at + timedelta(seconds=1)),
        replace(original, rationale="Mutated persisted state rationale."),
        replace(
            original,
            dimensions=(replace(dimension, dimension_key="diagnosis"),),
        ),
        replace(
            original,
            dimensions=(
                replace(
                    dimension,
                    standing=DimensionStanding.INSUFFICIENT,
                    supported_claim_ids=(),
                ),
            ),
        ),
        replace(
            original,
            dimensions=(
                replace(
                    dimension,
                    conflict_status=DimensionConflictStatus.UNRESOLVED,
                ),
            ),
        ),
        replace(
            original,
            dimensions=(
                replace(
                    dimension,
                    supported_claim_ids=(CLAIM_A, CLAIM_B),
                ),
            ),
        ),
        replace(
            original,
            dimensions=(
                replace(
                    dimension,
                    basis_evaluation_ids=(EVAL_A, EVAL_B),
                ),
            ),
        ),
        replace(
            original,
            dimensions=(
                replace(
                    dimension,
                    rationale="Mutated dimension rationale.",
                ),
            ),
        ),
        replace(
            original,
            dimensions=(
                dimension,
                CompetenceDimensionState(
                    "diagnosis",
                    DimensionStanding.UNKNOWN,
                    rationale="New dimension changes canonical state content.",
                ),
            ),
        ),
    )


@pytest.mark.parametrize("case_index", range(14))
def test_same_state_id_is_permanently_bound_to_exact_state_content(case_index: int) -> None:
    original = _state()
    mutated = _mutated_states(original)[case_index]
    with pytest.raises(
        InvalidPersonalCapabilityStateSetSuccessor,
        match="may not mutate retained state",
    ):
        validate_personal_capability_state_set_successor_v1(
            predecessor=_set(original),
            successor=_set(mutated),
        )


def test_recomputation_under_same_state_id_is_rejected_even_if_standing_is_unchanged() -> None:
    original = _state()
    recomputed = replace(
        original,
        derived_at=original.derived_at + timedelta(minutes=30),
        dimensions=(
            replace(
                original.dimensions[0],
                basis_evaluation_ids=(EVAL_A, EVAL_B),
            ),
        ),
        rationale="Recomputed from an expanded basis but illegally reused the old state id.",
    )
    with pytest.raises(
        InvalidPersonalCapabilityStateSetSuccessor,
        match=f"may not mutate retained state: {original.state_id}",
    ):
        validate_personal_capability_state_set_successor_v1(
            predecessor=_set(original),
            successor=_set(recomputed),
        )


def test_recomputation_with_new_id_must_retain_old_state_and_then_passes() -> None:
    original = _state("state_original")
    recomputed = replace(
        original,
        state_id=PersonalCapabilityStateId("state_recomputed"),
        derived_at=original.derived_at + timedelta(minutes=30),
        dimensions=(
            replace(
                original.dimensions[0],
                basis_evaluation_ids=(EVAL_A, EVAL_B),
            ),
        ),
        rationale="Recomputed state appended under a fresh immutable identity.",
    )
    receipt = validate_personal_capability_state_set_successor_v1(
        predecessor=_set(original),
        successor=_set(original, recomputed),
    )
    assert receipt.retained_state_ids == (original.state_id,)
    assert receipt.added_state_ids == (recomputed.state_id,)


def test_replacing_old_state_with_fresh_id_is_still_deletion_and_rejected() -> None:
    old = _state("state_old")
    replacement = replace(
        old,
        state_id=PersonalCapabilityStateId("state_replacement"),
        derived_at=old.derived_at + timedelta(minutes=1),
    )
    with pytest.raises(
        InvalidPersonalCapabilityStateSetSuccessor,
        match=f"may not remove persisted state: {old.state_id}",
    ):
        validate_personal_capability_state_set_successor_v1(
            predecessor=_set(old),
            successor=_set(replacement),
        )


def test_deletion_is_rejected_even_when_multiple_unrelated_states_are_appended() -> None:
    old_a = _state("state_old_a")
    old_b = _state("state_old_b")
    new_c = _state("state_new_c")
    with pytest.raises(
        InvalidPersonalCapabilityStateSetSuccessor,
        match=f"may not remove persisted state: {old_a.state_id}",
    ):
        validate_personal_capability_state_set_successor_v1(
            predecessor=_set(old_a, old_b),
            successor=_set(old_b, new_c),
        )


def test_state_id_rename_is_not_mutation_but_remove_plus_append_and_is_rejected() -> None:
    original = _state("state_identity_a")
    renamed = replace(
        original,
        state_id=PersonalCapabilityStateId("state_identity_b"),
    )
    with pytest.raises(
        InvalidPersonalCapabilityStateSetSuccessor,
        match="may not remove persisted state",
    ):
        validate_personal_capability_state_set_successor_v1(
            predecessor=_set(original),
            successor=_set(renamed),
        )


def test_structurally_valid_unproven_state_can_be_persisted_without_authority() -> None:
    state = _state("state_structural_only")
    receipt = validate_personal_capability_state_set_successor_v1(
        predecessor=PersonalCapabilityStateSet(SUBJECT),
        successor=_set(state),
    )
    assert receipt.added_state_ids == (state.state_id,)
    assert not hasattr(receipt, "accepted_state_id")
    assert not hasattr(receipt, "derivation_receipt")
    assert not hasattr(receipt, "progression_authorized")


def test_append_order_does_not_impose_as_of_or_derived_at_order() -> None:
    later_state = _state("state_later")
    historical = replace(
        later_state,
        state_id=PersonalCapabilityStateId("state_historical_backfill"),
        as_of=datetime(2018, 1, 1, tzinfo=timezone.utc),
        derived_at=T0 + timedelta(days=10),
    )
    receipt = validate_personal_capability_state_set_successor_v1(
        predecessor=_set(later_state),
        successor=_set(later_state, historical),
    )
    assert receipt.added_state_ids == (historical.state_id,)


def test_state_set_subclass_cannot_override_snapshot_transition_surface() -> None:
    class StateSetSubclass(PersonalCapabilityStateSet):
        pass

    malicious = StateSetSubclass(SUBJECT, (_state(),))
    with pytest.raises(
        InvalidPersonalCapabilityStateSetSuccessor,
        match="successor must be PersonalCapabilityStateSet",
    ):
        validate_personal_capability_state_set_successor_v1(
            predecessor=PersonalCapabilityStateSet(SUBJECT),
            successor=malicious,
        )


def test_state_record_subclass_cannot_enter_persisted_snapshot() -> None:
    class StateSubclass(PersonalCapabilityState):
        pass

    original = _state()
    malicious_state = StateSubclass(
        state_id=original.state_id,
        subject_ref=original.subject_ref,
        concept_ref=original.concept_ref,
        frame_ref=original.frame_ref,
        derivation_policy_ref=original.derivation_policy_ref,
        deriver_ref=original.deriver_ref,
        as_of=original.as_of,
        derived_at=original.derived_at,
        dimensions=original.dimensions,
        rationale=original.rationale,
    )
    successor = PersonalCapabilityStateSet(SUBJECT, (malicious_state,))
    with pytest.raises(
        InvalidPersonalCapabilityStateSetSuccessor,
        match="successor states must contain exact PersonalCapabilityState values",
    ):
        validate_personal_capability_state_set_successor_v1(
            predecessor=PersonalCapabilityStateSet(SUBJECT),
            successor=successor,
        )


class _AlwaysEqualDimension(CompetenceDimensionState):
    def __eq__(self, other: object) -> bool:
        return True


class _StateIdSubclass(PersonalCapabilityStateId):
    pass


class _AlwaysEqualSubjectRef(CapabilitySubjectRef):
    def __eq__(self, other: object) -> bool:
        return True

    __hash__ = CapabilitySubjectRef.__hash__


class _ConceptRefSubclass(CapabilityConceptRef):
    pass


class _CapabilityIdSubclass(CapabilityId):
    pass


class _FrameRefSubclass(CompetenceFrameRef):
    pass


class _FrameIdSubclass(CompetenceFrameId):
    pass


class _PolicyRefSubclass(StateDerivationPolicyRef):
    pass


class _DeriverRefSubclass(StateDeriverRef):
    pass


class _ClaimIdSubclass(CapabilityClaimId):
    pass


class _EvaluationIdSubclass(ClaimEvaluationId):
    pass


class _DateTimeSubclass(datetime):
    pass


class _StringSubclass(str):
    pass


class _IntSubclass(int):
    pass


def _nested_subclass_states(
    original: PersonalCapabilityState,
) -> tuple[PersonalCapabilityState, ...]:
    dimension = original.dimensions[0]
    capability_id = original.concept_ref.capability_id
    frame_id = original.frame_ref.frame_id
    malicious_dimension = _AlwaysEqualDimension(
        dimension_key=dimension.dimension_key,
        standing=dimension.standing,
        supported_claim_ids=dimension.supported_claim_ids,
        basis_evaluation_ids=dimension.basis_evaluation_ids,
        rationale="Materially changed nested dimension hidden by malicious equality.",
        conflict_status=dimension.conflict_status,
    )
    return (
        replace(
            original,
            state_id=_StateIdSubclass(original.state_id.value),
        ),
        replace(
            original,
            subject_ref=_AlwaysEqualSubjectRef(original.subject_ref.value),
        ),
        replace(
            original,
            concept_ref=_ConceptRefSubclass(
                original.concept_ref.capability_id,
                original.concept_ref.revision,
            ),
        ),
        replace(
            original,
            concept_ref=CapabilityConceptRef(
                _CapabilityIdSubclass(capability_id.namespace, capability_id.key),
                original.concept_ref.revision,
            ),
        ),
        replace(
            original,
            frame_ref=_FrameRefSubclass(
                original.frame_ref.frame_id,
                original.frame_ref.revision,
            ),
        ),
        replace(
            original,
            frame_ref=CompetenceFrameRef(
                _FrameIdSubclass(frame_id.namespace, frame_id.key),
                original.frame_ref.revision,
            ),
        ),
        replace(
            original,
            derivation_policy_ref=_PolicyRefSubclass(
                original.derivation_policy_ref.namespace,
                original.derivation_policy_ref.key,
                original.derivation_policy_ref.revision,
            ),
        ),
        replace(
            original,
            deriver_ref=_DeriverRefSubclass(
                original.deriver_ref.kind,
                original.deriver_ref.ref,
            ),
        ),
        replace(
            original,
            as_of=_DateTimeSubclass(
                original.as_of.year,
                original.as_of.month,
                original.as_of.day,
                original.as_of.hour,
                original.as_of.minute,
                original.as_of.second,
                original.as_of.microsecond,
                tzinfo=original.as_of.tzinfo,
            ),
        ),
        replace(
            original,
            dimensions=(malicious_dimension,),
        ),
        replace(
            original,
            dimensions=(
                replace(
                    dimension,
                    supported_claim_ids=(_ClaimIdSubclass(CLAIM_A.value),),
                ),
            ),
        ),
        replace(
            original,
            dimensions=(
                replace(
                    dimension,
                    basis_evaluation_ids=(_EvaluationIdSubclass(EVAL_A.value),),
                ),
            ),
        ),
        replace(
            original,
            derivation_policy_ref=StateDerivationPolicyRef(
                _StringSubclass(original.derivation_policy_ref.namespace),
                original.derivation_policy_ref.key,
                original.derivation_policy_ref.revision,
            ),
        ),
        replace(
            original,
            derivation_policy_ref=StateDerivationPolicyRef(
                original.derivation_policy_ref.namespace,
                original.derivation_policy_ref.key,
                _IntSubclass(original.derivation_policy_ref.revision),
            ),
        ),
    )


@pytest.mark.parametrize("case_index", range(14))
def test_nested_behavioral_subclasses_cannot_enter_persisted_state_graph(
    case_index: int,
) -> None:
    original = _state()
    malicious = _nested_subclass_states(original)[case_index]
    successor = PersonalCapabilityStateSet(SUBJECT, (malicious,))
    with pytest.raises(
        InvalidPersonalCapabilityStateSetSuccessor,
        match="exact",
    ):
        validate_personal_capability_state_set_successor_v1(
            predecessor=_set(original),
            successor=successor,
        )


def test_malicious_nested_dimension_equality_cannot_hide_material_mutation() -> None:
    original = _state()
    malicious = _nested_subclass_states(original)[9]

    assert original == malicious

    with pytest.raises(
        InvalidPersonalCapabilityStateSetSuccessor,
        match=r"successor\.states\[0\]\.dimensions\[0\].*exact core value type",
    ):
        validate_personal_capability_state_set_successor_v1(
            predecessor=_set(original),
            successor=PersonalCapabilityStateSet(SUBJECT, (malicious,)),
        )


def test_snapshot_hash_rejects_nested_behavioral_subclass_graph() -> None:
    malicious = _nested_subclass_states(_state())[9]
    with pytest.raises(
        InvalidPersonalCapabilityStateSetSuccessor,
        match="exact",
    ):
        personal_capability_state_set_sha256_v1(
            PersonalCapabilityStateSet(SUBJECT, (malicious,))
        )


class _AlwaysEqualFakeCapabilityId:
    namespace = "core"
    key = "forged_capability"

    def __eq__(self, other: object) -> bool:
        return True

    def __str__(self) -> str:
        return "core:forged_capability"


class _AlwaysEqualFakeConceptRef:
    capability_id = _AlwaysEqualFakeCapabilityId()
    revision = 1

    def __eq__(self, other: object) -> bool:
        return True

    def __str__(self) -> str:
        return "core:forged_capability@1"


class _AlwaysEqualFakeDimension:
    dimension_key = "execution"
    standing = DimensionStanding.SUPPORTED
    supported_claim_ids = (CLAIM_A,)
    basis_evaluation_ids = (EVAL_A,)
    rationale = "Forged dimension serialized content."
    conflict_status = DimensionConflictStatus.NONE

    def __eq__(self, other: object) -> bool:
        return True


class _SpoofedEnumText(str):
    def __new__(cls, comparable_value: str, serialized_value: str):
        instance = str.__new__(cls, comparable_value)
        instance._serialized_value = serialized_value
        return instance

    @property
    def value(self) -> str:
        return self._serialized_value


def test_unrelated_fake_concept_ref_cannot_pass_direct_object_exactness_probe() -> None:
    original = _state()
    tampered = replace(original)
    object.__setattr__(tampered, "concept_ref", _AlwaysEqualFakeConceptRef())

    assert original == tampered

    with pytest.raises(
        InvalidPersonalCapabilityStateSetSuccessor,
        match="exact core value type: CapabilityConceptRef",
    ):
        validate_personal_capability_state_set_successor_v1(
            predecessor=_set(original),
            successor=PersonalCapabilityStateSet(SUBJECT, (tampered,)),
        )


def test_exact_concept_ref_with_unrelated_fake_capability_id_is_rejected() -> None:
    original = _state()
    tampered_ref = replace(original.concept_ref)
    object.__setattr__(
        tampered_ref,
        "capability_id",
        _AlwaysEqualFakeCapabilityId(),
    )
    tampered = replace(original)
    object.__setattr__(tampered, "concept_ref", tampered_ref)

    with pytest.raises(
        InvalidPersonalCapabilityStateSetSuccessor,
        match="exact core value type: CapabilityId",
    ):
        validate_personal_capability_state_set_successor_v1(
            predecessor=_set(original),
            successor=PersonalCapabilityStateSet(SUBJECT, (tampered,)),
        )


def test_unrelated_fake_dimension_is_rejected_before_equality_or_serialization() -> None:
    original = _state()
    tampered = replace(original)
    object.__setattr__(tampered, "dimensions", (_AlwaysEqualFakeDimension(),))

    assert original == tampered

    with pytest.raises(
        InvalidPersonalCapabilityStateSetSuccessor,
        match="exact core value type: CompetenceDimensionState",
    ):
        validate_personal_capability_state_set_successor_v1(
            predecessor=_set(original),
            successor=PersonalCapabilityStateSet(SUBJECT, (tampered,)),
        )


@pytest.mark.parametrize(
    ("target", "comparable", "serialized", "expected_type_name"),
    (
        ("standing", "supported", "insufficient", "DimensionStanding"),
        ("conflict_status", "none", "unresolved", "DimensionConflictStatus"),
        ("deriver_kind", "rule", "model", "StateDeriverKind"),
    ),
)
def test_post_construction_enum_spoof_is_rejected_before_retained_state_equality(
    target: str,
    comparable: str,
    serialized: str,
    expected_type_name: str,
) -> None:
    original = _state()
    tampered = replace(original)
    spoof = _SpoofedEnumText(comparable, serialized)

    if target == "deriver_kind":
        deriver_ref = replace(original.deriver_ref)
        object.__setattr__(deriver_ref, "kind", spoof)
        object.__setattr__(tampered, "deriver_ref", deriver_ref)
    else:
        dimension = replace(original.dimensions[0])
        object.__setattr__(dimension, target, spoof)
        object.__setattr__(tampered, "dimensions", (dimension,))

    assert original == tampered

    with pytest.raises(
        InvalidPersonalCapabilityStateSetSuccessor,
        match=f"exact core value type: {expected_type_name}",
    ):
        validate_personal_capability_state_set_successor_v1(
            predecessor=_set(original),
            successor=PersonalCapabilityStateSet(SUBJECT, (tampered,)),
        )


def test_snapshot_hash_rejects_post_construction_fake_concept_before_serialization() -> None:
    tampered = replace(_state())
    object.__setattr__(tampered, "concept_ref", _AlwaysEqualFakeConceptRef())

    with pytest.raises(
        InvalidPersonalCapabilityStateSetSuccessor,
        match="exact core value type: CapabilityConceptRef",
    ):
        personal_capability_state_set_sha256_v1(
            PersonalCapabilityStateSet(SUBJECT, (tampered,))
        )


def test_state_snapshot_transition_has_exact_narrow_import_authority_surface() -> None:
    import capability_lab.state.snapshot_transition as transition_module

    path = Path(transition_module.__file__)
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add((0, alias.name, alias.asname, ()))
        elif isinstance(node, ast.ImportFrom):
            imports.add(
                (
                    node.level,
                    node.module or "",
                    None,
                    tuple(alias.name for alias in node.names),
                )
            )

    assert imports == {
        (0, "__future__", None, ("annotations",)),
        (0, "dataclasses", None, ("dataclass",)),
        (0, "datetime", None, ("datetime",)),
        (0, "hashlib", None, ()),
        (
            0,
            "capability_lab.epistemics",
            None,
            (
                "CapabilityClaimId",
                "CapabilitySubjectRef",
                "ClaimEvaluationId",
            ),
        ),
        (
            0,
            "capability_lab.semantics",
            None,
            ("CapabilityConceptRef", "CapabilityId"),
        ),
        (
            1,
            "core",
            None,
            (
                "CompetenceDimensionState",
                "CompetenceFrameId",
                "CompetenceFrameRef",
                "DimensionConflictStatus",
                "DimensionStanding",
                "PersonalCapabilityState",
                "PersonalCapabilityStateId",
                "PersonalCapabilityStateSet",
                "StateDerivationPolicyRef",
                "StateDeriverKind",
                "StateDeriverRef",
                "StateError",
            ),
        ),
    }
