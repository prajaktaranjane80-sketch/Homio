import json, tempfile, os
from pathlib import Path

def load_state(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def atomic_save(path, state):
    path = Path(path)
    fd, tmp = tempfile.mkstemp(prefix='.reos-', suffix='.tmp', dir=path.parent)
    os.close(fd)
    p = Path(tmp)
    try:
        p.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding='utf-8')
        os.replace(p, path)
    finally:
        p.unlink(missing_ok=True)
