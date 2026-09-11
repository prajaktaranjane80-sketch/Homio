from __future__ import annotations

import hashlib
import json
from typing import Any


SCHEMA_VERSION = "1.0"
ALGORITHM = "sha256"


def canonicalize(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def fingerprint(value: Any) -> str:
    return hashlib.sha256(
        canonicalize(value).encode("utf-8")
    ).hexdigest()


__all__ = [
    "ALGORITHM",
    "SCHEMA_VERSION",
    "canonicalize",
    "fingerprint",
]
