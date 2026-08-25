def is_approval_subtask(item):
    t = item.get('title','').lower()
    return 'approve' in t or 'freeze' in t

def next_subtask(gate):
    return next((x for x in gate['subtasks'] if x['status'] not in ('DONE','CLOSED','READY_FOR_APPROVAL')), None)
