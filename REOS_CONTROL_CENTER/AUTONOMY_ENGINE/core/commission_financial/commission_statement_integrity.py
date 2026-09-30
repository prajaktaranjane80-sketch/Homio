from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .commission_statement import CommissionStatement
from .commission_statement_snapshot import (
    CommissionStatementSnapshot,
)


class CommissionStatementIntegrityError(
    ValueError
):
    """Statement integrity failure."""


@dataclass(frozen=True, slots=True)
class CommissionStatementIntegrityReport:
    valid: bool
    statement_fingerprint: str
    snapshot_fingerprint: str
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "statement_fingerprint": (
                self.statement_fingerprint
            ),
            "snapshot_fingerprint": (
                self.snapshot_fingerprint
            ),
            "reasons": list(self.reasons),
        }


def inspect_integrity(
    statement: CommissionStatement,
    snapshot: CommissionStatementSnapshot,
) -> CommissionStatementIntegrityReport:
    if not isinstance(
        statement,
        CommissionStatement,
    ):
        raise CommissionStatementIntegrityError(
            "statement must be CommissionStatement."
        )

    if not isinstance(
        snapshot,
        CommissionStatementSnapshot,
    ):
        raise CommissionStatementIntegrityError(
            "snapshot must be CommissionStatementSnapshot."
        )

    reasons: list[str] = []

    current_fingerprint = (
        statement.immutable_fingerprint
    )

    if (
        statement.statement_id
        != snapshot.statement_id
    ):
        reasons.append("statement_id mismatch")

    if (
        statement.tenant_id
        != snapshot.tenant_id
    ):
        reasons.append("tenant_id mismatch")

    if (
        statement.commission_id
        != snapshot.commission_id
    ):
        reasons.append("commission_id mismatch")

    if (
        statement.statement_version
        != snapshot.statement_version
    ):
        reasons.append(
            "statement_version mismatch"
        )

    if not snapshot.verify():
        reasons.append(
            "snapshot fingerprint is invalid"
        )

    regenerated = (
        CommissionStatementSnapshot
        .from_statement(statement)
    )

    if (
        regenerated.snapshot_fingerprint
        != snapshot.snapshot_fingerprint
    ):
        reasons.append(
            "statement does not match snapshot"
        )

    return CommissionStatementIntegrityReport(
        valid=not reasons,
        statement_fingerprint=(
            current_fingerprint
        ),
        snapshot_fingerprint=(
            snapshot.snapshot_fingerprint
        ),
        reasons=tuple(reasons),
    )


def assert_integrity(
    statement: CommissionStatement,
    snapshot: CommissionStatementSnapshot,
) -> None:
    report = inspect_integrity(
        statement,
        snapshot,
    )

    if not report.valid:
        raise CommissionStatementIntegrityError(
            "; ".join(report.reasons)
        )


__all__ = [
    "CommissionStatementIntegrityError",
    "CommissionStatementIntegrityReport",
    "inspect_integrity",
    "assert_integrity",
]
