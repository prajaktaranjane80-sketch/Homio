from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RepositoryFinding:
    path: str
    reason: str
    category: str


class RepositoryRuntime:
    """Targeted Git/repository inspection."""

    def __init__(
        self,
        root: Path,
        *,
        max_results: int = 20,
    ) -> None:
        self.root = Path(root).resolve()
        self.max_results = max_results

    def _git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=self.root,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"git command failed: {result.stderr.strip()}"
            )

        return result.stdout.strip()

    def branch(self) -> str:
        return self._git(
            "branch",
            "--show-current",
        )

    def head(self) -> str:
        return self._git(
            "rev-parse",
            "HEAD",
        )

    def worktree_clean(self) -> bool:
        return not bool(
            self._git(
                "status",
                "--porcelain",
            )
        )

    def changed_paths(self) -> list[str]:
        output = self._git(
            "status",
            "--porcelain",
        )

        return [
            line[3:]
            for line in output.splitlines()
            if len(line) >= 4
        ][: self.max_results]

    def find_paths(
        self,
        keywords: list[str],
    ) -> list[RepositoryFinding]:
        tracked = self._git(
            "ls-files",
        ).splitlines()

        terms = [
            item.lower().strip()
            for item in keywords
            if item and item.strip()
        ]

        result: list[RepositoryFinding] = []

        for path in tracked:
            low = path.lower()

            matched = next(
                (
                    term
                    for term in terms
                    if term in low
                ),
                None,
            )

            if matched is None:
                continue

            result.append(
                RepositoryFinding(
                    path=path,
                    reason=f"keyword:{matched}",
                    category="TRACKED_PATH",
                )
            )

            if len(result) >= self.max_results:
                break

        return result
