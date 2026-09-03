"""ACRL T06 — checkpoint validation layer."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re

from .checkpoint_engine import (
    CheckpointEngine,
    ExecutionCheckpoint,
)
from .checkpoint_identity import (
    build_checkpoint_identity,
)


_SHA256 = re.compile(
    r"^[0-9a-f]{64}$"
)


class CheckpointValidationStatus(
    str,
    Enum,
):
    VALID = "VALID"
    INVALID = "INVALID"


@dataclass(frozen=True)
class CheckpointValidationReport:
    """Immutable validation report."""

    status: CheckpointValidationStatus
    checks: tuple[str, ...]
    failures: tuple[str, ...]

    @property
    def valid(self) -> bool:
        return (
            self.status
            == CheckpointValidationStatus.VALID
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "valid": self.valid,
            "checks": list(self.checks),
            "failures": list(self.failures),
        }


def validate_checkpoint(
    checkpoint: ExecutionCheckpoint,
) -> CheckpointValidationReport:
    """Validate checkpoint contract without mutation."""

    if not isinstance(
        checkpoint,
        ExecutionCheckpoint,
    ):
        raise TypeError(
            "checkpoint must be ExecutionCheckpoint."
        )

    checks: list[str] = []
    failures: list[str] = []

    def check(
        name: str,
        condition: bool,
        reason: str,
    ) -> None:
        checks.append(name)

        if not condition:
            failures.append(reason)

    check(
        "schema_version",
        checkpoint.metadata.schema_version
        == CheckpointEngine.SCHEMA_VERSION,
        "Unsupported checkpoint schema version.",
    )

    check(
        "authoritative_source",
        checkpoint.source
        == CheckpointEngine.AUTHORITATIVE_SOURCE,
        "Checkpoint source is not REOS_STATE.",
    )

    check(
        "checkpoint_id",
        bool(
            checkpoint.metadata.checkpoint_id.strip()
        ),
        "Checkpoint ID must not be empty.",
    )

    check(
        "created_at",
        bool(
            checkpoint.metadata.created_at.strip()
        ),
        "Checkpoint created_at must not be empty.",
    )

    check(
        "state_fingerprint",
        bool(
            _SHA256.fullmatch(
                checkpoint.state_fingerprint
            )
        ),
        "State fingerprint must be valid SHA-256.",
    )

    check(
        "checkpoint_fingerprint",
        bool(
            _SHA256.fullmatch(
                checkpoint.checkpoint_fingerprint
            )
        ),
        "Checkpoint fingerprint must be valid SHA-256.",
    )

    try:
        state_valid = checkpoint.verify_integrity()
    except Exception as exc:
        state_valid = False
        failures.append(
            f"Integrity verification raised: {type(exc).__name__}"
        )

    checks.append("integrity")
    if not state_valid:
        failures.append(
            "Checkpoint integrity verification failed."
        )

    try:
        identity = build_checkpoint_identity(
            checkpoint
        )
        identity_valid = (
            len(identity.canonical_sha256) == 64
        )
    except Exception as exc:
        identity_valid = False
        failures.append(
            f"Identity validation raised: {type(exc).__name__}"
        )

    checks.append("identity")
    if not identity_valid:
        failures.append(
            "Checkpoint identity validation failed."
        )

    return CheckpointValidationReport(
        status=(
            CheckpointValidationStatus.VALID
            if not failures
            else CheckpointValidationStatus.INVALID
        ),
        checks=tuple(checks),
        failures=tuple(failures),
    )


__all__ = [
    "CheckpointValidationReport",
    "CheckpointValidationStatus",
    "validate_checkpoint",
]