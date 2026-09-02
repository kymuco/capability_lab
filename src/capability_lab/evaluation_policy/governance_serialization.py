"""Strict deterministic serialization for PR12.7 policy-governance artifacts.

The serializer is intentionally stable across governance reload/reimport. Each
public operation captures the currently published immutable governance
generation once and performs the complete reconstruction against that one
generation. This avoids cached old-generation bindings and prevents a live
module reload from changing helpers midway through one serialization operation.
"""

from __future__ import annotations

import importlib
import json

from capability_lab.epistemics import EvaluationPolicyRef

from .specification import DomainEvaluationPolicySpecification


_SCHEMA_VERSION = 1
_GOVERNANCE_MODULE = "capability_lab.evaluation_policy.governance"
_PUBLISHED_GENERATION_ATTR = "_pr12_7_published_governance_generation"


def _governance():
    live = importlib.import_module(_GOVERNANCE_MODULE)
    return getattr(live, _PUBLISHED_GENERATION_ATTR, live)


def _fail(governance, message: str) -> None:
    raise governance.InvalidDomainEvaluationPolicyGovernance(message)


def _obj(governance, payload: object, fields: set[str], label: str) -> dict:
    if type(payload) is not dict:
        _fail(governance, f"{label} must be a JSON object")
    if any(type(key) is not str for key in payload):
        _fail(governance, f"{label} keys must use exact str JSON-object storage")
    actual = set(payload)
    if actual != fields:
        _fail(
            governance,
            f"{label} fields must match schema exactly; "
            f"missing={tuple(sorted(fields - actual))!r}, "
            f"unknown={tuple(sorted(actual - fields))!r}",
        )
    return payload


def _exact_str(governance, value: object, field_name: str) -> str:
    if type(value) is not str:
        _fail(governance, f"{field_name} must use exact str storage")
    return value


def _exact_list(governance, value: object, field_name: str) -> list:
    if type(value) is not list:
        _fail(governance, f"{field_name} must be a JSON array")
    return value


def _schema(governance, obj: dict, label: str) -> None:
    if type(obj["schema_version"]) is not int or obj["schema_version"] != _SCHEMA_VERSION:
        _fail(governance, f"{label} schema_version must be exact integer 1")


def _loads(governance, payload: object):
    if type(payload) is not str:
        _fail(governance, "JSON payload must be a string")

    def no_duplicate_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                _fail(
                    governance,
                    f"duplicate JSON object keys are forbidden: {key!r}",
                )
            result[key] = value
        return result

    def reject_constant(value: str):
        _fail(governance, f"non-finite JSON constant is forbidden: {value}")

    try:
        return json.loads(
            payload,
            object_pairs_hook=no_duplicate_pairs,
            parse_constant=reject_constant,
        )
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        if isinstance(exc, governance.InvalidDomainEvaluationPolicyGovernance):
            raise
        raise governance.InvalidDomainEvaluationPolicyGovernance(
            f"invalid JSON payload: {exc}"
        ) from exc


def _dumps(governance, payload: object) -> str:
    try:
        return json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, governance.InvalidDomainEvaluationPolicyGovernance):
            raise
        raise governance.InvalidDomainEvaluationPolicyGovernance(
            f"payload is not canonically JSON serializable: {exc}"
        ) from exc


def _review_to_dict(governance, value: object) -> dict:
    return governance._review_payload(governance._strict_review(value))


def _review_from_dict(governance, payload: object):
    obj = _obj(
        governance,
        payload,
        {
            "schema_version",
            "review_id",
            "policy_ref",
            "specification_sha256",
            "reviewer_ref",
            "verdict",
            "reviewed_at",
            "rationale",
        },
        "domain evaluation policy review",
    )
    _schema(governance, obj, "domain evaluation policy review")
    review_id = _exact_str(governance, obj["review_id"], "review_id")
    policy_ref = _exact_str(governance, obj["policy_ref"], "policy_ref")
    specification_sha256 = _exact_str(
        governance,
        obj["specification_sha256"],
        "specification_sha256",
    )
    verdict = _exact_str(governance, obj["verdict"], "verdict")
    reviewed_at = _exact_str(governance, obj["reviewed_at"], "reviewed_at")
    rationale = _exact_str(governance, obj["rationale"], "rationale")
    reviewer_obj = _obj(
        governance,
        obj["reviewer_ref"],
        {"kind", "ref"},
        "reviewer_ref",
    )
    reviewer_kind = _exact_str(
        governance,
        reviewer_obj["kind"],
        "reviewer_ref.kind",
    )
    reviewer_ref = _exact_str(
        governance,
        reviewer_obj["ref"],
        "reviewer_ref.ref",
    )
    try:
        result = governance.DomainEvaluationPolicyReview(
            review_id=governance.DomainEvaluationPolicyReviewId(review_id),
            policy_ref=EvaluationPolicyRef.parse(policy_ref),
            specification_sha256=specification_sha256,
            reviewer_ref=governance.DomainEvaluationPolicyReviewerRef(
                governance.DomainEvaluationPolicyReviewerKind(reviewer_kind),
                reviewer_ref,
            ),
            verdict=governance.DomainEvaluationPolicyReviewVerdict(verdict),
            reviewed_at=governance._parse_time(reviewed_at, "reviewed_at"),
            rationale=rationale,
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, governance.InvalidDomainEvaluationPolicyGovernance):
            raise
        raise governance.InvalidDomainEvaluationPolicyGovernance(
            f"invalid domain evaluation policy review: {exc}"
        ) from exc
    if _review_to_dict(governance, result) != obj:
        _fail(
            governance,
            "domain evaluation policy review must equal canonical reconstruction",
        )
    return result


def domain_evaluation_policy_review_to_dict(value: object) -> dict:
    governance = _governance()
    return _review_to_dict(governance, value)


def domain_evaluation_policy_review_from_dict(payload: object):
    governance = _governance()
    return _review_from_dict(governance, payload)


def domain_evaluation_policy_review_to_json(value: object) -> str:
    governance = _governance()
    return _dumps(governance, _review_to_dict(governance, value))


def domain_evaluation_policy_review_from_json(payload: object):
    governance = _governance()
    return _review_from_dict(governance, _loads(governance, payload))


def _review_ledger_to_dict(governance, value: object) -> dict:
    return governance._review_ledger_payload(governance._strict_review_ledger(value))


def _review_ledger_from_dict(governance, payload: object):
    obj = _obj(
        governance,
        payload,
        {"schema_version", "reviews"},
        "domain evaluation policy review ledger",
    )
    _schema(governance, obj, "domain evaluation policy review ledger")
    reviews_payload = _exact_list(governance, obj["reviews"], "reviews")
    reviews = tuple(_review_from_dict(governance, item) for item in reviews_payload)
    result = governance.DomainEvaluationPolicyReviewLedger(reviews=reviews)
    if _review_ledger_to_dict(governance, result) != obj:
        _fail(
            governance,
            "domain evaluation policy review ledger must equal canonical reconstruction",
        )
    return result


def domain_evaluation_policy_review_ledger_to_dict(value: object) -> dict:
    governance = _governance()
    return _review_ledger_to_dict(governance, value)


def domain_evaluation_policy_review_ledger_from_dict(payload: object):
    governance = _governance()
    return _review_ledger_from_dict(governance, payload)


def domain_evaluation_policy_review_ledger_to_json(value: object) -> str:
    governance = _governance()
    return _dumps(governance, _review_ledger_to_dict(governance, value))


def domain_evaluation_policy_review_ledger_from_json(payload: object):
    governance = _governance()
    return _review_ledger_from_dict(governance, _loads(governance, payload))


def _registry_entry_to_dict(governance, value: object) -> dict:
    # Registry strict reconstruction is applied by the public registry serializer.
    return {
        "policy_ref": str(value.policy_ref),
        "specification_sha256": value.specification_sha256,
        "specification": value.specification.to_dict(),
        "review_id": str(value.review_id),
        "review_sha256": value.review_sha256,
        "admitted_at": governance._format_time(value.admitted_at),
        "predecessor_registry_sha256": value.predecessor_registry_sha256,
    }


def _registry_entry_from_dict(governance, payload: object):
    obj = _obj(
        governance,
        payload,
        {
            "policy_ref",
            "specification_sha256",
            "specification",
            "review_id",
            "review_sha256",
            "admitted_at",
            "predecessor_registry_sha256",
        },
        "policy registry entry",
    )
    policy_ref = _exact_str(governance, obj["policy_ref"], "registry entry policy_ref")
    specification_sha256 = _exact_str(
        governance,
        obj["specification_sha256"],
        "registry entry specification_sha256",
    )
    review_id = _exact_str(governance, obj["review_id"], "registry entry review_id")
    review_sha256 = _exact_str(
        governance,
        obj["review_sha256"],
        "registry entry review_sha256",
    )
    admitted_at = _exact_str(
        governance,
        obj["admitted_at"],
        "registry entry admitted_at",
    )
    predecessor = _exact_str(
        governance,
        obj["predecessor_registry_sha256"],
        "registry entry predecessor_registry_sha256",
    )
    if type(obj["specification"]) is not dict:
        _fail(governance, "registry entry specification must be a JSON object")
    try:
        specification = DomainEvaluationPolicySpecification.from_dict(obj["specification"])
        result = governance.DomainEvaluationPolicyRegistryEntry(
            policy_ref=EvaluationPolicyRef.parse(policy_ref),
            specification_sha256=specification_sha256,
            specification=specification,
            review_id=governance.DomainEvaluationPolicyReviewId(review_id),
            review_sha256=review_sha256,
            admitted_at=governance._parse_time(
                admitted_at,
                "registry entry admitted_at",
            ),
            predecessor_registry_sha256=predecessor,
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, governance.InvalidDomainEvaluationPolicyGovernance):
            raise
        raise governance.InvalidDomainEvaluationPolicyGovernance(
            f"invalid policy registry entry: {exc}"
        ) from exc
    if _registry_entry_to_dict(governance, result) != obj:
        _fail(
            governance,
            "policy registry entry must equal canonical reconstruction",
        )
    return result


def _registry_to_dict(governance, value: object) -> dict:
    return governance._registry_payload(governance._strict_registry(value))


def _registry_from_dict(governance, payload: object):
    obj = _obj(
        governance,
        payload,
        {"schema_version", "entries"},
        "domain evaluation policy registry",
    )
    _schema(governance, obj, "domain evaluation policy registry")
    entries_payload = _exact_list(governance, obj["entries"], "entries")
    entries = tuple(
        _registry_entry_from_dict(governance, item) for item in entries_payload
    )
    result = governance.DomainEvaluationPolicyRegistry(entries=entries)
    if _registry_to_dict(governance, result) != obj:
        _fail(
            governance,
            "domain evaluation policy registry must equal canonical reconstruction",
        )
    return result


def domain_evaluation_policy_registry_to_dict(value: object) -> dict:
    governance = _governance()
    return _registry_to_dict(governance, value)


def domain_evaluation_policy_registry_from_dict(payload: object):
    governance = _governance()
    return _registry_from_dict(governance, payload)


def domain_evaluation_policy_registry_to_json(value: object) -> str:
    governance = _governance()
    return _dumps(governance, _registry_to_dict(governance, value))


def domain_evaluation_policy_registry_from_json(payload: object):
    governance = _governance()
    return _registry_from_dict(governance, _loads(governance, payload))


def _receipt_to_dict(governance, value: object) -> dict:
    return governance._receipt_payload(governance._strict_receipt(value))


def _receipt_from_dict(governance, payload: object):
    obj = _obj(
        governance,
        payload,
        {
            "schema_version",
            "policy_ref",
            "specification_sha256",
            "review_id",
            "review_sha256",
            "predecessor_registry_sha256",
            "successor_registry_sha256",
            "admitted_at",
        },
        "domain evaluation policy admission receipt",
    )
    _schema(governance, obj, "domain evaluation policy admission receipt")
    policy_ref = _exact_str(governance, obj["policy_ref"], "receipt policy_ref")
    specification_sha256 = _exact_str(
        governance,
        obj["specification_sha256"],
        "receipt specification_sha256",
    )
    review_id = _exact_str(governance, obj["review_id"], "receipt review_id")
    review_sha256 = _exact_str(governance, obj["review_sha256"], "receipt review_sha256")
    predecessor = _exact_str(
        governance,
        obj["predecessor_registry_sha256"],
        "receipt predecessor_registry_sha256",
    )
    successor = _exact_str(
        governance,
        obj["successor_registry_sha256"],
        "receipt successor_registry_sha256",
    )
    admitted_at = _exact_str(governance, obj["admitted_at"], "receipt admitted_at")
    try:
        result = governance.DomainEvaluationPolicyAdmissionReceipt(
            policy_ref=EvaluationPolicyRef.parse(policy_ref),
            specification_sha256=specification_sha256,
            review_id=governance.DomainEvaluationPolicyReviewId(review_id),
            review_sha256=review_sha256,
            predecessor_registry_sha256=predecessor,
            successor_registry_sha256=successor,
            admitted_at=governance._parse_time(admitted_at, "receipt admitted_at"),
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, governance.InvalidDomainEvaluationPolicyGovernance):
            raise
        raise governance.InvalidDomainEvaluationPolicyGovernance(
            f"invalid domain evaluation policy admission receipt: {exc}"
        ) from exc
    if _receipt_to_dict(governance, result) != obj:
        _fail(
            governance,
            "domain evaluation policy admission receipt must equal canonical reconstruction",
        )
    return result


def domain_evaluation_policy_admission_receipt_to_dict(value: object) -> dict:
    governance = _governance()
    return _receipt_to_dict(governance, value)


def domain_evaluation_policy_admission_receipt_from_dict(payload: object):
    governance = _governance()
    return _receipt_from_dict(governance, payload)


def domain_evaluation_policy_admission_receipt_to_json(value: object) -> str:
    governance = _governance()
    return _dumps(governance, _receipt_to_dict(governance, value))


def domain_evaluation_policy_admission_receipt_from_json(payload: object):
    governance = _governance()
    return _receipt_from_dict(governance, _loads(governance, payload))
