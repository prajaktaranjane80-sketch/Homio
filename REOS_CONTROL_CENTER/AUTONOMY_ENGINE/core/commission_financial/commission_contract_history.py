from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from .commission_contract import (
    CommissionContract,
    CommissionContractConflictError,
    CommissionContractValidationError,
)


class CommissionContractHistoryError(
    ValueError
):
    """Base historical-contract error."""


class CommissionContractHistoryOrderError(
    CommissionContractHistoryError
):
    """Historical versions are not strictly ordered."""


class CommissionContractHistoryIdentityError(
    CommissionContractHistoryError
):
    """Historical versions do not share one identity."""


@dataclass(frozen=True, slots=True)
class CommissionContractHistory:
    """Immutable version chain for one commission contract.

    This object is a pure domain value.

    It does not:
    - persist contracts,
    - replace a database,
    - mutate Control Center state,
    - publish events,
    - execute governance,
    - execute calculation,
    - execute settlement,
    - own ACRL recovery.
    """

    contracts: tuple[
        CommissionContract,
        ...]

    def __post_init__(self) -> None:
        contracts = tuple(
            self.contracts
        )

        if not contracts:
            raise CommissionContractHistoryError(
                "At least one contract version is required."
            )

        if any(
            not isinstance(
                contract,
                CommissionContract,
            )
            for contract in contracts
        ):
            raise CommissionContractHistoryError(
                "History contains invalid contract values."
            )

        identity = contracts[0].identity_key

        for contract in contracts:
            if contract.identity_key != identity:
                raise CommissionContractHistoryIdentityError(
                    "All history entries must share the same "
                    "tenant and commission identity."
                )

        versions = [
            contract.contract_version
            for contract in contracts
        ]

        if versions != sorted(versions):
            raise CommissionContractHistoryOrderError(
                "Contract versions must be ascending."
            )

        if len(
            versions
        ) != len(
            set(versions)
        ):
            raise CommissionContractHistoryOrderError(
                "Duplicate contract versions are forbidden."
            )

        expected = list(
            range(
                versions[0],
                versions[-1] + 1,
            )
        )

        if versions != expected:
            raise CommissionContractHistoryOrderError(
                "Contract history cannot contain version gaps."
            )

        for previous, current in zip(
            contracts,
            contracts[1:],
        ):
            if (
                previous.effective_to
                is not None
                and current.effective_from
                < previous.effective_to
            ):
                raise CommissionContractHistoryOrderError(
                    "Historical contract effective windows overlap."
                )

            if (
                current.effective_from
                < previous.effective_from
            ):
                raise CommissionContractHistoryOrderError(
                    "Historical contract effective dates "
                    "must be chronological."
                )

        object.__setattr__(
            self,
            "contracts",
            contracts,
        )

    @classmethod
    def from_contract(
        cls,
        contract: CommissionContract,
    ) -> "CommissionContractHistory":
        return cls(
            contracts=(contract,)
        )

    @property
    def tenant_id(self) -> str:
        return self.contracts[0].tenant_id

    @property
    def commission_id(self) -> str:
        return self.contracts[0].commission_id

    @property
    def identity_key(self) -> tuple[str, str]:
        return (
            self.tenant_id,
            self.commission_id,
        )

    @property
    def latest(self) -> CommissionContract:
        return self.contracts[-1]

    @property
    def earliest(self) -> CommissionContract:
        return self.contracts[0]

    @property
    def version_numbers(self) -> tuple[int, ...]:
        return tuple(
            contract.contract_version
            for contract in self.contracts
        )

    def append(
        self,
        contract: CommissionContract,
    ) -> "CommissionContractHistory":
        if not isinstance(
            contract,
            CommissionContract,
        ):
            raise CommissionContractHistoryError(
                "contract must be CommissionContract."
            )

        if contract.identity_key != self.identity_key:
            raise CommissionContractHistoryIdentityError(
                "Contract identity does not match history."
            )

        expected_version = (
            self.latest.contract_version + 1
        )

        if (
            contract.contract_version
            != expected_version
        ):
            raise CommissionContractHistoryOrderError(
                "New contract version must be exactly "
                f"{expected_version}."
            )

        if (
            self.latest.effective_to
            is None
        ):
            raise CommissionContractHistoryOrderError(
                "Previous active term must have an end "
                "before a subsequent version begins."
            )

        if (
            contract.effective_from
            < self.latest.effective_to
        ):
            raise CommissionContractHistoryOrderError(
                "New contract begins before previous term ends."
            )

        return CommissionContractHistory(
            contracts=(
                self.contracts
                + (contract,)
            )
        )

    def find_version(
        self,
        version: int,
    ) -> CommissionContract:
        matches = tuple(
            contract
            for contract in self.contracts
            if contract.contract_version == version
        )

        if len(matches) != 1:
            raise CommissionContractValidationError(
                "Requested commission contract version "
                "does not exist."
            )

        return matches[0]

    def effective_at(
        self,
        at: datetime,
    ) -> CommissionContract:
        matches = tuple(
            contract
            for contract in self.contracts
            if contract.is_effective_at(
                at
            )
        )

        if len(matches) != 1:
            raise CommissionContractValidationError(
                "No unique active commission contract "
                "exists at the requested time."
            )

        return matches[0]

    def assert_compatible(
        self,
        other: "CommissionContractHistory",
    ) -> None:
        if not isinstance(
            other,
            CommissionContractHistory,
        ):
            raise CommissionContractConflictError(
                "other must be CommissionContractHistory."
            )

        if self.identity_key != other.identity_key:
            raise CommissionContractConflictError(
                "History identities differ."
            )

        if (
            self.version_numbers
            != other.version_numbers
        ):
            raise CommissionContractConflictError(
                "History version sequences differ."
            )

        for left, right in zip(
            self.contracts,
            other.contracts,
        ):
            left.assert_compatible(
                right
            )

    def to_dict(
        self,
    ) -> dict[str, object]:
        return {
            "tenant_id": self.tenant_id,
            "commission_id": self.commission_id,
            "versions": [
                contract.to_dict()
                for contract in self.contracts
            ],
        }


def build_contract_history(
    contracts: Iterable[
        CommissionContract
    ],
) -> CommissionContractHistory:
    """Build and validate an immutable history chain."""

    return CommissionContractHistory(
        contracts=tuple(
            contracts
        )
    )


__all__ = [
    "CommissionContractHistoryError",
    "CommissionContractHistoryOrderError",
    "CommissionContractHistoryIdentityError",
    "CommissionContractHistory",
    "build_contract_history",
]
