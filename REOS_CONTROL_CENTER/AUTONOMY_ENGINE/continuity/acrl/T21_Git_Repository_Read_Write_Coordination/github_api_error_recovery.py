"""T21 safe, classified GitHub API recovery.

This module classifies errors and returns a typed recovery decision.
It does not bypass authentication, permissions, branch protection,
repository access, or rate limits.

A single 404 is ambiguous: GitHub may conceal inaccessible private
resources behind the same status used for missing resources.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from datetime import timezone
from email.utils import parsedate_to_datetime
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


class GitHubAPIOutcome(str, Enum):
    RATE_LIMITED = "RATE_LIMITED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    AMBIGUOUS_NOT_FOUND = "AMBIGUOUS_NOT_FOUND"
    STALE_SHA_NEEDS_RECONCILIATION = "STALE_SHA_NEEDS_RECONCILIATION"
    TRANSIENT_FAILURE_RETRYABLE = "TRANSIENT_FAILURE_RETRYABLE"
    RECOVERY_REQUIRED_USER_ACTION = "RECOVERY_REQUIRED_USER_ACTION"
    FAIL_CLOSED = "FAIL_CLOSED"


@dataclass(frozen=True, slots=True)
class GitHubAPIRecovery:
    kind: GitHubAPIErrorKind
    outcome: GitHubAPIOutcome
    retryable: bool
    requires_readback: bool
    retry_after_seconds: int | None
    max_retries: int
    action: str


def _normalized_headers(
    headers: Mapping[str, str] | None,
) -> dict[str, str]:
    """Normalize header names without logging response secrets."""
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
    """Read a Retry-After delay or primary-rate-limit reset timestamp."""
    retry_after = headers.get("retry-after", "")

    if retry_after:
        # GitHub normally supplies seconds. Also accept a valid HTTP date.
        try:
            numeric_delay = float(retry_after)
            if math.isfinite(numeric_delay):
                return max(0, math.ceil(numeric_delay))
        except (TypeError, ValueError, OverflowError):
            pass

        try:
            retry_at = parsedate_to_datetime(retry_after)
            if retry_at.tzinfo is None:
                retry_at = retry_at.replace(tzinfo=timezone.utc)

            current_epoch = (
                int(time.time())
                if now_epoch is None
                else int(now_epoch)
            )
            return max(0, math.ceil(retry_at.timestamp() - current_epoch))
        except (TypeError, ValueError, OverflowError):
            pass

    # X-RateLimit-Reset is meaningful as the required wait when the
    # remaining request budget has reached zero.
    if headers.get("x-ratelimit-remaining") == "0":
        reset = headers.get("x-ratelimit-reset", "")
        if reset:
            try:
                current_epoch = (
                    int(time.time())
                    if now_epoch is None
                    else int(now_epoch)
                )
                return max(0, math.ceil(float(reset) - current_epoch))
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
    """Return a deterministic, fail-closed recovery recommendation."""
    if status_code is not None:
        if (
            isinstance(status_code, bool)
            or not isinstance(status_code, int)
            or not 100 <= status_code <= 599
        ):
            raise ValueError("Invalid HTTP status code.")

    if not isinstance(operation_is_write, bool):
        raise ValueError("operation_is_write must be a boolean.")

    values = _normalized_headers(headers)
    safe_message = message.casefold()

    primary_rate_limit = (
        values.get("x-ratelimit-remaining") == "0"
    )
    secondary_rate_limit = any(
        phrase in safe_message
        for phrase in (
            "secondary rate limit",
            "secondary rate-limit",
            "abuse detection",
            "rate limit",
            "rate-limit",
            "too many requests",
        )
    )
    retry_after_present = bool(values.get("retry-after"))

    rate_limited = (
        status_code == 429
        or (
            status_code == 403
            and (
                primary_rate_limit
                or secondary_rate_limit
                or retry_after_present
            )
        )
    )

    if status_code in {403, 429} and rate_limited:
        delay = _retry_after_seconds(
            values,
            now_epoch=now_epoch,
        )

        # GitHub's guidance for a secondary-rate-limit response without
        # Retry-After or a usable primary reset is to wait at least 60 s.
        if delay is None:
            delay = 60

        return GitHubAPIRecovery(
            kind=GitHubAPIErrorKind.RATE_LIMITED,
            outcome=GitHubAPIOutcome.RATE_LIMITED,
            retryable=not operation_is_write,
            requires_readback=operation_is_write,
            retry_after_seconds=delay,
            max_retries=1 if not operation_is_write else 0,
            action=(
                "RATE_LIMITED: stop requests until the server-directed "
                "wait has elapsed. Safe reads may use at most one "
                "bounded retry. Writes must not be retried automatically; "
                "read back the target first and resolve the write outcome. "
                "If the limit persists, stop and require a later retry."
            ),
        )

    if status_code == 401:
        return GitHubAPIRecovery(
            kind=GitHubAPIErrorKind.AUTHENTICATION_REQUIRED,
            outcome=GitHubAPIOutcome.RECOVERY_REQUIRED_USER_ACTION,
            retryable=False,
            requires_readback=operation_is_write,
            retry_after_seconds=None,
            max_retries=0,
            action=(
                "AUTHENTICATION_REQUIRED: verify the authenticated identity, "
                "session validity, and required endpoint permissions through "
                "the approved connection. Do not rotate credentials blindly."
            ),
        )

    if status_code == 403:
        return GitHubAPIRecovery(
            kind=GitHubAPIErrorKind.PERMISSION_DENIED,
            outcome=GitHubAPIOutcome.PERMISSION_DENIED,
            retryable=False,
            requires_readback=operation_is_write,
            retry_after_seconds=None,
            max_retries=0,
            action=(
                "PERMISSION_DENIED: do not retry or bypass the denial. "
                "Verify which authorized connection made the request, "
                "whether the GitHub App/connection has access to the exact "
                "Homio repository, the endpoint's required permissions "
                "(Contents: write for content writes), and applicable "
                "branch protection/rulesets. If access is not granted, stop "
                "and use an already-authorized owner workflow."
            ),
        )

    if status_code == 404:
        return GitHubAPIRecovery(
            kind=GitHubAPIErrorKind.NOT_FOUND,
            outcome=GitHubAPIOutcome.AMBIGUOUS_NOT_FOUND,
            retryable=False,
            requires_readback=operation_is_write,
            retry_after_seconds=None,
            max_retries=0,
            action=(
                "AMBIGUOUS_NOT_FOUND: a single 404 does not prove that the "
                "resource is absent; GitHub may return 404 when credentials "
                "cannot access a private resource. Verify the authenticated "
                "identity and repository access first, then exact owner/repo, "
                "HTTP endpoint and method, branch/ref, path spelling/case, "
                "parent directory, and URL encoding. Use an authorized "
                "read-only metadata or parent-tree check to confirm absence. "
                "Do not sweep guessed paths, repeat the same failed request "
                "blindly, or silently switch branches."
            ),
        )

    if status_code in {409, 422}:
        is_conflict = status_code == 409

        return GitHubAPIRecovery(
            kind=(
                GitHubAPIErrorKind.CONFLICT
                if is_conflict
                else GitHubAPIErrorKind.VALIDATION_OR_STALE_SHA
            ),
            outcome=GitHubAPIOutcome.STALE_SHA_NEEDS_RECONCILIATION,
            retryable=False,
            requires_readback=True,
            retry_after_seconds=None,
            max_retries=0,
            action=(
                "STALE_SHA_NEEDS_RECONCILIATION: reread the live branch HEAD, "
                "target path and current blob SHA. Rebuild the change from "
                "the verified baseline. Never guess a SHA, overwrite newer "
                "content, or force-push around the conflict."
            ),
        )

    if status_code is not None and 500 <= status_code <= 599:
        safe_to_retry = not operation_is_write

        return GitHubAPIRecovery(
            kind=GitHubAPIErrorKind.SERVER_ERROR,
            outcome=(
                GitHubAPIOutcome.TRANSIENT_FAILURE_RETRYABLE
                if safe_to_retry
                else GitHubAPIOutcome.RECOVERY_REQUIRED_USER_ACTION
            ),
            retryable=safe_to_retry,
            requires_readback=operation_is_write,
            retry_after_seconds=None,
            max_retries=2 if safe_to_retry else 0,
            action=(
                "TRANSIENT_FAILURE_RETRYABLE: use at most two bounded "
                "exponential-backoff retries for a safe read. For a write, "
                "read back the exact branch, commit and path before any "
                "decision to retry."
                if safe_to_retry
                else
                "RECOVERY_REQUIRED_USER_ACTION: the write outcome may be "
                "ambiguous. Read back the exact target before proceeding; "
                "do not automatically repeat the write."
            ),
        )

    if status_code is None:
        transport = (transport_error or "").strip().casefold()

        if any(
            word in transport
            for word in ("tls", "ssl", "certificate")
        ):
            return GitHubAPIRecovery(
                kind=GitHubAPIErrorKind.TLS_FAILURE,
                outcome=GitHubAPIOutcome.FAIL_CLOSED,
                retryable=False,
                requires_readback=operation_is_write,
                retry_after_seconds=None,
                max_retries=0,
                action=(
                    "FAIL_CLOSED: inspect the TLS/certificate problem. "
                    "Never disable certificate verification."
                ),
            )

        if "timeout" in transport or "timed out" in transport:
            safe_to_retry = not operation_is_write

            return GitHubAPIRecovery(
                kind=GitHubAPIErrorKind.TIMEOUT,
                outcome=(
                    GitHubAPIOutcome.TRANSIENT_FAILURE_RETRYABLE
                    if safe_to_retry
                    else GitHubAPIOutcome.RECOVERY_REQUIRED_USER_ACTION
                ),
                retryable=safe_to_retry,
                requires_readback=operation_is_write,
                retry_after_seconds=None,
                max_retries=1 if safe_to_retry else 0,
                action=(
                    "TRANSIENT_FAILURE_RETRYABLE: one bounded retry is "
                    "allowed for a safe read."
                    if safe_to_retry
                    else
                    "RECOVERY_REQUIRED_USER_ACTION: read back remote state "
                    "before any retry because the write may have succeeded."
                ),
            )

        if "connection" in transport or "network" in transport:
            safe_to_retry = not operation_is_write

            return GitHubAPIRecovery(
                kind=GitHubAPIErrorKind.NETWORK_FAILURE,
                outcome=(
                    GitHubAPIOutcome.TRANSIENT_FAILURE_RETRYABLE
                    if safe_to_retry
                    else GitHubAPIOutcome.RECOVERY_REQUIRED_USER_ACTION
                ),
                retryable=safe_to_retry,
                requires_readback=operation_is_write,
                retry_after_seconds=None,
                max_retries=1 if safe_to_retry else 0,
                action=(
                    "TRANSIENT_FAILURE_RETRYABLE: one bounded retry is "
                    "allowed for a safe read."
                    if safe_to_retry
                    else
                    "RECOVERY_REQUIRED_USER_ACTION: independently read "
                    "remote state before any retry of the write."
                ),
            )

    return GitHubAPIRecovery(
        kind=GitHubAPIErrorKind.UNKNOWN,
        outcome=GitHubAPIOutcome.FAIL_CLOSED,
        retryable=False,
        requires_readback=operation_is_write,
        retry_after_seconds=None,
        max_retries=0,
        action=(
            "FAIL_CLOSED: the error is unclassified. Do not retry blindly. "
            "Inspect the error safely and independently check remote state "
            "if a write might have been attempted."
        ),
    )


__all__ = [
    "GitHubAPIErrorKind",
    "GitHubAPIOutcome",
    "GitHubAPIRecovery",
    "classify_github_api_failure",
]
