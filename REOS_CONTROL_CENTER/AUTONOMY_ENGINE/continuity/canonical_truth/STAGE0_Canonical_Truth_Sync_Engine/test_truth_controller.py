from pathlib import Path
from tempfile import TemporaryDirectory
import json

from reos_control_center import calculate_hash
from .truth_sync_controller import CanonicalTruthSyncController


def _write_valid_state(root: Path) -> None:
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    state = {
        "execution": {
            "current_gate": "CORE-005",
            "current_task": "task",
            "current_subtask": "CORE-005-T01",
            "status": "CONTROL_CENTER_DRIVEN",
        },
        "integrity": {"sha256": None},
    }
    state["integrity"]["sha256"] = calculate_hash(state)

    (data_dir / "state.json").write_text(
        json.dumps(state),
        encoding="utf-8",
    )


def test_controller_inspects_authority():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_valid_state(root)

        controller = CanonicalTruthSyncController(root)
        result = controller.inspect()

        assert result["manifest"].current_gate == "CORE-005"