from __future__ import annotations

from .scheduler_models import SchedulerRequest


def validate_authority_boundary(
    request: SchedulerRequest,
) -> None:
    if not request.loop_id:
        raise ValueError(
            "T26 loop boundary is required."
        )

    if not request.continuity_fingerprint:
        raise ValueError(
            "T24 continuity identity is required."
        )

    if not request.evidence_fingerprint:
        raise ValueError(
            "T23 evidence identity is required."
        )

    if request.policy.require_budget:
        if request.work_budget < 0:
            raise ValueError(
                "Invalid T25 work budget."
            )

        if request.token_budget < 0:
            raise ValueError(
                "Invalid T25 token budget."
            )

        if request.context_budget < 0:
            raise ValueError(
                "Invalid T25 context budget."
            )
