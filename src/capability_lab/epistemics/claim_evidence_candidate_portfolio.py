"""PR12.8 complete snapshot-bound claim evidence candidate portfolio v1."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json

from capability_lab.semantics import CapabilityConceptRef, CapabilityId

from .core import (
    CapabilityClaim,
    CapabilityClaimId,
    CapabilitySubjectRef,
    EpistemicError,
    EvidenceId,
    EvidenceRecord,
    canonical_time,
    format_time,
    parse_time,
)
from .record_set import EpistemicRecordSet
from .snapshot_transition import epistemic_snapshot_sha256_v1


class ClaimEvidenceCandidatePortfolioError(EpistemicError):
    """Base error for PR12.8 complete evidence-candidate portfolio governance."""


class InvalidClaimEvidenceCandidatePortfolio(ClaimEvidenceCandidatePortfolioError):
    """The supplied portfolio or selection violates PR12.8 completeness."""


_SCHEMA_VERSION = 1
_SHA256_HEX_DIGITS = frozenset("0123456789abcdef")


def _fail(message: str) -> None:
    raise InvalidClaimEvidenceCandidatePortfolio(message)


def _validate_sha256(value: object, field_name: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in _SHA256_HEX_DIGITS for character in value)
    ):
        _fail(f"{field_name} must be 64 lowercase hexadecimal SHA-256 characters")
    return value


def _canonical_boundary(value: object, field_name: str) -> datetime:
    if type(value) is not datetime:
        _fail(f"{field_name} must use exact datetime")
    try:
        return canonical_time(value, field_name)
    except EpistemicError as exc:
        raise InvalidClaimEvidenceCandidatePortfolio(str(exc)) from exc


def _strict_stored_utc_time(value: object, field_name: str) -> datetime:
    if type(value) is not datetime or value.tzinfo is not timezone.utc:
        _fail(f"{field_name} must use exact canonical UTC datetime")
    return value


def _strict_claim_id(value: object, field_name: str = "claim_id") -> CapabilityClaimId:
    if type(value) is not CapabilityClaimId or type(value.value) is not str:
        _fail(f"{field_name} must use exact CapabilityClaimId")
    try:
        restored = CapabilityClaimId(value.value)
    except (TypeError, ValueError) as exc:
        raise InvalidClaimEvidenceCandidatePortfolio(
            f"{field_name} failed strict reconstruction: {exc}"
        ) from exc
    if restored != value:
        _fail(f"{field_name} must equal strict semantic reconstruction")
    return value


def _strict_subject_ref(
    value: object,
    field_name: str = "subject_ref",
) -> CapabilitySubjectRef:
    if type(value) is not CapabilitySubjectRef or type(value.value) is not str:
        _fail(f"{field_name} must use exact CapabilitySubjectRef")
    try:
        restored = CapabilitySubjectRef(value.value)
    except (TypeError, ValueError) as exc:
        raise InvalidClaimEvidenceCandidatePortfolio(
            f"{field_name} failed strict reconstruction: {exc}"
        ) from exc
    if restored != value:
        _fail(f"{field_name} must equal strict semantic reconstruction")
    return value


def _strict_evidence_id(
    value: object,
    field_name: str = "evidence_id",
) -> EvidenceId:
    if type(value) is not EvidenceId or type(value.value) is not str:
        _fail(f"{field_name} must use exact EvidenceId")
    try:
        restored = EvidenceId(value.value)
    except (TypeError, ValueError) as exc:
        raise InvalidClaimEvidenceCandidatePortfolio(
            f"{field_name} failed strict reconstruction: {exc}"
        ) from exc
    if restored != value:
        _fail(f"{field_name} must equal strict semantic reconstruction")
    return value


def _strict_concept_ref(
    value: object,
    field_name: str = "concept_ref",
) -> CapabilityConceptRef:
    if type(value) is not CapabilityConceptRef:
        _fail(f"{field_name} must use exact CapabilityConceptRef")
    if type(value.capability_id) is not CapabilityId:
        _fail(f"{field_name}.capability_id must use exact CapabilityId")
    if (
        type(value.capability_id.namespace) is not str
        or type(value.capability_id.key) is not str
        or type(value.revision) is not int
    ):
        _fail(f"{field_name} contains non-exact scalar fields")
    try:
        restored = CapabilityConceptRef(
            CapabilityId(value.capability_id.namespace, value.capability_id.key),
            value.revision,
        )
    except (TypeError, ValueError) as exc:
        raise InvalidClaimEvidenceCandidatePortfolio(
            f"{field_name} failed strict reconstruction: {exc}"
        ) from exc
    if restored != value:
        _fail(f"{field_name} must equal strict semantic reconstruction")
    return value


def _strict_evidence_id_tuple(value: object, field_name: str) -> tuple[EvidenceId, ...]:
    if type(value) is not tuple:
        _fail(f"{field_name} must use exact tuple")
    items = value
    for item in items:
        _strict_evidence_id(item, field_name)
    if len(set(items)) != len(items):
        _fail(f"{field_name} must not contain duplicate ids")
    return tuple(sorted(items))


def _strict_records(records: object) -> EpistemicRecordSet:
    if type(records) is not EpistemicRecordSet:
        _fail("records must use exact EpistemicRecordSet")
    if (
        type(records.evidence_records) is not tuple
        or type(records.claims) is not tuple
        or type(records.evaluations) is not tuple
    ):
        _fail("EpistemicRecordSet containers must use exact tuples")

    for evidence in records.evidence_records:
        if type(evidence) is not EvidenceRecord:
            _fail("records evidence must use exact EvidenceRecord")
        _strict_evidence_id(evidence.evidence_id)
        _strict_subject_ref(evidence.subject_ref)
        _strict_stored_utc_time(evidence.recorded_at, "evidence recorded_at")

    for claim in records.claims:
        if type(claim) is not CapabilityClaim:
            _fail("records claims must use exact CapabilityClaim")
        _strict_claim_id(claim.claim_id)
        _strict_subject_ref(claim.subject_ref)
        _strict_concept_ref(claim.concept_ref)
        _strict_stored_utc_time(claim.created_at, "claim created_at")

    try:
        restored = EpistemicRecordSet.from_json(records.to_json())
    except (TypeError, ValueError) as exc:
        raise InvalidClaimEvidenceCandidatePortfolio(
            f"records failed strict reconstruction: {exc}"
        ) from exc
    if restored != records:
        _fail("records must equal strict semantic reconstruction")
    return records


def _resolve_exact_claim(
    *,
    records: EpistemicRecordSet,
    claim_id: CapabilityClaimId,
) -> CapabilityClaim:
    checked = _strict_records(records)
    target_id = _strict_claim_id(claim_id)
    matches = tuple(claim for claim in checked.claims if claim.claim_id == target_id)
    if len(matches) != 1:
        _fail("claim_id is absent or ambiguous in supplied EpistemicRecordSet")
    claim = matches[0]
    if type(claim) is not CapabilityClaim:
        _fail("resolved claim must use exact CapabilityClaim")
    return claim


@dataclass(frozen=True, slots=True)
class ClaimEvidenceCandidatePortfolioReceipt:
    """Deterministic audit/cache representation of one complete PR12.8 portfolio."""

    snapshot_sha256: str
    claim_id: CapabilityClaimId
    subject_ref: CapabilitySubjectRef
    concept_ref: CapabilityConceptRef
    as_of: datetime
    evidence_ids: tuple[EvidenceId, ...] = ()
    excluded_future_evidence_ids: tuple[EvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "snapshot_sha256",
            _validate_sha256(self.snapshot_sha256, "snapshot_sha256"),
        )
        _strict_claim_id(self.claim_id)
        _strict_subject_ref(self.subject_ref)
        _strict_concept_ref(self.concept_ref)
        object.__setattr__(
            self,
            "as_of",
            _canonical_boundary(self.as_of, "portfolio as_of"),
        )

        evidence_ids = _strict_evidence_id_tuple(self.evidence_ids, "evidence_ids")
        future_ids = _strict_evidence_id_tuple(
            self.excluded_future_evidence_ids,
            "excluded_future_evidence_ids",
        )
        if set(evidence_ids) & set(future_ids):
            _fail("admissible and excluded future evidence ids must be disjoint")
        object.__setattr__(self, "evidence_ids", evidence_ids)
        object.__setattr__(self, "excluded_future_evidence_ids", future_ids)

    def to_dict(self) -> dict:
        return claim_evidence_candidate_portfolio_receipt_to_dict(self)

    @classmethod
    def from_dict(cls, payload: object) -> "ClaimEvidenceCandidatePortfolioReceipt":
        return claim_evidence_candidate_portfolio_receipt_from_dict(payload)

    def to_json(self) -> str:
        return claim_evidence_candidate_portfolio_receipt_to_json(self)

    @classmethod
    def from_json(cls, payload: object) -> "ClaimEvidenceCandidatePortfolioReceipt":
        return claim_evidence_candidate_portfolio_receipt_from_json(payload)


def _strict_receipt(portfolio: object) -> ClaimEvidenceCandidatePortfolioReceipt:
    if type(portfolio) is not ClaimEvidenceCandidatePortfolioReceipt:
        _fail("portfolio must use exact ClaimEvidenceCandidatePortfolioReceipt")
    _validate_sha256(portfolio.snapshot_sha256, "snapshot_sha256")
    _strict_claim_id(portfolio.claim_id)
    _strict_subject_ref(portfolio.subject_ref)
    _strict_concept_ref(portfolio.concept_ref)
    _strict_stored_utc_time(portfolio.as_of, "portfolio as_of")
    _strict_evidence_id_tuple(portfolio.evidence_ids, "evidence_ids")
    _strict_evidence_id_tuple(
        portfolio.excluded_future_evidence_ids,
        "excluded_future_evidence_ids",
    )

    try:
        restored = ClaimEvidenceCandidatePortfolioReceipt(
            snapshot_sha256=portfolio.snapshot_sha256,
            claim_id=CapabilityClaimId(portfolio.claim_id.value),
            subject_ref=CapabilitySubjectRef(portfolio.subject_ref.value),
            concept_ref=CapabilityConceptRef(
                CapabilityId(
                    portfolio.concept_ref.capability_id.namespace,
                    portfolio.concept_ref.capability_id.key,
                ),
                portfolio.concept_ref.revision,
            ),
            as_of=portfolio.as_of,
            evidence_ids=tuple(EvidenceId(item.value) for item in portfolio.evidence_ids),
            excluded_future_evidence_ids=tuple(
                EvidenceId(item.value) for item in portfolio.excluded_future_evidence_ids
            ),
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InvalidClaimEvidenceCandidatePortfolio):
            raise
        raise InvalidClaimEvidenceCandidatePortfolio(
            f"portfolio failed strict reconstruction: {exc}"
        ) from exc
    if restored != portfolio:
        _fail("portfolio must equal strict semantic reconstruction")
    return portfolio


def build_complete_claim_evidence_candidate_portfolio_v1(
    *,
    records: EpistemicRecordSet,
    claim_id: CapabilityClaimId,
    as_of: datetime,
) -> ClaimEvidenceCandidatePortfolioReceipt:
    """Build every same-subject evidence candidate available by ``as_of``.

    Membership is intentionally non-evaluative. Evidence kind, outcome, context,
    provenance, claim text, concept heuristics, existing evaluations, reliability,
    bearing, policy, and dependence assumptions do not filter membership.
    """

    checked = _strict_records(records)
    target_id = _strict_claim_id(claim_id)
    boundary = _canonical_boundary(as_of, "portfolio as_of")
    claim = _resolve_exact_claim(records=checked, claim_id=target_id)
    if claim.created_at > boundary:
        _fail("target claim created_at must not follow portfolio as_of")

    admissible: list[EvidenceId] = []
    future: list[EvidenceId] = []
    for evidence in checked.evidence_records:
        if evidence.subject_ref != claim.subject_ref:
            continue
        if evidence.recorded_at <= boundary:
            admissible.append(evidence.evidence_id)
        else:
            future.append(evidence.evidence_id)

    return ClaimEvidenceCandidatePortfolioReceipt(
        snapshot_sha256=epistemic_snapshot_sha256_v1(checked),
        claim_id=claim.claim_id,
        subject_ref=claim.subject_ref,
        concept_ref=claim.concept_ref,
        as_of=boundary,
        evidence_ids=tuple(sorted(admissible)),
        excluded_future_evidence_ids=tuple(sorted(future)),
    )


def validate_exact_claim_evidence_candidate_selection_v1(
    *,
    records: EpistemicRecordSet,
    claim_id: CapabilityClaimId,
    as_of: datetime,
    selected_evidence_ids: tuple[EvidenceId, ...],
    portfolio: ClaimEvidenceCandidatePortfolioReceipt | None = None,
) -> tuple[EvidenceId, ...]:
    """Require caller selection to equal the complete records-derived portfolio."""

    checked = _strict_records(records)
    target_id = _strict_claim_id(claim_id)
    boundary = _canonical_boundary(as_of, "portfolio as_of")
    expected = build_complete_claim_evidence_candidate_portfolio_v1(
        records=checked,
        claim_id=target_id,
        as_of=boundary,
    )

    if portfolio is not None:
        supplied = _strict_receipt(portfolio)
        if supplied != expected:
            _fail(
                "portfolio content does not match complete records-derived candidate portfolio"
            )

    selected = _strict_evidence_id_tuple(
        selected_evidence_ids,
        "selected_evidence_ids",
    )
    expected_ids = expected.evidence_ids

    missing = tuple(sorted(set(expected_ids) - set(selected)))
    if missing:
        _fail(f"selection omits admissible evidence candidate: {missing[0]}")
    extra = tuple(sorted(set(selected) - set(expected_ids)))
    if extra:
        _fail(f"selection includes inadmissible evidence candidate: {extra[0]}")
    return selected


def claim_evidence_candidate_portfolio_receipt_to_dict(
    portfolio: ClaimEvidenceCandidatePortfolioReceipt,
) -> dict:
    checked = _strict_receipt(portfolio)
    return {
        "schema_version": _SCHEMA_VERSION,
        "snapshot_sha256": checked.snapshot_sha256,
        "claim_id": checked.claim_id.value,
        "subject_ref": checked.subject_ref.value,
        "concept_ref": str(checked.concept_ref),
        "as_of": format_time(checked.as_of),
        "evidence_ids": [item.value for item in checked.evidence_ids],
        "excluded_future_evidence_ids": [
            item.value for item in checked.excluded_future_evidence_ids
        ],
    }


def _require_exact_object(payload: object) -> dict:
    if type(payload) is not dict:
        _fail("portfolio payload must use exact object/dict")
    if any(type(key) is not str for key in payload):
        _fail("portfolio payload keys must use exact strings")
    expected_keys = {
        "schema_version",
        "snapshot_sha256",
        "claim_id",
        "subject_ref",
        "concept_ref",
        "as_of",
        "evidence_ids",
        "excluded_future_evidence_ids",
    }
    actual_keys = set(payload)
    unknown = actual_keys - expected_keys
    if unknown:
        _fail(f"portfolio payload contains unknown field: {sorted(unknown)[0]}")
    missing = expected_keys - actual_keys
    if missing:
        _fail(f"portfolio payload is missing field: {sorted(missing)[0]}")
    if type(payload["schema_version"]) is not int or payload["schema_version"] != _SCHEMA_VERSION:
        _fail("portfolio payload schema_version must be exact integer 1")
    return payload


def _ids_from_json_array(value: object, field_name: str) -> tuple[EvidenceId, ...]:
    if type(value) is not list:
        _fail(f"{field_name} must use exact JSON array/list")
    items: list[EvidenceId] = []
    for raw in value:
        if type(raw) is not str:
            _fail(f"{field_name} values must use exact strings")
        try:
            items.append(EvidenceId(raw))
        except (TypeError, ValueError) as exc:
            raise InvalidClaimEvidenceCandidatePortfolio(
                f"{field_name} contains invalid EvidenceId: {exc}"
            ) from exc
    result = tuple(items)
    if len(set(result)) != len(result):
        _fail(f"{field_name} must not contain duplicate ids")
    if result != tuple(sorted(result)):
        _fail(f"{field_name} must use canonical sorted order")
    return result


def claim_evidence_candidate_portfolio_receipt_from_dict(
    payload: object,
) -> ClaimEvidenceCandidatePortfolioReceipt:
    obj = _require_exact_object(payload)

    for field_name in (
        "snapshot_sha256",
        "claim_id",
        "subject_ref",
        "concept_ref",
        "as_of",
    ):
        if type(obj[field_name]) is not str:
            _fail(f"{field_name} must use exact string")

    try:
        concept_ref = CapabilityConceptRef.parse(obj["concept_ref"])
        boundary = parse_time(obj["as_of"], "portfolio as_of")
        claim_id = CapabilityClaimId(obj["claim_id"])
        subject_ref = CapabilitySubjectRef(obj["subject_ref"])
    except (TypeError, ValueError) as exc:
        raise InvalidClaimEvidenceCandidatePortfolio(
            f"portfolio payload failed semantic parsing: {exc}"
        ) from exc

    return ClaimEvidenceCandidatePortfolioReceipt(
        snapshot_sha256=obj["snapshot_sha256"],
        claim_id=claim_id,
        subject_ref=subject_ref,
        concept_ref=concept_ref,
        as_of=boundary,
        evidence_ids=_ids_from_json_array(obj["evidence_ids"], "evidence_ids"),
        excluded_future_evidence_ids=_ids_from_json_array(
            obj["excluded_future_evidence_ids"],
            "excluded_future_evidence_ids",
        ),
    )


def claim_evidence_candidate_portfolio_receipt_to_json(
    portfolio: ClaimEvidenceCandidatePortfolioReceipt,
) -> str:
    try:
        return json.dumps(
            claim_evidence_candidate_portfolio_receipt_to_dict(portfolio),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InvalidClaimEvidenceCandidatePortfolio):
            raise
        raise InvalidClaimEvidenceCandidatePortfolio(
            f"portfolio is not canonically JSON serializable: {exc}"
        ) from exc


def _reject_json_constant(value: str):
    _fail(f"non-standard JSON constant is forbidden: {value}")


def _reject_duplicate_json_pairs(pairs: list[tuple[str, object]]) -> dict:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            _fail(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def claim_evidence_candidate_portfolio_receipt_from_json(
    payload: object,
) -> ClaimEvidenceCandidatePortfolioReceipt:
    if type(payload) is not str:
        _fail("portfolio JSON payload must use exact string")
    try:
        decoded = json.loads(
            payload,
            object_pairs_hook=_reject_duplicate_json_pairs,
            parse_constant=_reject_json_constant,
        )
    except InvalidClaimEvidenceCandidatePortfolio:
        raise
    except (TypeError, ValueError) as exc:
        raise InvalidClaimEvidenceCandidatePortfolio(
            f"portfolio JSON is invalid: {exc}"
        ) from exc
    return claim_evidence_candidate_portfolio_receipt_from_dict(decoded)
