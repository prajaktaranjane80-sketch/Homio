from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Iterable


@dataclass(frozen=True, slots=True)
class ContextItem:
    category: str
    key: str
    value: Any
    priority: int


class WorkContext:
    """Compact deterministic context compiler."""

    SECRET_KEYS = frozenset(
        {
            "password",
            "token",
            "secret",
            "api_key",
            "private_key",
            "cookie",
            "authorization",
        }
    )

    def __init__(
        self,
        *,
        max_items: int = 80,
        max_chars: int = 24000,
    ) -> None:
        self.max_items = max_items
        self.max_chars = max_chars

    @classmethod
    def redact(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: (
                    "[REDACTED]"
                    if str(key).lower() in cls.SECRET_KEYS
                    else cls.redact(item)
                )
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [cls.redact(item) for item in value]
        return value

    def compile(
        self,
        items: Iterable[ContextItem],
    ) -> dict[str, Any]:
        ordered = sorted(
            items,
            key=lambda x: (-x.priority, x.category, x.key),
        )[: self.max_items]

        result: list[dict[str, Any]] = []

        for item in ordered:
            candidate = asdict(item)
            candidate["value"] = (
                "[REDACTED]"
                if str(item.key).lower() in self.SECRET_KEYS
                else self.redact(item.value)
            )

            current_size = len(str(result + [candidate]))
            if current_size > self.max_chars:
                break

            result.append(candidate)

        return {
            "items": result,
            "count": len(result),
            "max_chars": self.max_chars,
            "full_file_dump": False,
        }
