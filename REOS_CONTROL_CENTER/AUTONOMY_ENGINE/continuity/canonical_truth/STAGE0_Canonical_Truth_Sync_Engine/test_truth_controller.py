from pathlib import Path
from tempfile import TemporaryDirectory
import json
from .truth_sync_controller import CanonicalTruthSyncController


def test_controller_inspects_authority():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root/"data").mkdir()
        (root/"data/state.json").write_text(json.dumps({"execution": {"current_gate":"CORE-005", "current_task":"task", "current_subtask":"CORE-005-T01", "status":"CONTROL_CENTER_DRIVEN"}}), encoding="utf-8")
        controller = CanonicalTruthSyncController(root)
        result = controller.inspect()
        assert result["manifest"].current_gate == "CORE-005"
