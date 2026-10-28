from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
WORKFLOWS = ROOT / ".github" / "workflows"
ACTIONS = ROOT / ".github" / "actions"

CHECKOUT_PIN = (
    "3d3c42e5aac5ba805825da76410c181273ba90b1"
)
SETUP_PYTHON_PIN = (
    "6d4fd22b20465ccc0f7354476588e8df7c9ca0e0"
)
SETUP_NODE_PIN = (
    "949feb2413d6458794dcd2491c4babbbce0c15c1"
)
CACHE_PIN = (
    "55cc8345863c7cc4c66a329aec7e433d2d1c52a9"
)
UPLOAD_ARTIFACT_PIN = (
    "cf430e030ddbb5b0abf93d22962f4752f3646cd9"
)

EXPECTED_ACTION_PINS = {
    "actions/checkout": CHECKOUT_PIN,
    "actions/setup-python": SETUP_PYTHON_PIN,
    "actions/setup-node": SETUP_NODE_PIN,
    "actions/cache": CACHE_PIN,
    "actions/cache/restore": CACHE_PIN,
    "actions/cache/save": CACHE_PIN,
    "actions/upload-artifact": UPLOAD_ARTIFACT_PIN,
}

USES_PATTERN = re.compile(
    r"^\s*uses:\s*"
    r"(actions/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*)"
    r"@([^\s#]+)",
    re.MULTILINE,
)

GUARDED_WORKFLOWS = (
    ".github/workflows/reusable-ai001-acceptance-validation.yml",
    ".github/workflows/reusable-ai001-t01-transition.yml",
    ".github/workflows/reusable-ai001-t02-transition.yml",
    ".github/workflows/reusable-ai001-t03-transition.yml",
    ".github/workflows/reusable-ai001-t04-transition.yml",
    ".github/workflows/reusable-ai001-t05-transition.yml",
    ".github/workflows/reusable-ai001-t06-transition.yml",
    ".github/workflows/reusable-ai001-t07-transition.yml",
    ".github/workflows/reusable-ai001-t08-transition.yml",
    ".github/workflows/reusable-ai001-t09-transition.yml",
    ".github/workflows/reusable-ai001-t10-approval.yml",
    ".github/workflows/reusable-core008-acceptance-validation.yml",
    ".github/workflows/reusable-core008-t06-transition.yml",
    ".github/workflows/reusable-core008-t07-transition.yml",
    ".github/workflows/reusable-core008-t08-transition.yml",
    ".github/workflows/reusable-core008-t09-transition.yml",
    ".github/workflows/reusable-core008-t10-approval.yml",
)


def read(path: Path) -> str:
    assert path.is_file(), (
        f"Required CI policy file is missing: {path.relative_to(ROOT)}"
    )
    return path.read_text(encoding="utf-8")


def configuration_files() -> list[Path]:
    files = (
        list(WORKFLOWS.rglob("*.yml"))
        + list(WORKFLOWS.rglob("*.yaml"))
        + list(ACTIONS.rglob("action.yml"))
    )
    return sorted(set(files))


def test_runtime_sensitive_actions_use_verified_immutable_pins():
    seen: set[str] = set()

    for path in configuration_files():
        content = read(path)

        for action_name, reference in USES_PATTERN.findall(content):
            if action_name not in EXPECTED_ACTION_PINS:
                continue

            expected_reference = EXPECTED_ACTION_PINS[action_name]

            assert reference == expected_reference, (
                f"{path.relative_to(ROOT)} uses {action_name}@{reference}; "
                f"expected immutable SHA {expected_reference}. "
                "Review the official action release and runtime before upgrading."
            )

            seen.add(action_name)

    required_actions = {
        "actions/checkout",
        "actions/setup-python",
        "actions/setup-node",
        "actions/cache/restore",
        "actions/cache/save",
        "actions/upload-artifact",
    }

    missing = sorted(required_actions - seen)

    assert not missing, (
        "Expected runtime-sensitive action references were not found: "
        + ", ".join(missing)
    )


def test_every_guarded_workflow_uses_pinned_bootstrap_and_sha_bindings():
    backend = read(WORKFLOWS / "backend-ci.yml")

    for relative_path in GUARDED_WORKFLOWS:
        path = ROOT / relative_path
        content = read(path)

        assert f"uses: actions/checkout@{CHECKOUT_PIN}" in content, (
            f"{relative_path} must use the verified checkout SHA."
        )
        assert f"uses: actions/setup-python@{SETUP_PYTHON_PIN}" in content, (
            f"{relative_path} must use the verified setup-python SHA."
        )

        assert "workflow_call:" in content, (
            f"{relative_path} must remain a reusable workflow."
        )
        assert 'PYTHONDONTWRITEBYTECODE: "1"' in content, (
            f"{relative_path} must disable implicit Python bytecode writes."
        )
        assert "GIT_CONFIG_VALUE_0: reos-development" in content, (
            f"{relative_path} must suppress the Git default-branch hint."
        )
        assert "EXPECTED_SHA: ${{ github.sha }}" in content, (
            f"{relative_path} must bind its expected SHA to the triggering commit."
        )
        assert "VERIFIED_CODE_SHA: ${{ github.sha }}" in content, (
            f"{relative_path} must bind the verified code SHA to the triggering commit."
        )

        quoted_path = f'"{relative_path}"'

        assert backend.count(quoted_path) == 2, (
            f"{relative_path} must remain in both push and pull_request "
            "path filters in backend-ci.yml."
        )


def test_compile_check_is_in_memory_and_does_not_regenerate_bytecode():
    compile_script = read(
        ACTIONS
        / "homio-backend-ci/verification/scripts/compile_and_contracts.sh"
    )

    assert "python -m compileall" not in compile_script, (
        "compileall writes bytecode into the workspace; use in-memory compilation."
    )
    assert "tokenize.open(source_path)" in compile_script, (
        "The compile check must respect Python source encoding declarations."
    )
    assert 'compile(source, str(source_path), "exec", dont_inherit=True)' in (
        compile_script
    ), (
        "The compile check must compile source in memory without writing .pyc files."
    )
