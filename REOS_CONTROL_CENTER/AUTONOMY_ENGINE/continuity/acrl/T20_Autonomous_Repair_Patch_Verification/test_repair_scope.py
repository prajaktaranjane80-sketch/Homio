from __future__ import annotations

import pytest

from .repair_models import RepairPolicy, RepairRequest
from .repair_scope import (
    is_safe_relative_path,
    patch_paths,
    validate_scope,
)


def make_request(
    patch: str,
    allowed: tuple[str, ...],
):
    return RepairRequest(
        repair_id="repair-001",
        authorization_fingerprint="a" * 64,
        authorization_nonce="nonce-001",
        diagnosis_fingerprint="b" * 64,
        impact_fingerprint="c" * 64,
        baseline_fingerprint="d" * 64,
        allowed_paths=allowed,
        forbidden_paths=(),
        candidate_patch=patch,
    )


def _single_file_patch(path: str) -> str:
    return (
        f"--- a/{path}\n"
        f"+++ b/{path}\n"
        "@@ -1 +1 @@\n"
        "-old\n"
        "+new\n"
    )


def test_patch_paths_are_deterministic():
    assert patch_paths(
        _single_file_patch("src/b.py")
    ) == ("src/b.py",)


def test_scope_accepts_authorized_path():
    request = make_request(
        _single_file_patch("src/b.py"),
        ("src/b.py",),
    )

    assert validate_scope(
        request,
        RepairPolicy(),
    ) == ("src/b.py",)


def test_scope_blocks_escape():
    request = make_request(
        _single_file_patch("src/other.py"),
        ("src/b.py",),
    )

    with pytest.raises(ValueError):
        validate_scope(request, RepairPolicy())


@pytest.mark.parametrize(
    "path",
    [
        "data/state.json",
        "DATA/STATE.JSON",
        "architecture/example.json",
        "REOS_CONTROL_CENTER/architecture/example.json",
        "AUTONOMY_ENGINE/continuity/acrl/"
        "T18_Safe_Execution_Authorization_Guard/example.py",
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
        "T18_Safe_Execution_Authorization_Guard/example.py",
        ".git/config",
        ".gitignore",
        ".gitmodules",
    ],
)
def test_scope_blocks_protected_paths(path: str):
    request = make_request(
        _single_file_patch(path),
        (path,),
    )

    with pytest.raises(ValueError):
        validate_scope(request, RepairPolicy())


@pytest.mark.parametrize(
    "path",
    [
        "C:/secret.py",
        r"C:\secret.py",
        "/etc/passwd",
        "../secret.py",
        "src/../secret.py",
        "src//file.py",
        "src/./file.py",
        "src/file.py/",
        " src/file.py",
        "src/file.py ",
        "src/\x00file.py",
        "src/\nfile.py",
    ],
)
def test_unsafe_relative_paths_are_rejected(path: str):
    assert not is_safe_relative_path(path)


@pytest.mark.parametrize(
    "path",
    [
        "src/app.py",
        "REOS_CONTROL_CENTER/Frontend/src/app/page.tsx",
        "src/file name.py",
    ],
)
def test_valid_relative_paths_are_accepted(path: str):
    assert is_safe_relative_path(path)
