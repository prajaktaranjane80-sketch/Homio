from __future__ import annotations

import pytest

from .git_models import GitPolicy
from .git_policy import validate_policy
from .git_scope import is_safe_repository_path


def test_safe_path():
    assert is_safe_repository_path("src/app.py")


def test_absolute_path_rejected():
    assert not is_safe_repository_path("/etc/passwd")


def test_parent_path_rejected():
    assert not is_safe_repository_path("../secret.py")


@pytest.mark.parametrize(
    "path",
    [
        "C:/secret.py",
        r"C:\secret.py",
        "//server/share/file.py",
        "src//app.py",
        "src/./app.py",
        "src/../secret.py",
        "src/app.py/",
        " src/app.py",
        "src/app.py ",
        "src/\x00app.py",
        "src/\napp.py",
        "",
    ],
)
def test_unsafe_repository_paths_are_rejected(path: str):
    assert not is_safe_repository_path(path)


@pytest.mark.parametrize(
    "path",
    [
        "src/app.py",
        "REOS_CONTROL_CENTER/Frontend/src/app/page.tsx",
        "src/file name.py",
    ],
)
def test_valid_repository_paths_are_accepted(path: str):
    assert is_safe_repository_path(path)


def test_force_push_policy_rejected():
    policy = GitPolicy(
        allow_force_push=True,
    )

    with pytest.raises(ValueError):
        validate_policy(policy)
