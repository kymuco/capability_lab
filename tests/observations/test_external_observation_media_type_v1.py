from capability_lab.observations import (
    ExternalObservationEnvelope,
    ExternalObservationPayloadRef,
    external_observation_sha256_v1,
)

from test_external_observation_v1 import _observation


def test_mime_parameter_value_case_is_preserved_exactly_across_round_trip() -> None:
    media_type = "multipart/form-data; boundary=AbC123"
    payload = ExternalObservationPayloadRef(
        ref="multipart-payload",
        sha256="d" * 64,
        byte_size=512,
        media_type=media_type,
    )
    observation = _observation(payload_refs=(payload,))

    restored = ExternalObservationEnvelope.from_json(observation.to_json())

    assert payload.media_type == media_type
    assert restored.payload_refs[0].media_type == media_type
    assert restored == observation
    assert external_observation_sha256_v1(restored) == (
        external_observation_sha256_v1(observation)
    )
