from __future__ import annotations

from majordomus.core.domain import Issue, Severity

_SEVERITY_ORDER = {
    Severity.ERROR: 0,
    Severity.WARN: 1,
}


def sort_issues(issues: list[Issue]) -> list[Issue]:
    return sorted(
        issues,
        key=lambda item: (
            _SEVERITY_ORDER[item.severity],
            item.code,
            item.project or "",
            item.location.path,
            item.task_id or "",
            item.message,
        ),
    )
