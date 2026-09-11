from __future__ import annotations

from .git_identity import fingerprint
from .git_models import GitRepositorySnapshot
from .git_repository import GitRepository


class GitReader:
    def __init__(
        self,
        repository_root,
    ) -> None:
        self.repository = GitRepository(
            repository_root
        )

    def snapshot(
        self,
    ) -> GitRepositorySnapshot:
        branch = self.repository.branch()
        head = self.repository.head()
        status = self.repository.status_porcelain()

        payload = {
            "branch": branch,
            "head": head,
            "status": status,
            "remotes": self.repository.remote_names(),
        }

        return GitRepositorySnapshot(
            repository_root=str(
                self.repository.root
            ),
            branch=branch,
            head_sha=head,
            status_porcelain=status,
            working_tree_clean=(status == ""),
            remote_names=self.repository.remote_names(),
            fingerprint=fingerprint(payload),
        )

    def status(self) -> str:
        return self.repository.status_porcelain()

    def head(self) -> str:
        return self.repository.head()

    def branch(self) -> str:
        return self.repository.branch()
