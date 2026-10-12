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
            "current_task": "Search filters",
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


def test_end_to_end_sync():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_valid_state(root)

        # Git metadata may be unavailable in an isolated fixture.
        # The canonical state itself must still pass its integrity check.
        controller = CanonicalTruthSyncController(root)
        bundle = controller.inspect()

        assert bundle["plan"].blocked is False
        assert bundle["manifest"].current_gate == "CORE-005"