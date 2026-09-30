"""CORE-007 — Governance Security & Tenant Boundary.

This module defines the explicit security contract owned by CORE-007.

CORE-001 remains the authoritative identity/authorization boundary.
CORE-007 only validates that governance evaluation context is correctly
scoped before governance decisions are interpreted.

This module does NOT:
- authenticate identities,
- grant permissions,
- replace RBAC/ABAC,
- issue sessions,
- own tenant lifecycle,
- mutate domain state.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import hashlib
import json


GOVERNANCE_SECURITY_SCHEMA_VERSION = 1


class GovernanceSecurityError(ValueError):
    """Base governance security error."""


class GovernanceTenantViolation(
    GovernanceSecurityError
):
    """Cross-tenant request detected."""


class GovernanceSubjectViolation(
    GovernanceSecurityError
):
    """Cross-subject request detected."""


class GovernanceActorViolation(
    GovernanceSecurityError
):
    """Invalid actor/security relationship."""


class GovernanceContextViolation(
    GovernanceSecurityError
):
    """Invalid governance execution context."""


class GovernancePrivilegeClass(str, Enum):
    STANDARD = "STANDARD"
    PRIVILEGED = "PRIVILEGED"
    SYSTEM = "SYSTEM"


def _text(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GovernanceSecurityError(
            f"{field_name} must be non-empty text."
        )
    return value.strip()


def _utc(
    value: datetime,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise GovernanceSecurityError(
            f"{field_name} must be datetime."
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise GovernanceSecurityError(
            f"{field_name} must be timezone-aware."
        )

    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class GovernanceSecurityContext:
    """Immutable scope context for CORE-007 operations."""

    tenant_id: str
    subject_id: str

    actor_id: str
    actor_tenant_id: str

    target_tenant_id: str | None = None
    target_subject_id: str | None = None

    action_code: str = "GOVERNANCE_EVALUATION"

    operating_mode: str | None = None
    jurisdiction: str | None = None

    privilege_class: GovernancePrivilegeClass = (
        GovernancePrivilegeClass.STANDARD
    )

    captured_at: datetime = datetime(
        1970,
        1,
        1,
        tzinfo=timezone.utc,
    )

    schema_version: int = (
        GOVERNANCE_SECURITY_SCHEMA_VERSION
    )

    def __post_init__(self) -> None:
        for name in (
            "tenant_id",
            "subject_id",
            "actor_id",
            "actor_tenant_id",
            "action_code",
        ):
            object.__setattr__(
                self,
                name,
                _text(
                    getattr(self, name),
                    name,
                ),
            )

        for name in (
            "target_tenant_id",
            "target_subject_id",
            "operating_mode",
            "jurisdiction",
        ):
            value = getattr(self, name)

            if value is not None:
                object.__setattr__(
                    self,
                    name,
                    _text(value, name),
                )

        if not isinstance(
            self.privilege_class,
            GovernancePrivilegeClass,
        ):
            raise GovernanceSecurityError(
                "privilege_class must be "
                "GovernancePrivilegeClass."
            )

        object.__setattr__(
            self,
            "captured_at",
            _utc(
                self.captured_at,
                "captured_at",
            ),
        )

        if self.schema_version != (
            GOVERNANCE_SECURITY_SCHEMA_VERSION
        ):
            raise GovernanceSecurityError(
                "Unsupported governance security schema."
            )

    @property
    def scope_fingerprint(self) -> str:
        material = {
            "tenant_id": self.tenant_id,
            "subject_id": self.subject_id,
            "actor_id": self.actor_id,
            "actor_tenant_id": self.actor_tenant_id,
            "target_tenant_id": self.target_tenant_id,
            "target_subject_id": self.target_subject_id,
            "action_code": self.action_code,
            "operating_mode": self.operating_mode,
            "jurisdiction": self.jurisdiction,
            "privilege_class": (
                self.privilege_class.value
            ),
            "schema_version": self.schema_version,
        }

        raw = json.dumps(
            material,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")

        return hashlib.sha256(raw).hexdigest()


class GovernanceSecurityBoundary:
    """Explicit pre-evaluation governance security boundary."""

    @staticmethod
    def validate(
        context: GovernanceSecurityContext,
    ) -> None:
        if not isinstance(
            context,
            GovernanceSecurityContext,
        ):
            raise GovernanceSecurityError(
                "context must be GovernanceSecurityContext."
            )

        if (
            context.actor_tenant_id
            != context.tenant_id
        ):
            raise GovernanceTenantViolation(
                "Actor belongs to another tenant."
            )

        if (
            context.target_tenant_id is not None
            and context.target_tenant_id
            != context.tenant_id
        ):
            raise GovernanceTenantViolation(
                "Target tenant does not match context tenant."
            )

        if (
            context.target_subject_id is not None
            and context.target_subject_id
            != context.subject_id
        ):
            raise GovernanceSubjectViolation(
                "Target subject does not match context subject."
            )

        if (
            context.privilege_class
            is GovernancePrivilegeClass.SYSTEM
            and context.actor_id.startswith("system:")
            is False
        ):
            raise GovernanceActorViolation(
                "SYSTEM governance privilege requires "
                "a system actor reference."
            )

        if not context.action_code.strip():
            raise GovernanceContextViolation(
                "Governance action code is required."
            )

    @staticmethod
    def assert_tenant(
        *,
        expected_tenant_id: str,
        actual_tenant_id: str,
    ) -> None:
        if (
            expected_tenant_id
            != actual_tenant_id
        ):
            raise GovernanceTenantViolation(
                "Governance operation crosses tenant boundary."
            )

    @staticmethod
    def assert_subject(
        *,
        expected_subject_id: str,
        actual_subject_id: str,
    ) -> None:
        if (
            expected_subject_id
            != actual_subject_id
        ):
            raise GovernanceSubjectViolation(
                "Governance operation crosses subject boundary."
            )

    @staticmethod
    def assert_separation_of_duties(
        *,
        decision_actor_id: str,
        approval_actor_id: str,
    ) -> None:
        if not decision_actor_id.strip():
            raise GovernanceActorViolation(
                "decision_actor_id is required."
            )

        if not approval_actor_id.strip():
            raise GovernanceActorViolation(
                "approval_actor_id is required."
            )

        if (
            decision_actor_id
            == approval_actor_id
        ):
            raise GovernanceActorViolation(
                "Decision and approval actors must be "
                "different for separation-of-duties protected "
                "governance actions."
            )
