from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess


class GitTruthError(RuntimeError):
    pass


@dataclass(frozen=True)
class GitTruth:
    branch: str
    commit: str
    clean: bool | None


class GitTruthReader:
    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()

    def _run(self, *args: str) -> str:
        proc = subprocess.run(
            ["git", *args],
            cwd=self.root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if proc.returncode != 0:
            raise GitTruthError(proc.stderr.strip() or "git command failed")
        return proc.stdout.strip()

    def read(self) -> GitTruth:
        try:
            branch = self._run("branch", "--show-current")
            commit = self._run("rev-parse", "HEAD")
            status = self._run("status", "--porcelain")
            return GitTruth(branch=branch, commit=commit, clean=(status == ""))
        except GitTruthError:
            # Fixture/testing environments may intentionally omit .git.
            # Production execution should run inside the canonical repository.
            return GitTruth(branch="UNAVAILABLE", commit="UNAVAILABLE", clean=None)
