from __future__ import annotations

from AUTONOMY_ENGINE.continuity.acrl.T18_Safe_Execution_Authorization_Guard.authorization_models import (
    ExecutionAuthorization,
)
from AUTONOMY_ENGINE.continuity.acrl.T18_Safe_Execution_Authorization_Guard.authorization_registry import (
    AuthorizationDecision,
)

from .git_models import GitTransactionRequest


class GitAuthorizationError(ValueError):
    pass


def validate_write_authorization(
    authorization: ExecutionAuthorization,
    request: GitTransactionRequest,
) -> None:
    if not isinstance(
        authorization,
        ExecutionAuthorization,
    ):
        raise GitAuthorizationError(
            "T21 requires T18 ExecutionAuthorization."
        )

    if authorization.decision is not AuthorizationDecision.AUTHORIZE:
        raise GitAuthorizationError(
            "T21 requires T18 AUTHORIZE."
        )

    if not authorization.execution_authorized:
        raise GitAuthorizationError(
            "T18 execution authorization is inactive."
        )

    if authorization.state_mutated:
        raise GitAuthorizationError(
            "T18 reports state mutation."
        )

    if not authorization.requires_external_executor:
        raise GitAuthorizationError(
            "External executor boundary is required."
        )

    if (
        request.authorization_fingerprint
        != authorization.authorization_fingerprint
    ):
        raise GitAuthorizationError(
            "Authorization fingerprint mismatch."
        )

    if not request.authorization_nonce.strip():
        raise GitAuthorizationError(
            "Authorization nonce is required."
        )
