from __future__ import annotations

from AUTONOMY_ENGINE.continuity.acrl.T18_Safe_Execution_Authorization_Guard.authorization_models import (
    ExecutionAuthorization,
)
from AUTONOMY_ENGINE.continuity.acrl.T18_Safe_Execution_Authorization_Guard.authorization_registry import (
    AuthorizationDecision,
)


class RepairAuthorizationError(ValueError):
    pass


def validate_authorization(
    authorization: ExecutionAuthorization,
) -> None:
    if not isinstance(
        authorization,
        ExecutionAuthorization,
    ):
        raise RepairAuthorizationError(
            "T20 requires T18 ExecutionAuthorization."
        )

    if authorization.decision is not AuthorizationDecision.AUTHORIZE:
        raise RepairAuthorizationError(
            "T20 requires explicit T18 AUTHORIZE decision."
        )

    if not authorization.execution_authorized:
        raise RepairAuthorizationError(
            "T18 execution authorization is not active."
        )

    if authorization.state_mutated:
        raise RepairAuthorizationError(
            "T18 reports state mutation."
        )

    if not authorization.requires_external_executor:
        raise RepairAuthorizationError(
            "T20 requires external execution boundary."
        )
