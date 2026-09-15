"""TaskFlow command-line interface."""

import argparse
import asyncio
from pathlib import Path

from .config import load_config
from .executor import execute
from .storage import Storage


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="taskflow", description="Run dependent shell tasks concurrently.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run", help="execute tasks from a JSON config")
    run_parser.add_argument("config", type=Path)
    run_parser.add_argument("--dry-run", action="store_true", help="show dependencies without executing tasks")
    subparsers.add_parser("history", help="show previous task runs")
    args = parser.parse_args(argv)
    storage = Storage()
    if args.command == "run":
        try:
            tasks = load_config(args.config)
            if args.dry_run:
                for task in tasks:
                    dependencies = ", ".join(task.dependencies) or "none"
                    print(f"{task.name}: depends on {dependencies}")
                return 0
            results = asyncio.run(execute(tasks, storage))
        except (ValueError, OSError, RuntimeError) as exc:
            parser.error(str(exc))
        for result in results:
            print(f"{result.task_name}: {result.status}")
        return 0 if all(result.status == "SUCCESS" for result in results) else 1

    rows = storage.history()
    print("TASK\tSTART\tEND\tEXIT\tSTATUS")
    for row in rows:
        print("\t".join("-" if value is None else str(value) for value in row))
    return 0
