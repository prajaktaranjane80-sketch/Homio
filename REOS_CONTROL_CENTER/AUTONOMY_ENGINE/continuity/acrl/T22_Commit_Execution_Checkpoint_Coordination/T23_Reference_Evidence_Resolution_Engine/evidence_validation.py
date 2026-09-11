from __future__ import annotations

import re

from .evidence_models import (
    EvidenceReference,
    EvidenceStatus,
    ResolutionRequest,
)
from .evidence_policy import (
    EvidencePolicy,
    validate_policy,
)


_SHA64 = re.compile(
    r"^[0-9a-fA-F]{64}$"
)


def _require_string(
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


def validate_evidence(
    evidence: EvidenceReference,
    policy: EvidencePolicy,
) -> None:
    validate_policy(
        policy
    )

    _require_string(
        evidence.evidence_id,
        "evidence_id",
    )

    _require_string(
        evidence.subject,
        "subject",
    )

    _require_string(
        evidence.source_layer,
        "source_layer",
    )

    _require_string(
        evidence.source_name,
        "source_name",
    )

    if not _SHA64.fullmatch(
        evidence.content_fingerprint
    ):
        raise ValueError(
            "content_fingerprint must be SHA256."
        )

    if evidence.metadata_fingerprint:
        if not _SHA64.fullmatch(
            evidence.metadata_fingerprint
        ):
            raise ValueError(
                "metadata_fingerprint must be SHA256."
            )

    if not evidence.immutable:
        if not policy.allow_non_immutable_evidence:
            raise ValueError(
                "Mutable evidence is not allowed."
            )

    if evidence.status is EvidenceStatus.INVALID:
        raise ValueError(
            "Invalid evidence cannot enter resolution."
        )


def validate_resolution_request(
    request: ResolutionRequest,
) -> None:
    _require_string(
        request.resolution_id,
        "resolution_id",
    )

    _require_string(
        request.subject,
        "subject",
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

    if request.request_fingerprint:
        if not _SHA64.fullmatch(
            request.request_fingerprint
        ):
            raise ValueError(
                "request_fingerprint must be SHA256."
            )
