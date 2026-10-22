from __future__ import annotations

import ast
import hashlib
import re
from pathlib import Path

from .repair_identity import fingerprint, text_fingerprint
from .repair_models import (
    PatchVerification,
    RepairReason,
    RepairRequest,
    VerificationEvidence,
)
from .repair_scope import patch_paths


_SHA1 = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_PYTHON_SUFFIXES = frozenset({".py", ".pyw"})


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_fingerprint(root: Path | str) -> str:
    base = Path(root).resolve()
    entries: list[dict[str, str]] = []

    for path in sorted(base.rglob("*")):
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

        # Execution-time coordination artifact, not verified source.
        if relative == ".reos_t21_transaction.lock":
            continue

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
    """Check Python syntax locally; external evidence covers other formats."""
    root = Path(workspace).resolve()

    for relative in paths:
        if Path(relative).suffix.lower() not in _PYTHON_SUFFIXES:
            continue

        path = root / relative
        try:
            path.resolve().relative_to(root)
        except ValueError:
            return False

        if path.is_symlink() or not path.is_file():
            return False

        try:
            ast.parse(
                path.read_text(encoding="utf-8"),
                filename=str(path),
            )
        except (OSError, UnicodeError, SyntaxError):
            return False

    return True


def external_evidence_fingerprint(
    evidence: VerificationEvidence,
) -> str:
    """Bind external verification metadata and verdicts into one digest."""
    return fingerprint(
        {
            "external_executor": evidence.external_executor,
            "command": evidence.command,
            "run_id": evidence.run_id,
            "source_commit_sha": evidence.source_commit_sha,
            "result_fingerprint": evidence.result_fingerprint,
            "syntax_passed": evidence.syntax_passed,
            "tests_passed": evidence.tests_passed,
            "regression_passed": evidence.regression_passed,
        }
    )


def _valid_evidence(
    request: RepairRequest,
    evidence: VerificationEvidence,
    changed_paths: tuple[str, ...],
) -> bool:
    if not isinstance(evidence.external_executor, str):
        return False

    if not evidence.external_executor.strip():
        return False

    if not _SHA256.fullmatch(evidence.evidence_fingerprint):
        return False

    non_python_changes = any(
        Path(path).suffix.lower() not in _PYTHON_SUFFIXES
        for path in changed_paths
    )

    if not non_python_changes:
        return True

    # Non-Python files must be tied to a specific source commit and external
    # verification run, with command identity and a stable result fingerprint.
    if not _SHA1.fullmatch(request.source_commit_sha):
        return False

    if evidence.source_commit_sha != request.source_commit_sha:
        return False

    if not evidence.command.strip() or not evidence.run_id.strip():
        return False

    if not _SHA256.fullmatch(evidence.result_fingerprint):
        return False

    return (
        evidence.evidence_fingerprint
        == external_evidence_fingerprint(evidence)
    )


def verify_patch(
    *,
    workspace: Path | str,
    request: RepairRequest,
    evidence: VerificationEvidence,
) -> PatchVerification:
    changed_paths = tuple(
        sorted(patch_paths(request.candidate_patch))
    )

    syntax_passed = syntax_check(workspace, changed_paths)
    evidence_valid = _valid_evidence(
        request,
        evidence,
        changed_paths,
    )

    passed = (
        syntax_passed
        and evidence.syntax_passed is True
        and evidence.tests_passed is True
        and evidence.regression_passed is True
        and evidence_valid
    )

    if not syntax_passed or evidence.syntax_passed is not True:
        reason = RepairReason.SYNTAX_FAILURE
    elif evidence.tests_passed is not True:
        reason = RepairReason.TEST_FAILURE
    elif evidence.regression_passed is not True:
        reason = RepairReason.REGRESSION_FAILURE
    elif not evidence_valid:
        reason = RepairReason.VERIFICATION_REQUIRED
    else:
        reason = RepairReason.VALID

    return PatchVerification(
        passed=passed,
        changed_paths=changed_paths,
        patch_fingerprint=text_fingerprint(
            request.candidate_patch
        ),
        final_tree_fingerprint=tree_fingerprint(workspace),
        evidence=evidence,
        reason=reason,
    )
