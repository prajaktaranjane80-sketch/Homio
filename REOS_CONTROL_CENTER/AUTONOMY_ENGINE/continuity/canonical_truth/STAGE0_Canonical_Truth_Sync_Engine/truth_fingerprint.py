from __future__ import annotations

import hashlib
from typing import Any

from .semantic_normalizer import canonical_json


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()
