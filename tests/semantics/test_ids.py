import pytest

from capability_lab.semantics import CapabilityId, InvalidIdentifierError


@pytest.mark.parametrize(
    "value",
    [
        "core:algebra",
        "civilization_bootstrap:basic_circuits",
        "local.a7c392:horse_husbandry",
    ],
)
def test_capability_id_roundtrip(value: str) -> None:
    capability_id = CapabilityId.parse(value)
    assert str(capability_id) == value


@pytest.mark.parametrize(
    "value",
    [
        "Core:algebra",
        "core:BasicCircuits",
        "core/basic_circuits",
        "core",
        "core:a:b",
        ":algebra",
        "core:",
        "core.bad-segment:algebra",
    ],
)
def test_invalid_capability_ids_rejected(value: str) -> None:
    with pytest.raises(InvalidIdentifierError):
        CapabilityId.parse(value)


def test_id_identity_is_independent_of_display_metadata() -> None:
    assert CapabilityId("core", "algebra") == CapabilityId.parse("core:algebra")
