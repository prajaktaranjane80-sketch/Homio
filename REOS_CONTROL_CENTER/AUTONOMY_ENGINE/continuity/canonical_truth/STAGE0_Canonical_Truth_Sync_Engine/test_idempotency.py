from pathlib import Path
from tempfile import TemporaryDirectory
from .derived_sync_engine import DerivedSyncEngine
from .truth_models import CanonicalManifest, ReconciliationPlan


def test_derived_sync_is_repeatable():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        m = CanonicalManifest("1", "HOMIO / REOS", "reos-development", "x", "state.json", "d", "r", "CORE-005", "task", "T01", "OK", tuple(), tuple(), "m")
        p = ReconciliationPlan("p", "d", ("ENSURE_DERIVED_ARTIFACTS",), tuple(), False, "ok")
        engine = DerivedSyncEngine(root)
        a = engine.synchronize(m, p)
        b = engine.synchronize(m, p)
        assert a.receipt_digest == b.receipt_digest
