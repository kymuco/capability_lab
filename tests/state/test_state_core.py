from datetime import datetime, timedelta, timezone

import pytest

from capability_lab.epistemics import CapabilityClaimId, CapabilitySubjectRef, ClaimEvaluationId
from capability_lab.semantics import CapabilityConceptRef
from capability_lab.state import (
    CompetenceDimensionDefinition,
    CompetenceDimensionState,
    CompetenceFrame,
    CompetenceFrameCatalog,
    CompetenceFrameId,
    CompetenceFrameRef,
    DimensionStanding,
    InvalidCompetenceFrame,
    InvalidPersonalCapabilityState,
    InvalidStateSet,
    PersonalCapabilityState,
    PersonalCapabilityStateId,
    PersonalCapabilityStateSet,
    StateDerivationPolicyRef,
    StateDeriverKind,
    StateDeriverRef,
)


T0 = datetime(2026, 8, 15, 6, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("subject_01")
CONCEPT = CapabilityConceptRef.parse("civilization_bootstrap:electric_motor_construction@1")
FRAME_REF = CompetenceFrameRef.parse("civilization_bootstrap:technical_competence@1")
POLICY = StateDerivationPolicyRef.parse("core:manual_supported_state@1")
DERIVER = StateDeriverRef(StateDeriverKind.HUMAN, "operator")


def frame() -> CompetenceFrame:
    return CompetenceFrame(
        frame_id=CompetenceFrameId.parse("civilization_bootstrap:technical_competence"),
        revision=1,
        name="Technical competence",
        description="A bounded technical-generalist decomposition used as a domain fixture.",
        dimensions=(
            CompetenceDimensionDefinition("execution", "Execution", "Construction and execution in the stated scope."),
            CompetenceDimensionDefinition("diagnosis", "Diagnosis", "Diagnosis of faults and unexpected outcomes."),
        ),
    )


def supported_dimension() -> CompetenceDimensionState:
    return CompetenceDimensionState(
        dimension_key="execution",
        standing=DimensionStanding.SUPPORTED,
        supported_claim_ids=(CapabilityClaimId("claim_execution"),),
        basis_evaluation_ids=(ClaimEvaluationId("eval_execution"),),
        rationale="A scoped execution claim is supported by a governed evaluation.",
    )


def unknown_dimension() -> CompetenceDimensionState:
    return CompetenceDimensionState(
        dimension_key="diagnosis",
        standing=DimensionStanding.UNKNOWN,
        rationale="No governed diagnosis evaluation is represented at this boundary.",
    )


def state(*, subject=SUBJECT, concept=CONCEPT, as_of=T0) -> PersonalCapabilityState:
    return PersonalCapabilityState(
        state_id=PersonalCapabilityStateId("state_motor_01"),
        subject_ref=subject,
        concept_ref=concept,
        frame_ref=FRAME_REF,
        derivation_policy_ref=POLICY,
        deriver_ref=DERIVER,
        as_of=as_of,
        derived_at=T0 + timedelta(minutes=5),
        dimensions=(supported_dimension(), unknown_dimension()),
        rationale="Current supported state for the bounded motor-construction capability.",
    )


def test_frame_is_versioned_and_dimension_order_is_deterministic() -> None:
    value = frame()
    assert str(value.ref) == "civilization_bootstrap:technical_competence@1"
    assert [item.key for item in value.dimensions] == ["diagnosis", "execution"]


def test_frame_rejects_duplicate_dimension_keys() -> None:
    with pytest.raises(InvalidCompetenceFrame, match="duplicate dimension keys"):
        CompetenceFrame(
            frame_id=CompetenceFrameId.parse("core:test_frame"),
            revision=1,
            name="Test frame",
            description="Duplicate dimension fixture.",
            dimensions=(
                CompetenceDimensionDefinition("execution", "Execution", "First definition."),
                CompetenceDimensionDefinition("execution", "Execution 2", "Second definition."),
            ),
        )


def test_same_dimension_key_may_exist_in_different_frames() -> None:
    first = CompetenceFrame(
        CompetenceFrameId.parse("core:first"),
        1,
        "First",
        "First bounded frame.",
        (CompetenceDimensionDefinition("execution", "Execution", "Meaning within first frame."),),
    )
    second = CompetenceFrame(
        CompetenceFrameId.parse("music:performance"),
        1,
        "Performance",
        "Musical performance frame.",
        (CompetenceDimensionDefinition("execution", "Execution", "Meaning within musical frame."),),
    )
    assert first.dimensions[0].key == second.dimensions[0].key
    assert first.ref != second.ref


def test_frame_catalog_rejects_two_current_revisions_of_same_frame_id() -> None:
    current = frame()
    later = CompetenceFrame(
        frame_id=current.frame_id,
        revision=2,
        name=current.name,
        description=current.description,
        dimensions=current.dimensions,
    )
    with pytest.raises(InvalidCompetenceFrame, match="at most one current revision"):
        CompetenceFrameCatalog((current, later))


def test_unknown_is_first_class_and_carries_no_basis() -> None:
    value = unknown_dimension()
    assert value.standing is DimensionStanding.UNKNOWN
    assert value.supported_claim_ids == ()
    assert value.basis_evaluation_ids == ()


@pytest.mark.parametrize(
    "claims,evaluations",
    [
        ((CapabilityClaimId("claim"),), ()),
        ((), (ClaimEvaluationId("eval"),)),
    ],
)
def test_unknown_rejects_hidden_support_or_basis(claims, evaluations) -> None:
    with pytest.raises(InvalidPersonalCapabilityState, match="UNKNOWN"):
        CompetenceDimensionState(
            "diagnosis",
            DimensionStanding.UNKNOWN,
            supported_claim_ids=claims,
            basis_evaluation_ids=evaluations,
            rationale="Invalid hidden basis.",
        )


def test_insufficient_requires_basis_and_forbids_supported_claim_content() -> None:
    with pytest.raises(InvalidPersonalCapabilityState, match="requires at least one basis"):
        CompetenceDimensionState(
            "diagnosis",
            DimensionStanding.INSUFFICIENT,
            rationale="Nothing evaluated.",
        )
    with pytest.raises(InvalidPersonalCapabilityState, match="must not claim supported"):
        CompetenceDimensionState(
            "diagnosis",
            DimensionStanding.INSUFFICIENT,
            supported_claim_ids=(CapabilityClaimId("claim"),),
            basis_evaluation_ids=(ClaimEvaluationId("eval"),),
            rationale="Invalid supported content.",
        )


def test_supported_is_not_a_mastery_score() -> None:
    value = supported_dimension()
    assert value.standing is DimensionStanding.SUPPORTED
    assert not hasattr(value, "score")
    assert not hasattr(value, "mastery")
    assert not hasattr(value, "level")


def test_historical_reconstruction_allows_later_derivation() -> None:
    value = state(as_of=T0)
    assert value.derived_at > value.as_of


def test_state_rejects_derived_at_before_as_of() -> None:
    with pytest.raises(InvalidPersonalCapabilityState, match="derived_at"):
        PersonalCapabilityState(
            state_id=PersonalCapabilityStateId("state_bad_time"),
            subject_ref=SUBJECT,
            concept_ref=CONCEPT,
            frame_ref=FRAME_REF,
            derivation_policy_ref=POLICY,
            deriver_ref=DERIVER,
            as_of=T0,
            derived_at=T0 - timedelta(seconds=1),
            dimensions=(unknown_dimension(),),
            rationale="Invalid future-boundary reconstruction.",
        )


def test_state_set_is_structurally_one_subject() -> None:
    other = CapabilitySubjectRef("subject_02")
    foreign = PersonalCapabilityState(
        state_id=PersonalCapabilityStateId("state_other"),
        subject_ref=other,
        concept_ref=CONCEPT,
        frame_ref=FRAME_REF,
        derivation_policy_ref=POLICY,
        deriver_ref=DERIVER,
        as_of=T0,
        derived_at=T0,
        dimensions=(CompetenceDimensionState("diagnosis", DimensionStanding.UNKNOWN, rationale="Unknown."),),
        rationale="Foreign-subject state.",
    )
    with pytest.raises(InvalidStateSet, match="exactly one subject"):
        PersonalCapabilityStateSet(subject_ref=SUBJECT, states=(foreign,))


def test_no_state_record_is_distinct_from_an_unknown_state_record() -> None:
    empty = PersonalCapabilityStateSet(subject_ref=SUBJECT)
    explicit = PersonalCapabilityStateSet(subject_ref=SUBJECT, states=(state(),))
    assert empty.states == ()
    assert explicit.states[0].dimensions[0].standing is DimensionStanding.UNKNOWN
