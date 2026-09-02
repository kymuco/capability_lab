"""PR12.4 accepted interpretation to deterministic CapabilityClaim materialization."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json

from capability_lab.epistemics import (
    ActorRef,
    CapabilityClaim,
    CapabilityClaimId,
    EpistemicRecordSet,
    EpistemicSnapshotSuccessionReceipt,
    ProvenanceSource,
    ProvenanceSourceKind,
    ProvenanceStep,
    ProvenanceTrail,
    epistemic_snapshot_sha256_v1,
    validate_epistemic_snapshot_successor_v1,
)
from capability_lab.semantics import CapabilityCatalog

from .core import (
    ExternalEvidenceClaimInterpretationCandidate,
    ExternalEvidenceInterpretationPolicyRef,
    ExternalEvidenceInterpretationProposalId,
    InvalidExternalEvidenceInterpretation,
    _exact,
    _sha256,
    _strict_candidate,
    _time,
    external_evidence_claim_interpretation_candidate_sha256_v1,
)
from .review import (
    ExternalEvidenceClaimInterpretationReview,
    ExternalEvidenceInterpretationReviewId,
    _strict_review,
    external_evidence_claim_interpretation_review_sha256_v1,
)
from .review_ledger import (
    ExternalEvidenceInterpretationReviewLedger,
    require_accepted_external_evidence_claim_interpretation_review_v1,
)

_CLAIM_SEMANTIC_HASH_DOMAIN = (
    b"capability_lab/external_interpretation_claim_semantics@1\x00"
)
_CLAIM_ID_HASH_DOMAIN = (
    b"capability_lab/external_interpretation_claim_record_identity@1\x00"
)
_CLAIM_HASH_DOMAIN = b"capability_lab/materialized_capability_claim@1\x00"
_RECEIPT_HASH_DOMAIN = (
    b"capability_lab/external_evidence_interpretation_claim_materialization_receipt@1\x00"
)
_MATERIALIZATION_OPERATION_KEY = "external_interpretation_claim_materialize"
_MATERIALIZATION_SOURCE_REF = "capability_lab"
_MATERIALIZATION_NOTE = (
    "Materialized exact human-admitted interpretation proposal as an evaluable "
    "CapabilityClaim; no truth or evidence-bearing conclusion is implied."
)

EXTERNAL_EVIDENCE_INTERPRETATION_CLAIM_MATERIALIZATION_POLICY_V1 = (
    ExternalEvidenceInterpretationPolicyRef(
        "capability_lab",
        "accepted_external_interpretation_claim_materialization",
        1,
    )
)


@dataclass(frozen=True, slots=True)
class ExternalEvidenceInterpretationClaimMaterializationReceipt:
    policy_ref: ExternalEvidenceInterpretationPolicyRef
    proposal_id: ExternalEvidenceInterpretationProposalId
    candidate_sha256: str
    review_id: ExternalEvidenceInterpretationReviewId
    review_sha256: str
    claim_id: CapabilityClaimId
    claim_sha256: str
    predecessor_snapshot_sha256: str
    successor_snapshot_sha256: str
    materialized_at: datetime

    def __post_init__(self) -> None:
        if self.policy_ref != EXTERNAL_EVIDENCE_INTERPRETATION_CLAIM_MATERIALIZATION_POLICY_V1:
            raise InvalidExternalEvidenceInterpretation(
                "materialization receipt must use the frozen PR12.4 policy"
            )
        _exact(self.proposal_id, ExternalEvidenceInterpretationProposalId, "proposal_id")
        object.__setattr__(
            self,
            "candidate_sha256",
            _sha256(self.candidate_sha256, "candidate_sha256"),
        )
        _exact(self.review_id, ExternalEvidenceInterpretationReviewId, "review_id")
        object.__setattr__(
            self,
            "review_sha256",
            _sha256(self.review_sha256, "review_sha256"),
        )
        _exact(self.claim_id, CapabilityClaimId, "claim_id")
        object.__setattr__(
            self,
            "claim_sha256",
            _sha256(self.claim_sha256, "claim_sha256"),
        )
        object.__setattr__(
            self,
            "predecessor_snapshot_sha256",
            _sha256(
                self.predecessor_snapshot_sha256,
                "predecessor_snapshot_sha256",
            ),
        )
        object.__setattr__(
            self,
            "successor_snapshot_sha256",
            _sha256(
                self.successor_snapshot_sha256,
                "successor_snapshot_sha256",
            ),
        )
        object.__setattr__(
            self,
            "materialized_at",
            _time(self.materialized_at, "materialized_at"),
        )

    def to_dict(self) -> dict:
        from .claim_materialization_serialization import (
            external_evidence_interpretation_claim_materialization_receipt_to_dict,
        )

        return external_evidence_interpretation_claim_materialization_receipt_to_dict(self)

    @classmethod
    def from_dict(
        cls,
        payload: object,
    ) -> "ExternalEvidenceInterpretationClaimMaterializationReceipt":
        from .claim_materialization_serialization import (
            external_evidence_interpretation_claim_materialization_receipt_from_dict,
        )

        return external_evidence_interpretation_claim_materialization_receipt_from_dict(
            payload
        )

    def to_json(self) -> str:
        from .claim_materialization_serialization import (
            external_evidence_interpretation_claim_materialization_receipt_to_json,
        )

        return external_evidence_interpretation_claim_materialization_receipt_to_json(self)

    @classmethod
    def from_json(
        cls,
        payload: object,
    ) -> "ExternalEvidenceInterpretationClaimMaterializationReceipt":
        from .claim_materialization_serialization import (
            external_evidence_interpretation_claim_materialization_receipt_from_json,
        )

        return external_evidence_interpretation_claim_materialization_receipt_from_json(
            payload
        )


@dataclass(frozen=True, slots=True)
class ExternalEvidenceInterpretationClaimMaterialization:
    """In-memory validated PR12.4 result.

    The PR11.3 succession receipt intentionally remains validator-issued and is
    therefore not reconstructed from untrusted serialized data.
    """

    claim: CapabilityClaim
    successor_snapshot: EpistemicRecordSet
    succession_receipt: EpistemicSnapshotSuccessionReceipt
    materialization_receipt: ExternalEvidenceInterpretationClaimMaterializationReceipt

    def __post_init__(self) -> None:
        _strict_claim(self.claim)
        _strict_snapshot(self.successor_snapshot, "successor_snapshot")
        if not isinstance(
            self.succession_receipt,
            EpistemicSnapshotSuccessionReceipt,
        ) or not self.succession_receipt.validator_issued:
            raise InvalidExternalEvidenceInterpretation(
                "succession_receipt must be validator-issued by PR11.3"
            )
        _strict_materialization_receipt(self.materialization_receipt)


def _strict_snapshot(
    snapshot: EpistemicRecordSet,
    label: str,
) -> EpistemicRecordSet:
    if type(snapshot) is not EpistemicRecordSet:
        raise InvalidExternalEvidenceInterpretation(
            f"{label} must use exact EpistemicRecordSet"
        )
    try:
        restored = EpistemicRecordSet.from_json(snapshot.to_json())
    except (TypeError, ValueError) as exc:
        raise InvalidExternalEvidenceInterpretation(
            f"{label} failed strict reconstruction: {exc}"
        ) from exc
    if restored != snapshot:
        raise InvalidExternalEvidenceInterpretation(
            f"{label} must equal strict semantic reconstruction"
        )
    return snapshot


def _strict_claim(claim: CapabilityClaim) -> CapabilityClaim:
    if type(claim) is not CapabilityClaim:
        raise InvalidExternalEvidenceInterpretation(
            "claim must use exact CapabilityClaim"
        )
    try:
        container = EpistemicRecordSet(claims=(claim,))
        restored = EpistemicRecordSet.from_json(container.to_json())
    except (TypeError, ValueError) as exc:
        raise InvalidExternalEvidenceInterpretation(
            f"claim failed strict reconstruction: {exc}"
        ) from exc
    if len(restored.claims) != 1 or restored.claims[0] != claim:
        raise InvalidExternalEvidenceInterpretation(
            "claim must equal strict semantic reconstruction"
        )
    return claim


def _strict_materialization_receipt(
    receipt: ExternalEvidenceInterpretationClaimMaterializationReceipt,
) -> ExternalEvidenceInterpretationClaimMaterializationReceipt:
    if type(receipt) is not ExternalEvidenceInterpretationClaimMaterializationReceipt:
        raise InvalidExternalEvidenceInterpretation(
            "materialization_receipt must use exact "
            "ExternalEvidenceInterpretationClaimMaterializationReceipt"
        )
    restored = ExternalEvidenceInterpretationClaimMaterializationReceipt(
        policy_ref=ExternalEvidenceInterpretationPolicyRef(
            receipt.policy_ref.namespace,
            receipt.policy_ref.key,
            receipt.policy_ref.revision,
        ),
        proposal_id=ExternalEvidenceInterpretationProposalId(receipt.proposal_id.value),
        candidate_sha256=receipt.candidate_sha256,
        review_id=ExternalEvidenceInterpretationReviewId(receipt.review_id.value),
        review_sha256=receipt.review_sha256,
        claim_id=CapabilityClaimId(receipt.claim_id.value),
        claim_sha256=receipt.claim_sha256,
        predecessor_snapshot_sha256=receipt.predecessor_snapshot_sha256,
        successor_snapshot_sha256=receipt.successor_snapshot_sha256,
        materialized_at=receipt.materialized_at,
    )
    if restored != receipt:
        raise InvalidExternalEvidenceInterpretation(
            "materialization_receipt must equal strict semantic reconstruction"
        )
    return receipt


def _strict_materialization(
    value: ExternalEvidenceInterpretationClaimMaterialization,
) -> ExternalEvidenceInterpretationClaimMaterialization:
    if type(value) is not ExternalEvidenceInterpretationClaimMaterialization:
        raise InvalidExternalEvidenceInterpretation(
            "materialization must use exact "
            "ExternalEvidenceInterpretationClaimMaterialization"
        )
    _strict_claim(value.claim)
    _strict_snapshot(value.successor_snapshot, "successor_snapshot")
    if not isinstance(
        value.succession_receipt,
        EpistemicSnapshotSuccessionReceipt,
    ) or not value.succession_receipt.validator_issued:
        raise InvalidExternalEvidenceInterpretation(
            "succession_receipt must be validator-issued by PR11.3"
        )
    _strict_materialization_receipt(value.materialization_receipt)
    return value


def materialized_capability_claim_sha256_v1(claim: CapabilityClaim) -> str:
    claim = _strict_claim(claim)
    canonical = EpistemicRecordSet(claims=(claim,)).to_json()
    digest = hashlib.sha256()
    digest.update(_CLAIM_HASH_DOMAIN)
    digest.update(canonical.encode("utf-8"))
    return digest.hexdigest()


def _claim_semantic_payload(
    candidate: ExternalEvidenceClaimInterpretationCandidate,
) -> dict:
    candidate = _strict_candidate(candidate)
    return {
        "subject_ref": str(candidate.subject_ref),
        "concept_ref": str(candidate.concept_ref),
        "statement": candidate.claim_statement,
        "scope": {
            "description": candidate.claim_scope.description,
            "tags": list(candidate.claim_scope.tags),
        },
    }


def _canonical_json(payload: object) -> str:
    try:
        return json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise InvalidExternalEvidenceInterpretation(
            f"claim identity payload is not canonically JSON serializable: {exc}"
        ) from exc


def _claim_semantic_sha256_v1(
    candidate: ExternalEvidenceClaimInterpretationCandidate,
) -> str:
    digest = hashlib.sha256()
    digest.update(_CLAIM_SEMANTIC_HASH_DOMAIN)
    digest.update(_canonical_json(_claim_semantic_payload(candidate)).encode("utf-8"))
    return digest.hexdigest()


def _claim_record_identity_sha256_v1(
    *,
    candidate: ExternalEvidenceClaimInterpretationCandidate,
    accepted_review: ExternalEvidenceClaimInterpretationReview,
) -> str:
    candidate = _strict_candidate(candidate)
    accepted_review = _strict_review(accepted_review)
    payload = {
        "policy_ref": str(
            EXTERNAL_EVIDENCE_INTERPRETATION_CLAIM_MATERIALIZATION_POLICY_V1
        ),
        "claim_semantics": _claim_semantic_payload(candidate),
        "created_at": accepted_review.reviewed_at.isoformat(),
        "provenance": {
            "source_kind": ProvenanceSourceKind.SYSTEM.value,
            "source_ref": _MATERIALIZATION_SOURCE_REF,
            "operation_key": _MATERIALIZATION_OPERATION_KEY,
            "occurred_at": accepted_review.reviewed_at.isoformat(),
            "actor_ref": accepted_review.reviewer_ref.ref,
            "mechanism_ref": str(
                EXTERNAL_EVIDENCE_INTERPRETATION_CLAIM_MATERIALIZATION_POLICY_V1
            ),
            "note": _MATERIALIZATION_NOTE,
        },
    }
    digest = hashlib.sha256()
    digest.update(_CLAIM_ID_HASH_DOMAIN)
    digest.update(_canonical_json(payload).encode("utf-8"))
    return digest.hexdigest()


def _deterministic_claim_id(
    *,
    candidate: ExternalEvidenceClaimInterpretationCandidate,
    accepted_review: ExternalEvidenceClaimInterpretationReview,
) -> CapabilityClaimId:
    return CapabilityClaimId(
        "external_interpretation:"
        + _claim_record_identity_sha256_v1(
            candidate=candidate,
            accepted_review=accepted_review,
        )
    )


def _build_claim(
    *,
    candidate: ExternalEvidenceClaimInterpretationCandidate,
    accepted_review: ExternalEvidenceClaimInterpretationReview,
) -> CapabilityClaim:
    candidate = _strict_candidate(candidate)
    accepted_review = _strict_review(accepted_review)
    claim_id = _deterministic_claim_id(
        candidate=candidate,
        accepted_review=accepted_review,
    )
    try:
        claim = CapabilityClaim(
            claim_id=claim_id,
            subject_ref=candidate.subject_ref,
            concept_ref=candidate.concept_ref,
            statement=candidate.claim_statement,
            scope=candidate.claim_scope,
            created_at=accepted_review.reviewed_at,
            provenance=ProvenanceTrail(
                sources=(
                    ProvenanceSource(
                        ProvenanceSourceKind.SYSTEM,
                        _MATERIALIZATION_SOURCE_REF,
                    ),
                ),
                steps=(
                    ProvenanceStep(
                        operation_key=_MATERIALIZATION_OPERATION_KEY,
                        occurred_at=accepted_review.reviewed_at,
                        actor_ref=ActorRef(accepted_review.reviewer_ref.ref),
                        mechanism_ref=str(
                            EXTERNAL_EVIDENCE_INTERPRETATION_CLAIM_MATERIALIZATION_POLICY_V1
                        ),
                        note=_MATERIALIZATION_NOTE,
                    ),
                ),
            ),
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InvalidExternalEvidenceInterpretation):
            raise
        raise InvalidExternalEvidenceInterpretation(
            f"cannot construct deterministic CapabilityClaim: {exc}"
        ) from exc
    return _strict_claim(claim)


def _same_claim_semantics(left: CapabilityClaim, right: CapabilityClaim) -> bool:
    return (
        left.subject_ref == right.subject_ref
        and left.concept_ref == right.concept_ref
        and left.statement == right.statement
        and left.scope == right.scope
    )


def _build_successor(
    *,
    predecessor: EpistemicRecordSet,
    claim: CapabilityClaim,
) -> tuple[EpistemicRecordSet, EpistemicSnapshotSuccessionReceipt]:
    predecessor = _strict_snapshot(predecessor, "epistemic_snapshot")
    claim = _strict_claim(claim)
    for existing in predecessor.claims:
        if existing.claim_id == claim.claim_id:
            raise InvalidExternalEvidenceInterpretation(
                "deterministic materialized claim_id already exists in predecessor snapshot"
            )
        if _same_claim_semantics(existing, claim):
            raise InvalidExternalEvidenceInterpretation(
                "semantically identical CapabilityClaim already exists in predecessor "
                "snapshot under a different claim_id; PR12.4 does not reconcile or "
                "duplicate pre-existing claim identity"
            )
    try:
        successor = EpistemicRecordSet(
            evidence_records=predecessor.evidence_records,
            claims=predecessor.claims + (claim,),
            evaluations=predecessor.evaluations,
        )
        receipt = validate_epistemic_snapshot_successor_v1(
            predecessor=predecessor,
            successor=successor,
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InvalidExternalEvidenceInterpretation):
            raise
        raise InvalidExternalEvidenceInterpretation(
            f"cannot admit materialized claim through PR11.3 succession: {exc}"
        ) from exc
    if receipt.added_claim_ids != (claim.claim_id,):
        raise InvalidExternalEvidenceInterpretation(
            "PR12.4 succession must append exactly the deterministic materialized claim"
        )
    if receipt.added_evidence_ids or receipt.added_evaluation_ids:
        raise InvalidExternalEvidenceInterpretation(
            "PR12.4 succession may not add evidence or ClaimEvaluation records"
        )
    return successor, receipt


def _build_materialization_receipt(
    *,
    predecessor: EpistemicRecordSet,
    successor: EpistemicRecordSet,
    candidate: ExternalEvidenceClaimInterpretationCandidate,
    accepted_review: ExternalEvidenceClaimInterpretationReview,
    claim: CapabilityClaim,
) -> ExternalEvidenceInterpretationClaimMaterializationReceipt:
    return ExternalEvidenceInterpretationClaimMaterializationReceipt(
        policy_ref=EXTERNAL_EVIDENCE_INTERPRETATION_CLAIM_MATERIALIZATION_POLICY_V1,
        proposal_id=candidate.proposal_id,
        candidate_sha256=external_evidence_claim_interpretation_candidate_sha256_v1(
            candidate
        ),
        review_id=accepted_review.review_id,
        review_sha256=external_evidence_claim_interpretation_review_sha256_v1(
            accepted_review
        ),
        claim_id=claim.claim_id,
        claim_sha256=materialized_capability_claim_sha256_v1(claim),
        predecessor_snapshot_sha256=epistemic_snapshot_sha256_v1(predecessor),
        successor_snapshot_sha256=epistemic_snapshot_sha256_v1(successor),
        materialized_at=accepted_review.reviewed_at,
    )


def materialize_accepted_external_evidence_interpretation_claim_v1(
    *,
    epistemic_snapshot: EpistemicRecordSet,
    catalog: CapabilityCatalog,
    candidate: ExternalEvidenceClaimInterpretationCandidate,
    review_ledger: ExternalEvidenceInterpretationReviewLedger,
) -> ExternalEvidenceInterpretationClaimMaterialization:
    """Create one evaluable claim from one exact terminal PR12.3 ACCEPT.

    This transition establishes claim identity only. It does not assess evidence
    bearing, reliability, claim truth, capability state, readiness, mastery, or
    permission.
    """

    predecessor = _strict_snapshot(epistemic_snapshot, "epistemic_snapshot")
    candidate = _strict_candidate(candidate)
    accepted_review = (
        require_accepted_external_evidence_claim_interpretation_review_v1(
            review_ledger=review_ledger,
            epistemic_snapshot=predecessor,
            catalog=catalog,
            candidate=candidate,
        )
    )
    claim = _build_claim(
        candidate=candidate,
        accepted_review=accepted_review,
    )
    successor, succession_receipt = _build_successor(
        predecessor=predecessor,
        claim=claim,
    )
    materialization_receipt = _build_materialization_receipt(
        predecessor=predecessor,
        successor=successor,
        candidate=candidate,
        accepted_review=accepted_review,
        claim=claim,
    )
    result = ExternalEvidenceInterpretationClaimMaterialization(
        claim=claim,
        successor_snapshot=successor,
        succession_receipt=succession_receipt,
        materialization_receipt=materialization_receipt,
    )
    validate_external_evidence_interpretation_claim_materialization_v1(
        epistemic_snapshot=predecessor,
        catalog=catalog,
        candidate=candidate,
        review_ledger=review_ledger,
        materialization=result,
    )
    return result


def validate_external_evidence_interpretation_claim_materialization_v1(
    *,
    epistemic_snapshot: EpistemicRecordSet,
    catalog: CapabilityCatalog,
    candidate: ExternalEvidenceClaimInterpretationCandidate,
    review_ledger: ExternalEvidenceInterpretationReviewLedger,
    materialization: ExternalEvidenceInterpretationClaimMaterialization,
) -> None:
    """Replay every PR12.4 binding and the PR11.3 append-only transition."""

    predecessor = _strict_snapshot(epistemic_snapshot, "epistemic_snapshot")
    candidate = _strict_candidate(candidate)
    materialization = _strict_materialization(materialization)
    accepted_review = (
        require_accepted_external_evidence_claim_interpretation_review_v1(
            review_ledger=review_ledger,
            epistemic_snapshot=predecessor,
            catalog=catalog,
            candidate=candidate,
        )
    )
    expected_claim = _build_claim(
        candidate=candidate,
        accepted_review=accepted_review,
    )
    if materialization.claim != expected_claim:
        raise InvalidExternalEvidenceInterpretation(
            "materialized CapabilityClaim does not equal exact deterministic claim"
        )
    expected_successor, expected_succession_receipt = _build_successor(
        predecessor=predecessor,
        claim=expected_claim,
    )
    if materialization.successor_snapshot != expected_successor:
        raise InvalidExternalEvidenceInterpretation(
            "successor_snapshot does not equal exact PR12.4 append-only successor"
        )
    if materialization.succession_receipt != expected_succession_receipt:
        raise InvalidExternalEvidenceInterpretation(
            "succession_receipt does not equal validator-issued PR11.3 receipt"
        )
    expected_receipt = _build_materialization_receipt(
        predecessor=predecessor,
        successor=expected_successor,
        candidate=candidate,
        accepted_review=accepted_review,
        claim=expected_claim,
    )
    if materialization.materialization_receipt != expected_receipt:
        raise InvalidExternalEvidenceInterpretation(
            "materialization_receipt does not match exact PR12.4 governance basis"
        )


def external_evidence_interpretation_claim_materialization_receipt_sha256_v1(
    receipt: ExternalEvidenceInterpretationClaimMaterializationReceipt,
) -> str:
    receipt = _strict_materialization_receipt(receipt)
    from .claim_materialization_serialization import (
        external_evidence_interpretation_claim_materialization_receipt_to_json,
    )

    digest = hashlib.sha256()
    digest.update(_RECEIPT_HASH_DOMAIN)
    digest.update(
        external_evidence_interpretation_claim_materialization_receipt_to_json(
            receipt
        ).encode("utf-8")
    )
    return digest.hexdigest()
