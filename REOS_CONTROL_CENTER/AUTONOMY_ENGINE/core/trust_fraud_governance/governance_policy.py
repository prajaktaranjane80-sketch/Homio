"""CORE-007 T04/T05 — governance policy contracts.

This module defines immutable governance policy contracts.

Ownership:
- Owns governance-policy definition and version identity.
- Does not own trust scoring.
- Does not own fraud detection.
- Does not own risk-rule evaluation.
- Does not own authorization.
- Does not own Control Center state.
- Does not persist workflow state.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any, Mapping


GOVERNANCE_SCHEMA_VERSION = 1
GOVERNANCE_POLICY_ENGINE_VERSION = "1.0"


class GovernancePolicyError(ValueError):
    """Base governance-policy error."""


class GovernancePolicyValidationError(
    GovernancePolicyError
):
    """Invalid governance-policy definition."""


class GovernancePolicyConflictError(
    GovernancePolicyError
):
    """Conflicting governance-policy identity."""


class GovernanceActionClass(str, Enum):
    INFORMATIONAL = "INFORMATIONAL"
    REVIEW = "REVIEW"
    HIGH_RISK = "HIGH_RISK"
    CRITICAL = "CRITICAL"


class GovernanceDisposition(str, Enum):
    CONTINUE = "CONTINUE"
    REVIEW = "REVIEW"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    ESCALATE = "ESCALATE"


_ACTION_RANK = {
    GovernanceActionClass.INFORMATIONAL: 0,
    GovernanceActionClass.REVIEW: 1,
    GovernanceActionClass.HIGH_RISK: 2,
    GovernanceActionClass.CRITICAL: 3,
}


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GovernancePolicyValidationError(
            f"{field} must be non-empty text."
        )
    return value.strip()


def _utc(value: datetime, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise GovernancePolicyValidationError(
            f"{field} must be datetime."
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise GovernancePolicyValidationError(
            f"{field} must be timezone-aware."
        )

    return value.astimezone(timezone.utc)


def _canonical(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value

    if isinstance(value, datetime):
        return _utc(value, "datetime").isoformat()

    if isinstance(value, Mapping):
        return {
            str(key): _canonical(value[key])
            for key in sorted(
                value,
                key=lambda item: str(item),
            )
        }

    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]

    if isinstance(value, (str, int, float, bool)) or value is None:
        return value

    raise GovernancePolicyValidationError(
        f"Unsupported value type: {type(value).__name__}"
    )


def _fingerprint(value: Any) -> str:
    payload = json.dumps(
        _canonical(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True, slots=True)
class GovernanceRule:
    """Single immutable governance rule."""

    rule_id: str
    version: str
    action_class: GovernanceActionClass
    disposition: GovernanceDisposition
    priority: int
    reason: str
    enabled: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "rule_id",
            _text(self.rule_id, "rule_id"),
        )
        object.__setattr__(
            self,
            "version",
            _text(self.version, "version"),
        )
        object.__setattr__(
            self,
            "reason",
            _text(self.reason, "reason"),
        )

        if not isinstance(
            self.action_class,
            GovernanceActionClass,
        ):
            raise GovernancePolicyValidationError(
                "action_class must be GovernanceActionClass."
            )

        if not isinstance(
            self.disposition,
            GovernanceDisposition,
        ):
            raise GovernancePolicyValidationError(
                "disposition must be GovernanceDisposition."
            )

        if (
            isinstance(self.priority, bool)
            or not isinstance(self.priority, int)
            or self.priority < 1
        ):
            raise GovernancePolicyValidationError(
                "priority must be an integer >= 1."
            )

        if not isinstance(self.enabled, bool):
            raise GovernancePolicyValidationError(
                "enabled must be boolean."
            )

    @property
    def identity_key(self) -> tuple[str, str]:
        return self.rule_id, self.version

    @property
    def fingerprint(self) -> str:
        return _fingerprint(
            {
                "rule_id": self.rule_id,
                "version": self.version,
                "action_class": self.action_class,
                "disposition": self.disposition,
                "priority": self.priority,
                "reason": self.reason,
                "enabled": self.enabled,
            }
        )


@dataclass(frozen=True, slots=True)
class GovernancePolicy:
    """Versioned immutable governance policy."""

    policy_id: str
    version: str
    rules: tuple[GovernanceRule, ...]

    effective_at: datetime | None = None
    expires_at: datetime | None = None
    schema_version: int = GOVERNANCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "policy_id",
            _text(self.policy_id, "policy_id"),
        )
        object.__setattr__(
            self,
            "version",
            _text(self.version, "version"),
        )

        if self.schema_version != GOVERNANCE_SCHEMA_VERSION:
            raise GovernancePolicyValidationError(
                "Unsupported governance schema version."
            )

        if not isinstance(self.rules, tuple):
            raise GovernancePolicyValidationError(
                "rules must be tuple."
            )

        seen: set[tuple[str, str]] = set()

        for rule in self.rules:
            if not isinstance(rule, GovernanceRule):
                raise GovernancePolicyValidationError(
                    "rules must contain GovernanceRule."
                )

            if rule.identity_key in seen:
                raise GovernancePolicyConflictError(
                    "Duplicate governance rule identity."
                )

            seen.add(rule.identity_key)

        effective = (
            _utc(self.effective_at, "effective_at")
            if self.effective_at is not None
            else None
        )

        expires = (
            _utc(self.expires_at, "expires_at")
            if self.expires_at is not None
            else None
        )

        if (
            effective is not None
            and expires is not None
            and expires <= effective
        ):
            raise GovernancePolicyValidationError(
                "expires_at must be after effective_at."
            )

        object.__setattr__(self, "effective_at", effective)
        object.__setattr__(self, "expires_at", expires)

        object.__setattr__(
            self,
            "rules",
            tuple(
                sorted(
                    self.rules,
                    key=lambda rule: (
                        -rule.priority,
                        rule.rule_id,
                        rule.version,
                    ),
                )
            ),
        )

    @property
    def identity_key(self) -> tuple[str, str]:
        return self.policy_id, self.version

    @property
    def fingerprint(self) -> str:
        return _fingerprint(
            {
                "policy_id": self.policy_id,
                "version": self.version,
                "rules": tuple(
                    rule.fingerprint
                    for rule in self.rules
                ),
                "effective_at": self.effective_at,
                "expires_at": self.expires_at,
                "schema_version": self.schema_version,
            }
        )

    def is_active(self, evaluated_at: datetime) -> bool:
        when = _utc(evaluated_at, "evaluated_at")

        return (
            (
                self.effective_at is None
                or when >= self.effective_at
            )
            and (
                self.expires_at is None
                or when < self.expires_at
            )
        )

    def assert_compatible(
        self,
        other: "GovernancePolicy",
    ) -> None:
        if not isinstance(other, GovernancePolicy):
            raise GovernancePolicyValidationError(
                "other must be GovernancePolicy."
            )

        if self.identity_key != other.identity_key:
            raise GovernancePolicyConflictError(
                "Governance policy identities differ."
            )

        if self.fingerprint != other.fingerprint:
            raise GovernancePolicyConflictError(
                "Same governance policy identity "
                "contains conflicting definitions."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "version": self.version,
            "rules": [
                {
                    "rule_id": rule.rule_id,
                    "version": rule.version,
                    "action_class": rule.action_class.value,
                    "disposition": rule.disposition.value,
                    "priority": rule.priority,
                    "reason": rule.reason,
                    "enabled": rule.enabled,
                    "fingerprint": rule.fingerprint,
                }
                for rule in self.rules
            ],
            "effective_at": (
                self.effective_at.isoformat()
                if self.effective_at is not None
                else None
            ),
            "expires_at": (
                self.expires_at.isoformat()
                if self.expires_at is not None
                else None
            ),
            "schema_version": self.schema_version,
            "fingerprint": self.fingerprint,
        }
