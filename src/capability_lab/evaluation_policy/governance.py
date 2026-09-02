"""PR12.7 governed HUMAN policy review, terminal admission, and immutable registry v1."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import re
import unicodedata

from capability_lab.epistemics import EvaluationPolicyRef

from .specification import (
    DomainEvaluationPolicySpecification,
    InvalidDomainEvaluationPolicySpecification,
    _strict_policy_ref,
    _strict_specification,
    domain_evaluation_policy_specification_sha256_v1,
)


class InvalidDomainEvaluationPolicyGovernance(InvalidDomainEvaluationPolicySpecification):
    """The supplied PR12.7 policy-governance artifact or transition is invalid."""


_OPAQUE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_CANONICAL_TIME_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z$"
)
_REVIEW_HASH_DOMAIN = b"capability_lab/domain_evaluation_policy_review@1\x00"
_REVIEW_LEDGER_HASH_DOMAIN = b"capability_lab/domain_evaluation_policy_review_ledger@1\x00"
_REGISTRY_HASH_DOMAIN = b"capability_lab/domain_evaluation_policy_registry@1\x00"
_RECEIPT_HASH_DOMAIN = b"capability_lab/domain_evaluation_policy_admission_receipt@1\x00"

# Runtime-only issued-authority registry.  A review ledger is deliberately a
# serializable structural/audit artifact; it does not become terminal-review
# authority merely because it contains a structurally valid APPROVE value.
#
# The strong reference prevents Python id reuse for a live issued capability.
# Runtime authority is intentionally not reconstructible from JSON.  A host
# crossing a process boundary must explicitly replay the terminal-review
# admission function before policy-registry admission.
_ISSUED_REVIEW_ADMISSIONS: dict[int, tuple[object, tuple[object, ...]]] = {}


def _fail(message: str) -> None:
    raise InvalidDomainEvaluationPolicyGovernance(message)


def _opaque_id(value: object, field_name: str) -> str:
    if type(value) is not str or _OPAQUE_ID_RE.fullmatch(value) is None:
        _fail(f"{field_name} must be a canonical opaque ASCII identifier")
    return value


def _sha256(value: object, field_name: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        _fail(f"{field_name} must be a lowercase 64-character SHA-256 hex digest")
    return value


def _text(value: object, field_name: str) -> str:
    if type(value) is not str:
        _fail(f"{field_name} must use exact str storage")
    cleaned = unicodedata.normalize("NFC", value).strip()
    if not cleaned:
        _fail(f"{field_name} must be non-empty")
    return cleaned


def _time(value: object, field_name: str) -> datetime:
    if type(value) is not datetime:
        _fail(f"{field_name} must use exact datetime storage")
    if value.tzinfo is None or value.utcoffset() is None:
        _fail(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _strict_time(value: object, field_name: str) -> datetime:
    if type(value) is not datetime:
        _fail(f"{field_name} must use exact datetime storage")
    if value.tzinfo is not timezone.utc:
        _fail(f"{field_name} must use canonical UTC storage")
    restored = _time(value, field_name)
    if restored != value:
        _fail(f"{field_name} must equal canonical UTC reconstruction")
    return restored


def _format_time(value: datetime) -> str:
    value = _strict_time(value, "time")
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _parse_time(value: object, field_name: str) -> datetime:
    if type(value) is not str or _CANONICAL_TIME_RE.fullmatch(value) is None:
        _fail(f"{field_name} must use canonical UTC ISO-8601 with six fractional digits")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ").replace(
            tzinfo=timezone.utc
        )
    except ValueError as exc:
        raise InvalidDomainEvaluationPolicyGovernance(
            f"{field_name} must be valid canonical UTC time: {exc}"
        ) from exc
    if _format_time(parsed) != value:
        _fail(f"{field_name} must equal canonical time reconstruction")
    return parsed


def _canonical_json(payload: object) -> bytes:
    try:
        return json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise InvalidDomainEvaluationPolicyGovernance(
            f"governance payload is not canonically JSON serializable: {exc}"
        ) from exc


def _hash(domain: bytes, payload: object) -> str:
    digest = hashlib.sha256()
    digest.update(domain)
    digest.update(_canonical_json(payload))
    return digest.hexdigest()


@dataclass(frozen=True, order=True, slots=True)
class DomainEvaluationPolicyReviewId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _opaque_id(self.value, "review id"))

    def __str__(self) -> str:
        return self.value


class DomainEvaluationPolicyReviewerKind(str, Enum):
    HUMAN = "HUMAN"


@dataclass(frozen=True, order=True, slots=True)
class DomainEvaluationPolicyReviewerRef:
    kind: DomainEvaluationPolicyReviewerKind
    ref: str

    def __post_init__(self) -> None:
        if type(self.kind) is not DomainEvaluationPolicyReviewerKind:
            _fail("reviewer kind must use exact DomainEvaluationPolicyReviewerKind")
        if self.kind is not DomainEvaluationPolicyReviewerKind.HUMAN:
            _fail("PR12.7 v1 requires an explicitly declared HUMAN reviewer")
        object.__setattr__(self, "ref", _opaque_id(self.ref, "reviewer ref"))


class DomainEvaluationPolicyReviewVerdict(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"


@dataclass(frozen=True, slots=True)
class DomainEvaluationPolicyReview:
    review_id: DomainEvaluationPolicyReviewId
    policy_ref: EvaluationPolicyRef
    specification_sha256: str
    reviewer_ref: DomainEvaluationPolicyReviewerRef
    verdict: DomainEvaluationPolicyReviewVerdict
    reviewed_at: datetime
    rationale: str

    def __post_init__(self) -> None:
        if type(self.review_id) is not DomainEvaluationPolicyReviewId:
            _fail("review_id must use exact DomainEvaluationPolicyReviewId")
        object.__setattr__(self, "policy_ref", _strict_policy_ref(self.policy_ref))
        object.__setattr__(
            self,
            "specification_sha256",
            _sha256(self.specification_sha256, "specification_sha256"),
        )
        if type(self.reviewer_ref) is not DomainEvaluationPolicyReviewerRef:
            _fail("reviewer_ref must use exact DomainEvaluationPolicyReviewerRef")
        if type(self.verdict) is not DomainEvaluationPolicyReviewVerdict:
            _fail("verdict must use exact DomainEvaluationPolicyReviewVerdict")
        object.__setattr__(self, "reviewed_at", _time(self.reviewed_at, "reviewed_at"))
        object.__setattr__(self, "rationale", _text(self.rationale, "review rationale"))

    def to_dict(self) -> dict:
        from .governance_serialization import domain_evaluation_policy_review_to_dict

        return domain_evaluation_policy_review_to_dict(self)

    @classmethod
    def from_dict(cls, payload: object) -> "DomainEvaluationPolicyReview":
        from .governance_serialization import domain_evaluation_policy_review_from_dict

        return domain_evaluation_policy_review_from_dict(payload)

    def to_json(self) -> str:
        from .governance_serialization import domain_evaluation_policy_review_to_json

        return domain_evaluation_policy_review_to_json(self)

    @classmethod
    def from_json(cls, payload: object) -> "DomainEvaluationPolicyReview":
        from .governance_serialization import domain_evaluation_policy_review_from_json

        return domain_evaluation_policy_review_from_json(payload)


def _strict_review_id(value: DomainEvaluationPolicyReviewId) -> DomainEvaluationPolicyReviewId:
    if type(value) is not DomainEvaluationPolicyReviewId:
        _fail("review_id must use exact DomainEvaluationPolicyReviewId")
    if type(value.value) is not str:
        _fail("review_id value must use exact str storage")
    restored = DomainEvaluationPolicyReviewId(value.value)
    if restored.value != value.value:
        _fail("review_id must equal strict scalar reconstruction")
    return restored


def _strict_reviewer_ref(
    value: DomainEvaluationPolicyReviewerRef,
) -> DomainEvaluationPolicyReviewerRef:
    if type(value) is not DomainEvaluationPolicyReviewerRef:
        _fail("reviewer_ref must use exact DomainEvaluationPolicyReviewerRef")
    if type(value.kind) is not DomainEvaluationPolicyReviewerKind:
        _fail("reviewer_ref kind must use exact DomainEvaluationPolicyReviewerKind")
    if type(value.ref) is not str:
        _fail("reviewer_ref ref must use exact str storage")
    restored = DomainEvaluationPolicyReviewerRef(value.kind, value.ref)
    if restored.kind is not value.kind or restored.ref != value.ref:
        _fail("reviewer_ref must equal strict scalar reconstruction")
    return restored


def _strict_review(value: DomainEvaluationPolicyReview) -> DomainEvaluationPolicyReview:
    if type(value) is not DomainEvaluationPolicyReview:
        _fail("review must use exact DomainEvaluationPolicyReview")
    review_id = _strict_review_id(value.review_id)
    policy_ref = _strict_policy_ref(value.policy_ref)
    specification_sha256 = _sha256(value.specification_sha256, "specification_sha256")
    reviewer_ref = _strict_reviewer_ref(value.reviewer_ref)
    if type(value.verdict) is not DomainEvaluationPolicyReviewVerdict:
        _fail("review verdict must use exact DomainEvaluationPolicyReviewVerdict")
    reviewed_at = _strict_time(value.reviewed_at, "reviewed_at")
    if type(value.rationale) is not str:
        _fail("review rationale must use exact str storage")
    restored = DomainEvaluationPolicyReview(
        review_id=review_id,
        policy_ref=policy_ref,
        specification_sha256=specification_sha256,
        reviewer_ref=reviewer_ref,
        verdict=value.verdict,
        reviewed_at=reviewed_at,
        rationale=value.rationale,
    )
    if restored.rationale != value.rationale:
        _fail("review rationale must already use canonical text storage")
    return restored


def _review_payload(value: DomainEvaluationPolicyReview) -> dict:
    value = _strict_review(value)
    return {
        "schema_version": 1,
        "review_id": str(value.review_id),
        "policy_ref": str(value.policy_ref),
        "specification_sha256": value.specification_sha256,
        "reviewer_ref": {
            "kind": value.reviewer_ref.kind.value,
            "ref": value.reviewer_ref.ref,
        },
        "verdict": value.verdict.value,
        "reviewed_at": _format_time(value.reviewed_at),
        "rationale": value.rationale,
    }


def domain_evaluation_policy_review_sha256_v1(
    review: DomainEvaluationPolicyReview,
) -> str:
    return _hash(_REVIEW_HASH_DOMAIN, _review_payload(review))


def validate_domain_evaluation_policy_review_v1(
    *,
    specification: DomainEvaluationPolicySpecification,
    review: DomainEvaluationPolicyReview,
) -> None:
    specification = _strict_specification(specification)
    review = _strict_review(review)
    expected_digest = domain_evaluation_policy_specification_sha256_v1(specification)
    if review.policy_ref != specification.policy_ref:
        _fail("review policy_ref does not match exact specification policy_ref")
    if review.specification_sha256 != expected_digest:
        _fail("review specification_sha256 does not match exact PR12.6 specification")


def review_domain_evaluation_policy_specification_v1(
    *,
    specification: DomainEvaluationPolicySpecification,
    review_id: DomainEvaluationPolicyReviewId,
    reviewer_ref: DomainEvaluationPolicyReviewerRef,
    verdict: DomainEvaluationPolicyReviewVerdict,
    reviewed_at: datetime,
    rationale: str,
) -> DomainEvaluationPolicyReview:
    """Create one declared-HUMAN review of one exact PR12.6 policy specification."""

    specification = _strict_specification(specification)
    review = DomainEvaluationPolicyReview(
        review_id=review_id,
        policy_ref=specification.policy_ref,
        specification_sha256=domain_evaluation_policy_specification_sha256_v1(
            specification
        ),
        reviewer_ref=reviewer_ref,
        verdict=verdict,
        reviewed_at=reviewed_at,
        rationale=rationale,
    )
    validate_domain_evaluation_policy_review_v1(
        specification=specification,
        review=review,
    )
    return review


@dataclass(frozen=True, slots=True)
class DomainEvaluationPolicyReviewLedger:
    """Serializable structural review lineage; not terminal authority by itself."""

    reviews: tuple[DomainEvaluationPolicyReview, ...] = ()

    def __post_init__(self) -> None:
        if type(self.reviews) is not tuple:
            _fail("review ledger reviews must use exact tuple storage")
        restored = tuple(_strict_review(review) for review in self.reviews)
        seen_ids: set[DomainEvaluationPolicyReviewId] = set()
        seen_identities: set[tuple[EvaluationPolicyRef, str]] = set()
        for review in restored:
            if review.review_id in seen_ids:
                _fail(f"duplicate review_id in review ledger: {review.review_id}")
            identity = (review.policy_ref, review.specification_sha256)
            if identity in seen_identities:
                _fail("exact policy specification already has a terminal review in ledger")
            seen_ids.add(review.review_id)
            seen_identities.add(identity)
        object.__setattr__(self, "reviews", restored)

    def to_dict(self) -> dict:
        from .governance_serialization import domain_evaluation_policy_review_ledger_to_dict

        return domain_evaluation_policy_review_ledger_to_dict(self)

    @classmethod
    def from_dict(cls, payload: object) -> "DomainEvaluationPolicyReviewLedger":
        from .governance_serialization import domain_evaluation_policy_review_ledger_from_dict

        return domain_evaluation_policy_review_ledger_from_dict(payload)

    def to_json(self) -> str:
        from .governance_serialization import domain_evaluation_policy_review_ledger_to_json

        return domain_evaluation_policy_review_ledger_to_json(self)

    @classmethod
    def from_json(cls, payload: object) -> "DomainEvaluationPolicyReviewLedger":
        from .governance_serialization import domain_evaluation_policy_review_ledger_from_json

        return domain_evaluation_policy_review_ledger_from_json(payload)


def _strict_review_ledger(
    value: DomainEvaluationPolicyReviewLedger,
) -> DomainEvaluationPolicyReviewLedger:
    if type(value) is not DomainEvaluationPolicyReviewLedger:
        _fail("review_ledger must use exact DomainEvaluationPolicyReviewLedger")
    if type(value.reviews) is not tuple:
        _fail("review_ledger reviews must use exact tuple storage")
    return DomainEvaluationPolicyReviewLedger(
        reviews=tuple(_strict_review(review) for review in value.reviews)
    )


def _review_ledger_payload(value: DomainEvaluationPolicyReviewLedger) -> dict:
    value = _strict_review_ledger(value)
    return {
        "schema_version": 1,
        "reviews": [_review_payload(review) for review in value.reviews],
    }


def domain_evaluation_policy_review_ledger_sha256_v1(
    review_ledger: DomainEvaluationPolicyReviewLedger,
) -> str:
    return _hash(_REVIEW_LEDGER_HASH_DOMAIN, _review_ledger_payload(review_ledger))


def validate_domain_evaluation_policy_review_ledger_successor_v1(
    previous: DomainEvaluationPolicyReviewLedger,
    current: DomainEvaluationPolicyReviewLedger,
) -> None:
    previous = _strict_review_ledger(previous)
    current = _strict_review_ledger(current)
    if len(current.reviews) < len(previous.reviews):
        _fail("review ledger successor may not remove prior terminal reviews")
    if current.reviews[: len(previous.reviews)] != previous.reviews:
        _fail("review ledger successor must preserve the exact prior review prefix")


class DomainEvaluationPolicyReviewAdmission:
    """Runtime-only proof that one exact review passed terminal admission.

    Instances cannot be constructed through the public constructor and are not
    serializable.  The admission function issues them and binds them to the
    exact review plus the exact predecessor/successor transition and the exact
    current review-ledger snapshot used for downstream authority.
    """

    __slots__ = (
        "policy_ref",
        "specification_sha256",
        "review_id",
        "review_sha256",
        "predecessor_review_ledger_sha256",
        "successor_review_ledger_sha256",
        "review_ledger_sha256",
    )

    def __init__(self, *args: object, **kwargs: object) -> None:
        _fail(
            "review admission authority can only be issued by "
            "admit_domain_evaluation_policy_review_v1"
        )

    def __setattr__(self, name: str, value: object) -> None:
        _fail("review admission authority is immutable")

    def __reduce__(self):
        _fail("review admission authority is runtime-only and not serializable")

    def __repr__(self) -> str:
        return (
            "DomainEvaluationPolicyReviewAdmission("
            f"policy_ref={self.policy_ref!s}, "
            f"specification_sha256={self.specification_sha256!r}, "
            f"review_id={self.review_id!s})"
        )


def _review_admission_payload(
    value: DomainEvaluationPolicyReviewAdmission,
) -> tuple[object, ...]:
    if type(value) is not DomainEvaluationPolicyReviewAdmission:
        _fail("review_admission must use exact DomainEvaluationPolicyReviewAdmission")
    return (
        str(_strict_policy_ref(value.policy_ref)),
        _sha256(value.specification_sha256, "review admission specification_sha256"),
        str(_strict_review_id(value.review_id)),
        _sha256(value.review_sha256, "review admission review_sha256"),
        _sha256(
            value.predecessor_review_ledger_sha256,
            "review admission predecessor_review_ledger_sha256",
        ),
        _sha256(
            value.successor_review_ledger_sha256,
            "review admission successor_review_ledger_sha256",
        ),
        _sha256(
            value.review_ledger_sha256,
            "review admission review_ledger_sha256",
        ),
    )


def _strict_review_admission(
    value: DomainEvaluationPolicyReviewAdmission,
) -> DomainEvaluationPolicyReviewAdmission:
    if type(value) is not DomainEvaluationPolicyReviewAdmission:
        _fail("review_admission must use exact DomainEvaluationPolicyReviewAdmission")
    issued = _ISSUED_REVIEW_ADMISSIONS.get(id(value))
    if issued is None or issued[0] is not value:
        _fail(
            "review admission authority was not issued by the terminal-review admission path"
        )
    current_payload = _review_admission_payload(value)
    if issued[1] != current_payload:
        _fail("review admission authority no longer matches its issued transition")
    return value


def _issue_review_admission(
    *,
    review: DomainEvaluationPolicyReview,
    predecessor_review_ledger: DomainEvaluationPolicyReviewLedger,
    transition_successor_review_ledger: DomainEvaluationPolicyReviewLedger,
    current_review_ledger: DomainEvaluationPolicyReviewLedger,
) -> DomainEvaluationPolicyReviewAdmission:
    review = _strict_review(review)
    predecessor_review_ledger = _strict_review_ledger(predecessor_review_ledger)
    transition_successor_review_ledger = _strict_review_ledger(
        transition_successor_review_ledger
    )
    current_review_ledger = _strict_review_ledger(current_review_ledger)
    validate_domain_evaluation_policy_review_ledger_successor_v1(
        predecessor_review_ledger,
        transition_successor_review_ledger,
    )
    if len(transition_successor_review_ledger.reviews) != len(
        predecessor_review_ledger.reviews
    ) + 1:
        _fail("terminal-review authority must bind an exact one-review append transition")
    if transition_successor_review_ledger.reviews[-1] != review:
        _fail("terminal-review authority transition must append the exact review")
    if current_review_ledger.reviews[: len(transition_successor_review_ledger.reviews)] != (
        transition_successor_review_ledger.reviews
    ):
        _fail("current review ledger must preserve the admitted transition prefix")

    admission = object.__new__(DomainEvaluationPolicyReviewAdmission)
    object.__setattr__(admission, "policy_ref", review.policy_ref)
    object.__setattr__(admission, "specification_sha256", review.specification_sha256)
    object.__setattr__(admission, "review_id", review.review_id)
    object.__setattr__(
        admission,
        "review_sha256",
        domain_evaluation_policy_review_sha256_v1(review),
    )
    object.__setattr__(
        admission,
        "predecessor_review_ledger_sha256",
        domain_evaluation_policy_review_ledger_sha256_v1(predecessor_review_ledger),
    )
    object.__setattr__(
        admission,
        "successor_review_ledger_sha256",
        domain_evaluation_policy_review_ledger_sha256_v1(
            transition_successor_review_ledger
        ),
    )
    object.__setattr__(
        admission,
        "review_ledger_sha256",
        domain_evaluation_policy_review_ledger_sha256_v1(current_review_ledger),
    )
    payload = _review_admission_payload(admission)
    _ISSUED_REVIEW_ADMISSIONS[id(admission)] = (admission, payload)
    return admission


def admit_domain_evaluation_policy_review_v1(
    *,
    review_ledger: DomainEvaluationPolicyReviewLedger,
    specification: DomainEvaluationPolicySpecification,
    review: DomainEvaluationPolicyReview,
) -> tuple[DomainEvaluationPolicyReviewLedger, DomainEvaluationPolicyReviewAdmission]:
    """Admit one exact terminal review and issue runtime transition authority.

    Exact replay is idempotent for ledger content, but it issues fresh runtime
    authority bound to the exact current ledger snapshot.  A populated ledger
    constructed or deserialized without this transition call is audit data only.
    """

    review_ledger = _strict_review_ledger(review_ledger)
    specification = _strict_specification(specification)
    review = _strict_review(review)
    validate_domain_evaluation_policy_review_v1(
        specification=specification,
        review=review,
    )
    identity = (review.policy_ref, review.specification_sha256)
    for index, existing in enumerate(review_ledger.reviews):
        existing_identity = (existing.policy_ref, existing.specification_sha256)
        if existing_identity == identity:
            if _review_payload(existing) != _review_payload(review):
                _fail("exact policy specification already has a different terminal review")
            predecessor = DomainEvaluationPolicyReviewLedger(
                reviews=review_ledger.reviews[:index]
            )
            transition_successor = DomainEvaluationPolicyReviewLedger(
                reviews=review_ledger.reviews[: index + 1]
            )
            admission = _issue_review_admission(
                review=review,
                predecessor_review_ledger=predecessor,
                transition_successor_review_ledger=transition_successor,
                current_review_ledger=review_ledger,
            )
            return review_ledger, admission
        if existing.review_id == review.review_id:
            _fail("review_id is already bound to a different policy specification")

    successor = DomainEvaluationPolicyReviewLedger(
        reviews=review_ledger.reviews + (review,)
    )
    validate_domain_evaluation_policy_review_ledger_successor_v1(
        review_ledger,
        successor,
    )
    admission = _issue_review_admission(
        review=review,
        predecessor_review_ledger=review_ledger,
        transition_successor_review_ledger=successor,
        current_review_ledger=successor,
    )
    return successor, admission


def resolve_domain_evaluation_policy_terminal_review_v1(
    *,
    review_ledger: DomainEvaluationPolicyReviewLedger,
    specification: DomainEvaluationPolicySpecification,
) -> DomainEvaluationPolicyReview:
    """Structurally resolve a review; this does not establish admission authority."""

    review_ledger = _strict_review_ledger(review_ledger)
    specification = _strict_specification(specification)
    digest = domain_evaluation_policy_specification_sha256_v1(specification)
    matches = tuple(
        review
        for review in review_ledger.reviews
        if review.policy_ref == specification.policy_ref
        and review.specification_sha256 == digest
    )
    if len(matches) != 1:
        _fail("exact policy specification has no terminal review in supplied ledger")
    review = matches[0]
    validate_domain_evaluation_policy_review_v1(
        specification=specification,
        review=review,
    )
    return review


def validate_domain_evaluation_policy_review_admission_v1(
    *,
    review_ledger: DomainEvaluationPolicyReviewLedger,
    specification: DomainEvaluationPolicySpecification,
    review_admission: DomainEvaluationPolicyReviewAdmission,
) -> DomainEvaluationPolicyReview:
    """Validate sealed runtime authority against one exact review-ledger transition."""

    review_ledger = _strict_review_ledger(review_ledger)
    specification = _strict_specification(specification)
    review_admission = _strict_review_admission(review_admission)
    specification_sha256 = domain_evaluation_policy_specification_sha256_v1(
        specification
    )
    if review_admission.policy_ref != specification.policy_ref:
        _fail("review admission policy_ref does not match exact specification")
    if review_admission.specification_sha256 != specification_sha256:
        _fail("review admission specification_sha256 does not match exact specification")
    current_ledger_sha256 = domain_evaluation_policy_review_ledger_sha256_v1(
        review_ledger
    )
    if review_admission.review_ledger_sha256 != current_ledger_sha256:
        _fail("review admission authority is stale for the supplied review ledger")

    matches = tuple(
        (index, review)
        for index, review in enumerate(review_ledger.reviews)
        if review.policy_ref == specification.policy_ref
        and review.specification_sha256 == specification_sha256
    )
    if len(matches) != 1:
        _fail("review admission exact specification has no unique review in supplied ledger")
    index, review = matches[0]
    validate_domain_evaluation_policy_review_v1(
        specification=specification,
        review=review,
    )
    if review_admission.review_id != review.review_id:
        _fail("review admission review_id does not match exact terminal review")
    review_sha256 = domain_evaluation_policy_review_sha256_v1(review)
    if review_admission.review_sha256 != review_sha256:
        _fail("review admission review_sha256 does not match exact terminal review")

    predecessor = DomainEvaluationPolicyReviewLedger(
        reviews=review_ledger.reviews[:index]
    )
    transition_successor = DomainEvaluationPolicyReviewLedger(
        reviews=review_ledger.reviews[: index + 1]
    )
    predecessor_sha256 = domain_evaluation_policy_review_ledger_sha256_v1(predecessor)
    successor_sha256 = domain_evaluation_policy_review_ledger_sha256_v1(
        transition_successor
    )
    if review_admission.predecessor_review_ledger_sha256 != predecessor_sha256:
        _fail("review admission predecessor digest does not match exact transition")
    if review_admission.successor_review_ledger_sha256 != successor_sha256:
        _fail("review admission successor digest does not match exact transition")
    return review


def require_approved_domain_evaluation_policy_review_v1(
    *,
    review_ledger: DomainEvaluationPolicyReviewLedger,
    specification: DomainEvaluationPolicySpecification,
    review_admission: DomainEvaluationPolicyReviewAdmission,
) -> DomainEvaluationPolicyReview:
    """Require sealed terminal-review authority and an exact APPROVE verdict."""

    review = validate_domain_evaluation_policy_review_admission_v1(
        review_ledger=review_ledger,
        specification=specification,
        review_admission=review_admission,
    )
    if review.verdict is not DomainEvaluationPolicyReviewVerdict.APPROVE:
        _fail("policy specification terminal review is REJECT, not APPROVE")
    return review


@dataclass(frozen=True, slots=True)
class DomainEvaluationPolicyRegistryEntry:
    policy_ref: EvaluationPolicyRef
    specification_sha256: str
    specification: DomainEvaluationPolicySpecification
    review_id: DomainEvaluationPolicyReviewId
    review_sha256: str
    admitted_at: datetime
    predecessor_registry_sha256: str

    def __post_init__(self) -> None:
        policy_ref = _strict_policy_ref(self.policy_ref)
        specification_sha256 = _sha256(
            self.specification_sha256,
            "specification_sha256",
        )
        specification = _strict_specification(self.specification)
        review_id = _strict_review_id(self.review_id)
        review_sha256 = _sha256(self.review_sha256, "review_sha256")
        admitted_at = _time(self.admitted_at, "admitted_at")
        predecessor = _sha256(
            self.predecessor_registry_sha256,
            "predecessor_registry_sha256",
        )
        if specification.policy_ref != policy_ref:
            _fail("registry entry policy_ref does not match embedded specification")
        if domain_evaluation_policy_specification_sha256_v1(specification) != specification_sha256:
            _fail("registry entry specification_sha256 does not match embedded specification")
        object.__setattr__(self, "policy_ref", policy_ref)
        object.__setattr__(self, "specification_sha256", specification_sha256)
        object.__setattr__(self, "specification", specification)
        object.__setattr__(self, "review_id", review_id)
        object.__setattr__(self, "review_sha256", review_sha256)
        object.__setattr__(self, "admitted_at", admitted_at)
        object.__setattr__(self, "predecessor_registry_sha256", predecessor)


def _strict_registry_entry(
    value: DomainEvaluationPolicyRegistryEntry,
) -> DomainEvaluationPolicyRegistryEntry:
    if type(value) is not DomainEvaluationPolicyRegistryEntry:
        _fail("registry entry must use exact DomainEvaluationPolicyRegistryEntry")
    if type(value.specification_sha256) is not str:
        _fail("registry entry specification_sha256 must use exact str storage")
    if type(value.review_sha256) is not str:
        _fail("registry entry review_sha256 must use exact str storage")
    if type(value.predecessor_registry_sha256) is not str:
        _fail("registry entry predecessor_registry_sha256 must use exact str storage")
    return DomainEvaluationPolicyRegistryEntry(
        policy_ref=_strict_policy_ref(value.policy_ref),
        specification_sha256=value.specification_sha256,
        specification=_strict_specification(value.specification),
        review_id=_strict_review_id(value.review_id),
        review_sha256=value.review_sha256,
        admitted_at=_strict_time(value.admitted_at, "admitted_at"),
        predecessor_registry_sha256=value.predecessor_registry_sha256,
    )


def _registry_entry_payload(value: DomainEvaluationPolicyRegistryEntry) -> dict:
    value = _strict_registry_entry(value)
    return {
        "policy_ref": str(value.policy_ref),
        "specification_sha256": value.specification_sha256,
        "specification": value.specification.to_dict(),
        "review_id": str(value.review_id),
        "review_sha256": value.review_sha256,
        "admitted_at": _format_time(value.admitted_at),
        "predecessor_registry_sha256": value.predecessor_registry_sha256,
    }


def _registry_payload_from_entries(
    entries: tuple[DomainEvaluationPolicyRegistryEntry, ...],
) -> dict:
    return {
        "schema_version": 1,
        "entries": [_registry_entry_payload(entry) for entry in entries],
    }


def _registry_sha256_from_entries(
    entries: tuple[DomainEvaluationPolicyRegistryEntry, ...],
) -> str:
    return _hash(_REGISTRY_HASH_DOMAIN, _registry_payload_from_entries(entries))


@dataclass(frozen=True, slots=True)
class DomainEvaluationPolicyRegistry:
    """One append-only immutable lineage of exact policy-ref -> exact content bindings."""

    entries: tuple[DomainEvaluationPolicyRegistryEntry, ...] = ()

    def __post_init__(self) -> None:
        if type(self.entries) is not tuple:
            _fail("registry entries must use exact tuple storage")
        restored = tuple(_strict_registry_entry(entry) for entry in self.entries)
        seen_refs: set[EvaluationPolicyRef] = set()
        for index, entry in enumerate(restored):
            if entry.policy_ref in seen_refs:
                _fail(f"duplicate policy_ref in registry: {entry.policy_ref}")
            expected_predecessor = _registry_sha256_from_entries(restored[:index])
            if entry.predecessor_registry_sha256 != expected_predecessor:
                _fail("registry entry predecessor digest does not match exact prior registry prefix")
            seen_refs.add(entry.policy_ref)
        object.__setattr__(self, "entries", restored)

    def to_dict(self) -> dict:
        from .governance_serialization import domain_evaluation_policy_registry_to_dict

        return domain_evaluation_policy_registry_to_dict(self)

    @classmethod
    def from_dict(cls, payload: object) -> "DomainEvaluationPolicyRegistry":
        from .governance_serialization import domain_evaluation_policy_registry_from_dict

        return domain_evaluation_policy_registry_from_dict(payload)

    def to_json(self) -> str:
        from .governance_serialization import domain_evaluation_policy_registry_to_json

        return domain_evaluation_policy_registry_to_json(self)

    @classmethod
    def from_json(cls, payload: object) -> "DomainEvaluationPolicyRegistry":
        from .governance_serialization import domain_evaluation_policy_registry_from_json

        return domain_evaluation_policy_registry_from_json(payload)


def _strict_registry(value: DomainEvaluationPolicyRegistry) -> DomainEvaluationPolicyRegistry:
    if type(value) is not DomainEvaluationPolicyRegistry:
        _fail("registry must use exact DomainEvaluationPolicyRegistry")
    if type(value.entries) is not tuple:
        _fail("registry entries must use exact tuple storage")
    return DomainEvaluationPolicyRegistry(
        entries=tuple(_strict_registry_entry(entry) for entry in value.entries)
    )


def _registry_payload(value: DomainEvaluationPolicyRegistry) -> dict:
    value = _strict_registry(value)
    return _registry_payload_from_entries(value.entries)


def domain_evaluation_policy_registry_sha256_v1(
    registry: DomainEvaluationPolicyRegistry,
) -> str:
    registry = _strict_registry(registry)
    return _registry_sha256_from_entries(registry.entries)


def validate_domain_evaluation_policy_registry_successor_v1(
    previous: DomainEvaluationPolicyRegistry,
    current: DomainEvaluationPolicyRegistry,
) -> None:
    previous = _strict_registry(previous)
    current = _strict_registry(current)
    if len(current.entries) < len(previous.entries):
        _fail("policy registry successor may not remove prior admitted policies")
    if current.entries[: len(previous.entries)] != previous.entries:
        _fail("policy registry successor must preserve the exact prior registry prefix")


def resolve_admitted_domain_evaluation_policy_v1(
    *,
    registry: DomainEvaluationPolicyRegistry,
    policy_ref: EvaluationPolicyRef,
    specification_sha256: str,
) -> DomainEvaluationPolicySpecification:
    """Resolve only an exact admitted ref+content binding; no latest/supersession semantics."""

    registry = _strict_registry(registry)
    policy_ref = _strict_policy_ref(policy_ref)
    specification_sha256 = _sha256(specification_sha256, "specification_sha256")
    matches = tuple(entry for entry in registry.entries if entry.policy_ref == policy_ref)
    if len(matches) != 1:
        _fail("policy_ref is not admitted in supplied registry")
    entry = matches[0]
    if entry.specification_sha256 != specification_sha256:
        _fail("admitted policy digest does not match requested exact content")
    specification = _strict_specification(entry.specification)
    if domain_evaluation_policy_specification_sha256_v1(specification) != specification_sha256:
        _fail("admitted policy embedded content fails exact digest replay")
    return specification


@dataclass(frozen=True, slots=True)
class DomainEvaluationPolicyAdmissionReceipt:
    policy_ref: EvaluationPolicyRef
    specification_sha256: str
    review_id: DomainEvaluationPolicyReviewId
    review_sha256: str
    predecessor_registry_sha256: str
    successor_registry_sha256: str
    admitted_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "policy_ref", _strict_policy_ref(self.policy_ref))
        object.__setattr__(
            self,
            "specification_sha256",
            _sha256(self.specification_sha256, "specification_sha256"),
        )
        object.__setattr__(self, "review_id", _strict_review_id(self.review_id))
        object.__setattr__(self, "review_sha256", _sha256(self.review_sha256, "review_sha256"))
        object.__setattr__(
            self,
            "predecessor_registry_sha256",
            _sha256(self.predecessor_registry_sha256, "predecessor_registry_sha256"),
        )
        object.__setattr__(
            self,
            "successor_registry_sha256",
            _sha256(self.successor_registry_sha256, "successor_registry_sha256"),
        )
        object.__setattr__(self, "admitted_at", _time(self.admitted_at, "admitted_at"))

    def to_dict(self) -> dict:
        from .governance_serialization import domain_evaluation_policy_admission_receipt_to_dict

        return domain_evaluation_policy_admission_receipt_to_dict(self)

    @classmethod
    def from_dict(cls, payload: object) -> "DomainEvaluationPolicyAdmissionReceipt":
        from .governance_serialization import domain_evaluation_policy_admission_receipt_from_dict

        return domain_evaluation_policy_admission_receipt_from_dict(payload)

    def to_json(self) -> str:
        from .governance_serialization import domain_evaluation_policy_admission_receipt_to_json

        return domain_evaluation_policy_admission_receipt_to_json(self)

    @classmethod
    def from_json(cls, payload: object) -> "DomainEvaluationPolicyAdmissionReceipt":
        from .governance_serialization import domain_evaluation_policy_admission_receipt_from_json

        return domain_evaluation_policy_admission_receipt_from_json(payload)


def _strict_receipt(
    value: DomainEvaluationPolicyAdmissionReceipt,
) -> DomainEvaluationPolicyAdmissionReceipt:
    if type(value) is not DomainEvaluationPolicyAdmissionReceipt:
        _fail("receipt must use exact DomainEvaluationPolicyAdmissionReceipt")
    for field_name in (
        "specification_sha256",
        "review_sha256",
        "predecessor_registry_sha256",
        "successor_registry_sha256",
    ):
        if type(getattr(value, field_name)) is not str:
            _fail(f"receipt {field_name} must use exact str storage")
    return DomainEvaluationPolicyAdmissionReceipt(
        policy_ref=_strict_policy_ref(value.policy_ref),
        specification_sha256=value.specification_sha256,
        review_id=_strict_review_id(value.review_id),
        review_sha256=value.review_sha256,
        predecessor_registry_sha256=value.predecessor_registry_sha256,
        successor_registry_sha256=value.successor_registry_sha256,
        admitted_at=_strict_time(value.admitted_at, "admitted_at"),
    )


def _receipt_payload(value: DomainEvaluationPolicyAdmissionReceipt) -> dict:
    value = _strict_receipt(value)
    return {
        "schema_version": 1,
        "policy_ref": str(value.policy_ref),
        "specification_sha256": value.specification_sha256,
        "review_id": str(value.review_id),
        "review_sha256": value.review_sha256,
        "predecessor_registry_sha256": value.predecessor_registry_sha256,
        "successor_registry_sha256": value.successor_registry_sha256,
        "admitted_at": _format_time(value.admitted_at),
    }


def domain_evaluation_policy_admission_receipt_sha256_v1(
    receipt: DomainEvaluationPolicyAdmissionReceipt,
) -> str:
    return _hash(_RECEIPT_HASH_DOMAIN, _receipt_payload(receipt))


def validate_domain_evaluation_policy_admission_receipt_v1(
    *,
    predecessor_registry: DomainEvaluationPolicyRegistry,
    successor_registry: DomainEvaluationPolicyRegistry,
    review_ledger: DomainEvaluationPolicyReviewLedger,
    review_admission: DomainEvaluationPolicyReviewAdmission,
    specification: DomainEvaluationPolicySpecification,
    receipt: DomainEvaluationPolicyAdmissionReceipt,
) -> None:
    predecessor_registry = _strict_registry(predecessor_registry)
    successor_registry = _strict_registry(successor_registry)
    review_ledger = _strict_review_ledger(review_ledger)
    specification = _strict_specification(specification)
    receipt = _strict_receipt(receipt)
    review = require_approved_domain_evaluation_policy_review_v1(
        review_ledger=review_ledger,
        specification=specification,
        review_admission=review_admission,
    )
    validate_domain_evaluation_policy_registry_successor_v1(
        predecessor_registry,
        successor_registry,
    )
    if len(successor_registry.entries) != len(predecessor_registry.entries) + 1:
        _fail("admission receipt successor must append exactly one registry entry")
    entry = successor_registry.entries[-1]
    specification_sha256 = domain_evaluation_policy_specification_sha256_v1(
        specification
    )
    review_sha256 = domain_evaluation_policy_review_sha256_v1(review)
    predecessor_sha256 = domain_evaluation_policy_registry_sha256_v1(
        predecessor_registry
    )
    successor_sha256 = domain_evaluation_policy_registry_sha256_v1(successor_registry)
    if receipt.policy_ref != specification.policy_ref:
        _fail("receipt policy_ref does not match exact admitted specification")
    if receipt.specification_sha256 != specification_sha256:
        _fail("receipt specification_sha256 does not match exact admitted specification")
    if receipt.review_id != review.review_id:
        _fail("receipt review_id does not match terminal APPROVE review")
    if receipt.review_sha256 != review_sha256:
        _fail("receipt review_sha256 does not match terminal APPROVE review")
    if receipt.predecessor_registry_sha256 != predecessor_sha256:
        _fail("receipt predecessor_registry_sha256 does not match predecessor registry")
    if receipt.successor_registry_sha256 != successor_sha256:
        _fail("receipt successor_registry_sha256 does not match successor registry")
    if receipt.admitted_at < review.reviewed_at:
        _fail("receipt admitted_at must not precede terminal policy review")
    if entry.policy_ref != receipt.policy_ref:
        _fail("receipt policy_ref does not match appended registry entry")
    if entry.specification_sha256 != receipt.specification_sha256:
        _fail("receipt specification_sha256 does not match appended registry entry")
    if entry.review_id != receipt.review_id or entry.review_sha256 != receipt.review_sha256:
        _fail("receipt review binding does not match appended registry entry")
    if entry.predecessor_registry_sha256 != receipt.predecessor_registry_sha256:
        _fail("receipt predecessor digest does not match appended registry entry")
    if entry.admitted_at != receipt.admitted_at:
        _fail("receipt admitted_at does not match appended registry entry")
    if entry.specification.to_json() != specification.to_json():
        _fail("receipt successor embeds different specification content")


def _receipt_for_existing_entry(
    *,
    registry: DomainEvaluationPolicyRegistry,
    entry_index: int,
) -> tuple[
    DomainEvaluationPolicyRegistry,
    DomainEvaluationPolicyRegistry,
    DomainEvaluationPolicyAdmissionReceipt,
]:
    predecessor = DomainEvaluationPolicyRegistry(entries=registry.entries[:entry_index])
    successor = DomainEvaluationPolicyRegistry(entries=registry.entries[: entry_index + 1])
    entry = successor.entries[-1]
    receipt = DomainEvaluationPolicyAdmissionReceipt(
        policy_ref=entry.policy_ref,
        specification_sha256=entry.specification_sha256,
        review_id=entry.review_id,
        review_sha256=entry.review_sha256,
        predecessor_registry_sha256=entry.predecessor_registry_sha256,
        successor_registry_sha256=domain_evaluation_policy_registry_sha256_v1(successor),
        admitted_at=entry.admitted_at,
    )
    return predecessor, successor, receipt


def admit_domain_evaluation_policy_v1(
    *,
    registry: DomainEvaluationPolicyRegistry,
    review_ledger: DomainEvaluationPolicyReviewLedger,
    review_admission: DomainEvaluationPolicyReviewAdmission,
    specification: DomainEvaluationPolicySpecification,
    admitted_at: datetime,
) -> tuple[DomainEvaluationPolicyRegistry, DomainEvaluationPolicyAdmissionReceipt]:
    """Admit exact approved policy content using sealed terminal-review authority."""

    registry = _strict_registry(registry)
    review_ledger = _strict_review_ledger(review_ledger)
    specification = _strict_specification(specification)
    review = require_approved_domain_evaluation_policy_review_v1(
        review_ledger=review_ledger,
        specification=specification,
        review_admission=review_admission,
    )
    admitted_at = _time(admitted_at, "admitted_at")
    if admitted_at < review.reviewed_at:
        _fail("admitted_at must not precede terminal policy review")
    specification_sha256 = domain_evaluation_policy_specification_sha256_v1(
        specification
    )
    review_sha256 = domain_evaluation_policy_review_sha256_v1(review)

    for index, existing in enumerate(registry.entries):
        if existing.policy_ref != specification.policy_ref:
            continue
        if existing.specification_sha256 != specification_sha256:
            _fail("policy_ref is already immutably bound to different specification content")
        if existing.specification.to_json() != specification.to_json():
            _fail("policy_ref exact-content replay failed despite matching digest")
        if existing.review_id != review.review_id or existing.review_sha256 != review_sha256:
            _fail("same admitted policy content may only replay its exact original terminal review")
        predecessor, original_successor, receipt = _receipt_for_existing_entry(
            registry=registry,
            entry_index=index,
        )
        validate_domain_evaluation_policy_admission_receipt_v1(
            predecessor_registry=predecessor,
            successor_registry=original_successor,
            review_ledger=review_ledger,
            review_admission=review_admission,
            specification=specification,
            receipt=receipt,
        )
        return registry, receipt

    predecessor_sha256 = domain_evaluation_policy_registry_sha256_v1(registry)
    entry = DomainEvaluationPolicyRegistryEntry(
        policy_ref=specification.policy_ref,
        specification_sha256=specification_sha256,
        specification=specification,
        review_id=review.review_id,
        review_sha256=review_sha256,
        admitted_at=admitted_at,
        predecessor_registry_sha256=predecessor_sha256,
    )
    successor = DomainEvaluationPolicyRegistry(entries=registry.entries + (entry,))
    validate_domain_evaluation_policy_registry_successor_v1(registry, successor)
    receipt = DomainEvaluationPolicyAdmissionReceipt(
        policy_ref=specification.policy_ref,
        specification_sha256=specification_sha256,
        review_id=review.review_id,
        review_sha256=review_sha256,
        predecessor_registry_sha256=predecessor_sha256,
        successor_registry_sha256=domain_evaluation_policy_registry_sha256_v1(successor),
        admitted_at=admitted_at,
    )
    validate_domain_evaluation_policy_admission_receipt_v1(
        predecessor_registry=registry,
        successor_registry=successor,
        review_ledger=review_ledger,
        review_admission=review_admission,
        specification=specification,
        receipt=receipt,
    )
    return successor, receipt
