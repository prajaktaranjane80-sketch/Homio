"""ACRL T03 — deterministic execution-state identity."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping


@dataclass(frozen=True)
class StateIdentity:
    """Deterministic identity of reconstructed execution state."""

    schema_version: str
    semantic_sha256: str
    source_sha256: str

    def to_dict(self) -> dict[str, str]:
        return {
            "schema_version": self.schema_version,
            "semantic_sha256": self.semantic_sha256,
            "source_sha256": self.source_sha256,
        }

    def identity_key(self) -> str:
        canonical = json.dumps(
            self.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()


def build_state_identity(
    state: Mapping[str, Any],
    source_sha256: str,
    *,
    schema_version: str = "1.0",
) -> StateIdentity:
    """Build semantic + source identity for state."""

    if not isinstance(state, Mapping):
        raise TypeError("state must be a mapping.")

    if not isinstance(
        source_sha256,
        str,
    ) or not source_sha256.strip():
        raise ValueError(
            "source_sha256 must be a non-empty string."
        )

    canonical = json.dumps(
        dict(state),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    semantic_sha256 = hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()

    return StateIdentity(
        schema_version=schema_version,
        semantic_sha256=semantic_sha256,
        source_sha256=source_sha256.strip(),
    )


__all__ = [
    "StateIdentity",
    "build_state_identity",
]
