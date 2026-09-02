"""Strict deterministic serialization for PR6 proposal snapshots."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import re
from typing import Any, Mapping

from capability_lab.epistemics import CapabilitySubjectRef, ClaimScope
from capability_lab.semantics import (
    CapabilityConceptRef,
    CapabilityId,
    ConceptLifecycle,
    RelationKind,
    RelationScope,
    RelationStrength,
)

from .core import (
    CapabilityProposal,
    CapabilityProposalId,
    ClaimCreateCandidate,
    ConceptCandidateSpec,
    ConceptCreateCandidate,
    ConceptMergeCandidate,
    ConceptRevisionCandidate,
    ConceptSplitCandidate,
    InvalidProposalError,
    ProposalBasisKind,
    ProposalBasisRef,
    ProposalGenerationPolicyRef,
    ProposalGeneratorRef,
    ProposalKind,
    ProposalMechanismKind,
    ProposalReview,
    ProposalReviewId,
    ProposalReviewPolicyRef,
    ProposalReviewerRef,
    ProposalReviewVerdict,
    RelationCreateCandidate,
)

_SCHEMA_VERSION = 1
_TIME_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]{1,6})?(?:Z|[+-][0-9]{2}:[0-9]{2})$"
)


def proposal_set_to_json(record_set) -> str:
    return json.dumps(
        proposal_set_to_dict(record_set),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def proposal_set_from_json(payload: object):
    if not isinstance(payload, str):
        raise InvalidProposalError("proposal-set JSON payload must be a string")

    def reject_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise InvalidProposalError(f"duplicate JSON object key: {key!r}")
            result[key] = value
        return result

    def reject_constant(value: str):
        raise InvalidProposalError(f"non-finite JSON number is forbidden: {value}")

    try:
        decoded = json.loads(
            payload,
            object_pairs_hook=reject_duplicates,
            parse_constant=reject_constant,
        )
    except InvalidProposalError:
        raise
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise InvalidProposalError("proposal-set JSON payload must be valid strict JSON") from exc
    return proposal_set_from_dict(decoded)


def proposal_set_to_dict(record_set) -> dict[str, Any]:
    from .record_set import CapabilityProposalSet

    if not isinstance(record_set, CapabilityProposalSet):
        raise InvalidProposalError("record_set must be CapabilityProposalSet")
    return {
        "schema_version": _SCHEMA_VERSION,
        "subject_ref": None if record_set.subject_ref is None else str(record_set.subject_ref),
        "proposals": [_proposal_to_dict(item) for item in record_set.proposals],
        "reviews": [_review_to_dict(item) for item in record_set.reviews],
    }


def proposal_set_from_dict(payload: object):
    from .record_set import CapabilityProposalSet

    mapping = _mapping(payload, "proposal set")
    _keys(mapping, {"schema_version", "subject_ref", "proposals", "reviews"}, "proposal set")
    if mapping["schema_version"] != _SCHEMA_VERSION:
        raise InvalidProposalError(
            f"proposal set schema_version must be exactly {_SCHEMA_VERSION}"
        )
    subject_ref_raw = mapping["subject_ref"]
    subject_ref = None if subject_ref_raw is None else CapabilitySubjectRef(_string(subject_ref_raw, "subject_ref"))
    proposals = tuple(_proposal_from_dict(item) for item in _list(mapping["proposals"], "proposals"))
    reviews = tuple(_review_from_dict(item) for item in _list(mapping["reviews"], "reviews"))
    return CapabilityProposalSet(subject_ref=subject_ref, proposals=proposals, reviews=reviews)


def _proposal_to_dict(proposal: CapabilityProposal) -> dict[str, Any]:
    return {
        "proposal_id": str(proposal.proposal_id),
        "kind": proposal.kind.value,
        "payload": _payload_to_dict(proposal.payload),
        "subject_ref": None if proposal.subject_ref is None else str(proposal.subject_ref),
        "generator_ref": {
            "kind": proposal.generator_ref.kind.value,
            "ref": proposal.generator_ref.ref,
        },
        "generation_policy_ref": str(proposal.generation_policy_ref),
        "created_at": _format_time(proposal.created_at),
        "rationale": proposal.rationale,
        "basis_refs": [
            {"kind": item.kind.value, "ref": item.ref} for item in proposal.basis_refs
        ],
        "supersedes_proposal_id": (
            None
            if proposal.supersedes_proposal_id is None
            else str(proposal.supersedes_proposal_id)
        ),
    }


def _proposal_from_dict(payload: object) -> CapabilityProposal:
    mapping = _mapping(payload, "proposal")
    _keys(
        mapping,
        {
            "proposal_id",
            "kind",
            "payload",
            "subject_ref",
            "generator_ref",
            "generation_policy_ref",
            "created_at",
            "rationale",
            "basis_refs",
            "supersedes_proposal_id",
        },
        "proposal",
    )
    try:
        kind = ProposalKind(_string(mapping["kind"], "proposal kind"))
    except ValueError as exc:
        raise InvalidProposalError(f"unknown proposal kind: {mapping['kind']!r}") from exc
    generator_mapping = _mapping(mapping["generator_ref"], "generator_ref")
    _keys(generator_mapping, {"kind", "ref"}, "generator_ref")
    try:
        generator_kind = ProposalMechanismKind(
            _string(generator_mapping["kind"], "generator kind")
        )
    except ValueError as exc:
        raise InvalidProposalError("unknown generator mechanism kind") from exc
    subject_raw = mapping["subject_ref"]
    supersedes_raw = mapping["supersedes_proposal_id"]
    basis_refs = tuple(
        _basis_from_dict(item) for item in _list(mapping["basis_refs"], "basis_refs")
    )
    return CapabilityProposal(
        proposal_id=CapabilityProposalId(_string(mapping["proposal_id"], "proposal_id")),
        kind=kind,
        payload=_payload_from_dict(kind, mapping["payload"]),
        subject_ref=(
            None if subject_raw is None else CapabilitySubjectRef(_string(subject_raw, "subject_ref"))
        ),
        generator_ref=ProposalGeneratorRef(
            kind=generator_kind,
            ref=_string(generator_mapping["ref"], "generator ref"),
        ),
        generation_policy_ref=ProposalGenerationPolicyRef.parse(
            _string(mapping["generation_policy_ref"], "generation_policy_ref")
        ),
        created_at=_parse_time(mapping["created_at"], "created_at"),
        rationale=_string(mapping["rationale"], "rationale"),
        basis_refs=basis_refs,
        supersedes_proposal_id=(
            None
            if supersedes_raw is None
            else CapabilityProposalId(_string(supersedes_raw, "supersedes_proposal_id"))
        ),
    )


def _review_to_dict(review: ProposalReview) -> dict[str, Any]:
    return {
        "review_id": str(review.review_id),
        "proposal_id": str(review.proposal_id),
        "reviewer_ref": {
            "kind": review.reviewer_ref.kind.value,
            "ref": review.reviewer_ref.ref,
        },
        "review_policy_ref": str(review.review_policy_ref),
        "reviewed_at": _format_time(review.reviewed_at),
        "verdict": review.verdict.value,
        "rationale": review.rationale,
    }


def _review_from_dict(payload: object) -> ProposalReview:
    mapping = _mapping(payload, "proposal review")
    _keys(
        mapping,
        {
            "review_id",
            "proposal_id",
            "reviewer_ref",
            "review_policy_ref",
            "reviewed_at",
            "verdict",
            "rationale",
        },
        "proposal review",
    )
    reviewer_mapping = _mapping(mapping["reviewer_ref"], "reviewer_ref")
    _keys(reviewer_mapping, {"kind", "ref"}, "reviewer_ref")
    try:
        reviewer_kind = ProposalMechanismKind(
            _string(reviewer_mapping["kind"], "reviewer kind")
        )
        verdict = ProposalReviewVerdict(_string(mapping["verdict"], "review verdict"))
    except ValueError as exc:
        raise InvalidProposalError("unknown proposal review enum value") from exc
    return ProposalReview(
        review_id=ProposalReviewId(_string(mapping["review_id"], "review_id")),
        proposal_id=CapabilityProposalId(_string(mapping["proposal_id"], "proposal_id")),
        reviewer_ref=ProposalReviewerRef(
            kind=reviewer_kind,
            ref=_string(reviewer_mapping["ref"], "reviewer ref"),
        ),
        review_policy_ref=ProposalReviewPolicyRef.parse(
            _string(mapping["review_policy_ref"], "review_policy_ref")
        ),
        reviewed_at=_parse_time(mapping["reviewed_at"], "reviewed_at"),
        verdict=verdict,
        rationale=_string(mapping["rationale"], "review rationale"),
    )


def _basis_from_dict(payload: object) -> ProposalBasisRef:
    mapping = _mapping(payload, "proposal basis")
    _keys(mapping, {"kind", "ref"}, "proposal basis")
    try:
        kind = ProposalBasisKind(_string(mapping["kind"], "proposal basis kind"))
    except ValueError as exc:
        raise InvalidProposalError("unknown proposal basis kind") from exc
    return ProposalBasisRef(kind=kind, ref=_string(mapping["ref"], "proposal basis ref"))


def _payload_to_dict(payload) -> dict[str, Any]:
    if isinstance(payload, ConceptCreateCandidate):
        return {"proposed": _concept_spec_to_dict(payload.proposed)}
    if isinstance(payload, ConceptRevisionCandidate):
        return {
            "target_ref": str(payload.target_ref),
            "proposed_name": payload.proposed_name,
            "proposed_definition": payload.proposed_definition,
            "proposed_aliases": list(payload.proposed_aliases),
            "proposed_lifecycle": payload.proposed_lifecycle.value,
            "deprecation_note": payload.deprecation_note,
        }
    if isinstance(payload, ConceptSplitCandidate):
        return {
            "source_ref": str(payload.source_ref),
            "outputs": [_concept_spec_to_dict(item) for item in payload.outputs],
        }
    if isinstance(payload, ConceptMergeCandidate):
        return {
            "source_refs": [str(item) for item in payload.source_refs],
            "output": _concept_spec_to_dict(payload.output),
        }
    if isinstance(payload, RelationCreateCandidate):
        return {
            "source_ref": str(payload.source_ref),
            "target_ref": str(payload.target_ref),
            "kind": payload.kind.value,
            "scope": (
                None
                if payload.scope is None
                else {"key": payload.scope.key, "description": payload.scope.description}
            ),
            "strength": payload.strength.value,
            "provenance_refs": list(payload.provenance_refs),
        }
    if isinstance(payload, ClaimCreateCandidate):
        return {
            "concept_ref": str(payload.concept_ref),
            "statement": payload.statement,
            "scope": {
                "description": payload.scope.description,
                "tags": list(payload.scope.tags),
            },
        }
    raise InvalidProposalError(f"unsupported proposal payload: {type(payload).__name__}")


def _payload_from_dict(kind: ProposalKind, payload: object):
    mapping = _mapping(payload, f"{kind.value} payload")
    if kind is ProposalKind.CREATE_CONCEPT:
        _keys(mapping, {"proposed"}, "create_concept payload")
        return ConceptCreateCandidate(_concept_spec_from_dict(mapping["proposed"]))
    if kind is ProposalKind.REVISE_CONCEPT:
        _keys(
            mapping,
            {
                "target_ref",
                "proposed_name",
                "proposed_definition",
                "proposed_aliases",
                "proposed_lifecycle",
                "deprecation_note",
            },
            "revise_concept payload",
        )
        try:
            lifecycle = ConceptLifecycle(
                _string(mapping["proposed_lifecycle"], "proposed_lifecycle")
            )
        except ValueError as exc:
            raise InvalidProposalError("unknown proposed concept lifecycle") from exc
        note = mapping["deprecation_note"]
        if note is not None:
            note = _string(note, "deprecation_note")
        return ConceptRevisionCandidate(
            target_ref=CapabilityConceptRef.parse(_string(mapping["target_ref"], "target_ref")),
            proposed_name=_string(mapping["proposed_name"], "proposed_name"),
            proposed_definition=_string(mapping["proposed_definition"], "proposed_definition"),
            proposed_aliases=tuple(_string(item, "proposed alias") for item in _list(mapping["proposed_aliases"], "proposed_aliases")),
            proposed_lifecycle=lifecycle,
            deprecation_note=note,
        )
    if kind is ProposalKind.SPLIT_CONCEPT:
        _keys(mapping, {"source_ref", "outputs"}, "split_concept payload")
        return ConceptSplitCandidate(
            source_ref=CapabilityConceptRef.parse(_string(mapping["source_ref"], "source_ref")),
            outputs=tuple(_concept_spec_from_dict(item) for item in _list(mapping["outputs"], "outputs")),
        )
    if kind is ProposalKind.MERGE_CONCEPTS:
        _keys(mapping, {"source_refs", "output"}, "merge_concepts payload")
        return ConceptMergeCandidate(
            source_refs=tuple(
                CapabilityConceptRef.parse(_string(item, "source_ref"))
                for item in _list(mapping["source_refs"], "source_refs")
            ),
            output=_concept_spec_from_dict(mapping["output"]),
        )
    if kind is ProposalKind.CREATE_RELATION:
        _keys(
            mapping,
            {"source_ref", "target_ref", "kind", "scope", "strength", "provenance_refs"},
            "create_relation payload",
        )
        scope_raw = mapping["scope"]
        scope = None
        if scope_raw is not None:
            scope_mapping = _mapping(scope_raw, "relation scope")
            _keys(scope_mapping, {"key", "description"}, "relation scope")
            scope = RelationScope(
                key=_string(scope_mapping["key"], "relation scope key"),
                description=_string(scope_mapping["description"], "relation scope description"),
            )
        try:
            relation_kind = RelationKind(_string(mapping["kind"], "relation kind"))
            strength = RelationStrength(_string(mapping["strength"], "relation strength"))
        except ValueError as exc:
            raise InvalidProposalError("unknown relation candidate enum value") from exc
        return RelationCreateCandidate(
            source_ref=CapabilityConceptRef.parse(_string(mapping["source_ref"], "source_ref")),
            target_ref=CapabilityConceptRef.parse(_string(mapping["target_ref"], "target_ref")),
            kind=relation_kind,
            scope=scope,
            strength=strength,
            provenance_refs=tuple(
                _string(item, "provenance ref")
                for item in _list(mapping["provenance_refs"], "provenance_refs")
            ),
        )
    if kind is ProposalKind.CREATE_CLAIM:
        _keys(mapping, {"concept_ref", "statement", "scope"}, "create_claim payload")
        scope_mapping = _mapping(mapping["scope"], "claim candidate scope")
        _keys(scope_mapping, {"description", "tags"}, "claim candidate scope")
        return ClaimCreateCandidate(
            concept_ref=CapabilityConceptRef.parse(_string(mapping["concept_ref"], "concept_ref")),
            statement=_string(mapping["statement"], "claim candidate statement"),
            scope=ClaimScope(
                description=_string(scope_mapping["description"], "claim scope description"),
                tags=tuple(
                    _string(item, "claim scope tag")
                    for item in _list(scope_mapping["tags"], "claim scope tags")
                ),
            ),
        )
    raise InvalidProposalError(f"unsupported proposal kind: {kind.value}")


def _concept_spec_to_dict(spec: ConceptCandidateSpec) -> dict[str, Any]:
    return {
        "suggested_capability_id": str(spec.suggested_capability_id),
        "name": spec.name,
        "definition": spec.definition,
        "aliases": list(spec.aliases),
    }


def _concept_spec_from_dict(payload: object) -> ConceptCandidateSpec:
    mapping = _mapping(payload, "concept candidate spec")
    _keys(
        mapping,
        {"suggested_capability_id", "name", "definition", "aliases"},
        "concept candidate spec",
    )
    return ConceptCandidateSpec(
        suggested_capability_id=CapabilityId.parse(
            _string(mapping["suggested_capability_id"], "suggested_capability_id")
        ),
        name=_string(mapping["name"], "candidate name"),
        definition=_string(mapping["definition"], "candidate definition"),
        aliases=tuple(
            _string(item, "candidate alias")
            for item in _list(mapping["aliases"], "candidate aliases")
        ),
    )


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise InvalidProposalError(f"{label} must be a JSON object")
    return value


def _list(value: object, label: str) -> list:
    if not isinstance(value, list):
        raise InvalidProposalError(f"{label} must be a JSON array")
    return value


def _string(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise InvalidProposalError(f"{label} must be a string")
    return value


def _keys(mapping: Mapping[str, Any], expected: set[str], label: str) -> None:
    actual = set(mapping)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        details = []
        if missing:
            details.append("missing=" + ",".join(missing))
        if extra:
            details.append("extra=" + ",".join(extra))
        raise InvalidProposalError(f"{label} fields must match schema exactly ({'; '.join(details)})")


def _format_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_time(value: object, label: str) -> datetime:
    text = _string(value, label)
    if _TIME_RE.fullmatch(text) is None:
        raise InvalidProposalError(
            f"{label} must use extended ISO-8601 with T and an explicit timezone"
        )
    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise InvalidProposalError(f"{label} must be valid ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise InvalidProposalError(f"{label} must be timezone-aware")
    return parsed.astimezone(timezone.utc)
