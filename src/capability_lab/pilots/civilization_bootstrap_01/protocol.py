"""Civilization Bootstrap Pilot 01 protocol semantics.

PR10.0 defines the participant-facing protocol only. It deliberately does not
contain evaluation thresholds, answer keys, state bindings, or recommendation
logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
import unicodedata

from capability_lab.semantics import CapabilityConceptRef
from capability_lab.state import CompetenceFrameRef


class PilotProtocolError(ValueError):
    """Base validation error for pilot protocol records."""


class InvalidPilotProtocol(PilotProtocolError):
    pass


_REF_RE = re.compile(
    r"^([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*):"
    r"([a-z][a-z0-9_]*)@([1-9][0-9]*)$"
)
_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def _clean_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise InvalidPilotProtocol(f"{field_name} must be a string")
    cleaned = unicodedata.normalize("NFC", value).strip()
    if not cleaned:
        raise InvalidPilotProtocol(f"{field_name} must be non-empty")
    return cleaned


def _key(value: object, field_name: str) -> str:
    if not isinstance(value, str) or _KEY_RE.fullmatch(value) is None:
        raise InvalidPilotProtocol(f"{field_name} must use canonical lowercase key syntax")
    return value


@dataclass(frozen=True, order=True, slots=True)
class PilotProtocolRef:
    namespace: str
    key: str
    revision: int

    def __post_init__(self) -> None:
        if not isinstance(self.namespace, str) or not self.namespace:
            raise InvalidPilotProtocol("protocol namespace must be non-empty")
        if not re.fullmatch(r"[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*", self.namespace):
            raise InvalidPilotProtocol("protocol namespace must use canonical namespace syntax")
        _key(self.key, "protocol key")
        if isinstance(self.revision, bool) or not isinstance(self.revision, int) or self.revision < 1:
            raise InvalidPilotProtocol("protocol revision must be an integer >= 1")

    @classmethod
    def parse(cls, value: object) -> "PilotProtocolRef":
        if not isinstance(value, str):
            raise InvalidPilotProtocol("protocol ref must be a string")
        match = _REF_RE.fullmatch(value)
        if match is None:
            raise InvalidPilotProtocol("protocol ref must use '<namespace>:<key>@<revision>'")
        return cls(match.group(1), match.group(2), int(match.group(3)))

    def __str__(self) -> str:
        return f"{self.namespace}:{self.key}@{self.revision}"


class PilotCaptureKind(str, Enum):
    TEXT_RESPONSE = "TEXT_RESPONSE"
    FILE_ARTIFACT = "FILE_ARTIFACT"


class PilotProbeRequirement(str, Enum):
    REQUIRED = "REQUIRED"
    OPTIONAL = "OPTIONAL"


@dataclass(frozen=True, slots=True)
class PilotProbeDefinition:
    probe_id: str
    title: str
    requirement: PilotProbeRequirement
    allowed_capture_kinds: tuple[PilotCaptureKind, ...]
    participant_prompt: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "probe_id", _key(self.probe_id, "probe id"))
        object.__setattr__(self, "title", _clean_text(self.title, "probe title"))
        if not isinstance(self.requirement, PilotProbeRequirement):
            raise InvalidPilotProtocol("probe requirement must be PilotProbeRequirement")
        if not isinstance(self.allowed_capture_kinds, tuple) or not self.allowed_capture_kinds:
            raise InvalidPilotProtocol("probe allowed_capture_kinds must be a non-empty tuple")
        if any(not isinstance(item, PilotCaptureKind) for item in self.allowed_capture_kinds):
            raise InvalidPilotProtocol("probe allowed_capture_kinds must contain PilotCaptureKind values")
        if len(set(self.allowed_capture_kinds)) != len(self.allowed_capture_kinds):
            raise InvalidPilotProtocol("probe allowed_capture_kinds must not contain duplicates")
        object.__setattr__(
            self,
            "participant_prompt",
            _clean_text(self.participant_prompt, "participant prompt"),
        )


@dataclass(frozen=True, slots=True)
class PilotProtocol:
    protocol_ref: PilotProtocolRef
    title: str
    description: str
    capability_ref: CapabilityConceptRef
    frame_ref: CompetenceFrameRef
    participant_instructions: tuple[str, ...]
    privacy_boundaries: tuple[str, ...]
    physical_boundaries: tuple[str, ...]
    probes: tuple[PilotProbeDefinition, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.protocol_ref, PilotProtocolRef):
            raise InvalidPilotProtocol("protocol_ref must be PilotProtocolRef")
        object.__setattr__(self, "title", _clean_text(self.title, "protocol title"))
        object.__setattr__(self, "description", _clean_text(self.description, "protocol description"))
        if not isinstance(self.capability_ref, CapabilityConceptRef):
            raise InvalidPilotProtocol("capability_ref must be CapabilityConceptRef")
        if not isinstance(self.frame_ref, CompetenceFrameRef):
            raise InvalidPilotProtocol("frame_ref must be CompetenceFrameRef")
        for field_name in ("participant_instructions", "privacy_boundaries", "physical_boundaries"):
            values = getattr(self, field_name)
            if not isinstance(values, tuple) or not values:
                raise InvalidPilotProtocol(f"{field_name} must be a non-empty tuple")
            cleaned = tuple(_clean_text(item, field_name) for item in values)
            if len(set(cleaned)) != len(cleaned):
                raise InvalidPilotProtocol(f"{field_name} must not contain duplicates")
            object.__setattr__(self, field_name, cleaned)
        if not isinstance(self.probes, tuple) or not self.probes:
            raise InvalidPilotProtocol("probes must be a non-empty tuple")
        if any(not isinstance(item, PilotProbeDefinition) for item in self.probes):
            raise InvalidPilotProtocol("probes must contain PilotProbeDefinition values")
        probe_ids = tuple(item.probe_id for item in self.probes)
        if len(set(probe_ids)) != len(probe_ids):
            raise InvalidPilotProtocol("probe ids must be unique")

    def probe(self, probe_id: str) -> PilotProbeDefinition:
        key = _key(probe_id, "probe id")
        for probe in self.probes:
            if probe.probe_id == key:
                return probe
        raise InvalidPilotProtocol(f"unknown probe id: {key}")

    @property
    def required_probe_ids(self) -> tuple[str, ...]:
        return tuple(
            probe.probe_id
            for probe in self.probes
            if probe.requirement is PilotProbeRequirement.REQUIRED
        )


CIVILIZATION_BOOTSTRAP_PILOT_01_PROTOCOL_REF = PilotProtocolRef(
    "civilization_bootstrap", "pilot_01_basic_electricity", 1
)


def build_civilization_bootstrap_pilot_01_protocol_v1() -> PilotProtocol:
    """Return the frozen participant-facing Pilot 01 protocol."""

    return PilotProtocol(
        protocol_ref=CIVILIZATION_BOOTSTRAP_PILOT_01_PROTOCOL_REF,
        title="Civilization Bootstrap Pilot 01 — Basic Electricity",
        description=(
            "A first real one-subject Capability Lab pilot over bounded basic-electricity work. "
            "The protocol captures what the participant actually produces; it does not contain "
            "grading thresholds, answer keys, capability-state conclusions, or recommendations."
        ),
        capability_ref=CapabilityConceptRef.parse("civilization_bootstrap:basic_electricity@1"),
        frame_ref=CompetenceFrameRef.parse("civilization_bootstrap:technical_competence@1"),
        participant_instructions=(
            "Respond naturally rather than optimizing for what you think Capability Lab wants to see.",
            "State assumptions, uncertainty, and any tools or references you actually used.",
            "Do not use a prepared answer key supplied by the pilot; this protocol intentionally contains none.",
            "Skipping the optional execution probe is allowed and remains unobserved rather than a failed attempt.",
        ),
        privacy_boundaries=(
            "Protocol code and schemas may be versioned; participant responses and artifacts are private by default.",
            "A local capture is not automatically an EvidenceRecord, claim, evaluation, state, achievement, or frontier input.",
            "Copying or sharing a private workspace is a data export; this protocol does not grant publication permission.",
            "Declared subject-provided origin is provenance metadata, not authentication of human authorship.",
        ),
        physical_boundaries=(
            "Use only ordinary bounded low-voltage DC contexts suitable for the participant's existing equipment and experience.",
            "Do not work on mains wiring, high-voltage systems, opened power supplies, or unknown energized systems.",
            "The pilot protocol is not a safety certification or permission to perform electrical work.",
        ),
        probes=(
            PilotProbeDefinition(
                probe_id="conceptual_explanation",
                title="Conceptual explanation",
                requirement=PilotProbeRequirement.REQUIRED,
                allowed_capture_kinds=(PilotCaptureKind.TEXT_RESPONSE,),
                participant_prompt=(
                    "Without using a prepared answer, explain in your own words how voltage, current, and resistance relate "
                    "in a simple low-voltage DC circuit. Include Ohm's law, what changes when voltage increases at fixed "
                    "resistance, what changes when resistance increases at fixed voltage, and one concrete example. "
                    "State your assumptions and any uncertainty."
                ),
            ),
            PilotProbeDefinition(
                probe_id="calculation_work",
                title="Calculation work",
                requirement=PilotProbeRequirement.REQUIRED,
                allowed_capture_kinds=(PilotCaptureKind.TEXT_RESPONSE,),
                participant_prompt=(
                    "Show your work for each bounded calculation: (1) 5.0 V across 1.0 kΩ — current; "
                    "(2) a 9.0 V source, a stated 2.0 V LED drop, and a 330 Ω series resistor — resistor current under "
                    "that idealized assumption; (3) a 5.0 V source with 100 Ω and 220 Ω in series — total current and "
                    "voltage drop across each resistor; (4) 12.0 V across 1.0 kΩ — resistor power. Calculators are allowed "
                    "if you declare their use."
                ),
            ),
            PilotProbeDefinition(
                probe_id="diagnosis_reasoning",
                title="Diagnosis reasoning",
                requirement=PilotProbeRequirement.REQUIRED,
                allowed_capture_kinds=(PilotCaptureKind.TEXT_RESPONSE,),
                participant_prompt=(
                    "A 5 V battery-powered LED circuit that previously worked no longer lights. It contains a source, "
                    "switch, series resistor, LED, and wires. Describe a safe diagnostic sequence using visual inspection "
                    "and a multimeter. Explain what you would measure, in what order, how each result would change your "
                    "next step, and at least three plausible fault hypotheses. Do not work on mains or unknown energized systems."
                ),
            ),
            PilotProbeDefinition(
                probe_id="execution_artifact",
                title="Optional low-voltage execution artifact",
                requirement=PilotProbeRequirement.OPTIONAL,
                allowed_capture_kinds=(PilotCaptureKind.TEXT_RESPONSE, PilotCaptureKind.FILE_ARTIFACT),
                participant_prompt=(
                    "If you already have appropriate low-voltage components and can work within the protocol boundary, "
                    "assemble or inspect a simple battery- or USB-powered DC circuit and preserve your own photos or "
                    "measurement notes as captures. Do not use mains, high-voltage systems, opened power supplies, or "
                    "unknown energized systems. If suitable equipment is unavailable, skip this probe."
                ),
            ),
        ),
    )
