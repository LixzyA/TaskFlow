"""Retry failed task attempts with exponential backoff."""

import asyncio
from collections.abc import Awaitable, Callable

from .config import Task
from .storage import TaskResult


async def run_with_retries(task: Task, run_once: Callable[[Task], Awaitable[TaskResult]]) -> TaskResult:
    for attempt in range(task.retries + 1):
        result = await run_once(task)
        if result.status == "SUCCESS" or attempt == task.retries:
            return result
        await asyncio.sleep(task.retry_backoff_seconds * (2**attempt))
    raise AssertionError("unreachable")
