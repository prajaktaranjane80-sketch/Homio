"""ACRL T14 deterministic identities."""
from __future__ import annotations
import hashlib
import json
from typing import Any


def canonicalize(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonicalize(value).encode("utf-8")).hexdigest()


def fingerprint_manifest(items: Any) -> str:
    return fingerprint(items)
