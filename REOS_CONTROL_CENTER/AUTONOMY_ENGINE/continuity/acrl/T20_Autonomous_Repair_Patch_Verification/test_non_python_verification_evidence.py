from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from .patch_verification import (
    external_evidence_fingerprint,
    syntax_check,
    tree_fingerprint,
    verify_patch,
)
from .repair_models import (
    RepairRequest,
    VerificationEvidence,
)


SOURCE_COMMIT = "a" * 40
RESULT_FINGERPRINT = "b" * 64

PATCH = (
    "--- a/src/component.tsx\n"
    "+++ b/src/component.tsx\n"
    "@@ -1 +1 @@\n"
    "-export const value = 1;\n"
    "+export const value = 2;\n"
)


def make_request(
    root: Path,
    *,
    source_commit: str = SOURCE_COMMIT,
) -> RepairRequest:
    return RepairRequest(
        repair_id="web-repair-001",
        authorization_fingerprint="c" * 64,
        authorization_nonce="web-nonce-001",
        diagnosis_fingerprint="d" * 64,
        impact_fingerprint="e" * 64,
        baseline_fingerprint=tree_fingerprint(root),
        allowed_paths=("src/component.tsx",),
        forbidden_paths=(),
        candidate_patch=PATCH,
        source_commit_sha=source_commit,
    )


def make_external_evidence(
    *,
    source_commit: str = SOURCE_COMMIT,
) -> VerificationEvidence:
    evidence = VerificationEvidence(
        syntax_passed=True,
        tests_passed=True,
        regression_passed=True,
        external_executor="HOMIO frontend verification",
        evidence_fingerprint="0" * 64,
        command="npm run typecheck && npm run lint && npm run build",
        run_id="https://github.com/example/repository/actions/runs/123456",
        source_commit_sha=source_commit,
        result_fingerprint=RESULT_FINGERPRINT,
    )

    return replace(
        evidence,
        evidence_fingerprint=external_evidence_fingerprint(evidence),
    )


def build_workspace(root: Path) -> Path:
    source = root / "src"
    source.mkdir(parents=True)

    (source / "component.tsx").write_text(
        "export const value = 2;\n",
        encoding="utf-8",
    )

    return root


def test_non_python_change_requires_bound_external_evidence(
    tmp_path: Path,
) -> None:
    workspace = build_workspace(tmp_path / "workspace")
    request = make_request(workspace)
    evidence = make_external_evidence()

    result = verify_patch(
        workspace=workspace,
        request=request,
        evidence=evidence,
    )

    assert result.passed is True
    assert result.reason.value == "VALID"
    assert result.changed_paths == ("src/component.tsx",)


def test_non_python_change_fails_closed_without_run_identity(
    tmp_path: Path,
) -> None:
    workspace = build_workspace(tmp_path / "workspace")
    request = make_request(workspace)

    evidence = VerificationEvidence(
        syntax_passed=True,
        tests_passed=True,
        regression_passed=True,
        external_executor="frontend-runner",
        evidence_fingerprint="f" * 64,
    )

    result = verify_patch(
        workspace=workspace,
        request=request,
        evidence=evidence,
    )

    assert result.passed is False
    assert result.reason.value == "VERIFICATION_REQUIRED"


def test_non_python_evidence_must_match_requested_source_commit(
    tmp_path: Path,
) -> None:
    workspace = build_workspace(tmp_path / "workspace")
    request = make_request(
        workspace,
        source_commit="c" * 40,
    )
    evidence = make_external_evidence(source_commit=SOURCE_COMMIT)

    result = verify_patch(
        workspace=workspace,
        request=request,
        evidence=evidence,
    )

    assert result.passed is False
    assert result.reason.value == "VERIFICATION_REQUIRED"


def test_result_fingerprint_is_part_of_evidence_binding(
    tmp_path: Path,
) -> None:
    workspace = build_workspace(tmp_path / "workspace")
    request = make_request(workspace)
    evidence = make_external_evidence()

    tampered = replace(
        evidence,
        result_fingerprint="9" * 64,
    )

    result = verify_patch(
        workspace=workspace,
        request=request,
        evidence=tampered,
    )

    assert result.passed is False
    assert result.reason.value == "VERIFICATION_REQUIRED"


def test_non_python_path_escape_is_rejected(
    tmp_path: Path,
) -> None:
    workspace = build_workspace(tmp_path / "workspace")

    (tmp_path / "outside.tsx").write_text(
        "export const value = 1;\n",
        encoding="utf-8",
    )

    assert syntax_check(workspace, ("../outside.tsx",)) is False


def test_missing_non_python_path_is_rejected(
    tmp_path: Path,
) -> None:
    workspace = build_workspace(tmp_path / "workspace")

    assert syntax_check(workspace, ("src/missing.tsx",)) is False


def test_non_python_symlink_is_rejected(
    tmp_path: Path,
) -> None:
    workspace = build_workspace(tmp_path / "workspace")
    outside = tmp_path / "outside.tsx"

    outside.write_text(
        "export const value = 1;\n",
        encoding="utf-8",
    )

    link = workspace / "src" / "linked.tsx"

    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        # Some Windows configurations do not permit symlink creation.
        return

    assert syntax_check(workspace, ("src/linked.tsx",)) is False
