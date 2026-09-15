"""Configuration loading and validation."""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any
from pydantic import TypeAdapter, ValidationError

from .validation import TaskInput


@dataclass(frozen=True)
class Task:
    name: str
    command: str
    timeout: float | None = None
    dependencies: tuple[str, ...] = ()
    retries: int = 0
    retry_backoff_seconds: float = 1.0


def load_config(path: str | Path) -> list[Task]:
    """Load a task list from a JSON file, raising ValueError for bad input."""
    config_path = Path(path)
    try:
        data: Any = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read config {config_path}: {exc}") from exc

    raw_tasks = data if isinstance(data, list) else data.get("tasks") if isinstance(data, dict) else None
    if not isinstance(raw_tasks, list):
        raise ValueError("config must be a JSON list or an object with a 'tasks' list")

    try:
        inputs = TypeAdapter(list[TaskInput]).validate_python(raw_tasks)
    except ValidationError as exc:
        raise ValueError(f"invalid task configuration: {exc}") from exc

    tasks: list[Task] = []
    names: set[str] = set()
    for task_input in inputs:
        name = task_input.name
        if name in names:
            raise ValueError(f"duplicate task name: {name}")
        names.add(name)
        tasks.append(Task(name, task_input.command, task_input.timeout, tuple(task_input.dependencies), task_input.retries, task_input.retry_backoff_seconds))

    known = {task.name for task in tasks}
    for task in tasks:
        missing = set(task.dependencies) - known
        if missing:
            raise ValueError(f"task {task.name!r} has unknown dependencies: {', '.join(sorted(missing))}")
    _check_cycles(tasks)
    return tasks


def _check_cycles(tasks: list[Task]) -> None:
    state: dict[str, int] = {}
    by_name = {task.name: task for task in tasks}

    def visit(name: str) -> None:
        if state.get(name) == 1:
            raise ValueError("task dependencies contain a cycle")
        if state.get(name) == 2:
            return
        state[name] = 1
        for dependency in by_name[name].dependencies:
            visit(dependency)
        state[name] = 2

    for task in tasks:
        visit(task.name)
