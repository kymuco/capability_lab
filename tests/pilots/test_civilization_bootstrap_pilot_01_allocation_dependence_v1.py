from types import SimpleNamespace

import pytest

from capability_lab.pilots.civilization_bootstrap_01 import (
    InvalidPilotEvidenceMaterialization,
    PilotMaterializationAllocationDeclaration,
    PilotMaterializedEvidenceAllocationEntry,
    PilotObservationAllocationKind,
    PilotObservationAllocationRef,
    pilot_observation_allocation_dependence_key_v1,
    validate_pilot_materialized_evidence_shared_allocation_preconditions_v1,
)
from capability_lab.pilots.civilization_bootstrap_01 import (
    materialization_allocation_dependence as allocation_module,
)


def _ref(kind, ref):
    return PilotObservationAllocationRef(kind, ref)


def _fake_temporal_entry(evidence_id):
    basis = SimpleNamespace(evidence=SimpleNamespace(evidence_id=evidence_id))
    upstream = SimpleNamespace(basis_entry=basis)
    mechanism = SimpleNamespace(upstream_lineage_entry=upstream)
    coordination = SimpleNamespace(mechanism_entry=mechanism)
    return SimpleNamespace(coordination_entry=coordination)


def _fake_allocation_entry(evidence_id, *allocations):
    temporal_entry = _fake_temporal_entry(evidence_id)
    return SimpleNamespace(
        temporal_entry=temporal_entry,
        allocation_declaration=SimpleNamespace(
            candidate_sha256="1" * 64,
            allocations=tuple(allocations),
        ),
        allocation_keys=tuple(
            sorted(
                pilot_observation_allocation_dependence_key_v1(item)
                for item in allocations
            )
        ),
    )


def _patch_entries(monkeypatch):
    def canonical(values):
        return tuple(
            sorted(
                tuple(values),
                key=lambda item: str(
                    item.temporal_entry.coordination_entry.mechanism_entry
                    .upstream_lineage_entry.basis_entry.evidence.evidence_id
                ),
            )
        )

    monkeypatch.setattr(allocation_module, "_allocation_entries_tuple", canonical)
    return canonical


def _patch_prior_gate(monkeypatch):
    monkeypatch.setattr(
        allocation_module._temporal_completeness,
        "validate_pilot_materialized_evidence_reviewed_temporal_origin_preconditions_v1",
        lambda entries, **kwargs: tuple(entries),
    )


def _validate(entries):
    marker = object()
    return validate_pilot_materialized_evidence_shared_allocation_preconditions_v1(
        entries,
        source_lineage_graph=marker,
        source_completeness_review=marker,
        mechanism_lineage_graph=marker,
        mechanism_completeness_review=marker,
        coordination_lineage_graph=marker,
        coordination_completeness_review=marker,
        temporal_lineage_graph=marker,
        temporal_completeness_review=marker,
    )


def test_shared_exact_allocation_block_rejects_reviewed_temporal_basis(
    monkeypatch,
) -> None:
    canonical = _patch_entries(monkeypatch)
    _patch_prior_gate(monkeypatch)
    shared = _ref(
        PilotObservationAllocationKind.ALLOCATION_BLOCK,
        "allocation_block:shared_01",
    )
    entries = (
        _fake_allocation_entry("evidence_b", shared),
        _fake_allocation_entry("evidence_a", shared),
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="share one exact declared experimental allocation/assignment causal identity",
    ):
        _validate(entries)
    assert canonical(entries)[0].temporal_entry.coordination_entry.mechanism_entry.upstream_lineage_entry.basis_entry.evidence.evidence_id == "evidence_a"


@pytest.mark.parametrize(
    "kind,ref",
    [
        (
            PilotObservationAllocationKind.ASSIGNMENT_EPISODE,
            "assignment_episode:shared_01",
        ),
        (
            PilotObservationAllocationKind.RANDOMIZATION_STATE,
            "randomization_state:shared_01",
        ),
        (
            PilotObservationAllocationKind.ADAPTIVE_ALLOCATION_STATE,
            "adaptive_allocation_state:shared_01",
        ),
        (
            PilotObservationAllocationKind.CLUSTER_ASSIGNMENT_UNIT,
            "cluster_assignment_unit:shared_01",
        ),
        (
            PilotObservationAllocationKind.MATCHED_ALLOCATION_SET,
            "matched_allocation_set:shared_01",
        ),
    ],
)
def test_other_shared_exact_allocation_identities_reject(
    monkeypatch, kind, ref
) -> None:
    _patch_entries(monkeypatch)
    _patch_prior_gate(monkeypatch)
    shared = _ref(kind, ref)
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="shared-allocation independence preconditions",
    ):
        _validate(
            (
                _fake_allocation_entry("evidence_a", shared),
                _fake_allocation_entry("evidence_b", shared),
            )
        )


def test_distinct_allocation_refs_clear_only_exact_allocation_gate(
    monkeypatch,
) -> None:
    canonical = _patch_entries(monkeypatch)
    _patch_prior_gate(monkeypatch)
    a = _ref(
        PilotObservationAllocationKind.ALLOCATION_BLOCK,
        "allocation_block:a",
    )
    b = _ref(
        PilotObservationAllocationKind.ALLOCATION_BLOCK,
        "allocation_block:b",
    )
    entries = (
        _fake_allocation_entry("evidence_b", b),
        _fake_allocation_entry("evidence_a", a),
    )
    assert _validate(entries) == canonical(entries)


def test_empty_allocation_declarations_do_not_assert_independent_randomization(
    monkeypatch,
) -> None:
    canonical = _patch_entries(monkeypatch)
    _patch_prior_gate(monkeypatch)
    entries = (
        _fake_allocation_entry("evidence_b"),
        _fake_allocation_entry("evidence_a"),
    )
    assert _validate(entries) == canonical(entries)


def test_prior_temporal_review_rejects_before_distinct_allocation_can_help(
    monkeypatch,
) -> None:
    _patch_entries(monkeypatch)
    a = _ref(
        PilotObservationAllocationKind.ASSIGNMENT_EPISODE,
        "assignment_episode:a",
    )
    b = _ref(
        PilotObservationAllocationKind.ASSIGNMENT_EPISODE,
        "assignment_episode:b",
    )

    def reject(*args, **kwargs):
        raise InvalidPilotEvidenceMaterialization(
            "temporal declarations are not reviewed COMPLETE_FOR_SCOPE"
        )

    monkeypatch.setattr(
        allocation_module._temporal_completeness,
        "validate_pilot_materialized_evidence_reviewed_temporal_origin_preconditions_v1",
        reject,
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="temporal declarations are not reviewed COMPLETE_FOR_SCOPE",
    ):
        _validate(
            (
                _fake_allocation_entry("evidence_a", a),
                _fake_allocation_entry("evidence_b", b),
            )
        )


def test_allocation_key_is_domain_separated_kind_sensitive_and_opaque() -> None:
    raw_ref = "shared:opaque_allocation_123"
    block = _ref(PilotObservationAllocationKind.ALLOCATION_BLOCK, raw_ref)
    episode = _ref(PilotObservationAllocationKind.ASSIGNMENT_EPISODE, raw_ref)
    block_key = pilot_observation_allocation_dependence_key_v1(block)
    episode_key = pilot_observation_allocation_dependence_key_v1(episode)
    assert block_key.startswith("pilot_observation_allocation:")
    assert len(block_key.removeprefix("pilot_observation_allocation:")) == 64
    assert raw_ref not in block_key
    assert block_key != episode_key


def test_allocation_declaration_canonicalizes_order() -> None:
    first = _ref(
        PilotObservationAllocationKind.ASSIGNMENT_EPISODE,
        "assignment_episode:z",
    )
    second = _ref(
        PilotObservationAllocationKind.ALLOCATION_BLOCK,
        "allocation_block:a",
    )
    declaration = PilotMaterializationAllocationDeclaration(
        candidate_sha256="1" * 64,
        allocations=(first, second),
    )
    assert declaration.allocations == (second, first)


def test_allocation_declaration_rejects_duplicate_exact_refs() -> None:
    allocation = _ref(
        PilotObservationAllocationKind.RANDOMIZATION_STATE,
        "randomization_state:duplicate",
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="must not repeat an exact allocation ref",
    ):
        PilotMaterializationAllocationDeclaration(
            candidate_sha256="1" * 64,
            allocations=(allocation, allocation),
        )


def test_allocation_declaration_requires_tuple() -> None:
    allocation = _ref(
        PilotObservationAllocationKind.MATCHED_ALLOCATION_SET,
        "matched_allocation_set:one",
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="allocation declaration allocations must be a tuple",
    ):
        PilotMaterializationAllocationDeclaration(
            candidate_sha256="1" * 64,
            allocations=[allocation],
        )


def test_allocation_ref_requires_enum_and_canonical_opaque_ascii() -> None:
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="kind must be PilotObservationAllocationKind",
    ):
        PilotObservationAllocationRef(
            "ALLOCATION_BLOCK",
            "allocation_block:raw_string_kind",
        )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="canonical opaque ASCII identifier",
    ):
        _ref(
            PilotObservationAllocationKind.OTHER,
            "allocation ref with spaces",
        )


def test_allocation_entry_is_bound_to_exact_candidate(monkeypatch) -> None:
    class FakeTemporalEntry:
        pass

    monkeypatch.setattr(
        allocation_module._temporal,
        "PilotMaterializedEvidenceTemporalEntry",
        FakeTemporalEntry,
    )
    monkeypatch.setattr(
        allocation_module._materialization,
        "pilot_evidence_materialization_candidate_sha256",
        lambda candidate: "1" * 64,
    )

    temporal_entry = FakeTemporalEntry()
    temporal_entry.coordination_entry = SimpleNamespace(
        mechanism_entry=SimpleNamespace(
            upstream_lineage_entry=SimpleNamespace(
                basis_entry=SimpleNamespace(candidate=object())
            )
        )
    )
    declaration = PilotMaterializationAllocationDeclaration(
        candidate_sha256="2" * 64,
        allocations=(),
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="candidate_sha256 does not match exact basis candidate",
    ):
        PilotMaterializedEvidenceAllocationEntry(
            temporal_entry,
            declaration,
        )


def test_validator_rejects_wrong_entry_type_without_monkeypatch() -> None:
    marker = object()
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="must contain PilotMaterializedEvidenceAllocationEntry",
    ):
        validate_pilot_materialized_evidence_shared_allocation_preconditions_v1(
            (object(),),
            source_lineage_graph=marker,
            source_completeness_review=marker,
            mechanism_lineage_graph=marker,
            mechanism_completeness_review=marker,
            coordination_lineage_graph=marker,
            coordination_completeness_review=marker,
            temporal_lineage_graph=marker,
            temporal_completeness_review=marker,
        )


def test_allocation_enum_does_not_encode_arm_or_probability_equivalence() -> None:
    names = set(PilotObservationAllocationKind.__members__)
    assert "TREATMENT_ARM" not in names
    assert "ARM_LABEL" not in names
    assert "ALLOCATION_PROBABILITY" not in names
    assert "RANDOMIZATION_ALGORITHM" not in names
