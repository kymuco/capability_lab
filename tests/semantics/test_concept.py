import pytest

from capability_lab.semantics import (
    CapabilityConcept,
    CapabilityId,
    ConceptLifecycle,
    InvalidConceptError,
)


ID = CapabilityId("civilization_bootstrap", "electric_motor_construction")


def test_concept_normalizes_text_and_alias_order() -> None:
    concept = CapabilityConcept(
        ID,
        " Electric Motor Construction ",
        " Build an electric motor in a stated context. ",
        aliases=("Двигатель", "Motor Building"),
    )
    assert concept.name == "Electric Motor Construction"
    assert concept.definition == "Build an electric motor in a stated context."
    assert concept.aliases == ("Motor Building", "Двигатель")


def test_display_name_does_not_change_identity() -> None:
    first = CapabilityConcept(ID, "Motor Construction", "Definition A")
    second = CapabilityConcept(ID, "Electric Motor Construction", "Definition A")
    assert first.capability_id == second.capability_id


def test_concept_requires_name() -> None:
    with pytest.raises(InvalidConceptError):
        CapabilityConcept(ID, "", "Definition")


def test_concept_requires_definition() -> None:
    with pytest.raises(InvalidConceptError):
        CapabilityConcept(ID, "Name", "")


@pytest.mark.parametrize("revision", [0, -1, 1.5, True])
def test_invalid_revision_rejected(revision) -> None:
    with pytest.raises(InvalidConceptError):
        CapabilityConcept(ID, "Name", "Definition", revision=revision)


def test_duplicate_alias_rejected() -> None:
    with pytest.raises(InvalidConceptError):
        CapabilityConcept(ID, "Name", "Definition", aliases=("Motor", " Motor "))


def test_deprecated_concept_requires_note() -> None:
    with pytest.raises(InvalidConceptError):
        CapabilityConcept(
            ID,
            "Name",
            "Definition",
            lifecycle=ConceptLifecycle.DEPRECATED,
        )


def test_deprecated_concept_preserves_identity() -> None:
    concept = CapabilityConcept(
        ID,
        "Name",
        "Definition",
        revision=3,
        lifecycle=ConceptLifecycle.DEPRECATED,
        deprecation_note="Split into narrower concepts.",
    )
    assert concept.capability_id == ID
    assert concept.lifecycle is ConceptLifecycle.DEPRECATED


def test_active_concept_rejects_deprecation_note() -> None:
    with pytest.raises(InvalidConceptError):
        CapabilityConcept(ID, "Name", "Definition", deprecation_note="Not active")
