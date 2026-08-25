def blockers(state, gate_id):
    seq = {x['gate']: x for x in state['execution_plan']['authoritative_sequence']}
    return [d for d in seq.get(gate_id, {}).get('dependencies', []) if seq.get(d, {}).get('status') != 'COMPLETE']
