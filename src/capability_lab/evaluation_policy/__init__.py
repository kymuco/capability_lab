"""Generic declarative evaluation-policy specifications and governed admission."""

import os as _os

from . import governance_import_hardening as _governance_import_hardening
from .governance_import_hardening import (
    install_governance_import_hardening_v1,
    reset_governance_publication_after_fork_v1,
)

install_governance_import_hardening_v1()

from .specification import (
    DOMAIN_EVALUATION_SUFFICIENCY_SEMANTICS_V1,
    DomainEvaluationPolicyRequirement,
    DomainEvaluationPolicySpecification,
    InvalidDomainEvaluationPolicySpecification,
    domain_evaluation_policy_specification_applies_to_v1,
    domain_evaluation_policy_specification_sha256_v1,
)
from .serialization import (
    domain_evaluation_policy_specification_from_dict,
    domain_evaluation_policy_specification_from_json,
    domain_evaluation_policy_specification_to_dict,
    domain_evaluation_policy_specification_to_json,
)

from . import governance as _governance
from . import review_process_authority as _review_process_authority
from . import registry_authority as _registry_authority
from . import requirement_application_authority as _requirement_application_authority
from .governance_serialization import (
    domain_evaluation_policy_admission_receipt_from_dict,
    domain_evaluation_policy_admission_receipt_from_json,
    domain_evaluation_policy_admission_receipt_to_dict,
    domain_evaluation_policy_admission_receipt_to_json,
    domain_evaluation_policy_registry_from_dict,
    domain_evaluation_policy_registry_from_json,
    domain_evaluation_policy_registry_to_dict,
    domain_evaluation_policy_registry_to_json,
    domain_evaluation_policy_review_from_dict,
    domain_evaluation_policy_review_from_json,
    domain_evaluation_policy_review_ledger_from_dict,
    domain_evaluation_policy_review_ledger_from_json,
    domain_evaluation_policy_review_ledger_to_dict,
    domain_evaluation_policy_review_ledger_to_json,
    domain_evaluation_policy_review_to_dict,
    domain_evaluation_policy_review_to_json,
)
from .requirement_application import (
    ClaimDomainPolicyRequirementApplicationReceipt,
    ClaimDomainPolicyRequirementMappingProposal,
    ClaimPolicyRequirementMappingReview,
    ClaimPolicyRequirementMappingReviewAdmission,
    ClaimPolicyRequirementMappingReviewId,
    ClaimPolicyRequirementMappingReviewerKind,
    ClaimPolicyRequirementMappingReviewerRef,
    ClaimPolicyRequirementMappingReviewLedger,
    ClaimPolicyRequirementMappingReviewVerdict,
    DomainPolicyRequirementApplicationDisposition,
    DomainPolicyRequirementApplicationEntry,
    DomainPolicyRequirementApplicationError,
    InvalidDomainPolicyRequirementApplication,
    admit_claim_policy_requirement_mapping_review_v1,
    apply_admitted_domain_policy_requirements_v1,
    build_claim_domain_policy_requirement_mapping_proposal_v1,
    claim_domain_policy_requirement_application_receipt_from_dict,
    claim_domain_policy_requirement_application_receipt_from_json,
    claim_domain_policy_requirement_application_receipt_to_dict,
    claim_domain_policy_requirement_application_receipt_to_json,
    claim_domain_policy_requirement_mapping_proposal_from_dict,
    claim_domain_policy_requirement_mapping_proposal_from_json,
    claim_domain_policy_requirement_mapping_proposal_sha256_v1,
    claim_domain_policy_requirement_mapping_proposal_to_dict,
    claim_domain_policy_requirement_mapping_proposal_to_json,
    claim_policy_requirement_mapping_review_from_dict,
    claim_policy_requirement_mapping_review_from_json,
    claim_policy_requirement_mapping_review_ledger_from_dict,
    claim_policy_requirement_mapping_review_ledger_from_json,
    claim_policy_requirement_mapping_review_ledger_sha256_v1,
    claim_policy_requirement_mapping_review_ledger_to_dict,
    claim_policy_requirement_mapping_review_ledger_to_json,
    claim_policy_requirement_mapping_review_sha256_v1,
    claim_policy_requirement_mapping_review_to_dict,
    claim_policy_requirement_mapping_review_to_json,
    domain_policy_requirement_application_entry_from_dict,
    domain_policy_requirement_application_entry_to_dict,
    require_approved_claim_policy_requirement_mapping_review_v1,
    review_claim_domain_policy_requirement_mapping_proposal_v1,
    validate_claim_domain_policy_requirement_application_v1,
    validate_claim_domain_policy_requirement_mapping_proposal_v1,
    validate_claim_policy_requirement_mapping_review_admission_v1,
    validate_claim_policy_requirement_mapping_review_ledger_successor_v1,
    validate_claim_policy_requirement_mapping_review_v1,
)
from .directional_evaluation import (
    ClaimDomainPolicyDirectionalEvaluationReceipt,
    DomainPolicyDirectionalEvaluationError,
    InvalidDomainPolicyDirectionalEvaluation,
    build_claim_domain_policy_directional_evaluation_v1,
    claim_domain_policy_directional_claim_evaluation_sha256_v1,
    claim_domain_policy_directional_evaluation_receipt_from_dict,
    claim_domain_policy_directional_evaluation_receipt_from_json,
    claim_domain_policy_directional_evaluation_receipt_sha256_v1,
    claim_domain_policy_directional_evaluation_receipt_to_dict,
    claim_domain_policy_directional_evaluation_receipt_to_json,
    validate_claim_domain_policy_directional_evaluation_v1,
)


_GOVERNANCE_DYNAMIC_EXPORTS = frozenset(
    {
        "DomainEvaluationPolicyAdmissionReceipt",
        "DomainEvaluationPolicyRegistry",
        "DomainEvaluationPolicyRegistryEntry",
        "DomainEvaluationPolicyReview",
        "DomainEvaluationPolicyReviewAdmission",
        "DomainEvaluationPolicyReviewId",
        "DomainEvaluationPolicyReviewerKind",
        "DomainEvaluationPolicyReviewerRef",
        "DomainEvaluationPolicyReviewLedger",
        "DomainEvaluationPolicyReviewVerdict",
        "InvalidDomainEvaluationPolicyGovernance",
        "admit_domain_evaluation_policy_review_v1",
        "admit_domain_evaluation_policy_v1",
        "domain_evaluation_policy_admission_receipt_sha256_v1",
        "domain_evaluation_policy_registry_sha256_v1",
        "domain_evaluation_policy_review_ledger_sha256_v1",
        "domain_evaluation_policy_review_sha256_v1",
        "require_approved_domain_evaluation_policy_review_v1",
        "resolve_admitted_domain_evaluation_policy_v1",
        "resolve_domain_evaluation_policy_terminal_review_v1",
        "review_domain_evaluation_policy_specification_v1",
        "validate_domain_evaluation_policy_admission_receipt_v1",
        "validate_domain_evaluation_policy_registry_successor_v1",
        "validate_domain_evaluation_policy_review_admission_v1",
        "validate_domain_evaluation_policy_review_ledger_successor_v1",
        "validate_domain_evaluation_policy_review_v1",
    }
)


def __getattr__(name: str):
    if name not in _GOVERNANCE_DYNAMIC_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    generation = _governance_import_hardening._stable_current_published_generation()
    return getattr(generation, name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | _GOVERNANCE_DYNAMIC_EXPORTS)


def _clear_runtime_authorities_after_fork() -> None:
    reset_governance_publication_after_fork_v1()
    _review_process_authority.clear_review_process_authorities_after_fork_v1()
    _registry_authority.clear_policy_registry_authorities_after_fork_v1()
    _requirement_application_authority.clear_mapping_review_process_authorities_after_fork_v1()


if hasattr(_os, "register_at_fork"):
    _os.register_at_fork(after_in_child=_clear_runtime_authorities_after_fork)


__all__ = [
    "DOMAIN_EVALUATION_SUFFICIENCY_SEMANTICS_V1",
    "DomainEvaluationPolicyRequirement",
    "DomainEvaluationPolicySpecification",
    "InvalidDomainEvaluationPolicySpecification",
    "domain_evaluation_policy_specification_applies_to_v1",
    "domain_evaluation_policy_specification_sha256_v1",
    "domain_evaluation_policy_specification_from_dict",
    "domain_evaluation_policy_specification_from_json",
    "domain_evaluation_policy_specification_to_dict",
    "domain_evaluation_policy_specification_to_json",
    "DomainEvaluationPolicyAdmissionReceipt",
    "DomainEvaluationPolicyRegistry",
    "DomainEvaluationPolicyRegistryEntry",
    "DomainEvaluationPolicyReview",
    "DomainEvaluationPolicyReviewAdmission",
    "DomainEvaluationPolicyReviewId",
    "DomainEvaluationPolicyReviewerKind",
    "DomainEvaluationPolicyReviewerRef",
    "DomainEvaluationPolicyReviewLedger",
    "DomainEvaluationPolicyReviewVerdict",
    "InvalidDomainEvaluationPolicyGovernance",
    "admit_domain_evaluation_policy_review_v1",
    "admit_domain_evaluation_policy_v1",
    "domain_evaluation_policy_admission_receipt_sha256_v1",
    "domain_evaluation_policy_registry_sha256_v1",
    "domain_evaluation_policy_review_ledger_sha256_v1",
    "domain_evaluation_policy_review_sha256_v1",
    "require_approved_domain_evaluation_policy_review_v1",
    "resolve_admitted_domain_evaluation_policy_v1",
    "resolve_domain_evaluation_policy_terminal_review_v1",
    "review_domain_evaluation_policy_specification_v1",
    "validate_domain_evaluation_policy_admission_receipt_v1",
    "validate_domain_evaluation_policy_registry_successor_v1",
    "validate_domain_evaluation_policy_review_admission_v1",
    "validate_domain_evaluation_policy_review_ledger_successor_v1",
    "validate_domain_evaluation_policy_review_v1",
    "domain_evaluation_policy_admission_receipt_from_dict",
    "domain_evaluation_policy_admission_receipt_from_json",
    "domain_evaluation_policy_admission_receipt_to_dict",
    "domain_evaluation_policy_admission_receipt_to_json",
    "domain_evaluation_policy_registry_from_dict",
    "domain_evaluation_policy_registry_from_json",
    "domain_evaluation_policy_registry_to_dict",
    "domain_evaluation_policy_registry_to_json",
    "domain_evaluation_policy_review_from_dict",
    "domain_evaluation_policy_review_from_json",
    "domain_evaluation_policy_review_ledger_from_dict",
    "domain_evaluation_policy_review_ledger_from_json",
    "domain_evaluation_policy_review_ledger_to_dict",
    "domain_evaluation_policy_review_ledger_to_json",
    "domain_evaluation_policy_review_to_dict",
    "domain_evaluation_policy_review_to_json",
    "ClaimDomainPolicyRequirementApplicationReceipt",
    "ClaimDomainPolicyRequirementMappingProposal",
    "ClaimPolicyRequirementMappingReview",
    "ClaimPolicyRequirementMappingReviewAdmission",
    "ClaimPolicyRequirementMappingReviewId",
    "ClaimPolicyRequirementMappingReviewerKind",
    "ClaimPolicyRequirementMappingReviewerRef",
    "ClaimPolicyRequirementMappingReviewLedger",
    "ClaimPolicyRequirementMappingReviewVerdict",
    "DomainPolicyRequirementApplicationDisposition",
    "DomainPolicyRequirementApplicationEntry",
    "DomainPolicyRequirementApplicationError",
    "InvalidDomainPolicyRequirementApplication",
    "admit_claim_policy_requirement_mapping_review_v1",
    "apply_admitted_domain_policy_requirements_v1",
    "build_claim_domain_policy_requirement_mapping_proposal_v1",
    "claim_domain_policy_requirement_application_receipt_from_dict",
    "claim_domain_policy_requirement_application_receipt_from_json",
    "claim_domain_policy_requirement_application_receipt_to_dict",
    "claim_domain_policy_requirement_application_receipt_to_json",
    "claim_domain_policy_requirement_mapping_proposal_from_dict",
    "claim_domain_policy_requirement_mapping_proposal_from_json",
    "claim_domain_policy_requirement_mapping_proposal_sha256_v1",
    "claim_domain_policy_requirement_mapping_proposal_to_dict",
    "claim_domain_policy_requirement_mapping_proposal_to_json",
    "claim_policy_requirement_mapping_review_from_dict",
    "claim_policy_requirement_mapping_review_from_json",
    "claim_policy_requirement_mapping_review_ledger_from_dict",
    "claim_policy_requirement_mapping_review_ledger_from_json",
    "claim_policy_requirement_mapping_review_ledger_sha256_v1",
    "claim_policy_requirement_mapping_review_ledger_to_dict",
    "claim_policy_requirement_mapping_review_ledger_to_json",
    "claim_policy_requirement_mapping_review_sha256_v1",
    "claim_policy_requirement_mapping_review_to_dict",
    "claim_policy_requirement_mapping_review_to_json",
    "domain_policy_requirement_application_entry_from_dict",
    "domain_policy_requirement_application_entry_to_dict",
    "require_approved_claim_policy_requirement_mapping_review_v1",
    "review_claim_domain_policy_requirement_mapping_proposal_v1",
    "validate_claim_domain_policy_requirement_application_v1",
    "validate_claim_domain_policy_requirement_mapping_proposal_v1",
    "validate_claim_policy_requirement_mapping_review_admission_v1",
    "validate_claim_policy_requirement_mapping_review_ledger_successor_v1",
    "validate_claim_policy_requirement_mapping_review_v1",
    "ClaimDomainPolicyDirectionalEvaluationReceipt",
    "DomainPolicyDirectionalEvaluationError",
    "InvalidDomainPolicyDirectionalEvaluation",
    "build_claim_domain_policy_directional_evaluation_v1",
    "claim_domain_policy_directional_claim_evaluation_sha256_v1",
    "claim_domain_policy_directional_evaluation_receipt_from_dict",
    "claim_domain_policy_directional_evaluation_receipt_from_json",
    "claim_domain_policy_directional_evaluation_receipt_sha256_v1",
    "claim_domain_policy_directional_evaluation_receipt_to_dict",
    "claim_domain_policy_directional_evaluation_receipt_to_json",
    "validate_claim_domain_policy_directional_evaluation_v1",
]
