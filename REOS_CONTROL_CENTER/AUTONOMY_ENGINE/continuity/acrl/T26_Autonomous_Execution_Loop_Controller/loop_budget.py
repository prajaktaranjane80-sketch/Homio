from __future__ import annotations


def remaining_budget(
    loop,
) -> tuple[int, int, int]:
    return (
        max(
            0,
            loop.total_work_budget
            - loop.work_consumed,
        ),
        max(
            0,
            loop.total_token_budget
            - loop.token_consumed,
        ),
        max(
            0,
            loop.total_context_budget
            - loop.context_consumed,
        ),
    )


def has_budget(
    loop,
    *,
    work: int = 0,
    tokens: int = 0,
    context: int = 0,
) -> bool:
    remaining = remaining_budget(
        loop
    )

    return (
        work <= remaining[0]
        and tokens <= remaining[1]
        and context <= remaining[2]
    )


def consume_budget(
    loop,
    *,
    work: int,
    tokens: int,
    context: int,
):
    if min(
        work,
        tokens,
        context,
    ) < 0:
        raise ValueError(
            "Budget consumption cannot be negative."
        )

    if not has_budget(
        loop,
        work=work,
        tokens=tokens,
        context=context,
    ):
        raise ValueError(
            "Loop budget exhausted."
        )

    return (
        loop.work_consumed + work,
        loop.token_consumed + tokens,
        loop.context_consumed + context,
    )
