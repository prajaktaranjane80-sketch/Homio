from __future__ import annotations

import re
from collections.abc import Mapping

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


def classify_git_push_error(
    error: BaseException,
    *,
    headers: Mapping[str, str] | None = None,
    now_epoch: int | None = None,
) -> tuple[GitReason, str]:
    """Classify push errors safely via the shared T21 recovery policy."""
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

    match = _STATUS_CODE.search(message)
    status_code = int(match.group(1)) if match else None

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
            "network is unreachable",
            "failed to connect",
        )
    ):
        transport_error = "network"

    # A textual rate-limit response may omit a parseable HTTP status.
    if status_code is None and (
        "rate limit" in message or "too many requests" in message
    ):
        status_code = 403

    recovery = classify_github_api_failure(
        status_code,
        headers=headers,
        message=message,
        operation_is_write=True,
        transport_error=transport_error,
        now_epoch=now_epoch,
    )

    mapped_reason = {
        GitHubAPIErrorKind.RATE_LIMITED: GitReason.RATE_LIMITED,
        GitHubAPIErrorKind.AUTHENTICATION_REQUIRED: GitReason.AUTHENTICATION_FAILED,
        GitHubAPIErrorKind.PERMISSION_DENIED: GitReason.AUTHORIZATION_DENIED,
        GitHubAPIErrorKind.NOT_FOUND: GitReason.REMOTE_NOT_FOUND,
        GitHubAPIErrorKind.CONFLICT: GitReason.NON_FAST_FORWARD,
        GitHubAPIErrorKind.VALIDATION_OR_STALE_SHA: GitReason.NON_FAST_FORWARD,
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

    # Do not automatically retry a write with an ambiguous remote outcome.
    repository.run("push", remote, f"HEAD:{branch}")


def verify_remote_branch(
    repository: GitRepository,
    *,
    remote: str,
    branch: str,
) -> str:
    """Read back the remote branch using a read-only Git operation."""
    output = repository.run(
        "ls-remote",
        remote,
        f"refs/heads/{branch}",
    ).stdout.strip()

    if not output:
        raise ValueError("Remote branch could not be verified.")

    return output.split("\t", 1)[0]
