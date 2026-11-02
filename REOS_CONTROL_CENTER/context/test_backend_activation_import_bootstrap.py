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
