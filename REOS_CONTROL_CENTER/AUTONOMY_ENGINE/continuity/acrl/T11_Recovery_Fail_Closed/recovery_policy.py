"""ACRL T11 — Recovery policy."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RecoveryPolicyError(RuntimeError):
    """Base recovery policy error."""


class RecoveryPolicyValidationError(RecoveryPolicyError):
    """Invalid recovery policy."""


class RecoveryPolicyDecision(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    FAIL_CLOSED = "FAIL_CLOSED"


@dataclass(frozen=True)
class RecoveryPolicy:
    version: str
    automatic_recovery_enabled: bool
    destructive_recovery_allowed: bool
    authority_required: bool
    integrity_required: bool
    unknown_failure_fails_closed: bool
    architecture_drift_fails_closed: bool
    authority_conflict_fails_closed: bool
    integrity_failure_fails_closed: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "automatic_recovery_enabled": (
                self.automatic_recovery_enabled
            ),
            "destructive_recovery_allowed": (
                self.destructive_recovery_allowed
            ),
            "authority_required": self.authority_required,
            "integrity_required": self.integrity_required,
            "unknown_failure_fails_closed": (
                self.unknown_failure_fails_closed
            ),
            "architecture_drift_fails_closed": (
                self.architecture_drift_fails_closed
            ),
            "authority_conflict_fails_closed": (
                self.authority_conflict_fails_closed
            ),
            "integrity_failure_fails_closed": (
                self.integrity_failure_fails_closed
            ),
        }


class RecoveryPolicyEngine:
    """Immutable, deterministic recovery policy."""

    POLICY_VERSION = "T11-POLICY-1.0"

    @classmethod
    def default(cls) -> RecoveryPolicy:
        return RecoveryPolicy(
            version=cls.POLICY_VERSION,
            automatic_recovery_enabled=True,
            destructive_recovery_allowed=False,
            authority_required=True,
            integrity_required=True,
            unknown_failure_fails_closed=True,
            architecture_drift_fails_closed=True,
            authority_conflict_fails_closed=True,
            integrity_failure_fails_closed=True,
        )

    @classmethod
    def validate(
        cls,
        policy: RecoveryPolicy,
    ) -> bool:
        if not isinstance(
            policy,
            RecoveryPolicy,
        ):
            raise RecoveryPolicyValidationError(
                "Invalid recovery policy."
            )

        if policy.version != cls.POLICY_VERSION:
            raise RecoveryPolicyValidationError(
                "Unsupported recovery policy version."
            )

        if policy.destructive_recovery_allowed:
            raise RecoveryPolicyValidationError(
                "Destructive automatic recovery is forbidden."
            )

        if not policy.authority_required:
            raise RecoveryPolicyValidationError(
                "Authority verification is mandatory."
            )

        if not policy.integrity_required:
            raise RecoveryPolicyValidationError(
                "Integrity verification is mandatory."
            )

        return True


__all__ = [
    "RecoveryPolicy",
    "RecoveryPolicyDecision",
    "RecoveryPolicyEngine",
    "RecoveryPolicyError",
    "RecoveryPolicyValidationError",
]