from __future__ import annotations

import re

from .loop_models import LoopRequest
from .loop_policy import (
    LoopPolicy,
    validate_policy,
)


_SHA40 = re.compile(
    r"^[0-9a-fA-F]{40}$"
)

_SHA64 = re.compile(
    r"^[0-9a-fA-F]{64}$"
)


def _required(
    value: str,
    name: str,
) -> None:
    if not isinstance(
        value,
        str,
    ):
        raise ValueError(
            f"{name} must be a string."
        )

    if not value.strip():
        raise ValueError(
            f"{name} is required."
        )


def validate_request(
    request: LoopRequest,
    policy: LoopPolicy,
) -> None:
    validate_policy(
        policy
    )

    _required(
        request.loop_id,
        "loop_id",
    )

    _required(
        request.execution_intent,
        "execution_intent",
    )

    _required(
        request.checkpoint_id,
        "checkpoint_id",
    )

    _required(
        request.continuity_recovery_id,
        "continuity_recovery_id",
    )

    _required(
        request.evidence_resolution_id,
        "evidence_resolution_id",
    )

    if not _SHA64.fullmatch(
        request.checkpoint_fingerprint
    ):
        raise ValueError(
            "Invalid checkpoint fingerprint."
        )

    if not _SHA64.fullmatch(
        request.continuity_fingerprint
    ):
        raise ValueError(
            "Invalid continuity fingerprint."
        )

    if not _SHA64.fullmatch(
        request.evidence_fingerprint
    ):
        raise ValueError(
            "Invalid evidence fingerprint."
        )

    if request.max_iterations <= 0:
        raise ValueError(
            "max_iterations must be positive."
        )

    if (
        request.max_iterations
        > policy.max_iterations_hard_limit
    ):
        raise ValueError(
            "Requested iterations exceed hard limit."
        )

    if request.max_retries_per_iteration < 0:
        raise ValueError(
            "Retry count cannot be negative."
        )

    if (
        request.max_retries_per_iteration
        > policy.max_retries_hard_limit
    ):
        raise ValueError(
            "Requested retries exceed hard limit."
        )

    if request.no_progress_limit <= 0:
        raise ValueError(
            "no_progress_limit must be positive."
        )

    if (
        request.no_progress_limit
        > policy.max_no_progress_hard_limit
    ):
        raise ValueError(
            "No-progress limit exceeds hard limit."
        )

    for value, name in (
        (
            request.total_work_budget,
            "total_work_budget",
        ),
        (
            request.total_token_budget,
            "total_token_budget",
        ),
        (
            request.total_context_budget,
            "total_context_budget",
        ),
    ):
        if value < 0:
            raise ValueError(
                f"{name} cannot be negative."
            )
