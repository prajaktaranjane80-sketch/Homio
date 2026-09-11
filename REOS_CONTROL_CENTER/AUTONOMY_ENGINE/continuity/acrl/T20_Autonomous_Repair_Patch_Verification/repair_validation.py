from __future__ import annotations

import re

from .repair_models import (
    RepairPolicy,
    RepairRequest,
)
from .repair_policy import validate_policy
from .repair_scope import normalize_path


_SHA256 = re.compile(
    r"^[0-9a-f]{64}$"
)


def validate_request(
    request: RepairRequest,
    policy: RepairPolicy,
) -> None:
    validate_policy(policy)

    if not request.repair_id.strip():
        raise ValueError(
            "repair_id is required."
        )

    if not _SHA256.fullmatch(
        request.authorization_fingerprint
    ):
        raise ValueError(
            "Invalid authorization fingerprint."
        )

    if not request.authorization_nonce.strip():
        raise ValueError(
            "Authorization nonce is required."
        )

    if not _SHA256.fullmatch(
        request.diagnosis_fingerprint
    ):
        raise ValueError(
            "Invalid diagnosis fingerprint."
        )

    if not _SHA256.fullmatch(
        request.impact_fingerprint
    ):
        raise ValueError(
            "Invalid impact fingerprint."
        )

    if not _SHA256.fullmatch(
        request.baseline_fingerprint
    ):
        raise ValueError(
            "Invalid baseline fingerprint."
        )

    if request.attempt <= 0:
        raise ValueError(
            "Repair attempt must be positive."
        )

    if request.attempt > policy.max_attempts:
        raise ValueError(
            "Repair retry budget exhausted."
        )

    allowed = tuple(
        sorted(
            {
                normalize_path(path)
                for path in request.allowed_paths
            }
        )
    )

    if allowed != tuple(
        sorted(
            request.allowed_paths
        )
    ):
        raise ValueError(
            "Allowed repair paths must be canonical."
        )
