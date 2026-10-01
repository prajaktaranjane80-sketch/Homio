from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Mapping, Any


class FinancialSecurityError(PermissionError):
    """Financial security-boundary error."""


class FinancialTenantBoundaryError(
    FinancialSecurityError
):
    """Cross-tenant financial access."""


class FinancialAuthorizationError(
    FinancialSecurityError
):
    """Financial authorization denied."""


class FinancialAuthorizationAction(str, Enum):
    READ = "READ"
    CREATE_ENTITLEMENT = "CREATE_ENTITLEMENT"
    CALCULATE = "CALCULATE"
    ADJUST = "ADJUST"
    SETTLE = "SETTLE"
    RECONCILE = "RECONCILE"
    RELEASE = "RELEASE"
    CLOSEOUT = "CLOSEOUT"


@dataclass(frozen=True, slots=True)
class FinancialAuthorizationRequest:
    tenant_id: str
    resource_tenant_id: str
    actor_reference: str
    resource_reference: str
    action: FinancialAuthorizationAction
    authorization_reference: str
    sensitive: bool = True
    context: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        for field in (
            "tenant_id",
            "resource_tenant_id",
            "actor_reference",
            "resource_reference",
            "authorization_reference",
        ):
            value = getattr(self, field)

            if (
                not isinstance(
                    value,
                    str,
                )
                or not value.strip()
            ):
                raise FinancialAuthorizationError(
                    f"{field} is required."
                )

            object.__setattr__(
                self,
                field,
                value.strip(),
            )

        if not isinstance(
            self.action,
            FinancialAuthorizationAction,
        ):
            raise FinancialAuthorizationError(
                "Invalid financial authorization action."
            )

        if not isinstance(
            self.sensitive,
            bool,
        ):
            raise FinancialAuthorizationError(
                "sensitive must be boolean."
            )


@dataclass(frozen=True, slots=True)
class FinancialAuthorizationDecision:
    allowed: bool
    tenant_valid: bool
    authorization_valid: bool
    action: str
    resource_reference: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "tenant_valid": self.tenant_valid,
            "authorization_valid": (
                self.authorization_valid
            ),
            "action": self.action,
            "resource_reference": (
                self.resource_reference
            ),
            "reason": self.reason,
        }


class FinancialSecurityBoundary:
    """
    Read-only adapter to the existing CORE-001 authorization authority.

    No RBAC/ABAC engine is created here.
    """

    def __init__(
        self,
        authorization_verifier: Callable[
            [FinancialAuthorizationRequest],
            bool,
        ],
    ) -> None:
        if not callable(authorization_verifier):
            raise TypeError(
                "authorization_verifier must be callable."
            )

        self._authorization_verifier = (
            authorization_verifier
        )

    def authorize(
        self,
        request: FinancialAuthorizationRequest,
    ) -> FinancialAuthorizationDecision:
        if not isinstance(
            request,
            FinancialAuthorizationRequest,
        ):
            raise TypeError(
                "request must be FinancialAuthorizationRequest."
            )

        tenant_valid = (
            request.tenant_id
            == request.resource_tenant_id
        )

        if not tenant_valid:
            raise FinancialTenantBoundaryError(
                "Financial resource belongs to another tenant."
            )

        authorization_valid = bool(
            self._authorization_verifier(
                request
            )
        )

        decision = FinancialAuthorizationDecision(
            allowed=authorization_valid,
            tenant_valid=True,
            authorization_valid=authorization_valid,
            action=request.action.value,
            resource_reference=request.resource_reference,
            reason=(
                "authorized"
                if authorization_valid
                else "authorization denied"
            ),
        )

        if not authorization_valid:
            raise FinancialAuthorizationError(
                decision.reason
            )

        return decision


__all__ = [
    "FinancialAuthorizationAction",
    "FinancialAuthorizationDecision",
    "FinancialAuthorizationError",
    "FinancialAuthorizationRequest",
    "FinancialSecurityBoundary",
    "FinancialSecurityError",
    "FinancialTenantBoundaryError",
]
