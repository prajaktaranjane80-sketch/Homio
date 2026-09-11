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


def text_fingerprint(value: str) -> str:
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()
