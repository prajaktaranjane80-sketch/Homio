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
    """Cross-tenant operation."""


class GovernanceSubjectViolation(
    GovernanceSecurityError
):
    """Cross-subject operation."""


class GovernanceActorViolation(
    GovernanceSecurityError
):
    """Invalid actor boundary."""


class GovernanceContextViolation(
    GovernanceSecurityError
):
    """Invalid governance security context."""


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
    if (
        value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise GovernanceSecurityError(
            f"{field_name} must be timezone-aware."
        )
    return value.astimezone(timezone.utc)


def _fingerprint(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")

    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True, slots=True)
class GovernanceSecurityContext:
    """
    Security boundary for governance operations.

    CORE-001 remains the actual identity/authorization owner.
    CORE-007 only validates domain boundaries and required
    authorization references.
    """

    tenant_id: str
    subject_id: str

    actor_id: str
    actor_tenant_id: str

    target_tenant_id: str | None = None
    target_subject_id: str | None = None

    action_code: str = (
        "GOVERNANCE_EVALUATION"
    )

    operating_mode: str | None = None
    jurisdiction: str | None = None

    privilege_class: GovernancePrivilegeClass = (
        GovernancePrivilegeClass.STANDARD
    )

    captured_at: datetime = (
        datetime(
            1970,
            1,
            1,
            tzinfo=timezone.utc,
        )
    )

    schema_version: int = (
        GOVERNANCE_SECURITY_SCHEMA_VERSION
    )

    sensitive_risk_data_class: str = (
        "CONTROLLED"
    )

    data_minimization_basis: str = (
        "DOMAIN_REQUIRED_ONLY"
    )

    review_authorized: bool = False
    override_authorized: bool = False

    privacy_mode: str = "MINIMIZED"

    def __post_init__(self) -> None:
        for name in (
            "tenant_id",
            "subject_id",
            "actor_id",
            "actor_tenant_id",
            "action_code",
            "sensitive_risk_data_class",
            "data_minimization_basis",
            "privacy_mode",
        ):
            object.__setattr__(
                self,
                name,
                _text(
                    getattr(self, name),
                    name,
                ),
            )

        if self.target_tenant_id is not None:
            object.__setattr__(
                self,
                "target_tenant_id",
                _text(
                    self.target_tenant_id,
                    "target_tenant_id",
                ),
            )

        if self.target_subject_id is not None:
            object.__setattr__(
                self,
                "target_subject_id",
                _text(
                    self.target_subject_id,
                    "target_subject_id",
                ),
            )

        if self.operating_mode is not None:
            object.__setattr__(
                self,
                "operating_mode",
                _text(
                    self.operating_mode,
                    "operating_mode",
                ),
            )

        if self.jurisdiction is not None:
            object.__setattr__(
                self,
                "jurisdiction",
                _text(
                    self.jurisdiction,
                    "jurisdiction",
                ),
            )

        if not isinstance(
            self.privilege_class,
            GovernancePrivilegeClass,
        ):
            raise GovernanceSecurityError(
                "Invalid privilege_class."
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
                "Unsupported security schema."
            )

        if not isinstance(
            self.review_authorized,
            bool,
        ):
            raise GovernanceSecurityError(
                "review_authorized must bool."
            )

        if not isinstance(
            self.override_authorized,
            bool,
        ):
            raise GovernanceSecurityError(
                "override_authorized must bool."
            )

    @property
    def scope_fingerprint(self) -> str:
        return _fingerprint(
            {
                "tenant_id": self.tenant_id,
                "subject_id": self.subject_id,
                "actor_tenant_id": (
                    self.actor_tenant_id
                ),
                "target_tenant_id": (
                    self.target_tenant_id
                ),
                "target_subject_id": (
                    self.target_subject_id
                ),
                "action_code": self.action_code,
                "operating_mode": (
                    self.operating_mode
                ),
                "jurisdiction": (
                    self.jurisdiction
                ),
                "privilege_class": (
                    self.privilege_class.value
                ),
                "sensitive_risk_data_class": (
                    self.sensitive_risk_data_class
                ),
                "data_minimization_basis": (
                    self.data_minimization_basis
                ),
                "review_authorized": (
                    self.review_authorized
                ),
                "override_authorized": (
                    self.override_authorized
                ),
                "privacy_mode": self.privacy_mode,
                "schema_version": (
                    self.schema_version
                ),
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "subject_id": self.subject_id,
            "actor_id": self.actor_id,
            "actor_tenant_id": (
                self.actor_tenant_id
            ),
            "target_tenant_id": (
                self.target_tenant_id
            ),
            "target_subject_id": (
                self.target_subject_id
            ),
            "action_code": self.action_code,
            "operating_mode": (
                self.operating_mode
            ),
            "jurisdiction": (
                self.jurisdiction
            ),
            "privilege_class": (
                self.privilege_class.value
            ),
            "captured_at": (
                self.captured_at.isoformat()
            ),
            "schema_version": (
                self.schema_version
            ),
            "sensitive_risk_data_class": (
                self.sensitive_risk_data_class
            ),
            "data_minimization_basis": (
                self.data_minimization_basis
            ),
            "review_authorized": (
                self.review_authorized
            ),
            "override_authorized": (
                self.override_authorized
            ),
            "privacy_mode": self.privacy_mode,
            "scope_fingerprint": (
                self.scope_fingerprint
            ),
        }


class GovernanceSecurityBoundary:
    """
    CORE-007 security boundary.

    CORE-001 remains the authoritative authorization system.
    """

    @staticmethod
    def validate(
        context: GovernanceSecurityContext,
    ) -> None:
        if not isinstance(
            context,
            GovernanceSecurityContext,
        ):
            raise GovernanceSecurityError(
                "context must GovernanceSecurityContext."
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
                "Target tenant does not match context."
            )

        if (
            context.target_subject_id is not None
            and context.target_subject_id
            != context.subject_id
        ):
            raise GovernanceSubjectViolation(
                "Target subject does not match context."
            )

        if not context.action_code.strip():
            raise GovernanceContextViolation(
                "action_code is required."
            )

        if (
            context.privacy_mode
            not in {
                "MINIMIZED",
                "CONTROLLED",
            }
        ):
            raise GovernanceContextViolation(
                "Unsupported privacy mode."
            )

        if (
            context.sensitive_risk_data_class
            == "RESTRICTED"
            and context.privacy_mode
            != "MINIMIZED"
        ):
            raise GovernanceContextViolation(
                "Restricted risk data requires "
                "MINIMIZED privacy mode."
            )

    @staticmethod
    def assert_tenant(
        context: GovernanceSecurityContext,
        tenant_id: str,
    ) -> None:
        GovernanceSecurityBoundary.validate(
            context
        )

        if context.tenant_id != tenant_id:
            raise GovernanceTenantViolation(
                "Governance operation crosses tenant boundary."
            )

    @staticmethod
    def assert_subject(
        context: GovernanceSecurityContext,
        subject_id: str,
    ) -> None:
        GovernanceSecurityBoundary.validate(
            context
        )

        if context.subject_id != subject_id:
            raise GovernanceSubjectViolation(
                "Governance operation crosses subject boundary."
            )

    @staticmethod
    def assert_separation_of_duties(
        *,
        actor_id: str,
        reviewer_id: str,
    ) -> None:
        actor_id = _text(
            actor_id,
            "actor_id",
        )

        reviewer_id = _text(
            reviewer_id,
            "reviewer_id",
        )

        if actor_id == reviewer_id:
            raise GovernanceActorViolation(
                "Actor and reviewer must be separate "
                "for protected review."
            )

    @staticmethod
    def require_review_reference(
        context: GovernanceSecurityContext,
        reference: str,
    ) -> None:
        GovernanceSecurityBoundary.validate(
            context
        )

        _text(
            reference,
            "review_reference",
        )

        if not context.review_authorized:
            raise GovernanceActorViolation(
                "Review authorization reference is "
                "required from CORE-001."
            )

    @staticmethod
    def require_override_reference(
        context: GovernanceSecurityContext,
        reference: str,
    ) -> None:
        GovernanceSecurityBoundary.validate(
            context
        )

        _text(
            reference,
            "override_reference",
        )

        if not context.override_authorized:
            raise GovernanceActorViolation(
                "Override authorization must be "
                "supplied by the authoritative "
                "authorization boundary."
            )


__all__ = [
    "GOVERNANCE_SECURITY_SCHEMA_VERSION",
    "GovernanceSecurityError",
    "GovernanceTenantViolation",
    "GovernanceSubjectViolation",
    "GovernanceActorViolation",
    "GovernanceContextViolation",
    "GovernancePrivilegeClass",
    "GovernanceSecurityContext",
    "GovernanceSecurityBoundary",
]
