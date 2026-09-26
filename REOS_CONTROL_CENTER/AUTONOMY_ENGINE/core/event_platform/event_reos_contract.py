from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping, Any


class REOSEventContractError(ValueError):
    """CORE-002 / REOS integration contract violation."""


@dataclass(frozen=True, slots=True)
class REOSIntegrationContract:
    """
    Boundary between CORE-002 and REOS Control Center.

    CORE-002 can discover/verify execution context,
    but cannot mutate canonical Control Center state.
    """

    gate_name: str
    task_name: str
    verification_command: str
    canonical_state_owned_externally: bool = True

    def __post_init__(self) -> None:
        for name, value in (
            ("gate_name", self.gate_name),
            ("task_name", self.task_name),
            (
                "verification_command",
                self.verification_command,
            ),
        ):
            if not isinstance(value, str):
                raise TypeError(
                    f"{name} must be string"
                )

            if not value.strip():
                raise ValueError(
                    f"{name} cannot be empty"
                )

        if not self.canonical_state_owned_externally:
            raise REOSEventContractError(
                "CORE-002 cannot own Control Center state"
            )


class REOSIntegrationBoundary:
    """
    Read/verify-only integration boundary.
    """

    def __init__(
        self,
        *,
        discover_contract: Callable[
            [],
            Mapping[str, Any],
        ],
        verify: Callable[
            [str],
            bool,
        ],
    ) -> None:
        self._discover_contract = (
            discover_contract
        )
        self._verify = verify

    def discover(
        self,
    ) -> Mapping[str, Any]:
        result = self._discover_contract()

        if not isinstance(
            result,
            Mapping,
        ):
            raise REOSEventContractError(
                "REOS contract discovery must return mapping"
            )

        return dict(result)

    def verify(
        self,
        command: str,
    ) -> bool:
        if not isinstance(
            command,
            str,
        ) or not command.strip():
            raise ValueError(
                "verification command is required"
            )

        return bool(
            self._verify(command)
        )


__all__ = [
    "REOSEventContractError",
    "REOSIntegrationContract",
    "REOSIntegrationBoundary",
]
