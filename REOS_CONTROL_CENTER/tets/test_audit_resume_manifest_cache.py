from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = (
    REPOSITORY_ROOT
    / ".github/actions/homio-backend-ci/verification/scripts/audit_resume_manifest_cache.py"
)

spec = importlib.util.spec_from_file_location(
    "audit_resume_manifest_cache_under_test",
    SCRIPT_PATH,
)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Cannot load cache adapter: {SCRIPT_PATH}")

cache_adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cache_adapter)


def test_git_tree_parser_preserves_exact_git_blob_sha_and_spaces():
    raw = (
        b"100644 blob " + b"a" * 40
        + b"\tREOS_CONTROL_CENTER/data/state.json\0"
        + b"100644 blob " + b"b" * 40
        + b"\tpath with spaces/blueprint.md\0"
        + b"040000 tree " + b"c" * 40
        + b"\tignored-directory\0"
    )

    parsed = cache_adapter.parse_git_tree(raw)

    assert parsed == {
        "REOS_CONTROL_CENTER/data/state.json": "a" * 40,
        "path with spaces/blueprint.md": "b" * 40,
    }


def test_git_tree_parser_fails_closed_on_unsafe_paths():
    raw = b"100644 blob " + b"a" * 40 + b"\t../outside.json\0"

    with pytest.raises(cache_adapter.CacheInitializationError):
        cache_adapter.parse_git_tree(raw)


def test_git_tree_parser_fails_closed_on_malformed_blob_identity():
    raw = b"100644 blob not-a-sha\tfile.py\0"

    with pytest.raises(cache_adapter.CacheInitializationError):
        cache_adapter.parse_git_tree(raw)


def test_git_diff_parser_handles_add_modify_delete_and_rename():
    raw = (
        b"A\0new/file.py\0"
        b"M\0changed/file.py\0"
        b"D\0removed/file.py\0"
        b"R100\0old/name.py\0new/name.py\0"
        b"C090\0copy-source.py\0copy-target.py\0"
    )

    changed, deleted = cache_adapter.parse_name_status(raw)

    assert changed == (
        "changed/file.py",
        "copy-target.py",
        "new/file.py",
        "new/name.py",
    )
    assert deleted == ("old/name.py", "removed/file.py")


def test_git_diff_parser_rejects_incomplete_rename():
    with pytest.raises(cache_adapter.CacheInitializationError):
        cache_adapter.parse_name_status(b"R100\0old/path.py\0")


def test_git_diff_parser_rejects_unmerged_or_unknown_status():
    with pytest.raises(cache_adapter.CacheInitializationError):
        cache_adapter.parse_name_status(b"U\0conflicted.py\0")


def test_cache_path_must_be_external_to_git_worktree(tmp_path: Path):
    workspace = tmp_path / "repo"
    runner_temp = tmp_path / "runner-temp"
    workspace.mkdir()
    runner_temp.mkdir()
    valid = runner_temp / "homio-acrl" / "audit_resume_manifest.json"

    assert cache_adapter.validate_cache_destination(
        workspace,
        runner_temp,
        valid,
    ) == valid.resolve()

    with pytest.raises(cache_adapter.CacheInitializationError):
        cache_adapter.validate_cache_destination(
            workspace,
            runner_temp,
            workspace / "REOS_CONTROL_CENTER" / "data" / "state.json",
        )


def test_cache_path_cannot_be_arbitrary_external_file(tmp_path: Path):
    workspace = tmp_path / "repo"
    runner_temp = tmp_path / "runner-temp"
    workspace.mkdir()
    runner_temp.mkdir()

    with pytest.raises(cache_adapter.CacheInitializationError):
        cache_adapter.validate_cache_destination(
            workspace,
            runner_temp,
            runner_temp / "another-manifest.json",
        )


def test_current_position_uses_authoritative_task_id_not_label():
    state = {
        "execution": {
            "current_gate": "APP-001",
            "current_task": (
                "APP-001-T01: Implement application shell and design system."
            ),
            "current_subtask": "APP-001-T01",
            "status": "CONTROL_CENTER_DRIVEN",
        }
    }

    position = cache_adapter._current_position(state)

    assert position["current_gate"] == "APP-001"
    assert position["current_task"] == "APP-001-T01"
    assert position["current_subtask"] == "APP-001-T01"
    assert position["current_subtask_status"] == "CONTROL_CENTER_DRIVEN"
    assert position["current_task_label"].endswith("design system.")


def test_current_position_fails_closed_when_subtask_is_missing():
    state = {
        "execution": {
            "current_gate": "APP-001",
            "current_task": "some label",
            "current_subtask": None,
            "status": "CONTROL_CENTER_DRIVEN",
        }
    }

    with pytest.raises(cache_adapter.CacheInitializationError):
        cache_adapter._current_position(state)


def test_baseline_scope_fails_closed_when_t16_did_not_inspect_a_path():
    with pytest.raises(cache_adapter.CacheInitializationError):
        cache_adapter._assert_inventory_covers_scope(
            ("REOS_CONTROL_CENTER/data/state.json", "source.py"),
            {"source.py"},
        )


def test_baseline_scope_passes_when_t16_inspected_every_path():
    cache_adapter._assert_inventory_covers_scope(
        ("REOS_CONTROL_CENTER/data/state.json", "source.py"),
        {"REOS_CONTROL_CENTER/data/state.json", "source.py"},
    )


def test_composite_initializes_and_publishes_cache_only_after_ci_passes():
    action_path = (
        REPOSITORY_ROOT
        / ".github/actions/homio-backend-ci/verification/action.yml"
    )
    action = action_path.read_text(encoding="utf-8")

    assert "uses: actions/cache/restore@v4" in action
    assert "Run complete ACRL suite" in action
    assert (
        "Seal and independently read back external T14 resume cache"
        in action
    )
    assert "uses: actions/cache/save@v4" in action
    assert "uses: actions/upload-artifact@v4" in action
    assert action.index("Run complete ACRL suite") < action.index(
        "Seal and independently read back external T14 resume cache"
    )
    assert action.index(
        "Seal and independently read back external T14 resume cache"
    ) < action.index("uses: actions/cache/save@v4")
    assert "github.ref == 'refs/heads/reos-development'" in action
    assert "github.event_name == 'pull_request'" not in action


def test_resume_cache_adapter_uses_external_write_target_and_no_state_writer():
    source = SCRIPT_PATH.read_text(encoding="utf-8")

    assert "validate_cache_destination" in source
    assert "RUNNER_TEMP" in source
    assert "CONTROL_CENTER_ROOT" in source
    assert (
        "T14_Repository_Intelligence_Context.audit_resume_manifest"
        in source
    )
    assert (
        "T16_Repository_Intelligence_File_Discovery.repository_intelligence"
        in source
    )
    assert "STATE.write_text" not in source
    assert "STATE_PATH.write_text" not in source
    assert "state.json" in source
