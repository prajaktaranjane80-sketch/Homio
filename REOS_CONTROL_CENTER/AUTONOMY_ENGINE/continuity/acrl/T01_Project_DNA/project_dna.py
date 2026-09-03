"""ACRL T01 — Project DNA.

Autonomous Continuity & Recovery Layer.

T01 provides a read-only, deterministic project identity projection
for a new AI/operator session.

Authority model
---------------
Authoritative sources remain:

    1. REOS_CONTROL_CENTER/data/state.json
    2. Approved/frozen architecture represented by controller state
    3. Git repository for code/history

T01 does not create a second project state.

T01 responsibilities
--------------------
- Read authoritative controller state.
- Validate the minimum Project DNA contract.
- Produce an immutable project identity projection.
- Produce a deterministic source fingerprint.
- Produce a compact machine bootstrap payload.
- Expose authority/continuity metadata without granting permission.
- Fail closed on invalid authoritative state.

T01 must NOT:
- mutate state.json
- mutate architecture
- mutate roadmap
- approve actions
- transition gates
- authorize writes
- repair code
- use chat history as project memory
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


DNA_SCHEMA_VERSION = "2.0"


class ProjectDNAError(RuntimeError):
    """Base error for Project DNA failures."""


class ProjectDNASourceError(ProjectDNAError):
    """Raised when an authoritative DNA source is missing or unreadable."""


class ProjectDNAIntegrityError(ProjectDNAError):
    """Raised when authoritative Project DNA is structurally invalid."""


@dataclass(frozen=True)
class ProjectDNA:
    """Immutable identity projection derived from authoritative state."""

    product: str
    project_name: str
    project_type: str
    north_star: str
    operating_principle: str

    controller_version: str
    state_schema_version: int
    phase: str

    canonical_source: str
    architecture_before_code: bool
    single_source_of_truth: bool
    micro_modular: bool
    no_duplicate_logic: bool
    no_silent_architecture_changes: bool
    chat_history_is_not_project_memory: bool

    source_state_sha256: str
    semantic_state_sha256: str

    dna_schema_version: str = DNA_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        """Return the canonical serializable Project DNA projection."""

        return {
            "schema_version": self.dna_schema_version,
            "product": self.product,
            "project_name": self.project_name,
            "project_type": self.project_type,
            "north_star": self.north_star,
            "operating_principle": self.operating_principle,
            "controller_version": self.controller_version,
            "state_schema_version": self.state_schema_version,
            "phase": self.phase,
            "authority": {
                "canonical_source": self.canonical_source,
                "architecture_before_code": self.architecture_before_code,
                "single_source_of_truth": self.single_source_of_truth,
                "micro_modular": self.micro_modular,
                "no_duplicate_logic": self.no_duplicate_logic,
                "no_silent_architecture_changes": (
                    self.no_silent_architecture_changes
                ),
                "chat_history_is_not_project_memory": (
                    self.chat_history_is_not_project_memory
                ),
                "execution_authority": "NOT_GRANTED",
                "write_authority": "NOT_GRANTED",
                "approval_authority": "NOT_GRANTED",
            },
            "fingerprint": {
                "source_state_sha256": self.source_state_sha256,
                "semantic_state_sha256": self.semantic_state_sha256,
            },
        }

    def resume_identity(self) -> str:
        """Return compact deterministic authority context for a new session."""

        return "\n".join(
            (
                f"HOMIO / REOS — PROJECT DNA v{self.dna_schema_version}",
                "=" * 62,
                f"PRODUCT={self.product}",
                f"PROJECT={self.project_name}",
                f"TYPE={self.project_type}",
                f"PHASE={self.phase}",
                f"CONTROLLER_VERSION={self.controller_version}",
                f"STATE_SCHEMA_VERSION={self.state_schema_version}",
                f"CANONICAL_SOURCE={self.canonical_source}",
                "CHAT_MEMORY=NON_AUTHORITATIVE",
                "ARCHITECTURE_CHANGE=FORBIDDEN_WITHOUT_AUTHORITY",
                "DUPLICATE_LOGIC=FORBIDDEN",
                "EXECUTION_AUTHORITY=NOT_GRANTED",
                "WRITE_AUTHORITY=NOT_GRANTED",
                f"STATE_SHA256={self.source_state_sha256}",
                f"SEMANTIC_STATE_SHA256={self.semantic_state_sha256}",
            )
        )

    def bootstrap_payload(self) -> dict[str, Any]:
        """Return the minimum machine bootstrap payload for a new AI agent."""

        return {
            "dna_schema_version": self.dna_schema_version,
            "project": {
                "product": self.product,
                "name": self.project_name,
                "type": self.project_type,
                "phase": self.phase,
                "north_star": self.north_star,
                "operating_principle": self.operating_principle,
            },
            "authority": {
                "canonical_source": self.canonical_source,
                "chat_memory_authoritative": False,
                "execution_authorized": False,
                "write_authorized": False,
                "approval_authorized": False,
            },
            "compatibility": {
                "controller_version": self.controller_version,
                "state_schema_version": self.state_schema_version,
            },
            "fingerprint": {
                "source_state_sha256": self.source_state_sha256,
                "semantic_state_sha256": self.semantic_state_sha256,
            },
        }


class ProjectDNAReader:
    """Read-only Project DNA reader backed by controller state."""

    def __init__(
        self,
        control_center_root: Path | str | None = None,
    ) -> None:
        if control_center_root is None:
            # File location:
            # .../REOS_CONTROL_CENTER/
            #     AUTONOMY_ENGINE/continuity/acrl/
            #     T01_Project_DNA/project_dna.py
            self.root = Path(__file__).resolve().parents[4]
        else:
            self.root = Path(control_center_root).resolve()

        self.state_path = self.root / "data" / "state.json"

    @staticmethod
    def _read_state(path: Path) -> dict[str, Any]:
        """Read authoritative state as a JSON object."""

        if not path.exists():
            raise ProjectDNASourceError(
                f"Authoritative state not found: {path}"
            )

        if not path.is_file():
            raise ProjectDNASourceError(
                f"Authoritative state path is not a file: {path}"
            )

        try:
            raw = path.read_text(encoding="utf-8-sig")
            value = json.loads(raw)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ProjectDNASourceError(
                f"Unable to read authoritative state: {path}"
            ) from exc

        if not isinstance(value, dict):
            raise ProjectDNASourceError(
                "Authoritative state must contain a JSON object."
            )

        return value

    @staticmethod
    def _required_string(
        mapping: Mapping[str, Any],
        key: str,
        section: str,
    ) -> str:
        value = mapping.get(key)

        if not isinstance(value, str) or not value.strip():
            raise ProjectDNAIntegrityError(
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
            raise ProjectDNAIntegrityError(
                f"{section}.{key} must be boolean."
            )

        return value

    @staticmethod
    def _required_int(
        mapping: Mapping[str, Any],
        key: str,
        section: str,
    ) -> int:
        value = mapping.get(key)

        if isinstance(value, bool) or not isinstance(value, int):
            raise ProjectDNAIntegrityError(
                f"{section}.{key} must be an integer."
            )

        return value

    @staticmethod
    def _source_sha256(path: Path) -> str:
        """Hash the exact authoritative state bytes."""

        try:
            return hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError as exc:
            raise ProjectDNASourceError(
                f"Unable to fingerprint authoritative state: {path}"
            ) from exc

    @staticmethod
    def _semantic_sha256(state: Mapping[str, Any]) -> str:
        """Hash canonical JSON semantics independent of formatting."""

        try:
            canonical = json.dumps(
                state,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise ProjectDNAIntegrityError(
                "Unable to produce semantic Project DNA fingerprint."
            ) from exc

        return hashlib.sha256(canonical).hexdigest()

    def read(self) -> ProjectDNA:
        """Build Project DNA exclusively from authoritative state."""

        state = self._read_state(self.state_path)

        meta = state.get("meta")
        constitution = state.get("constitution")
        project = state.get("project")
        phases = state.get("phases")

        if not isinstance(meta, Mapping):
            raise ProjectDNAIntegrityError(
                "state.meta must be an object."
            )

        if not isinstance(constitution, Mapping):
            raise ProjectDNAIntegrityError(
                "state.constitution must be an object."
            )

        if not isinstance(project, Mapping):
            raise ProjectDNAIntegrityError(
                "state.project must be an object."
            )

        if not isinstance(phases, Mapping):
            raise ProjectDNAIntegrityError(
                "state.phases must be an object."
            )

        canonical_source = self._required_string(
            constitution,
            "canonical_source",
            "constitution",
        )

        if canonical_source != "data/state.json":
            raise ProjectDNAIntegrityError(
                "Project DNA requires data/state.json as canonical source."
            )

        architecture_before_code = self._required_bool(
            constitution,
            "architecture_before_code",
            "constitution",
        )

        single_source_of_truth = self._required_bool(
            constitution,
            "single_source_of_truth",
            "constitution",
        )

        micro_modular = self._required_bool(
            constitution,
            "micro_modular",
            "constitution",
        )

        no_duplicate_logic = self._required_bool(
            constitution,
            "no_duplicate_logic",
            "constitution",
        )

        no_silent_architecture_changes = self._required_bool(
            constitution,
            "no_silent_architecture_changes",
            "constitution",
        )

        chat_history_is_not_project_memory = self._required_bool(
            constitution,
            "chat_history_is_not_project_memory",
            "constitution",
        )

        if not chat_history_is_not_project_memory:
            raise ProjectDNAIntegrityError(
                "Chat history cannot be an authoritative Project DNA source."
            )

        if not single_source_of_truth:
            raise ProjectDNAIntegrityError(
                "Project DNA requires single_source_of_truth=true."
            )

        if not architecture_before_code:
            raise ProjectDNAIntegrityError(
                "Project DNA requires architecture_before_code=true."
            )

        if not no_duplicate_logic:
            raise ProjectDNAIntegrityError(
                "Project DNA requires no_duplicate_logic=true."
            )

        if not no_silent_architecture_changes:
            raise ProjectDNAIntegrityError(
                "Project DNA requires no_silent_architecture_changes=true."
            )

        return ProjectDNA(
            product=self._required_string(meta, "product", "meta"),
            project_name=self._required_string(
                project,
                "name",
                "project",
            ),
            project_type=self._required_string(
                project,
                "type",
                "project",
            ),
            north_star=self._required_string(
                project,
                "north_star",
                "project",
            ),
            operating_principle=self._required_string(
                project,
                "operating_principle",
                "project",
            ),
            controller_version=self._required_string(
                meta,
                "control_center_version",
                "meta",
            ),
            state_schema_version=self._required_int(
                meta,
                "schema_version",
                "meta",
            ),
            phase=self._required_string(
                phases,
                "current",
                "phases",
            ),
            canonical_source=canonical_source,
            architecture_before_code=architecture_before_code,
            single_source_of_truth=single_source_of_truth,
            micro_modular=micro_modular,
            no_duplicate_logic=no_duplicate_logic,
            no_silent_architecture_changes=no_silent_architecture_changes,
            chat_history_is_not_project_memory=(
                chat_history_is_not_project_memory
            ),
            source_state_sha256=self._source_sha256(self.state_path),
            semantic_state_sha256=self._semantic_sha256(state),
        )


def read_project_dna(
    control_center_root: Path | str | None = None,
) -> ProjectDNA:
    """Convenience API for reading authoritative Project DNA."""

    return ProjectDNAReader(control_center_root).read()


__all__ = [
    "DNA_SCHEMA_VERSION",
    "ProjectDNA",
    "ProjectDNAError",
    "ProjectDNAIntegrityError",
    "ProjectDNASourceError",
    "ProjectDNAReader",
    "read_project_dna",
]