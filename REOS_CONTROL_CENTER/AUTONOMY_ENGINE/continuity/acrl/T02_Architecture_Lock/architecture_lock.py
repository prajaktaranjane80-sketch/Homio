"""ACRL T02 â€” Architecture Lock.

Read-only architectural authority projection for HOMIO / REOS.

T02 verifies that the authoritative controller state contains an
explicitly frozen architecture and that its architectural identity
remains deterministic.

Authority remains:
    REOS_CONTROL_CENTER/data/state.json

T02 must never:
    - mutate state
    - mutate architecture
    - approve changes
    - authorize execution
    - authorize writes
    - repair project code
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
from typing import Any, Mapping


ARCHITECTURE_LOCK_SCHEMA_VERSION = "1.0"


class ArchitectureLockError(RuntimeError):
    """Base error for T02 failures."""


class ArchitectureLockSourceError(ArchitectureLockError):
    """Authoritative source is missing or unreadable."""


class ArchitectureNotLockedError(ArchitectureLockError):
    """Architecture is not explicitly frozen."""


class ArchitectureDriftError(ArchitectureLockError):
    """Architecture identity changed."""


class ArchitectureLockIntegrityError(ArchitectureLockError):
    """Architecture authority data is structurally invalid."""


@dataclass(frozen=True)
class ArchitectureLock:
    """Immutable architectural authority projection."""

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

    schema_version: str = ARCHITECTURE_LOCK_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic serializable representation."""

        return {
            "schema_version": self.schema_version,
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
                "execution_authorized": False,
                "write_authorized": False,
                "approval_authorized": False,
            },
            "architecture_fingerprint": (
                self.architecture_fingerprint
            ),
            "source_state_sha256": (
                self.source_state_sha256
            ),
        }

    def is_locked(self) -> bool:
        """Return whether architecture is explicitly frozen."""

        return self.architecture_status == "FROZEN"


class ArchitectureLockReader:
    """Read-only reader for authoritative architecture state."""

    def __init__(
        self,
        control_center_root: Path | str | None = None,
    ) -> None:
        if control_center_root is None:
            # File:
            # .../REOS_CONTROL_CENTER/
            #   AUTONOMY_ENGINE/continuity/acrl/
            #   T02_Architecture_Lock/architecture_lock.py
            #
            # parents[4] = REOS_CONTROL_CENTER
            self.root = Path(
                __file__
            ).resolve().parents[4]
        else:
            self.root = Path(
                control_center_root
            ).resolve()

        self.state_path = (
            self.root
            / "data"
            / "state.json"
        )

    @staticmethod
    def _load_state_bytes(
        path: Path,
    ) -> tuple[bytes, dict[str, Any]]:
        """Read bytes once and derive JSON from the same snapshot."""

        if not path.exists():
            raise ArchitectureLockSourceError(
                f"Authoritative state not found: {path}"
            )

        if not path.is_file():
            raise ArchitectureLockSourceError(
                f"Authoritative state path is not a file: {path}"
            )

        try:
            raw = path.read_bytes()
            text = raw.decode("utf-8-sig")
            value = json.loads(text)
        except (
            OSError,
            UnicodeError,
            json.JSONDecodeError,
        ) as exc:
            raise ArchitectureLockSourceError(
                f"Unable to read authoritative state: {path}"
            ) from exc

        if not isinstance(value, dict):
            raise ArchitectureLockIntegrityError(
    "Authoritative state must contain a JSON object."
)

        return raw, value

    @staticmethod
    def _required_string(
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
    def _required_bool(
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
    def _sha256_bytes(raw: bytes) -> str:
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _architecture_fingerprint(
        architecture: Mapping[str, Any],
    ) -> str:
        try:
            canonical = json.dumps(
                architecture,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ArchitectureLockIntegrityError(
                "Architecture cannot be canonically fingerprinted."
            ) from exc

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _validate_hash(
        value: str,
        field: str,
    ) -> None:
        if (
            len(value) != 64
            or any(
                char not in "0123456789abcdef"
                for char in value
            )
        ):
            raise ArchitectureLockIntegrityError(
                f"{field} must be a lowercase SHA-256 hex digest."
            )

    def read(self) -> ArchitectureLock:
        """Read and validate frozen architecture authority."""

        raw, state = self._load_state_bytes(
            self.state_path
        )

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

        canonical_source = self._required_string(
            constitution,
            "canonical_source",
            "constitution",
        )

        if canonical_source != "data/state.json":
            raise ArchitectureLockIntegrityError(
                "Architecture authority must use data/state.json."
            )

        architecture_before_code = (
            self._required_bool(
                constitution,
                "architecture_before_code",
                "constitution",
            )
        )

        no_silent_changes = self._required_bool(
            constitution,
            "no_silent_architecture_changes",
            "constitution",
        )

        no_duplicate_logic = self._required_bool(
            constitution,
            "no_duplicate_logic",
            "constitution",
        )

        if not architecture_before_code:
            raise ArchitectureNotLockedError(
                "Architecture-before-code policy is disabled."
            )

        if not no_silent_changes:
            raise ArchitectureNotLockedError(
                "Silent architecture changes are permitted."
            )

        if not no_duplicate_logic:
            raise ArchitectureNotLockedError(
                "Duplicate logic protection is disabled."
            )

        architecture_id = self._required_string(
            architecture,
            "id",
            "architecture",
        )

        architecture_version = self._required_string(
            architecture,
            "version",
            "architecture",
        )

        architecture_status = self._required_string(
            architecture,
            "status",
            "architecture",
        )

        architecture_phase = self._required_string(
            architecture,
            "phase",
            "architecture",
        )

        if architecture_status != "FROZEN":
            raise ArchitectureNotLockedError(
                "Authoritative architecture is not FROZEN."
            )

        architecture_fingerprint = (
            self._architecture_fingerprint(
                architecture
            )
        )

        source_state_sha256 = (
            self._sha256_bytes(raw)
        )

        self._validate_hash(
            architecture_fingerprint,
            "architecture_fingerprint",
        )

        self._validate_hash(
            source_state_sha256,
            "source_state_sha256",
        )

        return ArchitectureLock(
            architecture_id=architecture_id,
            architecture_version=architecture_version,
            architecture_status=architecture_status,
            architecture_phase=architecture_phase,
            canonical_source=canonical_source,
            architecture_before_code=(
                architecture_before_code
            ),
            no_silent_architecture_changes=(
                no_silent_changes
            ),
            no_duplicate_logic=no_duplicate_logic,
            architecture_fingerprint=(
                architecture_fingerprint
            ),
            source_state_sha256=(
                source_state_sha256
            ),
        )

    def verify_fingerprint(
        self,
        expected_fingerprint: str,
    ) -> ArchitectureLock:
        """Verify current architecture against expected fingerprint."""

        if (
            not isinstance(
                expected_fingerprint,
                str,
            )
            or not expected_fingerprint.strip()
        ):
            raise ArchitectureDriftError(
                "Expected architecture fingerprint is required."
            )

        expected = expected_fingerprint.strip()

        self._validate_hash(
            expected,
            "expected_fingerprint",
        )

        current = self.read()

        if (
            current.architecture_fingerprint
            != expected
        ):
            raise ArchitectureDriftError(
                "Authoritative architecture fingerprint has changed."
            )

        return current


def read_architecture_lock(
    control_center_root: Path | str | None = None,
) -> ArchitectureLock:
    """Convenience API."""

    return ArchitectureLockReader(
        control_center_root
    ).read()


__all__ = [
    "ARCHITECTURE_LOCK_SCHEMA_VERSION",
    "ArchitectureDriftError",
    "ArchitectureLock",
    "ArchitectureLockError",
    "ArchitectureLockIntegrityError",
    "ArchitectureLockReader",
    "ArchitectureLockSourceError",
    "ArchitectureNotLockedError",
    "read_architecture_lock",
]

