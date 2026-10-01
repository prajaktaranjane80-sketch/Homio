from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping, Any


CORE008_REOS_AUTHORITY = (
    "REOS_CONTROL_CENTER"
)

CORE008_CANONICAL_STATE = (
    "data/state.json"
)


class CommissionREOSContractError(ValueError):
    """CORE-008 / REOS integration-contract error."""


@dataclass(frozen=True, slots=True)
class CommissionREOSIntegrationContract:
    gate_id: str
    gate_name: str
    task_name: str
    verification_command: str

    canonical_state_path: str = (
        CORE008_CANONICAL_STATE
    )

    canonical_state_owned_externally: bool = True
    autonomous_project_state_mutation_allowed: bool = False

    def __post_init__(self) -> None:
        for field in (
            "gate_id",
            "gate_name",
            "task_name",
            "verification_command",
        ):
            value = getattr(self, field)

            if (
                not isinstance(
                    value,
                    str,
                )
                or not value.strip()
            ):
                raise CommissionREOSContractError(
                    f"{field} cannot be empty."
                )

        if (
            self.canonical_state_path
            != CORE008_CANONICAL_STATE
        ):
            raise CommissionREOSContractError(
                "CORE-008 canonical state must remain data/state.json."
            )

        if not self.canonical_state_owned_externally:
            raise CommissionREOSContractError(
                "CORE-008 cannot own Control Center state."
            )

        if self.autonomous_project_state_mutation_allowed:
            raise CommissionREOSContractError(
                "CORE-008 cannot autonomously mutate project state."
            )


@dataclass(frozen=True, slots=True)
class CommissionREOSExecutionReference:
    gate_id: str
    task_name: str
    execution_reference: str
    verification_reference: str

    def __post_init__(self) -> None:
        for field in (
            "gate_id",
            "task_name",
            "execution_reference",
            "verification_reference",
        ):
            value = getattr(self, field)

            if (
                not isinstance(
                    value,
                    str,
                )
                or not value.strip()
            ):
                raise CommissionREOSContractError(
                    f"{field} cannot be empty."
                )

            object.__setattr__(
                self,
                field,
                value.strip(),
            )


class CommissionREOSBoundary:
    """
    Read/verify-only CORE-008 integration boundary.

    Control Center remains the authority for:
        gate state
        task state
        verification
        approval
        canonical project state
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
            raise TypeError(
                "discover must be callable."
            )

        if not callable(verify):
            raise TypeError(
                "verify must be callable."
            )

        self._discover = discover
        self._verify = verify

    def discover_contract(
        self,
    ) -> dict[str, Any]:
        result = self._discover()

        if not isinstance(
            result,
            Mapping,
        ):
            raise CommissionREOSContractError(
                "REOS discovery must return a mapping."
            )

        return dict(result)

    def verify(
        self,
        verification_command: str,
    ) -> bool:
        if (
            not isinstance(
                verification_command,
                str,
            )
            or not verification_command.strip()
        ):
            raise CommissionREOSContractError(
                "verification_command is required."
            )

        return bool(
            self._verify(
                verification_command
            )
        )


def validate_reos_contract(
    contract: CommissionREOSIntegrationContract,
) -> None:
    if not isinstance(
        contract,
        CommissionREOSIntegrationContract,
    ):
        raise CommissionREOSContractError(
            "Invalid CORE-008 REOS integration contract."
        )

    if (
        contract.canonical_state_path
        != CORE008_CANONICAL_STATE
    ):
        raise CommissionREOSContractError(
            "Invalid canonical-state path."
        )

    if not contract.canonical_state_owned_externally:
        raise CommissionREOSContractError(
            "REOS Control Center state cannot be owned by CORE-008."
        )

    if contract.autonomous_project_state_mutation_allowed:
        raise CommissionREOSContractError(
            "Autonomous project-state mutation is prohibited."
        )


__all__ = [
    "CORE008_CANONICAL_STATE",
    "CORE008_REOS_AUTHORITY",
    "CommissionREOSBoundary",
    "CommissionREOSContractError",
    "CommissionREOSExecutionReference",
    "CommissionREOSIntegrationContract",
    "validate_reos_contract",
]
