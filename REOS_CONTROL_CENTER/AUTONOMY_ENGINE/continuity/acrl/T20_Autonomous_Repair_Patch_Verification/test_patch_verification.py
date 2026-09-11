from __future__ import annotations

from pathlib import Path

from .patch_verification import (
    syntax_check,
    tree_fingerprint,
)


def test_python_syntax_passes(tmp_path: Path):
    source = tmp_path / "src"
    source.mkdir()

    file = source / "app.py"
    file.write_text(
        "VALUE = 1\n",
        encoding="utf-8",
    )

    assert syntax_check(
        tmp_path,
        ("src/app.py",),
    )


def test_python_syntax_fails(tmp_path: Path):
    source = tmp_path / "src"
    source.mkdir()

    file = source / "app.py"
    file.write_text(
        "def broken(:\n",
        encoding="utf-8",
    )

    assert not syntax_check(
        tmp_path,
        ("src/app.py",),
    )


def test_tree_fingerprint_is_deterministic(
    tmp_path: Path,
):
    file = tmp_path / "a.txt"

    file.write_text(
        "hello",
        encoding="utf-8",
    )

    first = tree_fingerprint(
        tmp_path
    )
    second = tree_fingerprint(
        tmp_path
    )

    assert first == second
