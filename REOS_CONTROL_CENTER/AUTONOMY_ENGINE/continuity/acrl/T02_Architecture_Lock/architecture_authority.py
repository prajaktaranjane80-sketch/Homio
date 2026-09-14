"""ACRL T02 — Canonical Architecture Authority Reconstruction.

This module reconstructs the architecture authority directly from the
canonical REOS_CONTROL_CENTER/data/state.json schema.

It does not create architecture, change architecture, or grant execution
authority.

The current canonical state may legitimately contain an approved architecture
set that is not yet frozen. In that situation the reconstruction must report
that condition and keep code-change authority blocked.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


ARCHITECTURE_AUTHORITY_SCHEMA_VERSION = "1.0"


class ArchitectureAuthorityError(RuntimeError):
    """Base error for canonical architecture authority reconstruction."""


class ArchitectureAuthoritySourceError(
    ArchitectureAuthorityError
):
    """Canonical architecture source is missing or unreadable."""


class ArchitectureAuthorityIntegrityError(
    ArchitectureAuthorityError
):
    """Canonical architecture authority is structurally invalid."""


@dataclass(frozen=True)
class ArchitectureAuthority:
    """Immutable projection of canonical architecture authority."""

    canonical_source: str
    status: str
    locked: bool

    architecture_before_code: bool
    no_silent_architecture_changes: bool
    no_duplicate_logic: bool

    approved: tuple[tuple[str, str, str], ...]
    pending: tuple[tuple[str, str, str], ...]

    architecture_fingerprint: str
    source_state_sha256: str

    schema_version: str = (
        ARCHITECTURE_AUTHORITY_SCHEMA_VERSION
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "canonical_source": self.canonical_source,
            "status": self.status,
            "locked": self.locked,
            "policies": {
                "architecture_before_code": (
                    self.architecture_before_code
                ),
                "no_silent_architecture_changes": (
                    self.no_silent_architecture_changes
                ),
                "no_duplicate_logic": self.no_duplicate_logic,
            },
            "approved": [
                {
                    "id": item[0],
                    "name": item[1],
                    "status": item[2],
                }
                for item in self.approved
            ],
            "pending": [
                {
                    "id": item[0],
                    "name": item[1],
                    "status": item[2],
                }
                for item in self.pending
            ],
            "fingerprints": {
                "architecture_sha256": (
                    self.architecture_fingerprint
                ),
                "state_sha256": (
                    self.source_state_sha256
                ),
            },
            "authority": {
                "execution_authorized": False,
                "write_authorized": False,
                "approval_authorized": False,
            },
        }

    def is_frozen(self) -> bool:
        """Return whether canonical architecture is explicitly locked."""

        return self.locked

    def code_changes_allowed(self) -> bool:
        """Return whether architecture permits code progression."""

        return self.locked


class ArchitectureAuthorityReader:
    """Read-only reader for canonical architecture authority."""

    def __init__(
        self,
        control_center_root: Path | str | None = None,
    ) -> None:
        if control_center_root is None:
            self.root = Path(__file__).resolve().parents[4]
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
    def _read_state(
        path: Path,
    ) -> tuple[bytes, dict[str, Any]]:
        if not path.exists():
            raise ArchitectureAuthoritySourceError(
                f"Authoritative state not found: {path}"
            )

        if not path.is_file():
            raise ArchitectureAuthoritySourceError(
                f"Authoritative state is not a file: {path}"
            )

        try:
            raw = path.read_bytes()
            value = json.loads(
                raw.decode("utf-8-sig")
            )
        except (
            OSError,
            UnicodeError,
            json.JSONDecodeError,
        ) as exc:
            raise ArchitectureAuthoritySourceError(
                f"Unable to read authoritative state: {path}"
            ) from exc

        if not isinstance(value, dict):
            raise ArchitectureAuthorityIntegrityError(
                "Authoritative state must be a JSON object."
            )

        return raw, value

    @staticmethod
    def _required_mapping(
        value: Any,
        field: str,
    ) -> Mapping[str, Any]:
        if not isinstance(value, Mapping):
            raise ArchitectureAuthorityIntegrityError(
                f"{field} must be an object."
            )

        return value

    @staticmethod
    def _required_bool(
        mapping: Mapping[str, Any],
        key: str,
    ) -> bool:
        value = mapping.get(key)

        if not isinstance(value, bool):
            raise ArchitectureAuthorityIntegrityError(
                f"{key} must be boolean."
            )

        return value

    @staticmethod
    def _architecture_entries(
        value: Any,
        section: str,
    ) -> tuple[tuple[str, str, str], ...]:
        if not isinstance(value, list):
            raise ArchitectureAuthorityIntegrityError(
                f"architecture.{section} must be a list."
            )

        entries: list[tuple[str, str, str]] = []

        for index, item in enumerate(value):
            if not isinstance(item, Mapping):
                raise ArchitectureAuthorityIntegrityError(
                    f"architecture.{section}[{index}] must be an object."
                )

            item_id = item.get("id")
            name = item.get("name")
            status = item.get("status")

            if not isinstance(item_id, str) or not item_id.strip():
                raise ArchitectureAuthorityIntegrityError(
                    f"architecture.{section}[{index}].id "
                    "must be a non-empty string."
                )

            if not isinstance(name, str) or not name.strip():
                raise ArchitectureAuthorityIntegrityError(
                    f"architecture.{section}[{index}].name "
                    "must be a non-empty string."
                )

            if not isinstance(status, str) or not status.strip():
                raise ArchitectureAuthorityIntegrityError(
                    f"architecture.{section}[{index}].status "
                    "must be a non-empty string."
                )

            entries.append(
                (
                    item_id.strip(),
                    name.strip(),
                    status.strip(),
                )
            )

        return tuple(entries)

    @staticmethod
    def _architecture_fingerprint(
        architecture: Mapping[str, Any],
    ) -> str:
        canonical = json.dumps(
            architecture,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

    def read(self) -> ArchitectureAuthority:
        """Reconstruct architecture authority from canonical state."""

        raw, state = self._read_state(
            self.state_path
        )

        constitution = self._required_mapping(
            state.get("constitution"),
            "state.constitution",
        )

        architecture = self._required_mapping(
            state.get("architecture"),
            "state.architecture",
        )

        canonical_source = constitution.get(
            "canonical_source"
        )

        if canonical_source != "data/state.json":
            raise ArchitectureAuthorityIntegrityError(
                "Architecture authority must use data/state.json."
            )

        architecture_before_code = (
            self._required_bool(
                constitution,
                "architecture_before_code",
            )
        )

        no_silent_changes = self._required_bool(
            constitution,
            "no_silent_architecture_changes",
        )

        no_duplicate_logic = self._required_bool(
            constitution,
            "no_duplicate_logic",
        )

        approved = self._architecture_entries(
            architecture.get("approved"),
            "approved",
        )

        pending = self._architecture_entries(
            architecture.get("pending"),
            "pending",
        )

        locked = architecture.get("locked")

        if not isinstance(locked, bool):
            raise ArchitectureAuthorityIntegrityError(
                "architecture.locked must be boolean."
            )

        status = (
            "FROZEN"
            if locked
            else "APPROVED_NOT_FROZEN"
        )

        architecture_fingerprint = (
            self._architecture_fingerprint(
                architecture
            )
        )

        source_state_sha256 = hashlib.sha256(
            raw
        ).hexdigest()

        return ArchitectureAuthority(
            canonical_source=canonical_source,
            status=status,
            locked=locked,
            architecture_before_code=(
                architecture_before_code
            ),
            no_silent_architecture_changes=(
                no_silent_changes
            ),
            no_duplicate_logic=no_duplicate_logic,
            approved=approved,
            pending=pending,
            architecture_fingerprint=(
                architecture_fingerprint
            ),
            source_state_sha256=(
                source_state_sha256
            ),
        )


def read_architecture_authority(
    control_center_root: Path | str | None = None,
) -> ArchitectureAuthority:
    """Convenience API for canonical architecture reconstruction."""

    return ArchitectureAuthorityReader(
        control_center_root
    ).read()


__all__ = [
    "ARCHITECTURE_AUTHORITY_SCHEMA_VERSION",
    "ArchitectureAuthority",
    "ArchitectureAuthorityError",
    "ArchitectureAuthorityIntegrityError",
    "ArchitectureAuthorityReader",
    "ArchitectureAuthoritySourceError",
    "read_architecture_authority",
]
