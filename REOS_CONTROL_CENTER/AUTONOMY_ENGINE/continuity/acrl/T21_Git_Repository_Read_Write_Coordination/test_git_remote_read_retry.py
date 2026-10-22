from __future__ import annotations

from types import SimpleNamespace

import pytest

from AUTONOMY_ENGINE.continuity.acrl.T21_Git_Repository_Read_Write_Coordination.git_models import (
    GitPolicy,
)
from AUTONOMY_ENGINE.continuity.acrl.T21_Git_Repository_Read_Write_Coordination.git_push import (
    push_branch,
    verify_remote_branch,
)


SHA = "a" * 40


def valid_ref(sha: str = SHA, ref: str = "refs/heads/main") -> str:
    return f"{sha}\t{ref}\n"


class FakeRemoteRepository:
    def __init__(self, *outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def run(self, *args, **kwargs):
        self.calls.append(args)

        if not self.outcomes:
            raise AssertionError("Unexpected extra remote operation.")

        outcome = self.outcomes.pop(0)

        if isinstance(outcome, BaseException):
            raise outcome

        return SimpleNamespace(stdout=outcome)

    def remote_names(self):
        return ("origin",)


class HeaderError(RuntimeError):
    def __init__(self, message: str, headers: dict[str, str]):
        super().__init__(message)
        self.headers = headers


def test_503_readback_retries_and_returns_exact_commit():
    repository = FakeRemoteRepository(
        RuntimeError("HTTP 503 Service Unavailable"),
        valid_ref(),
    )
    delays = []

    result = verify_remote_branch(
        repository,
        remote="origin",
        branch="main",
        sleep_fn=delays.append,
    )

    assert result == SHA
    assert len(repository.calls) == 2
    assert delays == [0.25]
    assert repository.calls[0] == (
        "ls-remote",
        "origin",
        "refs/heads/main",
    )


def test_rate_limit_readback_honors_retry_after():
    repository = FakeRemoteRepository(
        HeaderError(
            "HTTP 403 API rate limit exceeded",
            {"Retry-After": "12"},
        ),
        valid_ref(),
    )
    delays = []

    result = verify_remote_branch(
        repository,
        remote="origin",
        branch="main",
        sleep_fn=delays.append,
    )

    assert result == SHA
    assert len(repository.calls) == 2
    assert delays == [12.0]


def test_403_permission_denial_fails_without_retry():
    repository = FakeRemoteRepository(
        RuntimeError(
            "HTTP 403 Resource not accessible by integration"
        )
    )
    delays = []

    with pytest.raises(RuntimeError, match="Resource not accessible"):
        verify_remote_branch(
            repository,
            remote="origin",
            branch="main",
            sleep_fn=delays.append,
        )

    assert len(repository.calls) == 1
    assert delays == []


def test_404_fails_without_retry_or_branch_switch():
    repository = FakeRemoteRepository(
        RuntimeError("HTTP 404 Not Found")
    )
    delays = []

    with pytest.raises(RuntimeError, match="404"):
        verify_remote_branch(
            repository,
            remote="origin",
            branch="main",
            sleep_fn=delays.append,
        )

    assert len(repository.calls) == 1
    assert repository.calls[0] == (
        "ls-remote",
        "origin",
        "refs/heads/main",
    )
    assert delays == []


def test_timeout_readback_uses_one_bounded_retry():
    repository = FakeRemoteRepository(
        RuntimeError("Git command timed out: ls-remote"),
        valid_ref(),
    )
    delays = []

    result = verify_remote_branch(
        repository,
        remote="origin",
        branch="main",
        sleep_fn=delays.append,
    )

    assert result == SHA
    assert len(repository.calls) == 2
    assert len(delays) == 1


def test_503_stops_after_two_retries():
    repository = FakeRemoteRepository(
        RuntimeError("HTTP 503 Service Unavailable"),
        RuntimeError("HTTP 503 Service Unavailable"),
        RuntimeError("HTTP 503 Service Unavailable"),
    )
    delays = []

    with pytest.raises(RuntimeError, match="503"):
        verify_remote_branch(
            repository,
            remote="origin",
            branch="main",
            sleep_fn=delays.append,
        )

    assert len(repository.calls) == 3
    assert delays == [0.25, 0.5]


def test_unknown_error_fails_closed_without_retry():
    repository = FakeRemoteRepository(
        RuntimeError("Unclassified remote failure")
    )
    delays = []

    with pytest.raises(RuntimeError, match="Unclassified"):
        verify_remote_branch(
            repository,
            remote="origin",
            branch="main",
            sleep_fn=delays.append,
        )

    assert len(repository.calls) == 1
    assert delays == []


def test_empty_readback_is_not_retried():
    repository = FakeRemoteRepository("")
    delays = []

    with pytest.raises(ValueError, match="could not be verified"):
        verify_remote_branch(
            repository,
            remote="origin",
            branch="main",
            sleep_fn=delays.append,
        )

    assert len(repository.calls) == 1
    assert delays == []


def test_wrong_returned_ref_is_rejected():
    repository = FakeRemoteRepository(
        valid_ref(ref="refs/heads/another-branch")
    )

    with pytest.raises(ValueError, match="different ref"):
        verify_remote_branch(
            repository,
            remote="origin",
            branch="main",
            sleep_fn=lambda _: None,
        )

    assert len(repository.calls) == 1


@pytest.mark.parametrize("retry_count", [-1, 3, True, 1.5])
def test_retry_budget_outside_policy_is_rejected(retry_count):
    repository = FakeRemoteRepository(valid_ref())

    with pytest.raises(ValueError, match="max_retries"):
        verify_remote_branch(
            repository,
            remote="origin",
            branch="main",
            max_retries=retry_count,
            sleep_fn=lambda _: None,
        )

    assert repository.calls == []


def test_push_write_is_not_automatically_retried():
    repository = FakeRemoteRepository(
        RuntimeError("HTTP 503 Service Unavailable")
    )

    with pytest.raises(RuntimeError, match="503"):
        push_branch(
            repository,
            remote="origin",
            branch="main",
            policy=GitPolicy(),
        )

    assert len(repository.calls) == 1
    assert repository.calls[0] == (
        "push",
        "origin",
        "HEAD:main",
    )
