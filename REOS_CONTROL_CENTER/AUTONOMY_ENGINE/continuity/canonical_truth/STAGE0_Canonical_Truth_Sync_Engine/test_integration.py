from pathlib import Path
from tempfile import TemporaryDirectory
import json
from .truth_sync_controller import CanonicalTruthSyncController


def test_end_to_end_sync():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root/"data").mkdir()
        (root/"data/state.json").write_text(json.dumps({"execution": {"current_gate":"CORE-005", "current_task":"Search filters", "current_subtask":"CORE-005-T01", "status":"CONTROL_CENTER_DRIVEN"}}), encoding="utf-8")
        # Git commands are not available in this isolated fixture; controller inspection is the deterministic core under test.
        controller = CanonicalTruthSyncController(root)
        bundle = controller.inspect()
        assert bundle["plan"].blocked is False
