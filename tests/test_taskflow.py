import asyncio
import json

from app.v0.config import load_config
from app.v0.executor import execute
from app.v0.storage import Storage


def test_dependencies_failure_and_timeout_are_persisted(tmp_path):
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"tasks": [
        {"name": "bad", "command": "python -c \"import sys; sys.exit(2)\""},
        {"name": "blocked", "command": "python -c \"print('must not run')\"", "dependencies": ["bad"]},
        {"name": "slow", "command": "python -c \"import time; time.sleep(1)\"", "timeout": 0.05},
    ]}), encoding="utf-8")
    storage = Storage(tmp_path / "taskflow.db")
    results = asyncio.run(execute(load_config(config), storage))
    assert [result.status for result in results] == ["FAILED", "FAILED", "TIMEOUT"]
    assert len(storage.history()) == 3
