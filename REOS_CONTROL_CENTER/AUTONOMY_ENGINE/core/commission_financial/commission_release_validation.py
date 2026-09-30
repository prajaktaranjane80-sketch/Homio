from __future__ import annotations

from datetime import datetime
from typing import Any

from .commission_release import (
    CommissionRelease,
    CommissionReleaseState,
)
from .commission_statement import CommissionStatement


def validate_release(
    release: CommissionRelease,
    statement: CommissionStatement,
    *,
    at: datetime,
) -> tuple[str, ...]:
    errors: list[str] = []

    if not isinstance(
        release,
        CommissionRelease,
    ):
        return (
            "release must be CommissionRelease.",
        )

    if not isinstance(
        statement,
        CommissionStatement,
    ):
        return (
            "statement must be CommissionStatement.",
        )

    if release.tenant_id != statement.tenant_id:
        errors.append("tenant mismatch")

    if release.commission_id != statement.commission_id:
        errors.append("commission mismatch")

    if release.statement_id != statement.statement_id:
        errors.append("statement mismatch")

    if release.evaluated_at > at:
        errors.append(
            "release cannot be evaluated after validation time"
        )

    if not release.all_checks_passed:
        if release.state is CommissionReleaseState.RELEASED:
            errors.append(
                "RELEASED state requires every release check to pass"
            )

    if (
        release.state
        is CommissionReleaseState.RELEASED
        and not release.authorization_reference
    ):
        errors.append(
            "RELEASED state requires authorization reference"
        )

    if (
        release.state
        is CommissionReleaseState.RELEASED
        and release.released_at is None
    ):
        errors.append(
            "RELEASED state requires released_at"
        )

    return tuple(errors)


def release_validation_report(
    release: CommissionRelease,
    statement: CommissionStatement,
    *,
    at: datetime,
) -> dict[str, Any]:
    errors = validate_release(
        release,
        statement,
        at=at,
    )

    return {
        "valid": not errors,
        "errors": errors,
    }


__all__ = [
    "validate_release",
    "release_validation_report",
]
