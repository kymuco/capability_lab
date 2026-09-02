"""Curated Civilization Bootstrap seed capability graph v0.

This module is domain content, not a generic domain-pack framework. It contains
person-agnostic shared semantics plus one explicit domain competence frame.
Editorial families are documentation/curation aids and are not encoded as
SPECIALIZES edges unless the narrower capability is defensibly a semantic
specialization of the broader one.
"""

from __future__ import annotations

from capability_lab.semantics import (
    CapabilityCatalog,
    CapabilityConcept,
    CapabilityId,
    CapabilityNamespace,
    CapabilityRelation,
    ConceptLifecycle,
    RelationKind,
    RelationScope,
    RelationStrength,
)
from capability_lab.state import (
    CompetenceDimensionDefinition,
    CompetenceFrame,
    CompetenceFrameCatalog,
    CompetenceFrameId,
)


CIVILIZATION_BOOTSTRAP_NAMESPACE = CapabilityNamespace(
    "civilization_bootstrap",
    "Civilization Bootstrap",
    "Curated technical-generalist seed semantics; not a curriculum, authority hierarchy, or complete civilization ontology.",
)
CIVILIZATION_BOOTSTRAP_SEED_VERSION = "v0"


_CONCEPT_SPECS: tuple[tuple[str, str, str], ...] = (
    # Foundations / inquiry
    ("technical_inquiry", "Technical Inquiry", "Investigate a bounded technical question by making assumptions explicit, gathering observations, testing explanations, and communicating limitations."),
    ("quantitative_estimation", "Quantitative Estimation", "Construct and check order-of-magnitude estimates for bounded technical quantities using explicit assumptions and units."),
    ("dimensional_analysis", "Dimensional Analysis", "Use physical dimensions and units to construct, transform, and sanity-check bounded quantitative relationships."),
    ("physical_measurement", "Physical Measurement", "Select and use appropriate measurement concepts to obtain, record, and interpret bounded physical quantities with stated conditions."),
    ("uncertainty_and_error_analysis", "Uncertainty and Error Analysis", "Identify material sources of measurement uncertainty and error and reason about their effect on bounded technical conclusions."),
    ("experimental_design", "Experimental Design", "Design a bounded experiment that distinguishes relevant hypotheses through controlled observations and explicit variables."),
    ("fault_isolation", "Fault Isolation", "Localize causes of unexpected behavior in a bounded technical system by forming and testing discriminating hypotheses."),
    ("technical_explanation", "Technical Explanation", "Explain a bounded technical mechanism or result with inspectable reasoning, assumptions, evidence, and limitations."),
    # Matter / materials
    ("material_behavior_and_processing", "Material Behavior and Processing", "Reason about how composition, structure, environment, and processing affect the behavior of bounded material systems."),
    ("material_property_selection", "Material Property Selection", "Select candidate materials for a bounded function by relating relevant properties, environment, manufacturability, and failure modes."),
    ("stoichiometric_preparation", "Stoichiometric Preparation", "Calculate and prepare bounded material quantities from explicit composition or reaction relationships while preserving units and constraints."),
    ("acid_base_control", "Acid-Base Control", "Reason about and control acidity or alkalinity in a bounded chemical process using explicit concentration, equilibrium, and measurement assumptions."),
    ("oxidation_reduction", "Oxidation-Reduction Reasoning", "Reason about electron-transfer, oxidation-state, and electrochemical behavior in bounded chemical or material systems."),
    ("thermal_material_processing", "Thermal Material Processing", "Reason about and execute bounded heating or cooling processes that intentionally change material state or microstructure."),
    ("corrosion_and_degradation", "Corrosion and Degradation", "Identify and reason about bounded chemical or environmental material degradation mechanisms and plausible mitigation strategies."),
    # Energy / physical systems
    ("energy_system_reasoning", "Energy System Reasoning", "Reason about bounded systems that store, transfer, transform, or dissipate energy using explicit physical models and constraints."),
    ("mechanical_work_and_power", "Mechanical Work and Power", "Calculate and interpret force, work, torque, energy, and power relationships in bounded mechanical systems."),
    ("thermodynamic_energy_balance", "Thermodynamic Energy Balance", "Construct and interpret bounded energy balances involving heat, work, stored energy, and state changes."),
    ("heat_transfer", "Heat Transfer", "Reason about conduction, convection, radiation, and thermal resistance in bounded heat-transfer situations."),
    ("fluid_pressure_and_flow", "Fluid Pressure and Flow", "Reason quantitatively about bounded fluid pressure, flow, resistance, continuity, and energy relationships."),
    ("basic_electricity", "Basic Electricity", "Reason quantitatively about charge, current, voltage, resistance, electrical energy, and power in bounded contexts."),
    ("electromagnetism", "Electromagnetism", "Reason about bounded relationships among electric current, magnetic fields, induction, force, and energy conversion."),
    # Fabrication / metrology
    ("fabrication_process_execution", "Fabrication Process Execution", "Plan and carry out bounded fabrication operations while respecting dimensions, materials, process limits, and stated safety constraints."),
    ("hand_tool_operations", "Hand Tool Operations", "Select and use common hand tools for bounded fabrication, assembly, adjustment, and disassembly tasks with controlled technique."),
    ("dimensional_metrology", "Dimensional Metrology", "Measure and inspect bounded dimensions, geometry, fit, and tolerances using appropriate dimensional instruments and references."),
    ("mechanical_joining", "Mechanical Joining", "Create, inspect, and reason about bounded mechanical joints using fasteners, fits, adhesives, or related joining methods."),
    ("soldering", "Soldering", "Create and inspect bounded soldered electrical joints in an explicit training or prototype context while recognizing process and safety limits."),
    ("welding", "Welding", "Reason about and execute bounded welding operations in an explicitly controlled training context while recognizing process, material, and safety limits."),
    ("casting_and_molding", "Casting and Molding", "Reason about and execute bounded mold preparation, filling, solidification, release, and defect inspection for suitable materials."),
    ("machining", "Machining", "Plan, execute, and inspect bounded material-removal operations against explicit dimensions, tolerances, tooling, and process constraints."),
    # Mechanical systems
    ("mechanical_system_reasoning", "Mechanical System Reasoning", "Reason about bounded assemblies that transmit motion, load, pressure, or mechanical power through interacting components."),
    ("mechanisms_and_power_transmission", "Mechanisms and Power Transmission", "Analyze bounded linkages, gears, belts, chains, shafts, ratios, torque paths, and motion conversion."),
    ("bearings_and_lubrication", "Bearings and Lubrication", "Select, inspect, and reason about bounded bearing and lubrication arrangements under explicit load, speed, alignment, and environment constraints."),
    ("valves_and_flow_control", "Valves and Flow Control", "Reason about and configure bounded valves and passive flow-control elements to influence fluid direction, isolation, pressure, or flow."),
    ("pump_systems", "Pump Systems", "Analyze, assemble, or diagnose bounded pump systems by relating pressure, flow, mechanical input, losses, and component behavior."),
    ("compression_systems", "Compression Systems", "Analyze or diagnose bounded gas-compression systems using explicit pressure, temperature, flow, sealing, and energy relationships."),
    ("electric_motor_systems", "Electric Motor Systems", "Analyze, assemble, or diagnose bounded electric motor systems by relating electromagnetic torque production, electrical input, mechanical load, and losses."),
    ("generator_systems", "Generator Systems", "Analyze, assemble, or diagnose bounded electrical generation systems by relating mechanical input, electromagnetic induction, electrical output, and losses."),
    ("refrigeration_systems", "Refrigeration Systems", "Reason about or diagnose bounded refrigeration cycles and components using explicit energy, phase-change, compression, and heat-transfer relationships."),
    # Electrical / information systems
    ("electrical_information_system_reasoning", "Electrical and Information System Reasoning", "Reason about bounded systems that sense, transform, communicate, compute, or control information using electrical or digital mechanisms."),
    ("electrical_measurement", "Electrical Measurement", "Measure and interpret bounded voltage, current, resistance, continuity, frequency, or related electrical quantities with appropriate instrumentation and stated limits."),
    ("basic_circuits", "Basic Circuits", "Analyze bounded DC or low-complexity electrical circuits by relating topology, component behavior, voltage, current, resistance, and power."),
    ("analog_electronics", "Analog Electronics", "Analyze and build bounded analog signal or power-conditioning circuits using explicit component and operating assumptions."),
    ("digital_logic", "Digital Logic", "Reason about and implement bounded Boolean, combinational, sequential, and state-based digital logic."),
    ("sensing_and_signal_conditioning", "Sensing and Signal Conditioning", "Select, connect, and reason about bounded sensors and signal-conditioning paths from physical quantity to usable electrical representation."),
    ("feedback_control", "Feedback Control", "Reason about bounded feedback systems using explicit plant, sensor, actuator, stability, error, and response concepts."),
    ("embedded_programming", "Embedded Programming", "Implement and debug bounded software that interacts with constrained hardware, timing, I/O, and device state."),
    ("microcontroller_sensor_systems", "Microcontroller Sensor Systems", "Build and debug a bounded microcontroller-based sensing system that acquires, processes, and exposes physical measurements."),
    ("radio_communication", "Radio Communication", "Reason about, assemble, or diagnose bounded radio links using explicit signal, modulation, propagation, antenna, and interface assumptions."),
    # Infrastructure
    ("infrastructure_system_reasoning", "Infrastructure System Reasoning", "Reason about bounded technical systems that provide essential water, sanitation, power, thermal, shelter, or food-preservation functions."),
    ("potable_water_treatment", "Potable Water Treatment", "Reason about bounded processes for producing microbiologically and chemically safer drinking water, including treatment barriers, measurement, and limitations."),
    ("sanitation_systems", "Sanitation Systems", "Reason about bounded collection, separation, treatment, and contamination-control functions in sanitation systems."),
    ("low_voltage_power_distribution", "Low-Voltage Power Distribution", "Analyze or assemble bounded low-voltage power-distribution arrangements with explicit source, load, conductor, protection, measurement, and isolation assumptions."),
    ("heating_and_ventilation", "Heating and Ventilation", "Reason about bounded heating and ventilation systems using explicit heat-transfer, airflow, comfort, moisture, and energy constraints."),
    ("structural_construction", "Structural Construction", "Reason about and execute bounded structural assembly tasks using explicit loads, geometry, material behavior, joints, and construction constraints."),
    ("food_preservation", "Food Preservation", "Reason about bounded methods that slow spoilage or pathogen growth through temperature, moisture, acidity, packaging, or related controls."),
    # Life systems
    ("life_support_system_reasoning", "Life-Support System Reasoning", "Reason about bounded biological, agricultural, nutrition, contamination-control, and public-health systems relevant to sustaining human life."),
    ("biological_systems_reasoning", "Biological Systems Reasoning", "Reason about bounded biological systems using cell, organism, metabolism, regulation, inheritance, ecology, and environment concepts at an appropriate level."),
    ("microbiology_and_contamination_control", "Microbiology and Contamination Control", "Reason about bounded microbial growth, transmission, contamination pathways, control barriers, and measurement limitations."),
    ("soil_and_crop_systems", "Soil and Crop Systems", "Reason about bounded plant-production systems using soil, water, nutrient, light, climate, pest, and crop-development constraints."),
    ("nutrition_and_food_safety", "Nutrition and Food Safety", "Reason about bounded human nutrition needs and food-safety risks using explicit composition, contamination, storage, and preparation assumptions."),
    ("public_health_reasoning", "Public Health Reasoning", "Reason about bounded population-level health risks, transmission, prevention, measurement, and intervention tradeoffs without implying clinical authority."),
    ("first_aid_principles", "First-Aid Principles", "Explain and recognize bounded first-aid priorities, escalation limits, and emergency-response principles without implying credentialing or permission to perform regulated care."),
)


# Editorial families are not graph structure. SPECIALIZES is reserved for a
# defensible semantic narrowing, not for UI grouping or curriculum membership.
_SPECIALIZES_SPECS: tuple[tuple[str, str], ...] = (
    ("electrical_measurement", "physical_measurement"),
    ("dimensional_metrology", "physical_measurement"),
)


_SCOPE_DESCRIPTIONS = {
    "conceptual_analysis": "For bounded conceptual analysis rather than universal prerequisite or curriculum claims.",
    "bench_validation": "For bounded bench measurement, validation, and diagnosis under stated instrumentation limits.",
    "bounded_execution": "For bounded practical execution under explicit tools, supervision, environment, and safety constraints.",
    "functional_reconstruction": "For rough functional reconstruction or repair rather than industrial-grade replication.",
    "system_diagnosis": "For diagnosing bounded system behavior or faults rather than every possible operating context.",
    "bounded_implementation": "For implementing a bounded prototype with explicitly stated hardware, software, and interface assumptions.",
    "process_safety_reasoning": "For reasoning about a bounded process whose definition includes contamination or protection constraints; this does not grant professional authority.",
    "field_reasoning": "For bounded field operation, maintenance, or troubleshooting rather than unrestricted professional practice.",
    "prototype_assembly": "For assembling a bounded prototype; alternative fabrication routes may exist.",
}


# source, target, strength, relation-local scope key
_SUPPORTED_BY_SPECS: tuple[tuple[str, str, RelationStrength, str], ...] = (
    ("experimental_design", "uncertainty_and_error_analysis", RelationStrength.STRONG, "conceptual_analysis"),
    ("fault_isolation", "physical_measurement", RelationStrength.STRONG, "system_diagnosis"),
    ("stoichiometric_preparation", "quantitative_estimation", RelationStrength.STRONG, "bounded_execution"),
    ("stoichiometric_preparation", "dimensional_analysis", RelationStrength.STRONG, "conceptual_analysis"),
    ("acid_base_control", "stoichiometric_preparation", RelationStrength.MODERATE, "bounded_execution"),
    ("oxidation_reduction", "stoichiometric_preparation", RelationStrength.MODERATE, "conceptual_analysis"),
    ("thermal_material_processing", "heat_transfer", RelationStrength.STRONG, "bounded_execution"),
    ("corrosion_and_degradation", "oxidation_reduction", RelationStrength.STRONG, "conceptual_analysis"),
    ("mechanical_work_and_power", "quantitative_estimation", RelationStrength.STRONG, "conceptual_analysis"),
    ("thermodynamic_energy_balance", "dimensional_analysis", RelationStrength.STRONG, "conceptual_analysis"),
    ("heat_transfer", "thermodynamic_energy_balance", RelationStrength.STRONG, "conceptual_analysis"),
    ("fluid_pressure_and_flow", "dimensional_analysis", RelationStrength.MODERATE, "conceptual_analysis"),
    ("electromagnetism", "basic_electricity", RelationStrength.STRONG, "conceptual_analysis"),
    ("dimensional_metrology", "physical_measurement", RelationStrength.STRONG, "bounded_execution"),
    ("soldering", "hand_tool_operations", RelationStrength.MODERATE, "prototype_assembly"),
    ("welding", "material_property_selection", RelationStrength.MODERATE, "bounded_execution"),
    ("casting_and_molding", "thermal_material_processing", RelationStrength.STRONG, "functional_reconstruction"),
    ("machining", "dimensional_metrology", RelationStrength.STRONG, "bounded_execution"),
    ("mechanisms_and_power_transmission", "mechanical_work_and_power", RelationStrength.STRONG, "conceptual_analysis"),
    ("valves_and_flow_control", "fluid_pressure_and_flow", RelationStrength.STRONG, "bounded_execution"),
    ("pump_systems", "fluid_pressure_and_flow", RelationStrength.STRONG, "system_diagnosis"),
    ("pump_systems", "mechanisms_and_power_transmission", RelationStrength.MODERATE, "functional_reconstruction"),
    ("compression_systems", "fluid_pressure_and_flow", RelationStrength.STRONG, "system_diagnosis"),
    ("electric_motor_systems", "electromagnetism", RelationStrength.STRONG, "conceptual_analysis"),
    ("electric_motor_systems", "mechanisms_and_power_transmission", RelationStrength.MODERATE, "functional_reconstruction"),
    ("generator_systems", "electromagnetism", RelationStrength.STRONG, "conceptual_analysis"),
    ("refrigeration_systems", "thermodynamic_energy_balance", RelationStrength.STRONG, "conceptual_analysis"),
    ("refrigeration_systems", "compression_systems", RelationStrength.STRONG, "system_diagnosis"),
    ("electrical_measurement", "basic_electricity", RelationStrength.STRONG, "bench_validation"),
    ("basic_circuits", "electrical_measurement", RelationStrength.STRONG, "bench_validation"),
    ("basic_circuits", "basic_electricity", RelationStrength.STRONG, "conceptual_analysis"),
    ("analog_electronics", "basic_circuits", RelationStrength.STRONG, "conceptual_analysis"),
    ("digital_logic", "basic_circuits", RelationStrength.MODERATE, "conceptual_analysis"),
    ("sensing_and_signal_conditioning", "analog_electronics", RelationStrength.STRONG, "bounded_implementation"),
    ("sensing_and_signal_conditioning", "electrical_measurement", RelationStrength.STRONG, "bench_validation"),
    ("feedback_control", "sensing_and_signal_conditioning", RelationStrength.MODERATE, "conceptual_analysis"),
    ("embedded_programming", "digital_logic", RelationStrength.MODERATE, "bounded_implementation"),
    ("microcontroller_sensor_systems", "sensing_and_signal_conditioning", RelationStrength.STRONG, "bounded_implementation"),
    ("microcontroller_sensor_systems", "embedded_programming", RelationStrength.STRONG, "bounded_implementation"),
    ("radio_communication", "electromagnetism", RelationStrength.MODERATE, "conceptual_analysis"),
    ("potable_water_treatment", "fluid_pressure_and_flow", RelationStrength.MODERATE, "field_reasoning"),
    ("potable_water_treatment", "microbiology_and_contamination_control", RelationStrength.STRONG, "process_safety_reasoning"),
    ("sanitation_systems", "microbiology_and_contamination_control", RelationStrength.STRONG, "process_safety_reasoning"),
    ("low_voltage_power_distribution", "electrical_measurement", RelationStrength.STRONG, "bench_validation"),
    ("heating_and_ventilation", "heat_transfer", RelationStrength.STRONG, "conceptual_analysis"),
    ("structural_construction", "material_property_selection", RelationStrength.STRONG, "bounded_execution"),
    ("food_preservation", "microbiology_and_contamination_control", RelationStrength.STRONG, "process_safety_reasoning"),
    ("microbiology_and_contamination_control", "biological_systems_reasoning", RelationStrength.STRONG, "conceptual_analysis"),
    ("soil_and_crop_systems", "biological_systems_reasoning", RelationStrength.MODERATE, "field_reasoning"),
    ("nutrition_and_food_safety", "microbiology_and_contamination_control", RelationStrength.MODERATE, "process_safety_reasoning"),
    ("public_health_reasoning", "microbiology_and_contamination_control", RelationStrength.STRONG, "conceptual_analysis"),
)


_REQUIRES_SPECS: tuple[tuple[str, str, str], ...] = (
    ("low_voltage_power_distribution", "basic_electricity", "conceptual_analysis"),
)


_ENABLED_BY_SPECS: tuple[tuple[str, str, str], ...] = (
    ("microcontroller_sensor_systems", "soldering", "prototype_assembly"),
    ("radio_communication", "soldering", "prototype_assembly"),
    ("structural_construction", "hand_tool_operations", "functional_reconstruction"),
)


def _capability_id(key: str) -> CapabilityId:
    return CapabilityId(CIVILIZATION_BOOTSTRAP_NAMESPACE.namespace_id, key)


def _scope(key: str) -> RelationScope:
    return RelationScope(key, _SCOPE_DESCRIPTIONS[key])


def build_civilization_bootstrap_seed_catalog_v0() -> CapabilityCatalog:
    """Return the immutable deterministic PR5 seed semantic snapshot."""

    concepts = tuple(
        CapabilityConcept(
            capability_id=_capability_id(key),
            name=name,
            definition=definition,
            revision=1,
            lifecycle=ConceptLifecycle.ACTIVE,
        )
        for key, name, definition in _CONCEPT_SPECS
    )

    relations: list[CapabilityRelation] = []
    for source, target in _SPECIALIZES_SPECS:
        relations.append(
            CapabilityRelation(
                _capability_id(source),
                _capability_id(target),
                RelationKind.SPECIALIZES,
            )
        )

    for source, target, strength, scope_key in _SUPPORTED_BY_SPECS:
        relations.append(
            CapabilityRelation(
                _capability_id(source),
                _capability_id(target),
                RelationKind.SUPPORTED_BY,
                scope=_scope(scope_key),
                strength=strength,
            )
        )

    for source, target, scope_key in _REQUIRES_SPECS:
        relations.append(
            CapabilityRelation(
                _capability_id(source),
                _capability_id(target),
                RelationKind.REQUIRES,
                scope=_scope(scope_key),
            )
        )

    for source, target, scope_key in _ENABLED_BY_SPECS:
        relations.append(
            CapabilityRelation(
                _capability_id(source),
                _capability_id(target),
                RelationKind.ENABLED_BY,
                scope=_scope(scope_key),
            )
        )

    return CapabilityCatalog(
        namespaces=(CIVILIZATION_BOOTSTRAP_NAMESPACE,),
        concepts=concepts,
        relations=tuple(relations),
    )


CIVILIZATION_BOOTSTRAP_TECHNICAL_COMPETENCE_FRAME_V1 = CompetenceFrame(
    frame_id=CompetenceFrameId.parse("civilization_bootstrap:technical_competence"),
    revision=1,
    name="Civilization Bootstrap Technical Competence",
    description="A domain-defined, non-ordinal decomposition for representing scoped technical capability claims without a universal mastery score.",
    dimensions=(
        CompetenceDimensionDefinition(
            "conceptual_knowledge",
            "Conceptual Knowledge",
            "Understand relevant principles, mechanisms, models, assumptions, and constraints for the bounded claim.",
        ),
        CompetenceDimensionDefinition(
            "calculation",
            "Calculation",
            "Perform and interpret quantitative reasoning appropriate to the bounded claim.",
        ),
        CompetenceDimensionDefinition(
            "execution",
            "Execution",
            "Carry out the relevant practical operation within the claim's explicit tools, environment, assistance, and safety context.",
        ),
        CompetenceDimensionDefinition(
            "diagnosis",
            "Diagnosis",
            "Identify, localize, and reason about failures or unexpected behavior within the bounded claim context.",
        ),
        CompetenceDimensionDefinition(
            "transfer",
            "Transfer",
            "Apply the scoped capability in a materially changed but related context without treating transfer as automatic.",
        ),
        CompetenceDimensionDefinition(
            "independence",
            "Independence",
            "Perform within the explicitly stated assistance, reference, collaboration, tool, and automation boundary; this is not human value or authority.",
        ),
        CompetenceDimensionDefinition(
            "explanation",
            "Explanation",
            "Communicate mechanism, reasoning, observations, assumptions, and limitations clearly enough for inspection.",
        ),
    ),
)


def build_civilization_bootstrap_frame_catalog_v1() -> CompetenceFrameCatalog:
    """Return the exact shared frame snapshot used by the seed domain."""

    return CompetenceFrameCatalog(
        frames=(CIVILIZATION_BOOTSTRAP_TECHNICAL_COMPETENCE_FRAME_V1,)
    )


__all__ = [
    "CIVILIZATION_BOOTSTRAP_NAMESPACE",
    "CIVILIZATION_BOOTSTRAP_SEED_VERSION",
    "CIVILIZATION_BOOTSTRAP_TECHNICAL_COMPETENCE_FRAME_V1",
    "build_civilization_bootstrap_frame_catalog_v1",
    "build_civilization_bootstrap_seed_catalog_v0",
]
