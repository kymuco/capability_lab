"""PR12.10 complete evidence lineage profiles and shared-origin dependence gate v1."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import json

from capability_lab.semantics import CapabilityConceptRef, CapabilityId

from .claim_evidence_disposition_coverage import (
    ClaimEvidenceDispositionCoverageError,
    ClaimEvidenceDispositionCoverageReceipt,
    validate_complete_claim_evidence_disposition_coverage_v1,
)
from .core import (
    CapabilityClaimId,
    CapabilitySubjectRef,
    EpistemicError,
    EvidenceId,
    ProvenanceSource,
    ProvenanceSourceKind,
    canonical_time,
    format_time,
    parse_time,
)
from .record_set import EpistemicRecordSet


class ClaimEvidenceLineageDependenceError(EpistemicError):
    """Base error for PR12.10 evidence-lineage dependence governance."""


class InvalidClaimEvidenceLineageDependence(ClaimEvidenceLineageDependenceError):
    """The supplied lineage artifact violates PR12.10 deterministic semantics."""


class EvidenceLineageRelation(str, Enum):
    """The only pairwise lineage conclusions PR12.10 v1 is allowed to emit."""

    PROVEN_SHARED_LINEAGE = "proven_shared_lineage"
    UNRESOLVED = "unresolved"


_SCHEMA_VERSION = 1
_SHA256_HEX_DIGITS = frozenset("0123456789abcdef")
_ORIGIN_KINDS = frozenset(
    {
        ProvenanceSourceKind.ARTIFACT,
        ProvenanceSourceKind.EXTERNAL_RECORD,
    }
)


def _fail(message: str) -> None:
    raise InvalidClaimEvidenceLineageDependence(message)


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
        raise InvalidClaimEvidenceLineageDependence(str(exc)) from exc


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
        raise InvalidClaimEvidenceLineageDependence(
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
        raise InvalidClaimEvidenceLineageDependence(
            f"{field_name} failed strict reconstruction: {exc}"
        ) from exc
    if restored != value:
        _fail(f"{field_name} must equal strict semantic reconstruction")
    return value


def _strict_evidence_id(value: object, field_name: str = "evidence_id") -> EvidenceId:
    if type(value) is not EvidenceId or type(value.value) is not str:
        _fail(f"{field_name} must use exact EvidenceId")
    try:
        restored = EvidenceId(value.value)
    except (TypeError, ValueError) as exc:
        raise InvalidClaimEvidenceLineageDependence(
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
        raise InvalidClaimEvidenceLineageDependence(
            f"{field_name} failed strict reconstruction: {exc}"
        ) from exc
    if restored != value:
        _fail(f"{field_name} must equal strict semantic reconstruction")
    return value


def _strict_evidence_id_tuple(
    value: object,
    field_name: str,
    *,
    require_nonempty: bool = False,
) -> tuple[EvidenceId, ...]:
    if type(value) is not tuple:
        _fail(f"{field_name} must use exact tuple")
    items = value
    for index, item in enumerate(items):
        _strict_evidence_id(item, f"{field_name}[{index}]")
    if require_nonempty and not items:
        _fail(f"{field_name} must be non-empty")
    if len(set(items)) != len(items):
        _fail(f"{field_name} must not contain duplicate ids")
    canonical = tuple(sorted(items))
    if canonical != items:
        _fail(f"{field_name} must use canonical evidence-id ordering")
    return items


def _strict_origin_source(
    value: object,
    field_name: str,
) -> ProvenanceSource:
    if type(value) is not ProvenanceSource:
        _fail(f"{field_name} must use exact ProvenanceSource")
    if type(value.kind) is not ProvenanceSourceKind:
        _fail(f"{field_name}.kind must use exact ProvenanceSourceKind")
    if value.kind not in _ORIGIN_KINDS:
        _fail(
            f"{field_name}.kind must be ARTIFACT or EXTERNAL_RECORD for PR12.10 origins"
        )
    if type(value.ref) is not str:
        _fail(f"{field_name}.ref must use exact str")
    try:
        restored = ProvenanceSource(value.kind, value.ref)
    except (TypeError, ValueError) as exc:
        raise InvalidClaimEvidenceLineageDependence(
            f"{field_name} failed strict reconstruction: {exc}"
        ) from exc
    if restored != value:
        _fail(f"{field_name} must equal strict semantic reconstruction")
    return value


def _strict_origin_tuple(
    value: object,
    field_name: str,
) -> tuple[ProvenanceSource, ...]:
    if type(value) is not tuple:
        _fail(f"{field_name} must use exact tuple")
    items = value
    for index, item in enumerate(items):
        _strict_origin_source(item, f"{field_name}[{index}]")
    if len(set(items)) != len(items):
        _fail(f"{field_name} must not contain duplicate origins")
    canonical = tuple(sorted(items))
    if canonical != items:
        _fail(f"{field_name} must use canonical origin ordering")
    return items


@dataclass(frozen=True, slots=True)
class EvidenceLineageProfile:
    """Deterministic derivation roots and concrete provenance origins for one evidence."""

    evidence_id: EvidenceId
    direct_parent_evidence_ids: tuple[EvidenceId, ...] = ()
    root_evidence_ids: tuple[EvidenceId, ...] = ()
    origin_sources: tuple[ProvenanceSource, ...] = ()

    def __post_init__(self) -> None:
        _strict_evidence_id(self.evidence_id)
        if type(self.direct_parent_evidence_ids) is not tuple:
            _fail("direct_parent_evidence_ids must use exact tuple")
        if type(self.root_evidence_ids) is not tuple:
            _fail("root_evidence_ids must use exact tuple")
        if type(self.origin_sources) is not tuple:
            _fail("origin_sources must use exact tuple")
        for index, item in enumerate(self.direct_parent_evidence_ids):
            _strict_evidence_id(item, f"direct_parent_evidence_ids[{index}]")
        for index, item in enumerate(self.root_evidence_ids):
            _strict_evidence_id(item, f"root_evidence_ids[{index}]")
        for index, item in enumerate(self.origin_sources):
            _strict_origin_source(item, f"origin_sources[{index}]")
        object.__setattr__(
            self,
            "direct_parent_evidence_ids",
            tuple(sorted(self.direct_parent_evidence_ids)),
        )
        object.__setattr__(
            self,
            "root_evidence_ids",
            tuple(sorted(self.root_evidence_ids)),
        )
        object.__setattr__(self, "origin_sources", tuple(sorted(self.origin_sources)))
        _strict_evidence_id_tuple(
            self.direct_parent_evidence_ids,
            "direct_parent_evidence_ids",
        )
        _strict_evidence_id_tuple(
            self.root_evidence_ids,
            "root_evidence_ids",
            require_nonempty=True,
        )
        _strict_origin_tuple(self.origin_sources, "origin_sources")
        if self.evidence_id in self.direct_parent_evidence_ids:
            _fail("lineage profile may not name itself as a direct parent")

    def to_dict(self) -> dict:
        return evidence_lineage_profile_to_dict(self)

    @classmethod
    def from_dict(cls, payload: object) -> "EvidenceLineageProfile":
        return evidence_lineage_profile_from_dict(payload)


def _strict_profile(value: object, field_name: str = "lineage_profile") -> EvidenceLineageProfile:
    if type(value) is not EvidenceLineageProfile:
        _fail(f"{field_name} must use exact EvidenceLineageProfile")
    _strict_evidence_id(value.evidence_id, f"{field_name}.evidence_id")
    _strict_evidence_id_tuple(
        value.direct_parent_evidence_ids,
        f"{field_name}.direct_parent_evidence_ids",
    )
    _strict_evidence_id_tuple(
        value.root_evidence_ids,
        f"{field_name}.root_evidence_ids",
        require_nonempty=True,
    )
    _strict_origin_tuple(value.origin_sources, f"{field_name}.origin_sources")
    try:
        restored = EvidenceLineageProfile(
            evidence_id=EvidenceId(value.evidence_id.value),
            direct_parent_evidence_ids=tuple(
                EvidenceId(item.value) for item in value.direct_parent_evidence_ids
            ),
            root_evidence_ids=tuple(EvidenceId(item.value) for item in value.root_evidence_ids),
            origin_sources=tuple(
                ProvenanceSource(ProvenanceSourceKind(item.kind.value), item.ref)
                for item in value.origin_sources
            ),
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InvalidClaimEvidenceLineageDependence):
            raise
        raise InvalidClaimEvidenceLineageDependence(
            f"{field_name} failed strict reconstruction: {exc}"
        ) from exc
    if restored != value:
        _fail(f"{field_name} must equal strict semantic reconstruction")
    return value


def _canonical_profiles(
    value: object,
    *,
    require_canonical: bool,
) -> tuple[EvidenceLineageProfile, ...]:
    if type(value) is not tuple:
        _fail("lineage_profiles must use exact tuple")
    items = value
    for index, item in enumerate(items):
        _strict_profile(item, f"lineage_profiles[{index}]")
    ids = tuple(item.evidence_id for item in items)
    if len(set(ids)) != len(ids):
        _fail("lineage_profiles must contain exactly one profile per evidence id")
    canonical = tuple(sorted(items, key=lambda item: item.evidence_id))
    if require_canonical and canonical != items:
        _fail("lineage_profiles must use canonical evidence-id ordering")
    return canonical


@dataclass(frozen=True, slots=True)
class ClaimEvidenceLineageDependenceReceipt:
    """Deterministic complete PR12.10 lineage artifact for one PR12.9 coverage basis."""

    snapshot_sha256: str
    claim_id: CapabilityClaimId
    subject_ref: CapabilitySubjectRef
    concept_ref: CapabilityConceptRef
    as_of: datetime
    disposition_coverage_sha256: str
    lineage_profiles: tuple[EvidenceLineageProfile, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "snapshot_sha256",
            _validate_sha256(self.snapshot_sha256, "snapshot_sha256"),
        )
        _strict_claim_id(self.claim_id)
        _strict_subject_ref(self.subject_ref)
        _strict_concept_ref(self.concept_ref)
        object.__setattr__(self, "as_of", _canonical_boundary(self.as_of, "lineage as_of"))
        object.__setattr__(
            self,
            "disposition_coverage_sha256",
            _validate_sha256(
                self.disposition_coverage_sha256,
                "disposition_coverage_sha256",
            ),
        )
        object.__setattr__(
            self,
            "lineage_profiles",
            _canonical_profiles(self.lineage_profiles, require_canonical=False),
        )

    def to_dict(self) -> dict:
        return claim_evidence_lineage_dependence_receipt_to_dict(self)

    @classmethod
    def from_dict(cls, payload: object) -> "ClaimEvidenceLineageDependenceReceipt":
        return claim_evidence_lineage_dependence_receipt_from_dict(payload)

    def to_json(self) -> str:
        return claim_evidence_lineage_dependence_receipt_to_json(self)

    @classmethod
    def from_json(cls, payload: object) -> "ClaimEvidenceLineageDependenceReceipt":
        return claim_evidence_lineage_dependence_receipt_from_json(payload)


def _strict_receipt(value: object) -> ClaimEvidenceLineageDependenceReceipt:
    if type(value) is not ClaimEvidenceLineageDependenceReceipt:
        _fail("lineage must use exact ClaimEvidenceLineageDependenceReceipt")
    _validate_sha256(value.snapshot_sha256, "snapshot_sha256")
    _strict_claim_id(value.claim_id)
    _strict_subject_ref(value.subject_ref)
    _strict_concept_ref(value.concept_ref)
    _strict_stored_utc_time(value.as_of, "lineage as_of")
    _validate_sha256(value.disposition_coverage_sha256, "disposition_coverage_sha256")
    _canonical_profiles(value.lineage_profiles, require_canonical=True)
    try:
        restored = ClaimEvidenceLineageDependenceReceipt(
            snapshot_sha256=value.snapshot_sha256,
            claim_id=CapabilityClaimId(value.claim_id.value),
            subject_ref=CapabilitySubjectRef(value.subject_ref.value),
            concept_ref=CapabilityConceptRef(
                CapabilityId(
                    value.concept_ref.capability_id.namespace,
                    value.concept_ref.capability_id.key,
                ),
                value.concept_ref.revision,
            ),
            as_of=value.as_of,
            disposition_coverage_sha256=value.disposition_coverage_sha256,
            lineage_profiles=tuple(
                EvidenceLineageProfile(
                    evidence_id=EvidenceId(profile.evidence_id.value),
                    direct_parent_evidence_ids=tuple(
                        EvidenceId(item.value) for item in profile.direct_parent_evidence_ids
                    ),
                    root_evidence_ids=tuple(
                        EvidenceId(item.value) for item in profile.root_evidence_ids
                    ),
                    origin_sources=tuple(
                        ProvenanceSource(ProvenanceSourceKind(origin.kind.value), origin.ref)
                        for origin in profile.origin_sources
                    ),
                )
                for profile in value.lineage_profiles
            ),
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InvalidClaimEvidenceLineageDependence):
            raise
        raise InvalidClaimEvidenceLineageDependence(
            f"lineage failed strict reconstruction: {exc}"
        ) from exc
    if restored != value:
        _fail("lineage must equal strict semantic reconstruction")
    return value


def _validate_upstream_coverage(
    *,
    records: EpistemicRecordSet,
    claim_id: CapabilityClaimId,
    as_of: datetime,
    coverage: ClaimEvidenceDispositionCoverageReceipt,
) -> ClaimEvidenceDispositionCoverageReceipt:
    try:
        return validate_complete_claim_evidence_disposition_coverage_v1(
            records=records,
            claim_id=claim_id,
            as_of=as_of,
            coverage=coverage,
        )
    except ClaimEvidenceDispositionCoverageError as exc:
        raise InvalidClaimEvidenceLineageDependence(
            f"PR12.9 disposition coverage validation failed: {exc}"
        ) from exc


def _coverage_sha256(coverage: ClaimEvidenceDispositionCoverageReceipt) -> str:
    if type(coverage) is not ClaimEvidenceDispositionCoverageReceipt:
        _fail("coverage must use exact ClaimEvidenceDispositionCoverageReceipt")
    return sha256(coverage.to_json().encode("utf-8")).hexdigest()


def _candidate_ids(
    coverage: ClaimEvidenceDispositionCoverageReceipt,
) -> tuple[EvidenceId, ...]:
    return tuple(item.evidence_id for item in coverage.dispositions)


def _derive_profiles(
    *,
    records: EpistemicRecordSet,
    candidate_ids: tuple[EvidenceId, ...],
) -> tuple[EvidenceLineageProfile, ...]:
    by_value = {item.evidence_id.value: item for item in records.evidence_records}
    candidate_by_value = {item.value: item for item in candidate_ids}
    parents_by_value: dict[str, tuple[str, ...]] = {}
    direct_origins_by_value: dict[str, tuple[ProvenanceSource, ...]] = {}

    for evidence_id in candidate_ids:
        record = by_value.get(evidence_id.value)
        if record is None:
            _fail(f"validated candidate evidence is absent from records: {evidence_id}")
        parent_values = tuple(
            sorted(
                source.ref
                for source in record.provenance.sources
                if source.kind is ProvenanceSourceKind.EVIDENCE_RECORD
            )
        )
        for parent_value in parent_values:
            if parent_value not in candidate_by_value:
                _fail(
                    "validated candidate has an internal evidence parent outside "
                    "the exact PR12.8 candidate universe"
                )
        parents_by_value[evidence_id.value] = parent_values
        direct_origins_by_value[evidence_id.value] = tuple(
            sorted(
                source
                for source in record.provenance.sources
                if source.kind in _ORIGIN_KINDS
            )
        )

    memo: dict[str, EvidenceLineageProfile] = {}
    for target in tuple(sorted(candidate_by_value)):
        if target in memo:
            continue
        stack: list[tuple[str, bool]] = [(target, False)]
        while stack:
            current, exiting = stack.pop()
            if current in memo:
                continue
            if not exiting:
                stack.append((current, True))
                for parent in reversed(parents_by_value[current]):
                    if parent not in memo:
                        stack.append((parent, False))
                continue

            parent_values = parents_by_value[current]
            if parent_values:
                roots = {
                    root
                    for parent in parent_values
                    for root in memo[parent].root_evidence_ids
                }
            else:
                roots = {candidate_by_value[current]}

            origins = set(direct_origins_by_value[current])
            for parent in parent_values:
                origins.update(memo[parent].origin_sources)

            memo[current] = EvidenceLineageProfile(
                evidence_id=candidate_by_value[current],
                direct_parent_evidence_ids=tuple(
                    candidate_by_value[parent] for parent in parent_values
                ),
                root_evidence_ids=tuple(sorted(roots)),
                origin_sources=tuple(sorted(origins)),
            )

    return tuple(memo[key] for key in sorted(memo))


def build_claim_evidence_lineage_dependence_v1(
    *,
    records: EpistemicRecordSet,
    claim_id: CapabilityClaimId,
    as_of: datetime,
    coverage: ClaimEvidenceDispositionCoverageReceipt,
) -> ClaimEvidenceLineageDependenceReceipt:
    """Build complete deterministic lineage profiles after exact PR12.9 replay."""

    boundary = _canonical_boundary(as_of, "lineage as_of")
    checked_coverage = _validate_upstream_coverage(
        records=records,
        claim_id=claim_id,
        as_of=boundary,
        coverage=coverage,
    )
    profiles = _derive_profiles(
        records=records,
        candidate_ids=_candidate_ids(checked_coverage),
    )
    return ClaimEvidenceLineageDependenceReceipt(
        snapshot_sha256=checked_coverage.snapshot_sha256,
        claim_id=checked_coverage.claim_id,
        subject_ref=checked_coverage.subject_ref,
        concept_ref=checked_coverage.concept_ref,
        as_of=checked_coverage.as_of,
        disposition_coverage_sha256=_coverage_sha256(checked_coverage),
        lineage_profiles=profiles,
    )


def validate_claim_evidence_lineage_dependence_v1(
    *,
    records: EpistemicRecordSet,
    claim_id: CapabilityClaimId,
    as_of: datetime,
    coverage: ClaimEvidenceDispositionCoverageReceipt,
    lineage: ClaimEvidenceLineageDependenceReceipt,
) -> ClaimEvidenceLineageDependenceReceipt:
    """Require exact equality with an independently rebuilt PR12.10 lineage artifact."""

    supplied = _strict_receipt(lineage)
    expected = build_claim_evidence_lineage_dependence_v1(
        records=records,
        claim_id=claim_id,
        as_of=as_of,
        coverage=coverage,
    )
    if supplied != expected:
        _fail(
            "lineage content does not match exact records-derived provenance "
            "and validated PR12.9 coverage"
        )
    return supplied


def resolve_claim_evidence_pair_lineage_relation_v1(
    *,
    records: EpistemicRecordSet,
    claim_id: CapabilityClaimId,
    as_of: datetime,
    coverage: ClaimEvidenceDispositionCoverageReceipt,
    left_evidence_id: EvidenceId,
    right_evidence_id: EvidenceId,
    lineage: ClaimEvidenceLineageDependenceReceipt | None = None,
) -> EvidenceLineageRelation:
    """Resolve only proven shared lineage; absence of proof remains unresolved."""

    left = _strict_evidence_id(left_evidence_id, "left_evidence_id")
    right = _strict_evidence_id(right_evidence_id, "right_evidence_id")
    if left == right:
        _fail("pair lineage relation requires two distinct evidence ids")

    expected = build_claim_evidence_lineage_dependence_v1(
        records=records,
        claim_id=claim_id,
        as_of=as_of,
        coverage=coverage,
    )
    if lineage is not None:
        supplied = _strict_receipt(lineage)
        if supplied != expected:
            _fail("supplied lineage does not equal exact rebuilt lineage content")

    profiles = {profile.evidence_id: profile for profile in expected.lineage_profiles}
    left_profile = profiles.get(left)
    right_profile = profiles.get(right)
    if left_profile is None or right_profile is None:
        _fail("pair lineage relation requires exact PR12.8 candidate evidence ids")

    if set(left_profile.root_evidence_ids) & set(right_profile.root_evidence_ids):
        return EvidenceLineageRelation.PROVEN_SHARED_LINEAGE
    if set(left_profile.origin_sources) & set(right_profile.origin_sources):
        return EvidenceLineageRelation.PROVEN_SHARED_LINEAGE
    return EvidenceLineageRelation.UNRESOLVED


def evidence_lineage_profile_to_dict(profile: EvidenceLineageProfile) -> dict:
    checked = _strict_profile(profile)
    return {
        "evidence_id": checked.evidence_id.value,
        "direct_parent_evidence_ids": [
            item.value for item in checked.direct_parent_evidence_ids
        ],
        "root_evidence_ids": [item.value for item in checked.root_evidence_ids],
        "origin_sources": [
            {"kind": item.kind.value, "ref": item.ref}
            for item in checked.origin_sources
        ],
    }


def _require_exact_object(
    payload: object,
    *,
    expected_keys: set[str],
    field_name: str,
) -> dict:
    if type(payload) is not dict:
        _fail(f"{field_name} must use exact object/dict")
    if any(type(key) is not str for key in payload):
        _fail(f"{field_name} keys must use exact strings")
    actual_keys = set(payload)
    unknown = actual_keys - expected_keys
    if unknown:
        _fail(f"{field_name} contains unknown field: {sorted(unknown)[0]}")
    missing = expected_keys - actual_keys
    if missing:
        _fail(f"{field_name} is missing field: {sorted(missing)[0]}")
    return payload


def _evidence_id_list_from_dict(
    value: object,
    field_name: str,
    *,
    require_nonempty: bool = False,
) -> tuple[EvidenceId, ...]:
    if type(value) is not list:
        _fail(f"{field_name} must use exact array/list")
    if any(type(item) is not str for item in value):
        _fail(f"{field_name} values must use exact strings")
    try:
        items = tuple(EvidenceId(item) for item in value)
    except (TypeError, ValueError) as exc:
        raise InvalidClaimEvidenceLineageDependence(
            f"{field_name} contains invalid evidence id: {exc}"
        ) from exc
    _strict_evidence_id_tuple(
        items,
        field_name,
        require_nonempty=require_nonempty,
    )
    return items


def _origin_source_from_dict(payload: object, field_name: str) -> ProvenanceSource:
    data = _require_exact_object(
        payload,
        expected_keys={"kind", "ref"},
        field_name=field_name,
    )
    if type(data["kind"]) is not str or type(data["ref"]) is not str:
        _fail(f"{field_name} kind/ref must use exact strings")
    try:
        kind = ProvenanceSourceKind(data["kind"])
    except ValueError as exc:
        raise InvalidClaimEvidenceLineageDependence(
            f"{field_name}.kind is invalid"
        ) from exc
    if kind not in _ORIGIN_KINDS:
        _fail(f"{field_name}.kind must be artifact or external_record")
    try:
        return ProvenanceSource(kind, data["ref"])
    except (TypeError, ValueError) as exc:
        raise InvalidClaimEvidenceLineageDependence(
            f"{field_name} is invalid: {exc}"
        ) from exc


def evidence_lineage_profile_from_dict(payload: object) -> EvidenceLineageProfile:
    data = _require_exact_object(
        payload,
        expected_keys={
            "evidence_id",
            "direct_parent_evidence_ids",
            "root_evidence_ids",
            "origin_sources",
        },
        field_name="lineage profile",
    )
    if type(data["evidence_id"]) is not str:
        _fail("lineage profile evidence_id must use exact string")
    parents = _evidence_id_list_from_dict(
        data["direct_parent_evidence_ids"],
        "direct_parent_evidence_ids",
    )
    roots = _evidence_id_list_from_dict(
        data["root_evidence_ids"],
        "root_evidence_ids",
        require_nonempty=True,
    )
    raw_origins = data["origin_sources"]
    if type(raw_origins) is not list:
        _fail("origin_sources must use exact array/list")
    origins = tuple(
        _origin_source_from_dict(item, f"origin_sources[{index}]")
        for index, item in enumerate(raw_origins)
    )
    _strict_origin_tuple(origins, "origin_sources")
    try:
        profile = EvidenceLineageProfile(
            evidence_id=EvidenceId(data["evidence_id"]),
            direct_parent_evidence_ids=parents,
            root_evidence_ids=roots,
            origin_sources=origins,
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InvalidClaimEvidenceLineageDependence):
            raise
        raise InvalidClaimEvidenceLineageDependence(
            f"lineage profile is invalid: {exc}"
        ) from exc
    if evidence_lineage_profile_to_dict(profile) != data:
        _fail("lineage profile payload must use canonical ordering/content")
    return profile


def claim_evidence_lineage_dependence_receipt_to_dict(
    lineage: ClaimEvidenceLineageDependenceReceipt,
) -> dict:
    checked = _strict_receipt(lineage)
    return {
        "schema_version": _SCHEMA_VERSION,
        "snapshot_sha256": checked.snapshot_sha256,
        "claim_id": checked.claim_id.value,
        "subject_ref": checked.subject_ref.value,
        "concept_ref": str(checked.concept_ref),
        "as_of": format_time(checked.as_of),
        "disposition_coverage_sha256": checked.disposition_coverage_sha256,
        "lineage_profiles": [
            evidence_lineage_profile_to_dict(profile)
            for profile in checked.lineage_profiles
        ],
    }


def claim_evidence_lineage_dependence_receipt_from_dict(
    payload: object,
) -> ClaimEvidenceLineageDependenceReceipt:
    data = _require_exact_object(
        payload,
        expected_keys={
            "schema_version",
            "snapshot_sha256",
            "claim_id",
            "subject_ref",
            "concept_ref",
            "as_of",
            "disposition_coverage_sha256",
            "lineage_profiles",
        },
        field_name="lineage payload",
    )
    if type(data["schema_version"]) is not int or data["schema_version"] != _SCHEMA_VERSION:
        _fail("lineage schema_version must be exact integer 1")
    for field_name in (
        "snapshot_sha256",
        "claim_id",
        "subject_ref",
        "concept_ref",
        "as_of",
        "disposition_coverage_sha256",
    ):
        if type(data[field_name]) is not str:
            _fail(f"lineage {field_name} must use exact string")
    profiles_payload = data["lineage_profiles"]
    if type(profiles_payload) is not list:
        _fail("lineage_profiles must use exact array/list")
    profiles = tuple(
        evidence_lineage_profile_from_dict(item) for item in profiles_payload
    )
    ids = tuple(profile.evidence_id for profile in profiles)
    if len(set(ids)) != len(ids):
        _fail("lineage_profiles must not contain duplicate evidence ids")
    if tuple(sorted(ids)) != ids:
        _fail("lineage_profiles payload must use canonical evidence-id ordering")
    try:
        lineage = ClaimEvidenceLineageDependenceReceipt(
            snapshot_sha256=data["snapshot_sha256"],
            claim_id=CapabilityClaimId(data["claim_id"]),
            subject_ref=CapabilitySubjectRef(data["subject_ref"]),
            concept_ref=CapabilityConceptRef.parse(data["concept_ref"]),
            as_of=parse_time(data["as_of"], "lineage as_of"),
            disposition_coverage_sha256=data["disposition_coverage_sha256"],
            lineage_profiles=profiles,
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InvalidClaimEvidenceLineageDependence):
            raise
        raise InvalidClaimEvidenceLineageDependence(
            f"lineage payload is invalid: {exc}"
        ) from exc
    if claim_evidence_lineage_dependence_receipt_to_dict(lineage) != data:
        _fail("lineage payload must use canonical ordering/content")
    return lineage


def claim_evidence_lineage_dependence_receipt_to_json(
    lineage: ClaimEvidenceLineageDependenceReceipt,
) -> str:
    return json.dumps(
        claim_evidence_lineage_dependence_receipt_to_dict(lineage),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _reject_duplicate_json_pairs(pairs):
    output = {}
    for key, value in pairs:
        if key in output:
            _fail(f"lineage JSON contains duplicate key: {key}")
        output[key] = value
    return output


def _reject_json_constant(value: str):
    _fail(f"lineage JSON contains non-standard constant: {value}")


def claim_evidence_lineage_dependence_receipt_from_json(
    payload: object,
) -> ClaimEvidenceLineageDependenceReceipt:
    if type(payload) is not str:
        _fail("lineage JSON payload must use exact string")
    try:
        decoded = json.loads(
            payload,
            object_pairs_hook=_reject_duplicate_json_pairs,
            parse_constant=_reject_json_constant,
        )
    except InvalidClaimEvidenceLineageDependence:
        raise
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise InvalidClaimEvidenceLineageDependence(
            f"lineage JSON is invalid: {exc}"
        ) from exc
    lineage = claim_evidence_lineage_dependence_receipt_from_dict(decoded)
    if claim_evidence_lineage_dependence_receipt_to_json(lineage) != payload:
        _fail("lineage JSON must use exact canonical serialization")
    return lineage
