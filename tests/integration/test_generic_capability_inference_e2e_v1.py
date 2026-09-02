from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from capability_lab.derivation import (
    ClaimDimensionBinding,
    CompletePortfolioStateDerivationError,
    CompletePortfolioStateDerivationRequest,
    derive_supported_state_from_complete_portfolio_v1,
)
from capability_lab.epistemics import (
    CapabilitySubjectRef,
    ClaimEvaluationId,
    ClaimScope,
    ConflictStatus,
    CoverageStatus,
    EpistemicRecordSet,
    EvaluationConclusion,
    EvaluationPolicyRef,
    EvaluatorKind,
    EvaluatorRef,
    EvidenceAssessment,
    EvidenceBearing,
    EvidenceReliability,
    InvalidClaimEvaluationPortfolio,
    InvalidEpistemicSnapshotSuccessor,
    build_claim_evidence_disposition_coverage_v1,
    build_claim_evidence_lineage_dependence_v1,
    build_complete_claim_evaluation_portfolio_v1,
    build_complete_claim_evidence_candidate_portfolio_v1,
    validate_epistemic_snapshot_successor_v1,
    validate_exact_claim_evaluation_selection_v1,
)
from capability_lab.evaluation_policy import (
    ClaimPolicyRequirementMappingReviewId,
    ClaimPolicyRequirementMappingReviewerKind,
    ClaimPolicyRequirementMappingReviewerRef,
    ClaimPolicyRequirementMappingReviewLedger,
    ClaimPolicyRequirementMappingReviewVerdict,
    DomainEvaluationPolicyRegistry,
    DomainEvaluationPolicyRequirement,
    DomainEvaluationPolicyReviewId,
    DomainEvaluationPolicyReviewerKind,
    DomainEvaluationPolicyReviewerRef,
    DomainEvaluationPolicyReviewLedger,
    DomainEvaluationPolicyReviewVerdict,
    DomainEvaluationPolicySpecification,
    DomainPolicyRequirementApplicationDisposition,
    DomainPolicyRequirementApplicationEntry,
    admit_claim_policy_requirement_mapping_review_v1,
    admit_domain_evaluation_policy_review_v1,
    admit_domain_evaluation_policy_v1,
    apply_admitted_domain_policy_requirements_v1,
    build_claim_domain_policy_directional_evaluation_v1,
    build_claim_domain_policy_requirement_mapping_proposal_v1,
    domain_evaluation_policy_specification_sha256_v1,
    review_claim_domain_policy_requirement_mapping_proposal_v1,
    review_domain_evaluation_policy_specification_v1,
)
from capability_lab.interpretation import (
    ExternalEvidenceHumanClaimEvaluationDecision,
    ExternalEvidenceInterpretationProposalId,
    ExternalEvidenceInterpretationProposerKind,
    ExternalEvidenceInterpretationProposerRef,
    ExternalEvidenceInterpretationReviewId,
    ExternalEvidenceInterpretationReviewLedger,
    ExternalEvidenceInterpretationReviewerKind,
    ExternalEvidenceInterpretationReviewerRef,
    ExternalEvidenceInterpretationReviewVerdict,
    admit_external_evidence_claim_interpretation_review_v1,
    evaluate_materialized_external_evidence_claim_v1,
    materialize_accepted_external_evidence_interpretation_claim_v1,
    propose_external_evidence_claim_interpretation_v1,
    review_external_evidence_claim_interpretation_v1,
)
from capability_lab.observations import (
    ExternalObservationContextFactor,
    ExternalObservationContextFactorKind,
    ExternalObservationEnvelope,
    ExternalObservationEvidenceMaterializationId,
    ExternalObservationEvidenceMaterializationReview,
    ExternalObservationEvidenceMaterializationVerdict,
    ExternalObservationEvidenceReviewId,
    ExternalObservationEvidenceReviewerKind,
    ExternalObservationEvidenceReviewerRef,
    ExternalObservationForm,
    ExternalObservationId,
    ExternalObservationLedger,
    ExternalObservationOriginKind,
    ExternalObservationPayloadRef,
    ExternalObservationSourceKind,
    ExternalObservationSourceRef,
    REVIEWED_EXTERNAL_OBSERVATION_TO_EVIDENCE_POLICY_V1,
    admit_external_observation_v1,
    external_observation_evidence_materialization_candidate_sha256_v1,
    propose_external_observation_evidence_materialization_v1,
    resolve_reviewed_external_observation_evidence_materialization_v1,
)
from capability_lab.semantics import (
    CapabilityCatalog,
    CapabilityConcept,
    CapabilityId,
    CapabilityNamespace,
)
from capability_lab.state import (
    CompetenceDimensionDefinition,
    CompetenceFrame,
    CompetenceFrameId,
    CurrentStateSelectionAction,
    CurrentStateSelectionMechanismKind,
    CurrentStateSelectionPolicyRef,
    CurrentStateSelectorRef,
    DimensionConflictStatus,
    DimensionStanding,
    InvalidCurrentStateSelection,
    InvalidPersonalCapabilityStateAcceptance,
    PersonalCapabilityCurrentStateSelectionAuthorityBasis,
    PersonalCapabilityCurrentStateSelectionHistory,
    PersonalCapabilityCurrentStateSelectionRequest,
    PersonalCapabilityStateAcceptanceAdmission,
    PersonalCapabilityStateAcceptanceRequest,
    PersonalCapabilityStateAcceptanceSet,
    PersonalCapabilityStateId,
    PersonalCapabilityStateSet,
    StateAcceptanceMechanismKind,
    StateAcceptancePolicyRef,
    StateAccepterRef,
    accept_persisted_personal_capability_state_v1,
    build_complete_current_state_candidate_portfolio_v1,
    resolve_current_personal_capability_state_selection_v1,
    select_current_personal_capability_state_v1,
    validate_personal_capability_current_state_selection_v1,
    validate_personal_capability_state_acceptance_set_successor_v1,
    validate_personal_capability_state_set_successor_v1,
)


T0 = datetime(2026, 9, 1, 6, 0, tzinfo=timezone.utc)


def _at(minutes: int) -> datetime:
    return T0 + timedelta(minutes=minutes)


def _catalog() -> CapabilityCatalog:
    return CapabilityCatalog(
        namespaces=(
            CapabilityNamespace(
                namespace_id="research",
                display_name="Research",
                description="Research capabilities.",
            ),
        ),
        concepts=(
            CapabilityConcept(
                capability_id=CapabilityId.parse("research:signal_reasoning"),
                name="Signal reasoning",
                definition="Reason about bounded structured signals and evidence.",
            ),
        ),
    )


def _scope() -> ClaimScope:
    return ClaimScope(
        "Bounded interpretation of supplied signal evidence.",
        ("bounded_reasoning",),
    )


def _observation(*, suffix: str = "a", minute: int = 0) -> ExternalObservationEnvelope:
    return ExternalObservationEnvelope(
        observation_id=ExternalObservationId(f"obs-pr12-13-{suffix}"),
        subject_ref=CapabilitySubjectRef("subject-pr12-13"),
        source_ref=ExternalObservationSourceRef(
            ExternalObservationSourceKind.APPLICATION,
            "generic_external_workspace",
        ),
        source_event_id=f"event-pr12-13-{suffix}",
        form=ExternalObservationForm.ARTIFACT,
        origin_kind=ExternalObservationOriginKind.MIXED,
        observed_at=_at(minute),
        captured_at=_at(minute + 1),
        observation_started_at=_at(minute) - timedelta(minutes=2),
        context_factors=(
            ExternalObservationContextFactor(
                ExternalObservationContextFactorKind.ASSISTANCE,
                "A general-purpose assistant was available.",
            ),
            ExternalObservationContextFactor(
                ExternalObservationContextFactorKind.TOOL,
                "Python",
            ),
        ),
        payload_refs=(
            ExternalObservationPayloadRef(
                ref=f"artifact-pr12-13-{suffix}",
                sha256=(suffix[0] if suffix[0] in "abcdef" else "a") * 64,
                byte_size=256,
                media_type="text/plain",
            ),
        ),
    )


def _materialize_observation(
    *,
    ledger: ExternalObservationLedger,
    observation: ExternalObservationEnvelope,
    suffix: str,
    proposed_at: datetime,
    reviewed_at: datetime,
):
    ledger = admit_external_observation_v1(
        ledger=ledger,
        observation=observation,
    )
    candidate = propose_external_observation_evidence_materialization_v1(
        ledger=ledger,
        observation_id=observation.observation_id,
        materialization_id=ExternalObservationEvidenceMaterializationId(
            f"materialization-pr12-13-{suffix}"
        ),
        proposed_at=proposed_at,
    )
    review = ExternalObservationEvidenceMaterializationReview(
        review_id=ExternalObservationEvidenceReviewId(
            f"observation-review-pr12-13-{suffix}"
        ),
        materialization_id=candidate.materialization_id,
        candidate_sha256=external_observation_evidence_materialization_candidate_sha256_v1(
            candidate
        ),
        policy_ref=REVIEWED_EXTERNAL_OBSERVATION_TO_EVIDENCE_POLICY_V1,
        reviewer_ref=ExternalObservationEvidenceReviewerRef(
            ExternalObservationEvidenceReviewerKind.HUMAN,
            "human-observation-reviewer",
        ),
        verdict=ExternalObservationEvidenceMaterializationVerdict.MATERIALIZE,
        reviewed_at=reviewed_at,
        rationale="Human admits this exact external observation as neutral evidence.",
    )
    evidence, receipt = resolve_reviewed_external_observation_evidence_materialization_v1(
        ledger=ledger,
        candidate=candidate,
        review=review,
    )
    assert evidence is not None
    return ledger, candidate, review, evidence, receipt


def _claim_chain(evidence_snapshot: EpistemicRecordSet):
    catalog = _catalog()
    evidence = evidence_snapshot.evidence_records[0]
    candidate = propose_external_evidence_claim_interpretation_v1(
        epistemic_snapshot=evidence_snapshot,
        evidence_id=evidence.evidence_id,
        catalog=catalog,
        concept_ref=catalog.concepts[0].ref,
        claim_statement="The subject can reason about bounded signal evidence.",
        claim_scope=_scope(),
        proposer_ref=ExternalEvidenceInterpretationProposerRef(
            ExternalEvidenceInterpretationProposerKind.MODEL,
            "model-interpretation-proposer",
        ),
        proposal_id=ExternalEvidenceInterpretationProposalId(
            "interpretation-pr12-13"
        ),
        proposed_at=_at(4),
        rationale="The retained artifact may concern the bounded signal-reasoning claim.",
    )
    review = review_external_evidence_claim_interpretation_v1(
        epistemic_snapshot=evidence_snapshot,
        catalog=catalog,
        candidate=candidate,
        review_id=ExternalEvidenceInterpretationReviewId(
            "interpretation-review-pr12-13"
        ),
        reviewer_ref=ExternalEvidenceInterpretationReviewerRef(
            ExternalEvidenceInterpretationReviewerKind.HUMAN,
            "human-interpretation-reviewer",
        ),
        verdict=ExternalEvidenceInterpretationReviewVerdict.ACCEPT,
        reviewed_at=_at(5),
        rationale="Human accepts this exact evidence-to-claim interpretation only.",
    )
    review_ledger = admit_external_evidence_claim_interpretation_review_v1(
        review_ledger=ExternalEvidenceInterpretationReviewLedger(),
        epistemic_snapshot=evidence_snapshot,
        catalog=catalog,
        candidate=candidate,
        review=review,
    )
    materialization = materialize_accepted_external_evidence_interpretation_claim_v1(
        epistemic_snapshot=evidence_snapshot,
        catalog=catalog,
        candidate=candidate,
        review_ledger=review_ledger,
    )
    return catalog, candidate, review, review_ledger, materialization


def _pr12_5(
    *,
    evidence_snapshot: EpistemicRecordSet,
    catalog,
    candidate,
    review_ledger,
    materialization,
):
    decision = ExternalEvidenceHumanClaimEvaluationDecision(
        evaluator_ref=EvaluatorRef(
            EvaluatorKind.HUMAN,
            "human-generic-evidence-evaluator",
        ),
        evaluated_at=_at(6),
        bearing=EvidenceBearing.SUPPORTS,
        reliability=EvidenceReliability.HIGH,
        coverage_status=CoverageStatus.PARTIAL,
        conclusion=EvaluationConclusion.INSUFFICIENT,
        evidence_coverage_note="The artifact bears on the claim but does not itself establish domain sufficiency.",
        claim_coverage_notes="Generic PR12.5 policy has no domain sufficiency rule.",
        evidence_rationale="The exact retained artifact supports part of the bounded proposition.",
        evaluation_rationale="Preserve evidence-level support while remaining claim-wide insufficient.",
    )
    return evaluate_materialized_external_evidence_claim_v1(
        materialization_predecessor_snapshot=evidence_snapshot,
        current_epistemic_snapshot=materialization.successor_snapshot,
        catalog=catalog,
        candidate=candidate,
        review_ledger=review_ledger,
        materialization=materialization,
        decision=decision,
    )


def _domain_policy(claim):
    specification = DomainEvaluationPolicySpecification(
        policy_ref=EvaluationPolicyRef(
            "research",
            "signal_reasoning_domain_review",
            1,
        ),
        concept_ref=claim.concept_ref,
        claim_scope=claim.scope,
        requirements=(
            DomainEvaluationPolicyRequirement(
                "bounded_reasoning",
                "The evidence semantically covers bounded signal reasoning.",
                True,
            ),
            DomainEvaluationPolicyRequirement(
                "explanation_quality",
                "The evidence semantically covers a bounded explanatory account.",
                True,
            ),
        ),
    )
    review = review_domain_evaluation_policy_specification_v1(
        specification=specification,
        review_id=DomainEvaluationPolicyReviewId("policy-review-pr12-13"),
        reviewer_ref=DomainEvaluationPolicyReviewerRef(
            DomainEvaluationPolicyReviewerKind.HUMAN,
            "human-domain-policy-reviewer",
        ),
        verdict=DomainEvaluationPolicyReviewVerdict.APPROVE,
        reviewed_at=_at(5),
        rationale="Human reviewed the exact declarative domain sufficiency policy.",
    )
    review_ledger, review_admission = admit_domain_evaluation_policy_review_v1(
        review_ledger=DomainEvaluationPolicyReviewLedger(),
        specification=specification,
        review=review,
    )
    registry, registry_admission = admit_domain_evaluation_policy_v1(
        registry=DomainEvaluationPolicyRegistry(),
        review_ledger=review_ledger,
        review_admission=review_admission,
        specification=specification,
        admitted_at=_at(6),
    )
    return specification, registry, registry_admission


def _pr12_8_to_12(
    *,
    records: EpistemicRecordSet,
    claim,
    evidence_assessments: tuple[EvidenceAssessment, ...],
    mapping_entries: tuple[DomainPolicyRequirementApplicationEntry, ...],
    review_id: str = "mapping-review-pr12-13",
):
    specification, registry, _ = _domain_policy(claim)
    as_of = _at(8)

    candidate_portfolio = build_complete_claim_evidence_candidate_portfolio_v1(
        records=records,
        claim_id=claim.claim_id,
        as_of=as_of,
    )
    coverage = build_claim_evidence_disposition_coverage_v1(
        records=records,
        claim_id=claim.claim_id,
        as_of=as_of,
        dispositions=evidence_assessments,
    )
    lineage = build_claim_evidence_lineage_dependence_v1(
        records=records,
        claim_id=claim.claim_id,
        as_of=as_of,
        coverage=coverage,
    )
    proposal = build_claim_domain_policy_requirement_mapping_proposal_v1(
        records=records,
        claim_id=claim.claim_id,
        as_of=as_of,
        coverage=coverage,
        lineage=lineage,
        registry=registry,
        policy_ref=specification.policy_ref,
        specification_sha256=domain_evaluation_policy_specification_sha256_v1(
            specification
        ),
        requirement_applications=mapping_entries,
    )
    mapping_review = review_claim_domain_policy_requirement_mapping_proposal_v1(
        proposal=proposal,
        review_id=ClaimPolicyRequirementMappingReviewId(review_id),
        reviewer_ref=ClaimPolicyRequirementMappingReviewerRef(
            ClaimPolicyRequirementMappingReviewerKind.HUMAN,
            "human-requirement-mapping-reviewer",
        ),
        verdict=ClaimPolicyRequirementMappingReviewVerdict.APPROVE,
        reviewed_at=_at(9),
        rationale="Human reviewed the exact semantic requirement mapping.",
    )
    mapping_ledger, mapping_admission = admit_claim_policy_requirement_mapping_review_v1(
        review_ledger=ClaimPolicyRequirementMappingReviewLedger(),
        proposal=proposal,
        review=mapping_review,
    )
    application = apply_admitted_domain_policy_requirements_v1(
        records=records,
        claim_id=claim.claim_id,
        as_of=as_of,
        coverage=coverage,
        lineage=lineage,
        registry=registry,
        proposal=proposal,
        review_ledger=mapping_ledger,
        review_admission=mapping_admission,
    )
    evaluation, receipt = build_claim_domain_policy_directional_evaluation_v1(
        records=records,
        claim_id=claim.claim_id,
        as_of=as_of,
        coverage=coverage,
        lineage=lineage,
        registry=registry,
        proposal=proposal,
        review_ledger=mapping_ledger,
        review_admission=mapping_admission,
        application=application,
    )
    return {
        "candidate_portfolio": candidate_portfolio,
        "coverage": coverage,
        "lineage": lineage,
        "application": application,
        "evaluation": evaluation,
        "receipt": receipt,
    }


def _frame() -> CompetenceFrame:
    return CompetenceFrame(
        CompetenceFrameId.parse("research:signal_reasoning_frame"),
        1,
        "Signal reasoning frame",
        "A minimal frame used only to audit the governed generic handoff.",
        (
            CompetenceDimensionDefinition(
                "reasoning",
                "Reasoning",
                "Bounded signal-reasoning dimension.",
            ),
        ),
    )


def _positive_basis():
    observation = _observation()
    ledger, observation_candidate, observation_review, evidence, observation_receipt = (
        _materialize_observation(
            ledger=ExternalObservationLedger(subject_ref=observation.subject_ref),
            observation=observation,
            suffix="a",
            proposed_at=_at(2),
            reviewed_at=_at(3),
        )
    )

    empty_epistemics = EpistemicRecordSet()
    evidence_snapshot = EpistemicRecordSet(evidence_records=(evidence,))
    evidence_transition = validate_epistemic_snapshot_successor_v1(
        predecessor=empty_epistemics,
        successor=evidence_snapshot,
    )

    catalog, interpretation_candidate, interpretation_review, interpretation_ledger, materialization = (
        _claim_chain(evidence_snapshot)
    )
    pr12_5 = _pr12_5(
        evidence_snapshot=evidence_snapshot,
        catalog=catalog,
        candidate=interpretation_candidate,
        review_ledger=interpretation_ledger,
        materialization=materialization,
    )
    claim = materialization.claim

    assessment = EvidenceAssessment(
        evidence_id=evidence.evidence_id,
        bearing=EvidenceBearing.SUPPORTS,
        reliability=EvidenceReliability.HIGH,
        coverage_note="The exact external artifact is explicitly dispositioned for the domain policy.",
        rationale="Human-visible disposition retained across the complete PR12.9 universe.",
    )
    mappings = (
        DomainPolicyRequirementApplicationEntry(
            "bounded_reasoning",
            DomainPolicyRequirementApplicationDisposition.COVERED,
            (evidence.evidence_id,),
            "The exact artifact semantically covers bounded reasoning.",
        ),
        DomainPolicyRequirementApplicationEntry(
            "explanation_quality",
            DomainPolicyRequirementApplicationDisposition.COVERED,
            (evidence.evidence_id,),
            "The same artifact also semantically covers the required explanation.",
        ),
    )
    pr12_12 = _pr12_8_to_12(
        records=pr12_5.successor_snapshot,
        claim=claim,
        evidence_assessments=(assessment,),
        mapping_entries=mappings,
    )
    domain_evaluation = pr12_12["evaluation"]

    final_epistemics = EpistemicRecordSet(
        evidence_records=pr12_5.successor_snapshot.evidence_records,
        claims=pr12_5.successor_snapshot.claims,
        evaluations=pr12_5.successor_snapshot.evaluations + (domain_evaluation,),
    )
    domain_evaluation_transition = validate_epistemic_snapshot_successor_v1(
        predecessor=pr12_5.successor_snapshot,
        successor=final_epistemics,
    )

    portfolio = build_complete_claim_evaluation_portfolio_v1(
        records=final_epistemics,
        subject_ref=claim.subject_ref,
        concept_ref=claim.concept_ref,
        as_of=domain_evaluation.evaluated_at,
    )
    selected = validate_exact_claim_evaluation_selection_v1(
        records=final_epistemics,
        portfolio=portfolio,
        selected_evaluation_ids=portfolio.admissible_evaluation_ids,
    )

    frame = _frame()
    state = derive_supported_state_from_complete_portfolio_v1(
        records=final_epistemics,
        frame=frame,
        portfolio=portfolio,
        request=CompletePortfolioStateDerivationRequest(
            state_id=PersonalCapabilityStateId("state-pr12-13-signal-reasoning"),
            derived_at=_at(10),
            claim_dimension_bindings=(
                ClaimDimensionBinding(claim.claim_id, ("reasoning",)),
            ),
        ),
    )

    empty_states = PersonalCapabilityStateSet(claim.subject_ref)
    persisted_states = PersonalCapabilityStateSet(claim.subject_ref, (state,))
    state_transition = validate_personal_capability_state_set_successor_v1(
        predecessor=empty_states,
        successor=persisted_states,
    )

    acceptance = accept_persisted_personal_capability_state_v1(
        predecessor=empty_states,
        successor=persisted_states,
        request=PersonalCapabilityStateAcceptanceRequest(
            state_id=state.state_id,
            acceptance_policy_ref=StateAcceptancePolicyRef.parse(
                "research:pr12_13_state_acceptance@1"
            ),
            accepter_ref=StateAccepterRef(
                StateAcceptanceMechanismKind.HUMAN,
                "human-state-accepter",
            ),
            accepted_at=_at(11),
            rationale="Human explicitly accepts this exact persisted state for governance use.",
        ),
    )
    acceptance_admission = PersonalCapabilityStateAcceptanceAdmission(
        acceptance=acceptance,
        persistence_predecessor=empty_states,
        persistence_successor=persisted_states,
    )
    empty_acceptances = PersonalCapabilityStateAcceptanceSet(claim.subject_ref)
    accepted_states = PersonalCapabilityStateAcceptanceSet(
        claim.subject_ref,
        (acceptance,),
    )
    acceptance_transition = validate_personal_capability_state_acceptance_set_successor_v1(
        state_snapshot=persisted_states,
        predecessor=empty_acceptances,
        successor=accepted_states,
        admissions=(acceptance_admission,),
    )

    selection_history_empty = PersonalCapabilityCurrentStateSelectionHistory(
        claim.subject_ref
    )
    selection_history = select_current_personal_capability_state_v1(
        state_snapshot=persisted_states,
        acceptance_predecessor=empty_acceptances,
        acceptance_successor=accepted_states,
        acceptance_admissions=(acceptance_admission,),
        selection_history=selection_history_empty,
        request=PersonalCapabilityCurrentStateSelectionRequest(
            concept_ref=state.concept_ref,
            frame_ref=state.frame_ref,
            action=CurrentStateSelectionAction.SELECT,
            selected_state_id=state.state_id,
            selection_policy_ref=CurrentStateSelectionPolicyRef.parse(
                "research:pr12_13_current_state_selection@1"
            ),
            selector_ref=CurrentStateSelectorRef(
                CurrentStateSelectionMechanismKind.HUMAN,
                "human-current-state-selector",
            ),
            selected_at=_at(12),
            rationale="Human explicitly selects the accepted state as current.",
        ),
    )
    selection = selection_history.selections[0]
    authority_basis = PersonalCapabilityCurrentStateSelectionAuthorityBasis(
        selection=selection,
        state_snapshot=persisted_states,
        acceptance_predecessor=empty_acceptances,
        acceptance_successor=accepted_states,
        acceptance_admissions=(acceptance_admission,),
    )
    current = validate_personal_capability_current_state_selection_v1(
        authority_bases=(authority_basis,),
        history=selection_history,
        concept_ref=state.concept_ref,
        frame_ref=state.frame_ref,
    )

    return {
        "observation": observation,
        "observation_ledger": ledger,
        "observation_candidate": observation_candidate,
        "observation_review": observation_review,
        "observation_receipt": observation_receipt,
        "evidence": evidence,
        "empty_epistemics": empty_epistemics,
        "evidence_snapshot": evidence_snapshot,
        "evidence_transition": evidence_transition,
        "catalog": catalog,
        "interpretation_candidate": interpretation_candidate,
        "interpretation_review": interpretation_review,
        "interpretation_ledger": interpretation_ledger,
        "materialization": materialization,
        "pr12_5": pr12_5,
        "pr12_12": pr12_12,
        "final_epistemics": final_epistemics,
        "domain_evaluation_transition": domain_evaluation_transition,
        "portfolio": portfolio,
        "selected_evaluation_ids": selected,
        "frame": frame,
        "state": state,
        "empty_states": empty_states,
        "persisted_states": persisted_states,
        "state_transition": state_transition,
        "acceptance": acceptance,
        "acceptance_admission": acceptance_admission,
        "empty_acceptances": empty_acceptances,
        "accepted_states": accepted_states,
        "acceptance_transition": acceptance_transition,
        "selection_history_empty": selection_history_empty,
        "selection_history": selection_history,
        "selection": selection,
        "authority_basis": authority_basis,
        "current": current,
    }


def _reasoning_dimension(state):
    return next(item for item in state.dimensions if item.dimension_key == "reasoning")


def test_generic_external_observation_reaches_governed_current_state_without_shortcut():
    basis = _positive_basis()
    pr12_5_eval = basis["pr12_5"].evaluation
    pr12_12_eval = basis["pr12_12"]["evaluation"]

    assert basis["evidence_transition"].added_evidence_ids == (basis["evidence"].evidence_id,)
    assert basis["materialization"].succession_receipt.added_claim_ids == (
        basis["materialization"].claim.claim_id,
    )
    assert pr12_5_eval.conclusion is EvaluationConclusion.INSUFFICIENT
    assert pr12_5_eval.coverage.status is CoverageStatus.PARTIAL
    assert pr12_12_eval.conclusion is EvaluationConclusion.SUPPORTED
    assert pr12_12_eval.coverage.status is CoverageStatus.SUFFICIENT_FOR_CLAIM
    assert basis["pr12_12"]["application"].required_requirement_coverage_complete is True

    expected_evaluations = tuple(sorted((pr12_5_eval.evaluation_id, pr12_12_eval.evaluation_id)))
    assert basis["domain_evaluation_transition"].retained_evaluation_ids == (pr12_5_eval.evaluation_id,)
    assert basis["domain_evaluation_transition"].added_evaluation_ids == (pr12_12_eval.evaluation_id,)
    assert basis["portfolio"].admissible_evaluation_ids == expected_evaluations
    assert basis["selected_evaluation_ids"] == expected_evaluations

    reasoning = _reasoning_dimension(basis["state"])
    assert reasoning.basis_evaluation_ids == expected_evaluations
    assert reasoning.standing is DimensionStanding.SUPPORTED
    assert reasoning.conflict_status is DimensionConflictStatus.NONE
    assert reasoning.supported_claim_ids == (basis["materialization"].claim.claim_id,)

    assert basis["state_transition"].added_state_ids == (basis["state"].state_id,)
    assert basis["acceptance"].state_id == basis["state"].state_id
    assert basis["selection"].selected_state_id == basis["state"].state_id
    assert basis["current"] is not None
    assert basis["current"].selected_state_id == basis["state"].state_id


def test_complete_history_cannot_drop_older_pr12_5_evaluation():
    basis = _positive_basis()
    with pytest.raises(InvalidClaimEvaluationPortfolio, match="omits admissible claim evaluation"):
        validate_exact_claim_evaluation_selection_v1(
            records=basis["final_epistemics"],
            portfolio=basis["portfolio"],
            selected_evaluation_ids=(basis["pr12_12"]["evaluation"].evaluation_id,),
        )


def test_free_standing_pr12_12_evaluation_has_no_pr11_4_membership_before_persistence():
    basis = _positive_basis()
    before = basis["pr12_5"].successor_snapshot
    portfolio = build_complete_claim_evaluation_portfolio_v1(
        records=before,
        subject_ref=basis["materialization"].claim.subject_ref,
        concept_ref=basis["materialization"].claim.concept_ref,
        as_of=basis["pr12_12"]["evaluation"].evaluated_at,
    )
    assert basis["pr12_12"]["evaluation"].evaluation_id not in portfolio.admissible_evaluation_ids
    with pytest.raises(InvalidClaimEvaluationPortfolio, match="inadmissible claim evaluation"):
        validate_exact_claim_evaluation_selection_v1(
            records=before,
            portfolio=portfolio,
            selected_evaluation_ids=portfolio.admissible_evaluation_ids
            + (basis["pr12_12"]["evaluation"].evaluation_id,),
        )


def test_pr11_3_rejects_same_pr12_12_evaluation_id_with_changed_content():
    basis = _positive_basis()
    forged = replace(
        basis["pr12_12"]["evaluation"],
        rationale="Changed bytes under retained deterministic evaluation identity.",
    )
    replacement = EpistemicRecordSet(
        evidence_records=basis["final_epistemics"].evidence_records,
        claims=basis["final_epistemics"].claims,
        evaluations=(basis["pr12_5"].evaluation, forged),
    )
    with pytest.raises(InvalidEpistemicSnapshotSuccessor, match="may not mutate retained claim evaluation"):
        validate_epistemic_snapshot_successor_v1(
            predecessor=basis["final_epistemics"],
            successor=replacement,
        )


def test_historical_evaluation_append_stales_old_pr11_4_portfolio():
    basis = _positive_basis()
    historical = replace(
        basis["pr12_5"].evaluation,
        evaluation_id=ClaimEvaluationId("historical-pr12-13-generic-insufficient"),
        evaluated_at=_at(7),
        rationale="Historical separately identified evaluation retained by append-only persistence.",
    )
    extended = EpistemicRecordSet(
        evidence_records=basis["final_epistemics"].evidence_records,
        claims=basis["final_epistemics"].claims,
        evaluations=basis["final_epistemics"].evaluations + (historical,),
    )
    validate_epistemic_snapshot_successor_v1(
        predecessor=basis["final_epistemics"],
        successor=extended,
    )
    with pytest.raises(InvalidClaimEvaluationPortfolio, match="portfolio snapshot does not match"):
        validate_exact_claim_evaluation_selection_v1(
            records=extended,
            portfolio=basis["portfolio"],
            selected_evaluation_ids=basis["portfolio"].admissible_evaluation_ids,
        )
    rebuilt = build_complete_claim_evaluation_portfolio_v1(
        records=extended,
        subject_ref=basis["materialization"].claim.subject_ref,
        concept_ref=basis["materialization"].claim.concept_ref,
        as_of=basis["portfolio"].as_of,
    )
    assert historical.evaluation_id in rebuilt.admissible_evaluation_ids


def test_pr11_5_requires_complete_claim_dimension_binding_even_with_supported_evaluation():
    basis = _positive_basis()
    with pytest.raises(CompletePortfolioStateDerivationError, match="missing claim-dimension binding"):
        derive_supported_state_from_complete_portfolio_v1(
            records=basis["final_epistemics"],
            frame=basis["frame"],
            portfolio=basis["portfolio"],
            request=CompletePortfolioStateDerivationRequest(
                state_id=PersonalCapabilityStateId("state-pr12-13-missing-binding"),
                derived_at=_at(10),
                claim_dimension_bindings=(),
            ),
        )


def test_derived_but_unpersisted_state_cannot_be_accepted():
    basis = _positive_basis()
    with pytest.raises(InvalidPersonalCapabilityStateAcceptance):
        accept_persisted_personal_capability_state_v1(
            predecessor=basis["empty_states"],
            successor=basis["empty_states"],
            request=PersonalCapabilityStateAcceptanceRequest(
                state_id=basis["state"].state_id,
                acceptance_policy_ref=StateAcceptancePolicyRef.parse("research:pr12_13_state_acceptance@1"),
                accepter_ref=StateAccepterRef(StateAcceptanceMechanismKind.HUMAN, "human-state-accepter"),
                accepted_at=_at(11),
                rationale="Attempt to accept a state absent from persisted history.",
            ),
        )


def test_persisted_but_unaccepted_state_is_not_pr11_8_candidate():
    basis = _positive_basis()
    portfolio = build_complete_current_state_candidate_portfolio_v1(
        state_snapshot=basis["persisted_states"],
        acceptance_set=basis["empty_acceptances"],
        concept_ref=basis["state"].concept_ref,
        frame_ref=basis["state"].frame_ref,
        as_of=_at(11),
    )
    assert portfolio.candidate_state_ids == ()


def test_accepted_state_is_not_current_until_explicit_selection():
    basis = _positive_basis()
    assert resolve_current_personal_capability_state_selection_v1(
        history=basis["selection_history_empty"],
        concept_ref=basis["state"].concept_ref,
        frame_ref=basis["state"].frame_ref,
    ) is None


def test_structural_current_selection_is_not_pr11_8_authority_without_replay_basis():
    basis = _positive_basis()
    structural = resolve_current_personal_capability_state_selection_v1(
        history=basis["selection_history"],
        concept_ref=basis["state"].concept_ref,
        frame_ref=basis["state"].frame_ref,
    )
    assert structural is not None
    with pytest.raises(InvalidCurrentStateSelection):
        validate_personal_capability_current_state_selection_v1(
            authority_bases=(),
            history=basis["selection_history"],
            concept_ref=basis["state"].concept_ref,
            frame_ref=basis["state"].frame_ref,
        )
    governed = validate_personal_capability_current_state_selection_v1(
        authority_bases=(basis["authority_basis"],),
        history=basis["selection_history"],
        concept_ref=basis["state"].concept_ref,
        frame_ref=basis["state"].frame_ref,
    )
    assert governed == structural


def test_no_stage_in_e2e_trace_emits_permission_mastery_or_readiness_fields():
    basis = _positive_basis()
    artifacts = (
        basis["observation"],
        basis["evidence"],
        basis["materialization"].claim,
        basis["pr12_5"].evaluation,
        basis["pr12_12"]["evaluation"],
        basis["pr12_12"]["receipt"],
        basis["state"],
        basis["acceptance"],
        basis["selection"],
    )
    forbidden = {
        "permission",
        "permissions",
        "mastery",
        "readiness",
        "professional_authority",
        "human_worth",
    }
    for artifact in artifacts:
        field_names = set(getattr(artifact, "__dataclass_fields__", {}))
        assert field_names.isdisjoint(forbidden)


def test_mixed_pr12_12_remains_non_supported_and_unresolved_downstream():
    basis = _positive_basis()
    first = basis["evidence"]
    observation_b = _observation(suffix="b", minute=1)
    ledger_b, _, _, evidence_b, _ = _materialize_observation(
        ledger=basis["observation_ledger"],
        observation=observation_b,
        suffix="b",
        proposed_at=_at(3),
        reviewed_at=_at(4),
    )
    assert len(ledger_b.observations) == 2

    records = EpistemicRecordSet(
        evidence_records=basis["pr12_5"].successor_snapshot.evidence_records + (evidence_b,),
        claims=basis["pr12_5"].successor_snapshot.claims,
        evaluations=basis["pr12_5"].successor_snapshot.evaluations,
    )
    validate_epistemic_snapshot_successor_v1(
        predecessor=basis["pr12_5"].successor_snapshot,
        successor=records,
    )

    assessments = (
        EvidenceAssessment(
            evidence_id=first.evidence_id,
            bearing=EvidenceBearing.SUPPORTS,
            reliability=EvidenceReliability.HIGH,
            coverage_note="First retained evidence supports the bounded claim.",
            rationale="Explicit supporting disposition.",
        ),
        EvidenceAssessment(
            evidence_id=evidence_b.evidence_id,
            bearing=EvidenceBearing.CONTRADICTS,
            reliability=EvidenceReliability.HIGH,
            coverage_note="Second retained evidence contradicts the bounded claim.",
            rationale="Explicit contradicting disposition.",
        ),
    )
    mappings = (
        DomainPolicyRequirementApplicationEntry(
            "bounded_reasoning",
            DomainPolicyRequirementApplicationDisposition.COVERED,
            (first.evidence_id,),
            "Supporting evidence covers bounded reasoning.",
        ),
        DomainPolicyRequirementApplicationEntry(
            "explanation_quality",
            DomainPolicyRequirementApplicationDisposition.COVERED,
            (first.evidence_id,),
            "Supporting evidence covers explanation quality.",
        ),
    )
    mixed = _pr12_8_to_12(
        records=records,
        claim=basis["materialization"].claim,
        evidence_assessments=assessments,
        mapping_entries=mappings,
        review_id="mapping-review-pr12-13-mixed",
    )
    evaluation = mixed["evaluation"]
    assert evaluation.conclusion is EvaluationConclusion.MIXED
    assert evaluation.conflict_status is ConflictStatus.UNRESOLVED

    mixed_snapshot = EpistemicRecordSet(
        evidence_records=records.evidence_records,
        claims=records.claims,
        evaluations=records.evaluations + (evaluation,),
    )
    validate_epistemic_snapshot_successor_v1(
        predecessor=records,
        successor=mixed_snapshot,
    )
    portfolio = build_complete_claim_evaluation_portfolio_v1(
        records=mixed_snapshot,
        subject_ref=basis["materialization"].claim.subject_ref,
        concept_ref=basis["materialization"].claim.concept_ref,
        as_of=evaluation.evaluated_at,
    )
    state = derive_supported_state_from_complete_portfolio_v1(
        records=mixed_snapshot,
        frame=basis["frame"],
        portfolio=portfolio,
        request=CompletePortfolioStateDerivationRequest(
            state_id=PersonalCapabilityStateId("state-pr12-13-mixed"),
            derived_at=_at(10),
            claim_dimension_bindings=(
                ClaimDimensionBinding(basis["materialization"].claim.claim_id, ("reasoning",)),
            ),
        ),
    )
    reasoning = _reasoning_dimension(state)
    assert evaluation.evaluation_id in reasoning.basis_evaluation_ids
    assert reasoning.standing is DimensionStanding.INSUFFICIENT
    assert reasoning.conflict_status is DimensionConflictStatus.UNRESOLVED
