from dataclasses import replace
import importlib.util
from pathlib import Path

import pytest

from capability_lab.epistemics import (
    EpistemicRecordSet,
    EvidenceId,
    validate_epistemic_snapshot_successor_v1,
)
from capability_lab.evaluation_policy import (
    ClaimPolicyRequirementMappingReviewAdmission,
    ClaimPolicyRequirementMappingReviewId,
    ClaimPolicyRequirementMappingReviewerKind,
    ClaimPolicyRequirementMappingReviewerRef,
    ClaimPolicyRequirementMappingReviewVerdict,
    DomainPolicyRequirementApplicationDisposition,
    InvalidDomainPolicyDirectionalEvaluation,
    admit_claim_policy_requirement_mapping_review_v1,
    build_claim_domain_policy_directional_evaluation_v1,
    build_claim_domain_policy_requirement_mapping_proposal_v1,
    domain_evaluation_policy_specification_sha256_v1,
    review_claim_domain_policy_requirement_mapping_proposal_v1,
)


_BASE_PATH = Path(__file__).with_name(
    "test_domain_policy_directional_evaluation_v1.py"
)
_SPEC = importlib.util.spec_from_file_location(
    "_pr12_12_directional_base_tests",
    _BASE_PATH,
)
assert _SPEC is not None and _SPEC.loader is not None
_BASE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_BASE)


def _build_with(basis, **overrides):
    values = {
        "records": basis["records"],
        "claim_id": basis["claim"].claim_id,
        "as_of": _BASE._time(14),
        "coverage": basis["coverage"],
        "lineage": basis["lineage"],
        "registry": basis["registry"],
        "proposal": basis["proposal"],
        "review_ledger": basis["review_ledger"],
        "review_admission": basis["review_admission"],
        "application": basis["application"],
    }
    values.update(overrides)
    return build_claim_domain_policy_directional_evaluation_v1(**values)


def test_tampered_pr12_9_snapshot_basis_is_rejected_transitively():
    basis = _BASE._basis()
    forged = replace(basis["coverage"], snapshot_sha256="0" * 64)
    with pytest.raises(
        InvalidDomainPolicyDirectionalEvaluation,
        match="PR12.11 governed application replay failed",
    ):
        _build_with(basis, coverage=forged)


def test_tampered_pr12_10_snapshot_basis_is_rejected_transitively():
    basis = _BASE._basis()
    forged = replace(basis["lineage"], snapshot_sha256="0" * 64)
    with pytest.raises(
        InvalidDomainPolicyDirectionalEvaluation,
        match="PR12.11 governed application replay failed",
    ):
        _build_with(basis, lineage=forged)


def test_stale_mapping_review_admission_after_ledger_growth_is_rejected():
    basis = _BASE._basis()
    alternate_entries = tuple(
        replace(
            entry,
            disposition=DomainPolicyRequirementApplicationDisposition.NOT_COVERED,
            evidence_ids=(),
            rationale="Optional requirement explicitly not covered in alternate proposal.",
        )
        if entry.requirement_key == "edge_case_awareness"
        else entry
        for entry in basis["proposal"].requirement_applications
    )
    alternate_proposal = build_claim_domain_policy_requirement_mapping_proposal_v1(
        records=basis["records"],
        claim_id=basis["claim"].claim_id,
        as_of=_BASE._time(14),
        coverage=basis["coverage"],
        lineage=basis["lineage"],
        registry=basis["registry"],
        policy_ref=basis["specification"].policy_ref,
        specification_sha256=domain_evaluation_policy_specification_sha256_v1(
            basis["specification"]
        ),
        requirement_applications=alternate_entries,
    )
    alternate_review = review_claim_domain_policy_requirement_mapping_proposal_v1(
        proposal=alternate_proposal,
        review_id=ClaimPolicyRequirementMappingReviewId("mapping-review-2"),
        reviewer_ref=ClaimPolicyRequirementMappingReviewerRef(
            ClaimPolicyRequirementMappingReviewerKind.HUMAN,
            "human:mapping_reviewer",
        ),
        verdict=ClaimPolicyRequirementMappingReviewVerdict.APPROVE,
        reviewed_at=_BASE._time(16),
        rationale="Reviewed alternate complete mapping proposal.",
    )
    grown_ledger, _ = admit_claim_policy_requirement_mapping_review_v1(
        review_ledger=basis["review_ledger"],
        proposal=alternate_proposal,
        review=alternate_review,
    )

    with pytest.raises(
        InvalidDomainPolicyDirectionalEvaluation,
        match="PR12.11 governed application replay failed",
    ):
        _build_with(basis, review_ledger=grown_ledger)


def test_forged_mapping_review_admission_object_has_no_runtime_authority():
    basis = _BASE._basis()
    real = basis["review_admission"]
    forged = object.__new__(ClaimPolicyRequirementMappingReviewAdmission)
    for name in ClaimPolicyRequirementMappingReviewAdmission.__slots__:
        object.__setattr__(forged, name, getattr(real, name))

    with pytest.raises(
        InvalidDomainPolicyDirectionalEvaluation,
        match="PR12.11 governed application replay failed",
    ):
        _build_with(basis, review_admission=forged)


def test_real_pr12_12_claim_evaluation_can_cross_pr11_3_append_only_boundary():
    basis = _BASE._basis()
    successor = EpistemicRecordSet(
        evidence_records=basis["records"].evidence_records,
        claims=basis["records"].claims,
        evaluations=(basis["evaluation"],),
    )
    transition = validate_epistemic_snapshot_successor_v1(
        predecessor=basis["records"],
        successor=successor,
    )
    assert transition.added_evaluation_ids == (basis["evaluation"].evaluation_id,)
    assert transition.retained_evaluation_ids == ()


def test_directional_identity_changes_when_complete_directional_basis_changes():
    supported = _BASE._basis()
    mixed = _BASE._basis(
        bearings=(
            _BASE.EvidenceBearing.SUPPORTS,
            _BASE.EvidenceBearing.SUPPORTS,
            _BASE.EvidenceBearing.CONTRADICTS,
        )
    )
    assert supported["evaluation"].evaluation_id != mixed["evaluation"].evaluation_id
    assert supported["receipt"].evaluation_sha256 != mixed["receipt"].evaluation_sha256


def test_pr12_12_is_not_promoted_to_package_root_authority_surface():
    import capability_lab

    assert not hasattr(
        capability_lab,
        "build_claim_domain_policy_directional_evaluation_v1",
    )
    assert not hasattr(
        capability_lab,
        "ClaimDomainPolicyDirectionalEvaluationReceipt",
    )


def test_evaluation_id_is_not_derived_from_selected_requirement_evidence_only():
    basis = _BASE._basis(
        bearings=(
            _BASE.EvidenceBearing.SUPPORTS,
            _BASE.EvidenceBearing.SUPPORTS,
            _BASE.EvidenceBearing.CONTRADICTS,
        )
    )
    mapped = {
        evidence_id
        for entry in basis["application"].requirement_applications
        for evidence_id in entry.evidence_ids
    }
    assert mapped == {EvidenceId("e1"), EvidenceId("e2")}
    assert EvidenceId("e3") not in mapped
    assert EvidenceId("e3") in {
        item.evidence_id for item in basis["evaluation"].evidence_assessments
    }
