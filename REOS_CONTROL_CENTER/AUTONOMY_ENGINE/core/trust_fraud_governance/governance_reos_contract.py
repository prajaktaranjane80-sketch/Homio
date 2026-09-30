"""CORE-007 — REOS Control Center integration contract.

CORE-007 does not own:
- REOS_CONTROL_CENTER state,
- state.json,
- gate approval,
- task advancement.

This module consumes the existing CORE-002 REOS integration boundary
so that CORE-007 can discover and verify execution context without
creating a second Control Center.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from ..event_platform.event_reos_contract import (
    REOSIntegrationBoundary,
    REOSIntegrationContract,
    REOSEventContractError,
)


CORE007_REOS_CONTRACT_VERSION = "1.0"


class GovernanceREOSContractError(
    REOSEventContractError
):
    """CORE-007 to REOS contract violation."""


@dataclass(frozen=True, slots=True)
class GovernanceREOSExecutionContext:
    """Read-only execution context discovered from REOS."""

    gate_name: str
    task_name: str
    subtask_name: str

    verification_command: str

    canonical_state_reference: str = (
        "REOS_CONTROL_CENTER/data/state.json"
    )

    control_center_owned: bool = True
    contract_version: str = (
        CORE007_REOS_CONTRACT_VERSION
    )

    def __post_init__(self) -> None:
        for name in (
            "gate_name",
            "task_name",
            "subtask_name",
            "verification_command",
            "canonical_state_reference",
        ):
            value = getattr(self, name)

            if not isinstance(
                value,
                str,
            ) or not value.strip():
                raise GovernanceREOSContractError(
                    f"{name} must be non-empty text."
                )

        if not self.control_center_owned:
            raise GovernanceREOSContractError(
                "CORE-007 cannot become Control Center authority."
            )

        if self.contract_version != (
            CORE007_REOS_CONTRACT_VERSION
        ):
            raise GovernanceREOSContractError(
                "Unsupported CORE-007 REOS contract version."
            )


class GovernanceREOSBoundary:
    """Read/verify-only CORE-007 → REOS adapter."""

    def __init__(
        self,
        *,
        discover_contract,
        verify,
    ) -> None:
        self._boundary = REOSIntegrationBoundary(
            discover_contract=discover_contract,
            verify=verify,
        )

    def discover(
        self,
    ) -> GovernanceREOSExecutionContext:
        raw = self._boundary.discover()

        gate_name = self._read_required(
            raw,
            "gate_name",
        )
        task_name = self._read_required(
            raw,
            "task_name",
        )
        subtask_name = self._read_required(
            raw,
            "subtask_name",
        )
        verification_command = self._read_required(
            raw,
            "verification_command",
        )

        control_center_owned = raw.get(
            "control_center_owned",
            True,
        )

        if not isinstance(
            control_center_owned,
            bool,
        ):
            raise GovernanceREOSContractError(
                "control_center_owned must be boolean."
            )

        state_reference = raw.get(
            "canonical_state_reference",
            "REOS_CONTROL_CENTER/data/state.json",
        )

        return GovernanceREOSExecutionContext(
            gate_name=gate_name,
            task_name=task_name,
            subtask_name=subtask_name,
            verification_command=(
                verification_command
            ),
            canonical_state_reference=(
                state_reference
            ),
            control_center_owned=(
                control_center_owned
            ),
        )

    def verify(
        self,
        command: str,
    ) -> bool:
        return self._boundary.verify(command)

    def verify_current_subtask(
        self,
        context: GovernanceREOSExecutionContext,
    ) -> bool:
        return self.verify(
            context.verification_command
        )

    @staticmethod
    def build_contract(
        *,
        gate_name: str,
        task_name: str,
        verification_command: str,
    ) -> REOSIntegrationContract:
        """Build the shared CORE-002-compatible REOS contract."""

        return REOSIntegrationContract(
            gate_name=gate_name,
            task_name=task_name,
            verification_command=(
                verification_command
            ),
            canonical_state_owned_externally=True,
        )

    @staticmethod
    def _read_required(
        mapping: Mapping[str, Any],
        key: str,
    ) -> str:
        value = mapping.get(key)

        if (
            not isinstance(value, str)
            or not value.strip()
        ):
            raise GovernanceREOSContractError(
                f"REOS discovery field '{key}' "
                "must be non-empty text."
            )

        return value.strip()


__all__ = [
    "CORE007_REOS_CONTRACT_VERSION",
    "GovernanceREOSContractError",
    "GovernanceREOSExecutionContext",
    "GovernanceREOSBoundary",
]
