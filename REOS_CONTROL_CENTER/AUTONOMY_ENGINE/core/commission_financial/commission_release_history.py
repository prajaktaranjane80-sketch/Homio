from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .commission_release import CommissionRelease


class CommissionReleaseHistoryError(
    ValueError
):
    """Invalid financial release history."""


@dataclass(frozen=True, slots=True)
class CommissionReleaseHistoryEntry:
    release_id: str
    tenant_id: str
    commission_id: str
    statement_id: str
    release_version: int
    state: str
    release_fingerprint: str

    @classmethod
    def from_release(
        cls,
        release: CommissionRelease,
    ) -> "CommissionReleaseHistoryEntry":
        if not isinstance(
            release,
            CommissionRelease,
        ):
            raise CommissionReleaseHistoryError(
                "release must be CommissionRelease."
            )

        return cls(
            release_id=release.release_id,
            tenant_id=release.tenant_id,
            commission_id=release.commission_id,
            statement_id=release.statement_id,
            release_version=release.release_version,
            state=release.state.value,
            release_fingerprint=(
                release.immutable_fingerprint
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "release_id": self.release_id,
            "tenant_id": self.tenant_id,
            "commission_id": self.commission_id,
            "statement_id": self.statement_id,
            "release_version": (
                self.release_version
            ),
            "state": self.state,
            "release_fingerprint": (
                self.release_fingerprint
            ),
        }


@dataclass(frozen=True, slots=True)
class CommissionReleaseHistory:
    entries: tuple[
        CommissionReleaseHistoryEntry,
        ...
    ] = ()

    def append(
        self,
        release: CommissionRelease,
    ) -> "CommissionReleaseHistory":
        entry = (
            CommissionReleaseHistoryEntry
            .from_release(release)
        )

        if self.entries:
            latest = self.entries[-1]

            if (
                latest.tenant_id
                != entry.tenant_id
                or latest.release_id
                != entry.release_id
            ):
                raise CommissionReleaseHistoryError(
                    "Release history identity mismatch."
                )

            if (
                entry.release_version
                != latest.release_version + 1
            ):
                if (
                    entry.release_version
                    == latest.release_version
                    and entry.release_fingerprint
                    == latest.release_fingerprint
                ):
                    return self

                raise CommissionReleaseHistoryError(
                    "Release versions must advance sequentially."
                )

        elif entry.release_version != 1:
            raise CommissionReleaseHistoryError(
                "First release version must be 1."
            )

        return CommissionReleaseHistory(
            entries=self.entries + (entry,)
        )

    @property
    def latest(
        self,
    ) -> CommissionReleaseHistoryEntry | None:
        return (
            self.entries[-1]
            if self.entries
            else None
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "entries": [
                entry.to_dict()
                for entry in self.entries
            ]
        }


__all__ = [
    "CommissionReleaseHistoryError",
    "CommissionReleaseHistoryEntry",
    "CommissionReleaseHistory",
]
