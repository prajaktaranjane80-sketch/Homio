def ready_for_approval(gate):
    approval = next((x for x in gate.get('subtasks', []) if 'approve' in x.get('title','').lower() or 'freeze' in x.get('title','').lower()), None)
    blockers = [x['id'] for x in gate.get('subtasks', []) if x is not approval and x['status'] not in ('DONE','CLOSED')]
    criteria = [x['id'] for x in gate.get('criteria_state', []) if x['status'] != 'VERIFIED']
    return not blockers and not criteria
