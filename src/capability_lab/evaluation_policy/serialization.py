"""Strict deterministic serialization for PR12.6 policy specifications."""

from __future__ import annotations

import json

from capability_lab.epistemics import ClaimScope, EvaluationPolicyRef
from capability_lab.semantics import CapabilityConceptRef

from .specification import (
    DOMAIN_EVALUATION_SUFFICIENCY_SEMANTICS_V1,
    DomainEvaluationPolicyRequirement,
    DomainEvaluationPolicySpecification,
    InvalidDomainEvaluationPolicySpecification,
    _strict_specification,
)


_SCHEMA_VERSION = 1


def _fail(message: str) -> None:
    raise InvalidDomainEvaluationPolicySpecification(message)


def _obj(payload: object, fields: set[str], label: str) -> dict:
    if type(payload) is not dict:
        _fail(f"{label} must be a JSON object")
    if any(type(key) is not str for key in payload):
        _fail(f"{label} keys must use exact str JSON-object storage")
    actual = set(payload)
    if actual != fields:
        _fail(
            f"{label} fields must match schema exactly; "
            f"missing={tuple(sorted(fields-actual))!r}, "
            f"unknown={tuple(sorted(actual-fields))!r}"
        )
    return payload


def _exact_str(value: object, label: str) -> str:
    if type(value) is not str:
        _fail(f"{label} must use exact str storage")
    return value


def _no_duplicate_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            _fail(f"duplicate JSON object keys are forbidden: {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str):
    _fail(f"non-finite JSON constant is forbidden: {value}")


def _loads(payload: object):
    if type(payload) is not str:
        _fail("JSON payload must be a string")
    try:
        return json.loads(
            payload,
            object_pairs_hook=_no_duplicate_pairs,
            parse_constant=_reject_constant,
        )
    except InvalidDomainEvaluationPolicySpecification:
        raise
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise InvalidDomainEvaluationPolicySpecification(
            f"invalid JSON payload: {exc}"
        ) from exc


def _dumps(payload: object) -> str:
    try:
        return json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise InvalidDomainEvaluationPolicySpecification(
            f"payload is not canonically JSON serializable: {exc}"
        ) from exc


def domain_evaluation_policy_specification_to_dict(
    value: DomainEvaluationPolicySpecification,
) -> dict:
    value = _strict_specification(value)
    return {
        "schema_version": _SCHEMA_VERSION,
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


def domain_evaluation_policy_specification_from_dict(
    payload: object,
) -> DomainEvaluationPolicySpecification:
    fields = {
        "schema_version",
        "policy_ref",
        "concept_ref",
        "claim_scope",
        "requirements",
        "sufficiency_semantics",
    }
    obj = _obj(payload, fields, "domain evaluation policy specification")
    if type(obj["schema_version"]) is not int or obj["schema_version"] != _SCHEMA_VERSION:
        _fail("policy specification schema_version must be exact integer 1")

    policy_ref_text = _exact_str(obj["policy_ref"], "policy_ref")
    concept_ref_text = _exact_str(obj["concept_ref"], "concept_ref")
    sufficiency_semantics = _exact_str(
        obj["sufficiency_semantics"],
        "sufficiency_semantics",
    )
    if sufficiency_semantics != DOMAIN_EVALUATION_SUFFICIENCY_SEMANTICS_V1:
        _fail("policy specification must use frozen v1 sufficiency semantics")

    claim_scope_obj = _obj(
        obj["claim_scope"],
        {"description", "tags"},
        "claim_scope",
    )
    claim_scope_description = _exact_str(
        claim_scope_obj["description"],
        "claim_scope.description",
    )
    if type(claim_scope_obj["tags"]) is not list:
        _fail("claim_scope.tags must be a JSON array")
    if any(type(tag) is not str for tag in claim_scope_obj["tags"]):
        _fail("claim_scope.tags values must use exact str storage")

    if type(obj["requirements"]) is not list:
        _fail("requirements must be a JSON array")
    requirements = []
    for index, raw in enumerate(obj["requirements"]):
        item = _obj(
            raw,
            {"requirement_key", "description", "required_for_sufficiency"},
            f"requirements[{index}]",
        )
        requirement_key = _exact_str(
            item["requirement_key"],
            f"requirements[{index}].requirement_key",
        )
        description = _exact_str(
            item["description"],
            f"requirements[{index}].description",
        )
        if type(item["required_for_sufficiency"]) is not bool:
            _fail(
                f"requirements[{index}].required_for_sufficiency must use exact bool storage"
            )
        requirements.append(
            DomainEvaluationPolicyRequirement(
                requirement_key=requirement_key,
                description=description,
                required_for_sufficiency=item["required_for_sufficiency"],
            )
        )

    try:
        result = DomainEvaluationPolicySpecification(
            policy_ref=EvaluationPolicyRef.parse(policy_ref_text),
            concept_ref=CapabilityConceptRef.parse(concept_ref_text),
            claim_scope=ClaimScope(
                description=claim_scope_description,
                tags=tuple(claim_scope_obj["tags"]),
            ),
            requirements=tuple(requirements),
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, InvalidDomainEvaluationPolicySpecification):
            raise
        raise InvalidDomainEvaluationPolicySpecification(
            f"invalid domain evaluation policy specification: {exc}"
        ) from exc

    if domain_evaluation_policy_specification_to_dict(result) != obj:
        _fail("policy specification must equal canonical reconstruction")
    return result


def domain_evaluation_policy_specification_to_json(
    value: DomainEvaluationPolicySpecification,
) -> str:
    return _dumps(domain_evaluation_policy_specification_to_dict(value))


def domain_evaluation_policy_specification_from_json(
    payload: object,
) -> DomainEvaluationPolicySpecification:
    return domain_evaluation_policy_specification_from_dict(_loads(payload))
