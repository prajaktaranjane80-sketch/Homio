from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .commission_invoice import CommissionInvoice


class CommissionInvoiceConflictError(
    ValueError
):
    """Conflicting invoice version."""


@dataclass(frozen=True, slots=True)
class CommissionInvoiceComparison:
    same_identity: bool
    same_fingerprint: bool
    identical: bool
    left_fingerprint: str
    right_fingerprint: str

    def __post_init__(self) -> None:
        expected = (
            self.same_identity
            and self.same_fingerprint
        )

        if self.identical != expected:
            raise ValueError(
                "identical comparison is inconsistent."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "same_identity": (
                self.same_identity
            ),
            "same_fingerprint": (
                self.same_fingerprint
            ),
            "identical": self.identical,
            "left_fingerprint": (
                self.left_fingerprint
            ),
            "right_fingerprint": (
                self.right_fingerprint
            ),
        }


def compare_invoices(
    left: CommissionInvoice,
    right: CommissionInvoice,
) -> CommissionInvoiceComparison:
    if (
        not isinstance(
            left,
            CommissionInvoice,
        )
        or not isinstance(
            right,
            CommissionInvoice,
        )
    ):
        raise CommissionInvoiceConflictError(
            "Both values must be CommissionInvoice."
        )

    same_identity = (
        left.tenant_id
        == right.tenant_id
        and left.invoice_id
        == right.invoice_id
        and left.invoice_version
        == right.invoice_version
    )

    left_fingerprint = (
        left.immutable_fingerprint
    )

    right_fingerprint = (
        right.immutable_fingerprint
    )

    same_fingerprint = (
        left_fingerprint
        == right_fingerprint
    )

    return CommissionInvoiceComparison(
        same_identity=same_identity,
        same_fingerprint=same_fingerprint,
        identical=(
            same_identity
            and same_fingerprint
        ),
        left_fingerprint=left_fingerprint,
        right_fingerprint=right_fingerprint,
    )


def assert_no_conflict(
    left: CommissionInvoice,
    right: CommissionInvoice,
) -> None:
    comparison = compare_invoices(
        left,
        right,
    )

    if (
        comparison.same_identity
        and not comparison.same_fingerprint
    ):
        raise CommissionInvoiceConflictError(
            "Same invoice identity/version contains "
            "conflicting financial obligation."
        )


__all__ = [
    "CommissionInvoiceConflictError",
    "CommissionInvoiceComparison",
    "compare_invoices",
    "assert_no_conflict",
]
