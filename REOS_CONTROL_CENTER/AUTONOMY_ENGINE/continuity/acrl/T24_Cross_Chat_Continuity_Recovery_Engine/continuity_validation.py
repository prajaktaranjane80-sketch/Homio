from __future__ import annotations

import re

from .continuity_models import (
    ContinuityEvidence,
    ContinuityRequest,
)
from .continuity_policy import (
    ContinuityPolicy,
    validate_policy,
)


_SHA40 = re.compile(
    r"^[0-9a-fA-F]{40}$"
)

_SHA64 = re.compile(
    r"^[0-9a-fA-F]{64}$"
)


def _require(
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
    request: ContinuityRequest,
    policy: ContinuityPolicy,
) -> None:
    validate_policy(policy)

    _require(
        request.recovery_id,
        "recovery_id",
    )

    _require(
        request.project_id,
        "project_id",
    )

    _require(
        request.source_resolution_id,
        "source_resolution_id",
    )

    _require(
        request.expected_project_fingerprint,
        "expected_project_fingerprint",
    )

    _require(
        request.expected_state_fingerprint,
        "expected_state_fingerprint",
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
        request.recovery_nonce,
        "recovery_nonce",
    )

    if not request.evidence_ids:
        raise ValueError(
            "At least one evidence ID is required."
        )

    if len(
        set(request.evidence_ids)
    ) != len(
        request.evidence_ids
    ):
        raise ValueError(
            "Duplicate evidence IDs are not allowed."
        )

    if not _SHA64.fullmatch(
        request.expected_project_fingerprint
    ):
        raise ValueError(
            "Invalid project fingerprint."
        )

    if not _SHA64.fullmatch(
        request.expected_state_fingerprint
    ):
        raise ValueError(
            "Invalid state fingerprint."
        )

    if not _SHA40.fullmatch(
        request.expected_commit_sha
    ):
        raise ValueError(
            "Invalid commit SHA."
        )

    if request.execution_checkpoint_fingerprint:
        if not _SHA64.fullmatch(
            request.execution_checkpoint_fingerprint
        ):
            raise ValueError(
                "Invalid execution checkpoint fingerprint."
            )


def validate_evidence(
    evidence: ContinuityEvidence,
    policy: ContinuityPolicy,
) -> None:
    validate_policy(policy)

    _require(
        evidence.evidence_id,
        "evidence_id",
    )

    _require(
        evidence.subject,
        "subject",
    )

    _require(
        evidence.source_layer,
        "source_layer",
    )

    _require(
        evidence.source_name,
        "source_name",
    )

    if not _SHA64.fullmatch(
        evidence.content_fingerprint
    ):
        raise ValueError(
            "Invalid evidence fingerprint."
        )

    if not evidence.immutable:
        raise ValueError(
            "Continuity evidence must be immutable."
        )

    if (
        evidence.status.value
        == "INVALID"
    ):
        raise ValueError(
            "Invalid evidence cannot be recovered."
        )
