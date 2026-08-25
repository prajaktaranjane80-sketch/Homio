def materialize(state, gate_id, template):
    if gate_id in state.get('gate_plans', {}):
        return state['gate_plans'][gate_id]
    subs = template['subtasks']
    state['gate_plans'][gate_id] = {
        'id': gate_id,
        'name': template['name'],
        'objective': template['objective'],
        'status': 'CURRENT',
        'current_subtask': f"{gate_id}-{subs[0][0]}",
        'subtasks': [
            {'id': f"{gate_id}-{a}", 'title': b, 'priority': c, 'status': 'CURRENT' if i == 0 else 'PENDING'}
            for i, (a, b, c) in enumerate(subs)
        ],
        'criteria_state': [
            {'id': f"{gate_id}-AC{i:02d}", 'criterion': c, 'status': 'PENDING', 'evidence': None}
            for i, c in enumerate(template['criteria'], 1)
        ],
    }
    return state['gate_plans'][gate_id]
