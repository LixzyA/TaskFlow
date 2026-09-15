"""Dependency-aware concurrent task execution."""

import asyncio

from .config import Task
from .retry import run_with_retries
from .storage import Storage, TaskResult, utc_now


async def _run_task(task: Task) -> TaskResult:
    start = utc_now()
    process = await asyncio.create_subprocess_shell(
        task.command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    try:
        communicate = process.communicate()
        stdout, stderr = await asyncio.wait_for(communicate, task.timeout) if task.timeout else await communicate
        return TaskResult(task.name, start, utc_now(), process.returncode, stdout.decode(errors="replace"), stderr.decode(errors="replace"), "SUCCESS" if process.returncode == 0 else "FAILED")
    except asyncio.TimeoutError:
        process.kill()
        stdout, stderr = await process.communicate()
        return TaskResult(task.name, start, utc_now(), None, stdout.decode(errors="replace"), stderr.decode(errors="replace"), "TIMEOUT")


async def execute(tasks: list[Task], storage: Storage) -> list[TaskResult]:
    pending = {task.name: task for task in tasks}
    finished: dict[str, TaskResult] = {}
    running: dict[asyncio.Task[TaskResult], str] = {}

    while pending or running:
        for name, task in list(pending.items()):
            if not all(dependency in finished for dependency in task.dependencies):
                continue
            del pending[name]
            if all(finished[dependency].status == "SUCCESS" for dependency in task.dependencies):
                running[asyncio.create_task(run_with_retries(task, _run_task))] = name
            else:
                result = TaskResult(name, utc_now(), utc_now(), None, "", "dependency failed", "FAILED")
                storage.save(result)
                finished[name] = result
        if running:
            done, _ = await asyncio.wait(running, return_when=asyncio.FIRST_COMPLETED)
            for future in done:
                name = running.pop(future)
                result = future.result()
                storage.save(result)
                finished[name] = result
        elif pending:
            raise RuntimeError("unable to resolve task dependencies")
    return [finished[task.name] for task in tasks]
