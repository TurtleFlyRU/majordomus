from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from majordomus.core.domain import Issue, Location, Severity


def parse_yaml_file(
    path: Path, code: str, message: str, project: str | None = None
) -> tuple[Any | None, list[Issue]]:
    try:
        content = path.read_text(encoding="utf-8")
        data = yaml.safe_load(content)
        return data, []
    except yaml.YAMLError as exc:
        issue = Issue(
            code=code,
            severity=Severity.ERROR,
            message=f"{message}: {exc}",
            location=Location(path=str(path)),
            project=project,
        )
        return None, [issue]
    except OSError as exc:
        issue = Issue(
            code=code,
            severity=Severity.ERROR,
            message=f"{message}: {exc}",
            location=Location(path=str(path)),
            project=project,
        )
        return None, [issue]


def parse_json_file(
    path: Path, code: str, message: str, project: str | None = None
) -> tuple[Any | None, list[Issue]]:
    try:
        content = path.read_text(encoding="utf-8")
        data = json.loads(content)
        return data, []
    except json.JSONDecodeError as exc:
        issue = Issue(
            code=code,
            severity=Severity.ERROR,
            message=f"{message}: {exc.msg}",
            location=Location(path=str(path), line=exc.lineno, col=exc.colno),
            project=project,
        )
        return None, [issue]
    except OSError as exc:
        issue = Issue(
            code=code,
            severity=Severity.ERROR,
            message=f"{message}: {exc}",
            location=Location(path=str(path)),
            project=project,
        )
        return None, [issue]
