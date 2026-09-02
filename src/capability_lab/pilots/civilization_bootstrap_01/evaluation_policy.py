"""Pilot 01 claim-scope and human evaluation-policy specification.

PR11.0 defines what may be claimed and how reviewed Pilot 01 evidence may bear
on those claims. It deliberately does not create CapabilityClaim,
ClaimEvaluation, PersonalCapabilityState, or any downstream authority-bearing
record.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import re
import unicodedata

from capability_lab.epistemics import (
    ClaimScope,
    EvaluationPolicyRef,
    EvidenceBearing,
)
from capability_lab.semantics import CapabilityConceptRef

from .protocol import (
    CIVILIZATION_BOOTSTRAP_PILOT_01_PROTOCOL_REF,
    PilotProbeRequirement,
    PilotProtocol,
    PilotProtocolRef,
    build_civilization_bootstrap_pilot_01_protocol_v1,
)


class PilotEvaluationPolicyError(ValueError):
    """Base validation error for PR11.0 Pilot 01 evaluation policy."""


class InvalidPilotEvaluationPolicy(PilotEvaluationPolicyError):
    pass


_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_POLICY_HASH_DOMAIN = (
    b"capability_lab/civilization_bootstrap_pilot_01_evaluation_policy@1\x00"
)
PILOT_EVALUATION_POLICY_SCHEMA_V1 = (
    "civilization_bootstrap_pilot_01_evaluation_policy/v1"
)


def _clean_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise InvalidPilotEvaluationPolicy(f"{field_name} must be a string")
    cleaned = unicodedata.normalize("NFC", value).strip()
    if not cleaned:
        raise InvalidPilotEvaluationPolicy(f"{field_name} must be non-empty")
    return cleaned


def _key(value: object, field_name: str) -> str:
    if not isinstance(value, str) or _KEY_RE.fullmatch(value) is None:
        raise InvalidPilotEvaluationPolicy(
            f"{field_name} must use canonical lowercase key syntax"
        )
    return value


def _text_tuple(
    value: object,
    field_name: str,
    *,
    allow_empty: bool = False,
    key: bool = False,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise InvalidPilotEvaluationPolicy(
            f"{field_name} must be an iterable, not a string"
        )
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise InvalidPilotEvaluationPolicy(f"{field_name} must be iterable") from exc
    if not items and not allow_empty:
        raise InvalidPilotEvaluationPolicy(f"{field_name} must be non-empty")
    cleaned = tuple(
        _key(item, field_name) if key else _clean_text(item, field_name)
        for item in items
    )
    if len(set(cleaned)) != len(cleaned):
        raise InvalidPilotEvaluationPolicy(f"{field_name} must not contain duplicates")
    return cleaned


class PilotMissingProbeSemantics(str, Enum):
    REQUIRED_COVERAGE_GAP = "REQUIRED_COVERAGE_GAP"
    OPTIONAL_UNOBSERVED = "OPTIONAL_UNOBSERVED"


@dataclass(frozen=True, slots=True)
class PilotClaimTemplate:
    """Subject-free exact proposition template; not a CapabilityClaim record."""

    claim_key: str
    concept_ref: CapabilityConceptRef
    statement: str
    scope: ClaimScope
    sufficiency_probe_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "claim_key", _key(self.claim_key, "claim_key"))
        if not isinstance(self.concept_ref, CapabilityConceptRef):
            raise InvalidPilotEvaluationPolicy(
                "claim concept_ref must be exact CapabilityConceptRef"
            )
        object.__setattr__(
            self,
            "statement",
            _clean_text(self.statement, "claim statement"),
        )
        if not isinstance(self.scope, ClaimScope):
            raise InvalidPilotEvaluationPolicy("claim scope must be ClaimScope")
        object.__setattr__(
            self,
            "sufficiency_probe_ids",
            _text_tuple(
                self.sufficiency_probe_ids,
                "claim sufficiency_probe_ids",
                key=True,
            ),
        )


@dataclass(frozen=True, slots=True)
class PilotRubricCriterion:
    criterion_id: str
    requirement: str
    acceptable_variations: tuple[str, ...] = ()
    material_error_conditions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "criterion_id",
            _key(self.criterion_id, "criterion_id"),
        )
        object.__setattr__(
            self,
            "requirement",
            _clean_text(self.requirement, "criterion requirement"),
        )
        object.__setattr__(
            self,
            "acceptable_variations",
            _text_tuple(
                self.acceptable_variations,
                "criterion acceptable_variations",
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "material_error_conditions",
            _text_tuple(
                self.material_error_conditions,
                "criterion material_error_conditions",
                allow_empty=True,
            ),
        )


@dataclass(frozen=True, order=True, slots=True)
class PilotEvidenceBearingGuidance:
    bearing: EvidenceBearing
    condition: str

    def __post_init__(self) -> None:
        if not isinstance(self.bearing, EvidenceBearing):
            raise InvalidPilotEvaluationPolicy(
                "bearing guidance bearing must be EvidenceBearing"
            )
        object.__setattr__(
            self,
            "condition",
            _clean_text(self.condition, "bearing guidance condition"),
        )


@dataclass(frozen=True, slots=True)
class PilotProbeEvaluationRubric:
    probe_id: str
    claim_key: str
    criteria: tuple[PilotRubricCriterion, ...]
    bearing_guidance: tuple[PilotEvidenceBearingGuidance, ...]
    missing_probe_semantics: PilotMissingProbeSemantics

    def __post_init__(self) -> None:
        object.__setattr__(self, "probe_id", _key(self.probe_id, "probe_id"))
        object.__setattr__(self, "claim_key", _key(self.claim_key, "claim_key"))
        if not isinstance(self.criteria, tuple) or not self.criteria:
            raise InvalidPilotEvaluationPolicy(
                "probe rubric criteria must be a non-empty tuple"
            )
        if any(not isinstance(item, PilotRubricCriterion) for item in self.criteria):
            raise InvalidPilotEvaluationPolicy(
                "probe rubric criteria must contain PilotRubricCriterion values"
            )
        criterion_ids = tuple(item.criterion_id for item in self.criteria)
        if len(set(criterion_ids)) != len(criterion_ids):
            raise InvalidPilotEvaluationPolicy(
                "probe rubric criterion ids must be unique"
            )
        if (
            not isinstance(self.bearing_guidance, tuple)
            or len(self.bearing_guidance) != len(EvidenceBearing)
        ):
            raise InvalidPilotEvaluationPolicy(
                "probe rubric must define exactly one guidance entry for every EvidenceBearing"
            )
        if any(
            not isinstance(item, PilotEvidenceBearingGuidance)
            for item in self.bearing_guidance
        ):
            raise InvalidPilotEvaluationPolicy(
                "bearing_guidance must contain PilotEvidenceBearingGuidance values"
            )
        bearings = tuple(item.bearing for item in self.bearing_guidance)
        if set(bearings) != set(EvidenceBearing) or len(set(bearings)) != len(bearings):
            raise InvalidPilotEvaluationPolicy(
                "probe rubric bearing guidance must cover each EvidenceBearing exactly once"
            )
        object.__setattr__(
            self,
            "bearing_guidance",
            tuple(sorted(self.bearing_guidance)),
        )
        if not isinstance(self.missing_probe_semantics, PilotMissingProbeSemantics):
            raise InvalidPilotEvaluationPolicy(
                "missing_probe_semantics must be PilotMissingProbeSemantics"
            )

    def guidance_for(self, bearing: EvidenceBearing) -> PilotEvidenceBearingGuidance:
        if not isinstance(bearing, EvidenceBearing):
            raise InvalidPilotEvaluationPolicy("bearing must be EvidenceBearing")
        for guidance in self.bearing_guidance:
            if guidance.bearing is bearing:
                return guidance
        raise AssertionError("validated rubric must contain every EvidenceBearing")


@dataclass(frozen=True, slots=True)
class PilotHumanEvaluationPolicy:
    policy_ref: EvaluationPolicyRef
    protocol_ref: PilotProtocolRef
    claims: tuple[PilotClaimTemplate, ...]
    probe_rubrics: tuple[PilotProbeEvaluationRubric, ...]
    reliability_rule: str
    coverage_rule: str
    dependence_rule: str
    authority_boundaries: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.policy_ref, EvaluationPolicyRef):
            raise InvalidPilotEvaluationPolicy(
                "policy_ref must be EvaluationPolicyRef"
            )
        if not isinstance(self.protocol_ref, PilotProtocolRef):
            raise InvalidPilotEvaluationPolicy("protocol_ref must be PilotProtocolRef")
        if not isinstance(self.claims, tuple) or not self.claims:
            raise InvalidPilotEvaluationPolicy("claims must be a non-empty tuple")
        if any(not isinstance(item, PilotClaimTemplate) for item in self.claims):
            raise InvalidPilotEvaluationPolicy(
                "claims must contain PilotClaimTemplate values"
            )
        claim_keys = tuple(item.claim_key for item in self.claims)
        if len(set(claim_keys)) != len(claim_keys):
            raise InvalidPilotEvaluationPolicy("claim keys must be unique")
        if not isinstance(self.probe_rubrics, tuple) or not self.probe_rubrics:
            raise InvalidPilotEvaluationPolicy(
                "probe_rubrics must be a non-empty tuple"
            )
        if any(
            not isinstance(item, PilotProbeEvaluationRubric)
            for item in self.probe_rubrics
        ):
            raise InvalidPilotEvaluationPolicy(
                "probe_rubrics must contain PilotProbeEvaluationRubric values"
            )
        probe_ids = tuple(item.probe_id for item in self.probe_rubrics)
        if len(set(probe_ids)) != len(probe_ids):
            raise InvalidPilotEvaluationPolicy("probe rubric probe_ids must be unique")
        unknown_claim_keys = {
            item.claim_key for item in self.probe_rubrics
        } - set(claim_keys)
        if unknown_claim_keys:
            raise InvalidPilotEvaluationPolicy(
                "probe rubric references unknown claim_key"
            )
        rubric_by_probe = {item.probe_id: item for item in self.probe_rubrics}
        for claim in self.claims:
            for probe_id in claim.sufficiency_probe_ids:
                rubric = rubric_by_probe.get(probe_id)
                if rubric is None or rubric.claim_key != claim.claim_key:
                    raise InvalidPilotEvaluationPolicy(
                        "every claim sufficiency probe must have a rubric bound to that claim"
                    )
        object.__setattr__(
            self,
            "reliability_rule",
            _clean_text(self.reliability_rule, "reliability_rule"),
        )
        object.__setattr__(
            self,
            "coverage_rule",
            _clean_text(self.coverage_rule, "coverage_rule"),
        )
        object.__setattr__(
            self,
            "dependence_rule",
            _clean_text(self.dependence_rule, "dependence_rule"),
        )
        object.__setattr__(
            self,
            "authority_boundaries",
            _text_tuple(
                self.authority_boundaries,
                "authority_boundaries",
            ),
        )

    def claim(self, claim_key: str) -> PilotClaimTemplate:
        key = _key(claim_key, "claim_key")
        for claim in self.claims:
            if claim.claim_key == key:
                return claim
        raise InvalidPilotEvaluationPolicy(f"unknown claim_key: {key}")

    def rubric(self, probe_id: str) -> PilotProbeEvaluationRubric:
        key = _key(probe_id, "probe_id")
        for rubric in self.probe_rubrics:
            if rubric.probe_id == key:
                return rubric
        raise InvalidPilotEvaluationPolicy(f"unknown probe_id: {key}")


CIVILIZATION_BOOTSTRAP_PILOT_01_EVALUATION_POLICY_REF_V1 = EvaluationPolicyRef(
    "civilization_bootstrap",
    "pilot_01_basic_electricity_human_review",
    1,
)

PILOT_01_REASONING_CLAIM_KEY = "bounded_reasoning"
PILOT_01_EXECUTION_CLAIM_KEY = "bounded_execution"


def _bearing_guidance(
    *,
    supports: str,
    contradicts: str,
    indeterminate: str,
    not_relevant: str,
) -> tuple[PilotEvidenceBearingGuidance, ...]:
    return (
        PilotEvidenceBearingGuidance(EvidenceBearing.SUPPORTS, supports),
        PilotEvidenceBearingGuidance(EvidenceBearing.CONTRADICTS, contradicts),
        PilotEvidenceBearingGuidance(
            EvidenceBearing.INDETERMINATE,
            indeterminate,
        ),
        PilotEvidenceBearingGuidance(
            EvidenceBearing.NOT_RELEVANT,
            not_relevant,
        ),
    )


def build_civilization_bootstrap_pilot_01_evaluation_policy_v1(
) -> PilotHumanEvaluationPolicy:
    """Return the frozen PR11.0 human evaluation-policy specification."""

    capability_ref = CapabilityConceptRef.parse(
        "civilization_bootstrap:basic_electricity@1"
    )
    reasoning_claim = PilotClaimTemplate(
        claim_key=PILOT_01_REASONING_CLAIM_KEY,
        concept_ref=capability_ref,
        statement=(
            "Within the bounded low-voltage DC scope represented by Pilot 01, "
            "the subject can explain basic voltage/current/resistance relationships, "
            "perform the protocol's bounded circuit calculations, and reason through "
            "a safe diagnostic sequence for a simple DC circuit."
        ),
        scope=ClaimScope(
            description=(
                "Pilot 01 low-voltage DC conceptual explanation, bounded calculations, "
                "and diagnosis reasoning only; excludes mains, high voltage, certification, "
                "general electronics mastery, and practical execution not actually observed."
            ),
            tags=(
                "basic_electricity",
                "calculation",
                "conceptual_reasoning",
                "diagnosis",
                "low_voltage_dc",
                "pilot_01",
            ),
        ),
        sufficiency_probe_ids=(
            "conceptual_explanation",
            "calculation_work",
            "diagnosis_reasoning",
        ),
    )
    execution_claim = PilotClaimTemplate(
        claim_key=PILOT_01_EXECUTION_CLAIM_KEY,
        concept_ref=capability_ref,
        statement=(
            "Within the bounded low-voltage DC scope represented by Pilot 01, "
            "the subject can carry out or inspect a simple battery- or USB-powered DC "
            "circuit task while preserving relevant observations or measurements."
        ),
        scope=ClaimScope(
            description=(
                "Only practical low-voltage DC execution actually represented by the "
                "optional execution_artifact probe; absence of that optional observation "
                "is unobserved, not failure or contradiction."
            ),
            tags=(
                "basic_electricity",
                "execution",
                "low_voltage_dc",
                "pilot_01",
            ),
        ),
        sufficiency_probe_ids=("execution_artifact",),
    )

    conceptual = PilotProbeEvaluationRubric(
        probe_id="conceptual_explanation",
        claim_key=PILOT_01_REASONING_CLAIM_KEY,
        criteria=(
            PilotRubricCriterion(
                criterion_id="ohms_law_relationship",
                requirement=(
                    "States or correctly explains V = I * R and distinguishes voltage, "
                    "current, and resistance as different quantities."
                ),
                acceptable_variations=(
                    "Equivalent algebraic forms such as I = V / R or R = V / I are acceptable.",
                    "An intuitive analogy is acceptable when the electrical relationship remains correct.",
                ),
                material_error_conditions=(
                    "Treats voltage, current, and resistance as interchangeable quantities.",
                    "States a relationship incompatible with Ohm's law for the stated idealized resistor context.",
                ),
            ),
            PilotRubricCriterion(
                criterion_id="fixed_resistance_voltage_change",
                requirement=(
                    "Explains that increasing voltage at fixed resistance increases current."
                ),
                material_error_conditions=(
                    "Claims current decreases when voltage increases at fixed resistance.",
                ),
            ),
            PilotRubricCriterion(
                criterion_id="fixed_voltage_resistance_change",
                requirement=(
                    "Explains that increasing resistance at fixed voltage decreases current."
                ),
                material_error_conditions=(
                    "Claims current increases when resistance increases at fixed voltage.",
                ),
            ),
            PilotRubricCriterion(
                criterion_id="concrete_example",
                requirement=(
                    "Provides one internally consistent concrete low-voltage DC example."
                ),
                acceptable_variations=(
                    "Any safe bounded numeric or qualitative example consistent with the stated relationships is acceptable.",
                ),
            ),
            PilotRubricCriterion(
                criterion_id="assumptions_and_uncertainty",
                requirement=(
                    "Makes material assumptions or uncertainty explicit when they affect the explanation."
                ),
                acceptable_variations=(
                    "An explicit statement that no material uncertainty remains is acceptable when the explanation is otherwise bounded.",
                ),
            ),
        ),
        bearing_guidance=_bearing_guidance(
            supports=(
                "Use SUPPORTS only when the response materially satisfies the scoped conceptual requirements without a material contradiction."
            ),
            contradicts=(
                "Use CONTRADICTS only for an observed substantive misconception that directly conflicts with the scoped proposition; omission alone is not contradiction."
            ),
            indeterminate=(
                "Use INDETERMINATE when the response is ambiguous, materially incomplete, internally inconsistent, or cannot be interpreted confidently under the rubric."
            ),
            not_relevant=(
                "Use NOT_RELEVANT when the material does not actually address the conceptual_explanation probe or falls outside the bounded claim scope."
            ),
        ),
        missing_probe_semantics=PilotMissingProbeSemantics.REQUIRED_COVERAGE_GAP,
    )

    calculation = PilotProbeEvaluationRubric(
        probe_id="calculation_work",
        claim_key=PILOT_01_REASONING_CLAIM_KEY,
        criteria=(
            PilotRubricCriterion(
                criterion_id="five_volt_one_kilohm_current",
                requirement=(
                    "For 5.0 V across 1.0 kΩ, obtains 5.0 mA with a dimensionally valid Ohm's-law path."
                ),
                acceptable_variations=(
                    "0.005 A and equivalent correctly converted forms are acceptable.",
                ),
                material_error_conditions=(
                    "Uses a relationship that produces a materially wrong current for the stated resistor.",
                ),
            ),
            PilotRubricCriterion(
                criterion_id="led_series_resistor_current",
                requirement=(
                    "Under the stated idealized 2.0 V LED-drop assumption, uses 7.0 V across 330 Ω and obtains about 21.2 mA."
                ),
                acceptable_variations=(
                    "Reasonable rounding near 21 mA is acceptable when the stated assumption is preserved.",
                ),
                material_error_conditions=(
                    "Applies the full 9.0 V across the resistor while simultaneously claiming to honor the stated 2.0 V LED drop.",
                ),
            ),
            PilotRubricCriterion(
                criterion_id="series_network",
                requirement=(
                    "For 100 Ω + 220 Ω in series on 5.0 V, obtains 320 Ω total, "
                    "15.625 mA total current, and voltage drops about 1.5625 V and 3.4375 V that sum to 5.0 V."
                ),
                acceptable_variations=(
                    "Reasonable rounding is acceptable when current is common to both series resistors and the drops remain consistent.",
                ),
                material_error_conditions=(
                    "Treats series-branch currents as independent for this single-loop circuit.",
                    "Produces voltage drops materially inconsistent with the common current or source voltage.",
                ),
            ),
            PilotRubricCriterion(
                criterion_id="resistor_power",
                requirement=(
                    "For 12.0 V across 1.0 kΩ, obtains 0.144 W (144 mW) using a valid power relationship."
                ),
                acceptable_variations=(
                    "Equivalent use of P = VI, P = I^2 R, or P = V^2 / R is acceptable.",
                ),
            ),
            PilotRubricCriterion(
                criterion_id="work_and_units",
                requirement=(
                    "Shows enough intermediate work and units to inspect the reasoning rather than supplying unexplained numbers only."
                ),
                acceptable_variations=(
                    "Calculator use is acceptable when declared as required by the participant-facing protocol.",
                ),
            ),
        ),
        bearing_guidance=_bearing_guidance(
            supports=(
                "Use SUPPORTS when the bounded calculations and shown reasoning are materially correct across the probe."
            ),
            contradicts=(
                "Use CONTRADICTS only when observed calculation reasoning contains a substantive error that directly conflicts with the scoped proposition; a single transcription or harmless rounding issue need not be contradiction."
            ),
            indeterminate=(
                "Use INDETERMINATE when missing work, ambiguous units, or mixed correct/incorrect reasoning prevents a stable scoped judgment."
            ),
            not_relevant=(
                "Use NOT_RELEVANT when the material is not the calculation_work response or does not bear on the bounded calculation proposition."
            ),
        ),
        missing_probe_semantics=PilotMissingProbeSemantics.REQUIRED_COVERAGE_GAP,
    )

    diagnosis = PilotProbeEvaluationRubric(
        probe_id="diagnosis_reasoning",
        claim_key=PILOT_01_REASONING_CLAIM_KEY,
        criteria=(
            PilotRubricCriterion(
                criterion_id="safe_sequence",
                requirement=(
                    "Begins with safe bounded inspection and keeps the reasoning inside the protocol's low-voltage DC boundary."
                ),
                material_error_conditions=(
                    "Recommends mains, high-voltage, opened-power-supply, or unknown energized work.",
                ),
            ),
            PilotRubricCriterion(
                criterion_id="ordered_measurements",
                requirement=(
                    "Provides an ordered diagnostic sequence using visual inspection and a multimeter, including source/supply checks before deeper fault isolation."
                ),
            ),
            PilotRubricCriterion(
                criterion_id="branching_reasoning",
                requirement=(
                    "Explains how at least several possible measurement outcomes change the next diagnostic step."
                ),
                material_error_conditions=(
                    "Lists measurements without connecting results to subsequent diagnostic decisions.",
                ),
            ),
            PilotRubricCriterion(
                criterion_id="fault_hypotheses",
                requirement=(
                    "Identifies at least three plausible faults among source, switch, wiring/connection, resistor, LED orientation/device failure, or equivalent bounded causes."
                ),
            ),
            PilotRubricCriterion(
                criterion_id="measurement_interpretation",
                requirement=(
                    "Uses voltage/continuity or equivalent multimeter observations in a technically coherent way for the stated circuit."
                ),
            ),
        ),
        bearing_guidance=_bearing_guidance(
            supports=(
                "Use SUPPORTS when the diagnostic sequence is safe, technically coherent, and materially satisfies the scoped diagnosis criteria."
            ),
            contradicts=(
                "Use CONTRADICTS for observed unsafe or technically reversed diagnostic reasoning that directly conflicts with the scoped proposition."
            ),
            indeterminate=(
                "Use INDETERMINATE when the sequence is too incomplete, ambiguous, or internally inconsistent to distinguish a material misconception from omitted detail."
            ),
            not_relevant=(
                "Use NOT_RELEVANT when the material does not address diagnosis_reasoning or concerns a context outside the bounded low-voltage DC claim."
            ),
        ),
        missing_probe_semantics=PilotMissingProbeSemantics.REQUIRED_COVERAGE_GAP,
    )

    execution = PilotProbeEvaluationRubric(
        probe_id="execution_artifact",
        claim_key=PILOT_01_EXECUTION_CLAIM_KEY,
        criteria=(
            PilotRubricCriterion(
                criterion_id="bounded_execution_context",
                requirement=(
                    "Represents only a battery- or USB-powered low-voltage DC task inside the protocol physical boundary."
                ),
                material_error_conditions=(
                    "Represents mains, high voltage, an opened power supply, or an unknown energized system.",
                ),
            ),
            PilotRubricCriterion(
                criterion_id="observable_execution_content",
                requirement=(
                    "Contains enough participant-provided observation, measurement, or artifact content to inspect an actual bounded execution or inspection step."
                ),
                material_error_conditions=(
                    "Contains only a claim of having performed the task with no inspectable execution-related content.",
                ),
            ),
            PilotRubricCriterion(
                criterion_id="technical_coherence",
                requirement=(
                    "The represented measurements, connections, or observations are technically coherent with the described simple DC task."
                ),
            ),
            PilotRubricCriterion(
                criterion_id="provenance_limit",
                requirement=(
                    "Evaluator preserves the PR10.x provenance limit: declared subject-provided origin and local hashes do not authenticate human authorship or historical execution."
                ),
            ),
        ),
        bearing_guidance=_bearing_guidance(
            supports=(
                "Use SUPPORTS only when an actual materialized execution_artifact contains inspectable bounded execution content that bears positively on the execution proposition."
            ),
            contradicts=(
                "Use CONTRADICTS only when an observed execution artifact directly demonstrates a substantive unsafe or technically incompatible execution under the claim scope; absence of the optional probe is never contradiction."
            ),
            indeterminate=(
                "Use INDETERMINATE when an execution artifact exists but authenticity limits, ambiguity, incompleteness, or mixed technical content prevents a stable scoped judgment."
            ),
            not_relevant=(
                "Use NOT_RELEVANT when a supplied artifact does not actually bear on bounded practical execution under this claim."
            ),
        ),
        missing_probe_semantics=PilotMissingProbeSemantics.OPTIONAL_UNOBSERVED,
    )

    policy = PilotHumanEvaluationPolicy(
        policy_ref=CIVILIZATION_BOOTSTRAP_PILOT_01_EVALUATION_POLICY_REF_V1,
        protocol_ref=CIVILIZATION_BOOTSTRAP_PILOT_01_PROTOCOL_REF,
        claims=(reasoning_claim, execution_claim),
        probe_rubrics=(conceptual, calculation, diagnosis, execution),
        reliability_rule=(
            "Evidence reliability must be assessed explicitly by the human evaluator. "
            "EvidenceKind, successful materialization, receipt validity, and probe identity "
            "must not automatically promote reliability."
        ),
        coverage_rule=(
            "The bounded_reasoning claim may reach sufficient-for-claim coverage only after "
            "all three required reasoning probes are actually assessed. Missing required "
            "material is a coverage gap, not contradiction. The bounded_execution claim may "
            "reach sufficient coverage only from an actually observed optional execution_artifact; "
            "absence of that optional probe remains unobserved."
        ),
        dependence_rule=(
            "Multiple materialized EvidenceRecords may be assessed individually, but they must "
            "not be treated as independent/repeated support or used to justify multi-record "
            "sufficiency without the PR10.1 terminal reviewed-dependence precondition passing "
            "for the exact basis. A terminal dependence PASS is itself not claim support."
        ),
        authority_boundaries=(
            "CLAIM TEMPLATE != CAPABILITY CLAIM",
            "RUBRIC != CLAIM EVALUATION",
            "EVALUATION POLICY != EVALUATION",
            "EVIDENCE BEARING GUIDANCE != AUTOMATIC BEARING",
            "MISSING REQUIRED PROBE != CONTRADICTION",
            "MISSING OPTIONAL EXECUTION != FAILURE",
            "DEPENDENCE PASS != CLAIM SUPPORT",
            "PR11.0 != PERSONAL CAPABILITY STATE",
        ),
    )
    validate_civilization_bootstrap_pilot_01_evaluation_policy_v1(policy)
    return policy


def validate_civilization_bootstrap_pilot_01_evaluation_policy_v1(
    policy: PilotHumanEvaluationPolicy,
    *,
    protocol: PilotProtocol | None = None,
) -> None:
    """Fail closed if the policy drifts from exact Pilot 01 v1 protocol semantics."""

    if not isinstance(policy, PilotHumanEvaluationPolicy):
        raise InvalidPilotEvaluationPolicy(
            "policy must be PilotHumanEvaluationPolicy"
        )
    if policy.policy_ref != CIVILIZATION_BOOTSTRAP_PILOT_01_EVALUATION_POLICY_REF_V1:
        raise InvalidPilotEvaluationPolicy(
            "policy_ref does not match frozen Pilot 01 evaluation policy v1"
        )
    expected_protocol = (
        build_civilization_bootstrap_pilot_01_protocol_v1()
        if protocol is None
        else protocol
    )
    if not isinstance(expected_protocol, PilotProtocol):
        raise InvalidPilotEvaluationPolicy("protocol must be PilotProtocol")
    if policy.protocol_ref != expected_protocol.protocol_ref:
        raise InvalidPilotEvaluationPolicy(
            "evaluation policy protocol_ref does not match Pilot 01 protocol"
        )
    protocol_probe_ids = tuple(item.probe_id for item in expected_protocol.probes)
    rubric_probe_ids = tuple(item.probe_id for item in policy.probe_rubrics)
    if set(rubric_probe_ids) != set(protocol_probe_ids):
        raise InvalidPilotEvaluationPolicy(
            "evaluation policy must cover every Pilot 01 probe exactly once"
        )
    protocol_by_id = {item.probe_id: item for item in expected_protocol.probes}
    for rubric in policy.probe_rubrics:
        probe = protocol_by_id[rubric.probe_id]
        expected_missing = (
            PilotMissingProbeSemantics.REQUIRED_COVERAGE_GAP
            if probe.requirement is PilotProbeRequirement.REQUIRED
            else PilotMissingProbeSemantics.OPTIONAL_UNOBSERVED
        )
        if rubric.missing_probe_semantics is not expected_missing:
            raise InvalidPilotEvaluationPolicy(
                "probe missing semantics do not match protocol requirement"
            )
    for claim in policy.claims:
        if claim.concept_ref != expected_protocol.capability_ref:
            raise InvalidPilotEvaluationPolicy(
                "claim template concept_ref must match exact Pilot 01 capability_ref"
            )
    reasoning = policy.claim(PILOT_01_REASONING_CLAIM_KEY)
    if reasoning.sufficiency_probe_ids != (
        "conceptual_explanation",
        "calculation_work",
        "diagnosis_reasoning",
    ):
        raise InvalidPilotEvaluationPolicy(
            "bounded_reasoning claim must require the three frozen reasoning probes"
        )
    execution = policy.claim(PILOT_01_EXECUTION_CLAIM_KEY)
    if execution.sufficiency_probe_ids != ("execution_artifact",):
        raise InvalidPilotEvaluationPolicy(
            "bounded_execution claim must be isolated to execution_artifact"
        )
    if (
        policy.rubric("execution_artifact").missing_probe_semantics
        is not PilotMissingProbeSemantics.OPTIONAL_UNOBSERVED
    ):
        raise InvalidPilotEvaluationPolicy(
            "optional execution absence must remain unobserved"
        )


def pilot_evaluation_policy_to_dict_v1(
    policy: PilotHumanEvaluationPolicy,
) -> dict[str, object]:
    validate_civilization_bootstrap_pilot_01_evaluation_policy_v1(policy)
    return {
        "schema": PILOT_EVALUATION_POLICY_SCHEMA_V1,
        "policy_ref": str(policy.policy_ref),
        "protocol_ref": str(policy.protocol_ref),
        "claims": [
            {
                "claim_key": claim.claim_key,
                "concept_ref": str(claim.concept_ref),
                "statement": claim.statement,
                "scope": {
                    "description": claim.scope.description,
                    "tags": list(claim.scope.tags),
                },
                "sufficiency_probe_ids": list(claim.sufficiency_probe_ids),
            }
            for claim in policy.claims
        ],
        "probe_rubrics": [
            {
                "probe_id": rubric.probe_id,
                "claim_key": rubric.claim_key,
                "criteria": [
                    {
                        "criterion_id": criterion.criterion_id,
                        "requirement": criterion.requirement,
                        "acceptable_variations": list(
                            criterion.acceptable_variations
                        ),
                        "material_error_conditions": list(
                            criterion.material_error_conditions
                        ),
                    }
                    for criterion in rubric.criteria
                ],
                "bearing_guidance": [
                    {
                        "bearing": guidance.bearing.value,
                        "condition": guidance.condition,
                    }
                    for guidance in rubric.bearing_guidance
                ],
                "missing_probe_semantics": rubric.missing_probe_semantics.value,
            }
            for rubric in policy.probe_rubrics
        ],
        "reliability_rule": policy.reliability_rule,
        "coverage_rule": policy.coverage_rule,
        "dependence_rule": policy.dependence_rule,
        "authority_boundaries": list(policy.authority_boundaries),
    }


def pilot_evaluation_policy_to_json_v1(
    policy: PilotHumanEvaluationPolicy,
) -> str:
    return json.dumps(
        pilot_evaluation_policy_to_dict_v1(policy),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def pilot_evaluation_policy_sha256_v1(
    policy: PilotHumanEvaluationPolicy,
) -> str:
    digest = hashlib.sha256()
    digest.update(_POLICY_HASH_DOMAIN)
    digest.update(pilot_evaluation_policy_to_json_v1(policy).encode("utf-8"))
    return digest.hexdigest()
