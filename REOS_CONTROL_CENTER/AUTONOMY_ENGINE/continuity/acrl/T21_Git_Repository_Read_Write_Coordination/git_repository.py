from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class GitRepositoryError(RuntimeError):
    pass


class GitRepository:
    def __init__(
        self,
        repository_root: Path | str,
    ) -> None:
        self.root = Path(
            repository_root
        ).resolve()

        if not self.root.exists():
            raise GitRepositoryError(
                f"Repository not found: {self.root}"
            )

        if not self.root.is_dir():
            raise GitRepositoryError(
                "Repository root is not a directory."
            )

        if shutil.which("git") is None:
            raise GitRepositoryError(
                "Git executable not found."
            )

        result = self.run(
            "rev-parse",
            "--is-inside-work-tree",
        )

        if result.stdout.strip() != "true":
            raise GitRepositoryError(
                "Path is not a Git working tree."
            )

    def run(
        self,
        *args: str,
        timeout: int = 30,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise GitRepositoryError(
                f"Git command timed out: {' '.join(args)}"
            ) from exc

        if check and result.returncode != 0:
            raise GitRepositoryError(
                result.stderr.strip()
                or f"Git command failed: {' '.join(args)}"
            )

        return result

    def branch(self) -> str:
        return self.run(
            "branch",
            "--show-current",
        ).stdout.strip()

    def head(self) -> str:
        return self.run(
            "rev-parse",
            "HEAD",
        ).stdout.strip()

    def status_porcelain(self) -> str:
        return self.run(
            "status",
            "--porcelain=v1",
        ).stdout

    def diff_cached(self) -> str:
        return self.run(
            "diff",
            "--cached",
            "--no-ext-diff",
            "--binary",
        ).stdout

    def changed_files(self) -> tuple[str, ...]:
        output = self.run(
            "status",
            "--porcelain=v1",
        ).stdout

        paths: set[str] = set()

        for line in output.splitlines():
            if len(line) < 4:
                continue

            value = line[3:].strip()

            if " -> " in value:
                value = value.split(
                    " -> ",
                    1,
                )[1]

            paths.add(
                value.replace("\\", "/")
            )

        return tuple(
            sorted(paths)
        )

    def remote_names(self) -> tuple[str, ...]:
        output = self.run(
            "remote",
        ).stdout

        return tuple(
            sorted(
                item.strip()
                for item in output.splitlines()
                if item.strip()
            )
        )

    def commit_exists(
        self,
        sha: str,
    ) -> bool:
        result = self.run(
            "cat-file",
            "-e",
            f"{sha}^{{commit}}",
            check=False,
        )

        return result.returncode == 0

    def current_tree_sha(self) -> str:
        return self.run(
            "rev-parse",
            "HEAD^{tree}",
        ).stdout.strip()
