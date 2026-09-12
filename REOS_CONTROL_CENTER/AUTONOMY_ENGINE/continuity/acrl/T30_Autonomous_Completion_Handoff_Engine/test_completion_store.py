from .completion_store import CompletionStore, CompletionReplayError
from .completion_record import CompletionRecord
from .completion_models import CompletionState
def test_store_replay():
    s=CompletionStore(); r=CompletionRecord('M',CompletionState.COMPLETED,'x','ok'); s.put('M',r)
    try: s.put('M',r); assert False
    except CompletionReplayError: pass
