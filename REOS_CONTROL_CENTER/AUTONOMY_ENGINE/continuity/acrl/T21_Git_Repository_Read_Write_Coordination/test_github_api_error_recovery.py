from __future__ import annotations

import pytest

from .github_api_error_recovery import (
    GitHubAPIErrorKind,
    classify_github_api_failure,
)
from .git_models import GitReason
from .git_push import classify_git_push_error


def test_403_rate_limit_allows_bounded_retry_for_safe_read():
    result = classify_github_api_failure(
        403,
        headers={
            "X-RateLimit-Remaining": "0",
            "Retry-After": "12",
        },
        operation_is_write=False,
    )

    assert result.kind is GitHubAPIErrorKind.RATE_LIMITED
    assert result.retryable is True
    assert result.max_retries == 1
    assert result.retry_after_seconds == 12


def test_403_permission_denial_is_not_a_rate_limit():
    result = classify_github_api_failure(
        403,
        message="Resource not accessible by integration",
        operation_is_write=True,
    )

    assert result.kind is GitHubAPIErrorKind.PERMISSION_DENIED
    assert result.retryable is False
    assert result.max_retries == 0


def test_401_requires_authentication_review():
    result = classify_github_api_failure(
        401,
        operation_is_write=True,
    )

    assert result.kind is GitHubAPIErrorKind.AUTHENTICATION_REQUIRED
    assert result.retryable is False
    assert result.max_retries == 0


def test_404_never_silently_switches_branches():
    result = classify_github_api_failure(
        404,
        operation_is_write=True,
    )

    assert result.kind is GitHubAPIErrorKind.NOT_FOUND
    assert result.retryable is False
    assert "never silently switch branches" in result.action.lower()


def test_409_requires_readback_without_retry():
    result = classify_github_api_failure(
        409,
        operation_is_write=True,
    )

    assert result.kind is GitHubAPIErrorKind.CONFLICT
    assert result.requires_readback is True
    assert result.retryable is False
    assert result.max_retries == 0


def test_422_requires_current_state_validation():
    result = classify_github_api_failure(
        422,
        operation_is_write=True,
    )

    assert result.kind is GitHubAPIErrorKind.VALIDATION_OR_STALE_SHA
    assert result.requires_readback is True
    assert result.retryable is False


def test_429_write_requires_readback_and_no_automatic_retry():
    result = classify_github_api_failure(
        429,
        headers={"Retry-After": "30"},
        operation_is_write=True,
    )

    assert result.kind is GitHubAPIErrorKind.RATE_LIMITED
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
    assert result.retryable is True
    assert result.max_retries == 2


def test_server_error_write_requires_readback():
    result = classify_github_api_failure(
        503,
        operation_is_write=True,
    )

    assert result.kind is GitHubAPIErrorKind.SERVER_ERROR
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
    assert result.retryable is True
    assert result.max_retries == 1


def test_tls_failure_fails_closed():
    result = classify_github_api_failure(
        None,
        operation_is_write=True,
        transport_error="tls certificate verification failure",
    )

    assert result.kind is GitHubAPIErrorKind.TLS_FAILURE
    assert result.retryable is False
    assert result.max_retries == 0


def test_unknown_http_status_fails_closed():
    result = classify_github_api_failure(
        418,
        operation_is_write=False,
    )

    assert result.kind is GitHubAPIErrorKind.UNKNOWN
    assert result.retryable is False
    assert result.max_retries == 0


@pytest.mark.parametrize("status_code", [True, 99, 600, "403"])
def test_invalid_http_status_is_rejected(status_code):
    with pytest.raises(ValueError):
        classify_github_api_failure(status_code)


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
