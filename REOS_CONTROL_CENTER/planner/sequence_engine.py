def current_step(state):
    return next((x for x in state['execution_plan']['authoritative_sequence'] if x.get('status') == 'CURRENT'), None)
