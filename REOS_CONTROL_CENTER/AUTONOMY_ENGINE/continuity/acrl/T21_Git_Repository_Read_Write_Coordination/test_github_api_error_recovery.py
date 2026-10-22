from __future__ import annotations

from datetime import datetime, timezone
from email.utils import format_datetime

import pytest

from .github_api_error_recovery import (
    GitHubAPIErrorKind,
    GitHubAPIOutcome,
    classify_github_api_failure,
)
from .git_models import GitReason
from .git_push import classify_git_push_error


def test_403_primary_rate_limit_uses_server_headers():
    result = classify_github_api_failure(
        403,
        headers={
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": "1700000060",
            "Retry-After": "12",
        },
        operation_is_write=False,
        now_epoch=1700000000,
    )

    assert result.kind is GitHubAPIErrorKind.RATE_LIMITED
    assert result.outcome is GitHubAPIOutcome.RATE_LIMITED
    assert result.retryable is True
    assert result.max_retries == 1
    assert result.retry_after_seconds == 12


def test_403_retry_after_header_identifies_rate_limit():
    result = classify_github_api_failure(
        403,
        headers={"Retry-After": "15"},
        message="Forbidden",
        operation_is_write=False,
    )

    assert result.kind is GitHubAPIErrorKind.RATE_LIMITED
    assert result.outcome is GitHubAPIOutcome.RATE_LIMITED
    assert result.retryable is True
    assert result.retry_after_seconds == 15


def test_secondary_rate_limit_without_retry_after_waits_at_least_60_seconds():
    result = classify_github_api_failure(
        403,
        message="You have exceeded a secondary rate limit.",
        operation_is_write=False,
    )

    assert result.kind is GitHubAPIErrorKind.RATE_LIMITED
    assert result.retryable is True
    assert result.max_retries == 1
    assert result.retry_after_seconds == 60


def test_primary_rate_limit_reset_uses_supplied_clock():
    result = classify_github_api_failure(
        403,
        headers={
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": "1700000090",
        },
        now_epoch=1700000000,
        operation_is_write=False,
    )

    assert result.kind is GitHubAPIErrorKind.RATE_LIMITED
    assert result.retry_after_seconds == 90


def test_retry_after_http_date_is_parsed():
    now = 1700000000
    retry_at = datetime.fromtimestamp(
        now + 30,
        tz=timezone.utc,
    )

    result = classify_github_api_failure(
        429,
        headers={
            "Retry-After": format_datetime(retry_at, usegmt=True),
        },
        now_epoch=now,
        operation_is_write=False,
    )

    assert result.kind is GitHubAPIErrorKind.RATE_LIMITED
    assert result.retry_after_seconds == 30


def test_403_permission_denial_is_not_retried():
    result = classify_github_api_failure(
        403,
        message="Resource not accessible by integration",
        operation_is_write=True,
    )

    assert result.kind is GitHubAPIErrorKind.PERMISSION_DENIED
    assert result.outcome is GitHubAPIOutcome.PERMISSION_DENIED
    assert result.retryable is False
    assert result.max_retries == 0
    assert result.requires_readback is True
    assert "do not retry" in result.action.lower()
    assert "contents: write" in result.action.lower()


def test_403_permission_denial_without_rate_limit_headers_stays_denied():
    result = classify_github_api_failure(
        403,
        headers={"X-RateLimit-Remaining": "100"},
        message="Resource not accessible by integration",
        operation_is_write=False,
    )

    assert result.kind is GitHubAPIErrorKind.PERMISSION_DENIED
    assert result.retryable is False
    assert result.max_retries == 0


def test_401_requires_user_action():
    result = classify_github_api_failure(
        401,
        operation_is_write=True,
    )

    assert (
        result.kind
        is GitHubAPIErrorKind.AUTHENTICATION_REQUIRED
    )
    assert (
        result.outcome
        is GitHubAPIOutcome.RECOVERY_REQUIRED_USER_ACTION
    )
    assert result.retryable is False
    assert result.max_retries == 0


def test_404_is_ambiguous_not_confirmed_absence():
    result = classify_github_api_failure(
        404,
        message="Not Found",
        operation_is_write=True,
    )

    assert result.kind is GitHubAPIErrorKind.NOT_FOUND
    assert result.outcome is GitHubAPIOutcome.AMBIGUOUS_NOT_FOUND
    assert result.retryable is False
    assert result.max_retries == 0
    assert result.requires_readback is True
    assert "private resource" in result.action.lower()
    assert "never" in result.action.lower()
    assert "silently switch branches" in result.action.lower()


def test_404_does_not_trigger_a_guessed_branch_or_path_retry():
    result = classify_github_api_failure(
        404,
        message="Path not found",
        operation_is_write=False,
    )

    assert result.outcome is GitHubAPIOutcome.AMBIGUOUS_NOT_FOUND
    assert result.retryable is False
    assert result.max_retries == 0


def test_409_requires_readback_and_reconciliation():
    result = classify_github_api_failure(
        409,
        operation_is_write=True,
    )

    assert result.kind is GitHubAPIErrorKind.CONFLICT
    assert (
        result.outcome
        is GitHubAPIOutcome.STALE_SHA_NEEDS_RECONCILIATION
    )
    assert result.requires_readback is True
    assert result.retryable is False
    assert result.max_retries == 0


def test_422_requires_current_sha_and_validation_check():
    result = classify_github_api_failure(
        422,
        operation_is_write=True,
    )

    assert (
        result.kind
        is GitHubAPIErrorKind.VALIDATION_OR_STALE_SHA
    )
    assert (
        result.outcome
        is GitHubAPIOutcome.STALE_SHA_NEEDS_RECONCILIATION
    )
    assert result.requires_readback is True
    assert result.retryable is False


def test_429_write_never_retries_automatically():
    result = classify_github_api_failure(
        429,
        headers={"Retry-After": "30"},
        operation_is_write=True,
    )

    assert result.kind is GitHubAPIErrorKind.RATE_LIMITED
    assert result.outcome is GitHubAPIOutcome.RATE_LIMITED
    assert result.retryable is False
    assert result.requires_readback is True
    assert result.max_retries == 0
    assert result.retry_after_seconds == 30


def test_server_error_allows_at_most_two_safe_read_retries():
    result = classify_github_api_failure(
        503,
        operation_is_write=False,
    )

    assert result.kind is GitHubAPIErrorKind.SERVER_ERROR
    assert (
        result.outcome
        is GitHubAPIOutcome.TRANSIENT_FAILURE_RETRYABLE
    )
    assert result.retryable is True
    assert result.max_retries == 2


def test_server_error_write_requires_readback():
    result = classify_github_api_failure(
        503,
        operation_is_write=True,
    )

    assert result.kind is GitHubAPIErrorKind.SERVER_ERROR
    assert (
        result.outcome
        is GitHubAPIOutcome.RECOVERY_REQUIRED_USER_ACTION
    )
    assert result.retryable is False
    assert result.requires_readback is True
    assert result.max_retries == 0


def test_timeout_during_write_requires_remote_readback():
    result = classify_github_api_failure(
        None,
        operation_is_write=True,
        transport_error="timeout",
    )

    assert result.kind is GitHubAPIErrorKind.TIMEOUT
    assert (
        result.outcome
        is GitHubAPIOutcome.RECOVERY_REQUIRED_USER_ACTION
    )
    assert result.retryable is False
    assert result.requires_readback is True
    assert result.max_retries == 0


def test_network_failure_allows_only_bounded_safe_read_retry():
    result = classify_github_api_failure(
        None,
        operation_is_write=False,
        transport_error="network connection failure",
    )

    assert result.kind is GitHubAPIErrorKind.NETWORK_FAILURE
    assert (
        result.outcome
        is GitHubAPIOutcome.TRANSIENT_FAILURE_RETRYABLE
    )
    assert result.retryable is True
    assert result.max_retries == 1


def test_tls_failure_fails_closed():
    result = classify_github_api_failure(
        None,
        operation_is_write=True,
        transport_error="TLS certificate verification failure",
    )

    assert result.kind is GitHubAPIErrorKind.TLS_FAILURE
    assert result.outcome is GitHubAPIOutcome.FAIL_CLOSED
    assert result.retryable is False
    assert result.max_retries == 0


def test_unknown_http_status_fails_closed():
    result = classify_github_api_failure(
        418,
        operation_is_write=False,
    )

    assert result.kind is GitHubAPIErrorKind.UNKNOWN
    assert result.outcome is GitHubAPIOutcome.FAIL_CLOSED
    assert result.retryable is False
    assert result.max_retries == 0


@pytest.mark.parametrize(
    "status_code",
    [True, 99, 600, "403"],
)
def test_invalid_http_status_is_rejected(status_code):
    with pytest.raises(ValueError, match="status code"):
        classify_github_api_failure(status_code)


def test_non_boolean_write_flag_is_rejected():
    with pytest.raises(ValueError, match="boolean"):
        classify_github_api_failure(
            503,
            operation_is_write="yes",
        )


def test_git_push_403_rate_limit_maps_to_rate_limit_reason():
    reason, explanation = classify_git_push_error(
        RuntimeError("HTTP 403 API rate limit exceeded")
    )

    assert reason is GitReason.RATE_LIMITED
    assert explanation


def test_git_push_403_permission_denial_maps_to_authorization_reason():
    reason, explanation = classify_git_push_error(
        RuntimeError("HTTP 403 Resource not accessible by integration")
    )

    assert reason is GitReason.AUTHORIZATION_DENIED
    assert explanation


def test_git_push_404_explains_that_resource_may_be_inaccessible():
    reason, explanation = classify_git_push_error(
        RuntimeError("HTTP 404 Not Found")
    )

    assert reason is GitReason.REMOTE_NOT_FOUND
    assert "ambiguous_not_found" in explanation.lower()
    assert "private resource" in explanation.lower()


def test_git_push_non_fast_forward_is_not_a_generic_network_error():
    reason, explanation = classify_git_push_error(
        RuntimeError("non-fast-forward: fetch first")
    )

    assert reason is GitReason.NON_FAST_FORWARD
    assert explanation


def test_git_push_tls_failure_fails_closed():
    reason, explanation = classify_git_push_error(
        RuntimeError("TLS certificate verify failed")
    )

    assert reason is GitReason.TLS_FAILURE
    assert explanation
