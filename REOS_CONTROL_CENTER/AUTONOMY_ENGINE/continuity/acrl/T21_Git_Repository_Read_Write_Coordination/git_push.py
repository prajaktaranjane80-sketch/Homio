from __future__ import annotations

from .git_models import GitPolicy, GitReason
from .git_repository import GitRepository


def classify_git_push_error(error: BaseException) -> tuple[GitReason, str]:
    """Classify remote errors without returning raw stderr or credentials."""
    message = str(error).lower()

    if "429" in message or "rate limit" in message or "too many requests" in message:
        return GitReason.RATE_LIMITED, "Remote rate limit reached; retry later."

    if "407" in message or "proxy authentication" in message:
        return GitReason.PROXY_AUTH_REQUIRED, "Proxy authentication is required."

    if (
        "401" in message
        or "authentication failed" in message
        or "invalid username or password" in message
        or "could not read username" in message
        or "terminal prompts disabled" in message
    ):
        return (
            GitReason.AUTHENTICATION_FAILED,
            "Remote authentication failed; verify the configured credential securely.",
        )

    if "404" in message or "repository not found" in message or "couldn't find remote ref" in message:
        return (
            GitReason.REMOTE_NOT_FOUND,
            "Remote repository or branch was not found; verify the remote URL and access.",
        )

    if (
        "403" in message
        or "permission denied" in message
        or "write access to repository not granted" in message
    ):
        return (
            GitReason.AUTHORIZATION_DENIED,
            "Remote rejected the operation for insufficient permission.",
        )

    if "non-fast-forward" in message or "fetch first" in message:
        return (
            GitReason.NON_FAST_FORWARD,
            "Remote branch moved; reconcile its current state before retrying.",
        )

    if (
        "tls" in message
        or "ssl certificate" in message
        or "certificate verify failed" in message
    ):
        return (
            GitReason.TLS_FAILURE,
            "TLS verification failed; inspect the trusted certificate configuration.",
        )

    if (
        "timed out" in message
        or "timeout" in message
        or "could not resolve host" in message
        or "could not resolve proxy" in message
        or "connection reset" in message
        or "network is unreachable" in message
        or "failed to connect" in message
    ):
        return (
            GitReason.NETWORK_FAILURE,
            "Remote network operation failed; verify connectivity and retry safely.",
        )

    return (
        GitReason.PUSH_REJECTED,
        "Remote Git operation was rejected; inspect trusted diagnostics without exposing credentials.",
    )


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

    # Do not retry a write whose remote completion could be ambiguous.
    repository.run("push", remote, f"HEAD:{branch}")


def verify_remote_branch(
    repository: GitRepository,
    *,
    remote: str,
    branch: str,
) -> str:
    """Verify the remote branch using a read-only Git operation."""
    output = repository.run(
        "ls-remote",
        remote,
        f"refs/heads/{branch}",
    ).stdout.strip()

    if not output:
        raise ValueError("Remote branch could not be verified.")

    return output.split("\t", 1)[0]