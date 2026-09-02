from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from capability_lab.epistemics import CapabilitySubjectRef
from capability_lab.observations import (
    ExternalObservationContextFactor,
    ExternalObservationContextFactorKind,
    ExternalObservationEnvelope,
    ExternalObservationForm,
    ExternalObservationId,
    ExternalObservationLedger,
    ExternalObservationOriginKind,
    ExternalObservationPayloadRef,
    ExternalObservationSourceKind,
    ExternalObservationSourceRef,
    InvalidExternalObservation,
    InvalidExternalObservationLedger,
    admit_external_observation_v1,
    external_observation_ledger_sha256_v1,
    external_observation_sha256_v1,
    validate_external_observation_ledger_successor_v1,
    validate_external_observation_ledger_v1,
    validate_external_observation_v1,
)


T0 = datetime(2026, 8, 27, 6, 0, tzinfo=timezone.utc)
SUBJECT = CapabilitySubjectRef("subject-alpha")
SOURCE = ExternalObservationSourceRef(
    ExternalObservationSourceKind.APPLICATION,
    "hde_core",
)


def _payload(
    ref: str = "artifact-1",
    digest: str = "a" * 64,
) -> ExternalObservationPayloadRef:
    return ExternalObservationPayloadRef(
        ref=ref,
        sha256=digest,
        byte_size=128,
        media_type="text/plain",
    )


def _observation(
    *,
    observation_id: str = "obs-1",
    source_event_id: str = "evt-1",
    subject_ref: CapabilitySubjectRef = SUBJECT,
    form: ExternalObservationForm = ExternalObservationForm.ARTIFACT,
    origin_kind: ExternalObservationOriginKind = ExternalObservationOriginKind.MIXED,
    observed_at: datetime = T0,
    captured_at: datetime = T0 + timedelta(seconds=2),
    payload_refs=None,
) -> ExternalObservationEnvelope:
    if payload_refs is None:
        payload_refs = (_payload(),)
    return ExternalObservationEnvelope(
        observation_id=ExternalObservationId(observation_id),
        subject_ref=subject_ref,
        source_ref=SOURCE,
        source_event_id=source_event_id,
        form=form,
        origin_kind=origin_kind,
        observed_at=observed_at,
        captured_at=captured_at,
        observation_started_at=observed_at - timedelta(minutes=3),
        context_factors=(
            ExternalObservationContextFactor(
                ExternalObservationContextFactorKind.ASSISTANCE,
                "AI companion assistance was available.",
            ),
            ExternalObservationContextFactor(
                ExternalObservationContextFactorKind.TOOL,
                "Python",
            ),
        ),
        payload_refs=payload_refs,
    )


def test_external_observation_round_trip_and_digest_are_deterministic() -> None:
    observation = _observation(
        payload_refs=(
            _payload("artifact-2", "b" * 64),
            _payload("artifact-1", "a" * 64),
        )
    )

    restored = ExternalObservationEnvelope.from_json(observation.to_json())

    assert restored == observation
    assert tuple(item.ref for item in observation.payload_refs) == (
        "artifact-1",
        "artifact-2",
    )
    assert external_observation_sha256_v1(restored) == (
        external_observation_sha256_v1(observation)
    )
    validate_external_observation_v1(restored)


def test_payload_bearing_forms_require_at_least_one_exact_payload_ref() -> None:
    for form in (
        ExternalObservationForm.TEXT,
        ExternalObservationForm.ARTIFACT,
        ExternalObservationForm.CONVERSATION,
        ExternalObservationForm.BUNDLE,
    ):
        with pytest.raises(
            InvalidExternalObservation,
            match="require at least one payload ref",
        ):
            _observation(form=form, payload_refs=())


def test_event_form_may_be_metadata_only() -> None:
    observation = _observation(
        form=ExternalObservationForm.EVENT,
        payload_refs=(),
    )
    assert observation.payload_refs == ()
    validate_external_observation_v1(observation)


def test_exact_delivery_replay_is_idempotent_noop() -> None:
    observation = _observation()
    empty = ExternalObservationLedger(subject_ref=SUBJECT)

    admitted = admit_external_observation_v1(
        ledger=empty,
        observation=observation,
    )
    replayed = admit_external_observation_v1(
        ledger=admitted,
        observation=observation,
    )

    assert len(admitted.observations) == 1
    assert replayed is admitted
    assert external_observation_ledger_sha256_v1(replayed) == (
        external_observation_ledger_sha256_v1(admitted)
    )


def test_same_source_event_identity_with_different_content_fails_closed() -> None:
    original = _observation()
    ledger = admit_external_observation_v1(
        ledger=ExternalObservationLedger(subject_ref=SUBJECT),
        observation=original,
    )
    changed = replace(
        original,
        payload_refs=(_payload("artifact-1", "c" * 64),),
    )

    with pytest.raises(
        InvalidExternalObservationLedger,
        match="source_ref/source_event_id identity",
    ):
        admit_external_observation_v1(
            ledger=ledger,
            observation=changed,
        )


def test_same_observation_id_cannot_be_rebound_to_other_source_event() -> None:
    original = _observation()
    ledger = admit_external_observation_v1(
        ledger=ExternalObservationLedger(subject_ref=SUBJECT),
        observation=original,
    )
    rebound = replace(original, source_event_id="evt-2")

    with pytest.raises(
        InvalidExternalObservationLedger,
        match="observation_id is already bound",
    ):
        admit_external_observation_v1(
            ledger=ledger,
            observation=rebound,
        )


def test_subject_boundary_is_exact() -> None:
    ledger = ExternalObservationLedger(subject_ref=SUBJECT)
    other = _observation(
        subject_ref=CapabilitySubjectRef("subject-beta"),
    )

    with pytest.raises(
        InvalidExternalObservationLedger,
        match="subject_ref must match",
    ):
        admit_external_observation_v1(
            ledger=ledger,
            observation=other,
        )


def test_ledger_canonical_order_digest_and_round_trip() -> None:
    second = _observation(
        observation_id="obs-2",
        source_event_id="evt-2",
        observed_at=T0 + timedelta(minutes=1),
        captured_at=T0 + timedelta(minutes=1, seconds=1),
    )
    first = _observation()

    ledger = ExternalObservationLedger(
        subject_ref=SUBJECT,
        observations=(second, first),
    )
    restored = ExternalObservationLedger.from_json(ledger.to_json())

    assert tuple(str(item.observation_id) for item in ledger.observations) == (
        "obs-1",
        "obs-2",
    )
    assert restored == ledger
    assert external_observation_ledger_sha256_v1(restored) == (
        external_observation_ledger_sha256_v1(ledger)
    )
    validate_external_observation_ledger_v1(restored)


def test_append_only_succession_preserves_old_observation_and_adds_new_one() -> None:
    first = _observation()
    predecessor = ExternalObservationLedger(
        subject_ref=SUBJECT,
        observations=(first,),
    )
    second = _observation(
        observation_id="obs-2",
        source_event_id="evt-2",
        observed_at=T0 + timedelta(minutes=1),
        captured_at=T0 + timedelta(minutes=1, seconds=1),
    )
    successor = admit_external_observation_v1(
        ledger=predecessor,
        observation=second,
    )

    receipt = validate_external_observation_ledger_successor_v1(
        predecessor=predecessor,
        successor=successor,
    )

    assert receipt.validator_issued is True
    assert receipt.retained_observation_ids == (first.observation_id,)
    assert receipt.added_observation_ids == (second.observation_id,)
    assert predecessor.observations[0] == successor.observations[0]


def test_unrelated_new_event_does_not_stale_or_mutate_old_observation() -> None:
    first = _observation()
    predecessor = ExternalObservationLedger(
        subject_ref=SUBJECT,
        observations=(first,),
    )
    old_digest = external_observation_sha256_v1(first)

    second = _observation(
        observation_id="obs-2",
        source_event_id="evt-2",
        observed_at=T0 + timedelta(hours=2),
        captured_at=T0 + timedelta(hours=2, seconds=1),
    )
    successor = admit_external_observation_v1(
        ledger=predecessor,
        observation=second,
    )
    validate_external_observation_ledger_successor_v1(
        predecessor=predecessor,
        successor=successor,
    )

    retained = next(
        item
        for item in successor.observations
        if item.observation_id == first.observation_id
    )
    assert external_observation_sha256_v1(retained) == old_digest


def test_declared_model_and_assistance_metadata_remain_metadata() -> None:
    observation = _observation(
        origin_kind=ExternalObservationOriginKind.MODEL,
    )

    assert observation.origin_kind is ExternalObservationOriginKind.MODEL
    assert {
        item.kind for item in observation.context_factors
    } == {
        ExternalObservationContextFactorKind.ASSISTANCE,
        ExternalObservationContextFactorKind.TOOL,
    }
    assert not hasattr(observation, "outcome")
    assert not hasattr(observation, "concept_ref")
    assert not hasattr(observation, "score")
