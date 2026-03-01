from __future__ import annotations

from pathlib import Path

from majordomus.core.ports.filesystem import FileSystemPort


class TaskRegistry:
    def __init__(self, fs: FileSystemPort) -> None:
        self._fs = fs

    def list_task_files(self, governance_root: Path) -> list[Path]:
        tasks_dir = governance_root / "tasks"
        if not self._fs.is_dir(tasks_dir):
            return []
        return self._fs.glob(tasks_dir, "*.json")
