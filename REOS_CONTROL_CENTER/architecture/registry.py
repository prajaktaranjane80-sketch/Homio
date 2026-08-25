def is_approved(state, gate_id):
    return any(x.get('id') == gate_id and x.get('status') == 'APPROVED' for x in state['architecture']['approved'])
