from threading import RLock


class DecisionReplayError(RuntimeError):
    pass


class DecisionIdentityCollision(RuntimeError):
    pass


class DecisionStore:
    def __init__(self):
        self._lock = RLock()
        self._items = {}

    def get(self, decision_id: str):
        with self._lock:
            return self._items.get(decision_id)

    def put(self, decision_id: str, record) -> None:
        with self._lock:
            existing = self._items.get(decision_id)

            if existing is not None:
                if existing.fingerprint == record.fingerprint:
                    raise DecisionReplayError(
                        "decision already processed"
                    )

                raise DecisionIdentityCollision(
                    "decision identity collision"
                )

            self._items[decision_id] = record
