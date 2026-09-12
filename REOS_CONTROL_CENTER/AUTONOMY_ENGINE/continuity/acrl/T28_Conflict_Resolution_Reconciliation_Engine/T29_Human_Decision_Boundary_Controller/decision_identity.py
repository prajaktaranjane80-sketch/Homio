import hashlib
import json
from typing import Any


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def fingerprint(value: Any) -> str:
    return hashlib.sha256(
        canonical_json(value).encode("utf-8")
    ).hexdigest()


def decision_identity(
    *,
    decision_id: str,
    reconciliation_fingerprint: str,
    continuity_fingerprint: str,
    evidence_fingerprint: str,
    policy_fingerprint: str,
) -> str:
    return fingerprint(
        {
            "decision_id": decision_id,
            "reconciliation_fingerprint": reconciliation_fingerprint,
            "continuity_fingerprint": continuity_fingerprint,
            "evidence_fingerprint": evidence_fingerprint,
            "policy_fingerprint": policy_fingerprint,
        }
    )
