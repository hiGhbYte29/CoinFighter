import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from app.core.exceptions import AppError
from app.infrastructure.storage.json_store import JsonStore

TaskState = Literal["PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELED"]


class TaskRegistry:
    def __init__(self, directory: Path, json_store: JsonStore) -> None:
        self.directory = directory
        self.json_store = json_store
        self.directory.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()

    async def create(self, kind: str, request: dict[str, Any]) -> dict[str, Any]:
        identifier = f"{kind}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
        task = {
            "task_id": identifier,
            "kind": kind,
            "status": "PENDING",
            "progress": 0,
            "message": "任务已创建",
            "request": request,
            "result": None,
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
        }
        async with self._lock:
            self.json_store.write(self.directory / f"{identifier}.json", task)
        return task

    async def update(self, task_id: str, **changes: Any) -> dict[str, Any]:
        async with self._lock:
            task = self.get(task_id)
            task.update(changes)
            task["updated_at"] = datetime.now(UTC).isoformat()
            self.json_store.write(self.directory / f"{task_id}.json", task)
        return task

    def get(self, task_id: str) -> dict[str, Any]:
        if "/" in task_id or ".." in task_id:
            raise AppError("TASK_NOT_FOUND", "任务不存在", status_code=404)
        task = self.json_store.read(self.directory / f"{task_id}.json")
        if task is None:
            raise AppError("TASK_NOT_FOUND", "任务不存在", status_code=404)
        return task

    def list(self, *, kind: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        tasks = []
        for path in sorted(self.directory.glob("*.json"), reverse=True):
            task = self.json_store.read(path)
            if task and (kind is None or task.get("kind") == kind):
                tasks.append(task)
            if len(tasks) >= limit:
                break
        return tasks
