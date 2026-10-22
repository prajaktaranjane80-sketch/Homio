from __future__ import annotations

import re
import time
from collections.abc import Callable, Mapping

from .github_api_error_recovery import (
    GitHubAPIErrorKind,
    classify_github_api_failure,
)
from .git_models import GitPolicy, GitReason
from .git_repository import GitRepository


_STATUS_CODE = re.compile(
    r"\b(?:http(?:/\d+(?:\.\d+)?)?\s+)?"
    r"(401|403|404|409|422|429|5\d\d)\b",
    re.IGNORECASE,
)

_VALID_REMOTE_SHA = re.compile(
    r"(?:[0-9a-f]{40}|[0-9a-f]{64})",
    re.IGNORECASE,
)

_MAX_SAFE_READ_RETRIES = 2
_MAX_AUTOMATIC_RETRY_WAIT_SECONDS = 60.0
_BACKOFF_BASE_SECONDS = 0.25


def _classify_github_failure(
    error: BaseException,
    *,
    operation_is_write: bool,
    headers: Mapping[str, str] | None = None,
    now_epoch: int | None = None,
):
    """Classify a Git/GitHub error using the shared T21 recovery policy."""
    message = str(error).casefold()

    match = _STATUS_CODE.search(message)
    status_code = int(match.group(1)) if match else None

    if status_code is None and (
        "repository not found" in message
        or "couldn't find remote ref" in message
    ):
        status_code = 404
    elif status_code is None and (
        "authentication failed" in message
        or "invalid username or password" in message
        or "could not read username" in message
        or "terminal prompts disabled" in message
    ):
        status_code = 401
    elif status_code is None and (
        "rate limit" in message
        or "secondary rate" in message
        or "too many requests" in message
    ):
        status_code = 403

    transport_error = None

    if (
        "tls" in message
        or "ssl certificate" in message
        or "certificate verify failed" in message
    ):
        transport_error = "tls"
    elif "timeout" in message or "timed out" in message:
        transport_error = "timeout"
    elif any(
        phrase in message
        for phrase in (
            "could not resolve host",
            "could not resolve proxy",
            "connection reset",
            "connection refused",
            "network is unreachable",
            "failed to connect",
            "temporary failure in name resolution",
            "network connection failure",
        )
    ):
        transport_error = "network"

    resolved_headers = headers
    if resolved_headers is None:
        candidate_headers = getattr(error, "headers", None)
        if isinstance(candidate_headers, Mapping):
            resolved_headers = candidate_headers

    observed_epoch = (
        int(time.time()) if now_epoch is None else now_epoch
    )

    return classify_github_api_failure(
        status_code,
        headers=resolved_headers,
        message=message,
        operation_is_write=operation_is_write,
        transport_error=transport_error,
        now_epoch=observed_epoch,
    )


def classify_git_push_error(
    error: BaseException,
    *,
    headers: Mapping[str, str] | None = None,
    now_epoch: int | None = None,
) -> tuple[GitReason, str]:
    """Classify push failures without retrying an ambiguous remote write."""
    message = str(error).casefold()

    if "407" in message or "proxy authentication" in message:
        return (
            GitReason.PROXY_AUTH_REQUIRED,
            "Proxy authentication is required; do not retry with different credentials.",
        )

    if (
        "non-fast-forward" in message
        or "fetch first" in message
        or "stale info" in message
    ):
        return (
            GitReason.NON_FAST_FORWARD,
            "Remote branch may have moved; reread remote HEAD and reconcile before retrying.",
        )

    if (
        "authentication failed" in message
        or "invalid username or password" in message
        or "could not read username" in message
        or "terminal prompts disabled" in message
    ):
        return (
            GitReason.AUTHENTICATION_FAILED,
            "Remote authentication failed; verify the configured authentication securely.",
        )

    if (
        "repository not found" in message
        or "couldn't find remote ref" in message
    ):
        return (
            GitReason.REMOTE_NOT_FOUND,
            "Remote repository or ref was not found; verify owner, URL, exact ref and access.",
        )

    recovery = _classify_github_failure(
        error,
        operation_is_write=True,
        headers=headers,
        now_epoch=now_epoch,
    )

    mapped_reason = {
        GitHubAPIErrorKind.RATE_LIMITED: GitReason.RATE_LIMITED,
        GitHubAPIErrorKind.AUTHENTICATION_REQUIRED: (
            GitReason.AUTHENTICATION_FAILED
        ),
        GitHubAPIErrorKind.PERMISSION_DENIED: (
            GitReason.AUTHORIZATION_DENIED
        ),
        GitHubAPIErrorKind.NOT_FOUND: GitReason.REMOTE_NOT_FOUND,
        GitHubAPIErrorKind.CONFLICT: GitReason.NON_FAST_FORWARD,
        GitHubAPIErrorKind.VALIDATION_OR_STALE_SHA: (
            GitReason.NON_FAST_FORWARD
        ),
        GitHubAPIErrorKind.SERVER_ERROR: GitReason.NETWORK_FAILURE,
        GitHubAPIErrorKind.TIMEOUT: GitReason.NETWORK_FAILURE,
        GitHubAPIErrorKind.NETWORK_FAILURE: GitReason.NETWORK_FAILURE,
        GitHubAPIErrorKind.TLS_FAILURE: GitReason.TLS_FAILURE,
    }.get(recovery.kind)

    if mapped_reason is None:
        return (
            GitReason.PUSH_REJECTED,
            recovery.action,
        )

    return mapped_reason, recovery.action


def push_branch(
    repository: GitRepository,
    *,
    remote: str,
    branch: str,
    policy: GitPolicy,
) -> None:
    if not policy.allow_push:
        raise ValueError("Git push is disabled by policy.")

    if policy.allow_force_push:
        raise ValueError("Force push is forbidden in T21 V1.")

    if "--force" in {remote, branch}:
        raise ValueError("Force push arguments are forbidden.")

    if remote not in repository.remote_names():
        raise ValueError("Requested Git remote is unavailable.")

    # A push is a write. Do not retry it automatically when the
    # remote outcome may be ambiguous; read back the exact ref instead.
    repository.run("push", remote, f"HEAD:{branch}")


def verify_remote_branch(
    repository: GitRepository,
    *,
    remote: str,
    branch: str,
    max_retries: int = _MAX_SAFE_READ_RETRIES,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> str:
    """
    Read back one exact remote branch with bounded transient-error retries.

    Permission errors, missing refs, stale-state conflicts, TLS failures,
    and unknown errors fail closed. This function never switches branches
    and never retries a write operation.
    """
    if not isinstance(branch, str) or not branch.strip():
        raise ValueError("A non-empty remote branch is required.")

    if (
        isinstance(max_retries, bool)
        or not isinstance(max_retries, int)
        or not 0 <= max_retries <= _MAX_SAFE_READ_RETRIES
    ):
        raise ValueError(
            f"max_retries must be between 0 and "
            f"{_MAX_SAFE_READ_RETRIES}."
        )

    requested_ref = f"refs/heads/{branch}"
    retries_used = 0

    while True:
        try:
            result = repository.run(
                "ls-remote",
                remote,
                requested_ref,
            )
        except Exception as exc:
            recovery = _classify_github_failure(
                exc,
                operation_is_write=False,
            )

            allowed_retries = min(
                max_retries,
                recovery.max_retries,
            )

            if (
                not recovery.retryable
                or retries_used >= allowed_retries
            ):
                raise

            if recovery.retry_after_seconds is not None:
                delay = float(recovery.retry_after_seconds)
            else:
                delay = min(
                    1.0,
                    _BACKOFF_BASE_SECONDS * (2**retries_used),
                )

            # Never retry earlier than the server-directed delay.
            # If that delay exceeds the automatic wait budget, stop safely.
            if delay > _MAX_AUTOMATIC_RETRY_WAIT_SECONDS:
                raise RuntimeError(
                    "Remote readback retry was not attempted because "
                    "the server-directed wait exceeds the "
                    f"{_MAX_AUTOMATIC_RETRY_WAIT_SECONDS:.0f}-second "
                    "automatic recovery budget. Recheck after the "
                    "server reset time."
                ) from exc

            sleep_fn(delay)
            retries_used += 1
            continue

        output = (result.stdout or "").strip()

        if not output:
            raise ValueError(
                "Remote branch could not be verified. "
                "The requested ref was not silently replaced."
            )

        lines = [
            line for line in output.splitlines()
            if line.strip()
        ]

        if len(lines) != 1 or "\t" not in lines[0]:
            raise ValueError(
                "Remote readback did not return exactly one "
                "branch reference."
            )

        remote_sha, returned_ref = lines[0].split("\t", 1)

        if returned_ref != requested_ref:
            raise ValueError(
                "Remote readback returned a different ref; "
                "branch fallback is forbidden."
            )

        if not _VALID_REMOTE_SHA.fullmatch(remote_sha):
            raise ValueError(
                "Remote readback did not return a valid commit SHA."
            )

        return remote_sha.lower()
