from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class Task(BaseModel):
    id: str
    name: str
    my_party: str
    created_at: str
    status: str = Field(default="created")
    message: Optional[str] = None
    input_dir: Path
    intermediate_dir: Path
    final_dir: Path


class TaskManager:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.index_path = self.root / "index.json"

    def _load_index(self) -> Dict[str, Task]:
        if not self.index_path.exists():
            return {}
        data = json.loads(self.index_path.read_text(encoding="utf-8"))
        return {k: Task(**v) for k, v in data.items()}

    def _save_index(self, data: Dict[str, Task]) -> None:
        payload = {k: v.model_dump() for k, v in data.items()}
        self.index_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def create_task(self, name: str, my_party: str) -> Task:
        data = self._load_index()
        task_id = uuid.uuid4().hex[:8]
        task_dir = self.root / task_id
        input_dir = task_dir / "input"
        intermediate_dir = task_dir / "intermediate"
        final_dir = task_dir / "final"
        for p in (input_dir, intermediate_dir, final_dir):
            p.mkdir(parents=True, exist_ok=True)
        task = Task(
            id=task_id,
            name=name,
            my_party=my_party,
            created_at=datetime.utcnow().isoformat(),
            status="created",
            message=None,
            input_dir=input_dir,
            intermediate_dir=intermediate_dir,
            final_dir=final_dir,
        )
        data[task_id] = task
        self._save_index(data)
        return task

    def list_tasks(self) -> List[Task]:
        return list(self._load_index().values())

    def get_task(self, task_id: str) -> Task:
        data = self._load_index()
        if task_id not in data:
            raise KeyError(f"Task {task_id} not found")
        return data[task_id]

    def update_status(self, task_id: str, status: str, message: Optional[str] = None) -> Task:
        data = self._load_index()
        if task_id not in data:
            raise KeyError(f"Task {task_id} not found")
        task = data[task_id]
        task.status = status
        task.message = message
        data[task_id] = task
        self._save_index(data)
        return task
