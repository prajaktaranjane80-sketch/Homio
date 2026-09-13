from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class TestTarget:
    path: str
    reason: str
    confidence: str


class TestRuntime:
    """Targeted test discovery before broad regression."""

    def __init__(
        self,
        root: Path,
        *,
        max_targets: int = 20,
    ) -> None:
        self.root = Path(root).resolve()
        self.max_targets = max_targets

    def discover(
        self,
        keywords: list[str],
    ) -> list[TestTarget]:
        terms = {
            item.lower().strip()
            for item in keywords
            if item and item.strip()
        }

        result = []

        for path in self.root.rglob("test_*.py"):
            relative = path.relative_to(
                self.root
            ).as_posix()

            if any(
                term in relative.lower()
                for term in terms
            ):
                result.append(
                    TestTarget(
                        path=relative,
                        reason="filename match",
                        confidence="SUPPORTED",
                    )
                )
            else:
                try:
                    source = path.read_text(
                        encoding="utf-8"
                    )
                    tree = ast.parse(source)
                    text = ast.unparse(tree).lower()
                except (
                    OSError,
                    SyntaxError,
                    ValueError,
                ):
                    continue

                if any(term in text for term in terms):
                    result.append(
                        TestTarget(
                            path=relative,
                            reason="source match",
                            confidence="SUPPORTED",
                        )
                    )

            if len(result) >= self.max_targets:
                break

        return result
