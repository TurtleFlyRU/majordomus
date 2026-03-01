from pathlib import Path

from majordomus.core.adapters.fs_local import LocalFileSystemAdapter
from majordomus.core.governance.task_registry import TaskRegistry


def test_task_registry_returns_lexicographically_sorted_files(tmp_path: Path) -> None:
    governance_root = tmp_path / ".majordomus"
    tasks = governance_root / "tasks"
    tasks.mkdir(parents=True)

    (tasks / "TASK-0010.json").write_text("{}", encoding="utf-8")
    (tasks / "TASK-0002.json").write_text("{}", encoding="utf-8")
    (tasks / "TASK-0001.json").write_text("{}", encoding="utf-8")

    registry = TaskRegistry(LocalFileSystemAdapter())

    files = registry.list_task_files(governance_root)

    assert [item.name for item in files] == ["TASK-0001.json", "TASK-0002.json", "TASK-0010.json"]
