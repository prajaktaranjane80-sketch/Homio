
"""Fail-closed authorization adapter for the HOMIO AI platform.

This module does not create an identity, tenant-membership or resource-policy
engine. It delegates to injected, server-owned identity verification and the
existing domain authorization owner.

The caller must construct RequestContext from the trusted server-authenticated
request. A well-formed RequestContext is not, by itself, proof of identity.
"""
from __future__ import annotations

import re
from typing import Protocol
from uuid import uuid4

from .contracts import AuthorizationDecision, RequestContext, _identifier
from .errors import (
    AuthorizationServiceUnavailableError,
    RequestContextMissingError,
)

_OPERATION = re.compile(r"^[a-z][a-z0-9_.:-]{0,63}$")
_TOOL_NAME = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


class TrustedContextVerifierPort(Protocol):
    """Adapter over the existing server authentication boundary."""

    def verify_context(self, context: RequestContext) -> bool:
        """Verify principal, tenant and authentication-context provenance."""


class DomainAuthorizationPolicyPort(Protocol):
    """Adapter over the existing domain/resource authorization owner."""

    def authorize(
        self,
        context: RequestContext,
        *,
        operation: str,
        resource_id: str | None = None,
    ) -> AuthorizationDecision:
        """Authorize an operation in the context's established tenant scope."""


class AIPlatformAuthorization:
    """Implements the gateway and retrieval authorization ports.

    All authorization calls re-verify context. Any missing, invalid or
    unavailable dependency fails closed. Resource ownership and business
    permission decisions remain with the injected domain policy.
    """

    def __init__(
        self,
        *,
        identity_verifier: TrustedContextVerifierPort | None = None,
        domain_policy: DomainAuthorizationPolicyPort | None = None,
        enabled: bool = False,
    ) -> None:
        if not isinstance(enabled, bool):
            raise TypeError("enabled must be a boolean")

        if enabled:
            if not callable(
                getattr(identity_verifier, "verify_context", None)
            ):
                raise ValueError(
                    "an existing trusted-context verifier is required"
                )
            if not callable(
                getattr(domain_policy, "authorize", None)
            ):
                raise ValueError(
                    "the existing domain authorization policy is required"
                )

        self._identity_verifier = identity_verifier
        self._domain_policy = domain_policy
        self._enabled = enabled

    @property
    def enabled(self) -> bool:
        """Expose whether server configuration explicitly enabled the adapter."""
        return self._enabled

    @staticmethod
    def _decision(
        *,
        allowed: bool,
        reason_code: str,
    ) -> AuthorizationDecision:
        return AuthorizationDecision(
            allowed=allowed,
            decision_id=f"decision-{uuid4().hex}",
            reason_code=reason_code,
        )

    def _authorize(
        self,
        context: RequestContext,
        *,
        operation: str,
        resource_id: str | None = None,
    ) -> AuthorizationDecision:
        if not isinstance(context, RequestContext):
            raise RequestContextMissingError()

        if not self._enabled:
            return self._decision(
                allowed=False,
                reason_code="AUTHORIZATION_DISABLED",
            )

        if (
            not isinstance(operation, str)
            or not _OPERATION.fullmatch(operation)
        ):
            return self._decision(
                allowed=False,
                reason_code="INVALID_OPERATION",
            )

        normalized_resource: str | None = None
        if resource_id is not None:
            try:
                normalized_resource = _identifier(
                    resource_id,
                    "resource_id",
                )
            except (TypeError, ValueError):
                return self._decision(
                    allowed=False,
                    reason_code="INVALID_RESOURCE_ID",
                )

        try:
            trusted = self._identity_verifier.verify_context(context)
        except Exception:
            raise AuthorizationServiceUnavailableError() from None

        # Only literal bool results are accepted. Truthy strings/integers
        # must never be mistaken for a positive identity verification.
        if trusted is False:
            return self._decision(
                allowed=False,
                reason_code="IDENTITY_UNTRUSTED",
            )
        if trusted is not True:
            raise AuthorizationServiceUnavailableError()

        try:
            decision = self._domain_policy.authorize(
                context,
                operation=operation,
                resource_id=normalized_resource,
            )
        except Exception:
            raise AuthorizationServiceUnavailableError() from None

        if not isinstance(decision, AuthorizationDecision):
            raise AuthorizationServiceUnavailableError()

        return decision

    def authorize_request(
        self,
        context: RequestContext,
        *,
        operation: str,
    ) -> AuthorizationDecision:
        """Gateway entry point; delegates permissions to the domain policy."""
        return self._authorize(context, operation=operation)

    def authorize_search(
        self,
        context: RequestContext,
        *,
        operation: str,
    ) -> AuthorizationDecision:
        """Authorize the existing tenant-scoped inventory search operation."""
        if operation != "inventory.search":
            if not isinstance(context, RequestContext):
                raise RequestContextMissingError()
            return self._decision(
                allowed=False,
                reason_code="OPERATION_NOT_ALLOWED",
            )

        return self._authorize(
            context,
            operation="inventory.search",
        )

    def authorize_inventory(
        self,
        context: RequestContext,
        *,
        inventory_id: str,
    ) -> AuthorizationDecision:
        """Delegate resource ownership/access checks to the domain owner."""
        return self._authorize(
            context,
            operation="inventory.read",
            resource_id=inventory_id,
        )

    def authorize_tool_call(
        self,
        context: RequestContext,
        *,
        tool_name: str,
        resource_id: str | None = None,
    ) -> AuthorizationDecision:
        """Authorize a server-allowlisted tool independently of model output."""
        if (
            not isinstance(tool_name, str)
            or not _TOOL_NAME.fullmatch(tool_name)
        ):
            if not isinstance(context, RequestContext):
                raise RequestContextMissingError()
            return self._decision(
                allowed=False,
                reason_code="INVALID_TOOL_NAME",
            )

        return self._authorize(
            context,
            operation=f"agent.tool.{tool_name}",
            resource_id=resource_id,
        )


__all__ = [
    "AIPlatformAuthorization",
    "DomainAuthorizationPolicyPort",
    "TrustedContextVerifierPort",
]
