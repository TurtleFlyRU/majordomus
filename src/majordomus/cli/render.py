from __future__ import annotations

import json

from majordomus.core.domain import ProjectReport, WorkspaceReport


def render_project_report(report: ProjectReport, fmt: str) -> str:
    if fmt == "json":
        return json.dumps(report.to_dict(), ensure_ascii=False, sort_keys=True, indent=2)

    lines = [f"project={report.project} status={report.status.value}"]
    lines.append(
        f"stats tasks={report.stats.tasks} errors={report.stats.errors} "
        f"warns={report.stats.warns} time_ms={report.stats.time_ms}"
    )
    for issue in report.issues:
        lines.append(
            f"[{issue.severity.value}] {issue.code} {issue.location.path}: {issue.message}"
        )
    return "\n".join(lines)


def render_workspace_report(report: WorkspaceReport, fmt: str) -> str:
    if fmt == "json":
        return json.dumps(report.to_dict(), ensure_ascii=False, sort_keys=True, indent=2)

    lines = [
        f"workspace={report.workspace} mode={report.mode.value} ordering={report.ordering.value}",
        (
            "summary "
            f"total={report.summary.total_projects} pass={report.summary.passed_projects} "
            f"fail={report.summary.failed_projects} skip={report.summary.skipped_projects} "
            f"errors={report.summary.errors} warns={report.summary.warns}"
        ),
    ]

    for issue in report.issues:
        lines.append(
            f"[WS][{issue.severity.value}] {issue.code} {issue.location.path}: {issue.message}"
        )

    for project_report in report.project_reports:
        lines.append(
            f"project={project_report.project} status={project_report.status.value} "
            f"tasks={project_report.stats.tasks} errors={project_report.stats.errors} "
            f"warns={project_report.stats.warns}"
        )
        for issue in project_report.issues:
            lines.append(
                f"  [{issue.severity.value}] {issue.code} {issue.location.path}: {issue.message}"
            )

    lines.append(f"exit_code={report.exit_code}")
    return "\n".join(lines)
