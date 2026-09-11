from __future__ import annotations

import re

from .git_models import (
    GitPolicy,
    GitTransactionRequest,
)
from .git_policy import validate_policy


_SHA = re.compile(
    r"^[0-9a-f]{40}$"
)

_SHA256 = re.compile(
    r"^[0-9a-f]{64}$"
)


def validate_request(
    request: GitTransactionRequest,
    policy: GitPolicy,
) -> None:
    validate_policy(policy)

    if not request.transaction_id.strip():
        raise ValueError(
            "Transaction ID is required."
        )

    if not request.repair_id.strip():
        raise ValueError(
            "Repair ID is required."
        )

    if not _SHA256.fullmatch(
        request.repair_fingerprint
    ):
        raise ValueError(
            "Invalid repair fingerprint."
        )

    if not _SHA.fullmatch(
        request.expected_head_sha
    ):
        raise ValueError(
            "Invalid expected HEAD SHA."
        )

    if request.operation.value != "READ":
        if not request.authorization_fingerprint:
            raise ValueError(
                "Write operation requires authorization fingerprint."
            )

        if not request.authorization_nonce.strip():
            raise ValueError(
                "Write operation requires authorization nonce."
            )

    if request.push and not request.remote_name:
        raise ValueError(
            "Remote name is required for push."
        )
