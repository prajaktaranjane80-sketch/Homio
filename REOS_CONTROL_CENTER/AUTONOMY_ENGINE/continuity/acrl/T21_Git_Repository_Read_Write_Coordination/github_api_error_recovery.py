"""T21 safe, classified GitHub API recovery.

This module classifies errors and returns a typed recovery decision.
It never bypasses authentication, permissions, repository access,
branch protection, rulesets, or rate limits.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from datetime import timezone
from email.utils import parsedate_to_datetime
from enum import Enum
from pathlib import PurePosixPath
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
    CONFIRMED_NOT_FOUND = "CONFIRMED_NOT_FOUND"
    STALE_SHA_NEEDS_RECONCILIATION = (
        "STALE_SHA_NEEDS_RECONCILIATION"
    )
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


@dataclass(frozen=True, slots=True)
class GitHubNotFoundReadbackEvidence:
    """Evidence from successful, authorized read-only API lookups.

    Populate this from actual responses through the already-approved
    connection. It does not make network requests or authenticate the
    principal by itself.
    """

    original_status_code: int
    original_authenticated_identity: str
    original_identity_verified: bool
    authenticated_identity: str
    identity_verified: bool
    owner: str
    repository: str
    ref: str
    target_path: str
    repository_status_code: int
    ref_status_code: int
    parent_tree_path: str
    parent_tree_status_code: int
    parent_tree_entry_names: tuple[str, ...]


def _ambiguous_not_found(action: str) -> GitHubAPIRecovery:
    return GitHubAPIRecovery(
        kind=GitHubAPIErrorKind.NOT_FOUND,
        outcome=GitHubAPIOutcome.AMBIGUOUS_NOT_FOUND,
        retryable=False,
        requires_readback=True,
        retry_after_seconds=None,
        max_retries=0,
        action=action,
    )


def resolve_github_not_found(
    evidence: GitHubNotFoundReadbackEvidence | None,
    *,
    expected_owner: str,
    expected_repository: str,
    expected_ref: str,
    expected_path: str,
) -> GitHubAPIRecovery:
    """Resolve a 404 only after matching positive access/readback proof.

    A plain 404 always remains ambiguous. Confirmation requires that the
    original response was exactly 404, both identity observations are
    verified and identical, repository and ref reads succeeded, and the
    exact parent-tree read succeeded with the target absent. This function
    does not authorize writes or choose a fallback branch.
    """
    if (
        not isinstance(evidence, GitHubNotFoundReadbackEvidence)
        or isinstance(evidence.original_status_code, bool)
        or not isinstance(evidence.original_status_code, int)
        or evidence.original_status_code != 404
        or not isinstance(evidence.original_identity_verified, bool)
        or evidence.original_identity_verified is not True
        or not isinstance(evidence.identity_verified, bool)
        or evidence.identity_verified is not True
        or not isinstance(evidence.original_authenticated_identity, str)
        or not isinstance(evidence.authenticated_identity, str)
        or not evidence.original_authenticated_identity.strip()
        or evidence.original_authenticated_identity
        != evidence.authenticated_identity
    ):
        return _ambiguous_not_found(
            "AMBIGUOUS_NOT_FOUND: an original 404 plus verified, matching "
            "identity and readback evidence are required. Keep the 404 "
            "unresolved; do not retry blindly, switch branches, or write."
        )

    expected_values = (
        expected_owner,
        expected_repository,
        expected_ref,
        expected_path,
    )
    evidence_values = (
        evidence.owner,
        evidence.repository,
        evidence.ref,
        evidence.target_path,
    )
    if (
        any(
            not isinstance(value, str)
            or not value
            or value != value.strip()
            for value in expected_values + evidence_values
        )
        or evidence_values != expected_values
    ):
        return _ambiguous_not_found(
            "AMBIGUOUS_NOT_FOUND: readback owner/repository, ref or exact "
            "case-sensitive path does not match the request. Reconcile the "
            "target; never silently switch branches."
        )

    if (
        expected_path.startswith("/")
        or "\\" in expected_path
        or any(
            part in {"", ".", ".."}
            for part in expected_path.split("/")
        )
    ):
        return _ambiguous_not_found(
            "AMBIGUOUS_NOT_FOUND: target path is not a canonical repository "
            "relative path; do not normalize it into a different target."
        )

    path = PurePosixPath(expected_path)
    expected_parent = path.parent.as_posix()
    if expected_parent == ".":
        expected_parent = ""

    if (
        evidence.parent_tree_path != expected_parent
        or isinstance(evidence.repository_status_code, bool)
        or not isinstance(evidence.repository_status_code, int)
        or evidence.repository_status_code != 200
        or isinstance(evidence.ref_status_code, bool)
        or not isinstance(evidence.ref_status_code, int)
        or evidence.ref_status_code != 200
        or isinstance(evidence.parent_tree_status_code, bool)
        or not isinstance(evidence.parent_tree_status_code, int)
        or evidence.parent_tree_status_code != 200
        or not isinstance(evidence.parent_tree_entry_names, tuple)
    ):
        return _ambiguous_not_found(
            "AMBIGUOUS_NOT_FOUND: authorized repository, ref and exact "
            "parent-tree readback did not all return verified success. "
            "The original 404 remains unresolved."
        )

    names = evidence.parent_tree_entry_names
    if any(
        not isinstance(name, str)
        or not name
        or name in {".", ".."}
        or "/" in name
        or "\\" in name
        for name in names
    ):
        return _ambiguous_not_found(
            "AMBIGUOUS_NOT_FOUND: parent-tree readback entries are invalid; "
            "absence cannot be safely confirmed."
        )

    if path.name in names:
        return _ambiguous_not_found(
            "AMBIGUOUS_NOT_FOUND: the independently read parent tree still "
            "contains the requested target, so the 404 conflicts with "
            "readback. Check endpoint, method and encoding; do not write."
        )

    return GitHubAPIRecovery(
        kind=GitHubAPIErrorKind.NOT_FOUND,
        outcome=GitHubAPIOutcome.CONFIRMED_NOT_FOUND,
        retryable=False,
        requires_readback=False,
        retry_after_seconds=None,
        max_retries=0,
        action=(
            "CONFIRMED_NOT_FOUND: the same verified identity can access the "
            "exact repository and ref, and the successful parent-tree "
            "readback confirms the exact target path is absent. This confirms "
            "absence only; it does not authorize creating or overwriting "
            "anything. Any subsequent write still requires normal T18 "
            "authorization, T20 verification, and T21 scope/branch checks."
        ),
    )


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
    """Read Retry-After or the primary-rate-limit reset timestamp."""
    retry_after = headers.get("retry-after", "")

    if retry_after:
        try:
            value = float(retry_after)
            if math.isfinite(value):
                return max(0, math.ceil(value))
        except (TypeError, ValueError, OverflowError):
            pass

        try:
            retry_at = parsedate_to_datetime(retry_after)
            if retry_at.tzinfo is None:
                retry_at = retry_at.replace(tzinfo=timezone.utc)

            current = (
                int(time.time())
                if now_epoch is None
                else int(now_epoch)
            )
            return max(
                0,
                math.ceil(retry_at.timestamp() - current),
            )
        except (TypeError, ValueError, OverflowError):
            pass

    if headers.get("x-ratelimit-remaining") == "0":
        reset = headers.get("x-ratelimit-reset", "")

        if reset:
            try:
                current = (
                    int(time.time())
                    if now_epoch is None
                    else int(now_epoch)
                )
                return max(
                    0,
                    math.ceil(float(reset) - current),
                )
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

        # A secondary-rate-limit response without usable timing
        # information must wait at least one minute.
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
                "RATE_LIMITED: wait for the server-directed delay. "
                "Safe reads may use at most one bounded retry. Writes "
                "must not be automatically retried; read back the target "
                "first and resolve the write outcome. If the limit "
                "persists, stop and require a later retry."
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
                "AUTHENTICATION_REQUIRED: verify the authenticated "
                "identity, session validity, and endpoint permissions "
                "through the approved connection. Do not rotate "
                "credentials blindly."
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
                "Verify the authorized connection, access to the exact "
                "repository, required endpoint permissions (Contents: "
                "write for content writes), and branch protection or "
                "rulesets. If access is not granted, stop and use an "
                "already-authorized owner workflow."
            ),
        )

    if status_code == 404:
        return GitHubAPIRecovery(
            kind=GitHubAPIErrorKind.NOT_FOUND,
            outcome=GitHubAPIOutcome.AMBIGUOUS_NOT_FOUND,
            retryable=False,
            requires_readback=True,
            retry_after_seconds=None,
            max_retries=0,
            action=(
                "AMBIGUOUS_NOT_FOUND: a single 404 does not prove that "
                "the resource is absent; GitHub may return 404 when "
                "credentials cannot access a private resource. Verify "
                "the authenticated identity and repository access first, "
                "then exact owner/repo, HTTP endpoint and method, "
                "branch/ref, path spelling/case, parent directory, and "
                "URL encoding. Use an authorized read-only metadata or "
                "parent-tree check to confirm absence. "
                "Never silently switch branches. Do not sweep guessed "
                "paths or repeat the same failed request blindly."
            ),
        )

    if status_code in {409, 422}:
        return GitHubAPIRecovery(
            kind=(
                GitHubAPIErrorKind.CONFLICT
                if status_code == 409
                else GitHubAPIErrorKind.VALIDATION_OR_STALE_SHA
            ),
            outcome=(
                GitHubAPIOutcome.STALE_SHA_NEEDS_RECONCILIATION
            ),
            retryable=False,
            requires_readback=True,
            retry_after_seconds=None,
            max_retries=0,
            action=(
                "STALE_SHA_NEEDS_RECONCILIATION: reread the live branch "
                "HEAD, target path, and current blob SHA. Rebuild the "
                "change from the verified baseline. Never guess a SHA, "
                "overwrite newer content, or force-push around conflict."
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
                "backoff retries for a safe read. For a write, read back "
                "the exact branch, commit, and path before deciding what "
                "to do next."
                if safe_to_retry
                else
                "RECOVERY_REQUIRED_USER_ACTION: the write outcome may "
                "be ambiguous. Read back the exact target before "
                "proceeding; do not automatically repeat the write."
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
                    "TRANSIENT_FAILURE_RETRYABLE: one bounded retry "
                    "is allowed for a safe read."
                    if safe_to_retry
                    else
                    "RECOVERY_REQUIRED_USER_ACTION: read back remote "
                    "state before retrying because the write may "
                    "already have succeeded."
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
                    "TRANSIENT_FAILURE_RETRYABLE: one bounded retry "
                    "is allowed for a safe read."
                    if safe_to_retry
                    else
                    "RECOVERY_REQUIRED_USER_ACTION: independently read "
                    "remote state before retrying the write."
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
            "FAIL_CLOSED: the error is unclassified. Do not retry "
            "blindly. Inspect it safely and independently check remote "
            "state if a write might have been attempted."
        ),
    )


__all__ = [
    "GitHubAPIErrorKind",
    "GitHubAPIOutcome",
    "GitHubAPIRecovery",
    "GitHubNotFoundReadbackEvidence",
    "classify_github_api_failure",
    "resolve_github_not_found",
]
