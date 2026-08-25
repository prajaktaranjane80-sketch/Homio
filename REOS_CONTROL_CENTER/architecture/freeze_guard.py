def can_mutate(state, gate_id):
    return not any(x.get('id') == gate_id and x.get('status') == 'APPROVED' for x in state['architecture']['approved'])
