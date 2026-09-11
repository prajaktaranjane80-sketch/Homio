from __future__ import annotations

from typing import Any


def validate_authorization(
    authorization: Any,
    *,
    expected_fingerprint: str,
    expected_nonce: str,
) -> None:
    if authorization is None:
        raise ValueError(
            "T18 authorization is required."
        )

    decision = getattr(
        authorization,
        "decision",
        None,
    )

    decision_value = getattr(
        decision,
        "value",
        decision,
    )

    if decision_value != "AUTHORIZE":
        raise ValueError(
            "Authorization decision is not AUTHORIZE."
        )

    if not getattr(
        authorization,
        "execution_authorized",
        False,
    ):
        raise ValueError(
            "Execution authorization flag is not enabled."
        )

    if getattr(
        authorization,
        "state_mutated",
        True,
    ):
        raise ValueError(
            "Authorization indicates state mutation."
        )

    authorization_fingerprint = getattr(
        authorization,
        "authorization_fingerprint",
        "",
    )

    if authorization_fingerprint != expected_fingerprint:
        raise ValueError(
            "Authorization fingerprint mismatch."
        )

    if not expected_nonce.strip():
        raise ValueError(
            "Authorization nonce is required."
        )
