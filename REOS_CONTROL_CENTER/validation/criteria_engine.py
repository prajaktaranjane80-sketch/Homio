def pending(gate):
    return [x['id'] for x in gate.get('criteria_state', []) if x['status'] != 'VERIFIED']
