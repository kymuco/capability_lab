"""PR12.6 generic declarative domain evaluation-policy specification v1."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
import unicodedata

from capability_lab.epistemics import ClaimScope, EvaluationPolicyRef
from capability_lab.semantics import CapabilityConceptRef, CapabilityId


class InvalidDomainEvaluationPolicySpecification(ValueError):
    """The supplied generic domain evaluation-policy specification is invalid."""


_REQUIREMENT_KEY_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_POLICY_SPEC_HASH_DOMAIN = b"capability_lab/domain_evaluation_policy_specification@1\x00"
DOMAIN_EVALUATION_SUFFICIENCY_SEMANTICS_V1 = "all_required_requirements_explicitly_covered"


def _clean_text(value: object, field_name: str) -> str:
    if type(value) is not str:
        raise InvalidDomainEvaluationPolicySpecification(f"{field_name} must be a string")
    cleaned = unicodedata.normalize("NFC", value).strip()
    if not cleaned:
        raise InvalidDomainEvaluationPolicySpecification(f"{field_name} must be non-empty")
    return cleaned


def _strict_policy_ref(value: EvaluationPolicyRef) -> EvaluationPolicyRef:
    if type(value) is not EvaluationPolicyRef:
        raise InvalidDomainEvaluationPolicySpecification(
            "policy_ref must use exact EvaluationPolicyRef"
        )
    if type(value.namespace) is not str or type(value.key) is not str:
        raise InvalidDomainEvaluationPolicySpecification(
            "policy_ref namespace/key must use exact str storage"
        )
    if type(value.revision) is not int:
        raise InvalidDomainEvaluationPolicySpecification(
            "policy_ref revision must use exact int storage"
        )
    try:
        restored = EvaluationPolicyRef(value.namespace, value.key, value.revision)
    except (TypeError, ValueError) as exc:
        raise InvalidDomainEvaluationPolicySpecification(
            f"invalid policy_ref: {exc}"
        ) from exc
    if (
        restored.namespace != value.namespace
        or restored.key != value.key
        or restored.revision != value.revision
    ):
        raise InvalidDomainEvaluationPolicySpecification(
            "policy_ref must equal strict scalar reconstruction"
        )
    return restored


def _strict_concept_ref(value: CapabilityConceptRef) -> CapabilityConceptRef:
    if type(value) is not CapabilityConceptRef:
        raise InvalidDomainEvaluationPolicySpecification(
            "concept_ref must use exact CapabilityConceptRef"
        )
    if type(value.capability_id) is not CapabilityId:
        raise InvalidDomainEvaluationPolicySpecification(
            "concept_ref capability_id must use exact CapabilityId"
        )
    if (
        type(value.capability_id.namespace) is not str
        or type(value.capability_id.key) is not str
    ):
        raise InvalidDomainEvaluationPolicySpecification(
            "concept_ref capability_id fields must use exact str storage"
        )
    if type(value.revision) is not int:
        raise InvalidDomainEvaluationPolicySpecification(
            "concept_ref revision must use exact int storage"
        )
    try:
        restored_id = CapabilityId(
            namespace=value.capability_id.namespace,
            key=value.capability_id.key,
        )
        restored = CapabilityConceptRef(restored_id, value.revision)
    except (TypeError, ValueError) as exc:
        raise InvalidDomainEvaluationPolicySpecification(
            f"invalid concept_ref: {exc}"
        ) from exc
    if (
        restored.capability_id.namespace != value.capability_id.namespace
        or restored.capability_id.key != value.capability_id.key
        or restored.revision != value.revision
    ):
        raise InvalidDomainEvaluationPolicySpecification(
            "concept_ref must equal strict scalar reconstruction"
        )
    return restored


def _strict_claim_scope(value: ClaimScope) -> ClaimScope:
    if type(value) is not ClaimScope:
        raise InvalidDomainEvaluationPolicySpecification(
            "claim_scope must use exact ClaimScope"
        )
    if type(value.description) is not str:
        raise InvalidDomainEvaluationPolicySpecification(
            "claim_scope description must use exact str storage"
        )
    if type(value.tags) is not tuple or any(type(tag) is not str for tag in value.tags):
        raise InvalidDomainEvaluationPolicySpecification(
            "claim_scope tags must use canonical tuple[str, ...] storage"
        )
    try:
        restored = ClaimScope(description=value.description, tags=value.tags)
    except (TypeError, ValueError) as exc:
        raise InvalidDomainEvaluationPolicySpecification(
            f"invalid claim_scope: {exc}"
        ) from exc
    if restored.description != value.description or restored.tags != value.tags:
        raise InvalidDomainEvaluationPolicySpecification(
            "claim_scope must equal strict scalar reconstruction"
        )
    return restored


@dataclass(frozen=True, order=True, slots=True)
class DomainEvaluationPolicyRequirement:
    """One declarative semantic aspect that later evidence may explicitly cover."""

    requirement_key: str
    description: str
    required_for_sufficiency: bool

    def __post_init__(self) -> None:
        if type(self.requirement_key) is not str or _REQUIREMENT_KEY_RE.fullmatch(self.requirement_key) is None:
            raise InvalidDomainEvaluationPolicySpecification(
                "requirement_key must use lowercase machine-key syntax"
            )
        object.__setattr__(
            self,
            "description",
            _clean_text(self.description, "requirement description"),
        )
        if type(self.required_for_sufficiency) is not bool:
            raise InvalidDomainEvaluationPolicySpecification(
                "required_for_sufficiency must be an exact bool"
            )


@dataclass(frozen=True, slots=True)
class DomainEvaluationPolicySpecification:
    """Immutable declarative policy shape with no activation or evaluation authority."""

    policy_ref: EvaluationPolicyRef
    concept_ref: CapabilityConceptRef
    claim_scope: ClaimScope
    requirements: tuple[DomainEvaluationPolicyRequirement, ...]

    def __post_init__(self) -> None:
        if type(self.policy_ref) is not EvaluationPolicyRef:
            raise InvalidDomainEvaluationPolicySpecification(
                "policy_ref must use exact EvaluationPolicyRef"
            )
        if type(self.concept_ref) is not CapabilityConceptRef:
            raise InvalidDomainEvaluationPolicySpecification(
                "concept_ref must use exact CapabilityConceptRef"
            )
        if type(self.claim_scope) is not ClaimScope:
            raise InvalidDomainEvaluationPolicySpecification(
                "claim_scope must use exact ClaimScope"
            )
        if isinstance(self.requirements, (str, bytes)):
            raise InvalidDomainEvaluationPolicySpecification(
                "requirements must be an iterable of DomainEvaluationPolicyRequirement values"
            )
        try:
            requirements = tuple(self.requirements)
        except TypeError as exc:
            raise InvalidDomainEvaluationPolicySpecification("requirements must be iterable") from exc
        if not requirements:
            raise InvalidDomainEvaluationPolicySpecification(
                "domain evaluation policy specification requires at least one requirement"
            )
        if any(type(item) is not DomainEvaluationPolicyRequirement for item in requirements):
            raise InvalidDomainEvaluationPolicySpecification(
                "requirements must contain exact DomainEvaluationPolicyRequirement values"
            )
        keys = tuple(item.requirement_key for item in requirements)
        if len(set(keys)) != len(keys):
            raise InvalidDomainEvaluationPolicySpecification(
                "duplicate domain evaluation requirement_key values are forbidden"
            )
        if not any(item.required_for_sufficiency for item in requirements):
            raise InvalidDomainEvaluationPolicySpecification(
                "at least one requirement must be required_for_sufficiency"
            )
        object.__setattr__(self, "requirements", tuple(sorted(requirements)))

    def to_dict(self) -> dict:
        from .serialization import domain_evaluation_policy_specification_to_dict

        return domain_evaluation_policy_specification_to_dict(self)

    @classmethod
    def from_dict(cls, payload: object) -> "DomainEvaluationPolicySpecification":
        from .serialization import domain_evaluation_policy_specification_from_dict

        return domain_evaluation_policy_specification_from_dict(payload)

    def to_json(self) -> str:
        from .serialization import domain_evaluation_policy_specification_to_json

        return domain_evaluation_policy_specification_to_json(self)

    @classmethod
    def from_json(cls, payload: object) -> "DomainEvaluationPolicySpecification":
        from .serialization import domain_evaluation_policy_specification_from_json

        return domain_evaluation_policy_specification_from_json(payload)


def _strict_requirement(
    value: DomainEvaluationPolicyRequirement,
) -> DomainEvaluationPolicyRequirement:
    if type(value) is not DomainEvaluationPolicyRequirement:
        raise InvalidDomainEvaluationPolicySpecification(
            "requirement must use exact DomainEvaluationPolicyRequirement"
        )
    if type(value.requirement_key) is not str or type(value.description) is not str:
        raise InvalidDomainEvaluationPolicySpecification(
            "requirement textual fields must use exact str storage"
        )
    if type(value.required_for_sufficiency) is not bool:
        raise InvalidDomainEvaluationPolicySpecification(
            "requirement required_for_sufficiency must use exact bool storage"
        )
    restored = DomainEvaluationPolicyRequirement(
        requirement_key=value.requirement_key,
        description=value.description,
        required_for_sufficiency=value.required_for_sufficiency,
    )
    if (
        restored.requirement_key != value.requirement_key
        or restored.description != value.description
        or restored.required_for_sufficiency is not value.required_for_sufficiency
    ):
        raise InvalidDomainEvaluationPolicySpecification(
            "requirement must equal strict scalar reconstruction"
        )
    return restored


def _strict_specification(
    value: DomainEvaluationPolicySpecification,
) -> DomainEvaluationPolicySpecification:
    if type(value) is not DomainEvaluationPolicySpecification:
        raise InvalidDomainEvaluationPolicySpecification(
            "specification must use exact DomainEvaluationPolicySpecification"
        )
    policy_ref = _strict_policy_ref(value.policy_ref)
    concept_ref = _strict_concept_ref(value.concept_ref)
    claim_scope = _strict_claim_scope(value.claim_scope)
    if type(value.requirements) is not tuple:
        raise InvalidDomainEvaluationPolicySpecification(
            "specification requirements must use canonical tuple storage"
        )
    requirements = tuple(_strict_requirement(item) for item in value.requirements)
    restored = DomainEvaluationPolicySpecification(
        policy_ref=policy_ref,
        concept_ref=concept_ref,
        claim_scope=claim_scope,
        requirements=requirements,
    )
    if restored.requirements != requirements:
        raise InvalidDomainEvaluationPolicySpecification(
            "specification requirements must already use canonical ordering"
        )
    return restored


def _canonical_payload(value: DomainEvaluationPolicySpecification) -> dict:
    value = _strict_specification(value)
    return {
        "policy_ref": str(value.policy_ref),
        "concept_ref": str(value.concept_ref),
        "claim_scope": {
            "description": value.claim_scope.description,
            "tags": list(value.claim_scope.tags),
        },
        "requirements": [
            {
                "requirement_key": item.requirement_key,
                "description": item.description,
                "required_for_sufficiency": item.required_for_sufficiency,
            }
            for item in value.requirements
        ],
        "sufficiency_semantics": DOMAIN_EVALUATION_SUFFICIENCY_SEMANTICS_V1,
    }


def domain_evaluation_policy_specification_sha256_v1(
    value: DomainEvaluationPolicySpecification,
) -> str:
    """Hash exact declarative policy content; this digest grants no authority."""

    payload = json.dumps(
        _canonical_payload(value),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    digest = hashlib.sha256()
    digest.update(_POLICY_SPEC_HASH_DOMAIN)
    digest.update(payload)
    return digest.hexdigest()


def domain_evaluation_policy_specification_applies_to_v1(
    value: DomainEvaluationPolicySpecification,
    *,
    concept_ref: CapabilityConceptRef,
    claim_scope: ClaimScope,
) -> bool:
    """Return exact structural applicability without activating or evaluating policy."""

    value = _strict_specification(value)
    concept_ref = _strict_concept_ref(concept_ref)
    claim_scope = _strict_claim_scope(claim_scope)
    return value.concept_ref == concept_ref and value.claim_scope == claim_scope
