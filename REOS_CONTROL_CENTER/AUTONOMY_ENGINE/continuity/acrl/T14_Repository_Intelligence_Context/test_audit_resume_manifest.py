from __future__ import annotations

from datetime import datetime, timedelta, timezone

from AUTONOMY_ENGINE.continuity.acrl.T14_Repository_Intelligence_Context.audit_resume_manifest import (
    MANIFEST_STATUS,
    ResumeDecision,
    assess_resume_manifest,
    build_manifest,
    seal_manifest,
    validate_manifest_shape,
)

HEAD = "a" * 40
STATE = "b" * 40
OLD = "c" * 40
NEW = "d" * 40
NOW = datetime(2026, 10, 20, 12, 0, tzinfo=timezone.utc)


def make_manifest(**changes):
    value = {
        "schema_version": "1.0",
        "status": "SEALED",
        "manifest_status": MANIFEST_STATUS,
        "authority": "REOS_CONTROL_CENTER",
        "repository": "prajaktaranjane80-sketch/Homio",
        "branch": "reos-development",
        "audit_base_commit_sha": HEAD,
        "state_json_blob_sha": STATE,
        "position_snapshot": {
            "current_gate": "DISPLAY_ONLY_NOT_AUTHORITY"
        },
        "audited_path_blob_shas": {
            "src/a.py": OLD,
            "src/b.py": OLD,
        },
        "finding_status": {
            "P1-X": {
                "status": "PASS",
                "paths": ["src/a.py"],
                "evidence_ids": ["CI-1"],
            }
        },
        "test_ci_evidence": [
            {
                "evidence_id": "CI-1",
                "kind": "ci",
                "url": "https://github.com/example/run/1",
                "source_commit_sha": HEAD,
                "result": "PASS",
                "retrieved_at": NOW.isoformat(),
                "finding_ids": ["P1-X"],
            }
        ],
        "research_evidence": [
            {
                "evidence_id": "WEB-1",
                "kind": "research",
                "url": "https://docs.github.com/",
                "retrieved_at": NOW.isoformat(),
                "finding_ids": ["P1-X"],
            }
        ],
        "blockers": [],
        "generated_at": NOW.isoformat(),
    }
    value.update(changes)
    return seal_manifest(value)


def live(**changes):
    value = {
        "working_tree_clean": True,
        "repository": "prajaktaranjane80-sketch/Homio",
        "branch": "reos-development",
        "head_commit_sha": HEAD,
        "delta_base_commit_sha": HEAD,
        "state_json_blob_sha": STATE,
        "changed_paths": [],
        "deleted_paths": [],
        "path_blob_shas": {
            "src/a.py": OLD,
            "src/b.py": OLD,
        },
        "current_position": {
            "current_gate": "CORE-008",
            "current_task": "CORE-008-T04",
            "current_subtask": "CORE-008-T04",
            "current_subtask_status": "CONTROL_CENTER_DRIVEN",
        },
    }
    value.update(changes)
    return value


def test_unchanged_live_state_uses_fast_resume():
    result = assess_resume_manifest(make_manifest(), live(), now=NOW)
    assert result.decision is ResumeDecision.FAST_RESUME
    assert result.full_audit_required is False
    assert result.resume_packet["active_task"]["current_task"] == "CORE-008-T04"


def test_current_position_is_taken_from_live_state_not_manifest():
    result = assess_resume_manifest(make_manifest(), live(), now=NOW)
    assert result.resume_packet["active_task"]["current_gate"] == "CORE-008"
    assert result.resume_packet["active_task"]["current_gate"] != "DISPLAY_ONLY_NOT_AUTHORITY"


def test_state_sha_change_requires_full_bootstrap():
    result = assess_resume_manifest(
        make_manifest(),
        live(state_json_blob_sha=NEW),
        now=NOW,
    )
    assert result.decision is ResumeDecision.FULL_AUDIT_REQUIRED
    assert result.full_audit_required is True
    assert result.resume_packet["manifest_reuse"] is False


def test_branch_mismatch_never_falls_back_silently():
    result = assess_resume_manifest(
        make_manifest(),
        live(branch="main"),
        now=NOW,
    )
    assert result.decision is ResumeDecision.FULL_AUDIT_REQUIRED
    assert "fallback" in result.reason


def test_head_delta_invalidates_changed_path_and_transitive_dependents():
    manifest = make_manifest(audit_base_commit_sha=OLD)
    snapshot = live(
        head_commit_sha=HEAD,
        delta_base_commit_sha=OLD,
        changed_paths=["src/a.py"],
        path_blob_shas={"src/a.py": NEW, "src/b.py": OLD},
    )
    result = assess_resume_manifest(
        manifest,
        snapshot,
        dependency_graph={
            "src/a.py": ["src/b.py"],
            "src/b.py": ["tests/test_b.py"],
        },
        now=NOW,
    )
    assert result.decision is ResumeDecision.TARGETED_REAUDIT
    assert result.invalidated_paths == (
        "src/a.py",
        "src/b.py",
        "tests/test_b.py",
    )
    assert result.full_audit_required is False


def test_head_changed_without_verified_delta_requires_full_audit():
    result = assess_resume_manifest(
        make_manifest(audit_base_commit_sha=OLD),
        live(
            changed_paths=[],
            head_commit_sha=HEAD,
            delta_base_commit_sha=OLD,
        ),
        now=NOW,
    )
    assert result.decision is ResumeDecision.FULL_AUDIT_REQUIRED


def test_missing_sha_for_changed_path_fails_closed():
    result = assess_resume_manifest(
        make_manifest(audit_base_commit_sha=OLD),
        live(
            head_commit_sha=HEAD,
            delta_base_commit_sha=OLD,
            changed_paths=["src/a.py"],
            path_blob_shas={"src/b.py": OLD},
        ),
        now=NOW,
    )
    assert result.decision is ResumeDecision.FULL_AUDIT_REQUIRED


def test_deleted_path_invalidates_dependents():
    result = assess_resume_manifest(
        make_manifest(audit_base_commit_sha=OLD),
        live(
            head_commit_sha=HEAD,
            delta_base_commit_sha=OLD,
            changed_paths=[],
            deleted_paths=["src/a.py"],
            path_blob_shas={"src/b.py": OLD},
        ),
        dependency_graph={"src/a.py": ["src/b.py"]},
        now=NOW,
    )
    assert result.decision is ResumeDecision.TARGETED_REAUDIT
    assert "src/b.py" in result.invalidated_paths


def test_expired_ci_evidence_never_surfaces_as_current_pass():
    oldtime = (NOW - timedelta(days=40)).isoformat()
    manifest = make_manifest(
        test_ci_evidence=[
            {
                "evidence_id": "CI-OLD",
                "kind": "ci",
                "url": "https://example.test/run",
                "source_commit_sha": HEAD,
                "result": "PASS",
                "retrieved_at": oldtime,
            }
        ],
        finding_status={
            "P1-X": {
                "status": "PASS",
                "paths": ["src/a.py"],
                "evidence_ids": ["CI-OLD"],
            }
        },
    )
    result = assess_resume_manifest(manifest, live(), now=NOW)
    assert result.decision is ResumeDecision.TARGETED_REAUDIT
    assert "CI-OLD" in result.stale_evidence_ids
    assert result.resume_packet["last_exact_pass_evidence"] == []
    assert "P1-X" in result.affected_findings


def test_ci_evidence_from_an_older_commit_is_not_current_pass():
    manifest = make_manifest(
        test_ci_evidence=[
            {
                "evidence_id": "CI-OLD-SHA",
                "kind": "ci",
                "url": "https://example.test/run",
                "source_commit_sha": OLD,
                "result": "PASS",
                "retrieved_at": NOW.isoformat(),
            }
        ]
    )
    result = assess_resume_manifest(manifest, live(), now=NOW)
    assert "CI-OLD-SHA" in result.stale_evidence_ids
    assert result.resume_packet["last_exact_pass_evidence"] == []


def test_expired_research_requires_refresh_without_full_tree_scan():
    oldtime = (NOW - timedelta(days=45)).isoformat()
    manifest = make_manifest(
        research_evidence=[
            {
                "evidence_id": "WEB-OLD",
                "kind": "research",
                "url": "https://docs.example.test/",
                "retrieved_at": oldtime,
                "finding_ids": ["P1-X"],
            }
        ],
        finding_status={
            "P1-X": {
                "status": "PASS",
                "paths": [],
                "evidence_ids": ["WEB-OLD"],
            }
        },
    )
    result = assess_resume_manifest(manifest, live(), now=NOW)
    assert result.decision is ResumeDecision.TARGETED_REAUDIT
    assert result.full_audit_required is False
    assert "WEB-OLD" in result.stale_evidence_ids


def test_tampered_manifest_is_rejected():
    manifest = make_manifest()
    manifest["branch"] = "main"
    result = assess_resume_manifest(manifest, live(), now=NOW)
    assert result.decision is ResumeDecision.INVALID_MANIFEST
    assert result.full_audit_required is True


def test_unsafe_path_is_rejected():
    manifest = make_manifest(
        audited_path_blob_shas={"../secret.py": OLD}
    )
    result = assess_resume_manifest(manifest, live(), now=NOW)
    assert result.decision is ResumeDecision.INVALID_MANIFEST


def test_malformed_timestamp_fails_manifest_validation():
    manifest = make_manifest(generated_at="yesterday")
    result = assess_resume_manifest(manifest, live(), now=NOW)
    assert result.decision is ResumeDecision.INVALID_MANIFEST


def test_manifest_fingerprint_is_not_authority():
    manifest = make_manifest(
        position_snapshot={"current_task": "INVENTED"}
    )
    result = assess_resume_manifest(manifest, live(), now=NOW)
    assert result.decision is ResumeDecision.FAST_RESUME
    assert result.resume_packet["active_task"]["current_task"] == "CORE-008-T04"


def test_bad_dependency_graph_fails_closed():
    manifest = make_manifest(audit_base_commit_sha=OLD)
    result = assess_resume_manifest(
        manifest,
        live(
            head_commit_sha=HEAD,
            delta_base_commit_sha=OLD,
            changed_paths=["src/a.py"],
            path_blob_shas={"src/a.py": NEW, "src/b.py": OLD},
        ),
        dependency_graph={"src/a.py": "src/b.py"},
        now=NOW,
    )
    assert result.decision is ResumeDecision.FULL_AUDIT_REQUIRED


def test_uninitialized_template_cannot_fast_resume():
    result = assess_resume_manifest(
        {"schema_version": "1.0", "status": "UNINITIALIZED"},
        live(),
        now=NOW,
    )
    assert result.decision is ResumeDecision.INVALID_MANIFEST
    assert result.full_audit_required is True


def test_dirty_worktree_requires_fresh_audit():
    result = assess_resume_manifest(
        make_manifest(),
        live(working_tree_clean=False),
        now=NOW,
    )
    assert result.decision is ResumeDecision.FULL_AUDIT_REQUIRED
    assert result.full_audit_required is True


def test_delta_base_must_match_manifest_base():
    result = assess_resume_manifest(
        make_manifest(audit_base_commit_sha=OLD),
        live(
            head_commit_sha=HEAD,
            delta_base_commit_sha="e" * 40,
            changed_paths=["src/a.py"],
            path_blob_shas={"src/a.py": NEW, "src/b.py": OLD},
        ),
        now=NOW,
    )
    assert result.decision is ResumeDecision.FULL_AUDIT_REQUIRED


def test_builder_creates_a_validated_sealed_manifest():
    manifest = build_manifest(
        repository="prajaktaranjane80-sketch/Homio",
        branch="reos-development",
        audit_base_commit_sha=HEAD,
        state_json_blob_sha=STATE,
        position_snapshot={"current_task": "DISPLAY_ONLY"},
        audited_path_blob_shas={"src/a.py": OLD},
        finding_status={
            "P1-X": {
                "status": "OPEN",
                "paths": ["src/a.py"],
                "evidence_ids": [],
            }
        },
        test_ci_evidence=[],
        research_evidence=[],
        generated_at=NOW,
    )
    validate_manifest_shape(manifest)
    assert manifest["status"] == "SEALED"
    assert len(manifest["manifest_fingerprint"]) == 64


def test_t14_full_resolution_uses_one_t16_snapshot_for_multiple_terms(
    tmp_path,
    monkeypatch,
):
    from AUTONOMY_ENGINE.continuity.acrl.T14_Repository_Intelligence_Context import (
        repository_context,
    )

    root = tmp_path / "repo"
    (root / "core").mkdir(parents=True)
    (root / "tests").mkdir()

    (root / "core" / "alpha.py").write_text(
        "class Alpha: pass\n",
        encoding="utf-8",
    )
    (root / "tests" / "test_alpha.py").write_text(
        "def test_alpha(): assert True\n",
        encoding="utf-8",
    )

    calls = {"count": 0}
    original = repository_context.discover_repository

    def counted_discover(*args, **kwargs):
        calls["count"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(
        repository_context,
        "discover_repository",
        counted_discover,
    )

    request = repository_context.RepositoryContextRequest(
        repository_root=root,
        current_gate="CORE-004",
        current_task="Implement alpha domain",
        current_subtask="CORE-004-T02",
        candidate_paths=("core/alpha.py",),
        search_terms=("alpha", "domain", "test_alpha.py"),
    )
    report = repository_context.RepositoryContextEngine.resolve(request)

    assert (
        report.decision
        is repository_context.RepositoryContextDecision.RESOLVED
    )
    assert calls["count"] == 1
