from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[6]

BASELINE_HEAD = "ae9e2e24344c391a116cc85b8d358b80bfcaa8e4"

CORE001_ROOT = (
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/identity_tenant"
)

CORE001_SOURCE_BLOB_SHAS = {
    (
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/"
        "identity_tenant/__init__.py"
    ): "d5bdc08fd6194f1e9a4f15e37f0e114d62459388",
    (
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/"
        "identity_tenant/identity.py"
    ): "49564ab0e7b3f19d192c343bd444ba3b45ced192",
    (
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/"
        "identity_tenant/identity_contract.json"
    ): "de2634bdd93fe7f268bb4870b5bab914eca6e084",
    (
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/"
        "identity_tenant/membership.py"
    ): "919868a77bf589795c383a1fbb974fc69dede6ec",
    (
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/"
        "identity_tenant/membership_contract.json"
    ): "9304de1df604c1937d22cd682cfb88cc686b2fe5",
    (
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/"
        "identity_tenant/tenant.py"
    ): "5fdda5750f37ea14214ede72ff97c739526390d6",
    (
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/"
        "identity_tenant/tenant_contract.json"
    ): "2e8d0b9910f8bd320f3e02841dede25232123093",
    (
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/"
        "identity_tenant/tenant_isolation.py"
    ): "d96a41cd85b61b67d1a3c789750d441d71078a5b",
    (
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/"
        "identity_tenant/test_identity.py"
    ): "518d8c2b749c3f8129672a13dbc8462527c5edac",
    (
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/"
        "identity_tenant/test_membership.py"
    ): "1bdfe1252a3cb2deafffbc9e80ce1b423e897086",
    (
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/"
        "identity_tenant/test_t01_d_contract.py"
    ): "8c931d6c2f651c894a910385cdab268021109ae0",
    (
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/"
        "identity_tenant/test_t02_d_contract.py"
    ): "9e33ad521173886cda128472c4e6c1208131f6d9",
    (
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/"
        "identity_tenant/test_t03_d_contract.py"
    ): "16721b8308d098d639e3bceea7e0f7b94607d525",
    (
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/"
        "identity_tenant/test_tenant.py"
    ): "289237ba944bd4af7319b2b4934bac38cd8c1581",
    (
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/"
        "identity_tenant/test_tenant_isolation.py"
    ): "e7e5adb30a0fdc932cec3594c63f789c4be810a3",
}

SHA_PATTERN = re.compile(r"[0-9a-f]{40}")


class Core001SourceBaselineError(RuntimeError):
    """Raised when canonical CORE-001 source integrity cannot be proven."""


def valid_sha(value: object) -> bool:
    return (
        isinstance(value, str)
        and SHA_PATTERN.fullmatch(value) is not None
    )


def _run_git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    output = (completed.stdout or "").strip()

    if completed.returncode != 0:
        raise Core001SourceBaselineError(
            "Git source verification failed "
            f"({completed.returncode}): "
            f"{' '.join(arguments)}: {output}"
        )

    return output


def verify_core001_source_baseline(
    root: Path,
    source_sha: str,
    *,
    baseline_sha: str = BASELINE_HEAD,
) -> None:
    """
    Verify the exact CORE-001 file inventory and blob identities.

    Both refs are validated before any Git process is started.
    Both commits must contain exactly the reviewed 15 files with
    their expected Git blob SHAs.

    This check is read-only.
    """
    refs = (
        (baseline_sha, "reviewed baseline"),
        (source_sha, "owner source commit"),
    )

    expected_paths = set(CORE001_SOURCE_BLOB_SHAS)

    if len(expected_paths) != len(CORE001_SOURCE_BLOB_SHAS):
        raise Core001SourceBaselineError(
            "CORE-001 source manifest contains duplicate paths."
        )

    if len(expected_paths) != 15:
        raise Core001SourceBaselineError(
            "CORE-001 source manifest must contain exactly 15 paths."
        )

    # Validate every caller-supplied ref before any Git access.
    for ref, label in refs:
        if not valid_sha(ref):
            raise Core001SourceBaselineError(
                f"CORE-001 {label} SHA is invalid."
            )

    for ref, label in refs:
        listed = _run_git(
            root,
            "ls-tree",
            "-r",
            "--name-only",
            ref,
            CORE001_ROOT,
        )

        listed_paths = listed.splitlines() if listed else []
        actual_paths = set(listed_paths)

        if len(listed_paths) != len(actual_paths):
            raise Core001SourceBaselineError(
                f"CORE-001 source inventory has duplicate paths "
                f"at {label}."
            )

        if actual_paths != expected_paths:
            missing = sorted(expected_paths - actual_paths)
            unexpected = sorted(actual_paths - expected_paths)

            raise Core001SourceBaselineError(
                f"CORE-001 source inventory differs at {label}; "
                f"missing={missing}; unexpected={unexpected}"
            )

        for path, expected_blob_sha in sorted(
            CORE001_SOURCE_BLOB_SHAS.items()
        ):
            actual_blob_sha = _run_git(
                root,
                "rev-parse",
                f"{ref}:{path}",
            )

            if actual_blob_sha != expected_blob_sha:
                raise Core001SourceBaselineError(
                    f"CORE-001 source SHA mismatch at {label}: "
                    f"{path}; expected={expected_blob_sha}; "
                    f"actual={actual_blob_sha}"
                )


def main() -> int:
    try:
        expected_sha = os.environ.get("EXPECTED_SHA", "")

        if not valid_sha(expected_sha):
            raise Core001SourceBaselineError(
                "EXPECTED_SHA is missing or invalid."
            )

        checked_out_sha = _run_git(
            ROOT,
            "rev-parse",
            "HEAD",
        )

        if checked_out_sha != expected_sha:
            raise Core001SourceBaselineError(
                "Checked-out HEAD differs from EXPECTED_SHA."
            )

        verify_core001_source_baseline(
            ROOT,
            expected_sha,
        )

    except Core001SourceBaselineError as exc:
        print(
            f"CORE-001 source baseline verification failed: {exc}",
            file=sys.stderr,
        )
        return 1

    print("CORE001_SOURCE_BASELINE=PASS")
    print("CORE001_SOURCE_FILES_VERIFIED=15")
    print(f"CORE001_SOURCE_COMMIT={expected_sha}")
    print("CORE001_SOURCE_INVENTORY=EXACT")
    print("CORE001_SOURCE_BLOB_HASHES=EXACT")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
