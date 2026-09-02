"""PR12.2 governed external evidence-to-claim interpretation proposal boundary v1."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import re
import unicodedata

from capability_lab.epistemics import (
    CapabilitySubjectRef,
    ClaimScope,
    EpistemicRecordSet,
    EvidenceId,
    EvidenceRecord,
    ProvenanceSourceKind,
)
from capability_lab.observations import (
    REVIEWED_EXTERNAL_OBSERVATION_TO_EVIDENCE_POLICY_V1,
    external_observation_materialized_evidence_sha256_v1,
)
from capability_lab.semantics import CapabilityCatalog, CapabilityConceptRef


class ExternalEvidenceInterpretationError(ValueError):
    """Base validation error for PR12.2 interpretation proposals."""


class InvalidExternalEvidenceInterpretation(ExternalEvidenceInterpretationError):
    pass


_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_NAMESPACE_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*$")
_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_EXTERNAL_EVIDENCE_ID_RE = re.compile(r"^external_observation:[0-9a-f]{64}$")
_CANDIDATE_HASH_DOMAIN = (
    b"capability_lab/external_evidence_claim_interpretation_candidate@1\x00"
)


def _fail(message: str) -> None:
    raise InvalidExternalEvidenceInterpretation(message)


def _exact(value: object, expected: type, label: str):
    if type(value) is not expected:
        _fail(f"{label} must use exact type {expected.__name__}")
    return value


def _opaque_id(value: object, label: str) -> str:
    if type(value) is not str or _ID_RE.fullmatch(value) is None:
        _fail(f"{label} must be a canonical opaque ASCII identifier")
    return value


def _sha256(value: object, label: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        _fail(f"{label} must be 64 lowercase hexadecimal SHA-256 characters")
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


@dataclass(frozen=True, order=True, slots=True)
class ExternalEvidenceInterpretationProposalId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _opaque_id(self.value, "proposal id"))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, order=True, slots=True)
class ExternalEvidenceInterpretationPolicyRef:
    namespace: str
    key: str
    revision: int

    def __post_init__(self) -> None:
        if type(self.namespace) is not str or _NAMESPACE_RE.fullmatch(self.namespace) is None:
            _fail("policy namespace must use canonical syntax")
        if type(self.key) is not str or _KEY_RE.fullmatch(self.key) is None:
            _fail("policy key must use canonical syntax")
        if type(self.revision) is not int or self.revision < 1:
            _fail("policy revision must be an integer >= 1")

    @classmethod
    def parse(cls, value: object) -> "ExternalEvidenceInterpretationPolicyRef":
        if type(value) is not str:
            _fail("policy ref must be a string")
        match = re.fullmatch(
            r"([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*):([a-z][a-z0-9_]*)@([1-9][0-9]*)",
            value,
        )
        if match is None:
            _fail("policy ref must use '<namespace>:<key>@<revision>'")
        return cls(match.group(1), match.group(2), int(match.group(3)))

    def __str__(self) -> str:
        return f"{self.namespace}:{self.key}@{self.revision}"


EXTERNAL_EVIDENCE_CLAIM_INTERPRETATION_POLICY_V1 = (
    ExternalEvidenceInterpretationPolicyRef(
        "capability_lab", "external_evidence_claim_interpretation_proposal", 1
    )
)


class ExternalEvidenceInterpretationProposerKind(str, Enum):
    HUMAN = "HUMAN"
    MODEL = "MODEL"


@dataclass(frozen=True, order=True, slots=True)
class ExternalEvidenceInterpretationProposerRef:
    kind: ExternalEvidenceInterpretationProposerKind
    ref: str

    def __post_init__(self) -> None:
        _exact(self.kind, ExternalEvidenceInterpretationProposerKind, "proposer kind")
        object.__setattr__(self, "ref", _opaque_id(self.ref, "proposer ref"))


@dataclass(frozen=True, slots=True)
class ExternalEvidenceClaimInterpretationCandidate:
    proposal_id: ExternalEvidenceInterpretationProposalId
    policy_ref: ExternalEvidenceInterpretationPolicyRef
    evidence_id: EvidenceId
    evidence_sha256: str
    subject_ref: CapabilitySubjectRef
    concept_ref: CapabilityConceptRef
    claim_statement: str
    claim_scope: ClaimScope
    proposer_ref: ExternalEvidenceInterpretationProposerRef
    proposed_at: datetime
    rationale: str

    def __post_init__(self) -> None:
        _exact(self.proposal_id, ExternalEvidenceInterpretationProposalId, "proposal_id")
        if self.policy_ref != EXTERNAL_EVIDENCE_CLAIM_INTERPRETATION_POLICY_V1:
            _fail("candidate must use the frozen PR12.2 policy")
        _exact(self.evidence_id, EvidenceId, "evidence_id")
        object.__setattr__(
            self, "evidence_sha256", _sha256(self.evidence_sha256, "evidence_sha256")
        )
        _exact(self.subject_ref, CapabilitySubjectRef, "subject_ref")
        _exact(self.concept_ref, CapabilityConceptRef, "concept_ref")
        object.__setattr__(
            self,
            "claim_statement",
            _text(self.claim_statement, "claim_statement"),
        )
        _exact(self.claim_scope, ClaimScope, "claim_scope")
        _exact(
            self.proposer_ref,
            ExternalEvidenceInterpretationProposerRef,
            "proposer_ref",
        )
        object.__setattr__(self, "proposed_at", _time(self.proposed_at, "proposed_at"))
        object.__setattr__(self, "rationale", _text(self.rationale, "rationale"))


def _strict_snapshot(snapshot: EpistemicRecordSet) -> EpistemicRecordSet:
    if type(snapshot) is not EpistemicRecordSet:
        _fail("epistemic_snapshot must use exact EpistemicRecordSet")
    try:
        restored = EpistemicRecordSet.from_json(snapshot.to_json())
    except (TypeError, ValueError) as exc:
        raise InvalidExternalEvidenceInterpretation(
            f"epistemic_snapshot failed strict reconstruction: {exc}"
        ) from exc
    if restored != snapshot:
        _fail("epistemic_snapshot must equal strict semantic reconstruction")
    return snapshot


def _strict_catalog(catalog: CapabilityCatalog) -> CapabilityCatalog:
    if type(catalog) is not CapabilityCatalog:
        _fail("catalog must use exact CapabilityCatalog")
    try:
        restored = CapabilityCatalog.from_json(catalog.to_json())
    except (TypeError, ValueError) as exc:
        raise InvalidExternalEvidenceInterpretation(
            f"catalog failed strict reconstruction: {exc}"
        ) from exc
    if restored != catalog:
        _fail("catalog must equal strict semantic reconstruction")
    return catalog


def _strict_candidate(
    candidate: ExternalEvidenceClaimInterpretationCandidate,
) -> ExternalEvidenceClaimInterpretationCandidate:
    if type(candidate) is not ExternalEvidenceClaimInterpretationCandidate:
        _fail("candidate must use exact ExternalEvidenceClaimInterpretationCandidate")
    try:
        restored = ExternalEvidenceClaimInterpretationCandidate(
            proposal_id=ExternalEvidenceInterpretationProposalId(candidate.proposal_id.value),
            policy_ref=ExternalEvidenceInterpretationPolicyRef(
                candidate.policy_ref.namespace,
                candidate.policy_ref.key,
                candidate.policy_ref.revision,
            ),
            evidence_id=EvidenceId(candidate.evidence_id.value),
            evidence_sha256=candidate.evidence_sha256,
            subject_ref=CapabilitySubjectRef(candidate.subject_ref.value),
            concept_ref=CapabilityConceptRef.parse(str(candidate.concept_ref)),
            claim_statement=candidate.claim_statement,
            claim_scope=ClaimScope(
                candidate.claim_scope.description,
                tuple(candidate.claim_scope.tags),
            ),
            proposer_ref=ExternalEvidenceInterpretationProposerRef(
                ExternalEvidenceInterpretationProposerKind(candidate.proposer_ref.kind.value),
                candidate.proposer_ref.ref,
            ),
            proposed_at=candidate.proposed_at,
            rationale=candidate.rationale,
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InvalidExternalEvidenceInterpretation):
            raise
        raise InvalidExternalEvidenceInterpretation(
            f"candidate failed strict semantic reconstruction: {exc}"
        ) from exc
    if restored != candidate:
        _fail("candidate must equal strict semantic reconstruction")
    return candidate


def _find_external_evidence(
    *,
    epistemic_snapshot: EpistemicRecordSet,
    evidence_id: EvidenceId,
) -> EvidenceRecord:
    snapshot = _strict_snapshot(epistemic_snapshot)
    _exact(evidence_id, EvidenceId, "evidence_id")
    matches = tuple(
        item for item in snapshot.evidence_records if item.evidence_id == evidence_id
    )
    if len(matches) != 1:
        _fail("selected evidence_id is absent or ambiguous in epistemic_snapshot")
    evidence = matches[0]
    _validate_pr12_1_external_evidence_shape(evidence)
    return evidence


def _validate_pr12_1_external_evidence_shape(evidence: EvidenceRecord) -> None:
    if type(evidence) is not EvidenceRecord:
        _fail("selected evidence must use exact EvidenceRecord")
    evidence_id = str(evidence.evidence_id)
    if _EXTERNAL_EVIDENCE_ID_RE.fullmatch(evidence_id) is None:
        _fail("selected evidence is not a PR12.1 external-observation EvidenceRecord")
    if evidence.outcome is not None:
        _fail("PR12.1 external evidence must remain neutral with outcome=None")
    if evidence.context.scope_tags != ("external_observation",):
        _fail("PR12.1 external evidence must retain exact external_observation scope")
    if len(evidence.provenance.sources) != 1:
        _fail("PR12.1 external evidence must retain one exact external source")
    source = evidence.provenance.sources[0]
    if source.kind is not ProvenanceSourceKind.EXTERNAL_RECORD or source.ref != evidence_id:
        _fail("PR12.1 external evidence provenance must bind its exact observation digest")
    if len(evidence.provenance.steps) != 1:
        _fail("PR12.1 external evidence must retain one materialization step")
    step = evidence.provenance.steps[0]
    if step.operation_key != "external_observation_materialize":
        _fail("selected evidence lacks the PR12.1 materialization operation")
    if step.mechanism_ref != str(REVIEWED_EXTERNAL_OBSERVATION_TO_EVIDENCE_POLICY_V1):
        _fail("selected evidence does not bind the frozen PR12.1 materialization policy")
    if step.occurred_at != evidence.recorded_at:
        _fail("PR12.1 materialization step time must equal evidence recorded_at")


def _require_exact_concept(
    *,
    catalog: CapabilityCatalog,
    concept_ref: CapabilityConceptRef,
) -> None:
    checked = _strict_catalog(catalog)
    _exact(concept_ref, CapabilityConceptRef, "concept_ref")
    matches = tuple(
        concept
        for concept in checked.concepts
        if concept.capability_id == concept_ref.capability_id
    )
    if len(matches) != 1:
        _fail("selected capability concept is absent or ambiguous in catalog")
    if matches[0].ref != concept_ref:
        _fail(
            "catalog validation requires the exact concept revision; "
            "silent latest-revision substitution is forbidden"
        )


def external_evidence_claim_interpretation_candidate_sha256_v1(
    candidate: ExternalEvidenceClaimInterpretationCandidate,
) -> str:
    _strict_candidate(candidate)
    from .serialization import external_evidence_claim_interpretation_candidate_to_json

    digest = hashlib.sha256()
    digest.update(_CANDIDATE_HASH_DOMAIN)
    digest.update(
        external_evidence_claim_interpretation_candidate_to_json(candidate).encode("utf-8")
    )
    return digest.hexdigest()


def validate_external_evidence_claim_interpretation_candidate_v1(
    *,
    epistemic_snapshot: EpistemicRecordSet,
    catalog: CapabilityCatalog,
    candidate: ExternalEvidenceClaimInterpretationCandidate,
) -> None:
    candidate = _strict_candidate(candidate)
    evidence = _find_external_evidence(
        epistemic_snapshot=epistemic_snapshot,
        evidence_id=candidate.evidence_id,
    )
    try:
        evidence_sha256 = external_observation_materialized_evidence_sha256_v1(evidence)
    except (TypeError, ValueError) as exc:
        raise InvalidExternalEvidenceInterpretation(
            f"cannot hash exact selected EvidenceRecord: {exc}"
        ) from exc
    if candidate.evidence_sha256 != evidence_sha256:
        _fail("candidate evidence_sha256 does not match exact selected EvidenceRecord")
    if candidate.subject_ref != evidence.subject_ref:
        _fail("candidate subject_ref does not match selected EvidenceRecord")
    _require_exact_concept(catalog=catalog, concept_ref=candidate.concept_ref)
    if candidate.proposed_at < evidence.recorded_at:
        _fail("candidate proposed_at must not predate EvidenceRecord recorded_at")


def propose_external_evidence_claim_interpretation_v1(
    *,
    epistemic_snapshot: EpistemicRecordSet,
    evidence_id: EvidenceId,
    catalog: CapabilityCatalog,
    concept_ref: CapabilityConceptRef,
    claim_statement: str,
    claim_scope: ClaimScope,
    proposer_ref: ExternalEvidenceInterpretationProposerRef,
    proposal_id: ExternalEvidenceInterpretationProposalId,
    proposed_at: datetime,
    rationale: str,
) -> ExternalEvidenceClaimInterpretationCandidate:
    """Propose claim relevance for one exact retained external EvidenceRecord.

    This function creates no CapabilityClaim, EvidenceAssessment, ClaimEvaluation,
    personal state, progression authority, readiness, mastery, score, or permission.
    """

    evidence = _find_external_evidence(
        epistemic_snapshot=epistemic_snapshot,
        evidence_id=evidence_id,
    )
    _require_exact_concept(catalog=catalog, concept_ref=concept_ref)
    proposed = _time(proposed_at, "proposed_at")
    if proposed < evidence.recorded_at:
        _fail("proposal must not predate selected EvidenceRecord recorded_at")
    try:
        candidate = ExternalEvidenceClaimInterpretationCandidate(
            proposal_id=proposal_id,
            policy_ref=EXTERNAL_EVIDENCE_CLAIM_INTERPRETATION_POLICY_V1,
            evidence_id=evidence.evidence_id,
            evidence_sha256=external_observation_materialized_evidence_sha256_v1(evidence),
            subject_ref=evidence.subject_ref,
            concept_ref=concept_ref,
            claim_statement=claim_statement,
            claim_scope=claim_scope,
            proposer_ref=proposer_ref,
            proposed_at=proposed,
            rationale=rationale,
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InvalidExternalEvidenceInterpretation):
            raise
        raise InvalidExternalEvidenceInterpretation(
            f"cannot construct interpretation candidate: {exc}"
        ) from exc
    validate_external_evidence_claim_interpretation_candidate_v1(
        epistemic_snapshot=epistemic_snapshot,
        catalog=catalog,
        candidate=candidate,
    )
    return candidate
