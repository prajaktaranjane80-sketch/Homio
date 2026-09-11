from __future__ import annotations

import shutil
from pathlib import Path
from tempfile import mkdtemp


EXCLUDED = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
}


def create_isolated_workspace(
    repository_root: Path | str,
) -> Path:
    source = Path(repository_root).resolve()

    if not source.is_dir():
        raise ValueError(
            f"Repository root does not exist: {source}"
        )

    destination = Path(
        mkdtemp(
            prefix="reos_t20_repair_"
        )
    )

    for item in source.iterdir():
        if item.name in EXCLUDED:
            continue

        target = destination / item.name

        if item.is_dir():
            shutil.copytree(
                item,
                target,
                ignore=shutil.ignore_patterns(
                    *EXCLUDED
                ),
            )
        else:
            shutil.copy2(item, target)

    return destination


def discard_workspace(workspace: Path) -> None:
    if workspace.exists():
        shutil.rmtree(
            workspace,
            ignore_errors=False,
        )
