
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_backend_activation_bootstraps_canonical_acrl_import_namespace():
    repository_root = Path(__file__).resolve().parents[2]

    activation_script = (
        repository_root
        / ".github/actions/homio-backend-ci/transitions/"
        / "backend-workstream-activation/scripts/"
        / "activate_backend_workstream.py"
    )

    assert activation_script.is_file()

    probe = """
import importlib
import importlib.util
import sys
from pathlib import Path

activation_path = Path(sys.argv[1]).resolve()

spec = importlib.util.spec_from_file_location(
    "homio_backend_activation_import_smoke",
    activation_path,
)

assert spec is not None
assert spec.loader is not None

module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert module.ROOT == activation_path.parents[6]
assert module.CONTROL == module.ROOT / "REOS_CONTROL_CENTER"

assert str(module.CONTROL) in sys.path
assert str(module.ROOT) in sys.path

identity = importlib.import_module(
    "REOS_CONTROL_CENTER.context.github_actions_identity"
)

assert module.OWNER == identity.OWNER
assert module.OWNER_ID == identity.OWNER_ID
assert module.REPOSITORY == identity.REPOSITORY
assert module.REPOSITORY_ID == identity.REPOSITORY_ID
assert module.BRANCH == identity.BRANCH
assert module.BRANCH_REF == identity.BRANCH_REF
assert module.OIDC_ISSUER == identity.OIDC_ISSUER
assert module.EXPECTED_OIDC_SUBJECT == identity.EXPECTED_OIDC_SUBJECT

assert identity.OWNER == "prajaktaranjane80-sketch"
assert identity.OWNER_ID == "320960487"
assert identity.REPOSITORY == "prajaktaranjane80-sketch/Homio"
assert identity.REPOSITORY_ID == "1346051793"
assert identity.BRANCH_REF == "refs/heads/reos-development"

assert identity.EXPECTED_OIDC_SUBJECT == (
    "repo:prajaktaranjane80-sketch@320960487/"
    "Homio@1346051793:"
    "ref:refs/heads/reos-development"
)

# The controller was modified after the audited baseline and must be
# an explicitly authorized source path for the activation transition.
assert (
    "REOS_CONTROL_CENTER/reos_control_center.py"
    in module.EXPECTED_ACTIVATION_PATHS
)

# The activation transition must preserve all existing authorization and
# test-related source paths in its exact allowlist.
required_activation_paths = {
    ".github/actions/homio-backend-ci/transitions/"
    "backend-workstream-activation/action.yml",
    ".github/actions/homio-backend-ci/transitions/"
    "backend-workstream-activation/scripts/"
    "activate_backend_workstream.py",
    ".github/workflows/backend-ci.yml",
    ".github/workflows/reusable-backend-workstream-activation.yml",
    "REOS_CONTROL_CENTER/context/github_actions_identity.py",
    "REOS_CONTROL_CENTER/context/test_github_actions_identity.py",
    "REOS_CONTROL_CENTER/context/test_backend_control_projection.py",
    "REOS_CONTROL_CENTER/context/reos_control_center.py",
    "REOS_CONTROL_CENTER/context/test_backend_activation_import_bootstrap.py",
}

assert required_activation_paths.issubset(
    module.EXPECTED_ACTIVATION_PATHS
)

import AUTONOMY_ENGINE.continuity.acrl.repository_context  # noqa: E402

assert not any(
    name.startswith("REOS_CONTROL_CENTER.AUTONOMY_ENGINE")
    for name in sys.modules
), "ACRL was imported through a duplicate package namespace"
"""

    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"

    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            probe,
            str(activation_script),
        ],
        cwd=repository_root,
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert completed.returncode == 0, (
        "Activation import bootstrap failed.\n"
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )
