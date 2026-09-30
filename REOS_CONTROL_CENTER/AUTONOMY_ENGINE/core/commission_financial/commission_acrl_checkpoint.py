from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping, Any

from .commission_acrl_contract import (
    ACRLCheckpointCompatibility,
    CommissionACRLValidationError,
)


class CommissionACRLCheckpointError(ValueError):
    """CORE-008 / ACRL checkpoint compatibility error."""


@dataclass(frozen=True, slots=True)
class FinancialCheckpointBinding:
    """
    Financial binding to an existing ACRL checkpoint.

    No checkpoint engine is created here.
    """

    tenant_id: str
    commission_id: str
    checkpoint: ACRLCheckpointCompatibility

    def __post_init__(self) -> None:
        for name, value in (
            ("tenant_id", self.tenant_id),
            ("commission_id", self.commission_id),
        ):
            if not isinstance(value, str) or not value.strip():
                raise CommissionACRLValidationError(
                    f"{name} cannot be empty"
                )

            object.__setattr__(
                self,
                name,
                value.strip(),
            )

        if not isinstance(
            self.checkpoint,
            ACRLCheckpointCompatibility,
        ):
            raise CommissionACRLCheckpointError(
                "checkpoint must be ACRLCheckpointCompatibility"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "commission_id": self.commission_id,
            "checkpoint": self.checkpoint.to_dict(),
        }


class CommissionACRLCheckpointAdapter:
    """
    Read-only compatibility adapter for an existing ACRL checkpoint service.
    """

    def __init__(
        self,
        validate_checkpoint: Callable[
            [ACRLCheckpointCompatibility],
            bool,
        ],
    ) -> None:
        if not callable(validate_checkpoint):
            raise TypeError(
                "validate_checkpoint must be callable"
            )

        self._validate_checkpoint = validate_checkpoint

    def validate(
        self,
        binding: FinancialCheckpointBinding,
    ) -> bool:
        if not isinstance(
            binding,
            FinancialCheckpointBinding,
        ):
            raise TypeError(
                "binding must be FinancialCheckpointBinding"
            )

        return bool(
            self._validate_checkpoint(
                binding.checkpoint
            )
        )


__all__ = [
    "CommissionACRLCheckpointError",
    "CommissionACRLCheckpointAdapter",
    "FinancialCheckpointBinding",
]
