from __future__ import annotations

from pathlib import Path

from dependency_runtime import DependencyRuntime
from repository_runtime import RepositoryRuntime
from test_runtime import TestRuntime


def init_git(root: Path) -> None:
    import subprocess

    subprocess.run(
        ["git", "init"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )

    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )

    subprocess.run(
        ["git", "config", "user.name", "Test Runner"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )


def test_repository_runtime_reads_git_state(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()

    source = root / "inventory.py"
    source.write_text(
        "class Inventory: pass\n",
        encoding="utf-8",
    )

    init_git(root)

    import subprocess

    subprocess.run(
        ["git", "add", "."],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )

    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )

    runtime = RepositoryRuntime(root)

    assert runtime.branch() != ""
    assert len(runtime.head()) == 40
    assert runtime.worktree_clean() is True

    findings = runtime.find_paths(["inventory"])

    assert any(
        item.path == "inventory.py"
        for item in findings
    )


def test_repository_runtime_detects_changes(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()

    init_git(root)

    import subprocess

    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "initial"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )

    changed = root / "changed.py"
    changed.write_text(
        "x = 1\n",
        encoding="utf-8",
    )

    runtime = RepositoryRuntime(root)

    assert runtime.worktree_clean() is False
    assert "changed.py" in runtime.changed_paths()


def test_dependency_runtime_resolves_module(tmp_path):
    root = tmp_path / "repo"
    (root / "services").mkdir(parents=True)

    (root / "services" / "inventory.py").write_text(
        "class InventoryService: pass\n",
        encoding="utf-8",
    )

    runtime = DependencyRuntime(root)

    findings = runtime.resolve_module(
        "services.inventory"
    )

    assert len(findings) == 1
    assert findings[0].confidence == "VERIFIED"
    assert findings[0].relation == "MODULE_RESOLUTION"


def test_dependency_runtime_deduplicates():
    from dependency_runtime import DependencyFinding

    item = DependencyFinding(
        "a",
        "b",
        "IMPORT",
        "VERIFIED",
    )

    result = DependencyRuntime.deduplicate(
        [item, item]
    )

    assert result == [item]


def test_test_runtime_discovers_targeted_tests(tmp_path):
    root = tmp_path / "repo"
    test_dir = root / "tests"
    test_dir.mkdir(parents=True)

    path = test_dir / "test_inventory.py"

    path.write_text(
        """
def test_inventory_creation():
    assert True
""",
        encoding="utf-8",
    )

    runtime = TestRuntime(root)

    findings = runtime.discover(
        ["inventory"]
    )

    assert len(findings) == 1
    assert findings[0].path == "tests/test_inventory.py"
