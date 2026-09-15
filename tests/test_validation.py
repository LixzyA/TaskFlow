import json

import pytest

from app.v0.config import load_config


def test_validation_accepts_retry_settings(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps([{"name": "a", "command": "echo a", "retries": 2, "retry_backoff_seconds": 0.1}]), encoding="utf-8")
    task = load_config(path)[0]
    assert (task.retries, task.retry_backoff_seconds) == (2, 0.1)


def test_validation_rejects_unknown_fields(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps([{"name": "a", "command": "echo a", "unexpected": True}]), encoding="utf-8")
    with pytest.raises(ValueError, match="invalid task configuration"):
        load_config(path)
