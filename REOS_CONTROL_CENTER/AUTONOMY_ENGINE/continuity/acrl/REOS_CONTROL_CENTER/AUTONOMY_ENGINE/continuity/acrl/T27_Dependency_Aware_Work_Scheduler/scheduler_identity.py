from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
    )


def fingerprint(value: Any) -> str:
    return hashlib.sha256(
        canonical_json(value).encode("utf-8")
    ).hexdigest()


def scheduler_identity(
    *,
    scheduler_id: str,
    loop_id: str,
    loop_fingerprint: str,
    graph_fingerprint: str,
    policy_fingerprint: str,
    continuity_fingerprint: str,
    evidence_fingerprint: str,
) -> str:
    return fingerprint(
        {
            "scheduler_id": scheduler_id,
            "loop_id": loop_id,
            "loop_fingerprint": loop_fingerprint,
            "graph_fingerprint": graph_fingerprint,
            "policy_fingerprint": policy_fingerprint,
            "continuity_fingerprint": continuity_fingerprint,
            "evidence_fingerprint": evidence_fingerprint,
        }
    )
