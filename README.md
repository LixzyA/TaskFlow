## TaskFlow

```powershell
uv run taskflow run config.json
uv run taskflow run config.json --dry-run
uv run taskflow history
```

Configuration may be a task list or `{ "tasks": [...] }`:

```json
{
  "tasks": [
    {"name": "build", "command": "python -c \"print('ok')\""},
    {"name": "test", "command": "python -m pytest", "dependencies": ["build"], "timeout": 30, "retries": 2, "retry_backoff_seconds": 1}
  ]
}
```
