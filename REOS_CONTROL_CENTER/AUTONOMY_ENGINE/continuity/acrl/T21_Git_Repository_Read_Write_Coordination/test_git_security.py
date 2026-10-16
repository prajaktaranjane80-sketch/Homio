from __future__ import annotations

import pytest

from .git_models import GitPolicy
from .git_policy import (
    is_protected_path,
    validate_policy,
)
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
        ".reos_t21_transaction.lock",
        "data/state.json",
        "REOS_CONTROL_CENTER/data/state.json",
        "architecture/system.json",
        "REOS_CONTROL_CENTER/architecture/system.json",
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
        "T18_Safe_Execution_Authorization_Guard/authorization_models.py",
    ],
)
def test_protected_paths_are_rejected(path: str):
    assert is_protected_path(path, GitPolicy())


def test_force_push_policy_rejected():
    policy = GitPolicy(
        allow_force_push=True,
    )

    with pytest.raises(ValueError):
        validate_policy(policy)
