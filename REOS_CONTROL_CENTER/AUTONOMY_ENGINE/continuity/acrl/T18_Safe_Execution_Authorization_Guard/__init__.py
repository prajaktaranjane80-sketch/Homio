"""ACRL T18 — Safe Execution Authorization Guard."""

from .authorization_errors import (
    SafeAuthorizationCompatibilityError,
    SafeAuthorizationError,
    SafeAuthorizationInputError,
    SafeAuthorizationIntegrityError,
    SafeAuthorizationPolicyError,
    SafeAuthorizationSecurityError,
)

from .authorization_models import (
    AuthorizationRequest,
    ExecutionAuthorization,
    HumanApproval,
)

from .authorization_policy import (
    SafeAuthorizationPolicy,
)

from .authorization_registry import (
    AuthorizationDecision,
    AuthorizationReason,
)

from .execution_authorization import (
    ExecutionAuthorizationGuard,
    authorize_execution,
)


__all__ = [
    "AuthorizationDecision",
    "AuthorizationReason",
    "AuthorizationRequest",
    "ExecutionAuthorization",
    "ExecutionAuthorizationGuard",
    "HumanApproval",
    "SafeAuthorizationCompatibilityError",
    "SafeAuthorizationError",
    "SafeAuthorizationInputError",
    "SafeAuthorizationIntegrityError",
    "SafeAuthorizationPolicy",
    "SafeAuthorizationPolicyError",
    "SafeAuthorizationSecurityError",
    "authorize_execution",
]
