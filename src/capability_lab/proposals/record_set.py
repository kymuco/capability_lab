"""Immutable proposal/review snapshots and cross-layer validation."""

from __future__ import annotations

from dataclasses import dataclass

from capability_lab.epistemics import CapabilitySubjectRef, EpistemicRecordSet
from capability_lab.semantics import CapabilityCatalog, CapabilityConceptRef, CapabilityRelation

from .core import (
    CapabilityProposal,
    CapabilityProposalId,
    ClaimCreateCandidate,
    ConceptCreateCandidate,
    ConceptMergeCandidate,
    ConceptRevisionCandidate,
    ConceptSplitCandidate,
    InvalidProposalError,
    ProposalBasisKind,
    ProposalReview,
    RelationCreateCandidate,
)


class InvalidProposalSetError(InvalidProposalError):
    pass


@dataclass(frozen=True, slots=True)
class CapabilityProposalSet:
    """One-scope immutable proposal snapshot; never an acceptance/materialization engine."""

    subject_ref: CapabilitySubjectRef | None = None
    proposals: tuple[CapabilityProposal, ...] = ()
    reviews: tuple[ProposalReview, ...] = ()

    def __post_init__(self) -> None:
        if self.subject_ref is not None and not isinstance(self.subject_ref, CapabilitySubjectRef):
            raise InvalidProposalSetError("subject_ref must be CapabilitySubjectRef or None")
        proposals = _validated_tuple(self.proposals, CapabilityProposal, "proposals")
        reviews = _validated_tuple(self.reviews, ProposalReview, "reviews")
        proposals = tuple(sorted(proposals, key=lambda item: item.proposal_id))
        reviews = tuple(sorted(reviews, key=lambda item: item.review_id))

        _reject_duplicate_ids((item.proposal_id for item in proposals), "proposal id")
        _reject_duplicate_ids((item.review_id for item in reviews), "proposal review id")

        proposal_by_id = {item.proposal_id: item for item in proposals}
        for proposal in proposals:
            if proposal.subject_ref != self.subject_ref:
                raise InvalidProposalSetError(
                    "proposal subject scope must match proposal-set subject scope exactly"
                )
            parent_id = proposal.supersedes_proposal_id
            if parent_id is None:
                continue
            parent = proposal_by_id.get(parent_id)
            if parent is None:
                raise InvalidProposalSetError(
                    f"proposal supersedes missing proposal: {parent_id}"
                )
            if parent.subject_ref != proposal.subject_ref:
                raise InvalidProposalSetError(
                    "proposal supersession may not cross shared/person or subject boundaries"
                )
            if parent.created_at > proposal.created_at:
                raise InvalidProposalSetError(
                    "superseded proposal must not be created after its replacement"
                )

        _validate_supersession_acyclic(proposals)

        for review in reviews:
            proposal = proposal_by_id.get(review.proposal_id)
            if proposal is None:
                raise InvalidProposalSetError(
                    f"proposal review references missing proposal: {review.proposal_id}"
                )
            if review.reviewed_at < proposal.created_at:
                raise InvalidProposalSetError(
                    "proposal review reviewed_at must not precede proposal created_at"
                )

        object.__setattr__(self, "proposals", proposals)
        object.__setattr__(self, "reviews", reviews)

    def validate_against_capability_catalog(self, catalog: CapabilityCatalog) -> None:
        if not isinstance(catalog, CapabilityCatalog):
            raise InvalidProposalSetError("catalog must be CapabilityCatalog")
        namespace_ids = {item.namespace_id for item in catalog.namespaces}
        concept_by_id = {item.capability_id: item for item in catalog.concepts}
        existing_relation_keys = {item.semantic_key for item in catalog.relations}

        for proposal in self.proposals:
            for basis in proposal.basis_refs:
                if basis.kind is ProposalBasisKind.CAPABILITY_CONCEPT:
                    _require_exact_ref(
                        CapabilityConceptRef.parse(basis.ref),
                        concept_by_id,
                        "proposal basis",
                    )

            payload = proposal.payload
            if isinstance(payload, ConceptCreateCandidate):
                candidate_id = payload.proposed.suggested_capability_id
                _require_existing_namespace(candidate_id, namespace_ids, "create-concept candidate")
                if candidate_id in concept_by_id:
                    raise InvalidProposalSetError(
                        f"create-concept suggested id already exists in catalog: {candidate_id}"
                    )
                continue

            if isinstance(payload, ConceptRevisionCandidate):
                _require_exact_ref(payload.target_ref, concept_by_id, "revision target")
                continue

            if isinstance(payload, ConceptSplitCandidate):
                _require_exact_ref(payload.source_ref, concept_by_id, "split source")
                for output in payload.outputs:
                    candidate_id = output.suggested_capability_id
                    _require_existing_namespace(candidate_id, namespace_ids, "split output candidate")
                    if candidate_id in concept_by_id:
                        raise InvalidProposalSetError(
                            "split output suggested id already exists in catalog: "
                            f"{candidate_id}"
                        )
                continue

            if isinstance(payload, ConceptMergeCandidate):
                for ref in payload.source_refs:
                    _require_exact_ref(ref, concept_by_id, "merge source")
                candidate_id = payload.output.suggested_capability_id
                _require_existing_namespace(candidate_id, namespace_ids, "merge output candidate")
                if candidate_id in concept_by_id:
                    raise InvalidProposalSetError(
                        "merge output suggested id already exists in catalog: "
                        f"{candidate_id}"
                    )
                continue

            if isinstance(payload, RelationCreateCandidate):
                _require_exact_ref(payload.source_ref, concept_by_id, "relation source")
                _require_exact_ref(payload.target_ref, concept_by_id, "relation target")
                candidate_relation = CapabilityRelation(
                    source_id=payload.source_ref.capability_id,
                    target_id=payload.target_ref.capability_id,
                    kind=payload.kind,
                    scope=payload.scope,
                    strength=payload.strength,
                    provenance_refs=payload.provenance_refs,
                )
                if candidate_relation.semantic_key in existing_relation_keys:
                    raise InvalidProposalSetError(
                        "create-relation proposal duplicates an existing catalog relation: "
                        + repr(candidate_relation.semantic_key)
                    )
                continue

            if isinstance(payload, ClaimCreateCandidate):
                _require_exact_ref(payload.concept_ref, concept_by_id, "claim candidate concept")
                continue

            raise InvalidProposalSetError(
                f"unsupported proposal payload type: {type(payload).__name__}"
            )

    def validate_against_epistemics(self, records: EpistemicRecordSet) -> None:
        if not isinstance(records, EpistemicRecordSet):
            raise InvalidProposalSetError("records must be EpistemicRecordSet")
        evidence_by_id = {str(item.evidence_id): item for item in records.evidence_records}
        claim_by_id = {str(item.claim_id): item for item in records.claims}
        evaluation_by_id = {str(item.evaluation_id): item for item in records.evaluations}
        internal_record_ids = set(evidence_by_id) | set(claim_by_id) | set(evaluation_by_id)

        for proposal in self.proposals:
            for basis in proposal.basis_refs:
                if basis.kind is ProposalBasisKind.EVIDENCE_RECORD:
                    record = evidence_by_id.get(basis.ref)
                    if record is None:
                        raise InvalidProposalSetError(
                            f"proposal basis references missing evidence: {basis.ref}"
                        )
                    _require_private_basis_subject(proposal, record.subject_ref, basis.ref)
                elif basis.kind is ProposalBasisKind.CAPABILITY_CLAIM:
                    claim = claim_by_id.get(basis.ref)
                    if claim is None:
                        raise InvalidProposalSetError(
                            f"proposal basis references missing claim: {basis.ref}"
                        )
                    _require_private_basis_subject(proposal, claim.subject_ref, basis.ref)
                elif basis.kind is ProposalBasisKind.CLAIM_EVALUATION:
                    evaluation = evaluation_by_id.get(basis.ref)
                    if evaluation is None:
                        raise InvalidProposalSetError(
                            f"proposal basis references missing evaluation: {basis.ref}"
                        )
                    claim = claim_by_id.get(str(evaluation.claim_id))
                    if claim is None:
                        raise InvalidProposalSetError(
                            "epistemic snapshot is missing claim required by evaluation basis: "
                            f"{evaluation.claim_id}"
                        )
                    _require_private_basis_subject(proposal, claim.subject_ref, basis.ref)
                elif basis.kind in {
                    ProposalBasisKind.EXTERNAL_ARTIFACT,
                    ProposalBasisKind.OTHER,
                } and basis.ref in internal_record_ids:
                    raise InvalidProposalSetError(
                        "external/other proposal basis may not relabel an internal person-scoped "
                        "epistemic record id; use the matching typed proposal basis kind instead: "
                        f"{basis.ref}"
                    )

            payload = proposal.payload
            if isinstance(payload, RelationCreateCandidate):
                leaked_internal_refs = sorted(
                    set(payload.provenance_refs).intersection(internal_record_ids)
                )
                if leaked_internal_refs:
                    raise InvalidProposalSetError(
                        "relation candidate provenance_refs may not encode internal person-scoped "
                        "epistemic record ids; use typed proposal basis refs instead: "
                        + ", ".join(leaked_internal_refs)
                    )

    def to_dict(self) -> dict:
        from .serialization import proposal_set_to_dict

        return proposal_set_to_dict(self)

    @classmethod
    def from_dict(cls, payload: object) -> "CapabilityProposalSet":
        from .serialization import proposal_set_from_dict

        return proposal_set_from_dict(payload)

    def to_json(self) -> str:
        from .serialization import proposal_set_to_json

        return proposal_set_to_json(self)

    @classmethod
    def from_json(cls, payload: object) -> "CapabilityProposalSet":
        from .serialization import proposal_set_from_json

        return proposal_set_from_json(payload)


def _validated_tuple(value: object, item_type: type, field_name: str) -> tuple:
    if isinstance(value, (str, bytes)):
        raise InvalidProposalSetError(f"{field_name} must be an iterable")
    try:
        result = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise InvalidProposalSetError(f"{field_name} must be iterable") from exc
    if any(not isinstance(item, item_type) for item in result):
        raise InvalidProposalSetError(f"{field_name} contains invalid record type")
    return result


def _reject_duplicate_ids(values, label: str) -> None:
    seen = set()
    for value in values:
        if value in seen:
            raise InvalidProposalSetError(f"duplicate {label}: {value}")
        seen.add(value)


def _require_existing_namespace(capability_id, namespace_ids: set[str], label: str) -> None:
    if capability_id.namespace not in namespace_ids:
        raise InvalidProposalSetError(
            f"{label} uses namespace absent from catalog; PR6 does not create namespaces: "
            f"{capability_id.namespace}"
        )


def _require_exact_ref(ref, concept_by_id: dict, label: str) -> None:
    concept = concept_by_id.get(ref.capability_id)
    if concept is None:
        raise InvalidProposalSetError(f"{label} is absent from catalog: {ref}")
    if concept.revision != ref.revision:
        raise InvalidProposalSetError(
            f"{label} requires exact concept revision; silent latest substitution is forbidden: "
            f"proposal={ref}, catalog={concept.ref}"
        )


def _require_private_basis_subject(proposal: CapabilityProposal, subject_ref, ref: str) -> None:
    if proposal.subject_ref is None:
        raise InvalidProposalSetError(
            "person-scoped epistemic basis requires a person-scoped proposal; "
            f"shared proposal cannot cite internal private record {ref}"
        )
    if proposal.subject_ref != subject_ref:
        raise InvalidProposalSetError(
            "proposal epistemic basis subject must match proposal subject"
        )


def _validate_supersession_acyclic(proposals: tuple[CapabilityProposal, ...]) -> None:
    parent_by_id: dict[CapabilityProposalId, CapabilityProposalId] = {
        item.proposal_id: item.supersedes_proposal_id
        for item in proposals
        if item.supersedes_proposal_id is not None
    }
    for start in parent_by_id:
        seen: set[CapabilityProposalId] = set()
        current = start
        while current in parent_by_id:
            if current in seen:
                raise InvalidProposalSetError("proposal supersession lineage must be acyclic")
            seen.add(current)
            current = parent_by_id[current]
