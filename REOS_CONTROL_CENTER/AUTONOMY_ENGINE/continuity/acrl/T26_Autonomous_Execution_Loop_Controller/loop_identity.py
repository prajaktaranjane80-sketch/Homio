from __future__ import annotations

import hashlib
import json
from typing import Any


def canonicalize(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def fingerprint(value: Any) -> str:
    return hashlib.sha256(
        canonicalize(value).encode("utf-8")
    ).hexdigest()


def iteration_fingerprint(
    loop_id: str,
    iteration: int,
    checkpoint_fingerprint: str,
    continuity_fingerprint: str,
) -> str:
    return fingerprint(
        {
            "loop_id": loop_id,
            "iteration": iteration,
            "checkpoint_fingerprint": checkpoint_fingerprint,
            "continuity_fingerprint": continuity_fingerprint,
        }
    )
