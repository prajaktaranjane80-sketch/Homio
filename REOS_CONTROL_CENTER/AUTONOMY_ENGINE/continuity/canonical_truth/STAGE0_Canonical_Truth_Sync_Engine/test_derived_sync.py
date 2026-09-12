from pathlib import Path
from tempfile import TemporaryDirectory
from .truth_models import CanonicalManifest, ReconciliationPlan
from .derived_sync_engine import DerivedSyncEngine


def test_sync_creates_derived_artifacts():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        m = CanonicalManifest("1", "HOMIO / REOS", "reos-development", "x", str(root/"data/state.json"), "d", "abc", "CORE-005", "task", "CORE-005-T01", "CONTROL", tuple(), tuple(), "m")
        p = ReconciliationPlan("p", "d", ("ENSURE_DERIVED_ARTIFACTS",), tuple(), False, "ok")
        receipt = DerivedSyncEngine(root).synchronize(m, p)
        assert receipt.status.value == "SYNCHRONIZED"
        assert (root/"REOS_NEXT_CHAT.txt").exists()
