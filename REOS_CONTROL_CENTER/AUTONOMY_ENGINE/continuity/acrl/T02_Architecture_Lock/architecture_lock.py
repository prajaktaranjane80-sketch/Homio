"""ACRL T02 — Architecture Lock.

Provides a deterministic, read-only architecture authority projection.

This module does not redesign, mutate, or replace REOS architecture.
It verifies that the authoritative controller state declares the
architecture as locked and that the approved architecture identity
remains stable.

Authority remains with REOS_CONTROL_CENTER/data/state.json.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


class ArchitectureLockError(RuntimeError):
    """Base error for architecture-lock failures."""


class ArchitectureLockSourceError(ArchitectureLockError):
    """Raised when authoritative state cannot be read."""


class ArchitectureNotLockedError(ArchitectureLockError):
    """Raised when architecture is not approved/frozen."""


class ArchitectureDriftError(ArchitectureLockError):
    """Raised when the architecture fingerprint changes."""


class ArchitectureLockIntegrityError(ArchitectureLockError):
    """Raised when architecture authority data is invalid."""


@dataclass(frozen=True)
class ArchitectureLock:
    """Immutable architecture-lock projection."""

    architecture_id: str
    architecture_version: str
    architecture_status: str
    architecture_phase: str

    canonical_source: str
    architecture_before_code: bool
    no_silent_architecture_changes: bool
    no_duplicate_logic: bool

    architecture_fingerprint: str
    source_state_sha256: str

    def to_dict(self) -> dict[str, Any]:
        """Return the canonical serializable lock projection."""

        return {
            "schema_version": "1.0",
            "architecture_id": self.architecture_id,
            "architecture_version": self.architecture_version,
            "architecture_status": self.architecture_status,
            "architecture_phase": self.architecture_phase,
            "authority": {
                "canonical_source": self.canonical_source,
                "architecture_before_code": (
                    self.architecture_before_code
                ),
                "no_silent_architecture_changes": (
                    self.no_silent_architecture_changes
                ),
                "no_duplicate_logic": self.no_duplicate_logic,
            },
            "architecture_fingerprint": self.architecture_fingerprint,
            "source_state_sha256": self.source_state_sha256,
        }

    def is_locked(self) -> bool:
        """Return whether the architecture is explicitly locked."""

        return self.architecture_status == "FROZEN"


class ArchitectureLockReader:
    """Read-only reader for the authoritative architecture lock."""

    def __init__(
        self,
        control_center_root: Path | str | None = None,
    ) -> None:
        if control_center_root is None:
            self.root = Path(__file__).resolve().parents[3]
        else:
            self.root = Path(control_center_root)

        self.state_path = self.root / "data" / "state.json"

    @staticmethod
    def _read_state(path: Path) -> dict[str, Any]:
        if not path.exists():
            raise ArchitectureLockSourceError(
                f"Authoritative state not found: {path}"
            )

        try:
            raw = path.read_text(encoding="utf-8-sig")
            state = json.loads(raw)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ArchitectureLockSourceError(
                f"Unable to read authoritative state: {path}"
            ) from exc

        if not isinstance(state, dict):
            raise ArchitectureLockSourceError(
                "Authoritative state must contain a JSON object."
            )

        return state

    @staticmethod
    def _string(
        mapping: Mapping[str, Any],
        key: str,
        section: str,
    ) -> str:
        value = mapping.get(key)

        if not isinstance(value, str) or not value.strip():
            raise ArchitectureLockIntegrityError(
                f"{section}.{key} must be a non-empty string."
            )

        return value.strip()

    @staticmethod
    def _bool(
        mapping: Mapping[str, Any],
        key: str,
        section: str,
    ) -> bool:
        value = mapping.get(key)

        if not isinstance(value, bool):
            raise ArchitectureLockIntegrityError(
                f"{section}.{key} must be boolean."
            )

        return value

    @staticmethod
    def _sha256(path: Path) -> str:
        try:
            return hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError as exc:
            raise ArchitectureLockSourceError(
                f"Unable to fingerprint state: {path}"
            ) from exc

    @staticmethod
    def _architecture_fingerprint(
        architecture: Mapping[str, Any],
    ) -> str:
        """Create a deterministic fingerprint of architecture authority."""

        canonical = json.dumps(
            architecture,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

    def read(self) -> ArchitectureLock:
        """Read and validate the authoritative architecture lock."""

        state = self._read_state(self.state_path)

        meta = state.get("meta")
        constitution = state.get("constitution")
        architecture = state.get("architecture")

        if not isinstance(meta, Mapping):
            raise ArchitectureLockIntegrityError(
                "state.meta must be an object."
            )

        if not isinstance(constitution, Mapping):
            raise ArchitectureLockIntegrityError(
                "state.constitution must be an object."
            )

        if not isinstance(architecture, Mapping):
            raise ArchitectureLockIntegrityError(
                "state.architecture must be an object."
            )

        canonical_source = self._string(
            constitution,
            "canonical_source",
            "constitution",
        )

        if canonical_source != "data/state.json":
            raise ArchitectureLockIntegrityError(
                "Architecture authority must use data/state.json."
            )

        architecture_before_code = self._bool(
            constitution,
            "architecture_before_code",
            "constitution",
        )

        no_silent_architecture_changes = self._bool(
            constitution,
            "no_silent_architecture_changes",
            "constitution",
        )

        no_duplicate_logic = self._bool(
            constitution,
            "no_duplicate_logic",
            "constitution",
        )

        if not architecture_before_code:
            raise ArchitectureNotLockedError(
                "Architecture-before-code policy is not enabled."
            )

        if not no_silent_architecture_changes:
            raise ArchitectureNotLockedError(
                "Silent architecture changes are not forbidden."
            )

        if not no_duplicate_logic:
            raise ArchitectureNotLockedError(
                "Duplicate logic protection is not enabled."
            )

        architecture_id = self._string(
            architecture,
            "id",
            "architecture",
        )

        architecture_version = self._string(
            architecture,
            "version",
            "architecture",
        )

        architecture_status = self._string(
            architecture,
            "status",
            "architecture",
        )

        architecture_phase = self._string(
            architecture,
            "phase",
            "architecture",
        )

        if architecture_status != "FROZEN":
            raise ArchitectureNotLockedError(
                "Authoritative architecture is not FROZEN."
            )

        return ArchitectureLock(
            architecture_id=architecture_id,
            architecture_version=architecture_version,
            architecture_status=architecture_status,
            architecture_phase=architecture_phase,
            canonical_source=canonical_source,
            architecture_before_code=architecture_before_code,
            no_silent_architecture_changes=(
                no_silent_architecture_changes
            ),
            no_duplicate_logic=no_duplicate_logic,
            architecture_fingerprint=(
                self._architecture_fingerprint(architecture)
            ),
            source_state_sha256=self._sha256(self.state_path),
        )

    def verify_fingerprint(
        self,
        expected_fingerprint: str,
    ) -> ArchitectureLock:
        """Verify the current architecture against a known fingerprint."""

        if (
            not isinstance(expected_fingerprint, str)
            or not expected_fingerprint.strip()
        ):
            raise ArchitectureDriftError(
                "Expected architecture fingerprint is required."
            )

        current = self.read()

        if current.architecture_fingerprint != expected_fingerprint:
            raise ArchitectureDriftError(
                "Authoritative architecture fingerprint has changed."
            )

        return current


def read_architecture_lock(
    control_center_root: Path | str | None = None,
) -> ArchitectureLock:
    """Convenience API for reading the architecture lock."""

    return ArchitectureLockReader(control_center_root).read()


__all__ = [
    "ArchitectureDriftError",
    "ArchitectureLock",
    "ArchitectureLockError",
    "ArchitectureLockIntegrityError",
    "ArchitectureLockReader",
    "ArchitectureLockSourceError",
    "ArchitectureNotLockedError",
    "read_architecture_lock",
]