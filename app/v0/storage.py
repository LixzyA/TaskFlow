"""SQLite persistence for task runs."""

from dataclasses import dataclass
from datetime import datetime, timezone
import sqlite3
from pathlib import Path


@dataclass(frozen=True)
class TaskResult:
    task_name: str
    start_time: str
    end_time: str
    exit_code: int | None
    stdout: str
    stderr: str
    status: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Storage:
    def __init__(self, path: str | Path = "taskflow.db") -> None:
        self.path = str(path)
        with self._connect() as connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS task_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, task_name TEXT NOT NULL,
                start_time TEXT NOT NULL, end_time TEXT NOT NULL, exit_code INTEGER,
                stdout TEXT NOT NULL, stderr TEXT NOT NULL, status TEXT NOT NULL
            )""")

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def save(self, result: TaskResult) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO task_runs (task_name,start_time,end_time,exit_code,stdout,stderr,status) VALUES (?,?,?,?,?,?,?)",
                (result.task_name, result.start_time, result.end_time, result.exit_code, result.stdout, result.stderr, result.status),
            )

    def history(self) -> list[tuple]:
        with self._connect() as connection:
            return connection.execute(
                "SELECT task_name,start_time,end_time,exit_code,status FROM task_runs ORDER BY id"
            ).fetchall()
