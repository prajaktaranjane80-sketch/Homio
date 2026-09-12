from __future__ import annotations

from .scheduler_identity import fingerprint
from .scheduler_models import (
    ScheduleSnapshot,
    SchedulerPolicy,
)


def policy_fingerprint(
    policy: SchedulerPolicy,
) -> str:
    return fingerprint(
        policy.to_dict()
    )


def schedule_fingerprint(
    snapshot_payload: dict,
) -> str:
    payload = dict(
        snapshot_payload
    )

    payload.pop(
        "schedule_fingerprint",
        None,
    )

    return fingerprint(
        payload
    )
