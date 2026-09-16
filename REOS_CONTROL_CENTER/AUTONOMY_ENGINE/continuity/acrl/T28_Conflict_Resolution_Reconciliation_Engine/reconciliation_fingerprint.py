import hashlib
import json
from typing import Any

from .reconciliation_models import ReconciliationPolicy, Resolution


def validate_policy(policy: ReconciliationPolicy) -> None:
    if not policy.policy_version.strip():
        raise ValueError("policy_version required")

    if not isinstance(policy.require_evidence_for_high_conflict, bool):
        raise ValueError("require_evidence_for_high_conflict must be bool")

    if not isinstance(policy.allow_precedence_resolution, bool):
        raise ValueError("allow_precedence_resolution must be bool")

    if not isinstance(policy.allow_human_boundary, bool):
        raise ValueError("allow_human_boundary must be bool")


def resolution_fingerprint(resolutions: tuple[Resolution, ...]) -> str:
    payload: list[dict[str, Any]] = [
        {
            "conflict_id": resolution.conflict_id,
            "kind": resolution.kind.value,
            "selected_value": resolution.selected_value,
            "rationale": resolution.rationale,
            "evidence_ids": list(resolution.evidence_ids),
        }
        for resolution in resolutions
    ]

    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()
