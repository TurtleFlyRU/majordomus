from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from majordomus.core.domain import Issue, Location, Severity


class ValidationCache:
    def __init__(self, cache_file: Path) -> None:
        self._cache_file = cache_file
        self._data: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if self._cache_file.exists():
            try:
                self._data = json.loads(self._cache_file.read_text(encoding="utf-8"))
            except Exception:
                self._data = {}

    def save(self) -> None:
        try:
            self._cache_file.parent.mkdir(parents=True, exist_ok=True)
            self._cache_file.write_text(
                json.dumps(self._data, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
        except Exception:
            pass

    def get_issues(self, file_path: Path, current_hash: str) -> list[Issue] | None:
        key = str(file_path.resolve())
        entry = self._data.get(key)
        if entry and entry.get("hash") == current_hash:
            raw_issues = entry.get("issues", [])
            return [Issue.from_dict(item) for item in raw_issues]
        return None

    def set_issues(self, file_path: Path, current_hash: str, issues: list[Issue]) -> None:
        key = str(file_path.resolve())
        self._data[key] = {
            "hash": current_hash,
            "issues": [issue.to_dict() for issue in issues]
        }

    @staticmethod
    def calculate_hash(path: Path) -> str:
        try:
            content = path.read_bytes()
            return hashlib.sha256(content).hexdigest()
        except Exception:
            return ""
