"""CORE-007 T05 — controlled governance exceptions.

Exceptions are:
- explicit,
- scoped,
- versioned,
- time-bounded,
- evidence-linked.

This module does not bypass authorization.
It only models governance exceptions that another
authority may later consume under its own rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from uuid import UUID, uuid4


class ExceptionError(ValueError):
    """Base governance exception error."""


class ExceptionScopeError(ExceptionError):
    """Tenant or subject scope violation."""


class ExceptionState(str, Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


@dataclass(frozen=True, slots=True)
class GovernanceException:
    """Immutable, time-bounded governance exception."""

    exception_id: UUID
    tenant_id: str
    subject_id: str

    policy_id: str
    policy_version: str

    reason: str
    evidence_reference: str

    granted_at: datetime
    expires_at: datetime

    state: ExceptionState = ExceptionState.ACTIVE

    def __post_init__(self) -> None:
        if not self.tenant_id or not self.subject_id:
            raise ExceptionScopeError(
                "tenant_id and subject_id are required."
            )

        if not self.reason.strip():
            raise ExceptionError("reason is required.")

        if not self.evidence_reference.strip():
            raise ExceptionError(
                "evidence_reference is required."
            )

        granted = self._utc(
            self.granted_at,
            "granted_at",
        )
        expires = self._utc(
            self.expires_at,
            "expires_at",
        )

        if expires <= granted:
            raise ExceptionError(
                "expires_at must be after granted_at."
            )

        object.__setattr__(
            self,
            "granted_at",
            granted,
        )
        object.__setattr__(
            self,
            "expires_at",
            expires,
        )

    @staticmethod
    def _utc(
        value: datetime,
        field: str,
    ) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ExceptionError(
                f"{field} must be timezone-aware."
            )
        return value.astimezone(timezone.utc)

    @property
    def fingerprint(self) -> str:
        payload = {
            "exception_id": str(self.exception_id),
            "tenant_id": self.tenant_id,
            "subject_id": self.subject_id,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "reason": self.reason,
            "evidence_reference": self.evidence_reference,
            "granted_at": self.granted_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "state": self.state.value,
        }

        raw = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return hashlib.sha256(raw).hexdigest()

    def is_active(
        self,
        *,
        tenant_id: str,
        subject_id: str,
        at: datetime,
    ) -> bool:
        if (
            tenant_id != self.tenant_id
            or subject_id != self.subject_id
        ):
            raise ExceptionScopeError(
                "Exception scope does not match request."
            )

        timestamp = self._utc(at, "at")

        return (
            self.state is ExceptionState.ACTIVE
            and self.granted_at <= timestamp < self.expires_at
        )


class ExceptionRegistry:
    """Deterministic exception lifecycle operations."""

    @staticmethod
    def create(
        *,
        tenant_id: str,
        subject_id: str,
        policy_id: str,
        policy_version: str,
        reason: str,
        evidence_reference: str,
        granted_at: datetime,
        expires_at: datetime,
        exception_id: UUID | None = None,
    ) -> GovernanceException:
        return GovernanceException(
            exception_id=exception_id or uuid4(),
            tenant_id=tenant_id,
            subject_id=subject_id,
            policy_id=policy_id,
            policy_version=policy_version,
            reason=reason,
            evidence_reference=evidence_reference,
            granted_at=granted_at,
            expires_at=expires_at,
        )

    @staticmethod
    def expired(
        exception: GovernanceException,
        at: datetime,
    ) -> GovernanceException:
        timestamp = GovernanceException._utc(
            at,
            "at",
        )

        if timestamp < exception.expires_at:
            raise ExceptionError(
                "Exception is not yet expired."
            )

        return GovernanceException(
            exception_id=exception.exception_id,
            tenant_id=exception.tenant_id,
            subject_id=exception.subject_id,
            policy_id=exception.policy_id,
            policy_version=exception.policy_version,
            reason=exception.reason,
            evidence_reference=exception.evidence_reference,
            granted_at=exception.granted_at,
            expires_at=exception.expires_at,
            state=ExceptionState.EXPIRED,
        )

    @staticmethod
    def revoke(
        exception: GovernanceException,
        *,
        at: datetime,
        evidence_reference: str,
    ) -> GovernanceException:
        timestamp = GovernanceException._utc(
            at,
            "at",
        )

        if not evidence_reference.strip():
            raise ExceptionError(
                "Revocation evidence is required."
            )

        return GovernanceException(
            exception_id=exception.exception_id,
            tenant_id=exception.tenant_id,
            subject_id=exception.subject_id,
            policy_id=exception.policy_id,
            policy_version=exception.policy_version,
            reason=exception.reason,
            evidence_reference=evidence_reference,
            granted_at=exception.granted_at,
            expires_at=exception.expires_at,
            state=ExceptionState.REVOKED,
        )
