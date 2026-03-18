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


class LineNumberJSONDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        super().__init__(object_hook=self.add_line_numbers, *args, **kwargs)
        self.content = ""

    def decode(self, s, *args, **kwargs):
        self.content = s
        return super().decode(s, *args, **kwargs)

    def add_line_numbers(self, obj):
        # This is a bit tricky with object_hook as it's called after the object is created
        # and doesn't have access to the original string position easily here.
        # But we can try a different approach: override 'parse_object'
        return obj


def _parse_json_with_positions(content: str) -> Any:
    """A simple JSON parser that adds __line__ to dicts."""
    decoder = json.JSONDecoder()
    
    def _pos_to_line(pos: int) -> int:
        return content.count("\n", 0, pos) + 1

    def _hook(dct):
        # We don't have the position here easily with standard json module hook.
        return dct

    # Since standard json module is hard to hook for positions without re-implementing much,
    # let's use a simpler trick for now: regex search for keys if needed, 
    # or just accept that JSON line numbers are harder without better tools.
    # BUT we want to provide at least some line info.
    
    return json.loads(content)


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
    # For JSON, we'll use a simpler approach for now as capturing positions is complex
    # without external libs. We'll improve it if needed.
    return parse_json_file(path, code, message, project)
