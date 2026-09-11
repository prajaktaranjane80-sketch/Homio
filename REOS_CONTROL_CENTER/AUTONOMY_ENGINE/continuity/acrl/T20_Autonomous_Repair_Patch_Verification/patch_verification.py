from __future__ import annotations

import ast
import hashlib
from pathlib import Path

from .repair_identity import fingerprint
from .repair_models import (
    PatchVerification,
    RepairReason,
    RepairRequest,
    VerificationEvidence,
)
from .repair_scope import patch_paths


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def tree_fingerprint(
    root: Path | str,
) -> str:
    base = Path(root).resolve()

    entries: list[dict[str, str]] = []

    for path in sorted(
        base.rglob("*")
    ):
        if not path.is_file():
            continue

        if any(
            item in {
                ".git",
                ".pytest_cache",
                "__pycache__",
                ".venv",
                "venv",
                "node_modules",
            }
            for item in path.parts
        ):
            continue

        relative = path.relative_to(base).as_posix()

        entries.append(
            {
                "path": relative,
                "sha256": _sha256_file(path),
            }
        )

    return fingerprint(entries)


def syntax_check(
    workspace: Path | str,
    paths: tuple[str, ...],
) -> bool:
    root = Path(workspace).resolve()

    for relative in paths:
        if not relative.endswith(".py"):
            continue

        path = root / relative

        if not path.is_file():
            return False

        try:
            ast.parse(
                path.read_text(
                    encoding="utf-8"
                ),
                filename=str(path),
            )
        except (
            OSError,
            UnicodeError,
            SyntaxError,
        ):
            return False

    return True


def verify_patch(
    *,
    workspace: Path | str,
    request: RepairRequest,
    evidence: VerificationEvidence,
) -> PatchVerification:
    changed_paths = tuple(
        sorted(
            patch_paths(
                request.candidate_patch
            )
        )
    )

    syntax_passed = syntax_check(
        workspace,
        changed_paths,
    )

    passed = (
        syntax_passed
        and evidence.syntax_passed
        and evidence.tests_passed is True
        and evidence.regression_passed is True
    )

    if not syntax_passed:
        reason = RepairReason.SYNTAX_FAILURE
    elif evidence.tests_passed is not True:
        reason = RepairReason.TEST_FAILURE
    elif evidence.regression_passed is not True:
        reason = RepairReason.REGRESSION_FAILURE
    elif not passed:
        reason = RepairReason.VERIFICATION_REQUIRED
    else:
        reason = RepairReason.VALID

    return PatchVerification(
        passed=passed,
        changed_paths=changed_paths,
        patch_fingerprint=fingerprint(
            request.candidate_patch
        ),
        final_tree_fingerprint=tree_fingerprint(
            workspace
        ),
        evidence=evidence,
        reason=reason,
    )
