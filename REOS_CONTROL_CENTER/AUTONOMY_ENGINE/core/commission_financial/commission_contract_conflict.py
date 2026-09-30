from __future__ import annotations

from dataclasses import dataclass

from .commission_contract import (
    CommissionContract,
    CommissionContractConflictError,
)
from .commission_contract_terms import (
    compare_commission_terms,
)


class CommissionContractDuplicateError(
    CommissionContractConflictError
):
    """A duplicate contract command conflicts with existing terms."""


class CommissionContractVersionConflictError(
    CommissionContractConflictError
):
    """A version carries conflicting immutable terms."""


@dataclass(frozen=True, slots=True)
class CommissionContractConflictReport:
    """Deterministic contract conflict result."""

    conflict: bool
    reason: str | None
    same_identity: bool
    same_version: bool
    same_terms: bool

    def __post_init__(self) -> None:
        if self.conflict and not self.reason:
            raise ValueError(
                "Conflict requires a reason."
            )

        if not self.conflict and self.reason is not None:
            raise ValueError(
                "Non-conflict cannot carry a reason."
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "conflict": self.conflict,
            "reason": self.reason,
            "same_identity": self.same_identity,
            "same_version": self.same_version,
            "same_terms": self.same_terms,
        }


def detect_contract_conflict(
    existing: CommissionContract,
    incoming: CommissionContract,
) -> CommissionContractConflictReport:
    """Detect immutable term conflicts.

    This function never overwrites or mutates a contract.
    """

    comparison = compare_commission_terms(
        existing,
        incoming,
    )

    if not comparison.same_identity:
        return CommissionContractConflictReport(
            conflict=False,
            reason=None,
            same_identity=False,
            same_version=(
                comparison.same_version
            ),
            same_terms=(
                comparison.same_terms
            ),
        )

    if (
        comparison.same_version
        and comparison.same_terms
    ):
        return CommissionContractConflictReport(
            conflict=False,
            reason=None,
            same_identity=True,
            same_version=True,
            same_terms=True,
        )

    if (
        comparison.same_version
        and not comparison.same_terms
    ):
        return CommissionContractConflictReport(
            conflict=True,
            reason=(
                "Same commission identity and contract version "
                "contain conflicting immutable terms."
            ),
            same_identity=True,
            same_version=True,
            same_terms=False,
        )

    if (
        not comparison.same_version
        and not comparison.same_terms
    ):
        return CommissionContractConflictReport(
            conflict=False,
            reason=None,
            same_identity=True,
            same_version=False,
            same_terms=False,
        )

    return CommissionContractConflictReport(
        conflict=False,
        reason=None,
        same_identity=True,
        same_version=False,
        same_terms=True,
    )


def assert_no_contract_conflict(
    existing: CommissionContract,
    incoming: CommissionContract,
) -> None:
    report = detect_contract_conflict(
        existing,
        incoming,
    )

    if report.conflict:
        raise CommissionContractVersionConflictError(
            report.reason
        )


__all__ = [
    "CommissionContractDuplicateError",
    "CommissionContractVersionConflictError",
    "CommissionContractConflictReport",
    "detect_contract_conflict",
    "assert_no_contract_conflict",
]
