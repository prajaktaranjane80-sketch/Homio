"""ACRL T02 — deterministic architecture identity."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from .architecture_lock import ArchitectureLock


@dataclass(frozen=True)
class ArchitectureIdentity:
    """Stable semantic identity of frozen architecture."""

    architecture_id: str
    architecture_version: str
    architecture_status: str
    architecture_phase: str
    architecture_fingerprint: str

    def to_dict(self) -> dict[str, str]:
        return {
            "architecture_id": self.architecture_id,
            "architecture_version": self.architecture_version,
            "architecture_status": self.architecture_status,
            "architecture_phase": self.architecture_phase,
            "architecture_fingerprint": (
                self.architecture_fingerprint
            ),
        }

    def identity_key(self) -> str:
        """Return deterministic identity key."""

        canonical = json.dumps(
            self.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()


def build_architecture_identity(
    lock: ArchitectureLock,
) -> ArchitectureIdentity:
    """Build immutable identity from T02 architecture lock."""

    if not isinstance(lock, ArchitectureLock):
        raise TypeError(
            "lock must be ArchitectureLock."
        )

    return ArchitectureIdentity(
        architecture_id=lock.architecture_id,
        architecture_version=lock.architecture_version,
        architecture_status=lock.architecture_status,
        architecture_phase=lock.architecture_phase,
        architecture_fingerprint=(
            lock.architecture_fingerprint
        ),
    )


__all__ = [
    "ArchitectureIdentity",
    "build_architecture_identity",
]