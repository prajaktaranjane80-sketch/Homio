from __future__ import annotations

import re

from .checkpoint_models import CheckpointRequest
from .checkpoint_policy import (
    CheckpointPolicy,
    validate_policy,
)


_SHA40 = re.compile(r"^[0-9a-fA-F]{40}$")
_SHA64 = re.compile(r"^[0-9a-fA-F]{64}$")


def _require(value: str, name: str) -> None:
    if not isinstance(value, str):
        raise ValueError(
            f"{name} must be a string."
        )

    if not value.strip():
        raise ValueError(
            f"{name} is required."
        )


def validate_request(
    request: CheckpointRequest,
    policy: CheckpointPolicy,
) -> None:
    validate_policy(policy)

    _require(
        request.checkpoint_id,
        "checkpoint_id",
    )

    _require(
        request.execution_intent,
        "execution_intent",
    )

    _require(
        request.repository_root,
        "repository_root",
    )

    _require(
        request.expected_branch,
        "expected_branch",
    )

    _require(
        request.expected_commit_sha,
        "expected_commit_sha",
    )

    _require(
        request.transaction_id,
        "transaction_id",
    )

    _require(
        request.repair_id,
        "repair_id",
    )

    _require(
        request.repair_fingerprint,
        "repair_fingerprint",
    )

    _require(
        request.transaction_fingerprint,
        "transaction_fingerprint",
    )

    _require(
        request.authorization_fingerprint,
        "authorization_fingerprint",
    )

    _require(
        request.authorization_nonce,
        "authorization_nonce",
    )

    _require(
        request.protected_state_fingerprint,
        "protected_state_fingerprint",
    )

    if not _SHA40.fullmatch(
        request.expected_commit_sha
    ):
        raise ValueError(
            "expected_commit_sha must be a 40-character Git SHA."
        )

    if not _SHA64.fullmatch(
        request.repair_fingerprint
    ):
        raise ValueError(
            "repair_fingerprint must be SHA256."
        )

    if not _SHA64.fullmatch(
        request.transaction_fingerprint
    ):
        raise ValueError(
            "transaction_fingerprint must be SHA256."
        )

    if not _SHA64.fullmatch(
        request.authorization_fingerprint
    ):
        raise ValueError(
            "authorization_fingerprint must be SHA256."
        )

    if not _SHA64.fullmatch(
        request.protected_state_fingerprint
    ):
        raise ValueError(
            "protected_state_fingerprint must be SHA256."
        )

    if request.allow_replay:
        raise ValueError(
            "Replay is not permitted by T22."
        )
