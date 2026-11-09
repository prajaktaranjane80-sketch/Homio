
from __future__ import annotations

from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]

AGENT_BOOTSTRAP = REPOSITORY_ROOT / "AGENTS.md"

CANONICAL_ENTRYPOINT = (
    REPOSITORY_ROOT
    / "REOS_CONTROL_CENTER"
    / "AI_AGENT_ENTRYPOINT.py"
)

CANONICAL_STATE = (
    REPOSITORY_ROOT
    / "REOS_CONTROL_CENTER"
    / "data"
    / "state.json"
)

CI_RUNNER = (
    REPOSITORY_ROOT
    / ".github"
    / "actions"
    / "homio-backend-ci"
    / "verification"
    / "scripts"
    / "compile_and_contracts.sh"
)

CI_WORKFLOW = (
    REPOSITORY_ROOT
    / ".github"
    / "workflows"
    / "backend-ci.yml"
)


def read_required(path: Path) -> str:
    assert path.is_file(), (
        f"Required agent-bootstrap source is missing: "
        f"{path.relative_to(REPOSITORY_ROOT)}"
    )
    return path.read_text(encoding="utf-8")


def test_root_agent_bootstrap_is_discoverable_and_loads_superpowers_first():
    bootstrap = read_required(AGENT_BOOTSTRAP)

    required = (
        "HOMIO / REOS",
        "thin, auto-discoverable repository bootstrap",
        "using-superpowers",
        "ENGINEERING_SKILL_ROUTING",
        "AI_AGENT_ENTRYPOINT.py",
        "data/state.json",
        "reos-development",
        "T07",
        "T14",
        "BACKEND",
        "FRONTEND",
        "SHARED_INTEGRATION",
    )

    for item in required:
        assert item in bootstrap, (
            f"Root agent bootstrap is missing required instruction: {item}"
        )

    assert "## Mandatory startup" in bootstrap
    assert "## Skill execution" in bootstrap

    startup_section = bootstrap.split(
        "## Mandatory startup", 1
    )[1].split(
        "## Skill execution", 1
    )[0]

    skill_position = startup_section.index("using-superpowers")
    entrypoint_position = startup_section.index(
        "REOS_CONTROL_CENTER/AI_AGENT_ENTRYPOINT.py"
    )
    state_position = startup_section.index(
        "REOS_CONTROL_CENTER/data/state.json"
    )

    assert skill_position < entrypoint_position < state_position


def test_root_bootstrap_does_not_create_duplicate_policy_or_task_authority():
    bootstrap = read_required(AGENT_BOOTSTRAP).lower()
    entrypoint = read_required(CANONICAL_ENTRYPOINT)

    assert "not a second" in bootstrap
    assert "do not grant task authorization" in bootstrap
    assert "do not invent the next task" in bootstrap
    assert "do not create extra runners" in bootstrap

    assert "ENGINEERING_SKILL_ROUTING" in entrypoint
    assert "ENGINEERING_SKILL_WORKFLOW_RULES" in entrypoint

    assert (
        "task-specific skills before the corresponding engineering work"
        in bootstrap
    )


def test_bootstrap_preserves_owner_controlled_github_workflow():
    bootstrap = read_required(AGENT_BOOTSTRAP)

    assert "owner-controlled GitHub web-editor saves" in bootstrap
    assert "Do not perform direct Git writes" in bootstrap
    assert "PowerShell output is diagnostic evidence only" in bootstrap
    assert "complete file replacements" in bootstrap


def test_bootstrap_contract_is_part_of_the_existing_backend_ci_runner():
    runner = read_required(CI_RUNNER)

    assert "tets/test_ai_agent_entrypoint_contract.py" in runner
    assert "tets/test_agent_bootstrap_contract.py" in runner


def test_root_bootstrap_changes_trigger_existing_backend_ci():
    workflow = read_required(CI_WORKFLOW)

    assert '"AGENTS.md"' in workflow
