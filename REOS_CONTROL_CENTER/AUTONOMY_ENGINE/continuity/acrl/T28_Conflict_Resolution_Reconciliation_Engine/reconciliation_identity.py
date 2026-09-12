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


def reconciliation_identity(
    *,
    reconciliation_id: str,
    scheduler_fingerprint: str,
    continuity_fingerprint: str,
    evidence_fingerprint: str,
    policy_fingerprint: str,
) -> str:
    payload = {
        "reconciliation_id": reconciliation_id,
        "scheduler_fingerprint": scheduler_fingerprint,
        "continuity_fingerprint": continuity_fingerprint,
        "evidence_fingerprint": evidence_fingerprint,
        "policy_fingerprint": policy_fingerprint,
    }
    return fingerprint(payload)
