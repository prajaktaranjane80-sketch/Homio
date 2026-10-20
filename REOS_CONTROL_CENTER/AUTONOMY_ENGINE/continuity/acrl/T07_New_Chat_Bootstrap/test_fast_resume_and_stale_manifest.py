from __future__ import annotations

from datetime import datetime, timezone

from AUTONOMY_ENGINE.continuity.acrl.T07_New_Chat_Bootstrap.new_chat_bootstrap import (
    NewChatBootstrapEngine,
)
from AUTONOMY_ENGINE.continuity.acrl.T14_Repository_Intelligence_Context.audit_resume_manifest import (
    MANIFEST_STATUS,
    ResumeDecision,
    seal_manifest,
)

NOW = datetime(2026, 10, 20, 12, 0, tzinfo=timezone.utc)
HEAD = "a" * 40
STATE = "b" * 40
BLOB = "c" * 40


def _manifest():
    return seal_manifest({
        "schema_version": "1.0",
        "status": "SEALED",
        "manifest_status": MANIFEST_STATUS,
        "authority": "REOS_CONTROL_CENTER",
        "repository": "prajaktaranjane80-sketch/Homio",
        "branch": "reos-development",
        "audit_base_commit_sha": HEAD,
        "state_json_blob_sha": STATE,
        "position_snapshot": {
            "current_task": "MUST_NOT_BE_AUTHORITY"
        },
        "audited_path_blob_shas": {
            "core/a.py": BLOB
        },
        "finding_status": {
            "P1-EXAMPLE": {
                "status": "OPEN",
                "paths": ["core/a.py"],
                "evidence_ids": [],
            }
        },
        "test_ci_evidence": [],
        "research_evidence": [],
        "blockers": [],
        "generated_at": NOW.isoformat(),
    })


def _live(**overrides):
    snapshot = {
        "repository": "prajaktaranjane80-sketch/Homio",
        "branch": "reos-development",
        "head_commit_sha": HEAD,
        "delta_base_commit_sha": HEAD,
        "state_json_blob_sha": STATE,
        "working_tree_clean": True,
        "changed_paths": [],
        "deleted_paths": [],
        "path_blob_shas": {
            "core/a.py": BLOB
        },
        "current_position": {
            "current_gate": "CORE-008",
            "current_task": "CORE-008-T04",
            "current_subtask": "CORE-008-T04",
            "current_subtask_status": "CONTROL_CENTER_DRIVEN",
        },
    }
    snapshot.update(overrides)
    return snapshot


def test_t07_fast_resume_adapter_reuses_unchanged_manifest():
    result = NewChatBootstrapEngine.evaluate_fast_resume(
        manifest=_manifest(),
        live_snapshot=_live(),
        now=NOW,
    )
    assert result.decision is ResumeDecision.FAST_RESUME
    assert (
        result.resume_packet["active_task"]["current_task"]
        == "CORE-008-T04"
    )


def test_t07_forces_fresh_bootstrap_when_state_sha_changes():
    result = NewChatBootstrapEngine.evaluate_fast_resume(
        manifest=_manifest(),
        live_snapshot=_live(state_json_blob_sha="d" * 40),
        now=NOW,
    )
    assert result.decision is ResumeDecision.FULL_AUDIT_REQUIRED
    assert result.full_audit_required is True


def test_t07_targeted_resume_reports_only_changed_dependents():
    result = NewChatBootstrapEngine.evaluate_fast_resume(
        manifest=_manifest(),
        live_snapshot=_live(
            head_commit_sha="e" * 40,
            delta_base_commit_sha=HEAD,
            changed_paths=["core/a.py"],
            path_blob_shas={"core/a.py": "d" * 40},
        ),
        dependency_graph={
            "core/a.py": ["tests/test_a.py"]
        },
        now=NOW,
    )
    assert result.decision is ResumeDecision.TARGETED_REAUDIT
    assert result.invalidated_paths == (
        "core/a.py",
        "tests/test_a.py",
    )


def test_t07_does_not_trust_position_snapshot_in_manifest():
    result = NewChatBootstrapEngine.evaluate_fast_resume(
        manifest=_manifest(),
        live_snapshot=_live(),
        now=NOW,
    )
    assert (
        result.resume_packet["active_task"]["current_task"]
        == "CORE-008-T04"
    )
    assert (
        result.resume_packet["active_task"]["current_task"]
        != "MUST_NOT_BE_AUTHORITY"
    )
