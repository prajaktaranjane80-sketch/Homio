from __future__ import annotations

import subprocess
from pathlib import Path

from .repair_identity import text_fingerprint
from .repair_models import RepairRequest
from .repair_policy import validate_policy
from .repair_scope import patch_paths, validate_scope


class PatchEngineError(RuntimeError):
    pass


def validate_patch(
    request: RepairRequest,
) -> tuple[str, ...]:
    policy = request_policy(request)

    if not request.candidate_patch.strip():
        raise PatchEngineError(
            "Repair patch is empty."
        )

    if len(
        request.candidate_patch.encode("utf-8")
    ) > policy.max_patch_bytes:
        raise PatchEngineError(
            "Repair patch exceeds size limit."
        )

    paths = validate_scope(
        request,
        policy,
    )

    if not paths:
        raise PatchEngineError(
            "Repair patch contains no file paths."
        )

    return paths


def request_policy(request: RepairRequest):
    from .repair_models import RepairPolicy

    policy = RepairPolicy(
        policy_version=request.policy_version
    )

    validate_policy(policy)

    return policy


def apply_patch(
    workspace: Path | str,
    request: RepairRequest,
) -> tuple[str, ...]:
    root = Path(workspace).resolve()

    if not root.is_dir():
        raise PatchEngineError(
            "Repair workspace does not exist."
        )

    paths = validate_patch(request)

    patch_file = root / ".reos_t20_patch.diff"

    try:
        patch_file.write_text(
            request.candidate_patch,
            encoding="utf-8",
        )

        check = subprocess.run(
            [
                "git",
                "apply",
                "--check",
                "--whitespace=nowarn",
                str(patch_file),
            ],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if check.returncode != 0:
            raise PatchEngineError(
                check.stderr.strip()
                or "Patch check failed."
            )

        apply_result = subprocess.run(
            [
                "git",
                "apply",
                "--whitespace=nowarn",
                str(patch_file),
            ],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if apply_result.returncode != 0:
            raise PatchEngineError(
                apply_result.stderr.strip()
                or "Patch application failed."
            )

    finally:
        patch_file.unlink(
            missing_ok=True
        )

    actual = tuple(
        sorted(
            patch_paths(
                request.candidate_patch
            )
        )
    )

    if actual != paths:
        raise PatchEngineError(
            "Patch path set changed during application."
        )

    return paths


def patch_fingerprint(
    patch: str,
) -> str:
    return text_fingerprint(patch)
