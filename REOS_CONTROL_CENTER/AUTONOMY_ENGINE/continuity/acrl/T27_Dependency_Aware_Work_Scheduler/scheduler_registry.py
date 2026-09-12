from __future__ import annotations


class SchedulerRegistry:
    schema_version = "1.0"
    scheduler_version = "1.0"

    def validate(self) -> None:
        if not self.schema_version:
            raise ValueError(
                "scheduler schema version missing."
            )

        if not self.scheduler_version:
            raise ValueError(
                "scheduler version missing."
            )
