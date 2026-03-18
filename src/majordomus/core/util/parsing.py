from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from majordomus.core.domain import Issue, Location, Severity


class LineNumberSafeLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        mapping = super().construct_mapping(node, deep=deep)
        mapping["__line__"] = node.start_mark.line + 1
        return mapping


def parse_yaml_file(
    path: Path, code: str, message: str, project: str | None = None
) -> tuple[Any | None, list[Issue]]:
    try:
        content = path.read_text(encoding="utf-8")
        data = yaml.safe_load(content)
        return data, []
    except yaml.YAMLError as exc:
        line, col = 1, None
        if hasattr(exc, "problem_mark") and exc.problem_mark:
            line = exc.problem_mark.line + 1
            col = exc.problem_mark.column + 1
        issue = Issue(
            code=code,
            severity=Severity.ERROR,
            message=f"{message}: {exc}",
            location=Location(path=str(path), line=line, col=col),
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


def parse_yaml_with_line_numbers(
    path: Path, code: str, message: str, project: str | None = None
) -> tuple[Any | None, list[Issue]]:
    try:
        content = path.read_text(encoding="utf-8")
        data = yaml.load(content, Loader=LineNumberSafeLoader)
        return data, []
    except yaml.YAMLError as exc:
        line, col = 1, None
        if hasattr(exc, "problem_mark") and exc.problem_mark:
            line = exc.problem_mark.line + 1
            col = exc.problem_mark.column + 1
        issue = Issue(
            code=code,
            severity=Severity.ERROR,
            message=f"{message}: {exc}",
            location=Location(path=str(path), line=line, col=col),
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


def parse_json_with_line_numbers(
    path: Path, code: str, message: str, project: str | None = None
) -> tuple[Any | None, list[Issue]]:
    # JSON is valid YAML, so we reuse the YAML loader to get line numbers
    return parse_yaml_with_line_numbers(path, code, message, project)
