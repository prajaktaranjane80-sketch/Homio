from __future__ import annotations

from dataclasses import dataclass

from .commission_acrl_reconstruction import (
    FinancialReconstructionResult,
)


class CommissionACRLConflictError(ValueError):
    """CORE-008 ACRL reconstruction conflict."""


@dataclass(frozen=True, slots=True)
class CommissionACRLConflictResult:
    conflict: bool
    same_subject: bool
    same_fingerprint: bool
    reason: str


def compare_reconstruction_results(
    left: FinancialReconstructionResult,
    right: FinancialReconstructionResult,
) -> CommissionACRLConflictResult:
    if not isinstance(
        left,
        FinancialReconstructionResult,
    ):
        raise TypeError(
            "left must be FinancialReconstructionResult"
        )

    if not isinstance(
        right,
        FinancialReconstructionResult,
    ):
        raise TypeError(
            "right must be FinancialReconstructionResult"
        )

    same_subject = (
        left.request.tenant_id
        == right.request.tenant_id
        and left.request.commission_id
        == right.request.commission_id
        and left.request.subject
        == right.request.subject
    )

    same_fingerprint = (
        left.result_fingerprint
        == right.result_fingerprint
    )

    if not same_subject:
        return CommissionACRLConflictResult(
            conflict=False,
            same_subject=False,
            same_fingerprint=same_fingerprint,
            reason="different reconstruction subject",
        )

    if same_fingerprint:
        return CommissionACRLConflictResult(
            conflict=False,
            same_subject=True,
            same_fingerprint=True,
            reason="identical deterministic reconstruction",
        )

    return CommissionACRLConflictResult(
        conflict=True,
        same_subject=True,
        same_fingerprint=False,
        reason=(
            "same financial reconstruction subject produced "
            "different deterministic results"
        ),
    )


def assert_no_reconstruction_conflict(
    left: FinancialReconstructionResult,
    right: FinancialReconstructionResult,
) -> None:
    result = compare_reconstruction_results(
        left,
        right,
    )

    if result.conflict:
        raise CommissionACRLConflictError(
            result.reason
        )


__all__ = [
    "CommissionACRLConflictError",
    "CommissionACRLConflictResult",
    "compare_reconstruction_results",
    "assert_no_reconstruction_conflict",
]
