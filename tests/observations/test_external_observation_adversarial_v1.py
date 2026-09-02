import ast
from dataclasses import fields, replace
from datetime import timedelta
import json
from pathlib import Path

import pytest

from capability_lab.epistemics import CapabilitySubjectRef
from capability_lab.observations import (
    ExternalObservationEnvelope,
    ExternalObservationForm,
    ExternalObservationId,
    ExternalObservationLedger,
    ExternalObservationLedgerSuccessionReceipt,
    ExternalObservationOriginKind,
    InvalidExternalObservation,
    InvalidExternalObservationLedger,
    external_observation_sha256_v1,
    validate_external_observation_ledger_successor_v1,
    validate_external_observation_ledger_v1,
    validate_external_observation_v1,
)

from test_external_observation_v1 import (
    SUBJECT,
    T0,
    _observation,
    _payload,
)


def test_public_envelope_has_no_evidence_or_capability_interpretation_surface() -> None:
    names = {item.name for item in fields(ExternalObservationEnvelope)}
    forbidden = {
        "evidence_id",
        "evidence_kind",
        "outcome",
        "concept_ref",
        "claim_id",
        "evaluation_id",
        "state_id",
        "score",
        "grade",
        "mastery",
        "readiness",
        "permission",
        "success",
        "failure",
    }
    assert names.isdisjoint(forbidden)


def test_production_import_surface_has_no_evidence_or_hde_authority_import() -> None:
    root = Path(__file__).parents[2]
    path = root / "src/capability_lab/observations/core.py"
    source = path.read_text()
    tree = ast.parse(source)

    imports = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.extend(("import", alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(
                (
                    "from",
                    node.level,
                    node.module,
                    tuple(alias.name for alias in node.names),
                )
            )

    assert imports == [
        ("from", 0, "__future__", ("annotations",)),
        ("from", 0, "dataclasses", ("dataclass",)),
        ("from", 0, "datetime", ("datetime", "timezone")),
        ("from", 0, "enum", ("Enum",)),
        ("import", "hashlib"),
        ("import", "re"),
        ("import", "unicodedata"),
        (
            "from",
            0,
            "capability_lab.epistemics",
            ("CapabilitySubjectRef",),
        ),
    ]
    assert "EvidenceRecord" not in source
    assert "CapabilityClaim" not in source
    assert "ClaimEvaluation" not in source
    assert "capability_lab.hde" not in source
    assert "hde_core" not in source


def test_reused_source_event_identity_is_rejected_inside_ledger_constructor() -> None:
    first = _observation()
    second = _observation(
        observation_id="obs-2",
        source_event_id=first.source_event_id,
        payload_refs=(_payload("artifact-2", "b" * 64),),
    )

    with pytest.raises(
        InvalidExternalObservationLedger,
        match="source_ref/source_event_id",
    ):
        ExternalObservationLedger(
            subject_ref=SUBJECT,
            observations=(first, second),
        )


def test_append_only_successor_rejects_removal() -> None:
    first = _observation()
    second = _observation(
        observation_id="obs-2",
        source_event_id="evt-2",
        observed_at=T0 + timedelta(minutes=1),
        captured_at=T0 + timedelta(minutes=1, seconds=1),
    )
    predecessor = ExternalObservationLedger(
        subject_ref=SUBJECT,
        observations=(first, second),
    )
    successor = ExternalObservationLedger(
        subject_ref=SUBJECT,
        observations=(second,),
    )

    with pytest.raises(
        InvalidExternalObservationLedger,
        match="may not remove",
    ):
        validate_external_observation_ledger_successor_v1(
            predecessor=predecessor,
            successor=successor,
        )


def test_append_only_successor_rejects_retained_content_mutation() -> None:
    first = _observation()
    predecessor = ExternalObservationLedger(
        subject_ref=SUBJECT,
        observations=(first,),
    )
    changed = replace(
        first,
        payload_refs=(_payload("artifact-1", "f" * 64),),
    )
    successor = ExternalObservationLedger(
        subject_ref=SUBJECT,
        observations=(changed,),
    )

    with pytest.raises(
        InvalidExternalObservationLedger,
        match="may not mutate",
    ):
        validate_external_observation_ledger_successor_v1(
            predecessor=predecessor,
            successor=successor,
        )


def test_succession_subject_switch_is_rejected() -> None:
    predecessor = ExternalObservationLedger(
        subject_ref=SUBJECT,
        observations=(_observation(),),
    )
    other_subject = CapabilitySubjectRef("subject-beta")
    other = _observation(
        observation_id="obs-2",
        source_event_id="evt-2",
        subject_ref=other_subject,
    )
    successor = ExternalObservationLedger(
        subject_ref=other_subject,
        observations=(other,),
    )

    with pytest.raises(
        InvalidExternalObservationLedger,
        match="subject_ref must equal",
    ):
        validate_external_observation_ledger_successor_v1(
            predecessor=predecessor,
            successor=successor,
        )


def test_fresh_validation_keeps_corrupted_typed_primitives_inside_pr12_boundary() -> None:
    local_subject = CapabilitySubjectRef("subject-corrupt")
    observation = _observation(
        observation_id="obs-corrupt",
        source_event_id="evt-corrupt",
        subject_ref=local_subject,
    )
    object.__setattr__(observation.subject_ref, "value", "bad subject!")

    with pytest.raises(
        InvalidExternalObservation,
        match="strict semantic reconstruction",
    ):
        validate_external_observation_v1(observation)


def test_fresh_ledger_validation_rejects_post_construction_observation_corruption() -> None:
    ledger = ExternalObservationLedger(
        subject_ref=SUBJECT,
        observations=(_observation(),),
    )
    object.__setattr__(
        ledger.observations[0],
        "origin_kind",
        "subject",
    )

    with pytest.raises(InvalidExternalObservationLedger):
        validate_external_observation_ledger_v1(ledger)


def test_serialization_rejects_duplicate_keys_unknown_fields_and_nonfinite_values() -> None:
    observation = _observation()
    payload = observation.to_json()

    duplicate = payload.replace(
        '"schema_version":1',
        '"schema_version":1,"schema_version":1',
        1,
    )
    with pytest.raises(
        InvalidExternalObservation,
        match="duplicate JSON object keys",
    ):
        ExternalObservationEnvelope.from_json(duplicate)

    parsed = json.loads(payload)
    parsed["authority"] = "forbidden"
    with pytest.raises(
        InvalidExternalObservation,
        match="fields must match schema exactly",
    ):
        ExternalObservationEnvelope.from_json(
            json.dumps(parsed, separators=(",", ":"))
        )

    nonfinite = payload.replace('"byte_size":128', '"byte_size":NaN', 1)
    with pytest.raises(
        InvalidExternalObservation,
        match="non-finite JSON constant",
    ):
        ExternalObservationEnvelope.from_json(nonfinite)


def test_noncanonical_runtime_containers_fail_closed() -> None:
    observation = _observation()

    with pytest.raises(
        InvalidExternalObservation,
        match="context_factors must be exact tuple",
    ):
        ExternalObservationEnvelope(
            observation_id=ExternalObservationId("obs-list"),
            subject_ref=SUBJECT,
            source_ref=observation.source_ref,
            source_event_id="evt-list",
            form=ExternalObservationForm.EVENT,
            origin_kind=ExternalObservationOriginKind.SUBJECT,
            observed_at=T0,
            captured_at=T0,
            context_factors=[],
            payload_refs=(),
        )

    with pytest.raises(
        InvalidExternalObservationLedger,
        match="observations must be exact tuple",
    ):
        ExternalObservationLedger(
            subject_ref=SUBJECT,
            observations=[observation],
        )


def test_payload_change_changes_observation_digest_without_changing_source_identity() -> None:
    first = _observation()
    second = replace(
        first,
        payload_refs=(_payload("artifact-1", "d" * 64),),
    )

    assert first.source_event_key == second.source_event_key
    assert external_observation_sha256_v1(first) != (
        external_observation_sha256_v1(second)
    )


def test_publicly_constructed_succession_receipt_is_not_validator_issued() -> None:
    receipt = ExternalObservationLedgerSuccessionReceipt(
        predecessor_sha256="a" * 64,
        successor_sha256="b" * 64,
        retained_observation_ids=(),
        added_observation_ids=(),
    )
    assert receipt.validator_issued is False
