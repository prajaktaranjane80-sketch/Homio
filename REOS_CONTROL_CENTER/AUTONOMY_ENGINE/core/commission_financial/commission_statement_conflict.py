from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .commission_statement import CommissionStatement


class CommissionStatementConflictError(
    ValueError
):
    """Conflicting financial statement."""


@dataclass(frozen=True, slots=True)
class CommissionStatementComparison:
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
            "same_identity": self.same_identity,
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


def compare_statements(
    left: CommissionStatement,
    right: CommissionStatement,
) -> CommissionStatementComparison:
    if (
        not isinstance(
            left,
            CommissionStatement,
        )
        or not isinstance(
            right,
            CommissionStatement,
        )
    ):
        raise CommissionStatementConflictError(
            "Both values must be CommissionStatement."
        )

    same_identity = (
        left.tenant_id
        == right.tenant_id
        and left.statement_id
        == right.statement_id
        and left.statement_version
        == right.statement_version
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

    return CommissionStatementComparison(
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
    left: CommissionStatement,
    right: CommissionStatement,
) -> None:
    comparison = compare_statements(
        left,
        right,
    )

    if (
        comparison.same_identity
        and not comparison.same_fingerprint
    ):
        raise CommissionStatementConflictError(
            "Same statement identity/version contains "
            "conflicting financial totals."
        )


__all__ = [
    "CommissionStatementConflictError",
    "CommissionStatementComparison",
    "compare_statements",
    "assert_no_conflict",
]
