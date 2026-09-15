import asyncio

from app.v0.config import Task
from app.v0.retry import run_with_retries
from app.v0.storage import TaskResult


def test_retry_uses_exponential_backoff(monkeypatch):
    attempts = 0
    delays = []

    async def run_once(task):
        nonlocal attempts
        attempts += 1
        status = "SUCCESS" if attempts == 3 else "FAILED"
        return TaskResult(task.name, "start", "end", 0 if status == "SUCCESS" else 1, "", "", status)

    async def sleep(delay):
        delays.append(delay)

    monkeypatch.setattr(asyncio, "sleep", sleep)
    result = asyncio.run(run_with_retries(Task("a", "echo", retries=2, retry_backoff_seconds=0.5), run_once))
    assert result.status == "SUCCESS"
    assert (attempts, delays) == (3, [0.5, 1.0])
