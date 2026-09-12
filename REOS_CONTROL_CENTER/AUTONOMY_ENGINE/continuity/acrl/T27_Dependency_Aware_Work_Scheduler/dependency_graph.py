from __future__ import annotations

from .scheduler_identity import fingerprint
from .scheduler_models import WorkUnit


class DependencyGraph:
    def __init__(
        self,
        work_units: tuple[WorkUnit, ...],
    ) -> None:
        self.work_units = {
            item.work_id: item
            for item in work_units
        }

    def fingerprint(self) -> str:
        payload = [
            self.work_units[key].to_dict()
            for key in sorted(self.work_units)
        ]
        return fingerprint(payload)

    def validate_nodes(self) -> None:
        known = set(self.work_units)

        for item in self.work_units.values():
            if item.work_id in item.dependencies:
                raise ValueError(
                    f"Self dependency: {item.work_id}"
                )

            for dependency in item.dependencies:
                if dependency not in known:
                    raise ValueError(
                        f"Unknown dependency: "
                        f"{item.work_id}->{dependency}"
                    )

    def detect_cycle(self) -> bool:
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(
            work_id: str,
        ) -> bool:
            if work_id in visiting:
                return True

            if work_id in visited:
                return False

            visiting.add(work_id)

            for dependency in sorted(
                self.work_units[
                    work_id
                ].dependencies
            ):
                if visit(dependency):
                    return True

            visiting.remove(work_id)
            visited.add(work_id)
            return False

        for work_id in sorted(
            self.work_units
        ):
            if visit(work_id):
                return True

        return False
