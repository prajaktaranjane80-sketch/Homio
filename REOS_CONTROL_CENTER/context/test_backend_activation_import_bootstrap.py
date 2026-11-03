from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_backend_activation_bootstraps_canonical_acrl_import_namespace():
    repository_root = Path(__file__).resolve().parents[2]

    wrapper_script = (
        repository_root
        / ".github/actions/homio-backend-ci/transitions/"
        / "backend-workstream-activation/scripts/"
        / "activate_backend_workstream_wrapper.py"
    )

    activation_script = (
        repository_root
        / ".github/actions/homio-backend-ci/transitions/"
        / "backend-workstream-activation/scripts/"
        / "activate_backend_workstream.py"
    )

    assert wrapper_script.is_file()
    assert activation_script.is_file()

    probe = """
import importlib
import importlib.util
import sys
from pathlib import Path

wrapper_path = Path(sys.argv[1]).resolve()

spec = importlib.util.spec_from_file_location(
    "homio_backend_activation_wrapper_smoke",
    wrapper_path,
)

assert spec is not None
assert spec.loader is not None

wrapper = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = wrapper
spec.loader.exec_module(wrapper)

activation = wrapper.load_guarded_activation()

assert activation.ROOT == wrapper_path.parents[6]
assert activation.CONTROL == activation.ROOT / "REOS_CONTROL_CENTER"

assert str(activation.CONTROL) in sys.path
assert str(activation.ROOT) in sys.path

assert (
    activation.EXPECTED_ACTIVATION_PATHS
    == wrapper.REPAIRED_ACTIVATION_PATHS
)

identity = importlib.import_module(
    "REOS_CONTROL_CENTER.context.github_actions_identity"
)

assert activation.OWNER == identity.OWNER
assert activation.OWNER_ID == identity.OWNER_ID
assert activation.REPOSITORY == identity.REPOSITORY
assert activation.REPOSITORY_ID == identity.REPOSITORY_ID
assert activation.BRANCH == identity.BRANCH
assert activation.BRANCH_REF == identity.BRANCH_REF
assert activation.OIDC_ISSUER == identity.OIDC_ISSUER
assert activation.EXPECTED_OIDC_SUBJECT == identity.EXPECTED_OIDC_SUBJECT

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

required_activation_paths = {
    ".github/actions/homio-backend-ci/transitions/"
    "backend-workstream-activation/action.yml",
    ".github/actions/homio-backend-ci/transitions/"
    "backend-workstream-activation/scripts/"
    "activate_backend_workstream.py",
    ".github/actions/homio-backend-ci/transitions/"
    "backend-workstream-activation/scripts/"
    "activate_backend_workstream_wrapper.py",
    ".github/workflows/backend-ci.yml",
    ".github/workflows/reusable-backend-workstream-activation.yml",
    "REOS_CONTROL_CENTER/context/github_actions_identity.py",
    "REOS_CONTROL_CENTER/context/test_github_actions_identity.py",
    "REOS_CONTROL_CENTER/context/test_backend_control_projection.py",
    "REOS_CONTROL_CENTER/reos_control_center.py",
    "REOS_CONTROL_CENTER/PS Output",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
    "T17_Change_Impact_Dependency_Analysis/change_impact_analysis.py",
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/continuity/acrl/"
    "T17_Change_Impact_Dependency_Analysis/test_change_impact_analysis.py",
}

assert required_activation_paths.issubset(
    activation.EXPECTED_ACTIVATION_PATHS
)

assert (
    "REOS_CONTROL_CENTER/context/reos_control_center.py"
    not in activation.EXPECTED_ACTIVATION_PATHS
)

assert wrapper.source_paths_for_t17(
    (
        "REOS_CONTROL_CENTER/PS Output",
        "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/example.py",
    )
) == [
    "REOS_CONTROL_CENTER/AUTONOMY_ENGINE/example.py",
]

# Similar-looking paths are not silently excluded.
assert wrapper.source_paths_for_t17(
    ("other/PS Output",)
) == ["other/PS Output"]

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
            str(wrapper_script),
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
