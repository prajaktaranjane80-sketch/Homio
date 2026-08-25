def snapshot_copy(state_path, snapshot_dir):
    import shutil, datetime as dt
    from pathlib import Path
    p = Path(snapshot_dir); p.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    shutil.copy2(state_path, p / f'state_{stamp}.json')
