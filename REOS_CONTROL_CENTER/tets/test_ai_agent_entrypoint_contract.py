from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest

import AI_AGENT_ENTRYPOINT as entrypoint


REPOSITORY_NAME = "prajaktaranjane80-sketch/Homio"
CANONICAL_BRANCH = "reos-development"
CANONICAL_STATE = "REOS_CONTROL_CENTER/data/state.json"
EXPECTED_ORIGIN = (
    "https://github.com/prajaktaranjane80-sketch/Homio.git"
)

GIT_READ_COMMANDS = {
    ("rev-parse", "--show-toplevel"),
    ("branch", "--show-current"),
    ("config", "--get", "remote.origin.url"),
    ("rev-parse", "HEAD"),
    ("status", "--porcelain=v1", "--untracked-files=all"),
    (
        "rev-parse",
        "--abbrev-ref",
        "--symbolic-full-name",
        "@{upstream}",
    ),
    (
        "rev-list",
        "--left-right",
        "--count",
        "HEAD...@{upstream}",
    ),
}


def _install_preflight_fixture(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    status_output: str = "",
    upstream_output: str = "origin/reos-development",
    upstream_exit_code: int = 0,
    ahead_behind_output: str = "0\t0",
) -> list[tuple[str, ...]]:
    """Install deterministic local Git evidence without invoking Git or a network."""

    repository_root = tmp_path / "Homio"
    control_center = repository_root / "REOS_CONTROL_CENTER"

    t21_path = (
        control_center
        / "AUTONOMY_ENGINE"
        / "continuity"
        / "acrl"
        / "T21_Git_Repository_Read_Write_Coordination"
    )

    control_center.mkdir(parents=True)
    t21_path.mkdir(parents=True)

    monkeypatch.setattr(
        entrypoint,
        "CANONICAL_LOCAL_WORKSPACE",
        repository_root,
    )
    monkeypatch.setattr(
        entrypoint,
        "CANONICAL_CONTROL_CENTER",
        control_center,
    )
    monkeypatch.setattr(
        entrypoint,
        "CONTROL_CENTER_PATH",
        control_center,
    )
    monkeypatch.setattr(
        entrypoint,
        "ACRL_GIT_REPOSITORY_COORDINATION",
        t21_path,
    )
    monkeypatch.setattr(
        entrypoint,
        "EXPECTED_BRANCH",
        CANONICAL_BRANCH,
    )
    monkeypatch.setattr(
        entrypoint,
        "EXPECTED_ORIGIN",
        EXPECTED_ORIGIN,
    )
    monkeypatch.chdir(control_center)

    responses: dict[tuple[str, ...], tuple[int, str, str]] = {
        ("rev-parse", "--show-toplevel"): (
            0,
            str(repository_root),
            "",
        ),
        ("branch", "--show-current"): (
            0,
            CANONICAL_BRANCH,
            "",
        ),
        ("config", "--get", "remote.origin.url"): (
            0,
            EXPECTED_ORIGIN,
            "",
        ),
        ("rev-parse", "HEAD"): (
            0,
            "a" * 40,
            "",
        ),
        (
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ): (
            0,
            status_output,
            "",
        ),
        (
            "rev-parse",
            "--abbrev-ref",
            "--symbolic-full-name",
            "@{upstream}",
        ): (
            upstream_exit_code,
            upstream_output,
            "no upstream configured"
            if upstream_exit_code
            else "",
        ),
        (
            "rev-list",
            "--left-right",
            "--count",
            "HEAD...@{upstream}",
        ): (
            0,
            ahead_behind_output,
            "",
        ),
    }

    calls: list[tuple[str, ...]] = []

    def fake_run_git(*args: str) -> tuple[int, str, str]:
        command = tuple(args)
        calls.append(command)

        if command not in responses:
            return 2, "", f"Unexpected Git command: {command!r}"

        return responses[command]

    monkeypatch.setattr(
        entrypoint,
        "_run_git",
        fake_run_git,
    )

    return calls


def test_entrypoint_contract_has_canonical_identity_and_state_authority():
    contract = entrypoint.contract()
    paths = entrypoint.repository_paths()

    assert contract.project == "HOMIO / REOS"
    assert entrypoint.REPOSITORY_FULL_NAME == REPOSITORY_NAME
    assert entrypoint.EXPECTED_BRANCH == CANONICAL_BRANCH

    assert contract.authoritative_state == CANONICAL_STATE
    assert Path(paths["state"]).as_posix().endswith(CANONICAL_STATE)

    assert paths["t07"]
    assert paths["t14"]
    assert paths["t18"]
    assert paths["t20"]
    assert paths["t21"]
    assert paths["t22"]
    assert paths["t23"]
    assert paths["t24"]


def test_entrypoint_policy_preserves_separate_acrl_responsibilities():
    combined_rules = "\n".join(
        (
            *entrypoint.AI_OPERATING_RULES,
            *entrypoint.DEVELOPMENT_WORKFLOW_RULES,
            *entrypoint.REMOTE_GIT_SYNCHRONIZATION_RULES,
            *entrypoint.REPOSITORY_PREFLIGHT_RULES,
        )
    )

    assert "T18" in combined_rules
    assert "T20" in combined_rules
    assert "T21" in combined_rules
    assert "T22" in combined_rules
    assert "T07" in combined_rules
    assert "T14" in combined_rules

    assert "state.json" in combined_rules
    assert "chat history" in combined_rules.lower()
    assert "standalone runner" in combined_rules.lower()


def test_clean_synchronized_checkout_can_pass_local_preflight(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    _install_preflight_fixture(
        monkeypatch,
        tmp_path,
    )

    result = entrypoint.git_preflight()

    assert result["cwd_ok"] is True
    assert result["repository_root_ok"] is True
    assert result["branch_ok"] is True
    assert result["origin_ok"] is True
    assert result["local_head_ok"] is True
    assert result["t21_authority_ok"] is True

    assert result["clean_worktree"] is True
    assert result["upstream_configured"] is True
    assert result["upstream_ref"] == "origin/reos-development"
    assert result["ahead_by"] == 0
    assert result["behind_by"] == 0
    assert result["ahead_behind_ok"] is True
    assert result["divergent"] is False
    assert result["ready"] is True


@pytest.mark.parametrize(
    "status_output",
    [
        " M tracked_file.py",
        "?? untracked_file.py",
        " M tracked_file.py\n?? untracked_file.py",
        "A  staged_file.py",
        " D deleted_file.py",
    ],
)
def test_dirty_or_untracked_worktree_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    status_output: str,
):
    _install_preflight_fixture(
        monkeypatch,
        tmp_path,
        status_output=status_output,
    )

    result = entrypoint.git_preflight()

    assert result["clean_worktree"] is False
    assert result["ready"] is False


def test_missing_upstream_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    _install_preflight_fixture(
        monkeypatch,
        tmp_path,
        upstream_output="",
        upstream_exit_code=128,
    )

    result = entrypoint.git_preflight()

    assert result["upstream_configured"] is False
    assert result["ahead_behind_ok"] is False
    assert result["ready"] is False


@pytest.mark.parametrize(
    ("counts", "expected_ahead", "expected_behind", "expected_divergent"),
    [
        ("1\t0", 1, 0, False),
        ("0\t1", 0, 1, False),
        ("2\t3", 2, 3, True),
    ],
)
def test_ahead_behind_or_divergent_checkout_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    counts: str,
    expected_ahead: int,
    expected_behind: int,
    expected_divergent: bool,
):
    _install_preflight_fixture(
        monkeypatch,
        tmp_path,
        ahead_behind_output=counts,
    )

    result = entrypoint.git_preflight()

    assert result["ahead_by"] == expected_ahead
    assert result["behind_by"] == expected_behind
    assert result["divergent"] is expected_divergent
    assert result["ahead_behind_ok"] is False
    assert result["ready"] is False


def test_local_upstream_tracking_does_not_claim_live_remote_proof(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    _install_preflight_fixture(
        monkeypatch,
        tmp_path,
    )

    result = entrypoint.git_preflight()

    assert result["live_remote_tip_proven"] is False
    assert result["remote_readback_required"] is True


def test_preflight_uses_only_expected_read_only_git_queries(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    calls = _install_preflight_fixture(
        monkeypatch,
        tmp_path,
    )

    entrypoint.git_preflight()

    assert calls
    assert set(calls).issubset(GIT_READ_COMMANDS)

    forbidden_commands = {
        "add",
        "checkout",
        "clean",
        "commit",
        "fetch",
        "merge",
        "pull",
        "push",
        "rebase",
        "reset",
        "restore",
        "switch",
        "update-ref",
    }

    for command in calls:
        assert command[0] not in forbidden_commands


def test_startup_instructions_expose_preflight_without_claiming_remote_success(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    _install_preflight_fixture(
        monkeypatch,
        tmp_path,
    )

    instructions = entrypoint.startup_instructions()
    preflight = instructions["git_preflight"]

    assert instructions["project"] == "HOMIO / REOS"
    assert instructions["authority"] == "REOS_CONTROL_CENTER"
    assert instructions["chat_history_authority"] == "NON_AUTHORITATIVE"

    assert preflight["live_remote_tip_proven"] is False
    assert preflight["remote_readback_required"] is True
