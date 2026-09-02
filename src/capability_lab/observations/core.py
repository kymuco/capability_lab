"""PR12.0 generic external observation envelope and immutable ledger v1."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import re
import unicodedata

from capability_lab.epistemics import CapabilitySubjectRef


class ExternalObservationError(ValueError):
    """Base error for PR12.0 external-observation governance."""


class InvalidExternalObservation(ExternalObservationError):
    pass


class InvalidExternalObservationLedger(ExternalObservationError):
    pass


_OPAQUE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_MEDIA_TYPE_RE = re.compile(
    r"^[A-Za-z0-9!#$&^_.+-]+/[A-Za-z0-9!#$&^_.+-]+(?:\s*;\s*[A-Za-z0-9!#$&^_.+-]+=[A-Za-z0-9!#$&^_.+:-]+)*$"
)
_OBSERVATION_HASH_DOMAIN = b"capability_lab/external_observation@1\x00"
_LEDGER_HASH_DOMAIN = b"capability_lab/external_observation_ledger@1\x00"


def _fail(message: str) -> None:
    raise InvalidExternalObservation(message)


def _ledger_fail(message: str) -> None:
    raise InvalidExternalObservationLedger(message)


def _exact(value: object, expected: type, label: str):
    if type(value) is not expected:
        _fail(f"{label} must use exact type {expected.__name__}")
    return value


def _opaque_id(value: object, label: str) -> str:
    if type(value) is not str or _OPAQUE_ID_RE.fullmatch(value) is None:
        _fail(f"{label} must be a canonical opaque ASCII identifier")
    return value


def _text(value: object, label: str) -> str:
    if type(value) is not str:
        _fail(f"{label} must be a string")
    cleaned = unicodedata.normalize("NFC", value).strip()
    if not cleaned:
        _fail(f"{label} must be non-empty")
    return cleaned


def _time(value: object, label: str) -> datetime:
    if type(value) is not datetime:
        _fail(f"{label} must use exact datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        _fail(f"{label} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _sha256(value: object, label: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        _fail(f"{label} must be 64 lowercase hexadecimal SHA-256 characters")
    return value


def _strict_subject(value: object, label: str) -> CapabilitySubjectRef:
    value = _exact(value, CapabilitySubjectRef, label)
    try:
        restored = CapabilitySubjectRef(value.value)
    except (TypeError, ValueError) as exc:
        raise InvalidExternalObservation(
            f"{label} must survive strict semantic reconstruction: {exc}"
        ) from exc
    if restored != value:
        _fail(f"{label} must equal strict semantic reconstruction")
    return value


@dataclass(frozen=True, order=True, slots=True)
class ExternalObservationId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _opaque_id(self.value, "external observation id"),
        )

    def __str__(self) -> str:
        return self.value


class ExternalObservationSourceKind(str, Enum):
    APPLICATION = "application"
    AGENT_RUNTIME = "agent_runtime"
    TOOL = "tool"
    EXTERNAL_SYSTEM = "external_system"
    ACTOR = "actor"
    OTHER = "other"


@dataclass(frozen=True, order=True, slots=True)
class ExternalObservationSourceRef:
    kind: ExternalObservationSourceKind
    ref: str

    def __post_init__(self) -> None:
        _exact(self.kind, ExternalObservationSourceKind, "source kind")
        object.__setattr__(self, "ref", _opaque_id(self.ref, "source ref"))

    @property
    def key(self) -> tuple[str, str]:
        return self.kind.value, self.ref


class ExternalObservationForm(str, Enum):
    EVENT = "event"
    TEXT = "text"
    ARTIFACT = "artifact"
    CONVERSATION = "conversation"
    BUNDLE = "bundle"
    OTHER = "other"


class ExternalObservationOriginKind(str, Enum):
    SUBJECT = "subject"
    OTHER_HUMAN = "other_human"
    MODEL = "model"
    SYSTEM = "system"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class ExternalObservationContextFactorKind(str, Enum):
    TOOL = "tool"
    ASSISTANCE = "assistance"
    ACCOMMODATION = "accommodation"
    COLLABORATION = "collaboration"
    REFERENCE_MATERIAL = "reference_material"
    AUTOMATION = "automation"
    ENVIRONMENT = "environment"
    OTHER = "other"


@dataclass(frozen=True, order=True, slots=True)
class ExternalObservationContextFactor:
    kind: ExternalObservationContextFactorKind
    description: str

    def __post_init__(self) -> None:
        _exact(
            self.kind,
            ExternalObservationContextFactorKind,
            "context factor kind",
        )
        object.__setattr__(
            self,
            "description",
            _text(self.description, "context factor description"),
        )


@dataclass(frozen=True, order=True, slots=True)
class ExternalObservationPayloadRef:
    ref: str
    sha256: str
    byte_size: int | None = None
    media_type: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "ref", _opaque_id(self.ref, "payload ref"))
        object.__setattr__(
            self,
            "sha256",
            _sha256(self.sha256, "payload sha256"),
        )
        if self.byte_size is not None:
            if type(self.byte_size) is not int or self.byte_size < 0:
                _fail("payload byte_size must be an integer >= 0 or None")
        if self.media_type is not None:
            if (
                type(self.media_type) is not str
                or _MEDIA_TYPE_RE.fullmatch(self.media_type) is None
            ):
                _fail("payload media_type must use canonical MIME type syntax")
            # Preserve exact validated spelling and parameter values. MIME
            # parameter values may be case-sensitive, so whole-string
            # lowercasing would silently change source metadata.


def _strict_observation_id(value: object) -> ExternalObservationId:
    value = _exact(value, ExternalObservationId, "observation_id")
    try:
        restored = ExternalObservationId(value.value)
    except (TypeError, ValueError) as exc:
        raise InvalidExternalObservation(
            f"observation_id must survive strict semantic reconstruction: {exc}"
        ) from exc
    if restored != value:
        _fail("observation_id must equal strict semantic reconstruction")
    return value


def _strict_source_ref(value: object) -> ExternalObservationSourceRef:
    value = _exact(value, ExternalObservationSourceRef, "source_ref")
    try:
        restored = ExternalObservationSourceRef(value.kind, value.ref)
    except (TypeError, ValueError) as exc:
        raise InvalidExternalObservation(
            f"source_ref must survive strict semantic reconstruction: {exc}"
        ) from exc
    if restored != value:
        _fail("source_ref must equal strict semantic reconstruction")
    return value


def _strict_context_factor(
    value: object,
) -> ExternalObservationContextFactor:
    value = _exact(
        value,
        ExternalObservationContextFactor,
        "context factor",
    )
    try:
        restored = ExternalObservationContextFactor(
            value.kind,
            value.description,
        )
    except (TypeError, ValueError) as exc:
        raise InvalidExternalObservation(
            f"context factor must survive strict semantic reconstruction: {exc}"
        ) from exc
    if restored != value:
        _fail("context factor must equal strict semantic reconstruction")
    return value


def _strict_payload_ref(value: object) -> ExternalObservationPayloadRef:
    value = _exact(value, ExternalObservationPayloadRef, "payload ref")
    try:
        restored = ExternalObservationPayloadRef(
            value.ref,
            value.sha256,
            value.byte_size,
            value.media_type,
        )
    except (TypeError, ValueError) as exc:
        raise InvalidExternalObservation(
            f"payload ref must survive strict semantic reconstruction: {exc}"
        ) from exc
    if restored != value:
        _fail("payload ref must equal strict semantic reconstruction")
    return value


@dataclass(frozen=True, slots=True)
class ExternalObservationEnvelope:
    observation_id: ExternalObservationId
    subject_ref: CapabilitySubjectRef
    source_ref: ExternalObservationSourceRef
    source_event_id: str
    form: ExternalObservationForm
    origin_kind: ExternalObservationOriginKind
    observed_at: datetime
    captured_at: datetime
    observation_started_at: datetime | None = None
    context_factors: tuple[ExternalObservationContextFactor, ...] = ()
    payload_refs: tuple[ExternalObservationPayloadRef, ...] = ()

    def __post_init__(self) -> None:
        _strict_observation_id(self.observation_id)
        _strict_subject(self.subject_ref, "subject_ref")
        _strict_source_ref(self.source_ref)
        object.__setattr__(
            self,
            "source_event_id",
            _opaque_id(self.source_event_id, "source_event_id"),
        )
        _exact(self.form, ExternalObservationForm, "form")
        _exact(
            self.origin_kind,
            ExternalObservationOriginKind,
            "origin_kind",
        )
        observed_at = _time(self.observed_at, "observed_at")
        captured_at = _time(self.captured_at, "captured_at")
        if captured_at < observed_at:
            _fail("captured_at must not precede observed_at")
        observation_started_at = None
        if self.observation_started_at is not None:
            observation_started_at = _time(
                self.observation_started_at,
                "observation_started_at",
            )
            if observation_started_at > observed_at:
                _fail(
                    "observation_started_at must not follow observed_at"
                )

        if type(self.context_factors) is not tuple:
            _fail("context_factors must be exact tuple")
        if any(
            type(item) is not ExternalObservationContextFactor
            for item in self.context_factors
        ):
            _fail(
                "context_factors must contain exact "
                "ExternalObservationContextFactor values"
            )
        factors = tuple(_strict_context_factor(item) for item in self.context_factors)
        if len(set(factors)) != len(factors):
            _fail("context_factors must not contain duplicates")

        if type(self.payload_refs) is not tuple:
            _fail("payload_refs must be exact tuple")
        if any(
            type(item) is not ExternalObservationPayloadRef
            for item in self.payload_refs
        ):
            _fail(
                "payload_refs must contain exact "
                "ExternalObservationPayloadRef values"
            )
        payloads = tuple(_strict_payload_ref(item) for item in self.payload_refs)
        if len({item.ref for item in payloads}) != len(payloads):
            _fail("payload_refs must not reuse payload ref identity")
        if (
            self.form
            in {
                ExternalObservationForm.TEXT,
                ExternalObservationForm.ARTIFACT,
                ExternalObservationForm.CONVERSATION,
                ExternalObservationForm.BUNDLE,
            }
            and not payloads
        ):
            _fail(
                f"{self.form.value} observations require at least one payload ref"
            )

        object.__setattr__(self, "observed_at", observed_at)
        object.__setattr__(self, "captured_at", captured_at)
        object.__setattr__(
            self,
            "observation_started_at",
            observation_started_at,
        )
        object.__setattr__(
            self,
            "context_factors",
            tuple(
                sorted(
                    factors,
                    key=lambda item: (
                        item.kind.value,
                        item.description,
                    ),
                )
            ),
        )
        object.__setattr__(
            self,
            "payload_refs",
            tuple(sorted(payloads, key=lambda item: item.ref)),
        )

    @property
    def source_event_key(self) -> tuple[ExternalObservationSourceRef, str]:
        return self.source_ref, self.source_event_id

    def to_dict(self) -> dict:
        from .serialization import external_observation_to_dict

        return external_observation_to_dict(self)

    @classmethod
    def from_dict(cls, payload: object) -> "ExternalObservationEnvelope":
        from .serialization import external_observation_from_dict

        return external_observation_from_dict(payload)

    def to_json(self) -> str:
        from .serialization import external_observation_to_json

        return external_observation_to_json(self)

    @classmethod
    def from_json(cls, payload: object) -> "ExternalObservationEnvelope":
        from .serialization import external_observation_from_json

        return external_observation_from_json(payload)


def validate_external_observation_v1(
    observation: ExternalObservationEnvelope,
) -> None:
    if type(observation) is not ExternalObservationEnvelope:
        _fail("observation must use exact ExternalObservationEnvelope")
    try:
        restored = ExternalObservationEnvelope(
            observation_id=observation.observation_id,
            subject_ref=observation.subject_ref,
            source_ref=observation.source_ref,
            source_event_id=observation.source_event_id,
            form=observation.form,
            origin_kind=observation.origin_kind,
            observed_at=observation.observed_at,
            captured_at=observation.captured_at,
            observation_started_at=observation.observation_started_at,
            context_factors=observation.context_factors,
            payload_refs=observation.payload_refs,
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InvalidExternalObservation):
            raise
        raise InvalidExternalObservation(
            f"observation failed strict semantic reconstruction: {exc}"
        ) from exc
    if restored != observation:
        _fail("observation must equal strict semantic reconstruction")


def external_observation_sha256_v1(
    observation: ExternalObservationEnvelope,
) -> str:
    validate_external_observation_v1(observation)
    from .serialization import external_observation_to_json

    digest = hashlib.sha256()
    digest.update(_OBSERVATION_HASH_DOMAIN)
    digest.update(external_observation_to_json(observation).encode("utf-8"))
    return digest.hexdigest()


@dataclass(frozen=True, slots=True)
class ExternalObservationLedger:
    subject_ref: CapabilitySubjectRef
    observations: tuple[ExternalObservationEnvelope, ...] = ()

    def __post_init__(self) -> None:
        try:
            subject_ref = _strict_subject(self.subject_ref, "ledger subject_ref")
        except InvalidExternalObservation as exc:
            raise InvalidExternalObservationLedger(str(exc)) from exc
        if type(self.observations) is not tuple:
            _ledger_fail("observations must be exact tuple")
        if any(
            type(item) is not ExternalObservationEnvelope
            for item in self.observations
        ):
            _ledger_fail(
                "observations must contain exact ExternalObservationEnvelope values"
            )
        for item in self.observations:
            try:
                validate_external_observation_v1(item)
            except InvalidExternalObservation as exc:
                raise InvalidExternalObservationLedger(
                    f"ledger contains invalid observation: {exc}"
                ) from exc
            if item.subject_ref != subject_ref:
                _ledger_fail(
                    "every observation subject_ref must match ledger subject_ref"
                )

        observation_ids = tuple(
            item.observation_id for item in self.observations
        )
        if len(set(observation_ids)) != len(observation_ids):
            _ledger_fail("observation_id values must be unique")

        source_event_keys = tuple(
            item.source_event_key for item in self.observations
        )
        if len(set(source_event_keys)) != len(source_event_keys):
            _ledger_fail(
                "each exact source_ref/source_event_id identity may appear once"
            )

        object.__setattr__(self, "subject_ref", subject_ref)
        object.__setattr__(
            self,
            "observations",
            tuple(
                sorted(
                    self.observations,
                    key=lambda item: item.observation_id,
                )
            ),
        )

    def to_dict(self) -> dict:
        from .serialization import external_observation_ledger_to_dict

        return external_observation_ledger_to_dict(self)

    @classmethod
    def from_dict(cls, payload: object) -> "ExternalObservationLedger":
        from .serialization import external_observation_ledger_from_dict

        return external_observation_ledger_from_dict(payload)

    def to_json(self) -> str:
        from .serialization import external_observation_ledger_to_json

        return external_observation_ledger_to_json(self)

    @classmethod
    def from_json(cls, payload: object) -> "ExternalObservationLedger":
        from .serialization import external_observation_ledger_from_json

        return external_observation_ledger_from_json(payload)


def validate_external_observation_ledger_v1(
    ledger: ExternalObservationLedger,
) -> None:
    if type(ledger) is not ExternalObservationLedger:
        _ledger_fail("ledger must use exact ExternalObservationLedger")
    try:
        restored = ExternalObservationLedger(
            subject_ref=ledger.subject_ref,
            observations=ledger.observations,
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InvalidExternalObservationLedger):
            raise
        raise InvalidExternalObservationLedger(
            f"ledger failed strict semantic reconstruction: {exc}"
        ) from exc
    if restored != ledger:
        _ledger_fail("ledger must equal strict semantic reconstruction")


def external_observation_ledger_sha256_v1(
    ledger: ExternalObservationLedger,
) -> str:
    validate_external_observation_ledger_v1(ledger)
    from .serialization import external_observation_ledger_to_json

    digest = hashlib.sha256()
    digest.update(_LEDGER_HASH_DOMAIN)
    digest.update(
        external_observation_ledger_to_json(ledger).encode("utf-8")
    )
    return digest.hexdigest()


def admit_external_observation_v1(
    *,
    ledger: ExternalObservationLedger,
    observation: ExternalObservationEnvelope,
) -> ExternalObservationLedger:
    """Idempotently admit one exact source event into one subject ledger."""

    validate_external_observation_ledger_v1(ledger)
    validate_external_observation_v1(observation)
    if observation.subject_ref != ledger.subject_ref:
        _ledger_fail(
            "observation subject_ref must match ledger subject_ref"
        )

    by_source_event = {
        item.source_event_key: item for item in ledger.observations
    }
    existing = by_source_event.get(observation.source_event_key)
    if existing is not None:
        if (
            external_observation_sha256_v1(existing)
            == external_observation_sha256_v1(observation)
            and existing == observation
        ):
            return ledger
        _ledger_fail(
            "source_ref/source_event_id identity is already bound to "
            "different observation content"
        )

    by_observation_id = {
        item.observation_id: item for item in ledger.observations
    }
    existing = by_observation_id.get(observation.observation_id)
    if existing is not None:
        if (
            external_observation_sha256_v1(existing)
            == external_observation_sha256_v1(observation)
            and existing == observation
        ):
            return ledger
        _ledger_fail(
            "observation_id is already bound to different observation content"
        )

    return ExternalObservationLedger(
        subject_ref=ledger.subject_ref,
        observations=ledger.observations + (observation,),
    )