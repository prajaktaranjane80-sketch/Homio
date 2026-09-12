from threading import RLock

class CompletionReplayError(RuntimeError): pass
class CompletionIdentityCollision(RuntimeError): pass

class CompletionStore:
    def __init__(self):
        self._lock = RLock(); self._items = {}
    def get(self, mission_id):
        with self._lock: return self._items.get(mission_id)
    def put(self, mission_id, record):
        with self._lock:
            existing = self._items.get(mission_id)
            if existing is not None:
                if existing.fingerprint == record.fingerprint:
                    raise CompletionReplayError("completion already recorded")
                raise CompletionIdentityCollision("completion identity collision")
            self._items[mission_id] = record
