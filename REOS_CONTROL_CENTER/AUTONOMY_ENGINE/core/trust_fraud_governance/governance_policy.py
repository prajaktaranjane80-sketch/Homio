from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping
import hashlib
import json


GOVERNANCE_SCHEMA_VERSION = 1
GOVERNANCE_POLICY_ENGINE_VERSION = "1.0"


class GovernancePolicyError(ValueError):
    """Base governance-policy error."""


class GovernancePolicyValidationError(
    GovernancePolicyError
):
    """Invalid governance policy."""


class GovernancePolicyConflictError(
    GovernancePolicyError
):
    """Conflicting policy/rule identity."""


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
        return _utc(
            value,
            "datetime",
        ).isoformat()

    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in sorted(
                value.items(),
                key=lambda item: str(item[0]),
            )
        }

    if isinstance(value, (tuple, list)):
        return [
            _canonical(item)
            for item in value
        ]

    if (
        isinstance(
            value,
            (str, int, float, bool),
        )
        or value is None
    ):
        return value

    raise GovernancePolicyValidationError(
        "Unsupported canonical value."
    )


def _fingerprint(value: Any) -> str:
    raw = json.dumps(
        _canonical(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")

    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True, slots=True)
class GovernanceRule:
    """
    Immutable governance rule.

    Explicit PS Output contract:
    - identity
    - version
    - scope
    - applicability
    - precedence
    - outcome
    - exception/reference
    - provenance
    """

    rule_id: str
    version: str
    action_class: GovernanceActionClass
    disposition: GovernanceDisposition
    priority: int
    reason: str

    enabled: bool = True

    scope: Mapping[str, Any] = (
        field(default_factory=dict)
    )

    applicability: Mapping[str, Any] = (
        field(default_factory=dict)
    )

    precedence: int | None = None

    exception_reference: str | None = None

    provenance_reference: str = (
        "CORE-007.GOVERNANCE_RULE"
    )

    def __post_init__(self) -> None:
        for name in (
            "rule_id",
            "version",
            "reason",
            "provenance_reference",
        ):
            object.__setattr__(
                self,
                name,
                _text(
                    getattr(self, name),
                    name,
                ),
            )

        object.__setattr__(
            self,
            "priority",
            max(
                1,
                int(self.priority),
            ),
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

        if self.precedence is not None:
            if (
                isinstance(
                    self.precedence,
                    bool,
                )
                or not isinstance(
                    self.precedence,
                    int,
                )
                or self.precedence < 1
            ):
                raise GovernancePolicyValidationError(
                    "precedence must be integer >= 1."
                )

        if not isinstance(
            self.scope,
            Mapping,
        ):
            raise GovernancePolicyValidationError(
                "scope must be mapping."
            )

        if not isinstance(
            self.applicability,
            Mapping,
        ):
            raise GovernancePolicyValidationError(
                "applicability must be mapping."
            )

        object.__setattr__(
            self,
            "scope",
            dict(
                _canonical(self.scope)
            ),
        )

        object.__setattr__(
            self,
            "applicability",
            dict(
                _canonical(
                    self.applicability
                )
            ),
        )

        if self.exception_reference is not None:
            object.__setattr__(
                self,
                "exception_reference",
                _text(
                    self.exception_reference,
                    "exception_reference",
                ),
            )

    @property
    def identity_key(self) -> tuple[str, str]:
        return (
            self.rule_id,
            self.version,
        )

    @property
    def effective_precedence(self) -> int:
        return (
            self.precedence
            if self.precedence is not None
            else self.priority
        )

    @property
    def fingerprint(self) -> str:
        return _fingerprint(
            {
                "rule_id": self.rule_id,
                "version": self.version,
                "action_class": (
                    self.action_class.value
                ),
                "disposition": (
                    self.disposition.value
                ),
                "priority": self.priority,
                "precedence": (
                    self.effective_precedence
                ),
                "reason": self.reason,
                "enabled": self.enabled,
                "scope": self.scope,
                "applicability": (
                    self.applicability
                ),
                "exception_reference": (
                    self.exception_reference
                ),
                "provenance_reference": (
                    self.provenance_reference
                ),
            }
        )

    def applies_to(
        self,
        *,
        tenant_id: str,
        subject_id: str,
        risk_outcome: str | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> bool:
        context = context or {}

        if (
            self.scope.get("tenant_id")
            not in (None, tenant_id)
        ):
            return False

        if (
            self.scope.get("subject_id")
            not in (None, subject_id)
        ):
            return False

        allowed_outcomes = (
            self.applicability.get(
                "risk_outcomes"
            )
        )

        if (
            allowed_outcomes is not None
            and risk_outcome
            not in set(allowed_outcomes)
        ):
            return False

        allowed_modes = (
            self.applicability.get(
                "operating_modes"
            )
        )

        if (
            allowed_modes is not None
            and context.get(
                "operating_mode"
            ) not in set(allowed_modes)
        ):
            return False

        allowed_jurisdictions = (
            self.applicability.get(
                "jurisdictions"
            )
        )

        if (
            allowed_jurisdictions is not None
            and context.get(
                "jurisdiction"
            ) not in set(
                allowed_jurisdictions
            )
        ):
            return False

        return True


@dataclass(frozen=True, slots=True)
class GovernancePolicy:
    """Versioned immutable governance policy."""

    policy_id: str
    version: str
    rules: tuple[GovernanceRule, ...]

    effective_at: datetime | None = None
    expires_at: datetime | None = None

    schema_version: int = (
        GOVERNANCE_SCHEMA_VERSION
    )

    scope: Mapping[str, Any] = (
        field(default_factory=dict)
    )

    applicability: Mapping[str, Any] = (
        field(default_factory=dict)
    )

    exception_reference: str | None = None

    provenance_reference: str = (
        "CORE-007.GOVERNANCE_POLICY"
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "policy_id",
            _text(
                self.policy_id,
                "policy_id",
            ),
        )

        object.__setattr__(
            self,
            "version",
            _text(
                self.version,
                "version",
            ),
        )

        if self.schema_version != (
            GOVERNANCE_SCHEMA_VERSION
        ):
            raise GovernancePolicyValidationError(
                "Unsupported governance schema version."
            )

        if not isinstance(
            self.rules,
            tuple,
        ):
            raise GovernancePolicyValidationError(
                "rules must be tuple."
            )

        seen: set[tuple[str, str]] = set()

        for rule in self.rules:
            if not isinstance(
                rule,
                GovernanceRule,
            ):
                raise GovernancePolicyValidationError(
                    "rules must contain GovernanceRule."
                )

            if rule.identity_key in seen:
                raise GovernancePolicyConflictError(
                    "Duplicate governance rule identity."
                )

            seen.add(rule.identity_key)

        if self.effective_at is not None:
            object.__setattr__(
                self,
                "effective_at",
                _utc(
                    self.effective_at,
                    "effective_at",
                ),
            )

        if self.expires_at is not None:
            object.__setattr__(
                self,
                "expires_at",
                _utc(
                    self.expires_at,
                    "expires_at",
                ),
            )

        if (
            self.effective_at is not None
            and self.expires_at is not None
            and self.expires_at
            <= self.effective_at
        ):
            raise GovernancePolicyValidationError(
                "expires_at must be after effective_at."
            )

        if not isinstance(
            self.scope,
            Mapping,
        ):
            raise GovernancePolicyValidationError(
                "scope must be mapping."
            )

        if not isinstance(
            self.applicability,
            Mapping,
        ):
            raise GovernancePolicyValidationError(
                "applicability must be mapping."
            )

        object.__setattr__(
            self,
            "scope",
            dict(
                _canonical(
                    self.scope
                )
            ),
        )

        object.__setattr__(
            self,
            "applicability",
            dict(
                _canonical(
                    self.applicability
                )
            ),
        )

        if self.exception_reference is not None:
            object.__setattr__(
                self,
                "exception_reference",
                _text(
                    self.exception_reference,
                    "exception_reference",
                ),
            )

        object.__setattr__(
            self,
            "provenance_reference",
            _text(
                self.provenance_reference,
                "provenance_reference",
            ),
        )

    @property
    def identity_key(self) -> tuple[str, str]:
        return (
            self.policy_id,
            self.version,
        )

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
                "effective_at": (
                    self.effective_at.isoformat()
                    if self.effective_at
                    else None
                ),
                "expires_at": (
                    self.expires_at.isoformat()
                    if self.expires_at
                    else None
                ),
                "scope": self.scope,
                "applicability": (
                    self.applicability
                ),
                "exception_reference": (
                    self.exception_reference
                ),
                "provenance_reference": (
                    self.provenance_reference
                ),
            }
        )

    def is_active(
        self,
        evaluated_at: datetime,
    ) -> bool:
        when = _utc(
            evaluated_at,
            "evaluated_at",
        )

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

    def applies_to(
        self,
        *,
        tenant_id: str,
        subject_id: str,
        context: Mapping[str, Any] | None = None,
    ) -> bool:
        context = context or {}

        if (
            self.scope.get("tenant_id")
            not in (None, tenant_id)
        ):
            return False

        if (
            self.scope.get("subject_id")
            not in (None, subject_id)
        ):
            return False

        modes = self.applicability.get(
            "operating_modes"
        )

        if (
            modes is not None
            and context.get(
                "operating_mode"
            ) not in set(modes)
        ):
            return False

        return True

    def assert_compatible(
        self,
        other: "GovernancePolicy",
    ) -> None:
        if not isinstance(
            other,
            GovernancePolicy,
        ):
            raise GovernancePolicyValidationError(
                "other must GovernancePolicy."
            )

        if self.identity_key != other.identity_key:
            raise GovernancePolicyConflictError(
                "Governance policy identities differ."
            )

        if self.fingerprint != other.fingerprint:
            raise GovernancePolicyConflictError(
                "Same governance policy identity "
                "contains conflicting definition."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "version": self.version,
            "rules": [
                {
                    "rule_id": rule.rule_id,
                    "version": rule.version,
                    "action_class": (
                        rule.action_class.value
                    ),
                    "disposition": (
                        rule.disposition.value
                    ),
                    "priority": rule.priority,
                    "precedence": (
                        rule.effective_precedence
                    ),
                    "reason": rule.reason,
                    "enabled": rule.enabled,
                    "scope": dict(
                        rule.scope
                    ),
                    "applicability": dict(
                        rule.applicability
                    ),
                    "exception_reference": (
                        rule.exception_reference
                    ),
                    "provenance_reference": (
                        rule.provenance_reference
                    ),
                    "fingerprint": (
                        rule.fingerprint
                    ),
                }
                for rule in self.rules
            ],
            "effective_at": (
                self.effective_at.isoformat()
                if self.effective_at
                else None
            ),
            "expires_at": (
                self.expires_at.isoformat()
                if self.expires_at
                else None
            ),
            "scope": dict(self.scope),
            "applicability": dict(
                self.applicability
            ),
            "exception_reference": (
                self.exception_reference
            ),
            "provenance_reference": (
                self.provenance_reference
            ),
            "fingerprint": self.fingerprint,
        }


__all__ = [
    "GOVERNANCE_SCHEMA_VERSION",
    "GOVERNANCE_POLICY_ENGINE_VERSION",
    "GovernancePolicyError",
    "GovernancePolicyValidationError",
    "GovernancePolicyConflictError",
    "GovernanceActionClass",
    "GovernanceDisposition",
    "GovernanceRule",
    "GovernancePolicy",
]
