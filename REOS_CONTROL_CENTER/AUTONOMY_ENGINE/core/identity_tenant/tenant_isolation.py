from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import UUID

from .membership import Membership, MembershipStatus
from .tenant import TenantContext


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _validate_uuid(value: UUID, field_name: str) -> None:
    if not isinstance(value, UUID):
        raise TypeError(f"{field_name} must be UUID")


def _validate_aware(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be datetime")

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")

    return value


class TenantIsolationDecision(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"


class TenantIsolationReason(StrEnum):
    VALID = "VALID"
    NO_TENANT_CONTEXT = "NO_TENANT_CONTEXT"
    INVALID_TENANT_CONTEXT = "INVALID_TENANT_CONTEXT"
    TENANT_MISMATCH = "TENANT_MISMATCH"
    RESOURCE_TENANT_MISMATCH = "RESOURCE_TENANT_MISMATCH"
    MEMBERSHIP_TENANT_MISMATCH = "MEMBERSHIP_TENANT_MISMATCH"
    MEMBERSHIP_ORGANIZATION_MISMATCH = (
        "MEMBERSHIP_ORGANIZATION_MISMATCH"
    )
    MEMBERSHIP_REVISION_STALE = "MEMBERSHIP_REVISION_STALE"
    MEMBERSHIP_REVOKED = "MEMBERSHIP_REVOKED"
    MEMBERSHIP_EXPIRED = "MEMBERSHIP_EXPIRED"
    MEMBERSHIP_INVALID = "MEMBERSHIP_INVALID"
    INVALID_INPUT = "INVALID_INPUT"


class TenantIsolationDeniedError(RuntimeError):
    """Raised when a tenant boundary cannot be proven safely."""


@dataclass(frozen=True, slots=True)
class TenantIsolationResource:
    """
    Minimal tenant-bound resource reference.

    T04 does not own resource storage.
    It only carries the tenant identity required to
    verify the boundary.
    """

    resource_id: UUID
    tenant_id: UUID

    def __post_init__(self) -> None:
        _validate_uuid(self.resource_id, "resource_id")
        _validate_uuid(self.tenant_id, "tenant_id")


@dataclass(frozen=True, slots=True)
class TenantIsolationResult:
    """
    Structural tenant-boundary verification result.

    ALLOW means only that the tenant boundary was proven.
    It does not mean that authorization has been granted.
    """

    decision: TenantIsolationDecision
    reason: TenantIsolationReason
    tenant_id: UUID | None = None
    organization_id: UUID | None = None
    membership_id: UUID | None = None
    membership_revision: int | None = None
    checked_at: datetime = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if not isinstance(
            self.decision,
            TenantIsolationDecision,
        ):
            raise TypeError(
                "decision must be TenantIsolationDecision"
            )

        if not isinstance(
            self.reason,
            TenantIsolationReason,
        ):
            raise TypeError(
                "reason must be TenantIsolationReason"
            )

        if self.tenant_id is not None:
            _validate_uuid(self.tenant_id, "tenant_id")

        if self.organization_id is not None:
            _validate_uuid(
                self.organization_id,
                "organization_id",
            )

        if self.membership_id is not None:
            _validate_uuid(
                self.membership_id,
                "membership_id",
            )

        if self.membership_revision is not None:
            if not isinstance(self.membership_revision, int):
                raise TypeError(
                    "membership_revision must be int or None"
                )

            if self.membership_revision < 1:
                raise ValueError(
                    "membership_revision must be >= 1"
                )

        checked_at = (
            _utc_now()
            if self.checked_at is None
            else self.checked_at
        )

        checked_at = _validate_aware(
            checked_at,
            "checked_at",
        )

        object.__setattr__(
            self,
            "checked_at",
            checked_at,
        )

        if (
            self.decision is TenantIsolationDecision.ALLOW
            and self.reason is not TenantIsolationReason.VALID
        ):
            raise ValueError(
                "ALLOW result requires VALID reason"
            )

        if (
            self.decision is TenantIsolationDecision.DENY
            and self.reason is TenantIsolationReason.VALID
        ):
            raise ValueError(
                "DENY result cannot use VALID reason"
            )

    @property
    def allowed(self) -> bool:
        return self.decision is TenantIsolationDecision.ALLOW


class TenantIsolationBoundary:
    """
    CORE-001 T04 tenant isolation enforcement boundary.

    Responsibilities:
    - prove tenant context validity
    - prove tenant identity consistency
    - prove tenant-bound resource consistency
    - prove membership tenant/organization consistency
    - reject stale/revoked/expired membership authority

    Explicitly NOT responsible for:
    - authentication
    - authorization decisions
    - permission evaluation
    - policy evaluation
    - session management
    - delegation lifecycle
    - audit persistence
    - event persistence
    - AI decision making
    """

    def verify(
        self,
        *,
        tenant_context: TenantContext | None,
        requested_tenant_id: UUID | None = None,
        resource: TenantIsolationResource | None = None,
        membership: Membership | None = None,
        requested_organization_id: UUID | None = None,
        expected_membership_revision: int | None = None,
        at: datetime | None = None,
    ) -> TenantIsolationResult:
        timestamp = _utc_now() if at is None else at

        try:
            _validate_aware(timestamp, "at")

            if tenant_context is None:
                return self._deny(
                    TenantIsolationReason.NO_TENANT_CONTEXT
                )

            if not isinstance(
                tenant_context,
                TenantContext,
            ):
                return self._deny(
                    TenantIsolationReason.INVALID_TENANT_CONTEXT
                )

            if not tenant_context.is_valid:
                return self._deny(
                    TenantIsolationReason.INVALID_TENANT_CONTEXT,
                    tenant_id=tenant_context.tenant_id,
                )

            if requested_tenant_id is not None:
                _validate_uuid(
                    requested_tenant_id,
                    "requested_tenant_id",
                )

                if (
                    requested_tenant_id
                    != tenant_context.tenant_id
                ):
                    return self._deny(
                        TenantIsolationReason.TENANT_MISMATCH,
                        tenant_id=tenant_context.tenant_id,
                    )

            if resource is not None:
                if not isinstance(
                    resource,
                    TenantIsolationResource,
                ):
                    return self._deny(
                        TenantIsolationReason.INVALID_INPUT
                    )

                if (
                    resource.tenant_id
                    != tenant_context.tenant_id
                ):
                    return self._deny(
                        TenantIsolationReason.RESOURCE_TENANT_MISMATCH,
                        tenant_id=tenant_context.tenant_id,
                    )

            if requested_organization_id is not None:
                _validate_uuid(
                    requested_organization_id,
                    "requested_organization_id",
                )

            if membership is not None:
                if not isinstance(
                    membership,
                    Membership,
                ):
                    return self._deny(
                        TenantIsolationReason.INVALID_INPUT
                    )

                if (
                    membership.tenant_id
                    != tenant_context.tenant_id
                ):
                    return self._deny(
                        TenantIsolationReason.MEMBERSHIP_TENANT_MISMATCH,
                        tenant_id=tenant_context.tenant_id,
                        membership_id=membership.membership_id,
                        membership_revision=membership.revision,
                    )

                if (
                    requested_organization_id is not None
                    and membership.organization_id
                    != requested_organization_id
                ):
                    return self._deny(
                        TenantIsolationReason.MEMBERSHIP_ORGANIZATION_MISMATCH,
                        tenant_id=tenant_context.tenant_id,
                        organization_id=requested_organization_id,
                        membership_id=membership.membership_id,
                        membership_revision=membership.revision,
                    )

                if expected_membership_revision is not None:
                    if not isinstance(
                        expected_membership_revision,
                        int,
                    ):
                        return self._deny(
                            TenantIsolationReason.INVALID_INPUT
                        )

                    if expected_membership_revision < 1:
                        return self._deny(
                            TenantIsolationReason.INVALID_INPUT
                        )

                    if (
                        membership.revision
                        != expected_membership_revision
                    ):
                        return self._deny(
                            TenantIsolationReason.MEMBERSHIP_REVISION_STALE,
                            tenant_id=tenant_context.tenant_id,
                            organization_id=membership.organization_id,
                            membership_id=membership.membership_id,
                            membership_revision=membership.revision,
                        )

                if membership.status is MembershipStatus.REVOKED:
                    return self._deny(
                        TenantIsolationReason.MEMBERSHIP_REVOKED,
                        tenant_id=tenant_context.tenant_id,
                        organization_id=membership.organization_id,
                        membership_id=membership.membership_id,
                        membership_revision=membership.revision,
                    )

                if membership.status is MembershipStatus.EXPIRED:
                    return self._deny(
                        TenantIsolationReason.MEMBERSHIP_EXPIRED,
                        tenant_id=tenant_context.tenant_id,
                        organization_id=membership.organization_id,
                        membership_id=membership.membership_id,
                        membership_revision=membership.revision,
                    )

                if not membership.is_valid_at(timestamp):
                    return self._deny(
                        TenantIsolationReason.MEMBERSHIP_INVALID,
                        tenant_id=tenant_context.tenant_id,
                        organization_id=membership.organization_id,
                        membership_id=membership.membership_id,
                        membership_revision=membership.revision,
                    )

            return TenantIsolationResult(
                decision=TenantIsolationDecision.ALLOW,
                reason=TenantIsolationReason.VALID,
                tenant_id=tenant_context.tenant_id,
                organization_id=(
                    membership.organization_id
                    if membership is not None
                    else requested_organization_id
                ),
                membership_id=(
                    membership.membership_id
                    if membership is not None
                    else None
                ),
                membership_revision=(
                    membership.revision
                    if membership is not None
                    else None
                ),
                checked_at=timestamp,
            )

        except (TypeError, ValueError):
            return self._deny(
                TenantIsolationReason.INVALID_INPUT
            )

    def require_valid(
        self,
        *,
        tenant_context: TenantContext | None,
        requested_tenant_id: UUID | None = None,
        resource: TenantIsolationResource | None = None,
        membership: Membership | None = None,
        requested_organization_id: UUID | None = None,
        expected_membership_revision: int | None = None,
        at: datetime | None = None,
    ) -> TenantIsolationResult:
        result = self.verify(
            tenant_context=tenant_context,
            requested_tenant_id=requested_tenant_id,
            resource=resource,
            membership=membership,
            requested_organization_id=requested_organization_id,
            expected_membership_revision=expected_membership_revision,
            at=at,
        )

        if not result.allowed:
            raise TenantIsolationDeniedError(
                f"TENANT_ISOLATION_DENIED: {result.reason.value}"
            )

        return result

    @staticmethod
    def _deny(
        reason: TenantIsolationReason,
        *,
        tenant_id: UUID | None = None,
        organization_id: UUID | None = None,
        membership_id: UUID | None = None,
        membership_revision: int | None = None,
    ) -> TenantIsolationResult:
        return TenantIsolationResult(
            decision=TenantIsolationDecision.DENY,
            reason=reason,
            tenant_id=tenant_id,
            organization_id=organization_id,
            membership_id=membership_id,
            membership_revision=membership_revision,
        )
