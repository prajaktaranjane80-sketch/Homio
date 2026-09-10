from __future__ import annotations

import hashlib
import json
from typing import Any

from .authorization_models import (
    AuthorizationRequest,
)


def fingerprint(value: Any) -> str:
    canonical = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


def request_fingerprint(
    request: AuthorizationRequest,
) -> str:
    return fingerprint(
        {
            "operator_request_fingerprint": (
                request.operator_report.request_fingerprint
            ),
            "impact_fingerprint": (
                request.impact_report.fingerprint
            ),
            "approval": (
                request.approval.to_dict()
                if request.approval is not None
                else None
            ),
            "nonce": request.nonce,
        }
    )


def approval_scope_fingerprint(
    request: AuthorizationRequest,
) -> str:
    return fingerprint(
        {
            "operator_request_fingerprint": (
                request.operator_report.request_fingerprint
            ),
            "impact_fingerprint": (
                request.impact_report.fingerprint
            ),
            "action_type": (
                request.operator_report.proposal.action_type.value
                if request.operator_report.proposal is not None
                else None
            ),
            "risk": (
                request.operator_report.proposal.risk.value
                if request.operator_report.proposal is not None
                else None
            ),
        }
    )


def authorization_fingerprint(
    authorization_payload: dict[str, Any],
) -> str:
    return fingerprint(authorization_payload)


__all__ = [
    "fingerprint",
    "request_fingerprint",
    "approval_scope_fingerprint",
    "authorization_fingerprint",
]
