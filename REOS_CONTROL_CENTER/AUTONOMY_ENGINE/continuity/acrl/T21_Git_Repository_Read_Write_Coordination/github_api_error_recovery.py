"""T21 bounded, fail-closed classification of GitHub API failures.

This module does not make network calls or perform retries. It returns a
deterministic recovery recommendation for the caller to enforce.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping


class GitHubAPIErrorKind(str, Enum):
    RATE_LIMITED = "RATE_LIMITED"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    VALIDATION_OR_STALE_SHA = "VALIDATION_OR_STALE_SHA"
    SERVER_ERROR = "SERVER_ERROR"
    TIMEOUT = "TIMEOUT"
    NETWORK_FAILURE = "NETWORK_FAILURE"
    TLS_FAILURE = "TLS_FAILURE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class GitHubAPIRecovery:
    kind: GitHubAPIErrorKind
    retryable: bool
    requires_readback: bool
    retry_after_seconds: int | None
    max_retries: int
    action: str


def _normalized_headers(
    headers: Mapping[str, str] | None,
) -> dict[str, str]:
    if headers is None:
        return {}

    return {
        str(key).strip().lower(): str(value).strip()
        for key, value in headers.items()
    }


def _retry_after_seconds(
    headers: Mapping[str, str],
    *,
    now_epoch: int | None,
) -> int | None:
    retry_after = headers.get("retry-after", "")

    if retry_after:
        try:
            return max(0, int(float(retry_after)))
        except (TypeError, ValueError, OverflowError):
            pass

    reset = headers.get("x-ratelimit-reset", "")
    if reset and now_epoch is not None:
        try:
            return max(0, int(reset) - int(now_epoch))
        except (TypeError, ValueError, OverflowError):
            pass

    return None


def classify_github_api_failure(
    status_code: int | None,
    *,
    headers: Mapping[str, str] | None = None,
    message: str = "",
    operation_is_write: bool = False,
    transport_error: str | None = None,
    now_epoch: int | None = None,
) -> GitHubAPIRecovery:
    """Classify one failure without exposing response bodies or secrets."""
    if status_code is not None:
        if (
            isinstance(status_code, bool)
            or not isinstance(status_code, int)
            or not 100 <= status_code <= 599
        ):
            raise ValueError("Invalid HTTP status code.")

    values = _normalized_headers(headers)
    safe_message = message.casefold()
    rate_limited = (
        values.get("x-ratelimit-remaining") == "0"
        or "rate limit" in safe_message
        or "secondary rate" in safe_message
        or "abuse detection" in safe_message
        or "too many requests" in safe_message
    )

    if status_code in {403, 429} and (
        status_code == 429 or rate_limited
    ):
        return GitHubAPIRecovery(
            kind=GitHubAPIErrorKind.RATE_LIMITED,
            retryable=not operation_is_write,
            requires_readback=operation_is_write,
            retry_after_seconds=_retry_after_seconds(
                values,
                now_epoch=now_epoch,
            ),
            max_retries=1 if not operation_is_write else 0,
            action=(
                "Honor Retry-After or X-RateLimit-Reset and use a bounded "
                "retry budget. For writes, read back the target first and "
                "resolve whether the write already took effect."
            ),
        )

    if status_code == 401:
        return GitHubAPIRecovery(
            kind=GitHubAPIErrorKind.AUTHENTICATION_REQUIRED,
            retryable=False,
            requires_readback=False,
            retry_after_seconds=None,
            max_retries=0,
            action=(
                "Stop and verify the authorized authentication session "
                "and required scopes; do not rotate credentials blindly."
            ),
        )

    if status_code == 403:
        return GitHubAPIRecovery(
            kind=GitHubAPIErrorKind.PERMISSION_DENIED,
            retryable=False,
            requires_readback=False,
            retry_after_seconds=None,
            max_retries=0,
            action=(
                "Stop and inspect repository permissions, token scopes, "
                "branch protection, and rulesets. Do not blindly retry."
            ),
        )

    if status_code == 404:
        return GitHubAPIRecovery(
            kind=GitHubAPIErrorKind.NOT_FOUND,
            retryable=False,
            requires_readback=False,
            retry_after_seconds=None,
            max_retries=0,
            action=(
                "Verify owner, repository, exact ref, path spelling/case, "
                "and authorized access. Never silently switch branches."
            ),
        )

    if status_code == 409:
        return GitHubAPIRecovery(
            kind=GitHubAPIErrorKind.CONFLICT,
            retryable=False,
            requires_readback=True,
            retry_after_seconds=None,
            max_retries=0,
            action=(
                "Reread current branch, HEAD, and target content; reconcile "
                "the conflict against the original baseline. Never force-overwrite."
            ),
        )

    if status_code == 422:
        return GitHubAPIRecovery(
            kind=GitHubAPIErrorKind.VALIDATION_OR_STALE_SHA,
            retryable=False,
            requires_readback=True,
            retry_after_seconds=None,
            max_retries=0,
            action=(
                "Reread current state, expected SHA, and validation details. "
                "Rebuild the operation from verified current evidence."
            ),
        )

    if status_code is not None and 500 <= status_code <= 599:
        return GitHubAPIRecovery(
            kind=GitHubAPIErrorKind.SERVER_ERROR,
            retryable=not operation_is_write,
            requires_readback=operation_is_write,
            retry_after_seconds=None,
            max_retries=2 if not operation_is_write else 0,
            action=(
                "Use at most two bounded retries for a safe read. For a write, "
                "read back commit/ref/path state before considering any retry."
            ),
        )

    if status_code is None:
        transport = (transport_error or "").strip().casefold()

        if "tls" in transport or "ssl" in transport or "certificate" in transport:
            return GitHubAPIRecovery(
                kind=GitHubAPIErrorKind.TLS_FAILURE,
                retryable=False,
                requires_readback=operation_is_write,
                retry_after_seconds=None,
                max_retries=0,
                action=(
                    "Stop and inspect the TLS/certificate failure. "
                    "Do not disable certificate verification."
                ),
            )

        if "timeout" in transport or "timed out" in transport:
            return GitHubAPIRecovery(
                kind=GitHubAPIErrorKind.TIMEOUT,
                retryable=not operation_is_write,
                requires_readback=operation_is_write,
                retry_after_seconds=None,
                max_retries=1 if not operation_is_write else 0,
                action=(
                    "For reads, allow one bounded retry. For writes, read back "
                    "remote state first because the outcome may be ambiguous."
                ),
            )

        if "connection" in transport or "network" in transport:
            return GitHubAPIRecovery(
                kind=GitHubAPIErrorKind.NETWORK_FAILURE,
                retryable=not operation_is_write,
                requires_readback=operation_is_write,
                retry_after_seconds=None,
                max_retries=1 if not operation_is_write else 0,
                action=(
                    "For reads, allow one bounded retry. For writes, resolve "
                    "the remote outcome by readback before retrying."
                ),
            )

    return GitHubAPIRecovery(
        kind=GitHubAPIErrorKind.UNKNOWN,
        retryable=False,
        requires_readback=operation_is_write,
        retry_after_seconds=None,
        max_retries=0,
        action=(
            "Fail closed. Inspect the error class and independently reread "
            "remote state when a write might have been attempted."
        ),
    )


__all__ = [
    "GitHubAPIErrorKind",
    "GitHubAPIRecovery",
    "classify_github_api_failure",
]
