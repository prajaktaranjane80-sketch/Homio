from pathlib import Path
import shutil
BASE = Path(__file__).resolve().parent.parent
LIVE = Path(r'D:\HOMIO\REOS_CONTROL_CENTER')
if not LIVE.exists():
    raise SystemExit(f'Live folder not found: {LIVE}')
for part in ('01_core_architecture','02_execution_engine','03_continuity_integrity'):
    for src in (BASE/part).rglob('*'):
        if src.is_file() and src.name not in ('README.txt',):
            rel = src.relative_to(BASE/part)
            dest = LIVE/'modules'/rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
print('Micro-modules merged. data/state.json preserved.')
