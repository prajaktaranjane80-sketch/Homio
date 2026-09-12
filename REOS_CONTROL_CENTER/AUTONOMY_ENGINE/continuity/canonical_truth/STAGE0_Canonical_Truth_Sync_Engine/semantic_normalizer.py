from __future__ import annotations

import json
import re
from typing import Any


_VOLATILE_KEYS = {
    "updated_at",
    "modified_at",
    "generated_at",
    "timestamp",
    "time",
    "created_at",
    "verified_at",
}


def normalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: normalize(val)
            for key, val in sorted(value.items())
            if key not in _VOLATILE_KEYS
        }
    if isinstance(value, list):
        return [normalize(v) for v in value]
    if isinstance(value, str):
        return re.sub(r"\s+", " ", value.strip())
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(normalize(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
