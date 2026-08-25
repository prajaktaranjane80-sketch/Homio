
import json
from pathlib import Path

def test_policy_is_fail_closed():
    policy = json.loads(
        (Path(__file__).parents[1] / "policies" / "agent_policy.json").read_text()
    )
    assert policy["mode"] == "FAIL_CLOSED"
    assert policy["never_assume"] is True
    assert policy["semantic_mismatch_requires_proof"] is True
    assert policy["large_file_request_default"] is False
