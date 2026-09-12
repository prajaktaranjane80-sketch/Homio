from .canonical_manifest import build_manifest


def test_manifest_digest_is_deterministic():
    a = build_manifest(project="H", branch="b", authority_id="s", canonical_state_path="p", state_digest="d", state_revision="r", execution={"current_gate":"G","current_task":"T","current_subtask":"S","status":"OK"}, derived_artifacts=[], conflicts=())
    b = build_manifest(project="H", branch="b", authority_id="s", canonical_state_path="p", state_digest="d", state_revision="r", execution={"current_gate":"G","current_task":"T","current_subtask":"S","status":"OK"}, derived_artifacts=[], conflicts=())
    assert a.manifest_digest == b.manifest_digest
