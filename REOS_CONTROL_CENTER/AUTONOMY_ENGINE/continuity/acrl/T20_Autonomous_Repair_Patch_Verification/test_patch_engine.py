from __future__ import annotations

from pathlib import Path

import pytest

from .patch_engine import (
    apply_patch,
    patch_fingerprint,
)
from .repair_models import RepairRequest
from .repair_workspace import (
    create_isolated_workspace,
    discard_workspace,
)


def make_request(patch: str):
    return RepairRequest(
        repair_id="repair-002",
        authorization_fingerprint="a" * 64,
        authorization_nonce="nonce-002",
        diagnosis_fingerprint="b" * 64,
        impact_fingerprint="c" * 64,
        baseline_fingerprint="d" * 64,
        allowed_paths=("src/app.py",),
        forbidden_paths=(),
        candidate_patch=patch,
    )


def test_patch_application_in_isolated_workspace(tmp_path: Path):
    source = tmp_path / "src"
    source.mkdir()

    original = source / "app.py"
    original.write_text(
        "VALUE = 1\n",
        encoding="utf-8",
    )

    workspace = create_isolated_workspace(
        tmp_path
    )

    patch = (
        "--- a/src/app.py\n"
        "+++ b/src/app.py\n"
        "@@ -1 +1 @@\n"
        "-VALUE = 1\n"
        "+VALUE = 2\n"
    )

    try:
        request = make_request(patch)

        paths = apply_patch(
            workspace,
            request,
        )

        assert paths == (
            "src/app.py",
        )

        assert (
            (
                workspace
                / "src"
                / "app.py"
            ).read_text(
                encoding="utf-8"
            )
            == "VALUE = 2\n"
        )

        assert (
            original.read_text(
                encoding="utf-8"
            )
            == "VALUE = 1\n"
        )
    finally:
        discard_workspace(workspace)


def test_patch_fingerprint_is_stable():
    patch = (
        "--- a/src/app.py\n"
        "+++ b/src/app.py\n"
    )

    assert patch_fingerprint(patch) == (
        patch_fingerprint(patch)
    )


def test_invalid_patch_is_rejected(tmp_path: Path):
    source = tmp_path / "src"
    source.mkdir()

    (source / "app.py").write_text(
        "VALUE = 1\n",
        encoding="utf-8",
    )

    workspace = create_isolated_workspace(
        tmp_path
    )

    try:
        request = make_request(
            "this is not a unified diff"
        )

        with pytest.raises(Exception):
            apply_patch(
                workspace,
                request,
            )
    finally:
        discard_workspace(workspace)
