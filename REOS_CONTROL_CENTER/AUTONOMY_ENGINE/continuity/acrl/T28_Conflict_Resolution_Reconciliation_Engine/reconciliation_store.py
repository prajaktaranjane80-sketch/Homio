reconciliation_store.pyfrom threading import RLock


class ReconciliationReplayError(RuntimeError):
    pass


class ReconciliationIdentityCollision(RuntimeError):
    pass


class ReconciliationStore:
    def __init__(self):
        self._lock = RLock()
        self._items = {}

    def get(self, reconciliation_id: str):
        with self._lock:
            return self._items.get(reconciliation_id)

    def put(self, reconciliation_id: str, snapshot) -> None:
        with self._lock:
            existing = self._items.get(reconciliation_id)
            if existing is not None:
                if existing.fingerprint == snapshot.fingerprint:
                    raise ReconciliationReplayError(
                        "reconciliation already processed"
                    )
                raise ReconciliationIdentityCollision(
                    "reconciliation identity collision"
                )

            self._items[reconciliation_id] = snapshot
