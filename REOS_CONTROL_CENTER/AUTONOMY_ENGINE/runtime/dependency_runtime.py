from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class DependencyFinding:
    source: str
    target: str
    relation: str
    confidence: str


class DependencyRuntime:
    """Conservative dependency locator."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()

    def resolve_module(
        self,
        module_name: str,
    ) -> list[DependencyFinding]:
        normalized = module_name.replace(
            ".",
            "/",
        )

        candidates = (
            self.root / f"{normalized}.py",
            self.root / normalized / "__init__.py",
        )

        result = []

        for candidate in candidates:
            if candidate.exists():
                result.append(
                    DependencyFinding(
                        source=module_name,
                        target=str(
                            candidate.relative_to(self.root)
                        ),
                        relation="MODULE_RESOLUTION",
                        confidence="VERIFIED",
                    )
                )

        return result

    @staticmethod
    def deduplicate(
        findings: list[DependencyFinding],
    ) -> list[DependencyFinding]:
        seen = set()
        result = []

        for item in findings:
            key = (
                item.source,
                item.target,
                item.relation,
            )

            if key in seen:
                continue

            seen.add(key)
            result.append(item)

        return result
