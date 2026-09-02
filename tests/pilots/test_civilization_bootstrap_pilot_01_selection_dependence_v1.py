from types import SimpleNamespace

import pytest

from capability_lab.pilots.civilization_bootstrap_01 import (
    InvalidPilotEvidenceMaterialization,
    PilotMaterializationSelectionDeclaration,
    PilotMaterializedEvidenceSelectionEntry,
    PilotObservationSelectionKind,
    PilotObservationSelectionRef,
    build_pilot_materialization_selection_declaration_v1,
    pilot_observation_selection_dependence_key_v1,
    validate_pilot_materialized_evidence_shared_selection_preconditions_v1,
)
from capability_lab.pilots.civilization_bootstrap_01 import (
    materialization_selection_dependence as selection_module,
)


def _selection(kind, ref):
    return PilotObservationSelectionRef(kind, ref)


def _fake_entry(evidence_id, selections):
    allocation_entry = SimpleNamespace(
        temporal_entry=SimpleNamespace(
            coordination_entry=SimpleNamespace(
                mechanism_entry=SimpleNamespace(
                    upstream_lineage_entry=SimpleNamespace(
                        basis_entry=SimpleNamespace(
                            evidence=SimpleNamespace(evidence_id=evidence_id)
                        )
                    )
                )
            )
        )
    )
    declaration = SimpleNamespace(selections=tuple(selections))
    keys = tuple(
        sorted(
            pilot_observation_selection_dependence_key_v1(selection)
            for selection in selections
        )
    )
    return SimpleNamespace(
        allocation_entry=allocation_entry,
        selection_declaration=declaration,
        selection_keys=keys,
    )


def _patch_entries(monkeypatch):
    def canonical(values):
        return tuple(
            sorted(
                tuple(values),
                key=lambda item: str(
                    item.allocation_entry.temporal_entry.coordination_entry
                    .mechanism_entry.upstream_lineage_entry.basis_entry
                    .evidence.evidence_id
                ),
            )
        )

    monkeypatch.setattr(selection_module, "_selection_entries_tuple", canonical)
    return canonical


def _patch_prior_gate(monkeypatch):
    monkeypatch.setattr(
        selection_module._allocation_completeness,
        "validate_pilot_materialized_evidence_reviewed_allocation_origin_preconditions_v1",
        lambda entries, **kwargs: tuple(entries),
    )


def _validate(entries):
    marker = object()
    return validate_pilot_materialized_evidence_shared_selection_preconditions_v1(
        entries,
        source_lineage_graph=marker,
        source_completeness_review=marker,
        mechanism_lineage_graph=marker,
        mechanism_completeness_review=marker,
        coordination_lineage_graph=marker,
        coordination_completeness_review=marker,
        temporal_lineage_graph=marker,
        temporal_completeness_review=marker,
        allocation_lineage_graph=marker,
        allocation_completeness_review=marker,
    )


@pytest.mark.parametrize(
    "kind,ref",
    [
        (PilotObservationSelectionKind.SAMPLING_FRAME_INSTANCE, "sampling_frame:01"),
        (PilotObservationSelectionKind.SELECTION_EPISODE, "selection_episode:01"),
        (
            PilotObservationSelectionKind.COHORT_CONSTRUCTION_STATE,
            "cohort_construction_state:01",
        ),
        (PilotObservationSelectionKind.RECRUITMENT_BATCH, "recruitment_batch:01"),
        (PilotObservationSelectionKind.RESAMPLING_DRAW, "resampling_draw:01"),
        (
            PilotObservationSelectionKind.INCLUSION_POLICY_EXECUTION,
            "inclusion_policy_execution:01",
        ),
    ],
)
def test_shared_exact_selection_identity_rejects(monkeypatch, kind, ref) -> None:
    _patch_entries(monkeypatch)
    _patch_prior_gate(monkeypatch)
    shared = _selection(kind, ref)
    entries = (
        _fake_entry("evidence_a", (shared,)),
        _fake_entry("evidence_b", (shared,)),
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="shared-selection independence preconditions",
    ) as exc_info:
        _validate(entries)
    assert ref not in str(exc_info.value)
    assert "pilot_observation_selection:" in str(exc_info.value)


def test_distinct_exact_selection_refs_clear_only_exact_layer(monkeypatch) -> None:
    canonical = _patch_entries(monkeypatch)
    _patch_prior_gate(monkeypatch)
    entries = (
        _fake_entry(
            "evidence_a",
            (
                _selection(
                    PilotObservationSelectionKind.SELECTION_EPISODE,
                    "selection_episode:a",
                ),
            ),
        ),
        _fake_entry(
            "evidence_b",
            (
                _selection(
                    PilotObservationSelectionKind.SELECTION_EPISODE,
                    "selection_episode:b",
                ),
            ),
        ),
    )
    assert _validate(tuple(reversed(entries))) == canonical(entries)


def test_multiple_selection_refs_inside_one_observation_do_not_self_collide(
    monkeypatch,
) -> None:
    _patch_entries(monkeypatch)
    _patch_prior_gate(monkeypatch)
    entries = (
        _fake_entry(
            "evidence_a",
            (
                _selection(
                    PilotObservationSelectionKind.SAMPLING_FRAME_INSTANCE,
                    "sampling_frame:a",
                ),
                _selection(
                    PilotObservationSelectionKind.RECRUITMENT_BATCH,
                    "recruitment_batch:a",
                ),
            ),
        ),
        _fake_entry("evidence_b", ()),
    )
    assert _validate(entries) == entries


def test_empty_declarations_mean_no_refs_supplied_not_independence(monkeypatch) -> None:
    _patch_entries(monkeypatch)
    _patch_prior_gate(monkeypatch)
    entries = (
        _fake_entry("evidence_a", ()),
        _fake_entry("evidence_b", ()),
    )
    assert _validate(entries) == entries


def test_reviewed_allocation_failure_dominates_selection_separation(
    monkeypatch,
) -> None:
    _patch_entries(monkeypatch)

    def reject(*args, **kwargs):
        raise InvalidPilotEvidenceMaterialization(
            "allocation completeness precondition failed"
        )

    monkeypatch.setattr(
        selection_module._allocation_completeness,
        "validate_pilot_materialized_evidence_reviewed_allocation_origin_preconditions_v1",
        reject,
    )
    entries = (
        _fake_entry(
            "evidence_a",
            (
                _selection(
                    PilotObservationSelectionKind.SELECTION_EPISODE,
                    "selection_episode:a",
                ),
            ),
        ),
        _fake_entry(
            "evidence_b",
            (
                _selection(
                    PilotObservationSelectionKind.SELECTION_EPISODE,
                    "selection_episode:b",
                ),
            ),
        ),
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="allocation completeness precondition failed",
    ):
        _validate(entries)


def test_prior_gate_basis_ordering_mismatch_rejects(monkeypatch) -> None:
    _patch_entries(monkeypatch)

    def reversed_basis(entries, **kwargs):
        return tuple(reversed(tuple(entries)))

    monkeypatch.setattr(
        selection_module._allocation_completeness,
        "validate_pilot_materialized_evidence_reviewed_allocation_origin_preconditions_v1",
        reversed_basis,
    )
    entries = (
        _fake_entry("evidence_a", ()),
        _fake_entry("evidence_b", ()),
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="do not match reviewed allocation-origin basis ordering",
    ):
        _validate(entries)


def test_selection_declaration_is_canonical_and_duplicate_closed() -> None:
    first = _selection(
        PilotObservationSelectionKind.RECRUITMENT_BATCH,
        "recruitment_batch:b",
    )
    second = _selection(
        PilotObservationSelectionKind.COHORT_CONSTRUCTION_STATE,
        "cohort_state:a",
    )
    declaration = PilotMaterializationSelectionDeclaration(
        candidate_sha256="1" * 64,
        selections=(first, second),
    )
    assert declaration.selections == tuple(
        sorted((first, second), key=lambda item: (item.kind.value, item.ref))
    )

    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="must not repeat an exact selection ref",
    ):
        PilotMaterializationSelectionDeclaration(
            candidate_sha256="1" * 64,
            selections=(first, first),
        )


def test_selection_declaration_requires_tuple_and_sha256() -> None:
    selection = _selection(
        PilotObservationSelectionKind.SELECTION_EPISODE,
        "selection_episode:01",
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="candidate_sha256",
    ):
        PilotMaterializationSelectionDeclaration(
            candidate_sha256="A" * 64,
            selections=(selection,),
        )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="selections must be a tuple",
    ):
        PilotMaterializationSelectionDeclaration(
            candidate_sha256="a" * 64,
            selections=[selection],
        )


def test_candidate_builder_rejects_non_candidate() -> None:
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="candidate must be PilotEvidenceMaterializationCandidate",
    ):
        build_pilot_materialization_selection_declaration_v1(object())


def test_selection_entry_binds_declaration_to_exact_candidate(monkeypatch) -> None:
    class FakeAllocationEntry:
        def __init__(self, candidate):
            self.temporal_entry = SimpleNamespace(
                coordination_entry=SimpleNamespace(
                    mechanism_entry=SimpleNamespace(
                        upstream_lineage_entry=SimpleNamespace(
                            basis_entry=SimpleNamespace(candidate=candidate)
                        )
                    )
                )
            )

    monkeypatch.setattr(
        selection_module._allocation,
        "PilotMaterializedEvidenceAllocationEntry",
        FakeAllocationEntry,
    )
    monkeypatch.setattr(
        selection_module._materialization,
        "pilot_evidence_materialization_candidate_sha256",
        lambda candidate: "1" * 64,
    )
    allocation_entry = FakeAllocationEntry(object())
    matching = PilotMaterializationSelectionDeclaration(
        candidate_sha256="1" * 64,
    )
    entry = PilotMaterializedEvidenceSelectionEntry(allocation_entry, matching)
    assert entry.selection_keys == ()

    stale = PilotMaterializationSelectionDeclaration(
        candidate_sha256="2" * 64,
    )
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="does not match exact basis candidate",
    ):
        PilotMaterializedEvidenceSelectionEntry(allocation_entry, stale)


def test_selection_dependence_key_is_kind_sensitive_and_private() -> None:
    ref = "shared_raw_ref_that_must_not_escape"
    sampling = _selection(PilotObservationSelectionKind.SAMPLING_FRAME_INSTANCE, ref)
    recruitment = _selection(PilotObservationSelectionKind.RECRUITMENT_BATCH, ref)
    sampling_key = pilot_observation_selection_dependence_key_v1(sampling)
    recruitment_key = pilot_observation_selection_dependence_key_v1(recruitment)
    assert sampling_key != recruitment_key
    assert sampling_key.startswith("pilot_observation_selection:")
    assert ref not in sampling_key


def test_selection_ref_requires_enum_and_canonical_ascii() -> None:
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="kind must be PilotObservationSelectionKind",
    ):
        PilotObservationSelectionRef("SELECTION_EPISODE", "selection_episode:01")
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="canonical opaque ASCII identifier",
    ):
        PilotObservationSelectionRef(
            PilotObservationSelectionKind.SELECTION_EPISODE,
            "selection episode with spaces",
        )


def test_design_similarity_is_not_encoded_as_selection_identity_kind() -> None:
    names = {item.name for item in PilotObservationSelectionKind}
    assert "POPULATION_LABEL" not in names
    assert "COHORT_LABEL" not in names
    assert "SAMPLING_ALGORITHM" not in names
    assert "INCLUSION_RULE" not in names
    assert "DATASET_NAME" not in names
    assert "STUDY_FAMILY" not in names


def test_gate_rejects_wrong_entry_type_before_prior_gate(monkeypatch) -> None:
    called = False

    def prior(*args, **kwargs):
        nonlocal called
        called = True
        return ()

    monkeypatch.setattr(
        selection_module._allocation_completeness,
        "validate_pilot_materialized_evidence_reviewed_allocation_origin_preconditions_v1",
        prior,
    )
    marker = object()
    with pytest.raises(
        InvalidPilotEvidenceMaterialization,
        match="must contain PilotMaterializedEvidenceSelectionEntry",
    ):
        validate_pilot_materialized_evidence_shared_selection_preconditions_v1(
            (object(),),
            source_lineage_graph=marker,
            source_completeness_review=marker,
            mechanism_lineage_graph=marker,
            mechanism_completeness_review=marker,
            coordination_lineage_graph=marker,
            coordination_completeness_review=marker,
            temporal_lineage_graph=marker,
            temporal_completeness_review=marker,
            allocation_lineage_graph=marker,
            allocation_completeness_review=marker,
        )
    assert called is False
