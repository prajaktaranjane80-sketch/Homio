def already_applied(state, event_key):
    return any(e.get('idempotency_key') == event_key for e in state.get('events', []))
