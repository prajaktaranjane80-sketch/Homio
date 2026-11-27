from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

import verify_core001_source_baseline as verifier


EXPECTED_PATHS = {
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/identity_tenant/__init__.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/identity_tenant/identity.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/identity_tenant/identity_contract.json",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/identity_tenant/membership.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/identity_tenant/membership_contract.json",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/identity_tenant/tenant.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/identity_tenant/tenant_contract.json",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/identity_tenant/tenant_isolation.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/identity_tenant/test_identity.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/identity_tenant/test_membership.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/identity_tenant/test_t01_d_contract.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/identity_tenant/test_t02_d_contract.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/identity_tenant/test_t03_d_contract.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/identity_tenant/test_tenant.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/core/identity_tenant/test_tenant_isolation.py",
}


class TestCore001SourceBaseline(unittest.TestCase):
    SOURCE_SHA = "ffffffffffffffffffffffffffffffffffffffff"

    def fake_git(
        self,
        *,
        mismatch: tuple[str, str] | None = None,
        extra_path: str | None = None,
        missing_path: str | None = None,
    ):
        def run_git(root: Path, *arguments: str) -> str:
            if arguments[0] == "ls-tree":
                ref = arguments[3]
                paths = set(EXPECTED_PATHS)

                if ref == self.SOURCE_SHA:
                    if extra_path is not None:
                        paths.add(extra_path)

                    if missing_path is not None:
                        paths.discard(missing_path)

                return "\n".join(sorted(paths))

            if arguments[0] == "rev-parse":
                ref, path = arguments[1].split(":", 1)

                if mismatch == (ref, path):
                    return "0" * 40

                return verifier.CORE001_SOURCE_BLOB_SHAS[path]

            raise AssertionError(
                f"Unexpected Git command: {arguments}"
            )

        return run_git

    def test_manifest_contains_exact_canonical_core001_inventory(self):
        self.assertEqual(
            set(verifier.CORE001_SOURCE_BLOB_SHAS),
            EXPECTED_PATHS,
        )
        self.assertEqual(
            len(verifier.CORE001_SOURCE_BLOB_SHAS),
            15,
        )

    def test_accepts_exact_inventory_and_hashes_on_both_commits(self):
        with patch.object(
            verifier,
            "_run_git",
            side_effect=self.fake_git(),
        ) as mocked_git:
            verifier.verify_core001_source_baseline(
                Path("/repository"),
                self.SOURCE_SHA,
            )

        expected_git_calls = 2 + (2 * len(EXPECTED_PATHS))
        self.assertEqual(
            mocked_git.call_count,
            expected_git_calls,
        )

    def test_rejects_modified_core001_owner_source_blob(self):
        path = sorted(EXPECTED_PATHS)[0]

        with patch.object(
            verifier,
            "_run_git",
            side_effect=self.fake_git(
                mismatch=(self.SOURCE_SHA, path)
            ),
        ):
            with self.assertRaisesRegex(
                verifier.Core001SourceBaselineError,
                path,
            ):
                verifier.verify_core001_source_baseline(
                    Path("/repository"),
                    self.SOURCE_SHA,
                )

    def test_rejects_modified_reviewed_baseline_blob(self):
        path = sorted(EXPECTED_PATHS)[0]

        with patch.object(
            verifier,
            "_run_git",
            side_effect=self.fake_git(
                mismatch=(verifier.BASELINE_HEAD, path)
            ),
        ):
            with self.assertRaisesRegex(
                verifier.Core001SourceBaselineError,
                path,
            ):
                verifier.verify_core001_source_baseline(
                    Path("/repository"),
                    self.SOURCE_SHA,
                )

    def test_rejects_added_unreviewed_core001_source_file(self):
        with patch.object(
            verifier,
            "_run_git",
            side_effect=self.fake_git(
                extra_path=(
                    verifier.CORE001_ROOT
                    + "/unreviewed_authorization.py"
                )
            ),
        ):
            with self.assertRaisesRegex(
                verifier.Core001SourceBaselineError,
                "unexpected",
            ):
                verifier.verify_core001_source_baseline(
                    Path("/repository"),
                    self.SOURCE_SHA,
                )

    def test_rejects_removed_core001_source_file(self):
        missing = sorted(EXPECTED_PATHS)[0]

        with patch.object(
            verifier,
            "_run_git",
            side_effect=self.fake_git(
                missing_path=missing
            ),
        ):
            with self.assertRaisesRegex(
                verifier.Core001SourceBaselineError,
                "missing",
            ):
                verifier.verify_core001_source_baseline(
                    Path("/repository"),
                    self.SOURCE_SHA,
                )

    def test_rejects_invalid_owner_source_sha_before_git_access(self):
        with patch.object(
            verifier,
            "_run_git",
        ) as mocked_git:
            with self.assertRaisesRegex(
                verifier.Core001SourceBaselineError,
                "owner source commit SHA is invalid",
            ):
                verifier.verify_core001_source_baseline(
                    Path("/repository"),
                    "not-a-commit",
                )

        mocked_git.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
