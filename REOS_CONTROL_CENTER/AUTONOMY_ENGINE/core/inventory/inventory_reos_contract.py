"""
CORE-004 T10 — REOS Integration Contract

Owns:
- Control Center authority boundary
- canonical-state non-ownership
- execution compatibility contract
- gate/task discoverability
- verification contract
- explicit prohibition of autonomous project-state mutation

Does NOT own:
- Control Center state
- state.json
- gate transitions
- task approval
- execution authorization
- mutation execution
- repository mutation
- lifecycle
- availability
- ACRL continuity
- event transport

REOS_CONTROL_CENTER remains the canonical project-state authority.

This module describes what CORE-004 is allowed to discover, verify and
hand off. It does not mutate canonical REOS state.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Any, Callable, Mapping


class InventoryREOSContractError(
    ValueError
):
    """Base CORE-004 -> REOS integration error."""


class InventoryREOSAuthorityError(
    InventoryREOSContractError
):
    """Raised when canonical REOS authority is violated."""


class InventoryREOSVerificationError(
    InventoryREOSContractError
):
    """Raised when REOS verification contract is invalid."""


class InventoryREOSExecutionError(
    InventoryREOSContractError
):
    """Raised when execution compatibility is invalid."""


class REOSVerificationMode(str, Enum):
    READ_ONLY = "READ_ONLY"
    VERIFY_ONLY = "VERIFY_ONLY"


@dataclass(frozen=True, slots=True)
class InventoryREOSContract:
    """
    Immutable integration declaration between CORE-004 and REOS.

    The contract is intentionally explicit about ownership:
        canonical_state_owner = REOS_CONTROL_CENTER

    CORE-004 may describe its gate/task and verification expectations,
    but it cannot claim ownership of the canonical state.
    """

    gate_name: str
    task_name: str
    verification_command: str
    state_owner: str = "REOS_CONTROL_CENTER"
    canonical_state_owned_externally: bool = True
    autonomous_state_mutation_allowed: bool = False
    verification_mode: REOSVerificationMode = (
        REOSVerificationMode.VERIFY_ONLY
    )
    schema_version: int = 1

    def __post_init__(self) -> None:
        for field_name in (
            "gate_name",
            "task_name",
            "verification_command",
            "state_owner",
        ):
            value = getattr(
                self,
                field_name,
            )

            if not isinstance(
                value,
                str,
            ):
                raise InventoryREOSContractError(
                    f"{field_name} must be string."
                )

            if not value.strip():
                raise InventoryREOSContractError(
                    f"{field_name} cannot be empty."
                )

        if self.state_owner != "REOS_CONTROL_CENTER":
            raise InventoryREOSAuthorityError(
                "CORE-004 canonical state owner must remain "
                "REOS_CONTROL_CENTER."
            )

        if not self.canonical_state_owned_externally:
            raise InventoryREOSAuthorityError(
                "CORE-004 cannot own canonical Control Center state."
            )

        if self.autonomous_state_mutation_allowed:
            raise InventoryREOSAuthorityError(
                "CORE-004 cannot autonomously mutate REOS state."
            )

        if not isinstance(
            self.verification_mode,
            REOSVerificationMode,
        ):
            raise InventoryREOSContractError(
                "verification_mode is invalid."
            )

        if (
            not isinstance(
                self.schema_version,
                int,
            )
            or self.schema_version < 1
        ):
            raise InventoryREOSContractError(
                "schema_version must be >= 1."
            )

    @property
    def contract_key(self) -> tuple[str, str]:
        return (
            self.gate_name,
            self.task_name,
        )

    @property
    def fingerprint(self) -> str:
        payload = {
            "gate_name": self.gate_name,
            "task_name": self.task_name,
            "verification_command": (
                self.verification_command
            ),
            "state_owner": self.state_owner,
            "canonical_state_owned_externally": (
                self.canonical_state_owned_externally
            ),
            "autonomous_state_mutation_allowed": (
                self.autonomous_state_mutation_allowed
            ),
            "verification_mode": (
                self.verification_mode.value
            ),
            "schema_version": self.schema_version,
        }

        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

    def assert_execution_compatible(
        self,
        *,
        command: str,
        read_only: bool,
    ) -> None:
        if not isinstance(
            command,
            str,
        ) or not command.strip():
            raise InventoryREOSExecutionError(
                "Execution command is required."
            )

        if not read_only:
            raise InventoryREOSExecutionError(
                "CORE-004 REOS integration cannot authorize "
                "state-mutating execution."
            )

        if command != self.verification_command:
            raise InventoryREOSExecutionError(
                "Command is not the declared CORE-004 "
                "verification command."
            )

    def assert_authority_boundary(self) -> None:
        if self.state_owner != "REOS_CONTROL_CENTER":
            raise InventoryREOSAuthorityError(
                "Invalid canonical state owner."
            )

        if not self.canonical_state_owned_externally:
            raise InventoryREOSAuthorityError(
                "CORE-004 must not own canonical project state."
            )

        if self.autonomous_state_mutation_allowed:
            raise InventoryREOSAuthorityError(
                "Autonomous REOS state mutation is forbidden."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_name": self.gate_name,
            "task_name": self.task_name,
            "verification_command": (
                self.verification_command
            ),
            "state_owner": self.state_owner,
            "canonical_state_owned_externally": (
                self.canonical_state_owned_externally
            ),
            "autonomous_state_mutation_allowed": (
                self.autonomous_state_mutation_allowed
            ),
            "verification_mode": (
                self.verification_mode.value
            ),
            "schema_version": self.schema_version,
            "fingerprint": self.fingerprint,
        }


@dataclass(frozen=True, slots=True)
class InventoryREOSDiscovery:
    """
    Read-only snapshot returned by an external REOS discovery adapter.
    """

    gate_name: str
    task_name: str
    gate_status: str
    task_status: str
    canonical_state_owner: str
    verification_command: str

    def __post_init__(self) -> None:
        for field_name in (
            "gate_name",
            "task_name",
            "gate_status",
            "task_status",
            "canonical_state_owner",
            "verification_command",
        ):
            value = getattr(
                self,
                field_name,
            )

            if not isinstance(
                value,
                str,
            ) or not value.strip():
                raise InventoryREOSContractError(
                    f"{field_name} must be non-empty string."
                )

        if (
            self.canonical_state_owner
            != "REOS_CONTROL_CENTER"
        ):
            raise InventoryREOSAuthorityError(
                "Discovered canonical state owner is invalid."
            )

    def to_dict(self) -> dict[str, str]:
        return {
            "gate_name": self.gate_name,
            "task_name": self.task_name,
            "gate_status": self.gate_status,
            "task_status": self.task_status,
            "canonical_state_owner": (
                self.canonical_state_owner
            ),
            "verification_command": (
                self.verification_command
            ),
        }


class InventoryREOSIntegrationBoundary:
    """
    Read / verify-only adapter boundary.

    External callbacks own actual discovery and verification.

    No method in this class mutates Control Center state.
    """

    def __init__(
        self,
        *,
        discover: Callable[
            [],
            Mapping[str, Any],
        ],
        verify: Callable[
            [str],
            bool,
        ],
    ) -> None:
        if not callable(discover):
            raise InventoryREOSContractError(
                "discover must be callable."
            )

        if not callable(verify):
            raise InventoryREOSContractError(
                "verify must be callable."
            )

        self._discover = discover
        self._verify = verify

    def discover_contract(
        self,
    ) -> InventoryREOSDiscovery:
        result = self._discover()

        if not isinstance(
            result,
            Mapping,
        ):
            raise InventoryREOSContractError(
                "REOS discovery must return mapping."
            )

        required = {
            "gate_name",
            "task_name",
            "gate_status",
            "task_status",
            "canonical_state_owner",
            "verification_command",
        }

        missing = required - set(
            result
        )

        if missing:
            raise InventoryREOSContractError(
                "REOS discovery missing fields: "
                f"{sorted(missing)}"
            )

        return InventoryREOSDiscovery(
            gate_name=str(
                result["gate_name"]
            ),
            task_name=str(
                result["task_name"]
            ),
            gate_status=str(
                result["gate_status"]
            ),
            task_status=str(
                result["task_status"]
            ),
            canonical_state_owner=str(
                result["canonical_state_owner"]
            ),
            verification_command=str(
                result["verification_command"]
            ),
        )

    def verify(
        self,
        command: str,
    ) -> bool:
        if not isinstance(
            command,
            str,
        ) or not command.strip():
            raise InventoryREOSVerificationError(
                "Verification command is required."
            )

        return bool(
            self._verify(
                command
            )
        )


def validate_reos_discovery(
    contract: InventoryREOSContract,
    discovery: InventoryREOSDiscovery,
) -> None:
    """
    Verify that externally discovered REOS context agrees with the
    declared CORE-004 contract.
    """
    if contract.gate_name != discovery.gate_name:
        raise InventoryREOSVerificationError(
            "Discovered gate does not match CORE-004 contract."
        )

    if contract.task_name != discovery.task_name:
        raise InventoryREOSVerificationError(
            "Discovered task does not match CORE-004 contract."
        )

    if (
        contract.verification_command
        != discovery.verification_command
    ):
        raise InventoryREOSVerificationError(
            "Discovered verification command does not "
            "match CORE-004 contract."
        )

    if (
        discovery.canonical_state_owner
        != "REOS_CONTROL_CENTER"
    ):
        raise InventoryREOSAuthorityError(
            "REOS canonical state owner mismatch."
        )

    contract.assert_authority_boundary()


__all__ = [
    "InventoryREOSContractError",
    "InventoryREOSAuthorityError",
    "InventoryREOSVerificationError",
    "InventoryREOSExecutionError",
    "REOSVerificationMode",
    "InventoryREOSContract",
    "InventoryREOSDiscovery",
    "InventoryREOSIntegrationBoundary",
    "validate_reos_discovery",
]
