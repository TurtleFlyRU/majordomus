from __future__ import annotations

from pathlib import Path

from majordomus.core.ports.filesystem import FileSystemPort


class LocalFileSystemAdapter(FileSystemPort):
    def exists(self, path: Path) -> bool:
        return path.exists()

    def is_dir(self, path: Path) -> bool:
        return path.is_dir()

    def is_file(self, path: Path) -> bool:
        return path.is_file()

    def read_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def glob(self, path: Path, pattern: str) -> list[Path]:
        return sorted(path.glob(pattern), key=lambda item: str(item))
