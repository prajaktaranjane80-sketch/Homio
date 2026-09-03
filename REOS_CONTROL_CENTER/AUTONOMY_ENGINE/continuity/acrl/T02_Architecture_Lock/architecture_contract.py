"""ACRL T02 â€” architecture-lock contract validation."""

from __future__ import annotations

import re

from .architecture_lock import ArchitectureLock


_SHA256_RE = re.compile(
    r"^[0-9a-f]{64}$"
)


def validate_architecture_lock_contract(
    lock: ArchitectureLock,
) -> None:
    """Validate the machine-readable T02 contract boundary."""

    if not isinstance(lock, ArchitectureLock):
        raise TypeError(
            "lock must be ArchitectureLock."
        )

    if lock.schema_version != "1.0":
        raise ValueError(
            "Unsupported T02 architecture-lock schema."
        )

    if lock.architecture_status != "FROZEN":
        raise ValueError(
            "T02 requires FROZEN architecture."
        )

    if lock.canonical_source != "data/state.json":
        raise ValueError(
            "T02 requires data/state.json authority."
        )

    for field_name, value in (
        (
            "architecture_fingerprint",
            lock.architecture_fingerprint,
        ),
        (
            "source_state_sha256",
            lock.source_state_sha256,
        ),
    ):
        if not _SHA256_RE.fullmatch(value):
            raise ValueError(
                f"{field_name} is not valid SHA-256."
            )


def contract_dict() -> dict[str, object]:
    """Return non-authorizing contract metadata."""

    return {
        "schema_version": "1.0",
        "layer": "T02",
        "name": "Architecture Lock",
        "mode": "READ_ONLY",
        "canonical_source": "data/state.json",
        "permissions": {
            "read_state": True,
            "write_state": False,
            "modify_architecture": False,
            "approve_changes": False,
            "authorize_execution": False,
            "repair_code": False,
        },
        "safety": {
            "fail_closed_on_invalid_authority": True,
            "deterministic_fingerprints": True,
            "replay_safe": True,
            "idempotent": True,
        },
    }

__all__ = [
    "contract_dict",
    "validate_architecture_lock_contract",
]

